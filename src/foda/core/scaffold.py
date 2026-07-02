"""Scaffold de cliente nuevo (feature client_scaffold, banda tracer_bullet).

Fuente: 600_features/client_scaffold/tracer_bullet/spec.md.
"""

from pathlib import Path


_TOP_LEVEL_DIRS = ("010_inputs", "020_outputs", "data", "models")


def create_client(name: str, clients_root: Path) -> Path:
    """Crea clients_root/<name>/ y devuelve el Path a la carpeta creada.

    Implementacion minima (TDD, caso 2 / CA-02): agrega, sobre el tracer
    bullet del caso 1, las entradas de primer nivel del arbol
    (010_inputs/, 020_outputs/, data/, models/) y el archivo client.yaml
    (vacio por ahora). El contenido de client.yaml (name, created_at), las
    subcarpetas medallion de data/, la validacion del nombre y la
    comprobacion de duplicado se agregan en casos posteriores del bucle
    TDD.
    """
    client_dir = clients_root / name
    client_dir.mkdir(parents=True)

    for dir_name in _TOP_LEVEL_DIRS:
        (client_dir / dir_name).mkdir()

    (client_dir / "client.yaml").touch()

    return client_dir
