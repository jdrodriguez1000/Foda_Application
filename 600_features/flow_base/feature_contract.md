# Feature Contract — flow_base

> Artefacto **a nivel feature** (por encima de las bandas), creado por `feature_definer` en el paso *Definir*.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de iniciar la primera banda** (`D-030`).
> **Una feature tiene un solo `feature_contract`**, aunque recorra varias bandas (`tracer_bullet → stab_n`).

## Estrella Polar
Cualquier flujo concreto (Discovery, Ingestion, Cleaning, …) se implementa heredando de una única clase base `Flow` que garantiza, sin que cada flujo tenga que reimplementarlo, el mismo ciclo de vida en el mismo orden (`load_inputs → validate → execute → write_outputs`) y la misma validación temprana de contrato de entrada (`system_design.md` §9), consumiendo `ClientContext` (T-014) para resolver rutas sin conocer la estructura interna de `clients/<NAME>/`.

## Definición de "Terminado" (feature completa)
Condiciones que deben cumplirse para considerar la feature **terminada** (no una banda suelta, sino el total):
- Existe una clase base `Flow` (previsiblemente en `src/foda/core/flow.py`) con atributos de contrato `name`, `requires`, `produces` y un template method `run(ctx: ClientContext) -> FlowResult` que invoca en orden fijo `load_inputs → validate → execute → write_outputs` (§9).
- `validate()` base comprueba, como mínimo, que cada artefacto de `requires` existe en disco (resuelto vía `ctx`) y falla temprano con un error de contrato claro si falta alguno, antes de `execute()` (§9, §8).
- `FlowResult` encapsula estado (éxito/inconsistencias) y las rutas de los artefactos generados.
- `Artifact` es un descriptor mínimo y declarativo que permite a `requires`/`produces` resolver su ruta vía `ctx` y comprobar existencia.
- Un `Flow` concreto trivial (tracer bullet) demuestra end-to-end que la plantilla funciona: ejecuta las 4 fases en orden, corta temprano cuando falta un `require`, y deja en disco el artefacto declarado en `produces` cuando corre completo.
- Cada flujo real (Discovery, Ingestion, etc.) puede heredar de `Flow` y sobreescribir únicamente sus 4 hooks, sin tener que reimplementar la orquestación ni la validación mínima de existencia.

## Alcance Total
**In scope (toda la feature, a través de sus bandas):**
- Clase base `Flow` con contrato (`name`, `requires`, `produces`) y template method `run()`.
- Los 4 hooks sobreescribibles: `load_inputs`, `validate`, `execute`, `write_outputs`.
- `validate()` base: existencia en disco de los artefactos de `requires`, resuelta vía `ClientContext`; falla temprano con `FlowContractError` (o similar) si falta alguno.
- `FlowResult` (estado + rutas de artefactos generados).
- `Artifact` (descriptor declarativo mínimo, sin JSON Schema/Pydantic).
- Tracer bullet: un `Flow` concreto trivial (definido en tests) que ejercita el ciclo completo y prueba la integración con `ClientContext`.

**Out of scope (nunca, o en otra feature):**
- Flujos reales concretos (Discovery, Ingestion, Cleaning, …): cada uno es una feature/tarea futura que hereda de `Flow`.
- El orquestador (`foda run`, selección de pipeline nuevo/recurrente, rangos `--from/--to`, §11-§12): otra feature.
- Esquemas formales de artefactos (Pydantic/JSON Schema) para validar contenido/estructura de cada artefacto: diferido por flujo concreto (`D-042`, mismo criterio aplicado a `client_context`).
- Integración con el LLM (paso opcional dentro de `execute()` en flujos concretos).
- Introspección de "qué artefactos ya existen" más allá de lo que `ClientContext` ya expone (responsabilidad de `client_context`, no de `flow_base`).

## Bandas Previstas (eje vertical)
Qué endurece cada banda hacia la estrella polar (crear **solo** las que se necesiten; `D-029`):

| Banda | Qué aporta / endurece |
|---|---|
| `tracer_bullet` | Slice vertical mínimo end-to-end (NC-4): clase `Flow` + 4 hooks + template method `run()` en orden fijo, `validate()` base con comprobación de existencia en disco, `FlowResult`, `Artifact` mínimo, y un flujo trivial de prueba que valida la integración `Flow` ⇄ `ClientContext`. |
| `stab_1` *(prevista, no iniciada)* | Endurecimiento a determinar cuando los primeros flujos reales (p. ej. Discovery) consuman `Flow` y revelen necesidades no cubiertas por el tracer bullet (p. ej. mensajes de error más ricos, soporte a `requires` de artefactos de más de un flujo atrás, §8). |

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **por celda** viven en el `spec.md` de cada banda.
1. Un flujo concreto puede definirse heredando de `Flow` y sobreescribiendo únicamente sus 4 hooks, sin reimplementar la orquestación.
2. `run(ctx)` invoca `load_inputs → validate → execute → write_outputs` siempre en ese orden, para cualquier `Flow` concreto.
3. Si falta un artefacto declarado en `requires`, el flujo falla antes de `execute()`, con un error de contrato claro y sin dejar estado espurio en disco.
4. `run(ctx)` consume `ClientContext` (T-014) para resolver rutas de artefactos, sin conocer la estructura interna de `clients/<NAME>/`.
5. El resultado de `run(ctx)` es un `FlowResult` que expone estado (éxito/inconsistencias) y las rutas de los artefactos generados.

## Dependencias
- `client_context` (banda `tracer_bullet`, CONFORME): provee `ClientContext` en `src/foda/core/context.py`, consumida por `Flow.run(ctx: ClientContext)`.
- `700_architecture/system_design.md` §7 (estructura de carpetas), §8 (contrato de artefactos entre flujos), §9 (abstracción común de flujo).
- `800_persistence/decisions.md` D-042 (esquemas de contenido de artefacto diferidos por flujo, mismo criterio aplicado aquí).
- Es dependencia de todos los flujos concretos futuros (Discovery, Onboarding, Ingestion, …).

## Relación con Hitos de Producto
- Cuarta de las features fundacionales del orden de construcción abajo-hacia-arriba (`client_scaffold → client_context → flow_base → flujos`, `D-016`). Cierra la base sobre la que emergerá el hito **MVP** del producto (`D-029`): una vez terminada, los flujos concretos pueden empezar a construirse; no es un hito en sí misma.
