# Spec — flow_base

> Artefacto de la etapa 2 (`spec_writer`). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables **codificados (`CA-xx`) y enlazados a las historias de usuario (`HU-xx`)** de `definition.md`. **Requiere aprobación humana** (gate) antes de planear.
>
> Banda: `tracer_bullet`. Fuentes canónicas: `600_features/flow_base/tracer_bullet/definition.md`, `600_features/flow_base/feature_contract.md`, `600_features/client_context/tracer_bullet/spec.md` (patrón de spec del core y `ClientContext` ya construido), `700_architecture/system_design.md` (§4, §7, §8, §9), `800_persistence/decisions.md` (D-016, D-031, D-042). Código reutilizado: `src/foda/core/context.py` (`ClientContext`, T-014, CONFORME).

## Resumen
Clase base `Flow` (en `src/foda/core/flow.py`) que fija — **una sola vez, para todos los flujos** — el ciclo de vida `run(ctx) = load_inputs → validate → execute → write_outputs` en orden fijo, con `validate()` base que comprueba la **existencia en disco** de los artefactos declarados en `requires` (rutas resueltas vía `ClientContext`, T-014) y falla temprano con `FlowContractError` si falta alguno, devolviendo un `FlowResult` (éxito + rutas de artefactos producidos); acompañada de los descriptores mínimos `Artifact` (declarativo, resuelve su ruta vía `ctx`) y `FlowResult`.

---

## Decisiones formalizadas por spec_writer

La `definition.md` delegó explícitamente a esta etapa cuatro supuestos abiertos (los tres "puntos de confirmación para el GATE" + la forma de resolver la ruta de un `Artifact`). Se resuelven aquí con su razonamiento (NC-1/NC-2/NC-6); todos quedan listados abajo como **puntos del GATE humano** y no se asumen en silencio.

### DS-FLOW-1 — Excepción de contrato para "artefacto requerido ausente"
- **Decisión:** una excepción propia **`FlowContractError(Exception)`**, definida en `src/foda/core/flow.py`. `validate()` la lanza cuando algún artefacto de `requires` no existe en disco (ruta resuelta vía `ctx`), **antes** de `execute()`.
- **Razón:**
  - A diferencia de `client_context` (donde se eligió `FileNotFoundError` estándar por **no haber consumidor** que necesitara distinguir el error, DS-CTX-1), aquí **sí hay consumidor previsible**: el orquestador (`foda run`, feature futura) y los flujos concretos necesitarán **capturar específicamente** una violación de contrato para "informar al DS" (§9: *"si falta un artefacto requerido, el flujo falla temprano y con mensaje claro… informa al DS"*), distinguiéndola de otros `OSError`/`FileNotFoundError` incidentales. Un tipo de dominio hace ese `except` claro y estable (P8, observabilidad).
  - Semánticamente no es "un archivo no se encontró" a bajo nivel: es que **el flujo declaró** que necesita ese artefacto y el contrato se violó. `FlowContractError` nombra ese concepto de dominio (§8, §9).
  - Es la excepción nombrada como ejemplo tanto en `definition.md` (HU-03) como en `feature_contract.md`.
- **Alternativa descartada (NC-2):** reutilizar `FileNotFoundError`. Descartada porque acoplaría la violación de contrato del flujo a un error de E/S genérico y obligaría al orquestador a inspeccionar el mensaje para distinguir "contrato violado" de "un archivo del sistema faltó por otra causa". `FlowContractError` es testeable con `pytest.raises(FlowContractError)` y no impide capturarla como `Exception`.
- **Forma:** subclase directa de `Exception` (sin jerarquía propia de errores del core todavía: no hay un segundo tipo de error de flujo que justifique una base común, NC-2). El mensaje nombra el/los artefacto(s) faltante(s) (su `name` y su ruta resuelta) para diagnóstico.

### DS-FLOW-2 — Descriptor `Artifact` y resolución de su ruta vía `ctx`
- **Decisión:** un **dataclass congelado declarativo** `Artifact(name: str, base: str, relative: str)` con dos métodos de resolución:
  - `path(ctx: ClientContext) -> Path` → `<directorio base de ctx> / relative`.
  - `exists(ctx: ClientContext) -> bool` → `self.path(ctx).exists()`.
  - `base` es una **clave lógica** de una de las carpetas que `ClientContext` ya expone: `"inputs"`, `"outputs"`, `"bronze"`, `"silver"`, `"gold"`, `"models"` (mapeadas internamente a `ctx.inputs_dir`, `ctx.outputs_dir`, `ctx.bronze_dir`, `ctx.silver_dir`, `ctx.gold_dir`, `ctx.models_dir`).
  - `relative` es la ruta relativa dentro de esa carpeta base (p. ej. `"010_discovery/contract_data.json"`, §7).
- **Razón:**
  - Es **declarativo (datos puros)**, no un `lambda`/callable opaco: tiene `repr` legible, es comparable e inspeccionable, y su identidad (`name`) sirve para mensajes de error y para `FlowResult`. Cumple "descriptor mínimo y declarativo" de la `definition.md`.
  - La clave `base` obliga al `Artifact` a nombrar una **carpeta lógica** (§7/§8) y delega la ruta física en `ClientContext` (T-014): `flow_base` **no** reimplementa resolución de rutas ni conoce que `bronze` vive bajo `data/` (HU-05, Estrella Polar).
  - Sin JSON Schema/Pydantic (D-042, mismo criterio que `client_context`): el descriptor no valida contenido ni esquema, solo resuelve ruta y comprueba existencia.
- **Alternativa descartada (NC-2):** `Artifact(name, path_fn: Callable[[ClientContext], Path])`. Aunque es el mínimo absoluto de código, un callable **no es declarativo** (opaco, no comparable, sin `repr` útil) y contradice el requisito de descriptor "declarativo" de la `definition.md`. El dataclass con clave lógica es apenas más código y mucho más inspeccionable/testeable.
- **Guarda:** si `base` no es una de las seis claves conocidas, `path(ctx)` lanza `ValueError` (error de programación del autor del flujo, no de datos del cliente). Es una guarda defensiva mínima, no una historia de usuario.

### DS-FLOW-3 — Forma de `FlowResult`
- **Decisión:** un **dataclass congelado** `FlowResult(success: bool, outputs: list[Path])`:
  - `success: bool` — estado de la ejecución (`True` = éxito).
  - `outputs: list[Path]` — rutas resueltas de los artefactos producidos (declarados en `produces`), verificables en disco tras `run()`.
- **Razón:** es la superficie mínima que satisface HU-04 (estado + rutas de artefactos generados) y el criterio de feature 5. `success` cubre el eje "éxito/inconsistencias" en su forma binaria; las **inconsistencias como estado suave** (fallos no-excepcionales con lista de mensajes) **se difieren** a `stab_1`, cuando un flujo concreto las necesite (hoy la única "inconsistencia" ejercitada — `require` faltante — se modela como excepción `FlowContractError`, no como `FlowResult`, DS-FLOW-1). No se añade un campo `messages`/`inconsistencies` sin consumidor (NC-2).
- **Alternativa considerada:** incluir ya un campo de inconsistencias/mensajes. Diferida por no tener consumidor en esta banda (NC-2, mismo criterio D-042 de no construir superficie anticipada).

### DS-FLOW-4 — Template method `run` y firmas de los 4 hooks
- **Decisión:** `run(ctx)` es el **template method** (no sobreescribible por los flujos) que invoca los 4 hooks en orden fijo; los flujos concretos sobreescriben **solo** los hooks:

  ```python
  def run(self, ctx: ClientContext) -> FlowResult:
      self.load_inputs(ctx)              # 1
      self.validate(ctx)                 # 2  (puede lanzar FlowContractError)
      result = self.execute(ctx)         # 3
      self.write_outputs(ctx, result)    # 4
      return result
  ```

  | Hook | Firma | Responsabilidad base | Sobreescritura típica |
  |---|---|---|---|
  | `load_inputs` | `(self, ctx) -> None` | **No-op.** No escribe en disco. | Leer YAML (`010_inputs`) + JSON upstream (`020_outputs`) a estado de la instancia. |
  | `validate` | `(self, ctx) -> None` | **Comportamiento real:** para cada `Artifact` de `self.requires`, comprueba `artifact.exists(ctx)`; si alguno falta, lanza `FlowContractError` nombrándolo(s). No escribe en disco. | Ampliar con validación de contenido/esquema (diferido por flujo, D-042). |
  | `execute` | `(self, ctx) -> FlowResult` | **Lanza `NotImplementedError`** (el núcleo es específico del flujo). | Ejecutar el núcleo determinista y devolver un `FlowResult` (con `outputs = [a.path(ctx) for a in self.produces]`). |
  | `write_outputs` | `(self, ctx, result) -> None` | **No-op.** | Persistir en disco los artefactos declarados en `produces` (JSON `020_outputs` y/o datasets `data/`). |

- **Atributos de contrato:** `Flow` expone `name: str`, `requires: list[Artifact]`, `produces: list[Artifact]` con **valores base vacíos** (`name = ""`, `requires = []`, `produces = []`), de modo que un flujo que no declare `requires` pasa `validate()` trivialmente. El mecanismo exacto de asignación (atributos de clase en la subclase vs. `__init__`) es detalle de implementación de `plan_builder`; el contrato observable es que estos tres atributos existen y `validate()` los consume.
- **Quién construye el `FlowResult`:** lo construye `execute()` (el flujo concreto) y `run()` lo devuelve tal cual, fiel a §9 (`result = execute(ctx); write_outputs(ctx, result); return result`). Se documenta como **punto del GATE** por si se prefiere que `run()` ensamble el `FlowResult` a partir de `produces` (ver GATE #5).
- **Razón:** honra literalmente §9 (mismo orden, mismos 4 hooks, `run` devuelve el resultado de `execute`). Mantiene `run` como plantilla pura sin lógica de negocio (HU-02) y deja que el flujo concreto solo aporte sus hooks (HU-01). El orden `load_inputs → validate` (validar **después** de cargar) es el de §9: en un fallo de `require`, `load_inputs` **ya se ejecutó** (no escribe nada), pero `execute` y `write_outputs` **no** (HU-03).

---

## Contratos de Datos / Artefactos

`flow_base` no consume ni produce artefactos de cliente por sí mismo (es una **abstracción**, no un flujo concreto). El "contrato" que fija es el mecanismo por el que los flujos concretos declararán y validarán sus artefactos. Para el **tracer bullet** (flujo trivial definido en los tests) el contrato ejercitado es:

| Dirección | Artefacto (ejemplo tracer bullet) | Formato | Esquema / campos |
|---|---|---|---|
| requiere | `Artifact(name="input", base="inputs", relative="<flujo>/<archivo>")` → resuelto vía `ctx` bajo `010_inputs/` | archivo (marcador) | Solo se comprueba **existencia** en disco (no contenido, D-042). |
| produce | `Artifact(name="output", base="outputs", relative="<flujo>/<archivo>.json")` → resuelto vía `ctx` bajo `020_outputs/` | archivo | `write_outputs()` del flujo trivial lo materializa; su ruta se reporta en `FlowResult.outputs`. |
| produce (módulo) | `src/foda/core/flow.py` | módulo Python | Expone `Flow`, `Artifact`, `FlowResult`, `FlowContractError`. No escribe nada en `clients/` por sí mismo. |

> Alineado con §8 (cada flujo declara `requires`/`produces`) y §7 (carpetas lógicas). La resolución física de cada ruta es responsabilidad de `ClientContext` (T-014), no de `flow_base`.

---

## Comportamiento Esperado

Ejecución de `flow.run(ctx)` sobre un `Flow` concreto:

1. **`load_inputs(ctx)`** (fase 1). Base: no-op. Se invoca **siempre primero**, incluso si luego `validate` fallará. No escribe en disco.
2. **`validate(ctx)`** (fase 2). Base: por cada `Artifact` en `self.requires`, evalúa `artifact.exists(ctx)` (ruta resuelta vía `ctx`). 
   - Si **todos** existen → continúa.
   - Si **falta uno o más** → lanza `FlowContractError` cuyo mensaje nombra el/los artefacto(s) faltante(s) (`name` + ruta resuelta). No se invoca `execute` ni `write_outputs`. No se escribe nada en disco.
   - Si `requires` está vacío → pasa trivialmente.
3. **`execute(ctx)`** (fase 3). Base: lanza `NotImplementedError` (debe sobreescribirse). El flujo concreto ejecuta su núcleo y devuelve un `FlowResult(success=..., outputs=[...])`.
4. **`write_outputs(ctx, result)`** (fase 4). Base: no-op. El flujo concreto persiste en disco los artefactos de `produces`.
5. **`run` devuelve** el `FlowResult` producido por `execute`.

Notas de comportamiento:
- El **orden de las 4 fases es fijo e invariable**; `run` no es sobreescribible en el contrato (los flujos solo aportan hooks).
- `validate` y `load_inputs` base **no escriben** en el filesystem: ante un `require` faltante no queda estado espurio en disco (feature CA-3).
- `flow_base` resuelve rutas **exclusivamente** a través del `ClientContext` recibido (vía `Artifact.path(ctx)`); no reimplementa lógica de rutas (HU-05).

---

## Casos Límite y Errores

| Caso | Contexto | Resultado esperado |
|---|---|---|
| `require` faltante (uno) | un `Artifact` de `requires` no existe en disco | `FlowContractError` en `validate`, **antes** de `execute`; `execute` y `write_outputs` no se invocan; nada escrito. |
| `require` faltante (varios) | ≥2 `Artifact` de `requires` no existen | `FlowContractError`; el mensaje identifica los artefactos faltantes (agrega los ausentes). |
| `requires` vacío | flujo sin artefactos requeridos | `validate` pasa; `run` completa las 4 fases. |
| `execute` no sobreescrito | subclase de `Flow` sin override de `execute` | `NotImplementedError` al llegar a la fase 3 (el núcleo es específico del flujo). |
| `produces` no escrito por base | flujo que no sobreescribe `write_outputs` | Base es no-op: no se crea el artefacto; garantizar su existencia es responsabilidad del flujo concreto (no es error de `flow_base`). |
| `Artifact.base` inválido | `base` no ∈ {inputs, outputs, bronze, silver, gold, models} | `ValueError` en `Artifact.path(ctx)` (error de programación del autor del flujo). |
| `run` exitoso | flujo trivial con `require` presente y `execute`/`write_outputs` definidos | Devuelve `FlowResult(success=True, outputs=[...])`; los artefactos de `produces` existen en disco. |

**Limitaciones conocidas (banda `tracer_bullet`, documentadas):**
- **`write_outputs` transaccional:** si en el futuro se escriben múltiples artefactos y se requiere "todo o nada", esta banda no lo cubre (riesgo ya anotado en `definition.md`); el tracer bullet escribe un único artefacto simple.
- **`requires` multi-flujo complejo:** el mecanismo soporta `requires` con artefactos de varias carpetas/flujos, pero esta banda solo lo ejercita al mínimo necesario (se endurecerá con el primer flujo real, `stab_1`).
- **Validación de contenido/esquema:** fuera de alcance (D-042); `validate` base solo comprueba **existencia**.

---

## Interfaces / Firmas Públicas

```python
# src/foda/core/flow.py
from dataclasses import dataclass, field
from pathlib import Path

from foda.core.context import ClientContext


class FlowContractError(Exception):
    """Se lanza cuando un artefacto declarado en `requires` no existe en disco
    (violación del contrato de entrada del flujo), antes de execute()."""


@dataclass(frozen=True)
class Artifact:
    """Descriptor declarativo mínimo de un artefacto de flujo.

    Resuelve su ruta física a través de ClientContext (no reimplementa rutas).
    base ∈ {"inputs","outputs","bronze","silver","gold","models"} (carpetas §7).
    """
    name: str
    base: str
    relative: str

    def path(self, ctx: ClientContext) -> Path:
        """Ruta absoluta = <directorio base de ctx> / relative.
        Lanza ValueError si base no es una clave lógica conocida."""

    def exists(self, ctx: ClientContext) -> bool:
        """True si self.path(ctx) existe en disco."""


@dataclass(frozen=True)
class FlowResult:
    """Estado de una ejecución de flujo + rutas de artefactos producidos."""
    success: bool
    outputs: list[Path]


class Flow:
    """Abstracción común de un flujo (system_design §9).

    Template method run() invoca load_inputs → validate → execute → write_outputs
    en orden fijo. Los flujos concretos heredan y sobreescriben SOLO los 4 hooks.
    """
    name: str = ""
    requires: list[Artifact] = []       # vacío por defecto
    produces: list[Artifact] = []       # vacío por defecto

    def run(self, ctx: ClientContext) -> FlowResult:
        self.load_inputs(ctx)
        self.validate(ctx)
        result = self.execute(ctx)
        self.write_outputs(ctx, result)
        return result

    def load_inputs(self, ctx: ClientContext) -> None:
        """Base: no-op. Subclases cargan inputs (YAML/JSON) a su estado."""

    def validate(self, ctx: ClientContext) -> None:
        """Base: verifica que cada Artifact de requires exista en disco (vía ctx);
        lanza FlowContractError (antes de execute) si falta alguno."""

    def execute(self, ctx: ClientContext) -> FlowResult:
        """Base: raise NotImplementedError. Subclases ejecutan el núcleo y
        devuelven un FlowResult."""

    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
        """Base: no-op. Subclases persisten los artefactos de produces."""
```

- **Contrato de errores:** `FlowContractError` (require ausente) — excepción de dominio propia del core, testeable con `pytest.raises`. `NotImplementedError` (execute base sin override). `ValueError` (base de `Artifact` desconocida).
- **Consumo de `ClientContext` (T-014):** `run(ctx: ClientContext)` recibe la instancia ya construida; `Artifact.path(ctx)` usa sus propiedades públicas (`inputs_dir`, `outputs_dir`, `bronze_dir`, `silver_dir`, `gold_dir`, `models_dir`). `flow_base` **no** conoce la estructura interna de `clients/<NAME>/` (Estrella Polar, HU-05).
- **`run` como template method:** el contrato es que los flujos concretos **no** sobreescriben `run`; solo los 4 hooks. La orquestación y la validación mínima no se reimplementan (HU-01).

---

## Criterios de Aceptación (verificables)
> Cada criterio es traducible a uno o más tests sobre `Flow`/`Artifact`/`FlowResult` (usando un `Flow` trivial instrumentado y un `ClientContext` construido con `create_client(...)` bajo `tmp_path`) y traza a la(s) `HU-xx` que satisface. Cumple D-031 (trazabilidad codificada HU→CA).

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | Una subclase trivial de `Flow` que define solo `name`/`requires`/`produces` y sobreescribe únicamente `execute` y `write_outputs` (sin sobreescribir `run`) expone un `run(ctx)` heredado que se ejecuta hasta el final y devuelve un `FlowResult`, sin contener código de orquestación propio. | HU-01 |
| CA-02 | Instrumentando el flujo trivial (registrando cada hook llamado), una ejecución completa de `run(ctx)` invoca exactamente `load_inputs`, `validate`, `execute`, `write_outputs`, **en ese orden** y **una vez** cada uno. | HU-02 |
| CA-03 | Cuando falta un artefacto de `requires`, la secuencia de hooks registrada es `load_inputs`, `validate` y se detiene: `execute` y `write_outputs` **no** se invocan. | HU-02, HU-03 |
| CA-04 | Si un artefacto declarado en `requires` no existe en disco (ruta resuelta vía `ctx`), `run(ctx)` lanza `FlowContractError`, y el fallo ocurre en `validate` (antes de `execute`). | HU-03 |
| CA-05 | `FlowContractError` es un tipo de excepción propio definido en `src/foda/core/flow.py` (subclase de `Exception`), capturable de forma independiente con `pytest.raises(FlowContractError)`, y su mensaje nombra el artefacto requerido faltante (su `name` y/o su ruta resuelta). | HU-03 |
| CA-06 | Tras un `run(ctx)` que falla por `require` faltante, el/los artefacto(s) declarados en `produces` **no** existen en disco (no se escribió salida espuria; `write_outputs` no se ejecutó). | HU-03 |
| CA-07 | Tras un `run(ctx)` exitoso sobre el flujo trivial, el `FlowResult` devuelto tiene `success == True`. | HU-04 |
| CA-08 | El `FlowResult` devuelto por un `run(ctx)` exitoso expone en `outputs` la(s) ruta(s) resuelta(s) del/los artefacto(s) de `produces`, y cada una de esas rutas **existe** en disco tras la ejecución. | HU-04 |
| CA-09 | El flujo trivial resuelve las rutas de sus `requires`/`produces` exclusivamente a través del `ClientContext` recibido: `Artifact(base="outputs", relative=r).path(ctx) == ctx.outputs_dir / r` (y análogamente para las demás claves base), sin calcular ninguna ruta sin `ctx`. | HU-05 |
| CA-10 | `Artifact` es un descriptor declarativo con `name`, `base` (clave lógica ∈ {inputs, outputs, bronze, silver, gold, models}) y `relative`; `Artifact.path(ctx)` devuelve `<directorio base de ctx>/relative` y `Artifact.exists(ctx)` devuelve si esa ruta existe en disco. | HU-05, HU-01 |
| CA-11 | Una subclase de `Flow` que **no** sobreescribe `execute` provoca `NotImplementedError` al ejecutar `run(ctx)` (la base no implementa el núcleo). | HU-01 |
| CA-12 | Un `Flow` con `requires` vacío pasa `validate(ctx)` sin lanzar excepción y `run(ctx)` completa las 4 fases y devuelve un `FlowResult`. | HU-02, HU-01 |
| CA-13 | Con varios `requires` de los cuales más de uno no existe en disco, `run(ctx)` lanza `FlowContractError` y su mensaje identifica los artefactos faltantes (agrega los ausentes, no solo el primero). | HU-03 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` queda cubierta por ≥ 1 `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-10, CA-11, CA-12 |
| HU-02 | CA-02, CA-03, CA-12 |
| HU-03 | CA-03, CA-04, CA-05, CA-06, CA-13 |
| HU-04 | CA-07, CA-08 |
| HU-05 | CA-09, CA-10 |

---

## No-Objetivos
- **Flujos reales concretos** (Discovery, Onboarding, Ingestion, …): cada uno es una feature/tarea futura que hereda de `Flow`. El único flujo de esta banda es el **trivial de prueba**, definido en los tests.
- **Orquestador** (`foda run`, selección nuevo/recurrente, rangos `--from/--to`, §11–§12): otra feature.
- **Esquemas formales de artefactos** (Pydantic/JSON Schema, validación de contenido/estructura): diferido por flujo concreto (D-042). `validate` base solo comprueba **existencia**.
- **Integración con el LLM** (paso opcional dentro de `execute()` en flujos concretos): fuera de alcance.
- **Ampliación de `ClientContext`** (introspección de "qué artefactos existen", etc.): responsabilidad de `client_context`, no de `flow_base` (D-042).
- **`write_outputs` transaccional** e **inconsistencias como estado suave** en `FlowResult` (campo de mensajes): diferidos a `stab_1`, sin consumidor todavía (NC-2).
- **Jerarquía de excepciones del core** más allá de `FlowContractError`: no se crea una base común de errores sin un segundo tipo que la justifique (NC-2).

---

## Puntos de confirmación para el GATE humano
Decisiones tomadas por `spec_writer` (delegadas por la `definition.md`) que el humano valida o ajusta antes de `plan_builder`:
1. **DS-FLOW-1 — excepción de contrato:** ¿se acepta una excepción propia `FlowContractError(Exception)` en `flow.py` (por haber consumidor previsible: orquestador/flujos que la capturan para informar al DS, §9), en lugar de reutilizar `FileNotFoundError` como en `client_context`?
2. **DS-FLOW-2 — descriptor `Artifact`:** ¿se acepta el dataclass declarativo `Artifact(name, base, relative)` con `base` como clave lógica de carpeta (`inputs/outputs/bronze/silver/gold/models`) y `path(ctx)`/`exists(ctx)`, en vez de un callable `path_fn` opaco?
3. **DS-FLOW-3 — `FlowResult`:** ¿se acepta `FlowResult(success: bool, outputs: list[Path])` mínimo, difiriendo un campo de "inconsistencias/mensajes" a `stab_1`?
4. **DS-FLOW-4 — hooks base:** ¿se aceptan las responsabilidades base — `load_inputs`/`write_outputs` no-op, `validate` con comprobación real de existencia, `execute` lanzando `NotImplementedError` — y `run` como template method no sobreescribible?
5. **Quién construye el `FlowResult`:** ¿se acepta que lo construya `execute()` (fiel a §9: `return result`), o se prefiere que `run()` lo ensamble automáticamente a partir de `self.produces` (menos boilerplate por flujo, `outputs` garantizado == `produces` resueltos)?
6. **Orden `load_inputs` antes de `validate`:** ¿se acepta el orden de §9 (cargar y luego validar), con la consecuencia de que ante un `require` faltante `load_inputs` ya se ejecutó — no escribe nada — pero `execute`/`write_outputs` no (CA-03)?
