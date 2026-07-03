"""Contexto de lectura de un cliente existente (feature client_context, banda tracer_bullet).

Fuente: 600_features/client_context/tracer_bullet/spec.md.
"""

from pathlib import Path


class ClientContext:
    """Contexto de LECTURA de un cliente ya creado bajo clients_root/<name>/.

    Implementacion minima (TDD, casos 1-3 / CA-01, CA-05, CA-06): resuelve
    root = clients_root/name y expone name, root, inputs_dir, outputs_dir,
    bronze_dir, silver_dir y gold_dir. La validacion de existencia
    (FileNotFoundError) y las demas propiedades de ruta / is_recurring se
    agregan en casos posteriores del bucle TDD.
    """

    def __init__(self, name: str, clients_root: Path) -> None:
        self.name = name
        self.root = clients_root / name

    @property
    def inputs_dir(self) -> Path:
        return self.root / "010_inputs"

    @property
    def outputs_dir(self) -> Path:
        return self.root / "020_outputs"

    @property
    def bronze_dir(self) -> Path:
        return self._data_dir("bronze")

    @property
    def silver_dir(self) -> Path:
        return self._data_dir("silver")

    @property
    def gold_dir(self) -> Path:
        return self._data_dir("gold")

    @property
    def models_dir(self) -> Path:
        return self.root / "models"

    def _data_dir(self, layer: str) -> Path:
        """Resuelve root/data/<layer> (bronze/silver/gold comparten el prefijo data/)."""
        return self.root / "data" / layer
