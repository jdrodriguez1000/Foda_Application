"""Contexto de lectura de un cliente existente (feature client_context, banda tracer_bullet).

Fuente: 600_features/client_context/tracer_bullet/spec.md.
"""

from pathlib import Path


class ClientContext:
    """Contexto de LECTURA de un cliente ya creado bajo clients_root/<name>/.

    Implementacion minima (TDD, caso 1 / CA-01): resuelve root = clients_root/name
    y expone name y root. La validacion de existencia (FileNotFoundError) y las
    demas propiedades de ruta / is_recurring se agregan en casos posteriores del
    bucle TDD.
    """

    def __init__(self, name: str, clients_root: Path) -> None:
        self.name = name
        self.root = clients_root / name
