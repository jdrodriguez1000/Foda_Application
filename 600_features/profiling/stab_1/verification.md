# Verification — profiling (banda `stab_1`)

> Artefacto de la etapa 8 (`spec_verifier`). Verifica que lo construido **cumple la especificación aprobada** (`spec.md`, 23 criterios de aceptación CA-01…CA-23) de principio a fin. Auditoría de cobertura y ejecución de la suite completa; no añade funcionalidad.
>
> Fuentes: `600_features/profiling/stab_1/spec.md`, `definition.md`, `plan.md`, `state.json`. Código: `src/foda/flows/f040_profiling/profiling.py`. Tests: `tests/flows/test_profiling.py`, `tests/integration/test_profiling_integration.py`.

## Veredicto: **CONFORME**

La feature `profiling` banda `stab_1` cumple los 23 criterios de aceptación de `spec.md`, respeta el alcance de `definition.md` (in scope hecho, out of scope no invadido) y las restricciones aplicables. La suite completa está en verde (228 passed, 0 failed).

Precondición verificada: `stages.integration_tester.status == "done"` (TSK-36 cerrado). Se procede con la verificación.

---

## Matriz de trazabilidad (criterio → evidencia → estado)

Cada CA de `spec.md` está cubierto por un test unitario de la banda (`tests/flows/test_profiling.py`, caso del bucle TDD) y/o por los tests end-to-end de integración (`tests/integration/test_profiling_integration.py`).

| CA | Criterio (resumen) | Evidencia (test) | Estado |
|---|---|---|---|
| CA-01 | `global_score` float en [0.0,1.0] | caso 9 · `test_..._global_score_es_float_en_rango_0_1_fixture_mixta` | Cubierto |
| CA-02 | `global_score` == fórmula ponderada (ancla 0.875) | caso 10 · `test_..._global_score_coincide_con_formula_ponderada_ancla_0_875` | Cubierto |
| CA-03 | Clamp: penalización > files_declared ⇒ 0.0 | caso 11 · `test_..._global_score_es_0_0_cuando_penalizacion_total_excede_files_declared_clamp` | Cubierto |
| CA-04 | Borde files_declared==0 ⇒ 1.0 (sin div/0) | caso 12 · `test_..._global_score_es_1_0_cuando_files_declared_es_cero_borde_sin_division_por_cero` | Cubierto |
| CA-05 | Redondeo a 4 decimales + determinismo | caso 13 · `test_..._global_score_redondeado_a_4_decimales_y_deterministico_para_entradas_identicas` | Cubierto |
| CA-06 | `files_declared` == summary.files_declared | caso 3 · `test_..._files_declared_coincide_con_summary_files_declared` | Cubierto |
| CA-07 | `files_healthy` == archivos ingested sin inconsistencias | caso 4 · `test_..._files_healthy_coincide_con_conteo_de_archivos_sanos_fixture_mixta` | Cubierto |
| CA-08 | `files_with_problems` == archivos con problema | caso 5 · `test_..._files_with_problems_coincide_con_conteo_de_archivos_con_problemas_fixture_mixta` | Cubierto |
| CA-09 | Invariante healthy + with_problems == declared | caso 6 · `test_..._cumple_invariante_files_healthy_mas_files_with_problems_igual_files_declared` | Cubierto |
| CA-10 | unexpected_file no suma a declared pero sí a problems_by_type y baja score | caso 14 · `test_..._unexpected_file_no_incrementa_files_declared_pero_aporta_a_problems_by_type_y_reduce_global_score` + integración `test_run_health_completo_..._missing_column_y_unexpected_file` | Cubierto |
| CA-11 | `problems_by_type` 4 claves fijas = conteo de inconsistencies[] | caso 7 · `test_..._problems_by_type_tiene_las_4_claves_fijas_con_conteos_correctos_de_inconsistencies_top_level` | Cubierto |
| CA-12 | Sin inconsistencias ⇒ 4 claves en 0 | caso 8 · `test_..._problems_by_type_tiene_las_4_claves_en_cero_fixture_sin_inconsistencias` | Cubierto |
| CA-13 | `pareto` ordenado por count descendente | caso 18 · `test_..._pareto_ordenado_por_count_descendente_orden_distinto_del_vocabulario` | Cubierto |
| CA-14 | Empate ⇒ desempate por type alfabético ascendente | caso 19 · `test_..._pareto_ante_empate_de_count_desempata_por_type_alfabetico_ascendente` + integración (empate missing_column/unexpected_file) | Cubierto |
| CA-15 | `pareto` solo count≥1 y Σcount == Σproblems_by_type | caso 16 · `test_..._pareto_incluye_solo_tipos_con_count_mayor_igual_1_y_suma_de_counts_igual_a_suma_de_problems_by_type` | Cubierto |
| CA-16 | Cada entrada {type,count,pct} con pct==round(count/Σ,4) | caso 17 · `test_..._pareto_cada_entrada_tiene_type_count_pct_con_pct_igual_a_round_count_sobre_total_4` | Cubierto |
| CA-17 | Sin inconsistencias ⇒ `pareto == []` | casos 2 y 15 · `test_..._pareto_es_lista_vacia_fixture_sin_inconsistencias` | Cubierto |
| CA-18 | `schema_version == "0.2"` | caso 1 · `test_..._es_parseable_con_campos_y_serializacion_deterministas` (verificado en src línea 153) | Cubierto |
| CA-19 | Identidad conservada: client/flow/success | caso 1 · idem | Cubierto |
| CA-20 | `health` con exactamente 6 claves | caso 2 · `test_..._contiene_bloque_health_con_exactamente_6_claves_fixture_todos_sanos` | Cubierto |
| CA-21 | Dos run ⇒ reporte byte-idéntico | caso 20 · `test_..._dos_ejecuciones_con_mismo_ingestion_report_producen_profiling_report_byte_identico` | Cubierto |
| CA-22 | ingestion.success==false ⇒ no lanza, success=true, health calculado | caso 21 · `test_..._con_ingestion_success_false_no_lanza_y_reporte_tiene_success_true_con_health_calculado` | Cubierto |
| CA-23 | Sin ingestion_report.json ⇒ FlowContractError, no escribe | caso 22 · `test_profiling_validate_sin_ingestion_report_lanza_flowcontracterror_nombrandolo_y_no_escribe_profiling_report` | Cubierto |

**Resultado:** 23/23 CA cubiertos, 0 parciales, 0 no cubiertos.

Cobertura HU (vía tabla spec.md §Trazabilidad): HU-01…HU-05 cubiertas por ≥1 CA verificado. Sin huecos.

Refuerzo end-to-end (integración, TSK-36): la salud completa se verifica además sobre un `ingestion_report.json` producido por una corrida **real** de Ingestion (no fabricado a mano), con dos tipos de problema estructural genuinos (`missing_column`, `unexpected_file`), confirmando `files_declared`, conteos, `problems_by_type`, `global_score` (fórmula real) y `pareto` con desempate alfabético sobre el contrato multi-flujo `D-014`.

---

## Resultado de la suite

- `python -m pytest -q` (suite global) ⇒ **228 passed, 0 failed** (verde).
- `python -m pytest tests/flows/test_profiling.py tests/integration/test_profiling_integration.py -q` ⇒ 41 passed (25 unit de la feature + 16 de integración).

La regresión conocida y documentada desde el caso 1 del bucle TDD (assert literal `schema_version=='0.1'` en `test_profiling_integration.py`) quedó resuelta por `integration_tester` (TSK-36): actualizada a `"0.2"` + bloque health real. No hay rojos.

---

## Cumplimiento de alcance y restricciones

**In scope (definition.md) — hecho:**
- Salud estructural derivada exclusivamente de `ingestion_report.json`: verificado (código importa solo `json` + core, no lee `bronze/`).
- `global_score` ponderado, conteos, `problems_by_type`, `pareto` con desempate: cubiertos por CA-01…CA-17.
- Bloque `health` aditivo + bump `schema_version` "0.1"→"0.2": CA-18, CA-20 (src línea 153).
- Determinismo byte a byte: CA-21.

**Out of scope — respetado:**
- No lee `bronze/`, no compara `client_register.yaml`, no exporta csv/xlsx, no usa LLM: confirmado por inspección de imports de `src/foda/flows/f040_profiling/profiling.py` (solo `json`, `foda.core.context`, `foda.core.flow`).
- No modifica el gate `D-080` ni el core `ClientContext`/`Artifact`: sin cambios en esos módulos (los tests preexistentes de tracer_bullet re-verificados en verde).
- Vocabulario cerrado de 4 tipos no ampliado.

**Restricciones aplicables:**
- YAML in / JSON out y serialización determinista (`ensure_ascii=False, indent=2, sort_keys=True` + newline): CA-21 en verde.
- LLM aislado / flujo determinista: cumplido (sin dependencia de LLM).
- Contrato de artefactos vía `ClientContext`/`Artifact`: `requires` = ingestion_report, `produces` = profiling_report; error duro solo para `requires` ausente (CA-23).

---

## Hallazgos / huecos

Ninguno. No se detectaron criterios sin evidencia, tests en rojo, ni invasión de out-of-scope. No se requiere retorno a etapas anteriores (`spec_writer`, `plan_builder`, bucle TDD ni `integration_tester`).

---

## Cierre

Feature **verificada CONFORME**. Queda pendiente el cierre a `main` mediante los gates humanos terminales (`D-079`/`D-081`): la sesión principal abre el Pull Request (`current_stage = "human_test"`), el humano prueba la feature (`human_test`) y mergea el PR (`merge_to_main`). El `spec_verifier` no abre el PR ni mergea. A nivel feature, `status` permanece `"in_progress"` hasta completar esos gates.
