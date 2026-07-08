"""Flujo 030: Ingestion (feature ingestion, banda tracer_bullet).

Fuente: 600_features/ingestion/tracer_bullet/spec.md (DS-ING-1..8) y plan.md
(TSK-01..TSK-36). Bucle TDD en curso: caso 1 (CA-14) en VERDE (tdd_coder).
Implementacion minima (NC-2): execute() lee, para cada dataset declarado en
contract_data.json, sus archivos desde el landing
(ctx.inputs_dir/"030_ingestion") asumiendo formato delimitado por coma
(unico separador ejercitado por el fixture de este caso), cuenta
rows/columns y arma el reporte en memoria (esquema DS-ING-2, sin summary
detallado de inconsistencias todavia); write_outputs() escribe
ingestion_report.json de forma determinista (DS-ING-6). Los detalles finos
-deteccion de separador ;/|, lectura de xlsx, validacion de columnas contra
el mapa, copia a bronze, missing_file/unexpected_file- llegan en casos
posteriores del bucle TDD (no se adelantan, NC-2).

Caso 2 (CA-20) en VERDE (tdd_coder): Ingestion sobreescribe explicitamente
validate(), delegando en super().validate(ctx) (misma comprobacion base de
existencia de requires que ya se ejecutaba de forma heredada e implicita);
esto completa las 4 fases del template method definidas en la propia clase
(load_inputs, validate, execute, write_outputs) sin sobreescribir run().
El comportamiento observable de run() no cambia (NC-2): validate() del base
ya se invocaba dentro del template method antes de este caso.

Caso 4 (CA-02) en VERDE (tdd_coder): _read_comma_delimited se reemplaza por
_detect_separator/_read_delimited (plan.md Sec.1, TSK-04), que detectan el
separador (','/';'/'|') a partir de la cabecera en vez de asumir coma
siempre; separator ya no esta hardcodeado en execute().

Caso 6 (CA-04) en VERDE (tdd_coder): se agrega _read_xlsx (openpyxl,
read_only+data_only, primera hoja del workbook, separator=None) y
_read_file, que enruta por extension (.xlsx -> _read_xlsx; .csv/.txt ->
_read_delimited, sin distinguir extension para delimitados, DS-ING-7).
execute() llama a _read_file en vez de _read_delimited directamente.

Caso 8 (CA-11) cerrado (tdd_refactor, TSK-07): _copy_bytes(src, dst) copia
byte a byte (sin re-serializar) cada archivo del landing a
ctx.bronze_dir/<name>; execute() registra el plan de copia en
self._bronze_copies (mismo patron de estado compartido execute()/
write_outputs() que self._contract/self._map) y write_outputs() crea
ctx.bronze_dir y ejecuta las copias. Refactor: solo se tipo anoto
_copy_bytes(src: Path, dst: Path) y self._bronze_copies como
list[tuple[Path, Path]]; el resto del diseño ya era minimo y coherente
(NC-2/NC-3), sin cambios de comportamiento.

Caso 11 (CA-06) cerrado (tdd_refactor, TSK-08 -sub-caso missing_file-):
execute() verifica, para cada archivo declarado en contract_data.json, su
existencia en el landing ANTES de leerlo; si no existe, lo marca con
status="missing", agrega una inconsistencia {type: "missing_file", detail}
y lo excluye de la lectura y de self._bronze_copies (no se copia a
bronze). summary.files_ingested/files_with_inconsistencies y
FlowResult.success/report["success"] ahora se derivan del conteo real de
inconsistencias (antes siempre files_declared/0/True). Solo se implementa
missing_file (NC-2): unexpected_file (caso 12) y missing_column/
unexpected_column (casos 13-14) quedan pendientes. Refactor: se extrajeron
los helpers de modulo _missing_file_entry(name)/_ingested_file_entry(name,
separator, columns, rows), que construyen la entrada de reporte
(esquema DS-ING-2) por archivo; elimina la duplicacion de la forma del
diccionario entre ambas ramas y reduce el anidamiento de execute(), sin
cambiar el comportamiento (NC-2/NC-3).

Caso 12 (CA-07) cerrado (tdd_refactor, TSK-08 -sub-caso unexpected_file-):
execute() acumula los nombres declarados por el contrato (declared_names) y,
tras recorrer los datasets, calcula unexpected_files como los nombres
presentes en el landing que no estan en declared_names, ordenados
alfabeticamente (DS-ING-6); success ahora tambien exige unexpected_files
vacio. Los archivos sobrantes ya quedaban fuera de self._bronze_copies (solo
se llena para archivos declarados), por lo que no se copian a bronze sin
cambios adicionales. Refactor: se extrajo el helper de modulo
_unexpected_files(landing_dir, declared_names), que aisla el calculo (mismo
patron de funcion pura de modulo ya usado por _detect_separator/
_missing_file_entry/_ingested_file_entry); execute() ya no mezcla la logica
de deteccion de sobrantes con el resto del armado del reporte, sin cambiar
el comportamiento (NC-2/NC-3).

Caso 13 (CA-08) cerrado (tdd_refactor, TSK-09 -sub-caso missing_column-):
execute() valida, para cada archivo presente y leible, sus columnas contra
fields[] del dataset homologo (por kind) de map_client_data.json via
_validate_columns; si falta una columna required==true, marca
status="rejected", agrega la inconsistencia missing_column y excluye el
archivo de self._bronze_copies (no se copia a bronze). Se agrego
_rejected_file_entry (misma familia de _missing_file_entry/
_ingested_file_entry, esquema DS-ING-2). Refactor: se elimino la lectura
duplicada del mismo archivo (antes _read_file y _read_header lo leian por
separado); _read_delimited/_read_xlsx ahora devuelven tambien la cabecera
(header) junto con separator/columns/rows en una unica pasada, y _read_file
la propaga; se retiraron _read_header_delimited/_read_header_xlsx/
_read_header (ya redundantes). execute() llama _read_file una sola vez por
archivo. Sin cambio de comportamiento observable (NC-2/NC-3).

Caso 14 (CA-09) cerrado (tdd_refactor, TSK-09 -sub-caso unexpected_column-):
_validate_columns agrega, para cada nombre de columna del header que no
corresponde a ningun field.name de fields[] del dataset homologo, una
inconsistencia {type: "unexpected_column", detail}. Reutiliza la misma
rama de execute() que missing_column (status="rejected" via
_rejected_file_entry, sin copia a bronze); no se implementa aun el caso 15
(columna required==false ausente no es inconsistencia, NC-2). Refactor: se
extrajeron _missing_required_columns(header, fields) y
_unexpected_columns(header, fields), dos funciones puras de modulo con
responsabilidad unica (una por cada direccion de la comparacion
header/fields), reemplazando los dos bucles inline con construccion de
dict mezclada dentro de _validate_columns; este ahora solo compone el
resultado de ambas (misma simetria de nombres missing/unexpected ya usada
por _missing_file_entry/_unexpected_files, casos 11-12). Sin cambio de
comportamiento observable (NC-2/NC-3).

Caso 16 (CA-16) en VERDE (tdd_coder, DS-ING-9/ADR D-078): el reporte gana
la lista top-level report["inconsistencies"], que AGREGA todas las
inconsistencias del run (missing_file, unexpected_file, missing_column,
unexpected_column), cada una {type, detail} con detail no vacio. Las
entradas missing_column/unexpected_column se agregan ADEMAS de quedar
anidadas por archivo (aditivo, no se mueven). Se agrego
_unexpected_file_entry(name), que construye la entrada de inconsistencia
(type="unexpected_file") para cada nombre de unexpected_files (antes ese
sobrante solo vivia en la lista de nombres, deuda documentada en el caso
12). execute() acumula top_level_inconsistencies conforme recorre
missing_file/column_inconsistencies y, al final, agrega una entrada por
cada unexpected_file (orden estable: se recorren los datasets/archivos en
el orden del contrato, y los sobrantes en orden alfabetico via
_unexpected_files, DS-ING-6).
"""

import json
from pathlib import Path

import openpyxl

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowResult

# DS-ING-8: requires/produces declarados; no se amplia ClientContext/Artifact (NC-3).
_REQUIRES = [
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
_PRODUCES = [
    Artifact(
        name="ingestion_report",
        base="outputs",
        relative="030_ingestion/ingestion_report.json",
    ),
]


_SEPARATORS = [",", ";", "|"]


def _detect_separator(header_line: str) -> str:
    """Plan.md Sec.1: entre ','/';'/'|' elige el que aparece con mayor
    numero de ocurrencias en la linea de cabecera (sin empates en el
    fixture, DS-ING-7)."""
    return max(_SEPARATORS, key=header_line.count)


def _read_delimited(path) -> tuple[list[str], str, int, int]:
    """Plan.md Sec.1: detecta el separador (','/';'/'|') a partir de la
    cabecera, la parte en nombres de columna y cuenta columnas/filas.
    Devuelve (header, separator, columns, rows): header = nombres de
    columna de la cabecera (TSK-09), columns = nro de columnas de la
    cabecera, rows = nro de filas de datos no vacias (sin la cabecera).
    Cubre .csv y .txt indistintamente (la extension no determina el
    separador; DS-ING-7)."""
    lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() != ""
    ]
    separator = _detect_separator(lines[0])
    header = lines[0].split(separator)
    return header, separator, len(header), len(lines) - 1


def _read_xlsx(path) -> tuple[list[str], None, int, int]:
    """Plan.md Sec.1 (TSK-06): lee la primera hoja de un .xlsx con
    openpyxl, obtiene los nombres de columna de la cabecera (TSK-09) y
    cuenta columnas/filas. Devuelve (header, separator, columns, rows):
    header = nombres de columna no vacios de la primera fila (cabecera);
    separator es siempre None (Excel no tiene separador delimitado,
    CA-04); columns = nro de celdas de la primera fila con contenido
    (cabecera, incluyendo vacias); rows = nro de filas de datos
    posteriores con al menos una celda no vacia."""
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.worksheets[0]
    all_rows = [
        row
        for row in sheet.iter_rows(values_only=True)
        if any(cell is not None for cell in row)
    ]
    raw_header = all_rows[0]
    header = [str(cell) for cell in raw_header if cell is not None]
    return header, None, len(raw_header), len(all_rows) - 1


def _read_file(path) -> tuple[list[str], str | None, int, int]:
    """Enruta por extension (DS-ING-7): .xlsx via _read_xlsx (formato
    Excel, sin separador); el resto (.csv/.txt) via _read_delimited (la
    extension no determina el separador delimitado). Una unica lectura de
    path por llamada; devuelve tanto la cabecera (TSK-09) como
    separator/columns/rows (TSK-03..TSK-07), evitando releer el archivo
    para obtener la cabecera por separado."""
    if path.suffix == ".xlsx":
        return _read_xlsx(path)
    return _read_delimited(path)


def _missing_required_columns(header: list[str], fields: list[dict]) -> list[dict]:
    """TSK-09 (CA-08): fields[] con required==true cuyo name no esta en
    header (columnas leidas del archivo). El caso del opcional ausente
    (caso 15, required==false, no es inconsistencia) queda para un caso
    posterior del bucle TDD (NC-2)."""
    return [
        {
            "type": "missing_column",
            "detail": (
                f"Falta la columna requerida '{field.get('name')}' segun "
                "map_client_data.json."
            ),
        }
        for field in fields
        if field.get("required") and field.get("name") not in header
    ]


def _unexpected_columns(header: list[str], fields: list[dict]) -> list[dict]:
    """TSK-09 (CA-09): columnas de header que no corresponden a ningun
    field.name de fields[] del dataset homologo de map_client_data.json."""
    field_names = {field.get("name") for field in fields}
    return [
        {
            "type": "unexpected_column",
            "detail": (
                f"La columna '{column_name}' no esta declarada en los "
                "fields de map_client_data.json."
            ),
        }
        for column_name in header
        if column_name not in field_names
    ]


def _validate_columns(header: list[str], fields: list[dict]) -> list[dict]:
    """TSK-09 (CA-08/CA-09): compara header (columnas leidas del archivo)
    contra fields[] del dataset homologo de map_client_data.json
    (emparejado por kind, DS-ING-8). Devuelve la lista de inconsistencias
    de columnas (esquema DS-ING-2), combinando las de ambas direcciones de
    la comparacion: columnas requeridas ausentes (_missing_required_columns,
    caso 13) y columnas presentes no declaradas (_unexpected_columns, caso
    14)."""
    return _missing_required_columns(header, fields) + _unexpected_columns(
        header, fields
    )


def _copy_bytes(src: Path, dst: Path) -> None:
    """Plan.md Sec.1 (TSK-07): copia binaria fiel byte a byte, sin
    re-serializar ni normalizar el contenido (DS-ING-6, HU-04)."""
    dst.write_bytes(src.read_bytes())


def _missing_file_entry(name: str) -> dict:
    """TSK-08 (CA-06): entrada de reporte (esquema DS-ING-2) para un archivo
    declarado en contract_data.json pero ausente del landing: status
    "missing", sin rows/columns/separator/bronze_path (None) y una unica
    inconsistencia missing_file con detail legible."""
    return {
        "name": name,
        "status": "missing",
        "rows": None,
        "columns": None,
        "separator": None,
        "bronze_path": None,
        "inconsistencies": [
            {
                "type": "missing_file",
                "detail": (
                    f"'{name}' esta declarado en contract_data.json pero no "
                    "se encontro en el landing."
                ),
            }
        ],
    }


def _unexpected_file_entry(name: str) -> dict:
    """TSK-08/DS-ING-9 (CA-07/CA-16): entrada de inconsistencia
    (type="unexpected_file") para un archivo presente en el landing pero no
    declarado en contract_data.json, con destino a la lista top-level
    reporte["inconsistencies"] (ADR D-078)."""
    return {
        "type": "unexpected_file",
        "detail": (
            f"'{name}' esta presente en el landing pero no fue declarado en "
            "contract_data.json."
        ),
    }


def _unexpected_files(landing_dir: Path, declared_names: set[str]) -> list[str]:
    """TSK-08 (CA-07): nombres presentes en landing_dir que no estan en
    declared_names (archivos declarados por contract_data.json), en orden
    alfabetico ascendente (DS-ING-6). [] si landing_dir no existe."""
    if not landing_dir.exists():
        return []
    return sorted(
        path.name
        for path in landing_dir.iterdir()
        if path.is_file() and path.name not in declared_names
    )


def _ingested_file_entry(
    name: str, separator: str | None, columns: int, rows: int
) -> dict:
    """Entrada de reporte (esquema DS-ING-2) para un archivo presente y
    leido correctamente del landing: status "ingested", con
    rows/columns/separator provistos por _read_file y sin
    inconsistencias."""
    return {
        "name": name,
        "status": "ingested",
        "rows": rows,
        "columns": columns,
        "separator": separator,
        "bronze_path": None,
        "inconsistencies": [],
    }


def _rejected_file_entry(
    name: str,
    separator: str | None,
    columns: int,
    rows: int,
    inconsistencies: list[dict],
) -> dict:
    """TSK-09 (CA-08): entrada de reporte (esquema DS-ING-2) para un archivo
    presente y leido del landing, pero cuyas columnas no cumplen el mapa
    (map_client_data.json): status "rejected", conserva rows/columns/
    separator (el archivo si se pudo leer) y las inconsistencias de
    columnas detectadas por _validate_columns."""
    return {
        "name": name,
        "status": "rejected",
        "rows": rows,
        "columns": columns,
        "separator": separator,
        "bronze_path": None,
        "inconsistencies": inconsistencies,
    }


class Ingestion(Flow):
    """Flujo 030: carga y valida datos crudos, copia inmutable a bronze y
    emite reporte de carga (ingestion_report.json).

    Caso 1 (CA-14): happy path minimo end-to-end (dataset "ventas" con un
    unico archivo "ventas.csv", separador coma) que produce y escribe el
    reporte. El resto del comportamiento (otros separadores, xlsx, copia a
    bronze, validacion de columnas, inconsistencias) se agrega en casos
    posteriores del bucle TDD.
    """

    name = "ingestion"
    requires = _REQUIRES
    produces = _PRODUCES

    def __init__(self) -> None:
        self._contract: dict | None = None
        self._map: dict | None = None
        self._report: dict | None = None
        self._bronze_copies: list[tuple[Path, Path]] = []

    def load_inputs(self, ctx: ClientContext) -> None:
        """DS-ING-8: lee y parsea contract_data.json (fuente de los archivos
        esperados) y map_client_data.json (fuente de las columnas esperadas)
        a estado de instancia, solo si existen; si falta alguno, deja el
        estado sin cargar para que validate() (base) lo detecte."""
        contract_path = self.requires[0].path(ctx)
        if contract_path.exists():
            self._contract = json.loads(contract_path.read_text(encoding="utf-8"))
        map_path = self.requires[1].path(ctx)
        if map_path.exists():
            self._map = json.loads(map_path.read_text(encoding="utf-8"))

    def validate(self, ctx: ClientContext) -> None:
        """DS-ING-8 (CA-20): delega en la comprobacion base (existencia de
        requires); la validacion de contenido (columnas, contrato) llega en
        casos posteriores del bucle TDD (no se adelanta, NC-2)."""
        super().validate(ctx)

    def execute(self, ctx: ClientContext) -> FlowResult:
        """Deriva en memoria el reporte de carga (esquema DS-ING-2) para el
        caso 1: por cada dataset del contrato, lee sus archivos declarados
        del landing (separador coma) y cuenta rows/columns. Ademas registra
        en self._bronze_copies el plan de copia (origen landing, destino
        ctx.bronze_dir/<name>) de cada archivo leido (todos validos hasta
        el caso 8; el filtrado por inconsistencias llega en casos
        posteriores, TSK-08 en adelante). Devuelve FlowResult(success=True,
        outputs=[ruta del reporte])."""
        contract = self._contract or {}
        map_by_kind = {
            dataset.get("kind"): dataset
            for dataset in (self._map or {}).get("datasets", [])
        }
        landing_dir = ctx.inputs_dir / "030_ingestion"
        datasets_out = []
        files_declared = 0
        files_with_inconsistencies = 0
        declared_names: set[str] = set()
        self._bronze_copies = []
        top_level_inconsistencies: list[dict] = []
        for dataset in contract.get("historical_data", {}).get("datasets", []):
            fields = map_by_kind.get(dataset.get("kind"), {}).get("fields", [])
            files_out = []
            for file_ in dataset.get("files", []):
                files_declared += 1
                name = file_.get("name")
                declared_names.add(name)
                source_path = landing_dir / name
                if not source_path.exists():
                    # TSK-08 (CA-06): declarado en el contrato pero ausente
                    # del landing -> status="missing", inconsistencia
                    # missing_file, sin lectura ni copia a bronze.
                    files_with_inconsistencies += 1
                    entry = _missing_file_entry(name)
                    files_out.append(entry)
                    # DS-ING-9 (CA-16): tambien se agrega a la lista
                    # top-level reporte["inconsistencies"].
                    top_level_inconsistencies.extend(entry["inconsistencies"])
                    continue
                header, separator, columns, rows = _read_file(source_path)
                column_inconsistencies = _validate_columns(header, fields)
                if column_inconsistencies:
                    # TSK-09 (CA-08): presente y legible, pero le falta una
                    # columna required==true segun el mapa -> status
                    # "rejected", sin copia a bronze.
                    files_with_inconsistencies += 1
                    files_out.append(
                        _rejected_file_entry(
                            name, separator, columns, rows, column_inconsistencies
                        )
                    )
                    # DS-ING-9 (CA-16): las inconsistencias de columna
                    # siguen ADEMAS anidadas por archivo (arriba); tambien
                    # se agregan a la lista top-level.
                    top_level_inconsistencies.extend(column_inconsistencies)
                    continue
                self._bronze_copies.append((source_path, ctx.bronze_dir / name))
                files_out.append(
                    _ingested_file_entry(name, separator, columns, rows)
                )
            datasets_out.append(
                {
                    "kind": dataset.get("kind"),
                    "source_medium": dataset.get("source_medium"),
                    "files": files_out,
                }
            )
        # TSK-08 (CA-07): archivos presentes en el landing no declarados en
        # ningun dataset del contrato -> unexpected_files; nunca se
        # registran en self._bronze_copies (solo se copian los archivos
        # declarados leidos arriba), por lo que no se copian a bronze.
        unexpected_files = _unexpected_files(landing_dir, declared_names)
        # DS-ING-9 (CA-16): cada archivo sobrante agrega una inconsistencia
        # unexpected_file a la lista top-level (su hogar estructural, pues
        # no pertenece a ningun dataset del contrato).
        top_level_inconsistencies.extend(
            _unexpected_file_entry(name) for name in unexpected_files
        )
        files_ingested = files_declared - files_with_inconsistencies
        success = files_with_inconsistencies == 0 and not unexpected_files
        self._report = {
            "schema_version": "0.1",
            "client": contract.get("client"),
            "flow": "ingestion",
            "success": success,
            "summary": {
                "datasets_declared": len(datasets_out),
                "files_declared": files_declared,
                "files_ingested": files_ingested,
                "files_with_inconsistencies": files_with_inconsistencies,
            },
            "datasets": datasets_out,
            "unexpected_files": unexpected_files,
            "inconsistencies": top_level_inconsistencies,
        }
        report_path = self.produces[0].path(ctx)
        return FlowResult(success=success, outputs=[report_path])

    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
        """DS-ING-6: crea la carpeta destino y escribe ingestion_report.json
        de forma determinista (sort_keys + indent=2 + newline final).
        Ademas (CA-11, TSK-07) crea ctx.bronze_dir y copia byte a byte cada
        archivo del plan self._bronze_copies (origen landing -> destino
        ctx.bronze_dir/<name>), sin re-serializar ni normalizar el
        contenido."""
        ctx.bronze_dir.mkdir(parents=True, exist_ok=True)
        for src, dst in self._bronze_copies:
            _copy_bytes(src, dst)
        path = self.produces[0].path(ctx)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._report, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
