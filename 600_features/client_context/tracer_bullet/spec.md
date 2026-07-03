# Spec — client_context

> Artefacto de la etapa 2 (`spec_writer`). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables **codificados (`CA-xx`) y enlazados a las historias de usuario (`HU-xx`)** de `definition.md`. **Requiere aprobación humana** (gate) antes de planear.
>
> Banda: `tracer_bullet`. Fuentes canónicas: `600_features/client_context/tracer_bullet/definition.md`, `600_features/client_context/feature_contract.md`, `600_features/client_scaffold/tracer_bullet/spec.md` (contrato de errores del core y patrón `clients_root`), `700_architecture/system_design.md` (§7, §9, §12, §13), `800_persistence/decisions.md` (D-011, D-016, D-031).

## Resumen
Abstracción de **solo lectura** `ClientContext(name, clients_root)` (en `src/foda/core/context.py`) que, dado un cliente **ya creado** bajo `clients_root/<name>/`, valida su existencia, resuelve de forma determinista las rutas de sus carpetas (§7) y determina el modo **nuevo vs. recurrente** inferido del disco (`models/latest`), sin crear ni modificar nada en el filesystem.

---

## Decisiones formalizadas por spec_writer

La `definition.md` delegó explícitamente tres puntos de confirmación a esta etapa (dos supuestos del GATE + la forma de construir el contexto). Se resuelven así (razonamiento en cada punto, NC-1/NC-2/NC-6). Todos quedan listados abajo como **puntos del GATE humano**; no se asumen en silencio.

### DS-CTX-1 — Tipo de excepción para "cliente inexistente"
- **Decisión:** `FileNotFoundError` (excepción estándar de Python). Se lanza cuando `clients_root/<name>/client.yaml` **no existe** (incluye el caso de que ni siquiera exista la carpeta `clients_root/<name>/`).
- **Razón:**
  - Es el **contrapunto simétrico** de `FileExistsError`, que `create_client` ya usa para el cliente duplicado; `ClientContext` es la contraparte de LECTURA de `create_client`, y la ausencia de un recurso en disco (el `client.yaml` que marca la identidad del cliente, §13) es exactamente lo que `FileNotFoundError` modela.
  - Mantiene el **contrato de errores del core** basado en excepciones estándar de Python (`create_client` usa `ValueError` / `FileExistsError`); no se introduce una excepción propia `ClientNotFoundError` porque hoy **no hay consumidor** que necesite distinguirla del resto de `FileNotFoundError` (NC-2: no se construye superficie sin consumidor). `flow_base` (T-015) podrá promoverla a una excepción propia si en su momento lo requiere.
- **Alternativa descartada (NC-2):** `ValueError`. Descartada porque `ValueError` señala un *valor de argumento inválido* (uso que `create_client` reserva para el nombre malformado); aquí el argumento `name` puede ser perfectamente válido y aun así el cliente no existir en disco. `FileNotFoundError` es semánticamente más preciso y testeable con `pytest.raises(FileNotFoundError)`.

### DS-CTX-2 — Forma de exponer el modo nuevo/recurrente
- **Decisión:** una **propiedad booleana de solo lectura `is_recurring: bool`**. `True` ⇒ RECURRENTE; `False` ⇒ NUEVO. La determinación es `is_recurring == (clients_root/<name>/models/latest).exists()` (D-1 de la `definition.md`, §12, R9, D-011).
- **Razón:** es la superficie mínima que responde la pregunta de §12 ("¿pipeline nuevo o pipeline recurrente?"). No se introduce un `enum ClientMode` ni un método `get_mode()` porque añadirían abstracción y vocabulario sin un segundo estado que justifique un tipo enumerado (NC-2: simplicidad primero, sin abstracciones no solicitadas). El nombre `is_recurring` deja explícito el sentido del booleano (evita la ambigüedad de un `is_new`/`mode` sin polaridad clara).
- **Nota sobre `models/latest`:** la existencia se evalúa con `Path.exists()` sobre la entrada `models/latest` (sea carpeta, archivo o symlink resuelto). En la banda `tracer_bullet` los tests materializan `models/latest` como una carpeta bajo `tmp_path` (portable en Windows, sin depender de symlinks). Riesgo documentado en la `definition.md`: si la convención `models/latest` cambia (D-011), esta detección deberá actualizarse; hoy no se añade capa de abstracción intermedia sobre esa convención.

### DS-CTX-3 — Construcción del `ClientContext` y exposición de rutas
- **Decisión:** **constructor directo** `ClientContext(name: str, clients_root: Path)`. La validación de existencia ocurre **en el `__init__`**: si `clients_root/<name>/client.yaml` no existe, el constructor lanza `FileNotFoundError` (DS-CTX-1) **antes** de exponer un objeto (no existe un `ClientContext` "inválido"). Las rutas se exponen como **propiedades de solo lectura** que devuelven `Path`.
- **Superficie pública (mínima, NC-2):**
  - `name: str` — identidad del cliente (el valor recibido en el constructor; **no** se parsea `client.yaml`).
  - `root: Path` — la carpeta del cliente, `clients_root/<name>`.
  - `inputs_dir: Path` — `root/010_inputs`.
  - `outputs_dir: Path` — `root/020_outputs`.
  - `bronze_dir: Path` — `root/data/bronze`.
  - `silver_dir: Path` — `root/data/silver`.
  - `gold_dir: Path` — `root/data/gold`.
  - `models_dir: Path` — `root/models`.
  - `is_recurring: bool` — modo del cliente (DS-CTX-2).
- **Razón:**
  - El constructor con validación en `__init__` es el patrón más simple y hace imposible construir un contexto para un cliente inexistente (falla temprano, mensaje claro), coherente con la Estrella Polar ("respuesta fiable resuelta desde el disco").
  - `clients_root` es **parámetro explícito y requerido** (D-2 de la `definition.md`; mismo patrón que `create_client(name, clients_root)`): el core **no** re-resuelve `pyproject.toml` hacia arriba desde el cwd (eso vive en la capa CLI/orquestador, `client_new_cli`, NC-3). Esto mantiene el core puro y testeable con `tmp_path`, sin efectos del cwd (HU-04).
  - Las rutas son **derivadas deterministas** de `root`; se **resuelven** (se calculan) siempre, y para un cliente creado por `create_client` **existen** en disco. `ClientContext` valida la existencia del **cliente** (vía `client.yaml`), no la de cada subcarpeta individual (que `create_client` garantiza). No se añade introspección de "qué artefactos existen" (D-3 de la `definition.md`: diferida a banda posterior, sin consumidor todavía).
- **Alternativa descartada (NC-2):** una *factory* `ClientContext.load(name, clients_root)` o `resolve_client(...)`. Descartada por no aportar nada sobre el constructor directo en esta banda (una sola forma de construcción); añadir dos caminos sería superficie innecesaria.

---

## Contratos de Datos / Artefactos

| Dirección | Artefacto | Formato | Esquema / campos |
|---|---|---|---|
| requiere | `clients_root/<name>/client.yaml` | archivo (marcador) | Su **existencia** es el criterio de identidad del cliente (§13). Su **contenido no se parsea** en esta banda: solo se comprueba que el archivo exista. |
| requiere | `clients_root/<name>/models/latest` | entrada de filesystem (carpeta / symlink) | Su **existencia** determina el modo recurrente (D-1, §12, D-011). No se lee su contenido. |
| requiere | árbol del cliente (`010_inputs/`, `020_outputs/`, `data/{bronze,silver,gold}/`, `models/`) | filesystem | Estructura creada por `create_client` (`client_scaffold`, CONFORME); `ClientContext` la **resuelve**, no la crea. |
| produce | `src/foda/core/context.py` | módulo Python | Expone la clase pública `ClientContext` (constructor + propiedades de solo lectura). No escribe nada en el filesystem del cliente. |

> `ClientContext` es una abstracción de **solo lectura**: no crea, no modifica y no borra ninguna carpeta ni archivo bajo `clients_root/`. No modifica `pyproject.toml` ni la CLI (NC-3).

---

## Comportamiento Esperado

Construcción `ClientContext(name, clients_root)`:

1. **Resolver `root`** = `clients_root / name` (derivación pura de rutas; sin tocar disco todavía).
2. **Validar existencia del cliente:** comprobar que `root / "client.yaml"` **existe** como archivo. Si no existe (porque no existe la carpeta `root`, o existe pero sin `client.yaml`) → lanzar `FileNotFoundError` con un mensaje claro que indique el `name` y la ruta esperada. **No se crea ni modifica nada en el filesystem** (DS-CTX-1, HU-01).
3. **Exponer las rutas resueltas** (propiedades de solo lectura) según §7: `inputs_dir`, `outputs_dir`, `bronze_dir`, `silver_dir`, `gold_dir`, `models_dir`, más `root` y `name` (HU-02). Las rutas se calculan de forma determinista a partir de `root`; su valor no depende del cwd (HU-04).
4. **Determinar el modo** al consultar `is_recurring`: `True` si `models_dir / "latest"` existe, `False` en caso contrario. La determinación es **función pura del disco**; **no** se lee ningún flag de `client.yaml` (DS-CTX-2, D-1, HU-03).

Notas de comportamiento:
- El constructor no realiza escritura alguna en disco en ningún camino (éxito o error).
- `name` es el valor literal recibido; `ClientContext` **no** parsea `client.yaml` para obtenerlo ni valida el patrón del nombre (esa validación es responsabilidad de `create_client` en la creación; aquí el cliente ya existe).

---

## Casos Límite y Errores

| Caso | Contexto | Resultado esperado |
|---|---|---|
| Cliente inexistente | `clients_root/<name>/` no existe | `FileNotFoundError`; nada creado ni modificado. |
| Carpeta sin `client.yaml` | `clients_root/<name>/` existe pero **sin** `client.yaml` | `FileNotFoundError` (el marcador es `client.yaml`, no la carpeta); nada modificado. |
| Cliente válido, sin modelo | existe `client.yaml`, **no** existe `models/latest` (aunque `models/` esté vacía o tenga versiones sin puntero) | Construcción OK; `is_recurring == False` (NUEVO). |
| Cliente válido, con modelo vigente | existe `client.yaml` y existe `models/latest` | Construcción OK; `is_recurring == True` (RECURRENTE). |
| Flag espurio en `client.yaml` | `client.yaml` contiene un supuesto campo `mode`/`recurring`, pero **no** existe `models/latest` | `is_recurring == False`: el modo se infiere solo del disco, ignorando cualquier flag del YAML (D-1). |
| Rutas de un cliente recién creado | cliente creado por `create_client` | Las 6 propiedades de ruta apuntan exactamente a las ubicaciones §7 y **existen** en disco. |
| `clients_root` con cwd distinto | construcción bajo `tmp_path` con el cwd cambiado a otra carpeta | Las rutas resueltas dependen solo de `clients_root` (parámetro), no del cwd. |

**Limitaciones conocidas (banda `tracer_bullet`, documentadas):**
- **`models/latest` como symlink:** `Path.exists()` sigue symlinks; un `latest` que sea un symlink **roto** se evaluaría como inexistente (⇒ NUEVO). En esta banda los tests materializan `latest` como carpeta real; el manejo fino de symlinks rotos se difiere (no hay consumidor que lo requiera).
- **Filesystems case-insensitive (Windows/macOS):** la comprobación de existencia delega en la semántica del filesystem (hereda la limitación documentada en `client_scaffold`); no se añade normalización de mayúsculas.
- **Introspección de artefactos (§9):** "qué artefactos concretos ya existen" queda fuera de esta banda (D-3); solo se resuelven rutas y modo.

---

## Interfaces / Firmas Públicas

```python
# src/foda/core/context.py
from pathlib import Path


class ClientContext:
    """Contexto de LECTURA de un cliente ya creado bajo clients_root/<name>/.

    Valida la existencia del cliente (clients_root/<name>/client.yaml),
    resuelve de forma determinista las rutas de sus carpetas (system_design §7)
    y determina el modo nuevo/recurrente inferido del disco (models/latest, §12).
    No crea ni modifica nada en el filesystem.
    """

    def __init__(self, name: str, clients_root: Path) -> None:
        """Construye el contexto de un cliente existente.

        Lanza FileNotFoundError si clients_root/<name>/client.yaml no existe
        (cliente inexistente); en ese caso no toca el filesystem.
        clients_root se recibe ya resuelto (no se busca pyproject.toml).
        """

    # --- Identidad y rutas resueltas (§7) ---
    name: str                 # nombre del cliente (valor recibido)
    root: Path                # clients_root/<name>
    inputs_dir: Path          # root/010_inputs
    outputs_dir: Path         # root/020_outputs
    bronze_dir: Path          # root/data/bronze
    silver_dir: Path          # root/data/silver
    gold_dir: Path            # root/data/gold
    models_dir: Path          # root/models

    # --- Modo (§12) ---
    @property
    def is_recurring(self) -> bool:
        """True si existe models/latest (RECURRENTE); False si no (NUEVO).
        Función pura del disco; no lee ningún flag de client.yaml.
        """
```

- **Contrato de errores:** `FileNotFoundError` (cliente inexistente) — excepción estándar, testeable con `pytest.raises`. No se definen excepciones propias en esta banda (NC-2).
- **`root`, `name` y las 6 propiedades de ruta** son de solo lectura (no hay setters ni mutación); las rutas son consistentes con `system_design.md` §7.
- **Testabilidad:** el constructor acepta `clients_root: Path` inyectable, de modo que los tests construyen `ClientContext("ABC", tmp_path/"clients")` sobre un árbol creado por `create_client(...)` bajo `tmp_path`, sin dependencia del cwd del proceso pytest (HU-04).
- **Consumo por `flow_base`:** la firma canónica `Flow.run(ctx: ClientContext)` (§9) recibe una instancia de esta clase; `flow_base` accede a rutas/modo sin conocer la estructura interna de `clients/<NAME>/` (Estrella Polar). Su construcción/uso completo es de T-015, fuera de esta banda.

---

## Criterios de Aceptación (verificables)
> Cada criterio es traducible a uno o más tests unitarios sobre `ClientContext` (construidos sobre un árbol de cliente creado con `create_client(...)` bajo un `tmp_path`) y traza a la(s) `HU-xx` que satisface. Cumple D-031 (trazabilidad codificada HU→CA).

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | Dado un cliente creado con `create_client("ABC", tmp/clients)`, `ClientContext("ABC", tmp/clients)` se construye sin lanzar excepción y expone `name == "ABC"` y `root == tmp/clients/ABC`. | HU-01 |
| CA-02 | Para un `name` cuyo `tmp/clients/<name>/client.yaml` **no existe** (carpeta inexistente), `ClientContext(name, tmp/clients)` lanza `FileNotFoundError`. | HU-01 |
| CA-03 | Tras un intento fallido de construcción (cliente inexistente), el filesystem bajo `tmp/clients` es idéntico al previo a la llamada: no se crea ninguna carpeta ni archivo para ese `name`. | HU-01 |
| CA-04 | Si `tmp/clients/<name>/` existe como carpeta pero **no** contiene `client.yaml`, `ClientContext(name, tmp/clients)` lanza `FileNotFoundError` (el marcador de existencia es `client.yaml`, no la carpeta). | HU-01 |
| CA-05 | Para un cliente existente, `ctx.inputs_dir == tmp/clients/ABC/010_inputs` y `ctx.outputs_dir == tmp/clients/ABC/020_outputs`. | HU-02 |
| CA-06 | Para un cliente existente, `ctx.bronze_dir`, `ctx.silver_dir` y `ctx.gold_dir` son exactamente `tmp/clients/ABC/data/bronze`, `.../data/silver` y `.../data/gold`, respectivamente. | HU-02 |
| CA-07 | Para un cliente existente, `ctx.models_dir == tmp/clients/ABC/models`. | HU-02 |
| CA-08 | Para un cliente creado por `create_client`, las 6 rutas resueltas (`inputs_dir`, `outputs_dir`, `bronze_dir`, `silver_dir`, `gold_dir`, `models_dir`) **existen** en disco (son las carpetas del scaffold §7). | HU-02 |
| CA-09 | Para un cliente existente **sin** `models/latest` (aunque `models/` exista y esté vacía), `ctx.is_recurring == False` (modo NUEVO). | HU-03 |
| CA-10 | Para un cliente existente en el que se ha materializado `tmp/clients/ABC/models/latest` (p. ej. como carpeta), `ctx.is_recurring == True` (modo RECURRENTE). | HU-03 |
| CA-11 | El modo es función pura del disco: con un `client.yaml` que contiene un campo espurio (p. ej. `mode: recurring`) pero **sin** `models/latest`, `ctx.is_recurring == False` (no se lee ningún flag del YAML). | HU-03 |
| CA-12 | La resolución de rutas depende solo de `clients_root` y no del cwd: construido `ClientContext("ABC", tmp/clients)` con el cwd cambiado (`monkeypatch.chdir`) a un directorio no relacionado, `ctx.root` y las 6 rutas siguen apuntando bajo `tmp/clients/ABC` (parámetro), no bajo el cwd. | HU-04 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` queda cubierta por ≥ 1 `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02, CA-03, CA-04 |
| HU-02 | CA-05, CA-06, CA-07, CA-08 |
| HU-03 | CA-09, CA-10, CA-11 |
| HU-04 | CA-12 (y CA-01…CA-11, que se construyen todos con `clients_root` explícito bajo `tmp_path`) |

---

## No-Objetivos
- **Creación o modificación** de carpetas/archivos de cliente — eso es `create_client` (`client_scaffold`, CONFORME); `ClientContext` es de solo lectura (NC-3, no se toca ni se duplica el core existente).
- **Introspección de "qué artefactos concretos ya existen"** por cliente (§9) — diferida (D-3), sin consumidor todavía; se añadirá en `stab_1` cuando `flow_base` la consuma.
- **Resolución de la raíz del proyecto** (búsqueda de `pyproject.toml` hacia arriba desde el cwd) — vive en la capa CLI/orquestador (`client_new_cli`, CONFORME); el core recibe `clients_root` ya resuelto (D-2).
- **Parseo del contenido de `client.yaml`** (más allá de comprobar su existencia) — no requerido en esta banda; el modo se infiere del disco, no del YAML.
- **Validación del patrón del nombre** del cliente — responsabilidad de `create_client` en la creación; aquí el cliente ya existe.
- **Ejecución u orquestación de flujos** (`Flow.run`, secuencias §12) y **validación de contratos de artefactos** (§8) — features posteriores (`flow_base`, T-015, y flujos concretos).
- **Excepción propia** `ClientNotFoundError`, `enum ClientMode` u otras abstracciones no solicitadas (NC-2).
- **Registro central de clientes / base de datos** — el modelo sigue siendo carpeta-por-cliente (§13, D-006).

---

## Puntos de confirmación para el GATE humano
Decisiones tomadas por `spec_writer` (delegadas por la `definition.md`) que el humano valida o ajusta antes de `plan_builder`:
1. **DS-CTX-1 — excepción de cliente inexistente:** ¿se acepta `FileNotFoundError` (estándar, contrapunto simétrico de `FileExistsError` del core) en lugar de una excepción propia `ClientNotFoundError` o de `ValueError`?
2. **DS-CTX-2 — forma del modo:** ¿se acepta la propiedad booleana `is_recurring: bool` (`True` = recurrente, `False` = nuevo), en vez de un `enum ClientMode` o un método (NC-2)?
3. **DS-CTX-3 — API de construcción y rutas:** ¿se acepta el constructor directo `ClientContext(name, clients_root)` con validación en `__init__` (lanza `FileNotFoundError`), `clients_root` requerido, y las rutas expuestas como propiedades de solo lectura `inputs_dir/outputs_dir/bronze_dir/silver_dir/gold_dir/models_dir` (+ `root`, `name`)?
4. **Marcador de existencia:** ¿se acepta que el criterio de "cliente existe" sea la presencia de `client.yaml` (y no solo la de la carpeta `clients_root/<name>/`)? Consecuencia: una carpeta sin `client.yaml` se considera cliente inexistente (CA-04).
5. **Superficie de propiedades:** ¿se acepta exponer también `root` y `name` (identidad/ubicación del cliente, útiles para `flow_base`), o se prefiere limitar la superficie estrictamente a las 6 rutas §7 + `is_recurring`?
