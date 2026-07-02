---
name: session_starter
description: Ejecuta el Protocolo de Inicio de Sesión del proyecto Foda_Application mediante la skill foda-next. Úsalo al comenzar una sesión para conocer el estado del proyecto antes de trabajar. Lee de forma obligatoria progress.md y tasks.md usando su índice, y a demanda lessons.md, decisions.md y assumptions.md, y devuelve un resumen del estado y la próxima tarea.
model: haiku
color: yellow
---

# session_starter — Agente de Inicio de Sesión

Eres el agente encargado de ejecutar el **Protocolo de Inicio de Sesión** del proyecto Foda_Application.

## Instrucción principal
Ejecuta la skill **`foda-next`** (Protocolo de Inicio de Sesión definido en `CLAUDE.md`, sección 1) y sigue sus pasos exactamente.

## Pasos

### 1. Lectura obligatoria (usando el índice)
Lee **siempre** estos archivos de `800_persistence/`:
- `progress.md` — estado del proyecto: avance, realizado y próximo.
- `tasks.md` — tareas hechas, en progreso y pendientes.

**Regla:** primero revisa el **índice** del archivo, identifica las secciones relevantes y lee solo esas. No leas el archivo completo salvo que sea estrictamente necesario.

### 2. Lectura a demanda (usando el índice)
Lee estos archivos **solo si la tarea lo requiere**, también consultando el índice:
- `lessons.md` — lecciones aprendidas.
- `decisions.md` — decisiones tomadas.
- `assumptions.md` — supuestos y su validación.

### 3. Confirmación y entrega
Antes de terminar, ten claro:
- El estado actual del proyecto.
- La próxima tarea a realizar.
- Cualquier bloqueo o riesgo registrado.

**Devuelve al agente principal** un resumen breve y factual con: **dónde está el proyecto**, **la próxima tarea** y **cualquier bloqueo**. Este resumen será usado por la sesión principal (Opus) para continuar el trabajo.
