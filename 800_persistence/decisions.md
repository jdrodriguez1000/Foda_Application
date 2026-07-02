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
| D-004 | Skills de proyecto para inicio y cierre de sesión | Aceptada | 2026-07-01 |

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
- **Estado:** Aceptada
- **Fecha:** 2026-07-01
- **Contexto:** Facilitar la ejecución de los protocolos con comandos.
- **Decisión:** Crear las skills de proyecto `foda-next` (inicio) y `foda-status` (cierre) en `.claude/skills/`.
- **Consecuencias:** Los protocolos se invocan con `/foda-next` y `/foda-status`.
