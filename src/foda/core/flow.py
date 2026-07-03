"""Abstraccion base de flujo (feature flow_base, banda tracer_bullet).

Fuente: 600_features/flow_base/tracer_bullet/spec.md (DS-FLOW-2, Interfaces / Firmas
Publicas) y plan.md (TSK-01). Bucle TDD: caso 1 (CA-10) en verde.

Esta version implementa unicamente el dataclass `Artifact` (TSK-01), lo minimo
necesario para el caso 1 del bucle TDD. `FlowResult`, `FlowContractError` y `Flow`
se añaden en tareas/casos posteriores del mismo bucle.
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
