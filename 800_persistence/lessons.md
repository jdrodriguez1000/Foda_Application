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
| L-008 | Al construir los 8 agentes de desarrollo (T-009) se definió `state.json` inline y de forma repetida en cada uno de los 8 archivos de agente, duplicando la convención 8 veces. | Duplicar una convención compartida en múltiples archivos autosuficientes crea riesgo de desincronización (p. ej. si cambia el esquema de `state.json`, hay que tocar 8 archivos). Consolidarla en un único documento de referencia (`700_architecture/sdd_tdd_workflow.md`, T-010) reduce ese riesgo, aunque los agentes siguen sin referenciarlo explícitamente. | Punto abierto: evaluar que los agentes de desarrollo referencien `sdd_tdd_workflow.md` en vez de repetir la convención de `state.json` inline. |
| L-009 | El usuario entregó `980_guideline/methodology.md` y `principles.md`, que duplicaban parcialmente contenido ya presente en `system_design.md` y `sdd_tdd_workflow.md` (los 14 flujos/medallion, los P/E), y contenían citas a decisiones inexistentes (D-021, D-029). | Cuando llega documentación de guía nueva que se solapa con documentos ya existentes, conviene primero construir un mapa de "fuente única de verdad" por tema (qué documento es dueño de qué contenido) antes de editar ninguno, para no propagar la duplicación ni dejar citas fantasma sin resolver. | Se añadió a `methodology.md` una sección "Mapa de fuentes" (§0) que asigna cada tema a su dueño canónico; las citas fantasma se formalizaron como ADR reales (D-017, D-018) en vez de dejarlas colgando. |
| L-010 | Se necesitaba que los 10 agentes de `.claude/agents/` (que arrancan en frío) se comportaran según `980_guideline/principles.md`, pero un import `@` en `CLAUDE.md` solo se resuelve de forma garantizada en la sesión principal, no en subagentes invocados vía Task/Agent. | La vía robusta para vincular un subagente efímero a una guía de comportamiento es una cláusula explícita "lee X primero" dentro de la definición del propio agente (mecanismo independiente de versión de Claude Code), no confiar en que la herencia de `CLAUDE.md`/imports `@` llegue a los subagentes. | Se insertó la misma cláusula vinculante bajo el H1 de los 10 agentes, referenciando `980_guideline/principles.md` como fuente única (sin copiar su contenido). |
| L-011 | Al reconciliar la carpetería step-céntrica de D-017 (`703/705/710/720/<banda>/<flujo>/`) contra la feature-céntrica `600_features/<feature>/` ya en uso, se optó por insertar `<banda>` como subcarpeta y aplicar `replace_all` de la subcadena de ruta única `600_features/<feature>/` en los 8 agentes. | Un `replace_all` sobre una subcadena de ruta suficientemente única (que no aparece en ningún otro contexto del archivo) es una forma segura y limpia de propagar un cambio estructural repetido en varios archivos; conviene verificar después por grep que no queden rutas sin banda ni duplicaciones `<banda>/<banda>/`. | Verificado por grep tras el cambio: sin dobles `<banda>/<banda>/` ni rutas `600_features/<feature>/` residuales sin banda en los 8 agentes. |

## 4. Lecciones de Producto/Negocio
| ID | Contexto | Lección | Acción |
|---|---|---|---|
| — | _Sin registros aún._ | — | — |
