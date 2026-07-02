# Spec — client_scaffold

> Artefacto de la etapa 2 (`spec_writer`). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables **codificados (`CA-xx`) y enlazados a las historias de usuario (`HU-xx`)** de `definition.md`. **Requiere aprobación humana** (gate) antes de planear.
>
> Banda: `tracer_bullet`. Fuentes canónicas: `600_features/client_scaffold/tracer_bullet/definition.md`, `700_architecture/system_design.md` (§7, §10, §11, §13), `800_persistence/decisions.md` (D-016, D-011, D-019).
>
> **Nota de retro-ajuste (`D-031`):** los códigos `CA-xx`, la columna de trazabilidad → HU y la matriz de cobertura se añadieron retroactivamente al adoptar la trazabilidad codificada. `CA-0n` conserva el número del criterio original (antes citado como `ACn`).

## Resumen
Función core `create_client(name, clients_root)` que crea, de forma atómica y validada, el árbol de carpetas de un cliente nuevo bajo `clients/<NAME>/`, con una capa CLI fina (`foda client new <NAME>`) por encima.

---

## Decisiones formalizadas por spec_writer

La `definition.md` delegó explícitamente tres supuestos a esta etapa. Se resuelven así (razonamiento en cada punto, NC-1):

### DS-1 — Patrón seguro del nombre de cliente (regex exacto)
- **Regex:** `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`
- **Interpretación:**
  - Conjunto permitido: letras ASCII (`A–Z`, `a–z`), dígitos (`0–9`), guion bajo (`_`) y guion medio (`-`).
  - **Primer carácter** debe ser alfanumérico (letra o dígito). Se rechazan nombres que empiezan por `-` (se confunden con flags de CLI) o por `_`.
  - **Longitud:** entre 1 y 64 caracteres inclusive.
  - **Case-sensitive:** no hay normalización; el nombre de carpeta es exactamente el input (definition §Alcance).
  - **Solo ASCII:** `alfanumérico` se restringe a ASCII; se rechazan letras acentuadas (`á`, `ñ`, …) por predictibilidad y portabilidad de nombre de carpeta. *(Punto de confirmación en el GATE, ver más abajo.)*
- **Razón:** un nombre validado antes de tocar disco garantiza que el nombre de carpeta resultante es predecible (definition) y evita rutas peligrosas (`.`, `..`, separadores `/` `\`, espacios), que quedan fuera del conjunto y por tanto se rechazan.

### DS-2 — Atomicidad / rollback
Estrategia **validación-primero + limpieza-en-fallo** (todo-o-nada sobre el path observable `clients/<NAME>/`):
1. **Toda validación ocurre antes de cualquier escritura en disco:** primero se valida el nombre (DS-1); luego se comprueba que `clients/<NAME>/` no exista. Si cualquiera falla, se lanza la excepción correspondiente **sin haber creado nada**. Esto satisface los criterios de "no crea ninguna carpeta" (AC7) y "no sobrescribe" (AC8) sin necesidad de rollback.
2. **Ante un error de filesystem inesperado a mitad de la creación** (p. ej. falla tras crear `010_inputs/` pero antes de `data/`): se captura la excepción, se hace **limpieza best-effort** eliminando el árbol parcialmente creado `clients/<NAME>/`, y se relanza el error. El observable `clients/<NAME>/` no queda como carpeta huérfana parcial.
- **Alternativa considerada y descartada (NC-2):** construir en un directorio temporal y `os.replace()` atómico al destino. Da atomicidad más fuerte pero es innecesariamente compleja para la banda `tracer_bullet`; la validación-primero cubre los casos realistas (nombre inválido / duplicado) sin mutar disco, y la limpieza-en-fallo cubre el error raro de FS.

### DS-3 — Ubicación del módulo core
- **Módulo:** `src/foda/core/scaffold.py` (coherente con `system_design.md` §7: `src/foda/core/` aloja las abstracciones base).
- **Función pública:** `create_client(name: str, clients_root: Path) -> Path`.
- **`clients_root` es parámetro explícito y requerido** (no hay default ni estado global/cwd oculto): mantiene el core puro y totalmente testeable (los tests pasan un `tmp_path`), sin contaminar el `clients/` real del repo. La resolución de la ubicación real de `clients/` es responsabilidad de la capa CLI, no del core.
- **Capa CLI:** `src/foda/cli.py`, comando `foda client new <NAME>` (system_design §11). Resuelve `clients_root` (carpeta `clients/` del proyecto), invoca `create_client(...)` y traduce éxito/errores a salida de consola. Los tests atacan el core, no la CLI (definition §Alcance).

---

## Contratos de Datos / Artefactos

### Entrada (argumentos de `create_client`)
| Nombre | Tipo | Descripción |
|---|---|---|
| `name` | `str` | Nombre del cliente; debe cumplir DS-1. Sin normalización. |
| `clients_root` | `Path` | Directorio raíz bajo el cual se crea `<name>/`. Debe existir o ser creable por el proceso. |

### Salida (árbol producido en disco)
Estructura exacta creada bajo `clients_root/<NAME>/` (alineada con system_design §7 y §10):
```
<NAME>/
├── client.yaml            # archivo
├── 010_inputs/            # carpeta vacía (sin subcarpetas por flujo)
├── 020_outputs/           # carpeta vacía (sin subcarpetas por flujo)
├── data/
│   ├── bronze/            # carpeta vacía (capa medallion 🥉)
│   ├── silver/            # carpeta vacía (capa medallion 🥈)
│   └── gold/              # carpeta vacía (capa medallion 🥇)
└── models/                # carpeta vacía (sin versionado; lo crea Modelling a futuro)
```

### Artefacto `client.yaml`
| Campo | Tipo | Valor |
|---|---|---|
| `name` | `str` | Igual al `name` de entrada (idéntico, sin transformar). |
| `created_at` | `str` | Fecha de creación en formato ISO-8601 `YYYY-MM-DD` (UTC). |

Ejemplo:
```yaml
name: ABC
created_at: 2026-07-02
```
- Debe ser **YAML válido** parseable a un mapa con exactamente esas dos claves en esta primera versión (campos adicionales quedan para features futuras, definition §Supuestos).

### Valor de retorno
`create_client` devuelve el `Path` absoluto/normalizado a la carpeta creada (`clients_root/<NAME>`).

---

## Comportamiento Esperado
1. **Validar el nombre** contra DS-1. Si no cumple → lanzar `ValueError` con mensaje claro que indique el nombre recibido y el patrón esperado. **No se toca el disco.**
2. **Comprobar existencia:** si `clients_root/<NAME>/` ya existe (como carpeta o archivo) → lanzar `FileExistsError` con mensaje claro. **No se modifica ni sobrescribe nada existente.**
3. **Crear el árbol** de carpetas listado arriba bajo `clients_root/<NAME>/` (incluyendo las capas medallion y `models/` vacías).
4. **Escribir `client.yaml`** con `name` (= input) y `created_at` (fecha ISO-8601 de hoy, UTC).
5. **Devolver** el `Path` a la carpeta del cliente creada.
6. **Rollback en fallo (DS-2):** si un error de filesystem ocurre entre los pasos 3–4, eliminar best-effort `clients_root/<NAME>/` y relanzar la excepción original.

---

## Casos Límite y Errores
| Caso | Entrada | Resultado esperado |
|---|---|---|
| Nombre vacío | `""` | `ValueError`; nada creado. |
| Solo espacios | `"   "` | `ValueError`; nada creado. |
| Espacio interior | `"ab c"` | `ValueError`; nada creado. |
| Empieza por guion | `"-abc"` | `ValueError`; nada creado. |
| Empieza por guion bajo | `"_abc"` | `ValueError`; nada creado. |
| Separador de ruta | `"a/b"`, `"a\\b"` | `ValueError`; nada creado. |
| Nombres de ruta especiales | `"."`, `".."` | `ValueError`; nada creado. |
| Punto interior | `"ab.c"` | `ValueError`; nada creado. |
| Carácter no permitido | `"a!b"`, `"a@b"`, `"a b$"` | `ValueError`; nada creado. |
| No-ASCII / acentuado | `"añez"`, `"clienté"` | `ValueError`; nada creado. |
| Longitud > 64 | 65 caracteres válidos | `ValueError`; nada creado. |
| Nombre válido mínimo | `"X"` | Éxito; árbol creado. |
| Empieza por dígito | `"9lives"` | Éxito; árbol creado. |
| Con `_` y `-` | `"Client_1-a"` | Éxito; árbol creado. |
| Cliente duplicado | nombre cuya carpeta ya existe | `FileExistsError`; contenido existente intacto. |

**Limitaciones conocidas (documentadas, banda `tracer_bullet`):**
- **Filesystems case-insensitive (Windows/macOS por defecto):** la comprobación de existencia delega en la semántica del filesystem; `ABC` y `abc` se tratan como el mismo cliente en esos sistemas, aunque el regex los admita como distintos. No se añade normalización de mayúsculas en esta banda.
- **Nombres reservados de Windows** (`CON`, `PRN`, `AUX`, `NUL`, `COM1`…): pasan el regex pero pueden fallar al crear la carpeta; ese fallo se maneja vía DS-2 (limpieza + relanzar). No se filtran explícitamente en esta banda.

---

## Interfaces / Firmas Públicas
```python
# src/foda/core/scaffold.py
def create_client(name: str, clients_root: Path) -> Path:
    """Crea clients_root/<name>/ con el árbol de scaffold y client.yaml.
    Lanza ValueError si name no cumple el patrón seguro (DS-1).
    Lanza FileExistsError si clients_root/<name>/ ya existe.
    Devuelve el Path a la carpeta del cliente creada.
    """
```
- **Contrato de errores:** `ValueError` (nombre inválido) y `FileExistsError` (duplicado) — excepciones estándar de Python, testeables con `pytest.raises`. No se definen excepciones propias en esta banda (NC-2).
- **CLI (contrato de nivel):** `foda client new <NAME>` invoca el core; en éxito informa la ruta creada con código de salida 0; en error traduce la excepción a mensaje de consola y código de salida ≠ 0. (Los tests de esta feature cubren el core, no la CLI.)

---

## Criterios de Aceptación (verificables)
Cada criterio es traducible a uno o más tests unitarios sobre `create_client` (usando un `clients_root` temporal) y traza a la(s) historia(s) de usuario que satisface.

| ID | Criterio de aceptación | Trazabilidad → HU |
|---|---|---|
| CA-01 | `create_client("ABC", tmp)` crea el directorio `tmp/ABC/`. | HU-01 |
| CA-02 | Bajo `tmp/ABC/` existen exactamente estas entradas de primer nivel: archivo `client.yaml` y carpetas `010_inputs/`, `020_outputs/`, `data/`, `models/`. | HU-01 |
| CA-03 | `tmp/ABC/data/` contiene las subcarpetas `bronze/`, `silver/`, `gold/`, y las tres están vacías. | HU-01 |
| CA-04 | `tmp/ABC/models/` existe y está vacía (sin subcarpetas de versión). | HU-01 |
| CA-05 | `tmp/ABC/010_inputs/` y `tmp/ABC/020_outputs/` existen y están vacías (sin subcarpetas por flujo). | HU-01 |
| CA-06 | `tmp/ABC/client.yaml` es YAML válido que parsea a un mapa con clave `name == "ABC"` y clave `created_at` cuyo valor cumple el patrón `^\d{4}-\d{2}-\d{2}$`. | HU-02 |
| CA-07 | `create_client("ABC", tmp)` devuelve un `Path` que apunta a `tmp/ABC` (la carpeta creada). | HU-01, HU-05 |
| CA-08 | Para cada nombre inválido de la tabla de casos límite (`""`, `"-abc"`, `"a/b"`, `".."`, `"a b"`, `"añez"`, nombre de 65 caracteres, …), `create_client(nombre, tmp)` lanza `ValueError` y `tmp` no contiene ninguna carpeta nueva para ese nombre. | HU-03 |
| CA-09 | Para cada nombre válido representativo (`"X"`, `"9lives"`, `"Client_1-a"`), `create_client(...)` crea el árbol completo sin error. | HU-01 |
| CA-10 | Llamar `create_client("ABC", tmp)` cuando `tmp/ABC/` ya existe lanza `FileExistsError` y no modifica ni sobrescribe el contenido preexistente (un archivo centinela previo dentro de `tmp/ABC/` permanece intacto). | HU-04 |
| CA-11 | Toda comprobación (nombre y existencia) ocurre antes de escribir: tras un `ValueError` o un `FileExistsError`, el estado del filesystem para ese nombre es idéntico al previo a la llamada. | HU-03, HU-04 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` queda cubierta por ≥ 1 `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02, CA-03, CA-04, CA-05, CA-07, CA-09 |
| HU-02 | CA-06 |
| HU-03 | CA-08, CA-11 |
| HU-04 | CA-10, CA-11 |
| HU-05 | CA-07 |

---

## No-Objetivos
- Lógica de `ClientContext` (resolución de rutas de cliente existente, nuevo/recurrente) — feature `client_context` (T-014).
- Cualquier flujo de negocio (Discovery, Ingestion, …) y su lógica.
- Subcarpetas por flujo dentro de `010_inputs/` y `020_outputs/` (las crea cada flujo al correr).
- Versionado de modelos dentro de `models/` (`2026-07_v1/`, puntero `latest`) — feature de Modelling.
- Flag `--force` / sobrescritura de cliente existente — trabajo futuro pospuesto.
- Otros subcomandos de `foda client` (`list`, …).
- Tests de la capa CLI (los tests de esta feature cubren el core `create_client`).
- Filtrado de nombres reservados de Windows y normalización de mayúsculas (limitaciones conocidas, no objetivos de esta banda).

---

## Puntos de confirmación para el GATE humano
Decisiones tomadas por spec_writer (delegadas por la definition) que el humano puede validar o ajustar antes de `plan_builder`:
1. **DS-1 — límites del regex:** ¿se acepta longitud máxima 64, primer carácter alfanumérico obligatorio (rechazar `_`/`-` inicial) y restricción a **ASCII** (rechazar acentos/`ñ`)? Si el negocio necesita nombres con acentos, hay que ampliar el regex.
2. **DS-2 — atomicidad:** ¿se acepta "validación-primero + limpieza best-effort" en lugar de temp-dir + rename atómico?
3. **DS-3 — API del core:** ¿se acepta `create_client(name, clients_root) -> Path` con `clients_root` requerido y errores vía `ValueError` / `FileExistsError` estándar?
4. **Limitación case-insensitive:** ¿se acepta documentarla como limitación conocida (sin normalizar mayúsculas) en esta banda?
