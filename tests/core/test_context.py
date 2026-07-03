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


def test_client_context_expone_inputs_dir_y_outputs_dir(tmp_path: Path) -> None:
    """Caso 2 (CA-05): sobre un cliente creado con create_client("ABC", tmp/clients),
    ClientContext("ABC", tmp/clients) expone inputs_dir == tmp/clients/ABC/010_inputs
    y outputs_dir == tmp/clients/ABC/020_outputs."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)

    ctx = ClientContext("ABC", clients_root)

    assert ctx.inputs_dir == clients_root / "ABC" / "010_inputs"
    assert ctx.outputs_dir == clients_root / "ABC" / "020_outputs"


def test_client_context_expone_bronze_silver_gold_dir(tmp_path: Path) -> None:
    """Caso 3 (CA-06): sobre un cliente creado con create_client("ABC", tmp/clients),
    ClientContext("ABC", tmp/clients) expone bronze_dir, silver_dir y gold_dir bajo
    tmp/clients/ABC/data/{bronze,silver,gold}."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)

    ctx = ClientContext("ABC", clients_root)

    assert ctx.bronze_dir == clients_root / "ABC" / "data" / "bronze"
    assert ctx.silver_dir == clients_root / "ABC" / "data" / "silver"
    assert ctx.gold_dir == clients_root / "ABC" / "data" / "gold"


def test_client_context_expone_models_dir(tmp_path: Path) -> None:
    """Caso 4 (CA-07): sobre un cliente creado con create_client("ABC", tmp/clients),
    ClientContext("ABC", tmp/clients) expone models_dir == tmp/clients/ABC/models."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)

    ctx = ClientContext("ABC", clients_root)

    assert ctx.models_dir == clients_root / "ABC" / "models"


def test_client_context_las_6_rutas_existen_en_disco(tmp_path: Path) -> None:
    """Caso 5 (CA-08): sobre un cliente creado con create_client("ABC", tmp/clients),
    las 6 rutas resueltas por ClientContext (inputs_dir, outputs_dir, bronze_dir,
    silver_dir, gold_dir, models_dir) existen en disco como directorios."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)

    ctx = ClientContext("ABC", clients_root)

    assert ctx.inputs_dir.is_dir()
    assert ctx.outputs_dir.is_dir()
    assert ctx.bronze_dir.is_dir()
    assert ctx.silver_dir.is_dir()
    assert ctx.gold_dir.is_dir()
    assert ctx.models_dir.is_dir()
