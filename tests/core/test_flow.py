"""Tests unitarios de Flow/Artifact/FlowResult (feature flow_base, banda tracer_bullet).

Fuente: 600_features/flow_base/tracer_bullet/spec.md (CA-xx) y plan.md (casos TDD).
Bucle TDD: un test por caso, ejecutado en orden (state.json -> stages.tdd.cases).
"""

from pathlib import Path

import pytest

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowResult
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


@pytest.mark.parametrize(
    ("base", "dir_attr"),
    [
        ("inputs", "inputs_dir"),
        ("outputs", "outputs_dir"),
        ("bronze", "bronze_dir"),
        ("silver", "silver_dir"),
        ("gold", "gold_dir"),
        ("models", "models_dir"),
    ],
)
def test_artifact_path_resuelve_las_seis_claves_base_solo_via_ctx(
    tmp_path: Path, base: str, dir_attr: str
) -> None:
    """Caso 2 (CA-09): para las seis claves base (inputs/outputs/bronze/silver/gold/
    models), Artifact(base=k, relative=r).path(ctx) == ctx.<k>_dir / r; la ruta se
    resuelve exclusivamente via ctx (sin calculo propio de Artifact)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    relative = "010_discovery/archivo.json"
    artifact = Artifact(name="a", base=base, relative=relative)

    assert artifact.path(ctx) == getattr(ctx, dir_attr) / relative


def test_run_heredado_ejecuta_hasta_el_final_y_devuelve_flow_result(
    tmp_path: Path,
) -> None:
    """Caso 3 (CA-01): una subclase trivial de Flow que define solo name/requires/
    produces y sobreescribe UNICAMENTE execute y write_outputs (sin sobreescribir
    run) expone un run(ctx) heredado que se ejecuta hasta el final y devuelve un
    FlowResult, sin contener codigo de orquestacion propio."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    class TrivialFlow(Flow):
        name = "trivial"
        requires: list[Artifact] = []
        produces: list[Artifact] = []

        def execute(self, ctx: ClientContext) -> FlowResult:
            return FlowResult(success=True, outputs=[])

        def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
            pass

    flow = TrivialFlow()
    result = flow.run(ctx)

    assert isinstance(result, FlowResult)


def test_run_invoca_los_cuatro_hooks_en_orden_y_una_vez_cada_uno(
    tmp_path: Path,
) -> None:
    """Caso 4 (CA-02): instrumentando el flujo trivial (registrando cada hook
    invocado en una lista de instancia), una ejecucion completa de run(ctx)
    invoca exactamente load_inputs, validate, execute, write_outputs, en ese
    orden, y una sola vez cada uno."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    class InstrumentedFlow(Flow):
        name = "instrumented"
        requires: list[Artifact] = []
        produces: list[Artifact] = []

        def __init__(self) -> None:
            self.calls: list[str] = []

        def load_inputs(self, ctx: ClientContext) -> None:
            self.calls.append("load_inputs")

        def validate(self, ctx: ClientContext) -> None:
            self.calls.append("validate")

        def execute(self, ctx: ClientContext) -> FlowResult:
            self.calls.append("execute")
            return FlowResult(success=True, outputs=[])

        def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
            self.calls.append("write_outputs")

    flow = InstrumentedFlow()
    flow.run(ctx)

    assert flow.calls == ["load_inputs", "validate", "execute", "write_outputs"]


def test_run_exitoso_devuelve_flow_result_con_success_true(tmp_path: Path) -> None:
    """Caso 5 (CA-07): tras un run(ctx) exitoso sobre el flujo trivial, el
    FlowResult devuelto tiene success == True."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    class TrivialFlow(Flow):
        name = "trivial"
        requires: list[Artifact] = []
        produces: list[Artifact] = []

        def execute(self, ctx: ClientContext) -> FlowResult:
            return FlowResult(success=True, outputs=[])

        def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
            pass

    flow = TrivialFlow()
    result = flow.run(ctx)

    assert result.success is True


def test_run_exitoso_expone_outputs_resueltos_y_existentes_en_disco(
    tmp_path: Path,
) -> None:
    """Caso 6 (CA-08): tras un run(ctx) exitoso, FlowResult.outputs expone las
    rutas resueltas de produces (via Artifact.path(ctx)) y cada una de esas
    rutas existe en disco (materializada por write_outputs del flujo trivial)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    class TrivialFlow(Flow):
        name = "trivial"
        requires: list[Artifact] = []
        produces: list[Artifact] = [
            Artifact(name="out", base="outputs", relative="050_demo/out.json")
        ]

        def execute(self, ctx: ClientContext) -> FlowResult:
            return FlowResult(
                success=True, outputs=[a.path(ctx) for a in self.produces]
            )

        def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
            for artifact in self.produces:
                path = artifact.path(ctx)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding="utf-8")

    flow = TrivialFlow()
    result = flow.run(ctx)

    assert result.outputs == [ctx.outputs_dir / "050_demo/out.json"]
    for output_path in result.outputs:
        assert output_path.exists()
