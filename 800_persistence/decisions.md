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
