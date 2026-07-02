# Definition — client_new_cli

> Artefacto de la etapa 1 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `client_new_cli` (snake_case)
- **Banda:** `tracer_bullet` (D-019; celda = feature × banda)
- **Componente / flujo:** Interfaz CLI (`system_design.md` §7 `src/foda/cli.py`, §11 "Interfaz CLI") sobre la capa de aislamiento multi-tenant `clients/` construida en `client_scaffold`. No añade lógica de negocio: es la capa fina de cableado (comando → core) del comando `foda client new <NAME>`.

## Problema / Necesidad
El núcleo `create_client(name, clients_root) -> Path` (feature `client_scaffold`, banda `tracer_bullet`, **CONFORME**) ya crea el árbol de carpetas de un cliente nuevo de forma validada y testeada, pero **no existe todavía forma de invocarlo desde la línea de comandos**. `system_design.md` §11 define el comando `foda client new ABC` como la interfaz prevista, y la `definition.md` original de `client_scaffold` la listaba in-scope, pero el `spec_verifier` de esa feature dejó constancia (hallazgo F-2) de que la CLI no se construyó y quedó fuera del set de criterios de aceptación de esa banda. Esta feature cierra ese hueco: cablea el comando real sobre el core ya probado, para que un operador humano pueda crear un cliente sin escribir Python.

## Alcance

**In scope:**
- Comando `foda client new <NAME>` en `src/foda/cli.py` que:
  1. Recibe el `<NAME>` que teclea el usuario (argumento posicional).
  2. Resuelve la ubicación real de `clients/` **buscando hacia arriba** desde el directorio de trabajo actual (cwd) hasta encontrar el marcador de la raíz del proyecto (`pyproject.toml`), y usa `<raíz>/clients/` (decisión vinculante **D-C**, ver Riesgos y Supuestos).
  3. Invoca `create_client(name, clients_root)` del core de `client_scaffold` (`src/foda/core/scaffold.py`) — sin reimplementar validación de nombre ni creación de árbol.
  4. Traduce el resultado a consola:
     - **Éxito:** imprime la ruta creada, código de salida `0`.
     - **Error** (`ValueError` por nombre inválido, `FileExistsError` por cliente duplicado): imprime un mensaje claro dirigido al operador, código de salida `≠ 0`.
- Tests de la CLI (**D-B**, vinculante): invocación del comando, resolución de `clients_root` (incluyendo desde una subcarpeta anidada del proyecto), traducción de `ValueError`/`FileExistsError` a mensaje + código de salida, y el camino de éxito (código 0 + ruta impresa). Estos tests son **nuevos** de esta feature; no reutilizan como cobertura los tests unitarios del core de `client_scaffold` (que siguen validando `create_client` de forma aislada).

**Out of scope:**
- Cualquier lógica de negocio de creación de clientes (validación de nombre, árbol de carpetas, `client.yaml`): ya vive en `create_client` (`client_scaffold`, CONFORME) y no se toca ni se duplica.
- Otros subcomandos de `foda client` (p. ej. `foda client list`) — fuera de esta feature.
- Otros comandos de la CLI global (`foda run`, `foda status`, `foda export`, `system_design.md` §11) — fuera de esta feature.
- `ClientContext` y resolución de rutas de cliente existente — feature `client_context` (T-014).
- Framework de CLI concreto (`argparse` vs. `click`/`typer`, etc.) y su configuración fina — se delega a `spec_writer`/`plan_builder` si no está ya fijado en `system_design.md` o `decisions.md`.
- Qué ocurre si `clients/` no existe todavía en la raíz encontrada (crearla vs. fallar) — la **estrategia de descubrimiento** de la raíz (D-C) ya está decidida y es vinculante; este matiz puntual se deja como punto de confirmación para el GATE de `spec_writer` (ver Riesgos y Supuestos), no se re-abre la decisión de descubrimiento en sí.

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como **operador del harness FODA**, quiero ejecutar `foda client new <NAME>` desde la línea de comandos, para crear un cliente nuevo sin tener que invocar Python directamente. | Ejecutar el comando con un `<NAME>` válido crea `clients/<NAME>/` (vía `create_client`) e imprime la ruta creada; el proceso termina con código de salida `0`. |
| HU-02 | Como **operador**, quiero poder ejecutar el comando desde cualquier subcarpeta del proyecto, para no tener que recordar ni navegar manualmente hasta la raíz del repo antes de crear un cliente. | Invocado desde un cwd distinto a la raíz del proyecto (p. ej. una subcarpeta de `clients/` o `src/`), el comando localiza correctamente `<raíz>/clients/` mediante la búsqueda hacia arriba del marcador `pyproject.toml` (D-C) y crea el cliente en esa ubicación real, no en una relativa al cwd. |
| HU-03 | Como **operador**, quiero recibir un mensaje de error claro (sin traza de Python cruda) y un código de salida distinto de cero cuando el nombre es inválido, para saber de inmediato que la operación falló y por qué. | Un `<NAME>` que `create_client` rechaza con `ValueError` produce en consola un mensaje legible (no un traceback) y el proceso termina con código de salida `≠ 0`; no se crea ninguna carpeta. |
| HU-04 | Como **operador**, quiero recibir un mensaje de error claro y un código de salida distinto de cero cuando el cliente ya existe, para no confundir un intento fallido con un éxito silencioso. | Un `<NAME>` que `create_client` rechaza con `FileExistsError` produce en consola un mensaje legible y el proceso termina con código de salida `≠ 0`; el cliente existente no se modifica. |
| HU-05 | Como **desarrollador del harness**, quiero que la CLI tenga sus propios tests (independientes de los del core), para que el cableado comando→core esté verificado por sí mismo y no dependa implícitamente de la cobertura de `client_scaffold` (NC-5). | Existe una suite de tests que ejercita el comando `foda client new` (o su función de entrada) de punta a punta: resolución de `clients_root`, camino de éxito y ambos caminos de error, todos en verde. |

## Dependencias
- **`client_scaffold`** (banda `tracer_bullet`, **CONFORME**): provee `create_client(name: str, clients_root: Path) -> Path` en `src/foda/core/scaffold.py`, con contrato de errores `ValueError` (nombre inválido) / `FileExistsError` (duplicado). Esta feature es puro cableado sobre ese contrato ya estable; no depende de trabajo pendiente de `client_scaffold` (los hallazgos F-1/F-3 de su `verification.md` y el caso 18 diferido por D-032 son ajenos a esta feature).
- `700_architecture/system_design.md` §7 (estructura de carpetas: `src/foda/cli.py` como punto de entrada CLI, `clients/` en la raíz del proyecto) y §11 (contrato de la interfaz CLI: `foda client new ABC`).

## Riesgos y Supuestos
- **Decisión vinculante D-A (proceso):** esta feature recorre la cadena SDD/TDD completa con sus GATES humanos (`spec_writer`, `plan_builder`), igual que cualquier otra feature — no se trata como "solo cableado sin proceso" pese a su tamaño pequeño.
- **Decisión vinculante D-B (tests):** pese a que la `spec.md` de `client_scaffold` había declarado los tests de CLI como No-Objetivo de esa banda, NC-5 ("toda tarea tiene un test que la respalda... sin excepción") es una norma vinculante que prevalece. Esta feature **sí** lleva tests propios de la CLI (invocación, resolución de `clients_root`, códigos de salida 0/≠0, traducción de errores a mensaje de consola).
- **Decisión vinculante D-C (resolución de `clients_root`):** la CLI resuelve la carpeta `clients/` **buscando hacia arriba** desde el cwd, subiendo directorio por directorio hasta encontrar uno que contenga `pyproject.toml` (el marcador de la raíz del proyecto), y usa `<esa_raíz>/clients/`. No se implementa por flag, variable de entorno, ni asumiendo que el cwd ya es la raíz. Esta estrategia de descubrimiento es un dato de entrada para `spec_writer`, no una decisión a re-abrir.
- **Supuesto (punto de confirmación para el GATE):** si la búsqueda hacia arriba llega a la raíz del sistema de archivos sin encontrar `pyproject.toml`, el comando debe fallar con un mensaje claro y código de salida `≠ 0` (análogo a HU-03/HU-04). `spec_writer` debe formalizar este caso límite explícitamente como criterio de aceptación.
- **Supuesto (punto de confirmación para el GATE):** si `<raíz>/clients/` no existe todavía como carpeta (primer cliente del proyecto), la CLI debe crearla de forma transparente antes de invocar `create_client` (ya que `create_client` documenta que `clients_root` "debe existir o ser creable por el proceso" según `spec.md` de `client_scaffold`, pero no especifica quién la crea). Queda a `spec_writer` decidir si la CLI la crea explícitamente (`clients_root.mkdir(parents=True, exist_ok=True)`) o si delega esa responsabilidad en `create_client` — este último punto **no** está resuelto por D-C y no debe asumirse en silencio (NC-6).
- **Supuesto:** el framework de CLI concreto (stdlib `argparse` u otro) no está fijado por `system_design.md`; se asume la opción más simple compatible con NC-2 salvo que `spec_writer`/`plan_builder` decidan lo contrario.
- **Riesgo:** si en el futuro `client_scaffold` cambia la firma o el contrato de errores de `create_client`, esta CLI debe actualizarse en consecuencia; no hay hoy ninguna capa de abstracción intermedia (por diseño, NC-2).
