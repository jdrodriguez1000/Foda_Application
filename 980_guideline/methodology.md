# Metodología del Harness FODA

Este documento define el **proceso y el protocolo** para construir y operar **FODA** (*Forecast
Optimization Driven Agentic*): el motor (harness) reutilizable que replica el trabajo de los
científicos de datos de Sabbia Solutions & Services para la **planeación de demanda** con machine
learning, ejecutándolo de forma autónoma y controlada, garantizando la calidad y la reducción de la
varianza en los resultados.

---

## 0. Propósito y Mapa de Fuentes

### 0.1 Propósito
El objetivo del harness FODA es reducir el espacio de decisiones probabilísticas de los LLMs,
encuadrando su comportamiento mediante contratos, herramientas específicas y evaluación independiente,
para automatizar el 85–95% del trabajo de planeación de demanda y dejar al científico de datos como
revisor/aprobador del 5–15% restante.

> ⚠️ FODA predice **la demanda** de los productos del cliente, **no las ventas**.

### 0.2 Los dos planos (ver `D-001`)
El **MOTOR** (`foda-*`) contiene las definiciones canónicas reutilizables de esta metodología. La
**INSTANCIA** (`fda-*`) es la solución concreta de un cliente: una carpeta externa por empresa donde
corre el runtime y se generan los artefactos. El runtime de la instancia nunca vuelve al motor; el
puente entre planos es el instalador de terminal (`install.sh`).

### 0.3 Mapa de fuentes de verdad
Este archivo **no** repite lo que ya tiene dueño canónico en otro documento. Cada tema se consulta en
su fuente única:

| Tema | Fuente canónica | Este documento |
|---|---|---|
| Principios (P1–P8), Estándares (E1–E12), Normas de Comportamiento (NC-1…NC-6) | **`980_guideline/principles.md`** | Los referencia; no los repite |
| Arquitectura del **producto**: los 14 flujos, capas medallion, CLI, multi-tenant, contratos de artefactos | **`700_architecture/system_design.md`** | Los referencia; no los repite |
| Cadena de 8 agentes de desarrollo (SDD/TDD) y su `state.json` | **`700_architecture/sdd_tdd_workflow.md`** | La referencia; describe su encuadre de proceso |
| **Proceso/protocolo del harness**: patrón A/B/C, ciclo de construcción, estado runtime, gates, flujo del arnés | **este archivo** | — |

> **Comportamiento vinculante.** Todo agente del harness (la sesión principal y cualquier subagente)
> debe cumplir los P/E/NC de `principles.md` como restricciones inmutables. Este documento describe
> *cómo* se aplican en el flujo del arnés.

---

## 1. Modelo de Dos Capas (Gobernanza vs Ejecución)
El sistema no es un programa único, sino un "sistema de sistemas" dividido en dos capas para separar el
**valor de negocio** de la **ejecución técnica**.

### ¿Por qué dos capas?
1.  **Eliminación de Sesgo**: El ejecutor (Capa 2) no debe ser el mismo que aprueba el alcance (Capa 1).
2.  **Gestión de Contexto**: La Capa 1 mantiene la visión global; la Capa 2 opera con "Contexto Estricto" (E2) para evitar alucinaciones.
3.  **Seguridad**: La Capa 1 actúa como "GateKeeper" humano-IA (el **científico de datos**), asegurando que ninguna acción técnica ocurra sin alineación estratégica.

### Las dos capas en FODA
*   **Capa 1: Gobernanza** — *"¿Estamos prediciendo lo correcto?"*. Encuadra el problema de negocio del
    cliente y aprueba los checkpoints clave. La opera la **Instancia A (Governor)**, con el científico de
    datos como GateKeeper humano. Métricas Tipo 2 (valor de negocio, salud del sistema).
*   **Capa 2: Ejecución** — *"¿Lo estamos prediciendo bien?"*. Construye y corre el **pipeline de demanda**.
    La operan la **Instancia B (Planificador)** y los **Workers** que A ejecuta, con la **Instancia C
    (Evaluator)** como auditor. Métricas Tipo 1 (calidad de artefactos, MAPE, apego a especificación).

### Las fases del harness = los 14 flujos del pipeline
En FODA, las fases del ciclo de vida **son los 14 flujos del pipeline de demanda**. Cada flujo es una
"fase" en el sentido del §2 (patrón A/B/C) y produce artefactos canónicos (`*.json`/`*.yaml`/`.pkl`) que
sirven de handoff al siguiente, encadenados sobre la arquitectura de datos **bronze → silver → gold**.

> **Fuente única.** La tabla detallada de los 14 flujos (Discovery … Alerting), sus artefactos
> canónicos, las capas medallion y el checkpoint humano de *Modelling* viven en
> **`700_architecture/system_design.md` (§5, §10, §15)**. No se reproducen aquí para evitar
> divergencia. Lo único relevante para el proceso: cada flujo es una fase que aplica el patrón A/B/C.

---

## 2. El Patrón de Fase A/B/C (modelo plano)
En FODA, una **Fase** es un bloque lógico de trabajo que representa un hito del proyecto: cada uno de los
14 flujos del pipeline. Ninguna fase puede considerarse terminada hasta que supere su gate de aprobación.

Toda fase implementa la colaboración de **tres instancias independientes** (sesiones de IA con contexto
separado) para garantizar la calidad.

### Las Tres Instancias
1.  **Instancia A: Gobernanza (`foda-governor`)**
    *   **Rol**: Director del Proyecto y **único orquestador**. En la práctica es la **sesión principal de
        Claude Code** (nivel 0 del árbol de subagentes), operada junto al científico de datos.
    *   **Responsabilidad**: Define el contrato de la fase, gestiona las señales de bloqueo, ejecuta el plan
        (invoca a los Workers) y toma la decisión final "Avanzar o Repetir" (GateKeeper). Es el **único que
        escribe el estado** (`fda-harness-state.json` y `fda-execution-state.json`).
2.  **Instancia B: Planificación (`foda-<flujo>-planner`)**
    *   **Rol**: Capataz Técnico **planificador**. Es un **subagente** spawneado por A; **solo planifica**,
        **no ejecuta, no spawnea y no escribe artefactos** (`tools: Read`; ver modelo plano §2.1 y `D-009`).
        Es **específico por flujo** (`D-010`): su cadena de workers va embebida en su definición.
    *   **Responsabilidad**: Recibe la referencia al contrato y a los insumos, descompone el trabajo en
        micro-tareas y **devuelve a A el `orchestration_plan`** (qué Workers ejecutar, en qué orden y con qué
        inputs/outputs). **A** ejecuta ese plan y **A** persiste el plan.
    *   **Regla crítica (E12)**: El `orchestration_plan` que B devuelve lo persiste **A** en la sección
        `orchestration_plan` de `fda-execution-state.json`. Si el contexto crece durante la ejecución, A
        puede releer el plan desde el filesystem sin reconstruirlo. Ningún Worker se activa sin ese plan guardado.
3.  **Instancia C: Evaluación (`foda-<flujo>-evaluator`)**
    *   **Rol**: Auditor Independiente. Es un **subagente** spawneado por A; **no** lleva la herramienta
        `Agent` (no puede spawnear a nadie), lo que garantiza P3. Es **específico por flujo** (`D-010`): su
        rúbrica (dimensiones, vetos, anclas) va embebida en su definición.
    *   **Responsabilidad**: Actúa con un cerebro fresco (sin contexto de la ejecución). Lee el contrato y
        los artefactos finales del filesystem, aplica una rúbrica objetiva y emite un veredicto de aprobación
        o rechazo con feedback técnico. Escribe solo en `/eval` (nunca en el estado, que es de A).

### Jerarquía de Control y Llamadas
Las tres instancias tienen una jerarquía de control estricta que preserva P1 (Separación de Roles) y P3
(Evaluador Independiente).

```
A (Governor) ── única instancia que spawnea y única que escribe estado (modelo plano, D-009)
│
├──▶ spawea B (Planificador)   ← B PLANIFICA y devuelve el orchestration_plan (no ejecuta, no escribe)
│
├──▶ ejecuta el plan: spawea Workers (1..N, en paralelo si son independientes)
│         │
│         └──▶ escriben artefactos al filesystem; reportan a A solo la referencia (path)
│
└──▶ spawea C (Evaluator)      ← solo después de que los Workers terminan
          │
          └──▶ lee artefactos del filesystem → escribe veredicto en /eval → A decide
```

**Reglas que no pueden violarse (modelo plano, `D-009`):**

*   **A es la única instancia que spawnea y la única que escribe estado.** B, Workers y C **no se invocan
    entre sí**: todo pasa por A. Esto hace el motor robusto a la versión de Claude Code (no depende de
    subagentes anidados).
*   **B planifica, no ejecuta ni escribe.** B recibe el contrato + insumos y devuelve a A el
    `orchestration_plan`. **A** lo persiste en `fda-execution-state.json` antes de ejecutar (E12).
*   **A ejecuta el plan llamando a los Workers.** Secuencia: B planifica → A ejecuta Workers → C audita.
    A decide cuándo avanzar de una etapa a la siguiente. Los Workers independientes se ejecutan en paralelo (E7).
*   **Los Workers reportan a A**, no a B, y **solo la referencia** (path) al artefacto, nunca el contenido (E6).
*   **C no llama a nadie.** C solo lee artefactos del filesystem y escribe su veredicto en `/eval`. Toda la
    información que C necesita debe estar en los artefactos y en el Sprint Contract.
*   **Cada "llamada" es un agente con contexto fresco** (`Agent` tool con contexto limpio). Esto implementa
    P4 (Context Resets) y garantiza que ninguna instancia herede sesgos de las anteriores.

### 2.1 Implementación con modelo plano de Claude Code (D-009)
El patrón A/B/C se implementa con un **modelo plano**: la **sesión principal (A) es la única que spawnea**.
No se usan subagentes anidados (B no spawnea a los Workers). Esto hace el motor **robusto a la versión de
Claude Code**: no depende de la feature de anidamiento y está validado en el harness de referencia Caden
(ver `L-006`). Reemplaza el diseño anidado original de `D-005`.

*   **Mapa de spawneo** (la conversación principal es nivel 0; todo lo demás cuelga de A, nivel 1):
    ```
    nivel 0 ── foda-governor (A)  = sesión principal de Claude Code (ÚNICA que spawnea y escribe estado)
                 ├──▶ nivel 1 ── foda-<flujo>-planner (B)      → devuelve orchestration_plan a A
                 ├──▶ nivel 1 ── foda-<flujo>-<rol> (Workers)  → A los ejecuta según el plan de B
                 └──▶ nivel 1 ── foda-<flujo>-evaluator (C)    → audita y emite veredicto en /eval
    ```
*   **Política de `tools` por instancia** (hace cumplir P1 y P3 a nivel de herramienta):
    *   **A (Governor)**: sesión principal; **única** con capacidad de invocar subagentes (`Agent`) y de escribir estado.
    *   **B (`foda-<flujo>-planner`)**: `tools: Read` (solo planifica). **No** incluye `Agent` ni `Write`.
    *   **C (`foda-<flujo>-evaluator`)**: `tools: Read, Write` (escribe solo en `/eval`). **No** incluye `Agent`.
    *   **Workers (`foda-<flujo>-<rol>`)**: las herramientas de su dominio + `Write`. **No** incluyen `Agent`.
*   **Sin límite de profundidad relevante**: el árbol es plano (A → {B | Workers | C}, todos a nivel 1), así
    que el límite de 5 niveles de `L-002` deja de ser una restricción de diseño. Si en el futuro se necesitara
    paralelismo más rico, evaluar *agent teams* (contexto propio por worker), nunca reintroducir anidamiento
    sin revisar `D-009`.

### Los 4 Elementos Internos de la Fase
Para que estas instancias operen, deben existir:
1.  **Sprint Contract**: El acuerdo de lo que significa "terminado", propuesto por A y ratificado por B y C.
2.  **Workers**: Agentes especializados que A ejecuta según el plan de B, para el trabajo de dominio.
3.  **Rúbrica de Evaluación**: Los criterios de puntuación (0.0–1.0) que usará la Instancia C. Para evitar
    lenidad sistémica, toda rúbrica debe incluir obligatoriamente (ver E3 en `principles.md`):
    *   **a) Dimensiones definidas**: nombre, descripción y peso relativo. Estándar: *Precisión Factual*,
        *Completitud*, *Calidad de Fuentes/Referencias* y *Eficiencia de Herramientas*; un harness puede
        agregar dimensiones de dominio.
    *   **b) Ejemplos few-shot calibrados**: al menos 2 ejemplos con desglose por dimensión — uno aceptable
        (score global ≥ 0.7) y uno rechazado (score global < 0.5).
    *   **c) Anclas de calibración por nivel**: **1.0** cumplido sin observaciones; **0.5** cumplido
        parcialmente (corrección menor); **0.0** ausente o incumplido (rechazo directo).
4.  **Handoff Artifact**: El resultado tangible que C audita y A aprueba.

---

## 3. Persistencia, Trazabilidad y Memoria
La "fuente de verdad" reside en el filesystem, no en la memoria de los agentes. Esto garantiza que el
sistema nunca pierda contexto entre sesiones ni ante fallos.

### 3.1 Los Archivos de Estado (Single Writer Rule)
En el **modelo plano (`D-009`), solo A escribe estado.** Cada archivo tiene un único responsable:

*   **Harness State (`fda-harness-state.json`)** — **Responsable: A.** Fuente de verdad estratégica: fases,
    Sprint Contract, aprobaciones, CRs.
*   **Execution State (`fda-execution-state.json`)** — **Responsable: A.** Control táctico por flujo: el
    `orchestration_plan` que B devuelve y el avance de los Workers que A ejecuta.
*   **Progress Log (`project-progress.txt`)** — **Responsable: A.** Bitácora narrativa de avance. (B no puede
    escribir —`tools: Read`— y C escribe solo en `/eval`; por eso el progress log lo mantiene siempre A.)

### 3.2 Regla de Referencias Ligeras (E6)
Cuando un Worker completa su tarea, **reporta a A únicamente la referencia** al artefacto producido — el
path del archivo o el ID del recurso — nunca el contenido completo.

*   **Por qué**: Pasar contenido completo entre agentes produce el efecto "teléfono descompuesto": degrada
    la información, consume tokens y genera cuellos de botella.
*   **Cómo**: A actualiza `fda-execution-state.json` con la referencia (path/ID). Cualquier instancia que
    necesite el contenido lo lee directamente del filesystem usando esa referencia.
*   **Aplica a toda la cadena**: Workers → A (solo paths), B → A (solo el `orchestration_plan`), C → A (solo
    path a `/eval/verdict.json`). Ningún agente embebe contenido de artefactos en sus mensajes de reporte.

### 3.3 Otros Artefactos de Persistencia
*   **Handoff Artifacts**: Artefactos canónicos (`*.json`/`*.yaml`/`.pkl`) que genera un flujo y sirven de
    entrada al siguiente (la tabla completa está en `system_design.md`). Cada artefacto documenta las
    transformaciones aplicadas y permite **replicar** el proceso sobre otros archivos del cliente.
*   **Capas de datos (bronze/silver/gold)**: trazabilidad inmutable hacia atrás — **bronze** (crudo,
    nunca se sobrescribe) → **silver** (limpio) → **gold** (derivado/listo para ML). Un flujo nunca modifica
    una capa anterior; produce la siguiente. (Detalle en `system_design.md §10`.)
*   **Git History**: Registro inmutable de cambios con convención de commits estricta (ver Apéndice A).

### 3.4 Métricas y Memoria a Largo Plazo (Knowledge Base)
La memoria a largo plazo permite al sistema aprender de éxitos y errores pasados. Reside en `/knowledge`.

*   **Métricas (`/eval/metrics_summary.json`)** — **Responsable: C.** Se genera al finalizar la auditoría de
    cada fase (estructura en §5.2).
*   **Decisions Library (`/knowledge/decisions_library.md`)** — **Responsable: A.** Registro de decisiones de
    arquitectura (DA) reutilizables. Cada una indica nivel de reutilización (Alta/Media/Baja), justificación
    técnica y cuándo NO reutilizarla.
*   **Lessons Learned (`/knowledge/lessons_learned.md`)** — **Responsable: A.** Bitácora de errores, hallazgos
    de evaluación (major/minor) y bloqueos. Cada lección incluye una "Regla para escritores futuros".
*   **Índices (`_index.md`)** — Mapas de navegación por tipo de proyecto, stack o fecha.

**Protocolo de utilización (consulta).** Antes de iniciar cualquier flujo —especialmente **Cleaning**,
**Derivation**, **Featuring** y **Modelling**—, la **Instancia B** debe: (1) revisar `decisions_library.md`
para identificar DAs de alta reutilización aplicables; (2) revisar `lessons_learned.md` filtrando por la fase
a ejecutar; (3) integrar las "Reglas para escritores futuros" como restricciones inmutables en el Sprint
Contract (que A ratifica).

**Protocolo de actualización (persistencia).** Al cerrar un proyecto, **A** consolida las DAs aprobadas y las
lecciones (incluidos los hallazgos de C), actualiza los índices e integra el conocimiento nuevo en `/knowledge`
para el siguiente arnés.

---

## 4. Ciclo de Construcción: Fase 0 → Fase 1 → Fase 2 (SDD+TDD)

### 4.1 Fase 0: Definición Estructural (Contrato del Arnés)
Antes de construir un harness se define su interfaz:
*   **Entradas (Inputs)**: ¿Qué material "en bruto" recibe?
*   **Propósito (Intent)**: ¿Qué problema específico resuelve?
*   **Procesos**: ¿Qué transformaciones ocurren dentro?
*   **Salidas (Outputs)**: ¿Qué artefactos tangibles produce?

**Estrategia de exploración (E11 — de amplio a estrecho).** Cuando la definición requiere recopilar
información de dominio —sobre todo en **Discovery** y **Onboarding**—: (1) exploración amplia con preguntas
cortas y abiertas; (2) identificar dónde hay mayor densidad de información relevante; (3) profundizar solo
entonces; (4) no comprometer el plan/arquitectura/Sprint Contract a una sola fuente antes de explorar la
amplitud. B aplica el patrón durante la recopilación; A lo supervisa al revisar el Sprint Contract.

### 4.2 Fase 1: Diseño Agéntico
Definición de la infraestructura para ejecutar el arnés. Antes de construir el primer componente se cierra:
*   **Roles de Subagentes** (especialización de Workers) y **Política de Herramientas** (P7).
*   **Política de Escalamiento** (paralelismo y Reasoning Budget — P6, E8).
*   **Checkpoints Canónicos (E5)**: puntos de control donde el sistema guarda estado; ante fallo se reanuda
    desde el último checkpoint, no desde cero.
*   **Política de Fallback de Herramientas (E5)** — tres niveles en orden: **(1) Reintento** (hasta 2 veces;
    resuelve timeouts/rate limits); **(2) Fallback** (herramienta/método alternativo previamente definido);
    **(3) Escalamiento** (detener la tarea, registrar el bloqueo en `project-progress.txt` y pedir intervención
    humana). Nunca improvisar ni continuar con datos parciales — un resultado degradado es peor que un bloqueo
    explícito.
*   **Trigger de Context Reset (E2)**: forzar reinicio de contexto cuando ocurra **cualquiera** (lo que pase
    primero): **Cuantitativo** — uso de tokens ≥ 70% de la ventana activa; **Conductual** (más temprano y
    confiable) — señales de "ansiedad contextual": cerrar tareas sin completarlas, omitir pasos del ciclo
    SDD+TDD, respuestas más cortas/superficiales de lo usual, o declarar trabajo "terminado" sin evidencia de
    que se verificaron los criterios de aceptación. Ante duda, priorizar el reset sobre la compactación.

### 4.3 Fase 2: Construcción Iterativa (SDD+TDD)
Motor de ejecución técnica: ninguna pieza de trabajo se produce sin una especificación previa y un mecanismo
de validación.

**El ciclo de vida del componente (la ambición, Ln):**
1.  **SPEC (Specifier)**: Define el **Qué**. Transforma el contrato en especificación técnica detallada.
2.  **HUMAN REVIEW**: El humano aprueba intención y alcance de la especificación antes de proceder.
3.  **RED (Tester)**: Define el **Criterio de Éxito**. Escribe la prueba/checklist que el resultado debe
    cumplir — **antes** del código de producción.
4.  **GREEN (Executor)**: Define el **Cómo**. Produce el código/contenido mínimo para satisfacer la prueba.
5.  **REFACTOR (Optimizer)**: Mejora estructura, estilo y mantenibilidad sin alterar el comportamiento verificado.
6.  **EVAL (Instancia C)**: Auditoría independiente que valida la coherencia entre Spec, Test y Output.

**Adaptación según el tipo de artefacto** (el ciclo es un modelo mental universal):

| Paso | Construcción de Código | Construcción de Documentos | Construcción de un Flujo FODA (datos/ML) |
| :-- | :-- | :-- | :-- |
| **SPEC** | Interfaces, tipos y lógica de algoritmos. | Índice, temas clave y objetivos de información. | Contrato del flujo: entradas (capa de datos), transformaciones y artefacto de salida. |
| **RED** | Test unitario/integración que falla. | Checklist de aserciones (ej: "listar 3 riesgos"). | Aserciones de calidad de datos/modelo (ej: "MAPE ≤ umbral", "0 nulos en clave"). |
| **GREEN** | Código hasta que el test pasa. | Contenido hasta cubrir el checklist. | Transformación hasta producir el artefacto que pasa las aserciones. |
| **REFACTOR** | Limpia el código y aplica patrones. | Mejora estilo, claridad y Lenguaje Ubicuo. | Optimiza features/hiperparámetros sin degradar la métrica verificada. |

**Protocolo de construcción por celda — dimensionado por banda (`D-017` / `D-018`).**
El ciclo anterior es la **ambición (Ln)**. Su realización por **celda** (flujo × banda) se **dimensiona a la
banda** vía Escalamiento Proporcional (P6) y Mínima Complejidad (E4). La proporcionalidad se expresa como
**PESO del artefacto, no como fusión de pasos**: los 6 pasos conservan siempre su carril propio.

*   **Invariante (toda banda, `D-018`):** quien ejecuta ≠ quien prueba ≠ quien verifica; **Ejecutar, Probar y
    Verificar corren en tres contextos frescos distintos** (P1, P3); gate humano al cierre de celda (P5). La
    independencia crece hacia el final.
*   **Orden test-first (`D-018`):** *dentro* de **Ejecutar**, el ciclo unitario es **RED → GREEN → REFACTOR**
    (el test que falla se escribe **antes** del código). **Probar** es una capa de aceptación/integración
    **posterior e independiente** que corre la celda contra el *golden client* (E9) y **complementa** —no
    sustituye— a los tests unitarios.

| Paso | Instancia | Contexto | Artefacto / carril | Rigor en Tracer Bullet |
| :-- | :-- | :-- | :-- | :-- |
| Definir (banda) | A + humano | — | `600_features/<feature>/<banda>/definition.md` (slice_contract + BDD embebidos) | el peso de la banda |
| Diseñar | B | propio | `600_features/<feature>/<banda>/spec.md` | ≤1 pág (agente, skill, schema, I/O de capas) |
| Planear | B | propio | `600_features/<feature>/<banda>/plan.md` | checklist de construcción |
| Ejecutar (RED→GREEN→REFACTOR) | A + Workers (`E7`) | propio | código en `src/foda/…` + tests en `tests/…` (test-first) | definiciones + código determinista + tests unitarios test-first |
| Probar | **C-test** | **fresco** | tests de integración en `tests/…`; evidencia en `600_features/<feature>/<banda>/` | corre la celda contra el golden client (`E9`); valida schema/contract/determinismo |
| Verificar | **C-verify** + humano | **fresco** | `600_features/<feature>/<banda>/verification.md` + gate | audita vs `slice_contract` y brief L0; `APROBADO`/`REQUIERE SUBSANACIÓN` |

> **Carpetería (`D-019`).** Los números `703/705/710/720` son **etiquetas conceptuales de fase**, no
> carpetas. Los artefactos de construcción viven en la taxonomía feature/celda-céntrica
> `600_features/<feature>/<banda>/` (unidad = celda = feature × banda; banda por defecto de la primera
> pasada: `tracer_bullet`); el código y los tests van a `src/foda/…` y `tests/…`.

**Correspondencia con la cadena de 8 agentes de desarrollo (`sdd_tdd_workflow.md`, `D-008`/`D-015`):**
`feature_definer`→Definir · `spec_writer`→SPEC · `plan_builder`→Diseñar+Planear · `tdd_tester`→RED ·
`tdd_coder`→GREEN · `tdd_refactor`→REFACTOR (los tres dentro de "Ejecutar") · `integration_tester`→Probar
(contexto fresco) · `spec_verifier`→Verificar (contexto fresco).

**Mecánica:** un subagente termina y **devuelve control a A**, que encadena el siguiente (modelo plano,
`D-009`). Loop de subsanación con **tope ~2 rondas**; si no converge, **escala al humano**.
**Snapshots (`D-012`):** cada celda consume el snapshot previo y congela el suyo al aprobar; ese snapshot
alimenta el siguiente flujo, demostrando el end-to-end acumulado. En bandas superiores el mismo protocolo sube
de peso (Diseñar/Planear dejan de ser ≤1 pág) sin cambiar el invariante ni el mapa de instancias.

**Evaluación Temprana (E9).** No esperar al harness completo para evaluar (impacto del 30–80% en calidad a
costo mínimo). **Cuándo:** al completar el **primer componente funcional**, antes del segundo. **Cómo:**
(1) B selecciona ~20 casos representativos del dominio (frecuentes y críticos, no triviales ni extremos);
(2) C evalúa contra la rúbrica calibrada y produce un mini-veredicto por dimensión; (3) **A registra** el
resultado en `fda-execution-state.json` bajo `early_eval`; (4) si score ≥ 0.7, continuar; (5) si < 0.7,
ajustar Sprint Contract/especificación **antes** de seguir. B coordina, C produce el veredicto, A decide si el
ajuste requiere aprobación humana.

---

## 5. Gobernanza, Métricas y Gates
Control de calidad sistémico basado en indicadores cuantitativos y cualitativos. Toda fase concluye con un
artefacto de métricas.

### 5.1 Gates de Aprobación
*   **Automáticos**: criterios técnicos medibles definidos en los contratos (coverage, linting, pasar tests).
*   **Humanos**: decisiones estratégicas, aprobación de hitos de valor y revisiones de impacto (incluido el
    checkpoint de *Modelling* — ver `system_design.md`).

### 5.2 Estándar de Persistencia: `metrics_summary.json`
La **Instancia C** genera `/eval/metrics_summary.json` al finalizar su auditoría, con estructura mínima:
*   **Pipeline Data**: timestamps de completitud y cierre de cambios.
*   **Document/Artifact Status**: versión final, número de revisiones, estado de aprobación y score por rúbrica.
*   **Timeline Metrics**: tiempos de ciclo entre hitos clave.
*   **Change Requests (CR)**: registro de CRs gestionadas durante la fase.

### 5.3 Métricas Tipo 1 (micro-nivel): desempeño del agente y la tarea
*   **Eficiencia**: latencia de tarea y consumo de tokens vs. complejidad.
*   **Calidad**: score de rúbrica, tasa de rechazo y apego a especificación.

### 5.4 Métricas Tipo 2 (macro-nivel): salud y eficiencia del sistema
*   **Salud del Sistema**: velocidad de sprint, estabilidad de construcción y trazabilidad documental.
*   **Eficiencia Estratégica**: valor de negocio/costo, tiempo total de ciclo de fase y efectividad del Gatekeeper.

---

## 6. Flujo del Arnés (coreografía A/B/C)
El ciclo de vida de un arnés es una coreografía sincronizada entre las tres instancias.

### 6.1 Inicialización (Instancia A)
*   **Entrada**: el humano envía "Iniciemos" o "Continuemos" a la sesión activa (A).
*   **Determinación del modo**: A verifica si `fda-harness-state.json` existe:
    *   **No existe** → modo **Inicio** → ritual **E10-A**.
    *   **Existe e íntegro** → modo **Continuación** → ritual **E10-B**.
    *   **Existe pero corrupto** → `git restore`/`git checkout` sobre el archivo dañado. Si persiste, detener y
        reportar en `project-progress.txt` pidiendo intervención humana.
*   **Ritual E10-A (Inicio)**: (1) verificar directorio y ambiente; (2) crear jerarquía de carpetas; (3)
    inicializar `fda-harness-state.json`, `fda-execution-state.json` y `project-progress.txt` con esquemas
    vacíos; (4) `git init` + enlazar remoto en GitHub (`git remote add origin <url>`); (5) prueba de sanidad
    del ambiente; (6) registrar el arranque en `project-progress.txt` con timestamp.
*   **Ritual E10-B (Continuación)**: (1) verificar directorio/ambiente; (2) `git log --oneline -10`; (3) leer
    `project-progress.txt`; (4) cargar `fda-harness-state.json` y revisar el Sprint Contract vigente; (5) leer
    `fda-execution-state.json` (último checkpoint); (6) seleccionar la siguiente tarea prioritaria; (7) prueba
    de sanidad antes de comenzar.
*   **Reporte al humano (obligatorio)**: A presenta un resumen con (1) estado encontrado (modo, integridad,
    sanidad); (2) Sprint Contract propuesto (Inicio) o vigente (Continuación); (3) próxima acción.
*   **Gate de aprobación humana (P5)**: **Aprobado** → A escribe el Sprint Contract en `fda-harness-state.json`
    y spawnea B. **Ajuste** → A incorpora cambios y re-presenta. **Cancelación** → A registra y detiene.
    A no spawnea a B hasta recibir aprobación explícita.

### 6.2 Planificación (B) y Ejecución Técnica (A + Workers)
*   **Planificación (B)**: A spawnea a B pasándole la referencia al Sprint Contract. B lee el contrato y los
    insumos (`tools: Read`), consulta `decisions_library.md` y `lessons_learned.md`, y **devuelve a A el
    `orchestration_plan`**. B no ejecuta ni escribe.
*   **Persistencia del plan (A)**: A escribe el `orchestration_plan` en `fda-execution-state.json` (E12). Ningún
    Worker se activa sin el plan guardado.
*   **Ejecución de Workers (A)**: A spawnea los Workers según el plan (independientes en paralelo, E7). Cada
    Worker: (1) recibe su micro-tarea con objetivo, formato de salida y herramientas; (2) ejecuta el ciclo
    SDD+TDD (RED→GREEN→REFACTOR); (3) escribe su artefacto al filesystem; (4) reporta a A **solo la referencia**
    (E6).
*   **Estado (A)**: A actualiza `fda-execution-state.json` en cada checkpoint. Al terminar todos los Workers, A
    marca `EXECUTION_COMPLETE` y registra el resumen en `project-progress.txt`.

### 6.3 Auditoría y Gate de Aprobación (C + A)
*   **Paso 1 — Gate intermedio (A):** A verifica `EXECUTION_COMPLETE`; si algún Worker no completó, investiga el
    bloqueo. Confirmada la completitud, spawnea a C pasándole las referencias (paths) al Sprint Contract y a los
    artefactos.
*   **Paso 2 — Auditoría independiente (C):** C lee los artefactos del filesystem, evalúa contra la rúbrica
    calibrada y escribe **en sus dos archivos propios** — `/eval/metrics_summary.json` y `/eval/verdict.json`
    (`APPROVED`/`REJECTED` con hallazgos). C registra el cierre en `project-progress.txt`. **C nunca escribe
    en `fda-harness-state.json`.**
*   **Paso 3 — Decisión final (A — GateKeeper):** A lee `/eval/verdict.json` y decide "Avanzar o Repetir":
    `APPROVED` → A marca `PHASE_COMPLETE` y notifica al humano; `REJECTED` → A activa el protocolo de rechazo (§6.4).

### 6.4 Protocolo de Rechazo y Reintento
Cuando el veredicto de C es `REJECTED`, la fase entra en **Bloqueo de Fase**:
1.  **Rechazo Técnico (C → filesystem → A → B):** C escribe el rechazo en `/eval/verdict.json` y
    `/eval/eval_{artefacto}.json`. A lee el veredicto, marca `fda-harness-state.json` como `IN_REWORK` y
    **spawnea B de nuevo** pasándole la referencia al archivo de rechazo. C nunca contacta a B directamente. B
    lee el informe, consulta `lessons_learned.md` y replanifica solo los componentes fallidos; A re-ejecuta.
2.  **Rechazo Estratégico (Humano → A):** el artefacto o la spec no cumple el objetivo de negocio o cambia el
    alcance. A detiene el flujo, actualiza el Sprint Contract (o abre un CR) y marca `fda-harness-state.json`
    como `HOLD`. No avanza hasta nueva aprobación humana.
3.  **Registro de Aprendizaje:** todo rechazo (major/minor) lo registra A en `lessons_learned.md` al cerrar el
    proyecto, con los hallazgos de C.

### 6.5 Protocolo de Gestión de Cambios (CR)
Ante un CR sobre artefactos ya aprobados:
1.  **Registro (A):** A registra la solicitud en `fda-harness-state.json` bajo `change_requests` con un ID
    (ej. `CR_001`) y estado `OPEN`.
2.  **Registro técnico (B):** B crea `/changes/CR_XXXX_Nombre.md` con alcance, componentes afectados y análisis
    de impacto técnico.
3.  **Evaluación de impacto (B):** B evalúa qué fases, artefactos y pruebas se ven afectados y estima el esfuerzo.
4.  **Aprobación/Rechazo (A + humano):** tras la aprobación, A actualiza el CR a `APPROVED` y marca los
    artefactos afectados como `DEPRECATED` o `PENDING_REWORK`.
5.  **Ejecución:** el sistema reanuda la fase afectada desde el punto de cambio con el ciclo SDD+TDD.
6.  **Cierre (A):** tras la evaluación satisfactoria de C, A marca el CR como `CLOSED` y archiva el registro y
    los reportes de evaluación.

---

## 7. Evolución del Harness (E4: Mínima Complejidad)
Los harnesses no son estáticos: parten del mínimo viable y evolucionan conforme se validan o invalidan las
suposiciones sobre las limitaciones del modelo.

### 7.1 Principio de Construcción Mínima
*   Se construye con el menor número de componentes que satisfagan los contratos de la fase.
*   Cada componente codifica una suposición explícita sobre una limitación del modelo (ej: "sin este evaluador
    externo, el agente auto-aprueba su trabajo"), documentada al crearlo.
*   No se agrega un componente sin antes demostrar, con evidencia de una ejecución real, que su ausencia degrada
    la calidad del output.

### 7.2 Ciclo de Re-evaluación Periódica
Al cierre de cada proyecto, **A** ejecuta antes de consolidar lecciones:
1.  **Inventario**: listar componentes activos y la suposición que cada uno cubre.
2.  **Prueba de Remoción**: remover un componente a la vez (en prueba) y medir el impacto con la rúbrica de C.
3.  **Decisión**: si la calidad cae, el componente se mantiene y su suposición se refuerza en
    `decisions_library.md`; si no cae, se elimina y se registra como lección en `lessons_learned.md`.
4.  **Exploración de Nuevas Capacidades**: verificar si capacidades nuevas del modelo justifican componentes que
    antes no existían.

### 7.3 Responsabilidades y Registro
*   **Responsable**: A, junto al análisis de cierre de proyecto.
*   **Artefacto de salida**: una entrada en `decisions_library.md` por componente evaluado, con estado
    `MANTENIDO` o `ELIMINADO` y su evidencia.
*   **Frecuencia mínima**: una re-evaluación por proyecto completado; no es opcional.

---

## Apéndice A: Estándares de Ingeniería
*   **Convención de Commits**: `tipo(fase/sprint): descripción`.
*   **Estrategia de Ramas**: ramas por sprint con merge a `main` tras gate aprobado.
*   **Selección de Modelos**: el modelo adecuado según la tarea (Opus para specs, Sonnet para ejecución).
