"""Tests de integracion de Onboarding (feature onboarding, banda tracer_bullet,
etapa integration_tester, TSK-09).

Fuente: 600_features/onboarding/tracer_bullet/spec.md (CA-01, CA-12, CA-13,
CA-20, CA-21) y plan.md (Sec.5 Estrategia de Test: "Integracion
(integration_tester, TSK-09): end-to-end sobre el fixture real, comparando el
JSON producido contra un esperado fijo y verificando la invariante de no
tocar bronze/silver/gold"); 700_architecture/system_design.md (SS7 estructura
de carpetas, SS8 contrato de artefactos, SS9 abstraccion Flow/ClientContext).

A diferencia de tests/flows/test_onboarding.py (unit, bucle TDD cerrado,
22/22 casos verdes, feature aislada), este modulo verifica que Onboarding se
integra correctamente con el resto del sistema REAL:

- Flow.run(ctx) de punta a punta sobre un ClientContext de un cliente creado
  por create_client (client_scaffold, CONFORME), comparando el
  map_client_data.json producido contra un esperado FIJO (no solo aserciones
  parciales como en el unit).
- Resolucion de rutas de requires/produces via Artifact + ClientContext real
  (020_outputs/010_discovery/ y 020_outputs/020_onboarding/), sin asumir
  estructura: se verifica contra las propiedades reales de ClientContext.
- Interaccion con un flujo vecino: el map_client_data.json que Onboarding
  produce es exactamente el artefacto que un flujo downstream (p. ej.
  Ingestion/030) declararia como require, y lo consume sin fallar.
- Fallo temprano con error de contrato claro (FlowContractError, no una
  excepcion cruda) cuando el require no existe en el cliente real, sin dejar
  artefactos parciales.
- Aislamiento multi-tenant: dos clientes distintos bajo el mismo
  clients_root producen artefactos independientes, sin fuga de datos entre
  clients/<cliente>/.
- Invariante de capas: tras un run(ctx) exitoso, bronze/silver/gold quedan
  vacios (Onboarding no toca datos reales).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowContractError, FlowResult
from foda.core.scaffold import create_client
from foda.flows.f020_onboarding.onboarding import Onboarding


def _contrato_valido() -> dict:
    """Mismo fixture acordado (ventas + inventario, 4+4 niveles) que
    tests/flows/test_onboarding.py; se duplica aqui deliberadamente (no se
    importa del modulo unit) para que este archivo de integracion sea
    autocontenido y no dependa de la organizacion interna del bucle TDD."""
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
                {
                    "familia": "Snacks",
                    "categoria": "Papas",
                    "subcategoria": "Fritas",
                    "clase": "Papas 45g",
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
                            "name": "ventas_2023_2025.csv",
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
                            "name": "inventario_2024.csv",
                            "period_start": "2024-01-01",
                            "period_end": "2024-12-31",
                        },
                        {
                            "name": "inventario_2025.csv",
                            "period_start": "2025-01-01",
                            "period_end": "2025-12-31",
                        },
                    ],
                },
            ]
        },
    }


def _mapa_esperado() -> dict:
    """Esperado FIJO (DS-ONB-2/DS-ONB-4) para el fixture valido, derivado a
    mano del esquema acordado en spec.md; sirve para comparar el JSON
    producido por Onboarding contra un contrato, no contra su propia
    implementacion (evita el falso-verde de comparar codigo contra si
    mismo)."""
    return {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "hierarchies": {
            "product": {
                "levels": ["familia", "categoria", "subcategoria", "clase"],
                "depth": 4,
                "unique_values": {
                    "familia": ["Bebidas", "Snacks"],
                    "categoria": ["Aguas", "Gaseosas", "Papas"],
                    "subcategoria": ["Cola", "Fritas", "Sin gas"],
                    "clase": ["Agua 600ml", "Cola 1.5L", "Papas 45g"],
                },
                "unique_counts": {
                    "familia": 2,
                    "categoria": 3,
                    "subcategoria": 3,
                    "clase": 3,
                },
            },
            "geography": {
                "levels": ["region", "pais", "ciudad", "sede"],
                "depth": 4,
                "unique_values": {
                    "region": ["Andina"],
                    "pais": ["Colombia"],
                    "ciudad": ["Bogota", "Medellin"],
                    "sede": ["Sede Centro", "Sede Norte"],
                },
                "unique_counts": {"region": 1, "pais": 1, "ciudad": 2, "sede": 2},
            },
        },
        "datasets": [
            {
                "kind": "ventas",
                "source_medium": "csv",
                "periodicity": "mensual",
                "file_count": 1,
                "files": [
                    {
                        "name": "ventas_2023_2025.csv",
                        "period_start": "2023-01-01",
                        "period_end": "2025-12-31",
                    }
                ],
                "fields": [
                    {"name": "fecha", "type": "date", "required": True, "maps_to": "time"},
                    {"name": "sede", "type": "string", "required": True, "maps_to": "geography.sede"},
                    {"name": "clase", "type": "string", "required": True, "maps_to": "product.clase"},
                    {"name": "cantidad", "type": "integer", "required": True, "maps_to": "measure"},
                    {"name": "precio_unitario", "type": "number", "required": False, "maps_to": None},
                ],
            },
            {
                "kind": "inventario",
                "source_medium": "csv",
                "periodicity": "mensual",
                "file_count": 2,
                "files": [
                    {
                        "name": "inventario_2024.csv",
                        "period_start": "2024-01-01",
                        "period_end": "2024-12-31",
                    },
                    {
                        "name": "inventario_2025.csv",
                        "period_start": "2025-01-01",
                        "period_end": "2025-12-31",
                    },
                ],
                "fields": [
                    {"name": "fecha", "type": "date", "required": True, "maps_to": "time"},
                    {"name": "sede", "type": "string", "required": True, "maps_to": "geography.sede"},
                    {"name": "clase", "type": "string", "required": True, "maps_to": "product.clase"},
                    {"name": "stock", "type": "integer", "required": True, "maps_to": "measure"},
                ],
            },
        ],
        "totals": {"dataset_count": 2, "file_count": 3},
    }


def _escribir_contrato(ctx: ClientContext, contrato: dict) -> Path:
    """Escribe contract_data.json bajo la ruta real del require
    (010_discovery/, resuelta via Artifact + ClientContext), devolviendo la
    ruta escrita."""
    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True, exist_ok=True)
    contrato_path.write_text(
        json.dumps(contrato, ensure_ascii=False), encoding="utf-8"
    )
    return contrato_path


class _FlowVecino(Flow):
    """Flujo de juguete que simula el downstream (p. ej. Ingestion/030):
    declara como require exactamente el map_client_data.json producido por
    Onboarding y, si existe, lo parsea y expone dataset_count como salida
    trivial. Sirve solo para verificar la interaccion entre flujos vecinos
    (SS8), no para testear Ingestion (fuera de alcance, no-objetivo de
    spec.md)."""

    name = "flujo_vecino_integracion"
    requires = [
        Artifact(
            name="map_client_data", base="outputs",
            relative="020_onboarding/map_client_data.json",
        )
    ]
    produces = [
        Artifact(
            name="resumen", base="outputs",
            relative="030_vecino/resumen.json",
        )
    ]

    def execute(self, ctx: ClientContext) -> FlowResult:
        mapa = json.loads(self.requires[0].path(ctx).read_text(encoding="utf-8"))
        resumen = {"dataset_count": mapa["totals"]["dataset_count"]}
        self._resumen = resumen
        return FlowResult(success=True, outputs=[self.produces[0].path(ctx)])

    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
        path = self.produces[0].path(ctx)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._resumen), encoding="utf-8")


def test_run_end_to_end_sobre_cliente_real_produce_mapa_identico_al_esperado_fijo(
    tmp_path: Path,
) -> None:
    """Onboarding().run(ctx) de punta a punta sobre un ClientContext de un
    cliente real (create_client, CONFORME): el map_client_data.json escrito
    coincide EXACTAMENTE (contenido semantico completo) con el esperado fijo
    derivado a mano del contrato de datos de spec.md (DS-ONB-2/DS-ONB-4), y
    el FlowResult apunta a la ruta real resuelta por ClientContext."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)
    _escribir_contrato(ctx, _contrato_valido())

    result = Onboarding().run(ctx)

    ruta_esperada = ctx.outputs_dir / "020_onboarding" / "map_client_data.json"
    assert isinstance(result, FlowResult)
    assert result.success is True
    assert result.outputs == [ruta_esperada]
    assert ruta_esperada.is_file()

    mapa_producido = json.loads(ruta_esperada.read_text(encoding="utf-8"))
    assert mapa_producido == _mapa_esperado()


def test_run_exitoso_no_toca_bronze_silver_gold_del_cliente_real(
    tmp_path: Path,
) -> None:
    """Invariante de capas (CA-12) verificada sobre el arbol REAL creado por
    create_client: tras un run(ctx) exitoso, bronze/silver/gold siguen
    vacios (Onboarding solo escribe metadatos, nunca datos)."""
    clients_root = tmp_path / "clients"
    create_client("Wayne", clients_root)
    ctx = ClientContext("Wayne", clients_root)
    _escribir_contrato(ctx, _contrato_valido())

    Onboarding().run(ctx)

    for layer_dir in (ctx.bronze_dir, ctx.silver_dir, ctx.gold_dir):
        assert layer_dir.is_dir()
        assert list(layer_dir.iterdir()) == []


def test_run_falla_temprano_con_flow_contract_error_si_falta_contract_data_en_cliente_real(
    tmp_path: Path,
) -> None:
    """Camino de fallo de contrato integrado (CA-20): sobre un cliente real
    sin contract_data.json, run(ctx) lanza FlowContractError (no una
    excepcion cruda como FileNotFoundError/KeyError) y no deja
    map_client_data.json en disco."""
    clients_root = tmp_path / "clients"
    create_client("Globex", clients_root)
    ctx = ClientContext("Globex", clients_root)

    with pytest.raises(FlowContractError, match="contract_data"):
        Onboarding().run(ctx)

    ruta_output = ctx.outputs_dir / "020_onboarding" / "map_client_data.json"
    assert not ruta_output.exists()


def test_run_produce_artefacto_consumible_sin_fallar_por_un_flujo_vecino_real(
    tmp_path: Path,
) -> None:
    """Interaccion con flujos vecinos (SS8, D-014): el map_client_data.json
    que Onboarding produce es exactamente el artefacto que un flujo
    downstream declara como require, y ese flujo vecino lo consume sin
    fallar sobre el mismo ClientContext real."""
    clients_root = tmp_path / "clients"
    create_client("Initech", clients_root)
    ctx = ClientContext("Initech", clients_root)
    _escribir_contrato(ctx, _contrato_valido())

    resultado_onboarding = Onboarding().run(ctx)
    assert resultado_onboarding.success is True

    resultado_vecino = _FlowVecino().run(ctx)

    assert resultado_vecino.success is True
    ruta_resumen = ctx.outputs_dir / "030_vecino" / "resumen.json"
    assert ruta_resumen.is_file()
    assert json.loads(ruta_resumen.read_text(encoding="utf-8")) == {
        "dataset_count": 2
    }


def test_aislamiento_multi_tenant_entre_dos_clientes_reales_bajo_el_mismo_clients_root(
    tmp_path: Path,
) -> None:
    """Aislamiento multi-tenant (SS7): dos clientes reales distintos bajo el
    mismo clients_root, cada uno con su propio contract_data.json, producen
    map_client_data.json independientes bajo clients/<cliente>/ sin fuga de
    datos entre ellos (distinto client.code, distinto totals.file_count)."""
    clients_root = tmp_path / "clients"

    create_client("ClienteA", clients_root)
    ctx_a = ClientContext("ClienteA", clients_root)
    _escribir_contrato(ctx_a, _contrato_valido())

    contrato_b = _contrato_valido()
    contrato_b["client"] = {"code": "XYZ", "name": "Cliente XYZ Ltda.", "sector": "moda"}
    del contrato_b["historical_data"]["datasets"][1]  # solo el dataset ventas
    create_client("ClienteB", clients_root)
    ctx_b = ClientContext("ClienteB", clients_root)
    _escribir_contrato(ctx_b, contrato_b)

    resultado_a = Onboarding().run(ctx_a)
    resultado_b = Onboarding().run(ctx_b)

    assert resultado_a.success is True
    assert resultado_b.success is True

    mapa_a = json.loads(
        (ctx_a.outputs_dir / "020_onboarding" / "map_client_data.json").read_text(
            encoding="utf-8"
        )
    )
    mapa_b = json.loads(
        (ctx_b.outputs_dir / "020_onboarding" / "map_client_data.json").read_text(
            encoding="utf-8"
        )
    )

    assert mapa_a["client"]["code"] == "ABC"
    assert mapa_a["totals"] == {"dataset_count": 2, "file_count": 3}
    assert mapa_b["client"]["code"] == "XYZ"
    assert mapa_b["totals"] == {"dataset_count": 1, "file_count": 1}
    assert ctx_a.root != ctx_b.root
