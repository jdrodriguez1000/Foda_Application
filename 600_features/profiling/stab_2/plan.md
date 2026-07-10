# Plan — profiling (banda `stab_2`)

> Artefacto de la etapa 3 (`plan_builder`). Define el **cómo** de la implementación, descompone el trabajo en **tareas atómicas codificadas y trazables** (`TSK-xx → CA-xx`) y **enumera los casos de test** que guiarán el bucle TDD. **Requiere aprobación humana** (gate) antes de arrancar el bucle.
>
> Fuentes: `600_features/profiling/stab_2/spec.md` (CA-01…CA-25, DS-PRF2-1…6), código vigente CONFORME `stab_1` (`src/foda/flows/f040_profiling/profiling.py` con esquema v0.2 + bloque `health`, `src/foda/core/flow.py`, `src/foda/core/context.py`, `src/foda/core/scaffold.py`), esquema de entrada `ingestion_report.json` (`600_features/ingestion/tracer_bullet/spec.md`). `800_persistence/decisions.md` (`D-097`…`D-100`, `D-080`, `D-021`).

## Enfoque Técnico

Cambio **quirúrgico** (NC-2/NC-3): se **endurecen `Profiling.load_inputs()` y `Profiling.execute()`**, se **añade un override de `Profiling.validate()`** (validación de `weights`) y se **añade `pandas` como dependencia declarada**. No se sobreescribe `run()` (se sigue heredando el template method `load_inputs → validate → execute → write_outputs` de `Flow`), **no** se toca `write_outputs()` (su serialización determinista `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True) + "\n"` sirve tal cual para v0.3), **no** se amplía `ClientContext`/`Artifact`/`Flow`, **no** se toca el gate `D-080` ni la CLI (ya CONFORME).

Reparto de responsabilidades dentro del flujo:

- **`load_inputs(ctx)`:** además de parsear `ingestion_report.json` (único `requires`, ya presente en `stab_1`), comprueba **manualmente** la existencia del artefacto opcional `profiling_config.yaml` vía `Artifact(base="inputs", relative="040_profiling/profiling_config.yaml")`. Si existe, lo parsea con `yaml.safe_load` (PyYAML ya es dependencia, usado por `scaffold.py`) y deriva a estado de instancia (a) el **catálogo unificado de centinelas** (unión plana de las cajas `sentinels.{numeric, non_numeric, boolean}`, cada token convertido a `str(token)`, en un `set`/`frozenset`) y (b) los **pesos** declarados (`weights`) si están. Si `profiling_config.yaml` **no** existe, o no declara `sentinels`/`weights`, deja catálogo vacío y pesos default (`0.25` × 4). `profiling_config.yaml` **no** va en `requires` (opcional; si estuviera, `validate` base fallaría al faltar — `DS-PRF2-6`, `CA-18`).

- **`validate(ctx)` (nuevo override):** llama primero a `super().validate(ctx)` (comprobación base de existencia física de `ingestion_report.json`; si falta ⇒ `FlowContractError` nombrándolo, **antes** de `execute` — `CA-24`). Después, **si el cliente declaró `weights`**, valida la regla de `DS-PRF2-1`: exactamente las 4 claves `structural`/`completeness`/`validity`/`uniqueness`, cada una `≥ 0`, y suma `1.0 ± 1e-9`; en caso contrario lanza `FlowContractError` nombrando el problema. Si no declaró `weights`, no valida nada (se usan los 4 defaults). El orden `super().validate()` primero garantiza que la ausencia del `requires` prevalece sobre pesos inválidos.

- **`execute(ctx)` — cálculo determinista (sin LLM):**
  1. **Estructural (reutiliza los helpers de `stab_1`):** `files_declared`, `files_healthy`, `files_with_problems`, `problems_by_type` (4 claves fijas), `pareto`, y el score estructural (helper `_global_score` de `stab_1`, borde `files_declared==0 ⇒ 1.0`). Este score pasa a llamarse `structural_score` y su **detalle** (`files_declared`…`pareto`) se **reubica** de `health` a `defects.structural` (mismos valores y semántica que `stab_1`).
  2. **Lectura de `bronze/` (primera vez, solo lectura, `pandas`):** para cada archivo con `status == "ingested"` en `datasets[].files[]` (en orden declarado), resuelve `ctx.root / bronze_path` y lo lee como texto **sin auto-NA**: `.csv`/`.txt` con `pandas.read_csv(path, sep=<separator de la entrada>, dtype=str, keep_default_na=False, na_values=[])`; `.xlsx` con `pandas.read_excel(path, sheet_name=0, dtype=str, keep_default_na=False, na_values=[])` (primera hoja). La cabecera es cabecera, no dato. `bronze/` es **inalterable** (solo lectura, §10).
  3. **Completitud:** por archivo `rows`, `columns`, `cells = rows×columns`; celda **nula** = `NaN`/faltante **o** valor textual `""` tras `strip`; `null_cells` por archivo y `total_cells`, `null_cells` globales; `completeness_score = round(1 − null_cells/total_cells, 4)` (borde `total_cells==0 ⇒ 1.0`).
  4. **Validez:** celda **centinela** = celda **no nula** cuyo valor textual **literal** (sin recorte, comparación exacta y sensible a mayúsculas) coincide con algún token del catálogo unificado; `sentinel_cells` por archivo y global, `catalog_size` = nº de tokens de la unión; `validity_score = round(1 − sentinel_cells/total_cells, 4)` (borde `total_cells==0 ⇒ 1.0`; catálogo vacío ⇒ `sentinel_cells=0`, `validity_score=1.0`).
  5. **Unicidad:** por archivo `rows` y `duplicate_rows = df.duplicated(keep="first").sum()` (comparando la fila completa en modo texto, solo dentro del mismo archivo); `total_rows`, `duplicate_rows` globales; `uniqueness_score = round(1 − duplicate_rows/total_rows, 4)` (borde `total_rows==0 ⇒ 1.0`).
  6. **`global_score`:** `round(w_struct·structural_score + w_compl·completeness_score + w_valid·validity_score + w_uniq·uniqueness_score, 4)` con los pesos **efectivos** (override o default). Los pesos efectivos se publican en `health.weights`.
  7. Arma el reporte **v0.3** en memoria: identidad (`schema_version:"0.3"`, `client`, `flow`, `success:True`) + `health` (scoreboard) + `defects` (evidencia con 4 sub-bloques). `success` refleja la ejecución del flujo, **independiente** del `success` de `ingestion` (`CA-25`).
  8. `return FlowResult(success=True, outputs=[self.produces[0].path(ctx)])`.

- **`write_outputs(ctx, result)`:** **sin cambios**. `sort_keys=True` no reordena listas ⇒ el orden de `pareto` (heredado de `stab_1`) y de los `by_file` (fijado en `execute` por el orden declarado de `datasets[].files[]`) se preserva (`DS-PRF2-3`, `CA-09`, `CA-21`).

El catálogo de centinelas, los pesos y las claves de `defects` se manejan con **constantes/estructuras de módulo** (p. ej. `_WEIGHT_KEYS`, `_DEFAULT_WEIGHTS`, `_SENTINEL_BOXES`) para determinismo y legibilidad, sin configurabilidad no solicitada (NC-2). Los helpers nuevos (lectura de un DataFrame, conteo de nulos/centinelas/duplicados, construcción de cada sub-bloque de `defects`, media ponderada) son **funciones puras** del mismo módulo `profiling.py`.

## Archivos Afectados
- `pyproject.toml` — **modificar**: añadir `pandas` a `dependencies`. **Nota de riesgo (ver Riesgos):** `pandas` **no** estaba declarado ni lo usa `Ingestion` (que parsea con líneas + `openpyxl`); es una **dependencia nueva** pese a lo que sugería la nota A-020 de la spec. Ya está instalado en el entorno (2.3.2), pero debe declararse.
- `src/foda/flows/f040_profiling/profiling.py` — **modificar**: endurecer `load_inputs()` (parseo opcional de `profiling_config.yaml`: catálogo + pesos); **añadir** override `validate()` (regla de `weights`); reescribir `execute()` (reubicar estructural a `defects.structural`; leer `bronze/` con `pandas`; calcular 4 sub-scores + `global_score` ponderado; armar v0.3 con `health` + `defects`); bump `schema_version` a `"0.3"`; nuevos helpers puros y constantes de módulo. **No** se toca `write_outputs()` ni la firma de clase (`name`/`requires`/`produces`).
- `tests/flows/test_profiling.py` — **modificar**: añadir los tests unitarios de esta banda (casos 1–24). **Migración obligatoria** de los tests de `stab_1` que asertan el esquema v0.2 y el bloque `health` con las claves estructurales (ver Estrategia de Test): esos asserts se re-apuntan a `schema_version=="0.3"`, `health.structural_score` y `defects.structural.*`. Es el ajuste a tests existentes justificado por el bump de contrato aprobado (`DS-PRF2-5`, NC-3).
- `tests/integration/test_profiling_integration.py` — **modificar**: integración end-to-end del cálculo v0.3 (lectura real de `bronze/` + config), responsabilidad de `integration_tester`.

> El código de producción vive en `src/foda/…`, la config de proyecto en `pyproject.toml`, y los tests en `tests/…`; **nada** de código o test se escribe bajo `600_features/`.

## Tareas
> `TSK-xx` atómicas. Reglas: un solo responsable, un solo entregable, codificar ≠ testear. **Estado** inicial `no_implementada` (valores: `no_implementada` | `implementada` | `cancelada_suspendida`); el responsable es su único escritor (`D-021`). **Responsable** ∈ `{tdd_tester, tdd_coder, tdd_refactor, integration_tester, humano}`.

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Test: para un fixture v0.3, `profiling_report.json` declara `schema_version=="0.3"` y conserva identidad (`client==ctx.name`, `flow=="profiling"`, `success` bool) | Test en `tests/flows/test_profiling.py` | tdd_tester | no_implementada | CA-19, CA-20 |
| TSK-02 | Código: en `execute()`, subir `schema_version` a `"0.3"` conservando `client`/`flow`/`success` | `profiling.py::execute` | tdd_coder | no_implementada | CA-19, CA-20 |
| TSK-03 | Test: el reporte tiene **exactamente** las claves top-level `{schema_version, client, flow, success, health, defects}` y `defects` **exactamente** `{structural, completeness, validity, uniqueness}` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-22 |
| TSK-04 | Código: `execute()` arma el esqueleto v0.3 (top-level + `health` + `defects` con sus 4 sub-bloques), migrando el reporte v0.2 a la nueva forma | `profiling.py::execute` (+helpers) | tdd_coder | no_implementada | CA-22 |
| TSK-05 | Test: `health` tiene **exactamente** las 6 claves `{global_score, weights, structural_score, completeness_score, validity_score, uniqueness_score}`; los 4 sub-scores y `global_score` son `float` en `[0.0, 1.0]` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-01 |
| TSK-06 | Código: `execute()` arma el scoreboard `health` con las 6 claves (sub-scores como `float` en `[0,1]`) | `profiling.py::execute` (+helpers) | tdd_coder | no_implementada | CA-01 |
| TSK-07 | Test: `defects.structural` contiene `files_declared`, `files_healthy`, `files_with_problems`, `problems_by_type` (4 claves) y `pareto`, con los mismos valores que `stab_1` para el mismo `ingestion_report.json` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-23 |
| TSK-08 | Código: reubicar el detalle estructural de `stab_1` desde `health` a `defects.structural` (mismos helpers y valores) | `profiling.py::execute` | tdd_coder | no_implementada | CA-23 |
| TSK-09 | Test: `health.structural_score` == `global_score` que `stab_1` calcularía para el mismo `ingestion_report.json` (fórmula ponderada por severidad sobre `files_declared`; borde `files_declared==0 ⇒ 1.0`) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-05 |
| TSK-10 | Código: publicar `health.structural_score` reutilizando el helper de score estructural de `stab_1` | `profiling.py::execute` | tdd_coder | no_implementada | CA-05 |
| TSK-11 | Test: `defects.completeness.total_cells == Σ(rows×columns)` sobre archivos `status=="ingested"` (fixture con `bronze_path` a csv de contenido conocido) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-06 |
| TSK-12 | Andamiaje: añadir `pandas` a `dependencies` de `pyproject.toml` (habilita la lectura de `bronze/`) | `pyproject.toml` | tdd_coder | no_implementada | CA-06 (andamiaje) |
| TSK-13 | Código: en `execute()`, leer con `pandas` (modo texto, sin auto-NA) los archivos ingeridos y calcular `total_cells` + `rows`/`columns`/`cells` por archivo | `profiling.py::execute` (+helpers) | tdd_coder | no_implementada | CA-06 |
| TSK-14 | Test: `defects.completeness.null_cells` == nº de celdas nulas (`NaN` o `""` tras `strip`) sobre los ingeridos (fixture de contenido conocido) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-07 |
| TSK-15 | Código: contar celdas nulas (`isna` o texto vacío tras `strip`) por archivo y global | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-07 |
| TSK-16 | Test: `health.completeness_score == round(1 − null_cells/total_cells, 4)`, y `== 1.0` cuando `total_cells == 0` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-08 |
| TSK-17 | Código: calcular `completeness_score` con borde `total_cells==0 ⇒ 1.0` | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-08 |
| TSK-18 | Test: `defects.completeness.by_file` tiene `{name, rows, columns, cells, null_cells}` por archivo ingerido, en orden de `datasets[].files[]`, y `Σ by_file[].null_cells == null_cells` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-09 |
| TSK-19 | Código: construir `defects.completeness.by_file` en el orden declarado de archivos ingeridos | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-09 |
| TSK-20 | Test: `defects.uniqueness.total_rows == Σ rows` sobre los ingeridos (fixture) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-10 |
| TSK-21 | Código: calcular `total_rows` + `rows` por archivo, y `defects.uniqueness.by_file` | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-10 |
| TSK-22 | Test: `defects.uniqueness.duplicate_rows` == Σ por archivo de `DataFrame.duplicated(keep="first")`; coincide con fixture; `Σ by_file[].duplicate_rows == duplicate_rows` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-11 |
| TSK-23 | Código: contar filas duplicadas por archivo (`duplicated(keep="first")`) y global | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-11 |
| TSK-24 | Test: `health.uniqueness_score == round(1 − duplicate_rows/total_rows, 4)`, y `== 1.0` cuando `total_rows == 0` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-12 |
| TSK-25 | Código: calcular `uniqueness_score` con borde `total_rows==0 ⇒ 1.0` | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-12 |
| TSK-26 | Test: Profiling lee el catálogo de `010_inputs/040_profiling/profiling_config.yaml` unificando `numeric`/`non_numeric`/`boolean`; `defects.validity.catalog_size` == nº de tokens de la unión | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-17 |
| TSK-27 | Código: en `load_inputs()`, parsear `profiling_config.yaml` (opcional) y unificar las 3 cajas de `sentinels` en un catálogo plano de tokens `str`; exponer `catalog_size` | `profiling.py::load_inputs` (+helper) | tdd_coder | no_implementada | CA-17 |
| TSK-28 | Test: con catálogo no vacío, `defects.validity.sentinel_cells` == nº de celdas **no nulas** cuyo valor textual literal coincide exactamente con algún token del catálogo (fixture) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-13 |
| TSK-29 | Código: contar celdas centinela (no nula ∧ match exacto de token) por archivo y global | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-13 |
| TSK-30 | Test: `health.validity_score == round(1 − sentinel_cells/total_cells, 4)`, y `== 1.0` cuando `total_cells == 0` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-14 |
| TSK-31 | Código: calcular `validity_score` con borde `total_cells==0 ⇒ 1.0` | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-14 |
| TSK-32 | Test (confirmación): una celda nula **no** cuenta como centinela aunque `""` esté en el catálogo (exclusión mutua), y el token `-999` **no** matchea `"-999.0"` (match exacto) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-16 |
| TSK-33 | Test (confirmación): sin `profiling_config.yaml` o con catálogo vacío, `defects.validity.sentinel_cells==0`, `catalog_size==0` y `health.validity_score==1.0` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-15 |
| TSK-34 | Test (confirmación): si `profiling_config.yaml` **no existe**, `run(ctx)` no lanza y completa con catálogo vacío y pesos default | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-18 |
| TSK-35 | Test: `health.global_score == round(Σ w_i·subscore_i, 4)` con pesos default `0.25` (ancla sub-scores `0.875/0.98/0.95/0.90 ⇒ 0.9263`) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-02 |
| TSK-36 | Código: en `execute()`, calcular `global_score` como media ponderada de los 4 sub-scores con los pesos efectivos, redondeada a 4 decimales | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-02 |
| TSK-37 | Test: sin `weights` en config, `health.weights == {structural:0.25, completeness:0.25, validity:0.25, uniqueness:0.25}` y `global_score` == media aritmética de los 4 sub-scores | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-03 |
| TSK-38 | Código: usar pesos default `0.25`×4 cuando no hay override y **publicarlos** en `health.weights` | `profiling.py::execute` | tdd_coder | no_implementada | CA-03 |
| TSK-39 | Test: con `weights` válidos (4 claves, `≥0`, suma `1.0`), `health.weights` los refleja y `global_score` los usa; con `weights` inválidos (no suman `1.0`, falta clave o negativo), `run(ctx)` lanza `FlowContractError` y **no** escribe el reporte | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-04 |
| TSK-40 | Código: parsear `weights` (override) en `load_inputs()` y validar la regla de `DS-PRF2-1` en el override `validate()` (`FlowContractError` si viola) | `profiling.py::load_inputs`+`validate` | tdd_coder | no_implementada | CA-04 |
| TSK-41 | Test (confirmación): con `ingestion_report.success==false`, `run(ctx)` no lanza, devuelve `FlowResult(success=True)`, escribe reporte con `success==true` y `health`/`defects` calculados | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-25 |
| TSK-42 | Test (confirmación): sin `ingestion_report.json`, `run(ctx)` lanza `FlowContractError` en `validate` base nombrando el artefacto y **no** escribe `profiling_report.json` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-24 |
| TSK-43 | Test (confirmación): dos `run(ctx)` con las mismas entradas producen `profiling_report.json` byte-idéntico | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-21 |
| TSK-44 | Refactor de `profiling.py` (helpers puros de lectura/conteo, constantes, docstrings) sin cambiar comportamiento; suite verde | Diff de refactor + suite verde | tdd_refactor | no_implementada | CA-01..CA-25 |
| TSK-45 | Migración de los tests `stab_1` que asertan v0.2/`health` estructural al nuevo contrato v0.3 (`schema_version`, `health.structural_score`, `defects.structural.*`), suite verde | Diff en `test_profiling.py` | tdd_refactor | no_implementada | CA-05, CA-23 |
| TSK-46 | Test de integración end-to-end del cálculo v0.3 (lectura real de `bronze/` + `profiling_config.yaml`) vía flujo/CLI sobre cliente temporal | `tests/integration/test_profiling_integration.py` | integration_tester | no_implementada | CA-01..CA-25 |
| TSK-47 | Prueba humana end-to-end de la feature vía CLI (gate `human_test`) | Veredicto humano | humano | no_implementada | CA-01..CA-25 |

> **Casos de confirmación (NC-3/NC-5).** Los casos 16, 17, 18, 22, 23, 24 **no** llevan tarea-código propia: su verde se alcanza con producción ya construida por casos previos (detección exacta y exclusión mutua ya implícitas en la definición de centinela; catálogo vacío ya cubierto; `success` independiente ya fijado; `validate` base heredada; serialización determinista intacta). Son tests que **confirman** contrato/invariantes. Si un test rojo revelara una carencia real, se documenta (NC-6) y se añade la tarea-código correspondiente.

## Dependencias y Contratos
- **Consume:** `ingestion_report.json` (`020_outputs/030_ingestion/`), producido por `Ingestion` (CONFORME, determinista). Campos leídos: `summary.files_declared`, `datasets[].files[]` (`status`, `inconsistencies`, y para `ingested`: `bronze_path`, `separator`), lista top-level `inconsistencies[]` (`{type, detail}`).
- **Consume (contenido, primera vez):** los archivos ingeridos en `bronze/` (`ctx.root / bronze_path`), **solo lectura** (§10). No van en `requires` de `validate` (se referencian desde el `ingestion_report`).
- **Consume (opcional):** `profiling_config.yaml` (`010_inputs/040_profiling/`). Si falta ⇒ catálogo vacío + pesos default; **no** en `requires`.
- **Produce:** `profiling_report.json` (`020_outputs/040_profiling/`), esquema **v0.3**: identidad (`schema_version:"0.3"`, `client`, `flow`, `success`) + `health` (scoreboard) + `defects` (`structural`/`completeness`/`validity`/`uniqueness`).
- **Reutiliza sin ampliar:** `Flow`/`FlowResult`/`Artifact`/`FlowContractError` (`core/flow.py`), `ClientContext` (`core/context.py`), `yaml.safe_load` (PyYAML). **Nueva dependencia declarada:** `pandas` en `pyproject.toml`.
- **Supuesto de contrato (NC-2):** `ingestion_report.json` cumple el contrato de `ingestion` y los `bronze_path` de los archivos `ingested` existen físicamente. Manejo defensivo de un `ingestion_report.json` corrupto o de una copia bronze ausente pese a estar declarada `ingested` = **fuera de alcance**; solo la ausencia física del `ingestion_report.json` está cubierta (`CA-24`).

## Estrategia de Test
- **Unit (`tests/flows/test_profiling.py`):** un test por caso (1–24) sobre `ClientContext` bajo `tmp_path` con `create_client`, un `ingestion_report.json` de fixture con `bronze_path` que apunta a **csv de contenido conocido escritos en `ctx.bronze_dir`**, y un `profiling_config.yaml` **opcional** bajo `ctx.inputs_dir/"040_profiling"`. Aserciones sobre `health`/`defects` y `pytest.raises(FlowContractError)` para los errores duros (`weights` inválidos, `ingestion_report` ausente).
- **Fixtures / datos de prueba necesarios:**
  - Helper que fabrica un `ingestion_report.json` con `summary.files_declared`, `datasets[].files[]` (`status`, `inconsistencies`, `bronze_path`, `separator`), lista top-level `inconsistencies[]`, y `success` (bool).
  - Helper que **escribe físicamente** cada archivo bronze (csv de contenido conocido) en `ctx.root / bronze_path`, controlando nulos (`""`), tokens centinela y filas duplicadas para conteos deterministas.
  - Helper que escribe un `profiling_config.yaml` con `sentinels`/`weights` a demanda.
  - **Ancla numérica de la spec** reutilizable: 1 archivo 100×5, 10 nulos, 25 centinelas (catálogo de 5), 10 duplicados, estructura 1 `missing_column` sobre 4 declarados ⇒ `structural=0.875`, `completeness=0.98`, `validity=0.95`, `uniqueness=0.90`, `global=0.9263` (pesos default).
- **Migración de tests `stab_1` (NC-3, justificada por `DS-PRF2-5`):** los tests unitarios de `stab_1` que asertan `schema_version=="0.2"` y el bloque `health` con claves estructurales (`files_declared`, `problems_by_type`, `pareto`, `global_score` estructural) **rompen** al rediseñar el reporte a v0.3. Deben migrarse: `schema_version→"0.3"`, `health.global_score` estructural → `health.structural_score`, y el detalle estructural → `defects.structural.*`. Esta migración se ejecuta acompañando los casos que la fuerzan (1–9) y se consolida en TSK-45; es el único cambio a tests existentes, justificado por el bump de contrato aprobado.
- **Integración (`integration_tester`, fuera del bucle rojo/verde):** flujo real punta a punta leyendo `bronze/` y `profiling_config.yaml` reales, verificando coherencia entre `health` y `defects` y las invariantes de suma (`CA-01..CA-25`).

## Casos de Test (bucle TDD)
Ordenados de simple/estructural a complejo (NC-4: tracer bullet primero — los casos 1–5 establecen el esqueleto v0.3 completo reubicando lo estructural de `stab_1`; luego cada dimensión de contenido —completitud, unicidad, validez— fuerza sus conteos; después el score ponderado, la config y, al final, los invariantes de error/determinismo). Coinciden con `stages.tdd.cases[]` de `state.json`. Cada caso agrupa sus tareas de test y código.

| id | Descripción (verificable) | Tareas (`TSK-xx`) | Trazabilidad → CA |
|---|---|---|---|
| 1 | `profiling_report.json` declara `schema_version=="0.3"` y conserva identidad `client==ctx.name`, `flow=="profiling"`, `success` (bool) | TSK-01, TSK-02 | CA-19, CA-20 |
| 2 | Top-level **exactamente** `{schema_version, client, flow, success, health, defects}`; `defects` **exactamente** `{structural, completeness, validity, uniqueness}` | TSK-03, TSK-04 | CA-22 |
| 3 | `health` tiene **exactamente** las 6 claves `{global_score, weights, structural_score, completeness_score, validity_score, uniqueness_score}`; sub-scores y `global_score` `float` en `[0,1]` | TSK-05, TSK-06 | CA-01 |
| 4 | `defects.structural` = detalle estructural de `stab_1` (`files_declared`, `files_healthy`, `files_with_problems`, `problems_by_type` 4 claves, `pareto`) con los mismos valores | TSK-07, TSK-08 | CA-23 |
| 5 | `health.structural_score` == `global_score` que `stab_1` calcularía para el mismo `ingestion_report.json` (borde `files_declared==0 ⇒ 1.0`) | TSK-09, TSK-10 | CA-05 |
| 6 | `defects.completeness.total_cells == Σ(rows×columns)` sobre archivos `status=="ingested"` (lectura real de `bronze/` con `pandas`) | TSK-11, TSK-12, TSK-13 | CA-06 |
| 7 | `defects.completeness.null_cells` == nº de celdas nulas (`NaN` o `""` tras `strip`) | TSK-14, TSK-15 | CA-07 |
| 8 | `health.completeness_score == round(1 − null_cells/total_cells, 4)`, `==1.0` si `total_cells==0` | TSK-16, TSK-17 | CA-08 |
| 9 | `defects.completeness.by_file` = `{name, rows, columns, cells, null_cells}` por archivo en orden declarado; `Σ by_file[].null_cells == null_cells` | TSK-18, TSK-19 | CA-09 |
| 10 | `defects.uniqueness.total_rows == Σ rows` sobre los ingeridos | TSK-20, TSK-21 | CA-10 |
| 11 | `defects.uniqueness.duplicate_rows` == Σ por archivo de `duplicated(keep="first")`; `Σ by_file[].duplicate_rows == duplicate_rows` | TSK-22, TSK-23 | CA-11 |
| 12 | `health.uniqueness_score == round(1 − duplicate_rows/total_rows, 4)`, `==1.0` si `total_rows==0` | TSK-24, TSK-25 | CA-12 |
| 13 | Profiling lee `profiling_config.yaml` unificando `numeric`/`non_numeric`/`boolean`; `defects.validity.catalog_size` == nº de tokens de la unión | TSK-26, TSK-27 | CA-17 |
| 14 | Con catálogo no vacío, `defects.validity.sentinel_cells` == nº de celdas no nulas con match exacto de token | TSK-28, TSK-29 | CA-13 |
| 15 | `health.validity_score == round(1 − sentinel_cells/total_cells, 4)`, `==1.0` si `total_cells==0` | TSK-30, TSK-31 | CA-14 |
| 16 | Celda nula no es centinela aunque `""` esté en catálogo (exclusión mutua); token `-999` no matchea `"-999.0"` (match exacto) | TSK-32 | CA-16 |
| 17 | Sin config o catálogo vacío → `sentinel_cells==0`, `catalog_size==0`, `validity_score==1.0` | TSK-33 | CA-15 |
| 18 | Si `profiling_config.yaml` no existe, `run(ctx)` no lanza y completa con catálogo vacío + pesos default | TSK-34 | CA-18 |
| 19 | `health.global_score == round(Σ w_i·subscore_i, 4)` con pesos default (ancla `0.875/0.98/0.95/0.90 ⇒ 0.9263`) | TSK-35, TSK-36 | CA-02 |
| 20 | Sin `weights`, `health.weights == {…:0.25}` y `global_score` == media aritmética de los 4 sub-scores | TSK-37, TSK-38 | CA-03 |
| 21 | Con `weights` válidos, `health.weights` los refleja y `global_score` los usa; con `weights` inválidos, `FlowContractError` y no se escribe el reporte | TSK-39, TSK-40 | CA-04 |
| 22 | `ingestion.success==false` → sin excepción, `FlowResult(success=True)`, reporte con `success==true` y `health`/`defects` calculados | TSK-41 | CA-25 |
| 23 | Sin `ingestion_report.json` → `FlowContractError` en `validate` base; no se escribe `profiling_report.json` | TSK-42 | CA-24 |
| 24 | Dos `run(ctx)` con las mismas entradas → `profiling_report.json` byte-idéntico | TSK-43 | CA-21 |

> Tras el bucle: `tdd_refactor` (TSK-44, TSK-45), `integration_tester` (TSK-46) y el gate humano `human_test` (TSK-47) cierran la feature antes del PR/merge.

### Cobertura CA → caso
CA-01→3, CA-02→19, CA-03→20, CA-04→21, CA-05→5, CA-06→6, CA-07→7, CA-08→8, CA-09→9, CA-10→10, CA-11→11, CA-12→12, CA-13→14, CA-14→15, CA-15→17, CA-16→16, CA-17→13, CA-18→18, CA-19→1, CA-20→1, CA-21→24, CA-22→2, CA-23→4, CA-24→23, CA-25→22. **Los 25 CA quedan cubiertos por ≥ 1 caso.**

## Riesgos y notas para el GATE humano
1. **`pandas` es dependencia NUEVA (corrige la premisa de A-020).** La spec afirma que `Ingestion` ya usa `pandas`; **no es así**: `Ingestion` parsea csv con líneas + separador detectado a mano y xlsx con `openpyxl`. `pandas` **no** está declarado en `pyproject.toml`. Sí está **instalado** en el entorno (2.3.2), por lo que la banda funciona, pero TSK-12 lo **declara** explícitamente. La decisión humana A-020 (usar `pandas`) sigue siendo válida; solo se corrige su justificación. Alternativa (no recomendada sin decisión humana): replicar el parseo manual de `Ingestion` para evitar la dependencia — más código y más riesgo de divergencia de conteos; se descarta salvo indicación contraria (NC-6).
2. **Migración de tests `stab_1` (rompen con v0.3).** El rediseño de `health` y el bump a `"0.3"` invalidan varios asserts unitarios de `stab_1`. Es un cambio a tests existentes **inevitable y aprobado** por `DS-PRF2-5`; se acota a re-apuntar rutas (TSK-45), no borra cobertura.
3. **Reconciliación de estado.** `state.json` traía `spec_writer.awaiting_approval: true`. Dado que la sesión principal confirma la aprobación humana del GATE de la spec, se marcó `awaiting_approval: false` en `spec_writer` para reflejar el gate superado. Si esto no correspondiera, el humano debe indicarlo.
4. **Determinismo de `by_file` (no lo garantiza `sort_keys`).** El orden de las listas `by_file` se fija en `execute()` por el orden declarado de `datasets[].files[]`; `sort_keys=True` ordena claves de objetos, no listas. El caso 24 (byte-idéntico) lo protege.
