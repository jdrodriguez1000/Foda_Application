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
| A-005 | El diseño de la cadena SDD/TDD de 8 agentes de desarrollo (D-008) es viable con las capacidades de subagentes de Claude Code | Habría que rediseñar la orquestación, el checkpointing o la cadena de agentes | Se validará al construir e invocar la cadena completa (T-009, T-010, T-011). |

> **Nota (2026-07-01):** sesión de validación de `system_design.md` (T-008): A-004 pasa a Validado. A-005 sigue pendiente, se validará al construir T-009/T-010.

## 4. Supuestos Invalidados
| ID | Supuesto | Motivo | Fecha |
|---|---|---|---|
| — | _Sin registros aún._ | — | — |
