"""Tests unitarios de Flow/Artifact/FlowResult (feature flow_base, banda tracer_bullet).

Fuente: 600_features/flow_base/tracer_bullet/spec.md (CA-xx) y plan.md (casos TDD).
Bucle TDD: un test por caso, ejecutado en orden (state.json -> stages.tdd.cases).
"""

from pathlib import Path

import pytest

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowContractError, FlowResult
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


def test_run_con_requires_vacio_pasa_validate_y_completa_las_cuatro_fases(
    tmp_path: Path,
) -> None:
    """Caso 7 (CA-12): un Flow con requires vacio pasa validate(ctx) sin lanzar
    excepcion y run(ctx) completa las 4 fases devolviendo un FlowResult."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    class TrivialFlow(Flow):
        name = "trivial"
        requires: list[Artifact] = []
        produces: list[Artifact] = []

        def __init__(self) -> None:
            self.calls: list[str] = []

        def load_inputs(self, ctx: ClientContext) -> None:
            self.calls.append("load_inputs")

        def validate(self, ctx: ClientContext) -> None:
            self.calls.append("validate")
            super().validate(ctx)

        def execute(self, ctx: ClientContext) -> FlowResult:
            self.calls.append("execute")
            return FlowResult(success=True, outputs=[])

        def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
            self.calls.append("write_outputs")

    flow = TrivialFlow()

    # validate(ctx) no lanza (requires vacio pasa trivialmente).
    flow.validate(ctx)

    result = flow.run(ctx)

    assert isinstance(result, FlowResult)
    assert flow.calls == [
        "validate",
        "load_inputs",
        "validate",
        "execute",
        "write_outputs",
    ]


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


def test_run_sin_override_de_execute_lanza_not_implemented_error(
    tmp_path: Path,
) -> None:
    """Caso 8 (CA-11): una subclase de Flow que NO sobreescribe execute (solo
    hereda el hook base) provoca NotImplementedError al ejecutar run(ctx), pues
    la base no implementa el nucleo (especifico de cada flujo concreto)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    class FlowSinExecute(Flow):
        name = "sin_execute"
        requires: list[Artifact] = []
        produces: list[Artifact] = []

    flow = FlowSinExecute()

    with pytest.raises(NotImplementedError):
        flow.run(ctx)


def test_run_con_require_faltante_lanza_flow_contract_error_antes_de_execute(
    tmp_path: Path,
) -> None:
    """Caso 9 (CA-04): si un Artifact de requires no existe en disco (ruta
    resuelta via ctx), run(ctx) lanza FlowContractError, y el fallo ocurre en
    validate, ANTES de execute (execute no se invoca)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    class FlowConRequireFaltante(Flow):
        name = "con_require_faltante"
        requires: list[Artifact] = [
            Artifact(name="in", base="inputs", relative="010_demo/missing.json")
        ]
        produces: list[Artifact] = []

        def __init__(self) -> None:
            self.execute_invocado = False

        def execute(self, ctx: ClientContext) -> FlowResult:
            self.execute_invocado = True
            return FlowResult(success=True, outputs=[])

        def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
            pass

    flow = FlowConRequireFaltante()

    # El Artifact de requires no fue materializado en disco.
    assert not flow.requires[0].exists(ctx)

    with pytest.raises(FlowContractError):
        flow.run(ctx)

    # El fallo ocurrio en validate, antes de execute: execute no se invoco.
    assert flow.execute_invocado is False


def test_flow_contract_error_es_tipo_propio_y_mensaje_nombra_el_faltante(
    tmp_path: Path,
) -> None:
    """Caso 10 (CA-05): FlowContractError es un tipo de excepcion propio de
    flow.py (subclase de Exception), capturable de forma independiente con
    pytest.raises(FlowContractError), y su mensaje nombra el artefacto
    requerido faltante (su name y/o su ruta resuelta)."""
    assert issubclass(FlowContractError, Exception)

    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    faltante = Artifact(name="in", base="inputs", relative="010_demo/missing.json")

    class FlowConRequireFaltante(Flow):
        name = "con_require_faltante"
        requires: list[Artifact] = [faltante]
        produces: list[Artifact] = []

        def execute(self, ctx: ClientContext) -> FlowResult:
            return FlowResult(success=True, outputs=[])

    flow = FlowConRequireFaltante()

    assert not faltante.exists(ctx)

    with pytest.raises(FlowContractError) as exc_info:
        flow.run(ctx)

    mensaje = str(exc_info.value)
    assert faltante.name in mensaje
    assert str(faltante.path(ctx)) in mensaje
