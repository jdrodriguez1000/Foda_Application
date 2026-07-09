"""Suite unitaria del registro/resolucion de flujos (feature flow_orchestrator,
banda tracer_bullet). Independiente de la CLI, sin disco.

Fuente: 600_features/flow_orchestrator/tracer_bullet/spec.md (DS-ORQ-1/2, CA-10) y
plan.md (TSK-05..TSK-07). Bucle TDD en curso: caso 3 (CA-10/CA-04, TSK-07).

Tambien cubre el gate de progresion entre flujos de la feature profiling/
tracer_bullet (600_features/profiling/tracer_bullet/spec.md DS-PROF-2/DS-PROF-4,
plan.md TSK-11..TSK-18): PREDECESSORS y evaluate_predecessor_gate.
"""

import json

import pytest

import foda.orchestrator as orchestrator_module
from foda.core.context import ClientContext
from foda.core.flow import Flow
from foda.core.scaffold import create_client
from foda.flows.f020_onboarding.onboarding import Onboarding
from foda.flows.f040_profiling.profiling import Profiling
from foda.orchestrator import FLOWS, PREDECESSORS, evaluate_predecessor_gate, resolve_flow


def test_resolve_flow_onboarding_devuelve_instancia_de_onboarding() -> None:
    """Caso 1 (CA-10, TSK-05): resolve_flow("onboarding") devuelve una
    INSTANCIA de Onboarding (subclase de Flow), no la clase ni otro tipo."""
    flow = resolve_flow("onboarding")

    assert isinstance(flow, Onboarding)
    assert isinstance(flow, Flow)


def test_flows_es_mapeo_explicito_onboarding_a_clase_onboarding() -> None:
    """Caso 2 (CA-10, TSK-06): FLOWS es un mapeo explicito nombre->clase Flow
    que contiene "onboarding" -> Onboarding (la CLASE, no una instancia)."""
    assert isinstance(FLOWS, dict)
    assert "onboarding" in FLOWS
    assert FLOWS["onboarding"] is Onboarding

    for name, flow_cls in FLOWS.items():
        assert isinstance(name, str)
        assert isinstance(flow_cls, type)
        assert issubclass(flow_cls, Flow)


def test_resolve_flow_nombre_no_registrado_lanza_value_error() -> None:
    """Caso 3 (CA-10/CA-04, TSK-07): resolve_flow(<nombre no registrado>)
    lanza ValueError (no KeyError ni otra excepcion)."""
    with pytest.raises(ValueError):
        resolve_flow("inexistente")


def test_resolve_flow_profiling_devuelve_instancia_de_profiling() -> None:
    """Caso 6 (feature profiling/tracer_bullet, CA-06, TSK-09): resolve_flow(
    "profiling") devuelve una INSTANCIA de Profiling (subclase de Flow), via
    el registro FLOWS. Hoy "profiling" no esta registrado en FLOWS (solo
    "onboarding"/"ingestion"), por lo que resolve_flow lanza ValueError en vez
    de devolver la instancia esperada: rojo genuino, TSK-10 lo pone en verde."""
    flow = resolve_flow("profiling")

    assert isinstance(flow, Profiling)
    assert isinstance(flow, Flow)


def test_predecessors_mapea_profiling_a_ingestion_y_gate_es_noop_sin_predecesor(
    tmp_path,
) -> None:
    """Caso 7 (feature profiling/tracer_bullet, CA-12, TSK-11): PREDECESSORS
    es el mapa literal explicito {"profiling": "ingestion"} (DS-PROF-2), y
    evaluate_predecessor_gate(flow_name, ctx) devuelve None para un flujo SIN
    entrada registrada en PREDECESSORS (p. ej. "ingestion", que no tiene
    predecesor en esta banda: el par ingestion->onboarding queda excluido a
    proposito, ver spec DS-PROF-2) -- el gate es no-op, sin exigir ningun
    reporte en disco.

    Hoy ni PREDECESSORS ni evaluate_predecessor_gate existen en
    foda.orchestrator (solo TSK-10 -- registro de "profiling" en FLOWS -- esta
    en verde); el import de ambos en el modulo falla con ImportError. Rojo
    genuino: no hay typo ni error de sintaxis, falta el mapa y la funcion que
    TSK-12 debe introducir como esqueleto minimo."""
    assert PREDECESSORS == {"profiling": "ingestion"}

    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    assert evaluate_predecessor_gate("ingestion", ctx) is None


def _fabricar_ingestion_report(ctx: ClientContext, *, success: bool) -> None:
    """Helper local (plan.md, Estrategia de Test): fabrica un
    ingestion_report.json minimo en 020_outputs/030_ingestion/ del cliente,
    sin correr Ingestion real (aislamiento de unidad)."""
    report_dir = ctx.outputs_dir / "030_ingestion"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "0.1",
        "client": ctx.name,
        "flow": "ingestion",
        "success": success,
    }
    (report_dir / "ingestion_report.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def test_evaluate_predecessor_gate_profiling_devuelve_none_con_ingestion_report_success_true(
    tmp_path, monkeypatch
) -> None:
    """Caso 8 (feature profiling/tracer_bullet, CA-06, TSK-13): con
    ingestion_report.json presente y success:true, evaluate_predecessor_gate(
    "profiling", ctx) devuelve None (predecesor satisfecho, DS-PROF-4).

    "profiling" SI tiene entrada en PREDECESSORS (caso 7 ya en verde), asi que
    hoy el `if flow_name not in PREDECESSORS: return None` no se dispara: la
    funcion cae al final del cuerpo sin ninguna sentencia mas (TSK-12 solo
    implemento el esqueleto de la rama "sin predecesor") y devuelve None de
    forma implicita, para CUALQUIER estado del reporte -- no porque haya
    resuelto y leido ingestion_report.json (DS-PROF-4: "resuelve la ruta del
    reporte del predecesor con resolve_flow(<pred>).produces[0].path(ctx)").
    Por eso una asercion trivial `is None` pasaria hoy sin codigo nuevo y no
    seria un rojo valido (NC-5): se espia resolve_flow para exigir que la
    implementacion real (TSK-14) efectivamente lo invoque con "ingestion" al
    resolver la ruta del reporte, en vez de devolver None a ciegas. Rojo
    genuino: resolve_flow no se llama todavia dentro de evaluate_predecessor_gate."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)
    _fabricar_ingestion_report(ctx, success=True)

    llamadas: list[str] = []
    original_resolve_flow = orchestrator_module.resolve_flow

    def resolve_flow_espia(name: str):
        llamadas.append(name)
        return original_resolve_flow(name)

    monkeypatch.setattr(orchestrator_module, "resolve_flow", resolve_flow_espia)

    resultado = orchestrator_module.evaluate_predecessor_gate("profiling", ctx)

    assert resultado is None
    assert llamadas == ["ingestion"]


def test_evaluate_predecessor_gate_profiling_devuelve_mensaje_con_ingestion_report_ausente(
    tmp_path,
) -> None:
    """Caso 10 (feature profiling/tracer_bullet, CA-13, TSK-17): sin
    ingestion_report.json en disco, evaluate_predecessor_gate("profiling", ctx)
    devuelve un MENSAJE (str no vacio) que nombra a "ingestion" (DS-PROF-4:
    el gate debe identificar cual predecesor bloquea, tambien cuando su
    reporte simplemente no existe).

    A diferencia de los casos 8/9 (TSK-14/TSK-16), aqui NO se fabrica
    ingestion_report.json (el punto del caso es su ausencia). Hoy
    evaluate_predecessor_gate resuelve report_path via
    resolve_flow("ingestion").produces[0].path(ctx) y llama de inmediato
    report_path.read_text(encoding="utf-8") sin comprobar antes si el archivo
    existe ni capturar FileNotFoundError: read_text() lanza FileNotFoundError
    directamente (excepcion no controlada), en vez de devolver el str
    legible que este test exige. Rojo genuino (no accidental): no es un
    ImportError/TypeError por typo, sino la ausencia de manejo del caso
    "reporte ausente" que TSK-17/18 debe agregar."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    resultado = orchestrator_module.evaluate_predecessor_gate("profiling", ctx)

    assert isinstance(resultado, str)
    assert resultado != ""
    assert "ingestion" in resultado


def test_evaluate_predecessor_gate_profiling_devuelve_mensaje_con_ingestion_report_success_false(
    tmp_path,
) -> None:
    """Caso 9 (feature profiling/tracer_bullet, CA-07, TSK-15): con
    ingestion_report.json presente y success:false, evaluate_predecessor_gate(
    "profiling", ctx) devuelve un MENSAJE (str no vacio) que nombra a
    "ingestion" (DS-PROF-4: el gate debe identificar cual predecesor fallo).

    Hoy (TSK-14) evaluate_predecessor_gate solo tiene la rama explicita
    `if report["success"] is True: return None`; no hay ninguna rama para
    success:false, asi que el cuerpo de la funcion cae al final sin una
    sentencia `return` adicional y Python devuelve None de forma implicita.
    Este test exige `isinstance(resultado, str)` y `"ingestion" in resultado`,
    lo cual falla contra ese None implicito (AssertionError, no
    ImportError/TypeError accidental): rojo genuino que TSK-15 debe resolver
    agregando la rama success:false -> mensaje."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)
    _fabricar_ingestion_report(ctx, success=False)

    resultado = orchestrator_module.evaluate_predecessor_gate("profiling", ctx)

    assert isinstance(resultado, str)
    assert resultado != ""
    assert "ingestion" in resultado
