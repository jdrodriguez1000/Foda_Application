"""Punto de entrada de la CLI `foda` (feature client_new_cli, banda tracer_bullet).

Fuente: 600_features/client_new_cli/tracer_bullet/spec.md.

Implementacion parcial (TDD, casos 1-7 en verde / TSK-02, TSK-03, TSK-04):
parser argparse minimo, resolucion de la raiz del proyecto (marcador
pyproject.toml) hacia arriba desde el cwd (D-C) con su fallo controlado
(DS-CLI-1: raiz no encontrada -> stderr + codigo 1, sin tocar disco),
aseguramiento de clients_root, delegacion en create_client y traduccion del
camino de exito a consola. La traduccion de errores del core (ValueError /
FileExistsError) y los errores de parseo de argparse las agregan los casos
siguientes del bucle TDD (TSK-05).
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


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la CLI `foda`. Ver spec.md para el contrato completo."""
    parser = _build_parser()
    args = parser.parse_args(argv)

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

    created_path = create_client(args.name, clients_root)
    print(created_path)
    return 0
