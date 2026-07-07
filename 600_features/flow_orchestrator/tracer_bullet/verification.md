# Verification — flow_orchestrator (banda `tracer_bullet`)

> Artefacto de la etapa 8 (`spec_verifier`, última del flujo SDD/TDD). Verifica —de forma
> **independiente y crítica** (P3)— que lo construido **cumple la `spec.md` aprobada**. No añade
> funcionalidad ni casos: audita cobertura de cada criterio de aceptación (`CA-xx`) contra evidencia
> real y verificable (test que lo ejercita y/o comportamiento comprobable en el código).
>
> Fuentes: `spec.md` (14 CA), `definition.md` (alcance, HU-01…HU-05), `plan.md` (trazabilidad
> CA↔caso↔TSK), `state.json`, y el código/tests reales (`src/foda/orchestrator.py`, `src/foda/cli.py`,
> `tests/test_orchestrator.py`, `tests/cli/test_flow_orchestrator_cli.py`,
> `tests/integration/test_flow_orchestrator_integration.py`).

---

## Veredicto

**CONFORME.** Los 14 criterios de aceptación (CA-01…CA-14) tienen evidencia real y verificable; la
suite completa está en verde (145 passed); el alcance in-scope está cubierto, el out-of-scope
respetado, y las restricciones aplicables se cumplen. La feature `flow_orchestrator` / banda
`tracer_bullet` queda **cerrada**.

---

## Matriz de trazabilidad — CA → evidencia → estado

Cada CA se verificó leyendo el test citado (que **existe** y **ejerce** el criterio) y el código de
producción que lo soporta, no confiando en el `state.json`.

| CA | Criterio (resumen) | Evidencia (test que lo ejerce) | Estado |
|---|---|---|---|
| CA-01 | `run ABC --flow onboarding` con contrato válido → `0` y escribe `map_client_data.json` | `test_run_onboarding_con_contrato_valido_devuelve_0_y_escribe_map_client_data` (assert `result==0` + `map_client_data.exists()`); integración `test_run_end_to_end_...` (contenido real del mapa) | **Cubierto** |
| CA-02 | Éxito: `stdout` menciona flujo, cliente y ruta del artefacto | `test_run_onboarding_exitoso_stdout_confirma_flujo_cliente_y_artefacto` (assert `"onboarding"`, `"ABC"`, `"map_client_data.json"` en `stdout`); `_dispatch_run` construye ese mensaje | **Cubierto** |
| CA-03 | Delegación estricta: `flow.run` invocado 1 vez con `ctx.name=="ABC"` | `test_run_invoca_flow_run_una_sola_vez_con_ctx_cuyo_name_es_abc` (spy sobre `Onboarding.run`, `len(calls)==1`, `calls[0].name=="ABC"`) | **Cubierto** |
| CA-04 | `run ABC --flow inexistente` → `1`, `stderr` nombra el flujo, sin `Traceback`, sin artefacto | `test_run_flujo_inexistente_devuelve_1_stderr_nombra_flujo_sin_traceback_ni_artefacto` + unit `test_resolve_flow_nombre_no_registrado_lanza_value_error` | **Cubierto** |
| CA-05 | `run GHOST --flow onboarding` → `1`, `stderr` nombra el cliente, sin `Traceback`, nada escrito | `test_run_cliente_inexistente_devuelve_1_stderr_nombra_cliente_sin_traceback_ni_artefacto` | **Cubierto** |
| CA-06 | `run ABC` sin `contract_data.json` → `1`, `stderr` refleja `FlowContractError`, sin `Traceback`, no escribe mapa | `test_run_sin_contract_data_devuelve_1_stderr_refleja_flow_contract_error` (assert `"contract_data"` en `stderr`); integración `test_run_falla_temprano_...` con `Onboarding.validate` real | **Cubierto** |
| CA-07 | `status ABC` → `0` y lista `onboarding` con `contract_data`/`map_client_data` + marcador | `test_status_onboarding_lista_contract_data_y_map_client_data_con_marcadores` | **Cubierto** |
| CA-08 | `status` refleja el disco antes/después de un `run` exitoso (ambos `[presente]`) | `test_status_refleja_disco_antes_y_despues_de_run_exitoso` (marcador por línea, 3 invocaciones); integración `test_status_refleja_end_to_end_...` | **Cubierto** |
| CA-09 | `status GHOST` → `1`, `stderr` nombra el cliente (estilo `run`), sin `Traceback` | `test_status_cliente_inexistente_devuelve_1_stderr_nombra_cliente_sin_traceback` | **Cubierto** |
| CA-10 | `FLOWS` explícito + `resolve_flow`: `"onboarding"`→instancia `Onboarding`; no registrado→`ValueError` | `test_resolve_flow_onboarding_devuelve_instancia_de_onboarding`, `test_flows_es_mapeo_explicito_onboarding_a_clase_onboarding`, `test_resolve_flow_nombre_no_registrado_lanza_value_error` | **Cubierto** |
| CA-11 | Flujo falso en `FLOWS` descubierto por `status` y `run` sin tocar su lógica | `test_flujo_falso_en_flows_es_descubierto_por_status_y_run_sin_tocar_logica` (`FakeFlow` vía `monkeypatch.setitem`, iteración genérica de `FLOWS.items()`) | **Cubierto** |
| CA-12 | `run`/`status` no crean `clients/` ni carpeta del cliente inexistente | `test_run_y_status_cliente_inexistente_no_crean_arbol_de_clients` (assert `not clients_root.exists()`); integración `test_entry_point_real_run_cliente_inexistente_...` | **Cubierto** |
| CA-13 | Errores de parseo argparse → código `2` (`run ABC`, `run`, `status`) | `test_argparse_falta_argumento_requerido_devuelve_codigo_2` (3 `SystemExit.code==2`) | **Cubierto** |
| CA-14 | Suite de CLI de orquestación **independiente** de `client_new_cli`, en verde | Suite `tests/cli/test_flow_orchestrator_cli.py` (12 tests) + `tests/test_orchestrator.py` (3 tests); independencia verificada: **no** hay `conftest.py` en `tests/cli/` ni `tests/`, **no** hay import cruzado de `test_client_new_cli` (solo referencia textual en docstring), fixtures locales por test | **Cubierto** |

---

## Resultado de la suite

```
python -m pytest -q
145 passed in 5.32s
```

Verde completo, sin fallos ni errores. Coincide con el `suite_evidence` del `integration_tester`
(145 passed = 136 del bucle TDD + 9 de integración). Ninguna regresión.

---

## Cumplimiento de alcance y restricciones

**Alcance (`definition.md`):**
- **In scope hecho:** `foda run <cliente> --flow <flujo>` (resuelve cliente vía `ClientContext`,
  flujo vía `resolve_flow`, delega en `Flow.run`); `foda status <cliente>` (introspección de
  `requires`/`produces` vía `Artifact.exists`); manejo de los tres errores esperables (cliente
  inexistente → `FileNotFoundError`; flujo desconocido → `ValueError`; artefacto faltante →
  `FlowContractError`) traducidos a `stderr` + código `1`, sin `Traceback`; integración en la CLI
  `foda` existente sin CLI paralela. Las 5 HU quedan cubiertas por ≥1 CA verde.
- **Out of scope respetado:** no hay `--from/--to`, `--pipeline`, `foda export`, flujos nuevos,
  manifiesto de estado propio, validación de contenido en `status`, ni concurrencia. No se introdujo
  descubrimiento dinámico de flujos (registro literal `FLOWS`).

**Restricciones:**
- **R1 (Python 3.13+, solo stdlib):** `orchestrator.py`/`cli.py` usan únicamente `argparse`,
  `pathlib`, `sys`; cero dependencias nuevas. Verificado en los imports reales.
- **NC-2 (simplicidad):** registro literal `{"onboarding": Onboarding}`, sin abstracción de registro
  ni excepción propia (`ValueError` reutilizado).
- **NC-3 (cambio quirúrgico):** el despacho `run`/`status` no altera `client new`; el único
  `mkdir(clients_root)` queda en la rama de `client new` (línea 115 de `cli.py`), **después** de los
  `return` de `run`/`status` — coherente con CA-12.
- **D-021 (Single Writer):** `status` no lee estado propio; introspecciona el disco de artefactos.
- **Delegación estricta (C-5):** el orquestador no reimplementa lógica de flujo ni de rutas; toda
  ejecución pasa por `Flow.run(ctx)` y toda resolución de rutas por `ClientContext`/`Artifact`
  (confirmado por CA-03 y por la integración con el `Onboarding` real).

---

## Hallazgos / huecos

Ninguno. No se detectaron CA sin evidencia, tests citados inexistentes, tests que no ejerzan su
criterio, ni discrepancias entre el `state.json` y el código/tests reales. No hay recomendación de
retorno a etapas anteriores.

---

## Cierre

Feature `flow_orchestrator`, banda `tracer_bullet`: **CONFORME**. Cadena SDD/TDD (8/8 etapas)
completada. `stages.spec_verifier.status = "done"`; a nivel feature `status = "done"`,
`current_stage = "completed"`.
