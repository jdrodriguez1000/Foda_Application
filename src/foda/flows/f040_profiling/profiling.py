"""Flujo 040: Profiling (feature profiling).

Banda tracer_bullet: contrato de clase + execute()/write_outputs() que arman
y persisten el reporte minimo (esquema {schema_version, client, flow, success})
de forma deterministica, sin sobreescribir run() (template method heredado de
Flow), calcado del patron de Ingestion.

Banda stab_1 (bucle TDD en curso, red/green/refactor caso a caso):
- Caso 1 (CA-18, CA-19): bump aditivo de schema_version a "0.2" (DS-PRF-7);
  identidad client/flow/success sin cambios de tipo ni valor.
- Caso 2 (CA-20, CA-17): execute() arma el bloque health con las 6 claves
  fijas (global_score, files_declared, files_healthy, files_with_problems,
  problems_by_type, pareto). Implementacion MINIMA (NC-2, TDD estricto): para
  el fixture "todos sanos" del caso 2 basta con las 6 claves presentes,
  global_score==1.0 y pareto==[]; los valores de conteos, problems_by_type y
  la formula ponderada de global_score son placeholders (0 / {} / 1.0) que los
  casos 3-22 iran forzando a su forma real, uno a uno (fake-it-till-you-make-it).
  No se lee bronze/ ni client_register.yaml (fuera de alcance, DS-PRF-1).
- Caso 3 (CA-06, DS-PRF-3): health.files_declared ya no es un placeholder
  fijo; se lee de self._ingestion_report["summary"]["files_declared"]
  (cargado en load_inputs). files_healthy, files_with_problems,
  problems_by_type, global_score y pareto siguen como placeholders minimos
  (0 / {} / 1.0 / []) hasta sus propios casos (4-22).

Nota (NC-6): una version previa del caso 2 adelanto de una vez toda la logica
de health (DS-PRF-2..5). Por decision del humano se restauro el TDD estricto:
esa logica se revirtio a este minimo para reconstruirla caso a caso con
rojo->verde genuino.
"""

import json

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowResult

_REQUIRES = [
    Artifact(
        name="ingestion_report",
        base="outputs",
        relative="030_ingestion/ingestion_report.json",
    ),
]
_PRODUCES = [
    Artifact(
        name="profiling_report",
        base="outputs",
        relative="040_profiling/profiling_report.json",
    ),
]


class Profiling(Flow):
    """Flujo 040: analiza el ingreso ingerido y emite reporte de profiling
    (profiling_report.json)."""

    name = "profiling"
    requires = _REQUIRES
    produces = _PRODUCES

    def __init__(self) -> None:
        self._report: dict | None = None
        self._ingestion_report: dict | None = None

    def load_inputs(self, ctx: ClientContext) -> None:
        """Lee y parsea ingestion_report.json (unico require) a estado de
        instancia solo si existe; si no existe, deja el estado sin cargar
        para que validate() (base) lo detecte."""
        path = self.requires[0].path(ctx)
        if path.exists():
            self._ingestion_report = json.loads(path.read_text(encoding="utf-8"))

    def execute(self, ctx: ClientContext) -> FlowResult:
        """Arma en memoria el reporte de profiling: identidad (schema_version
        "0.2", client, flow, success) + bloque health con las 6 claves fijas.

        Caso 3 (DS-PRF-3): files_declared proviene de
        ingestion_report.summary.files_declared. Los demas campos de health
        siguen como placeholders minimos hasta sus propios casos (4-22),
        TDD estricto (NC-2)."""
        files_declared = self._ingestion_report.get("summary", {}).get(
            "files_declared", 0
        )
        self._report = {
            "schema_version": "0.2",
            "client": ctx.name,
            "flow": "profiling",
            "success": True,
            "health": {
                "global_score": 1.0,
                "files_declared": files_declared,
                "files_healthy": 0,
                "files_with_problems": 0,
                "problems_by_type": {},
                "pareto": [],
            },
        }
        return FlowResult(success=True, outputs=[self.produces[0].path(ctx)])

    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
        """Escribe profiling_report.json de forma deterministica (sort_keys
        + indent=2 + newline final), calcado de Ingestion.write_outputs."""
        path = self.produces[0].path(ctx)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._report, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
