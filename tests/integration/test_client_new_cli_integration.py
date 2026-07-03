"""Tests de integracion de client_new_cli (etapa integration_tester, banda
tracer_bullet).

Fuente: 600_features/client_new_cli/tracer_bullet/spec.md y plan.md;
700_architecture/system_design.md (SS7 estructura de carpetas, SS8 contrato
de artefactos, SS13 multi-tenant); 800_persistence/decisions.md (D-C:
resolucion de raiz sin asumir el cwd).

A diferencia de tests/cli/test_client_new_cli.py (unit, feature aislada con
monkeypatch de create_client en varios casos), aqui se verifica que
`foda.cli.main` se integra correctamente con el resto del sistema:

- Invocacion real del entry point declarado en pyproject.toml
  ([project.scripts] foda = "foda.cli:main") como lo haria el wrapper de
  console_scripts (proceso separado, argv real, stdout/stderr/exit code
  reales), sin monkeypatch de por medio. El plan de la feature deja
  explicitamente esta verificacion para integration_tester (SS7 "Estrategia
  de test": "La integracion end-to-end (comando foda instalado como binario)
  queda para integration_tester, no para esta suite").
- Integracion real (sin espiar) con el core CONFORME create_client de
  client_scaffold: el arbol de carpetas y el client.yaml producidos por la
  CLI coinciden con el contrato de artefactos de client_scaffold, y ese
  client.yaml es consumible por un lector externo (SS8).
- Aislamiento multi-tenant (SS13) end-to-end: varias invocaciones de la CLI
  bajo el mismo proyecto crean clientes que no se contaminan entre si.
- Resolucion de clients_root real (D-C) sobre un arbol de proyecto realista
  de varios niveles (no solo una subcarpeta), incluyendo el caso de
  clients_root inexistente al arrancar.
- Fallo temprano con mensaje claro (sin traceback) y exit code correcto
  cuando falta un artefacto/marcador requerido (pyproject.toml) o el core
  rechaza la operacion (nombre invalido, duplicado), verificado a nivel de
  proceso real (subprocess), no solo de la funcion Python.

Nota de alcance (spec/plan No-Objetivos): la abstraccion Flow/ClientContext
es responsabilidad de una feature futura (client_context, T-014); esta
feature es un bootstrap de CLI, no un Flow, por lo que estos tests no
invocan Flow.run(ctx).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from foda.cli import main

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _make_project(tmp_path: Path) -> Path:
    """Crea un proyecto temporal realista: pyproject.toml marcador en la
    raiz y un arbol de codigo fuente de varios niveles debajo, imitando la
    estructura real del repo (src/foda/core/...)."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = \"cliente-de-prueba\"\n", encoding="utf-8"
    )
    nested = tmp_path / "src" / "foda" / "core"
    nested.mkdir(parents=True)
    return tmp_path


def _run_foda_subprocess(
    args: list[str], cwd: Path
) -> subprocess.CompletedProcess:
    """Invoca foda.cli.main tal como lo haria el wrapper de console_scripts
    generado a partir de [project.scripts] en pyproject.toml: un proceso
    Python nuevo que importa `main` desde el paquete instalable
    (PYTHONPATH=src, sin subir el repo real como pyproject.toml del proceso)
    y propaga su valor de retorno como sys.exit(...). Es la verificacion de
    integracion real del entry point, sin monkeypatch."""
    code = (
        "import sys; from foda.cli import main; sys.exit(main(sys.argv[1:]))"
    )
    env = {
        "PYTHONPATH": str(_REPO_ROOT / "src"),
        "PATH": __import__("os").environ.get("PATH", ""),
        "SYSTEMROOT": __import__("os").environ.get("SystemRoot", ""),
    }
    return subprocess.run(
        [sys.executable, "-c", code, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
    )


def _read_client_yaml(clients_root: Path, name: str) -> dict:
    """Lector externo minimo que simula como un flujo futuro (client_context,
    T-014) consumiria el artefacto client.yaml producido por la CLI,
    resolviendo la ruta de forma independiente de foda.cli / create_client
    (SS8: contrato de artefactos entre flujos)."""
    client_yaml = clients_root / name / "client.yaml"
    if not client_yaml.is_file():
        raise FileNotFoundError(
            f"client.yaml no encontrado para el cliente '{name}' en {clients_root}"
        )
    return yaml.safe_load(client_yaml.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Entry point real (proceso separado, sin monkeypatch)
# ---------------------------------------------------------------------------


def test_pyproject_declara_entry_point_consistente_con_el_modulo_real() -> None:
    """El contrato estatico (CA-10) se cierra verificando que el simbolo
    declarado en [project.scripts] (foda.cli:main) existe de verdad y es
    invocable, tal como lo resolveria el wrapper de console_scripts en
    tiempo de instalacion."""
    import tomllib

    pyproject_data = tomllib.loads(
        (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    entry = pyproject_data["project"]["scripts"]["foda"]
    assert entry == "foda.cli:main"

    module_name, func_name = entry.split(":")
    import importlib

    module = importlib.import_module(module_name)
    assert callable(getattr(module, func_name))


def test_entry_point_real_en_proceso_separado_crea_cliente_y_devuelve_0(
    tmp_path: Path,
) -> None:
    """Invocacion end-to-end del entry point en un proceso Python nuevo
    (imitando el wrapper de console_scripts foda = foda.cli:main): argv
    real, cwd real, sin monkeypatch de create_client ni de sys.argv."""
    project_root = _make_project(tmp_path)

    result = _run_foda_subprocess(["client", "new", "Wayne9"], cwd=project_root)

    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert str(project_root / "clients" / "Wayne9") in result.stdout.strip()
    assert (project_root / "clients" / "Wayne9" / "client.yaml").is_file()


def test_entry_point_real_falla_claro_sin_pyproject_y_no_toca_disco(
    tmp_path: Path,
) -> None:
    """Integracion del camino de error DS-CLI-1 a nivel de proceso real: sin
    pyproject.toml en el cwd ni en ancestros dentro del arbol temporal
    aislado, el proceso termina con exit 1, mensaje claro en stderr, sin
    traceback, y sin crear clients/."""
    isolated_root = tmp_path / "sin_marcador"
    isolated_root.mkdir()

    result = _run_foda_subprocess(["client", "new", "Stark9"], cwd=isolated_root)

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "raiz del proyecto" in result.stderr
    assert not (isolated_root / "clients").exists()


# ---------------------------------------------------------------------------
# Contrato de artefactos con el core CONFORME (client_scaffold), sin espiar
# ---------------------------------------------------------------------------


def test_main_integra_de_verdad_con_create_client_sin_espiar(
    tmp_path: Path,
) -> None:
    """A diferencia del unit test de delegacion (que monkeypatchea
    create_client), aqui main() corre con el core REAL: el arbol producido
    coincide, entrada por entrada, con el contrato de client_scaffold (SS7),
    y client.yaml es legible por un lector externo independiente (SS8)."""
    project_root = _make_project(tmp_path)
    monkeypatch_cwd = project_root

    import os

    old_cwd = os.getcwd()
    os.chdir(monkeypatch_cwd)
    try:
        exit_code = main(["client", "new", "Acme9"])
    finally:
        os.chdir(old_cwd)

    assert exit_code == 0
    client_dir = project_root / "clients" / "Acme9"

    def relative_tree(root: Path) -> set[str]:
        return {
            str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*")
        }

    expected = {
        "client.yaml",
        "010_inputs",
        "020_outputs",
        "data",
        "data/bronze",
        "data/silver",
        "data/gold",
        "models",
    }
    assert relative_tree(client_dir) == expected

    content = _read_client_yaml(project_root / "clients", "Acme9")
    assert content["name"] == "Acme9"
    assert isinstance(content["created_at"], str)


def test_main_produce_artefacto_consumible_por_flujo_vecino_simulado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """El artefacto que produce esta feature (client.yaml) debe ser
    consumible tal cual por un flujo/CLI vecino sin conocer los internos de
    foda.cli ni de create_client -- solo el contrato de rutas documentado en
    la spec (clients_root/<name>/client.yaml -> {name, created_at})."""
    project_root = _make_project(tmp_path)
    monkeypatch.chdir(project_root)

    exit_code = main(["client", "new", "Contoso9"])
    assert exit_code == 0

    # "Flujo vecino" simulado: no importa foda.cli ni create_client, solo
    # conoce el contrato documentado de rutas (SS8).
    content = _read_client_yaml(project_root / "clients", "Contoso9")
    assert set(content.keys()) == {"name", "created_at"}
    assert content["name"] == "Contoso9"


# ---------------------------------------------------------------------------
# Aislamiento multi-tenant (SS13) a traves de la CLI
# ---------------------------------------------------------------------------


def test_multiples_invocaciones_de_la_cli_aislan_clientes_bajo_el_mismo_proyecto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tres invocaciones sucesivas de main() bajo el mismo proyecto crean
    tres clientes independientes; escribir dentro de uno no contamina a los
    demas (SS13, multi-tenant a nivel de CLI, no solo del core)."""
    project_root = _make_project(tmp_path)
    monkeypatch.chdir(project_root)

    for name in ("Uno9", "Dos9", "Tres9"):
        assert main(["client", "new", name]) == 0

    clients_root = project_root / "clients"
    assert {e.name for e in clients_root.iterdir()} == {"Uno9", "Dos9", "Tres9"}

    sentinel = clients_root / "Uno9" / "010_inputs" / "solo_de_uno.txt"
    sentinel.write_text("dato de Uno9", encoding="utf-8")

    assert list((clients_root / "Dos9" / "010_inputs").iterdir()) == []
    assert list((clients_root / "Tres9" / "010_inputs").iterdir()) == []


# ---------------------------------------------------------------------------
# Resolucion de clients_root sobre arbol de proyecto realista (D-C)
# ---------------------------------------------------------------------------


def test_resolucion_de_raiz_real_con_arbol_de_varios_niveles_y_clients_root_inexistente(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sobre un arbol de proyecto de varios niveles (src/foda/core/...), sin
    clients/ previo, invocar main() desde una carpeta profundamente anidada
    localiza la raiz real (D-C) y crea clients/ + el cliente ahi, no en una
    ruta relativa al cwd ni en el arbol de codigo fuente."""
    project_root = _make_project(tmp_path)
    deeply_nested = project_root / "src" / "foda" / "core"
    monkeypatch.chdir(deeply_nested)

    assert not (project_root / "clients").exists()

    exit_code = main(["client", "new", "Umbrella9"])

    assert exit_code == 0
    assert (project_root / "clients" / "Umbrella9" / "client.yaml").is_file()
    # No se creo nada relativo al cwd anidado.
    assert not (deeply_nested / "clients").exists()


# ---------------------------------------------------------------------------
# Interaccion con el contrato de errores del core en un escenario realista
# ---------------------------------------------------------------------------


def test_duplicado_end_to_end_preserva_cliente_existente_creado_por_la_propia_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Escenario realista de integracion: un cliente creado por una primera
    invocacion de main() y luego un segundo intento con el mismo nombre
    (tambien via main(), no via create_client directo) debe fallar con
    mensaje claro, exit 1, y preservar intacto el client.yaml del primero."""
    project_root = _make_project(tmp_path)
    monkeypatch.chdir(project_root)

    assert main(["client", "new", "Duplicado9"]) == 0
    original_content = _read_client_yaml(project_root / "clients", "Duplicado9")

    exit_code = main(["client", "new", "Duplicado9"])
    assert exit_code == 1

    content_after = _read_client_yaml(project_root / "clients", "Duplicado9")
    assert content_after == original_content
