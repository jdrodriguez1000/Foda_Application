# Verification — client_scaffold (banda `tracer_bullet`)

> Artefacto de la etapa 8 (`spec_verifier`). Verifica que lo construido cumple la especificación
> aprobada (`spec.md`, criterios `CA-01…CA-11`), deja constancia de la trazabilidad criterio →
> evidencia y del resultado de la suite, y cierra la feature/banda.
>
> Fuentes: `spec.md` (fuente de verdad), `definition.md` (alcance/HU), `plan.md` (casos TDD/tareas),
> `700_architecture/system_design.md` (§3 R1–R9, §7, §10), `800_persistence/decisions.md`
> (D-010, D-016, D-019, D-027, D-028; D-032 / GATE PA-3).

---

## Veredicto

**CONFORME** respecto a los criterios de aceptación `CA-01…CA-11` de `spec.md`.

- Los **11 criterios de aceptación** tienen evidencia (test verde y/o comportamiento comprobable).
- La **suite completa está en verde**: `32 passed` (26 unit + 6 integración).
- El **out of scope** de la `definition.md` se respeta.
- Se registran **tres hallazgos no bloqueantes** (F-1, F-2, F-3, ver abajo). Ninguno deja un `CA`
  sin cobertura ni rompe la suite; se documentan como trabajo residual / limitaciones conocidas
  para que el humano decida su tratamiento en bandas posteriores.

---

## Matriz de trazabilidad (CA → evidencia → estado)

| CA | Criterio (resumen) | Evidencia (test) | Estado |
|---|---|---|---|
| CA-01 | `create_client("ABC", tmp)` crea `tmp/ABC/`. | `tests/core/test_scaffold.py::test_create_client_crea_directorio_y_devuelve_su_path` | Cubierto |
| CA-02 | Primer nivel exacto: `client.yaml` + `010_inputs/`, `020_outputs/`, `data/`, `models/`. | `...::test_create_client_crea_arbol_de_primer_nivel_completo` (aserción de conjunto) + integración `...::test_arbol_producido_coincide_exactamente_con_system_design_seccion_7` | Cubierto |
| CA-03 | `data/` con `bronze/`, `silver/`, `gold/` vacías. | `...::test_create_client_data_contiene_capas_medallion_vacias` | Cubierto |
| CA-04 | `models/` existe y vacía (sin versionado). | `...::test_create_client_models_existe_y_vacia` | Cubierto |
| CA-05 | `010_inputs/` y `020_outputs/` existen y vacías. | `...::test_create_client_010_inputs_y_020_outputs_existen_y_vacias` | Cubierto |
| CA-06 | `client.yaml` YAML válido con `name == "ABC"` y `created_at` que cumple `^\d{4}-\d{2}-\d{2}$`. | `...::test_create_client_yaml_parsea_a_mapa_con_name_abc` + `...::test_create_client_yaml_created_at_cumple_patron_iso` + integración `...::test_client_yaml_es_consumible_como_contrato_por_un_lector_externo` | Cubierto (ver F-3) |
| CA-07 | Devuelve `Path` que apunta a `tmp/ABC`. | `...::test_create_client_crea_directorio_y_devuelve_su_path` (`assert result == expected`) | Cubierto |
| CA-08 | Nombres inválidos → `ValueError`, nada creado. | Casos 9–16: `test_..._nombre_vacio...`, `..._con_espacios...`, `..._inicia_guion_o_underscore...`, `..._con_separador_de_ruta...`, `..._ruta_especial...`, `..._con_caracter_no_permitido...`, `..._no_ascii...`, `..._muy_largo...` (cubren `""`, solo/interior espacios, `-`/`_` inicial, `/`/`\`, `.`/`..`, punto interior, `!`/`@`, no-ASCII, longitud 65) | Cubierto |
| CA-09 | Nombres válidos representativos (`"X"`, `"9lives"`, `"Client_1-a"`) crean árbol completo. | `...::test_create_client_nombres_validos_representativos_crean_arbol_completo` (parametrizado) | Cubierto |
| CA-10 | Duplicado → `FileExistsError`, contenido preexistente intacto. | `...::test_create_client_duplicado_lanza_fileexistserror_y_preserva_contenido` + integración `...::test_colision_con_archivo_preexistente_en_clients_root_lanza_fileexistserror` | Cubierto |
| CA-11 | Validación-primero: tras `ValueError`/`FileExistsError`, el FS para ese nombre queda idéntico. | Aserciones `list(clients_root.iterdir()) == []` en los casos 9–16 y preservación de contenido/entradas en el caso 17 (`assert list(client_dir.iterdir()) == [sentinel]`) | Cubierto |

**Resultado:** 11/11 criterios **cubiertos**. Ninguno parcial, ninguno sin cobertura.

### Trazabilidad HU → evidencia (vía CA)
Todas las HU de `definition.md` quedan cubiertas: HU-01 (CA-01/02/03/04/05/07/09), HU-02 (CA-06),
HU-03 (CA-08/11), HU-04 (CA-10/11), HU-05 (CA-07 + el core es invocable/testeable de forma aislada,
demostrado por toda la suite unit sobre `create_client`).

---

## Resultado de la suite

```
python -m pytest -q  ->  32 passed in ~0.16s
```

- 26 tests unit (`tests/core/test_scaffold.py`) + 6 tests de integración
  (`tests/integration/test_client_scaffold_integration.py`).
- **Verde**, sin fallos ni errores, sin regresiones. Coincide con la evidencia registrada por
  `integration_tester` en `state.json` (commit `a04a476`).

---

## Cumplimiento de alcance y restricciones

### Alcance (definition.md)
- **In scope — hecho:** función core `create_client(name, clients_root) -> Path`; árbol
  `client.yaml` + `010_inputs/` + `020_outputs/` + `data/{bronze,silver,gold}/` + `models/`;
  validación del nombre contra patrón seguro (DS-1, 7 reglas) sin normalización; fallo con
  `FileExistsError` si el cliente ya existe (sin `--force`, no se sobrescribe); tests unit sobre el
  core. **Excepción:** la capa CLI fina (`foda client new`) queda **pendiente** — ver F-2.
- **Out of scope — respetado:** no hay lógica de `ClientContext`, ni flujos de negocio, ni
  subcarpetas por flujo, ni versionado de `models/`, ni flag `--force`, ni otros subcomandos de
  `foda client`, ni tests de la CLI, ni filtrado de nombres reservados de Windows / normalización de
  mayúsculas. Verificado por la aserción de conjunto de CA-02 y el test de árbol exacto de
  integración (no aparecen entradas extra).

### Restricciones (system_design.md §3)
- **R1 — Python 3.13+:** `pyproject.toml` declara correctamente `requires-python = ">=3.13"`
  (conforme a D-010). El código usa solo stdlib + PyYAML (D-026), sin sintaxis fuera de 3.13.
  **Observación:** la suite se ejecutó en un runtime **Python 3.12.10** — ver F-1.
- **R3 — YAML como configuración/decisión humana:** `client.yaml` se escribe y es consumible como
  contrato por un lector externo (test de integración `..._consumible_como_contrato...`). Conforme.
- **R6 — persistencia por carpeta de cliente (multi-tenant):** aislamiento verificado por
  `...::test_multiples_clientes_bajo_mismo_clients_root_quedan_aislados` y
  `...::test_creacion_secuencial_de_varios_clientes_no_deja_estado_compartido`. Conforme.
- **LLM aislado / pipeline determinista:** no aplica a esta feature (bootstrap previo al pipeline,
  sin LLM). Conforme por no-aplicabilidad.

---

## Hallazgos (no bloqueantes)

### F-1 — Runtime de ejecución Python 3.12.10 vs R1 (3.13+)
- **Qué:** el entorno local donde corre `pytest` es **Python 3.12.10**, mientras R1/D-010 fija
  Python 3.13+ como obligatorio. El **artefacto** de la feature (`pyproject.toml`) sí declara
  `requires-python = ">=3.13"` correctamente y el código no usa sintaxis exclusiva de 3.13.
- **Impacto:** ninguno sobre los `CA` (la suite es verde y el código es compatible con 3.12/3.13).
  Es una desalineación del **entorno de desarrollo**, no un defecto del entregable.
- **Recomendación:** alinear el entorno a Python 3.13+ para que la suite verde se demuestre sobre el
  runtime mandatado por R1. No requiere volver a etapas de construcción.

### F-2 — Capa CLI (`foda client new`, TSK-07) no construida
- **Qué:** `src/foda/cli.py` **no existe**. La `definition.md` §Alcance y el `plan.md` (TSK-07)
  listan la capa CLI fina como entregable **in scope**, marcada "sin test en esta banda"
  (spec §No-Objetivos). La `spec.md` la describe solo como "contrato de nivel", **fuera** del
  conjunto de criterios de aceptación `CA-01…CA-11`.
- **Impacto:** **ningún `CA` queda sin cobertura** — todos los criterios de aceptación son sobre el
  core `create_client`, que está completo y verde. Es un hueco de **completitud de alcance** de la
  definition, no de los criterios de aceptación. Estado ya documentado por `integration_tester`
  (`scope_note`: "TSK-07 pendiente; la capa CLI tampoco existe aún").
- **Recomendación:** completar TSK-07 como tarea de cableado (sin test, por spec §No-Objetivos), o
  planificarla explícitamente en una banda posterior. No requiere reabrir el bucle TDD del core.

### F-3 — `created_at` usa fecha local en vez de UTC
- **Qué:** `scaffold.py` escribe `created_at` con `date.today().isoformat()` (fecha **local** del
  proceso). El contrato de datos de `spec.md` (§Artefacto `client.yaml` y §Comportamiento paso 4)
  especifica la fecha "ISO-8601 (UTC)". El `plan.md` sugería `datetime.now(timezone.utc)`.
- **Impacto:** **CA-06 solo verifica el patrón** `^\d{4}-\d{2}-\d{2}$`, que se cumple; por tanto no
  hay `CA` roto. Cerca de medianoche la fecha local puede diferir en un día de la UTC — desviación
  menor del contrato de datos, sin efecto en la cobertura de aceptación.
- **Recomendación:** corrección menor (`datetime.now(timezone.utc).date().isoformat()`) en una banda
  de estabilización, si se desea cumplir el matiz UTC del contrato. No bloqueante.

### Nota — Caso 18 / DS-2.2 (rollback best-effort) diferido
El caso 18 (rollback best-effort ante error de FS a mitad de creación, DS-2.2 / §Comportamiento
paso 6) fue **diferido** a una banda de estabilización posterior (`stab_n`) por decisión humana del
GATE PA-3, opción (c), registrada como **D-032**. **Ningún `CA-01…CA-11` depende de DS-2.2:** los
escenarios realistas (nombre inválido → `ValueError`, duplicado → `FileExistsError`) se resuelven con
la estrategia validación-primero (DS-2.1), plenamente cubierta por CA-08/CA-10/CA-11. Por tanto el
diferimiento **no** afecta la conformidad de esta banda; queda como limitación conocida documentada.

---

## Cierre
Feature `client_scaffold`, banda `tracer_bullet`: **CONFORME** a los criterios de aceptación de la
`spec.md` aprobada. Los tres hallazgos (F-1, F-2, F-3) y el diferimiento del caso 18 (D-032) son
condiciones conocidas y documentadas que no dejan ningún criterio de aceptación sin evidencia. La
cadena SDD/TDD de esta banda se cierra; el tratamiento de F-1/F-2/F-3 queda a criterio del humano
(alineación de entorno y/o banda de estabilización posterior).
