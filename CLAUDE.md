# CLAUDE.md — Instrucciones del Proyecto Foda_Application

Este archivo define los protocolos obligatorios que todo agente debe seguir al trabajar en este proyecto.

---

## Índice
1. [Protocolo de Inicio de Sesión](#1-protocolo-de-inicio-de-sesión)
2. [Protocolo de Cierre de Sesión](#2-protocolo-de-cierre-de-sesión)

---

## 1. Protocolo de Inicio de Sesión

Al comenzar **cada** sesión —y en particular cuando el usuario diga **"iniciemos la sesión"** (o equivalente)— la sesión principal **debe invocar el subagente `session_starter`** (Task tool). No leas los archivos de persistencia directamente: delega en el subagente.

- El subagente `session_starter` ejecuta el Protocolo de Inicio y devuelve un resumen con el **estado del proyecto**, la **próxima tarea** y los **bloqueos**.
- El detalle paso a paso del protocolo (qué archivos leer y cómo) vive en `.claude/agents/session_starter.md`, que es la **única fuente de verdad**.
- Tras recibir el resumen, la sesión principal confirma el estado antes de proponer o ejecutar acciones.

---

## 2. Protocolo de Cierre de Sesión

Al finalizar **cada** sesión —y en particular cuando el usuario diga **"cerremos la sesión"** (o equivalente)— la sesión principal **debe invocar el subagente `session_closer`** (Task tool), entregándole en el prompt un **resumen detallado de lo trabajado** en la sesión.

- El subagente `session_closer` arranca en frío (sin el historial de la conversación), por lo que **depende del resumen** que le entregue la sesión principal: lo realizado, tareas completadas/pendientes, lecciones, decisiones (ADR) y supuestos.
- El subagente actualiza los **5 archivos** de `800_persistence/` y ejecuta el **commit y push** a Git como último paso.
- El detalle paso a paso del protocolo vive en `.claude/agents/session_closer.md`, que es la **única fuente de verdad**.
- **Repositorio remoto:** `https://github.com/jdrodriguez1000/Foda_Application.git` (rama por defecto `main`).
