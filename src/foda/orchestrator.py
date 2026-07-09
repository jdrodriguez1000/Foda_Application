"""Orquestador de flujos (feature flow_orchestrator, banda tracer_bullet).

Fuente: 600_features/flow_orchestrator/tracer_bullet/spec.md (DS-ORQ-1, DS-ORQ-2)
y plan.md (TSK-01). Bucle TDD: caso 1 (resolve_flow("onboarding") devuelve una
instancia de Onboarding) en verde.

Vive fuera de core/ porque core no debe conocer flujos concretos (DS-ORQ-1).
FLOWS es un registro literal explicito (NC-2: sin descubrimiento dinamico).
"""

from foda.core.context import ClientContext
from foda.core.flow import Flow
from foda.flows.f020_onboarding.onboarding import Onboarding
from foda.flows.f030_ingestion.ingestion import Ingestion
from foda.flows.f040_profiling.profiling import Profiling

FLOWS: dict[str, type[Flow]] = {
    "onboarding": Onboarding,
    "ingestion": Ingestion,
    "profiling": Profiling,
}

PREDECESSORS: dict[str, str] = {
    "profiling": "ingestion",
}


def resolve_flow(name: str) -> Flow:
    """Devuelve una instancia del Flow registrado bajo name; lanza ValueError
    si name no esta en FLOWS (DS-ORQ-2)."""
    try:
        flow_cls = FLOWS[name]
    except KeyError as exc:
        raise ValueError(f"Flujo desconocido: {name!r}. Debe ser uno de {sorted(FLOWS)}.") from exc
    return flow_cls()


def evaluate_predecessor_gate(flow_name: str, ctx: ClientContext) -> str | None:
    """Evalua el gate de predecesor de flow_name (DS-PROF-2). Si flow_name no
    tiene entrada en PREDECESSORS, el gate es no-op y devuelve None."""
    if flow_name not in PREDECESSORS:
        return None
