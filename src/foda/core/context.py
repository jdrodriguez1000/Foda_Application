"""Contexto de lectura de un cliente existente (feature client_context, banda tracer_bullet).

Fuente: 600_features/client_context/tracer_bullet/spec.md.
"""

from pathlib import Path


class ClientContext:
    """Contexto de LECTURA de un cliente ya creado bajo clients_root/<name>/.

    Implementacion parcial (TDD, casos 1-6 / CA-01, CA-05, CA-06, CA-07, CA-09):
    resuelve root = clients_root/name y expone name, root, inputs_dir,
    outputs_dir, bronze_dir, silver_dir, gold_dir, models_dir e is_recurring
    (True si models_dir/"latest" existe; funcion pura del disco, no lee
    client.yaml). La validacion de existencia del cliente (FileNotFoundError)
    se agrega en casos posteriores del bucle TDD (9-11).
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

    @property
    def is_recurring(self) -> bool:
        return (self.models_dir / "latest").exists()

    def _data_dir(self, layer: str) -> Path:
        """Resuelve root/data/<layer> (bronze/silver/gold comparten el prefijo data/)."""
        return self.root / "data" / layer
