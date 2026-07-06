"""Flujo 020: Onboarding (feature onboarding, banda tracer_bullet).

Fuente: 600_features/onboarding/tracer_bullet/spec.md (DS-ONB-1..5) y plan.md
(TSK-01..TSK-09). Bucle TDD en curso: este archivo es el esqueleto minimo
importable requerido por el caso 1 (CA-01); NO implementa load_inputs,
validate, execute ni write_outputs (quedan para tdd_coder, caso a caso).
"""

from foda.core.flow import Artifact, Flow

# DS-ONB-5: requires/produces declarados; no se amplia ClientContext.
_REQUIRES = [
    Artifact(
        name="contract_data",
        base="outputs",
        relative="010_discovery/contract_data.json",
    )
]
_PRODUCES = [
    Artifact(
        name="map_client_data",
        base="outputs",
        relative="020_onboarding/map_client_data.json",
    )
]


class Onboarding(Flow):
    """Flujo 020: deriva map_client_data.json desde contract_data.json
    (determinista). Esqueleto: no sobreescribe execute/write_outputs todavia."""

    name = "onboarding"
    requires = _REQUIRES
    produces = _PRODUCES
