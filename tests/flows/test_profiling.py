"""Tests unitarios de Profiling (feature profiling, banda tracer_bullet).

Fuente: 600_features/profiling/tracer_bullet/spec.md (CA-xx) y plan.md
(casos TDD, TSK-01..TSK-08). Bucle TDD: un test por caso, ejecutado en orden
(state.json -> stages.tdd.cases). Este archivo arranca con el caso 1
(CA-01): Profiling es subclase de Flow con name/requires/produces correctos
(DS-PROF-1..4, calcado del patron de Ingestion, ver plan.md Sec.A).
"""

import json
from pathlib import Path

import pytest

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowContractError, FlowResult
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


def test_profiling_run_devuelve_flowresult_success_con_output_profiling_report(
    tmp_path: Path,
) -> None:
    """Caso 3 (CA-03, TSK-04): con ingestion_report.json (success:true)
    presente, Profiling().run(ctx) (ejecucion real y completa del template
    method heredado, sin espias) devuelve un FlowResult cuyo success es
    exactamente True y cuyo outputs es exactamente la lista de un solo
    elemento con la ruta absoluta ctx.outputs_dir/040_profiling/
    profiling_report.json (el unico Artifact declarado en Profiling.produces,
    ver caso 1). Aserciones especificas del caso 3 (no basta con
    isinstance(result, FlowResult) del caso 2): valor exacto de success y de
    outputs."""
    ctx = _build_ctx_con_ingestion_report_success_true(tmp_path)

    result = Profiling().run(ctx)

    expected_output_path = ctx.outputs_dir / "040_profiling/profiling_report.json"
    assert result.success is True
    assert result.outputs == [expected_output_path]


def test_profiling_report_json_en_disco_es_parseable_con_campos_y_serializacion_deterministas(
    tmp_path: Path,
) -> None:
    """Caso 4 (CA-04, TSK-06/TSK-07): tras Profiling().run(ctx) (con
    ingestion_report.json success:true presente, caso 1) el archivo
    ctx.outputs_dir/040_profiling/profiling_report.json existe en disco, es
    JSON parseable con success==True (boolean), schema_version=="0.1",
    client==ctx.name (=="ABC") y flow=="profiling"; y su contenido en disco
    es EXACTAMENTE la serializacion deterministica exigida por la spec
    (DS-PROF-3): json.dumps(<reporte>, ensure_ascii=False, indent=2,
    sort_keys=True) + "\n" byte a byte (claves ordenadas alfabeticamente,
    indentacion de 2 espacios y una unica newline final, sin espacio en
    blanco extra). No basta con que el JSON sea "equivalente" en contenido
    (ya cubierto en espiritu por json.loads()): esta asercion es especifica
    del FORMATO exacto del archivo en disco, distinta de result.success/
    result.outputs ya verificados en el caso 3."""
    ctx = _build_ctx_con_ingestion_report_success_true(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    assert ruta_reporte.exists()

    contenido_bruto = ruta_reporte.read_text(encoding="utf-8")
    reporte = json.loads(contenido_bruto)

    assert reporte["success"] is True
    assert reporte["schema_version"] == "0.1"
    assert reporte["client"] == ctx.name
    assert reporte["flow"] == "profiling"

    contenido_esperado = (
        json.dumps(reporte, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    assert contenido_bruto == contenido_esperado


def test_profiling_validate_sin_ingestion_report_lanza_flowcontracterror_nombrandolo_y_no_escribe_profiling_report(
    tmp_path: Path,
) -> None:
    """Caso 5 (CA-05, TSK-08): sin ingestion_report.json bajo
    ctx.outputs_dir/030_ingestion (el unico Artifact de Profiling.requires,
    caso 1), Profiling().validate(ctx) lanza FlowContractError cuyo mensaje
    nombra especificamente el artefacto ausente ("ingestion_report", no un
    mensaje generico), y una ejecucion real de Profiling().run(ctx) (que
    invoca validate() antes de execute()/write_outputs(), caso 2) propaga esa
    misma excepcion sin llegar a escribir profiling_report.json en disco:
    tras el fallo, ctx.outputs_dir/040_profiling/profiling_report.json NO
    existe.

    Aserciones especificas de este caso (no basta con
    isinstance(exc, FlowContractError), ya cubierto en espiritu por el
    contrato heredado de Flow.validate): el mensaje debe contener el nombre
    exacto del artefacto declarado en Profiling.requires
    ("ingestion_report") y, tras el fallo, el reporte de profiling no debe
    existir en disco (distingue este caso de los casos 3/4, que si escriben
    el reporte tras una ejecucion exitosa)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    ruta_ingestion_report = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    assert not ruta_ingestion_report.exists()

    flow = Profiling()

    with pytest.raises(FlowContractError) as excinfo_validate:
        flow.validate(ctx)
    assert "ingestion_report" in str(excinfo_validate.value)

    with pytest.raises(FlowContractError) as excinfo_run:
        flow.run(ctx)
    assert "ingestion_report" in str(excinfo_run.value)

    ruta_profiling_report = ctx.outputs_dir / "040_profiling/profiling_report.json"
    assert not ruta_profiling_report.exists()
