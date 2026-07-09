"""Orquestador de flujos (feature flow_orchestrator, banda tracer_bullet).

Fuente: 600_features/flow_orchestrator/tracer_bullet/spec.md (DS-ORQ-1, DS-ORQ-2)
y 600_features/profiling/tracer_bullet/spec.md (DS-PROF-2, DS-PROF-4).

Vive fuera de core/ porque core no debe conocer flujos concretos (DS-ORQ-1).
FLOWS y PREDECESSORS son registros literales explicitos (NC-2: sin
descubrimiento dinamico).
"""

import json

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
    tiene entrada en PREDECESSORS, el gate es no-op y devuelve None.

    Si flow_name tiene predecesor registrado, resuelve la ruta de su reporte
    con resolve_flow(<predecesor>).produces[0].path(ctx) (DS-PROF-4) y, si el
    reporte existe con success:true, el gate esta satisfecho y devuelve None.
    Si el reporte existe pero success no es true, devuelve un mensaje legible
    que nombra al predecesor y el motivo (DS-PROF-4)."""
    if flow_name not in PREDECESSORS:
        return None

    predecessor_name = PREDECESSORS[flow_name]
    report_path = resolve_flow(predecessor_name).produces[0].path(ctx)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report["success"] is True:
        return None
    return (
        f"El predecesor {predecessor_name!r} no tiene un reporte con "
        "success == true."
    )
