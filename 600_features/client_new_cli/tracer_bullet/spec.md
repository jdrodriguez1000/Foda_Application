# Spec — client_new_cli

> Artefacto de la etapa 2 (`spec_writer`). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables **codificados (`CA-xx`) y enlazados a las historias de usuario (`HU-xx`)** de `definition.md`. **Requiere aprobación humana** (gate) antes de planear.
>
> Banda: `tracer_bullet`. Fuentes canónicas: `600_features/client_new_cli/tracer_bullet/definition.md`, `600_features/client_new_cli/feature_contract.md`, `600_features/client_scaffold/tracer_bullet/spec.md` (DS-3: firma del core y contrato de errores), `700_architecture/system_design.md` (§7, §11), `800_persistence/decisions.md` (D-027, D-A/D-B/D-C).

## Resumen
Capa CLI fina `foda client new <NAME>` que resuelve la raíz del proyecto hacia arriba desde el cwd (marcador `pyproject.toml`), delega la creación del cliente en el core ya CONFORME `create_client(name, clients_root) -> Path`, e traduce el éxito (ruta impresa, código 0) o el error (mensaje claro, código ≠ 0) a la consola.

---

## Decisiones formalizadas por spec_writer

La `definition.md` delegó explícitamente tres puntos de confirmación a esta etapa. Se resuelven así (razonamiento en cada punto, NC-1/NC-6). Todos quedan listados abajo como **puntos del GATE humano**; no se asumen en silencio.

### DS-CLI-1 — Búsqueda de raíz sin marcador (punto de confirmación 1)
- **Decisión:** si la búsqueda hacia arriba desde el cwd llega a la raíz del sistema de archivos **sin** encontrar ningún directorio que contenga `pyproject.toml`, el comando **falla de forma controlada**: imprime a `stderr` un mensaje claro dirigido al operador (p. ej. "No se encontró la raíz del proyecto: no hay 'pyproject.toml' en el directorio actual ni en sus ancestros."), **sin traza de Python cruda**, y el proceso termina con **código de salida `1`** (≠ 0). No se crea ni modifica ninguna carpeta.
- **Razón:** es el mismo patrón de degradación limpia que HU-03/HU-04 (mensaje legible + código ≠ 0 + sin efectos en disco). Es el único modo de fallo propio de la resolución de `clients_root` (D-C) y, sin él, la búsqueda hacia arriba no tendría comportamiento definido en su caso límite. Alternativa descartada (NC-2): asumir el cwd como raíz por defecto — contradice D-C, que prohíbe expresamente asumir que el cwd es la raíz.

### DS-CLI-2 — Quién crea `<raíz>/clients/` (punto de confirmación 2)
- **Decisión:** la **CLI** crea `<raíz>/clients/` de forma explícita e idempotente (`clients_root.mkdir(parents=True, exist_ok=True)`) **antes** de invocar `create_client`, como parte de su responsabilidad de resolver la ubicación real de `clients/`.
- **Razón:** DS-3 de `client_scaffold` asigna explícitamente la **resolución de la ubicación real de `clients/` a la capa CLI, no al core** ("La resolución de la ubicación real de `clients/` es responsabilidad de la capa CLI"). Asegurar que la carpeta resuelta exista es la consecuencia natural de esa responsabilidad y deja el contrato observable independiente de detalles internos del core.
- **Nota sobre el core:** la implementación actual de `create_client` usa `mkdir(parents=True)`, por lo que *de facto* también crearía `clients_root`. Aun así se decide que la **CLI** lo haga explícitamente, para no depender de un detalle de implementación del core (que su `spec.md` no fija: solo dice que `clients_root` "debe existir o ser creable por el proceso") y para que la responsabilidad quede trazable en la capa correcta. La creación explícita en la CLI y el `parents=True` del core son compatibles (ambos idempotentes respecto a la carpeta `clients/`).
- **Alternativa descartada (b):** delegar la creación de `clients/` en `create_client`. Descartada porque acopla el contrato de la CLI a un detalle no garantizado del core y difumina la responsabilidad que DS-3 ya asignó a la CLI.

### DS-CLI-3 — Framework de CLI (punto de confirmación 3)
- **Decisión:** `argparse` de la biblioteca estándar, con subparsers para modelar `foda client new <NAME>`.
- **Razón:** cero dependencias nuevas (el proyecto declara solo `PyYAML` en `pyproject.toml`, D-027), coherente con NC-2 (simplicidad primero) y con el criterio del proyecto de usar solo stdlib + PyYAML. `click`/`typer` añadirían una dependencia externa sin beneficio para el alcance actual (un único subcomando). Consecuencia funcional a documentar: ante argumentos ausentes o subcomando desconocido, `argparse` imprime el *usage* a `stderr` y termina con **código `2`** (su convención propia) — también `≠ 0`, coherente con el contrato de error, aunque no es un caso de HU (ver Casos Límite).

---

## Contratos de Datos / Artefactos

| Dirección | Artefacto | Formato | Esquema / campos |
|---|---|---|---|
| requiere | `src/foda/core/scaffold.py::create_client(name: str, clients_root: Path) -> Path` | función Python | Contrato estable de `client_scaffold` (CONFORME): éxito → `Path` a `clients_root/<name>`; error → `ValueError` (nombre inválido) / `FileExistsError` (duplicado). No se reimplementa ni se toca. |
| requiere | `pyproject.toml` (marcador de raíz) | archivo | Debe existir en la raíz del proyecto; su presencia es el criterio para localizar `<raíz>` mediante la búsqueda hacia arriba (D-C). Su contenido no se parsea para esta feature: solo se usa su existencia como marcador. |
| produce | `src/foda/cli.py` | módulo Python | Expone la función pública `main(argv: list[str] | None = None) -> int` (punto de entrada de la CLI). |
| modifica | `pyproject.toml` | TOML | Añade la tabla `[project.scripts]` con `foda = "foda.cli:main"` para que el comando `foda` sea invocable desde consola. Cambio quirúrgico (NC-3); no altera dependencias ni el resto del archivo. |
| produce | `<raíz>/clients/<NAME>/` (árbol del cliente) | filesystem | Idéntico al que produce `create_client` (no es lógica nueva): `client.yaml` + `010_inputs/`, `020_outputs/`, `data/{bronze,silver,gold}/`, `models/`. La CLI garantiza además que `<raíz>/clients/` exista (DS-CLI-2). |
| produce | salida de consola + código de salida del proceso | stdout / stderr / exit code | Éxito → ruta creada por `stdout`, exit `0`. Error → mensaje claro por `stderr` (sin traceback), exit `≠ 0` (`1` para errores semánticos; `2` para errores de parseo de `argparse`). |

---

## Comportamiento Esperado
`main(argv)` implementa el flujo del comando `foda client new <NAME>`:

1. **Parsear** `argv` con `argparse`: comando `client`, subcomando `new`, argumento posicional obligatorio `NAME`. Si el parseo falla (falta `NAME`, subcomando desconocido), `argparse` imprime *usage* a `stderr` y termina con código `2`.
2. **Resolver la raíz del proyecto (D-C):** partir del cwd y subir directorio por directorio buscando el primero que contenga `pyproject.toml`. Ese directorio es `<raíz>`; se usará `clients_root = <raíz>/clients`.
   - Si la búsqueda llega a la raíz del filesystem sin encontrar `pyproject.toml` → imprimir mensaje claro a `stderr`, retornar `1`, **sin tocar disco** (DS-CLI-1).
3. **Asegurar `clients_root`:** `clients_root.mkdir(parents=True, exist_ok=True)` (DS-CLI-2). Idempotente: no falla si `clients/` ya existe.
4. **Delegar en el core:** invocar `create_client(NAME, clients_root)` — sin reimplementar validación de nombre ni creación del árbol.
5. **Traducir el resultado a consola:**
   - **Éxito:** imprimir la ruta devuelta (`Path` al cliente creado) por `stdout`; retornar `0`.
   - **`ValueError`** (nombre inválido, HU-03): capturar; imprimir mensaje legible por `stderr` (sin traceback); retornar `1`.
   - **`FileExistsError`** (duplicado, HU-04): capturar; imprimir mensaje legible por `stderr` (sin traceback); retornar `1`; no modificar el cliente existente.
6. **Sin decisiones silenciosas:** ningún error se traga sin mensaje; ningún éxito parcial se reporta como éxito.

> El código de retorno de `main` es el que la envoltura del `console_script` propaga como código de salida del proceso.

---

## Casos Límite y Errores
| Caso | Entrada / Contexto | Resultado esperado |
|---|---|---|
| Nombre válido, cwd = raíz | `client new ABC` desde `<raíz>` | Crea `<raíz>/clients/ABC/`; imprime ruta; exit `0`. |
| Nombre válido, cwd = subcarpeta anidada | `client new ABC` desde `<raíz>/src/foda/` | Localiza `<raíz>` hacia arriba; crea `<raíz>/clients/ABC/` (no relativo al cwd); exit `0`. |
| Primer cliente (no existe `clients/`) | `client new ABC` sin `<raíz>/clients/` previo | La CLI crea `<raíz>/clients/` y luego `ABC/`; exit `0`. |
| Sin marcador de proyecto | cwd sin `pyproject.toml` en el cwd ni en ancestros | Mensaje claro a `stderr`; exit `1`; nada creado. |
| Nombre inválido | `client new "a b"`, `client new ".."`, `client new "-x"`, … (los que `create_client` rechaza con `ValueError`) | Mensaje legible a `stderr` (sin traceback); exit `1`; nada creado. |
| Cliente duplicado | `client new ABC` cuando `<raíz>/clients/ABC/` ya existe | `FileExistsError` traducido a mensaje legible a `stderr`; exit `1`; cliente existente intacto. |
| Falta el argumento `NAME` | `client new` (sin nombre) | `argparse` imprime *usage* a `stderr`; exit `2` (convención de `argparse`). |
| Subcomando desconocido | `client frobnicate` | `argparse` imprime *usage*/error a `stderr`; exit `2`. |

**Limitaciones conocidas (heredadas del core, banda `tracer_bullet`):**
- Filesystems case-insensitive (Windows/macOS): `ABC` y `abc` se tratan como el mismo cliente al comprobar duplicado; la CLI no añade normalización (limitación documentada en `client_scaffold`).
- Nombres reservados de Windows (`CON`, `NUL`, …): pasan la validación de nombre pero pueden fallar al crear la carpeta; ese fallo lo maneja el core (no lo filtra la CLI).

---

## Interfaces / Firmas Públicas
```python
# src/foda/cli.py
def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la CLI `foda`.

    Parsea argv (por defecto sys.argv[1:]) y ejecuta el subcomando.
    Para `client new <NAME>`:
      - resuelve la raíz del proyecto (marcador pyproject.toml) hacia arriba
        desde el cwd (D-C) y usa <raíz>/clients como clients_root;
      - asegura que clients_root exista;
      - delega en core.scaffold.create_client(NAME, clients_root);
      - imprime la ruta creada (stdout) en éxito y devuelve 0;
      - traduce ValueError/FileExistsError/raíz-no-encontrada a un mensaje
        claro en stderr y devuelve un código != 0.
    Devuelve el código de salida del proceso.
    """
```
- **Console script:** `pyproject.toml` declara `[project.scripts]` con `foda = "foda.cli:main"`, de modo que `foda client new <NAME>` es invocable desde la terminal del entorno instalado.
- **Contrato de errores de la CLI:** no define excepciones propias (NC-2); consume el contrato `ValueError`/`FileExistsError` del core y lo traduce a `(mensaje en stderr, código de salida)`. La ausencia de marcador de proyecto se traduce igual (mensaje + código `1`).
- **Testabilidad:** `main(argv)` acepta `argv` inyectable y devuelve un `int`, de modo que los tests invocan `main(["client","new","ABC"])` bajo un `tmp_path` (con un `pyproject.toml` de prueba y `monkeypatch.chdir`) y verifican código de retorno + salida capturada + efectos en disco, sin lanzar un subproceso.

---

## Criterios de Aceptación (verificables)
> Cada criterio es traducible a uno o más tests de la CLI (invocando `main(argv)` bajo un proyecto temporal) y traza a la(s) `HU-xx` que satisface. Convención de tests: `tmp_path` contiene un `pyproject.toml` marcador; el cwd se fija con `monkeypatch.chdir`.

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | Con el cwd dentro de un proyecto temporal (existe `<raíz>/pyproject.toml`), `main(["client","new","ABC"])` crea el árbol de cliente en `<raíz>/clients/ABC/` (existe `<raíz>/clients/ABC/client.yaml` y las carpetas del scaffold). | HU-01 |
| CA-02 | En el camino de éxito de CA-01, `main(...)` devuelve `0` y la salida capturada en `stdout` contiene la ruta de `<raíz>/clients/ABC`. | HU-01 |
| CA-03 | La CLI no reimplementa lógica de negocio: con `create_client` espiado/monkeypatcheado, `main(["client","new","ABC"])` lo invoca exactamente una vez con `name == "ABC"` y `clients_root == <raíz>/clients`. | HU-01, HU-05 |
| CA-04 | Con el cwd en una subcarpeta anidada del proyecto (p. ej. `<raíz>/src/foda/`), `main(["client","new","ABC"])` crea el cliente en `<raíz>/clients/ABC/` (la raíz real localizada hacia arriba), no en una ruta relativa al cwd. | HU-02 |
| CA-05 | Cuando `<raíz>/clients/` no existe todavía, `main(["client","new","ABC"])` la crea y crea `ABC/` dentro, terminando con código `0` (primer cliente del proyecto). | HU-02 |
| CA-06 | Invocado con un cwd que no tiene `pyproject.toml` ni en él ni en ningún ancestro, `main(["client","new","ABC"])` devuelve un código `!= 0` (`1`), escribe en `stderr` un mensaje que menciona que no se encontró la raíz del proyecto, la salida no contiene `"Traceback"`, y no se crea ninguna carpeta `clients/` ni de cliente. | HU-02 |
| CA-07 | Para un `NAME` que `create_client` rechaza con `ValueError` (p. ej. `"a b"`, `".."`, `"-x"`), `main(["client","new",NAME])` devuelve `1`, escribe un mensaje legible en `stderr`, la salida no contiene `"Traceback"`, y no se crea ninguna carpeta para ese nombre. | HU-03 |
| CA-08 | Cuando `<raíz>/clients/ABC/` ya existe (con un archivo centinela dentro), `main(["client","new","ABC"])` devuelve `1`, escribe un mensaje legible en `stderr` (sin `"Traceback"`), y el archivo centinela del cliente existente permanece intacto. | HU-04 |
| CA-09 | Existe una suite de tests de la CLI (independiente de los tests del core de `client_scaffold`) que ejercita, todos en verde: el camino de éxito (CA-01/CA-02), la resolución desde subcarpeta (CA-04), la creación de `clients/` inexistente (CA-05), y los tres caminos de error (CA-06, CA-07, CA-08). | HU-05 |
| CA-10 | `pyproject.toml` declara `[project.scripts]` con la entrada `foda = "foda.cli:main"`, y `foda.cli.main` es invocable con una lista `argv` devolviendo un `int` (contrato de invocabilidad del comando). | HU-01, HU-05 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` queda cubierta por ≥ 1 `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02, CA-03, CA-10 |
| HU-02 | CA-04, CA-05, CA-06 |
| HU-03 | CA-07 |
| HU-04 | CA-08 |
| HU-05 | CA-03, CA-09, CA-10 |

---

## No-Objetivos
- Cualquier lógica de negocio de creación de clientes (validación de nombre, árbol de carpetas, `client.yaml`): vive en `create_client` (`client_scaffold`, CONFORME); no se toca ni se duplica.
- Otros subcomandos de `foda client` (`list`, …) y otros comandos globales (`foda run`, `foda status`, `foda export`).
- `ClientContext` y resolución de rutas de cliente existente — feature `client_context` (T-014).
- Flags/variables de entorno para fijar `clients_root`, o suponer que el cwd es la raíz — prohibido por D-C.
- Flag `--force` / sobrescritura de cliente existente.
- Normalización de mayúsculas y filtrado de nombres reservados de Windows (limitaciones conocidas del core).
- Configurabilidad del framework de CLI más allá de `argparse` (NC-2).

---

## Puntos de confirmación para el GATE humano
Decisiones tomadas por `spec_writer` (delegadas por la `definition.md`) que el humano valida o ajusta antes de `plan_builder`:
1. **DS-CLI-1 — raíz no encontrada:** ¿se acepta que, si la búsqueda hacia arriba no halla `pyproject.toml`, la CLI falle con mensaje claro + código `1` (sin tocar disco), en vez de asumir el cwd como raíz? (Coherente con D-C y análogo a HU-03/HU-04.)
2. **DS-CLI-2 — creación de `clients/`:** ¿se acepta que la **CLI** cree `<raíz>/clients/` explícitamente (`mkdir(parents=True, exist_ok=True)`) como parte de su responsabilidad de resolución (DS-3), en lugar de delegarlo en `create_client`?
3. **DS-CLI-3 — framework:** ¿se acepta `argparse` (stdlib, cero dependencias nuevas) para modelar `foda client new <NAME>`, con la consecuencia de que los errores de parseo devuelven código `2`?
4. **Códigos de salida concretos:** ¿se acepta la convención `0` = éxito, `1` = error semántico (nombre inválido / duplicado / raíz no encontrada), `2` = error de parseo de `argparse`? (La `definition.md` solo exige `≠ 0` en error; aquí se concreta para hacerlo testeable.)
5. **Entrada de consola:** ¿se acepta añadir `[project.scripts] foda = "foda.cli:main"` a `pyproject.toml` (cambio quirúrgico) para que el comando sea invocable como binario `foda`?
