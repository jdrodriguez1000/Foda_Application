# Feature Contract — flow_orchestrator

> Artefacto **a nivel feature** (por encima de las bandas), creado por `feature_definer` en el paso *Definir*.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de iniciar la primera banda** (`D-030`).
> **Una feature tiene un solo `feature_contract`**, aunque recorra varias bandas (`tracer_bullet → stab_n`).

## Estrella Polar
Un DS puede, desde la terminal, **disparar cualquier flujo concreto por su nombre** (`foda run <cliente> --flow <flujo>`) y **ver de un vistazo qué flujos han corrido y qué artefactos existen** para un cliente (`foda status <cliente>`), sin tener que inspeccionar carpetas a mano ni escribir código, materializando el rol de revisor/aprobador descrito en `system_design.md` (D-006) y cerrando la brecha de usabilidad identificada en L-040/D-062.

## Definición de "Terminado" (feature completa)
Condiciones que deben cumplirse para considerar la feature **terminada** (no una banda suelta, sino el total):
- `foda run <cliente> --flow <flujo>` ejecuta cualquier flujo registrado del pipeline (§5 de `system_design.md`) de punta a punta sobre un cliente existente, reutilizando `Flow.run(ctx)` (`flow_base`) y `ClientContext` (`client_context`) sin reimplementar orquestación propia.
- `foda status <cliente>` reporta, para cada flujo registrado, si sus artefactos `requires`/`produces` existen en disco para ese cliente, permitiendo inferir qué flujos ya corrieron y cuáles faltan.
- Los errores esperables (cliente inexistente, flujo desconocido, `FlowContractError` por artefacto faltante) se traducen a mensajes claros en stderr + código de salida distinto de 0, sin tracebacks crudos — consistente con el estilo ya establecido en `client_new_cli`.
- El mecanismo de "flujo descubrible por nombre" (§11 de `system_design.md`) escala sin rediseño a medida que se agregan más flujos concretos al pipeline (Ingestion, Profiling, …), sin tocar el CLI cada vez que se agrega un flujo si es evitable.

## Alcance Total
**In scope (toda la feature, a través de sus bandas):**
- Comando `foda run <cliente> --flow <flujo>`: ejecución de UN flujo por su nombre, de punta a punta.
- Comando `foda status <cliente>`: introspección de artefactos existentes por flujo registrado.
- Un mecanismo de resolución "nombre de flujo → instancia de `Flow`" (registro/lookup), evitando duplicar orquestación en el CLI.
- Manejo de errores claro y consistente con el estilo de `client_new_cli` (stderr + código de salida, sin traceback crudo) para: cliente inexistente, flujo desconocido, `FlowContractError`.

**Out of scope (nunca, o en otra feature):**
- `foda run --from/--to` (rangos de flujos).
- `foda run --pipeline new/recurring` (pipelines completos encadenados).
- `foda export` (descarga de artefactos a csv/xlsx).
- Cualquier lógica propia de un flujo concreto (Discovery, Ingestion, etc.): el orquestador solo dispara flujos ya construidos, no los implementa.
- Un manifiesto de ejecución/estado separado de los artefactos en disco (descartado explícitamente por `D-021`, Single Writer Rule).

## Bandas Previstas (eje vertical)
Qué endurece cada banda hacia la estrella polar (crear **solo** las que se necesiten; `D-029`):

| Banda | Qué aporta / endurece |
|---|---|
| `tracer_bullet` | Slice vertical mínimo end-to-end (NC-4): `foda run <cliente> --flow onboarding` y `foda status <cliente>` funcionando contra el único flujo concreto real hoy (`Onboarding`), con manejo de error básico (cliente inexistente, flujo desconocido, `FlowContractError`). El mecanismo de resolución de flujos por nombre queda genérico, pero solo se ejercita con un flujo registrado (D-062). |
| `stab_1` *(prevista, no iniciada)* | Registrar más flujos concretos a medida que se construyan (Ingestion, Profiling, …) y endurecer `foda status` para reportarlos todos; ampliar mensajes de error y casos límite no cubiertos por el tracer_bullet. |

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **por celda** viven en el `spec.md` de cada banda.
1. Dado un cliente existente con los artefactos de entrada necesarios, `foda run <cliente> --flow <flujo>` ejecuta ese flujo de punta a punta y deja sus artefactos de salida escritos en disco.
2. Dado un cliente existente al que le falta un artefacto requerido por el flujo, `foda run` falla con el mensaje de `FlowContractError` (o equivalente claro), sin traceback crudo, código de salida distinto de 0.
3. Dado un cliente inexistente o un nombre de flujo no registrado, `foda run`/`foda status` fallan con mensaje claro en stderr y código de salida distinto de 0, sin tocar disco.
4. Dado un cliente existente, `foda status <cliente>` reporta, para cada flujo registrado, qué artefactos de entrada/salida existen y cuáles no, permitiendo inferir el avance del pipeline para ese cliente.
5. El orquestador no reimplementa lógica de flujo: toda ejecución delega en `Flow.run(ctx)` (`flow_base`) y toda resolución de rutas delega en `ClientContext` (`client_context`).

## Dependencias
- `flow_base` (banda `tracer_bullet`, **CONFORME**): `Flow`, `FlowResult`, `Artifact`, `FlowContractError`.
- `client_context` (banda `tracer_bullet`, **CONFORME**): `ClientContext`, resolución de rutas y `FileNotFoundError` si el cliente no existe.
- `onboarding` (banda `tracer_bullet`, **CONFORME**): único flujo concreto real disponible para ejercitar el orquestador en esta banda.
- `client_new_cli` (banda `tracer_bullet`, **CONFORME**): referencia de estilo/estructura de la CLI `foda` (`src/foda/cli.py`, argparse, traducción de excepciones a stderr + código de salida).
- `700_architecture/system_design.md` §9 (abstracción `Flow`), §11 (interfaz CLI), §12 (caminos de ejecución nuevo/recurrente), §13 (multi-tenant).
- `800_persistence/decisions.md`: D-021 (Single Writer Rule, sin archivo de estado de runtime separado), D-054/D-062 (elección de esta feature y acotación de alcance).

## Relación con Hitos de Producto
- Cierra la brecha de usabilidad identificada tras completar 5 features de core/infraestructura (`client_scaffold`, `client_new_cli`, `client_context`, `flow_base`, `onboarding`); es el primer punto en que un humano puede disparar e inspeccionar el pipeline desde la terminal sin tocar código, contribuyendo al hito emergente **MVP**.
