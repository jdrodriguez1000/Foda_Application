# Plan de Implementación — client_scaffold

> Artefacto de la etapa 3 (`plan_builder`). Traduce la `spec.md` **aprobada** en un plan de
> implementación mínimo (NC-2) y en la lista **ordenada** de casos de test que guiarán el bucle
> TDD (red → green → refactor). **No** contiene código ni tests: solo el *cómo* y el *orden*.
>
> Banda: `tracer_bullet`. Fuentes: `spec.md` (esta celda), `700_architecture/system_design.md`
> (§3 R1–R9, §7 estructura, §10 medallion, §11 CLI), `980_guideline/principles.md` (NC-1…NC-6).
>
> **GATE humano al terminar:** este plan y sus casos TDD requieren aprobación del usuario antes de
> invocar `tdd_tester`.

---

## 1. Enfoque técnico

Slice vertical mínimo (NC-4): una función core pura + una capa CLI fina encima. Los tests atacan el
core; la CLI queda fuera del alcance de test de esta feature (spec §No-Objetivos).

### Core — `src/foda/core/scaffold.py`
Una única función pública, sin clases ni abstracciones nuevas (NC-2; la abstracción `Flow` **no**
aplica aquí: crear el scaffold no es un flujo del pipeline, es una operación previa de bootstrap):

```python
def create_client(name: str, clients_root: Path) -> Path: ...
```

Estructura interna sugerida (funciones privadas mínimas, solo si aportan claridad; el bucle TDD/
refactor decide su forma final):
- Validación del nombre contra el patrón DS-1 `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$` (un `re.fullmatch`
  o `re.match` con `$`). Falla → `ValueError` con mensaje que incluye el nombre recibido y el patrón
  esperado. **No toca disco.**
- Comprobación de existencia de `clients_root/<name>`: si existe (carpeta o archivo) → `FileExistsError`.
  **No toca disco.**
- Creación del árbol de carpetas (medallion + `models/` + `010_inputs/` + `020_outputs/`).
- Escritura de `client.yaml` con `name` y `created_at`.
- Retorno del `Path` a la carpeta creada.

**Orden invariante (DS-2):** toda validación (nombre + existencia) ocurre **antes** de cualquier
escritura. Ante un error de filesystem inesperado entre creación de carpetas y escritura del YAML,
limpieza best-effort de `clients_root/<name>` (`shutil.rmtree(..., ignore_errors=True)`) y relanzar
la excepción original.

**Dependencias de librería:**
- `pathlib`, `re`, `datetime`, `shutil` — stdlib (R1: Python 3.13+).
- `created_at`: fecha de hoy en UTC en formato `YYYY-MM-DD`
  (`datetime.now(timezone.utc).date().isoformat()`).
- **YAML:** el `client.yaml` de esta versión tiene solo dos claves escalares. Se escribe de forma
  determinista. Para **leerlo/parsearlo en los tests** (AC6) se necesita un parser YAML. Ver
  *Punto abierto PA-1* (PyYAML como dependencia del proyecto vs. escritura/lectura manual).

### CLI — `src/foda/cli.py`
Capa fina `foda client new <NAME>` (system_design §11). Resuelve `clients_root` (la carpeta
`clients/` del proyecto), invoca `create_client(...)`, traduce éxito → ruta + exit 0 y excepciones
→ mensaje de consola + exit ≠ 0. **Sin tests en esta feature** (spec §No-Objetivos); se implementa
al final como cableado, después de que el core esté en verde.

---

## 2. Archivos afectados

> El código **no** vive en `600_features/`; va en `src/foda/…` y `tests/…`.

| Ruta | Acción | Contenido |
|---|---|---|
| `src/foda/__init__.py` | crear | Marca de paquete (vacío). |
| `src/foda/core/__init__.py` | crear | Marca de paquete (vacío). |
| `src/foda/core/scaffold.py` | crear | Función `create_client(name, clients_root) -> Path`. |
| `src/foda/cli.py` | crear | Comando `foda client new <NAME>` (cableado final, sin test). |
| `tests/__init__.py` | crear (si aplica) | Marca de paquete de tests. |
| `tests/core/test_scaffold.py` | crear | Tests unitarios de `create_client` (usan `tmp_path`). |
| `pyproject.toml` | crear | Config mínima de proyecto/paquete + pytest, para que imports y test runner resuelvan. Ver PA-2. |

**Nota de infraestructura:** este es el **primer** artefacto de código del repo (no existe `src/`,
`tests/` ni `pyproject.toml`). Por eso el plan incluye el andamiaje mínimo de paquete/tests. Es
alcance necesario, no opcional, pero se mantiene al mínimo (NC-2): sin dependencias que la spec no
exija. Ver puntos abiertos PA-1 y PA-2 para el GATE.

---

## 3. Orden de trabajo (de lo básico a lo completo)

El bucle TDD consume los casos de la §5 en orden. La secuencia de implementación asociada es:

1. **Andamiaje mínimo** (`pyproject.toml`, `src/foda/` y `tests/` con sus `__init__.py`) para poder
   ejecutar `pytest` e importar `foda.core.scaffold`. (Habilita el primer rojo/verde.)
2. **Camino feliz mínimo (tracer bullet):** `create_client` crea `clients_root/<name>` y devuelve su
   `Path`. (Caso 1.)
3. **Contenido del árbol de primer nivel** y subcarpetas (medallion, `models/`, `010_inputs/`,
   `020_outputs/`). (Casos 2–5.)
4. **`client.yaml`** con `name` y `created_at`. (Casos 6–7.)
5. **Nombres válidos representativos.** (Caso 8.)
6. **Validación del nombre** (patrón DS-1) para todos los grupos de casos límite → `ValueError` sin
   tocar disco. (Casos 9–15.)
7. **Duplicado** → `FileExistsError` sin sobrescribir. (Caso 16.)
8. **Invariante validación-antes-de-escritura** explícito: tras error, el FS para ese nombre queda
   idéntico. (Caso 17.)
9. **(Opcional/GATE) Rollback en fallo de FS** (DS-2.2), si se decide testear con monkeypatch. (Caso
   18, ver PA-3.)
10. **Cableado CLI** `foda client new` (sin test), una vez el core está verde y refactorizado.

---

## 4. Dependencias y contratos

- **Consume:** nada de otras features. Solo stdlib (+ posible PyYAML, PA-1).
- **Produce:** la función core `create_client` y el árbol de cliente en disco, que serán consumidos
  por `client_context` (T-014) y por los flujos del pipeline. El contrato público es la firma y los
  errores estándar (`ValueError`, `FileExistsError`) definidos en la spec §Interfaces.
- **Contrato de datos:** `client.yaml` = mapa con exactamente `name` (str, == input) y `created_at`
  (str `YYYY-MM-DD`, UTC). Estructura de carpetas alineada con system_design §7 y §10.
- **Restricciones respetadas:** R1 (Python 3.13+), R3 (YAML de configuración), R6 (persistencia por
  carpeta de cliente).

---

## 5. Casos de test (lista ordenada para el bucle TDD)

Cada caso es una afirmación verificable atómica sobre `create_client`, usando un `clients_root`
temporal (`tmp_path` de pytest). Orden: fundamental → complejo. Trazabilidad a los criterios de
aceptación (AC) de la spec entre paréntesis.

1. `create_client("ABC", tmp)` crea el directorio `tmp/ABC/` y devuelve un `Path` que apunta a él. (AC1, AC7)
2. Bajo `tmp/ABC/` existen exactamente estas entradas de primer nivel: archivo `client.yaml` y carpetas `010_inputs/`, `020_outputs/`, `data/`, `models/`. (AC2)
3. `tmp/ABC/010_inputs/` y `tmp/ABC/020_outputs/` existen y están vacías. (AC5)
4. `tmp/ABC/data/` contiene `bronze/`, `silver/`, `gold/`, y las tres están vacías. (AC3)
5. `tmp/ABC/models/` existe y está vacía (sin subcarpetas de versión). (AC4)
6. `tmp/ABC/client.yaml` es YAML válido que parsea a un mapa cuya clave `name == "ABC"`. (AC6)
7. `tmp/ABC/client.yaml` tiene `created_at` cuyo valor cumple el patrón `^\d{4}-\d{2}-\d{2}$`. (AC6)
8. Para cada nombre válido representativo (`"X"`, `"9lives"`, `"Client_1-a"`), `create_client(...)` crea el árbol completo sin error. (AC9)
9. Nombre vacío `""` lanza `ValueError` y no crea ninguna carpeta. (AC8, AC11)
10. Nombre solo-espacios `"   "` y con espacio interior `"ab c"` lanzan `ValueError`; nada creado. (AC8, AC11)
11. Nombre que empieza por guion `"-abc"` o por guion bajo `"_abc"` lanza `ValueError`; nada creado. (AC8, AC11)
12. Nombre con separador de ruta `"a/b"` o `"a\\b"` lanza `ValueError`; nada creado. (AC8, AC11)
13. Nombres de ruta especiales `"."` y `".."` lanzan `ValueError`; nada creado. (AC8, AC11)
14. Nombre con punto interior `"ab.c"` o carácter no permitido (`"a!b"`, `"a@b"`) lanza `ValueError`; nada creado. (AC8, AC11)
15. Nombre no-ASCII / acentuado (`"añez"`, `"clienté"`) lanza `ValueError`; nada creado. (AC8, AC11)
16. Nombre de longitud > 64 (65 caracteres válidos) lanza `ValueError`; nada creado. (AC8, AC11)
17. `create_client("ABC", tmp)` cuando `tmp/ABC/` ya existe (con un archivo centinela dentro) lanza `FileExistsError` y deja el contenido preexistente intacto. (AC10, AC11)
18. **(Opcional, sujeto a GATE — PA-3)** Si un error de filesystem ocurre tras crear parte del árbol, `create_client` limpia best-effort `tmp/<name>/` (no queda carpeta parcial) y relanza la excepción original. (DS-2.2)

> Nota de granularidad: los casos 9–16 podrían fusionarse en un único test parametrizado sobre la
> tabla de nombres inválidos de la spec. Se enumeran por separado por trazabilidad; el bucle TDD/
> refactor puede consolidarlos en un `pytest.mark.parametrize` durante el refactor (green→refactored)
> sin perder cobertura.

---

## 6. Estrategia de test

- **Unit tests** sobre `create_client` en `tests/core/test_scaffold.py`, usando el fixture `tmp_path`
  de pytest como `clients_root` (nunca el `clients/` real del repo — DS-3).
- **Fixtures / datos de prueba:** ninguno externo. Los nombres válidos e inválidos se derivan de la
  tabla de casos límite de la spec; el caso 17 requiere pre-crear `tmp/ABC/` con un archivo centinela.
- **Parser YAML en tests** (caso 6/7): ver PA-1.
- **Sin tests de la CLI** en esta feature (spec §No-Objetivos).
- **Caso 18 (rollback FS):** requiere provocar un fallo de filesystem simulado (p. ej. `monkeypatch`
  sobre `Path.mkdir` o `open` para que lance en mitad de la creación). Es la única prueba que necesita
  mocking; se marca opcional a decisión del GATE (PA-3).

---

## 7. Puntos abiertos para el GATE humano (NC-6)

- **PA-1 — Parser/serializador YAML.** El core escribe un `client.yaml` de dos claves escalares (se
  puede hacer sin dependencias). Pero **leerlo en los tests** (AC6) requiere un parser. Propuesta:
  adoptar **PyYAML** como dependencia del proyecto (coherente con R3: la configuración del sistema es
  YAML y otras features la leerán). Alternativa mínima: escribir y leer el YAML "a mano" en esta banda
  para no introducir dependencias todavía. ¿Se aprueba PyYAML como dependencia, o se pospone?
- **PA-2 — Andamiaje de paquete (`pyproject.toml`).** Es la primera feature con código: hay que crear
  el esqueleto de paquete y la config de pytest. ¿Se aprueba crear `pyproject.toml` mínimo (metadata
  del paquete `foda`, `src/`-layout, pytest y `python_requires >= 3.13`) en esta feature, o el usuario
  prefiere una tarea de bootstrap separada previa?
- **PA-3 — ¿Se testea el rollback de FS (caso 18)?** Es la única prueba que exige mocking y cubre un
  error raro (DS-2.2). Opciones: (a) incluirla como caso TDD con `monkeypatch`; (b) implementar la
  limpieza best-effort pero **documentarla sin test** en esta banda `tracer_bullet`. Recomendación por
  simplicidad (NC-2): opción (b), dejando el caso 18 como no-objetivo de test de esta banda.
