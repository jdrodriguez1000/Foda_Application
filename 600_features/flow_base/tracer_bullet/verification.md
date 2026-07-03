# Verification — flow_base (banda `tracer_bullet`, T-015)

> Artefacto de la etapa 8 (`spec_verifier`). Verifica que lo construido **cumple la spec aprobada**
> (`spec.md`, GATE humano superado) recorriendo cada criterio de aceptación `CA-xx` y comprobando que
> hay evidencia (test en verde) que lo respalda. Audita; no construye ni modifica código de producción.
>
> Fuentes: `spec.md` (CA-01…CA-13 + guarda DS-FLOW-2), `definition.md` (HU-01…HU-05), `plan.md`,
> `state.json`, `src/foda/core/flow.py`, `tests/core/test_flow.py`,
> `tests/integration/test_flow_base_integration.py`.

---

## Veredicto: **CONFORME**

Los 13 criterios de aceptación (`CA-01`…`CA-13`) más la guarda defensiva `DS-FLOW-2` (caso 14, añadido
por el humano en el GATE) están cubiertos por un test en verde. La suite completa está en verde
(**94 passed**). El alcance de `definition.md` (in scope hecho, out of scope respetado) y las
restricciones aplicables se cumplen. No hay huecos bloqueantes.

---

## Precondición verificada

`state.json → stages.integration_tester.status == "done"` (4 tests de integración en verde). La feature
tiene la integración cerrada; procede la verificación contra la spec.

---

## Resultado de la suite

```
python -m pytest -q  →  94 passed in 0.55s   (verde, 0 fallos, 0 errores)
```

Desglose relevante:
- `tests/core/test_flow.py` — 14 casos unit del bucle TDD (1 parametrizado sobre 6 claves base).
- `tests/integration/test_flow_base_integration.py` — 4 casos de integración end-to-end.
- Resto de la suite (client_scaffold / client_context / client_new_cli) — sin regresiones.

---

## Matriz de trazabilidad CA → evidencia → estado

| CA | Criterio (resumen) | HU | Test (evidencia) | Estado |
|---|---|---|---|---|
| CA-01 | Subclase trivial hereda `run(ctx)` sin orquestación propia y devuelve `FlowResult` | HU-01 | `test_flow.py::test_run_heredado_ejecuta_hasta_el_final_y_devuelve_flow_result` | Cubierto |
| CA-02 | `run(ctx)` invoca los 4 hooks en orden fijo, una vez cada uno | HU-02 | `test_flow.py::test_run_invoca_los_cuatro_hooks_en_orden_y_una_vez_cada_uno` | Cubierto |
| CA-03 | Ante `require` faltante la secuencia corta tras `validate` (no `execute`/`write_outputs`) | HU-02, HU-03 | `test_flow.py::test_run_con_require_faltante_secuencia_se_detiene_tras_validate` | Cubierto |
| CA-04 | `require` inexistente → `FlowContractError` en `validate`, antes de `execute` | HU-03 | `test_flow.py::test_run_con_require_faltante_lanza_flow_contract_error_antes_de_execute` | Cubierto |
| CA-05 | `FlowContractError` tipo propio (subclase de `Exception`); mensaje nombra el faltante | HU-03 | `test_flow.py::test_flow_contract_error_es_tipo_propio_y_mensaje_nombra_el_faltante` | Cubierto |
| CA-06 | Tras fallo por `require`, `produces` no existe en disco (sin salida espuria) | HU-03 | `test_flow.py::test_run_con_require_faltante_no_deja_produces_en_disco` | Cubierto |
| CA-07 | `run(ctx)` exitoso → `FlowResult.success == True` | HU-04 | `test_flow.py::test_run_exitoso_devuelve_flow_result_con_success_true` | Cubierto |
| CA-08 | `FlowResult.outputs` = rutas resueltas de `produces`, existentes en disco | HU-04 | `test_flow.py::test_run_exitoso_expone_outputs_resueltos_y_existentes_en_disco` | Cubierto |
| CA-09 | Rutas resueltas solo vía `ctx` para las 6 claves base (`ctx.<k>_dir / relative`) | HU-05 | `test_flow.py::test_artifact_path_resuelve_las_seis_claves_base_solo_via_ctx` (parametrizado ×6) | Cubierto |
| CA-10 | `Artifact` declarativo (`name`/`base`/`relative`); `path(ctx)`/`exists(ctx)` correctos | HU-05, HU-01 | `test_flow.py::test_artifact_path_y_exists_para_base_outputs` | Cubierto |
| CA-11 | Subclase sin override de `execute` → `NotImplementedError` en `run(ctx)` | HU-01 | `test_flow.py::test_run_sin_override_de_execute_lanza_not_implemented_error` | Cubierto |
| CA-12 | `requires` vacío pasa `validate` y `run(ctx)` completa las 4 fases | HU-02, HU-01 | `test_flow.py::test_run_con_requires_vacio_pasa_validate_y_completa_las_cuatro_fases` | Cubierto |
| CA-13 | Varios `require` faltantes → mensaje agrega **todos** los ausentes | HU-03 | `test_flow.py::test_run_con_varios_requires_faltantes_mensaje_identifica_todos` | Cubierto |
| DS-FLOW-2 | `Artifact.path(ctx)` con `base` desconocida → `ValueError` (guarda GATE) | — | `test_flow.py::test_artifact_path_con_base_desconocida_lanza_value_error` | Cubierto |

**Refuerzo de integración (end-to-end sobre cliente real vía `create_client`):**

| Test de integración | Refuerza |
|---|---|
| `test_run_end_to_end_sobre_cliente_real_resuelve_require_existente_y_produce_output` | CA-04 (feliz), CA-07, CA-08 |
| `test_run_end_to_end_falla_temprano_si_el_require_no_existe_en_el_cliente_real` | CA-04, CA-05, CA-06 |
| `test_artifact_base_coincide_con_las_carpetas_reales_de_create_client` | CA-09, CA-10 (contrato `flow_base ⇄ client_context ⇄ client_scaffold`) |
| `test_run_end_to_end_produce_artefacto_consumible_por_flujo_vecino` | §8 (artefacto de un flujo = `require` del vecino) |

---

## Cobertura HU → CA (toda HU cubierta por ≥1 CA con evidencia)

| HU | Cubierta por | Estado |
|---|---|---|
| HU-01 | CA-01, CA-10, CA-11, CA-12 | Cubierta |
| HU-02 | CA-02, CA-03, CA-12 | Cubierta |
| HU-03 | CA-03, CA-04, CA-05, CA-06, CA-13 | Cubierta |
| HU-04 | CA-07, CA-08 | Cubierta |
| HU-05 | CA-09, CA-10 | Cubierta |

Las 5 historias de usuario quedan cubiertas por al menos un CA con test en verde.

---

## Cumplimiento de alcance y restricciones

**In scope (`definition.md`) — hecho:**
- Clase base `Flow` con atributos de contrato (`name`/`requires`/`produces`), template method `run(ctx)`
  en orden fijo y 4 hooks sobreescribibles. ✓
- `validate()` base con comprobación real de existencia en disco de `requires`, fallo temprano con
  `FlowContractError` antes de `execute()`. ✓
- `FlowResult(success, outputs)` y `Artifact(name, base, relative)` declarativos. ✓
- Tracer bullet (flujo trivial en los tests) que ejercita orden de fases, corte por `require` faltante y
  materialización de `produces`; valida la integración `Flow ⇄ ClientContext`. ✓

**Out of scope — respetado:**
- No hay flujos reales concretos, ni orquestador, ni esquemas Pydantic/JSON Schema, ni integración LLM,
  ni ampliación de `ClientContext`. `src/foda/core/flow.py` expone solo `Flow`/`Artifact`/`FlowResult`/
  `FlowContractError`. ✓
- `write_outputs` transaccional e "inconsistencias como estado suave" en `FlowResult` correctamente
  diferidos (sin campo `messages`), conforme DS-FLOW-3 / NC-2. ✓

**Restricciones aplicables:**
- **R1 (Python 3.13+, solo stdlib):** `flow.py` importa solo `dataclasses` y `pathlib` (+ type hint de
  `ClientContext`); cero dependencias nuevas. ✓
- **D-042 (sin validación de contenido/esquema):** `validate` base solo comprueba existencia. ✓
- **NC-3 (cambios quirúrgicos):** `context.py` y `scaffold.py` intactos; se consumen tal cual. ✓
- **LLM aislado:** N/A en esta abstracción (fuera de alcance). ✓
- **GATE #5 / #6:** `execute()` construye el `FlowResult` (`run` lo devuelve tal cual); orden
  `load_inputs → validate → execute → write_outputs`. Verificado por CA-02/CA-03. ✓

---

## Hallazgos / huecos

- **Bloqueantes:** ninguno.
- **No bloqueantes (backlog, sin acción en esta banda):**
  1. **`write_outputs` transaccional** y **inconsistencias como estado suave** (`FlowResult.messages`):
     diferidos a `stab_1` (sin consumidor hoy, NC-2 / DS-FLOW-3). Cuando un flujo real escriba múltiples
     artefactos con semántica "todo o nada", endurecer aquí.
  2. **`requires` multi-flujo complejo:** el mecanismo lo soporta; esta banda solo lo ejercita al mínimo
     (caso 13, dos faltantes). Se endurecerá con el primer flujo real (`stab_1`).
  3. Estos puntos ya están documentados como limitaciones conocidas en `spec.md` y `definition.md`; no
     representan incumplimiento de la spec de esta banda.

---

## Cierre

Feature `flow_base` / banda `tracer_bullet` (T-015): **CONFORME**. La cadena SDD/TDD de 8 etapas queda
completa para esta celda. Sin retorno a etapas anteriores.
