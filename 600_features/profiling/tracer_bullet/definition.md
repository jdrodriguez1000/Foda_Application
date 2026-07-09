# Definition — profiling

> Artefacto de la etapa 1 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `profiling` (snake_case)
- **Banda:** `tracer_bullet` (D-019; celda = feature × banda)
- **Componente / flujo:** 040 Profiling (`system_design.md` §5, §6, §8, §10, §15). Sigue a Ingestion (030) en la secuencia canónica `Discovery → Onboarding → Ingestion → Profiling → Cleaning → …` (`990_documents/expected_workflow.md`). Hereda de `Flow` (`flow_base`, CONFORME) y consume `ClientContext` (`client_context`, CONFORME).

## Problema / Necesidad
Esta feature resuelve **dos necesidades entrelazadas, deliberadamente acotadas**:

1. **Esqueleto vertical del flujo 040.** Ingestion (030) ya produce una copia inmutable de los datos crudos en `bronze/` y un `ingestion_report.json` con un campo `success`, pero ningún flujo posterior existe todavía. Antes de construir la lógica pesada de salud de datos (indicador global, desglose por tipo de problema, pareto, exportables), hace falta el esqueleto mínimo de `Profiling` como `Flow` concreto: que arranque, lea el reporte de su predecesor y produzca su propio reporte mínimo, integrado a la abstracción `Flow`/`ClientContext` ya existente. Ese esqueleto es el terreno donde se apoya la segunda necesidad.

2. **Gate de progresión entre flujos (`D-080`, T-036).** Durante la prueba humana de `ingestion` (T-033) se detectó que nada impedía encadenar flujos aunque el predecesor hubiera terminado con inconsistencias (`success:false`): un operador o script que solo mirara el exit code no se enteraría. El ADR `D-080` (puntos 1-3) define la política — ningún flujo corre si su predecesor no terminó con `success == true`, salvo `--force` explícito, y si no hay OK, `foda run` falla limpio (exit 1, sin escribir nada) — pero esos puntos quedaron **pendientes de implementación** porque, por NC-2/NC-4, no se construye un gate genérico sin un caso de uso concreto que lo ejercite. `profiling` es ese primer caso de uso: el primer flujo real posterior a `ingestion`, cuyo predecesor ya escribe `success` en su reporte.

Sin este esqueleto no hay dónde materializar el gate; sin el gate, cualquier flujo futuro (incluida la versión completa de `profiling` en `stab_1`) podría encadenarse sobre datos de `bronze/` que Ingestion marcó como inconsistentes, sin que nadie se entere por el exit code.

## Alcance

**In scope (banda `tracer_bullet`):**
- Un `Flow` concreto `Profiling` (hereda de `flow_base`) que:
  1. Declara como `requires`: `ingestion_report.json` (`020_outputs/030_ingestion/`), el artefacto que representa el reporte de su predecesor.
  2. Declara como `produces`: un reporte mínimo `profiling_report.json` en `020_outputs/040_profiling/`, con al menos un campo `success` (boolean).
  3. Completa las 4 fases del template method de `Flow` (`load_inputs → validate → execute → write_outputs`), análogo a `Ingestion`/`Onboarding`.
- **Gate de progresión entre flujos** (`D-080`, puntos 1-3, T-036), implementado y ejercitado sobre `profiling`:
  a. Antes de ejecutar `profiling`, se lee `ingestion_report.json` (el reporte del predecesor `ingestion`) y se comprueba su campo `success`.
  b. Si `success != true` y no se invocó con `--force`, la ejecución de `profiling` **falla limpio**: código de salida 1, mensaje claro que identifique el flujo predecesor y el motivo, y **sin escribir ningún artefacto de `profiling`** (ni `profiling_report.json` ni ningún otro).
  c. Un flag `--force` (a nivel `foda run`) permite ejecutar `profiling` de todos modos aunque el predecesor no tenga `success == true`, dejando registrada una advertencia (dónde y en qué formato queda esa advertencia es un supuesto abierto para `spec_writer`, ver más abajo).
- Fixtures fabricados por esta banda: un `ingestion_report.json` con `success:true` (camino feliz del gate) y otro con `success:false` (camino de fallo del gate), análogos en espíritu a los fixtures fabricados por `onboarding`/`ingestion`.

**Out of scope (esta banda; se retoma explícitamente en `stab_1` o feature posterior):**
- **Lógica de salud de datos**: cálculo del indicador global de salud (%), desglose por tipo de problema (faltantes, duplicados, inconsistentes, desactualizados, incompletos, periodicidad menor a la mínima) y pareto. `profiling_report.json` en esta banda es un reporte mínimo (con `success`), no el informe de salud real descrito en `system_design.md` §15.
- **Lectura real de `bronze/`**: esta banda no necesita leer ni auditar los datos copiados por Ingestion; su único insumo es el reporte JSON del predecesor.
- **Exportables csv/xlsx** (`foda export --flow profiling`).
- **Comparación contra `client_register.yaml`** (Discovery real aún no existe).
- Uso de LLM (Profiling es determinista, §6).
- El gate de progresión para flujos anteriores a `ingestion` (`discovery`/`onboarding` quedan exceptuados por `D-080` punto 5, ya decidido; no se revisita aquí).

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como **desarrollador del harness**, quiero que `Profiling` se integre como un `Flow` concreto sobre `ClientContext`, para reutilizar la orquestación y resolución de rutas ya construidas en `flow_base`/`client_context`. | `Profiling` hereda de `Flow`, declara `requires`/`produces` como `Artifact`, y su `run(ctx)` completa las 4 fases del template method sin reimplementar orquestación propia. |
| HU-02 | Como **operador del harness**, quiero que `foda run` bloquee la ejecución de `profiling` si el `ingestion_report.json` de su predecesor no tiene `success == true`, para no encadenar flujos sobre datos que `ingestion` ya marcó como inconsistentes. | Dado un `ingestion_report.json` con `success:false`, `foda run <cliente> --flow profiling` (sin `--force`) sale con código 1, imprime un mensaje claro identificando el bloqueo, y no escribe `profiling_report.json` ni ningún otro artefacto de `profiling`. |
| HU-03 | Como **operador del harness**, quiero poder forzar la ejecución de `profiling` con un flag `--force` aunque el predecesor no tenga `success == true`, para poder inspeccionar manualmente el flujo en un escenario de depuración sin tener que corregir `ingestion` primero. | Dado un `ingestion_report.json` con `success:false`, `foda run <cliente> --flow profiling --force` ejecuta `profiling` de todos modos, deja registrada una advertencia, y produce su reporte mínimo con normalidad. |
| HU-04 | Como **operador del harness**, quiero que `profiling` corra con normalidad cuando el predecesor sí tuvo éxito, para confirmar que el gate no introduce fricción en el camino feliz. | Dado un `ingestion_report.json` con `success:true`, `foda run <cliente> --flow profiling` (sin `--force`) ejecuta `profiling` sin bloqueo y produce `profiling_report.json` con normalidad. |
| HU-05 | Como **flujo downstream futuro (Cleaning)**, quiero que `profiling` produzca un reporte mínimo con un campo `success`, para que, en el futuro, el mismo patrón de gate se pueda encadenar entre `profiling` y `cleaning`. | Para el fixture acordado, `profiling_report.json` existe en `020_outputs/040_profiling/` y expone al menos el campo `success` (boolean), coherente con el resultado de la ejecución. |

## Dependencias
- `flow_base` (banda `tracer_bullet`, **CONFORME**): clase base `Flow`, `FlowResult`, `Artifact`, `FlowContractError` (`src/foda/core/flow.py`).
- `client_context` (banda `tracer_bullet`, **CONFORME**): `ClientContext` (`src/foda/core/context.py`).
- `ingestion` (banda `tracer_bullet`, **CONFORME**): produce `ingestion_report.json` con campo `success` (`src/foda/flows/f030_ingestion/ingestion.py`); es el reporte que el gate de esta feature debe leer.
- `flow_orchestrator` (banda `tracer_bullet`, **CONFORME**): CLI `foda run`/`foda status` (`src/foda/cli.py`, `src/foda/orchestrator.py`); el gate y el flag `--force` se materializan en esta capa (probablemente en `_dispatch_run` o en `Profiling.validate()`; la ubicación exacta queda a `spec_writer`/`plan_builder`, ver supuestos).
- `700_architecture/system_design.md` §5 (modelo de flujos), §6 (determinismo), §7 (estructura de carpetas), §8 (contrato de artefactos), §10 (capas medallion, exportables), §15 (detalle 040 Profiling).
- `800_persistence/decisions.md`: `D-080` (gate de progresión + exit code; puntos 1-3 pendientes, esta feature los implementa), `D-079`/`D-081` (política de ramas y PR).

## Riesgos y Supuestos
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** dónde vive exactamente la lógica del gate — dentro de `Profiling.validate()`/`execute()` (el propio flujo se niega a correr), o en la capa de despacho de la CLI (`_dispatch_run` en `src/foda/cli.py`, antes de invocar `flow.run(ctx)`), o en el `orchestrator` (`resolve_flow`/registro de predecesores). `system_design.md` no fija esto; queda a `spec_writer`/`plan_builder` decidirlo explícitamente (NC-6), siendo consistente con el estilo ya usado por `FlowContractError` en `flow_base`.
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** cómo se declara/descubre "quién es el predecesor de quién" (¿hardcodeado a `ingestion → profiling` en esta banda, análogo a `FLOWS` en `orchestrator.py`, o mediante algún mapa explícito de predecesores?). Dado el alcance acotado de esta banda (un único par ingestion→profiling), NC-2 sugiere la solución más simple; `spec_writer`/`plan_builder` deben decidirlo y documentarlo.
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** formato exacto de `profiling_report.json` en esta banda (¿solo `success`, o también `timestamp`/`predecessor`/algún campo adicional mínimo?) y formato/destino exacto de la advertencia que deja `--force` (¿stderr, campo en el propio reporte, log?). `system_design.md` no lo fija para este esqueleto mínimo (el informe de salud real es de `stab_1`); queda a `spec_writer`/`plan_builder` proponerlo, respetando NC-2.
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** cómo se propaga el flag `--force` desde `argparse` (`run_parser` en `cli.py`) hasta la comprobación del gate — como argumento nuevo de `_dispatch_run`, o pasado dentro de `ClientContext`/`FlowResult`. Queda a `spec_writer`/`plan_builder` definirlo sin ampliar innecesariamente el contrato de `Flow` (NC-2/NC-3).
- **Aclaración de dominio (no es ambigüedad, para que `spec_writer` no la confunda):** esta banda de `profiling` **no** calcula salud de datos, no lee `bronze/`, y no exporta csv/xlsx; eso es explícitamente `stab_1` o una feature posterior. El propósito de esta banda es doble: (a) esqueleto vertical mínimo de `Flow` para 040, y (b) anfitrión concreto del gate de progresión `D-080`/T-036.
- **Riesgo:** si en el futuro `discovery`/`onboarding` dejan de estar exceptuados del gate (`D-080` punto 5 es una excepción "temporal"), habrá que revisar si el mismo mecanismo construido aquí para `ingestion → profiling` generaliza sin cambios o si requiere ajuste; no se aborda en esta banda.
- **Riesgo:** el nombre exacto del artefacto/reporte de esta banda (`profiling_report.json`) es una propuesta de este documento, análoga a `ingestion_report.json`/`map_client_data.json`; `spec_writer` puede ajustarlo si encuentra una razón de peso, documentándolo (NC-6).
