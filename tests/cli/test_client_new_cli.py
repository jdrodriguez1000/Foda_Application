"""Suite de tests de la CLI `foda client new <NAME>` (feature client_new_cli,
banda tracer_bullet). Independiente de los tests del core `client_scaffold`
(CA-09). Invoca `main(argv)` en proceso, bajo un proyecto temporal (`tmp_path`
con un `pyproject.toml` marcador y `monkeypatch.chdir`).

Fuente: 600_features/client_new_cli/tracer_bullet/plan.md (caso 1 de 12).
"""

from foda.cli import main


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


def test_main_camino_feliz_devuelve_0(tmp_path, monkeypatch):
    """Caso 1 (CA-01, CA-10): con el cwd dentro de un proyecto temporal
    (existe <raiz>/pyproject.toml), main(["client","new","ABC"]) devuelve
    el int 0 (camino feliz, invocabilidad)."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = main(["client", "new", "ABC"])

    assert result == 0
