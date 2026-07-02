"""Suite de tests de la CLI `foda client new <NAME>` (feature client_new_cli,
banda tracer_bullet). Independiente de los tests del core `client_scaffold`
(CA-09). Invoca `main(argv)` en proceso, bajo un proyecto temporal (`tmp_path`
con un `pyproject.toml` marcador y `monkeypatch.chdir`).

Fuente: 600_features/client_new_cli/tracer_bullet/plan.md (caso 1 de 12).
"""

from foda.cli import main


def test_main_camino_feliz_devuelve_0(tmp_path, monkeypatch):
    """Caso 1 (CA-01, CA-10): con el cwd dentro de un proyecto temporal
    (existe <raiz>/pyproject.toml), main(["client","new","ABC"]) devuelve
    el int 0 (camino feliz, invocabilidad)."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = main(["client", "new", "ABC"])

    assert result == 0
