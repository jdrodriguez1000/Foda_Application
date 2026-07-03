# Feature Contract — client_context

> Artefacto **a nivel feature** (por encima de las bandas), creado por `feature_definer` en el paso *Definir*.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de iniciar la primera banda** (`D-030`).
> **Una feature tiene un solo `feature_contract`**, aunque recorra varias bandas (`tracer_bullet → stab_n`).

## Estrella Polar
Cualquier flujo (`Flow.run(ctx: ClientContext)`, `system_design.md` §9) puede pedirle a `ClientContext` "¿quién es este cliente, dónde están sus carpetas y en qué modo (nuevo/recurrente) debe operar?" y obtener una respuesta fiable resuelta desde el disco, sin que el flujo tenga que conocer la estructura de `clients/<NAME>/` ni reimplementar su propia lógica de resolución de rutas o de detección de modo.

## Definición de "Terminado" (feature completa)
Condiciones que deben cumplirse para considerar la feature **terminada** (no una banda suelta, sino el total):
- Existe una abstracción `ClientContext` (en `src/foda/core/context.py`) que, dado un cliente existente, resuelve de forma determinista sus rutas de `010_inputs/`, `020_outputs/`, `data/{bronze,silver,gold}/` y `models/` (`system_design.md` §7).
- `ClientContext` determina el modo **nuevo vs. recurrente** de forma determinista e inferida del disco (`models/latest`), sin depender de un flag editable en `client.yaml` (§12).
- `ClientContext` falla con un error claro si el cliente no existe, sin crear ni modificar nada en el filesystem (es una abstracción de LECTURA, contraparte de `create_client`).
- `ClientContext` expone la introspección de "qué artefactos ya existen" para un cliente (§9: "qué artefactos ya existen"), necesaria para que flujos posteriores puedan reanudar/continuar trabajo — capacidad que se añade cuando tenga un consumidor real (`flow_base`, T-015), no antes.
- `ClientContext` es consumida por `flow_base` mediante la firma canónica `Flow.run(ctx: ClientContext)` sin que `flow_base` tenga que conocer la estructura interna de `clients/<NAME>/`.

## Alcance Total
**In scope (toda la feature, a través de sus bandas):**
- Validación de existencia de un cliente dado (`clients_root/<name>/client.yaml`).
- Resolución de rutas de `010_inputs/`, `020_outputs/`, `data/bronze`, `data/silver`, `data/gold`, `models/`.
- Determinación determinista del modo nuevo/recurrente inferida del disco (existencia de `models/latest`).
- Introspección de artefactos existentes por cliente (qué se ha generado ya), para soportar reanudación — en banda posterior, cuando tenga consumidor real.

**Out of scope (nunca, o en otra feature):**
- Creación o modificación de carpetas de cliente (`create_client`, feature `client_scaffold`, CONFORME).
- Validación de contratos de artefactos entre flujos (§8) — responsabilidad de `flow_base` y de cada flujo.
- Ejecución u orquestación de flujos — features posteriores (`flow_base`, T-015, y flujos concretos).
- Resolución de la raíz del proyecto (búsqueda de `pyproject.toml` hacia arriba desde el cwd) — vive en la capa CLI/orquestador, ya construida en `client_new_cli`; el core de `ClientContext` recibe `clients_root` ya resuelto.
- Registro central de clientes / base de datos — el modelo sigue siendo carpeta-por-cliente en disco (§13, D-006).

## Bandas Previstas (eje vertical)
Qué endurece cada banda hacia la estrella polar (crear **solo** las que se necesiten; `D-029`):

| Banda | Qué aporta / endurece |
|---|---|
| `tracer_bullet` | Slice vertical mínimo end-to-end (NC-4): validación de existencia del cliente, rutas resueltas de `010_inputs/020_outputs/data/{bronze,silver,gold}/models`, y determinación de modo nuevo/recurrente inferida de `models/latest`. Introspección de artefactos existentes queda diferida (sin consumidor todavía). |
| `stab_1` *(prevista, no iniciada)* | Introspección de "qué artefactos ya existen" por cliente (soporte a reanudación), cuando `flow_base` la necesite realmente. |

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **por celda** viven en el `spec.md` de cada banda.
1. Dado un `clients_root` y el nombre de un cliente existente, `ClientContext` se construye correctamente y expone las rutas resueltas de sus carpetas (§7).
2. Dado el nombre de un cliente inexistente, `ClientContext` falla con un error claro, sin crear ni modificar nada en el filesystem.
3. `ClientContext` determina el modo `nuevo` o `recurrente` de forma determinista, inferida exclusivamente del disco (`models/latest`), sin necesidad de un flag editable en `client.yaml`.
4. `flow_base` (T-015) puede consumir `ClientContext` mediante `Flow.run(ctx: ClientContext)` sin conocer la estructura interna de `clients/<NAME>/`.
5. En su banda madura, `ClientContext` expone qué artefactos concretos existen ya para un cliente, soportando la reanudación de trabajo (distinta del modo nuevo/recurrente).

## Dependencias
- `client_scaffold` (banda `tracer_bullet`, CONFORME): provee `create_client(name, clients_root) -> Path` en `src/foda/core/scaffold.py`; la estructura de carpetas que crea es la que `ClientContext` debe resolver.
- `client_new_cli` (banda `tracer_bullet`, CONFORME): delegó explícitamente en esta feature la resolución de `ClientContext` y de rutas de cliente existente.
- `700_architecture/system_design.md` §7, §9, §12, §13.
- Es dependencia de `flow_base` (T-015) y, transitivamente, de todos los flujos concretos.

## Relación con Hitos de Producto
- Tercera de las features fundacionales del orden de construcción abajo-hacia-arriba (`client_scaffold → client_context → flow_base → flujos`, `D-016`). Contribuye a la base sobre la que emergerá el hito **MVP** del producto (`D-029`); no es un hito en sí misma.
