"""Suite de tests de la CLI del gate de progresion entre flujos (feature
profiling, banda tracer_bullet). Independiente de
tests/cli/test_flow_orchestrator_cli.py y tests/cli/test_client_new_cli.py:
no comparte fixtures (no hay conftest.py en tests/cli/), no importa nada de
esos modulos y no muta estado de proceso fuera de tmp_path/monkeypatch
(aislados por test via pytest). Invoca `main(argv)` en proceso, bajo un
proyecto+cliente temporal, mismo patron que test_flow_orchestrator_cli.py.

Fuente: 600_features/profiling/tracer_bullet/spec.md (DS-PROF-1..4,
CA-06..CA-13) y plan.md (Sec. "Estrategia de Test").
Bucle TDD: un test por caso, ejecutado en orden (state.json -> stages.tdd.cases).
"""

import json
from pathlib import Path

import pytest


def _seed_cliente_abc(tmp_path: Path) -> Path:
    """Crea <tmp_path>/clients/ABC/ con client.yaml (marcador de existencia
    que exige ClientContext). No siembra contract_data.json ni
    ingestion_report.json: cada test los fabrica segun lo que necesite
    verificar. Devuelve la raiz del proyecto (tmp_path)."""
    client_dir = tmp_path / "clients" / "ABC"
    client_dir.mkdir(parents=True)
    (client_dir / "client.yaml").write_text("name: ABC\n", encoding="utf-8")
    return tmp_path


def _fabricar_ingestion_report(tmp_path: Path, *, success: bool) -> Path:
    """Fabrica clients/ABC/020_outputs/030_ingestion/ingestion_report.json
    minimo (schema_version/client/flow/success), sin correr Ingestion real
    (aislamiento de unidad, mismo patron que test_orchestrator.py). Devuelve
    la ruta del reporte fabricado."""
    report_path = (
        tmp_path
        / "clients"
        / "ABC"
        / "020_outputs"
        / "030_ingestion"
        / "ingestion_report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "ingestion",
        "success": success,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


@pytest.fixture
def proyecto(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture comun a todos los tests de esta suite: crea <tmp_path>/
    pyproject.toml (marcador de raiz de proyecto que _find_project_root
    busca) y fija el cwd del proceso en tmp_path via monkeypatch.chdir.
    Devuelve tmp_path (la raiz del proyecto)."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_run_profiling_con_ingestion_report_success_true_sin_force_devuelve_0_y_escribe_reporte(
    tmp_path: Path, proyecto: Path, capsys
):
    """Caso 11 (CA-06, TSK-19/TSK-20): con ingestion_report.json (success:true)
    presente y SIN --force, main(["run","ABC","--flow","profiling"]) debe
    devolver 0, stdout debe contener un mensaje de completado (analogo al ya
    exigido para onboarding en test_flow_orchestrator_cli.py, caso 5:
    'profiling' + 'ABC' + el nombre del artefacto producido), y
    profiling_report.json debe existir en disco bajo
    020_outputs/040_profiling/. Ejercita el wiring del gate en la CLI
    (TSK-20: _dispatch_run debe llamar evaluate_predecessor_gate antes de
    flow.run); el flujo profiling ya esta registrado en FLOWS (caso 6,
    orchestrator.py) y evaluate_predecessor_gate ya evalua correctamente esta
    rama (caso 8, orchestrator.py), asi que el rojo esperado, si lo hay,
    proviene unicamente de la CLI, no del orquestador ni del flujo."""
    from foda.cli import main

    _seed_cliente_abc(proyecto)
    _fabricar_ingestion_report(proyecto, success=True)

    result = main(["run", "ABC", "--flow", "profiling"])

    assert result == 0
    captured = capsys.readouterr()
    assert "profiling" in captured.out
    assert "ABC" in captured.out
    assert "completado" in captured.out
    assert "profiling_report.json" in captured.out

    profiling_report = (
        tmp_path
        / "clients"
        / "ABC"
        / "020_outputs"
        / "040_profiling"
        / "profiling_report.json"
    )
    assert profiling_report.exists()


def test_run_profiling_con_ingestion_report_success_false_sin_force_devuelve_1_y_no_escribe_nada(
    tmp_path: Path, proyecto: Path, capsys
):
    """Caso 12 (CA-07/CA-08, TSK-21): con ingestion_report.json (success:false)
    presente y SIN --force, main(["run","ABC","--flow","profiling"]) debe
    devolver 1, stderr debe nombrar tanto al predecesor 'ingestion' como el
    motivo del bloqueo (el reporte no tiene success == true; el gate ya
    produce ese mensaje exacto, caso 9, orchestrator.py), y no debe existir
    NINGUN artefacto bajo 020_outputs/040_profiling/ (ni el directorio ni
    profiling_report.json): el gate debe cortar ANTES de flow.run, por lo que
    ni siquiera execute()/write_outputs() deben alcanzar a crear el
    subdirectorio.

    Rojo esperado (genuino, no accidental): _dispatch_run (src/foda/cli.py)
    hoy NO llama a evaluate_predecessor_gate (TSK-20/TSK-21 pendientes) antes
    de flow.run(ctx); con este fabricado (success:false), Profiling.validate()
    heredado solo exige que ingestion_report.json exista (existe, aunque con
    success:false) por lo que flow.run(ctx) hoy completa con exito (exit 0) y
    SI escribe profiling_report.json -- exactamente lo que este test prohibe.
    El gate en si (evaluate_predecessor_gate) ya esta completo y en verde
    desde el caso 9 (orchestrator.py); lo que falta es el wiring en la CLI."""
    from foda.cli import main

    _seed_cliente_abc(proyecto)
    _fabricar_ingestion_report(proyecto, success=False)

    result = main(["run", "ABC", "--flow", "profiling"])

    assert result == 1
    captured = capsys.readouterr()
    assert "ingestion" in captured.err
    assert "success" in captured.err

    profiling_dir = (
        tmp_path / "clients" / "ABC" / "020_outputs" / "040_profiling"
    )
    assert not profiling_dir.exists()


def test_run_profiling_con_ingestion_report_success_false_con_force_devuelve_0_escribe_reporte_y_advierte(
    tmp_path: Path, proyecto: Path, capsys
):
    """Caso 13 (CA-09/CA-10, TSK-24/TSK-25): con ingestion_report.json
    (success:false) presente y CON --force,
    main(["run","ABC","--flow","profiling","--force"]) debe devolver 0,
    profiling_report.json debe existir en disco bajo 020_outputs/040_profiling/
    (el gate se sobrepasa y flow.run corre con normalidad), y stderr debe
    contener una advertencia (una linea) que indique que se forzo la
    ejecucion sobrepasando el gate del predecesor 'ingestion'.

    Rojo esperado (genuino, no accidental): _dispatch_run (src/foda/cli.py)
    ya evalua el gate SIEMPRE (DS-PROF-1, wiring del caso 12) y, con
    --force, el 'if gate_message is not None and not args.force' es False,
    por lo que el despacho SI continua a flow.run(ctx) (exit 0, reporte
    escrito) -- las dos primeras aserciones (result==0, reporte presente)
    ya pasarian hoy. Pero la rama --force de TSK-25 (advertencia a stderr)
    todavia NO esta implementada (ver docstring de _dispatch_run: 'aun no
    esta implementada; hoy --force simplemente evita el bloqueo, sin emitir
    advertencia'), asi que stderr queda vacio y la tercera aserto (mensaje de
    advertencia en stderr, nombrando 'ingestion' y 'force') falla. No es un
    error de import/sintaxis accidental: evaluate_predecessor_gate ya esta
    completo y en verde desde el caso 9 (orchestrator.py); falta unicamente
    la rama de advertencia en la CLI."""
    from foda.cli import main

    _seed_cliente_abc(proyecto)
    _fabricar_ingestion_report(proyecto, success=False)

    result = main(["run", "ABC", "--flow", "profiling", "--force"])

    assert result == 0

    profiling_report = (
        tmp_path
        / "clients"
        / "ABC"
        / "020_outputs"
        / "040_profiling"
        / "profiling_report.json"
    )
    assert profiling_report.exists()

    captured = capsys.readouterr()
    stderr_lines = [line for line in captured.err.splitlines() if line.strip()]
    assert len(stderr_lines) == 1
    assert "ingestion" in stderr_lines[0]
    assert "force" in stderr_lines[0].lower()


_VENTAS_HEADER = "fecha,sede,clase,cantidad,precio_unitario"
_VENTAS_ROWS = [
    "2024-01-01,Sede Centro,Agua 600ml,10,1200",
    "2024-01-02,Sede Norte,Cola 1.5L,5,2500",
]


def _seed_cliente_abc_listo_para_ingestion(tmp_path: Path) -> Path:
    """Crea clients/ABC/ completo con lo que Ingestion.requires exige
    (DS-ING-7/DS-ING-8, mismo fixture minimo que
    tests/flows/test_ingestion.py::_build_ctx_fixture_minimo, adaptado al
    layout de disco de esta suite -- client.yaml via _seed_cliente_abc, mas
    contract_data.json/map_client_data.json bajo 020_outputs/ y el archivo
    crudo ventas.csv bajo 010_inputs/030_ingestion/): un unico dataset
    "ventas"/"ventas.csv" (separador coma), contrato y mapa coherentes entre
    si. 'ingestion' NO tiene predecesor en PREDECESSORS (caso 7,
    orchestrator.py), asi que este fixture NO fabrica ningun
    ingestion_report.json (no hay gate que satisfacer). Devuelve la raiz del
    proyecto (tmp_path)."""
    _seed_cliente_abc(tmp_path)
    client_dir = tmp_path / "clients" / "ABC"

    contract_data = {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "historical_data": {
            "datasets": [
                {
                    "kind": "ventas",
                    "source_medium": "csv",
                    "periodicity": "mensual",
                    "files": [
                        {
                            "name": "ventas.csv",
                            "period_start": "2023-01-01",
                            "period_end": "2025-12-31",
                        }
                    ],
                }
            ]
        },
    }
    contrato_path = client_dir / "020_outputs" / "010_discovery" / "contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    contrato_path.write_text(json.dumps(contract_data, ensure_ascii=False), encoding="utf-8")

    map_client_data = {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "datasets": [
            {
                "kind": "ventas",
                "fields": [
                    {"name": "fecha", "required": True},
                    {"name": "sede", "required": True},
                    {"name": "clase", "required": True},
                    {"name": "cantidad", "required": True},
                    {"name": "precio_unitario", "required": False},
                ],
            }
        ],
    }
    mapa_path = client_dir / "020_outputs" / "020_onboarding" / "map_client_data.json"
    mapa_path.parent.mkdir(parents=True)
    mapa_path.write_text(json.dumps(map_client_data, ensure_ascii=False), encoding="utf-8")

    landing_dir = client_dir / "010_inputs" / "030_ingestion"
    landing_dir.mkdir(parents=True)
    (landing_dir / "ventas.csv").write_text(
        "\n".join([_VENTAS_HEADER, *_VENTAS_ROWS]) + "\n", encoding="utf-8"
    )

    return tmp_path


def test_run_ingestion_flujo_sin_predecesor_gate_es_noop_y_corre_como_antes_de_la_feature(
    tmp_path: Path, proyecto: Path, capsys
):
    """Caso 15 (CA-12, TSK-27): 'ingestion' NO tiene predecesor registrado en
    PREDECESSORS (caso 7, orchestrator.py: PREDECESSORS == {"profiling":
    "ingestion"}), por lo que evaluate_predecessor_gate("ingestion", ctx)
    devuelve None (rama "sin predecesor", TSK-12, ya en verde) para
    CUALQUIER estado del disco -- ni siquiera se llega a resolver un
    predecesor ni a leer un reporte. El gate wireado en _dispatch_run
    (DS-PROF-1, casos 12/13, cli.py) es entonces un no-op puro para este
    flujo: main(["run","ABC","--flow","ingestion"]) debe comportarse
    EXACTAMENTE igual que antes de esta feature (no bloquea, no advierte).

    Este test corre ingestion de verdad (fixture minimo DS-ING-7/DS-ING-8:
    contract_data.json + map_client_data.json + ventas.csv, ver
    _seed_cliente_abc_listo_para_ingestion) SIN fabricar ningun
    ingestion_report.json de un predecesor (no aplica: ingestion no tiene
    predecesor) y SIN --force, para distinguir el no-op del gate (este caso)
    de los caminos "bloquea"/"advierte" que si dependen de PREDECESSORS
    (casos 12/13, exclusivos de 'profiling').

    Aserciones especificas (no triviales): (1) exit 0 y stdout de
    completado, igual que cualquier run exitoso previo a la feature de
    profiling (patron ya usado en test_run_onboarding_*,
    test_flow_orchestrator_cli.py); (2) ingestion_report.json queda escrito
    en disco; (3) sobre todo, stderr queda COMPLETAMENTE VACIO -- ninguna
    advertencia de gate ni mencion a '--force', que es precisamente lo que
    _dispatch_run SI emite cuando el flujo tiene predecesor y --force
    sobrepasa un gate_message (caso 13); un flujo sin predecesor jamas debe
    alcanzar esa rama.

    Rojo esperado (previsto por plan.md linea 87: no hay tarea-codigo propia
    para este caso, comportamiento ya cubierto por TSK-12/20/22/23/25): si
    este test pasa de inmediato sin codigo de produccion nuevo, no es un
    verde invalido -- documentar como already_green con la evidencia de
    pytest, igual que los casos 3/4/5/11/14."""
    from foda.cli import main

    _seed_cliente_abc_listo_para_ingestion(proyecto)

    result = main(["run", "ABC", "--flow", "ingestion"])

    assert result == 0
    captured = capsys.readouterr()
    assert "ingestion" in captured.out
    assert "ABC" in captured.out
    assert "completado" in captured.out
    assert captured.err == ""

    ingestion_report = (
        tmp_path
        / "clients"
        / "ABC"
        / "020_outputs"
        / "030_ingestion"
        / "ingestion_report.json"
    )
    assert ingestion_report.exists()


def test_run_profiling_con_ingestion_report_success_true_con_force_devuelve_0_escribe_reporte_y_sin_advertencia(
    tmp_path: Path, proyecto: Path, capsys
):
    """Caso 14 (CA-11, TSK-26): con ingestion_report.json (success:true)
    presente y CON --force, main(["run","ABC","--flow","profiling","--force"])
    debe devolver 0, profiling_report.json debe existir en disco bajo
    020_outputs/040_profiling/ (camino feliz: el gate ya deja pasar con
    success:true, caso 8, orchestrator.py, --force es irrelevante aqui), y
    stderr debe quedar COMPLETAMENTE VACIO: al ser gate_message is None
    (evaluate_predecessor_gate("profiling", ctx) con success:true, caso 8),
    la rama de advertencia de --force (TSK-25, "if gate_message is not None:
    ... else advierte") nunca se dispara, sin importar el valor de
    args.force. Distingue este caso del caso 13 (success:false + --force,
    que SI emite una linea de advertencia a stderr): la asercion
    'stderr == ""' es especifica del contrato "sin gate_message, --force no
    tiene efecto observable" (CA-11), no una trivialidad.

    Rojo esperado si lo hubiera (no se anticipa, ver nota TSK-26 en
    plan.md linea 87): _dispatch_run (src/foda/cli.py) ya evalua el gate
    SIEMPRE (DS-PROF-1) y, con success:true, evaluate_predecessor_gate
    devuelve None (caso 8, orchestrator.py, ya en verde) por lo que el
    bloque 'if gate_message is not None: ...' (TSK-25, caso 13, ya en verde)
    no ejecuta ninguna de sus dos ramas (ni bloqueo ni advertencia) --
    stderr queda vacio con o sin --force. Si esto se comprueba en verde sin
    codigo de produccion nuevo, no es un rojo invalido por error accidental:
    es un caso ya cubierto por el wiring de los casos 8/12/13 (already_green,
    documentado en plan.md)."""
    from foda.cli import main

    _seed_cliente_abc(proyecto)
    _fabricar_ingestion_report(proyecto, success=True)

    result = main(["run", "ABC", "--flow", "profiling", "--force"])

    assert result == 0

    profiling_report = (
        tmp_path
        / "clients"
        / "ABC"
        / "020_outputs"
        / "040_profiling"
        / "profiling_report.json"
    )
    assert profiling_report.exists()

    captured = capsys.readouterr()
    assert captured.err == ""


def test_run_profiling_con_ingestion_report_ausente_sin_force_devuelve_1_y_no_escribe_nada(
    tmp_path: Path, proyecto: Path, capsys
):
    """Caso 16 (CA-13, TSK-28): con ingestion_report.json AUSENTE (no
    fabricado por este test -- ese es precisamente el punto: el cliente
    'ABC' existe (client.yaml) pero jamas corrio 'ingestion') y SIN --force,
    main(["run","ABC","--flow","profiling"]) debe devolver 1, stderr debe
    nombrar tanto al predecesor 'ingestion' como el motivo (el reporte no
    existe/no se encontro; el gate ya produce ese mensaje exacto, caso 10,
    orchestrator.py::evaluate_predecessor_gate, rama 'reporte ausente'), y no
    debe existir NINGUN artefacto bajo 020_outputs/040_profiling/ (ni el
    directorio ni profiling_report.json): el gate debe cortar ANTES de
    flow.run, por lo que ni siquiera execute()/write_outputs() deben
    alcanzar a crear el subdirectorio.

    Previsto por plan.md linea 87 como already_green: la rama "reporte
    ausente -> mensaje" del gate (caso 10, evaluate_predecessor_gate) y el
    wiring "bloquea sin --force" en _dispatch_run (caso 12, cli.py) ya estan
    en verde; para ESTE escenario (ausente en vez de success:false) el
    comportamiento observable de la CLI deberia ser identico al del caso 12
    (bloqueo, exit 1, sin escritura), solo que el mensaje de gate proviene de
    la rama "reporte ausente" (FileNotFoundError capturado, caso 10) en vez
    de la rama "success:false" (caso 9). Si este test pasa de inmediato sin
    codigo de produccion nuevo, no es un verde invalido -- documentar como
    already_green con la evidencia de pytest, igual que los casos 3/4/5/11/
    14/15. Las aserciones son especificas y no triviales: exit code exacto
    (1, no solo != 0), stderr debe nombrar el predecesor 'ingestion' (no
    generico), y la ausencia TOTAL del directorio 040_profiling/ en disco
    (no solo del archivo), distinguiendolo de un posible escenario donde el
    directorio se cree pero el reporte no se escriba."""
    from foda.cli import main

    _seed_cliente_abc(proyecto)
    # No se fabrica ingestion_report.json: el punto de este caso es su
    # ausencia (a diferencia del caso 12, que si lo fabrica con success:false).

    result = main(["run", "ABC", "--flow", "profiling"])

    assert result == 1
    captured = capsys.readouterr()
    assert "ingestion" in captured.err

    profiling_dir = (
        tmp_path / "clients" / "ABC" / "020_outputs" / "040_profiling"
    )
    assert not profiling_dir.exists()
