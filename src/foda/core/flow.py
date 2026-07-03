"""Abstraccion base de flujo (feature flow_base, banda tracer_bullet).

Fuente: 600_features/flow_base/tracer_bullet/spec.md (DS-FLOW-2/3/4, Interfaces /
Firmas Publicas) y plan.md (TSK-01, TSK-02, TSK-04). Bucle TDD: casos 1-3 (CA-09,
CA-10, CA-01) en verde.

Esta version implementa `Artifact` (TSK-01), `FlowResult` (TSK-02) y el esqueleto de
`Flow` con el template method `run` y los hooks base `load_inputs`/`execute`/
`write_outputs` (TSK-04), lo minimo necesario para los casos 1-3 del bucle TDD.
`Flow.validate` queda como placeholder no-op (se implementa en TSK-05, caso 9+) y
`FlowContractError` se añade en una tarea/caso posterior.
"""

from dataclasses import dataclass
from pathlib import Path

from foda.core.context import ClientContext

# DS-FLOW-2: claves logicas de carpeta soportadas por Artifact.base, mapeadas a las
# propiedades de ruta que ya expone ClientContext (T-014, CONFORME).
_BASE_TO_DIR_ATTR = {
    "inputs": "inputs_dir",
    "outputs": "outputs_dir",
    "bronze": "bronze_dir",
    "silver": "silver_dir",
    "gold": "gold_dir",
    "models": "models_dir",
}


@dataclass(frozen=True)
class Artifact:
    """Descriptor declarativo minimo de un artefacto de flujo.

    Resuelve su ruta fisica a traves de ClientContext (no reimplementa rutas).
    base ∈ {"inputs","outputs","bronze","silver","gold","models"} (carpetas §7).
    """

    name: str
    base: str
    relative: str

    def path(self, ctx: ClientContext) -> Path:
        """Ruta absoluta = <directorio base de ctx> / relative.

        Lanza ValueError si base no es una clave logica conocida (DS-FLOW-2, guarda
        defensiva de error de programacion del autor del flujo).
        """
        try:
            dir_attr = _BASE_TO_DIR_ATTR[self.base]
        except KeyError as exc:
            raise ValueError(
                f"Artifact.base desconocido: {self.base!r}. "
                f"Debe ser una de {sorted(_BASE_TO_DIR_ATTR)}."
            ) from exc
        return getattr(ctx, dir_attr) / self.relative

    def exists(self, ctx: ClientContext) -> bool:
        """True si self.path(ctx) existe en disco."""
        return self.path(ctx).exists()


@dataclass(frozen=True)
class FlowResult:
    """Estado de una ejecucion de flujo + rutas de artefactos producidos (DS-FLOW-3)."""

    success: bool
    outputs: list[Path]


class Flow:
    """Abstraccion comun de un flujo (system_design.md §9, DS-FLOW-4).

    Template method run() invoca load_inputs -> validate -> execute ->
    write_outputs en orden fijo. Los flujos concretos heredan y sobreescriben
    SOLO los 4 hooks; run() no es sobreescribible en el contrato.
    """

    name: str = ""
    requires: list[Artifact] = []
    produces: list[Artifact] = []

    def run(self, ctx: ClientContext) -> FlowResult:
        self.load_inputs(ctx)
        self.validate(ctx)
        result = self.execute(ctx)
        self.write_outputs(ctx, result)
        return result

    def load_inputs(self, ctx: ClientContext) -> None:
        """Base: no-op. Subclases cargan inputs (YAML/JSON) a su estado."""

    def validate(self, ctx: ClientContext) -> None:
        """Base (placeholder, TSK-05 pendiente): no-op."""

    def execute(self, ctx: ClientContext) -> FlowResult:
        """Base: raise NotImplementedError. Subclases ejecutan el nucleo y
        devuelven un FlowResult."""
        raise NotImplementedError(
            "Flow.execute() debe ser sobreescrito por la subclase concreta."
        )

    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
        """Base: no-op. Subclases persisten los artefactos de produces."""
