# Plan de Implementación — flow_orchestrator

> Artefacto de la etapa 3 (`plan_builder`). Traduce la `spec.md` **aprobada** en un plan de
> implementación mínimo (NC-2) y en la lista **ordenada** de casos de test que guiarán el bucle
> TDD (red → green → refactor). **No** contiene código ni tests: solo el *cómo* y el *orden*.
>
> Banda: `tracer_bullet`. Fuentes: `spec.md` (GATE humano aprobado, DS-ORQ-1..4),
> `600_features/client_new_cli/tracer_bullet/plan.md` (estilo de CLI y de plan), `src/foda/cli.py`
> (`_build_parser`, `_find_project_root`, `main`, traducción de errores), `src/foda/core/flow.py`
> (`Flow.run`, `Artifact.exists/.path`, `FlowContractError`), `src/foda/core/context.py`
> (`ClientContext`, `FileNotFoundError`), `src/foda/flows/f020_onboarding/onboarding.py`
> (`Onboarding`, `requires`/`produces`), `700_architecture/system_design.md` (§4, §11),
> `800_persistence/decisions.md` (D-021, D-062), `980_guideline/principles.md` (NC-1…NC-6).
>
> **GATE humano al terminar:** este plan y sus casos TDD requieren aprobación del usuario antes de
> invocar `tdd_tester`.

---

## 1. Enfoque técnico

Slice vertical mínimo (NC-4, NC-2) que **cablea** piezas ya CONFORMES sin reimplementar lógica de
flujo ni de rutas (delegación estricta C-5). Dos entregables de producción:

### 1.1 Módulo nuevo — `src/foda/orchestrator.py` (DS-ORQ-1/2)
Único punto de resolución nombre→flujo, reutilizado por `run` y `status`. Sin clases nuevas ni
descubrimiento dinámico (NC-2; No-Objetivos de la spec):

```python
from foda.core.flow import Flow
from foda.flows.f020_onboarding.onboarding import Onboarding

FLOWS: dict[str, type[Flow]] = {"onboarding": Onboarding}

def resolve_flow(name: str) -> Flow:
    """Devuelve una INSTANCIA del flujo registrado bajo `name` (FLOWS[name]()).
    Lanza ValueError si `name` no está en FLOWS (flujo desconocido, DS-ORQ-2)."""
```

- Vive **fuera de `core/`** para no invertir dependencias (`core` no debe conocer flujos concretos;
  DS-ORQ-1). Importa `Onboarding` de `foda.flows`.
- `resolve_flow` es **pura** (no toca disco). Registrar un flujo nuevo = añadir una entrada a
  `FLOWS`, sin editar `cli.py`/`run`/`status` (HU-05).

### 1.2 Extensión quirúrgica — `src/foda/cli.py` (NC-3, no toca `client new`)
Se añaden subparsers y despacho al `main` existente, reutilizando `_find_project_root` y el patrón de
traducción de errores ya vigente:

- **Parser** (`_build_parser`): añadir `run` (posicional `<cliente>` + opción **requerida** `--flow`)
  y `status` (posicional `<cliente>`). `argparse` cubre el código `2` cuando falta `<cliente>` o
  `--flow` (DS-ORQ-4).
- **Despacho en `main`** según `args.command`:
  - `run` (orden DS-ORQ-4): (1) `_find_project_root` (raíz no encontrada → `stderr` + `1`, sin
    disco); (2) `resolve_flow(<flujo>)` — **primero**, puro, sin disco (`ValueError` → `stderr` que
    nombra el flujo + `1`); (3) `ClientContext(<cliente>, clients_root)` (`FileNotFoundError` →
    `stderr` que nombra el cliente + `1`); (4) `flow.run(ctx)` (`FlowContractError` → `stderr` que
    nombra el/los artefacto(s) + `1`, antes de escribir salida); (5) éxito → confirmación por
    `stdout` que nombra flujo, cliente y ruta(s) de `FlowResult.outputs`, retorna `0`.
  - `status`: (1) raíz; (2) `ClientContext(<cliente>, clients_root)` (`FileNotFoundError` →
    `stderr` + `1`, mismo estilo que `run`); (3) por cada `(nombre, flujo)` de `FLOWS`, instanciar y,
    por cada `Artifact` en `flujo.requires` y luego `flujo.produces`, imprimir rol, nombre lógico,
    marcador `[presente]`/`[ausente]` (según `artifact.exists(ctx)`) y ruta relativa; retorna `0`.
    **Sin efectos en disco**, sin leer contenido de artefactos.
- **`clients_root = <raíz>/clients` NO se crea** (a diferencia de `client new`): `run`/`status` operan
  sobre clientes ya existentes (DS-ORQ-4, punto 5 del GATE). Se elimina/omite el `mkdir` en estas
  rutas; el `client new` conserva el suyo.

**Formato fijo de `foda status`** (DS-ORQ-3), estable para tests por subcadenas (rol, nombre lógico,
`presente`/`ausente`, ruta relativa al `root` del cliente):

```
onboarding:
  requires  contract_data     [presente]  020_outputs/010_discovery/contract_data.json
  produces  map_client_data   [ausente]   020_outputs/020_onboarding/map_client_data.json
```

**Dependencias de librería:** `argparse`, `pathlib`, `sys` — stdlib (R1: Python 3.13+). Cero
dependencias nuevas. Nuevos imports en `cli.py`: `from foda.orchestrator import resolve_flow, FLOWS`
y `from foda.core.flow import FlowContractError`.

---

## 2. Archivos afectados

> El código **no** vive en `600_features/`; va en `src/foda/…` y `tests/…`.

| Ruta | Acción | Contenido |
|---|---|---|
| `src/foda/orchestrator.py` | crear | `FLOWS: dict[str, type[Flow]]` (registro literal `{"onboarding": Onboarding}`) y `resolve_flow(name) -> Flow` (instancia; `ValueError` si desconocido). |
| `src/foda/cli.py` | modificar | Subparsers `run`/`status` en `_build_parser`; despacho `run`/`status` en `main`; sin `mkdir` de `clients/` en estas rutas. **No** toca `client new`. |
| `tests/test_orchestrator.py` | crear | Suite unitaria del registro/resolución (`FLOWS`, `resolve_flow`), independiente de la CLI. |
| `tests/cli/test_flow_orchestrator_cli.py` | crear | Suite de la CLI de orquestación (`run`/`status`), **independiente** de `test_client_new_cli.py` (CA-14). Invoca `main(argv)` bajo un proyecto+cliente temporal. |

**Notas de infraestructura:**
- El andamiaje ya existe (`pyproject.toml`, `src/foda/`, `src/foda/core/`, `src/foda/flows/`,
  `tests/`, `tests/cli/`). No se crea esqueleto nuevo ni entrada `[project.scripts]` (ya declarada por
  `client_new_cli`).
- Piezas CONFORMES consumidas sin modificar: `ClientContext`, `Flow.run`, `Artifact.exists/.path`,
  `FlowContractError`, `Onboarding`. La feature **no** añade artefactos de datos propios (D-021: el
  estado es el disco de artefactos de los flujos).

---

## 3. Orden de trabajo (de lo básico a lo completo)

El bucle TDD consume los casos de la §6 en orden:

1. **Registro/resolución de flujos** (`orchestrator.py`): `resolve_flow("onboarding")` → instancia de
   `Onboarding`; `FLOWS` explícito; flujo desconocido → `ValueError`. (Casos 1–3.)
2. **`run` — tracer happy path:** `run ABC --flow onboarding` con `contract_data.json` sembrado →
   `0`, escribe `map_client_data.json`, confirmación por `stdout`. (Casos 4–5.)
3. **`run` — delegación verificada:** `flow.run` invocado 1 vez con `ctx.name == "ABC"`. (Caso 6.)
4. **`run` — los tres errores semánticos:** flujo desconocido, cliente inexistente,
   `FlowContractError` → `1`, `stderr`, sin `Traceback`, sin escribir salida. (Casos 7–9.)
5. **`status` — happy path e introspección de disco:** lista `onboarding` con markers; refleja el
   disco antes/después de un `run` exitoso. (Casos 10–11.)
6. **`status` — cliente inexistente:** `1`, `stderr`, sin `Traceback`. (Caso 12.)
7. **No creación de `clients/`:** ante cliente inexistente, `run`/`status` no crean el árbol. (Caso 13.)
8. **Extensibilidad HU-05:** flujo falso en `FLOWS` descubierto por `run` y `status` sin tocar su
   lógica. (Caso 14.)
9. **Errores de parseo de `argparse`:** falta `--flow`/`<cliente>` → `2`. (Caso 15.)
10. **Refactor final** de ambas suites manteniendo verde (CA-14, criterio agregado).

---

## 4. Dependencias y contratos

- **Consume (CONFORME, no se reimplementa):**
  - `foda.core.context.ClientContext(name, clients_root)` → objeto con `name`, `root`,
    `outputs_dir`, …; `FileNotFoundError` si no existe `clients_root/<name>/client.yaml`.
  - `foda.core.flow.Flow.run(ctx) -> FlowResult`; puede lanzar `FlowContractError`.
  - `foda.core.flow.Artifact.exists(ctx) -> bool` y `.path(ctx) -> Path` (introspección de `status`).
  - `foda.flows.f020_onboarding.onboarding.Onboarding` (`requires = [contract_data]`,
    `produces = [map_client_data]`).
  - `pyproject.toml` (solo su **existencia** localiza `<raíz>` vía `_find_project_root`, D-C).
- **Produce:** `src/foda/orchestrator.py` (`FLOWS`, `resolve_flow`); la extensión de `src/foda/cli.py`
  con `run`/`status`; los efectos de `flow.run` en disco (escritos por el flujo, no por el orquestador).
- **Convención de códigos de salida (DS-ORQ-4):** `0` éxito · `1` error semántico (flujo desconocido,
  cliente inexistente, `FlowContractError`, raíz no encontrada) · `2` parseo de `argparse`.
- **Restricciones respetadas:** R1 (Python 3.13+, solo stdlib), NC-2 (registro literal, sin
  descubrimiento dinámico), NC-3 (no toca `client new`), D-021 (Single Writer: sin manifiesto propio).

---

## 5. Tareas (atómicas y trazables)

> Cada tarea es **atómica** y respeta las reglas de partición: **un solo responsable**, **un solo
> entregable**, y **código y test en tareas separadas**. **Estado** inicial `no_implementada`
> (valores: `no_implementada` | `implementada` | `cancelada_suspendida`); el **responsable de cada
> tarea es su único escritor de estado** (`D-021`). Trazabilidad → `CA-xx` de la spec.

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Crear `src/foda/orchestrator.py` con `FLOWS = {"onboarding": Onboarding}` y `resolve_flow(name) -> Flow` (instancia; `ValueError` si desconocido). | `orchestrator.py` | tdd_coder | no_implementada | CA-10 |
| TSK-02 | Extender `_build_parser` en `cli.py`: subparsers `run` (`<cliente>` + `--flow` requerido) y `status` (`<cliente>`); sin tocar `client new`. | `cli.py` (parser) | tdd_coder | no_implementada | CA-13 |
| TSK-03 | Implementar el despacho de `run` en `main` (orden DS-ORQ-4: raíz → `resolve_flow` → `ClientContext` → `flow.run`), con traducción de éxito (`stdout`, `0`) y de `ValueError`/`FileNotFoundError`/`FlowContractError` (`stderr`, `1`); sin crear `clients/`. | `cli.py` (despacho `run`) | tdd_coder | no_implementada | CA-01, CA-02, CA-04, CA-05, CA-06, CA-12 |
| TSK-04 | Implementar el despacho de `status` en `main`: `ClientContext` (error `FileNotFoundError`→`1`) e introspección `[presente]`/`[ausente]` por artefacto de cada flujo de `FLOWS` (formato DS-ORQ-3); sin efectos en disco. | `cli.py` (despacho `status`) | tdd_coder | no_implementada | CA-07, CA-08, CA-09, CA-11, CA-12 |
| TSK-05 | Escribir test: `resolve_flow("onboarding")` devuelve una instancia de `Onboarding` (subclase de `Flow`). | test resolución | tdd_tester | no_implementada | CA-10 |
| TSK-06 | Escribir test: `FLOWS` es un mapeo explícito nombre→clase `Flow` que contiene `"onboarding" -> Onboarding`. | test registro | tdd_tester | no_implementada | CA-10 |
| TSK-07 | Escribir test: `resolve_flow(<no registrado>)` lanza `ValueError`. | test flujo desconocido (unit) | tdd_tester | no_implementada | CA-10 |
| TSK-08 | Escribir test: `run ABC --flow onboarding` (contrato sembrado) → `0` y deja escrito `map_client_data.json`. | test run happy (código+disco) | tdd_tester | no_implementada | CA-01 |
| TSK-09 | Escribir test: en el éxito, `stdout` menciona flujo `onboarding`, cliente `ABC` y la ruta de `map_client_data.json`. | test run confirmación | tdd_tester | no_implementada | CA-02 |
| TSK-10 | Escribir test: con `flow.run`/`Onboarding.run` espiado, `run` lo invoca 1 vez con `ctx.name == "ABC"`. | test delegación | tdd_tester | no_implementada | CA-03 |
| TSK-11 | Escribir test: `run ABC --flow inexistente` → `1`, `stderr` nombra el flujo, sin `Traceback`, sin artefacto escrito. | test run flujo desconocido | tdd_tester | no_implementada | CA-04 |
| TSK-12 | Escribir test: `run GHOST --flow onboarding` → `1`, `stderr` nombra el cliente, sin `Traceback`, nada escrito. | test run cliente inexistente | tdd_tester | no_implementada | CA-05 |
| TSK-13 | Escribir test: `run ABC --flow onboarding` sin `contract_data.json` → `1`, `stderr` refleja `FlowContractError`, sin `Traceback`, no se escribe `map_client_data.json`. | test run artefacto faltante | tdd_tester | no_implementada | CA-06 |
| TSK-14 | Escribir test: `status ABC` → `0` y `stdout` lista `onboarding` con `contract_data` y `map_client_data`, cada uno con marcador de existencia. | test status listado | tdd_tester | no_implementada | CA-07 |
| TSK-15 | Escribir test: `status` refleja el disco — `contract_data` presente / `map_client_data` ausente; tras un `run` exitoso, ambos presentes. | test status refleja disco | tdd_tester | no_implementada | CA-08 |
| TSK-16 | Escribir test: `status GHOST` → `1`, `stderr` nombra el cliente (estilo `run`), sin `Traceback`. | test status cliente inexistente | tdd_tester | no_implementada | CA-09 |
| TSK-17 | Escribir test: ante cliente inexistente, ni `run GHOST …` ni `status GHOST` crean `<raíz>/clients/` ni la carpeta del cliente. | test no crea `clients/` | tdd_tester | no_implementada | CA-12 |
| TSK-18 | Escribir test: un flujo falso añadido a `FLOWS` (monkeypatch) es descubierto por `status ABC` (lo lista) y por `run ABC --flow fake` (despacha a `FakeFlow.run`), sin modificar la lógica de `run`/`status`. | test extensibilidad HU-05 | tdd_tester | no_implementada | CA-11 |
| TSK-19 | Escribir test: `run ABC` (falta `--flow`), `run` (falta `<cliente>`) y `status` (falta `<cliente>`) terminan con código `2` (`argparse`). | test parseo argparse | tdd_tester | no_implementada | CA-13 |
| TSK-20 | Refactor: consolidar/limpiar ambas suites (factorizar el fixture de proyecto+cliente temporal) manteniendo todo verde; garantiza la suite propia de orquestación (CA-14). | Refactor (sin cambio de comportamiento) | tdd_refactor | no_implementada | CA-14 |

---

## 6. Casos de test (lista ordenada para el bucle TDD)

Cada caso es una afirmación verificable atómica. Casos de CLI: se invoca `main(argv)` **en proceso**
bajo un **proyecto+cliente temporal** (`tmp_path` con `pyproject.toml` marcador; `clients/ABC/` con
`client.yaml`; `contract_data.json` sembrado en `clients/ABC/020_outputs/010_discovery/` cuando el
caso lo requiere; cwd fijado con `monkeypatch.chdir`). Orden: fundamental → complejo. Trazabilidad a
los `CA-xx` entre paréntesis. Deben coincidir con `stages.tdd.cases[]` de `state.json`.

1. `resolve_flow("onboarding")` devuelve una **instancia** de `Onboarding` (subclase de `Flow`). (CA-10)
2. `FLOWS` es un mapeo explícito nombre→clase `Flow` que contiene `"onboarding"` mapeado a `Onboarding`. (CA-10)
3. `resolve_flow(<nombre no registrado>)` lanza `ValueError`. (CA-10, CA-04)
4. `main(["run","ABC","--flow","onboarding"])` con `ABC` existente y `contract_data.json` presente/válido devuelve `0` y deja escrito `clients/ABC/020_outputs/020_onboarding/map_client_data.json`. (CA-01)
5. En el éxito del caso 4, `stdout` contiene una confirmación legible que menciona el flujo `onboarding`, el cliente `ABC` y la ruta del artefacto producido (`map_client_data.json`). (CA-02)
6. Con `Onboarding.run`/`flow.run` espiado, `main(["run","ABC","--flow","onboarding"])` lo invoca **exactamente una vez** con un `ctx` cuyo `name == "ABC"` (no deriva el mapa por su cuenta). (CA-03)
7. `main(["run","ABC","--flow","inexistente"])` devuelve `1`, `stderr` menciona el flujo desconocido (`inexistente`), la salida no contiene `"Traceback"`, y no se escribe ningún artefacto de salida. (CA-04)
8. `main(["run","GHOST","--flow","onboarding"])` (cliente inexistente) devuelve `1`, `stderr` menciona que el cliente no existe, sin `"Traceback"`, y no se crea/escribe ningún artefacto. (CA-05)
9. `main(["run","ABC","--flow","onboarding"])` con `ABC` existente pero **sin** `contract_data.json` devuelve `1`, `stderr` refleja el `FlowContractError` (artefacto requerido ausente), sin `"Traceback"`, y **no** se escribe `map_client_data.json`. (CA-06)
10. `main(["status","ABC"])` con `ABC` existente devuelve `0` y su `stdout` lista el flujo `onboarding` incluyendo `contract_data` y `map_client_data`, cada uno con marcador `[presente]`/`[ausente]`. (CA-07)
11. `foda status` refleja el disco: con `contract_data.json` presente y `map_client_data.json` ausente, `stdout` marca `contract_data` presente y `map_client_data` ausente; tras un `main(["run","ABC","--flow","onboarding"])` exitoso, un nuevo `main(["status","ABC"])` marca **ambos** presentes. (CA-08)
12. `main(["status","GHOST"])` (cliente inexistente) devuelve `1`, `stderr` menciona que el cliente no existe (mismo estilo que `run`), y la salida no contiene `"Traceback"`. (CA-09)
13. Ante cliente inexistente, ni `main(["run","GHOST","--flow","onboarding"])` ni `main(["status","GHOST"])` crean `<raíz>/clients/` ni la carpeta `clients/GHOST/`. (CA-12)
14. Con un flujo falso registrado en `FLOWS` (p. ej. `{"fake": FakeFlow}` vía monkeypatch), `main(["status","ABC"])` lista `fake` con sus artefactos y `main(["run","ABC","--flow","fake"])` despacha a `FakeFlow.run`, sin modificar la lógica de `run`/`status`. (CA-11)
15. Errores de parseo de `argparse` → código `2`: `main(["run","ABC"])` (falta `--flow`), `main(["run"])` (falta `<cliente>`) y `main(["status"])` (falta `<cliente>`). (CA-13)

> **CA-14 (agregado):** "existe una suite de tests de la CLI de orquestación, independiente de la de
> `client_new_cli`, que ejercita todo lo anterior en verde" es un criterio **agregado**, satisfecho
> por el conjunto de los casos 1–15 en `tests/cli/test_flow_orchestrator_cli.py` +
> `tests/test_orchestrator.py` y su refactor (TSK-20), no por un test aislado.

### Mapa caso → tareas (`TSK-xx`)
Cada caso agrupa su tarea-test y su(s) tarea(s)-código (el bucle corre por caso; las tareas son la
capa de trazabilidad).

| Caso | Tarea-test | Tarea(s)-código |
|---|---|---|
| 1 | TSK-05 | TSK-01 |
| 2 | TSK-06 | TSK-01 |
| 3 | TSK-07 | TSK-01 |
| 4 | TSK-08 | TSK-02, TSK-03 |
| 5 | TSK-09 | TSK-03 |
| 6 | TSK-10 | TSK-03 |
| 7 | TSK-11 | TSK-03 |
| 8 | TSK-12 | TSK-03 |
| 9 | TSK-13 | TSK-03 |
| 10 | TSK-14 | TSK-02, TSK-04 |
| 11 | TSK-15 | TSK-04 |
| 12 | TSK-16 | TSK-04 |
| 13 | TSK-17 | TSK-03, TSK-04 |
| 14 | TSK-18 | TSK-03, TSK-04 |
| 15 | TSK-19 | TSK-02 |
| (ambas suites) | TSK-20 (refactor) | — |

> Nota de granularidad: los casos 1–3 (unit del registro) requieren TSK-01 para el primer verde; los
> casos 4–9 comparten el despacho de `run` (TSK-03) y su primer verde necesita TSK-02+TSK-03 juntos;
> los casos 10–14 comparten el despacho de `status` (TSK-04). Se enumeran por trazabilidad de
> comportamiento, no por tests 1:1.

---

## 7. Estrategia de test

- **Unit del registro** en `tests/test_orchestrator.py`: prueban `resolve_flow`/`FLOWS` directamente,
  sin CLI, sin disco (casos 1–3). Verifican tipo devuelto (instancia de `Onboarding`/`Flow`),
  contenido del mapeo y `ValueError` para nombre no registrado.
- **Nivel CLI** en `tests/cli/test_flow_orchestrator_cli.py`, invocando `main(argv)` **en proceso**
  (sin `subprocess`): rápido y determinista; se verifica código de retorno + salida capturada
  (`capsys`) + efectos en disco.
- **Proyecto+cliente temporal (fixture):** `tmp_path` con `pyproject.toml` marcador y un cliente
  `clients/ABC/` sembrado con `client.yaml` (marcador de existencia que exige `ClientContext`) y, para
  los casos que lo requieren, `020_outputs/010_discovery/contract_data.json` con un contrato mínimo
  **válido** (que `Onboarding.validate` acepte). El cwd se fija con `monkeypatch.chdir`. Nunca se toca
  el `clients/` real del repo.
- **Delegación (caso 6):** `monkeypatch`/spy sobre `Onboarding.run` (o el símbolo resuelto por
  `resolve_flow`) para contar invocaciones y capturar el `ctx`, sin ejecutar el flujo real.
- **Errores (casos 7–9, 12):** se comprueba ausencia de `"Traceback"` en la salida (sin traza cruda),
  el código `1` y el efecto nulo/intacto en disco (p. ej. `map_client_data.json` no creado).
- **Extensibilidad (caso 14):** un `FakeFlow(Flow)` mínimo definido en el test (con `requires`/
  `produces` propios y `execute` no-op) se inyecta en `FLOWS` vía `monkeypatch.setitem`; se verifica
  que `status` lo lista y que `run --flow fake` lo despacha, **sin** tocar `cli.py`.
- **Errores de parseo (caso 15):** `argparse` llama `sys.exit(2)`; el test captura `SystemExit` y
  comprueba `code == 2`.
- **Fixtures / datos de prueba:** el contrato mínimo válido para `contract_data.json` se deriva del
  contrato de `Onboarding` (jerarquías con `levels` no vacíos, miembros coherentes, datasets con enums
  válidos; ver `onboarding.py`). La integración *end-to-end* (comando `foda` como binario) queda para
  `integration_tester`, no para esta suite.

---

## 8. Notas y riesgos (NC-1 / NC-6)

- **Sin puntos abiertos que bloqueen el GATE:** los cinco/seis puntos de confirmación de la spec
  (DS-ORQ-1..4, `run`/`status` no crean `clients/`, ubicación del módulo) fueron **aprobados por el
  humano** junto con la spec. Este plan los implementa sin reabrirlos.
- **Riesgo — contrato válido para el happy path:** los casos 4/5/6/11 exigen que `Onboarding.run`
  llegue a `execute` sin lanzar `FlowContractError`; el `contract_data.json` sembrado debe satisfacer
  **todas** las reglas de contenido que hoy valida `Onboarding.validate` (levels, maps_to, enums,
  fechas, unicidad de field.name). Se reutilizará el mismo contrato mínimo válido ya usado por la
  suite de `onboarding` como referencia; queda a criterio del `tdd_tester` construir el fixture.
- **Riesgo — un solo flujo real:** `FLOWS` se diseña genérico pero solo se ejercita con `onboarding`
  real; la extensibilidad HU-05 (caso 14) se prueba con un `FakeFlow` de test (limitación documentada
  en `definition.md`/spec).
- **Cambio quirúrgico en `cli.py`:** el `mkdir(clients_root)` existente pertenece a la ruta de
  `client new`; el despacho de `run`/`status` **no** debe crear `clients/`. Se mantiene la ruta de
  `client new` intacta (NC-3, CA-12).
- **Alcance de test de esta feature:** solo el orquestador (`orchestrator.py`) y su CLI (`run`/
  `status`); las piezas CONFORMES consumidas (`ClientContext`, `Flow`, `Onboarding`) ya tienen sus
  propias suites verdes y no se re-testean aquí.
