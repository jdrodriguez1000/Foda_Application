"""Suite unitaria del registro/resolucion de flujos (feature flow_orchestrator,
banda tracer_bullet). Independiente de la CLI, sin disco.

Fuente: 600_features/flow_orchestrator/tracer_bullet/spec.md (DS-ORQ-1/2, CA-10) y
plan.md (TSK-05..TSK-07). Bucle TDD en curso: caso 3 (CA-10/CA-04, TSK-07).

Tambien cubre el gate de progresion entre flujos de la feature profiling/
tracer_bullet (600_features/profiling/tracer_bullet/spec.md DS-PROF-2/DS-PROF-4,
plan.md TSK-11..TSK-18): PREDECESSORS y evaluate_predecessor_gate.
"""

import pytest

from foda.core.context import ClientContext
from foda.core.flow import Flow
from foda.core.scaffold import create_client
from foda.flows.f020_onboarding.onboarding import Onboarding
from foda.flows.f040_profiling.profiling import Profiling
from foda.orchestrator import FLOWS, PREDECESSORS, evaluate_predecessor_gate, resolve_flow


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


def test_resolve_flow_nombre_no_registrado_lanza_value_error() -> None:
    """Caso 3 (CA-10/CA-04, TSK-07): resolve_flow(<nombre no registrado>)
    lanza ValueError (no KeyError ni otra excepcion)."""
    with pytest.raises(ValueError):
        resolve_flow("inexistente")


def test_resolve_flow_profiling_devuelve_instancia_de_profiling() -> None:
    """Caso 6 (feature profiling/tracer_bullet, CA-06, TSK-09): resolve_flow(
    "profiling") devuelve una INSTANCIA de Profiling (subclase de Flow), via
    el registro FLOWS. Hoy "profiling" no esta registrado en FLOWS (solo
    "onboarding"/"ingestion"), por lo que resolve_flow lanza ValueError en vez
    de devolver la instancia esperada: rojo genuino, TSK-10 lo pone en verde."""
    flow = resolve_flow("profiling")

    assert isinstance(flow, Profiling)
    assert isinstance(flow, Flow)


def test_predecessors_mapea_profiling_a_ingestion_y_gate_es_noop_sin_predecesor(
    tmp_path,
) -> None:
    """Caso 7 (feature profiling/tracer_bullet, CA-12, TSK-11): PREDECESSORS
    es el mapa literal explicito {"profiling": "ingestion"} (DS-PROF-2), y
    evaluate_predecessor_gate(flow_name, ctx) devuelve None para un flujo SIN
    entrada registrada en PREDECESSORS (p. ej. "ingestion", que no tiene
    predecesor en esta banda: el par ingestion->onboarding queda excluido a
    proposito, ver spec DS-PROF-2) -- el gate es no-op, sin exigir ningun
    reporte en disco.

    Hoy ni PREDECESSORS ni evaluate_predecessor_gate existen en
    foda.orchestrator (solo TSK-10 -- registro de "profiling" en FLOWS -- esta
    en verde); el import de ambos en el modulo falla con ImportError. Rojo
    genuino: no hay typo ni error de sintaxis, falta el mapa y la funcion que
    TSK-12 debe introducir como esqueleto minimo."""
    assert PREDECESSORS == {"profiling": "ingestion"}

    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    assert evaluate_predecessor_gate("ingestion", ctx) is None
