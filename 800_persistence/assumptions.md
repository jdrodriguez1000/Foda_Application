# Assumptions — Supuestos del Proyecto

> Este archivo registra los **supuestos** del proyecto e indica si están **validados o no**.

---

## Índice
1. [Cómo Registrar un Supuesto](#1-cómo-registrar-un-supuesto)
2. [Supuestos Validados](#2-supuestos-validados)
3. [Supuestos Pendientes de Validar](#3-supuestos-pendientes-de-validar)
4. [Supuestos Invalidados](#4-supuestos-invalidados)

---

## 1. Cómo Registrar un Supuesto
Cada supuesto incluye: **ID**, **descripción**, **estado** (✅ Validado · ⏳ Pendiente · ❌ Invalidado), **impacto si es falso** y **evidencia/validación**.

## 2. Supuestos Validados
| ID | Supuesto | Impacto si es falso | Evidencia |
|---|---|---|---|
| A-002 | Hay acceso/credenciales para hacer push al remoto en GitHub | Falla el cierre de sesión (push) | Push exitoso en commit 2dd82ac y en sesiones posteriores. |
| A-003 | La rama principal del proyecto es `main` | Push a rama incorrecta | Confirmado: push exitoso a `origin/main` en múltiples sesiones. |
| A-001 | El alcance del proyecto será definido por el usuario a continuación | Retraso en el arranque | El usuario definió el alcance en la sesión 2026-07-01 a partir de `990_documents/expected_workflow.md` y `current_state.md`, y de las restricciones de diseño que estableció. |
| A-004 | El documento `700_architecture/system_design.md` refleja correctamente la intención del usuario | Rediseño o retrabajo en la fase de construcción | Confirmado: el usuario revisó y validó las 16 secciones sección por sección (5 bloques temáticos) en la sesión 2026-07-01, con 5 ajustes puntuales (ver D-010 a D-014). Documento actualizado a v0.2. |

## 3. Supuestos Pendientes de Validar
| ID | Supuesto | Impacto si es falso | Cómo validar |
|---|---|---|---|
| A-005 | El diseño de la cadena SDD/TDD de 8 agentes de desarrollo (D-008, D-015) es viable con las capacidades de subagentes de Claude Code | Habría que rediseñar la orquestación, el checkpointing o la cadena de agentes | Se validará al construir e invocar la cadena completa sobre una feature real (T-013). |
| A-006 | El import `@980_guideline/principles.md` añadido en `CLAUDE.md` §0 efectivamente carga el archivo en el contexto de la sesión principal al reiniciar Claude Code | Los P1-P8/E1-E12/NC-1...NC-6 no llegarían a la sesión principal de forma automática; habría que depender solo de que el usuario o el agente lean el archivo manualmente | Validar empíricamente en una sesión nueva (tras reiniciar) comprobando si el contenido de `principles.md` aparece disponible sin pedirlo explícitamente. |
| A-007 | En la banda `tracer_bullet` de `client_scaffold` no se filtran diferencias de nombre de cliente en filesystems case-insensitive (p. ej. en Windows, `ABC` y `abc` se tratan como el mismo directorio aunque el patrón DS-1/D-023 sea case-sensitive) | Un usuario podría intentar crear `abc` tras ya existir `ABC` y obtener un comportamiento de filesystem no controlado por la validación de duplicado, en vez de un error claro de `client_scaffold` | Limitación conocida aceptada explícitamente por el humano en el GATE de `spec.md`; se endurecerá en una banda posterior si se decide soportarlo. |
| A-008 | En la banda `tracer_bullet` de `client_scaffold` no se filtran nombres reservados de Windows (CON, NUL, PRN, AUX, COM1...9, LPT1...9, etc.) como nombre de cliente inválido | Un usuario en Windows podría pasar un nombre reservado del SO y obtener un error de filesystem críptico en vez de un `ValueError` claro de validación de nombre (DS-1/D-023) | Limitación conocida aceptada explícitamente por el humano en el GATE de `spec.md`; se endurecerá en una banda posterior si se decide soportarlo. |
| A-009 | El retro-ajuste de trazabilidad (D-031) sobre `plan.md` de `client_scaffold` (nueva sección de tareas TSK-01…TSK-13, mapa caso→TSK, renumeración de secciones) no alteró el contenido sustantivo de los 18 casos TDD ya aprobados, por lo que el GATE de plan sigue siendo válido en sustancia | Si el retro-ajuste introdujo un cambio de fondo no detectado, se podría arrancar el bucle TDD sobre un plan distinto al que el humano aprobó originalmente | Re-confirmar explícitamente con el humano el `plan.md` retro-ajustado (GATE) antes de invocar `tdd_tester` con el caso TDD #1. |

> **Nota (2026-07-01):** sesión de validación de `system_design.md` (T-008): A-004 pasa a Validado. A-005 sigue pendiente, se validará al construir T-009/T-010.
> **Nota (2026-07-02):** T-009/T-010/T-011 completadas (andamiaje: 8 agentes + `sdd_tdd_workflow.md` + plantilla `600_features/`). A-005 sigue Pendiente; ahora está más cerca de validarse porque solo falta ejecutar la cadena sobre la primera feature real (T-013).
> **Nota (2026-07-02):** se acordó el alcance de la primera feature real, `client_scaffold` (ver D-016), pero aún no se invocó la cadena de agentes. A-005 sigue Pendiente hasta ejecutarla de punta a punta.
> **Nota (2026-07-02):** sesión de gobernanza/reconciliación de `980_guideline/` (T-016): se añadió A-006 (pendiente) sobre la carga efectiva del import de `principles.md` en `CLAUDE.md`. A-005 sigue Pendiente sin cambios; no se trabajó en T-013 esta sesión.
> **Nota (2026-07-02):** sesión de reversión del runtime agéntico (T-019, D-020/021/022): sin cambios en A-005 ni A-006 (siguen Pendientes); no se trabajó en T-013. La sesión fue de gobernanza/documentación (recorte de `methodology.md`), sin código de aplicación.
> **Nota (2026-07-02):** sesión de construcción de `client_scaffold` (T-013, etapas 1-3 de la cadena SDD/TDD): feature_definer, spec_writer y plan_builder completados; GATE humano aprobado tras spec y tras plan. Se añaden A-007 y A-008 (limitaciones conocidas de la banda `tracer_bullet`, aceptadas explícitamente por el humano). A-005 sigue Pendiente: aún falta ejecutar el bucle TDD (tdd_tester/tdd_coder/tdd_refactor), integration_tester y spec_verifier para validarla de punta a punta. A-006 sigue Pendiente sin cambios.
> **Nota (2026-07-02):** T-021 completada (D-029/D-030 aplicadas a la documentación y a `client_scaffold`) y T-022 completada (trazabilidad codificada HU→CA→TSK, D-031), incluyendo el retro-ajuste de `plan.md` de `client_scaffold`. Se añade A-009 (pendiente): el GATE de plan debe re-confirmarse formalmente con el humano antes de reanudar el bucle TDD, aunque el contenido de los 18 casos no cambió. A-005 y A-006 siguen Pendientes sin cambios.

## 4. Supuestos Invalidados
| ID | Supuesto | Motivo | Fecha |
|---|---|---|---|
| — | _Sin registros aún._ | — | — |
