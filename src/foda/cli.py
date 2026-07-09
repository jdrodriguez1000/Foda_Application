"""Punto de entrada de la CLI `foda`, con tres subcomandos: `client new`
(feature client_new_cli, banda tracer_bullet) y `run` / `status` (feature
flow_orchestrator, banda tracer_bullet).

Fuente: 600_features/client_new_cli/tracer_bullet/spec.md y
600_features/flow_orchestrator/tracer_bullet/spec.md.

Implementacion completa (TDD): parser argparse minimo (delega en argparse el
codigo 2 para argumentos requeridos ausentes o subcomando desconocido),
resolucion de la raiz del proyecto (marcador pyproject.toml) hacia arriba
desde el cwd (D-C) con su fallo controlado (DS-CLI-1: raiz no encontrada ->
stderr + codigo 1, sin tocar disco).

`client new <name>`: asegura clients_root, delega en create_client,
traduccion del camino de exito a consola y traduccion de ValueError (nombre
invalido) / FileExistsError (duplicado) a stderr + codigo 1.

`run <name> --flow <flow>` (DS-ORQ-4): resuelve el flujo via resolve_flow,
construye el ClientContext del cliente existente y despacha a flow.run(ctx),
traduciendo cada fallo (flujo desconocido, cliente inexistente,
FlowContractError) a stderr + codigo 1 antes de escribir salida alguna.
El exit code refleja el resultado del flujo (T-035, ADR D-080 punto 4): 0
solo si el FlowResult tiene success=True; si success=False (camino blando de
inconsistencia de datos, sin excepcion) sale 1 con un mensaje que NO afirma
"completado", para no ocultar el fallo a scripts/CI (L-053).

`status <name>` (DS-ORQ-3): construye el ClientContext y lista, por cada
flujo registrado en FLOWS, sus artefactos requires/produces con un marcador
de presencia en disco, sin efectos en disco.

El entry point del paquete (`foda = "foda.cli:main"`, TSK-01) se declara en
pyproject.toml ([project.scripts]).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from foda.core.context import ClientContext
from foda.core.flow import FlowContractError
from foda.core.scaffold import create_client
from foda.orchestrator import FLOWS, resolve_flow


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

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("name")

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

    if args.command == "status":
        return _dispatch_status(args, clients_root)

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


def _build_client_context(name: str, clients_root: Path) -> ClientContext | None:
    """Construye ClientContext(name, clients_root), traduciendo un cliente
    inexistente (FileNotFoundError) a stderr; usado por _dispatch_run y
    _dispatch_status (mismo estilo DS-CLI-1: fallo controlado, sin
    Traceback). Devuelve None si el cliente no existe, para que el llamador
    retorne codigo 1 sin escribir salida adicional."""
    try:
        return ClientContext(name, clients_root)
    except FileNotFoundError as exc:
        print(f"foda: {exc}", file=sys.stderr)
        return None


def _dispatch_run(args: argparse.Namespace, clients_root: Path) -> int:
    """Despacha `foda run <cliente> --flow <flujo>` (DS-ORQ-4): resuelve el
    flujo (puro, sin disco), construye el ClientContext (lectura del cliente
    existente) y ejecuta flow.run(ctx), traduciendo cada fallo a stderr +
    codigo 1 antes de escribir salida alguna. Tras un flow.run sin excepcion,
    el exit code refleja result.success (T-035): 0 si True, 1 si False."""
    try:
        flow = resolve_flow(args.flow)
    except ValueError as exc:
        print(f"foda: {exc}", file=sys.stderr)
        return 1

    ctx = _build_client_context(args.name, clients_root)
    if ctx is None:
        return 1

    try:
        result = flow.run(ctx)
    except FlowContractError as exc:
        print(f"foda: {exc}", file=sys.stderr)
        return 1

    outputs = ", ".join(str(path) for path in result.outputs)
    if not result.success:
        # T-035 (ADR D-080 punto 4): un flujo que termina sin excepcion pero con
        # success=False (camino blando de inconsistencia de datos) no es un exito;
        # el exit code debe reflejarlo (1) para no ocultar el fallo a scripts/CI
        # que solo chequean el codigo de salida (L-053).
        print(
            f"foda: flujo {args.flow!r} finalizo SIN exito para el cliente "
            f"{args.name!r} (revise el reporte del flujo): {outputs}"
        )
        return 1

    print(f"foda: flujo {args.flow!r} completado para el cliente {args.name!r}: {outputs}")
    return 0


def _dispatch_status(args: argparse.Namespace, clients_root: Path) -> int:
    """Despacha `foda status <cliente>` (DS-ORQ-3): construye el ClientContext
    (lectura del cliente existente) y, por cada flujo registrado en FLOWS,
    lista sus artefactos requires/produces con un marcador de presencia en
    disco (sin efectos en disco, sin leer contenido de artefactos)."""
    ctx = _build_client_context(args.name, clients_root)
    if ctx is None:
        return 1

    for flow_name, flow_cls in FLOWS.items():
        flow = flow_cls()
        print(f"{flow_name}:")
        for role, artifacts in (("requires", flow.requires), ("produces", flow.produces)):
            for artifact in artifacts:
                marker = "[presente]" if artifact.exists(ctx) else "[ausente]"
                relative_path = artifact.path(ctx).relative_to(ctx.root)
                print(f"  {role}  {artifact.name}  {marker}  {relative_path}")

    return 0
