# Definition — flow_base

> Artefacto de la etapa 1 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `flow_base` (snake_case)
- **Banda:** `tracer_bullet` (D-019; celda = feature × banda)
- **Componente / flujo:** Abstracción común de flujo (`system_design.md` §9, `Flow`/`FlowResult`/`Artifact`), consumidora de `ClientContext` (T-014, CONFORME). Relacionada con §8 (contrato de artefactos entre flujos) y §7 (estructura de carpetas). No es un flujo concreto (Discovery, Ingestion, …): es la plantilla que todos los flujos (010–140) implementarán.

## Problema / Necesidad
`ClientContext` (feature `client_context`, CONFORME) ya sabe resolver rutas de un cliente y determinar su modo nuevo/recurrente, pero **ningún componente sabe todavía cómo debe ejecutarse un flujo**: nada define hoy el ciclo de vida común (leer inputs, validar, ejecutar el núcleo, escribir outputs) que `system_design.md` §9 exige para TODOS los flujos, ni qué ocurre cuando a un flujo le falta un artefacto requerido. Sin esta abstracción, cada flujo concreto (Discovery, Ingestion, Cleaning, …) tendría que reimplementar su propia orquestación y su propia validación de existencia de artefactos, violando la consistencia que §9 busca garantizar y duplicando lógica entre 12+ flujos futuros. Esta feature construye esa plantilla común, siguiente eslabón del orden de construcción abajo-hacia-arriba (`client_scaffold → client_context → flow_base → flujos`, D-016), y es requisito de todo flujo real posterior.

## Alcance

**In scope:**
- Clase base `Flow` (ubicación sugerida: `src/foda/core/flow.py`) con:
  1. Atributos de contrato: `name: str`, `requires: list[Artifact]`, `produces: list[Artifact]`.
  2. Template method `run(ctx: ClientContext) -> FlowResult` que invoca, EN ORDEN FIJO, las 4 fases: `load_inputs(ctx) → validate(ctx) → execute(ctx) → write_outputs(ctx, result)`.
  3. Cuatro hooks sobreescribibles por las subclases: `load_inputs`, `validate`, `execute`, `write_outputs`.
- `validate()` base con comportamiento real pero mínimo: comprueba que cada artefacto de `requires` **existe en disco** (ruta resuelta vía `ctx`); si falta alguno, falla ANTES de `execute()` con un error de contrato claro (p. ej. `FlowContractError`). No valida contenido ni esquema del artefacto (eso queda diferido a cada flujo concreto, mismo criterio que D-042).
- `FlowResult`: objeto de retorno que encapsula estado (éxito / inconsistencias) y las rutas de los artefactos generados.
- `Artifact`: descriptor mínimo y declarativo de un artefacto, lo justo para que `requires`/`produces` sean declarativos y `validate()` pueda resolver su ruta vía `ctx` y comprobar existencia. Sin JSON Schema/Pydantic todavía.
- Tracer bullet: un `Flow` concreto trivial (definido en los tests) que declara al menos 1 `require` y 1 `produce`, usado para probar: (a) que `run()` invoca las 4 fases en el orden correcto, (b) que `validate()` corta cuando falta el `require`, y (c) que `write_outputs()` deja el artefacto declarado en `produces`. Este tracer valida la integración `Flow` ⇄ `ClientContext` (T-014).

**Out of scope:**
- Cualquier flujo real (Discovery, Ingestion, Cleaning, …): cada uno es una feature/tarea futura que hereda de `Flow`.
- El orquestador (`foda run`, selección de pipeline nuevo/recurrente, rangos `--from/--to`, §11-§12): otra feature.
- Esquemas formales de artefactos (Pydantic/JSON Schema) para validar contenido/estructura: diferido por flujo concreto (mismo criterio que D-042, decisión ya tomada para `client_context`).
- Integración con el LLM.
- Cualquier ampliación de `ClientContext` (introspección de artefactos existentes, etc.): responsabilidad de la feature `client_context`, no de esta.

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como **desarrollador de un flujo concreto**, quiero heredar de una clase base `Flow` y sobreescribir solo sus 4 hooks (`load_inputs`, `validate`, `execute`, `write_outputs`), para no tener que reimplementar la orquestación común a todos los flujos. | Un `Flow` concreto trivial, definido solo con sus hooks, expone un `run(ctx)` funcional heredado de la base sin código de orquestación propio. |
| HU-02 | Como **operador del harness**, quiero que `run(ctx)` ejecute siempre las 4 fases en el mismo orden fijo (`load_inputs → validate → execute → write_outputs`), para que el comportamiento de cualquier flujo sea predecible y consistente con `system_design.md` §9. | Instrumentando el `Flow` trivial del tracer bullet, se observa que las 4 fases se invocan en ese orden exacto, siempre, para toda ejecución completa de `run(ctx)`. |
| HU-03 | Como **operador del harness**, quiero que un flujo falle temprano (antes de `execute()`) con un mensaje claro cuando le falta un artefacto requerido, para detectar inconsistencias de contrato sin ejecutar lógica de negocio sobre datos incompletos. | Si un artefacto de `requires` no existe en disco (ruta resuelta vía `ctx`), `run(ctx)` lanza un error de contrato explícito (p. ej. `FlowContractError`) antes de invocar `execute()`, y `write_outputs()` nunca se llama. |
| HU-04 | Como **desarrollador de un flujo concreto**, quiero recibir de vuelta un `FlowResult` que encapsule el estado de la ejecución y las rutas de los artefactos generados, para poder encadenar flujos o reportar el resultado sin inspeccionar el filesystem manualmente. | Tras un `run(ctx)` exitoso sobre el `Flow` trivial del tracer bullet, el `FlowResult` devuelto indica éxito y contiene la(s) ruta(s) del/los artefacto(s) declarados en `produces`, verificablemente presentes en disco. |
| HU-05 | Como **desarrollador del harness**, quiero que `Flow` consuma `ClientContext` (T-014) para resolver rutas de artefactos, para no duplicar la lógica de resolución de carpetas ya construida en `client_context`. | El `Flow` trivial del tracer bullet resuelve las rutas de sus artefactos `requires`/`produces` exclusivamente a través de un `ClientContext` recibido en `run(ctx)`, sin reimplementar resolución de rutas propia. |

## Dependencias
- **`client_context`** (banda `tracer_bullet`, **CONFORME**): provee `ClientContext` en `src/foda/core/context.py`, con rutas resueltas de `010_inputs`, `020_outputs`, `data/{bronze,silver,gold}`, `models` y determinación de modo nuevo/recurrente. `Flow.run(ctx: ClientContext)` la consume tal cual; `flow_base` no reimplementa resolución de rutas.
- `700_architecture/system_design.md` §7 (estructura de carpetas), §8 (contrato de artefactos entre flujos), §9 (abstracción común de flujo).
- `800_persistence/decisions.md` D-042 (esquemas formales de artefacto diferidos por flujo; mismo criterio adoptado aquí para no bloquear `flow_base` con validación de contenido).

## Riesgos y Supuestos
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** el tipo de excepción concreto para "artefacto requerido ausente" (p. ej. `FlowContractError` propia vs. reutilizar una excepción existente del core) no está fijado por `system_design.md`; queda a `spec_writer`/`plan_builder` definirlo explícitamente (NC-6, no asumir en silencio).
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** la forma exacta del descriptor `Artifact` (dataclass mínima con `name`/`path_fn` o similar) y de `FlowResult` (dataclass con `success`/`output_paths` o similar) no está fijada por `system_design.md`; queda a `spec_writer`/`plan_builder` decidirla, respetando NC-2 (simplicidad primero, sin JSON Schema/Pydantic en esta banda).
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** cómo se resuelve la ruta de un `Artifact` vía `ctx` (p. ej. un callable `Artifact.path(ctx)`, o un mapeo declarativo por carpeta lógica) no está fijado; queda a `spec_writer`/`plan_builder`.
- **Aclaración de dominio (no es una ambigüedad, se documenta para que `spec_writer` no la confunda):** `validate()` base solo comprueba EXISTENCIA en disco del artefacto (que el archivo/carpeta esté ahí), no su contenido ni esquema. Validar contenido/esquema es responsabilidad de cada flujo concreto al sobreescribir `validate()` (o de una capa posterior, D-042). Esta feature no bloquea contenido inválido, solo ausencia.
- **Riesgo:** el `requires` real de varios flujos (§8) puede depender de artefactos de más de un flujo atrás (p. ej. Reporting necesita `contract_data.json` además de la salida de Simulation); esta banda no ejercita ese caso multi-artefacto complejo más allá de lo necesario para probar el mecanismo con el tracer bullet — se revisará al construir el primer flujo real.
- **Riesgo:** si en el futuro `write_outputs()` necesita comportamiento transaccional (todo o nada al escribir múltiples artefactos), esta banda no lo cubre; el tracer bullet escribe un único artefacto simple.
