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
| D-009 | Fuente única de verdad de los protocolos de sesión en los archivos de los subagentes; CLAUDE.md delega e invoca por frase-gatillo | Aceptada | 2026-07-01 |
| D-010 | Python 3.13+ como versión obligatoria (R1) | Aceptada | 2026-07-01 |
| D-011 | Versionado de modelos ML en disco con puntero `latest`, en vez de sobrescribir un único `best_model.pkl` | Aceptada | 2026-07-01 |
| D-012 | Exports/descargables ubicados dentro de `020_outputs/<flujo>/`, sin carpeta `exports/` separada | Aceptada | 2026-07-01 |
| D-013 | API de Anthropic (Claude) como proveedor LLM por defecto, tras la abstracción `src/foda/llm/` | Aceptada | 2026-07-01 |
| D-014 | Los contratos de flujo permiten dependencias multi-flujo (no solo del flujo inmediatamente anterior) | Aceptada | 2026-07-01 |
| D-015 | Renombrar `tdd_red`→`tdd_tester` y `tdd_green`→`tdd_coder`; tools mínimas para los 8 agentes de desarrollo | Aceptada | 2026-07-02 |
| D-016 | Primera feature real = `client_scaffold`; orden de construcción abajo-hacia-arriba (client_scaffold → client_context → flow_base → flujos) | Aceptada | 2026-07-02 |

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

### D-009 — Fuente única de verdad de los protocolos de sesión en los archivos de los subagentes; CLAUDE.md delega e invoca por frase-gatillo
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** El protocolo de sesión estaba escrito 3 veces (`CLAUDE.md`, `session_starter.md`, `session_closer.md`), lo que causó una referencia colgante a las skills `foda-next`/`foda-status` ya eliminadas (ver T-006/D-005) dentro de los agentes, y riesgo de desincronización futura entre los tres documentos. Además, nada ordenaba invocar `session_starter`/`session_closer`, por lo que no se ejecutaban automáticamente al iniciar/cerrar sesión.
- **Decisión:** (a) el detalle paso a paso del protocolo vive únicamente en `.claude/agents/session_starter.md` y `.claude/agents/session_closer.md`, cada uno declarado explícitamente como fuente única de verdad; (b) `CLAUDE.md` §1/§2 se reduce a una política corta que delega en los subagentes, sin repetir pasos ni detalle de git ni de lectura por índice; (c) la invocación se dispara por frase-gatillo dicha por el usuario a la sesión principal: "iniciemos la sesión" invoca `session_starter`, "cerremos la sesión" invoca `session_closer` (con el resumen de la sesión en el prompt). No se usan hooks.
- **Consecuencias:** Se elimina la duplicación y la referencia colgante a skills eliminadas. `CLAUDE.md` queda más corto y estable; los agentes son autosuficientes al arrancar en frío. La invocación depende de que el usuario (o la sesión principal) use la frase-gatillo; se descartó por ahora un hook `SessionStart` automático por simplicidad, quedando como opción futura. Complementa/continúa D-005.

### D-010 — Python 3.13+ como versión obligatoria (R1)
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** Al validar la sección 3 (restricciones) de `system_design.md` con el usuario, la restricción R1 decía solo "Python" sin versión mínima.
- **Decisión:** Fijar Python 3.13+ como versión mínima obligatoria para todo el proyecto.
- **Consecuencias:** Se puede usar sintaxis y librerías compatibles solo con 3.13+; hay que verificar disponibilidad de esa versión en los entornos de despliegue/cliente.

### D-011 — Versionado de modelos ML en disco con puntero `latest`
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** El diseño original (v0.1) de la sección 7 (estructura de carpetas) guardaba un único `models/best_model.pkl`, sobrescribiéndolo en cada reentrenamiento, sin trazabilidad de versiones anteriores.
- **Decisión:** `models/` pasa a tener subcarpetas por versión (ej. `2026-07_v1/best_model.pkl` + metadatos) y un puntero `latest` que señala a la versión vigente.
- **Consecuencias:** Se gana trazabilidad y capacidad de rollback entre versiones de modelo; Inferences y otros flujos consumidores deben resolver el modelo vigente vía `models/latest` en lugar de una ruta fija. Aumenta ligeramente la complejidad de gestión de archivos.

### D-012 — Exports/descargables dentro de `020_outputs/<flujo>/`
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** El diseño original (v0.1) contemplaba una carpeta `exports/` separada para artefactos descargables (csv/xlsx de Profiling, Reporting, etc.).
- **Decisión:** Los artefactos descargables se guardan dentro de `020_outputs/<flujo>/`, junto con el resto de las salidas de ese flujo, sin carpeta `exports/` separada.
- **Consecuencias:** Estructura de carpetas más simple y consistente (todo lo que produce un flujo vive bajo su propio `020_outputs/<flujo>/`); no hay una ubicación centralizada única para todos los descargables del cliente.

### D-013 — API de Anthropic (Claude) como proveedor LLM por defecto
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** La sección 14 (encapsulamiento LLM) de `system_design.md` dejaba abierto qué proveedor LLM se usaría tras la abstracción `src/foda/llm/`.
- **Decisión:** Definir la API de Anthropic (Claude) como proveedor LLM por defecto, manteniendo la abstracción de `src/foda/llm/` para poder cambiar de proveedor/modelo sin tocar los flujos (Discovery, Exploration) que lo consumen.
- **Consecuencias:** Se simplifica la implementación inicial al fijar un proveedor concreto; el cambio a otro proveedor en el futuro requiere solo tocar la capa de abstracción, no los flujos.

### D-014 — Contratos de flujo con dependencias multi-flujo
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** El diseño original (v0.1) de la tabla de contratos de artefactos (sección 8) asumía implícitamente que cada flujo solo depende de los artefactos del flujo inmediatamente anterior. Al validar con el usuario se identificó que, por ejemplo, Reporting necesitará `contract_data.json` (de un flujo más atrás) además de la salida de Simulation.
- **Decisión:** Los contratos de flujo permiten declarar dependencias (`requires`) de artefactos de más de un flujo atrás, no solo del inmediatamente anterior. El conjunto exacto de `requires` se declarará al construir cada flujo concreto.
- **Consecuencias:** Mayor flexibilidad y realismo en el modelo de dependencias entre flujos; se pospone la declaración exacta de `requires` por flujo hasta la etapa de construcción (T-009 en adelante), lo que exige revisarlo cuidadosamente al implementar cada flujo.

### D-015 — Renombrar `tdd_red`→`tdd_tester` y `tdd_green`→`tdd_coder`; tools mínimas para los 8 agentes de desarrollo
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** D-008 nombró los agentes del bucle TDD `tdd_red` y `tdd_green` (por el color/estado del ciclo red-green-refactor). Al construirlos en T-009 el usuario pidió nombres que describan el rol del agente en vez del estado del ciclo.
- **Decisión:** Los agentes se renombran a `tdd_tester` (antes `tdd_red`: escribe un test que falla, rojo limpio, no toca código de producción) y `tdd_coder` (antes `tdd_green`: escribe el código mínimo para pasar a verde, máx. 2 reintentos y escalamiento a humano si falla). Los otros 6 agentes conservan su nombre. Además, se fija la política de `tools` mínima común a los 8 agentes de desarrollo: `Read, Glob, Grep, Write, Edit, Bash` (sin `Agent` ni herramientas web), porque la orquestación entre agentes la realiza la sesión principal, no los agentes de desarrollo entre sí.
- **Consecuencias:** D-008 queda parcialmente desactualizado en los nombres (el resto de su contenido sigue vigente); `700_architecture/sdd_tdd_workflow.md` y los archivos de agente en `.claude/agents/` usan los nombres nuevos, que son los vigentes. La política de tools mínima reduce la superficie de cada agente y refuerza que la orquestación es responsabilidad exclusiva de la sesión principal.

### D-016 — Primera feature real = `client_scaffold`; orden de construcción abajo-hacia-arriba
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** Con el andamiaje SDD/TDD completo (T-009/T-010/T-011), había que elegir cuál sería la primera feature real a construir con la cadena de 8 agentes (T-013), que además valida A-005. Se evaluaron 3 candidatas: `client_context`, `client_scaffold` y `flow_base`. `client_context` (resolución de rutas de cliente) necesita que exista una estructura de carpetas de cliente que leer; `flow_base` (abstracción `Flow`) necesita `client_context` para ubicar sus inputs/outputs. `client_scaffold` no depende de ninguna de las otras dos.
- **Decisión:** La primera feature real es `client_scaffold`, que implementa `foda client new <NAME>`: crea el árbol de carpetas de un cliente nuevo bajo `clients/<NAME>/` (`client.yaml`, `010_inputs/`, `020_outputs/`, `data/{bronze,silver,gold}/`, `models/`), genera `client.yaml` con identidad mínima (nombre, fecha de creación), valida el nombre del cliente exigiendo un patrón seguro (alfanumérico + `_`/`-`, sin normalización automática, para que el nombre de carpeta sea predecible) y falla con error claro si el cliente ya existe (sin sobrescribir; un flag `--force` queda como trabajo futuro fuera de alcance). Se entrega primero una función de core reutilizable `create_client(...)`, con una capa CLI fina encima; los tests atacan el core. Fuera de alcance de esta feature: la lógica de `ClientContext` (será T-014), cualquier flujo (Ingestion, etc.) y su versionado de modelos (será T-015 en adelante), y las sub-carpetas por flujo dentro de `010_inputs/`/`020_outputs/` (las crea cada flujo al correr). El orden de construcción queda establecido como abajo-hacia-arriba: `client_scaffold` → `client_context` → `flow_base` → flujos concretos.
- **Consecuencias:** T-013 queda con alcance concreto y acotado, listo para invocar `feature_definer`. Se registran T-014 (`client_context`) y T-015 (`flow_base`) en el backlog como continuación natural. No se escribió código ni artefactos de feature en esta sesión; solo se acordó el plan.
