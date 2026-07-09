"""Flujo 040: Profiling (feature profiling, banda tracer_bullet).

Fuente: 600_features/profiling/tracer_bullet/spec.md y plan.md. Bucle TDD en
curso: caso 1 (CA-01) en VERDE (tdd_coder). Implementacion minima (NC-2):
solo se declara el contrato de la clase (name/requires/produces), calcado
del patron de Ingestion (ver f030_ingestion/ingestion.py). Los hooks
load_inputs/execute/write_outputs (comportamiento real de ejecucion) llegan
en casos posteriores del bucle TDD (no se adelantan).
"""

from foda.core.flow import Artifact, Flow

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

    Caso 1 (CA-01): solo el contrato de clase (name, requires, produces). El
    resto del comportamiento (validate/execute/write_outputs) se agrega en
    casos posteriores del bucle TDD.
    """

    name = "profiling"
    requires = _REQUIRES
    produces = _PRODUCES
