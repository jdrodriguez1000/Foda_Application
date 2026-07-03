"""Tests unitarios de ClientContext (feature client_context, banda tracer_bullet).

Fuente: 600_features/client_context/tracer_bullet/spec.md (CA-xx) y plan.md (casos TDD).
Bucle TDD: un test por caso, ejecutado en orden (state.json -> stages.tdd.cases).
"""

from pathlib import Path

from foda.core.context import ClientContext
from foda.core.scaffold import create_client


def test_client_context_construye_sin_lanzar_y_expone_name_y_root(tmp_path: Path) -> None:
    """Caso 1 (CA-01): sobre un cliente creado con create_client("ABC", tmp/clients),
    ClientContext("ABC", tmp/clients) se construye sin lanzar excepcion y expone
    name == "ABC" y root == tmp/clients/ABC."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)

    ctx = ClientContext("ABC", clients_root)

    assert ctx.name == "ABC"
    assert ctx.root == clients_root / "ABC"
