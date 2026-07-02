"""Tests de integracion de client_scaffold (etapa integration_tester, banda tracer_bullet).

Fuente: 600_features/client_scaffold/tracer_bullet/spec.md y plan.md;
700_architecture/system_design.md (SS7 estructura de carpetas, SS8 contrato de
artefactos, SS13 multi-tenant).

A diferencia de tests/core/test_scaffold.py (unit, feature aislada), aqui se
verifica que create_client se integra correctamente con el resto del sistema:

- El arbol producido coincide EXACTAMENTE con el diseno de system_design SS7,
  bajo un `clients/` realista (no un `tmp_path` suelto de un solo caso).
- Aislamiento multi-tenant (SS13): varios clientes bajo el mismo `clients_root`
  no se contaminan entre si.
- El artefacto `client.yaml` que produce esta feature es consumible como
  contrato (SS8: "YAML = decision humana / configuracion") por un lector
  externo al modulo scaffold, tal como lo haria un flujo futuro (Discovery,
  client_context/T-014, etc.) sin acoplarse a los internos de create_client.
- Comportamiento de fallo temprano ante colisiones realistas (carpeta o
  archivo preexistente) sin excepciones crudas inesperadas.
- Creacion secuencial de varios clientes no deja estado compartido entre
  llamadas (sin variables de modulo mutables que persistan entre clientes).

Nota de alcance (spec SS No-Objetivos): la abstraccion Flow/ClientContext y la
capa CLI (`foda client new`) son responsabilidad de features futuras
(client_context T-014); create_client es una operacion de bootstrap previa al
pipeline, no un Flow. Por eso estos tests no invocan Flow.run(ctx): serian
fuera de alcance de esta feature.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from foda.core.scaffold import create_client


def _read_client_yaml(clients_root: Path, name: str) -> dict:
    """Lector externo minimo que simula como un flujo futuro (o
    client_context) consumiria el artefacto client.yaml producido por
    create_client, resolviendo la ruta de forma independiente del modulo
    scaffold (SS8: contrato de artefactos entre flujos)."""
    client_yaml = clients_root / name / "client.yaml"
    if not client_yaml.is_file():
        raise FileNotFoundError(
            f"client.yaml no encontrado para el cliente '{name}' en {clients_root}"
        )
    return yaml.safe_load(client_yaml.read_text(encoding="utf-8"))


def test_arbol_producido_coincide_exactamente_con_system_design_seccion_7(
    tmp_path: Path,
) -> None:
    """El arbol completo bajo clients_root/<name>/ coincide, entrada por
    entrada y de forma recursiva, con la estructura documentada en
    system_design SS7 para un cliente nuevo (sin subcarpetas por flujo
    todavia, ya que estas las crean los flujos al correr, no el scaffold)."""
    clients_root = tmp_path / "clients"
    clients_root.mkdir()

    client_dir = create_client("ACME", clients_root)

    def relative_tree(root: Path) -> set[str]:
        return {
            str(p.relative_to(root)).replace("\\", "/")
            for p in root.rglob("*")
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


def test_multiples_clientes_bajo_mismo_clients_root_quedan_aislados(
    tmp_path: Path,
) -> None:
    """SS13 (multi-tenant): crear varios clientes bajo el mismo clients_root
    no contamina el arbol ni el client.yaml de los demas; cada carpeta de
    cliente es independiente."""
    clients_root = tmp_path / "clients"
    clients_root.mkdir()

    create_client("ACME", clients_root)
    create_client("Globex", clients_root)
    create_client("Initech9", clients_root)

    top_level = {entry.name for entry in clients_root.iterdir()}
    assert top_level == {"ACME", "Globex", "Initech9"}

    for name in ("ACME", "Globex", "Initech9"):
        content = _read_client_yaml(clients_root, name)
        assert content["name"] == name

    # Escribir dentro de un cliente no debe afectar a los otros (aislamiento
    # de disco, no solo de nombre).
    sentinel = clients_root / "ACME" / "010_inputs" / "solo_de_acme.txt"
    sentinel.write_text("dato de ACME", encoding="utf-8")

    assert list((clients_root / "Globex" / "010_inputs").iterdir()) == []
    assert list((clients_root / "Initech9" / "010_inputs").iterdir()) == []


def test_client_yaml_es_consumible_como_contrato_por_un_lector_externo(
    tmp_path: Path,
) -> None:
    """SS8: client.yaml es la configuracion/identidad del cliente (YAML =
    decision humana/config) que otros componentes deben poder leer sin
    conocer los internos de create_client, solo el contrato de rutas
    documentado (clients_root/<name>/client.yaml -> {name, created_at})."""
    clients_root = tmp_path / "clients"
    clients_root.mkdir()

    create_client("Contoso", clients_root)

    content = _read_client_yaml(clients_root, "Contoso")

    assert set(content.keys()) == {"name", "created_at"}
    assert content["name"] == "Contoso"
    assert isinstance(content["created_at"], str)


def test_lector_externo_falla_temprano_y_claro_si_el_cliente_no_existe(
    tmp_path: Path,
) -> None:
    """Fallo temprano ante artefacto requerido ausente: un consumidor que
    intenta leer client.yaml de un cliente nunca creado obtiene un error
    claro (FileNotFoundError con mensaje explicito), no una excepcion cruda
    de bajo nivel."""
    clients_root = tmp_path / "clients"
    clients_root.mkdir()

    with pytest.raises(FileNotFoundError, match="Nope"):
        _read_client_yaml(clients_root, "Nope")


def test_creacion_secuencial_de_varios_clientes_no_deja_estado_compartido(
    tmp_path: Path,
) -> None:
    """Llamar create_client repetidamente para distintos clientes, con
    distintos clients_root, produce resultados totalmente independientes:
    no hay variables de modulo ni cache que arrastren datos de una llamada a
    la siguiente (regresion de integracion sobre un uso batch realista)."""
    resultados = []
    for i, name in enumerate(["Uno", "Dos9", "Tres-x"]):
        root = tmp_path / f"root_{i}"
        root.mkdir()
        client_dir = create_client(name, root)
        resultados.append((name, root, client_dir))

    for name, root, client_dir in resultados:
        assert client_dir == root / name
        content = _read_client_yaml(root, name)
        assert content["name"] == name
        # Ningun cliente ve carpetas de otro clients_root.
        assert {e.name for e in root.iterdir()} == {name}


def test_colision_con_archivo_preexistente_en_clients_root_lanza_fileexistserror(
    tmp_path: Path,
) -> None:
    """Caso de integracion realista no cubierto por el unit test de
    duplicado (que precrea una carpeta): si clients_root/<name> ya existe
    como ARCHIVO plano (p. ej. artefacto residual de otro proceso), create_client
    debe fallar con FileExistsError claro y no debe reemplazar el archivo ni
    dejar el arbol a medias."""
    clients_root = tmp_path / "clients"
    clients_root.mkdir()
    stray_file = clients_root / "Umbrella"
    stray_file.write_text("no soy una carpeta de cliente", encoding="utf-8")

    with pytest.raises(FileExistsError):
        create_client("Umbrella", clients_root)

    assert stray_file.is_file()
    assert stray_file.read_text(encoding="utf-8") == "no soy una carpeta de cliente"
