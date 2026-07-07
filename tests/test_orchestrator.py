"""Suite unitaria del registro/resolucion de flujos (feature flow_orchestrator,
banda tracer_bullet). Independiente de la CLI, sin disco.

Fuente: 600_features/flow_orchestrator/tracer_bullet/spec.md (DS-ORQ-1/2, CA-10) y
plan.md (TSK-05..TSK-07). Bucle TDD en curso: caso 1 (CA-10) en rojo.
"""

from foda.core.flow import Flow
from foda.flows.f020_onboarding.onboarding import Onboarding
from foda.orchestrator import FLOWS, resolve_flow


def test_resolve_flow_onboarding_devuelve_instancia_de_onboarding() -> None:
    """Caso 1 (CA-10, TSK-05): resolve_flow("onboarding") devuelve una
    INSTANCIA de Onboarding (subclase de Flow), no la clase ni otro tipo."""
    flow = resolve_flow("onboarding")

    assert isinstance(flow, Onboarding)
    assert isinstance(flow, Flow)


def test_flows_es_mapeo_explicito_onboarding_a_clase_onboarding() -> None:
    """Caso 2 (CA-10, TSK-06): FLOWS es un mapeo explicito nombre->clase Flow
    que contiene "onboarding" -> Onboarding (la CLASE, no una instancia)."""
    assert isinstance(FLOWS, dict)
    assert "onboarding" in FLOWS
    assert FLOWS["onboarding"] is Onboarding

    for name, flow_cls in FLOWS.items():
        assert isinstance(name, str)
        assert isinstance(flow_cls, type)
        assert issubclass(flow_cls, Flow)
