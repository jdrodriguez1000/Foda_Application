# Verification — client_new_cli (banda tracer_bullet)

> Artefacto de la etapa 8 (`spec_verifier`). Verifica que lo construido **cumple la
> especificación aprobada** (`spec.md`). Auditoría, no construcción: no se añade
> funcionalidad ni casos; se comprueba cobertura criterio → evidencia y se corre la
> suite completa.
>
> Fuentes: `spec.md`, `definition.md`, `plan.md`, `state.json` de esta celda;
> `src/foda/cli.py`, `pyproject.toml`, `tests/cli/test_client_new_cli.py`,
> `tests/integration/test_client_new_cli_integration.py`.

---

## Veredicto: **CONFORME**

Los 10 criterios de aceptación (`CA-01`…`CA-10`) de `spec.md` tienen evidencia
directa (test unitario y/o de integración que los cubre). La suite completa está en
verde (**54 passed**). El alcance de `definition.md` se cumple (in scope hecho, out of
scope respetado) y las restricciones aplicables (Python 3.13+, cero dependencias
nuevas, D-C, `[project.scripts]`) se satisfacen. No se detectan huecos.

---

## Matriz de trazabilidad (criterio → evidencia → estado)

| CA | Criterio (resumen) | Evidencia (test) | Estado |
|---|---|---|---|
| CA-01 | `main(["client","new","ABC"])` bajo proyecto temporal crea `<raíz>/clients/ABC/` (árbol + `client.yaml`) | `tests/cli/...::test_main_camino_feliz_devuelve_0`, `::test_main_camino_exito_crea_arbol_de_cliente`; integración `::test_main_integra_de_verdad_con_create_client_sin_espiar` (árbol comparado entrada por entrada) | Cubierto |
| CA-02 | Éxito → devuelve `0` y `stdout` contiene la ruta de `<raíz>/clients/ABC` | `tests/cli/...::test_main_camino_exito_stdout_contiene_ruta_del_cliente`; integración `::test_entry_point_real_en_proceso_separado_crea_cliente_y_devuelve_0` | Cubierto |
| CA-03 | No reimplementa negocio: `create_client` invocado 1 vez con `("ABC", <raíz>/clients)` | `tests/cli/...::test_main_delega_en_create_client_una_vez_con_argumentos_correctos` (spy `assert_called_once_with`) | Cubierto |
| CA-04 | Desde subcarpeta anidada, crea en `<raíz>/clients/ABC/` (raíz real hacia arriba), no relativo al cwd | `tests/cli/...::test_main_resuelve_raiz_real_desde_subcarpeta_anidada`; integración `::test_resolucion_de_raiz_real_con_arbol_de_varios_niveles_y_clients_root_inexistente` | Cubierto |
| CA-05 | `<raíz>/clients/` inexistente → la crea y crea `ABC/` dentro, código `0` | `tests/cli/...::test_main_crea_clients_root_inexistente_primer_cliente` | Cubierto |
| CA-06 | Sin `pyproject.toml` en cwd ni ancestros → `1`, mensaje en `stderr` (raíz), sin `"Traceback"`, nada creado (DS-CLI-1) | `tests/cli/...::test_main_sin_pyproject_devuelve_1_y_no_toca_disco`; integración a nivel de proceso `::test_entry_point_real_falla_claro_sin_pyproject_y_no_toca_disco` | Cubierto |
| CA-07 | `NAME` que `create_client` rechaza con `ValueError` (`"a b"`, `".."`, `"-x"`) → `1`, `stderr` legible, sin `"Traceback"`, nada creado | `tests/cli/...::test_main_nombre_invalido_devuelve_1_y_no_crea_nada` (parametrizado 3 nombres) | Cubierto |
| CA-08 | `<raíz>/clients/ABC/` ya existe → `1`, `stderr` legible sin `"Traceback"`, centinela intacto | `tests/cli/...::test_main_duplicado_devuelve_1_y_preserva_cliente_existente`; integración `::test_duplicado_end_to_end_preserva_cliente_existente_creado_por_la_propia_cli` | Cubierto |
| CA-09 | Suite propia de la CLI (independiente del core) que ejercita éxito, subcarpeta, `clients/` inexistente y los tres caminos de error, toda en verde | `tests/cli/test_client_new_cli.py` (12 tests, suite propia; sin reutilizar los del core `client_scaffold`) — 46 verdes en el bucle TDD | Cubierto |
| CA-10 | `pyproject.toml` declara `[project.scripts] foda = "foda.cli:main"` y `main(argv)` invocable devolviendo `int` | `tests/cli/...::test_pyproject_declara_entry_point_y_main_es_invocable`; integración `::test_pyproject_declara_entry_point_consistente_con_el_modulo_real` (resuelve e importa el símbolo real) | Cubierto |

**Casos límite de `argparse` (spec §Casos Límite, DS-CLI-3):** `NAME` ausente y
subcomando desconocido → código `2`. Cubiertos por
`tests/cli/...::test_main_sin_name_termina_con_codigo_2` y
`::test_main_subcomando_desconocido_termina_con_codigo_2`.

---

## Resultado de la suite completa

```
python -m pytest -q  ->  54 passed in ~0.5s   (VERDE)
```

Desglose: 46 tests del bucle TDD (12 de la CLI `tests/cli/` + 34 preexistentes del
core y otros) + 8 tests de integración de esta feature
(`tests/integration/test_client_new_cli_integration.py`). Sin fallos, sin regresiones.

---

## Cumplimiento de alcance y restricciones

**Alcance (`definition.md`):**
- **In scope hecho:** comando `foda client new <NAME>` en `src/foda/cli.py` que resuelve
  la raíz hacia arriba (marcador `pyproject.toml`, D-C), delega en
  `create_client(name, clients_root)` sin reimplementar negocio, y traduce éxito
  (ruta + código 0) / error (mensaje claro + código ≠ 0). Suite propia de la CLI (D-B,
  NC-5). Todas las HU (HU-01…HU-05) trazadas a ≥1 CA cubierto.
- **Out of scope respetado:** no se añade lógica de negocio (el core `create_client` no
  se toca ni se duplica); no se implementan otros subcomandos (`list`, `run`, …), ni
  `ClientContext`, ni flags/env para `clients_root`, ni `--force`, ni normalización de
  mayúsculas / nombres reservados de Windows. `src/foda/cli.py` es capa fina de cableado.

**Restricciones:**
- **Python 3.13+ (R1):** `pyproject.toml` declara `requires-python = ">=3.13"`. ✓
- **Cero dependencias nuevas (D-027):** `cli.py` usa solo stdlib (`argparse`, `pathlib`,
  `sys`); `dependencies` sigue siendo solo `PyYAML`. ✓
- **D-C (no asumir el cwd como raíz):** `_find_project_root` sube directorio por
  directorio buscando `pyproject.toml`; sin flag, sin env, sin suponer cwd. ✓
- **Entrada de consola:** `[project.scripts] foda = "foda.cli:main"` presente; símbolo
  real importable y callable (verificado por integración). ✓
- **Contrato de códigos de salida:** `0` éxito · `1` error semántico (nombre inválido /
  duplicado / raíz no encontrada) · `2` error de parseo de `argparse`. Verificado. ✓
- **Sin traza cruda:** los tests de error comprueban ausencia de `"Traceback"` en
  `stdout`/`stderr`. ✓
- **LLM aislado / YAML in–JSON out:** no aplican a esta feature (bootstrap de CLI, sin
  LLM; el `client.yaml` lo produce el core CONFORME `create_client`, no esta capa).

---

## Hallazgos / huecos

Ninguno. No se detectan criterios parciales ni no cubiertos, ni desviaciones de alcance
o restricciones. No procede retorno a etapas anteriores.

Observación (sin impacto en el veredicto): el caso de test 8 documenta una corrección
mecánica de aserción realizada por `tdd_coder` (la comprobación de no-creación para el
nombre `".."` se reescribió porque `tmp_path/"clients"/".."` se resuelve a `tmp_path`,
que siempre existe). La corrección es correcta y el contrato observable de CA-07 queda
verificado.

---

## Cierre

Feature `client_new_cli` (banda `tracer_bullet`): **CONFORME**. Se cierra la cadena
SDD/TDD para esta celda. `state.json`: `stages.spec_verifier.status = "done"`,
`status = "done"`, `current_stage = "completed"`.
