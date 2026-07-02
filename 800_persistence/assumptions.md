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

## 3. Supuestos Pendientes de Validar
| ID | Supuesto | Impacto si es falso | Cómo validar |
|---|---|---|---|
| A-004 | El documento `700_architecture/system_design.md` refleja correctamente la intención del usuario | Rediseño o retrabajo en la fase de construcción | Revisar el documento sección por sección con el usuario en la próxima sesión. |

## 4. Supuestos Invalidados
| ID | Supuesto | Motivo | Fecha |
|---|---|---|---|
| — | _Sin registros aún._ | — | — |
