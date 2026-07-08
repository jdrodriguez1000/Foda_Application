"""Tests de integracion de Ingestion (feature ingestion, banda tracer_bullet,
etapa integration_tester).

Fuente: 600_features/ingestion/tracer_bullet/spec.md (CA-01..CA-21, DS-ING-1..9)
y state.json (bucle TDD 22/22 casos cerrado, tests/flows/test_ingestion.py);
700_architecture/system_design.md (SS7 estructura de carpetas, SS8 contrato de
artefactos multi-flujo D-014, SS9 abstraccion Flow/ClientContext);
800_persistence/decisions.md (D-014: los contratos de flujo permiten
dependencias multi-flujo, no solo del flujo inmediatamente anterior).

A diferencia de tests/flows/test_ingestion.py (unit, bucle TDD cerrado, 22/22
casos verdes, feature aislada), este modulo verifica que Ingestion se integra
correctamente con el resto del sistema REAL:

- Flow.run(ctx) de punta a punta sobre un ClientContext de un cliente creado
  por create_client (client_scaffold, CONFORME), con contract_data.json
  fabricado (simula Discovery, DIFERIDO) y map_client_data.json producido por
  una ejecucion REAL de Onboarding().run(ctx) (no un fixture inerte): valida
  el contrato multi-flujo D-014 (Ingestion depende de 010_discovery -dos
  flujos atras- y de 020_onboarding -el flujo inmediatamente anterior-,
  simultaneamente).
- Resolucion de rutas de requires/produces via Artifact + ClientContext real
  (010_discovery/, 020_onboarding/, 030_ingestion/, data/bronze/), sin asumir
  estructura.
- Interaccion con un flujo vecino downstream: el ingestion_report.json que
  Ingestion produce es exactamente el artefacto que un flujo downstream
  (p. ej. Cleaning/050) declararia como require, y lo consume sin fallar.
- Fallo temprano con error de contrato claro (FlowContractError, no una
  excepcion cruda) cuando falta contract_data.json o map_client_data.json en
  el cliente real, sin dejar artefactos parciales (ni reporte ni bronze).
- Aislamiento multi-tenant: dos clientes distintos bajo el mismo
  clients_root producen reporte y bronze independientes, sin fuga de datos
  entre clients/<cliente>/.
- Invariante de capas: Ingestion nunca escribe en silver/gold; bronze solo
  recibe los archivos validos (copia parcial, DS-ING-5) sobre el arbol real
  creado por create_client.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowContractError, FlowResult
from foda.core.scaffold import create_client
from foda.flows.f020_onboarding.onboarding import Onboarding
from foda.flows.f030_ingestion.ingestion import Ingestion

_VENTAS_HEADER = "fecha,sede,clase,cantidad,precio_unitario"
_VENTAS_ROWS = [
    "2024-01-01,Sede Centro,Agua 600ml,10,1200",
    "2024-01-02,Sede Norte,Cola 1.5L,5,2500",
]
_INVENTARIO_HEADER = "fecha;sede;clase;stock"
_INVENTARIO_ROWS = [
    "2024-01-01;Sede Centro;Agua 600ml;100",
    "2024-01-02;Sede Norte;Cola 1.5L;50",
]


def _contrato_discovery() -> dict:
    """Simula la salida de Discovery (010_discovery/contract_data.json,
    DIFERIDO, no-objetivo de spec.md): fuente de los archivos esperados
    (DS-ING-8). Dos datasets (ventas/inventario) coherentes por 'kind' con el
    contrato de onboarding usado para producir el map_client_data.json real
    (mismos kind/fields, DS-ING-8: sin chequeo de coherencia mapa<->contrato,
    pero el fixture se mantiene coherente a proposito)."""
    return {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "historical_data": {
            "datasets": [
                {
                    "kind": "ventas",
                    "source_medium": "csv",
                    "periodicity": "mensual",
                    "files": [
                        {
                            "name": "ventas.csv",
                            "period_start": "2023-01-01",
                            "period_end": "2025-12-31",
                        }
                    ],
                },
                {
                    "kind": "inventario",
                    "source_medium": "csv",
                    "periodicity": "mensual",
                    "files": [
                        {
                            "name": "inventario_2024.txt",
                            "period_start": "2024-01-01",
                            "period_end": "2024-12-31",
                        }
                    ],
                },
            ]
        },
    }


def _contrato_onboarding_coherente() -> dict:
    """contract_data.json (esquema completo de onboarding, D-058) coherente
    con _contrato_discovery(): mismos kind/nombres de archivo, con
    hierarchies + fields que Onboarding necesita para producir un
    map_client_data.json real via run(ctx) (no un fixture inerte)."""
    return {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "product_hierarchy": {
            "levels": ["familia", "categoria", "subcategoria", "clase"],
            "members": [
                {
                    "familia": "Bebidas",
                    "categoria": "Aguas",
                    "subcategoria": "Sin gas",
                    "clase": "Agua 600ml",
                },
                {
                    "familia": "Bebidas",
                    "categoria": "Gaseosas",
                    "subcategoria": "Cola",
                    "clase": "Cola 1.5L",
                },
            ],
        },
        "geography": {
            "levels": ["region", "pais", "ciudad", "sede"],
            "members": [
                {
                    "region": "Andina",
                    "pais": "Colombia",
                    "ciudad": "Bogota",
                    "sede": "Sede Centro",
                },
                {
                    "region": "Andina",
                    "pais": "Colombia",
                    "ciudad": "Medellin",
                    "sede": "Sede Norte",
                },
            ],
        },
        "historical_data": {
            "datasets": [
                {
                    "kind": "ventas",
                    "source_medium": "csv",
                    "periodicity": "mensual",
                    "fields": [
                        {"name": "fecha", "type": "date", "required": True, "maps_to": "time"},
                        {"name": "sede", "type": "string", "required": True, "maps_to": "geography.sede"},
                        {"name": "clase", "type": "string", "required": True, "maps_to": "product.clase"},
                        {"name": "cantidad", "type": "integer", "required": True, "maps_to": "measure"},
                        {"name": "precio_unitario", "type": "number", "required": False, "maps_to": None},
                    ],
                    "files": [
                        {
                            "name": "ventas.csv",
                            "period_start": "2023-01-01",
                            "period_end": "2025-12-31",
                        }
                    ],
                },
                {
                    "kind": "inventario",
                    "source_medium": "csv",
                    "periodicity": "mensual",
                    "fields": [
                        {"name": "fecha", "type": "date", "required": True, "maps_to": "time"},
                        {"name": "sede", "type": "string", "required": True, "maps_to": "geography.sede"},
                        {"name": "clase", "type": "string", "required": True, "maps_to": "product.clase"},
                        {"name": "stock", "type": "integer", "required": True, "maps_to": "measure"},
                    ],
                    "files": [
                        {
                            "name": "inventario_2024.txt",
                            "period_start": "2024-01-01",
                            "period_end": "2024-12-31",
                        }
                    ],
                },
            ]
        },
    }


def _preparar_cliente_real(name: str, clients_root: Path) -> ClientContext:
    """Crea un cliente real (create_client, CONFORME), escribe
    010_discovery/contract_data.json (simulando Discovery) y ejecuta
    Onboarding().run(ctx) de VERDAD para producir 020_onboarding/
    map_client_data.json (no un fixture inerte): ejercita el contrato
    multi-flujo D-014 en el que Ingestion depende de un artefacto de dos
    flujos atras (contract_data) y de uno del flujo inmediatamente anterior
    (map_client_data) a la vez. Devuelve el ClientContext ya listo, antes de
    depositar los archivos crudos del landing de Ingestion."""
    create_client(name, clients_root)
    ctx = ClientContext(name, clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True, exist_ok=True)
    contrato_path.write_text(
        json.dumps(_contrato_onboarding_coherente(), ensure_ascii=False),
        encoding="utf-8",
    )

    onboarding_result = Onboarding().run(ctx)
    assert onboarding_result.success is True

    # Ingestion deriva los archivos esperados de contract_data.json
    # (DS-ING-8), no del artefacto de onboarding: se sobreescribe con el
    # subconjunto minimo (ventas + inventario, sin geography/product_hierarchy)
    # que Ingestion realmente consume, dejando intacto map_client_data.json
    # ya producido por la corrida real de Onboarding.
    contrato_path.write_text(
        json.dumps(_contrato_discovery(), ensure_ascii=False), encoding="utf-8"
    )
    return ctx


def _depositar_landing(ctx: ClientContext, files: dict[str, str]) -> None:
    landing_dir = ctx.inputs_dir / "030_ingestion"
    landing_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (landing_dir / name).write_text(content, encoding="utf-8")


def _archivos_validos() -> dict[str, str]:
    return {
        "ventas.csv": "\n".join([_VENTAS_HEADER, *_VENTAS_ROWS]) + "\n",
        "inventario_2024.txt": "\n".join([_INVENTARIO_HEADER, *_INVENTARIO_ROWS])
        + "\n",
    }


class _FlowVecinoDownstream(Flow):
    """Flujo de juguete que simula un downstream real (p. ej. Cleaning/050):
    declara como require exactamente el ingestion_report.json que Ingestion
    produce y, si existe, lo parsea y expone summary.files_ingested como
    salida trivial. Solo verifica la interaccion entre flujos vecinos (SS8,
    D-014), no testea Ingestion en si (fuera de alcance)."""

    name = "flujo_vecino_downstream_integracion"
    requires = [
        Artifact(
            name="ingestion_report", base="outputs",
            relative="030_ingestion/ingestion_report.json",
        )
    ]
    produces = [
        Artifact(
            name="resumen", base="outputs",
            relative="040_vecino/resumen.json",
        )
    ]

    def execute(self, ctx: ClientContext) -> FlowResult:
        reporte = json.loads(self.requires[0].path(ctx).read_text(encoding="utf-8"))
        self._resumen = {"files_ingested": reporte["summary"]["files_ingested"]}
        return FlowResult(success=True, outputs=[self.produces[0].path(ctx)])

    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
        path = self.produces[0].path(ctx)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._resumen), encoding="utf-8")


def test_run_end_to_end_sobre_cliente_real_con_map_producido_por_onboarding_real(
    tmp_path: Path,
) -> None:
    """Ingestion().run(ctx) de punta a punta sobre un ClientContext de un
    cliente real (create_client), con map_client_data.json producido por una
    corrida REAL de Onboarding (no un fixture inerte): contrato multi-flujo
    D-014 (contract_data de 010_discovery + map_client_data de
    020_onboarding). Los 2 archivos declarados y validos se copian a bronze,
    el reporte queda sin inconsistencias y success=True."""
    clients_root = tmp_path / "clients"
    ctx = _preparar_cliente_real("ABC", clients_root)
    _depositar_landing(ctx, _archivos_validos())

    result = Ingestion().run(ctx)

    ruta_reporte = ctx.outputs_dir / "030_ingestion" / "ingestion_report.json"
    assert isinstance(result, FlowResult)
    assert result.success is True
    assert ruta_reporte in result.outputs
    assert ruta_reporte.is_file()

    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))
    assert reporte["success"] is True
    assert reporte["summary"] == {
        "datasets_declared": 2,
        "files_declared": 2,
        "files_ingested": 2,
        "files_with_inconsistencies": 0,
    }
    assert reporte["unexpected_files"] == []
    assert reporte["inconsistencies"] == []

    for name in ("ventas.csv", "inventario_2024.txt"):
        bronze_path = ctx.bronze_dir / name
        assert bronze_path.is_file()
        landing_path = ctx.inputs_dir / "030_ingestion" / name
        assert bronze_path.read_bytes() == landing_path.read_bytes()


def test_run_exitoso_no_toca_silver_ni_gold_del_cliente_real(tmp_path: Path) -> None:
    """Invariante de capas: tras un run(ctx) exitoso sobre el arbol REAL
    creado por create_client, silver/gold quedan vacios (Ingestion solo
    escribe en bronze, nunca transforma ni promueve datos)."""
    clients_root = tmp_path / "clients"
    ctx = _preparar_cliente_real("Wayne", clients_root)
    _depositar_landing(ctx, _archivos_validos())

    Ingestion().run(ctx)

    for layer_dir in (ctx.silver_dir, ctx.gold_dir):
        assert layer_dir.is_dir()
        assert list(layer_dir.iterdir()) == []


def test_run_falla_temprano_con_flow_contract_error_si_falta_contract_data_en_cliente_real(
    tmp_path: Path,
) -> None:
    """Camino de fallo de contrato integrado (CA-21): sobre un cliente real
    con map_client_data.json ya producido pero SIN contract_data.json, run(ctx)
    lanza FlowContractError (no una excepcion cruda como KeyError/
    FileNotFoundError) y no deja ni ingestion_report.json ni copias en
    bronze."""
    clients_root = tmp_path / "clients"
    create_client("Globex", clients_root)
    ctx = ClientContext("Globex", clients_root)

    mapa_path = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa_path.parent.mkdir(parents=True, exist_ok=True)
    mapa_path.write_text(json.dumps({"datasets": []}), encoding="utf-8")

    with pytest.raises(FlowContractError, match="contract_data"):
        Ingestion().run(ctx)

    assert not (ctx.outputs_dir / "030_ingestion" / "ingestion_report.json").exists()
    assert ctx.bronze_dir.is_dir()
    assert list(ctx.bronze_dir.iterdir()) == []


def test_run_falla_temprano_con_flow_contract_error_si_falta_map_client_data_en_cliente_real(
    tmp_path: Path,
) -> None:
    """Camino de fallo de contrato integrado (CA-21), segundo require: sobre
    un cliente real con contract_data.json presente pero SIN
    map_client_data.json (Onboarding aun no corrio), run(ctx) lanza
    FlowContractError y no deja artefactos parciales."""
    clients_root = tmp_path / "clients"
    create_client("Initech", clients_root)
    ctx = ClientContext("Initech", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True, exist_ok=True)
    contrato_path.write_text(
        json.dumps(_contrato_discovery(), ensure_ascii=False), encoding="utf-8"
    )
    _depositar_landing(ctx, _archivos_validos())

    with pytest.raises(FlowContractError, match="map_client_data"):
        Ingestion().run(ctx)

    assert not (ctx.outputs_dir / "030_ingestion" / "ingestion_report.json").exists()
    assert ctx.bronze_dir.is_dir()
    assert list(ctx.bronze_dir.iterdir()) == []


def test_run_produce_artefacto_consumible_sin_fallar_por_un_flujo_vecino_downstream_real(
    tmp_path: Path,
) -> None:
    """Interaccion con flujos vecinos downstream (SS8, D-014): el
    ingestion_report.json que Ingestion produce es exactamente el artefacto
    que un flujo downstream declara como require, y ese flujo vecino lo
    consume sin fallar sobre el mismo ClientContext real."""
    clients_root = tmp_path / "clients"
    ctx = _preparar_cliente_real("Umbrella", clients_root)
    _depositar_landing(ctx, _archivos_validos())

    resultado_ingestion = Ingestion().run(ctx)
    assert resultado_ingestion.success is True

    resultado_vecino = _FlowVecinoDownstream().run(ctx)

    assert resultado_vecino.success is True
    ruta_resumen = ctx.outputs_dir / "040_vecino" / "resumen.json"
    assert ruta_resumen.is_file()
    assert json.loads(ruta_resumen.read_text(encoding="utf-8")) == {
        "files_ingested": 2
    }


def test_inconsistencia_parcial_real_copia_solo_los_validos_a_bronze_y_success_false(
    tmp_path: Path,
) -> None:
    """CA-18 integrado: sobre un cliente real con map_client_data.json real
    (Onboarding), un lote con 1 archivo valido y 1 con columna requerida
    ausente ('stock' de inventario_2024.txt) copia solo el valido a bronze,
    excluye el invalido, y el reporte refleja ambos estados con
    success=False."""
    clients_root = tmp_path / "clients"
    ctx = _preparar_cliente_real("Soylent", clients_root)
    archivos = _archivos_validos()
    archivos["inventario_2024.txt"] = (
        "fecha;sede;clase\n2024-01-01;Sede Centro;Agua 600ml\n"
    )
    _depositar_landing(ctx, archivos)

    result = Ingestion().run(ctx)

    assert result.success is False
    assert (ctx.bronze_dir / "ventas.csv").is_file()
    assert not (ctx.bronze_dir / "inventario_2024.txt").exists()

    reporte = json.loads(
        (ctx.outputs_dir / "030_ingestion" / "ingestion_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert reporte["success"] is False
    inventario_file = next(
        file_
        for dataset in reporte["datasets"]
        if dataset["kind"] == "inventario"
        for file_ in dataset["files"]
    )
    assert inventario_file["status"] == "rejected"
    assert inventario_file["bronze_path"] is None
    assert any(
        inconsistency["type"] == "missing_column"
        for inconsistency in inventario_file["inconsistencies"]
    )


def test_aislamiento_multi_tenant_entre_dos_clientes_reales_bajo_el_mismo_clients_root(
    tmp_path: Path,
) -> None:
    """Aislamiento multi-tenant (SS7): dos clientes reales distintos bajo el
    mismo clients_root, cada uno con su propio landing/contrato/mapa,
    producen reporte y copias en bronze independientes bajo
    clients/<cliente>/, sin fuga de datos entre ellos."""
    clients_root = tmp_path / "clients"

    ctx_a = _preparar_cliente_real("ClienteA", clients_root)
    _depositar_landing(ctx_a, _archivos_validos())

    ctx_b = _preparar_cliente_real("ClienteB", clients_root)
    # Cliente B: landing incompleto (falta inventario_2024.txt declarado).
    _depositar_landing(ctx_b, {"ventas.csv": _archivos_validos()["ventas.csv"]})

    resultado_a = Ingestion().run(ctx_a)
    resultado_b = Ingestion().run(ctx_b)

    assert resultado_a.success is True
    assert resultado_b.success is False

    assert (ctx_a.bronze_dir / "inventario_2024.txt").is_file()
    assert not (ctx_b.bronze_dir / "inventario_2024.txt").exists()

    reporte_b = json.loads(
        (ctx_b.outputs_dir / "030_ingestion" / "ingestion_report.json").read_text(
            encoding="utf-8"
        )
    )
    missing_entries = [
        inc for inc in reporte_b["inconsistencies"] if inc["type"] == "missing_file"
    ]
    assert len(missing_entries) == 1
    assert ctx_a.root != ctx_b.root
