# Feature Contract — client_scaffold

> Artefacto **a nivel feature** (por encima de las bandas), normalmente creado por `feature_definer` en el paso *Definir*.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 y es **obligatorio antes de iniciar la primera banda** (`D-030`).
>
> ⚠️ **Retro-ajuste (`D-030` §4).** `client_scaffold` ejecutó su banda `tracer_bullet` (definición, spec y plan aprobados) **antes** de que existiera la convención de `feature_contract`. Este contrato se escribe **retroactivamente** a partir de `tracer_bullet/definition.md` y `tracer_bullet/spec.md` para dejar la feature conforme con `D-030`. Fuentes: `600_features/client_scaffold/tracer_bullet/{definition.md, spec.md}`, `system_design.md` §7/§10/§11, `D-016`.

## Estrella Polar
Dar al operador del harness FODA un comando fiable y seguro (`foda client new <NAME>`) que genere el andamiaje de carpetas de un cliente nuevo bajo `clients/<NAME>/` de forma **predecible, validada y sin sobrescribir**, para que las features fundacionales posteriores (`client_context`, `flow_base`, flujos) tengan una estructura de carpetas garantizada sobre la cual operar.

## Definición de "Terminado" (feature completa)
- Existe una función core reutilizable `create_client(name, clients_root) -> Path` en `src/foda/core/scaffold.py`, testeable de forma aislada, y una capa CLI fina (`foda client new <NAME>`) por encima.
- Un nombre válido crea el árbol completo `clients/<NAME>/`: `client.yaml`, `010_inputs/`, `020_outputs/`, `data/{bronze,silver,gold}/`, `models/`.
- `client.yaml` contiene al menos `name` (idéntico al input) y `created_at` (fecha ISO-8601).
- Un nombre inválido (fuera del patrón seguro) o un cliente ya existente **fallan con error claro sin tocar/sobrescribir el disco**.
- La creación es todo-o-nada sobre el observable `clients/<NAME>/`: validación-primero + limpieza best-effort ante fallo de filesystem.

## Alcance Total
**In scope (toda la feature, a través de sus bandas):**
- Core `create_client(...)` con validación de nombre (patrón seguro), creación del árbol y `client.yaml` mínimo.
- Atomicidad/rollback best-effort ante fallo de filesystem.
- Capa CLI fina `foda client new <NAME>`.
- Endurecimiento controlado de las limitaciones conocidas del `tracer_bullet` en bandas de estabilización.

**Out of scope (nunca, o en otra feature):**
- Lógica de `ClientContext` (nuevo/recurrente, resolución de rutas) → feature `client_context` (T-014).
- Cualquier flujo de negocio (Discovery, Ingestion, …) → features posteriores (tras `flow_base`).
- Subcarpetas por flujo dentro de `010_inputs/`/`020_outputs/` → las crea cada flujo al correr.
- Versionado de modelos dentro de `models/` (`2026-07_v1/`, `latest`) → feature de Modelling.
- Flag `--force` / sobrescritura de cliente existente → trabajo futuro pospuesto.
- Otros subcomandos de `foda client` (`list`, …).

## Bandas Previstas (eje vertical)
Crear **solo** las que se necesiten (`D-029`):

| Banda | Qué aporta / endurece |
|---|---|
| `tracer_bullet` | Slice vertical mínimo end-to-end (NC-4): core `create_client` + CLI fina, validación DS-1 (`^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`), atomicidad DS-2 (validación-primero + limpieza best-effort), `client.yaml` mínimo. **Excepción `D-028`:** el caso de rollback ante fallo de FS se implementa **sin test** en esta banda. |
| `stab_1` *(prevista, no iniciada)* | Endurece limitaciones conocidas del `tracer_bullet`: **test del rollback best-effort** (cierra la excepción `D-028`), y evaluación del manejo de filesystems **case-insensitive** y **nombres reservados de Windows** (`CON`, `PRN`, `NUL`, …). |

## Criterios de Aceptación de la Feature
> Nivel feature. Los criterios **por celda** viven en el `spec.md` de cada banda (`tracer_bullet/spec.md` tiene 11 criterios verificables).
1. `foda client new <NAME>` con nombre válido crea `clients/<NAME>/` con la estructura completa y un `client.yaml` con `name` + `created_at`.
2. Nombre inválido → error claro y **cero** carpetas creadas.
3. Cliente ya existente → error claro y contenido preexistente **intacto**.
4. El core `create_client(...)` es invocable y testeable con un `clients_root` temporal, sin acoplarse al `clients/` real.
5. En su banda madura, el comportamiento de rollback ante fallo de FS está **respaldado por un test** (cierra `D-028`).

## Dependencias
- Ninguna feature previa (primera feature real de la cadena SDD/TDD, `D-016`). Depende solo de la arquitectura ya definida en `system_design.md` §7 (estructura `clients/`) y §10 (capas medallion).
- Es dependencia de `client_context` (T-014) y, transitivamente, de `flow_base` (T-015) y de todos los flujos concretos.

## Relación con Hitos de Producto
- Es la **primera** de las 3 features fundacionales del orden de construcción abajo-hacia-arriba (`client_scaffold → client_context → flow_base → flujos`, `D-016`). Contribuye a la base sobre la que emergerá el hito **MVP** del producto (`D-029`); no es un hito en sí misma.
