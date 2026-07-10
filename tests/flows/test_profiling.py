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
