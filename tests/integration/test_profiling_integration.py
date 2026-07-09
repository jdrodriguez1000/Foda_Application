"""Tests de integracion de Profiling (feature profiling, banda tracer_bullet,
etapa integration_tester).

Fuente: 600_features/profiling/tracer_bullet/spec.md (CA-01..CA-13,
DS-PROF-1..4) y plan.md (TSK-31, "test de integracion end-to-end: gate +
ejecucion de profiling via CLI sobre cliente temporal real");
700_architecture/system_design.md (SS7 estructura de carpetas, SS8 contrato
de artefactos multi-flujo D-014, SS9 abstraccion Flow/ClientContext);
800_persistence/decisions.md (D-080: gate de progresion entre flujos).

A diferencia de tests/flows/test_profiling.py (unit del Flow, 5 casos),
tests/test_orchestrator.py (unit de PREDECESSORS/evaluate_predecessor_gate,
sin disco real de un flujo predecesor corrido de verdad) y
tests/cli/test_profiling_gate_cli.py (CLI en proceso, ingestion_report.json
FABRICADO, sin correr Ingestion real), este modulo verifica que Profiling se
integra correctamente con el resto del sistema REAL:

- Flow.run(ctx) de punta a punta sobre un ClientContext de un cliente real
  (create_client), consumiendo un ingestion_report.json producido por una
  ejecucion REAL de Ingestion (que a su vez depende de un Onboarding real):
  ejercita el contrato multi-flujo D-014 (profiling depende, de forma
  transitiva, de discovery/onboarding/ingestion, no solo del predecesor
  inmediato).
- Resolucion de rutas de requires/produces via Artifact + ClientContext real
  (030_ingestion/, 040_profiling/), sin asumir estructura ni rutas
  hardcodeadas.
- El gate de progresion (evaluate_predecessor_gate + `foda run --flow
  profiling [--force]`) evaluado sobre el reporte REAL que Ingestion produce
  (success:true y success:false), no sobre un fixture fabricado.
- Interaccion con un flujo vecino downstream: el profiling_report.json que
  Profiling produce es exactamente el artefacto que un flujo downstream
  declararia como require, y lo consume sin fallar.
- Fallo temprano con error de contrato claro (FlowContractError, no una
  excepcion cruda) cuando falta ingestion_report.json en el cliente real.
- Aislamiento multi-tenant: dos clientes distintos bajo el mismo
  clients_root progresan de forma independiente por el gate y por
  Profiling, sin fuga de datos entre clients/<cliente>/.
- Invocacion del entry point declarado en pyproject.toml
  ([project.scripts] foda = "foda.cli:main") en un proceso separado, mismo
  patron que tests/integration/test_flow_orchestrator_integration.py.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from foda.cli import main
from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowContractError, FlowResult
from foda.core.scaffold import create_client
from foda.flows.f020_onboarding.onboarding import Onboarding
from foda.flows.f030_ingestion.ingestion import Ingestion
from foda.flows.f040_profiling.profiling import Profiling
from foda.orchestrator import FLOWS, PREDECESSORS, evaluate_predecessor_gate, resolve_flow

_REPO_ROOT = Path(__file__).resolve().parents[2]

_VENTAS_HEADER = "fecha,sede,clase,cantidad,precio_unitario"
_VENTAS_ROWS = [
    "2024-01-01,Sede Centro,Agua 600ml,10,1200",
    "2024-01-02,Sede Norte,Cola 1.5L,5,2500",
]


def _contrato_discovery() -> dict:
    """Simula la salida de Discovery (010_discovery/contract_data.json,
    DIFERIDO): fuente de los archivos esperados por Ingestion (DS-ING-8)."""
    return {
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
                },
            ]
        },
    }


def _contrato_onboarding_coherente() -> dict:
    """contract_data.json (esquema completo de onboarding) coherente con
    _contrato_discovery(): permite que Onboarding().run(ctx) produzca un
    map_client_data.json real que Ingestion consume de verdad."""
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
                {
                    "familia": "Bebidas",
                    "categoria": "Gaseosas",
                    "subcategoria": "Cola",
                    "clase": "Cola 1.5L",
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
                {
                    "region": "Andina",
                    "pais": "Colombia",
                    "ciudad": "Medellin",
                    "sede": "Sede Norte",
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
                        {"name": "precio_unitario", "type": "number", "required": False, "maps_to": None},
                    ],
                    "files": [
                        {
                            "name": "ventas.csv",
                            "period_start": "2023-01-01",
                            "period_end": "2025-12-31",
                        }
                    ],
                },
            ]
        },
    }


def _preparar_cliente_real(name: str, clients_root: Path) -> ClientContext:
    """Crea un cliente real (create_client, CONFORME), escribe
    010_discovery/contract_data.json (simulando Discovery) y ejecuta
    Onboarding().run(ctx) de VERDAD para producir map_client_data.json (no
    un fixture inerte). Devuelve el ClientContext ya listo, antes de
    depositar los archivos crudos del landing de Ingestion."""
    create_client(name, clients_root)
    ctx = ClientContext(name, clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True, exist_ok=True)
    contrato_path.write_text(
        json.dumps(_contrato_onboarding_coherente(), ensure_ascii=False),
        encoding="utf-8",
    )

    onboarding_result = Onboarding().run(ctx)
    assert onboarding_result.success is True

    contrato_path.write_text(
        json.dumps(_contrato_discovery(), ensure_ascii=False), encoding="utf-8"
    )
    return ctx


def _depositar_landing_valido(ctx: ClientContext) -> None:
    landing_dir = ctx.inputs_dir / "030_ingestion"
    landing_dir.mkdir(parents=True, exist_ok=True)
    (landing_dir / "ventas.csv").write_text(
        "\n".join([_VENTAS_HEADER, *_VENTAS_ROWS]) + "\n", encoding="utf-8"
    )


def _preparar_cliente_con_ingestion_success_true(name: str, clients_root: Path) -> ClientContext:
    """Cliente real con la cadena discovery(simulado)->onboarding real->
    ingestion real corrida de verdad, dejando ingestion_report.json con
    success:true en disco (no fabricado a mano)."""
    ctx = _preparar_cliente_real(name, clients_root)
    _depositar_landing_valido(ctx)
    resultado = Ingestion().run(ctx)
    assert resultado.success is True
    return ctx


def _preparar_cliente_con_ingestion_success_false(name: str, clients_root: Path) -> ClientContext:
    """Cliente real cuyo Ingestion real termina con success:false (archivo
    declarado pero ausente en el landing, DS-ING inconsistencia genuina), no
    un reporte fabricado a mano."""
    ctx = _preparar_cliente_real(name, clients_root)
    # Landing vacio: ventas.csv esta declarado en el contrato pero no se
    # deposita, lo que produce una inconsistencia real (missing_file).
    (ctx.inputs_dir / "030_ingestion").mkdir(parents=True, exist_ok=True)
    resultado = Ingestion().run(ctx)
    assert resultado.success is False
    return ctx


def _make_project(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = \"cliente-de-prueba\"\n", encoding="utf-8"
    )
    return tmp_path


def _run_foda_subprocess(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Invoca foda.cli.main tal como lo haria el wrapper de console_scripts
    generado a partir de [project.scripts] en pyproject.toml (mismo patron
    que test_flow_orchestrator_integration.py)."""
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


class _FlowVecinoDownstream(Flow):
    """Flujo de juguete que simula un downstream real (p. ej. Cleaning/050):
    declara como require exactamente el profiling_report.json que Profiling
    produce y, si existe, lo parsea y expone success como salida trivial.
    Solo verifica la interaccion entre flujos vecinos (SS8, D-014), no
    testea Profiling en si (fuera de alcance)."""

    name = "flujo_vecino_downstream_profiling_integracion"
    requires = [
        Artifact(
            name="profiling_report", base="outputs",
            relative="040_profiling/profiling_report.json",
        )
    ]
    produces = [
        Artifact(
            name="resumen", base="outputs",
            relative="050_vecino/resumen.json",
        )
    ]

    def execute(self, ctx: ClientContext) -> FlowResult:
        reporte = json.loads(self.requires[0].path(ctx).read_text(encoding="utf-8"))
        self._resumen = {"profiling_success": reporte["success"]}
        return FlowResult(success=True, outputs=[self.produces[0].path(ctx)])

    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
        path = self.produces[0].path(ctx)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._resumen), encoding="utf-8")


# ---------------------------------------------------------------------------
# Flow.run(ctx) de punta a punta sobre cadena multi-flujo real
# (discovery simulado -> onboarding real -> ingestion real -> profiling)
# ---------------------------------------------------------------------------


def test_run_end_to_end_sobre_cliente_real_con_ingestion_report_producido_por_ingestion_real(
    tmp_path: Path,
) -> None:
    """Profiling().run(ctx) de punta a punta sobre un ClientContext de un
    cliente real, consumiendo un ingestion_report.json producido por una
    corrida REAL de Ingestion (que a su vez depende de un Onboarding real):
    contrato multi-flujo D-014. El reporte de profiling queda con
    success=True y campos de identidad correctos."""
    clients_root = tmp_path / "clients"
    ctx = _preparar_cliente_con_ingestion_success_true("ABC", clients_root)

    result = Profiling().run(ctx)

    ruta_reporte = ctx.outputs_dir / "040_profiling" / "profiling_report.json"
    assert isinstance(result, FlowResult)
    assert result.success is True
    assert ruta_reporte in result.outputs
    assert ruta_reporte.is_file()

    reporte = json.loads(ruta_reporte.read_text(encoding="utf-8"))
    assert reporte == {
        "schema_version": "0.1",
        "client": "ABC",
        "flow": "profiling",
        "success": True,
    }
    # Serializacion deterministica (idem Ingestion/Onboarding).
    assert ruta_reporte.read_text(encoding="utf-8") == (
        json.dumps(reporte, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def test_run_falla_temprano_con_flow_contract_error_si_falta_ingestion_report_en_cliente_real(
    tmp_path: Path,
) -> None:
    """Camino de fallo de contrato integrado (CA-05): sobre un cliente real
    sin ingestion_report.json (ni siquiera Ingestion corrio), run(ctx) lanza
    FlowContractError (no una excepcion cruda) y no deja
    profiling_report.json en disco."""
    clients_root = tmp_path / "clients"
    create_client("Globex", clients_root)
    ctx = ClientContext("Globex", clients_root)

    with pytest.raises(FlowContractError, match="ingestion_report"):
        Profiling().run(ctx)

    assert not (ctx.outputs_dir / "040_profiling" / "profiling_report.json").exists()


def test_run_produce_artefacto_consumible_sin_fallar_por_un_flujo_vecino_downstream_real(
    tmp_path: Path,
) -> None:
    """Interaccion con flujos vecinos downstream (SS8, D-014): el
    profiling_report.json que Profiling produce es exactamente el artefacto
    que un flujo downstream declara como require, y ese flujo vecino lo
    consume sin fallar sobre el mismo ClientContext real."""
    clients_root = tmp_path / "clients"
    ctx = _preparar_cliente_con_ingestion_success_true("Umbrella", clients_root)

    resultado_profiling = Profiling().run(ctx)
    assert resultado_profiling.success is True

    resultado_vecino = _FlowVecinoDownstream().run(ctx)

    assert resultado_vecino.success is True
    ruta_resumen = ctx.outputs_dir / "050_vecino" / "resumen.json"
    assert ruta_resumen.is_file()
    assert json.loads(ruta_resumen.read_text(encoding="utf-8")) == {
        "profiling_success": True
    }


def test_resolve_flow_profiling_devuelve_la_clase_real_con_su_predecesor_registrado(
) -> None:
    """Interaccion con el registro real del orquestador (SS8, D-014):
    resolve_flow("profiling") no devuelve un doble de prueba sino una
    instancia de la clase Profiling real, y PREDECESSORS mapea 'profiling'
    a 'ingestion' (no un flujo arbitrario)."""
    flow = resolve_flow("profiling")

    assert isinstance(flow, Profiling)
    assert FLOWS["profiling"] is Profiling
    assert PREDECESSORS["profiling"] == "ingestion"
    assert [a.name for a in flow.requires] == ["ingestion_report"]
    assert [a.name for a in flow.produces] == ["profiling_report"]


# ---------------------------------------------------------------------------
# Gate de progresion evaluado sobre el reporte REAL de un Ingestion real
# (evaluate_predecessor_gate, in-process)
# ---------------------------------------------------------------------------


def test_evaluate_predecessor_gate_none_con_ingestion_report_real_success_true(
    tmp_path: Path,
) -> None:
    """El gate se evalua sobre un ingestion_report.json REAL (producido por
    Ingestion().run(ctx), no fabricado): con success:true, el gate esta
    satisfecho (None)."""
    clients_root = tmp_path / "clients"
    ctx = _preparar_cliente_con_ingestion_success_true("Wayne", clients_root)

    assert evaluate_predecessor_gate("profiling", ctx) is None


def test_evaluate_predecessor_gate_mensaje_con_ingestion_report_real_success_false(
    tmp_path: Path,
) -> None:
    """El gate se evalua sobre un ingestion_report.json REAL con
    success:false (producido por una inconsistencia genuina de Ingestion, no
    fabricado): el gate bloquea con un mensaje que nombra a 'ingestion'."""
    clients_root = tmp_path / "clients"
    ctx = _preparar_cliente_con_ingestion_success_false("Stark", clients_root)

    mensaje = evaluate_predecessor_gate("profiling", ctx)

    assert isinstance(mensaje, str)
    assert "ingestion" in mensaje


# ---------------------------------------------------------------------------
# `foda run --flow profiling [--force]` end-to-end (main(argv), in-process),
# cadena completa orchestrator -> cli -> ClientContext -> gate -> Flow.run
# ---------------------------------------------------------------------------


def test_cli_run_profiling_con_ingestion_real_success_true_sin_force_exit0_y_escribe_reporte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`foda run <cliente> --flow profiling` (CA-06) sobre un cliente real
    cuyo ingestion_report.json fue producido por un Ingestion real con
    success:true: el gate deja pasar, exit 0 y profiling_report.json queda
    escrito en disco con el contenido real de Profiling.run."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"
    ctx = _preparar_cliente_con_ingestion_success_true("ABC", clients_root)

    monkeypatch.chdir(project_root)
    exit_code = main(["run", "ABC", "--flow", "profiling"])

    assert exit_code == 0
    ruta_reporte = ctx.outputs_dir / "040_profiling" / "profiling_report.json"
    assert ruta_reporte.is_file()
    assert json.loads(ruta_reporte.read_text(encoding="utf-8"))["success"] is True


def test_cli_run_profiling_con_ingestion_real_success_false_sin_force_exit1_y_no_escribe_nada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CA-07/CA-08 sobre el reporte REAL de un Ingestion real (success:false
    por una inconsistencia genuina, no fabricado): el gate bloquea antes de
    flow.run, exit 1, stderr nombra 'ingestion' y no se escribe ningun
    artefacto bajo 040_profiling/."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"
    ctx = _preparar_cliente_con_ingestion_success_false("Initech", clients_root)

    monkeypatch.chdir(project_root)

    import contextlib
    import io

    buf_err = io.StringIO()
    with contextlib.redirect_stderr(buf_err):
        exit_code = main(["run", "Initech", "--flow", "profiling"])

    assert exit_code == 1
    stderr = buf_err.getvalue()
    assert "Traceback" not in stderr
    assert "ingestion" in stderr

    directorio_profiling = ctx.outputs_dir / "040_profiling"
    assert not directorio_profiling.exists() or list(directorio_profiling.iterdir()) == []


def test_cli_run_profiling_con_force_sobre_ingestion_real_success_false_exit0_advierte_y_escribe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CA-09/CA-10: con --force, el gate (evaluado sobre el reporte REAL de
    un Ingestion real con success:false) se sobrepasa; se emite una
    advertencia a stderr (nombrando 'ingestion' y 'force') y flow.run
    corre igual, dejando profiling_report.json escrito."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"
    ctx = _preparar_cliente_con_ingestion_success_false("Soylent", clients_root)

    monkeypatch.chdir(project_root)

    import contextlib
    import io

    buf_err = io.StringIO()
    with contextlib.redirect_stderr(buf_err):
        exit_code = main(["run", "Soylent", "--flow", "profiling", "--force"])

    assert exit_code == 0
    stderr = buf_err.getvalue()
    assert "ingestion" in stderr
    assert "force" in stderr

    ruta_reporte = ctx.outputs_dir / "040_profiling" / "profiling_report.json"
    assert ruta_reporte.is_file()


def test_cli_run_profiling_sin_ingestion_report_en_disco_sin_force_exit1_sin_artefacto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CA-13: sobre un cliente real donde ni siquiera Ingestion corrio (no
    hay ingestion_report.json en disco), `foda run --flow profiling` sin
    --force bloquea con exit 1, stderr claro, sin artefacto de profiling."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"
    create_client("GHOST", clients_root)
    ctx = ClientContext("GHOST", clients_root)

    monkeypatch.chdir(project_root)

    import contextlib
    import io

    buf_err = io.StringIO()
    with contextlib.redirect_stderr(buf_err):
        exit_code = main(["run", "GHOST", "--flow", "profiling"])

    assert exit_code == 1
    assert "ingestion" in buf_err.getvalue()
    assert not (ctx.outputs_dir / "040_profiling").exists()


def test_cli_run_ingestion_flujo_sin_predecesor_no_se_ve_afectado_por_el_gate_de_profiling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CA-12 de regresion: `foda run --flow ingestion` (flujo sin entrada en
    PREDECESSORS) sigue funcionando de forma identica a como lo hacia antes
    de introducir el gate de profiling, sobre un cliente real con la cadena
    discovery(simulado)->onboarding real ya corrida."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"
    ctx = _preparar_cliente_real("Aperture", clients_root)
    _depositar_landing_valido(ctx)

    monkeypatch.chdir(project_root)
    exit_code = main(["run", "Aperture", "--flow", "ingestion"])

    assert exit_code == 0
    assert (ctx.outputs_dir / "030_ingestion" / "ingestion_report.json").is_file()


def test_aislamiento_multi_tenant_del_gate_y_de_profiling_entre_dos_clientes_reales(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Aislamiento multi-tenant (SS7) a traves de la cadena completa: dos
    clientes reales bajo el mismo clients_root, uno con ingestion real
    success:true y otro con success:false, progresan de forma independiente
    por el gate y por Profiling sin fuga de datos entre clients/<cliente>/."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"

    ctx_a = _preparar_cliente_con_ingestion_success_true("ClienteA", clients_root)
    ctx_b = _preparar_cliente_con_ingestion_success_false("ClienteB", clients_root)

    monkeypatch.chdir(project_root)

    assert main(["run", "ClienteA", "--flow", "profiling"]) == 0
    assert main(["run", "ClienteB", "--flow", "profiling"]) == 1

    ruta_a = ctx_a.outputs_dir / "040_profiling" / "profiling_report.json"
    ruta_b = ctx_b.outputs_dir / "040_profiling" / "profiling_report.json"
    assert ruta_a.is_file()
    assert not ruta_b.exists()
    assert ctx_a.root != ctx_b.root


# ---------------------------------------------------------------------------
# Entry point real (proceso separado, sin monkeypatch) -- mismo patron que
# tests/integration/test_flow_orchestrator_integration.py
# ---------------------------------------------------------------------------


def test_entry_point_real_run_profiling_en_proceso_separado_con_ingestion_real_previa(
    tmp_path: Path,
) -> None:
    """Invocacion end-to-end de `foda run --flow profiling` en un proceso
    Python nuevo (imitando el wrapper de console_scripts foda =
    foda.cli:main): argv real, cwd real, sin monkeypatch. Se corre primero
    `foda run --flow ingestion` (success:true) y luego `foda run --flow
    profiling` en el MISMO subproceso invocado dos veces, verificando que el
    binario declarado en [project.scripts] ejecuta la cadena completa
    (orchestrator -> cli -> ClientContext -> gate -> Profiling real) y deja
    el artefacto en disco."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"
    ctx = _preparar_cliente_real("Wayne9", clients_root)
    _depositar_landing_valido(ctx)

    resultado_ingestion = _run_foda_subprocess(
        ["run", "Wayne9", "--flow", "ingestion"], cwd=project_root
    )
    assert resultado_ingestion.returncode == 0

    resultado_profiling = _run_foda_subprocess(
        ["run", "Wayne9", "--flow", "profiling"], cwd=project_root
    )

    assert resultado_profiling.returncode == 0
    assert "Traceback" not in resultado_profiling.stderr
    assert "profiling" in resultado_profiling.stdout
    assert "Wayne9" in resultado_profiling.stdout

    ruta_reporte = ctx.outputs_dir / "040_profiling" / "profiling_report.json"
    assert ruta_reporte.is_file()


def test_entry_point_real_status_en_proceso_separado_lista_flujo_profiling(
    tmp_path: Path,
) -> None:
    """`foda status <cliente>` a nivel de proceso real (subprocess): lista el
    flujo `profiling` real registrado en FLOWS con sus artefactos reales
    (ingestion_report/profiling_report)."""
    project_root = _make_project(tmp_path)
    clients_root = project_root / "clients"
    create_client("Stark9", clients_root)

    result = _run_foda_subprocess(["status", "Stark9"], cwd=project_root)

    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert "profiling:" in result.stdout
    assert "ingestion_report" in result.stdout
    assert "profiling_report" in result.stdout
    assert "[ausente]" in result.stdout


def test_pyproject_entry_point_resuelve_a_main_con_profiling_registrado() -> None:
    """El contrato estatico del entry point (foda.cli:main) expone tambien
    el flujo profiling ya registrado: se verifica que el simbolo declarado
    en [project.scripts] resuelve al mismo main() que construye run/status
    con FLOWS poblado incluyendo 'profiling'."""
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
    assert "profiling" in FLOWS
    assert PREDECESSORS.get("profiling") == "ingestion"
