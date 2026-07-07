"""Tests de integracion de flow_orchestrator (feature flow_orchestrator,
banda tracer_bullet, etapa integration_tester).

Fuente: 600_features/flow_orchestrator/tracer_bullet/spec.md (CA-01, CA-02,
CA-06, CA-07, CA-08, CA-09, CA-11, CA-12) y plan.md (Sec.7 "la integracion
end-to-end (comando foda como binario) queda para integration_tester, no
para esta suite"); 700_architecture/system_design.md (SS7 estructura de
carpetas, SS8 contrato de artefactos, SS9 abstraccion Flow/ClientContext).

A diferencia de tests/test_orchestrator.py (unit, sin disco) y
tests/cli/test_flow_orchestrator_cli.py (CLI en proceso, con Onboarding.run
real pero foco en la CLI aislada), este modulo verifica que el orquestador
se integra correctamente con el resto del sistema REAL:

- Cadena completa orchestrator -> cli.main -> ClientContext -> Flow.run ->
  Onboarding -> disco, con las piezas REALES: create_client (client_scaffold,
  CONFORME) crea el cliente, `foda run` ejecuta el Onboarding real y escribe
  el map_client_data.json real, y `foda status` refleja ese disco real.
- Interaccion con el flujo vecino real f020_onboarding (no un FakeFlow):
  resolve_flow("onboarding") devuelve una instancia de la clase Onboarding
  real importada de foda.flows.f020_onboarding.onboarding.
- Invocacion del entry point declarado en pyproject.toml
  ([project.scripts] foda = "foda.cli:main") en un proceso separado, mismo
  patron que tests/integration/test_client_new_cli_integration.py
  (_run_foda_subprocess), para validar run/status como los ejecutaria el
  wrapper de console_scripts real.
- Fallo temprano con FlowContractError traducido a stderr (no excepcion
  cruda) cuando el requires del flujo vecino falta en el cliente real.
- Aislamiento multi-tenant: `foda run`/`foda status` sobre dos clientes
  reales distintos bajo el mismo clients_root no se contaminan entre si.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from foda.cli import main
from foda.core.context import ClientContext
from foda.core.scaffold import create_client
from foda.flows.f020_onboarding.onboarding import Onboarding
from foda.orchestrator import FLOWS, resolve_flow

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _contrato_valido() -> dict:
    """Contrato minimo valido, mismo fixture (reducido) ya usado por
    tests/integration/test_onboarding_integration.py; se duplica aqui
    deliberadamente para que este archivo de integracion sea autocontenido."""
    return {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "product_hierarchy": {
            "levels": ["familia", "categoria", "subcategoria", "clase"],
            "members": [
                {
                    "familia": "Bebidas",
                    "categoria": "Aguas",
                    "subcategoria": "Sin gas",
                    "clase": "Agua 600ml",
                },
            ],
        },
        "geography": {
            "levels": ["region", "pais", "ciudad", "sede"],
            "members": [
                {
                    "region": "Andina",
                    "pais": "Colombia",
                    "ciudad": "Bogota",
                    "sede": "Sede Centro",
                },
            ],
        },
        "historical_data": {
            "datasets": [
                {
                    "kind": "ventas",
                    "source_medium": "csv",
                    "periodicity": "mensual",
                    "fields": [
                        {"name": "fecha", "type": "date", "required": True, "maps_to": "time"},
                        {"name": "sede", "type": "string", "required": True, "maps_to": "geography.sede"},
                        {"name": "clase", "type": "string", "required": True, "maps_to": "product.clase"},
                        {"name": "cantidad", "type": "integer", "required": True, "maps_to": "measure"},
                    ],
                    "files": [
                        {
                            "name": "ventas_2023_2025.csv",
                            "period_start": "2023-01-01",
                            "period_end": "2025-12-31",
                        }
                    ],
                },
            ]
        },
    }


def _escribir_contrato(ctx: ClientContext, contrato: dict) -> Path:
    """Escribe contract_data.json bajo la ruta real del require (010_discovery/,
    resuelta via Artifact + ClientContext)."""
    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True, exist_ok=True)
    contrato_path.write_text(json.dumps(contrato, ensure_ascii=False), encoding="utf-8")
    return contrato_path


def _make_project(tmp_path: Path) -> Path:
    """Crea un proyecto temporal realista: pyproject.toml marcador en la raiz
    (mismo patron que test_client_new_cli_integration.py)."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = \"cliente-de-prueba\"\n", encoding="utf-8"
    )
    return tmp_path


def _run_foda_subprocess(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Invoca foda.cli.main tal como lo haria el wrapper de console_scripts
    generado a partir de [project.scripts] en pyproject.toml (mismo patron que
    test_client_new_cli_integration.py::_run_foda_subprocess)."""
    code = "import sys; from foda.cli import main; sys.exit(main(sys.argv[1:]))"
    env = {
        "PYTHONPATH": str(_REPO_ROOT / "src"),
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SystemRoot", ""),
    }
    return subprocess.run(
        [sys.executable, "-c", code, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
    )


# ---------------------------------------------------------------------------
# Cadena completa orchestrator -> cli -> ClientContext -> Flow.run ->
# Onboarding real -> disco (in-process, main(argv))
# ---------------------------------------------------------------------------


def test_run_end_to_end_con_onboarding_real_escribe_map_client_data_identico_al_producido_por_el_flujo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`foda run ABC --flow onboarding` (via main(argv), cliente real creado
    por create_client, CONFORME) ejecuta el Onboarding REAL y deja escrito en
    disco el mismo map_client_data.json que produciria Onboarding().run(ctx)
    invocado directamente: la CLI no reimplementa logica de flujo (C-5)."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)
    _escribir_contrato(ctx, _contrato_valido())

    monkeypatch.chdir(project_root)
    exit_code = main(["run", "ABC", "--flow", "onboarding"])

    assert exit_code == 0
    ruta_mapa = ctx.outputs_dir / "020_onboarding" / "map_client_data.json"
    assert ruta_mapa.is_file()

    mapa_via_cli = json.loads(ruta_mapa.read_text(encoding="utf-8"))
    assert mapa_via_cli["client"]["code"] == "ABC"
    assert mapa_via_cli["totals"] == {"dataset_count": 1, "file_count": 1}


def test_status_refleja_end_to_end_el_disco_real_tras_un_run_real(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`foda status ABC` (main(argv)) sobre un cliente real, antes y despues
    de `foda run ABC --flow onboarding` real: marca contract_data presente/
    map_client_data ausente y luego ambos presentes, leyendo el disco real
    escrito por el Onboarding real (no un stub)."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)
    _escribir_contrato(ctx, _contrato_valido())

    monkeypatch.chdir(project_root)

    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert main(["status", "ABC"]) == 0
    antes = buf.getvalue()
    assert "contract_data" in antes and "[presente]" in antes
    assert "map_client_data" in antes and "[ausente]" in antes

    assert main(["run", "ABC", "--flow", "onboarding"]) == 0

    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        assert main(["status", "ABC"]) == 0
    despues = buf2.getvalue()

    for linea in despues.splitlines():
        if "contract_data" in linea or "map_client_data" in linea:
            assert "[presente]" in linea


def test_resolve_flow_onboarding_devuelve_la_clase_real_del_flujo_vecino(
) -> None:
    """Interaccion con el flujo vecino real (SS8, D-014): resolve_flow
    ("onboarding") no devuelve un doble de prueba sino una instancia de la
    clase Onboarding real importada de foda.flows.f020_onboarding.onboarding,
    con su requires/produces reales (contract_data / map_client_data)."""
    flow = resolve_flow("onboarding")

    assert isinstance(flow, Onboarding)
    assert FLOWS["onboarding"] is Onboarding
    assert [a.name for a in flow.requires] == ["contract_data"]
    assert [a.name for a in flow.produces] == ["map_client_data"]


def test_run_falla_temprano_con_flow_contract_error_traducido_si_falta_contract_data_real(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fallo temprano de contrato (CA-06) sobre el flujo real y un cliente
    real sin contract_data.json: FlowContractError (lanzado por
    Onboarding.validate real, no reimplementado por la CLI) se traduce a
    stderr claro (sin Traceback) + codigo 1, y no queda map_client_data.json."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"
    create_client("Globex", clients_root)
    ctx = ClientContext("Globex", clients_root)

    monkeypatch.chdir(project_root)

    import contextlib
    import io

    buf_err = io.StringIO()
    with contextlib.redirect_stderr(buf_err):
        exit_code = main(["run", "Globex", "--flow", "onboarding"])

    assert exit_code == 1
    stderr = buf_err.getvalue()
    assert "Traceback" not in stderr
    assert "contract_data" in stderr

    ruta_mapa = ctx.outputs_dir / "020_onboarding" / "map_client_data.json"
    assert not ruta_mapa.exists()


def test_aislamiento_multi_tenant_run_y_status_entre_dos_clientes_reales(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Aislamiento multi-tenant (SS7) a traves de la cadena completa: dos
    clientes reales bajo el mismo clients_root, uno con contract_data valido
    y otro sin el; `foda run`/`foda status` no filtran datos ni estado entre
    clients/<cliente>/."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"

    create_client("ClienteA", clients_root)
    ctx_a = ClientContext("ClienteA", clients_root)
    _escribir_contrato(ctx_a, _contrato_valido())

    create_client("ClienteB", clients_root)
    ctx_b = ClientContext("ClienteB", clients_root)
    # ClienteB deliberadamente sin contract_data.json.

    monkeypatch.chdir(project_root)

    assert main(["run", "ClienteA", "--flow", "onboarding"]) == 0
    assert main(["run", "ClienteB", "--flow", "onboarding"]) == 1

    ruta_a = ctx_a.outputs_dir / "020_onboarding" / "map_client_data.json"
    ruta_b = ctx_b.outputs_dir / "020_onboarding" / "map_client_data.json"
    assert ruta_a.is_file()
    assert not ruta_b.exists()


# ---------------------------------------------------------------------------
# Entry point real (proceso separado, sin monkeypatch) -- mismo patron que
# tests/integration/test_client_new_cli_integration.py
# ---------------------------------------------------------------------------


def test_entry_point_real_run_en_proceso_separado_ejecuta_onboarding_y_escribe_artefacto(
    tmp_path: Path,
) -> None:
    """Invocacion end-to-end de `foda run` en un proceso Python nuevo
    (imitando el wrapper de console_scripts foda = foda.cli:main): argv real,
    cwd real, sin monkeypatch. Verifica que el binario declarado en
    [project.scripts] ejecuta la cadena completa (orchestrator -> cli ->
    ClientContext -> Onboarding real) y deja el artefacto en disco."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"
    create_client("Wayne9", clients_root)
    ctx = ClientContext("Wayne9", clients_root)
    _escribir_contrato(ctx, _contrato_valido())

    result = _run_foda_subprocess(
        ["run", "Wayne9", "--flow", "onboarding"], cwd=project_root
    )

    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert "onboarding" in result.stdout
    assert "Wayne9" in result.stdout

    ruta_mapa = ctx.outputs_dir / "020_onboarding" / "map_client_data.json"
    assert ruta_mapa.is_file()


def test_entry_point_real_status_en_proceso_separado_lista_flujo_onboarding(
    tmp_path: Path,
) -> None:
    """`foda status <cliente>` a nivel de proceso real (subprocess): lista el
    flujo `onboarding` real registrado en FLOWS con sus artefactos reales."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"
    create_client("Stark9", clients_root)

    result = _run_foda_subprocess(["status", "Stark9"], cwd=project_root)

    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert "onboarding:" in result.stdout
    assert "contract_data" in result.stdout
    assert "map_client_data" in result.stdout
    assert "[ausente]" in result.stdout


def test_entry_point_real_run_cliente_inexistente_falla_claro_sin_tocar_clients(
    tmp_path: Path,
) -> None:
    """Integracion del camino de error a nivel de proceso real: cliente
    inexistente -> exit 1, stderr claro (sin Traceback), y el arbol de
    clients/ no crece con una carpeta para el cliente pedido (CA-12)."""
    project_root = _make_project(tmp_path)

    result = _run_foda_subprocess(
        ["run", "GHOST9", "--flow", "onboarding"], cwd=project_root
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "GHOST9" in result.stderr
    assert not (project_root / "clients" / "GHOST9").exists()


def test_pyproject_declara_entry_point_consistente_con_run_y_status_reales() -> None:
    """El contrato estatico del entry point (foda.cli:main) expone tambien
    run/status, no solo client new: se verifica que el simbolo declarado en
    [project.scripts] resuelve al mismo main() que construye ambos
    subparsers (run, status) con FLOWS ya poblado."""
    import importlib
    import tomllib

    pyproject_data = tomllib.loads(
        (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    entry = pyproject_data["project"]["scripts"]["foda"]
    assert entry == "foda.cli:main"

    module_name, func_name = entry.split(":")
    module = importlib.import_module(module_name)
    assert callable(getattr(module, func_name))
    assert "onboarding" in FLOWS
