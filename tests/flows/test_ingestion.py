"""Tests unitarios de Ingestion (feature ingestion, banda tracer_bullet).

Fuente: 600_features/ingestion/tracer_bullet/spec.md (CA-xx) y plan.md
(casos TDD, TSK-14..TSK-36). Bucle TDD: un test por caso, ejecutado en orden
(state.json -> stages.tdd.cases). Este archivo arranca con el caso 1
(CA-14): fixture minimo (un unico dataset "ventas"/"ventas.csv" coma,
DS-ING-7/DS-ING-8) con contract_data.json (fuente de los archivos esperados)
y map_client_data.json (fuente de las columnas esperadas) coherentes entre
si, mas el archivo crudo bajo el landing.
"""

import json
from pathlib import Path

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow
from foda.core.scaffold import create_client
from foda.flows.f030_ingestion.ingestion import Ingestion

_VENTAS_HEADER = "fecha,sede,clase,cantidad,precio_unitario"
_VENTAS_ROWS = [
    "2024-01-01,Sede Centro,Agua 600ml,10,1200",
    "2024-01-02,Sede Norte,Cola 1.5L,5,2500",
    "2024-01-03,Sede Centro,Papas 45g,20,900",
]


def _contract_data_minimo() -> dict:
    """DS-ING-8: fuente de los archivos esperados. Un unico dataset "ventas"
    con un unico archivo "ventas.csv" (caso 1, subconjunto minimo del fixture
    DS-ING-7)."""
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
                }
            ]
        },
    }


def _map_client_data_minimo() -> dict:
    """DS-ING-8: fuente de las columnas esperadas por dataset (fields[] con
    name/required), emparejadas por kind con el dataset homologo del
    contrato. Coherente con _contract_data_minimo (mismo kind "ventas")."""
    return {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "datasets": [
            {
                "kind": "ventas",
                "fields": [
                    {"name": "fecha", "required": True},
                    {"name": "sede", "required": True},
                    {"name": "clase", "required": True},
                    {"name": "cantidad", "required": True},
                    {"name": "precio_unitario", "required": False},
                ],
            }
        ],
    }


def _build_ctx_fixture_minimo(tmp_path: Path) -> ClientContext:
    """DS-ING-7 (subconjunto minimo, casos 1-3): construye un ClientContext
    bajo tmp_path con contract_data.json + map_client_data.json coherentes
    entre si (dataset "ventas" unico) bajo ctx.outputs_dir, y el archivo
    crudo ventas.csv (separador coma) bajo ctx.inputs_dir/"030_ingestion"."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(_contract_data_minimo(), ensure_ascii=False), encoding="utf-8"
    )

    mapa_path = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa_path.parent.mkdir(parents=True)
    mapa_path.write_text(
        json.dumps(_map_client_data_minimo(), ensure_ascii=False), encoding="utf-8"
    )

    landing_dir = ctx.inputs_dir / "030_ingestion"
    landing_dir.mkdir(parents=True)
    (landing_dir / "ventas.csv").write_text(
        "\n".join([_VENTAS_HEADER, *_VENTAS_ROWS]) + "\n", encoding="utf-8"
    )

    return ctx


def test_run_sobre_fixture_minimo_escribe_ingestion_report_y_lo_incluye_en_outputs(
    tmp_path: Path,
) -> None:
    """Caso 1 (CA-14): run(ctx) sobre el fixture minimo (dataset ventas /
    ventas.csv coma) escribe ingestion_report.json en
    ctx.outputs_dir / "030_ingestion/ingestion_report.json" y lo incluye en
    FlowResult.outputs; el archivo existe en disco."""
    ctx = _build_ctx_fixture_minimo(tmp_path)

    flow = Ingestion()
    result = flow.run(ctx)

    ruta_esperada = ctx.outputs_dir / "030_ingestion/ingestion_report.json"

    assert ruta_esperada.exists()
    assert ruta_esperada in result.outputs


def test_ingestion_hereda_flow_requires_produces_y_4_fases_sin_sobreescribir_run() -> None:
    """Caso 2 (CA-20): Ingestion hereda de Flow, declara requires/produces con
    los Artifact exactos de la spec y completa las 4 fases del template
    method (load_inputs, validate, execute, write_outputs) sin sobreescribir
    run. El caso 1 ya cubre que run() (heredado) produce el reporte
    end-to-end; este caso verifica la estructura declarativa de la clase que
    ese caso no comprueba: que Ingestion sobreescribe explicitamente las 4
    fases (incluida validate, aunque delegue en super().validate) y no
    sobreescribe run."""
    assert issubclass(Ingestion, Flow)

    assert Ingestion.requires == [
        Artifact(
            name="contract_data",
            base="outputs",
            relative="010_discovery/contract_data.json",
        ),
        Artifact(
            name="map_client_data",
            base="outputs",
            relative="020_onboarding/map_client_data.json",
        ),
    ]
    assert Ingestion.produces == [
        Artifact(
            name="ingestion_report",
            base="outputs",
            relative="030_ingestion/ingestion_report.json",
        ),
    ]

    # No sobreescribe run(): usa el template method heredado de Flow.
    assert "run" not in vars(Ingestion)
    assert Ingestion.run is Flow.run

    # Completa las 4 fases del template method (definidas explicitamente en
    # la propia clase, no solo heredadas en silencio).
    for hook in ("load_inputs", "validate", "execute", "write_outputs"):
        assert hook in vars(Ingestion), (
            f"Ingestion debe sobreescribir explicitamente el hook {hook!r} "
            "(spec Interfaces / Firmas Publicas, CA-20)."
        )


def test_reporte_registra_rows_columns_y_separator_correctos_para_ventas_csv_coma(
    tmp_path: Path,
) -> None:
    """Caso 3 (CA-01): para el archivo delimitado por coma (ventas.csv) el
    reporte registra el numero correcto de rows (filas de datos, sin
    cabecera: len(_VENTAS_ROWS) == 3) y columns (columnas de la cabecera:
    len(_VENTAS_HEADER.split(",")) == 5), y separator == ",". Reutiliza el
    fixture minimo (DS-ING-7, casos 1-3, un unico dataset "ventas")."""
    ctx = _build_ctx_fixture_minimo(tmp_path)

    flow = Ingestion()
    result = flow.run(ctx)

    ruta_reporte = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    archivo = reporte["datasets"][0]["files"][0]
    assert archivo["name"] == "ventas.csv"
    assert archivo["rows"] == len(_VENTAS_ROWS)
    assert archivo["columns"] == len(_VENTAS_HEADER.split(","))
    assert archivo["separator"] == ","

    assert result.success is True
