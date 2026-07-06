# Verification — onboarding (banda `tracer_bullet`)

> Artefacto de la etapa 8 (`spec_verifier`, SDD/TDD). Verifica que lo construido **cumple la
> especificación aprobada** (`spec.md`). El verificador **audita, no construye**: comprueba que cada
> criterio de aceptación tenga **evidencia** (test que lo cubre / comportamiento comprobable), corre
> la suite completa y emite veredicto. Fuentes: `spec.md`, `definition.md`, `plan.md`, `state.json`,
> `700_architecture/system_design.md`, `800_persistence/decisions.md`.

## Veredicto

**CONFORME.**

Los 22 criterios de aceptación de `spec.md` (CA-01…CA-21 + CA-05b) están **cubiertos** por evidencia
(test unitario y/o de integración en verde). La suite completa pasa (121 passed, sin regresión). El
alcance de `definition.md` se cumple (in scope hecho, out of scope respetado) y las restricciones
aplicables se satisfacen. La etapa previa (`integration_tester`) está cerrada (`status = "done"`),
requisito para verificar.

---

## Matriz de trazabilidad — criterio → evidencia → estado

| CA | Criterio (resumen) | HU | Evidencia (test) | Estado |
|---|---|---|---|---|
| CA-01 | `run(ctx)` sobre fixture válido escribe `map_client_data.json` y devuelve `FlowResult(success=True, outputs=[ruta])`; el archivo existe | HU-01, HU-05 | `test_run_sobre_fixture_valido_escribe_map_client_data_y_devuelve_flow_result` | Cubierto |
| CA-02 | `hierarchies.product.levels == [familia,categoria,subcategoria,clase]` y `depth == 4` | HU-01 | `test_hierarchies_product_levels_y_depth` | Cubierto |
| CA-03 | `hierarchies.geography.levels == [region,pais,ciudad,sede]` y `depth == 4` | HU-01 | `test_hierarchies_geography_levels_y_depth` | Cubierto |
| CA-04 | `unique_values`/`unique_counts` por nivel = distintos observados, orden alfabético | HU-01 | `test_hierarchies_unique_values_y_unique_counts_por_nivel` | Cubierto |
| CA-05 | Profundidad ≠ 4 (3 niveles) ⇒ `depth == 3`, sin hardcode de 4 | HU-01 | `test_hierarchies_product_levels_de_3_niveles_depth_igual_a_3` | Cubierto |
| CA-05b | Profundidad > 4 (5 niveles, incl. `sku`) ⇒ `depth == 5`, niveles en orden, uniques para los 5 | HU-01 | `test_hierarchies_product_levels_de_5_niveles_depth_igual_a_5_incl_sku` | Cubierto |
| CA-06 | 2 datasets con `kind`/`source_medium`/`periodicity` en orden de contrato | HU-02 | `test_datasets_kind_source_medium_periodicity_en_orden_de_contrato` | Cubierto |
| CA-07 | `file_count` 1 (ventas) y 2 (inventario); `files[*]` name/period (incl. multi-año) | HU-02 | `test_datasets_file_count_y_files_name_period_start_period_end` | Cubierto |
| CA-08 | `fields` con name/type/required/maps_to (incl. `precio_unitario` required=false, maps_to=null) | HU-03 | `test_datasets_fields_name_type_required_maps_to` | Cubierto |
| CA-09 | `maps_to` proviene del contrato, no del nombre de columna | HU-03 | `test_maps_to_proviene_del_contrato_no_del_nombre_de_columna` | Cubierto |
| CA-10 | `totals.dataset_count == 2` y `totals.file_count == 3` | HU-02 | `test_totals_dataset_count_y_file_count` | Cubierto |
| CA-11 | `Onboarding` hereda `Flow`, declara requires/produces y completa 4 fases sin sobreescribir `run` | HU-05 | `test_onboarding_hereda_flow_declara_contratos_y_completa_las_4_fases` | Cubierto |
| CA-12 | Tras `run` exitoso, nada bajo bronze/silver/gold; único artefacto `map_client_data.json` | HU-05 | `test_run_exitoso_no_deja_nada_bajo_bronze_silver_gold` | Cubierto |
| CA-13 | Dos `run` con mismo input ⇒ `map_client_data.json` idéntico byte a byte | HU-01 | `test_dos_run_con_mismo_input_producen_map_client_data_identico_byte_a_byte` | Cubierto |
| CA-14 | `levels == []` (product o geography) ⇒ `FlowContractError`; sin output | HU-04 | `test_product_levels_vacio_lanza_flow_contract_error_y_no_crea_output` | Cubierto |
| CA-15 | Miembro con claves que no coinciden con `levels` ⇒ `FlowContractError`; sin output | HU-04 | `test_miembro_con_claves_que_no_coinciden_con_levels_lanza_flow_contract_error_y_no_crea_output` | Cubierto |
| CA-16 | `maps_to` a `<level>` inexistente ⇒ `FlowContractError`; sin output | HU-04 | `test_maps_to_con_level_inexistente_lanza_flow_contract_error_y_no_crea_output` | Cubierto |
| CA-17 | Enum inválido (type/kind/source_medium/periodicity) ⇒ `FlowContractError`; sin output | HU-04 | `test_enum_invalido_en_field_type_lanza_flow_contract_error_y_no_crea_output` | Cubierto |
| CA-18 | Fecha no `YYYY-MM-DD` o `period_start > period_end` ⇒ `FlowContractError`; sin output | HU-04 | `test_period_start_mayor_que_period_end_lanza_flow_contract_error_y_no_crea_output` | Cubierto |
| CA-19 | Dos `field.name` duplicados en un dataset ⇒ `FlowContractError`; sin output | HU-04 | `test_field_name_duplicado_en_dataset_lanza_flow_contract_error_y_no_crea_output` | Cubierto |
| CA-20 | `contract_data.json` ausente ⇒ `FlowContractError` en `validate` (base); sin output | HU-04, HU-05 | `test_contract_data_ausente_lanza_flow_contract_error_y_no_crea_output` | Cubierto |
| CA-21 | Ante cualquier inconsistencia, el fallo ocurre en `validate` (antes de execute/write_outputs) | HU-04 | `test_ante_inconsistencia_el_fallo_ocurre_en_validate_antes_de_execute_write_outputs` | Cubierto |

**Cobertura:** 22/22 criterios **cubiertos**. 0 parciales, 0 no cubiertos.

### Cobertura de integración (refuerzo end-to-end, `tests/integration/test_onboarding_integration.py`)

| Test de integración | Refuerza |
|---|---|
| `test_run_end_to_end_sobre_cliente_real_produce_mapa_identico_al_esperado_fijo` | CA-01, CA-02…CA-10, CA-13 (determinismo vs. esperado fijo) |
| `test_run_exitoso_no_toca_bronze_silver_gold_del_cliente_real` | CA-12 |
| `test_run_falla_temprano_con_flow_contract_error_si_falta_contract_data_en_cliente_real` | CA-20, CA-21 |
| `test_run_produce_artefacto_consumible_sin_fallar_por_un_flujo_vecino_real` | HU-01/HU-05 (artefacto consumible downstream) |
| `test_aislamiento_multi_tenant_entre_dos_clientes_reales_bajo_el_mismo_clients_root` | Aislamiento por cliente (ClientContext) |

### Trazabilidad HU → CA (todas las HU cubiertas)

| HU | Cubierta por | Estado |
|---|---|---|
| HU-01 | CA-01, CA-02, CA-03, CA-04, CA-05, CA-05b, CA-13 | Cubierta |
| HU-02 | CA-06, CA-07, CA-10 | Cubierta |
| HU-03 | CA-08, CA-09 | Cubierta |
| HU-04 | CA-14, CA-15, CA-16, CA-17, CA-18, CA-19, CA-20, CA-21 | Cubierta |
| HU-05 | CA-01, CA-11, CA-12, CA-20 | Cubierta |

---

## Resultado de la suite completa

```
python -m pytest -q
121 passed in ~0.76s
```

- **Total: 121 passed, 0 failed** (verde).
- Composición: 22 unitarios (`tests/flows/test_onboarding.py`) + 5 de integración
  (`tests/integration/test_onboarding_integration.py`) de esta feature; el resto pertenece a las
  features previas (core `flow_base`/`client_context`, CLI, etc.) — sin regresión.

---

## Cumplimiento de alcance y restricciones

**In scope (`definition.md`) — hecho:**
- `Flow` concreto `Onboarding` que declara `requires=[contract_data]`/`produces=[map_client_data]` y
  completa las 4 fases del template method sin sobreescribir `run` (CA-11).
- Lee/parsea `contract_data.json`; valida coherencia **antes** de derivar; falla con
  `FlowContractError` sin escribir output ante inconsistencia (CA-14…CA-21).
- Deriva `map_client_data.json` con niveles/profundidad, valores únicos por nivel, inventario de
  datasets/archivos y esquema de columnas con `maps_to` (CA-01…CA-10).
- Profundidad dinámica de jerarquías (CA-05, CA-05b); multi-dataset/multi-archivo/multi-año
  (CA-06, CA-07); columnas required/opcional y `maps_to=null` (CA-08); `maps_to` por contrato, no
  por nombre (CA-09).

**Out of scope — respetado:**
- No hay Discovery real (usa fixture); no hay Ingestion (030) ni lectura de csv/xlsx reales; no se
  escribe en `bronze/`/`silver/`/`gold/` (CA-12, verificado también en integración). No se valida la
  existencia física de los archivos históricos. No se usa LLM (flujo determinista). No hay
  orquestador `foda run` ni ampliación de `ClientContext`. No se usa JSON Schema/Pydantic (validación
  explícita en `validate()`).

**Restricciones (system_design / decisiones) — satisfechas:**
- Determinismo (§6): serialización estable (`sort_keys=True`, `indent=2`, `ensure_ascii=False`,
  newline final); uniques ordenados alfabéticamente — verificado byte a byte (CA-13) y vs. esperado
  fijo (integración).
- Excepción de dominio única `FlowContractError` para require ausente y toda inconsistencia de
  contenido (DS-ONB-1).
- Ubicación de artefactos vía `Artifact(base="outputs", relative=...)` sin ampliar el core
  (DS-ONB-5).
- Reutilización de código CONFORME (`flow_base`, `client_context`) sin modificarlo (NC-3).

---

## Hallazgos / observaciones

- **OBS-1 (menor, no bloqueante).** El apartado *Comportamiento Esperado 2b* de `spec.md` enumera la
  regla de validación **"`field.required` es booleano"**, que **no** está codificada como criterio de
  aceptación `CA-xx` ni tiene test propio; el código de producción (`validate()`) tampoco la
  implementa como regla explícita. No constituye no conformidad porque la fuente de verdad de esta
  verificación son los criterios `CA-xx` (todos cubiertos) y ninguno la exige. Se deja como candidato
  de endurecimiento para `stab_1`: si se decide exigirla, la ruta es `spec_writer` (añadir `CA-xx`) →
  bucle TDD (test rojo→verde de la regla). No se corrige en esta banda (NC-3: cambios quirúrgicos; la
  feature cumple su contrato aprobado).

No se detectan huecos de cobertura sobre los criterios de aceptación aprobados. No se recomienda
retorno a etapas anteriores para el cierre de esta banda.
</content>
</invoke>
