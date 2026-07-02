"""Tests unitarios de create_client (feature client_scaffold, banda tracer_bullet).

Fuente: 600_features/client_scaffold/tracer_bullet/spec.md (CA-xx) y plan.md (casos TDD).
Bucle TDD: un test por caso, ejecutado en orden (state.json -> stages.tdd.cases).
"""

from pathlib import Path

from foda.core.scaffold import create_client


def test_create_client_crea_directorio_y_devuelve_su_path(tmp_path: Path) -> None:
    """Caso 1 (CA-01, CA-07): create_client("ABC", tmp) crea tmp/ABC/ y devuelve
    un Path que apunta a esa carpeta."""
    result = create_client("ABC", tmp_path)

    expected = tmp_path / "ABC"
    assert expected.is_dir()
    assert result == expected
