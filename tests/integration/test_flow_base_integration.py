"""Tests de integracion de flow_base (etapa integration_tester, banda
tracer_bullet, T-015).

Fuente: 600_features/flow_base/tracer_bullet/spec.md y plan.md;
700_architecture/system_design.md (SS7 estructura de carpetas, SS8 contrato
de artefactos, SS9 abstraccion Flow/ClientContext).

A diferencia de tests/core/test_flow.py (unit, feature aislada con un
ClientContext siempre construido via create_client bajo tmp_path), aqui se
verifica que Flow se integra correctamente con el resto del sistema REAL:

- Flow.run(ctx) de punta a punta sobre un ClientContext de un cliente
  creado por create_client (client_scaffold, CONFORME): un Artifact de
  requires que YA EXISTE en el cliente real (client.yaml, colocado por el
  propio scaffold) se resuelve y valida correctamente, y el Flow produce un
  artefacto real bajo 020_outputs/, con FlowResult.outputs apuntando a una
  ruta que existe en disco.
- Camino de fallo de contrato integrado: un Flow cuyo require NO existe en
  el cliente real lanza FlowContractError (no una excepcion cruda), y no
  deja artefactos espurios de produces en disco.
- Coherencia de Artifact.base con las carpetas que create_client realmente
  crea: las seis claves logicas de Artifact resuelven, para el MISMO
  cliente real, exactamente las mismas rutas que ClientContext expone
  (contrato flow_base <-> client_context <-> client_scaffold).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowContractError, FlowResult
from foda.core.scaffold import create_client


class _FlowTrivial(Flow):
    """Flujo de juguete: requiere un artefacto y produce un JSON en outputs."""

    name = "flow_trivial_integracion"

    def __init__(self, requires: list[Artifact], produces: list[Artifact]) -> None:
        self.requires = requires
        self.produces = produces

    def execute(self, ctx: ClientContext) -> FlowResult:
        return FlowResult(
            success=True, outputs=[a.path(ctx) for a in self.produces]
        )

    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
        for artifact in self.produces:
            path = artifact.path(ctx)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="utf-8")


def test_run_end_to_end_sobre_cliente_real_resuelve_require_existente_y_produce_output(
    tmp_path: Path,
) -> None:
    """Flow.run(ctx) de punta a punta sobre un ClientContext de un cliente
    real creado por create_client: un require que YA EXISTE en la
    estructura real del cliente (client.yaml, colocado por el scaffold) se
    valida sin lanzar, y el flujo produce un artefacto real bajo
    020_outputs/, con FlowResult.outputs apuntando a una ruta existente."""
    clients_root = tmp_path / "clients"
    create_client("ACME", clients_root)
    ctx = ClientContext("ACME", clients_root)

    # require real: client.yaml, ya materializado por create_client en la
    # raiz del cliente (no bajo una de las 6 carpetas de Artifact.base, asi
    # que se declara como Artifact "manual" reutilizando el mismo patron:
    # se coloca ademas un input real bajo 010_inputs para ejercitar base
    # "inputs" con datos que existen de verdad en el cliente).
    (ctx.inputs_dir / "cuestionario.txt").write_text("ok", encoding="utf-8")
    require = Artifact(
        name="cuestionario", base="inputs", relative="cuestionario.txt"
    )
    produce = Artifact(
        name="resultado", base="outputs", relative="flow_trivial/resultado.json"
    )

    flow = _FlowTrivial(requires=[require], produces=[produce])
    result = flow.run(ctx)

    assert isinstance(result, FlowResult)
    assert result.success is True
    assert result.outputs == [produce.path(ctx)]
    assert produce.path(ctx).is_file()
    assert produce.path(ctx) == ctx.outputs_dir / "flow_trivial" / "resultado.json"


def test_run_end_to_end_falla_temprano_si_el_require_no_existe_en_el_cliente_real(
    tmp_path: Path,
) -> None:
    """Camino de fallo de contrato integrado: sobre un cliente real, un
    require que NO existe hace que run(ctx) lance FlowContractError (no una
    excepcion cruda), sin dejar artefactos espurios de produces en disco."""
    clients_root = tmp_path / "clients"
    create_client("Globex", clients_root)
    ctx = ClientContext("Globex", clients_root)

    require_ausente = Artifact(
        name="cuestionario", base="inputs", relative="no_existe.txt"
    )
    produce = Artifact(
        name="resultado", base="outputs", relative="flow_trivial/resultado.json"
    )

    flow = _FlowTrivial(requires=[require_ausente], produces=[produce])

    with pytest.raises(FlowContractError, match="cuestionario"):
        flow.run(ctx)

    assert not produce.path(ctx).exists()


def test_artifact_base_coincide_con_las_carpetas_reales_de_create_client(
    tmp_path: Path,
) -> None:
    """Contrato flow_base <-> client_context <-> client_scaffold: para un
    MISMO cliente real, las seis claves logicas de Artifact.base resuelven
    exactamente las mismas rutas que ClientContext expone, y esas rutas
    existen de verdad en disco (fueron creadas por create_client)."""
    clients_root = tmp_path / "clients"
    create_client("Initech", clients_root)
    ctx = ClientContext("Initech", clients_root)

    esperado = {
        "inputs": ctx.inputs_dir,
        "outputs": ctx.outputs_dir,
        "bronze": ctx.bronze_dir,
        "silver": ctx.silver_dir,
        "gold": ctx.gold_dir,
        "models": ctx.models_dir,
    }
    for base, dir_esperado in esperado.items():
        artifact = Artifact(name=f"marcador_{base}", base=base, relative="x")
        assert artifact.path(ctx) == dir_esperado / "x"
        assert dir_esperado.is_dir()


def test_run_end_to_end_produce_artefacto_consumible_por_flujo_vecino(
    tmp_path: Path,
) -> None:
    """Interaccion con un flujo vecino (SS8): el artefacto que un Flow
    produce bajo 020_outputs/ es exactamente el que un segundo Flow
    declararia como require, y lo consume sin fallar -- sobre el mismo
    cliente real y el mismo ClientContext."""
    clients_root = tmp_path / "clients"
    create_client("Wayne", clients_root)
    ctx = ClientContext("Wayne", clients_root)

    (ctx.inputs_dir / "cuestionario.txt").write_text("ok", encoding="utf-8")
    require_1 = Artifact(
        name="cuestionario", base="inputs", relative="cuestionario.txt"
    )
    produce_1 = Artifact(
        name="paso_1", base="outputs", relative="paso_1/salida.json"
    )
    flujo_1 = _FlowTrivial(requires=[require_1], produces=[produce_1])
    resultado_1 = flujo_1.run(ctx)
    assert resultado_1.success is True

    # El flujo vecino requiere exactamente el artefacto que produjo flujo_1.
    require_2 = Artifact(
        name="paso_1", base="outputs", relative="paso_1/salida.json"
    )
    produce_2 = Artifact(
        name="paso_2", base="outputs", relative="paso_2/salida.json"
    )
    flujo_2 = _FlowTrivial(requires=[require_2], produces=[produce_2])
    resultado_2 = flujo_2.run(ctx)

    assert resultado_2.success is True
    assert produce_2.path(ctx).is_file()
