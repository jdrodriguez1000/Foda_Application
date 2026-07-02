# Decisions — Decisiones del Proyecto

> Este archivo registra las **decisiones tomadas** en el proyecto (estilo ADR: Architecture Decision Record) para dejar traza del porqué de cada elección.

---

## Índice
1. [Cómo Registrar una Decisión](#1-cómo-registrar-una-decisión)
2. [Índice de Decisiones](#2-índice-de-decisiones)
3. [Detalle de Decisiones](#3-detalle-de-decisiones)

---

## 1. Cómo Registrar una Decisión
Cada decisión sigue el formato: **ID**, **título**, **estado** (Propuesta / Aceptada / Rechazada / Reemplazada), **contexto**, **decisión** y **consecuencias**.

## 2. Índice de Decisiones
| ID | Título | Estado | Fecha |
|---|---|---|---|
| D-001 | Estructura de persistencia en `800_persistence` | Aceptada | 2026-07-01 |
| D-002 | Protocolos de sesión en `CLAUDE.md` | Aceptada | 2026-07-01 |
| D-003 | Cierre de sesión finaliza con commit y push a Git | Aceptada | 2026-07-01 |
| D-004 | Skills de proyecto para inicio y cierre de sesión | Reemplazada por D-005 | 2026-07-01 |
| D-005 | Migrar protocolos de inicio/cierre de skills a subagentes | Aceptada | 2026-07-01 |
| D-006 | Arquitectura del sistema como pipeline de flujos deterministas con artefactos como contrato | Aceptada | 2026-07-01 |
| D-007 | Crear carpeta `700_architecture/` para documentación de arquitectura | Aceptada | 2026-07-01 |
| D-008 | Adoptar metodología SDD + TDD mediante una cadena de 8 agentes de desarrollo | Aceptada | 2026-07-01 |

## 3. Detalle de Decisiones

### D-001 — Estructura de persistencia en `800_persistence`
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** Se necesita un seguimiento persistente del proyecto (avance, tareas, lecciones, decisiones y supuestos).
- **Decisión:** Crear la carpeta `800_persistence` con 5 archivos (`progress.md`, `tasks.md`, `lessons.md`, `decisions.md`, `assumptions.md`), cada uno con índice para búsqueda rápida.
- **Consecuencias:** Documentación centralizada y consultable sin leer todo el proyecto. Requiere mantener los archivos actualizados.

### D-002 — Protocolos de sesión en `CLAUDE.md`
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** Se requiere consistencia entre sesiones y agentes al trabajar en el proyecto.
- **Decisión:** Definir en `CLAUDE.md` un Protocolo de Inicio (lectura obligatoria de `progress.md` y `tasks.md`, a demanda del resto, siempre usando el índice) y un Protocolo de Cierre (actualizar los 5 archivos).
- **Consecuencias:** Arranque y cierre estandarizados; lectura eficiente vía índices.

### D-003 — Cierre de sesión finaliza con commit y push a Git
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** Se busca versionar y respaldar el trabajo de cada sesión.
- **Decisión:** El Protocolo de Cierre termina con `git add`, `commit` y `push` al remoto `https://github.com/jdrodriguez1000/Foda_Application.git` (rama `main`).
- **Consecuencias:** Historial y respaldo remoto por sesión; requiere credenciales/acceso al repositorio.

### D-004 — Skills de proyecto para inicio y cierre de sesión
- **Estado:** Reemplazada por D-005
- **Fecha:** 2026-07-01
- **Contexto:** Facilitar la ejecución de los protocolos con comandos.
- **Decisión:** Crear las skills de proyecto `foda-next` (inicio) y `foda-status` (cierre) en `.claude/skills/`.
- **Consecuencias:** Los protocolos se invocan con `/foda-next` y `/foda-status`. Se descubrió que el frontmatter `model:` no aplica a skills inline, lo que motivó la migración a subagentes (ver D-005). Las skills fueron eliminadas.

### D-005 — Migrar los protocolos de inicio/cierre de skills a subagentes
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** Las skills invocadas con slash command corren inline en el modelo de la sesión principal; el frontmatter `model:` de la skill no tiene efecto. Esto impedía fijar un modelo económico (Haiku) para el inicio de sesión y uno más capaz (Sonnet) para el cierre.
- **Decisión:** Reemplazar las skills `foda-next` y `foda-status` por dos subagentes en `.claude/agents/`: `session_starter` (model `haiku`, color amarillo, ejecuta el protocolo de inicio) y `session_closer` (model `sonnet`, color verde, ejecuta el protocolo de cierre). La sesión principal pasa a ejecutarse en Opus. Se eliminaron las skills antiguas y la carpeta `.claude/skills/`.
- **Consecuencias:** Se gana control del modelo por protocolo (economía en el inicio, capacidad en el cierre). Se pierde la invocación directa por slash command; ahora se invocan vía la herramienta Agent. Como los subagentes arrancan en frío, el cierre de sesión depende de que la sesión principal le entregue un resumen completo de lo trabajado.

### D-006 — Arquitectura del sistema como pipeline de flujos deterministas con artefactos como contrato
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** Triple S necesita replicar la lógica del científico de datos de forma escalable, migrando de un modelo manual a un modelo Service as a Software (SaaSw) que automatice 85-95% del trabajo, dejando al científico de datos como revisor/aprobador.
- **Decisión:** CLI en Python; multi-tenant por carpeta-por-cliente en disco (sin BD); capas medallion (bronze/silver/gold); YAML como entrada (config/decisión humana) y JSON como salida (resultado máquina); LLM encapsulado y usado solo en los flujos Discovery y Exploration; el resto del pipeline es determinista; abstracción común `Flow` (load_inputs → validate → execute → write_outputs) y `ClientContext`; caminos de ejecución diferenciados para cliente nuevo (genera modelo) vs cliente recurrente (reutiliza modelo). Documentado en `700_architecture/system_design.md`.
- **Consecuencias:** Core reproducible y testeable al aislar el LLM en dos flujos concretos. El documento es vivo y se afinará iterativamente. La persistencia en archivos (sin BD) puede migrar a base de datos en el futuro detrás de la abstracción `ClientContext` sin afectar al resto del sistema.

### D-007 — Crear carpeta `700_architecture/` para documentación de arquitectura
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** Se necesitaba un lugar para la documentación técnica de arquitectura, separado de `990_documents/` que guarda los documentos de negocio entregados por el usuario.
- **Decisión:** Crear `700_architecture/` y ubicar allí `system_design.md`.
- **Consecuencias:** Separación clara entre documentos de negocio (entrada) y documentos de diseño técnico (producidos por el equipo/agentes).

### D-008 — Adoptar metodología SDD + TDD mediante una cadena de 8 agentes de desarrollo
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** Se necesita construir la aplicación de forma disciplinada, trazable y reanudable, distinguiendo los **agentes de desarrollo** (que construyen la app) de los **agentes de runtime** (Discovery, Ingestion, etc., que son la app en sí). Los subagentes de Claude Code son efímeros (ver L-005), por lo que la reanudación de un flujo multi-etapa requiere checkpoint en disco.
- **Decisión:** Definir una cadena de 8 agentes de desarrollo en inglés snake_case: `feature_definer` (Sonnet, blue, produce `definition.md` e inicializa `state.json`), `spec_writer` (Opus, cyan, produce `spec.md`, GATE humano), `plan_builder` (Opus, purple, produce `plan.md` y enumera `tdd.cases`, GATE humano), `tdd_red` (Sonnet, red), `tdd_green` (Sonnet, green, reintenta máx. 2 veces y escala a humano si falla), `tdd_refactor` (Sonnet, orange), `integration_tester` (Sonnet, yellow) y `spec_verifier` (Opus, pink, produce `verification.md`). Orquestación: la sesión principal (Opus) encadena automáticamente tras `feature_definer`, con gates humanos obligatorios tras `spec_writer` y `plan_builder`. Bucle TDD: un caso de test a la vez, ciclo red→green→refactor hasta agotar los casos del plan. Commit por etapa. Persistencia por feature en `600_features/<feature>/` (`definition.md`, `spec.md`, `plan.md`, `verification.md`, `state.json` como máquina de estado con `feature`, `status`, `current_stage`, `stages{...}`); el código y los tests van a `src/foda/` y `tests/`, no dentro de `600_features/`.
- **Consecuencias:** Desarrollo estructurado, auditable y con human-in-the-loop antes de codificar. Requiere construir los 8 agentes y documentar la convención de `state.json` en una sesión futura (T-009, T-010, T-011). El diseño no se ha validado aún ejecutándolo (ver A-005).
