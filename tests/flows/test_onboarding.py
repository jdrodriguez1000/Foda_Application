"""Tests unitarios de Onboarding (feature onboarding, banda tracer_bullet).

Fuente: 600_features/onboarding/tracer_bullet/spec.md (CA-xx) y plan.md
(casos TDD, TSK-10.. TSK-32). Bucle TDD: un test por caso, ejecutado en orden
(state.json -> stages.tdd.cases).
"""

import json
from pathlib import Path

import pytest

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowContractError, FlowResult
from foda.core.scaffold import create_client
from foda.flows.f020_onboarding.onboarding import Onboarding


def _contrato_valido() -> dict:
    """Fixture valido (TSK-10): ventas + inventario, 4+4 niveles, tal como
    figura en el Sec Contratos de Datos de la spec (entrada esperada)."""
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
                        {
                            "name": "fecha",
                            "type": "date",
                            "required": True,
                            "maps_to": "time",
                        },
                        {
                            "name": "sede",
                            "type": "string",
                            "required": True,
                            "maps_to": "geography.sede",
                        },
                        {
                            "name": "clase",
                            "type": "string",
                            "required": True,
                            "maps_to": "product.clase",
                        },
                        {
                            "name": "cantidad",
                            "type": "integer",
                            "required": True,
                            "maps_to": "measure",
                        },
                        {
                            "name": "precio_unitario",
                            "type": "number",
                            "required": False,
                            "maps_to": None,
                        },
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
                        {
                            "name": "fecha",
                            "type": "date",
                            "required": True,
                            "maps_to": "time",
                        },
                        {
                            "name": "sede",
                            "type": "string",
                            "required": True,
                            "maps_to": "geography.sede",
                        },
                        {
                            "name": "clase",
                            "type": "string",
                            "required": True,
                            "maps_to": "product.clase",
                        },
                        {
                            "name": "stock",
                            "type": "integer",
                            "required": True,
                            "maps_to": "measure",
                        },
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


def test_run_sobre_fixture_valido_escribe_map_client_data_y_devuelve_flow_result(
    tmp_path: Path,
) -> None:
    """Caso 1 (CA-01): run(ctx) sobre el fixture valido escribe
    map_client_data.json en ctx.outputs_dir / "020_onboarding/map_client_data.json"
    y devuelve FlowResult(success=True, outputs=[esa ruta]); el archivo existe
    en disco."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
    )

    flow = Onboarding()
    result = flow.run(ctx)

    ruta_esperada = ctx.outputs_dir / "020_onboarding/map_client_data.json"

    assert isinstance(result, FlowResult)
    assert result.success is True
    assert result.outputs == [ruta_esperada]
    assert ruta_esperada.exists()


def test_onboarding_hereda_flow_declara_contratos_y_completa_las_4_fases(
    tmp_path: Path,
) -> None:
    """Caso 2 (CA-11): Onboarding hereda Flow, declara requires/produces con
    los Artifact esperados y completa las 4 fases del template method sin
    sobreescribir run.

    Nota TDD (D-037, plan.md Sec.5): este caso nace en verde directo. El
    esqueleto de Onboarding construido para el caso 1 (CA-01, TSK-02) ya
    hereda de Flow, declara requires/produces con los Artifact exactos del
    contrato y no sobreescribe run(), por lo que las 4 fases del template
    method (load_inputs -> validate -> execute -> write_outputs) ya se
    ejecutan en el orden correcto. No hubo ciclo rojo->verde para este caso:
    se confirmo empiricamente (tdd_tester) que el test pasa sin cambios de
    produccion, y el humano aprobo tratarlo como verde directo, sin pasar
    por tdd_coder/tdd_refactor."""
    assert issubclass(Onboarding, Flow)
    assert Onboarding.requires == [
        Artifact(
            name="contract_data",
            base="outputs",
            relative="010_discovery/contract_data.json",
        )
    ]
    assert Onboarding.produces == [
        Artifact(
            name="map_client_data",
            base="outputs",
            relative="020_onboarding/map_client_data.json",
        )
    ]
    assert Onboarding.run is Flow.run

    calls: list[str] = []

    class Instrumented(Onboarding):
        def load_inputs(self, ctx: ClientContext) -> None:
            calls.append("load_inputs")
            super().load_inputs(ctx)

        def validate(self, ctx: ClientContext) -> None:
            calls.append("validate")
            super().validate(ctx)

        def execute(self, ctx: ClientContext) -> FlowResult:
            calls.append("execute")
            return super().execute(ctx)

        def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
            calls.append("write_outputs")
            super().write_outputs(ctx, result)

    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
    )

    Instrumented().run(ctx)

    assert calls == ["load_inputs", "validate", "execute", "write_outputs"]


def test_hierarchies_product_levels_y_depth(tmp_path: Path) -> None:
    """Caso 3 (CA-02): en el mapa, hierarchies.product.levels ==
    ["familia","categoria","subcategoria","clase"] (orden declarado tal como
    figura en product_hierarchy.levels del contrato) y
    hierarchies.product.depth == 4 (DS-ONB-2, esquema de map_client_data.json,
    Sec. Salida de la spec)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
    )

    Onboarding().run(ctx)

    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa = json.loads(ruta_salida.read_text(encoding="utf-8"))

    product = mapa.get("hierarchies", {}).get("product", {})
    assert product.get("levels") == ["familia", "categoria", "subcategoria", "clase"]
    assert product.get("depth") == 4


def test_hierarchies_geography_levels_y_depth(tmp_path: Path) -> None:
    """Caso 4 (CA-03): en el mapa, hierarchies.geography.levels ==
    ["region","pais","ciudad","sede"] (orden declarado tal como figura en
    geography.levels del contrato) y hierarchies.geography.depth == 4
    (DS-ONB-2, esquema de map_client_data.json, Sec. Salida de la spec)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
    )

    Onboarding().run(ctx)

    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa = json.loads(ruta_salida.read_text(encoding="utf-8"))

    geography = mapa.get("hierarchies", {}).get("geography", {})
    assert geography.get("levels") == ["region", "pais", "ciudad", "sede"]
    assert geography.get("depth") == 4


def test_hierarchies_unique_values_y_unique_counts_por_nivel(tmp_path: Path) -> None:
    """Caso 5 (CA-04, DS-ONB-3): para cada nivel de product y geography,
    unique_values reporta los valores distintos observados en members en
    orden alfabetico ascendente y unique_counts el conteo correspondiente.
    Con el fixture: product.unique_values.familia == ["Bebidas","Snacks"]
    (unique_counts.familia == 2) y geography.unique_values.ciudad ==
    ["Bogota","Medellin"] (unique_counts.ciudad == 2)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
    )

    Onboarding().run(ctx)

    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa = json.loads(ruta_salida.read_text(encoding="utf-8"))

    product = mapa.get("hierarchies", {}).get("product", {})
    geography = mapa.get("hierarchies", {}).get("geography", {})

    assert product.get("unique_values", {}).get("familia") == ["Bebidas", "Snacks"]
    assert product.get("unique_counts", {}).get("familia") == 2
    assert geography.get("unique_values", {}).get("ciudad") == ["Bogota", "Medellin"]
    assert geography.get("unique_counts", {}).get("ciudad") == 2


def test_datasets_kind_source_medium_periodicity_en_orden_de_contrato(
    tmp_path: Path,
) -> None:
    """Caso 6 (CA-06): el mapa lista los 2 datasets del fixture con su
    kind/source_medium/periodicity correctos y en el orden en que aparecen
    en el contrato (ventas, luego inventario); DS-ONB-2 (Sec. Salida de la
    spec)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
    )

    Onboarding().run(ctx)

    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa = json.loads(ruta_salida.read_text(encoding="utf-8"))

    datasets = mapa.get("datasets", [])
    resumen = [
        {
            "kind": ds.get("kind"),
            "source_medium": ds.get("source_medium"),
            "periodicity": ds.get("periodicity"),
        }
        for ds in datasets
    ]
    assert resumen == [
        {"kind": "ventas", "source_medium": "csv", "periodicity": "mensual"},
        {"kind": "inventario", "source_medium": "csv", "periodicity": "mensual"},
    ]


def test_datasets_file_count_y_files_name_period_start_period_end(
    tmp_path: Path,
) -> None:
    """Caso 7 (CA-07): el mapa refleja file_count == 1 para ventas y
    file_count == 2 para inventario, y cada files[*] del dataset expone
    name/period_start/period_end tal como figuran en el contrato, incluido
    el archivo multi-anio de ventas (2023-01-01 -> 2025-12-31); DS-ONB-2
    (Sec. Salida de la spec)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
    )

    Onboarding().run(ctx)

    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa = json.loads(ruta_salida.read_text(encoding="utf-8"))

    datasets = mapa.get("datasets", [])
    ventas = datasets[0]
    inventario = datasets[1]

    assert ventas.get("file_count") == 1
    assert ventas.get("files") == [
        {
            "name": "ventas_2023_2025.csv",
            "period_start": "2023-01-01",
            "period_end": "2025-12-31",
        }
    ]

    assert inventario.get("file_count") == 2
    assert inventario.get("files") == [
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
    ]


def test_datasets_fields_name_type_required_maps_to(tmp_path: Path) -> None:
    """Caso 8 (CA-08): cada dataset expone fields con name/type/required/
    maps_to por columna, en el orden en que figuran en el contrato, incluido
    precio_unitario (dataset ventas) con required=False y maps_to=None
    (DS-ONB-2, Sec. Salida de la spec)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
    )

    Onboarding().run(ctx)

    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa = json.loads(ruta_salida.read_text(encoding="utf-8"))

    datasets = mapa.get("datasets", [])
    ventas = datasets[0]
    inventario = datasets[1]

    assert ventas.get("fields") == [
        {"name": "fecha", "type": "date", "required": True, "maps_to": "time"},
        {
            "name": "sede",
            "type": "string",
            "required": True,
            "maps_to": "geography.sede",
        },
        {
            "name": "clase",
            "type": "string",
            "required": True,
            "maps_to": "product.clase",
        },
        {
            "name": "cantidad",
            "type": "integer",
            "required": True,
            "maps_to": "measure",
        },
        {
            "name": "precio_unitario",
            "type": "number",
            "required": False,
            "maps_to": None,
        },
    ]

    assert inventario.get("fields") == [
        {"name": "fecha", "type": "date", "required": True, "maps_to": "time"},
        {
            "name": "sede",
            "type": "string",
            "required": True,
            "maps_to": "geography.sede",
        },
        {
            "name": "clase",
            "type": "string",
            "required": True,
            "maps_to": "product.clase",
        },
        {
            "name": "stock",
            "type": "integer",
            "required": True,
            "maps_to": "measure",
        },
    ]


def test_maps_to_proviene_del_contrato_no_del_nombre_de_columna(
    tmp_path: Path,
) -> None:
    """Caso 9 (CA-09): maps_to se toma del contrato, no se infiere del
    nombre de columna. Fixture deliberadamente disenado para romper
    cualquier coincidencia nombre<->maps_to (a diferencia del fixture
    canonico del caso 8, donde el nombre de columna y su maps_to coinciden
    semanticamente): una columna cuyo nombre NO sugiere ninguna jerarquia
    (articulo_id) mapea a "product.clase", y una columna cuyo nombre SI
    sugiere "product.clase" (clase) mapea a null en el contrato; simetrico
    para geography.sede (punto_venta / sede). Si la implementacion
    infiriera maps_to del nombre de la columna en lugar de leerlo del
    contrato, este test fallaria.

    Nota TDD (D-037, plan.md Sec.5, precedente caso 2/CA-11): este caso
    nace en verde directo. _dataset() (cerrado en el caso 8, CA-08,
    TSK-18/TSK-04, con refactor incluido) ya hace un pass-through puro de
    field.get("maps_to") sin ninguna logica de inferencia por nombre, por
    lo que ningun fixture puede producir un rojo legitimo para CA-09: no
    hay funcionalidad pendiente que codificar. Se confirmo empiricamente
    (tdd_tester) que este test pasa sin cambios de produccion, y el humano
    aprobo tratarlo como verde directo, sin pasar por
    tdd_coder/tdd_refactor."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato = _contrato_valido()
    contrato["historical_data"]["datasets"][0]["fields"] = [
        {
            "name": "articulo_id",
            "type": "string",
            "required": True,
            "maps_to": "product.clase",
        },
        {
            "name": "clase",
            "type": "string",
            "required": True,
            "maps_to": None,
        },
        {
            "name": "punto_venta",
            "type": "string",
            "required": True,
            "maps_to": "geography.sede",
        },
        {
            "name": "sede",
            "type": "string",
            "required": True,
            "maps_to": None,
        },
    ]

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(contrato, ensure_ascii=False), encoding="utf-8"
    )

    Onboarding().run(ctx)

    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa = json.loads(ruta_salida.read_text(encoding="utf-8"))

    ventas = mapa.get("datasets", [])[0]
    assert ventas.get("fields") == [
        {
            "name": "articulo_id",
            "type": "string",
            "required": True,
            "maps_to": "product.clase",
        },
        {"name": "clase", "type": "string", "required": True, "maps_to": None},
        {
            "name": "punto_venta",
            "type": "string",
            "required": True,
            "maps_to": "geography.sede",
        },
        {"name": "sede", "type": "string", "required": True, "maps_to": None},
    ]


def test_hierarchies_product_levels_de_3_niveles_depth_igual_a_3(
    tmp_path: Path,
) -> None:
    """Caso 11 (CA-05, TSK-21/TSK-03): dado un contrato cuya
    product_hierarchy.levels tiene 3 niveles (no 4) con miembros coherentes
    (exactamente esas 3 claves), el mapa refleja hierarchies.product.levels
    en el orden declarado y hierarchies.product.depth == 3, sin asumir 4
    niveles.

    Nota TDD (D-037, plan.md Sec.7, precedente casos 2/CA-11 y 9/CA-09): este
    caso nace en verde directo. _hierarchy() (cerrado en el caso 4, CA-03)
    ya deriva depth = len(levels) e itera unique_values/unique_counts sobre
    la lista `levels` recibida, sin asumir ni hardcodear 4 niveles ni claves
    fijas (familia/categoria/subcategoria/clase); plan.md Sec.7 anticipa
    explicitamente que esta genericidad cubre las variantes de 3 y 5
    niveles (CA-05/CA-05b). Se confirmo empiricamente (tdd_tester) que este
    test pasa sin cambios de produccion, y el humano aprobo tratarlo como
    verde directo, sin pasar por tdd_coder/tdd_refactor."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato = _contrato_valido()
    contrato["product_hierarchy"] = {
        "levels": ["categoria", "subcategoria", "clase"],
        "members": [
            {
                "categoria": "Aguas",
                "subcategoria": "Sin gas",
                "clase": "Agua 600ml",
            },
            {
                "categoria": "Gaseosas",
                "subcategoria": "Cola",
                "clase": "Cola 1.5L",
            },
            {
                "categoria": "Papas",
                "subcategoria": "Fritas",
                "clase": "Papas 45g",
            },
        ],
    }

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(contrato, ensure_ascii=False), encoding="utf-8"
    )

    Onboarding().run(ctx)

    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa = json.loads(ruta_salida.read_text(encoding="utf-8"))

    product = mapa.get("hierarchies", {}).get("product", {})
    assert product.get("levels") == ["categoria", "subcategoria", "clase"]
    assert product.get("depth") == 3


def test_hierarchies_product_levels_de_5_niveles_depth_igual_a_5_incl_sku(
    tmp_path: Path,
) -> None:
    """Caso 12 (CA-05b, TSK-22/TSK-03): dado un contrato cuya
    product_hierarchy.levels tiene 5 niveles (incl. sku, ["familia",
    "categoria","subcategoria","clase","sku"]) con miembros coherentes
    (exactamente esas 5 claves), el mapa refleja hierarchies.product.levels
    en el orden declarado, hierarchies.product.depth == 5, y
    unique_values/unique_counts calculados tambien para el 5.o nivel (sku),
    sin topar la profundidad en 4 ni perder el nivel adicional.

    Nota TDD (D-037, plan.md Sec.7, precedente casos 2/CA-11, 9/CA-09 y
    11/CA-05): este caso nace en verde directo. _hierarchy() (cerrado en el
    caso 4, CA-03) ya deriva depth = len(levels) e itera unique_values/
    unique_counts sobre la lista `levels` recibida completa, sin asumir ni
    hardcodear 4 niveles ni claves fijas; plan.md Sec.7 anticipa
    explicitamente que esta genericidad cubre tanto la variante de 3
    niveles (CA-05, caso 11) como la de 5 niveles (CA-05b, este caso). Se
    confirmo empiricamente (tdd_tester) que este test pasa sin cambios de
    produccion, y el humano aprobo tratarlo como verde directo, sin pasar
    por tdd_coder/tdd_refactor."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato = _contrato_valido()
    contrato["product_hierarchy"] = {
        "levels": ["familia", "categoria", "subcategoria", "clase", "sku"],
        "members": [
            {
                "familia": "Bebidas",
                "categoria": "Aguas",
                "subcategoria": "Sin gas",
                "clase": "Agua 600ml",
                "sku": "SKU-001",
            },
            {
                "familia": "Bebidas",
                "categoria": "Gaseosas",
                "subcategoria": "Cola",
                "clase": "Cola 1.5L",
                "sku": "SKU-002",
            },
            {
                "familia": "Snacks",
                "categoria": "Papas",
                "subcategoria": "Fritas",
                "clase": "Papas 45g",
                "sku": "SKU-003",
            },
        ],
    }

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(contrato, ensure_ascii=False), encoding="utf-8"
    )

    Onboarding().run(ctx)

    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa = json.loads(ruta_salida.read_text(encoding="utf-8"))

    product = mapa.get("hierarchies", {}).get("product", {})
    assert product.get("levels") == [
        "familia",
        "categoria",
        "subcategoria",
        "clase",
        "sku",
    ]
    assert product.get("depth") == 5
    assert product.get("unique_values", {}).get("sku") == [
        "SKU-001",
        "SKU-002",
        "SKU-003",
    ]
    assert product.get("unique_counts", {}).get("sku") == 3


def test_totals_dataset_count_y_file_count(tmp_path: Path) -> None:
    """Caso 10 (CA-10): el mapa expone totals.dataset_count == 2 (ventas +
    inventario) y totals.file_count == 3 (1 archivo de ventas + 2 archivos
    de inventario), es decir la suma de file_count de cada dataset
    (DS-ONB-2, Sec. Salida de la spec; plan.md Sec.1 'totals')."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
    )

    Onboarding().run(ctx)

    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa = json.loads(ruta_salida.read_text(encoding="utf-8"))

    totals = mapa.get("totals", {})
    assert totals.get("dataset_count") == 2
    assert totals.get("file_count") == 3


def test_dos_run_con_mismo_input_producen_map_client_data_identico_byte_a_byte(
    tmp_path: Path,
) -> None:
    """Caso 13 (CA-13, DS-ONB-4): dos ejecuciones de run(ctx) con el mismo
    contract_data.json producen un map_client_data.json identico byte a
    byte. Se ejecuta run() dos veces (instancias frescas de Onboarding,
    sobre el mismo ctx/contrato) y se comparan los bytes crudos
    (read_bytes()) del archivo de salida entre ambas corridas.

    Nota TDD (D-037, plan.md Sec.5, precedente casos 2/CA-11, 9/CA-09,
    11/CA-05 y 12/CA-05b): este caso nace en verde directo. write_outputs()
    (cerrado desde el caso 1, CA-01, TSK-02) ya serializa con
    json.dumps(self._mapa, ensure_ascii=False, indent=2, sort_keys=True) +
    "\n" -- exactamente el criterio de determinismo exigido por DS-ONB-4
    (TSK-06), aunque plan.md aun listaba TSK-06 como no_implementada:
    sort_keys=True hace irrelevante el orden de insercion de las claves de
    objeto, y unique_values ya usa sorted() (caso 5, CA-04), por lo que no
    queda ninguna fuente real de no-determinismo entre corridas con el
    mismo input. Se confirmo empiricamente (tdd_tester) que este test pasa
    sin cambios de produccion, y el humano aprobo tratarlo como verde
    directo, sin pasar por tdd_coder/tdd_refactor."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
    )

    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"

    Onboarding().run(ctx)
    primera_corrida = ruta_salida.read_bytes()

    ruta_salida.unlink()

    Onboarding().run(ctx)
    segunda_corrida = ruta_salida.read_bytes()

    assert primera_corrida == segunda_corrida


def test_run_exitoso_no_deja_nada_bajo_bronze_silver_gold(tmp_path: Path) -> None:
    """Caso 14 (CA-12): tras un run(ctx) exitoso, ctx.bronze_dir/silver_dir/
    gold_dir no contienen ningun archivo ni carpeta; el unico artefacto
    escrito por Onboarding es map_client_data.json (DS-ONB-5, plan.md Sec.
    'No toca bronze/silver/gold no datos reales', feature CA-3).

    Nota TDD (D-037, precedente casos 2/CA-11, 9/CA-09, 11/CA-05, 12/CA-05b
    y 13/CA-13): este caso nace en verde directo. `Onboarding.load_inputs`/
    `execute`/`write_outputs` (cerrados en casos previos) solo leen
    contract_data.json y escriben map_client_data.json bajo
    020_onboarding/; el codigo nunca referencia ctx.bronze_dir/silver_dir/
    gold_dir. create_client() (core CONFORME, no re-testeado aqui) ya crea
    esas carpetas vacias en el scaffold antes de que Onboarding corra, y
    ningun hook de Onboarding escribe en ellas. Se confirmo empiricamente
    (tdd_tester) que este test pasa sin cambios de produccion, y el humano
    aprobo tratarlo como verde directo, sin pasar por
    tdd_coder/tdd_refactor."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
    )

    Onboarding().run(ctx)

    assert list(ctx.bronze_dir.iterdir()) == []
    assert list(ctx.silver_dir.iterdir()) == []
    assert list(ctx.gold_dir.iterdir()) == []


def test_contract_data_ausente_lanza_flow_contract_error_y_no_crea_output(
    tmp_path: Path,
) -> None:
    """Caso 15 (CA-20): si contract_data.json no existe en disco, run(ctx)
    lanza FlowContractError en validate() (existencia base, DS-ONB-5 fase
    2a) antes de derivar nada, y no se crea map_client_data.json.

    Nota TDD (D-037, precedente casos 2/CA-11, 9/CA-09, 11/CA-05, 12/CA-05b,
    13/CA-13 y 14/CA-12): este caso nace en verde directo. Onboarding.validate()
    (cerrado desde el caso 1, CA-01, TSK-02) delega integramente en
    super().validate(ctx) (Flow.validate, core CONFORME, no re-testeado
    aqui), que ya comprueba la existencia fisica de cada Artifact de
    requires y lanza FlowContractError si falta antes de que run() llame a
    execute()/write_outputs(); Onboarding no necesita logica propia para
    este caso. Se confirmo empiricamente (tdd_tester) que este test pasa
    sin cambios de produccion, y el humano pre-autorizo cerrar verdes
    directos sin aprobacion individual, por lo que se cierra directamente
    (sin pasar por tdd_coder/tdd_refactor)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    # No se escribe contract_data.json: el require queda ausente en disco.
    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"

    with pytest.raises(FlowContractError):
        Onboarding().run(ctx)

    assert not ruta_salida.exists()


def test_product_levels_vacio_lanza_flow_contract_error_y_no_crea_output(
    tmp_path: Path,
) -> None:
    """Caso 16 (CA-14, TSK-26/TSK-07): si product_hierarchy.levels == []
    (jerarquia declarada sin niveles), run(ctx) lanza FlowContractError en
    validate() -- validacion de coherencia de contenido, TSK-07 -- antes de
    llegar a execute()/write_outputs(), y no se crea map_client_data.json.

    Hoy Onboarding.validate() (caso 1, CA-01, TSK-02) delega integramente en
    super().validate(ctx) (Flow.validate, existencia base del require) y no
    valida el contenido del contrato ya cargado; con levels == [] no se
    lanza ningun error y run(ctx) completa exitosamente, escribiendo
    map_client_data.json. Este test debe fallar hoy (rojo genuino) porque
    no se lanza FlowContractError: la validacion de contenido (TSK-07)
    todavia no existe."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato = _contrato_valido()
    contrato["product_hierarchy"]["levels"] = []

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(contrato, ensure_ascii=False), encoding="utf-8"
    )

    ruta_salida = ctx.outputs_dir / "020_onboarding/map_client_data.json"

    with pytest.raises(FlowContractError):
        Onboarding().run(ctx)

    assert not ruta_salida.exists()
