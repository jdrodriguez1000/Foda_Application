# Feature Contract — client_new_cli

> Artefacto **a nivel feature** (por encima de las bandas), creado por `feature_definer` en el paso *Definir*.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de iniciar la primera banda** (`D-030`).
> **Una feature tiene un solo `feature_contract`**, aunque recorra varias bandas (`tracer_bullet → stab_n`).

## Estrella Polar
Un operador del harness FODA teclea `foda client new <NAME>` desde cualquier subcarpeta del proyecto y obtiene, de forma predecible, o bien la ruta del cliente recién creado con código de salida 0, o bien un mensaje de error claro con código de salida ≠ 0 — sin tener que conocer ni tocar el core `create_client`.

## Definición de "Terminado" (feature completa)
Condiciones que deben cumplirse para considerar la feature **terminada** (no una banda suelta, sino el total):
- El comando `foda client new <NAME>` existe, es invocable desde la CLI del paquete (`src/foda/cli.py`, `system_design.md` §7/§11) y delega toda la lógica de negocio en `create_client(name, clients_root)` (feature `client_scaffold`, ya CONFORME) — no reimplementa validación ni creación de árbol (NC-2, NC-3).
- La CLI resuelve `clients_root` buscando hacia arriba desde el cwd el marcador `pyproject.toml` de la raíz del proyecto y usa `<raíz>/clients/` (D-C), sin depender de flags, variables de entorno ni de que el usuario esté parado en la raíz.
- En éxito: imprime la ruta creada y termina con código de salida `0`.
- En error (`ValueError` por nombre inválido, `FileExistsError` por cliente duplicado, o falta de marcador de proyecto): imprime un mensaje claro dirigido al operador y termina con código de salida `≠ 0`, sin traza de Python cruda ni comportamiento silencioso.
- La CLI está cubierta por tests propios (invocación, resolución de `clients_root`, traducción de errores, códigos de salida) en cumplimiento de NC-5 — no reutiliza como "cobertura" los tests del core de `client_scaffold`.

## Alcance Total
**In scope (toda la feature, a través de sus bandas):**
- Comando `foda client new <NAME>` en `src/foda/cli.py`.
- Resolución de `clients_root` por búsqueda hacia arriba desde el cwd con marcador `pyproject.toml` (D-C).
- Traducción de éxito/errores del core a salida de consola y código de salida del proceso.
- Tests de la CLI (unitarios y/o de integración, según decida `spec_writer`/`plan_builder`).

**Out of scope (nunca, o en otra feature):**
- Cualquier lógica de negocio nueva de creación de clientes: toda la validación de nombre y creación del árbol de carpetas ya vive en `create_client` (`client_scaffold`, CONFORME) y no se toca ni se duplica aquí.
- Otros subcomandos de `foda client` (p. ej. `foda client list`) — fuera de esta feature.
- Otros comandos de la CLI global (`foda run`, `foda status`, `foda export`) — fuera de esta feature.
- `ClientContext` y resolución de rutas de cliente existente — feature `client_context` (T-014).

## Bandas Previstas (eje vertical)
Qué endurece cada banda hacia la estrella polar (crear **solo** las que se necesiten; `D-029`):

| Banda | Qué aporta / endurece |
|---|---|
| `tracer_bullet` | Slice vertical mínimo end-to-end (NC-4): comando `foda client new <NAME>` funcional, resolución de `clients_root` hacia arriba con marcador `pyproject.toml`, traducción de éxito/errores a consola + código de salida, con tests propios de la CLI. |

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **por celda** viven en el `spec.md` de cada banda.
1. Ejecutar `foda client new <NAME>` con un nombre válido desde cualquier subcarpeta del proyecto crea `clients/<NAME>/` (vía `create_client`) e imprime la ruta creada con código de salida `0`.
2. Ejecutar `foda client new <NAME>` con un nombre inválido o duplicado no crea/modifica nada, imprime un mensaje de error claro y termina con código de salida `≠ 0`.
3. La resolución de `clients_root` funciona correctamente cuando el comando se invoca desde el cwd raíz del proyecto y desde una subcarpeta anidada, siempre localizando el `pyproject.toml` de la raíz real del repo.
4. La CLI tiene tests propios en verde que cubren los tres puntos anteriores (NC-5).

## Dependencias
- `client_scaffold` (banda `tracer_bullet`, CONFORME): provee `create_client(name: str, clients_root: Path) -> Path` en `src/foda/core/scaffold.py`, con contrato de errores `ValueError` / `FileExistsError`.
- `700_architecture/system_design.md` §7 (estructura de carpetas, `src/foda/cli.py`) y §11 (interfaz CLI).

## Relación con Hitos de Producto
- Cierra el hallazgo F-2 de `verification.md` de `client_scaffold` (capa CLI in-scope de la definition pero no construida) y ejecuta la tarea `T-023` de `800_persistence/tasks.md`.
