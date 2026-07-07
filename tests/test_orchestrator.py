"""Suite unitaria del registro/resolucion de flujos (feature flow_orchestrator,
banda tracer_bullet). Independiente de la CLI, sin disco.

Fuente: 600_features/flow_orchestrator/tracer_bullet/spec.md (DS-ORQ-1/2, CA-10) y
plan.md (TSK-05..TSK-07). Bucle TDD en curso: caso 1 (CA-10) en rojo.
"""

from foda.core.flow import Flow
from foda.flows.f020_onboarding.onboarding import Onboarding
from foda.orchestrator import resolve_flow


def test_resolve_flow_onboarding_devuelve_instancia_de_onboarding() -> None:
    """Caso 1 (CA-10, TSK-05): resolve_flow("onboarding") devuelve una
    INSTANCIA de Onboarding (subclase de Flow), no la clase ni otro tipo."""
    flow = resolve_flow("onboarding")

    assert isinstance(flow, Onboarding)
    assert isinstance(flow, Flow)
