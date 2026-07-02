# Definition — client_scaffold

> Artefacto de la etapa 1 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas** (`HU-xx`). No describe el *cómo*.
>
> **Nota de retro-ajuste (`D-031`):** las historias de usuario `HU-xx` se añadieron retroactivamente al adoptar la trazabilidad codificada; se derivan de los criterios de aceptación originales de esta definición.

## Feature
- **Nombre:** `client_scaffold` (snake_case)
- **Banda:** `tracer_bullet` (D-019; celda = feature × banda)
- **Componente / flujo:** Capa de aislamiento multi-tenant `clients/` de `system_design.md` §7 (`src/foda/core/`). No pertenece a un flujo de negocio (Discovery, Ingestion, …) sino a la infraestructura base que todos los flujos usarán para ubicar los datos de un cliente. Es la **primera** de las 3 features fundacionales del orden de construcción abajo-hacia-arriba acordado en D-016 (`client_scaffold` → `client_context` → `flow_base` → flujos concretos).

## Problema / Necesidad
Hoy no existe forma automatizada de crear el árbol de carpetas de un cliente nuevo bajo `clients/<NAME>/`. Un operador del harness FODA necesita un comando de CLI (`foda client new <NAME>`) que genere ese andamiaje de forma predecible y segura, para que las features posteriores (`client_context`, `flow_base`, flujos concretos) tengan una estructura de carpetas garantizada sobre la cual operar.

## Alcance

**In scope:**
- Función core reutilizable `create_client(name: str, ...)` en `src/foda/core/` que crea el árbol de carpetas de un cliente nuevo bajo `clients/<NAME>/`:
  - `client.yaml` — identidad y configuración mínima del cliente (al menos: nombre y fecha de creación).
  - `010_inputs/`
  - `020_outputs/`
  - `data/` con subcarpetas `bronze/`, `silver/`, `gold/` (capas medallion vacías; ver `system_design.md` §10).
  - `models/` (carpeta vacía; el versionado de modelos —p. ej. `2026-07_v1/`, `latest`— es responsabilidad de una feature futura de Modelling, no de esta).
- Validación del nombre del cliente contra un patrón seguro: alfanumérico + `_`/`-` únicamente. Sin normalización automática (no se transforma el input; si no cumple el patrón, se rechaza con error claro), para que el nombre de carpeta resultante sea predecible.
- Falla con error claro si el cliente ya existe (`clients/<NAME>/` ya presente). **No hay flag `--force`** en esta primera versión: no se sobrescribe bajo ninguna circunstancia.
- Capa de CLI fina sobre el core: comando `foda client new <NAME>` (ver `system_design.md` §11) que invoca `create_client(...)` y traduce su resultado/errores a salida de consola.
- Los tests (unitarios, etapa TDD) atacan el **core** (`create_client`), no la capa CLI.

**Out of scope:**
- Lógica de `ClientContext` (resolución de rutas de cliente existente, detección de cliente nuevo/recurrente) — será la feature `client_context` (T-014).
- Cualquier flujo de negocio (Discovery, Ingestion, etc.) y su lógica — serán features posteriores (T-015 en adelante), tras `flow_base`.
- Sub-carpetas por flujo dentro de `010_inputs/` y `020_outputs/` (p. ej. `010_inputs/010_discovery/`) — las crea cada flujo al correr, no el scaffold del cliente.
- Versionado de modelos dentro de `models/` (p. ej. `2026-07_v1/`, puntero `latest`) — corresponde a la feature de Modelling.
- Flag `--force` / sobrescritura de un cliente existente — trabajo futuro explícitamente pospuesto.
- Comando `foda client list` u otros subcomandos de `foda client` — fuera de esta feature.

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** para trazabilidad end-to-end (`definition → spec → plan`). La spec enlaza cada `CA-xx` a una `HU-xx`.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como **operador del harness FODA**, quiero crear el andamiaje de carpetas de un cliente nuevo con un solo comando (`foda client new <NAME>`), para disponer de una estructura predecible sobre la cual operen los flujos posteriores. | Un nombre válido crea `clients/<NAME>/` con la estructura completa: `client.yaml`, `010_inputs/`, `020_outputs/`, `data/{bronze,silver,gold}/`, `models/`. |
| HU-02 | Como **operador**, quiero que el cliente se cree con una identidad mínima, para saber a qué cliente y desde cuándo corresponde la carpeta. | `client.yaml` contiene al menos el nombre del cliente y la fecha de creación. |
| HU-03 | Como **operador**, quiero que un nombre de cliente inválido sea rechazado con un error claro y sin crear nada, para que los nombres de carpeta sean seguros y predecibles. | Un nombre que no cumple el patrón seguro (alfanumérico + `_`/`-`) falla con mensaje claro y **no crea ninguna carpeta**. |
| HU-04 | Como **operador**, quiero que no se sobrescriba un cliente existente, para no perder datos por accidente. | Un nombre de cliente que ya existe falla con mensaje claro y **no modifica/sobrescribe** lo existente. |
| HU-05 | Como **desarrollador de las features posteriores** (`client_context`, flujos), quiero una función core `create_client(...)` reutilizable y testeable de forma aislada, para construir sobre ella sin acoplarme a la CLI. | `create_client(...)` es invocable y testeable de forma independiente de la CLI; los tests unitarios cubren creación exitosa, nombre inválido y cliente duplicado. |

## Dependencias
- Ninguna feature previa (es la primera feature real construida con la cadena SDD/TDD; ver D-016). Depende únicamente de la arquitectura ya definida en `system_design.md` §7 (estructura de `clients/`) y §10 (capas medallion).
- Es dependencia de `client_context` (T-014) y transitivamente de `flow_base` (T-015) y de todos los flujos concretos.

## Riesgos y Supuestos
- **Supuesto:** el patrón "seguro" para el nombre de cliente se interpreta como alfanumérico + `_`/`-` (según D-016), sin exigir mayúsculas/minúsculas específicas ni longitud mínima/máxima; `spec_writer` deberá formalizar el patrón exacto (regex) si se requiere mayor precisión.
- **Supuesto:** `client.yaml` en esta primera versión (banda `tracer_bullet`) solo requiere identidad mínima (nombre + fecha de creación); campos adicionales de configuración quedan abiertos a features futuras.
- **Riesgo:** si el proceso de creación falla a mitad de camino (p. ej. error de filesystem tras crear `010_inputs/` pero antes de `data/`), puede quedar un cliente parcialmente creado. Esta feature no define explícitamente una estrategia de rollback/atomicidad; `spec_writer` debe decidir si es necesaria para el criterio de aceptación 3/4 (no dejar carpetas huérfanas) o si se documenta como limitación conocida.
- **Riesgo:** la ubicación exacta de `create_client(...)` dentro de `src/foda/core/` (nombre de módulo/archivo) no está fijada aquí; queda para `spec_writer`/`plan_builder`.
