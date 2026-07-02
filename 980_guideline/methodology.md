# Metodología de Desarrollo del Motor FODA

Esta es la **metodología de ingeniería para construir** el motor FODA (*Forecast Optimization Driven
Agentic*): cómo se desarrolla, de forma disciplinada, trazable y reanudable, el código determinista que
replica el trabajo del científico de datos para la planeación de demanda.

> **Alcance.** Este documento cubre **desarrollo**, no runtime. El **runtime** de FODA es **código
> Python determinista** (multi-tenant, orquestado por el CLI, con el LLM aislado en Discovery y
> Exploration) y lo define **exclusivamente `system_design.md`** (`D-006`, `D-020`). Los únicos agentes
> de IA del proyecto son los **8 agentes de desarrollo** que construyen ese código; en runtime **no hay
> agentes orquestando** (`D-020`).

---

## 0. Propósito y Mapa de Fuentes

### 0.1 Propósito
Reducir el espacio de decisiones probabilísticas durante la **construcción** del motor, encuadrando el
trabajo de los agentes de desarrollo mediante especificaciones, tests y verificación independiente, con
el científico de datos como **GateKeeper humano**. El objetivo del producto —automatizar el 85–95% del
trabajo de planeación de demanda— se logra construyendo un core determinista y reproducible.

> ⚠️ FODA predice **la demanda** de los productos del cliente, **no las ventas**.

### 0.2 Mapa de fuentes de verdad
Este documento no repite lo que ya tiene dueño canónico:

| Tema | Fuente canónica |
|---|---|
| Principios (P1–P8), Estándares (E1–E12), Normas de Comportamiento (NC-1…NC-6) | **`980_guideline/principles.md`** |
| Arquitectura del **runtime**: 14 flujos, medallion, CLI, multi-tenant, contratos de artefactos | **`700_architecture/system_design.md`** |
| Cadena de 8 agentes de desarrollo y su `state.json` | **`700_architecture/sdd_tdd_workflow.md`** |
| **Metodología de construcción** (este archivo): ciclo SDD+TDD, gates, persistencia de desarrollo, evaluación, evolución | **este documento** |

> **Comportamiento vinculante.** Todo agente de desarrollo debe cumplir los P/E/NC de `principles.md`
> como restricciones inmutables.

---

## 1. Ciclo de Construcción (SDD+TDD)
Ninguna pieza de trabajo se produce sin una especificación previa y un mecanismo de validación. El ciclo
de vida de un componente es:

1.  **SPEC (Specifier)** — Define el **Qué**: transforma la definición en especificación técnica.
2.  **HUMAN REVIEW** — El humano aprueba intención y alcance antes de proceder (gate).
3.  **RED (Tester)** — Define el **Criterio de Éxito**: escribe la prueba que falla, **antes** del código.
4.  **GREEN (Executor)** — Define el **Cómo**: código mínimo para que la prueba pase.
5.  **REFACTOR (Optimizer)** — Mejora estructura y mantenibilidad sin alterar el comportamiento verificado.
6.  **VERIFY (Evaluador independiente)** — Auditoría que valida la coherencia entre Spec, Test y Output.

**Correspondencia con la cadena de 8 agentes** (`sdd_tdd_workflow.md`, `D-008`/`D-015`):
`feature_definer`→Definir · `spec_writer`→SPEC · `plan_builder`→Diseñar+Planear · `tdd_tester`→RED ·
`tdd_coder`→GREEN · `tdd_refactor`→REFACTOR · `integration_tester`→Probar (contexto fresco) ·
`spec_verifier`→Verificar (contexto fresco).

**Invariantes (`D-018`):** quien ejecuta ≠ quien prueba ≠ quien verifica (contextos frescos, P1/P3);
**orden test-first** (el test que falla se escribe antes del código); gate humano al cierre (P5).

**Dimensionado por banda (`D-017`/`D-019`).** La unidad de trabajo es la **celda = feature × banda**. El
peso de los artefactos se **dimensiona a la banda** (P6, E4): en la banda **Tracer Bullet** (primer slice
vertical end-to-end, NC-4) Diseñar y Planear son ligeros. Los artefactos viven en
`600_features/<feature>/<banda>/{definition.md, spec.md, plan.md, verification.md, state.json}`; el código
y los tests en `src/foda/…` y `tests/…`.

**Contratos explícitos en dos niveles (P5, `D-030`).** "Terminado" se acuerda **antes** de ejecutar
(P5) en dos planos que no se confunden con las bandas (`D-029`):

- **`feature_contract` (por feature) — ADOPTADO.** Es la "estrella polar" / definición de "terminado"
  total de la feature. Es **obligatorio** y debe existir **antes de iniciar la primera banda**. Vive a
  **nivel feature**, por encima de las bandas: `600_features/<feature>/feature_contract.md`. Lo crea
  `feature_definer` (paso *Definir*). No es un artefacto de celda: una feature tiene **un** `feature_contract`
  aunque recorra varias bandas.
- **`slice_contract` (por celda = feature × banda) — DIFERIDO.** Definiría qué entrega cada banda como
  *slice* hacia el `feature_contract`. Su adopción queda **diferida** (no se construye ni se exige todavía,
  E4/NC-2). Cuando se adopte, podría **fusionarse con `spec.md`** —que ya captura comportamiento + criterios
  de aceptación por celda— para evitar duplicación; queda como decisión futura.

**Adaptación según el tipo de artefacto:**

| Paso | Código determinista | Documento | Flujo FODA (datos/ML) |
| :-- | :-- | :-- | :-- |
| **SPEC** | Interfaces, tipos, lógica | Índice y objetivos | Contrato del flujo (entradas de capa, transformación, salida) |
| **RED** | Test unitario que falla | Checklist de aserciones | Aserciones de calidad (ej: "MAPE ≤ umbral", "0 nulos en clave") |
| **GREEN** | Código hasta pasar el test | Contenido hasta cubrir el checklist | Transformación hasta pasar las aserciones |
| **REFACTOR** | Limpieza y patrones | Estilo y claridad | Optimizar features/hiperparámetros sin degradar la métrica |

---

## 2. Gates de Aprobación
*   **Automáticos:** criterios técnicos medibles (pasar `pytest`, cobertura de criterios de aceptación).
*   **Humanos:** el científico de datos aprueba intención/alcance. En la cadena SDD/TDD hay gate humano
    obligatorio **tras `spec_writer`** y **tras `plan_builder`** (ver `sdd_tdd_workflow.md §4`). Ningún
    agente cruza un gate por su cuenta: lo hace la sesión principal tras la aprobación humana.

---

## 3. Persistencia y Trazabilidad (desarrollo)
La fuente de verdad reside en el **filesystem**, no en la memoria de los agentes. Esto permite reanudar
el trabajo entre sesiones y ante fallos (E1, E5).

### 3.1 Capas de persistencia
| Capa | Dónde | Qué guarda |
|---|---|---|
| Proyecto / sesión | `800_persistence/` | `progress` · `tasks` · `lessons` · `decisions` · `assumptions` |
| Por celda (SDD/TDD) | `600_features/<feature>/<banda>/state.json` | máquina de estado de la construcción |

### 3.2 Single Writer Rule (`D-021`)
Cada archivo de estado tiene **un único responsable de escritura**, para evitar condiciones de carrera.
No se adoptan archivos de estado de runtime agéntico (los 3 `fda-*` de la metodología original quedan
descartados por `D-020`/`D-021`): en runtime el **estado son los propios artefactos** bajo
`clients/<NAME>/`, y la reanudación sale de qué artefactos existen (Principio 5 de `system_design`).

### 3.3 Git y reanudación
- **Commit por etapa** con prefijo convencional; el **push** se hace en el cierre de sesión (`D-003`).
- Para retomar una celda interrumpida, la sesión principal lee su `state.json` (`status`,
  `current_stage`) y reinvoca al agente correspondiente con contexto fresco.

---

## 4. Evaluación
La independencia del evaluador (P3: quien genera no evalúa) ya se cumple en desarrollo: `integration_tester`
y `spec_verifier` corren en **contextos frescos**, separados de quien codifica.

**La evaluación se dimensiona a la naturaleza de la salida (`D-022`):**

| Tipo de salida | Naturaleza | Evaluación |
|---|---|---|
| **Código determinista** (core, mayoría de flujos) | Objetiva | **Tests** (RED) + **veredicto binario** de `spec_verifier` (CONFORME/NO CONFORME) + matriz de trazabilidad. **Ya implementado; suficiente.** |
| **Salidas de LLM** (Discovery, Exploration) | Subjetiva | **Rúbrica calibrada 0.0–1.0**: dimensiones+pesos, **few-shot** (≥2 ejemplos, uno ≥0.7 y uno <0.5) y **anclas** (1.0/0.5/0.0). Combate la lenidad del evaluador (E3). |
| **Calidad ML** (Modelling/Inferences) | Cuantitativa | Aserción tipo "MAPE ≤ umbral" (encaja como test) + **evaluación temprana** (~20 casos representativos, E9). |

> **Principio rector:** *rúbrica solo donde el LLM aporta* — el espejo del Principio 1 de diseño
> (*"LLM solo donde aporta"*). Aplicar rúbrica calibrada al código determinista sería overkill; los tests
> ya son objetivos. La ubicación concreta de cada rúbrica se define al construir Discovery/Exploration.

**Evaluación Temprana (E9).** No esperar a tener todo el flujo para evaluar (impacto del 30–80% en calidad
a costo mínimo). Al completar el primer componente funcional, evaluar una muestra de ~20 casos
representativos; si la calidad es baja, ajustar la especificación **antes** de continuar.

---

## 5. Evolución del Harness (E4: Mínima Complejidad)
El harness de desarrollo parte del mínimo viable y evoluciona:
- Se construye con el **menor número de componentes** que satisfagan el trabajo (E4, NC-2).
- Cada componente codifica una **suposición explícita** sobre una limitación del modelo; no se agrega un
  componente sin evidencia de que su ausencia degrada la calidad.
- **Prueba de remoción periódica:** quitar un componente a la vez y medir el impacto; si la calidad no
  cae, se elimina (el modelo ya no requiere ese andamiaje) y se registra la lección.

---

## Apéndice: Estándares de Ingeniería
*   **Convención de commits:** `tipo(<feature>): descripción` (`feat`/`spec`/`plan`/`test`/`refactor`/`verify`).
*   **Estrategia de ramas:** merge a `main` tras gate aprobado.
*   **Selección de modelos:** el modelo adecuado según la tarea (Opus para specs/verificación, Sonnet para ejecución, Haiku para tareas ligeras).
