"""Scaffold de cliente nuevo (feature client_scaffold, banda tracer_bullet).

Fuente: 600_features/client_scaffold/tracer_bullet/spec.md.
"""

from pathlib import Path

import yaml


_TOP_LEVEL_DIRS = ("010_inputs", "020_outputs", "data", "models")
_MEDALLION_DIRS = ("bronze", "silver", "gold")


def create_client(name: str, clients_root: Path) -> Path:
    """Crea clients_root/<name>/ y devuelve el Path a la carpeta creada.

    Implementacion minima (TDD, hasta caso 6 / CA-02, CA-03, CA-06): agrega,
    sobre el tracer bullet del caso 1, las entradas de primer nivel del
    arbol (010_inputs/, 020_outputs/, data/, models/), las subcarpetas
    medallion de data/ (bronze/, silver/, gold/) y el archivo client.yaml
    con contenido YAML valido que incluye name. La validacion del nombre y
    la comprobacion de duplicado se agregan en casos posteriores del bucle
    TDD.
    """
    client_dir = clients_root / name
    client_dir.mkdir(parents=True)

    for dir_name in _TOP_LEVEL_DIRS:
        (client_dir / dir_name).mkdir()

    for layer_name in _MEDALLION_DIRS:
        (client_dir / "data" / layer_name).mkdir()

    client_yaml = client_dir / "client.yaml"
    client_yaml.write_text(yaml.safe_dump({"name": name}), encoding="utf-8")

    return client_dir
