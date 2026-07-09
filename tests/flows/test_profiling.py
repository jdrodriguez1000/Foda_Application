"""Tests unitarios de Profiling (feature profiling, banda tracer_bullet).

Fuente: 600_features/profiling/tracer_bullet/spec.md (CA-xx) y plan.md
(casos TDD, TSK-01..TSK-08). Bucle TDD: un test por caso, ejecutado en orden
(state.json -> stages.tdd.cases). Este archivo arranca con el caso 1
(CA-01): Profiling es subclase de Flow con name/requires/produces correctos
(DS-PROF-1..4, calcado del patron de Ingestion, ver plan.md Sec.A).
"""

import json
from pathlib import Path

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowResult
from foda.core.scaffold import create_client
from foda.flows.f040_profiling.profiling import Profiling


def test_profiling_es_subclase_de_flow_con_contrato_correcto() -> None:
    """CA-01: Profiling es subclase de Flow, name=="profiling", requires es
    [Artifact ingestion_report @ outputs/030_ingestion/ingestion_report.json]
    y produces es [Artifact profiling_report @
    outputs/040_profiling/profiling_report.json]."""
    assert issubclass(Profiling, Flow)
    assert Profiling.name == "profiling"

    assert Profiling.requires == [
        Artifact(
            name="ingestion_report",
            base="outputs",
            relative="030_ingestion/ingestion_report.json",
        )
    ]
    assert Profiling.produces == [
        Artifact(
            name="profiling_report",
            base="outputs",
            relative="040_profiling/profiling_report.json",
        )
    ]


def _build_ctx_con_ingestion_report_success_true(tmp_path: Path) -> ClientContext:
    """DS-PROF-1..4: ClientContext bajo tmp_path con ingestion_report.json
    (success:true) ya presente bajo ctx.outputs_dir/"030_ingestion" (el unico
    requires de Profiling, caso 1), suficiente para que Flow.validate() base
    no lance FlowContractError y la ejecucion llegue hasta execute()."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "client": "ABC",
                "flow": "ingestion",
                "success": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return ctx


def test_profiling_hereda_run_de_flow_e_invoca_las_4_fases_en_orden(
    tmp_path: Path,
) -> None:
    """Caso 2 (CA-02): Profiling no sobreescribe run() (usa el template
    method heredado de Flow, DS-PROF-1..4 / plan.md Sec.A) y una ejecucion
    real de run(ctx) invoca load_inputs -> validate -> execute ->
    write_outputs en ese orden.

    Se instrumenta la INSTANCIA con spies que delegan a la implementacion
    real de cada hook (no la sustituyen), de modo que el orden registrado
    refleje la ejecucion autentica y no un doble de prueba. Con
    ingestion_report.json (success:true) presente, validate() (heredado de
    Flow) no lanza FlowContractError; execute() aun no esta sobreescrito por
    Profiling (llega en el caso 3, TSK-05) por lo que la llamada real a
    Flow.execute() base lanza NotImplementedError: la ejecucion todavia no
    llega a completarse, evidencia correcta de que la fase de ejecucion no
    existe aun (no es un fallo accidental de import/sintaxis)."""
    ctx = _build_ctx_con_ingestion_report_success_true(tmp_path)

    flow = Profiling()
    calls: list[str] = []

    original_load_inputs = flow.load_inputs
    original_validate = flow.validate
    original_execute = flow.execute
    original_write_outputs = flow.write_outputs

    def spy_load_inputs(ctx: ClientContext) -> None:
        calls.append("load_inputs")
        original_load_inputs(ctx)

    def spy_validate(ctx: ClientContext) -> None:
        calls.append("validate")
        original_validate(ctx)

    def spy_execute(ctx: ClientContext) -> FlowResult:
        calls.append("execute")
        return original_execute(ctx)

    def spy_write_outputs(ctx: ClientContext, result: FlowResult) -> None:
        calls.append("write_outputs")
        original_write_outputs(ctx, result)

    flow.load_inputs = spy_load_inputs  # type: ignore[method-assign]
    flow.validate = spy_validate  # type: ignore[method-assign]
    flow.execute = spy_execute  # type: ignore[method-assign]
    flow.write_outputs = spy_write_outputs  # type: ignore[method-assign]

    assert "run" not in vars(Profiling)
    assert Profiling.run is Flow.run

    result = flow.run(ctx)

    assert calls == ["load_inputs", "validate", "execute", "write_outputs"]
    assert isinstance(result, FlowResult)
