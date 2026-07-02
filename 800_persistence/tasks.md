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
| T-021 | Aplicar ajustes de gobernanza: vocabulario de bandas (D-029) + `feature_contract` (D-030) | 2026-07-02 | Checklist completo (6/6 ítems): (1) `700_architecture/sdd_tdd_workflow.md` v0.1→v0.2 — nueva sección §6 «Bandas y Ejes de Crecimiento». (2) `980_guideline/methodology.md` — añadido en §1 el bloque "Contratos explícitos en dos niveles (P5, D-030)" documentando `feature_contract` (adoptado) y `slice_contract` (diferido); el documento no mencionaba contratos tras el recorte de D-020, así que fue introducir el modelo, no solo reconciliar (ver L-017). (3) `600_features/README.md` — árbol de directorios y paso 2 de "Cómo arrancar" reflejan `feature_contract.md`; corregida referencia colgante `§6`→`§7` (L-017). (4) Plantilla `600_features/_template/feature_contract.md` creada. (5) `.claude/agents/feature_definer.md` — nuevo paso 2 "Escribir feature_contract.md", regla de uno por feature, pasos renumerados. (6) Retro-ajuste: creado `600_features/client_scaffold/feature_contract.md`. Ver D-029, D-030, L-017. |
| T-022 | Codificar la cadena de trazabilidad HU→CA→TSK (D-031): plantillas, agentes, `sdd_tdd_workflow.md` y retro-ajuste de `client_scaffold` | 2026-07-02 | A pedido del usuario para trazabilidad total `definition.md`→`spec.md`→`plan.md`. `definition.md` usa historias de usuario `HU-xx` (formato Connextra); `spec.md` codifica `CA-xx` enlazados a ≥1 `HU-xx` con matriz de cobertura HU→Spec; `plan.md` descompone en tareas atómicas `TSK-xx` (ID/Descripción/Entregable/Responsable/Estado/Trazabilidad→CA) con reglas de partición (un responsable, un entregable, código y test separados). El bucle TDD sigue corriendo por caso de `state.json` sin cambios de esquema; las TSK son capa de trazabilidad. Actualizadas las 3 plantillas, `feature_definer.md`, `spec_writer.md`, `plan_builder.md`, y `sdd_tdd_workflow.md` (v0.2→v0.3, regla transversal §8). Retro-ajustado `client_scaffold/tracer_bullet/`: `definition.md` (HU-01…HU-05), `spec.md` (CA-01…CA-11 + matriz), `plan.md` (nueva sección de tareas TSK-01…TSK-13, 18 casos mapeados a CA y TSK, secciones renumeradas). Ver D-031, L-018, A-009. |

## 3. Tareas En Progreso
| ID | Tarea | Prioridad | Notas |
|---|---|---|---|
| T-013 | Construir la primera feature real del sistema: `client_scaffold` (`foda client new <NAME>`), ejecutando la cadena de 8 agentes de punta a punta | 🔴 Alta | Valida A-005 (validado en gran medida). Alcance acordado con el usuario (ver D-016). Etapas completadas: 1) `feature_definer` ✅; 2) `spec_writer` ✅ (GATE APROBADO); 3) `plan_builder` ✅ (GATE APROBADO, retro-ajustado con trazabilidad D-031, GATE re-confirmado A-009 validado); 4) **bucle TDD del core cerrado** — casos 1-17 recorridos con tdd_tester→tdd_coder→tdd_refactor (varios "verde directo": 3, 5, 8, 15, 17, ver L-020), 26 tests en verde sin regresiones; caso 18 (rollback DS-2.2) **diferido** por GATE PA-3 opción (c) (D-032), no entra en esta banda. Bootstrap del paquete `foda` hecho dentro de la feature (`pyproject.toml`, src-layout, `src/foda/core/scaffold.py` con `create_client`+`_validate_name`, `tests/core/test_scaffold.py`). **Falta:** etapa `integration_tester`, etapa `spec_verifier` (`verification.md`), y cablear la capa CLI (TSK-07: `foda client new <NAME>` sobre el core, sin test en esta banda). **Próximo paso:** invocar `integration_tester` con el nombre de la feature. |

## 4. Tareas Pendientes
| ID | Tarea | Prioridad | Notas |
|---|---|---|---|
| T-023 | Cablear la capa CLI `foda client new <NAME>` (TSK-07) sobre el core `create_client` de `client_scaffold` | 🟡 Media | Sin test en esta banda (según plan). Decidir en la próxima sesión si entra en el cierre de la banda `tracer_bullet` de T-013 o si se difiere a una banda posterior; coordinar con `integration_tester`/`spec_verifier`. |

## 5. Backlog
| ID | Tarea | Notas |
|---|---|---|
| T-014 | Construir feature `client_context` (resolución de rutas, cliente nuevo vs. recurrente) | Depende de T-013 (`client_scaffold`). Orden abajo-hacia-arriba acordado en D-016. |
| T-015 | Construir feature `flow_base` (abstracción `Flow`: load_inputs → validate → execute → write_outputs) | Depende de T-014 (`client_context`). Orden abajo-hacia-arriba acordado en D-016. |
| T-024 | `client_scaffold` banda `stab_n`: escribir test que simule fallo de I/O e implementar el rollback best-effort DS-2.2 (caso 18) | Trabajo diferido por GATE PA-3 opción (c), ver D-032. |
| ~~T-017~~ | ~~Construir los agentes runtime del patrón A/B/C descrito en `980_guideline/` (`foda-governor`, `foda-<flujo>-planner`, `foda-<flujo>-evaluator`)~~ | **Cancelada por D-020** (2026-07-02): el runtime NO es agéntico; lo define exclusivamente `system_design.md`. |
| ~~T-018~~ | ~~Reconciliar por completo el plano runtime descrito en `980_guideline/` (`fda-*-state.json`, `install.sh`, distinción planos MOTOR/INSTANCIA) con la arquitectura ya construida~~ | **Cancelada por D-020** (2026-07-02): se descartan MOTOR/INSTANCIA y `fda-*-state.json`; no hay plano runtime que reconciliar. |
| T-020 | Diseñar las rúbricas calibradas concretas (dimensiones+pesos, few-shot, anclas) para las salidas no deterministas de Discovery y Exploration | Trabajo futuro identificado en D-022. Se hará al construir esos flujos, después de T-013/T-014/T-015. |
