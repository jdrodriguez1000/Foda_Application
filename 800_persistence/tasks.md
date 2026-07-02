# Tasks — Tareas del Proyecto

> Este archivo responde a: **¿Qué se hizo y qué falta?** Lista las tareas realizadas y las próximas a realizar.

---

## Índice
1. [Convenciones](#1-convenciones)
2. [Tareas Completadas](#2-tareas-completadas)
3. [Tareas En Progreso](#3-tareas-en-progreso)
4. [Tareas Pendientes](#4-tareas-pendientes)
5. [Backlog](#5-backlog)

---

## 1. Convenciones
- **ID:** identificador único (T-001, T-002, ...).
- **Estado:** ✅ Completada · 🔄 En progreso · ⏳ Pendiente · 🧊 Backlog.
- **Prioridad:** 🔴 Alta · 🟡 Media · 🟢 Baja.

## 2. Tareas Completadas
| ID | Tarea | Fecha | Notas |
|---|---|---|---|
| T-001 | Crear estructura `800_persistence` con archivos de seguimiento | 2026-07-01 | 5 archivos creados con índice. |
| T-003 | Crear `CLAUDE.md` con protocolos de inicio y cierre de sesión | 2026-07-01 | Incluye paso final de commit y push a Git. |
| T-004 | Inicializar repositorio Git y configurar remoto `origin` (rama `main`) | 2026-07-01 | Remoto: Foda_Application.git. |
| T-005 | Crear skills de proyecto `foda-next` y `foda-status` | 2026-07-01 | En `.claude/skills/`. Reemplazadas por T-006. |
| T-006 | Migrar protocolos de inicio/cierre de skills a subagentes (`session_starter`, `session_closer`) y eliminar skills antiguas | 2026-07-01 | Ver D-005. `session_starter` en model `haiku`, `session_closer` en model `sonnet`. |
| T-002 | Definir alcance y requerimientos del proyecto | 2026-07-01 | Alcance definido a partir de `990_documents/expected_workflow.md` y `current_state.md`, y del diseño de arquitectura. Se seguirá afinando iterativamente. |
| T-007 | Análisis y documento de diseño de arquitectura del sistema (`700_architecture/system_design.md` v0.1) | 2026-07-01 | Borrador con 16 secciones; pendiente de validación con el usuario (ver T-008). |
| T-012 | Corregir subagentes de sesión (referencias rotas a skills `foda-next`/`foda-status` ya eliminadas), eliminar duplicación CLAUDE.md↔agentes estableciendo fuente única de verdad en los agentes, y establecer invocación por frase-gatillo ("iniciemos/cerremos la sesión") | 2026-07-01 | Ver D-009 y L-006. Archivos: `CLAUDE.md`, `.claude/agents/session_starter.md`, `.claude/agents/session_closer.md`. |
| T-008 | Revisar y validar `700_architecture/system_design.md` con el usuario, sección por sección | 2026-07-01 | 16 secciones en 5 bloques, todas confirmadas. Documento actualizado de v0.1 a v0.2. Ver D-010 a D-014, A-004 (validado), L-007. |
| T-009 | Construir los 8 agentes de desarrollo SDD/TDD en `.claude/agents/` (`feature_definer`, `spec_writer`, `plan_builder`, `tdd_tester`, `tdd_coder`, `tdd_refactor`, `integration_tester`, `spec_verifier`) con los modelos y colores acordados | 2026-07-02 | Ver D-008, D-015. Renombrados `tdd_red`→`tdd_tester`, `tdd_green`→`tdd_coder`. Tools mínimas: Read, Glob, Grep, Write, Edit, Bash (sin Agent/web). |
| T-010 | Documentar la convención de `state.json` y la orquestación de la cadena SDD/TDD en `700_architecture/sdd_tdd_workflow.md` | 2026-07-02 | Ver D-008, D-015. Fuente única de verdad de la cadena SDD/TDD (v0.1). |
| T-011 | Crear la estructura de carpetas `600_features/` con una plantilla/ejemplo de feature | 2026-07-02 | `README.md` + `_template/` con esqueletos de los 4 documentos + `state.json` inicial. Sin feature de ejemplo ficticia (decisión del usuario); la primera feature real cumplirá ese rol. |
| T-016 | Reconciliar `980_guideline/` (`principles.md`, `methodology.md`) con lo ya construido: reparar `principles.md` como canon vinculante, insertar cláusula de lectura obligatoria en los 10 agentes, importar en `CLAUDE.md`, reorganizar `methodology.md` con mapa de fuentes y resolver contradicciones/citas fantasma | 2026-07-02 | Ver D-017, D-018, D-019, L-009, L-010, L-011. Sesión de gobernanza/reconciliación, sin código de aplicación. Genera T-017/T-018 como trabajo futuro (agentes runtime y plano runtime), luego canceladas por D-020. |
| T-019 | Revertir el runtime agéntico importado por la metodología: recortar `980_guideline/methodology.md` a "Metodología de Desarrollo del Motor" y formalizar la reversión al runtime determinista de `system_design.md` | 2026-07-02 | Ver D-020, D-021, D-022, L-012, L-013, L-014. El usuario reportó sentirse perdido con la complejidad agregada por la metodología importada; se contrastó contra `system_design.md` (D-006) y se decidió revertir. Se rescataron solo dos piezas de la metodología: Single Writer Rule (D-021) y rúbrica de evaluación calibrada para salidas no deterministas (D-022). Cancela T-017/T-018. |

## 3. Tareas En Progreso
| ID | Tarea | Prioridad | Notas |
|---|---|---|---|
| T-013 | Construir la primera feature real del sistema: `client_scaffold` (`foda client new <NAME>`), ejecutando la cadena de 8 agentes de punta a punta | 🔴 Alta | Valida A-005. Alcance acordado con el usuario (ver D-016). Etapas completadas: 1) `feature_definer` ✅ (`definition.md`, commit `453a386`); 2) `spec_writer` ✅ (`spec.md`, commit `bb3b60a`, GATE humano APROBADO — resolvió DS-1/D-023, DS-2/D-024, DS-3/D-025, 11 criterios de aceptación); 3) `plan_builder` ✅ (`plan.md` con 18 casos TDD, commit `0c2d682`, GATE humano APROBADO — confirmó PA-1/D-026 adoptar PyYAML, PA-2/D-027 bootstrap del paquete dentro de la feature, PA-3/D-028 caso 18 sin test en tracer_bullet). Sesión SUSPENDIDA antes de arrancar el bucle TDD. **Próximo paso:** invocar `tdd_tester` con el caso TDD #1 (crea `tmp/ABC/` y devuelve su Path). |

## 4. Tareas Pendientes
| ID | Tarea | Prioridad | Notas |
|---|---|---|---|
| — | _Ninguna._ | — | — |

## 5. Backlog
| ID | Tarea | Notas |
|---|---|---|
| T-014 | Construir feature `client_context` (resolución de rutas, cliente nuevo vs. recurrente) | Depende de T-013 (`client_scaffold`). Orden abajo-hacia-arriba acordado en D-016. |
| T-015 | Construir feature `flow_base` (abstracción `Flow`: load_inputs → validate → execute → write_outputs) | Depende de T-014 (`client_context`). Orden abajo-hacia-arriba acordado en D-016. |
| ~~T-017~~ | ~~Construir los agentes runtime del patrón A/B/C descrito en `980_guideline/` (`foda-governor`, `foda-<flujo>-planner`, `foda-<flujo>-evaluator`)~~ | **Cancelada por D-020** (2026-07-02): el runtime NO es agéntico; lo define exclusivamente `system_design.md`. |
| ~~T-018~~ | ~~Reconciliar por completo el plano runtime descrito en `980_guideline/` (`fda-*-state.json`, `install.sh`, distinción planos MOTOR/INSTANCIA) con la arquitectura ya construida~~ | **Cancelada por D-020** (2026-07-02): se descartan MOTOR/INSTANCIA y `fda-*-state.json`; no hay plano runtime que reconciliar. |
| T-020 | Diseñar las rúbricas calibradas concretas (dimensiones+pesos, few-shot, anclas) para las salidas no deterministas de Discovery y Exploration | Trabajo futuro identificado en D-022. Se hará al construir esos flujos, después de T-013/T-014/T-015. |
