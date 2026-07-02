# Progress — Estado del Proyecto

> Este archivo responde a: **¿Cómo va el proyecto?** Muestra el avance general, lo realizado y lo próximo a realizar.

---

## Índice
1. [Resumen del Estado](#1-resumen-del-estado)
2. [Métricas de Avance](#2-métricas-de-avance)
3. [Lo Realizado](#3-lo-realizado)
4. [En Progreso](#4-en-progreso)
5. [Próximo a Realizar](#5-próximo-a-realizar)
6. [Bloqueos y Riesgos](#6-bloqueos-y-riesgos)
7. [Historial de Actualizaciones](#7-historial-de-actualizaciones)

---

## 1. Resumen del Estado
- **Proyecto:** Foda_Application
- **Fase actual:** Diseño de arquitectura del sistema (validación pendiente con el usuario)
- **Estado general:** 🟡 En diseño
- **Última actualización:** 2026-07-01

## 2. Métricas de Avance
| Métrica | Valor |
|---|---|
| Avance global | 25% (alcance definido + diseño de arquitectura v0.1 + diseño de cadena SDD/TDD acordado, sin construir; sesión actual fue mantenimiento de infraestructura de protocolos, sin avance funcional) |
| Tareas completadas | 8 |
| Tareas pendientes | 4 |

## 3. Lo Realizado
- Creación de la estructura de persistencia (`800_persistence`) con los 5 archivos de seguimiento.
- Creación de `CLAUDE.md` con Protocolo de Inicio y Protocolo de Cierre de Sesión (incluye commit y push a Git).
- Inicialización del repositorio Git, configuración del remoto `origin` y rama `main`.
- Migración de los protocolos de inicio/cierre de skills de proyecto a subagentes: se crearon `session_starter` (model `haiku`, protocolo foda-next) y `session_closer` (model `sonnet`, protocolo foda-status) en `.claude/agents/`, y se eliminaron las skills antiguas `foda-next` y `foda-status` (junto con la carpeta `.claude/skills/`). Motivo: el frontmatter `model:` no aplica a skills invocadas inline, solo a agentes.
- La sesión principal ahora se ejecuta en Opus 4.8 (fijado como default vía `/model`).
- Se leyeron y analizaron `990_documents/expected_workflow.md` (pipeline esperado de ~14 flujos) y `990_documents/current_state.md` (situación actual del negocio Triple S / Sabbia).
- Se definió el alcance del negocio: planeación de demanda con ML, modelo objetivo Service as a Software (SaaSw), automatización 85-95%, científico de datos como revisor/aprobador; se predice demanda de productos, no ventas.
- El usuario fijó restricciones de diseño clave: CLI sin frontend, Python, determinista por defecto con LLM aislado, multi-tenant por carpeta-por-cliente en disco (sin BD), entrada YAML / salida JSON, datos crudos a capa bronze, cliente nuevo genera modelo / cliente recurrente reutiliza modelo, estructura de carpetas por flujo con prefijos numéricos.
- Se creó `700_architecture/system_design.md` (v0.1, borrador) con el diseño completo de arquitectura: contexto, principios, restricciones (R1-R9), visión general, modelo de los 14 flujos, clasificación por determinismo, estructura de carpetas, contrato de artefactos, abstracción `Flow`/`ClientContext`, capas medallion, interfaz CLI, caminos nuevo vs recurrente, multi-tenant, encapsulamiento del LLM, detalle por flujo y puntos abiertos.
- Se diseñó (a nivel conceptual, sin construir código) la cadena de 8 **agentes de desarrollo** SDD/TDD (`feature_definer`, `spec_writer`, `plan_builder`, `tdd_red`, `tdd_green`, `tdd_refactor`, `integration_tester`, `spec_verifier`), con modelos/colores asignados, gates humanos tras spec y plan, bucle red→green→refactor por caso de test, política de reintento (máx. 2) y escalamiento a humano, commit por etapa, y persistencia en disco vía `state.json` por feature (los subagentes son efímeros; la resumibilidad depende de checkpoints en disco). Se definió la distinción entre agentes de desarrollo (construyen la app) y agentes de runtime (Discovery, Ingestion, etc., que son la app). Se acordó la estructura de artefactos por feature en `600_features/<feature>/`.
- Sesión de mantenimiento de infraestructura de protocolos (T-012, D-009, L-006): se corrigieron referencias colgantes a las skills `foda-next`/`foda-status` (ya eliminadas en T-006) dentro de `.claude/agents/session_starter.md` y `.claude/agents/session_closer.md`; se eliminó la duplicación del protocolo entre `CLAUDE.md` y los agentes, dejando el detalle paso a paso solo en los agentes (fuente única de verdad) y reduciendo `CLAUDE.md` §1/§2 a una política corta que delega e invoca por frase-gatillo ("iniciemos la sesión" / "cerremos la sesión"). No hubo cambios de código de aplicación ni de arquitectura.

## 4. En Progreso
- _Ninguna tarea en progreso._

## 5. Próximo a Realizar
- Revisar y validar `700_architecture/system_design.md` con el usuario, sección por sección (T-008).
- Construir los 8 agentes de desarrollo SDD/TDD en `.claude/agents/` (T-009).
- Documentar la convención de `state.json` y la orquestación de la cadena SDD/TDD en `700_architecture/sdd_tdd_workflow.md` (T-010).
- Crear la estructura de carpetas `600_features/` con una plantilla/ejemplo de feature (T-011).

## 6. Bloqueos y Riesgos
- _Ninguno registrado._

## 7. Historial de Actualizaciones
| Fecha | Cambio |
|---|---|
| 2026-07-01 | Creación inicial del archivo. |
| 2026-07-01 | Cierre de sesión: andamiaje del proyecto (persistencia, CLAUDE.md, Git, skills). |
| 2026-07-01 | Sesión de verificación: sin trabajo nuevo, sigue a la espera de que el usuario defina el alcance del proyecto (T-002). |
| 2026-07-01 | Migración de protocolos de skills a subagentes (`session_starter`, `session_closer`); eliminación de skills antiguas `foda-next`/`foda-status`; sesión principal fijada en Opus 4.8. Sigue pendiente T-002. |
| 2026-07-01 | T-002 completada: alcance definido a partir de `990_documents/expected_workflow.md` y `current_state.md`. Se creó `700_architecture/system_design.md` v0.1 con el diseño de arquitectura del sistema (14 flujos, determinismo por defecto, LLM aislado, multi-tenant en disco, CLI en Python). Pendiente validación del documento con el usuario antes de iniciar desarrollo. |
| 2026-07-01 | Sesión de diseño (sin código): se acordó la cadena de 8 agentes de desarrollo SDD/TDD y su orquestación (gates humanos, bucle TDD, checkpoint en disco vía `state.json`, `600_features/`). Registradas T-009, T-010, T-011 como pendientes; T-008 sigue vigente. Ver D-008, L-005, A-005. |
| 2026-07-01 | Sesión de mantenimiento (T-012): corregidas referencias colgantes a skills eliminadas en `session_starter`/`session_closer`; eliminada duplicación del protocolo entre `CLAUDE.md` y los agentes (fuente única de verdad en los agentes); invocación por frase-gatillo. Sin cambios de código ni de arquitectura. Ver D-009, L-006. |
