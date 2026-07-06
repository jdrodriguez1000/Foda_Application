# Definition — flow_orchestrator

> Artefacto de la etapa 1 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `flow_orchestrator` (snake_case)
- **Banda:** `tracer_bullet` (D-019; celda = feature × banda)
- **Componente / flujo:** Orquestador de la CLI `foda` (`system_design.md` §4 "Orquestador", §11 "Interfaz CLI"). No es un flujo del pipeline 010–140: es el componente de código que dispara flujos concretos (hoy, solo `Onboarding`/020) y reporta su estado, apoyándose en `Flow`/`FlowResult`/`FlowContractError` (`flow_base`, CONFORME) y `ClientContext` (`client_context`, CONFORME).

## Problema / Necesidad
Tras completar `client_scaffold`, `client_new_cli`, `client_context`, `flow_base` y `onboarding`, existe ya un flujo concreto real (`Onboarding`) capaz de producir `map_client_data.json`, pero **no hay ninguna forma de dispararlo ni de inspeccionarlo desde la terminal**: hoy solo se puede instanciar `Onboarding` y llamar `.run(ctx)` escribiendo código Python ad-hoc. Esto contradice el rol del DS como revisor/aprobador (`system_design.md` D-006) y el diseño de CLI ya definido en `system_design.md` §11, que nunca se materializó (diferido por `D-054`/T-026). `flow_orchestrator` resuelve esta brecha construyendo los comandos `foda run` y `foda status` diseñados en §11, acotados a lo que la banda `tracer_bullet` necesita (D-062): un flujo por su nombre, sin rangos ni pipelines encadenados.

## Alcance

**In scope (banda `tracer_bullet`):**
- `foda run <cliente> --flow <flujo>`: resuelve el cliente vía `ClientContext(cliente, clients_root)`, resuelve `<flujo>` a una instancia concreta de `Flow` (mecanismo de resolución nombre→flujo, a definir por `spec_writer`/`plan_builder`; el único flujo registrado hoy es `onboarding`), y ejecuta `flow.run(ctx)`.
- `foda status <cliente>`: resuelve el cliente vía `ClientContext` y, para cada flujo registrado (hoy, solo `onboarding`), reporta qué artefactos de `requires`/`produces` existen en disco (usando `Artifact.exists(ctx)` de `flow_base`), permitiendo inferir qué flujos han corrido.
- Manejo de errores claro (stderr + código de salida ≠ 0, sin traceback crudo, estilo consistente con `client_new_cli`):
  1. Cliente inexistente → `ClientContext` lanza `FileNotFoundError`, la CLI lo traduce.
  2. Nombre de flujo desconocido (no registrado) → error propio de la CLI/orquestador.
  3. Artefacto requerido faltante → `FlowContractError` (ya existente en `flow_base`), la CLI lo traduce.
- Integración con la CLI `foda` existente (`src/foda/cli.py`), añadiendo los subcomandos `run` y `status` junto al ya existente `client new`, manteniendo el mismo estilo (argparse, traducción de excepciones).

**Out of scope (esta banda; puede o no llegar en `stab_1`):**
- `foda run --from/--to` (rangos de flujos encadenados).
- `foda run --pipeline new/recurring` (pipelines completos).
- `foda export` (descarga de artefactos a csv/xlsx).
- Registrar o construir flujos nuevos (Discovery, Ingestion, Profiling, …): esta feature solo orquesta flujos ya construidos; hoy el único disponible es `onboarding`.
- Un archivo de manifiesto/estado de ejecución separado (descartado por `D-021`, Single Writer Rule); `foda status` introspecciona el disco vía `ClientContext`/`Artifact`, no lee un estado propio.
- Ejecución concurrente/paralela de flujos.

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como **DS**, quiero ejecutar `foda run <cliente> --flow onboarding` desde la terminal, para disparar el flujo Onboarding de punta a punta sin escribir código Python ad-hoc. | Dado un cliente existente con `contract_data.json` presente, el comando ejecuta `Onboarding.run(ctx)`, deja `map_client_data.json` escrito en disco, imprime una confirmación legible y termina con código de salida 0. |
| HU-02 | Como **DS**, quiero que `foda run` falle con un mensaje claro cuando el cliente no existe, el flujo indicado no está registrado, o falta un artefacto requerido por el flujo (`FlowContractError`), para diagnosticar el problema sin leer código ni tracebacks. | Cada uno de los tres casos (cliente inexistente, flujo desconocido, artefacto faltante) produce un mensaje específico en stderr y código de salida ≠ 0, sin traceback de Python expuesto al usuario. |
| HU-03 | Como **DS**, quiero ejecutar `foda status <cliente>` para ver qué flujos han corrido y qué artefactos existen para ese cliente, para decidir el siguiente paso sin inspeccionar carpetas a mano. | Dado un cliente existente, el comando lista, para el flujo registrado (`onboarding`), si sus artefactos de entrada/salida (`contract_data.json`, `map_client_data.json`) existen o no en disco. |
| HU-04 | Como **DS**, quiero que `foda status` también falle con un mensaje claro si el cliente no existe, para no confundir "cliente sin actividad" con "cliente inexistente". | Dado un cliente inexistente, `foda status` produce un mensaje claro en stderr (mismo estilo que `foda run`) y código de salida ≠ 0. |
| HU-05 | Como **desarrollador del harness**, quiero que el orquestador resuelva flujos por nombre a través de un mecanismo simple y explícito (no hardcodeado por completo en el CLI ni sobre-diseñado), para poder registrar flujos nuevos en el futuro sin rediseñar el CLI. | Existe una forma explícita de mapear el string `<flujo>` (p. ej. `"onboarding"`) a una instancia concreta de `Flow`, reutilizada tanto por `foda run` como por `foda status`; añadir un flujo nuevo no requiere cambiar la lógica de `foda run`/`foda status`, solo registrar el flujo nuevo. |

## Dependencias
- `flow_base` (banda `tracer_bullet`, **CONFORME**): `Flow`, `FlowResult`, `Artifact`, `FlowContractError` (`src/foda/core/flow.py`).
- `client_context` (banda `tracer_bullet`, **CONFORME**): `ClientContext` (`src/foda/core/context.py`), `FileNotFoundError` si el cliente no existe.
- `onboarding` (banda `tracer_bullet`, **CONFORME**): `Onboarding` (`src/foda/flows/f020_onboarding/onboarding.py`), único flujo concreto real disponible para ejercitar el orquestador.
- `client_new_cli` (banda `tracer_bullet`, **CONFORME**): `src/foda/cli.py` (argparse, resolución de `clients_root` vía `pyproject.toml`, estilo de traducción de excepciones a stderr + código de salida) — el orquestador se integra en el mismo archivo/estilo, no crea una CLI paralela.
- `700_architecture/system_design.md` §4 (orquestador), §9 (abstracción `Flow`), §11 (interfaz CLI), §12 (caminos nuevo/recurrente).
- `800_persistence/decisions.md`: D-021 (Single Writer Rule), D-054 (orden de construcción), D-062 (elección y acotación de esta feature).

## Riesgos y Supuestos
- **Supuesto abierto (punto de confirmación para el GATE de `spec_writer`):** el mecanismo concreto de "resolución de flujo por nombre" (p. ej. un diccionario literal `{"onboarding": Onboarding}` en el módulo del orquestador, vs. un registro más formal) no está decidido; queda a `spec_writer`/`plan_builder` proponerlo explícitamente, respetando NC-2 (simplicidad primero) — dado que hoy solo existe UN flujo concreto real, la solución más simple posible es preferible a una abstracción de registro genérica sin necesidad demostrada (E4).
- **Supuesto abierto (punto de confirmación para el GATE de `spec_writer`):** el tipo de excepción a usar para "flujo desconocido" (p. ej. `ValueError` vs. una excepción propia del orquestador) no está decidido; queda a `spec_writer`/`plan_builder` definirlo explícitamente (NC-6), siguiendo el patrón ya usado en `client_new_cli` (`ValueError`/`FileExistsError` traducidos a stderr + código 1).
- **Supuesto abierto (punto de confirmación para el GATE de `spec_writer`):** el formato exacto de salida de `foda status` (texto plano legible vs. una estructura más formal) no está fijado por `system_design.md` más allá de "muestra qué flujos se han ejecutado y qué artefactos existen"; queda a `spec_writer`/`plan_builder` proponerlo, cubriendo como mínimo lo listado en HU-03.
- **Riesgo:** con un solo flujo concreto real (`onboarding`) disponible, el tracer_bullet solo puede ejercitar `foda run`/`foda status` contra ese flujo; el mecanismo de resolución de flujos quedará genéricamente diseñado pero no probado contra un segundo flujo real hasta que se construya uno (Ingestion u otro).
- **Riesgo:** `foda status` depende de que cada `Flow` declare correctamente su `requires`/`produces` como `Artifact` (ya lo hace `Onboarding`); si un flujo futuro no los declara con fidelidad, `foda status` reportará información incompleta para ese flujo — no es un riesgo de esta feature en sí, pero condiciona su utilidad futura.
- **Aclaración de dominio (no es ambigüedad, para que `spec_writer` no la confunda):** `foda status` NO valida el contenido de los artefactos ni corre ninguna lógica de flujo; solo comprueba existencia en disco vía `Artifact.exists(ctx)`. Validar contenido/consistencia es responsabilidad del propio flujo al correr (`validate()`), no del orquestador.
