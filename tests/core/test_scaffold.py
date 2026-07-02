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


def test_create_client_crea_arbol_de_primer_nivel_completo(tmp_path: Path) -> None:
    """Caso 2 (CA-02): bajo tmp/ABC/ existen exactamente estas entradas de
    primer nivel: archivo client.yaml y carpetas 010_inputs/, 020_outputs/,
    data/, models/ (ni mas ni menos)."""
    create_client("ABC", tmp_path)

    client_dir = tmp_path / "ABC"
    entries = {entry.name for entry in client_dir.iterdir()}

    assert entries == {"client.yaml", "010_inputs", "020_outputs", "data", "models"}
    assert (client_dir / "client.yaml").is_file()
    assert (client_dir / "010_inputs").is_dir()
    assert (client_dir / "020_outputs").is_dir()
    assert (client_dir / "data").is_dir()
    assert (client_dir / "models").is_dir()


def test_create_client_010_inputs_y_020_outputs_existen_y_vacias(tmp_path: Path) -> None:
    """Caso 3 (CA-05): tmp/ABC/010_inputs/ y tmp/ABC/020_outputs/ existen y
    estan vacias (sin subcarpetas por flujo)."""
    create_client("ABC", tmp_path)

    client_dir = tmp_path / "ABC"
    inputs_dir = client_dir / "010_inputs"
    outputs_dir = client_dir / "020_outputs"

    assert inputs_dir.is_dir()
    assert outputs_dir.is_dir()
    assert list(inputs_dir.iterdir()) == []
    assert list(outputs_dir.iterdir()) == []
