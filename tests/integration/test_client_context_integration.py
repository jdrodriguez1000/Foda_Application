"""Tests de integracion de client_context (etapa integration_tester, banda
tracer_bullet).

Fuente: 600_features/client_context/tracer_bullet/spec.md y plan.md;
700_architecture/system_design.md (SS7 estructura de carpetas, SS8 contrato de
artefactos, SS9 abstraccion Flow/ClientContext, SS12 caminos nuevo/recurrente,
SS13 multi-tenant).

A diferencia de tests/core/test_context.py (unit, feature aislada), aqui se
verifica que ClientContext se integra correctamente con el resto del sistema
real (sin mocks de filesystem):

- Contrato de artefactos con create_client (client_scaffold, CONFORME):
  ClientContext resuelve EXACTAMENTE las carpetas que create_client crea en
  disco, ni una carpeta de mas ni de menos (SS7/SS8).
- Camino nuevo -> recurrente end-to-end (SS12): un cliente recien creado por
  create_client es NUEVO; al materializar models/latest (como lo haria
  Modelling al final del pipeline "nuevo"), el mismo cliente pasa a
  RECURRENTE sin reconstruir nada mas.
- Superficie suficiente para el consumo por Flow.run(ctx) (SS9): desde un
  ClientContext real se puede leer un input colocado en 010_inputs, escribir
  un artefacto JSON en 020_outputs y escribir datasets en bronze/silver/gold,
  simulando el ciclo load_inputs -> execute -> write_outputs de un flujo,
  sin conocer la estructura interna de clients/<NAME>/.
- Fallo temprano ante cliente inexistente: un "flujo vecino" simulado que
  recibe un ClientContext para un cliente nunca creado obtiene un
  FileNotFoundError claro en la construccion, antes de ejecutar cualquier
  logica de negocio (no una excepcion cruda a mitad de un run()).
- Aislamiento multi-tenant (SS13): dos ClientContext sobre el mismo
  clients_root resuelven rutas disjuntas y no se contaminan entre si.

Nota de alcance (spec SS No-Objetivos / plan): Flow/flow_base (T-015) no
existen todavia; estos tests no importan ni construyen una clase Flow real,
solo verifican -mediante una funcion local que imita run(ctx)- que la
superficie publica de ClientContext es suficiente y coherente para ese
consumo futuro (SS9).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from foda.core.context import ClientContext
from foda.core.scaffold import create_client


def test_client_context_resuelve_exactamente_el_arbol_creado_por_create_client(
    tmp_path: Path,
) -> None:
    """Contrato de artefactos client_scaffold -> client_context (SS7/SS8):
    las 6 rutas que expone ClientContext coinciden, una a una, con las
    carpetas que create_client realmente crea en disco -- ni de mas ni de
    menos -- y ambas partes acuerdan la misma raiz (root)."""
    clients_root = tmp_path / "clients"
    client_dir = create_client("ACME", clients_root)

    ctx = ClientContext("ACME", clients_root)

    assert ctx.root == client_dir

    # Solo las carpetas "hoja" (sin subcarpetas) son comparables 1:1 con las
    # rutas que expone ClientContext: "data/" es un contenedor intermedio del
    # scaffold (SS7), no una de las 6 rutas de la spec (que aterrizan en
    # bronze/silver/gold dentro de data/).
    all_dirs = {p for p in client_dir.rglob("*") if p.is_dir()}
    created_leaf_dirs = {
        p for p in all_dirs if not any(other.parent == p for other in all_dirs)
    }
    ctx_dirs = {
        ctx.inputs_dir,
        ctx.outputs_dir,
        ctx.bronze_dir,
        ctx.silver_dir,
        ctx.gold_dir,
        ctx.models_dir,
    }
    assert ctx_dirs == created_leaf_dirs
    assert all(d.is_dir() for d in ctx_dirs)


def test_camino_nuevo_a_recurrente_end_to_end_sobre_el_mismo_cliente(
    tmp_path: Path,
) -> None:
    """SS12: un cliente recien creado por create_client es NUEVO. Al
    materializar models/latest (como lo haria Modelling al terminar el
    pipeline "nuevo"), un ClientContext construido despues sobre el MISMO
    cliente ya lo reporta como RECURRENTE, sin que create_client ni
    ClientContext requieran cambios ni reconstruccion adicional."""
    clients_root = tmp_path / "clients"
    create_client("Globex", clients_root)

    ctx_nuevo = ClientContext("Globex", clients_root)
    assert ctx_nuevo.is_recurring is False

    # Simula el efecto de Modelling (SS8: produce modelo versionado en
    # models/<version>/ + puntero models/latest) al final del pipeline nuevo.
    version_dir = ctx_nuevo.models_dir / "2026-07-03"
    version_dir.mkdir(parents=True)
    (version_dir / "best_model.pkl").write_text("modelo-dummy", encoding="utf-8")
    (ctx_nuevo.models_dir / "latest").mkdir()

    ctx_recurrente = ClientContext("Globex", clients_root)
    assert ctx_recurrente.is_recurring is True
    # El resto de rutas no cambia: mismo cliente, mismo arbol base.
    assert ctx_recurrente.root == ctx_nuevo.root
    assert ctx_recurrente.bronze_dir == ctx_nuevo.bronze_dir


def _run_fake_flow(ctx: ClientContext) -> dict:
    """Imita el ciclo load_inputs -> execute -> write_outputs de Flow.run(ctx)
    (system_design SS9), usando SOLO la superficie publica de ClientContext
    (sin conocer la estructura interna de clients/<NAME>/). No es una clase
    Flow real (flow_base es de una feature futura, T-015): es la prueba de
    que la superficie de ClientContext alcanza para ese consumo."""
    # 1. load_inputs: lee un YAML/dato colocado en 010_inputs.
    raw_input = (ctx.inputs_dir / "cuestionario.txt").read_text(encoding="utf-8")

    # 2. validate + execute: nucleo minimo determinista.
    result = {"echo": raw_input.strip(), "client": ctx.name}

    # 3. write_outputs: JSON en 020_outputs + dataset en bronze/.
    (ctx.outputs_dir / "discovery.json").write_text(
        json.dumps(result), encoding="utf-8"
    )
    (ctx.bronze_dir / "raw.csv").write_text("col_a,col_b\n1,2\n", encoding="utf-8")

    return result


def test_client_context_es_superficie_suficiente_para_flow_run_ctx(
    tmp_path: Path,
) -> None:
    """SS9: desde un ClientContext real se pueden obtener todas las rutas
    necesarias para leer inputs y escribir outputs/data de un cliente real,
    tal como lo haria Flow.run(ctx). Se ejercita el ciclo completo
    (leer input -> ejecutar -> escribir output + dataset) usando unicamente
    inputs_dir/outputs_dir/bronze_dir, sin abrir la implementacion interna
    de ClientContext ni de create_client."""
    clients_root = tmp_path / "clients"
    create_client("Initech", clients_root)
    ctx = ClientContext("Initech", clients_root)

    # Un DS coloca un input real antes de correr el flujo (010_inputs).
    (ctx.inputs_dir / "cuestionario.txt").write_text(
        "respuestas del cliente", encoding="utf-8"
    )

    result = _run_fake_flow(ctx)

    assert result == {"echo": "respuestas del cliente", "client": "Initech"}
    assert (ctx.outputs_dir / "discovery.json").is_file()
    written = json.loads((ctx.outputs_dir / "discovery.json").read_text(encoding="utf-8"))
    assert written == result
    assert (ctx.bronze_dir / "raw.csv").is_file()


def _construir_contexto_de_flujo_vecino(name: str, clients_root: Path) -> ClientContext:
    """Simula como un flujo/orquestador vecino construiria su ClientContext
    para un cliente dado, sin conocer si ese cliente existe de antemano."""
    return ClientContext(name, clients_root)


def test_fallo_temprano_con_mensaje_claro_si_el_flujo_vecino_recibe_cliente_inexistente(
    tmp_path: Path,
) -> None:
    """Fallo temprano (SS9: 'el flujo falla temprano y con mensaje claro' si
    falta un artefacto requerido): un orquestador/flujo vecino que intenta
    construir el ClientContext de un cliente nunca creado por create_client
    obtiene un FileNotFoundError claro (menciona el nombre del cliente) antes
    de ejecutar cualquier logica de negocio -- no una excepcion cruda de bajo
    nivel ni un ClientContext parcialmente construido."""
    clients_root = tmp_path / "clients"
    clients_root.mkdir()
    create_client("Wayne", clients_root)  # otro cliente si existe, real

    with pytest.raises(FileNotFoundError, match="Stark"):
        _construir_contexto_de_flujo_vecino("Stark", clients_root)

    # El cliente real no se ve afectado por el intento fallido del vecino.
    ctx_wayne = ClientContext("Wayne", clients_root)
    assert ctx_wayne.root.is_dir()


def test_dos_client_context_bajo_el_mismo_clients_root_quedan_aislados(
    tmp_path: Path,
) -> None:
    """SS13 (multi-tenant): dos ClientContext construidos sobre el mismo
    clients_root resuelven rutas totalmente disjuntas; escribir un output a
    traves de un ClientContext no es visible desde el ClientContext del otro
    cliente, y el modo (nuevo/recurrente) de uno no afecta al del otro."""
    clients_root = tmp_path / "clients"
    create_client("Umbrella", clients_root)
    create_client("Oscorp", clients_root)

    ctx_umbrella = ClientContext("Umbrella", clients_root)
    ctx_oscorp = ClientContext("Oscorp", clients_root)

    assert ctx_umbrella.root != ctx_oscorp.root
    assert ctx_umbrella.inputs_dir != ctx_oscorp.inputs_dir

    (ctx_umbrella.models_dir / "latest").mkdir()
    assert ctx_umbrella.is_recurring is True
    assert ctx_oscorp.is_recurring is False

    (ctx_umbrella.outputs_dir / "solo_de_umbrella.json").write_text(
        "{}", encoding="utf-8"
    )
    assert list(ctx_oscorp.outputs_dir.iterdir()) == []
