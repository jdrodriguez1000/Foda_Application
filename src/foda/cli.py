"""Punto de entrada de la CLI `foda` (feature client_new_cli, banda tracer_bullet).

Fuente: 600_features/client_new_cli/tracer_bullet/spec.md.

Implementacion completa (TDD, casos 1-12 en verde / TSK-01 a TSK-05): parser
argparse minimo (delega en argparse el codigo 2 para NAME ausente o
subcomando desconocido), resolucion de la raiz del proyecto (marcador
pyproject.toml) hacia arriba desde el cwd (D-C) con su fallo controlado
(DS-CLI-1: raiz no encontrada -> stderr + codigo 1, sin tocar disco),
aseguramiento de clients_root, delegacion en create_client, traduccion del
camino de exito a consola y traduccion de ValueError (nombre invalido) /
FileExistsError (duplicado) a stderr + codigo 1. El entry point del paquete
(`foda = "foda.cli:main"`, TSK-01) se declara en pyproject.toml
([project.scripts]).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from foda.core.context import ClientContext
from foda.core.flow import FlowContractError
from foda.core.scaffold import create_client
from foda.orchestrator import resolve_flow


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="foda")
    subparsers = parser.add_subparsers(dest="command")

    client_parser = subparsers.add_parser("client")
    client_subparsers = client_parser.add_subparsers(dest="client_command")

    new_parser = client_subparsers.add_parser("new")
    new_parser.add_argument("name")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("name")
    run_parser.add_argument("--flow", required=True)

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

    if args.command == "run":
        return _dispatch_run(args, clients_root)

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


def _dispatch_run(args: argparse.Namespace, clients_root: Path) -> int:
    """Despacha `foda run <cliente> --flow <flujo>` (DS-ORQ-4): resuelve el
    flujo (puro, sin disco), construye el ClientContext (lectura del cliente
    existente) y ejecuta flow.run(ctx), traduciendo cada fallo a stderr +
    codigo 1 antes de escribir salida alguna."""
    try:
        flow = resolve_flow(args.flow)
    except ValueError as exc:
        print(f"foda: {exc}", file=sys.stderr)
        return 1

    try:
        ctx = ClientContext(args.name, clients_root)
    except FileNotFoundError as exc:
        print(f"foda: {exc}", file=sys.stderr)
        return 1

    try:
        result = flow.run(ctx)
    except FlowContractError as exc:
        print(f"foda: {exc}", file=sys.stderr)
        return 1

    outputs = ", ".join(str(path) for path in result.outputs)
    print(f"foda: flujo {args.flow!r} completado para el cliente {args.name!r}: {outputs}")
    return 0
