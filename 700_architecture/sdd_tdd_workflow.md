# SDD/TDD Workflow — Foda_Application

> Documento de arquitectura que describe **cómo funciona la cadena de 8 agentes de desarrollo** (SDD + TDD) como sistema: la máquina de estado `state.json` que gobierna cada feature y la orquestación de las etapas. Es la **fuente única de verdad** de la convención de `state.json` y del encadenamiento; los archivos de cada agente en `.claude/agents/` describen el detalle de *su* etapa y deben ser coherentes con este documento.

**Versión:** 0.1 · **Fecha:** 2026-07-02 · Ver [D-008](../800_persistence/decisions.md).

---

## Índice
1. [Propósito y Distinción de Agentes](#1-propósito-y-distinción-de-agentes)
2. [La Cadena de 8 Agentes](#2-la-cadena-de-8-agentes)
3. [Diagrama de Orquestación](#3-diagrama-de-orquestación)
4. [Gates Humanos](#4-gates-humanos)
5. [El Bucle TDD](#5-el-bucle-tdd)
6. [Convención de `state.json`](#6-convención-de-statejson)
7. [Reglas Transversales](#7-reglas-transversales)
8. [Artefactos por Feature](#8-artefactos-por-feature)
9. [Reanudación y Bloqueos](#9-reanudación-y-bloqueos)

---

## 1. Propósito y Distinción de Agentes

El proyecto distingue dos clases de agentes (ver D-008):

- **Agentes de desarrollo** — *construyen* la aplicación. Son los 8 de esta cadena. Viven en `.claude/agents/`.
- **Agentes de runtime** — *son* la aplicación (Discovery, Exploration, etc.). Se implementan como código en `src/foda/` y no forman parte de esta cadena.

La cadena SDD/TDD aplica **Spec-Driven Development** (definir → especificar → planear, con aprobación humana antes de codificar) seguido de **Test-Driven Development** (rojo → verde → refactor por caso), cerrando con integración y verificación contra la spec.

**Por qué existe `state.json`:** los subagentes de Claude Code **arrancan en frío y son efímeros** (lección L-005): no comparten memoria entre invocaciones. Para que un desarrollo multi-etapa sea **reanudable y auditable**, el estado de cada feature debe persistir **en disco**, no en la conversación. `state.json` es esa máquina de estado.

---

## 2. La Cadena de 8 Agentes

| # | Agente | Modelo | Color | Produce | Gate |
|---|---|---|---|---|---|
| 1 | `feature_definer` | Sonnet | blue | `definition.md` + init `state.json` | — |
| 2 | `spec_writer` | Opus | cyan | `spec.md` | 🚧 humano |
| 3 | `plan_builder` | Opus | purple | `plan.md` + `stages.tdd.cases[]` | 🚧 humano |
| 4 | `tdd_tester` | Sonnet | red | un test que falla (rojo) | — |
| 5 | `tdd_coder` | Sonnet | green | código mínimo (verde) | — |
| 6 | `tdd_refactor` | Sonnet | orange | mejora de diseño (verde total) | — |
| 7 | `integration_tester` | Sonnet | yellow | tests de integración | — |
| 8 | `spec_verifier` | Opus | pink | `verification.md` + cierre | — |

> **Nota de nomenclatura:** D-008 nombró originalmente las etapas 4 y 5 como `tdd_red` y `tdd_green`; se renombraron a **`tdd_tester`** y **`tdd_coder`** al construirlas (T-009, 2026-07-02).

**Modelos:** las etapas de **juicio** (spec, plan, verificación) usan Opus; las de **ejecución mecánica** (bucle TDD, integración, definición) usan Sonnet. La **orquestación** la lleva la sesión principal (Opus).

---

## 3. Diagrama de Orquestación

```
                         (sesión principal = Opus orquesta)

  feature_definer ─▶ spec_writer ──🚧──▶ plan_builder ──🚧──▶ ┌─ bucle TDD ─┐
                     (GATE humano)       (GATE humano)         │             │
                                                               ▼             │
                                                          tdd_tester         │
                                                               │             │
                                                               ▼             │
                                                          tdd_coder          │
                                                               │             │
                                                               ▼             │
                                                          tdd_refactor ──────┘
                                                               │
                          ¿quedan casos pending?  ── sí ──▶ vuelve a tdd_tester
                                                               │
                                                              no
                                                               ▼
                                                     integration_tester
                                                               │
                                                               ▼
                                                        spec_verifier
                                                               │
                                              ┌────────────────┴────────────────┐
                                          CONFORME                        NO CONFORME
                                       feature = done              blocked + etapa de retorno
```

**Encadenamiento:** la sesión principal invoca cada agente vía la herramienta Agent, le entrega en el prompt el **contexto en frío** (nombre de la feature, id de caso cuando aplica, resultado de la etapa previa) y encadena automáticamente la siguiente etapa **excepto** en los gates humanos.

---

## 4. Gates Humanos

Hay **dos gates obligatorios**, ambos antes de escribir código:

1. **Tras `spec_writer`** — el usuario aprueba la **especificación** antes de planear.
2. **Tras `plan_builder`** — el usuario aprueba el **plan y la lista de casos de test** antes de arrancar el bucle TDD.

Protocolo del gate:
- El agente deja su etapa en `status = "done"` pero marca `awaiting_approval = true` y **no** avanza `current_stage` a la siguiente etapa.
- La sesión principal **pausa**, presenta el artefacto al usuario y espera su decisión.
- **OK** → la sesión principal limpia `awaiting_approval` y encadena la siguiente etapa.
- **Cambios** → se re-ejecuta la misma etapa con el feedback.

Ningún agente se auto-aprueba: el juicio humano es el que abre el gate.

---

## 5. El Bucle TDD

El bucle cubre **un caso de test a la vez**, en el orden definido en `stages.tdd.cases[]` (de simple a complejo):

1. **`tdd_tester`** escribe **un** test que falla y confirma el **rojo limpio** (falla por aserción, no por error accidental). No escribe código de producción (salvo esqueleto mínimo importable). Caso → `red`.
2. **`tdd_coder`** escribe el código **mínimo** para pasar ese test sin romper la suite. **Máx. 2 reintentos**; si no logra el verde, marca `blocked` y escala a humano. Caso → `green`.
3. **`tdd_refactor`** mejora el diseño manteniendo **toda la suite en verde**, sin cambiar comportamiento. Caso → `done`.

Al cerrar cada caso, `tdd_refactor` decide:
- **Quedan casos `pending`** → el bucle **vuelve a `tdd_tester`** con el siguiente caso.
- **No quedan** → `stages.tdd.status = "done"` y avanza a `integration_tester`.

El bucle **no tiene gates humanos internos**: fluye automático hasta agotar los casos o bloquearse.

---

## 6. Convención de `state.json`

Un archivo por feature en `600_features/<feature>/state.json`. Es la máquina de estado que todos los agentes leen al arrancar y actualizan al terminar.

### 6.1 Esquema

```json
{
  "feature": "<feature>",              // snake_case, identidad de la feature
  "status": "in_progress",             // estado global de la feature
  "current_stage": "spec_writer",      // etapa actual o siguiente a ejecutar
  "stages": {
    "feature_definer":    { "status": "done",    "artifact": "definition.md" },
    "spec_writer":        { "status": "pending", "artifact": "spec.md",  "gate": "human", "awaiting_approval": false },
    "plan_builder":       { "status": "pending", "artifact": "plan.md",  "gate": "human", "awaiting_approval": false },
    "tdd": {
      "status": "pending",
      "cases": [
        { "id": 1, "desc": "afirmación verificable", "status": "pending" }
      ]
    },
    "integration_tester": { "status": "pending" },
    "spec_verifier":      { "status": "pending", "artifact": "verification.md" }
  }
}
```

### 6.2 Valores de `status`

**A nivel de feature y de etapa:**

| Valor | Significado |
|---|---|
| `pending` | Aún no iniciada. |
| `in_progress` | El agente de esa etapa está trabajando. |
| `done` | Etapa completada satisfactoriamente. |
| `blocked` | Detenida; requiere decisión humana (ver §9). |

**A nivel de caso TDD (`stages.tdd.cases[].status`):**

| Valor | Puesto por | Significado |
|---|---|---|
| `pending` | `plan_builder` | Caso enumerado, aún sin cubrir. |
| `red` | `tdd_tester` | Test escrito y fallando (rojo confirmado). |
| `green` | `tdd_coder` | Código mínimo lo hace pasar. |
| `refactored` | `tdd_refactor` | (opcional) refactor aplicado, previo al cierre. |
| `done` | `tdd_refactor` | Ciclo red→green→refactor completo para el caso. |
| `blocked` | `tdd_coder` | No se logró el verde tras 2 reintentos. |

### 6.3 Quién escribe qué

| Etapa | Lee | Escribe |
|---|---|---|
| `feature_definer` | — | crea el archivo; `feature_definer=done`, `current_stage=spec_writer` |
| `spec_writer` | estado + `definition.md` | `spec_writer=done` + `awaiting_approval=true` (gate) |
| `plan_builder` | estado + `spec.md` | `plan_builder=done` + `awaiting_approval=true` + puebla `tdd.cases[]` |
| `tdd_tester` | estado + spec/plan | caso → `red` |
| `tdd_coder` | estado + test rojo | caso → `green` (o `blocked`) |
| `tdd_refactor` | estado + código | caso → `done`; decide `current_stage` (bucle o `integration_tester`) |
| `integration_tester` | estado + spec/plan | `integration_tester=done`, `current_stage=spec_verifier` |
| `spec_verifier` | estado + spec/def | `spec_verifier=done` + feature `status=done`/`current_stage=completed` (o `blocked`) |

**Reglas de transición clave:**
- Ningún agente avanza `current_stage` a través de un gate: eso lo hace la sesión principal tras la aprobación humana.
- `current_stage` siempre apunta a la etapa **en curso o la siguiente a ejecutar**.
- Un `blocked` en cualquier etapa propaga `status = "blocked"` a nivel de feature.

---

## 7. Reglas Transversales

- **Arranque en frío:** cada agente recibe en el prompt lo que necesita (nombre de la feature, id de caso, resultado previo) y **relee `state.json`** para partir del estado real.
- **Validación del gate previo:** cada agente verifica que la etapa anterior esté `done` (y no `awaiting_approval` cuando aplica) antes de trabajar; si la cadena está fuera de orden, se detiene e informa.
- **Commit por etapa, sin push:** cada agente cierra con `git add` + `git commit` usando prefijo convencional (`feat`/`spec`/`plan`/`test`/`refactor`/`verify`) y `(<feature>)` en el mensaje. **El `push` se hace solo en el cierre de sesión** (D-003).
- **Separación de artefactos:** el código va a `src/foda/…`, los tests a `tests/…`; en `600_features/<feature>/` solo viven los `.md` SDD y `state.json`.
- **Herramientas mínimas:** los 8 agentes usan `Read, Glob, Grep, Write, Edit, Bash` (sin `Agent` ni herramientas web); la orquestación de subagentes la hace la sesión principal.

---

## 8. Artefactos por Feature

Estructura esperada en `600_features/<feature>/` (ver también T-011):

```
600_features/<feature>/
├── definition.md       # feature_definer — qué y por qué
├── spec.md             # spec_writer — comportamiento, contratos, criterios de aceptación
├── plan.md             # plan_builder — cómo + lista de casos de test
├── verification.md     # spec_verifier — veredicto y trazabilidad
└── state.json          # máquina de estado de la cadena
```

El **código y los tests NO viven aquí**: `src/foda/…` y `tests/…` respectivamente.

---

## 9. Reanudación y Bloqueos

**Reanudación:** para retomar una feature interrumpida, la sesión principal lee `state.json`, mira `status` y `current_stage`, y reinvoca el agente correspondiente con el contexto en frío. No se pierde trabajo porque cada etapa quedó commiteada.

**Bloqueos (`blocked`):** ocurren cuando un agente no puede avanzar sin decisión humana:
- `tdd_coder` no logra el verde en 2 reintentos → posible defecto de spec/plan.
- `integration_tester` halla un fallo que exige cambiar spec/contrato o toca otro flujo.
- `spec_verifier` emite **NO CONFORME**.

En todos los casos el agente marca `blocked`, deja diagnóstico y **etapa de retorno recomendada** (`spec_writer`, `plan_builder`, bucle TDD o `integration_tester`), y devuelve el control a la sesión principal, que decide con el usuario.

---

## Puntos abiertos
- Formalizar el esquema de `state.json` con validación (p. ej. JSON Schema / Pydantic) al construir el primer feature real.
- Evaluar si conviene que los agentes **referencien** esta convención en lugar de repetirla inline en cada archivo de `.claude/agents/`.
- Validar la viabilidad de la cadena ejecutándola sobre una feature real (supuesto A-005).
