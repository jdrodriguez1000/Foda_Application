# Verification — profiling (banda `tracer_bullet`)

> Artefacto de la etapa 8 (`spec_verifier`). Verifica que lo construido **cumple la especificación aprobada** (`spec.md`): cada criterio de aceptación (`CA-xx`) tiene evidencia (test y/o comportamiento comprobable). Auditoría, no construcción.

## Veredicto

**CONFORME.**

Los 13 criterios de aceptación de `spec.md` (CA-01…CA-13) están **cubiertos** por evidencia de test. La suite completa está en **verde (207 passed)**. El alcance de `definition.md` se respeta (in scope hecho, out of scope no invadido) y las restricciones aplicables se cumplen.

## Precondición de entrada

- `stages.integration_tester.status = "done"` (15 tests de integración en `tests/integration/test_profiling_integration.py`, suite en 207 passed). Precondición satisfecha: se procede a verificar.

## Matriz de trazabilidad (CA → evidencia → estado)

| CA | Criterio (resumen) | Evidencia (test) | Estado |
|---|---|---|---|
| CA-01 | `Profiling` subclase de `Flow`; `name`, `requires`, `produces` correctos | `tests/flows/test_profiling.py::test_profiling_es_subclase_de_flow_con_contrato_correcto` (caso 1) | Cubierto |
| CA-02 | No sobreescribe `run`; invoca las 4 fases en orden | `tests/flows/test_profiling.py::test_profiling_hereda_run_de_flow_e_invoca_las_4_fases_en_orden` (caso 2) | Cubierto |
| CA-03 | Con `ingestion_report` (success:true), `run(ctx)` → `FlowResult(success=True, outputs=[…profiling_report.json])` | `tests/flows/test_profiling.py::test_profiling_run_devuelve_flowresult_success_con_output_profiling_report` (caso 3); integración `test_run_end_to_end_sobre_cliente_real_con_ingestion_report_producido_por_ingestion_real` | Cubierto |
| CA-04 | `profiling_report.json` parseable, campos de identidad y serialización determinista | `tests/flows/test_profiling.py::test_profiling_report_json_en_disco_es_parseable_con_campos_y_serializacion_deterministas` (caso 4) | Cubierto |
| CA-05 | Sin `ingestion_report`, `validate(ctx)` lanza `FlowContractError` nombrándolo; no escribe reporte | `tests/flows/test_profiling.py::test_profiling_validate_sin_ingestion_report_lanza_flowcontracterror_nombrandolo_y_no_escribe_profiling_report` (caso 5); borde CLI caso 17 `test_run_profiling_con_ingestion_report_ausente_con_force_devuelve_1_por_flow_contracterror`; integración `test_run_falla_temprano_con_flow_contract_error_si_falta_ingestion_report_en_cliente_real` | Cubierto |
| CA-06 | `foda run --flow profiling` success:true sin `--force` → exit 0, stdout completado, reporte presente | `tests/test_orchestrator.py::test_resolve_flow_profiling_devuelve_instancia_de_profiling` (caso 6); `test_evaluate_predecessor_gate_profiling_devuelve_none_con_ingestion_report_success_true` (caso 8); `tests/cli/test_profiling_gate_cli.py::test_run_profiling_con_ingestion_report_success_true_sin_force_devuelve_0_y_escribe_reporte` (caso 11); integración `test_cli_run_profiling_con_ingestion_real_success_true_sin_force_exit0_y_escribe_reporte` | Cubierto |
| CA-07 | success:false sin `--force` → exit 1, stderr nombra `ingestion` + motivo | `tests/test_orchestrator.py::test_evaluate_predecessor_gate_profiling_devuelve_mensaje_con_ingestion_report_success_false` (caso 9); `tests/cli/test_profiling_gate_cli.py::test_run_profiling_con_ingestion_report_success_false_sin_force_devuelve_1_y_no_escribe_nada` (caso 12); integración `test_cli_run_profiling_con_ingestion_real_success_false_sin_force_exit1_y_no_escribe_nada` | Cubierto |
| CA-08 | En CA-07 no se escribe ningún artefacto bajo `040_profiling/` | `tests/cli/test_profiling_gate_cli.py::test_run_profiling_con_ingestion_report_success_false_sin_force_devuelve_1_y_no_escribe_nada` (caso 12); integración misma prueba de disco | Cubierto |
| CA-09 | `--force` con success:false → exit 0, reporte presente | `tests/cli/test_profiling_gate_cli.py::test_run_profiling_con_ingestion_report_success_false_con_force_devuelve_0_escribe_reporte_y_advierte` (caso 13); integración `test_cli_run_profiling_con_force_sobre_ingestion_real_success_false_exit0_advierte_y_escribe` | Cubierto |
| CA-10 | En CA-09, advertencia a stderr sobre el gate sobrepasado (`ingestion`) | `tests/cli/test_profiling_gate_cli.py::test_run_profiling_con_ingestion_report_success_false_con_force_devuelve_0_escribe_reporte_y_advierte` (caso 13); integración caso `_con_force_…_advierte_y_escribe` | Cubierto |
| CA-11 | `--force` con success:true → exit 0, reporte presente, sin advertencia espuria | `tests/cli/test_profiling_gate_cli.py::test_run_profiling_con_ingestion_report_success_true_con_force_devuelve_0_escribe_reporte_y_sin_advertencia` (caso 14) | Cubierto |
| CA-12 | `PREDECESSORS == {"profiling":"ingestion"}`; flujo sin predecesor → gate no-op | `tests/test_orchestrator.py::test_predecessors_mapea_profiling_a_ingestion_y_gate_es_noop_sin_predecesor` (caso 7); `tests/cli/test_profiling_gate_cli.py::test_run_ingestion_flujo_sin_predecesor_gate_es_noop_y_corre_como_antes_de_la_feature` (caso 15); integración `test_cli_run_ingestion_flujo_sin_predecesor_no_se_ve_afectado_por_el_gate_de_profiling` | Cubierto |
| CA-13 | `ingestion_report` ausente sin `--force` → exit 1, stderr claro, sin artefacto | `tests/test_orchestrator.py::test_evaluate_predecessor_gate_profiling_devuelve_mensaje_con_ingestion_report_ausente` (caso 10); `tests/cli/test_profiling_gate_cli.py::test_run_profiling_con_ingestion_report_ausente_sin_force_devuelve_1_y_no_escribe_nada` (caso 16); integración `test_cli_run_profiling_sin_ingestion_report_en_disco_sin_force_exit1_sin_artefacto` | Cubierto |

**Resultado: 13/13 CA cubiertos.** Ningún criterio queda parcial o no cubierto.

## Resultado de la suite

```
python -m pytest -q  →  207 passed in 5.71s   (verde)
```

Desglose relevante: 17 casos del bucle TDD unitario/CLI (`tests/flows/test_profiling.py`, `tests/test_orchestrator.py`, `tests/cli/test_profiling_gate_cli.py`) + 15 tests de integración (`tests/integration/test_profiling_integration.py`), sin regresiones sobre la base preexistente.

## Cumplimiento de alcance y restricciones

**In scope (`definition.md`) — hecho:**
- `Flow` concreto `Profiling` que declara `requires` (`ingestion_report.json`) y `produces` (`profiling_report.json` con campo `success`) y completa las 4 fases del template method sin reimplementar orquestación (CA-01…CA-05).
- Gate de progresión `D-080` puntos 1-3, alojado en `_dispatch_run` (DS-PROF-1), con mapa `PREDECESSORS` (DS-PROF-2), evaluador `evaluate_predecessor_gate` (DS-PROF-4) y flag `--force` (CA-06…CA-13).
- Fixtures fabricados: `ingestion_report.json` con `success:true` y `success:false` ejercitados en los tests CLI e integración.

**Out of scope — respetado (no invadido):**
- No hay lógica de salud de datos (indicador global, desglose, pareto): `profiling_report.json` es mínimo (`schema_version`, `client`, `flow`, `success`).
- No se lee ni audita `bronze/`; el único insumo es el reporte JSON del predecesor.
- No hay exportables csv/xlsx, ni comparación contra `client_register.yaml`, ni uso de LLM (Profiling determinista). Confirmado por lectura de `spec.md` §No-Objetivos y por la ausencia de esos comportamientos en la suite.

**Restricciones aplicables:**
- **JSON out determinista:** `profiling_report.json` con `sort_keys`, `indent=2`, newline final (CA-04, verificado byte a byte en el caso 4).
- **LLM aislado:** no se introduce llamada a LLM (Profiling es determinista); cumplido.
- **Ruta del predecesor no hardcodeada:** se resuelve vía `resolve_flow("ingestion").produces[0].path(ctx)` (DS-PROF-2), reutilizando `ClientContext`.
- **Sin ampliar el contrato de `Flow`:** `--force` vive en la CLI (`args.force`), no en `ClientContext` ni en `Flow.run` (DS-PROF-1/DS-PROF-4); cumplido.

## Hallazgos / observaciones

- **Observación (no bloqueante, ajena a esta feature):** `pyproject.toml` declara `requires-python = ">=3.13"`, mientras que el intérprete del entorno de verificación es **Python 3.12.10**. La suite completa corre en verde (207 passed) sobre 3.12, por lo que **no afecta la conformidad de `profiling`** (ningún CA ni comportamiento de la feature depende de una característica de 3.13). Es una condición de entorno preexistente, no un defecto introducido por esta feature. Se deja constancia para que el humano alinee entorno y declaración si lo estima (no requiere retorno a ninguna etapa de la cadena de `profiling`).
- **Deuda conocida y aceptada (heredada del bucle TDD, no bloqueante):** (1) duplicación deliberada de fixtures entre suites de `tests/cli/` (aislamiento sin `conftest.py` compartido, documentada en el docstring del módulo); (2) duplicación preexistente del patrón `print(f"foda: {msg}", file=sys.stderr); return 1` en `cli.py`. Ambas fueron señaladas y justificadas en los refactors de los casos 11/12/15; no constituyen incumplimiento de la spec.

No se detectan huecos de cobertura ni incumplimientos de la spec. No se recomienda retorno a etapas anteriores.
