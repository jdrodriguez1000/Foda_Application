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

## 3. Supuestos Pendientes de Validar
| ID | Supuesto | Impacto si es falso | Cómo validar |
|---|---|---|---|
| A-001 | El alcance del proyecto será definido por el usuario a continuación | Retraso en el arranque | Esperar explicación del usuario. |

## 4. Supuestos Invalidados
| ID | Supuesto | Motivo | Fecha |
|---|---|---|---|
| — | _Sin registros aún._ | — | — |
