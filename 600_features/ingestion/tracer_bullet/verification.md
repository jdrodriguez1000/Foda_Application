# Verification — ingestion (banda `tracer_bullet`)

> Artefacto de la etapa 8 (`spec_verifier`, SDD/TDD). Verifica que lo construido **cumple la especificación aprobada** (`spec.md`, CA-01..CA-21) de principio a fin. **Auditoría, no construcción**: se traza cobertura (cada criterio de aceptación → evidencia), se corre la suite completa y se emite veredicto. Fuentes: `spec.md`, `definition.md`, `plan.md`, `state.json`, `tests/flows/test_ingestion.py` (bucle TDD 22/22), `tests/integration/test_ingestion_integration.py` (7 tests).

## Veredicto

**CONFORME.** Los 21 criterios de aceptación de `spec.md` (CA-01..CA-21) tienen evidencia verificable (test unitario del bucle TDD y/o test de integración, todos en verde). La suite completa pasa (174 passed). El alcance de `definition.md` (in scope hecho, out of scope respetado) y las restricciones aplicables (Python 3.13+, JSON in/out, LLM aislado, no toca silver/gold) se cumplen. Sin huecos ni no conformidades.

## Precondición de etapa

`state.json` → `stages.integration_tester.status = "done"` (7 tests de integración verdes, sin defectos de la feature detectados). Precondición satisfecha: se verifica sobre una feature con integración cerrada.

## Matriz de trazabilidad — criterio → evidencia → estado

| CA | Criterio (resumen) | HU | Evidencia (test) | Estado |
|---|---|---|---|---|
| CA-01 | `ventas.csv` coma: `rows`/`columns` correctos, `separator == ","` | HU-01 | unit `test_reporte_registra_rows_columns_y_separator_correctos_para_ventas_csv_coma` (caso 3) | Cubierto |
| CA-02 | `inventario_2024.txt` `;`: `rows`/`columns`, `separator == ";"` | HU-01 | unit `..._para_inventario_2024_txt_punto_y_coma` (caso 4) | Cubierto |
| CA-03 | `inventario_2025.csv` `\|`: `rows`/`columns`, `separator == "\|"` | HU-01 | unit `..._para_inventario_2025_csv_barra_vertical` (caso 5) | Cubierto |
| CA-04 | `precios.xlsx`: `rows`/`columns` (1ª hoja), `separator == null` | HU-01 | unit `..._y_separator_null_para_precios_xlsx` (caso 6) | Cubierto |
| CA-05 | presentes == declarados en contrato ⇒ sin missing/unexpected, `unexpected_files == []`, `files_ingested == files_declared` | HU-02 | unit `test_presentes_igual_declarados_...` (caso 10) | Cubierto |
| CA-06 | archivo declarado ausente ⇒ `status=="missing"` + `missing_file`; sin copia; `success == False` | HU-02 | unit `test_archivo_declarado_en_contrato_no_presente_marca_missing_...` (caso 11) | Cubierto |
| CA-07 | archivo presente no declarado ⇒ `unexpected_files` + `unexpected_file`; sin copia; `success == False` | HU-02 | unit `test_archivo_presente_no_declarado_en_contrato_va_a_unexpected_files_...` (caso 12) | Cubierto |
| CA-08 | columna `required==true` ausente ⇒ `status=="rejected"` + `missing_column`; sin copia; `success == False` | HU-03 | unit `test_archivo_sin_columna_requerida_segun_mapa_marca_rejected_...` (caso 13) | Cubierto |
| CA-09 | columna no declarada en `fields` ⇒ `status=="rejected"` + `unexpected_column`; sin copia; `success == False` | HU-03 | unit `test_archivo_con_columna_no_declarada_segun_mapa_marca_rejected_...` (caso 14) | Cubierto |
| CA-10 | columna `required==false` ausente ⇒ no es inconsistencia; `ingested` | HU-03 | unit `test_archivo_sin_columna_opcional_segun_mapa_no_es_inconsistencia_...` (caso 15) | Cubierto |
| CA-11 | por archivo válido, copia byte a byte idéntica en `ctx.bronze_dir/<name>` | HU-04 | unit `test_cada_archivo_valido_tiene_copia_byte_a_byte_identica_en_bronze` (caso 8) | Cubierto |
| CA-12 | la copia conserva formato/separador/extensión (`\|` sigue `\|`; `.xlsx` idéntico) | HU-04 | unit `test_copia_en_bronze_conserva_formato_separador_y_extension` (caso 9) | Cubierto |
| CA-13 | dos `run(ctx)` con mismas entradas ⇒ reporte y copias byte-idénticos | HU-04, HU-01 | unit `test_dos_ejecuciones_con_las_mismas_entradas_producen_reporte_y_copias_bronze_byte_identicos` (caso 20) | Cubierto |
| CA-14 | `run(ctx)` escribe `ingestion_report.json` en la ruta y lo incluye en `FlowResult.outputs` | HU-05 | unit `test_run_sobre_fixture_minimo_escribe_ingestion_report_y_lo_incluye_en_outputs` (caso 1) | Cubierto |
| CA-15 | el reporte expone, por archivo, `name`/`rows`/`columns` | HU-05 | unit `test_reporte_expone_por_archivo_name_rows_y_columns_...` (caso 7) | Cubierto |
| CA-16 | lista top-level `inconsistencies[]` (DS-ING-9): cada una `type` del vocabulario cerrado + `detail` no vacío | HU-05 | unit `test_lista_top_level_inconsistencies_agrega_tipos_del_vocabulario_cerrado_con_detail_no_vacio` (caso 16) | Cubierto |
| CA-17 | `summary` con `datasets_declared`/`files_declared`/`files_ingested`/`files_with_inconsistencies` coherentes | HU-05 | unit `test_summary_reporta_los_4_conteos_derivados_del_contrato_y_coherentes_con_el_detalle` (caso 17) | Cubierto |
| CA-18 | inconsistencia parcial: válidos se copian, inválidos no; reporte refleja ambos; `success == False` | HU-02, HU-03, HU-04 | unit `test_inconsistencia_parcial_copia_los_validos_y_excluye_el_invalido_con_bronze_path_coherente` (caso 19) + integración `test_inconsistencia_parcial_real_copia_solo_los_validos_a_bronze_y_success_false` | Cubierto |
| CA-19 | `success == True` sii sin inconsistencias; si no, `False` y el reporte se escribe igualmente | HU-05 | unit `test_success_es_true_sii_reporte_sin_inconsistencias_y_reporte_se_escribe_en_ambos_casos` (caso 18) | Cubierto |
| CA-20 | `Ingestion(Flow)` con `requires`/`produces` exactos y las 4 fases sin sobreescribir `run` | HU-06 | unit `test_ingestion_hereda_flow_requires_produces_y_4_fases_sin_sobreescribir_run` (caso 2) | Cubierto |
| CA-21 | falta `contract_data.json` **o** `map_client_data.json` ⇒ `FlowContractError` en `validate`; sin reporte ni bronze | HU-06, HU-05 | unit `test_contract_data_ausente_...` (caso 21) + `test_map_client_data_ausente_...` (caso 22) + integración `..._si_falta_contract_data_...` y `..._si_falta_map_client_data_...` | Cubierto |

**Cobertura: 21/21 criterios cubiertos. 0 parciales, 0 no cubiertos.**

### Cobertura de HU (vía CA)
Toda `HU-xx` de `definition.md` queda cubierta por ≥ 1 `CA-xx` verificado: HU-01 (CA-01..04, CA-13), HU-02 (CA-05..07, CA-18), HU-03 (CA-08..10, CA-18), HU-04 (CA-11..13, CA-18), HU-05 (CA-14..17, CA-19, CA-21), HU-06 (CA-20, CA-21).

## Resultado de la suite completa

```
python -m pytest -q
174 passed in 1.96s
```

- **Verde**, sin fallos ni errores. Sin regresiones.
- Desglose de la feature `ingestion`: 22 tests unitarios (`tests/flows/test_ingestion.py`, bucle TDD 22/22 cerrado) + 7 tests de integración (`tests/integration/test_ingestion_integration.py`). Los 145 restantes corresponden a features previas CONFORMES (`flow_base`, `client_context`, `onboarding`, etc.), todas en verde: sin efectos colaterales de esta feature.

## Cumplimiento de alcance y restricciones

**In scope (`definition.md`) — hecho:**
- `Ingestion(Flow)` con `requires=[contract_data, map_client_data]` / `produces=[ingestion_report]` y las 4 fases del template method sin sobreescribir `run` (CA-20).
- Formatos csv/txt/xlsx con separadores coma/`;`/`\|` y detección al leer (CA-01..04).
- Validación de conjunto de archivos contra `contract_data.json` (CA-05..07) y de columnas contra `map_client_data.json` (CA-08..10), reparto DS-ING-8.
- Copia inmutable byte a byte a `data/bronze/` de los archivos válidos (CA-11..12), copia parcial por archivo (CA-18).
- Reporte de carga JSON con archivos, filas/columnas e inconsistencias (CA-14..17, CA-19), lista top-level `inconsistencies[]` (DS-ING-9/D-078, CA-16).
- Fixtures fabricados coherentes contrato↔mapa ejercitando los 3 separadores + xlsx + `.txt` y ≥ 2 `kind` ≠ ventas.

**Out of scope — respetado:**
- No usa LLM (verificado: sin referencias a llm/anthropic/openai en `src/foda/flows/f030_ingestion/`; determinismo comprobado por CA-13).
- No escribe en `silver/`/`gold/` (verificado: sin referencias en el módulo + integración `test_run_exitoso_no_toca_silver_ni_gold_del_cliente_real`).
- No transforma datos (bronze es copia fiel, CA-11/CA-12). No hace profiling ni cleaning. Discovery real y comparación contra `client_register` diferidos. Medios `database`/`api` y validación de tipos no implementados (correcto para la banda).

**Restricciones aplicables:**
- **Python ≥ 3.13** — `pyproject.toml` `requires-python = ">=3.13"`. Cumple.
- **JSON de contrato / JSON de salida** — entradas `contract_data.json`/`map_client_data.json` y salida `ingestion_report.json` en JSON con serialización determinista (`sort_keys`, `indent=2`, newline; DS-ING-6). Los datos crudos (csv/txt/xlsx) se copian byte a byte sin re-serializar. Cumple.
- **LLM aislado** — Ingestion es determinista, sin LLM. Cumple.
- **Dependencia `openpyxl`** — declarada en `pyproject.toml`, autorizada en el GATE (DS-ING-7, punto 8). Cumple.
- **NC-3 (cambios quirúrgicos)** — no se amplió el core (`ClientContext`/`Artifact`); se reutilizó `base="inputs"` para el landing (DS-ING-4). Cumple.

## Hallazgos / huecos

Ninguno. No hay criterios sin cubrir, ni tests en rojo, ni desviaciones respecto a la spec aprobada (incluida la enmienda DS-ING-9/ADR D-078). No se requiere retorno a etapas anteriores.

## Cierre

Feature `ingestion` (banda `tracer_bullet`) **CONFORME**. La cadena SDD/TDD (etapas 1–8) queda cerrada para esta feature.
