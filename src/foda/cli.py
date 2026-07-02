"""Punto de entrada de la CLI `foda` (feature client_new_cli, banda tracer_bullet).

Fuente: 600_features/client_new_cli/tracer_bullet/spec.md.

Implementacion parcial (TDD, casos 1-9 en verde / TSK-02, TSK-03, TSK-04,
TSK-05): parser argparse minimo, resolucion de la raiz del proyecto
(marcador pyproject.toml) hacia arriba desde el cwd (D-C) con su fallo
controlado (DS-CLI-1: raiz no encontrada -> stderr + codigo 1, sin tocar
disco), aseguramiento de clients_root, delegacion en create_client,
traduccion del camino de exito a consola y traduccion de ValueError (nombre
invalido) / FileExistsError (duplicado) a stderr + codigo 1. Los errores de
parseo de argparse (NAME ausente, subcomando desconocido) los agregan los
casos siguientes del bucle TDD.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from foda.core.scaffold import create_client


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="foda")
    subparsers = parser.add_subparsers(dest="command")

    client_parser = subparsers.add_parser("client")
    client_subparsers = client_parser.add_subparsers(dest="client_command")

    new_parser = client_subparsers.add_parser("new")
    new_parser.add_argument("name")

    return parser


def _find_project_root(start: Path) -> Path | None:
    """Busca hacia arriba desde start el primer directorio que contenga
    pyproject.toml (D-C). Devuelve None si no se encuentra."""
    current = start.resolve()
    while True:
        if (current / "pyproject.toml").exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


def _protect_dash_prefixed_name(argv: list[str]) -> list[str]:
    """Si argv es 'client new <NAME>' y NAME empieza con "-" (p. ej. "-x"),
    inserta un separador "--" antes de NAME para que argparse lo trate como
    valor posicional en vez de opcion desconocida, dejando que create_client
    lo rechace como nombre invalido (CA-07/DS-CLI-3)."""
    if (
        len(argv) >= 3
        and argv[0] == "client"
        and argv[1] == "new"
        and argv[2].startswith("-")
        and argv[2] != "--"
    ):
        return argv[:2] + ["--"] + argv[2:]
    return argv


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la CLI `foda`. Ver spec.md para el contrato completo."""
    raw_argv = _protect_dash_prefixed_name(list(sys.argv[1:] if argv is None else argv))

    parser = _build_parser()
    args = parser.parse_args(raw_argv)

    project_root = _find_project_root(Path.cwd())
    if project_root is None:
        print(
            "foda: no se encontro la raiz del proyecto (ningun ancestro "
            "contiene pyproject.toml)",
            file=sys.stderr,
        )
        return 1

    clients_root = project_root / "clients"
    clients_root.mkdir(parents=True, exist_ok=True)

    try:
        created_path = create_client(args.name, clients_root)
    except ValueError as exc:
        print(f"foda: nombre de cliente invalido: {exc}", file=sys.stderr)
        return 1
    except FileExistsError as exc:
        print(f"foda: el cliente ya existe: {exc}", file=sys.stderr)
        return 1

    print(created_path)
    return 0
