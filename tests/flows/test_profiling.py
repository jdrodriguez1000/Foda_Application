"""Tests unitarios de Profiling (feature profiling, banda tracer_bullet).

Fuente: 600_features/profiling/tracer_bullet/spec.md (CA-xx) y plan.md
(casos TDD, TSK-01..TSK-08). Bucle TDD: un test por caso, ejecutado en orden
(state.json -> stages.tdd.cases). Este archivo arranca con el caso 1
(CA-01): Profiling es subclase de Flow con name/requires/produces correctos
(DS-PROF-1..4, calcado del patron de Ingestion, ver plan.md Sec.A).
"""

from foda.core.flow import Artifact, Flow
from foda.flows.f040_profiling.profiling import Profiling


def test_profiling_es_subclase_de_flow_con_contrato_correcto() -> None:
    """CA-01: Profiling es subclase de Flow, name=="profiling", requires es
    [Artifact ingestion_report @ outputs/030_ingestion/ingestion_report.json]
    y produces es [Artifact profiling_report @
    outputs/040_profiling/profiling_report.json]."""
    assert issubclass(Profiling, Flow)
    assert Profiling.name == "profiling"

    assert Profiling.requires == [
        Artifact(
            name="ingestion_report",
            base="outputs",
            relative="030_ingestion/ingestion_report.json",
        )
    ]
    assert Profiling.produces == [
        Artifact(
            name="profiling_report",
            base="outputs",
            relative="040_profiling/profiling_report.json",
        )
    ]
