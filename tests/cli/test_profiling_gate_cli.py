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
