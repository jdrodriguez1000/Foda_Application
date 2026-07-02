"""Suite de tests de la CLI `foda client new <NAME>` (feature client_new_cli,
banda tracer_bullet). Independiente de los tests del core `client_scaffold`
(CA-09). Invoca `main(argv)` en proceso, bajo un proyecto temporal (`tmp_path`
con un `pyproject.toml` marcador y `monkeypatch.chdir`).

Fuente: 600_features/client_new_cli/tracer_bullet/plan.md (caso 1 de 12).
"""

from unittest.mock import MagicMock

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


def test_main_camino_feliz_devuelve_0(tmp_path, monkeypatch):
    """Caso 1 (CA-01, CA-10): con el cwd dentro de un proyecto temporal
    (existe <raiz>/pyproject.toml), main(["client","new","ABC"]) devuelve
    el int 0 (camino feliz, invocabilidad)."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = main(["client", "new", "ABC"])

    assert result == 0
