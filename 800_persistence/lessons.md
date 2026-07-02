# Lessons — Lecciones Aprendidas

> Este archivo registra las **lecciones aprendidas** durante el proyecto para no repetir errores y reforzar lo que funciona.

---

## Índice
1. [Cómo Registrar una Lección](#1-cómo-registrar-una-lección)
2. [Lecciones Técnicas](#2-lecciones-técnicas)
3. [Lecciones de Proceso](#3-lecciones-de-proceso)
4. [Lecciones de Producto/Negocio](#4-lecciones-de-productonegocio)

---

## 1. Cómo Registrar una Lección
Cada lección incluye: **ID**, **contexto** (qué pasó), **lección** (qué aprendimos) y **acción** (qué haremos distinto).

## 2. Lecciones Técnicas
| ID | Contexto | Lección | Acción |
|---|---|---|---|
| L-002 | Se invocó `foda-status` con frontmatter `model: sonnet` esperando que corriera en Sonnet, pero la sesión estaba en Haiku 4.5. | El frontmatter `model:` solo aplica a agentes/subagentes; las skills invocadas inline con slash command corren siempre en el modelo de la sesión activa. | Para fijar el modelo por protocolo, usar subagentes (herramienta Agent) en vez de skills inline. |
| L-003 | Al migrar los protocolos a subagentes, el cierre de sesión no tenía acceso al historial de la conversación. | Los subagentes arrancan en frío (sin historial); el protocolo de cierre depende de que la sesión principal le entregue un resumen completo de lo trabajado. | El agente `session_closer` exige recibir el resumen de sesión en el prompt antes de actualizar los 5 archivos. |

## 3. Lecciones de Proceso
| ID | Contexto | Lección | Acción |
|---|---|---|---|
| L-001 | Arranque del proyecto | Definir persistencia y protocolos desde el inicio da trazabilidad y continuidad entre sesiones. | Mantener disciplina: ejecutar `foda-next` al iniciar y `foda-status` al cerrar. |
| L-004 | Se diseñó `700_architecture/system_design.md` definiendo primero principios (determinista por defecto, LLM aislado, artefactos como contrato entre flujos) antes de codificar. | Definir principios de diseño antes de codificar produce una arquitectura testeable y reproducible. | Mantener el documento de diseño como referencia obligatoria antes de iniciar cualquier construcción de código. |
| L-005 | Se diseñó una cadena de 8 agentes de desarrollo SDD/TDD; los subagentes de Claude Code son efímeros (arranque en frío) y no se pueden pausar/reanudar como procesos vivos. | La resumibilidad de un flujo multi-etapa entre sesiones se logra con checkpointing a disco (artefactos + `state.json`), no con estado en memoria del agente; cada etapa debe ser atómica para poder reanudar limpiamente. | Diseñar todo flujo largo orquestado por subagentes con persistencia en disco por etapa y re-invocación desde el último checkpoint. |
| L-006 | Al migrar de skills a subagentes (T-006/D-005) quedó una referencia colgante a las skills `foda-next`/`foda-status` ya eliminadas, mencionada dentro del `description` e "Instrucción principal" de `session_starter.md`/`session_closer.md`. Además se detectó que los cambios hechos en `CLAUDE.md` durante una sesión no se recargan en la sesión en curso (se lee solo al arrancar). | Mantener una única fuente de verdad por artefacto evita desincronización entre documentos que describen el mismo protocolo; los cambios a `CLAUDE.md` solo surten efecto pleno a partir de la siguiente sesión. | El detalle paso a paso del protocolo de sesión vive únicamente en `.claude/agents/session_starter.md` y `session_closer.md`; `CLAUDE.md` solo delega e invoca por frase-gatillo. Ver D-009. |
| L-007 | Se validó `700_architecture/system_design.md` (16 secciones) con el usuario en una sola sesión. | Agrupar las secciones en bloques temáticos afines y hacer preguntas concretas al final de cada bloque (en vez de sección por sección o el documento completo de una vez) permitió validar un documento largo de forma eficiente, con feedback puntual y accionable. | Para futuras revisiones de documentos extensos con el usuario, organizar la revisión en bloques temáticos con checkpoints de confirmación. |

## 4. Lecciones de Producto/Negocio
| ID | Contexto | Lección | Acción |
|---|---|---|---|
| — | _Sin registros aún._ | — | — |
