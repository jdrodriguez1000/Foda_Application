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
    """Caso 4 (CA-04, TSK-06/TSK-07) de tracer_bullet, AJUSTADO por
    stab_1/caso 1 (CA-18, CA-19, TSK-01): tras Profiling().run(ctx) (con
    ingestion_report.json success:true presente, caso 1) el archivo
    ctx.outputs_dir/040_profiling/profiling_report.json existe en disco, es
    JSON parseable con success==True (boolean), schema_version=="0.2"
    (bump aditivo de stab_1, DS-PRF-7 -antes "0.1" en tracer_bullet-),
    client==ctx.name (=="ABC") y flow=="profiling"; y su contenido en disco
    es EXACTAMENTE la serializacion deterministica exigida por la spec
    (DS-PROF-3/DS-PRF-7): json.dumps(<reporte>, ensure_ascii=False, indent=2,
    sort_keys=True) + "\n" byte a byte (claves ordenadas alfabeticamente,
    indentacion de 2 espacios y una unica newline final, sin espacio en
    blanco extra). No basta con que el JSON sea "equivalente" en contenido
    (ya cubierto en espiritu por json.loads()): esta asercion es especifica
    del FORMATO exacto del archivo en disco, distinta de result.success/
    result.outputs ya verificados en el caso 3.

    Este es el UNICO ajuste a un test existente que exige stab_1 (ver
    plan.md, Estrategia de Test): la banda stab_1 cambia el contrato de
    schema_version de forma aditiva pero incompatible con la aserción
    literal "0.1" ya presente. Hoy (antes de tdd_coder) Profiling.execute()
    aun escribe "0.1" (implementacion vigente de tracer_bullet, ver
    profiling.py), por lo que esta aserción falla en rojo limpio hasta que
    TSK-02 suba el schema_version a "0.2"."""
    ctx = _build_ctx_con_ingestion_report_success_true(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    assert ruta_reporte.exists()

    contenido_bruto = ruta_reporte.read_text(encoding="utf-8")
    reporte = json.loads(contenido_bruto)

    assert reporte["success"] is True
    assert reporte["schema_version"] == "0.2"
    assert reporte["client"] == ctx.name
    assert reporte["flow"] == "profiling"

    contenido_esperado = (
        json.dumps(reporte, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    assert contenido_bruto == contenido_esperado


def _build_ctx_con_ingestion_report_todos_sanos(tmp_path: Path, n_files: int = 2) -> ClientContext:
    """stab_1, DS-PRF-3/DS-PRF-7: ClientContext bajo tmp_path con un
    ingestion_report.json de fixture "todos sanos" (ver spec.md, tabla
    "Casos Limite y Errores"): summary.files_declared==n_files, un unico
    dataset con n_files archivos, todos status=="ingested" e
    inconsistencies==[], y la lista top-level inconsistencies==[] (sin
    problemas de ningun tipo). Sigue el esquema DS-ING-2/DS-ING-9 de
    ingestion_report.json (600_features/ingestion/tracer_bullet/spec.md)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    archivos_sanos = [
        {
            "name": f"archivo_{i}.csv",
            "status": "ingested",
            "rows": 10,
            "columns": 3,
            "separator": ",",
            "bronze_path": f"data/bronze/archivo_{i}.csv",
            "inconsistencies": [],
        }
        for i in range(n_files)
    ]

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": True,
        "summary": {"files_declared": n_files},
        "datasets": [{"files": archivos_sanos}],
        "unexpected_files": [],
        "inconsistencies": [],
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_contiene_bloque_health_con_exactamente_6_claves_fixture_todos_sanos(
    tmp_path: Path,
) -> None:
    """Caso 2 (CA-20, CA-17, TSK-03/TSK-04): tras Profiling().run(ctx) con un
    ingestion_report.json de fixture "todos sanos" (ver
    _build_ctx_con_ingestion_report_todos_sanos y spec.md, tabla "Casos
    Limite y Errores": files_declared=N>0, sin inconsistencias),
    profiling_report.json contiene un objeto health cuyas claves son
    EXACTAMENTE las 6 siguientes (ni de mas ni de menos): global_score,
    files_declared, files_healthy, files_with_problems, problems_by_type,
    pareto (DS-PRF-7). Para este fixture "todos sanos" se ancla ademas el
    valor esperado global_score==1.0 y pareto==[] (sin problemas que
    penalicen ni que listar en el ranking).

    Hoy (antes de tdd_coder) Profiling.execute() aun no arma ningun bloque
    health (profiling.py vigente solo produce schema_version/client/flow/
    success), por lo que reporte["health"] lanza KeyError: rojo limpio por
    ausencia de funcionalidad, no por error accidental."""
    ctx = _build_ctx_con_ingestion_report_todos_sanos(tmp_path, n_files=2)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    health = reporte["health"]
    assert set(health.keys()) == {
        "global_score",
        "files_declared",
        "files_healthy",
        "files_with_problems",
        "problems_by_type",
        "pareto",
    }
    assert health["global_score"] == 1.0
    assert health["pareto"] == []


def test_profiling_report_health_files_declared_coincide_con_summary_files_declared(
    tmp_path: Path,
) -> None:
    """Caso 3 (CA-06, DS-PRF-3): tras Profiling().run(ctx) con un
    ingestion_report.json de fixture "todos sanos" cuyo
    summary.files_declared==2 (ver _build_ctx_con_ingestion_report_todos_sanos),
    profiling_report.json['health']['files_declared'] es EXACTAMENTE igual a
    ese valor (2), no un placeholder fijo.

    Hoy (antes de tdd_coder) Profiling.execute() hardcodea
    health.files_declared en 0 (implementacion minima del caso 2, ver
    profiling.py), por lo que esta aserción falla en rojo limpio (0 != 2),
    no por un error accidental de import/sintaxis."""
    ctx = _build_ctx_con_ingestion_report_todos_sanos(tmp_path, n_files=2)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    assert reporte["health"]["files_declared"] == 2


def _build_ctx_con_ingestion_report_mixto(tmp_path: Path) -> ClientContext:
    """stab_1, DS-PRF-3: ClientContext bajo tmp_path con un
    ingestion_report.json de fixture MIXTA (declara 4 archivos, ver spec.md
    "Casos Limite y Errores", fila "Camino feliz parcial"):
    summary.files_declared==4, datasets[0].files con 2 archivos SANOS
    (status=="ingested" e inconsistencies==[]) y 2 archivos NO sanos: uno con
    status!="ingested" ("rejected", inconsistencies==[]) y otro con
    status=="ingested" pero inconsistencies NO vacia. Conteo esperado
    (DS-PRF-3): files_healthy==2, files_with_problems==2. Sigue el esquema
    DS-ING-2/DS-ING-9 de ingestion_report.json
    (600_features/ingestion/tracer_bullet/spec.md), calcado del estilo de
    _build_ctx_con_ingestion_report_todos_sanos."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    archivos = [
        {
            "name": "sano_1.csv",
            "status": "ingested",
            "rows": 10,
            "columns": 3,
            "separator": ",",
            "bronze_path": "data/bronze/sano_1.csv",
            "inconsistencies": [],
        },
        {
            "name": "sano_2.csv",
            "status": "ingested",
            "rows": 8,
            "columns": 3,
            "separator": ",",
            "bronze_path": "data/bronze/sano_2.csv",
            "inconsistencies": [],
        },
        {
            "name": "rechazado.csv",
            "status": "rejected",
            "rows": 0,
            "columns": 0,
            "separator": ",",
            "bronze_path": "data/bronze/rechazado.csv",
            "inconsistencies": [],
        },
        {
            "name": "con_columna_faltante.csv",
            "status": "ingested",
            "rows": 5,
            "columns": 2,
            "separator": ",",
            "bronze_path": "data/bronze/con_columna_faltante.csv",
            "inconsistencies": [{"type": "missing_column", "detail": "falta col x"}],
        },
    ]

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": True,
        "summary": {"files_declared": 4},
        "datasets": [{"files": archivos}],
        "unexpected_files": [],
        "inconsistencies": [{"type": "missing_column", "detail": "falta col x"}],
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_health_files_healthy_coincide_con_conteo_de_archivos_sanos_fixture_mixta(
    tmp_path: Path,
) -> None:
    """Caso 4 (CA-07, DS-PRF-3, TSK-06/TSK-08): tras Profiling().run(ctx) con
    un ingestion_report.json de fixture MIXTA (ver
    _build_ctx_con_ingestion_report_mixto: 4 archivos declarados, 2 sanos
    -status=="ingested" e inconsistencies==[]-, 1 con status=="rejected" y 1
    con inconsistencies no vacia), profiling_report.json['health']
    ['files_healthy'] es EXACTAMENTE 2 (el conteo real de archivos sanos), no
    un placeholder fijo.

    Hoy (antes de tdd_coder) Profiling.execute() hardcodea
    health.files_healthy en 0 (placeholder minimo del caso 2, ver
    profiling.py), por lo que esta aserción falla en rojo limpio (0 != 2, un
    valor distinto de 0 y del total declarado), no por un error accidental de
    import/sintaxis."""
    ctx = _build_ctx_con_ingestion_report_mixto(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    assert reporte["health"]["files_healthy"] == 2


def test_profiling_report_health_files_with_problems_coincide_con_conteo_de_archivos_con_problemas_fixture_mixta(
    tmp_path: Path,
) -> None:
    """stab_1, caso 5 (CA-08, DS-PRF-3, TSK-07/TSK-08): tras
    Profiling().run(ctx) con la fixture MIXTA (ver
    _build_ctx_con_ingestion_report_mixto: 4 archivos declarados, 2 sanos
    -status=="ingested" e inconsistencies==[]-, 1 con status!="ingested"
    ("rejected") y 1 con status=="ingested" pero inconsistencies NO vacia),
    profiling_report.json['health']['files_with_problems'] es EXACTAMENTE 2
    (el conteo real de archivos con problemas: status!="ingested" O
    inconsistencies!=[]), no un placeholder fijo.

    Hoy (antes de tdd_coder) Profiling.execute() hardcodea
    health.files_with_problems en 0 (placeholder minimo heredado del caso 2,
    ver profiling.py), por lo que esta aserción falla en rojo limpio (0 != 2,
    un valor distinto de 0), no por un error accidental de import/sintaxis."""
    ctx = _build_ctx_con_ingestion_report_mixto(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    assert reporte["health"]["files_with_problems"] == 2


def test_profiling_report_health_cumple_invariante_files_healthy_mas_files_with_problems_igual_files_declared(
    tmp_path: Path,
) -> None:
    """stab_1, caso 6 (CA-09, DS-PRF-3, TSK-09): tras Profiling().run(ctx) con
    la fixture MIXTA (ver _build_ctx_con_ingestion_report_mixto: 4 archivos
    declarados, 2 sanos, 1 con status!="ingested" y 1 con inconsistencies no
    vacia), se cumple la invariante
    health['files_healthy'] + health['files_with_problems'] ==
    health['files_declared'] (2 + 2 == 4): los archivos declarados quedan
    particionados exactamente entre sanos y con problemas, sin residuo ni
    doble conteo (DS-PRF-3: "los unexpected_file no rompen la identidad
    porque no entran en ninguno de los tres terminos").

    Nota (NC-6, plan.md Sec. "Cases sin tarea-codigo propia"): este caso NO
    tiene tarea-codigo propia asignada a tdd_coder (TSK-09 es solo test). Los
    casos 4 (TSK-06/TSK-08) y 5 (TSK-07/TSK-08) ya implementaron
    _contar_archivos_sanos/_contar_archivos_con_problemas como predicados
    complementarios (De Morgan) sobre la misma particion de
    datasets[].files[], por lo que la invariante que aqui se verifica es una
    CONSECUENCIA matematica directa de esa implementacion ya construida, no
    una funcionalidad nueva. Se documenta explicitamente (NC-1/NC-6) que este
    test se ejecuta y pasa en VERDE de inmediato (sin que tdd_coder deba
    escribir codigo de produccion): es un test de CONFIRMACION del invariante
    ya garantizado por construccion (files_healthy y files_with_problems
    particionan exactamente el mismo iterable _archivos(ingestion_report)
    via predicados mutuamente excluyentes y exhaustivos), y su valor esta en
    dejar el invariante explicito y protegido de regresiones futuras. No es
    un rojo accidental invalido: es la excepcion pre-aprobada por el humano
    en el gate de plan_builder (plan.md, casos "sin tarea-codigo propia") para
    este caso especifico; si en el futuro una refactorizacion rompiera la
    particion exacta, este test pasaria a fallar y detectaria la regresion."""
    ctx = _build_ctx_con_ingestion_report_mixto(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    health = reporte["health"]
    assert health["files_healthy"] + health["files_with_problems"] == health["files_declared"]


def _build_ctx_con_ingestion_report_inconsistencias_variadas(tmp_path: Path) -> ClientContext:
    """stab_1, caso 7 (CA-11, DS-PRF-4): ClientContext bajo tmp_path con un
    ingestion_report.json cuya lista top-level inconsistencies[] mezcla los
    4 tipos del vocabulario cerrado con conteos DISTINTOS entre si y >1 para
    al menos uno (missing_file: 2, unexpected_file: 1, missing_column: 3,
    unexpected_column: 0), de forma que una implementacion que solo pase el
    fixture "todos ceros" (caso 8) o un placeholder {} no pueda acertar por
    casualidad: exige realmente contar ocurrencias por type sobre la lista
    top-level inconsistencies[] (DS-PRF-4), no sobre datasets[].files[]
    (fuente distinta, DS-PRF-3, ya cubierta en casos 3-6). files_declared/
    datasets[].files[] se dejan minimos y no relacionados con este conteo:
    este caso no verifica files_healthy/files_with_problems."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    inconsistencias = (
        [{"type": "missing_file", "detail": f"falta archivo {i}"} for i in range(2)]
        + [{"type": "unexpected_file", "detail": "archivo sobrante"}]
        + [{"type": "missing_column", "detail": f"falta columna {i}"} for i in range(3)]
    )

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": True,
        "summary": {"files_declared": 0},
        "datasets": [],
        "unexpected_files": [],
        "inconsistencies": inconsistencias,
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_health_problems_by_type_tiene_las_4_claves_fijas_con_conteos_correctos_de_inconsistencies_top_level(
    tmp_path: Path,
) -> None:
    """stab_1, caso 7 (CA-11, DS-PRF-4, TSK-10/TSK-11): tras
    Profiling().run(ctx) con un ingestion_report.json cuya lista top-level
    inconsistencies[] mezcla los 4 tipos del vocabulario cerrado con
    conteos variados (ver
    _build_ctx_con_ingestion_report_inconsistencias_variadas: missing_file=2,
    unexpected_file=1, missing_column=3, unexpected_column=0),
    profiling_report.json['health']['problems_by_type'] es EXACTAMENTE un
    dict con las 4 claves fijas missing_file/unexpected_file/missing_column/
    unexpected_column, cada una un int>=0 igual al nº de ocurrencias de ese
    type en esa lista top-level (no en datasets[].files[], fuente distinta
    ya cubierta en los casos 3-6).

    Hoy (antes de tdd_coder) Profiling.execute() hardcodea
    health.problems_by_type en {} (placeholder minimo del caso 2, ver
    profiling.py), por lo que health['problems_by_type']['missing_file']
    lanza KeyError: rojo limpio por ausencia de funcionalidad (el conteo
    real aun no existe), no por un error accidental de import/sintaxis."""
    ctx = _build_ctx_con_ingestion_report_inconsistencias_variadas(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    problems_by_type = reporte["health"]["problems_by_type"]
    assert set(problems_by_type.keys()) == {
        "missing_file",
        "unexpected_file",
        "missing_column",
        "unexpected_column",
    }
    assert problems_by_type == {
        "missing_file": 2,
        "unexpected_file": 1,
        "missing_column": 3,
        "unexpected_column": 0,
    }


def test_profiling_report_health_problems_by_type_tiene_las_4_claves_en_cero_fixture_sin_inconsistencias(
    tmp_path: Path,
) -> None:
    """stab_1, caso 8 (CA-12, DS-PRF-4, TSK-12): tras Profiling().run(ctx) con
    la fixture "todos sanos" (ver _build_ctx_con_ingestion_report_todos_sanos:
    lista top-level inconsistencies==[], sin problemas de ningun tipo),
    profiling_report.json['health']['problems_by_type'] es EXACTAMENTE un
    dict con las 4 claves fijas missing_file/unexpected_file/missing_column/
    unexpected_column, TODAS con valor 0 (esquema estable y completo incluso
    sin inconsistencias que contar, DS-PRF-4: "las claves con cero
    ocurrencias se incluyen igualmente").

    Nota (NC-1/NC-6, plan.md Sec. "Cases sin tarea-codigo propia"): TSK-12 es
    la unica tarea de este caso y es de tipo test (no hay tarea-codigo
    asignada a tdd_coder para el caso 8). El caso 7 (TSK-10/TSK-11) ya
    implemento Profiling._problems_by_type(ingestion_report), que inicializa
    las 4 claves fijas en 0 antes de iterar la lista top-level
    inconsistencies[] sumando ocurrencias; con una lista vacia (fixture "todos
    sanos"), el resultado es necesariamente {todas las claves: 0} por
    construccion, sin codigo nuevo. Se documenta explicitamente (NC-1/NC-6)
    que este test se ejecuta y pasa en VERDE de inmediato: es un test de
    CONFIRMACION del contrato ya garantizado por la implementacion del caso 7
    (la inicializacion a 0 de las 4 claves), no una funcionalidad nueva. No es
    un rojo accidental invalido ni una decision silenciosa: es la excepcion
    pre-aprobada por el humano en el gate de plan_builder (plan.md, casos
    "sin tarea-codigo propia", que lista explicitamente el caso 8) para este
    caso especifico; su valor esta en dejar el contrato de esquema completo
    (4 claves siempre presentes, incluso en 0) protegido de regresiones
    futuras."""
    ctx = _build_ctx_con_ingestion_report_todos_sanos(tmp_path, n_files=2)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    problems_by_type = reporte["health"]["problems_by_type"]
    assert problems_by_type == {
        "missing_file": 0,
        "unexpected_file": 0,
        "missing_column": 0,
        "unexpected_column": 0,
    }


def test_profiling_report_health_global_score_es_float_en_rango_0_1_fixture_mixta(
    tmp_path: Path,
) -> None:
    """stab_1, caso 9 (CA-01, DS-PRF-2, TSK-13): tras Profiling().run(ctx) con
    la fixture MIXTA (ver _build_ctx_con_ingestion_report_mixto: 4 archivos
    declarados, 2 sanos y 2 con problemas, con una inconsistencia top-level
    missing_column), profiling_report.json['health']['global_score'] es
    EXACTAMENTE un valor de tipo float y cae dentro del rango cerrado
    [0.0, 1.0] (CA-01). Este caso NO exige el valor exacto de la formula
    ponderada (eso es CA-02, caso 10, con su propia ancla 0.875): solo el
    tipo y el rango del campo, condicion necesaria previa a verificar la
    formula completa.

    Nota (NC-1/NC-6, plan.md Sec. "Cases sin tarea-codigo propia"): TSK-13
    es la unica tarea de este caso y es de tipo test (no hay tarea-codigo
    asignada a tdd_coder para el caso 9, plan.md lista explicitamente el
    caso 9 en esa seccion). Profiling.execute() aun deja
    health.global_score como placeholder fijo 1.0 (heredado del caso 2, ver
    profiling.py): 1.0 es de tipo float y pertenece a [0.0, 1.0], por lo que
    esta aserción PASA EN VERDE DE INMEDIATO incluso con la fixture MIXTA
    (no la trivial "todos sanos" del caso 2), sin que se necesite escribir
    ningun codigo de produccion nuevo. No es un rojo accidental invalido:
    es la excepcion pre-aprobada por el humano en el gate de plan_builder
    para este caso especifico (igual que los casos 6 y 8); su valor esta en
    dejar el contrato de tipo/rango de global_score protegido de
    regresiones futuras (p. ej. si una implementacion futura de la formula
    ponderada -caso 10- devolviera un int, un valor negativo o mayor que
    1.0, este test lo detectaria)."""
    ctx = _build_ctx_con_ingestion_report_mixto(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    global_score = reporte["health"]["global_score"]
    assert isinstance(global_score, float)
    assert 0.0 <= global_score <= 1.0


def test_profiling_report_health_global_score_coincide_con_formula_ponderada_ancla_0_875(
    tmp_path: Path,
) -> None:
    """stab_1, caso 10 (CA-02, DS-PRF-2, TSK-14): tras Profiling().run(ctx)
    con la fixture MIXTA (ver _build_ctx_con_ingestion_report_mixto:
    files_declared==4, y la lista top-level inconsistencies[] con exactamente
    1 ocurrencia de missing_column, resto de tipos en 0 -ver
    problems_by_type ya verificado en el caso 7-), profiling_report.json
    ['health']['global_score'] es EXACTAMENTE igual al valor que produce la
    formula ponderada de DS-PRF-2:

        penalizacion_total = Sum(peso[tipo] * problems_by_type[tipo])
                            = 1.0*0 + 0.5*1 + 0.3*0 + 0.1*0 = 0.5
        global_score = round(max(0.0, 1.0 - penalizacion_total/files_declared), 4)
                     = round(max(0.0, 1.0 - 0.5/4), 4)
                     = round(0.875, 4) = 0.875

    Esta es la ancla numerica exacta de la spec (spec.md, tabla "Casos
    Limite y Errores", fila "Camino feliz parcial", y CA-02: "1
    missing_column sobre files_declared=4 => 0.875").

    Motivo del rojo esperado (no accidental): Profiling.execute() todavia
    deja health.global_score como placeholder fijo 1.0 (heredado del caso 2
    y confirmado sin cambios en el caso 9); con la fixture MIXTA
    1.0 != 0.875, por lo que la asercion de igualdad exacta debe fallar por
    valor incorrecto, no por ImportError/AttributeError/KeyError (el bloque
    health y la clave global_score ya existen desde los casos 2 y 9)."""
    ctx = _build_ctx_con_ingestion_report_mixto(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    assert reporte["health"]["global_score"] == 0.875


def _build_ctx_con_ingestion_report_penalizacion_excede_files_declared(
    tmp_path: Path,
) -> ClientContext:
    """stab_1, caso 11 (CA-03, DS-PRF-2): ClientContext bajo tmp_path con un
    ingestion_report.json cuya penalizacion_total pondera por encima de
    files_declared (ancla sugerida en plan.md, Estrategia de Test):
    files_declared=1, lista top-level inconsistencies[] con missing_file=1 y
    unexpected_file=2 (pesos DS-PRF-2: missing_file=1.0, unexpected_file=0.3)
    => penalizacion_total = 1.0*1 + 0.3*2 = 1.6 > files_declared=1, de forma
    que 1.0 - 1.6/1 = -0.6 < 0.0 y el clamp inferior max(0.0, ...) debe
    forzar global_score a 0.0 (CA-03) en vez de un valor negativo.
    datasets[]/files[] se dejan vacios: este caso no verifica
    files_healthy/files_with_problems (ya cubiertos en casos 4-6)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    inconsistencias = [
        {"type": "missing_file", "detail": "falta archivo 1"},
        {"type": "unexpected_file", "detail": "archivo sobrante 1"},
        {"type": "unexpected_file", "detail": "archivo sobrante 2"},
    ]

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": True,
        "summary": {"files_declared": 1},
        "datasets": [],
        "unexpected_files": [],
        "inconsistencies": inconsistencias,
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_health_global_score_es_0_0_cuando_penalizacion_total_excede_files_declared_clamp(
    tmp_path: Path,
) -> None:
    """stab_1, caso 11 (CA-03, DS-PRF-2, TSK-16/TSK-17): tras
    Profiling().run(ctx) con un ingestion_report.json cuya penalizacion_total
    pondera por encima de files_declared (ver
    _build_ctx_con_ingestion_report_penalizacion_excede_files_declared:
    files_declared=1, missing_file=1, unexpected_file=2 =>
    penalizacion_total = 1.0*1 + 0.3*2 = 1.6 > 1), profiling_report.json
    ['health']['global_score'] es EXACTAMENTE 0.0 (clamp inferior), no un
    valor negativo (1.0 - 1.6/1 = -0.6 sin clamp).

    Motivo del rojo esperado (no accidental): Profiling._global_score(...)
    (ver profiling.py, caso 10) todavia no aplica el clamp inferior
    max(0.0, ...) sobre el resultado de la formula ponderada, por lo que con
    esta fixture devuelve el valor negativo -0.6 en vez de 0.0; la asercion
    de igualdad exacta debe fallar por valor incorrecto (-0.6 != 0.0), no por
    ImportError/AttributeError/KeyError (el bloque health y la clave
    global_score ya existen desde los casos 2, 9 y 10)."""
    ctx = _build_ctx_con_ingestion_report_penalizacion_excede_files_declared(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    assert reporte["health"]["global_score"] == 0.0


def _build_ctx_con_ingestion_report_files_declared_cero(tmp_path: Path) -> ClientContext:
    """stab_1, caso 12 (CA-04, DS-PRF-2): ClientContext bajo tmp_path con un
    ingestion_report.json cuyo summary.files_declared==0 (borde: ningun
    archivo declarado), y una inconsistencia top-level presente (missing_file
    x1, peso 1.0) para que, si la formula ponderada se aplicara sin la guarda
    del borde, penalizacion_total/files_declared dividiria por cero
    (ZeroDivisionError) en vez de devolver 1.0 directamente (CA-04, DS-PRF-2:
    'si files_declared == 0 -> 1.0'). datasets[]/files[] se dejan vacios: este
    caso no verifica files_healthy/files_with_problems (ya cubiertos en casos
    4-6)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    inconsistencias = [
        {"type": "missing_file", "detail": "falta archivo 1"},
    ]

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": True,
        "summary": {"files_declared": 0},
        "datasets": [],
        "unexpected_files": [],
        "inconsistencies": inconsistencias,
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_health_global_score_es_1_0_cuando_files_declared_es_cero_borde_sin_division_por_cero(
    tmp_path: Path,
) -> None:
    """stab_1, caso 12 (CA-04, DS-PRF-2, TSK-18/TSK-19): tras
    Profiling().run(ctx) con un ingestion_report.json cuyo
    summary.files_declared==0 (ver
    _build_ctx_con_ingestion_report_files_declared_cero: 0 archivos
    declarados, con una inconsistencia top-level missing_file presente),
    profiling_report.json['health']['global_score'] es EXACTAMENTE 1.0 (borde
    explicito de DS-PRF-2: 'si files_declared == 0 -> 1.0'), sin lanzar
    ZeroDivisionError ni ninguna otra excepcion, pese a existir una
    inconsistencia que en cualquier otro caso restaria del score.

    Motivo del rojo esperado (no accidental, sujeto a confirmacion): si
    Profiling._global_score(...) (ver profiling.py) no aplicara la guarda
    files_declared==0 antes de dividir por files_declared, la ejecucion
    lanzaria ZeroDivisionError (fallo por excepcion no capturada, no por
    ImportError/AttributeError/KeyError, ya que el bloque health y la clave
    global_score existen desde los casos 2, 9 y 10)."""
    ctx = _build_ctx_con_ingestion_report_files_declared_cero(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    assert reporte["health"]["global_score"] == 1.0


def _build_ctx_con_ingestion_report_division_no_exacta(tmp_path: Path) -> ClientContext:
    """stab_1, caso 13 (CA-05, DS-PRF-2): ClientContext bajo tmp_path con un
    ingestion_report.json cuya division penalizacion_total/files_declared NO
    es exacta a 4 decimales, para que el redondeo round(x,4) de DS-PRF-2 sea
    observable: files_declared=3, lista top-level inconsistencies[] con
    exactamente 1 ocurrencia de missing_column (peso 0.5, resto de tipos en
    0) => penalizacion_total=0.5, 1.0 - 0.5/3 == 0.8333333333333334 (decimal
    periodico, float sin redondear), que round(...,4) deja en EXACTAMENTE
    0.8333. Sin el round(x,4), el valor comparado por igualdad estricta
    (0.8333333333333334) no coincidiria con el ancla 0.8333: el test es
    discriminante respecto del redondeo, no solo de la formula (ya cubierta
    por el caso 10). datasets[]/files[] se dejan vacios: este caso no
    verifica files_healthy/files_with_problems (ya cubiertos en casos 4-6)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    inconsistencias = [
        {"type": "missing_column", "detail": "columna faltante 1"},
    ]

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": True,
        "summary": {"files_declared": 3},
        "datasets": [],
        "unexpected_files": [],
        "inconsistencies": inconsistencias,
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_health_global_score_redondeado_a_4_decimales_y_deterministico_para_entradas_identicas(
    tmp_path: Path,
) -> None:
    """stab_1, caso 13 (CA-05, DS-PRF-2, TSK-20): tras Profiling().run(ctx)
    con un ingestion_report.json cuya division no es exacta a 4 decimales
    (ver _build_ctx_con_ingestion_report_division_no_exacta: files_declared=3,
    missing_column=1 => penalizacion_total=0.5, 1.0-0.5/3==
    0.8333333333333334 sin redondear),
    profiling_report.json['health']['global_score'] es EXACTAMENTE 0.8333
    (round(x,4) de DS-PRF-2/CA-05), NO el float largo sin redondear. Ademas,
    dos ejecuciones independientes con la misma entrada (dos ClientContext
    distintos construidos con la misma fixture, dos llamadas separadas a
    Profiling().run(ctx)) producen exactamente el mismo valor de
    global_score (determinismo exigido por CA-05: 'dos entradas identicas
    dan exactamente el mismo valor').

    Motivo del rojo esperado (no accidental, sujeto a confirmacion): si
    Profiling._global_score(...) (ver profiling.py, caso 10) NO aplicara
    round(...,4) sobre el resultado de la formula ponderada, la primera
    aserción de igualdad estricta fallaria por valor incorrecto (float largo
    0.8333333333333334 != ancla 0.8333 redondeada a 4 decimales), no por
    ImportError/AttributeError/KeyError (el bloque health y la clave
    global_score existen desde los casos 2, 9 y 10)."""
    ctx_1 = _build_ctx_con_ingestion_report_division_no_exacta(tmp_path / "run_1")
    ctx_2 = _build_ctx_con_ingestion_report_division_no_exacta(tmp_path / "run_2")

    Profiling().run(ctx_1)
    Profiling().run(ctx_2)

    ruta_reporte_1 = ctx_1.outputs_dir / "040_profiling/profiling_report.json"
    ruta_reporte_2 = ctx_2.outputs_dir / "040_profiling/profiling_report.json"
    reporte_1 = json.loads(ruta_reporte_1.read_text(encoding="utf-8"))
    reporte_2 = json.loads(ruta_reporte_2.read_text(encoding="utf-8"))

    assert reporte_1["health"]["global_score"] == 0.8333
    assert reporte_2["health"]["global_score"] == reporte_1["health"]["global_score"]


def _build_ctx_con_ingestion_report_con_unexpected_files(tmp_path: Path) -> ClientContext:
    """stab_1, caso 14 (CA-10, DS-PRF-3/DS-PRF-4): ClientContext bajo
    tmp_path con un ingestion_report.json cuyo summary.files_declared==2
    (2 archivos SANOS en datasets[0].files, status=="ingested" e
    inconsistencies==[]) y, ADEMAS, 2 archivos "unexpected_file"
    (sobrantes no declarados): reflejados en la lista informativa top-level
    unexpected_files[] (contrato de ingestion, DS-ING-9) y, sobre todo, con
    2 entradas type=="unexpected_file" en la lista top-level
    inconsistencies[] (fuente canonica de problems_by_type, DS-PRF-4, igual
    que missing_file/missing_column en los casos 7/10). Un archivo sobrante
    NO es un archivo declarado (DS-PRF-3: 'los unexpected_file NO son
    archivos declarados: no cuentan en files_declared'), por lo que
    summary.files_declared se deja fijo en 2 (no en 4), pese a que hay 2
    archivos sanos + 2 sobrantes en el filesystem simulado."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    archivos_declarados_sanos = [
        {
            "name": "sano_1.csv",
            "status": "ingested",
            "rows": 10,
            "columns": 3,
            "separator": ",",
            "bronze_path": "data/bronze/sano_1.csv",
            "inconsistencies": [],
        },
        {
            "name": "sano_2.csv",
            "status": "ingested",
            "rows": 8,
            "columns": 3,
            "separator": ",",
            "bronze_path": "data/bronze/sano_2.csv",
            "inconsistencies": [],
        },
    ]

    inconsistencias = [
        {"type": "unexpected_file", "detail": "archivo sobrante 1"},
        {"type": "unexpected_file", "detail": "archivo sobrante 2"},
    ]

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": True,
        "summary": {"files_declared": 2},
        "datasets": [{"files": archivos_declarados_sanos}],
        "unexpected_files": ["sobrante_1.csv", "sobrante_2.csv"],
        "inconsistencies": inconsistencias,
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_health_unexpected_file_no_incrementa_files_declared_pero_aporta_a_problems_by_type_y_reduce_global_score(
    tmp_path: Path,
) -> None:
    """stab_1, caso 14 (CA-10, DS-PRF-3/DS-PRF-4, TSK-22, test-only): tras
    Profiling().run(ctx) con un ingestion_report.json con >=1
    unexpected_file (ver _build_ctx_con_ingestion_report_con_unexpected_files:
    summary.files_declared==2, 2 archivos declarados sanos, y 2 entradas
    type=="unexpected_file" en la lista top-level inconsistencies[]), se
    cumplen las 3 aserciones de CA-10 simultaneamente sobre el MISMO
    profiling_report.json:

    (a) health.files_declared == 2 (EXACTAMENTE el valor de
        summary.files_declared, NO 4): los 2 archivos sobrantes NO
        incrementan files_declared (DS-PRF-3, ya ratificado por el caso 3,
        pero aqui bajo presencia real de unexpected_file, no solo por
        ausencia de ellos).
    (b) health.problems_by_type["unexpected_file"] == 2 (EXACTAMENTE el
        conteo real de esas 2 entradas top-level, DS-PRF-4, mismo mecanismo
        que missing_file/missing_column ya verificado en el caso 7 pero
        anclado especificamente al tipo unexpected_file).
    (c) health.global_score < 1.0 (el peso 0.3 de unexpected_file, DS-PRF-2,
        penaliza el score: round(max(0.0, 1.0 - 0.3*2/2), 4) == 0.7, ancla
        exacta que se verifica ademas del "< 1.0" generico).

    Nota (NC-1/NC-6, plan.md linea 62 TSK-22 y linea 117 caso 14): segun
    plan.md este caso tiene UNICAMENTE TSK-22 (tarea de tipo test), SIN
    tarea-codigo propia asociada (no hay una TSK-2x de tipo "Codigo" para
    CA-10 en la tabla de plan.md). Se ejecuto el test tal como esta escrito
    contra el profiling.py vigente (sin ningun cambio de produccion) y
    PASO EN VERDE DE INMEDIATO: Profiling.execute() ya lee files_declared
    exclusivamente de summary.files_declared (caso 3/DS-PRF-3, sin tocar
    datasets[].files[] ni unexpected_files[] para ese conteo),
    Profiling._problems_by_type ya cuenta type=="unexpected_file" sobre la
    lista top-level inconsistencies[] igual que cualquier otro tipo del
    vocabulario cerrado (caso 7/DS-PRF-4, sin trato especial ni exclusion),
    y Profiling._global_score ya pondera unexpected_file con su peso 0.3
    dentro de la formula generica (caso 10/DS-PRF-2). Las 3 aserciones de
    CA-10 son, por tanto, consecuencia directa de logica YA CONSTRUIDA y
    generica en los casos 3/7/10 (que nunca trataron unexpected_file como
    caso especial, sino como un tipo mas del vocabulario cerrado), no una
    funcionalidad nueva: no hay codigo que escribir para este caso, siguiendo
    el precedente documentado en los casos 6/8/9/11/12/13 (excepcion
    pre-aprobada por el humano en el gate de plan_builder). Se deja el test
    como CONFIRMACION/guardia de regresion especifica de CA-10 (detectaria,
    por ejemplo, que una futura refactorizacion empezara a sumar
    unexpected_file a files_declared, o a excluirlo por error de
    problems_by_type/global_score). Se recomienda saltar tdd_coder para este
    caso y pasar directo a tdd_refactor, igual que en los casos
    6/8/9/11/12/13; queda a decision de la sesion principal."""
    ctx = _build_ctx_con_ingestion_report_con_unexpected_files(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    health = reporte["health"]
    assert health["files_declared"] == 2
    assert health["problems_by_type"]["unexpected_file"] == 2
    assert health["global_score"] == 0.7
    assert health["global_score"] < 1.0


def test_profiling_report_health_pareto_es_lista_vacia_fixture_sin_inconsistencias(
    tmp_path: Path,
) -> None:
    """stab_1, caso 15 (CA-17, DS-PRF-5, TSK-23, test-only): tras
    Profiling().run(ctx) con la fixture "todos sanos" (ver
    _build_ctx_con_ingestion_report_todos_sanos: lista top-level
    inconsistencies==[], sin problemas de ningun tipo),
    profiling_report.json['health']['pareto'] == [] (sin entradas, porque no
    hay ningun tipo de inconsistencia con count>=1 que rankear).

    Nota (NC-1/NC-6, plan.md linea 63 TSK-23 y linea 79 "Cases sin
    tarea-codigo propia", que lista explicitamente el caso 15): TSK-23 es la
    UNICA tarea de este caso y es de tipo test (no hay tarea-codigo asignada
    a tdd_coder para el caso 15; la tarea-codigo que arma el bloque health
    completo para el camino "todos sanos", incluido pareto=[], es TSK-04 del
    caso 2, ya "done"). Se ejecuto el test tal como esta escrito contra el
    profiling.py vigente (sin ningun cambio de produccion) y PASO EN VERDE DE
    INMEDIATO: Profiling.execute() (linea 149) todavia deja
    health["pareto"] como el literal fijo [] (placeholder minimo desde el
    caso 2, documentado explicitamente en su propio docstring como pendiente
    "hasta sus propios casos (15-19)"), y ese literal cumple CA-17 por
    construccion para CUALQUIER ingestion_report, no solo para el "todos
    sanos" de este caso -- es decir, el placeholder actual no es capaz aun
    de discriminar entre "sin inconsistencias" (donde pareto==[] es
    correcto) y "con inconsistencias" (donde pareto==[] seria INCORRECTO,
    ver caso 16/CA-15). Por eso este test especifico, aislado con su propia
    fixture "todos sanos", SI es geninamente discriminante del contrato
    CA-17 (detectaria una regresion si una futura implementacion de pareto
    dejara de devolver [] cuando no hay inconsistencias), aunque no
    discrimina "placeholder" de "logica real" -- esa distincion la cubriran
    los casos 16-19, que exigiran contenido no vacio y forzaran la
    implementacion real de _pareto(problems_by_type). No es un rojo
    accidental invalido ni una decision silenciosa: es la excepcion
    pre-aprobada por el humano en el gate de plan_builder (plan.md, casos
    "sin tarea-codigo propia"), mismo patron que los casos 6/8/9/11/12/13/14.
    Se recomienda saltar tdd_coder para este caso y pasar directo a
    tdd_refactor; queda a decision de la sesion principal."""
    ctx = _build_ctx_con_ingestion_report_todos_sanos(tmp_path, n_files=2)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    assert reporte["health"]["pareto"] == []


def _build_ctx_con_ingestion_report_inconsistencias_para_pareto(tmp_path: Path) -> ClientContext:
    """stab_1, caso 16 (CA-15, DS-PRF-5): ClientContext bajo tmp_path con un
    ingestion_report.json cuya lista top-level inconsistencies[] tiene
    ocurrencias reales de AL MENOS 2 tipos distintos del vocabulario cerrado
    con count>=1 (missing_file=2, missing_column=3), dejando los otros 2
    tipos (unexpected_file, unexpected_column) en count==0 (DS-PRF-4), para
    poder verificar que health.pareto NO incluye entradas para los tipos en
    0 (CA-15) y que la suma de los counts de pareto no pierde informacion
    respecto a problems_by_type. files_declared/datasets[].files[] se dejan
    minimos y no relacionados con este conteo (igual que en la fixture del
    caso 7, _build_ctx_con_ingestion_report_inconsistencias_variadas)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    inconsistencias = (
        [{"type": "missing_file", "detail": f"falta archivo {i}"} for i in range(2)]
        + [{"type": "missing_column", "detail": f"falta columna {i}"} for i in range(3)]
    )

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": True,
        "summary": {"files_declared": 0},
        "datasets": [],
        "unexpected_files": [],
        "inconsistencies": inconsistencias,
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_health_pareto_incluye_solo_tipos_con_count_mayor_igual_1_y_suma_de_counts_igual_a_suma_de_problems_by_type(
    tmp_path: Path,
) -> None:
    """stab_1, caso 16 (CA-15, DS-PRF-5, TSK-24/TSK-25): tras
    Profiling().run(ctx) con un ingestion_report.json cuya lista top-level
    inconsistencies[] tiene ocurrencias reales de 2 tipos distintos del
    vocabulario cerrado (ver
    _build_ctx_con_ingestion_report_inconsistencias_para_pareto:
    missing_file=2, missing_column=3, resto de tipos -unexpected_file,
    unexpected_column- en 0), profiling_report.json['health']['pareto']
    cumple (CA-15):

    (a) contiene ENTRADAS SOLO para los tipos con count>=1 (missing_file,
        missing_column): ningun tipo con count==0 (unexpected_file,
        unexpected_column) aparece en pareto, aunque las 4 claves si
        aparecen siempre en problems_by_type (DS-PRF-4, ya verificado en el
        caso 7).
    (b) Σ(entrada['count'] for entrada in pareto) ==
        Σ(problems_by_type.values()) (5 == 2+3+0+0): sin perdida de
        informacion entre problems_by_type y pareto.

    Motivo del rojo esperado (no accidental): Profiling.execute() todavia
    deja health.pareto como el literal fijo [] (placeholder heredado del
    caso 2, confirmado sin cambios en el caso 15 para la fixture "todos
    sanos"); con esta fixture problems_by_type tiene 2 tipos con count>=1
    (missing_file=2, missing_column=3), por lo que pareto==[] NO satisface
    (a) (debe tener 2 entradas, no 0) ni (b) (Σ(pareto[].count)==0 !=
    Σ(problems_by_type.values())==5): fallo por valor/contenido incorrecto,
    no por ImportError/AttributeError/KeyError (el bloque health, la clave
    pareto y problems_by_type ya existen desde los casos 2, 7 y 15)."""
    ctx = _build_ctx_con_ingestion_report_inconsistencias_para_pareto(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    health = reporte["health"]
    problems_by_type = health["problems_by_type"]
    pareto = health["pareto"]

    tipos_en_pareto = {entrada["type"] for entrada in pareto}
    assert tipos_en_pareto == {"missing_file", "missing_column"}
    for tipo_en_cero in ("unexpected_file", "unexpected_column"):
        assert tipo_en_cero not in tipos_en_pareto

    assert sum(entrada["count"] for entrada in pareto) == sum(
        problems_by_type.values()
    )


def _build_ctx_con_ingestion_report_inconsistencias_para_pct(tmp_path: Path) -> ClientContext:
    """stab_1, caso 17 (CA-16, DS-PRF-5): ClientContext bajo tmp_path con un
    ingestion_report.json cuya lista top-level inconsistencies[] produce,
    deliberadamente, un total NO divisible exacto (missing_file=1,
    missing_column=2 => Σ=3), para que pct=round(count/Σ,4) de un decimal
    periodico (1/3=0.3333..., 2/3=0.6666...) y el round(.,4) sea realmente
    discriminante: si execute() no redondeara (o no calculara pct en
    absoluto), el valor no coincidiria con la ancla exacta de 4 decimales.
    Resto de tipos (unexpected_file, unexpected_column) en count==0, para
    reconfirmar (igual que el caso 16) que no aparecen en pareto.
    files_declared/datasets[].files[] se dejan minimos y no relacionados con
    este conteo (igual que en la fixture del caso 16)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    inconsistencias = (
        [{"type": "missing_file", "detail": "falta archivo 0"}]
        + [{"type": "missing_column", "detail": f"falta columna {i}"} for i in range(2)]
    )

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": True,
        "summary": {"files_declared": 0},
        "datasets": [],
        "unexpected_files": [],
        "inconsistencies": inconsistencias,
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_health_pareto_cada_entrada_tiene_type_count_pct_con_pct_igual_a_round_count_sobre_total_4(
    tmp_path: Path,
) -> None:
    """stab_1, caso 17 (CA-16, DS-PRF-5, TSK-26/TSK-27): tras
    Profiling().run(ctx) con un ingestion_report.json cuya lista top-level
    inconsistencies[] produce un total no divisible exacto (ver
    _build_ctx_con_ingestion_report_inconsistencias_para_pct: missing_file=1,
    missing_column=2, Σ(problems_by_type.values())==3),
    profiling_report.json['health']['pareto'] cumple (CA-16):

    (a) cada entrada tiene EXACTAMENTE las 3 claves type/count/pct (ni de
        mas ni de menos).
    (b) 'type' es str, 'count' es int >= 1 (ya cubierto en espiritu por el
        caso 16, se reconfirma aqui con los tipos exactos).
    (c) 'pct' es float e IGUAL a round(count/Σ(problems_by_type.values()),4):
        para missing_file (count=1) pct==round(1/3,4)==0.3333; para
        missing_column (count=2) pct==round(2/3,4)==0.6667. Al ser un
        decimal periodico, esta ancla es genuinamente discriminante del
        round(.,4): un pct sin redondear (0.3333333333333333) o ausente NO
        pasaria esta asercion.

    Motivo del rojo esperado (no accidental): Profiling._pareto(...)
    (src/foda/flows/f040_profiling/profiling.py, caso 16) construye hoy cada
    entrada de pareto SOLO con las claves {type, count} (list comprehension
    literal, sin 'pct'); por lo tanto cada entrada de pareto carece de la
    clave 'pct' -> KeyError al acceder a entrada['pct'], no
    ImportError/AttributeError accidental (el bloque health, la clave
    pareto, problems_by_type y las claves type/count de cada entrada ya
    existen desde los casos 2, 7 y 16)."""
    ctx = _build_ctx_con_ingestion_report_inconsistencias_para_pct(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    health = reporte["health"]
    problems_by_type = health["problems_by_type"]
    pareto = health["pareto"]
    total = sum(problems_by_type.values())

    assert len(pareto) == 2
    for entrada in pareto:
        assert set(entrada.keys()) == {"type", "count", "pct"}
        assert isinstance(entrada["type"], str)
        assert isinstance(entrada["count"], int) and entrada["count"] >= 1
        assert isinstance(entrada["pct"], float)
        assert entrada["pct"] == round(entrada["count"] / total, 4)

    entradas_por_tipo = {entrada["type"]: entrada for entrada in pareto}
    assert entradas_por_tipo["missing_file"]["pct"] == 0.3333
    assert entradas_por_tipo["missing_column"]["pct"] == 0.6667


def _build_ctx_con_ingestion_report_counts_distintos_para_orden_pareto(
    tmp_path: Path,
) -> ClientContext:
    """stab_1, caso 18 (CA-13, DS-PRF-5): ClientContext bajo tmp_path con un
    ingestion_report.json cuya lista top-level inconsistencies[] produce, a
    proposito, 4 counts DISTINTOS entre si (missing_file=1,
    unexpected_file=2, missing_column=4, unexpected_column=3) elegidos para
    que el orden descendente por count esperado (missing_column=4,
    unexpected_column=3, unexpected_file=2, missing_file=1) sea distinto, en
    las 4 posiciones, del orden natural de _TIPOS_INCONSISTENCIA (vocabulario
    fijo missing_file, unexpected_file, missing_column, unexpected_column):
    el test es asi genuinamente discriminante de un ordenamiento real por
    count desc, no solo de la presencia de las entradas (ya cubierta desde
    el caso 16). files_declared/datasets[].files[] se dejan minimos y no
    relacionados con este conteo (igual que en las fixtures de los casos
    16-17)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    inconsistencias = (
        [{"type": "missing_file", "detail": "falta archivo 0"}]
        + [{"type": "unexpected_file", "detail": f"archivo inesperado {i}"} for i in range(2)]
        + [{"type": "missing_column", "detail": f"falta columna {i}"} for i in range(4)]
        + [{"type": "unexpected_column", "detail": f"columna inesperada {i}"} for i in range(3)]
    )

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": True,
        "summary": {"files_declared": 0},
        "datasets": [],
        "unexpected_files": [],
        "inconsistencies": inconsistencias,
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_health_pareto_ordenado_por_count_descendente_orden_distinto_del_vocabulario(
    tmp_path: Path,
) -> None:
    """stab_1, caso 18 (CA-13, DS-PRF-5, TSK-28): tras Profiling().run(ctx)
    con un ingestion_report.json cuyos 4 tipos tienen counts distintos entre
    si (ver _build_ctx_con_ingestion_report_counts_distintos_para_orden_pareto:
    missing_file=1, unexpected_file=2, missing_column=4,
    unexpected_column=3), profiling_report.json['health']['pareto'] queda
    ORDENADO por 'count' de mayor a menor (CA-13):

    (a) [e["count"] for e in pareto] es una secuencia NO creciente (cada
        elemento >= al siguiente).
    (b) los valores concretos esperados, en orden, son [4, 3, 2, 1]
        (missing_column, unexpected_column, unexpected_file, missing_file):
        el orden descendente por count difiere, en las 4 posiciones, del
        orden natural del vocabulario cerrado (missing_file, unexpected_file,
        missing_column, unexpected_column) con el que Profiling._pareto
        itera problems_by_type.items() hoy, haciendo la ancla genuinamente
        discriminante de un ordenamiento real (no de una coincidencia con el
        orden del dict).

    Motivo del rojo esperado (no accidental): Profiling._pareto(...)
    (src/foda/flows/f040_profiling/profiling.py, casos 16-17) construye hoy
    la lista de entradas iterando problems_by_type.items() SIN ordenar, por
    lo que el orden resultante es el orden de insercion del dict (el mismo
    de _TIPOS_INCONSISTENCIA: missing_file, unexpected_file, missing_column,
    unexpected_column), dando counts_en_pareto==[1, 2, 4, 3] en vez de
    [4, 3, 2, 1]: fallo de valor/orden, no ImportError/AttributeError/
    KeyError (el bloque health, pareto y sus claves type/count/pct ya
    existen desde los casos 2, 7, 16 y 17)."""
    ctx = _build_ctx_con_ingestion_report_counts_distintos_para_orden_pareto(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    health = reporte["health"]
    pareto = health["pareto"]

    counts_en_pareto = [entrada["count"] for entrada in pareto]

    assert counts_en_pareto == sorted(counts_en_pareto, reverse=True)
    assert counts_en_pareto == [4, 3, 2, 1]
    assert [entrada["type"] for entrada in pareto] == [
        "missing_column",
        "unexpected_column",
        "unexpected_file",
        "missing_file",
    ]


def _build_ctx_con_ingestion_report_empate_de_count_para_desempate_pareto(
    tmp_path: Path,
) -> ClientContext:
    """stab_1, caso 19 (CA-14, DS-PRF-5): ClientContext bajo tmp_path con un
    ingestion_report.json cuya lista top-level inconsistencies[] produce, a
    proposito, un EMPATE de count entre dos tipos (missing_file=5,
    missing_column=5) y dos tipos restantes con counts distintos y menores
    (unexpected_column=3, unexpected_file=1), elegidos para que el desempate
    alfabetico ascendente por 'type' (CA-14: missing_column < missing_file)
    sea DISTINTO del orden de insercion de _TIPOS_INCONSISTENCIA (vocabulario
    fijo missing_file, unexpected_file, missing_column, unexpected_column,
    donde missing_file aparece ANTES que missing_column): el test es asi
    genuinamente discriminante de un desempate alfabetico real, no de la
    estabilidad del sort() sobre el orden del vocabulario (que produciria
    missing_file antes que missing_column, el orden incorrecto). Los otros
    dos tipos (unexpected_column=3, unexpected_file=1) quedan con counts
    unicos y menores que el empate, de forma que el bloque empatado ocupa
    inequivocamente las 2 primeras posiciones del ranking por count
    descendente (ya cubierto por el caso 18) y el resto del orden no
    interfiere con la aserción del desempate. files_declared/
    datasets[].files[] se dejan minimos y no relacionados con este conteo
    (igual que en las fixtures de los casos 16-18)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    inconsistencias = (
        [{"type": "missing_file", "detail": f"falta archivo {i}"} for i in range(5)]
        + [{"type": "missing_column", "detail": f"falta columna {i}"} for i in range(5)]
        + [{"type": "unexpected_column", "detail": f"columna inesperada {i}"} for i in range(3)]
        + [{"type": "unexpected_file", "detail": "archivo inesperado 0"}]
    )

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": True,
        "summary": {"files_declared": 0},
        "datasets": [],
        "unexpected_files": [],
        "inconsistencies": inconsistencias,
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_health_pareto_ante_empate_de_count_desempata_por_type_alfabetico_ascendente(
    tmp_path: Path,
) -> None:
    """stab_1, caso 19 (CA-14, DS-PRF-5, TSK-29/TSK-30): tras
    Profiling().run(ctx) con un ingestion_report.json cuyos counts producen
    un empate entre dos tipos (ver
    _build_ctx_con_ingestion_report_empate_de_count_para_desempate_pareto:
    missing_file=5, missing_column=5 empatados en el TOPE del ranking;
    unexpected_column=3, unexpected_file=1 sin empate),
    profiling_report.json['health']['pareto'] queda ordenado, en caso de
    empate de 'count', por 'type' alfabetico ASCENDENTE (CA-14):

    (a) los counts en pareto siguen no crecientes (invariante ya cubierto
        por el caso 18): [5, 5, 3, 1].
    (b) dentro del bloque empatado (los dos primeros elementos, ambos
        count==5), el orden exacto es ["missing_column", "missing_file"]
        (alfabetico ascendente), NO ["missing_file", "missing_column"] (el
        orden de insercion de _TIPOS_INCONSISTENCIA que produciria un sort
        estable sin desempate explicito).
    (c) la secuencia completa de 'type' en pareto es EXACTAMENTE
        ["missing_column", "missing_file", "unexpected_column",
        "unexpected_file"].

    Motivo del rojo esperado (no accidental): Profiling._pareto(...)
    (src/foda/flows/f040_profiling/profiling.py, caso 18) ordena hoy con
    sorted(entradas, key=lambda entrada: -entrada["count"]), SIN clave de
    desempate por 'type'; al ser sorted() estable, un empate de count
    preserva el orden de insercion previo (el orden de
    problems_by_type.items(), igual al de _TIPOS_INCONSISTENCIA: missing_file
    antes que missing_column), por lo que el bloque empatado sale como
    ["missing_file", "missing_column"] en vez de ["missing_column",
    "missing_file"]: fallo de valor/orden en la asercion de la secuencia
    completa de 'type', no ImportError/AttributeError/KeyError (el bloque
    health, pareto y sus claves type/count/pct ya existen desde los casos 2,
    7, 16, 17 y 18)."""
    ctx = _build_ctx_con_ingestion_report_empate_de_count_para_desempate_pareto(tmp_path)

    Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    health = reporte["health"]
    pareto = health["pareto"]

    counts_en_pareto = [entrada["count"] for entrada in pareto]
    tipos_en_pareto = [entrada["type"] for entrada in pareto]

    assert counts_en_pareto == [5, 5, 3, 1]
    assert tipos_en_pareto == [
        "missing_column",
        "missing_file",
        "unexpected_column",
        "unexpected_file",
    ]


def _build_ctx_con_ingestion_report_determinismo_pareto_completo(
    tmp_path: Path,
) -> ClientContext:
    """stab_1, caso 20 (CA-21, DS-PRF-7, TSK-32): ClientContext bajo
    tmp_path con un ingestion_report.json de fixture "con inconsistencias
    reales" disenada para ejercitar TODO el bloque health (no solo
    global_score/pareto de forma trivial):

    - summary.files_declared==5, datasets[0].files con 5 archivos
      declarados: 2 SANOS (status=="ingested" e inconsistencies==[]) y 3
      con problemas (2 con status=="rejected", 1 status=="ingested" pero
      con inconsistencies no vacia), de forma que files_healthy==2 y
      files_with_problems==3 (DS-PRF-3, mismo patron que la fixture MIXTA
      de los casos 4-6).
    - lista top-level inconsistencies[] con los 4 tipos del vocabulario
      cerrado en counts variados y con un EMPATE deliberado
      (missing_file=4, missing_column=4, unexpected_file=2,
      unexpected_column=0), para que problems_by_type tenga las 4 claves
      con valores no triviales y pareto deba ejercitar el filtro
      count>=1, el calculo de pct, el orden por count descendente Y el
      desempate alfabetico ascendente (DS-PRF-5, CA-13/CA-14/CA-15/CA-16)
      en un unico fixture, calcado del patron de las fixtures de los casos
      16-19 (_build_ctx_con_ingestion_report_counts_distintos_para_orden_pareto/
      _empate_de_count_para_desempate_pareto).

    global_score resultante (DS-PRF-2, no exacto por division, ejercita
    tambien el redondeo a 4 decimales del caso 13):
    penalizacion_total = 1.0*4 + 0.3*2 + 0.5*4 + 0.1*0 = 4.0+0.6+2.0 = 6.6
    score = round(max(0.0, 1.0 - 6.6/5), 4) = round(max(0.0, -0.32), 4) = 0.0
    (clamp inferior, caso 11, tambien ejercitado)."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    archivos = [
        {
            "name": "sano_1.csv",
            "status": "ingested",
            "rows": 10,
            "columns": 3,
            "separator": ",",
            "bronze_path": "data/bronze/sano_1.csv",
            "inconsistencies": [],
        },
        {
            "name": "sano_2.csv",
            "status": "ingested",
            "rows": 8,
            "columns": 3,
            "separator": ",",
            "bronze_path": "data/bronze/sano_2.csv",
            "inconsistencies": [],
        },
        {
            "name": "rechazado_1.csv",
            "status": "rejected",
            "rows": 0,
            "columns": 0,
            "separator": ",",
            "bronze_path": "data/bronze/rechazado_1.csv",
            "inconsistencies": [],
        },
        {
            "name": "rechazado_2.csv",
            "status": "rejected",
            "rows": 0,
            "columns": 0,
            "separator": ",",
            "bronze_path": "data/bronze/rechazado_2.csv",
            "inconsistencies": [],
        },
        {
            "name": "con_columna_faltante.csv",
            "status": "ingested",
            "rows": 5,
            "columns": 2,
            "separator": ",",
            "bronze_path": "data/bronze/con_columna_faltante.csv",
            "inconsistencies": [{"type": "missing_column", "detail": "falta col x"}],
        },
    ]

    inconsistencias = (
        [{"type": "missing_file", "detail": f"falta archivo {i}"} for i in range(4)]
        + [{"type": "missing_column", "detail": f"falta columna {i}"} for i in range(4)]
        + [{"type": "unexpected_file", "detail": f"archivo sobrante {i}"} for i in range(2)]
    )

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": True,
        "summary": {"files_declared": 5},
        "datasets": [{"files": archivos}],
        "unexpected_files": ["sobrante_1.csv", "sobrante_2.csv"],
        "inconsistencies": inconsistencias,
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_dos_ejecuciones_con_mismo_ingestion_report_producen_profiling_report_byte_identico(
    tmp_path: Path,
) -> None:
    """stab_1, caso 20 (CA-21, DS-PRF-7, TSK-32): dos Profiling().run(ctx)
    independientes, cada una sobre su propio ClientContext (arboles de
    directorios separados bajo tmp_path/"run_1" y tmp_path/"run_2", mismo
    patron que el test de determinismo del caso 13), pero alimentadas con
    EL MISMO ingestion_report.json de fixture (ver
    _build_ctx_con_ingestion_report_determinismo_pareto_completo: 5 archivos
    declarados con mezcla de sanos/con-problemas y una lista top-level
    inconsistencies[] con los 4 tipos, incluido un EMPATE de count entre
    missing_file y missing_column), producen un profiling_report.json cuyo
    contenido en disco es EXACTAMENTE byte-idéntico entre ambas ejecuciones
    (CA-21): se leen los bytes crudos (read_bytes(), no el JSON parseado)
    de cada profiling_report.json y se comparan con igualdad estricta.

    El fixture ejercita simultaneamente TODO el bloque health (no solo un
    campo trivial): files_declared/files_healthy/files_with_problems desde
    la mezcla de datasets[].files[], las 4 claves de problems_by_type desde
    la lista top-level inconsistencies[], global_score con clamp inferior
    (penalizacion_total=6.6 > files_declared=5) y, sobre todo, pareto con
    multiples entradas (filtro count>=1, pct, orden por count descendente Y
    desempate alfabetico ascendente ante el empate deliberado
    missing_file==missing_column==4): si el determinismo dependiera de
    cualquier fuente de no-determinismo real (orden de iteracion de dict no
    fijado, hash aleatorio de sets/frozensets, timestamps, ids de objeto,
    etc.) en cualquiera de esos calculos, este test lo detectaria como una
    diferencia de bytes entre las dos ejecuciones.

    Motivo esperado (NC-1/NC-6, plan.md linea 79, 'Cases sin tarea-codigo
    propia', que lista explicitamente el caso 20): segun el plan, el
    determinismo NO tiene tarea-codigo propia (TSK-32 es unicamente de tipo
    test): lo garantiza la serializacion determinista ya existente y
    verificada de Flow.write_outputs() (json.dumps(..., ensure_ascii=False,
    indent=2, sort_keys=True) + '\\n', confirmada byte a byte en el caso 1)
    combinada con el orden fijo de pareto ya implementado y verificado en
    los casos 18-19 (sorted(entradas, key=lambda e: (-e['count'],
    e['type']))), mas la ausencia de cualquier fuente de aleatoriedad/estado
    mutable compartido en execute()/los helpers privados del modulo (todos
    puros, sin cache ni variables de modulo mutables). Se ejecuto el test
    tal como esta escrito contra el profiling.py vigente (sin ningun cambio
    de produccion) y PASO EN VERDE DE INMEDIATO: no es un rojo accidental
    invalido ni una decision silenciosa, es la excepcion pre-aprobada por el
    humano en el gate de plan_builder para este caso especifico (mismo
    patron que los casos 6/8/9/11/12/13/14/15). Se recomienda saltar
    tdd_coder para este caso (no hay codigo que escribir) y pasar directo a
    tdd_refactor; queda a decision de la sesion principal."""
    ctx_1 = _build_ctx_con_ingestion_report_determinismo_pareto_completo(tmp_path / "run_1")
    ctx_2 = _build_ctx_con_ingestion_report_determinismo_pareto_completo(tmp_path / "run_2")

    Profiling().run(ctx_1)
    Profiling().run(ctx_2)

    ruta_reporte_1 = ctx_1.outputs_dir / "040_profiling/profiling_report.json"
    ruta_reporte_2 = ctx_2.outputs_dir / "040_profiling/profiling_report.json"

    bytes_reporte_1 = ruta_reporte_1.read_bytes()
    bytes_reporte_2 = ruta_reporte_2.read_bytes()

    assert bytes_reporte_1 == bytes_reporte_2

    reporte_1 = json.loads(bytes_reporte_1.decode("utf-8"))
    health = reporte_1["health"]
    assert health["files_declared"] == 5
    assert health["files_healthy"] == 2
    assert health["files_with_problems"] == 3
    assert health["problems_by_type"] == {
        "missing_file": 4,
        "unexpected_file": 2,
        "missing_column": 4,
        "unexpected_column": 0,
    }
    assert health["global_score"] == 0.0
    assert [entrada["type"] for entrada in health["pareto"]] == [
        "missing_column",
        "missing_file",
        "unexpected_file",
    ]


def _build_ctx_con_ingestion_report_success_false(tmp_path: Path) -> ClientContext:
    """stab_1, caso 21 (CA-22, DS-PRF-6): ClientContext bajo tmp_path con un
    ingestion_report.json cuyo campo top-level success es EXACTAMENTE False
    (el flujo predecesor ingestion fallo), pero con datos validos y no
    triviales para ejercitar el bloque health completo (calcado del estilo
    de _build_ctx_con_ingestion_report_mixto): summary.files_declared==3,
    datasets[0].files con 1 archivo sano (status=="ingested",
    inconsistencies==[]) y 2 archivos con problemas (uno status=="rejected",
    otro status=="ingested" con inconsistencies no vacia), y la lista
    top-level inconsistencies[] con 2 ocurrencias de missing_file (DS-PRF-4).
    DS-PRF-6 ratifica que Profiling calcula la salud igual sobre estos datos
    disponibles, sin que el success==false de ingestion lo altere."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    archivos = [
        {
            "name": "sano_1.csv",
            "status": "ingested",
            "rows": 10,
            "columns": 3,
            "separator": ",",
            "bronze_path": "data/bronze/sano_1.csv",
            "inconsistencies": [],
        },
        {
            "name": "rechazado.csv",
            "status": "rejected",
            "rows": 0,
            "columns": 0,
            "separator": ",",
            "bronze_path": "data/bronze/rechazado.csv",
            "inconsistencies": [],
        },
        {
            "name": "con_archivo_faltante.csv",
            "status": "ingested",
            "rows": 5,
            "columns": 2,
            "separator": ",",
            "bronze_path": "data/bronze/con_archivo_faltante.csv",
            "inconsistencies": [{"type": "missing_file", "detail": "referencia rota"}],
        },
    ]

    ingestion_report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": False,
        "summary": {"files_declared": 3},
        "datasets": [{"files": archivos}],
        "unexpected_files": [],
        "inconsistencies": [
            {"type": "missing_file", "detail": "falta archivo 1"},
            {"type": "missing_file", "detail": "falta archivo 2"},
        ],
    }

    report_path = ctx.outputs_dir / "030_ingestion/ingestion_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(ingestion_report, ensure_ascii=False),
        encoding="utf-8",
    )
    return ctx


def test_profiling_report_con_ingestion_success_false_no_lanza_y_reporte_tiene_success_true_con_health_calculado(
    tmp_path: Path,
) -> None:
    """stab_1, caso 21 (CA-22, DS-PRF-6, TSK-33): con un ingestion_report.json
    cuyo success es EXACTAMENTE False pero con datos validos y no triviales
    (ver _build_ctx_con_ingestion_report_success_false: files_declared=3, 1
    archivo sano, 2 con problemas, 2 ocurrencias top-level de missing_file),
    Profiling().run(ctx):

    (a) NO lanza ninguna excepcion (la llamada se completa con normalidad).
    (b) devuelve un FlowResult cuyo success es EXACTAMENTE True (el
        success de profiling_report refleja la ejecucion del propio flujo
        Profiling, independiente del success de ingestion, DS-PRF-6).
    (c) el profiling_report.json escrito en disco tiene success == true
        (bool, no el string "true").
    (d) el bloque health esta calculado sobre los datos disponibles, no
        vacio ni degradado por el success==false de ingestion:
        files_declared==3, files_healthy==1, files_with_problems==2,
        problems_by_type['missing_file']==2 (resto de tipos en 0),
        global_score==round(max(0.0, 1.0 - 1.0*2/3), 4)==0.3333 (formula
        ponderada real, DS-PRF-2, peso missing_file=1.0), y pareto tiene
        exactamente 1 entrada {'type':'missing_file','count':2,
        'pct':1.0} (unico tipo con count>=1, DS-PRF-5).

    Motivo esperado (NC-1/NC-6): revisado
    src/foda/flows/f040_profiling/profiling.py completo (execute(), casos
    1-19): Profiling.execute() nunca lee self._ingestion_report['success']
    en ningun punto (ni para condicionar el FlowResult ni para alterar el
    calculo de health); FlowResult(success=True, ...) es un literal
    incondicional (linea 166) y files_declared/files_healthy/
    files_with_problems/problems_by_type/global_score/pareto se derivan
    unicamente de summary.files_declared, datasets[].files[] y la lista
    top-level inconsistencies[] (DS-PRF-2..5), fuentes todas independientes
    del campo success del ingestion_report de entrada. Se ejecuto el test
    tal como esta escrito contra el profiling.py vigente (sin ningun cambio
    de produccion) y PASO EN VERDE DE INMEDIATO: no es un rojo accidental
    invalido ni una decision silenciosa, es la misma excepcion pre-aprobada
    por el humano en el gate de plan_builder que ya se documento en los
    casos 6/8/9/11/12/13/14/15/20 (logica generica ya construida en casos
    previos que satisface por construccion un caso confirmatorio posterior).
    Se recomienda saltar tdd_coder para este caso (no hay codigo que
    escribir) y pasar directo a tdd_refactor; queda a decision de la sesion
    principal."""
    ctx = _build_ctx_con_ingestion_report_success_false(tmp_path)

    result = Profiling().run(ctx)

    assert result.success is True

    ruta_reporte = ctx.outputs_dir / "040_profiling/profiling_report.json"
    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))

    assert reporte["success"] is True

    health = reporte["health"]
    assert health["files_declared"] == 3
    assert health["files_healthy"] == 1
    assert health["files_with_problems"] == 2
    assert health["problems_by_type"] == {
        "missing_file": 2,
        "unexpected_file": 0,
        "missing_column": 0,
        "unexpected_column": 0,
    }
    assert health["global_score"] == 0.3333
    assert health["pareto"] == [{"type": "missing_file", "count": 2, "pct": 1.0}]


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
