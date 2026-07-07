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
"""

import json

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


def _read_comma_delimited(path) -> tuple[int, int]:
    """Lee un archivo delimitado por coma (unico separador del caso 1) y
    devuelve (columns, rows): columns = nro de columnas de la cabecera,
    rows = nro de filas de datos no vacias (sin la cabecera)."""
    lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() != ""
    ]
    header = lines[0].split(",")
    return len(header), len(lines) - 1


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
        del landing (separador coma) y cuenta rows/columns. Devuelve
        FlowResult(success=True, outputs=[ruta del reporte])."""
        contract = self._contract or {}
        landing_dir = ctx.inputs_dir / "030_ingestion"
        datasets_out = []
        files_declared = 0
        for dataset in contract.get("historical_data", {}).get("datasets", []):
            files_out = []
            for file_ in dataset.get("files", []):
                files_declared += 1
                name = file_.get("name")
                columns, rows = _read_comma_delimited(landing_dir / name)
                files_out.append(
                    {
                        "name": name,
                        "status": "ingested",
                        "rows": rows,
                        "columns": columns,
                        "separator": ",",
                        "bronze_path": None,
                        "inconsistencies": [],
                    }
                )
            datasets_out.append(
                {
                    "kind": dataset.get("kind"),
                    "source_medium": dataset.get("source_medium"),
                    "files": files_out,
                }
            )
        self._report = {
            "schema_version": "0.1",
            "client": contract.get("client"),
            "flow": "ingestion",
            "success": True,
            "summary": {
                "datasets_declared": len(datasets_out),
                "files_declared": files_declared,
                "files_ingested": files_declared,
                "files_with_inconsistencies": 0,
            },
            "datasets": datasets_out,
            "unexpected_files": [],
        }
        report_path = self.produces[0].path(ctx)
        return FlowResult(success=True, outputs=[report_path])

    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
        """DS-ING-6: crea la carpeta destino y escribe ingestion_report.json
        de forma determinista (sort_keys + indent=2 + newline final)."""
        path = self.produces[0].path(ctx)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._report, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
