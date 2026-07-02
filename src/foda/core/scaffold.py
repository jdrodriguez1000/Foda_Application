"""Scaffold de cliente nuevo (feature client_scaffold, banda tracer_bullet).

Fuente: 600_features/client_scaffold/tracer_bullet/spec.md.
"""

from pathlib import Path


def create_client(name: str, clients_root: Path) -> Path:
    """Crea clients_root/<name>/ y devuelve el Path a la carpeta creada.

    Implementacion minima (TDD, caso 1 / CA-01, CA-07): solo cubre el
    tracer bullet (creacion del directorio y retorno del Path). La
    validacion del nombre, el arbol completo y client.yaml se agregan en
    casos posteriores del bucle TDD.
    """
    client_dir = clients_root / name
    client_dir.mkdir(parents=True)
    return client_dir
