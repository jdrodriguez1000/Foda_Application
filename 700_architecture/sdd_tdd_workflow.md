# SDD/TDD Workflow — Foda_Application

> Documento de arquitectura que describe **cómo funciona la cadena de 8 agentes de desarrollo** (SDD + TDD) como sistema: la máquina de estado `state.json` que gobierna cada feature y la orquestación de las etapas. Es la **fuente única de verdad** de la convención de `state.json` y del encadenamiento; los archivos de cada agente en `.claude/agents/` describen el detalle de *su* etapa y deben ser coherentes con este documento.

**Versión:** 0.3 · **Fecha:** 2026-07-02 · Ver [D-008](../800_persistence/decisions.md).

> **Cambios v0.3:** se añade la **cadena de trazabilidad codificada** `HU-xx → CA-xx → TSK-xx` (definition → spec → plan) y las **tareas atómicas** del plan como regla transversal (§8). Ver [D-031](../800_persistence/decisions.md).
> **Cambios v0.2:** se añade §6 «Bandas y Ejes de Crecimiento» con la taxonomía de bandas (`tracer_bullet → stab_n`) y la distinción entre eje vertical (madurez de una feature) y eje horizontal (crecimiento del producto: hitos MVP/Final y evolución). Ver [D-029](../800_persistence/decisions.md).

---

## Índice
1. [Propósito y Distinción de Agentes](#1-propósito-y-distinción-de-agentes)
2. [La Cadena de 8 Agentes](#2-la-cadena-de-8-agentes)
3. [Diagrama de Orquestación](#3-diagrama-de-orquestación)
4. [Gates Humanos](#4-gates-humanos)
5. [El Bucle TDD](#5-el-bucle-tdd)
6. [Bandas y Ejes de Crecimiento](#6-bandas-y-ejes-de-crecimiento)
7. [Convención de `state.json`](#7-convención-de-statejson)
8. [Reglas Transversales](#8-reglas-transversales)
9. [Artefactos por Feature](#9-artefactos-por-feature)
10. [Reanudación y Bloqueos](#10-reanudación-y-bloqueos)

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

## 6. Bandas y Ejes de Crecimiento

La **banda** dimensiona el esfuerzo del ciclo SDD/TDD por celda (D-017/D-019). El crecimiento del producto ocurre en **dos ejes ortogonales** que la palabra "banda" no debe mezclar (`D-029`):

### 6.1 Eje vertical — madurez de UNA feature

Una feature se endurece de forma controlada a lo largo de bandas sucesivas:

```
tracer_bullet → stab_1 → stab_2 → …
```

- `tracer_bullet` es la **primera pasada** (slice vertical mínimo de punta a punta); las bandas `stab_n` son **bandas de estabilización** que refinan la MISMA feature **sin cambiar su alcance** (endurecen, no amplían).
- Cada banda es una **subcarpeta hermana** bajo la feature: `600_features/<feature>/<banda>/`.
- Una feature crea **solo las bandas que necesita**: muchas se quedan en `tracer_bullet`.
- La **unidad de trabajo es la celda = feature × banda**, y `state.json` es **por celda** (campo `band`). `spec_verifier` cierra **por celda**, no por feature.

### 6.2 Eje horizontal — crecimiento del PRODUCTO

- **MVP y Final NO son bandas ni carpetas:** son **hitos de producto emergentes** (etiquetas del roadmap) que aparecen cuando el conjunto de features necesarias alcanza madurez suficiente. Una feature "terminada" es un hito superior (alcanza su banda madura), distinto del cierre de celda que hace `spec_verifier`.
- **Evolución = agregar features NUEVAS.** No es una banda: cada feature nueva **arranca en su propio `tracer_bullet`** y recorre la cadena SDD/TDD estándar. **No existen bandas `evol_n`.**

### 6.3 Alcance de adopción (E4/NC-2)

Se adopta **ahora** solo el **vocabulario del eje vertical** (`tracer_bullet`, `stab_n`). La maquinaria de hitos MVP/Final y de la fase de evolución queda como **convención futura documentada**, no construida.

---

## 7. Convención de `state.json`

Un archivo por **celda** (feature × banda, ver §6) en `600_features/<feature>/<banda>/state.json` (`D-019`). Es la máquina de estado que todos los agentes leen al arrancar y actualizan al terminar.

### 6.1 Esquema

```json
{
  "feature": "<feature>",              // snake_case, identidad de la feature
  "band": "<banda>",                   // banda del eje vertical: tracer_bullet | stab_n — §6, D-019/D-029
  "status": "in_progress",             // estado global de la celda
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
| `blocked` | Detenida; requiere decisión humana (ver §10). |

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

## 8. Reglas Transversales

- **Unidad = celda (feature × banda):** cada agente recibe en el prompt `<feature>` y `<banda>` (por defecto `tracer_bullet`) y opera sobre `600_features/<feature>/<banda>/`; el código y los tests van a `src/foda/…` y `tests/…` (`D-019`).
- **Arranque en frío:** cada agente recibe en el prompt lo que necesita (feature, banda, id de caso, resultado previo) y **relee `state.json`** para partir del estado real.
- **Validación del gate previo:** cada agente verifica que la etapa anterior esté `done` (y no `awaiting_approval` cuando aplica) antes de trabajar; si la cadena está fuera de orden, se detiene e informa.
- **Commit por etapa, sin push:** cada agente cierra con `git add` + `git commit` usando prefijo convencional (`feat`/`spec`/`plan`/`test`/`refactor`/`verify`) y `(<feature>)` en el mensaje. **El `push` se hace solo en el cierre de sesión** (D-003).
- **Separación de artefactos:** el código va a `src/foda/…`, los tests a `tests/…`; en `600_features/<feature>/<banda>/` solo viven los `.md` SDD y `state.json`.
- **Herramientas mínimas:** los 8 agentes usan `Read, Glob, Grep, Write, Edit, Bash` (sin `Agent` ni herramientas web); la orquestación de subagentes la hace la sesión principal.
- **Trazabilidad codificada end-to-end (`D-031`):** los artefactos SDD encadenan una traza por códigos: `HU-xx` (historias de usuario en `definition.md`) → `CA-xx` (criterios de aceptación en `spec.md`, cada uno enlazado a su HU + matriz de cobertura) → `TSK-xx` (tareas en `plan.md`, cada una enlazada a su CA). Las **tareas del plan** son **atómicas**: un solo responsable (∈ `{tdd_tester, tdd_coder, tdd_refactor, integration_tester, humano}`), un solo entregable, y **código y test en tareas separadas**. Cada tarea tiene **estado** (`no_implementada` | `implementada` | `cancelada_suspendida`) y su **responsable es el único escritor** de ese estado (Single Writer, `D-021`). El bucle TDD sigue corriendo **por caso** (§5); cada caso agrupa sus `TSK-xx` de test y código —las tareas son la capa de trazabilidad, no cambian el mecanismo del bucle.

---

## 9. Artefactos por Feature

Estructura esperada en `600_features/<feature>/<banda>/` (celda = feature × banda, ver §6; `D-019`):

```
600_features/<feature>/
└── <banda>/                # eje vertical: tracer_bullet (primera pasada) o stab_n (estabilización) — §6
    ├── definition.md       # feature_definer — qué y por qué
    ├── spec.md             # spec_writer — comportamiento, contratos, criterios de aceptación
    ├── plan.md             # plan_builder — cómo + lista de casos de test
    ├── verification.md     # spec_verifier — veredicto y trazabilidad
    └── state.json          # máquina de estado de la celda
```

El **código y los tests NO viven aquí**: `src/foda/…` y `tests/…` respectivamente.

---

## 10. Reanudación y Bloqueos

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
