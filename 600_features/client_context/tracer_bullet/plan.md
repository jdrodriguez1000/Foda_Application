# Plan de Implementación — client_context

> Artefacto de la etapa 3 (`plan_builder`). Traduce la `spec.md` **aprobada** (GATE humano superado)
> en un plan de implementación mínimo (NC-2) y en la lista **ordenada** de casos de test que guiarán
> el bucle TDD (red → green → refactor). **No** contiene código ni tests: solo el *cómo* y el *orden*.
>
> Banda: `tracer_bullet`. Fuentes: `spec.md` (esta celda, GATE humano aprobado),
> `definition.md` (HU-01…HU-04, decisiones vinculantes D-1/D-2/D-3),
> `src/foda/core/scaffold.py` (`create_client`, CONFORME — provee el fixture del cliente),
> `700_architecture/system_design.md` (§7 estructura, §9 `ClientContext`, §12 nuevo/recurrente,
> §13 multi-tenant), `800_persistence/decisions.md` (D-011, D-016, D-031, D-037),
> `980_guideline/principles.md` (NC-1…NC-6).
>
> **GATE humano al terminar:** este plan y sus casos TDD requieren aprobación del usuario antes de
> invocar `tdd_tester`.

---

## 1. Enfoque técnico

Slice vertical mínimo (NC-4, NC-2): una **abstracción de solo lectura** `ClientContext` que resuelve
y orienta el árbol de un cliente **ya creado** por `create_client` (`src/foda/core/scaffold.py`,
CONFORME). La feature **no crea ni modifica** nada en el filesystem del cliente y **no toca** el core
existente (NC-3): solo lo consume en los tests como fixture para materializar el árbol bajo `tmp_path`.

### Módulo a producir — `src/foda/core/context.py`

Una única clase pública, sin abstracciones nuevas más allá de lo especificado (NC-2). Es la
contraparte de LECTURA de `create_client` y la implementación de la abstracción `ClientContext` que
§9 define para `Flow.run(ctx: ClientContext)` (su consumo por `flow_base`/T-015 queda fuera de esta
banda):

```python
class ClientContext:
    def __init__(self, name: str, clients_root: Path) -> None: ...
    # propiedades de solo lectura:
    name, root, inputs_dir, outputs_dir, bronze_dir, silver_dir, gold_dir, models_dir, is_recurring
```

Flujo interno (spec §Comportamiento Esperado, DS-CTX-1/2/3):

1. **Resolver `root`** = `clients_root / name` (derivación pura de rutas; sin tocar disco).
2. **Validar existencia del cliente en `__init__`:** comprobar que `root / "client.yaml"` **existe**
   como archivo. Si no existe (porque no existe `root`, o existe pero sin `client.yaml`) → lanzar
   `FileNotFoundError` con un mensaje que incluya el `name` y la ruta esperada. **No se crea ni
   modifica nada en el filesystem** en ningún camino (éxito o error) (DS-CTX-1, HU-01). No existe un
   `ClientContext` "inválido": la validación es en el constructor, antes de exponer el objeto.
3. **Exponer las 6 rutas resueltas** (propiedades de solo lectura que devuelven `Path`) según §7:
   `inputs_dir = root/010_inputs`, `outputs_dir = root/020_outputs`, `bronze_dir = root/data/bronze`,
   `silver_dir = root/data/silver`, `gold_dir = root/data/gold`, `models_dir = root/models`; más
   `root` y `name` (identidad/ubicación). Derivación determinista de `root`; su valor no depende del
   cwd (HU-04, DS-CTX-3).
4. **Determinar el modo** al consultar `is_recurring`: `True` si `models_dir / "latest"` existe,
   `False` en caso contrario. Función **pura del disco**; **no** se lee ningún flag de `client.yaml`
   (DS-CTX-2, D-1, HU-03).

**Dependencias de librería:** `pathlib` — stdlib (R1: Python 3.13+). **Cero** dependencias nuevas. No
se parsea `client.yaml` (solo se comprueba su existencia), por lo que `ClientContext` **no** importa
`yaml`.

**La abstracción `Flow`** no se implementa aquí: `ClientContext` es su *insumo* de lectura; `Flow.run`
y la orquestación son de `flow_base` (T-015), fuera de esta banda (spec §No-Objetivos).

---

## 2. Archivos afectados

> El código **no** vive en `600_features/`; va en `src/foda/…` y `tests/…`.

| Ruta | Acción | Contenido |
|---|---|---|
| `src/foda/core/context.py` | crear | Clase pública `ClientContext(name, clients_root)`: validación de existencia en `__init__` (`FileNotFoundError`), 8 propiedades de ruta/identidad y `is_recurring`. Solo lectura; no escribe en disco. |
| `tests/core/test_context.py` | crear | Suite unit de `ClientContext`, que materializa el cliente con `create_client(...)` bajo `tmp_path`. Independiente de la suite de `scaffold`. |

**Notas de infraestructura:**
- El andamiaje ya existe (`pyproject.toml`, `src/foda/core/`, `tests/core/`): esta feature **no** crea
  esqueleto nuevo, solo el módulo `context.py` y su test.
- El core `create_client` está CONFORME y **no se toca** (NC-3, spec §No-Objetivos): los tests lo
  consumen tal cual para preparar el fixture del árbol de cliente.
- `tests/core/` ya existe (convención sin `__init__.py`; `pyproject.toml` usa `pythonpath=["src"]` +
  `testpaths=["tests"]`).

---

## 3. Orden de trabajo (de lo básico a lo completo)

El bucle TDD consume los casos de la §6 en orden. Secuencia de implementación asociada:

1. **Tracer bullet — construcción mínima:** `ClientContext("ABC", tmp/clients)` sobre un cliente
   creado por `create_client` se construye sin excepción y expone `name` y `root`. (Caso 1.)
2. **Rutas resueltas §7:** `inputs_dir`/`outputs_dir`, luego `bronze/silver/gold`, luego `models_dir`,
   y la comprobación de que las 6 existen en disco para un cliente recién creado. (Casos 2–5.)
3. **Modo nuevo/recurrente (función del disco):** `is_recurring == False` sin `models/latest`;
   `== True` con `models/latest` materializado; ignora flags espurios de `client.yaml`. (Casos 6–8.)
4. **Casos límite de existencia:** carpeta inexistente → `FileNotFoundError`; el fallo no toca el
   filesystem; carpeta sin `client.yaml` → `FileNotFoundError`. (Casos 9–11.)
5. **Independencia del cwd:** las rutas dependen solo de `clients_root`, no del cwd
   (`monkeypatch.chdir`). (Caso 12.)
6. **Refactor final** de la suite manteniendo verde.

> Nota (D-037): varios casos parten de un objeto ya construido (el rojo artificial no aporta cuando la
> propiedad es trivial una vez existe la clase); el bucle decidirá "verde directo" caso a caso. Aquí
> solo se enumeran los casos.

---

## 4. Dependencias y contratos

- **Consume (solo en tests, como fixture):** `foda.core.scaffold.create_client(name, clients_root) ->
  Path` (feature `client_scaffold`, CONFORME), que materializa el árbol §7 (`client.yaml`,
  `010_inputs/`, `020_outputs/`, `data/{bronze,silver,gold}/`, `models/`) bajo `tmp_path`.
- **Produce:** el módulo `src/foda/core/context.py` con la clase pública `ClientContext`
  (constructor + propiedades de solo lectura). No produce ningún efecto en el filesystem del cliente.
- **Contrato de errores:** `FileNotFoundError` (cliente inexistente = ausencia de `client.yaml`),
  excepción estándar, testeable con `pytest.raises(FileNotFoundError)` (DS-CTX-1). No se definen
  excepciones propias (`ClientNotFoundError`) ni enums (`ClientMode`) en esta banda (NC-2).
- **Marcador de existencia:** presencia de `client.yaml` (no solo de la carpeta) (DS-CTX-3, CA-04).
- **Modo:** `is_recurring == (root/models/latest).exists()` (DS-CTX-2, D-1); no se lee `client.yaml`.
- **Restricciones respetadas:** R1 (Python 3.13+, solo stdlib), D-2 (`clients_root` recibido ya
  resuelto; el core no busca `pyproject.toml`), D-3 (introspección de artefactos diferida), NC-3
  (no se toca `create_client`).

---

## 5. Tareas (atómicas y trazables)

> Cada tarea es **atómica** y respeta las reglas de partición: **un solo responsable**, **un solo
> entregable**, y **código y test en tareas separadas**. **Estado** inicial `no_implementada`
> (valores: `no_implementada` | `implementada` | `cancelada_suspendida`); el **responsable de cada
> tarea es su único escritor de estado** (`D-021`). Trazabilidad → `CA-xx` de la spec.

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Crear `src/foda/core/context.py` con la clase `ClientContext` y `__init__(name, clients_root)`: resolver `root`, validar existencia de `root/client.yaml` (lanzar `FileNotFoundError` con mensaje claro si falta; sin tocar disco) y exponer `name`/`root`. | `context.py` (esqueleto + validación + `name`/`root`) | tdd_coder | no_implementada | CA-01, CA-02, CA-03, CA-04 |
| TSK-02 | Añadir las 6 propiedades de ruta de solo lectura (`inputs_dir`, `outputs_dir`, `bronze_dir`, `silver_dir`, `gold_dir`, `models_dir`) derivadas de `root` según §7. | `context.py` (propiedades de ruta) | tdd_coder | no_implementada | CA-05, CA-06, CA-07, CA-08, CA-12 |
| TSK-03 | Añadir la propiedad de solo lectura `is_recurring` = `(models_dir/"latest").exists()` (función pura del disco; no lee `client.yaml`). | `context.py` (`is_recurring`) | tdd_coder | no_implementada | CA-09, CA-10, CA-11 |
| TSK-04 | Escribir el test de construcción válida: sobre un cliente creado con `create_client`, `ClientContext("ABC", tmp/clients)` no lanza y expone `name == "ABC"` y `root == tmp/clients/ABC`. | test construcción válida (caso 1) | tdd_tester | no_implementada | CA-01 |
| TSK-05 | Escribir el test de `inputs_dir`/`outputs_dir` correctos (§7). | test rutas inputs/outputs (caso 2) | tdd_tester | no_implementada | CA-05 |
| TSK-06 | Escribir el test de `bronze_dir`/`silver_dir`/`gold_dir` correctos (§7). | test rutas medallion (caso 3) | tdd_tester | no_implementada | CA-06 |
| TSK-07 | Escribir el test de `models_dir` correcto (§7). | test ruta models (caso 4) | tdd_tester | no_implementada | CA-07 |
| TSK-08 | Escribir el test de que las 6 rutas resueltas **existen** en disco para un cliente creado por `create_client`. | test existencia de rutas (caso 5) | tdd_tester | no_implementada | CA-08 |
| TSK-09 | Escribir el test de `is_recurring == False` para un cliente **sin** `models/latest` (aunque `models/` exista y esté vacía). | test modo NUEVO (caso 6) | tdd_tester | no_implementada | CA-09 |
| TSK-10 | Escribir el test de `is_recurring == True` tras materializar `models/latest` (como carpeta) bajo `tmp_path`. | test modo RECURRENTE (caso 7) | tdd_tester | no_implementada | CA-10 |
| TSK-11 | Escribir el test de que un `client.yaml` con flag espurio (`mode: recurring`) pero **sin** `models/latest` da `is_recurring == False` (no se lee el YAML). | test flag espurio ignorado (caso 8) | tdd_tester | no_implementada | CA-11 |
| TSK-12 | Escribir el test de `FileNotFoundError` cuando `tmp/clients/<name>/` no existe (carpeta inexistente). | test cliente inexistente (caso 9) | tdd_tester | no_implementada | CA-02 |
| TSK-13 | Escribir el test de que, tras el intento fallido (cliente inexistente), el filesystem bajo `tmp/clients` queda idéntico (no se crea nada para ese `name`). | test fallo sin efecto en disco (caso 10) | tdd_tester | no_implementada | CA-03 |
| TSK-14 | Escribir el test de `FileNotFoundError` cuando la carpeta existe pero **sin** `client.yaml` (marcador = `client.yaml`, no la carpeta). | test carpeta sin `client.yaml` (caso 11) | tdd_tester | no_implementada | CA-04 |
| TSK-15 | Escribir el test de independencia del cwd: con `monkeypatch.chdir` a un dir no relacionado, `root` y las 6 rutas siguen bajo `tmp/clients/ABC` (parámetro), no bajo el cwd. | test independencia del cwd (caso 12) | tdd_tester | no_implementada | CA-12 |
| TSK-16 | Refactor: consolidar/limpiar la suite (factorizar el fixture del cliente creado con `create_client`; parametrizar rutas) manteniendo todo verde. | Refactor (sin cambio de comportamiento) | tdd_refactor | no_implementada | CA-01…CA-12 |

---

## 6. Casos de test (lista ordenada para el bucle TDD)

Cada caso es una afirmación verificable atómica sobre `ClientContext`, construida sobre un árbol de
cliente materializado con `create_client(...)` bajo un `tmp_path`. Orden: fundamental → complejo.
Trazabilidad a los `CA-xx` de la spec entre paréntesis. Deben coincidir con `stages.tdd.cases[]` de
`state.json`.

1. Sobre un cliente creado con `create_client("ABC", tmp/clients)`, `ClientContext("ABC", tmp/clients)` se construye **sin lanzar** excepción y expone `name == "ABC"` y `root == tmp/clients/ABC`. (CA-01)
2. Para ese cliente, `ctx.inputs_dir == tmp/clients/ABC/010_inputs` y `ctx.outputs_dir == tmp/clients/ABC/020_outputs`. (CA-05)
3. Para ese cliente, `ctx.bronze_dir`, `ctx.silver_dir` y `ctx.gold_dir` son `tmp/clients/ABC/data/bronze`, `.../data/silver` y `.../data/gold`, respectivamente. (CA-06)
4. Para ese cliente, `ctx.models_dir == tmp/clients/ABC/models`. (CA-07)
5. Para un cliente creado por `create_client`, las 6 rutas resueltas (`inputs_dir`, `outputs_dir`, `bronze_dir`, `silver_dir`, `gold_dir`, `models_dir`) **existen** en disco. (CA-08)
6. Para un cliente existente **sin** `models/latest` (aunque `models/` exista y esté vacía), `ctx.is_recurring == False` (modo NUEVO). (CA-09)
7. Tras materializar `tmp/clients/ABC/models/latest` (como carpeta), `ctx.is_recurring == True` (modo RECURRENTE). (CA-10)
8. Con un `client.yaml` que contiene un campo espurio (p. ej. `mode: recurring`) pero **sin** `models/latest`, `ctx.is_recurring == False` (el modo no se lee del YAML). (CA-11)
9. Para un `name` cuyo `tmp/clients/<name>/client.yaml` no existe (carpeta inexistente), `ClientContext(name, tmp/clients)` lanza `FileNotFoundError`. (CA-02)
10. Tras ese intento fallido de construcción, el filesystem bajo `tmp/clients` es idéntico al previo a la llamada: no se crea ninguna carpeta ni archivo para ese `name`. (CA-03)
11. Si `tmp/clients/<name>/` existe como carpeta pero **no** contiene `client.yaml`, `ClientContext(name, tmp/clients)` lanza `FileNotFoundError` (el marcador es `client.yaml`, no la carpeta). (CA-04)
12. Construido `ClientContext("ABC", tmp/clients)` con el cwd cambiado (`monkeypatch.chdir`) a un directorio no relacionado, `ctx.root` y las 6 rutas siguen apuntando bajo `tmp/clients/ABC` (parámetro), no bajo el cwd. (CA-12)

### Mapa caso → tareas (`TSK-xx`)
Cada caso agrupa su tarea-test y su(s) tarea(s)-código (el bucle corre por caso; las tareas son la
capa de trazabilidad).

| Caso | Tarea-test | Tarea(s)-código |
|---|---|---|
| 1 | TSK-04 | TSK-01 |
| 2 | TSK-05 | TSK-02 |
| 3 | TSK-06 | TSK-02 |
| 4 | TSK-07 | TSK-02 |
| 5 | TSK-08 | TSK-02 |
| 6 | TSK-09 | TSK-03 |
| 7 | TSK-10 | TSK-03 |
| 8 | TSK-11 | TSK-03 |
| 9 | TSK-12 | TSK-01 |
| 10 | TSK-13 | TSK-01 |
| 11 | TSK-14 | TSK-01 |
| 12 | TSK-15 | TSK-01, TSK-02 |
| (toda la suite) | TSK-16 (refactor) | — |

---

## 7. Estrategia de test

- **Unit** en `tests/core/test_context.py`, construyendo `ClientContext(...)` en proceso (sin
  `subprocess`): rápido y determinista.
- **Fixture del cliente:** cada test materializa el árbol con `create_client(NAME, tmp_path/"clients")`
  (core CONFORME), y luego construye `ClientContext(NAME, tmp_path/"clients")`. Nunca se toca el
  `clients/` real del repo. El fixture se factoriza en el refactor final (TSK-16).
- **Modo recurrente (caso 7):** se materializa `models/latest` como **carpeta** bajo `tmp_path`
  (portable en Windows, sin depender de symlinks; spec DS-CTX-2).
- **Flag espurio (caso 8):** se reescribe `client.yaml` añadiendo `mode: recurring` (o se crea con ese
  contenido) sin crear `models/latest`; se verifica `is_recurring == False` (el YAML no se lee).
- **Casos de error (9, 11):** `pytest.raises(FileNotFoundError)` con un `name` sin `client.yaml`
  (carpeta ausente, o carpeta presente pero vacía de marcador).
- **Sin efecto en disco (caso 10):** capturar el estado de `tmp/clients` antes de la llamada (p. ej.
  set de rutas con `rglob`) y comprobar que es idéntico tras el `FileNotFoundError`.
- **Independencia del cwd (caso 12):** `monkeypatch.chdir` a otra carpeta (p. ej. `tmp_path/"otro"`)
  antes de construir; asertar que `root` y las 6 rutas siguen bajo `tmp/clients/ABC`.
- **Fixtures / datos de prueba:** ninguno externo; todo se deriva de `tmp_path` y de los nombres de la
  spec. La integración *end-to-end* queda para `integration_tester`, no para esta suite.

---

## 8. Notas y riesgos (NC-1 / NC-6)

- **Sin puntos abiertos que bloqueen el GATE:** los cinco puntos de confirmación de la spec (DS-CTX-1
  excepción `FileNotFoundError`, DS-CTX-2 `is_recurring: bool`, DS-CTX-3 constructor + propiedades,
  marcador `client.yaml`, exposición de `root`/`name`) fueron **aprobados por el humano** junto con la
  spec. Este plan los implementa sin reabrirlos.
- **Riesgo — `models/latest` como symlink roto:** `Path.exists()` sigue symlinks; un `latest` roto se
  evaluaría como inexistente (⇒ NUEVO). En esta banda los tests materializan `latest` como carpeta
  real; el manejo fino de symlinks rotos se difiere (sin consumidor). Limitación heredada/documentada.
- **Riesgo — filesystems case-insensitive (Windows/macOS):** la comprobación de existencia delega en la
  semántica del filesystem (limitación heredada de `client_scaffold`); no se añade normalización.
- **Introspección de artefactos (§9, D-3):** fuera de esta banda; solo se resuelven rutas y modo.
- **Alcance de test de esta feature:** solo `ClientContext`; el core `create_client` ya tiene su suite
  verde (feature `client_scaffold`) y no se re-testea aquí (se usa como fixture, NC-3).
