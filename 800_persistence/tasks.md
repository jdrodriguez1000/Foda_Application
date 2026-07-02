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

## 3. Tareas En Progreso
| ID | Tarea | Prioridad | Notas |
|---|---|---|---|
| — | _Ninguna._ | — | — |

## 4. Tareas Pendientes
| ID | Tarea | Prioridad | Notas |
|---|---|---|---|
| T-013 | Construir la primera feature real del sistema: `client_scaffold` (`foda client new <NAME>`), ejecutando la cadena de 8 agentes de punta a punta | 🔴 Alta | Valida A-005. Alcance acordado con el usuario (ver D-016): crear árbol de carpetas de cliente nuevo (`client.yaml`, `010_inputs/`, `020_outputs/`, `data/{bronze,silver,gold}/`, `models/`), validar nombre (patrón seguro, sin normalización), fallar si el cliente ya existe (sin `--force` por ahora), función core `create_client(...)` con capa CLI fina encima. Fuera de alcance: `ClientContext`, flujos, sub-carpetas por flujo. Próximo paso: invocar `feature_definer`. Andamiaje completo (T-009/T-010/T-011), sin bloqueos. |

## 5. Backlog
| ID | Tarea | Notas |
|---|---|---|
| T-014 | Construir feature `client_context` (resolución de rutas, cliente nuevo vs. recurrente) | Depende de T-013 (`client_scaffold`). Orden abajo-hacia-arriba acordado en D-016. |
| T-015 | Construir feature `flow_base` (abstracción `Flow`: load_inputs → validate → execute → write_outputs) | Depende de T-014 (`client_context`). Orden abajo-hacia-arriba acordado en D-016. |
