"""Suite de tests de la CLI `foda client new <NAME>` (feature client_new_cli,
banda tracer_bullet). Independiente de los tests del core `client_scaffold`
(CA-09). Invoca `main(argv)` en proceso, bajo un proyecto temporal (`tmp_path`
con un `pyproject.toml` marcador y `monkeypatch.chdir`).

Fuente: 600_features/client_new_cli/tracer_bullet/plan.md (caso 1 de 12).
"""

from unittest.mock import MagicMock

import pytest

import foda.cli
from foda.cli import main


def test_main_delega_en_create_client_una_vez_con_argumentos_correctos(tmp_path, monkeypatch):
    """Caso 4 (CA-03): con create_client espiado/monkeypatcheado,
    main(["client","new","ABC"]) lo invoca exactamente una vez con
    name == "ABC" y clients_root == <raiz>/clients."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    spy = MagicMock(return_value=tmp_path / "clients" / "ABC")
    monkeypatch.setattr(foda.cli, "create_client", spy)

    main(["client", "new", "ABC"])

    spy.assert_called_once_with("ABC", tmp_path / "clients")


def test_main_camino_exito_crea_arbol_de_cliente(tmp_path, monkeypatch):
    """Caso 2 (CA-01): en el camino de exito, main(...) crea el arbol de
    cliente en <raiz>/clients/ABC/ (existe <raiz>/clients/ABC/client.yaml y
    las carpetas del scaffold: 010_inputs/, 020_outputs/, data/, models/)."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["client", "new", "ABC"])

    client_dir = tmp_path / "clients" / "ABC"
    assert (client_dir / "client.yaml").is_file()
    assert (client_dir / "010_inputs").is_dir()
    assert (client_dir / "020_outputs").is_dir()
    assert (client_dir / "data").is_dir()
    assert (client_dir / "models").is_dir()


def test_main_camino_exito_stdout_contiene_ruta_del_cliente(tmp_path, monkeypatch, capsys):
    """Caso 3 (CA-02): en el camino de exito, la salida capturada en stdout
    contiene la ruta de <raiz>/clients/ABC."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["client", "new", "ABC"])

    captured = capsys.readouterr()
    expected_path = tmp_path / "clients" / "ABC"
    assert str(expected_path) in captured.out


def test_main_crea_clients_root_inexistente_primer_cliente(tmp_path, monkeypatch):
    """Caso 5 (CA-05): cuando <raiz>/clients/ no existe todavia,
    main(["client","new","ABC"]) la crea y crea ABC/ dentro, terminando con
    codigo 0 (primer cliente del proyecto)."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert not (tmp_path / "clients").exists()

    result = main(["client", "new", "ABC"])

    assert result == 0
    assert (tmp_path / "clients").is_dir()
    assert (tmp_path / "clients" / "ABC").is_dir()


def test_main_resuelve_raiz_real_desde_subcarpeta_anidada(tmp_path, monkeypatch):
    """Caso 6 (CA-04): con el cwd en una subcarpeta anidada (p. ej.
    <raiz>/src/foda/), main(["client","new","ABC"]) crea el cliente en
    <raiz>/clients/ABC/ (raiz real localizada hacia arriba), no relativo
    al cwd."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    nested = tmp_path / "src" / "foda"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    result = main(["client", "new", "ABC"])

    assert result == 0
    assert (tmp_path / "clients" / "ABC").is_dir()
    assert not (nested / "clients").exists()


def test_main_sin_pyproject_devuelve_1_y_no_toca_disco(tmp_path, monkeypatch, capsys):
    """Caso 7 (CA-06, DS-CLI-1): con un cwd sin pyproject.toml ni en el ni
    en ancestros, main(["client","new","ABC"]) devuelve 1, escribe en
    stderr un mensaje que menciona que no se encontro la raiz del
    proyecto, la salida no contiene "Traceback", y no se crea ninguna
    carpeta clients/ ni de cliente."""
    # Aislar de cualquier pyproject.toml real de ancestros: raiz de un
    # filesystem temporal sin marcador.
    no_project_root = tmp_path / "sin_proyecto"
    no_project_root.mkdir()
    monkeypatch.chdir(no_project_root)
    monkeypatch.setattr(
        "foda.cli._find_project_root", lambda start: None
    )

    result = main(["client", "new", "ABC"])

    captured = capsys.readouterr()
    assert result == 1
    assert "raiz" in captured.err.lower() or "raíz" in captured.err.lower()
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err
    assert not (no_project_root / "clients").exists()


@pytest.mark.parametrize("nombre_invalido", ["a b", "..", "-x"])
def test_main_nombre_invalido_devuelve_1_y_no_crea_nada(
    nombre_invalido, tmp_path, monkeypatch, capsys
):
    """Caso 8 (CA-07): para un NAME que create_client rechaza con
    ValueError (p. ej. "a b", "..", "-x"), main(["client","new",NAME])
    devuelve 1, escribe un mensaje legible en stderr, la salida no
    contiene "Traceback", y no se crea ninguna carpeta para ese nombre."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = main(["client", "new", nombre_invalido])

    captured = capsys.readouterr()
    assert result == 1
    assert captured.err.strip() != ""
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err
    assert not (tmp_path / "clients" / nombre_invalido).exists()


def test_main_camino_feliz_devuelve_0(tmp_path, monkeypatch):
    """Caso 1 (CA-01, CA-10): con el cwd dentro de un proyecto temporal
    (existe <raiz>/pyproject.toml), main(["client","new","ABC"]) devuelve
    el int 0 (camino feliz, invocabilidad)."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = main(["client", "new", "ABC"])

    assert result == 0
