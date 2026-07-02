"""Scaffold de cliente nuevo (feature client_scaffold, banda tracer_bullet).

Fuente: 600_features/client_scaffold/tracer_bullet/spec.md.
"""

from datetime import date
from pathlib import Path

import yaml


_TOP_LEVEL_DIRS = ("010_inputs", "020_outputs", "data", "models")
_MEDALLION_DIRS = ("bronze", "silver", "gold")


def _validate_name(name: str) -> None:
    """Valida name antes de tocar el filesystem (CA-08, CA-11).

    Implementacion minima (casos 9-12): rechaza el nombre vacio,
    cualquier nombre que contenga espacios (solo-espacios o espacio
    interior), cualquier nombre cuyo primer caracter sea "-" o "_"
    (DS-1: el primer caracter debe ser alfanumerico), y cualquier nombre
    que contenga un separador de ruta ("/" o "\\"), para evitar que
    clients_root / name resuelva a una subruta anidada fuera de
    clients_root. Las demas reglas ("." / "..", caracteres no permitidos,
    no-ASCII, longitud>64) se agregan en los casos 13-16 del bucle TDD.
    """
    if name == "":
        raise ValueError("name no puede ser vacio")
    if " " in name:
        raise ValueError("name no puede contener espacios")
    if name[0] in ("-", "_"):
        raise ValueError("name no puede empezar por - ni _")
    if "/" in name or "\\" in name:
        raise ValueError("name no puede contener separadores de ruta")
    if name in (".", ".."):
        raise ValueError("name no puede ser \".\" ni \"..\"")


def create_client(name: str, clients_root: Path) -> Path:
    """Crea clients_root/<name>/ y devuelve el Path a la carpeta creada.

    Implementacion minima (TDD, hasta caso 9 / CA-02, CA-03, CA-06, CA-08):
    agrega, sobre el tracer bullet del caso 1, las entradas de primer nivel
    del arbol (010_inputs/, 020_outputs/, data/, models/), las subcarpetas
    medallion de data/ (bronze/, silver/, gold/), el archivo client.yaml
    con contenido YAML valido que incluye name y created_at (fecha ISO
    YYYY-MM-DD del dia de creacion), y una validacion inicial del nombre
    (por ahora solo rechaza vacio) antes de crear cualquier carpeta. El
    resto de las reglas de validacion y la comprobacion de duplicado se
    agregan en casos posteriores del bucle TDD.
    """
    _validate_name(name)

    client_dir = clients_root / name
    client_dir.mkdir(parents=True)

    for dir_name in _TOP_LEVEL_DIRS:
        (client_dir / dir_name).mkdir()

    for layer_name in _MEDALLION_DIRS:
        (client_dir / "data" / layer_name).mkdir()

    client_yaml = client_dir / "client.yaml"
    yaml_content = {"name": name, "created_at": date.today().isoformat()}
    # default_style="'" fuerza comillas en los escalares para que created_at
    # (p.ej. "2026-07-02") se relea como str y no como date via el resolver
    # implicito de YAML.
    client_yaml.write_text(
        yaml.safe_dump(yaml_content, default_style="'"), encoding="utf-8"
    )

    return client_dir
