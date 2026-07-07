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

import openpyxl

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


def _build_ctx(
    tmp_path: Path,
    contract_data: dict,
    map_client_data: dict,
    files: dict[str, str | bytes],
) -> ClientContext:
    """DS-ING-7/DS-ING-8: construye un ClientContext bajo tmp_path con
    contract_data.json + map_client_data.json bajo ctx.outputs_dir, y uno o
    mas archivos crudos (name -> contenido, texto delimitado o bytes
    binarios p. ej. .xlsx) bajo ctx.inputs_dir/"030_ingestion". Helper
    compartido por las fixtures de cada caso del bucle TDD (evita duplicar
    el andamiaje de directorios)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(
        json.dumps(contract_data, ensure_ascii=False), encoding="utf-8"
    )

    mapa_path = ctx.outputs_dir / "020_onboarding/map_client_data.json"
    mapa_path.parent.mkdir(parents=True)
    mapa_path.write_text(
        json.dumps(map_client_data, ensure_ascii=False), encoding="utf-8"
    )

    landing_dir = ctx.inputs_dir / "030_ingestion"
    landing_dir.mkdir(parents=True)
    for name, content in files.items():
        if isinstance(content, bytes):
            (landing_dir / name).write_bytes(content)
        else:
            (landing_dir / name).write_text(content, encoding="utf-8")

    return ctx


def _build_ctx_fixture_minimo(tmp_path: Path) -> ClientContext:
    """DS-ING-7 (subconjunto minimo, casos 1-3): ClientContext con
    contract_data.json + map_client_data.json coherentes entre si (dataset
    "ventas" unico) y el archivo crudo ventas.csv (separador coma)."""
    return _build_ctx(
        tmp_path,
        _contract_data_minimo(),
        _map_client_data_minimo(),
        {"ventas.csv": "\n".join([_VENTAS_HEADER, *_VENTAS_ROWS]) + "\n"},
    )


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


_INVENTARIO_HEADER = "fecha;sede;clase;stock"
_INVENTARIO_ROWS = [
    "2024-01-01;Sede Centro;Agua 600ml;120",
    "2024-01-02;Sede Norte;Cola 1.5L;80",
]


def _contract_data_inventario_2024() -> dict:
    """DS-ING-8: fuente de los archivos esperados. Un unico dataset
    "inventario" con un unico archivo "inventario_2024.txt" (caso 4,
    subconjunto DS-ING-7 aislado para el separador ';')."""
    return {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "historical_data": {
            "datasets": [
                {
                    "kind": "inventario",
                    "source_medium": "csv",
                    "periodicity": "mensual",
                    "files": [
                        {
                            "name": "inventario_2024.txt",
                            "period_start": "2023-01-01",
                            "period_end": "2025-12-31",
                        }
                    ],
                }
            ]
        },
    }


def _map_client_data_inventario_2024() -> dict:
    """DS-ING-8: fuente de las columnas esperadas del dataset "inventario"
    (fields[] con name/required), emparejadas por kind con el dataset
    homologo del contrato. Coherente con _contract_data_inventario_2024
    (mismo kind "inventario")."""
    return {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "datasets": [
            {
                "kind": "inventario",
                "fields": [
                    {"name": "fecha", "required": True},
                    {"name": "sede", "required": True},
                    {"name": "clase", "required": True},
                    {"name": "stock", "required": True},
                ],
            }
        ],
    }


def _build_ctx_fixture_inventario_2024(tmp_path: Path) -> ClientContext:
    """DS-ING-7 (subconjunto aislado, caso 4): ClientContext con
    contract_data.json + map_client_data.json coherentes entre si (dataset
    "inventario" unico) y el archivo crudo inventario_2024.txt (separador
    ';')."""
    return _build_ctx(
        tmp_path,
        _contract_data_inventario_2024(),
        _map_client_data_inventario_2024(),
        {"inventario_2024.txt": "\n".join([_INVENTARIO_HEADER, *_INVENTARIO_ROWS]) + "\n"},
    )


def test_reporte_registra_rows_columns_y_separator_correctos_para_inventario_2024_txt_punto_y_coma(
    tmp_path: Path,
) -> None:
    """Caso 4 (CA-02): para el archivo delimitado por punto y coma
    (inventario_2024.txt) el reporte registra el numero correcto de rows
    (filas de datos, sin cabecera: len(_INVENTARIO_ROWS) == 2) y columns
    (columnas de la cabecera: len(_INVENTARIO_HEADER.split(";")) == 4), y
    separator == ";". La extension no determina el separador (DS-ING-7):
    el archivo es .txt pero el contenido esta delimitado por ';'."""
    ctx = _build_ctx_fixture_inventario_2024(tmp_path)

    flow = Ingestion()
    result = flow.run(ctx)

    ruta_reporte = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    archivo = reporte["datasets"][0]["files"][0]
    assert archivo["name"] == "inventario_2024.txt"
    assert archivo["rows"] == len(_INVENTARIO_ROWS)
    assert archivo["columns"] == len(_INVENTARIO_HEADER.split(";"))
    assert archivo["separator"] == ";"

    assert result.success is True


_INVENTARIO_2025_HEADER = "fecha|sede|clase|stock"
_INVENTARIO_2025_ROWS = [
    "2025-01-01|Sede Centro|Agua 600ml|150",
    "2025-01-02|Sede Norte|Cola 1.5L|95",
]


def _contract_data_inventario_2025() -> dict:
    """DS-ING-8: fuente de los archivos esperados. Un unico dataset
    "inventario" con un unico archivo "inventario_2025.csv" (caso 5,
    subconjunto DS-ING-7 aislado para el separador '|')."""
    return {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "historical_data": {
            "datasets": [
                {
                    "kind": "inventario",
                    "source_medium": "csv",
                    "periodicity": "mensual",
                    "files": [
                        {
                            "name": "inventario_2025.csv",
                            "period_start": "2023-01-01",
                            "period_end": "2025-12-31",
                        }
                    ],
                }
            ]
        },
    }


def _map_client_data_inventario_2025() -> dict:
    """DS-ING-8: fuente de las columnas esperadas del dataset "inventario"
    (fields[] con name/required), emparejadas por kind con el dataset
    homologo del contrato. Coherente con _contract_data_inventario_2025
    (mismo kind "inventario")."""
    return {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "datasets": [
            {
                "kind": "inventario",
                "fields": [
                    {"name": "fecha", "required": True},
                    {"name": "sede", "required": True},
                    {"name": "clase", "required": True},
                    {"name": "stock", "required": True},
                ],
            }
        ],
    }


def _build_ctx_fixture_inventario_2025(tmp_path: Path) -> ClientContext:
    """DS-ING-7 (subconjunto aislado, caso 5): ClientContext con
    contract_data.json + map_client_data.json coherentes entre si (dataset
    "inventario" unico) y el archivo crudo inventario_2025.csv (separador
    '|')."""
    return _build_ctx(
        tmp_path,
        _contract_data_inventario_2025(),
        _map_client_data_inventario_2025(),
        {
            "inventario_2025.csv": "\n".join(
                [_INVENTARIO_2025_HEADER, *_INVENTARIO_2025_ROWS]
            )
            + "\n"
        },
    )


def test_reporte_registra_rows_columns_y_separator_correctos_para_inventario_2025_csv_barra_vertical(
    tmp_path: Path,
) -> None:
    """Caso 5 (CA-03): para el archivo delimitado por barra vertical
    (inventario_2025.csv) el reporte registra el numero correcto de rows
    (filas de datos, sin cabecera: len(_INVENTARIO_2025_ROWS) == 2) y columns
    (columnas de la cabecera: len(_INVENTARIO_2025_HEADER.split("|")) == 4),
    y separator == "|"."""
    ctx = _build_ctx_fixture_inventario_2025(tmp_path)

    flow = Ingestion()
    result = flow.run(ctx)

    ruta_reporte = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    archivo = reporte["datasets"][0]["files"][0]
    assert archivo["name"] == "inventario_2025.csv"
    assert archivo["rows"] == len(_INVENTARIO_2025_ROWS)
    assert archivo["columns"] == len(_INVENTARIO_2025_HEADER.split("|"))
    assert archivo["separator"] == "|"

    assert result.success is True


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


_PRECIOS_HEADER = ["clase", "precio", "moneda"]
_PRECIOS_ROWS = [
    ["Agua 600ml", 1200, "COP"],
    ["Cola 1.5L", 2500, "COP"],
    ["Papas 45g", 900, "COP"],
]


def _contract_data_precios() -> dict:
    """DS-ING-8: fuente de los archivos esperados. Un unico dataset
    "precios" con un unico archivo "precios.xlsx" (caso 6, subconjunto
    DS-ING-7 aislado para el lector .xlsx, source_medium "xlsx")."""
    return {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "historical_data": {
            "datasets": [
                {
                    "kind": "precios",
                    "source_medium": "xlsx",
                    "periodicity": "mensual",
                    "files": [
                        {
                            "name": "precios.xlsx",
                            "period_start": "2023-01-01",
                            "period_end": "2025-12-31",
                        }
                    ],
                }
            ]
        },
    }


def _map_client_data_precios() -> dict:
    """DS-ING-8: fuente de las columnas esperadas del dataset "precios"
    (fields[] con name/required), emparejadas por kind con el dataset
    homologo del contrato. Coherente con _contract_data_precios (mismo kind
    "precios")."""
    return {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "datasets": [
            {
                "kind": "precios",
                "fields": [
                    {"name": "clase", "required": True},
                    {"name": "precio", "required": True},
                    {"name": "moneda", "required": True},
                ],
            }
        ],
    }


def _precios_xlsx_bytes() -> bytes:
    """Fabrica en memoria un .xlsx (openpyxl) con cabecera _PRECIOS_HEADER
    y filas _PRECIOS_ROWS en la primera hoja (unica hoja del workbook), y
    devuelve su contenido binario para escribirlo bajo el landing."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(_PRECIOS_HEADER)
    for row in _PRECIOS_ROWS:
        sheet.append(row)

    import io

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _build_ctx_fixture_precios(tmp_path: Path) -> ClientContext:
    """DS-ING-7 (subconjunto aislado, caso 6): ClientContext con
    contract_data.json + map_client_data.json coherentes entre si (dataset
    "precios" unico) y el archivo crudo precios.xlsx (primera hoja,
    formato Excel, sin separador delimitado)."""
    return _build_ctx(
        tmp_path,
        _contract_data_precios(),
        _map_client_data_precios(),
        {"precios.xlsx": _precios_xlsx_bytes()},
    )


def test_reporte_registra_rows_columns_correctos_y_separator_null_para_precios_xlsx(
    tmp_path: Path,
) -> None:
    """Caso 6 (CA-04): para el archivo Excel (precios.xlsx, primera hoja)
    el reporte registra el numero correcto de rows (filas de datos, sin
    cabecera: len(_PRECIOS_ROWS) == 3) y columns (columnas de la cabecera:
    len(_PRECIOS_HEADER) == 3), y separator == null (None en Python)."""
    ctx = _build_ctx_fixture_precios(tmp_path)

    flow = Ingestion()
    result = flow.run(ctx)

    ruta_reporte = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    archivo = reporte["datasets"][0]["files"][0]
    assert archivo["name"] == "precios.xlsx"
    assert archivo["rows"] == len(_PRECIOS_ROWS)
    assert archivo["columns"] == len(_PRECIOS_HEADER)
    assert archivo["separator"] is None

    assert result.success is True
