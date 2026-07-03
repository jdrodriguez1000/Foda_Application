# Plan de Implementación — flow_base

> Artefacto de la etapa 3 (`plan_builder`). Traduce la `spec.md` **aprobada** (GATE humano superado)
> en un plan de implementación mínimo (NC-2) y en la lista **ordenada** de casos de test que guiarán
> el bucle TDD (red → green → refactor). **No** contiene código ni tests: solo el *cómo* y el *orden*.
>
> Banda: `tracer_bullet`. Fuentes: `spec.md` (esta celda, GATE humano aprobado — las 6 decisiones
> DS-FLOW-1…4 + GATE #5/#6 quedaron ACEPTADAS tal cual), `definition.md` (HU-01…HU-05),
> `feature_contract.md` (estrella polar), `src/foda/core/context.py` (`ClientContext`, T-014, CONFORME
> — insumo de resolución de rutas), `src/foda/core/scaffold.py` (`create_client`, CONFORME — provee el
> fixture del cliente bajo `tmp_path`), `700_architecture/system_design.md` (§7 estructura, §8 contrato
> de artefactos, §9 abstracción `Flow`), `800_persistence/decisions.md` (D-021, D-031, D-037, D-042),
> `980_guideline/principles.md` (NC-1…NC-6).
>
> **GATE humano al terminar:** este plan y sus casos TDD requieren aprobación del usuario antes de
> invocar `tdd_tester`.

---

## 1. Enfoque Técnico

Slice vertical mínimo (NC-4, NC-2): un único módulo `src/foda/core/flow.py` que fija —una sola vez,
para todos los flujos futuros— la abstracción común de flujo de `system_design.md` §9. La feature
**no** implementa ningún flujo real (Discovery, Ingestion, …): el único flujo de esta banda es el
**trivial de prueba**, definido en los tests. **No** toca el core existente (`context.py`, `scaffold.py`
están CONFORME y se consumen tal cual; NC-3).

### Módulo a producir — `src/foda/core/flow.py`

Cuatro artefactos públicos, en el orden en que se construirán (de dato puro a orquestación):

1. **`FlowContractError(Exception)`** (DS-FLOW-1) — excepción de dominio propia del core. La lanza
   `validate()` cuando un artefacto de `requires` no existe en disco, **antes** de `execute()`.
   Subclase directa de `Exception` (sin jerarquía propia todavía, NC-2). Su mensaje nombra el/los
   artefacto(s) faltante(s) (su `name` y su ruta resuelta) para diagnóstico (P8).

2. **`Artifact(name: str, base: str, relative: str)`** (DS-FLOW-2) — `@dataclass(frozen=True)`
   declarativo. Resuelve su ruta física **exclusivamente** vía `ClientContext` (T-014), sin
   reimplementar lógica de rutas (HU-05):
   - `path(ctx) -> Path` → `<directorio base de ctx> / relative`, donde `base` es una **clave lógica**
     mapeada a una propiedad de `ctx`: `"inputs"→ctx.inputs_dir`, `"outputs"→ctx.outputs_dir`,
     `"bronze"→ctx.bronze_dir`, `"silver"→ctx.silver_dir`, `"gold"→ctx.gold_dir`,
     `"models"→ctx.models_dir`. Si `base` no es una de las seis claves conocidas → `ValueError`
     (guarda defensiva: error de programación del autor del flujo, no de datos del cliente).
   - `exists(ctx) -> bool` → `self.path(ctx).exists()`.

3. **`FlowResult(success: bool, outputs: list[Path])`** (DS-FLOW-3) — `@dataclass(frozen=True)` mínimo:
   `success` (True = éxito) y `outputs` (rutas resueltas de los artefactos producidos). Sin campo de
   inconsistencias/mensajes (diferido a `stab_1`, sin consumidor hoy; NC-2).

4. **`Flow`** (DS-FLOW-4) — abstracción común. Atributos de contrato con valores base vacíos
   (`name = ""`, `requires = []`, `produces = []`) y **template method** `run(ctx)` **no
   sobreescribible** que invoca los 4 hooks en **orden fijo** (GATE #6):

   ```python
   def run(self, ctx: ClientContext) -> FlowResult:
       self.load_inputs(ctx)              # 1
       self.validate(ctx)                 # 2  (puede lanzar FlowContractError)
       result = self.execute(ctx)         # 3  (el flujo concreto construye el FlowResult)
       self.write_outputs(ctx, result)    # 4
       return result                      # devuelve tal cual lo de execute (GATE #5)
   ```

   | Hook | Firma | Base |
   |---|---|---|
   | `load_inputs` | `(self, ctx) -> None` | **No-op.** No escribe en disco. |
   | `validate` | `(self, ctx) -> None` | **Real:** por cada `Artifact` de `self.requires`, comprueba `artifact.exists(ctx)`; si falta ≥1, lanza `FlowContractError` **agregando todos** los ausentes (name + ruta). No escribe en disco. `requires` vacío → pasa trivialmente. |
   | `execute` | `(self, ctx) -> FlowResult` | **Lanza `NotImplementedError`** (el núcleo es específico del flujo; el flujo concreto lo sobreescribe y **construye y devuelve** el `FlowResult`, GATE #5). |
   | `write_outputs` | `(self, ctx, result) -> None` | **No-op.** No escribe en disco. |

   **GATE #5 (ACEPTADO):** el `FlowResult` lo construye `execute()` (el flujo concreto); `run()` lo
   devuelve tal cual (`return result`), fiel a §9. `run()` **no** ensambla el `FlowResult` a partir de
   `produces`.

**Dependencias de librería:** `dataclasses`, `pathlib` — stdlib (R1: Python 3.13+). Importa
`ClientContext` desde `foda.core.context` solo para type hints; **cero** dependencias nuevas. No
importa `yaml` (no lee contenido; `validate` base solo comprueba **existencia**, D-042).

### Flujo trivial de prueba (vive en los tests, no en `src/`)

Los tests definen una o más subclases mínimas de `Flow` (p. ej. `TrivialFlow`) que:
- declaran `name`, `requires` y `produces` con `Artifact`s bajo `tmp_path`;
- sobreescriben **solo** `execute` (construye y devuelve `FlowResult(success=True, outputs=[a.path(ctx) for a in self.produces])`) y `write_outputs` (materializa en disco los artefactos de `produces`);
- opcionalmente instrumentan los hooks (registran en una lista el orden de invocación) para CA-02/CA-03.

El `ClientContext` de los tests se construye con `create_client(NAME, tmp_path/"clients")` (core
CONFORME) + `ClientContext(NAME, tmp_path/"clients")`. Nunca se toca el `clients/` real del repo.

---

## 2. Archivos Afectados

> El código **no** vive en `600_features/`; va en `src/foda/…` y `tests/…`.

| Ruta | Acción | Contenido |
|---|---|---|
| `src/foda/core/flow.py` | crear | `FlowContractError`, `Artifact` (frozen, `path`/`exists`, `ValueError` en base inválida), `FlowResult` (frozen), `Flow` (atributos de contrato + `run` template method + 4 hooks base). Solo `stdlib`. |
| `tests/core/test_flow.py` | crear | Suite unit de `Flow`/`Artifact`/`FlowResult`, con el flujo trivial instrumentado y `ClientContext` construido vía `create_client(...)` bajo `tmp_path`. Independiente de las suites de `scaffold`/`context`. |

**Notas de infraestructura:**
- El andamiaje ya existe (`pyproject.toml`, `src/foda/core/`, `tests/core/`): esta feature **no** crea
  esqueleto nuevo, solo `flow.py` y su test.
- El core `context.py`/`scaffold.py` está CONFORME y **no se toca** (NC-3): los tests lo consumen tal
  cual para preparar el fixture del árbol de cliente.
- `tests/core/` ya existe (convención sin `__init__.py`; `pyproject.toml` usa `pythonpath=["src"]` +
  `testpaths=["tests"]`).

---

## 3. Orden de Trabajo (de lo básico a lo completo)

El bucle TDD consume los casos de la §6 en orden. Secuencia de implementación asociada:

1. **`Artifact` (dato puro, sin `Flow`):** `path(ctx)`/`exists(ctx)` para una clave base; luego la
   equivalencia con las seis claves lógicas (`ctx.<x>_dir / relative`). (Casos 1–2.)
2. **Ciclo feliz de `run`:** subclase trivial hereda `run` y llega al final devolviendo un
   `FlowResult`; luego el orden exacto de los 4 hooks; luego `success == True` y `outputs` presentes
   en disco. (Casos 3–6.)
3. **Bordes de la plantilla:** `requires` vacío pasa `validate` y completa las 4 fases; `execute` sin
   override → `NotImplementedError`. (Casos 7–8.)
4. **Caminos de error de contrato (`validate`):** `require` faltante → `FlowContractError` en
   `validate` antes de `execute`; tipo propio capturable + mensaje que nombra el faltante; secuencia
   de hooks que corta tras `validate`; sin salida espuria en disco; varios faltantes agregados en el
   mensaje. (Casos 9–13.)
5. **Refactor final** de la suite manteniendo verde.

> Nota (D-037): algunos casos parten de un objeto ya construido; el rojo artificial no aporta cuando
> el comportamiento es trivial una vez existe la clase. El bucle decidirá "verde directo" caso a caso.
> Aquí solo se enumeran los casos.

---

## 4. Dependencias y Contratos

- **Consume (en `src/`, solo type hints):** `foda.core.context.ClientContext` (T-014, CONFORME). En
  runtime, `Artifact.path(ctx)` usa sus propiedades públicas de ruta (`inputs_dir`, `outputs_dir`,
  `bronze_dir`, `silver_dir`, `gold_dir`, `models_dir`). `flow_base` **no** conoce la estructura
  interna de `clients/<NAME>/` (HU-05, estrella polar).
- **Consume (solo en tests, como fixture):** `foda.core.scaffold.create_client(name, clients_root) ->
  Path` (feature `client_scaffold`, CONFORME), que materializa el árbol §7 bajo `tmp_path`.
- **Produce:** el módulo `src/foda/core/flow.py` que expone `Flow`, `Artifact`, `FlowResult`,
  `FlowContractError`. No escribe nada en `clients/` por sí mismo (es una abstracción).
- **Contrato de errores:** `FlowContractError` (require ausente — excepción de dominio propia,
  testeable con `pytest.raises(FlowContractError)`; DS-FLOW-1). `NotImplementedError` (execute base
  sin override; DS-FLOW-4). `ValueError` (base de `Artifact` desconocida; DS-FLOW-2).
- **Restricciones respetadas:** R1 (Python 3.13+, solo stdlib), D-042 (sin JSON Schema/Pydantic;
  `validate` base solo comprueba existencia), NC-3 (no se toca `context.py`/`scaffold.py`), GATE #5
  (`execute` construye el `FlowResult`), GATE #6 (orden `load_inputs → validate → execute →
  write_outputs`).

---

## 5. Tareas (atómicas y trazables)

> Cada tarea es **atómica** y respeta las reglas de partición: **un solo responsable**, **un solo
> entregable**, y **código y test en tareas separadas**. **Estado** inicial `no_implementada`
> (valores: `no_implementada` | `implementada` | `cancelada_suspendida`); el **responsable de cada
> tarea es su único escritor de estado** (`D-021`). Trazabilidad → `CA-xx` de la spec.

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Crear `src/foda/core/flow.py` con el dataclass congelado `Artifact(name, base, relative)`: `path(ctx)` mapea `base` (clave lógica ∈ {inputs, outputs, bronze, silver, gold, models}) a la propiedad de ruta de `ctx` y devuelve `<dir base>/relative` (o `ValueError` si `base` es desconocida); `exists(ctx)` = `path(ctx).exists()`. | `flow.py` (`Artifact`) | tdd_coder | no_implementada | CA-09, CA-10 |
| TSK-02 | Añadir el dataclass congelado `FlowResult(success: bool, outputs: list[Path])`. | `flow.py` (`FlowResult`) | tdd_coder | no_implementada | CA-07, CA-08 |
| TSK-03 | Añadir la excepción de dominio `FlowContractError(Exception)` con docstring de contrato. | `flow.py` (`FlowContractError`) | tdd_coder | no_implementada | CA-04, CA-05, CA-13 |
| TSK-04 | Añadir la clase `Flow` con atributos de contrato (`name=""`, `requires=[]`, `produces=[]`), el template method `run(ctx)` en orden fijo `load_inputs → validate → execute → write_outputs` (devuelve el `FlowResult` de `execute`), y los hooks base `load_inputs` (no-op), `execute` (`NotImplementedError`), `write_outputs` (no-op). `validate` queda como placeholder no-op en esta tarea. | `flow.py` (`Flow` esqueleto + `run` + 3 hooks) | tdd_coder | no_implementada | CA-01, CA-02, CA-07, CA-08, CA-11, CA-12 |
| TSK-05 | Implementar el comportamiento base de `Flow.validate(ctx)`: por cada `Artifact` de `self.requires`, comprobar `artifact.exists(ctx)`; si falta ≥1, lanzar `FlowContractError` cuyo mensaje **agrega** todos los ausentes (name + ruta resuelta); no escribir en disco; `requires` vacío pasa trivialmente. | `flow.py` (`Flow.validate`) | tdd_coder | no_implementada | CA-03, CA-04, CA-05, CA-06, CA-13 |
| TSK-06 | Escribir el test de `Artifact.path(ctx)` para una clave base = `ctx.<base>_dir / relative` y `Artifact.exists(ctx)` = existencia en disco de esa ruta. | test `Artifact` path/exists (caso 1) | tdd_tester | no_implementada | CA-10 |
| TSK-07 | Escribir el test de que `Artifact(base=k, relative=r).path(ctx)` coincide con `ctx.<k>_dir / r` para las seis claves base (`inputs/outputs/bronze/silver/gold/models`), resolviendo solo vía `ctx`. | test `Artifact` seis claves (caso 2) | tdd_tester | no_implementada | CA-09 |
| TSK-08 | Escribir el test de que una subclase trivial de `Flow` (solo `name`/`requires`/`produces` + override de `execute`/`write_outputs`, sin sobreescribir `run`) ejecuta `run(ctx)` hasta el final y devuelve un `FlowResult`. | test `run` heredado (caso 3) | tdd_tester | no_implementada | CA-01 |
| TSK-09 | Escribir el test que, instrumentando los hooks del flujo trivial, verifica que `run(ctx)` invoca `load_inputs`, `validate`, `execute`, `write_outputs` **en ese orden** y **una vez** cada uno. | test orden de hooks (caso 4) | tdd_tester | no_implementada | CA-02 |
| TSK-10 | Escribir el test de que, tras un `run(ctx)` exitoso, `FlowResult.success == True`. | test `success` (caso 5) | tdd_tester | no_implementada | CA-07 |
| TSK-11 | Escribir el test de que `FlowResult.outputs` contiene las rutas resueltas de `produces` y cada una **existe** en disco tras `run(ctx)`. | test `outputs` en disco (caso 6) | tdd_tester | no_implementada | CA-08 |
| TSK-12 | Escribir el test de que un `Flow` con `requires` vacío pasa `validate(ctx)` sin excepción y `run(ctx)` completa las 4 fases devolviendo un `FlowResult`. | test `requires` vacío (caso 7) | tdd_tester | no_implementada | CA-12 |
| TSK-13 | Escribir el test de que una subclase que **no** sobreescribe `execute` provoca `NotImplementedError` al ejecutar `run(ctx)`. | test `execute` no implementado (caso 8) | tdd_tester | no_implementada | CA-11 |
| TSK-14 | Escribir el test de que, con un `Artifact` de `requires` inexistente en disco, `run(ctx)` lanza `FlowContractError` y el fallo ocurre en `validate` (antes de `execute`). | test `require` faltante (caso 9) | tdd_tester | no_implementada | CA-04 |
| TSK-15 | Escribir el test de que `FlowContractError` es tipo propio de `flow.py` (subclase de `Exception`), capturable con `pytest.raises(FlowContractError)`, y su mensaje nombra el artefacto faltante (name y/o ruta). | test tipo + mensaje del error (caso 10) | tdd_tester | no_implementada | CA-05 |
| TSK-16 | Escribir el test que, instrumentando los hooks, verifica que ante un `require` faltante la secuencia registrada es `load_inputs`, `validate` y se detiene: `execute` y `write_outputs` **no** se invocan. | test corte de secuencia (caso 11) | tdd_tester | no_implementada | CA-03 |
| TSK-17 | Escribir el test de que, tras un `run(ctx)` que falla por `require` faltante, el/los artefacto(s) de `produces` **no** existen en disco (sin salida espuria). | test sin salida espuria (caso 12) | tdd_tester | no_implementada | CA-06 |
| TSK-18 | Escribir el test de que, con varios `requires` de los cuales más de uno no existe, `run(ctx)` lanza `FlowContractError` cuyo mensaje identifica **todos** los faltantes (agrega, no solo el primero). | test agregación de faltantes (caso 13) | tdd_tester | no_implementada | CA-13 |
| TSK-20 | Escribir el test de que `Artifact(base=<clave desconocida>, relative=r).path(ctx)` lanza `ValueError` (guarda defensiva de `base` no ∈ {inputs, outputs, bronze, silver, gold, models}). Verde directo contra el código ya presente en TSK-01. | test `base` inválida → `ValueError` (caso 14) | tdd_tester | no_implementada | DS-FLOW-2 |
| TSK-19 | Refactor: consolidar/limpiar la suite (factorizar el fixture `ClientContext` creado con `create_client`, el flujo trivial y el instrumentado; parametrizar las seis claves base) manteniendo todo verde. | Refactor (sin cambio de comportamiento) | tdd_refactor | no_implementada | CA-01…CA-13, DS-FLOW-2 |

---

## 6. Casos de Test (lista ordenada para el bucle TDD)

Cada caso es una afirmación verificable atómica sobre `Artifact`/`Flow`/`FlowResult`, construida sobre
un `ClientContext` materializado con `create_client(...)` bajo un `tmp_path`. Orden: fundamental →
complejo. Trazabilidad a los `CA-xx` de la spec entre paréntesis. Deben coincidir con
`stages.tdd.cases[]` de `state.json`. Cada caso = **un** test que falla primero.

1. `Artifact(name="a", base="outputs", relative=r).path(ctx) == ctx.outputs_dir / r`, y `Artifact.exists(ctx)` devuelve `True/False` según exista esa ruta en disco. (CA-10)
2. Para las **seis** claves base (`inputs/outputs/bronze/silver/gold/models`), `Artifact(base=k, relative=r).path(ctx) == ctx.<k>_dir / r`; la ruta se resuelve **solo** vía `ctx`, sin cálculo propio. (CA-09)
3. Una subclase trivial de `Flow` (define `name`/`requires`/`produces` y sobreescribe solo `execute` y `write_outputs`, **sin** sobreescribir `run`) ejecuta el `run(ctx)` heredado hasta el final y devuelve un `FlowResult`. (CA-01)
4. Instrumentando el flujo trivial, `run(ctx)` invoca exactamente `load_inputs`, `validate`, `execute`, `write_outputs`, **en ese orden** y **una vez** cada uno. (CA-02)
5. Tras un `run(ctx)` exitoso sobre el flujo trivial, el `FlowResult` devuelto tiene `success == True`. (CA-07)
6. Tras un `run(ctx)` exitoso, `FlowResult.outputs` expone la(s) ruta(s) resuelta(s) de `produces`, y cada una **existe** en disco. (CA-08)
7. Un `Flow` con `requires` vacío pasa `validate(ctx)` sin lanzar y `run(ctx)` completa las 4 fases devolviendo un `FlowResult`. (CA-12)
8. Una subclase de `Flow` que **no** sobreescribe `execute` provoca `NotImplementedError` al ejecutar `run(ctx)`. (CA-11)
9. Si un `Artifact` de `requires` no existe en disco (ruta resuelta vía `ctx`), `run(ctx)` lanza `FlowContractError`, y el fallo ocurre en `validate` (antes de `execute`). (CA-04)
10. `FlowContractError` es un tipo propio definido en `src/foda/core/flow.py` (subclase de `Exception`), capturable con `pytest.raises(FlowContractError)`, y su mensaje nombra el artefacto requerido faltante (su `name` y/o ruta resuelta). (CA-05)
11. Instrumentando los hooks, ante un `require` faltante la secuencia registrada es `load_inputs`, `validate` y se detiene: `execute` y `write_outputs` **no** se invocan. (CA-03)
12. Tras un `run(ctx)` que falla por `require` faltante, el/los artefacto(s) de `produces` **no** existen en disco (no se escribió salida espuria; `write_outputs` no se ejecutó). (CA-06)
13. Con varios `requires` de los cuales más de uno no existe en disco, `run(ctx)` lanza `FlowContractError` cuyo mensaje identifica **todos** los faltantes (agrega los ausentes, no solo el primero). (CA-13)
14. `Artifact(base=<clave desconocida>, relative=r).path(ctx)` lanza `ValueError` cuando `base` no ∈ {inputs, outputs, bronze, silver, gold, models} (guarda defensiva de DS-FLOW-2: error de programación del autor del flujo). (DS-FLOW-2 — sin `CA-xx` propio; añadido por el humano en el GATE.)

### Mapa caso → tareas (`TSK-xx`)
Cada caso agrupa su tarea-test y su(s) tarea(s)-código (el bucle corre por caso; las tareas son la
capa de trazabilidad).

| Caso | CA | Tarea-test | Tarea(s)-código |
|---|---|---|---|
| 1 | CA-10 | TSK-06 | TSK-01 |
| 2 | CA-09 | TSK-07 | TSK-01 |
| 3 | CA-01 | TSK-08 | TSK-04 |
| 4 | CA-02 | TSK-09 | TSK-04 |
| 5 | CA-07 | TSK-10 | TSK-02, TSK-04 |
| 6 | CA-08 | TSK-11 | TSK-02, TSK-04 |
| 7 | CA-12 | TSK-12 | TSK-04, TSK-05 |
| 8 | CA-11 | TSK-13 | TSK-04 |
| 9 | CA-04 | TSK-14 | TSK-03, TSK-05 |
| 10 | CA-05 | TSK-15 | TSK-03, TSK-05 |
| 11 | CA-03 | TSK-16 | TSK-05 |
| 12 | CA-06 | TSK-17 | TSK-05 |
| 13 | CA-13 | TSK-18 | TSK-03, TSK-05 |
| 14 | DS-FLOW-2 | TSK-20 | TSK-01 |
| (toda la suite) | CA-01…CA-13, DS-FLOW-2 | TSK-19 (refactor) | — |

### Cobertura CA → caso (los 13 CA quedan cubiertos)

| CA | Caso | CA | Caso |
|---|---|---|---|
| CA-01 | 3 | CA-08 | 6 |
| CA-02 | 4 | CA-09 | 2 |
| CA-03 | 11 | CA-10 | 1 |
| CA-04 | 9 | CA-11 | 8 |
| CA-05 | 10 | CA-12 | 7 |
| CA-06 | 12 | CA-13 | 13 |
| CA-07 | 5 | DS-FLOW-2 | 14 |

---

## 7. Estrategia de Test

- **Unit** en `tests/core/test_flow.py`, ejercitando `Artifact`/`Flow`/`FlowResult` en proceso (sin
  `subprocess`): rápido y determinista.
- **Fixture del contexto:** cada test materializa el cliente con `create_client(NAME,
  tmp_path/"clients")` (core CONFORME) y construye `ClientContext(NAME, tmp_path/"clients")`. Nunca se
  toca el `clients/` real del repo. El fixture se factoriza en el refactor final (TSK-19).
- **Flujo trivial de prueba (definido en el test):** subclase de `Flow` con `execute` que construye y
  devuelve `FlowResult(success=True, outputs=[a.path(ctx) for a in self.produces])` y `write_outputs`
  que materializa cada `produces` en disco (p. ej. `p.path(ctx).write_text("ok")`, creando el padre si
  falta). Un `require` "presente" se materializa creando su archivo bajo `tmp_path` antes del `run`.
- **Flujo instrumentado (casos 4, 11):** subclase que registra en una lista de instancia el nombre de
  cada hook invocado, para asertar orden y corte de secuencia.
- **Casos de error (9, 10, 13):** `pytest.raises(FlowContractError)` con `requires` cuyos `Artifact`
  no existen en disco; en el caso 10 se inspecciona el mensaje (name/ruta del faltante) y en el 13 se
  verifica que **todos** los faltantes aparecen.
- **`execute` no implementado (caso 8):** subclase que hereda `execute` base y no lo sobreescribe;
  `pytest.raises(NotImplementedError)`.
- **Sin salida espuria (caso 12):** declarar `produces` bajo `tmp_path`, provocar el fallo por
  `require` faltante y asertar `not produce.path(ctx).exists()` para cada producido.
- **`base` inválida (guarda DS-FLOW-2, caso 14):** no tiene `CA-xx` propio en la spec, pero el humano
  lo **aprobó explícitamente en el GATE** como caso del bucle (caso 14). `pytest.raises(ValueError)`
  al llamar `Artifact(base=<clave desconocida>).path(ctx)`; el comportamiento ya está en el código de
  TSK-01, por lo que el caso 14 se resolverá como "verde directo" (D-037).
- **Integración:** el ejercicio *end-to-end* `Flow` ⇄ `ClientContext` (tracer bullet completo) lo
  refuerza `integration_tester` tras el bucle unit; esta suite unit ya cubre la integración mínima al
  construir el `ctx` con el core real.
- **Fixtures / datos de prueba:** ninguno externo; todo se deriva de `tmp_path` y de los nombres de la
  spec.

---

## 8. Notas y Riesgos (NC-1 / NC-6)

- **Sin puntos abiertos que bloqueen el GATE:** las 6 decisiones de la spec (DS-FLOW-1 excepción
  propia; DS-FLOW-2 `Artifact` con clave lógica + `ValueError`; DS-FLOW-3 `FlowResult` mínimo;
  DS-FLOW-4 hooks base + `run` template no sobreescribible; GATE #5 `execute` construye el
  `FlowResult`; GATE #6 orden `load_inputs → validate → execute → write_outputs`) fueron **aprobadas
  por el humano** junto con la spec. Este plan las implementa sin reabrirlas.
- **Guarda `base` inválida (caso 14):** el humano la **añadió en el GATE** como caso 14 del bucle
  (traza a DS-FLOW-2, sin `CA-xx` propio). El código ya está en TSK-01; el test es TSK-20 (verde
  directo, D-037).
- **`write_outputs` transaccional** y **inconsistencias como estado suave** (`FlowResult.messages`):
  fuera de esta banda, diferidos a `stab_1` (sin consumidor; NC-2), como fija la spec.
- **`requires` multi-flujo complejo:** el mecanismo lo soporta; esta banda solo lo ejercita al mínimo
  (caso 13, dos faltantes). Se endurecerá con el primer flujo real (`stab_1`).
- **Alcance de test de esta feature:** solo `Flow`/`Artifact`/`FlowResult`; el core `create_client` y
  `ClientContext` ya tienen sus suites verdes y no se re-testean aquí (se usan como fixture, NC-3).
