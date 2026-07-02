"""Tests unitarios de create_client (feature client_scaffold, banda tracer_bullet).

Fuente: 600_features/client_scaffold/tracer_bullet/spec.md (CA-xx) y plan.md (casos TDD).
Bucle TDD: un test por caso, ejecutado en orden (state.json -> stages.tdd.cases).
"""

import re
from pathlib import Path

import pytest
import yaml

from foda.core.scaffold import create_client

_CREATED_AT_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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


def test_create_client_data_contiene_capas_medallion_vacias(tmp_path: Path) -> None:
    """Caso 4 (CA-03): tmp/ABC/data/ contiene bronze/, silver/ y gold/, y las
    tres estan vacias (capa medallion)."""
    create_client("ABC", tmp_path)

    data_dir = tmp_path / "ABC" / "data"
    bronze_dir = data_dir / "bronze"
    silver_dir = data_dir / "silver"
    gold_dir = data_dir / "gold"

    assert bronze_dir.is_dir()
    assert silver_dir.is_dir()
    assert gold_dir.is_dir()
    assert list(bronze_dir.iterdir()) == []
    assert list(silver_dir.iterdir()) == []
    assert list(gold_dir.iterdir()) == []


def test_create_client_models_existe_y_vacia(tmp_path: Path) -> None:
    """Caso 5 (CA-04): tmp/ABC/models/ existe y esta vacia, sin subcarpetas
    de version."""
    create_client("ABC", tmp_path)

    models_dir = tmp_path / "ABC" / "models"

    assert models_dir.is_dir()
    assert list(models_dir.iterdir()) == []


def test_create_client_yaml_parsea_a_mapa_con_name_abc(tmp_path: Path) -> None:
    """Caso 6 (CA-06): tmp/ABC/client.yaml es YAML valido que parsea a un
    mapa cuya clave name == "ABC"."""
    create_client("ABC", tmp_path)

    client_yaml = tmp_path / "ABC" / "client.yaml"
    content = yaml.safe_load(client_yaml.read_text(encoding="utf-8"))

    assert isinstance(content, dict)
    assert content["name"] == "ABC"


def test_create_client_yaml_created_at_cumple_patron_iso(tmp_path: Path) -> None:
    """Caso 7 (CA-06): tmp/ABC/client.yaml tiene una clave created_at cuyo
    valor (str) cumple el patron ISO-8601 de fecha ^\\d{4}-\\d{2}-\\d{2}$."""
    create_client("ABC", tmp_path)

    client_yaml = tmp_path / "ABC" / "client.yaml"
    content = yaml.safe_load(client_yaml.read_text(encoding="utf-8"))

    assert isinstance(content, dict)
    created_at = content["created_at"]
    assert isinstance(created_at, str)
    assert _CREATED_AT_PATTERN.match(created_at)


def test_create_client_nombre_vacio_lanza_valueerror_y_no_crea_nada(tmp_path: Path) -> None:
    """Caso 9 (CA-08, CA-11): create_client("", tmp) lanza ValueError y no
    crea ninguna carpeta bajo tmp (tmp queda tal cual estaba antes de la
    llamada, sin entradas nuevas)."""
    with pytest.raises(ValueError):
        create_client("", tmp_path)

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("name", ["   ", "ab c"])
def test_create_client_nombre_con_espacios_lanza_valueerror_y_no_crea_nada(
    tmp_path: Path, name: str
) -> None:
    """Caso 10 (CA-08, CA-11): create_client(nombre, tmp) lanza ValueError
    para un nombre solo-espacios ("   ") o con espacio interior ("ab c"), y
    no crea ninguna carpeta bajo tmp (tmp queda tal cual estaba antes de la
    llamada, sin entradas nuevas). Cada nombre usa su propia clients_root
    (subcarpeta de tmp_path) para evitar interferencia entre parametrizaciones."""
    clients_root = tmp_path / "root"
    clients_root.mkdir()

    with pytest.raises(ValueError):
        create_client(name, clients_root)

    assert list(clients_root.iterdir()) == []


@pytest.mark.parametrize("name", ["-abc", "_abc"])
def test_create_client_nombre_inicia_guion_o_underscore_lanza_valueerror_y_no_crea_nada(
    tmp_path: Path, name: str
) -> None:
    """Caso 11 (CA-08, CA-11): create_client(nombre, tmp) lanza ValueError
    para un nombre que empieza por guion ("-abc") o por underscore ("_abc")
    (DS-1: el primer caracter debe ser alfanumerico), y no crea ninguna
    carpeta bajo tmp (tmp queda tal cual estaba antes de la llamada, sin
    entradas nuevas). Cada nombre usa su propia clients_root (subcarpeta de
    tmp_path) para evitar interferencia entre parametrizaciones."""
    clients_root = tmp_path / "root"
    clients_root.mkdir()

    with pytest.raises(ValueError):
        create_client(name, clients_root)

    assert list(clients_root.iterdir()) == []


@pytest.mark.parametrize("name", ["a/b", "a\\b"])
def test_create_client_nombre_con_separador_de_ruta_lanza_valueerror_y_no_crea_nada(
    tmp_path: Path, name: str
) -> None:
    """Caso 12 (CA-08, CA-11): create_client(nombre, tmp) lanza ValueError
    para un nombre con separador de ruta, ya sea "/" ("a/b") o "\\" ("a\\b")
    (DS-1: el conjunto permitido es solo letras/digitos/_/-; los separadores
    de ruta quedan fuera y deben rechazarse antes de tocar el filesystem,
    para evitar escritura fuera de clients_root). No debe crearse ninguna
    carpeta bajo clients_root (tmp queda tal cual estaba antes de la
    llamada, sin entradas nuevas). Cada nombre usa su propia clients_root
    (subcarpeta de tmp_path) para evitar interferencia entre
    parametrizaciones."""
    clients_root = tmp_path / "root"
    clients_root.mkdir()

    with pytest.raises(ValueError):
        create_client(name, clients_root)

    assert list(clients_root.iterdir()) == []


@pytest.mark.parametrize("name", [".", ".."])
def test_create_client_nombre_ruta_especial_lanza_valueerror_y_no_crea_nada(
    tmp_path: Path, name: str
) -> None:
    """Caso 13 (CA-08, CA-11): create_client(nombre, tmp) lanza ValueError
    para un nombre de ruta especial, ya sea "." o ".." (DS-1: el conjunto
    permitido es solo letras/digitos/_/-; estos nombres especiales de
    filesystem quedan fuera y deben rechazarse antes de tocar el
    filesystem, para evitar que clients_root / name resuelva a la propia
    clients_root o a su carpeta padre). No debe crearse ninguna carpeta
    nueva bajo clients_root (tmp queda tal cual estaba antes de la
    llamada, sin entradas nuevas). Cada nombre usa su propia clients_root
    (subcarpeta de tmp_path) para evitar interferencia entre
    parametrizaciones."""
    clients_root = tmp_path / "root"
    clients_root.mkdir()

    with pytest.raises(ValueError):
        create_client(name, clients_root)

    assert list(clients_root.iterdir()) == []


@pytest.mark.parametrize("name", ["ab.c", "a!b", "a@b"])
def test_create_client_nombre_con_caracter_no_permitido_lanza_valueerror_y_no_crea_nada(
    tmp_path: Path, name: str
) -> None:
    """Caso 14 (CA-08, CA-11): create_client(nombre, tmp) lanza ValueError
    para un nombre con punto interior ("ab.c") o con un caracter fuera del
    conjunto permitido por DS-1 (letras/digitos ASCII, "_", "-"), ya sea "!"
    ("a!b") o "@" ("a@b"). No debe crearse ninguna carpeta nueva bajo
    clients_root (tmp queda tal cual estaba antes de la llamada, sin
    entradas nuevas). Cada nombre usa su propia clients_root (subcarpeta de
    tmp_path) para evitar interferencia entre parametrizaciones."""
    clients_root = tmp_path / "root"
    clients_root.mkdir()

    with pytest.raises(ValueError):
        create_client(name, clients_root)

    assert list(clients_root.iterdir()) == []


@pytest.mark.parametrize("name", ["X", "9lives", "Client_1-a"])
def test_create_client_nombres_validos_representativos_crean_arbol_completo(
    tmp_path: Path, name: str
) -> None:
    """Caso 8 (CA-09): para cada nombre valido representativo ("X", "9lives",
    "Client_1-a"), create_client crea el arbol completo sin lanzar excepcion.
    Cada nombre usa su propia clients_root (subcarpeta de tmp_path) para
    evitar colision de duplicado entre parametrizaciones."""
    clients_root = tmp_path / name

    result = create_client(name, clients_root)

    client_dir = clients_root / name
    assert result == client_dir
    assert client_dir.is_dir()
    assert (client_dir / "client.yaml").is_file()
