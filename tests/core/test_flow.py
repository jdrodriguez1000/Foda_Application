"""Tests unitarios de Flow/Artifact/FlowResult (feature flow_base, banda tracer_bullet).

Fuente: 600_features/flow_base/tracer_bullet/spec.md (CA-xx) y plan.md (casos TDD).
Bucle TDD: un test por caso, ejecutado en orden (state.json -> stages.tdd.cases).
"""

from pathlib import Path

from foda.core.context import ClientContext
from foda.core.flow import Artifact
from foda.core.scaffold import create_client


def test_artifact_path_y_exists_para_base_outputs(tmp_path: Path) -> None:
    """Caso 1 (CA-10): sobre un ClientContext construido con create_client(...) bajo
    tmp_path, Artifact(name="a", base="outputs", relative=r).path(ctx) ==
    ctx.outputs_dir / r; y Artifact.exists(ctx) refleja la existencia en disco de
    esa ruta (False antes de crearla, True despues de crearla)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    relative = "010_discovery/contract_data.json"
    artifact = Artifact(name="a", base="outputs", relative=relative)

    assert artifact.path(ctx) == ctx.outputs_dir / relative
    assert artifact.exists(ctx) is False

    artifact.path(ctx).parent.mkdir(parents=True)
    artifact.path(ctx).write_text("ok", encoding="utf-8")

    assert artifact.exists(ctx) is True
