"""Punto de entrada de la CLI `foda` (feature client_new_cli, banda tracer_bullet).

Fuente: 600_features/client_new_cli/tracer_bullet/spec.md.

Esqueleto minimo (TDD, caso 1 en rojo): solo la firma publica existe; la
implementacion real (parser argparse, resolucion de raiz, delegacion en
create_client, traduccion a consola) la escribe tdd_coder en la fase verde,
guiada por los casos 1-12 del plan.
"""

from __future__ import annotations


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la CLI `foda`. Ver spec.md para el contrato completo.

    No implementado todavia (fase RED del bucle TDD, caso 1).
    """
    raise NotImplementedError("foda.cli.main aun no implementado (TDD caso 1)")
