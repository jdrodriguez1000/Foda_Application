# Plan de Implementación — client_new_cli

> Artefacto de la etapa 3 (`plan_builder`). Traduce la `spec.md` **aprobada** en un plan de
> implementación mínimo (NC-2) y en la lista **ordenada** de casos de test que guiarán el bucle
> TDD (red → green → refactor). **No** contiene código ni tests: solo el *cómo* y el *orden*.
>
> Banda: `tracer_bullet`. Fuentes: `spec.md` (esta celda, GATE humano aprobado),
> `600_features/client_scaffold/tracer_bullet/spec.md` (firma y contrato de errores del core
> CONFORME), `700_architecture/system_design.md` (§7 estructura, §11 CLI),
> `800_persistence/decisions.md` (D-027, D-A/D-B/D-C), `980_guideline/principles.md` (NC-1…NC-6).
>
> **GATE humano al terminar:** este plan y sus casos TDD requieren aprobación del usuario antes de
> invocar `tdd_tester`.

---

## 1. Enfoque técnico

Slice vertical mínimo (NC-4, NC-2): una **capa CLI fina** que cablea el núcleo YA construido y
verificado `create_client(name, clients_root) -> Path` (`src/foda/core/scaffold.py`, CONFORME). La
feature **no añade lógica de negocio**: valida nada del nombre, no crea el árbol del cliente ni el
`client.yaml` — todo eso ya lo hace el core. La CLI solo **resuelve la ubicación**, **delega** y
**traduce** el resultado a consola.

### Módulo a producir — `src/foda/cli.py`
Una única función pública, sin clases ni abstracciones nuevas (NC-2; la abstracción `Flow` **no**
aplica: crear un cliente es bootstrap, no un flujo del pipeline):

```python
def main(argv: list[str] | None = None) -> int: ...
```

Flujo interno de `main` (spec §Comportamiento Esperado):
1. **Parsear** `argv` con `argparse` (DS-CLI-3): comando `client`, subcomando `new`, posicional
   obligatorio `NAME`. Fallo de parseo (falta `NAME`, subcomando desconocido) → `argparse` imprime
   *usage* a `stderr` y termina con **código 2** (su convención; `SystemExit(2)`).
2. **Resolver la raíz del proyecto (D-C):** partir del cwd y subir directorio por directorio
   buscando el primero que contenga `pyproject.toml`; ese directorio es `<raíz>`, y
   `clients_root = <raíz>/clients`. Si se llega a la raíz del filesystem sin encontrarlo →
   mensaje claro a `stderr`, retornar `1`, **sin tocar disco** (DS-CLI-1).
3. **Asegurar `clients_root`:** `clients_root.mkdir(parents=True, exist_ok=True)` (DS-CLI-2,
   idempotente).
4. **Delegar en el core:** `create_client(NAME, clients_root)` — sin reimplementar nada.
5. **Traducir el resultado:**
   - Éxito → imprimir la ruta devuelta por `stdout`; retornar `0`.
   - `ValueError` (nombre inválido) → mensaje legible por `stderr` (sin traceback); retornar `1`.
   - `FileExistsError` (duplicado) → mensaje legible por `stderr` (sin traceback); retornar `1`;
     no modificar el cliente existente.

**Dependencias de librería:** `argparse`, `pathlib`, `sys` — stdlib (R1: Python 3.13+). Cero
dependencias nuevas (DS-CLI-3, D-027). El import de `create_client` es
`from foda.core.scaffold import create_client`.

### Marcador de consola — `pyproject.toml`
Adición **quirúrgica** (NC-3) de la tabla `[project.scripts]` con `foda = "foda.cli:main"`, para que
el comando `foda client new <NAME>` sea invocable como binario. No altera dependencias ni el resto
del archivo.

---

## 2. Archivos afectados

> El código **no** vive en `600_features/`; va en `src/foda/…` y `tests/…`.

| Ruta | Acción | Contenido |
|---|---|---|
| `src/foda/cli.py` | crear | Función pública `main(argv) -> int`: parser `argparse`, resolución de raíz, cableado a `create_client`, traducción a consola. |
| `pyproject.toml` | modificar | Añadir `[project.scripts]` con `foda = "foda.cli:main"` (cambio quirúrgico; sin tocar dependencias). |
| `tests/cli/test_client_new_cli.py` | crear | Suite de tests de la CLI, **independiente** de los del core (CA-09). Invoca `main(argv)` bajo un proyecto temporal (`tmp_path` + `pyproject.toml` marcador + `monkeypatch.chdir`). |

**Notas de infraestructura:**
- El andamiaje de paquete ya existe (`pyproject.toml`, `src/foda/`, `src/foda/core/`, `tests/`): esta
  feature **no** crea esqueleto nuevo, solo el módulo `cli.py`, su test y la línea `[project.scripts]`.
- El core `create_client` está CONFORME y **no se toca** (spec §No-Objetivos): la CLI lo consume tal cual.
- La carpeta `tests/cli/` es nueva; se sigue la convención existente (no hay `__init__.py` en
  `tests/core/` ni `tests/integration/`; `pyproject.toml` usa `pythonpath=["src"]` + `testpaths=["tests"]`).

---

## 3. Orden de trabajo (de lo básico a lo completo)

El bucle TDD consume los casos de la §6 en orden. La secuencia de implementación asociada es:

1. **Tracer bullet — camino feliz mínimo:** `main(["client","new","ABC"])` bajo proyecto temporal
   devuelve `0` y crea `<raíz>/clients/ABC/`, imprimiendo la ruta. Requiere parser mínimo + resolución
   de raíz + `mkdir(clients)` + delegación + traducción de éxito. (Casos 1–3.)
2. **Delegación verificada:** `create_client` invocado exactamente una vez con args correctos. (Caso 4.)
3. **Creación de `clients/` inexistente** (primer cliente). (Caso 5.)
4. **Resolución desde subcarpeta anidada** (raíz real, no cwd). (Caso 6.)
5. **Raíz no encontrada** (sin marcador) → código 1, `stderr`, sin traceback, nada creado (DS-CLI-1). (Caso 7.)
6. **Traducción de errores del core:** `ValueError` (nombre inválido) → código 1. (Caso 8.)
7. **Duplicado:** `FileExistsError` → código 1, cliente existente intacto. (Caso 9.)
8. **Errores de parseo de `argparse`:** falta `NAME` / subcomando desconocido → código 2. (Casos 10–11.)
9. **Contrato de invocabilidad + entrada de consola:** `[project.scripts]` en `pyproject.toml` y
   `main` invocable con `argv` devolviendo `int`. (Caso 12.)
10. **Refactor final** de la suite manteniendo verde.

---

## 4. Dependencias y contratos

- **Consume:** `foda.core.scaffold.create_client(name, clients_root) -> Path` (feature `client_scaffold`,
  CONFORME). Contrato de errores: `ValueError` (nombre inválido) / `FileExistsError` (duplicado). El
  marcador `pyproject.toml` (solo su **existencia**, no su contenido) para localizar `<raíz>` (D-C).
- **Produce:** el módulo `src/foda/cli.py` con `main(argv) -> int`; la entrada de consola
  `[project.scripts] foda = "foda.cli:main"`; el árbol `<raíz>/clients/<NAME>/` en disco (idéntico al
  del core, no lógica nueva) y la garantía de que `<raíz>/clients/` exista (DS-CLI-2).
- **Convención de códigos de salida:** `0` éxito · `1` error semántico (nombre inválido / duplicado /
  raíz no encontrada) · `2` error de parseo de `argparse`.
- **Restricciones respetadas:** R1 (Python 3.13+, solo stdlib aquí), D-027 (sin dependencias nuevas
  además de PyYAML), D-C (no se asume el cwd como raíz).

---

## 5. Tareas (atómicas y trazables)

> Cada tarea es **atómica** y respeta las reglas de partición: **un solo responsable**, **un solo
> entregable**, y **código y test en tareas separadas**. **Estado** inicial `no_implementada`
> (valores: `no_implementada` | `implementada` | `cancelada_suspendida`); el **responsable de cada
> tarea es su único escritor de estado** (`D-021`). Trazabilidad → `CA-xx` de la spec (o andamiaje
> justificado).

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Añadir la tabla `[project.scripts]` con `foda = "foda.cli:main"` a `pyproject.toml` (cambio quirúrgico, sin tocar dependencias). | `pyproject.toml` (`[project.scripts]`) | tdd_coder | no_implementada | CA-10 |
| TSK-02 | Crear `src/foda/cli.py` con el parser `argparse` (`client new <NAME>`) y el esqueleto de `main(argv) -> int`; incluye el comportamiento de código 2 en fallo de parseo. | `cli.py` (parser + firma) | tdd_coder | no_implementada | CA-10 (y casos 10–11) |
| TSK-03 | Implementar en `main` la resolución de la raíz hacia arriba (marcador `pyproject.toml`) y el fallo controlado DS-CLI-1 (código 1, `stderr`, sin tocar disco). | `cli.py` (resolución de raíz) | tdd_coder | no_implementada | CA-04, CA-06 |
| TSK-04 | Implementar el aseguramiento de `clients_root` (`mkdir(parents=True, exist_ok=True)`, DS-CLI-2), la delegación en `create_client` y la traducción de éxito (imprimir ruta, retornar 0). | `cli.py` (delegación + éxito) | tdd_coder | no_implementada | CA-01, CA-02, CA-03, CA-05 |
| TSK-05 | Implementar la traducción de errores del core `ValueError` / `FileExistsError` a mensaje legible en `stderr` (sin traceback) y código 1. | `cli.py` (traducción de errores) | tdd_coder | no_implementada | CA-07, CA-08 |
| TSK-06 | Escribir el test del camino feliz: `main` devuelve 0, crea `<raíz>/clients/ABC/` e imprime la ruta (casos 1–3). | test camino feliz | tdd_tester | no_implementada | CA-01, CA-02 |
| TSK-07 | Escribir el test de delegación: `create_client` invocado 1 vez con `name`/`clients_root` correctos (caso 4). | test delegación | tdd_tester | no_implementada | CA-03 |
| TSK-08 | Escribir el test de creación de `clients/` inexistente (primer cliente, código 0) (caso 5). | test `clients/` inexistente | tdd_tester | no_implementada | CA-05 |
| TSK-09 | Escribir el test de resolución desde subcarpeta anidada (raíz real, no cwd) (caso 6). | test resolución anidada | tdd_tester | no_implementada | CA-04 |
| TSK-10 | Escribir el test de raíz no encontrada → código 1, `stderr`, sin `Traceback`, nada creado (caso 7). | test raíz no encontrada | tdd_tester | no_implementada | CA-06 |
| TSK-11 | Escribir el test de nombre inválido (`ValueError`) → código 1, `stderr` legible, sin `Traceback`, nada creado (caso 8). | test nombre inválido | tdd_tester | no_implementada | CA-07 |
| TSK-12 | Escribir el test de duplicado (`FileExistsError`) → código 1, `stderr` legible, centinela intacto (caso 9). | test duplicado | tdd_tester | no_implementada | CA-08 |
| TSK-13 | Escribir el test de errores de parseo de `argparse`: falta `NAME` y subcomando desconocido → código 2 (casos 10–11). | test parseo argparse | tdd_tester | no_implementada | CA-10 (Casos Límite spec) |
| TSK-14 | Escribir el test del contrato de invocabilidad + entrada de consola: `[project.scripts]` declarado y `main(argv)` devuelve `int` (caso 12). | test invocabilidad / `[project.scripts]` | tdd_tester | no_implementada | CA-10 |
| TSK-15 | Refactor: consolidar/limpiar la suite de la CLI (parametrizar y factorizar el fixture del proyecto temporal) manteniendo todo verde (CA-09). | Refactor (sin cambio de comportamiento) | tdd_refactor | no_implementada | CA-09 |

---

## 6. Casos de test (lista ordenada para el bucle TDD)

Cada caso es una afirmación verificable atómica sobre `main(argv)`, invocada bajo un **proyecto
temporal** (`tmp_path` con un `pyproject.toml` marcador; cwd fijado con `monkeypatch.chdir`). Orden:
fundamental → complejo. Trazabilidad a los `CA-xx` de la spec entre paréntesis. Deben coincidir con
`stages.tdd.cases[]` de `state.json`.

1. `main(["client","new","ABC"])` con el cwd dentro de un proyecto temporal (existe `<raíz>/pyproject.toml`) devuelve el `int` `0`. (CA-01, CA-10)
2. En el camino de éxito, `main(...)` crea el árbol de cliente en `<raíz>/clients/ABC/` (existe `<raíz>/clients/ABC/client.yaml` y las carpetas del scaffold). (CA-01)
3. En el camino de éxito, la salida capturada en `stdout` contiene la ruta de `<raíz>/clients/ABC`. (CA-02)
4. Con `create_client` espiado/monkeypatcheado, `main(["client","new","ABC"])` lo invoca **exactamente una vez** con `name == "ABC"` y `clients_root == <raíz>/clients`. (CA-03)
5. Cuando `<raíz>/clients/` no existe todavía, `main(["client","new","ABC"])` la crea y crea `ABC/` dentro, terminando con código `0` (primer cliente del proyecto). (CA-05)
6. Con el cwd en una subcarpeta anidada (p. ej. `<raíz>/src/foda/`), `main(["client","new","ABC"])` crea el cliente en `<raíz>/clients/ABC/` (raíz real localizada hacia arriba), no relativo al cwd. (CA-04)
7. Con un cwd sin `pyproject.toml` ni en él ni en ancestros, `main(["client","new","ABC"])` devuelve `1`, escribe en `stderr` un mensaje que menciona que no se encontró la raíz del proyecto, la salida no contiene `"Traceback"`, y no se crea ninguna carpeta `clients/` ni de cliente. (CA-06)
8. Para un `NAME` que `create_client` rechaza con `ValueError` (p. ej. `"a b"`, `".."`, `"-x"`), `main(["client","new",NAME])` devuelve `1`, escribe un mensaje legible en `stderr`, la salida no contiene `"Traceback"`, y no se crea ninguna carpeta para ese nombre. (CA-07)
9. Cuando `<raíz>/clients/ABC/` ya existe (con un archivo centinela dentro), `main(["client","new","ABC"])` devuelve `1`, escribe un mensaje legible en `stderr` (sin `"Traceback"`), y el archivo centinela del cliente existente permanece intacto. (CA-08)
10. Ante argumento `NAME` ausente (`main(["client","new"])`), `argparse` imprime *usage* a `stderr` y termina con código `2` (convención de `argparse`, DS-CLI-3). (Casos Límite spec)
11. Ante subcomando desconocido (`main(["client","frobnicate"])`), `argparse` imprime *usage*/error a `stderr` y termina con código `2`. (Casos Límite spec)
12. `pyproject.toml` declara `[project.scripts]` con la entrada `foda = "foda.cli:main"`, y `foda.cli.main` es invocable con una lista `argv` devolviendo un `int` (contrato de invocabilidad del comando). (CA-10)

### Mapa caso → tareas (`TSK-xx`)
Cada caso agrupa su tarea-test y su(s) tarea(s)-código (el bucle corre por caso; las tareas son la
capa de trazabilidad).

| Caso(s) | Tarea-test | Tarea(s)-código |
|---|---|---|
| 1–3 | TSK-06 | TSK-02, TSK-03, TSK-04 |
| 4 | TSK-07 | TSK-04 |
| 5 | TSK-08 | TSK-04 |
| 6 | TSK-09 | TSK-03 |
| 7 | TSK-10 | TSK-03 |
| 8 | TSK-11 | TSK-05 |
| 9 | TSK-12 | TSK-05 |
| 10–11 | TSK-13 | TSK-02 |
| 12 | TSK-14 | TSK-01, TSK-02 |
| (toda la suite) | TSK-15 (refactor) | — |

> Nota de granularidad: los casos 1–3 comparten la misma invocación de `main` y se cubren con uno o
> pocos tests (asserts atómicos sobre código de retorno, disco y `stdout`); se enumeran por
> trazabilidad. El código de producción del tracer (casos 1–3) requiere las tareas TSK-02/03/04 juntas
> para el primer verde. CA-09 ("suite propia en verde") es un criterio **agregado** que se satisface
> con la suite completa (casos 1–12) y su refactor (TSK-15), no con un test aislado.

---

## 7. Estrategia de test

- **Unit / de nivel CLI** en `tests/cli/test_client_new_cli.py`, invocando `main(argv)` **en proceso**
  (sin `subprocess`): rápido y determinista, verificando código de retorno + salida capturada
  (`capsys`) + efectos en disco.
- **Proyecto temporal (fixture):** un `tmp_path` que contiene un `pyproject.toml` marcador; el cwd se
  fija con `monkeypatch.chdir(tmp_path)` (o una subcarpeta anidada para el caso 6). Nunca se toca el
  `clients/` real del repo (DS-3, D-C).
- **Delegación (caso 4):** `monkeypatch`/spy sobre `foda.cli.create_client` (o el símbolo importado en
  `cli.py`) para capturar los argumentos sin ejecutar el core; se comprueba `call_count == 1` y los
  valores de `name` y `clients_root`.
- **Errores del core (casos 8–9):** se ejercen con nombres reales que el core rechaza (`"a b"`, `".."`,
  `"-x"`) y con un cliente pre-creado + archivo centinela; se verifica ausencia de `"Traceback"` en la
  salida (sin traza cruda) y el efecto nulo/intacto en disco.
- **Errores de parseo (casos 10–11):** `argparse` llama `sys.exit(2)`; el test captura `SystemExit` y
  comprueba `code == 2`. (Si la implementación decide envolver el parseo, se ajusta el aserto al mismo
  contrato observable: código 2.)
- **Contrato estático (caso 12):** leer `pyproject.toml` y verificar la clave `[project.scripts].foda ==
  "foda.cli:main"`; e invocar `main(["client","new","ABC"])` comprobando que el retorno es `int`.
- **Fixtures / datos de prueba:** ninguno externo; todo se deriva del `tmp_path` y de los nombres de la
  spec. La integración *end-to-end* (comando `foda` instalado como binario) queda para
  `integration_tester`, no para esta suite.

---

## 8. Notas y riesgos (NC-1 / NC-6)

- **Sin puntos abiertos que bloqueen el GATE:** los cinco puntos de confirmación de la spec
  (DS-CLI-1, DS-CLI-2, DS-CLI-3, códigos de salida `0/1/2`, `[project.scripts]`) fueron **aprobados por
  el humano** junto con la spec. Este plan los implementa sin reabrirlos.
- **Riesgo — parseo de `pyproject.toml` en el caso 12:** leer el TOML requiere `tomllib` (stdlib de
  Python 3.11+, disponible en 3.13; R1). No se añade dependencia. Alternativa mínima si se prefiere:
  comprobar la línea como texto. Se deja a criterio del `tdd_tester`, sin cambiar el contrato observable.
- **Riesgo — filesystem case-insensitive y nombres reservados de Windows:** limitaciones **heredadas
  del core** (spec §Casos Límite); la CLI no añade normalización ni filtrado (No-Objetivos). No afectan
  a los casos enumerados.
- **Riesgo — `create_client` de facto ya crea `clients/`:** la CLI lo crea explícitamente igualmente
  (DS-CLI-2, idempotente) para no depender de un detalle no garantizado del core; ambos `mkdir` son
  compatibles.
- **Alcance de test de esta feature:** solo la CLI (`main`); el core `create_client` ya tiene su propia
  suite verde (feature `client_scaffold`) y no se re-testea aquí.
