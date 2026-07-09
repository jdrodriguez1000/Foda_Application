# Plan — profiling (banda `stab_1`)

> Artefacto de la etapa 3 (`plan_builder`). Define el **cómo** de la implementación, descompone el trabajo en **tareas atómicas codificadas y trazables** (`TSK-xx → CA-xx`) y **enumera los casos de test** que guiarán el bucle TDD. **Requiere aprobación humana** (gate) antes de arrancar el bucle.
>
> Fuentes: `600_features/profiling/stab_1/spec.md` (CA-01…CA-23, DS-PRF-1…7), código vigente CONFORME (`src/foda/flows/f040_profiling/profiling.py` banda tracer_bullet, `src/foda/core/flow.py`, `src/foda/core/context.py`), esquema de entrada `ingestion_report.json` (`600_features/ingestion/tracer_bullet/spec.md`).

## Enfoque Técnico

Cambio **quirúrgico** (NC-2/NC-3): se **endurece únicamente `Profiling.execute()`**. No se sobreescribe `run()` (se sigue heredando el template method `load_inputs → validate → execute → write_outputs` de `Flow`), no se toca `write_outputs()` (su serialización determinista ya sirve), no se amplía `ClientContext`/`Artifact`/`Flow`, no se toca el gate `D-080` ni la CLI (ya CONFORME en `tracer_bullet`).

Toda la lógica nueva vive en `execute(ctx)` y en **helpers privados puros** del mismo módulo `profiling.py`, que operan sobre el dict `ingestion_report` ya parseado (sin leer `bronze/`, sin LLM). Reparto de responsabilidades dentro del flujo:

- **`load_inputs(ctx)` (nuevo hook, hoy no-op heredado):** parsea `ingestion_report.json` (el único `requires`) a un dict en estado de instancia (`self._ingestion`). Se corre **después** de `validate` base según el template method, pero como `Profiling` no sobreescribe `run()`, el orden es `load_inputs → validate → execute`; por seguridad el parseo se hace en `load_inputs` **o** al inicio de `execute` sobre la ruta ya validada. **Decisión de plan:** parsear al inicio de `execute(ctx)` leyendo `self.requires[0].path(ctx)`, para no depender del orden `load_inputs`/`validate` y mantener el manejo de ausencia física en `validate` base (`CA-23`). No se añade manejo defensivo de JSON corrupto/campos ausentes (fuera de alcance, spec §No-Objetivos).

- **`execute(ctx)`:** orquesta el cálculo determinista de la salud estructural y arma el reporte **v0.2** en memoria:
  1. `report = json.loads(self.requires[0].path(ctx).read_text(...))`.
  2. `files_declared = report["summary"]["files_declared"]`.
  3. `files_healthy` / `files_with_problems`: iterando `report["datasets"][*]["files"][*]`; un archivo declarado es **sano** si `status == "ingested"` **y** `inconsistencies == []`; en caso contrario, **con problemas** (`DS-PRF-3`).
  4. `problems_by_type`: dict con las **4 claves fijas** (`missing_file`, `unexpected_file`, `missing_column`, `unexpected_column`), contando ocurrencias en la lista **top-level** `report["inconsistencies"]` por `type` (`DS-PRF-4`).
  5. `global_score`: `penalizacion = Σ peso[t]·problems_by_type[t]` con pesos `{missing_file:1.0, missing_column:0.5, unexpected_file:0.3, unexpected_column:0.1}`; `score = max(0.0, 1.0 − penalizacion/files_declared)` redondeado a 4 decimales; si `files_declared == 0` → `1.0` (`DS-PRF-2`).
  6. `pareto`: lista de `{type, count, pct}` solo con tipos de `count ≥ 1`, ordenada por `count` desc y `type` alfabético asc; `pct = round(count/Σ(problems_by_type.values()), 4)`; `[]` si no hay problemas (`DS-PRF-5`).
  7. `self._report = {"schema_version": "0.2", "client": ctx.name, "flow": "profiling", "success": True, "health": {…}}` (`DS-PRF-7`); `success` refleja la ejecución del flujo, **independiente** del `success` de `ingestion` (`DS-PRF-6`).
  8. `return FlowResult(success=True, outputs=[self.produces[0].path(ctx)])`.

- **`write_outputs(ctx, result)`:** **sin cambios** — la serialización determinista existente (`json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True) + "\n"`) sirve tal cual para v0.2. `sort_keys` no reordena listas, por lo que el orden de `pareto` fijado en `execute` se preserva (`DS-PRF-7`, `CA-21`).

Los pesos y las 4 claves del vocabulario se declaran como **constantes de módulo** (p. ej. `_WEIGHTS`, `_PROBLEM_TYPES`) para determinismo y legibilidad, sin configurabilidad no solicitada (NC-2).

## Archivos Afectados
- `src/foda/flows/f040_profiling/profiling.py` — **modificar** (endurecer `execute()`; añadir `load_inputs()`/helpers de cálculo privados y constantes de módulo; bump `schema_version` a `"0.2"`). **No** se toca `write_outputs()` ni la firma de clase (`name`/`requires`/`produces`).
- `tests/flows/test_profiling.py` — **modificar** (añadir los tests unitarios de esta banda, casos 1–22; se conservan los tests de `tracer_bullet` salvo el ajuste del que fija `schema_version=="0.1"`, que pasa a `"0.2"` — ver nota en Estrategia de Test).
- `tests/integration/test_profiling_integration.py` — **modificar** (integración end-to-end del cálculo de salud; responsabilidad de `integration_tester`).

> El código de producción vive en `src/foda/…` y los tests en `tests/…`; **nada** de código o test se escribe bajo `600_features/`.

## Tareas
> `TSK-xx` atómicas. Reglas: un solo responsable, un solo entregable, codificar ≠ testear. **Estado** inicial `no_implementada` (valores: `no_implementada` | `implementada` | `cancelada_suspendida`); el responsable es su único escritor (`D-021`). **Responsable** ∈ `{tdd_tester, tdd_coder, tdd_refactor, integration_tester, humano}`.

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Test: para fixture "todos sanos", `profiling_report.json` declara `schema_version=="0.2"` y conserva identidad (`client==ctx.name`, `flow=="profiling"`, `success` bool) | Test en `tests/flows/test_profiling.py` | tdd_tester | no_implementada | CA-18, CA-19 |
| TSK-02 | Código: en `execute()`, subir `schema_version` a `"0.2"` conservando `client`/`flow`/`success` | `profiling.py::execute` | tdd_coder | no_implementada | CA-18, CA-19 |
| TSK-03 | Test: el reporte contiene un objeto `health` con **exactamente** las 6 claves `global_score`, `files_declared`, `files_healthy`, `files_with_problems`, `problems_by_type`, `pareto` (fixture todos sanos) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-20 |
| TSK-04 | Código: `execute()` arma el bloque `health` completo para el camino "todos sanos" (`global_score=1.0`, conteos, `problems_by_type` 4 claves en 0, `pareto=[]`) | `profiling.py::execute` (+helpers) | tdd_coder | no_implementada | CA-20, CA-17 |
| TSK-05 | Test: `health.files_declared == ingestion_report.summary.files_declared` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-06 |
| TSK-06 | Test: `health.files_healthy` == nº de `datasets[].files[]` con `status=="ingested"` **y** `inconsistencies==[]` (fixture con mezcla) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-07 |
| TSK-07 | Test: `health.files_with_problems` == nº de `datasets[].files[]` con `status!="ingested"` **o** `inconsistencies!=[]` (fixture con mezcla) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-08 |
| TSK-08 | Código: en `execute()`, clasificación por archivo declarado (`files_healthy`/`files_with_problems`) iterando `datasets[].files[]` | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-07, CA-08 |
| TSK-09 | Test: se cumple la invariante `files_healthy + files_with_problems == files_declared` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-09 |
| TSK-10 | Test: `health.problems_by_type` tiene **exactamente** las 4 claves fijas, cada una `int≥0` = nº de ocurrencias de ese `type` en la lista top-level `ingestion_report.inconsistencies[]` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-11 |
| TSK-11 | Código: en `execute()`, conteo `problems_by_type` (4 claves fijas) desde `ingestion_report.inconsistencies[]` | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-11 |
| TSK-12 | Test: fixture sin inconsistencias → `problems_by_type` con las 4 claves en `0` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-12 |
| TSK-13 | Test: `health.global_score` es `float` en `[0.0, 1.0]` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-01 |
| TSK-14 | Test: `global_score == round(max(0.0, 1.0 − Σ peso[t]·problems_by_type[t] / files_declared), 4)` con los pesos de `DS-PRF-2` (ancla: 1 `missing_column` sobre `files_declared=4` ⇒ `0.875`) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-02 |
| TSK-15 | Código: en `execute()`, penalización ponderada por pesos y `global_score = 1.0 − penalizacion/files_declared` | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-02 |
| TSK-16 | Test: cuando `penalización_total > files_declared`, `global_score == 0.0` (clamp) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-03 |
| TSK-17 | Código: aplicar `max(0.0, …)` al `global_score` (clamp inferior) | `profiling.py::execute` | tdd_coder | no_implementada | CA-03 |
| TSK-18 | Test: cuando `files_declared == 0`, `global_score == 1.0` (borde, sin división por cero) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-04 |
| TSK-19 | Código: borde `files_declared == 0 ⇒ global_score = 1.0` (guarda antes de dividir) | `profiling.py::execute` | tdd_coder | no_implementada | CA-04 |
| TSK-20 | Test: `global_score` redondeado a 4 decimales (`round(x,4)`); dos entradas idénticas dan exactamente el mismo valor | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-05 |
| TSK-21 | Código: aplicar `round(score, 4)` al `global_score` | `profiling.py::execute` | tdd_coder | no_implementada | CA-05 |
| TSK-22 | Test: ≥1 `unexpected_file` **no** incrementa `files_declared` pero **sí** aporta a `problems_by_type.unexpected_file` y reduce `global_score` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-10 |
| TSK-23 | Test: fixture sin inconsistencias → `health.pareto == []` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-17 |
| TSK-24 | Test: `health.pareto` incluye **solo** tipos con `count ≥ 1` y `Σ(pareto[].count) == Σ(problems_by_type.values())` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-15 |
| TSK-25 | Código: en `execute()`, construir `pareto` con las entradas de `count ≥ 1` (sin pérdida de información) | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-15 |
| TSK-26 | Test: cada entrada de `pareto` tiene `type` (str), `count` (int ≥ 1) y `pct` (float) con `pct == round(count/Σ(problems_by_type.values()), 4)` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-16 |
| TSK-27 | Código: añadir `pct = round(count/total, 4)` a cada entrada de `pareto` | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-16 |
| TSK-28 | Test: `health.pareto` ordenado por `count` **descendente** (fixture con conteos distintos) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-13 |
| TSK-29 | Código: ordenar `pareto` por `count` descendente | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-13 |
| TSK-30 | Test: ante empate de `count`, `pareto` se ordena por `type` alfabético **ascendente** (desempate determinista) | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-14 |
| TSK-31 | Código: desempate por `type` alfabético ascendente (clave de orden compuesta) | `profiling.py::execute` (+helper) | tdd_coder | no_implementada | CA-14 |
| TSK-32 | Test: dos `run(ctx)` con el mismo `ingestion_report.json` producen `profiling_report.json` byte-idéntico | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-21 |
| TSK-33 | Test: con `ingestion_report.success == false`, `run(ctx)` no lanza, devuelve `FlowResult(success=True,…)`, escribe reporte con `success==true` y `health` calculado sobre lo disponible | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-22 |
| TSK-34 | Test: sin `ingestion_report.json`, `run(ctx)` lanza `FlowContractError` en `validate` nombrando el artefacto y **no** escribe `profiling_report.json` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-23 |
| TSK-35 | Refactor de `profiling.py` (helpers de cálculo, constantes, docstrings) sin cambiar comportamiento; suite verde | Diff de refactor + suite verde | tdd_refactor | no_implementada | CA-01..CA-23 |
| TSK-36 | Test de integración end-to-end del cálculo de salud vía flujo/CLI sobre cliente temporal real | `tests/integration/test_profiling_integration.py` | integration_tester | no_implementada | CA-01..CA-23 |
| TSK-37 | Prueba humana end-to-end de la feature vía CLI (gate `human_test`) | Veredicto humano | humano | no_implementada | CA-01..CA-23 |

> **Cases sin tarea-código propia (confirmación de comportamiento ya presente, NC-3/NC-5).** Los casos 5 (`files_declared`), 6 (invariante), 8 (`problems_by_type` todo 0), 9 (rango de `global_score`), 15 (`pareto==[]`), 20 (determinismo), 21 (`ingestion` fallido) y 22 (`requires` ausente) **no** llevan tarea-código nueva: su verde se alcanza con la producción ya construida por tareas previas (o heredada de `Flow`/`write_outputs`). Son tests que **confirman** contrato/invariantes: no se añade código que ningún caso nuevo exija. El `tdd_coder` no crea producción para estos casos; si un test rojo revelara una carencia real, se documenta (NC-6) y se añade la tarea-código correspondiente.

## Dependencias y Contratos
- **Consume:** `ingestion_report.json` (`020_outputs/030_ingestion/`), producido por `Ingestion` (CONFORME, determinista). Campos leídos: `summary.files_declared`, `datasets[].files[].status`/`.inconsistencies`, lista top-level `inconsistencies[]` (`{type, detail}`), y `unexpected_files[]` (los `unexpected_file` no cuentan como declarados). **No** se leen `bronze/` ni crudos.
- **Produce:** `profiling_report.json` (`020_outputs/040_profiling/`), esquema **v0.2**: identidad conservada (`schema_version:"0.2"`, `client`, `flow`, `success`) + bloque `health` (`global_score`, `files_declared`, `files_healthy`, `files_with_problems`, `problems_by_type`, `pareto`).
- **Reutiliza sin ampliar:** `Flow`/`FlowResult`/`Artifact`/`FlowContractError` (`core/flow.py`), `ClientContext` (`core/context.py`). No modifica `run()`, `write_outputs()`, el gate `D-080`, la CLI, ni el esquema de `ingestion_report.json`.
- **Supuesto de contrato (NC-2):** `ingestion_report.json` cumple el contrato de `ingestion` (esquema CONFORME). Manejo defensivo de JSON corrupto o campos ausentes = **fuera de alcance**; solo la ausencia física del archivo está cubierta (`CA-23`).

## Estrategia de Test
- **Unit (`tests/flows/test_profiling.py`):** un test por caso (1–22) sobre `ClientContext` bajo `tmp_path` con `create_client` + un `ingestion_report.json` de fixture con conteos conocidos, en el estilo de los tests de `tracer_bullet` ya presentes (helper `_build_ctx_con_ingestion_report_*`). Aserciones sobre el bloque `health` resultante y `pytest.raises(FlowContractError)` para el error duro.
- **Fixtures / datos de prueba:** helper(s) que fabrican un `ingestion_report.json` con:
  - `summary.files_declared` (int) con el valor deseado (incl. `0` para el borde).
  - `datasets[].files[]` con `status ∈ {"ingested","rejected","missing"}` e `inconsistencies` (lista, vacía o no) para controlar `files_healthy`/`files_with_problems`.
  - lista top-level `inconsistencies[]` de `{type, detail}` con `type` en el vocabulario cerrado de 4, para controlar `problems_by_type`/`pareto`/`global_score`.
  - `unexpected_files[]` para el caso de sobrantes (caso 14).
  - `success` (bool) para el caso de `ingestion` fallido (caso 21).
  - **Anclas numéricas de la spec** reutilizables: `{missing_column:1, files_declared:4} ⇒ 0.875`; `{missing_file:1,missing_column:1,unexpected_file:1,unexpected_column:1, files_declared:4} ⇒ 0.525`; `{missing_file:1,unexpected_file:2, files_declared:1} ⇒ 0.0` (clamp).
- **Nota sobre el test heredado de `tracer_bullet`:** el test unitario que hoy fija `schema_version=="0.1"` y el esquema mínimo `{schema_version,client,flow,success}` debe **actualizarse** al nuevo contrato v0.2 (schema `"0.2"` + bloque `health`), porque esta banda cambia el comportamiento observable del reporte de forma **aditiva pero incompatible con esa aserción literal**. Es el único ajuste a tests existentes (NC-3: cambio mínimo, justificado por el bump de contrato aprobado en `DS-PRF-7`); lo realiza el `tdd_tester` en el caso 1. Los tests de gate/CLI de `tracer_bullet` (que no asertan el cuerpo del `health`) no se tocan.
- **Integración (`integration_tester`, fuera del bucle rojo/verde):** flujo real punta a punta y coherencia entre capas con un `ingestion_report.json` realista (`CA-01..CA-23`).

## Casos de Test (bucle TDD)
Ordenados de simple/estructural a complejo (NC-4: tracer bullet primero — el camino "todos sanos" establece el esqueleto v0.2 completo; luego se añaden entradas con problemas que fuerzan cada cálculo). Coinciden con `stages.tdd.cases[]` de `state.json`. Cada caso agrupa sus tareas de test y código.

| id | Descripción (verificable) | Tareas (`TSK-xx`) | Trazabilidad → CA |
|---|---|---|---|
| 1 | `profiling_report.json` declara `schema_version=="0.2"` y conserva identidad `client==ctx.name`, `flow=="profiling"`, `success` (bool) | TSK-01, TSK-02 | CA-18, CA-19 |
| 2 | El reporte contiene un objeto `health` con **exactamente** las 6 claves `global_score`, `files_declared`, `files_healthy`, `files_with_problems`, `problems_by_type`, `pareto` (fixture "todos sanos": `global_score=1.0`, `pareto=[]`) | TSK-03, TSK-04 | CA-20, CA-17 |
| 3 | `health.files_declared == ingestion_report.summary.files_declared` | TSK-05 | CA-06 |
| 4 | `health.files_healthy` == nº de `datasets[].files[]` con `status=="ingested"` y `inconsistencies==[]` | TSK-06, TSK-08 | CA-07 |
| 5 | `health.files_with_problems` == nº de `datasets[].files[]` con `status!="ingested"` o `inconsistencies!=[]` | TSK-07, TSK-08 | CA-08 |
| 6 | Invariante `files_healthy + files_with_problems == files_declared` | TSK-09 | CA-09 |
| 7 | `health.problems_by_type` tiene las 4 claves fijas, cada una `int≥0` = ocurrencias de ese `type` en la lista top-level `inconsistencies[]` | TSK-10, TSK-11 | CA-11 |
| 8 | Fixture sin inconsistencias → `problems_by_type` con las 4 claves en `0` | TSK-12 | CA-12 |
| 9 | `health.global_score` es `float` en `[0.0, 1.0]` | TSK-13 | CA-01 |
| 10 | `global_score == round(max(0.0, 1.0 − Σ peso[t]·problems_by_type[t]/files_declared), 4)` (ancla `0.875`) | TSK-14, TSK-15 | CA-02 |
| 11 | Cuando `penalización_total > files_declared`, `global_score == 0.0` (clamp) | TSK-16, TSK-17 | CA-03 |
| 12 | Cuando `files_declared == 0`, `global_score == 1.0` (borde, sin división por cero) | TSK-18, TSK-19 | CA-04 |
| 13 | `global_score` redondeado a 4 decimales; dos entradas idénticas dan el mismo valor | TSK-20, TSK-21 | CA-05 |
| 14 | ≥1 `unexpected_file` no incrementa `files_declared` pero sí aporta a `problems_by_type.unexpected_file` y reduce `global_score` | TSK-22 | CA-10 |
| 15 | Fixture sin inconsistencias → `health.pareto == []` | TSK-23 | CA-17 |
| 16 | `pareto` incluye solo tipos con `count ≥ 1` y `Σ(pareto[].count) == Σ(problems_by_type.values())` | TSK-24, TSK-25 | CA-15 |
| 17 | Cada entrada de `pareto` tiene `type`/`count`/`pct` con `pct == round(count/Σ, 4)` | TSK-26, TSK-27 | CA-16 |
| 18 | `pareto` ordenado por `count` descendente | TSK-28, TSK-29 | CA-13 |
| 19 | Empate de `count` → orden por `type` alfabético ascendente | TSK-30, TSK-31 | CA-14 |
| 20 | Dos `run(ctx)` con el mismo `ingestion_report.json` → `profiling_report.json` byte-idéntico | TSK-32 | CA-21 |
| 21 | `ingestion.success==false` → sin excepción, `FlowResult(success=True)`, reporte con `success==true` y `health` calculado | TSK-33 | CA-22 |
| 22 | Sin `ingestion_report.json` → `FlowContractError` en `validate` nombrando el artefacto; no se escribe `profiling_report.json` | TSK-34 | CA-23 |

> Tras el bucle: `tdd_refactor` (TSK-35), `integration_tester` (TSK-36) y el gate humano `human_test` (TSK-37) cierran la feature antes del PR/merge.

### Cobertura CA → caso
CA-01→9, CA-02→10, CA-03→11, CA-04→12, CA-05→13, CA-06→3, CA-07→4, CA-08→5, CA-09→6, CA-10→14, CA-11→7, CA-12→8, CA-13→18, CA-14→19, CA-15→16, CA-16→17, CA-17→2/15, CA-18→1, CA-19→1, CA-20→2, CA-21→20, CA-22→21, CA-23→22. **Los 23 CA quedan cubiertos por ≥ 1 caso.**
