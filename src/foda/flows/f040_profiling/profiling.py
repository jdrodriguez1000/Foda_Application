"""Flujo 040: Profiling (feature profiling, banda tracer_bullet).

Fuente: 600_features/profiling/tracer_bullet/spec.md y plan.md. Bucle TDD en
curso: caso 1 (CA-01) en VERDE (tdd_coder). Implementacion minima (NC-2):
solo se declara el contrato de la clase (name/requires/produces), calcado
del patron de Ingestion (ver f030_ingestion/ingestion.py). Los hooks
load_inputs/execute/write_outputs (comportamiento real de ejecucion) llegan
en casos posteriores del bucle TDD (no se adelantan).

Caso 2 (CA-02) en VERDE (tdd_coder, TSK-05): Profiling no sobreescribe run()
(usa el template method heredado de Flow); execute(ctx) arma en memoria el
reporte minimo (esquema {schema_version, client, flow, success}, sin leer
bronze todavia -esta banda no calcula salud de datos, NC-2) y
write_outputs(ctx, result) lo persiste de forma deterministica, calcado del
patron de Ingestion.write_outputs (sort_keys + indent=2 + newline final, sin
la parte de copia a bronze que no aplica a este flujo).

Banda stab_1, caso 1 (CA-18, CA-19, TSK-02) en VERDE (tdd_coder): bump
aditivo de schema_version a "0.2" (DS-PRF-7); identidad client/flow/success
sin cambios de tipo ni valor. El bloque health y demas logica de stab_1
llegan en casos posteriores del bucle TDD (no se adelantan, NC-2).
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
    """Flujo 040: analiza el bronze ingerido y emite reporte de profiling
    (profiling_report.json).

    Caso 1 (CA-01): solo el contrato de clase (name, requires, produces).
    Caso 2 (CA-02): execute()/write_outputs() arman y persisten el reporte
    minimo (sin sobreescribir run(), heredado de Flow).
    """

    name = "profiling"
    requires = _REQUIRES
    produces = _PRODUCES

    def __init__(self) -> None:
        self._report: dict | None = None

    def execute(self, ctx: ClientContext) -> FlowResult:
        """Arma en memoria el reporte minimo de profiling (esta banda no lee
        bronze/ ni calcula salud de datos, NC-2)."""
        self._report = {
            "schema_version": "0.2",
            "client": ctx.name,
            "flow": "profiling",
            "success": True,
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
