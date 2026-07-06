"""Flujo 020: Onboarding (feature onboarding, banda tracer_bullet).

Fuente: 600_features/onboarding/tracer_bullet/spec.md (DS-ONB-1..5) y plan.md
(TSK-01..TSK-09). Bucle TDD en curso: caso 1 (CA-01, TSK-02) y caso 3 (CA-02,
TSK-03 parcial) cerrados (derivacion minima de hierarchies.product.levels/
depth). El resto de jerarquias/datasets/totals (TSK-03..TSK-05), la
serializacion determinista (TSK-06) y la validacion de contenido (TSK-07)
quedan para casos posteriores del bucle.
"""

import json

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowResult

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
    (determinista). Caso 1 (CA-01): happy path minimo end-to-end; el mapa
    completo (jerarquias/datasets/totals) se agrega en casos posteriores."""

    name = "onboarding"
    requires = _REQUIRES
    produces = _PRODUCES

    def __init__(self) -> None:
        self._contract: dict | None = None
        self._mapa: dict | None = None

    def load_inputs(self, ctx: ClientContext) -> None:
        """DS-ONB-5: lee y parsea contract_data.json a estado de instancia solo
        si el archivo existe; si no existe, deja el estado sin cargar para que
        validate() (base) lo detecte."""
        path = self.requires[0].path(ctx)
        if path.exists():
            self._contract = json.loads(path.read_text(encoding="utf-8"))

    def validate(self, ctx: ClientContext) -> None:
        """Fase 2a (DS-ONB-5): existencia base del require. La coherencia de
        contenido (fase 2b) se agrega en casos posteriores del bucle."""
        super().validate(ctx)

    def execute(self, ctx: ClientContext) -> FlowResult:
        """Deriva en memoria el mapa canonico (identidad del cliente +
        jerarquia de producto) y devuelve FlowResult(success=True,
        outputs=[ruta de produces[0]])."""
        contract = self._contract or {}
        product_levels = contract.get("product_hierarchy", {}).get("levels", [])
        mapa = {
            "schema_version": contract.get("schema_version"),
            "client": contract.get("client"),
            "hierarchies": {
                "product": {
                    "levels": product_levels,
                    "depth": len(product_levels),
                }
            },
        }
        self._mapa = mapa
        return FlowResult(success=True, outputs=[self.produces[0].path(ctx)])

    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
        """DS-ONB-5: crea la carpeta destino y escribe map_client_data.json."""
        path = self.produces[0].path(ctx)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._mapa, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
