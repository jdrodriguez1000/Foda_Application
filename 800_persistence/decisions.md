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
| D-017 | Protocolo de construcción por celda dimensionado por banda (formaliza la cita fantasma "D-021") | Aceptada | 2026-07-02 |
| D-018 | Invariante de independencia (tres contextos frescos) y orden test-first del ciclo unitario (formaliza la cita fantasma "D-029") | Aceptada | 2026-07-02 |
| D-019 | Reconciliación de carpetería de construcción: `600_features` feature/celda-céntrica con banda como subcarpeta | Aceptada | 2026-07-02 |
| D-020 | Runtime NO agéntico: se descarta A/B/C-runtime y MOTOR/INSTANCIA de la metodología; `methodology.md` recortado a metodología de desarrollo | Aceptada | 2026-07-02 |
| D-021 | Single Writer Rule como norma de persistencia; no se adoptan los 3 archivos `fda-*` de la metodología | Aceptada | 2026-07-02 |
| D-022 | Rúbrica de evaluación calibrada solo para salidas NO deterministas (LLM/ML); el código determinista sigue con tests + veredicto binario | Aceptada | 2026-07-02 |
| D-023 | `client_scaffold` — patrón de validación de nombre de cliente (DS-1) | Aceptada | 2026-07-02 |
| D-024 | `client_scaffold` — estrategia de atomicidad: validación-primero + limpieza best-effort (DS-2) | Aceptada | 2026-07-02 |
| D-025 | `client_scaffold` — ubicación y firma del core, capa CLI fina, tipos de error (DS-3) | Aceptada | 2026-07-02 |
| D-026 | Adoptar PyYAML como dependencia del proyecto | Aceptada | 2026-07-02 |
| D-027 | Bootstrap del paquete `foda` (`pyproject.toml`, layout `src/`) dentro de la feature `client_scaffold` | Aceptada | 2026-07-02 |
| D-028 | Caso TDD #18 (rollback de filesystem) implementado sin test en la banda `tracer_bullet` | Aceptada | 2026-07-02 |
| D-029 | Taxonomía de bandas y ejes de crecimiento del producto (vertical feature vs. horizontal producto) | Aceptada | 2026-07-02 |
| D-030 | Contratos en dos niveles: `feature_contract` (adoptado) + `slice_contract` (diferido) | Aceptada | 2026-07-02 |
| D-031 | Cadena de trazabilidad codificada HU→CA→TSK y tareas atómicas del plan | Aceptada | 2026-07-02 |
| D-032 | GATE PA-3 (opción c): posponer el rollback best-effort DS-2.2 (caso TDD 18) a banda `stab_n`; refina D-028 | Aceptada | 2026-07-02 |
| D-033 | Cierre CONFORME de `client_scaffold` (banda `tracer_bullet`) con 3 hallazgos no bloqueantes (F-1, F-2, F-3) | Aceptada | 2026-07-02 |
| D-034 | `client_new_cli` entra por la cadena SDD/TDD completa, no por cableado directo | Aceptada | 2026-07-02 |
| D-035 | `client_new_cli` sí lleva tests propios de la capa CLI (NC-5 prevalece sobre el No-Objetivo previo de `client_scaffold`) | Aceptada | 2026-07-02 |
| D-036 | `client_new_cli` — resolución de `clients_root` buscando `pyproject.toml` hacia arriba desde el cwd | Aceptada | 2026-07-02 |
| D-037 | Patrón "verde directo, sin rojo artificial" consolidado como práctica estándar del bucle TDD del harness | Aceptada | 2026-07-02 |
| D-038 | `client_new_cli` — ramas `except ValueError`/`except FileExistsError` en `cli.py` se mantienen separadas | Aceptada | 2026-07-02 |
| D-039 | `clients/` y `.venv/` no se versionan en Git; se añaden a `.gitignore` | Aceptada | 2026-07-03 |
| D-040 | `client_context` — modo nuevo/recurrente inferido del disco vía `models/latest`, sin flag editable en `client.yaml` | Aceptada | 2026-07-03 |
| D-041 | `client_context` — `clients_root` como parámetro del constructor, el core no resuelve `pyproject.toml` desde el cwd | Aceptada | 2026-07-03 |
| D-042 | `client_context` — introspección de artefactos existentes diferida a `flow_base` (T-015) | Aceptada | 2026-07-03 |
| D-043 | `client_context` — `FileNotFoundError` como validación de existencia vía `client.yaml` (DS-CTX-1) | Aceptada | 2026-07-03 |
| D-044 | `client_context` — `is_recurring` como propiedad booleana `== (models/latest).exists()` (DS-CTX-2) | Aceptada | 2026-07-03 |
| D-045 | `client_context` — constructor directo con validación en `__init__` y rutas como propiedades de solo lectura (DS-CTX-3) | Aceptada | 2026-07-03 |
| D-046 | Cierre CONFORME de `client_context` (banda `tracer_bullet`) con 2 hallazgos no bloqueantes (F-1, F-2) | Aceptada | 2026-07-03 |
| D-047 | `flow_base` — `FlowContractError(Exception)` propia en `flow.py` (DS-FLOW-1) | Aceptada | 2026-07-03 |
| D-048 | `flow_base` — `Artifact(name, base, relative)` declarativo con clave `base` mapeada (DS-FLOW-2) | Aceptada | 2026-07-03 |
| D-049 | `flow_base` — `FlowResult(success, outputs)` mínimo (DS-FLOW-3) | Aceptada | 2026-07-03 |
| D-050 | `flow_base` — hooks base + `run` como template method no sobreescribible (DS-FLOW-4) | Aceptada | 2026-07-03 |
| D-051 | `flow_base` — GATE#5: `execute()` construye y devuelve el `FlowResult` | Aceptada | 2026-07-03 |
| D-052 | `flow_base` — GATE#6: orden `load_inputs → validate` en el template method | Aceptada | 2026-07-03 |
| D-053 | Cierre CONFORME de `flow_base` (banda `tracer_bullet`), sin hallazgos bloqueantes | Aceptada | 2026-07-03 |
| D-054 | Próxima feature a construir (T-026): `onboarding` (flujo 020), descartando por ahora discovery, `stab_1` de `flow_base` y el orquestador `foda run` | Aceptada | 2026-07-03 |
| D-055 | `onboarding` arranca simulando la salida de Discovery: `contract_data.json` fabricado como fixture/maniquí realista | Aceptada | 2026-07-03 |
| D-056 | Se confirma la estrategia `tracer_bullet` (slice vertical mínimo) también para `onboarding` y features siguientes | Aceptada | 2026-07-03 |
| D-057 | Se confirma la estrategia de escalabilidad progresiva: el tracer_bullet de `onboarding` arranca con el caso más simple (pocos productos, geografía sencilla); la jerarquía real se soporta endureciendo en bandas posteriores, no rediseñando | Aceptada | 2026-07-03 |
| D-058 | `onboarding` — contrato `contract_data.json`: jerarquías dinámicas, datasets con esquema propio y Modelo B de mapeo columna→nivel vía `maps_to` | Aceptada | 2026-07-03 |
| D-059 | `onboarding` — ubicación de artefactos (`020_outputs/010_discovery/` y `020_outputs/020_onboarding/`) y separación de responsabilidades con Ingestion (no toca bronze) | Aceptada | 2026-07-03 |
| D-060 | `onboarding` — pre-autorización del humano para el cierre automático de casos "verde directo" sin GATE individual | Aceptada | 2026-07-06 |

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

### D-017 — Protocolo de construcción por celda dimensionado por banda
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** Al reconciliar `980_guideline/methodology.md`, su §7 referenciaba una decisión "D-021 §6" que nunca se registró (`decisions.md` llegaba solo a D-016). La cita apuntaba a la idea de dimensionar el ciclo SDD+TDD según la "banda" de trabajo (p. ej. *Tracer Bullet*). Se formaliza como ADR real. Nota de numeración: se usa el ID secuencial siguiente (D-017) en lugar del número citado "D-021" para no dejar huecos en la serie; las referencias en `methodology.md` se actualizan a D-017.
- **Decisión:** El ciclo SDD+TDD (Definir → Diseñar → Planear → Ejecutar → Probar → Verificar) es la **ambición**; su realización concreta por **celda** (flujo × banda) se **dimensiona a la banda** vía Escalamiento Proporcional (P6) y Mínima Complejidad (E4). La proporcionalidad se expresa como **PESO del artefacto, no como fusión de pasos**: los 6 pasos conservan siempre su carril propio. En la banda **Tracer Bullet**, Diseñar y Planear son ligeros (≤1 pág / checklist) y el peso vive en el `slice_contract` (nivel banda) y en la verificación; en bandas superiores esos artefactos suben de peso sin cambiar el invariante ni el mapa de instancias. Artefactos por paso bajo `703_definition/ 705_design/ 710_plan/ 720_build/<banda>/`.
- **Consecuencias:** Se elimina una cita fantasma y queda un protocolo de construcción escalable por banda. Complementa a D-008 (cadena de 8 agentes) describiendo cómo se dimensiona su esfuerzo. Introduce el concepto de "banda" y la carpetería `703/705/710/720`, que aún debe reconciliarse con la actual `600_features/` (trabajo futuro). Se apoya en D-018 para el orden y la independencia del ciclo.

### D-018 — Invariante de independencia (tres contextos frescos) y orden test-first del ciclo unitario
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** El §7 de `methodology.md` citaba una decisión "D-029" inexistente y presentaba una **tensión no resuelta**: el "Ciclo de Vida del Componente" describía RED→GREEN (test **primero**), mientras la tabla de bandas describía Ejecutar→Probar (test **después**, por un evaluador independiente). Había que decidir explícitamente el orden. Nota de numeración: se usa el ID secuencial siguiente (D-018) en lugar del número citado "D-029".
- **Decisión:** (a) **Invariante de independencia (toda banda):** quien ejecuta ≠ quien prueba ≠ quien verifica; **Ejecutar, Probar y Verificar corren en tres contextos frescos distintos** (P1, P3), con gate humano al cierre de celda (P5). (b) **Orden test-first:** *dentro* del paso **Ejecutar**, el ciclo unitario es **RED → GREEN → REFACTOR**: el test unitario que falla se escribe **antes** del código de producción, tal como lo implementan `tdd_tester` → `tdd_coder` → `tdd_refactor`. (c) **"Probar" no reemplaza al test unitario:** el paso Probar (Instancia C-test, contexto fresco) es una capa de **aceptación/integración posterior e independiente** que corre la celda contra el *golden client* (E9) y **complementa** —no sustituye— a los tests unitarios test-first. "Verificar" (C-verify + humano) audita contra el `slice_contract`.
- **Consecuencias:** Se elimina la cita fantasma y la ambigüedad TDD. `methodology.md` queda alineado con la cadena de 8 agentes ya construida (D-008, D-015): `tdd_tester`=RED, `tdd_coder`=GREEN, `tdd_refactor`=REFACTOR (todos dentro de "Ejecutar"), `integration_tester`="Probar" (contexto fresco), `spec_verifier`="Verificar". Refuerza que la independencia crece hacia el final del ciclo.

### D-019 — Reconciliación de carpetería de construcción: `600_features` feature/celda-céntrica con banda como subcarpeta
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** D-017 introdujo una carpetería **step-céntrica** (`703_definition/705_design/710_plan/720_build/<banda>/<flujo>/`) para el protocolo de construcción por celda, que **chocaba** con la carpetería **feature-céntrica** `600_features/<feature>/` ya construida y en uso por la cadena de 8 agentes (D-008/D-015). Ambas organizan los mismos artefactos de construcción con ejes distintos: una por paso, otra por unidad. Mantener las dos violaría E4/NC-2 (mínima complejidad).
- **Decisión:** Se adopta la **Opción A (feature/celda-céntrica)**. (1) `600_features/` sigue siendo la **taxonomía única** de construcción. (2) Se introduce la **banda como subcarpeta**: la unidad de trabajo es la **celda = feature × banda**, con home físico `600_features/<feature>/<banda>/{definition.md, spec.md, plan.md, verification.md, state.json}`. La banda por defecto de la primera pasada es `tracer_bullet`. (3) `state.json` pasa a ser **por celda** (dentro de la carpeta de banda) e incluye un campo `"band"`. (4) Los números `703/705/710/720` de D-017 quedan como **etiquetas conceptuales de fase** (Definir/Diseñar/Planear/Ejecutar/Probar/Verificar), **no como carpetas**. (5) Código y tests siguen en `src/foda/…` y `tests/…` (fuera de `600_features/`). (6) Cada agente recibe en el prompt `<feature>` y `<banda>` y opera sobre `600_features/<feature>/<banda>/`. Correspondencia de fase: `definition`↔703, `spec`↔705, `plan`↔710, build (`src`/`tests`)↔720, integración↔Probar, `verification`↔Verificar.
- **Consecuencias:** Una sola taxonomía de construcción (E4/NC-2); se preserva la cadena de 8 agentes (NC-3) añadiendo solo el nivel `<banda>`; la banda queda de primera clase para slices verticales (NC-4). Se actualizaron `methodology.md §4.3`, `sdd_tdd_workflow.md` (§6/§7/§8), `600_features/README.md`, `600_features/_template/state.json` y las rutas de artefacto de los 8 agentes. Refina el aspecto de carpetería de D-017 (que se mantiene por lo demás). Pendiente futuro: si un flujo necesita una segunda banda, se crea otra subcarpeta hermana sin tocar la primera.

### D-020 — Runtime NO agéntico: se descarta A/B/C-runtime y MOTOR/INSTANCIA; `methodology.md` recortado a metodología de desarrollo
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** La metodología importada en `980_guideline/methodology.md` introdujo un **runtime agéntico** (patrón A/B/C: `foda-governor` / `foda-<flujo>-planner` / `foda-<flujo>-evaluator` + workers, uno por cada uno de los 14 flujos) y dos **planos MOTOR/INSTANCIA** externos (`foda-*`/`fda-*`) con `install.sh` y archivos `fda-harness-state.json`/`fda-execution-state.json`. Esto **contradice** el diseño ya acordado en `system_design.md` (D-006): runtime **determinista**, multi-tenant `clients/<NAME>/`, orquestador = **CLI (código)**, LLM aislado en Discovery/Exploration. Agregaba complejidad contra E4/NC-2. Además, la metodología citaba `D-005`/`D-009`/`D-010` con significados que no coinciden con el `decisions.md` real (evidencia de que se importó de otro harness).
- **Decisión:** El **runtime lo define exclusivamente `system_design.md`** (determinista, multi-tenant, orquestado por código; LLM aislado en 2 flujos). Se **descarta del harness**: el patrón A/B/C como runtime, los agentes `foda-governor`/`planner`/`evaluator`, los planos MOTOR/INSTANCIA externos, `install.sh` y los archivos `fda-*-state.json`. Los **únicos agentes de IA** son los **8 de desarrollo** (D-008) que construyen el código determinista. `methodology.md` se **recorta** a "Metodología de Desarrollo del Motor" (ciclo SDD+TDD, gates, persistencia de desarrollo, evaluación, evolución/mínima complejidad). De la metodología se **rescatan dos piezas**, formalizadas en D-021 (Single Writer Rule) y D-022 (rúbrica de evaluación para salidas no deterministas).
- **Consecuencias:** Se elimina complejidad no justificada y se preserva el modelo original coherente. Se **cancelan/revisan** T-017 (crear agentes runtime) y T-018 (reconciliar plano runtime), que dejan de aplicar. `principles.md`, la cláusula vinculante en los 10 agentes, el import en `CLAUDE.md` y la carpetería por banda (D-017/D-018/D-019) **se conservan** (son de desarrollo). Las citas fantasma desaparecen al recortar.

### D-021 — Single Writer Rule como norma de persistencia; no se adoptan los 3 archivos `fda-*`
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** La metodología proponía 3 archivos de estado de runtime (`fda-harness-state.json` estratégico, `fda-execution-state.json` táctico, `project-progress.txt` narrativo). Bajo el runtime determinista (D-020) son en su mayoría **redundantes**: el estado de runtime **son los propios artefactos** bajo `clients/<NAME>/` (el `ClientContext` sabe qué existe; `foda status ABC`), y la idempotencia/reanudación sale de la existencia de artefactos (Principio 5 de `system_design`).
- **Decisión:** **No se adoptan** los 3 archivos. Se conserva la persistencia existente: `800_persistence/` (5 archivos, nivel proyecto/desarrollo) + `600_features/<feature>/<banda>/state.json` (por celda). Se adopta como **norma explícita** la **Single Writer Rule**: cada archivo de estado tiene un único responsable de escritura, para evitar condiciones de carrera. (Opción futura, si se necesita: un manifiesto de corrida ligero por cliente para alimentar `foda status`.)
- **Consecuencias:** Persistencia simple y sin duplicación; se rescata el único principio valioso del modelo de la metodología.

### D-022 — Rúbrica de evaluación calibrada solo para salidas NO deterministas
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** Hoy `spec_verifier` evalúa de forma **binaria** (CONFORME/NO CONFORME) con matriz de trazabilidad + suite `pytest`, y `integration_tester` valida integración: adecuado y suficiente para **código determinista** (los tests son objetivos). Pero Discovery y Exploration producen **salidas de LLM** (documentos, propuesta de features) **sin ningún control de calidad**, y ahí es donde se juega la **reducción de varianza** (objetivo de negocio del proyecto).
- **Decisión:** (a) El **código determinista** sigue evaluándose con **tests + veredicto binario** de `spec_verifier` (evaluación independiente, P3); **no** se le añade rúbrica (sería overkill). (b) Para las **salidas NO deterministas** (documentos de Discovery, propuesta de features de Exploration) y como **evaluación temprana** de la calidad ML se adopta una **rúbrica calibrada 0.0–1.0** con dimensiones+pesos, **few-shot** (≥2 ejemplos, uno ≥0.7 y uno <0.5) y **anclas** (1.0/0.5/0.0), más **evaluación temprana** con ~20 casos representativos (E9). Es el espejo del Principio 1: *"evaluación con rúbrica solo donde el LLM aporta"*. La ubicación y el contenido concretos de cada rúbrica se definen al construir Discovery/Exploration.
- **Consecuencias:** Control de calidad donde de verdad se necesita (lo no determinista), sin sobre-ingeniería en el código. Queda como trabajo futuro diseñar las rúbricas concretas al construir esos flujos.

### D-023 — `client_scaffold`: patrón de validación de nombre de cliente (DS-1)
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** `spec_writer` necesitaba resolver, para `create_client(name, ...)`, qué nombres de cliente son válidos como nombre de carpeta en disco, dejado abierto por D-016 ("patrón seguro, sin normalización").
- **Decisión:** El nombre de cliente debe cumplir `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`: solo ASCII, el primer carácter debe ser alfanumérico, longitud 1–64, case-sensitive y sin normalización automática (no se recorta espacios ni se cambia mayúsculas/minúsculas).
- **Consecuencias:** Nombre de carpeta predecible y determinista a partir del nombre lógico del cliente. Deja fuera de alcance del tracer_bullet el manejo de filesystems case-insensitive y nombres reservados de Windows (ver A-007, A-008).

### D-024 — `client_scaffold`: atomicidad por validación-primero + limpieza best-effort (DS-2)
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** Había que decidir cómo evitar dejar un árbol de carpetas a medio crear si el filesystem falla a mitad de `create_client(...)`. Se evaluó también un patrón temp-dir + rename atómico.
- **Decisión:** Se valida todo lo posible antes de tocar el filesystem (nombre válido, cliente no existe ya); si de todos modos ocurre un fallo de filesystem a mitad de la creación del árbol, se hace una limpieza best-effort del árbol parcial creado hasta ese punto. Se descarta el patrón temp+rename por ser sobre-complejidad para el tracer_bullet (NC-2).
- **Consecuencias:** Comportamiento simple y suficiente para la banda tracer_bullet; no hay garantía de atomicidad estricta ante fallos de filesystem a mitad de escritura (aceptado como límite conocido de esta banda).

### D-025 — `client_scaffold`: ubicación/firma del core, capa CLI fina, tipos de error (DS-3)
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** D-016 ya pedía "core reutilizable + capa CLI fina encima"; faltaba fijar la ubicación exacta del módulo, la firma de la función y los tipos de excepción a usar.
- **Decisión:** El core vive en `src/foda/core/scaffold.py` con firma `create_client(name: str, clients_root: Path) -> Path`. Errores: `ValueError` para nombre inválido (no cumple DS-1), `FileExistsError` para cliente duplicado. La CLI fina vive en `src/foda/cli.py` y expone `foda client new <NAME>`.
- **Consecuencias:** Core testeable de forma aislada con `tmp_path` (sin acoplar a rutas reales); la CLI solo traduce argumentos/errores a códigos de salida y mensajes, sin lógica propia.

### D-026 — Adoptar PyYAML como dependencia del proyecto (PA-1)
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** `client_scaffold` necesita generar `client.yaml` con identidad mínima del cliente. `system_design.md` (R3) ya establecía YAML como formato de entrada/configuración, pero el proyecto no tenía aún una dependencia YAML concreta.
- **Decisión:** Se adopta PyYAML como dependencia del proyecto para leer/escribir YAML, coherente con R3.
- **Consecuencias:** Primera dependencia externa declarada del proyecto; debe listarse en `pyproject.toml` (ver D-027).

### D-027 — Bootstrap del paquete `foda` dentro de la feature `client_scaffold` (PA-2)
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** El proyecto aún no tenía `pyproject.toml` ni estructura de paquete Python instalable. Se evaluó crear una tarea de bootstrap separada antes de `client_scaffold` versus hacerlo dentro de la propia feature.
- **Decisión:** El bootstrap mínimo del paquete (`pyproject.toml`: paquete `foda`, layout `src/`, pytest, `python >= 3.13` conforme a D-010, dependencia PyYAML de D-026) se hace **dentro** de `plan.md` de `client_scaffold`, como parte de sus pasos de implementación, en vez de como tarea separada previa.
- **Consecuencias:** `client_scaffold` es el primer slice vertical legítimo (NC-4) que deja el proyecto con un paquete Python funcional de punta a punta (bootstrap + primera feature), evitando una tarea de "andamiaje" sin valor de negocio propio.

### D-028 — Caso TDD #18 (rollback de filesystem) sin test en `tracer_bullet` (PA-3)
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** El plan de `client_scaffold` incluye 18 casos TDD; el caso 18 cubre la limpieza best-effort de DS-2 (D-024) ante fallo de filesystem a mitad de creación, un escenario difícil de testear de forma simple (requiere simular fallos de I/O).
- **Decisión:** El caso 18 se **implementa sin test** en la banda `tracer_bullet`, respetando NC-2 (simplicidad primero); se endurecerá con test en una banda posterior.
- **Consecuencias:** Excepción explícita y documentada a NC-5 ("toda tarea tiene un test que la respalda") para este caso puntual, aprobada por el humano en el GATE del plan. Queda como trabajo pendiente de banda futura escribir el test de este caso.

### D-029 — Taxonomía de bandas y ejes de crecimiento del producto
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** El concepto de "banda" (D-017/D-019) estaba definido solo para la primera pasada (`tracer_bullet`), sin nombres para bandas posteriores ni relación con hitos de producto. El usuario aportó su forma de trabajo habitual (bandas tracer_bullet / estabilización / MVP / evolución / final) y se detectó que la palabra "banda" mezclaba dos ejes ortogonales: profundizar UNA feature (vertical) vs. hacer crecer el PRODUCTO agregando features (horizontal).
- **Decisión:** (1) **Eje vertical (madurez de UNA feature):** las bandas por feature son `tracer_bullet → stab_1 → stab_2 → …` (bandas de estabilización que endurecen la MISMA feature de forma controlada). Cada banda es una subcarpeta hermana bajo la feature: `600_features/<feature>/<banda>/` (refina, no cambia, D-017/D-019). Una feature crea solo las bandas que necesita. (2) **MVP y Final = hitos de PRODUCTO emergentes (Opción A elegida por el usuario), NO son bandas.** No son carpetas de ninguna feature; son etiquetas del roadmap del producto que emergen cuando el conjunto de features necesarias alcanza madurez suficiente. (3) **Evolución = agregar features NUEVAS**, no es una banda: cada feature nueva de la fase de evolución arranca en su propio `tracer_bullet` y recorre la cadena SDD/TDD estándar como cualquier otra; por tanto NO existen bandas `evol_n`. (4) **Alcance de adopción (E4/NC-2):** se adopta AHORA solo el VOCABULARIO de bandas del eje vertical (`tracer_bullet`, `stab_n`); la maquinaria de hitos MVP/Final y de la fase de evolución se documenta como convención futura, NO se construye todavía.
- **Consecuencias:** Se separan limpiamente los dos ejes; se preserva la carpetería existente (`600_features/<feature>/<banda>/`); "feature terminada" pasa a ser un hito superior (la feature alcanza su banda madura), mientras `spec_verifier` sigue cerrando por CELDA (feature × banda). Pendiente de aplicar en docs (ver tarea nueva de aplicación en `tasks.md`). No se editó ningún documento en esta sesión; queda para la próxima.

### D-030 — Contratos en dos niveles: `feature_contract` (adoptado) + `slice_contract` (diferido)
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** D-017 mencionaba un `slice_contract "nivel banda"` que nunca se definió ni creó. Al formalizar el modelo de bandas (D-029) se vio la necesidad de un contrato explícito por feature (materializa P5 — contratos explícitos antes de ejecutar). El usuario decidió DOS artefactos separados.
- **Decisión:** (1) **`feature_contract` (por feature):** es la "estrella polar" / definición de "terminado" total de la feature. Es OBLIGATORIO y debe existir ANTES de iniciar la primera banda. Vive a NIVEL FEATURE, por encima de las bandas: `600_features/<feature>/feature_contract.md`. Lo crea el agente `feature_definer` (decisión del usuario). Materializa P5. (2) **`slice_contract` (por celda/banda):** define qué entrega cada banda como slice hacia el `feature_contract`. Su ADOPCIÓN queda DIFERIDA (no se construye ni se exige todavía; E4/NC-2). (3) **Nota abierta:** cuando se adopte el `slice_contract`, podría FUSIONARSE con `spec.md` (que ya captura comportamiento + criterios de aceptación por celda) para evitar duplicación (E4); queda como decisión futura, sin resolver ahora. (4) **Retro-ajuste pendiente:** `client_scaffold` ejecutó su `tracer_bullet` SIN `feature_contract`, por lo que queda temporalmente no-conforme; debe retro-escribirse su `feature_contract` como parte de la tarea nueva.
- **Consecuencias:** Contratos explícitos alineados con P5; el `feature_definer` gana la responsabilidad de crear el `feature_contract`. Pendiente de aplicar en docs, plantilla y agente (ver tarea nueva en `tasks.md`). No se editó ningún documento en esta sesión; queda para la próxima.

### D-032 — GATE PA-3 (opción c): posponer el rollback best-effort DS-2.2 (caso 18) a banda `stab_n`
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** El plan de `client_scaffold` reservaba el caso TDD #18 (rollback best-effort ante fallo de filesystem a mitad de creación, DS-2.2) como GATE humano opcional (D-028 preveía "implementar sin test"). Al llegar al caso 18 tras cerrar en verde los casos 1-17 (26 tests), se presentaron al humano 3 opciones: (a) implementar sin test como preveía D-028, (b) implementar con un test que simule el fallo de I/O, (c) posponer el rollback por completo a una banda de estabilización posterior.
- **Decisión:** El humano eligió la opción **(c) POSPONER**. No se implementa ni testea DS-2.2 en la banda `tracer_bullet`. `client_scaffold` cierra su tracer_bullet solo con la estrategia validación-primero (DS-2.1, D-024), que ya cubre los escenarios realistas (nombre inválido, cliente duplicado) sin llegar a mutar disco antes de fallar. El error raro de filesystem a mitad de creación del árbol se acepta como limitación conocida y documentada de esta banda. Esta decisión **refina D-028**: en vez de "implementar sin test", el caso 18 queda `deferred` en `state.json` con el campo `gate_decision` registrando la justificación, para una banda `stab_n` futura.
- **Consecuencias:** El core `create_client(...)` no implementa rollback/limpieza best-effort; un fallo de I/O a mitad de creación puede dejar un árbol parcial en disco (límite conocido, análogo a A-007/A-008). El bucle TDD de `client_scaffold` (casos 1-17) queda cerrado con 26 tests en verde sin este caso. Trabajo pendiente explícito para una banda `stab_n` de `client_scaffold`: escribir el test que simule el fallo de I/O e implementar DS-2.2.

### D-033 — Cierre CONFORME de `client_scaffold` (banda `tracer_bullet`) con 3 hallazgos no bloqueantes
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** Tras cerrar el bucle TDD (casos 1-17, 26 tests) y correr `integration_tester` (6 tests de integración, 32 passed), `spec_verifier` recorrió los 11 CA de `spec.md` de `client_scaffold` buscando evidencia de test/comportamiento para cada uno.
- **Decisión:** Veredicto **CONFORME**: los 11 CA (CA-01…CA-11) tienen evidencia verificable en la suite, documentada en `600_features/client_scaffold/tracer_bullet/verification.md` con matriz de trazabilidad CA→test. Se registran 3 hallazgos NO bloqueantes, no requeridos para el veredicto: **F-1** desalineación de entorno (runtime local Python 3.12.10, pero R1/D-010 exige 3.13+; el `pyproject.toml` ya declara `requires-python = ">=3.13"` correctamente, el problema es del entorno local, no del entregable). **F-2** la capa CLI `foda client new` (TSK-07) no fue construida en esta banda: estaba in-scope de la definición de la feature pero fuera de los 11 CA verificables. **F-3** `created_at` en `client.yaml` usa `date.today()` (fecha local) en vez de UTC como sugiere el contrato de artefacto; CA-06 solo valida el patrón de fecha, no la zona horaria, así que no bloquea el veredicto.
- **Consecuencias:** `client_scaffold/tracer_bullet` queda cerrada. F-1 se resuelve alineando el entorno de desarrollo local a Python 3.13+ (fuera del alcance de esta feature). F-2 da origen a la nueva feature `client_new_cli` (T-023, ver D-034 a D-036). F-3 queda como tarea de backlog T-025 para una banda `stab_n` futura.

### D-034 — `client_new_cli` entra por la cadena SDD/TDD completa
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** El hallazgo F-2 de `spec_verifier` (D-033) dejó pendiente construir la capa CLI de `client_scaffold`. Existían dos caminos: cablear la CLI directamente sobre `create_client(...)` sin pasar por la cadena de agentes (más rápido, pero sin gates ni trazabilidad), o tratarla como una feature nueva con su propia cadena SDD/TDD completa.
- **Decisión:** Se consultó al humano y se decidió que la capa CLI se construye como una **feature nueva** (`client_new_cli`), recorriendo la cadena SDD/TDD completa de los 8 agentes (feature_definer → spec_writer → plan_builder → bucle TDD → integration_tester → spec_verifier), no como cableado directo.
- **Consecuencias:** Se preserva la disciplina P5 (contratos explícitos) y P3 (evaluador independiente) también para la capa CLI; a cambio, toma más pasos que un cableado directo. `client_new_cli` recorre su propia banda `tracer_bullet` bajo `600_features/client_new_cli/tracer_bullet/`.

### D-035 — `client_new_cli` sí lleva tests propios de la capa CLI
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** `client_scaffold` (D-025) había dejado la capa CLI explícitamente fuera de los tests de su banda ("capa CLI fina... sin lógica propia"). Al construir ahora la CLI como feature completa (D-034), esa decisión de alcance previa entraba en tensión con NC-5 ("toda tarea tiene un test que la respalda... sin excepción").
- **Decisión:** `client_new_cli` **sí lleva tests propios** de la capa CLI (12 casos TDD sobre `main(argv)`), aceptado explícitamente por el humano en el GATE de `plan.md`. NC-5 prevalece sobre el No-Objetivo que la definición de `client_scaffold` había fijado para la CLI.
- **Consecuencias:** Ver L-023. Los 12 casos TDD de `client_new_cli` cubren camino feliz, invocabilidad, resolución de raíz de proyecto, nombres inválidos, duplicados, argumentos ausentes/desconocidos y el contrato `[project.scripts]`.

### D-036 — `client_new_cli`: resolución de `clients_root` buscando `pyproject.toml` hacia arriba desde el cwd
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** `spec_writer` de `client_new_cli` necesitaba resolver cómo la CLI localiza la raíz del proyecto (y por tanto `clients/`) al ejecutarse desde cualquier subcarpeta (HU-02), sin asumir que el cwd es siempre la raíz.
- **Decisión:** La CLI busca `pyproject.toml` hacia arriba desde el cwd hasta encontrar la raíz del proyecto (marcador de raíz); si no lo encuentra en el cwd ni en ningún ancestro, falla con código de salida 1 y mensaje claro en stderr (DS-CLI-1). `clients_root` se resuelve como `<raíz>/clients/`, creado por la CLI con `mkdir` idempotente si no existe (DS-CLI-2), no por el core `create_client`.
- **Consecuencias:** La CLI es invocable desde cualquier subcarpeta del proyecto (HU-02), reflejado en los casos TDD 6 y 7. `create_client(...)` del core sigue sin conocer la noción de "raíz de proyecto"; esa responsabilidad queda enteramente en la capa CLI (`src/foda/cli.py`), preservando el aislamiento del core (D-025).

### D-037 — Patrón "verde directo, sin rojo artificial" consolidado como práctica estándar del bucle TDD
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** En `client_scaffold` (L-020), 5 de 18 casos TDD llegaron "verde directo" (comportamiento ya cubierto por un caso anterior) y se cerraron sin forzar un rojo artificial, documentando la razón. En `client_new_cli`, el mismo patrón se repitió en 7 de 12 casos (2, 3, 4, 5, 6, 10, 11), reforzado por el orquestador (sesión principal) como decisión explícita en vez de tratarse caso a caso.
- **Decisión:** Se formaliza como práctica estándar de la cadena SDD/TDD del harness (no exclusiva de una feature): cuando el test de un caso posterior del plan pasa en verde de inmediato porque el tracer bullet u otro comportamiento ya construido lo cubre, el caso se cierra como `done` conservando el test como cobertura de regresión, con una nota (`tdd_note`) que documenta explícitamente qué caso/comportamiento previo lo cubre (NC-6), sin invocar `tdd_coder` ni `tdd_refactor` para ese caso.
- **Consecuencias:** Evita forzar fallos artificiales que violarían NC-2 (simplicidad); reduce trabajo redundante en el bucle TDD sin perder cobertura de regresión ni trazabilidad de la decisión. Aplica a toda feature futura del harness, no solo a `client_scaffold`/`client_new_cli`. Ver L-020, L-024.

### D-038 — `client_new_cli`: ramas `except ValueError`/`except FileExistsError` en `cli.py` se mantienen separadas
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** En el refactor del caso 9 (duplicado), se evaluó consolidar las ramas `except ValueError` (nombre inválido, caso 8) y `except FileExistsError` (cliente duplicado, caso 9) de `main()` en `src/foda/cli.py`, ya que ambas envuelven la llamada a `create_client` y devuelven `return 1`.
- **Decisión:** NO se consolidan. La `spec.md` de `client_new_cli` exige mensajes de error distintos por historia de usuario (CA-07 para nombre inválido, CA-08 para duplicado); fusionar ambas ramas en un único `except (ValueError, FileExistsError)` con un `if/elif` interno para elegir el mensaje degradaría la claridad sin reducir duplicación real.
- **Consecuencias:** `cli.py` conserva dos bloques `except` explícitos y paralelos, cada uno con su propio mensaje a stderr, priorizando legibilidad y trazabilidad directa a su CA sobre la eliminación de una duplicación menor.

### D-039 — `clients/` y `.venv/` no se versionan en Git
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Al verificar el uso real de la CLI, el usuario creó `clients/DEMO_ABC/` con `foda client new DEMO_ABC` y recreó `.venv/` con Python 3.13, quedando ambos como untracked en `git status`. El usuario pidió explícitamente dejar `clients/DEMO_ABC/` en disco (no eliminarlo). `system_design.md`/D-006 ya establece el modelo multi-tenant como carpeta-por-cliente **en disco, sin base de datos**: los datos de cliente son datos de runtime generados por la aplicación, no código fuente ni artefactos de diseño.
- **Decisión:** Se añaden `clients/` y `.venv/` a `.gitignore`. `clients/` no se versiona porque es el directorio de datos de runtime multi-tenant (coherente con D-006, no requiere una decisión nueva de arquitectura, solo su reflejo en `.gitignore`); `.venv/` no se versiona porque es un entorno virtual local reproducible desde `pyproject.toml`. El cliente de prueba `clients/DEMO_ABC/` permanece en disco (a pedido del usuario) pero fuera del control de versiones.
- **Consecuencias:** El repositorio no arrastra datos de cliente ni el entorno virtual; cualquier colaborador nuevo reproduce `.venv/` siguiendo `README.md` y genera sus propios clientes de prueba sin ensuciar el historial de Git. Si en el futuro se necesita un cliente de ejemplo versionado (p. ej. para fixtures de test), deberá vivir fuera de `clients/` o excepcionarse explícitamente en `.gitignore`.

### D-040 — `client_context`: modo nuevo/recurrente inferido del disco vía `models/latest`
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Al definir el alcance de `client_context` (HU de "determinar modo nuevo vs. recurrente"), había que decidir cómo se determina ese modo: mediante un flag explícito en `client.yaml` (que alguien debería mantener sincronizado) o infiriéndolo de artefactos ya existentes en disco.
- **Decisión:** El modo se infiere exclusivamente del disco: RECURRENTE ⇔ existe `models/latest`; NUEVO ⇔ no existe. No se añade ningún flag editable de modo en `client.yaml`. Refleja R9 y `system_design.md` §12.
- **Consecuencias:** Se evita un estado duplicado que podría desincronizarse del contenido real de `models/`; el modo es siempre una consecuencia observable del filesystem, no una entrada humana que pueda mentir. Un `client.yaml` con un campo `mode` espurio se ignora (ver CA-11).

### D-041 — `client_context`: `clients_root` como parámetro del constructor
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Igual que en `client_new_cli` (D-036), había que decidir si `ClientContext` resuelve por sí mismo la raíz del proyecto (buscando `pyproject.toml` desde el cwd) o si la recibe ya resuelta.
- **Decisión:** `ClientContext(name, clients_root)` recibe `clients_root` como parámetro explícito, con el mismo patrón que `create_client(name, clients_root)`. El core no re-resuelve `pyproject.toml` desde el cwd; esa resolución vive únicamente en la capa CLI.
- **Consecuencias:** El core sigue siendo testeable de forma aislada con `tmp_path` (sin acoplar a rutas reales ni al cwd del proceso), preservando el aislamiento ya establecido en D-025/D-036.

### D-042 — `client_context`: introspección de artefactos existentes diferida a `flow_base`
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Durante la definición de alcance surgió la pregunta de si `client_context` también debía saber "qué pasos ya se hicieron" (reanudación/idempotencia por flujo), distinta de "si el cliente ya tiene modelo" (nuevo vs. recurrente). Ambas nociones son ortogonales: un cliente con limpieza hecha pero sin modelo sigue siendo NUEVO correctamente.
- **Decisión:** La introspección de "qué artefactos existen" (para soportar reanudación de un flujo donde se dejó) queda **fuera de alcance** de `client_context` y se difiere a cuando `flow_base` (T-015) la consuma (E4/NC-2, no construir antes de tener consumidor).
- **Consecuencias:** `client_context` se mantiene acotado a resolución de rutas + determinación de modo nuevo/recurrente; la lógica de idempotencia por artefacto (§2.5 de `system_design.md`) se diseñará junto con `Flow.run(ctx)` en T-015, con el contexto concreto de qué necesita saber cada flujo.

### D-043 — `client_context`: `FileNotFoundError` como validación de existencia vía `client.yaml` (DS-CTX-1)
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** `spec_writer` necesitaba fijar qué excepción lanza `ClientContext` si el cliente no existe, y qué archivo se usa como marcador de existencia.
- **Decisión:** El marcador de existencia de un cliente es su archivo `client.yaml` (no solo la existencia de la carpeta). Si no existe, el constructor lanza `FileNotFoundError` con mensaje claro que incluye el nombre del cliente y la ruta esperada.
- **Consecuencias:** Un cliente con carpeta pero sin `client.yaml` (estado inconsistente) se trata como inexistente, evitando construir un `ClientContext` sobre un árbol incompleto o corrupto.

### D-044 — `client_context`: `is_recurring` como propiedad booleana `== (models/latest).exists()` (DS-CTX-2)
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Formaliza a nivel de spec la decisión de alcance D-040: se necesitaba fijar la firma exacta de la propiedad que expone el modo nuevo/recurrente.
- **Decisión:** `ClientContext.is_recurring` es una propiedad booleana de solo lectura, calculada como `(models/latest).exists()`, evaluada en el momento de la consulta (no cacheada al construir el objeto).
- **Consecuencias:** El valor de `is_recurring` puede cambiar durante la vida de un mismo objeto `ClientContext` si el filesystem cambia (p. ej. tras entrenar un modelo), lo cual es el comportamiento deseado: siempre refleja el estado real del disco.

### D-045 — `client_context`: constructor directo con validación en `__init__` y rutas de solo lectura (DS-CTX-3)
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Había que fijar el patrón de construcción de `ClientContext`: constructor directo vs. método de fábrica (`ClientContext.for_client(...)`), y si las rutas se calculan una vez o en cada acceso.
- **Decisión:** Constructor directo `ClientContext(name, clients_root)` que valida la existencia del cliente en `__init__` (lanzando `FileNotFoundError` si falta, D-043). Las rutas (`inputs_dir`, `outputs_dir`, `bronze_dir`, `silver_dir`, `gold_dir`, `models_dir`) se exponen como propiedades de solo lectura, derivadas de `root`/`name`, sin setters.
- **Consecuencias:** Un `ClientContext` construido con éxito garantiza que el cliente existe (invariante de constructor); las propiedades son inmutables desde fuera, evitando que un consumidor corrompa las rutas de un contexto ya construido.

### D-046 — Cierre CONFORME de `client_context` (banda `tracer_bullet`) con 2 hallazgos no bloqueantes
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Tras cerrar el bucle TDD (12/12 casos) y correr `integration_tester` (5 tests de integración), `spec_verifier` recorrió los 12 CA de `spec.md` de `client_context` buscando evidencia de test/comportamiento para cada uno.
- **Decisión:** Veredicto **CONFORME**: los 12 CA tienen evidencia verificable en la suite, documentada en `600_features/client_context/tracer_bullet/verification.md` con matriz de trazabilidad CA→test completa. Se registran 2 hallazgos NO bloqueantes: **F-1** 6 de los 12 casos llegaron en "verde directo" (D-037) sin rojo genuino, documentado, sin afectar la cobertura. **F-2** limitaciones aceptadas para esta banda: un symlink `models/latest` roto se evalúa como inexistente (⇒ NUEVO); los filesystems case-insensitive heredan la semántica del FS sin normalización adicional. Ninguna tiene consumidor hoy que la requiera.
- **Consecuencias:** `client_context/tracer_bullet` queda cerrada. F-2 se registra como limitación conocida en `assumptions.md` (A-010, A-011), análogo a A-007/A-008 de `client_scaffold`; se endurecerá en una banda futura solo si un flujo consumidor lo exige.

### D-047 — `flow_base`: `FlowContractError(Exception)` propia (DS-FLOW-1)
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** `spec_writer` necesitaba fijar qué excepción lanza `Flow.validate()` cuando faltan artefactos requeridos (`requires`). `client_context` (D-043) había usado `FileNotFoundError`, una excepción estándar de Python, para su propio caso de "no existe".
- **Decisión:** `flow_base` define una excepción de dominio propia, `FlowContractError(Exception)`, en `src/foda/core/flow.py`, en vez de reutilizar `FileNotFoundError` u otra excepción estándar. `validate()` la lanza una sola vez, agregando en el mensaje TODOS los artefactos `requires` faltantes (no solo el primero).
- **Consecuencias:** A diferencia de `client_context`, aquí sí hay un consumidor previsible de la excepción (el futuro orquestador/`foda run`, §9 de `system_design.md`, que necesitará capturarla específicamente para informar al científico de datos qué falta), lo que justifica una excepción de dominio dedicada en vez de una genérica.

### D-048 — `flow_base`: `Artifact(name, base, relative)` declarativo con clave `base` mapeada (DS-FLOW-2)
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Había que decidir cómo un flujo concreto declara SUS artefactos (`requires`/`produces`) de forma que `Flow.validate()` pueda resolver su ruta real contra un `ClientContext` sin que cada flujo reimplemente la lógica de rutas. Se evaluó también un callable `path_fn(ctx) -> Path` opaco por artefacto.
- **Decisión:** Se adopta `Artifact(name, base, relative)`, un dataclass congelado (`frozen=True`) puramente declarativo: `base` es una clave lógica de texto (una de `inputs/outputs/bronze/silver/gold/models`) que `Artifact.path(ctx)` mapea a la propiedad correspondiente de `ClientContext` (p. ej. `base="bronze"` → `ctx.bronze_dir`), concatenada con `relative`. Si `base` no es una de las 6 claves conocidas, `path(ctx)` lanza `ValueError`. Se descarta el callable `path_fn` opaco por ser menos legible/declarativo y más difícil de auditar en `spec.md`/`plan.md`.
- **Consecuencias:** Los flujos concretos declaran sus artefactos como datos simples e inspeccionables (útil para futura introspección/documentación automática), sin poder inyectar lógica arbitraria de resolución de rutas. Reutiliza `ClientContext` (T-014) tal cual, sin tocarlo (NC-3).

### D-049 — `flow_base`: `FlowResult(success, outputs)` mínimo (DS-FLOW-3)
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Había que fijar qué devuelve `Flow.run(ctx)` al terminar. Se evaluó incluir desde ya un campo para mensajes/inconsistencias de ejecución (p. ej. avisos no bloqueantes de un flujo).
- **Decisión:** `FlowResult` es un dataclass congelado mínimo con solo dos campos: `success: bool` y `outputs: list[Path]`. Se difiere explícitamente un campo de "inconsistencias/mensajes" a una banda `stab_1` futura, cuando exista un consumidor real que lo necesite (E4/NC-2).
- **Consecuencias:** Contrato de retorno simple y suficiente para el tracer_bullet; un flujo concreto que necesite reportar avisos no bloqueantes deberá esperar a la ampliación de `FlowResult` en `stab_1`.

### D-050 — `flow_base`: hooks base + `run` como template method no sobreescribible (DS-FLOW-4)
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Había que fijar el mecanismo exacto por el que los flujos concretos heredan de `Flow`: si `run()` es libre de sobreescribirse o si está fijado, y qué hacen por defecto los 4 hooks (`load_inputs`, `validate`, `execute`, `write_outputs`) sin sobreescribir.
- **Decisión:** `run(ctx) -> FlowResult` es un template method NO sobreescribible (documentado como tal; el tracer_bullet no lo impone técnicamente con un guard runtime) que invoca siempre, en orden fijo, `load_inputs(ctx) → validate(ctx) → execute(ctx) → write_outputs(ctx)`. Los flujos concretos heredan y sobreescriben SOLO los 4 hooks. Por defecto: `load_inputs`/`write_outputs` son no-op; `validate` tiene comportamiento real (agrega faltantes de `requires`, D-047); `execute` lanza `NotImplementedError` (obliga a todo flujo concreto a implementarlo).
- **Consecuencias:** Todo flujo futuro (010–140) queda forzado a seguir la misma secuencia de 4 pasos, garantizando comportamiento uniforme del pipeline (orquestador, logging, manejo de errores futuro) sin que cada flujo reimplemente el orden.

### D-051 — `flow_base`: GATE#5 — `execute()` construye y devuelve el `FlowResult`
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** En el GATE de spec se presentó al humano una ambigüedad de diseño (NC-1): ¿quién ensambla el `FlowResult` final — el hook `execute()` de cada flujo concreto, o el propio `run()` de la clase base a partir de lo que devuelven los hooks?
- **Decisión:** El humano eligió que `execute()` (implementado por el flujo concreto) construye y devuelve el `FlowResult` completo; `run()` simplemente lo retorna tal cual, sin reensamblarlo. Es la opción más fiel a la redacción de §9 de `system_design.md`, frente a la alternativa de que `run()` ensamblara el resultado a partir de piezas devueltas por los hooks.
- **Consecuencias:** Cada flujo concreto es responsable de reportar su propio éxito/outputs; `run()` queda como pura orquestación de la secuencia de 4 pasos, sin lógica de negocio.

### D-052 — `flow_base`: GATE#6 — orden `load_inputs → validate`
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** En el GATE de spec se resolvió explícitamente el orden entre `load_inputs` y `validate` (ninguno de los documentos previos lo fijaba de forma inequívoca), y qué implica ese orden si `validate` falla.
- **Decisión:** El orden es `load_inputs → validate` (no al revés). Ante un `requires` faltante, `load_inputs` ya se ejecutó (pero no escribe nada, es no-op por defecto en el tracer_bullet) mientras que `execute`/`write_outputs` NO llegan a correr.
- **Consecuencias:** Un flujo concreto que sobreescriba `load_inputs` con lógica real debe asumir que puede ejecutarse incluso si luego `validate` falla; el tracer_bullet no sufre este riesgo porque el hook base es no-op.

### D-053 — Cierre CONFORME de `flow_base` (banda `tracer_bullet`), sin hallazgos bloqueantes
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Tras cerrar el bucle TDD (14/14 casos) y correr `integration_tester` (4 tests de integración), `spec_verifier` recorrió los 13 CA de `spec.md` de `flow_base` buscando evidencia de test/comportamiento para cada uno.
- **Decisión:** Veredicto **CONFORME**: los 13 CA (CA-01…CA-13) tienen evidencia verificable en la suite, documentada en `600_features/flow_base/tracer_bullet/verification.md` con matriz de trazabilidad completa. A diferencia de `client_scaffold`/`client_context`, no se registraron hallazgos no bloqueantes nuevos en esta feature.
- **Consecuencias:** `flow_base/tracer_bullet` queda cerrada; es la cuarta feature en recorrer la cadena de 8 agentes de punta a punta CONFORME. Con esta feature construida, queda disponible el contrato base que consumirán el primer flujo concreto y/o el futuro orquestador.

### D-031 — Cadena de trazabilidad codificada HU→CA→TSK y tareas atómicas del plan
- **Estado:** Aceptada
- **Fecha:** 2026-07-02
- **Contexto:** El usuario exigió trazabilidad total entre `definition.md`, `spec.md` y `plan.md`: poder seguir el hilo de por qué existe cada pieza de trabajo desde la necesidad de negocio hasta la tarea concreta. Se resolvió con el usuario en tres preguntas: (1) el responsable de cada tarea puede ser un agente de desarrollo o el humano; (2) las tareas del plan son una capa de trazabilidad adicional, el bucle TDD sigue corriendo por "caso" de `state.json` sin cambios (cambio mínimo, NC-2/NC-3); (3) `client_scaffold` se retro-ajusta ahora, ya que su plan estaba aprobado pero sin esta capa.
- **Decisión:** (a) `definition.md` expresa el qué/por qué como **historias de usuario codificadas `HU-xx`** (formato Connextra: "Como... quiero... para..."). (b) `spec.md` codifica sus criterios de aceptación como `CA-xx`, cada uno enlazado a ≥1 `HU-xx`, con una **matriz de cobertura** HU→Spec explícita: si una HU queda sin ningún CA que la cubra, la spec está incompleta y `spec_writer` debe detenerse. (c) `plan.md` descompone el trabajo en **tareas atómicas `TSK-xx`** con columnas ID / Descripción / Entregable / Responsable / Estado / Trazabilidad→CA. Reglas de partición de una tarea: un solo responsable, un solo entregable, código y test siempre en tareas separadas. Responsable ∈ {`tdd_tester`, `tdd_coder`, `tdd_refactor`, `integration_tester`, humano} (exactamente uno por tarea). Estado ∈ {no_implementada, implementada, cancelada_suspendida}; el responsable de cada tarea es su único escritor del campo estado (alinea con la Single Writer Rule, D-021). (d) Reconciliación con el bucle TDD: las tareas TSK son una **capa de trazabilidad**, no reemplazan el mecanismo de ejecución; el bucle TDD (`tdd_tester`→`tdd_coder`→`tdd_refactor`) sigue corriendo por **caso** de `tdd.cases` en `state.json`, sin cambios al esquema ni al mecanismo; cada caso agrupa sus TSK de test y de código correspondientes.
- **Consecuencias:** Trazabilidad end-to-end HU→CA→TSK verificable en cualquier momento. Se actualizaron las 3 plantillas (`_template/definition.md`, `spec.md`, `plan.md`), los 3 agentes de la primera mitad de la cadena (`feature_definer`, `spec_writer`, `plan_builder`) y `700_architecture/sdd_tdd_workflow.md` (v0.2→v0.3, nueva regla transversal §8: cadena HU→CA→TSK). `600_features/client_scaffold/tracer_bullet/` fue retro-ajustada: `definition.md` (HU-01…HU-05), `spec.md` (CA-01…CA-11 + matriz de cobertura), `plan.md` (nueva sección de tareas TSK-01…TSK-13, los 18 casos TDD mapeados a CA y a TSK, secciones renumeradas). El contenido sustantivo de los 18 casos TDD no cambió, solo se le añadió trazabilidad; aun así, por higiene de proceso, el GATE de plan ya aprobado debe **re-confirmarse** con el humano antes de invocar `tdd_tester` con el caso #1 (ver nota en `assumptions.md`). La regla de partición (un responsable, un entregable) resuelve quién escribe el estado de cada tarea sin violar D-021.

### D-054 — Próxima feature a construir (T-026): `onboarding` (flujo 020)
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Con `flow_base` cerrado (T-015), quedaba pendiente T-026: decidir colaborativamente con el humano cuál es la siguiente feature a construir. Estaban sobre la mesa 3 opciones (D-016 agotado en su forma original, ver §5 de `progress.md`): (a) el primer flujo concreto del pipeline de 14; (b) la banda `stab_1` de `flow_base`; (c) el orquestador `foda run`. Se deliberó en términos de negocio (sin tecnicismos) con el usuario.
- **Decisión:** La próxima feature es `onboarding` (flujo 020), NO Discovery (flujo 010) pese a ser el primero del pipeline. Se descarta Discovery por ahora porque es uno de los dos únicos flujos con núcleo LLM (no determinista, D-006/D-013), difícil de probar con TDD, y tiene pendiente T-020 (diseño de rúbricas para salidas no deterministas, D-022) sin resolver. También se descartan la banda `stab_1` de `flow_base` y el orquestador `foda run`: el orden natural es construir primero un flujo concreto real que valide la abstracción `Flow` con un caso de punta a punta, antes de endurecer límites diferidos o de orquestar múltiples flujos que aún no existen.
- **Consecuencias:** T-026 queda resuelta. Se define una hoja de ruta de 14 features de producto (una por flujo), registrada en `progress.md` como brújula (no como contrato cerrado): onboarding es la primera, con el bloque determinista (ingestion, profiling, cleaning, derivation, featuring, inferences, simulation, reporting, monitoring, alerting) firme, y las de LLM (discovery, exploration) y ML (modelling, inferences) sujetas a decisiones futuras. Nueva tarea T-027: iniciar la cadena SDD/TDD de `onboarding` desde `feature_definer`.

### D-055 — `onboarding` arranca simulando la salida de Discovery (fixture de `contract_data.json`)
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** `onboarding` requiere como entrada `contract_data.json`, artefacto que en el pipeline real produce Discovery (flujo 010). Discovery aún no existe (D-054 lo descarta por ahora). Se necesitaba decidir cómo alimentar `onboarding` sin romper el orden del pipeline ni construir Discovery prematuramente.
- **Decisión:** `onboarding` arranca **simulando la salida de Discovery**: se fabrica un `contract_data.json` simulado y realista que sirve de entrada (test fixture/maniquí), propuesto originalmente por el usuario y aceptado por ser una técnica estándar que respeta el orden del pipeline y permite trabajar con un flujo determinista, fácil de probar con TDD.
- **Consecuencias:** La primera sub-tarea al definir la feature `onboarding` (con `feature_definer`) será acordar y documentar explícitamente la forma de ese `contract_data.json` simulado, sin decidirlo en silencio (NC-6). Ver A-012: ese fixture fija implícitamente el contrato que Discovery deberá cumplir en el futuro.

### D-056 — Confirmación: estrategia `tracer_bullet` se mantiene para `onboarding` y features siguientes
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Con la decisión de construir `onboarding` a continuación (D-054), había que confirmar si la forma de construcción cambia respecto a las 4 features anteriores.
- **Decisión:** `onboarding` (y las features siguientes) se construyen igual que `client_scaffold`, `client_new_cli`, `client_context` y `flow_base`: primero la banda `tracer_bullet` (slice vertical mínimo completo de entrada a salida, NC-4), difiriendo casos de borde y complejidad a bandas de endurecimiento posteriores (`stab_1`, `stab_n`).
- **Consecuencias:** No hay cambio de proceso; se reutiliza la cadena de 8 agentes y el vocabulario de bandas (D-029) sin modificaciones.

### D-057 — Confirmación: estrategia de escalabilidad progresiva para `onboarding`
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** `onboarding` mapea la estructura de datos del cliente (jerarquía de productos familia→categoría→subcategoría→clase, y geografía región→país→ciudad→sede, `system_design.md` §15). Había que decidir si el tracer_bullet debe cubrir esa variedad completa desde el inicio o no.
- **Decisión:** El tracer_bullet de `onboarding` arranca con el caso más simple (pocos productos, geografía única/sencilla). La variedad real (jerarquías completas) se soporta escalando/endureciendo en bandas posteriores, NO rediseñando, apoyándose en el principio de diseño de escalabilidad estructural de `system_design.md` §2.6.
- **Consecuencias:** El tracer_bullet de `onboarding` queda acotado y simple (NC-2/NC-4); queda como trabajo esperado de bandas `stab_n` futuras soportar jerarquías completas de productos y geografía, sin que eso implique retrabajo estructural del diseño del flujo.

### D-058 — `onboarding`: contrato `contract_data.json` (jerarquías dinámicas, datasets con esquema propio, Modelo B de mapeo)
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Había que fijar, punto por punto con el humano (NC-6, sin decisiones silenciosas), la forma exacta del fixture `contract_data.json` que simula la salida de Discovery (D-055). Surgieron varias preguntas de diseño: ¿la jerarquía tiene siempre 4 niveles?, ¿cómo se listan los miembros?, ¿un archivo de datos puede cubrir varios años?, ¿las columnas de un archivo se llaman igual que los niveles de la jerarquía?
- **Decisión:** (1) **Jerarquías dinámicas**: el array `levels` (de `product_hierarchy`/`geography_hierarchy`) es la fuente de verdad de cuántos y cuáles niveles hay; la profundidad es VARIABLE, no fija en 4. (2) **Miembros**: lista plana de dicts cuyas claves deben coincidir EXACTAMENTE con los `levels` declarados. (3) **`historical_data.datasets`**: lista de datasets, cada uno con `kind`, `source_medium`, `periodicity`, `fields` (esquema propio del dataset, no del archivo) y `files`; se separan 3 conceptos ortogonales — tipo de dataset (`kind`), cobertura temporal del archivo (`period_start`/`period_end`) y periodicidad de los registros (`periodicity`) — permitiendo que un solo archivo cubra varios años (p. ej. ventas 2023→2025). (4) **Esquema por campo** (`fields`): `name` (único dentro del dataset), `type`, `required` (bool), `maps_to`. (5) **Modelo B — mapeo columna→nivel declarado en el contrato**: cada campo declara `maps_to` ∈ {`"product.<level>"`, `"geography.<level>"`, `"time"`, `"measure"`, `null`}; `onboarding` CONSUME ese mapeo, nunca lo adivina por coincidencia de nombres (resuelve la duda de que las columnas de un archivo real pueden llamarse distinto a los niveles de la jerarquía, ver L-034). (6) **Vocabularios controlados (enums cerrados)**: `field.type` ∈ {string, integer, number, date, boolean}; `kind` ∈ {ventas, inventario, ordenes_compra, devoluciones, promociones, precios}; `source_medium` ∈ {csv, xlsx, database, api}; `periodicity` ∈ {diaria, semanal, quincenal, mensual, trimestral, semestral, anual}. El fixture solo usa ventas+inventario, pero el contrato admite los demás sin rediseño futuro, porque se predice demanda (no ventas) y hacen falta más datasets (inventario para quiebres de stock, órdenes de compra, etc.) para reconstruirla. (7) **Fechas** en formato `YYYY-MM-DD`, con validación `period_start ≤ period_end`.
- **Consecuencias:** El contrato queda expresivo y extensible sin comprometer la simplicidad del tracer_bullet (el fixture concreto solo instancia 2 datasets y 4+4 niveles, D-057). Formaliza DS-ONB-1 a DS-ONB-5 de `spec.md`. El caso límite de profundidad dinámica se prueba en ambas direcciones (CA-05 reducción, CA-05b incremento a 5 niveles) a pedido del humano en el GATE (ver L-035). Ver L-034, A-013 (el fixture sigue siendo un contrato provisional con Discovery).

### D-059 — `onboarding`: ubicación de artefactos y separación de responsabilidades con Ingestion
- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Contexto:** Había que aclarar dos dudas de arquitectura antes de que `plan_builder` planificara la implementación: (a) ¿dónde viven `contract_data.json` y `map_client_data.json` en el árbol de carpetas del cliente?, ¿requiere esto ampliar `ClientContext`?; (b) ¿`onboarding` debe validar los datos reales (bronze) contra el mapa que construye, o eso es de otro flujo?
- **Decisión:** (a) `contract_data.json` (fixture de Discovery) vive en `020_outputs/010_discovery/`, y `map_client_data.json` (salida de `onboarding`) en `020_outputs/020_onboarding/` — ambos son salidas de máquina, NO `010_inputs` (confirmado contra `system_design.md` §7). La resolución de rutas `020_outputs/<flujo>/<archivo>` YA está soportada por `Artifact(name, base, relative)` con `base="outputs"` + `relative="<flujo>/<archivo>"` (D-048), verificado leyendo `src/foda/core/context.py` y `src/foda/core/flow.py`: NO requiere ampliar `ClientContext`. (b) `onboarding` (020) construye el mapa a partir de METADATOS del contrato y NO toca datos reales/bronze (que aún no existe cuando corre Onboarding, según el orden del pipeline); la validación de los datos reales contra el mapa es responsabilidad de Ingestion (030).
- **Consecuencias:** `plan_builder` planifica sin necesidad de tocar `ClientContext` (NC-3, cambio mínimo); el alcance de `onboarding` queda acotado a metadatos, dejando la validación de datos reales claramente fuera (evita solapamiento de responsabilidades con la futura feature `ingestion`).

### D-060 — `onboarding`: pre-autorización del humano para el cierre automático de casos "verde directo" sin GATE individual
- **Estado:** Aceptada
- **Fecha:** 2026-07-06
- **Contexto:** El patrón "verde directo" (D-037) venía cerrándose caso por caso con aprobación explícita del humano en cada uno (visible en los casos 2, 9, 11, 12, 13, 14 de `onboarding`). Con el bucle TDD avanzando rápido y una alta proporción de casos verde-directo (L-037), pedir aprobación individual por cada uno añadía fricción sin aportar valor adicional, dado que el patrón ya está consolidado como práctica estándar del harness (D-037).
- **Decisión:** A partir del caso 14 de `onboarding`, el humano PRE-AUTORIZÓ al harness a cerrar automáticamente los casos que resulten "verde directo" (test permanente promovido + docstring/evidencia + commit) SIN pedir aprobación individual previa, simplemente reportándolos al humano después de cerrados. Los casos con rojo genuino siguen su ciclo normal completo red→green→refactor sin ningún cambio. El primer caso cerrado bajo esta pre-autorización fue el caso 15 (CA-20, `contract_data.json` ausente → `FlowContractError`).
- **Consecuencias:** Reduce fricción de proceso en el bucle TDD sin relajar la exigencia de documentar la razón del verde directo (NC-6) ni la de conservar el test como cobertura de regresión (D-037 sigue vigente sin cambios). Esta pre-autorización aplica hacia adelante en `onboarding` (casos 19-22 restantes) y queda registrada para que futuras sesiones/features la respeten sin tener que volver a consultarla, salvo que el humano decida revocarla explícitamente.
