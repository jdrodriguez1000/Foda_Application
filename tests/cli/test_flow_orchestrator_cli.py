"""Suite de tests de la CLI de orquestacion `foda run`/`foda status`
(feature flow_orchestrator, banda tracer_bullet). Independiente de
tests/cli/test_client_new_cli.py (CA-14). Invoca `main(argv)` en proceso,
bajo un proyecto+cliente temporal (`tmp_path` con `pyproject.toml` marcador,
`clients/ABC/client.yaml` y, cuando el caso lo requiere,
`020_outputs/010_discovery/contract_data.json` con un contrato minimo
valido).

Fuente: 600_features/flow_orchestrator/tracer_bullet/plan.md (Sec.6, Sec.7).
Bucle TDD: un test por caso, ejecutado en orden (state.json -> stages.tdd.cases).
"""

import json
from pathlib import Path

from foda.cli import main
from foda.core.flow import FlowResult
from foda.flows.f020_onboarding.onboarding import Onboarding


def _contrato_valido() -> dict:
    """Contrato minimo valido (mismo fixture de referencia usado por
    tests/flows/test_onboarding.py::_contrato_valido) que Onboarding.validate
    acepta: levels no vacios, members coherentes con levels, maps_to validos,
    enums de vocabulario cerrado, fechas YYYY-MM-DD y field.name unico por
    dataset."""
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
                {
                    "familia": "Snacks",
                    "categoria": "Papas",
                    "subcategoria": "Fritas",
                    "clase": "Papas 45g",
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
                        {
                            "name": "fecha",
                            "type": "date",
                            "required": True,
                            "maps_to": "time",
                        },
                        {
                            "name": "sede",
                            "type": "string",
                            "required": True,
                            "maps_to": "geography.sede",
                        },
                        {
                            "name": "clase",
                            "type": "string",
                            "required": True,
                            "maps_to": "product.clase",
                        },
                        {
                            "name": "cantidad",
                            "type": "integer",
                            "required": True,
                            "maps_to": "measure",
                        },
                        {
                            "name": "precio_unitario",
                            "type": "number",
                            "required": False,
                            "maps_to": None,
                        },
                    ],
                    "files": [
                        {
                            "name": "ventas_2023_2025.csv",
                            "period_start": "2023-01-01",
                            "period_end": "2025-12-31",
                        }
                    ],
                },
                {
                    "kind": "inventario",
                    "source_medium": "csv",
                    "periodicity": "mensual",
                    "fields": [
                        {
                            "name": "fecha",
                            "type": "date",
                            "required": True,
                            "maps_to": "time",
                        },
                        {
                            "name": "sede",
                            "type": "string",
                            "required": True,
                            "maps_to": "geography.sede",
                        },
                        {
                            "name": "clase",
                            "type": "string",
                            "required": True,
                            "maps_to": "product.clase",
                        },
                        {
                            "name": "stock",
                            "type": "integer",
                            "required": True,
                            "maps_to": "measure",
                        },
                    ],
                    "files": [
                        {
                            "name": "inventario_2024.csv",
                            "period_start": "2024-01-01",
                            "period_end": "2024-12-31",
                        },
                        {
                            "name": "inventario_2025.csv",
                            "period_start": "2025-01-01",
                            "period_end": "2025-12-31",
                        },
                    ],
                },
            ]
        },
    }


def _seed_cliente_abc(tmp_path: Path, *, con_contrato: bool) -> Path:
    """Crea <tmp_path>/clients/ABC/ con client.yaml (marcador de existencia
    que exige ClientContext) y, si con_contrato, con
    020_outputs/010_discovery/contract_data.json valido. Devuelve la raiz del
    proyecto (tmp_path)."""
    client_dir = tmp_path / "clients" / "ABC"
    client_dir.mkdir(parents=True)
    (client_dir / "client.yaml").write_text("name: ABC\n", encoding="utf-8")

    if con_contrato:
        contrato_path = client_dir / "020_outputs" / "010_discovery" / "contract_data.json"
        contrato_path.parent.mkdir(parents=True)
        contrato_path.write_text(
            json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
        )

    return tmp_path


def test_run_onboarding_con_contrato_valido_devuelve_0_y_escribe_map_client_data(
    tmp_path, monkeypatch
):
    """Caso 4 (CA-01): main(["run","ABC","--flow","onboarding"]) con ABC
    existente y contract_data.json presente/valido devuelve 0 y deja escrito
    clients/ABC/020_outputs/020_onboarding/map_client_data.json."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    _seed_cliente_abc(tmp_path, con_contrato=True)
    monkeypatch.chdir(tmp_path)

    result = main(["run", "ABC", "--flow", "onboarding"])

    assert result == 0
    map_client_data = (
        tmp_path
        / "clients"
        / "ABC"
        / "020_outputs"
        / "020_onboarding"
        / "map_client_data.json"
    )
    assert map_client_data.exists()


def test_run_onboarding_exitoso_stdout_confirma_flujo_cliente_y_artefacto(
    tmp_path, monkeypatch, capsys
):
    """Caso 5 (CA-02, TSK-09): en el exito del caso 4, stdout contiene una
    confirmacion legible que menciona el flujo onboarding, el cliente ABC y
    la ruta del artefacto producido (map_client_data.json)."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    _seed_cliente_abc(tmp_path, con_contrato=True)
    monkeypatch.chdir(tmp_path)

    result = main(["run", "ABC", "--flow", "onboarding"])

    assert result == 0
    captured = capsys.readouterr()
    assert "onboarding" in captured.out
    assert "ABC" in captured.out
    assert "map_client_data.json" in captured.out


def test_run_invoca_flow_run_una_sola_vez_con_ctx_cuyo_name_es_abc(
    tmp_path, monkeypatch
):
    """Caso 6 (CA-03, TSK-10): con Onboarding.run espiado (sin ejecutar el
    flujo real), main(["run","ABC","--flow","onboarding"]) lo invoca
    EXACTAMENTE UNA VEZ con un ctx cuyo name == "ABC" (verifica delegacion
    estricta: el orquestador no deriva el mapa por su cuenta ni reimplementa
    la logica de flujo, solo despacha a flow.run(ctx))."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    _seed_cliente_abc(tmp_path, con_contrato=False)
    monkeypatch.chdir(tmp_path)

    calls = []

    def fake_run(self, ctx):
        calls.append(ctx)
        return FlowResult(success=True, outputs=[])

    monkeypatch.setattr(Onboarding, "run", fake_run)

    result = main(["run", "ABC", "--flow", "onboarding"])

    assert result == 0
    assert len(calls) == 1
    assert calls[0].name == "ABC"


def test_run_cliente_inexistente_devuelve_1_stderr_nombra_cliente_sin_traceback_ni_artefacto(
    tmp_path, monkeypatch, capsys
):
    """Caso 8 (CA-05, TSK-12): main(["run","GHOST","--flow","onboarding"])
    con GHOST inexistente (no sembrado bajo clients/) devuelve 1, stderr
    menciona el cliente GHOST/que no existe, la salida no contiene
    "Traceback" y no se crea ningun artefacto ni carpeta del cliente GHOST.
    _dispatch_run construye ClientContext(args.name, clients_root) y traduce
    el FileNotFoundError resultante (mensaje "No existe el cliente 'GHOST'...")
    a stderr + return 1 antes de invocar flow.run."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = main(["run", "GHOST", "--flow", "onboarding"])

    assert result == 1
    captured = capsys.readouterr()
    assert "GHOST" in captured.err
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err
    ghost_dir = tmp_path / "clients" / "GHOST"
    assert not ghost_dir.exists()


def test_run_sin_contract_data_devuelve_1_stderr_refleja_flow_contract_error(
    tmp_path, monkeypatch, capsys
):
    """Caso 9 (CA-06, TSK-13): main(["run","ABC","--flow","onboarding"]) con
    ABC existente pero SIN 020_outputs/010_discovery/contract_data.json
    devuelve 1, stderr refleja el FlowContractError de Flow.validate (nombra
    el artefacto requerido ausente "contract_data"), la salida no contiene
    "Traceback" y no se escribe map_client_data.json. _dispatch_run construye
    ClientContext (que solo exige client.yaml) y delega en flow.run(ctx);
    Onboarding hereda Flow.validate, que compara self.requires contra disco
    antes de execute/write_outputs."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    _seed_cliente_abc(tmp_path, con_contrato=False)
    monkeypatch.chdir(tmp_path)

    result = main(["run", "ABC", "--flow", "onboarding"])

    assert result == 1
    captured = capsys.readouterr()
    assert "contract_data" in captured.err
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err
    map_client_data = (
        tmp_path
        / "clients"
        / "ABC"
        / "020_outputs"
        / "020_onboarding"
        / "map_client_data.json"
    )
    assert not map_client_data.exists()


def test_status_onboarding_lista_contract_data_y_map_client_data_con_marcadores(
    tmp_path, monkeypatch, capsys
):
    """Caso 10 (CA-07, TSK-14): main(["status","ABC"]) con ABC existente y
    contract_data.json presente pero map_client_data.json ausente (estado
    inicial tipico) devuelve 0 y stdout lista el flujo onboarding incluyendo
    contract_data y map_client_data, cada uno con su marcador de presencia
    (DS-ORQ-3: "[presente]"/"[ausente]"). El subcomando `status` aun no esta
    registrado en _build_parser/main, por lo que argparse lo rechaza como
    subcomando desconocido (SystemExit(2)) en vez de devolver un codigo de
    resultado; este es el rojo esperado hasta que TSK-14 lo implemente."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    _seed_cliente_abc(tmp_path, con_contrato=True)
    monkeypatch.chdir(tmp_path)

    result = main(["status", "ABC"])

    assert result == 0
    captured = capsys.readouterr()
    assert "onboarding" in captured.out
    assert "contract_data" in captured.out
    assert "map_client_data" in captured.out
    assert "[presente]" in captured.out
    assert "[ausente]" in captured.out


def test_run_flujo_inexistente_devuelve_1_stderr_nombra_flujo_sin_traceback_ni_artefacto(
    tmp_path, monkeypatch, capsys
):
    """Caso 7 (CA-04, TSK-11): main(["run","ABC","--flow","inexistente"])
    devuelve 1, stderr menciona el flujo desconocido ("inexistente"), la
    salida no contiene "Traceback" y no se escribe ningun artefacto de
    salida. resolve_flow(args.flow) es lo primero que hace _dispatch_run
    (antes de tocar disco), asi que basta con comprobar que
    map_client_data.json no existe."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    _seed_cliente_abc(tmp_path, con_contrato=True)
    monkeypatch.chdir(tmp_path)

    result = main(["run", "ABC", "--flow", "inexistente"])

    assert result == 1
    captured = capsys.readouterr()
    assert "inexistente" in captured.err
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err
    map_client_data = (
        tmp_path
        / "clients"
        / "ABC"
        / "020_outputs"
        / "020_onboarding"
        / "map_client_data.json"
    )
    assert not map_client_data.exists()
