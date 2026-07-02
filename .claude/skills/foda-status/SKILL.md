---
name: foda-status
description: Ejecuta el Protocolo de Cierre de Sesión del proyecto Foda_Application. Úsalo al finalizar una sesión para actualizar los 5 archivos de persistencia con lo trabajado y, finalmente, hacer commit y push al repositorio remoto.
model: inherit
---

# foda-status — Protocolo de Cierre de Sesión

Ejecuta el **Protocolo de Cierre de Sesión** definido en `CLAUDE.md` (sección 2).

## Pasos

### 1. Actualizar los 5 archivos de `800_persistence/`
Con lo realizado y trabajado durante la sesión:

1. **`progress.md`** — actualizar estado general, métricas de avance, lo realizado, lo en progreso y lo próximo; añadir entrada al historial con la fecha.
2. **`tasks.md`** — mover a completadas las tareas terminadas, actualizar las en progreso y registrar nuevas pendientes.
3. **`lessons.md`** — registrar lecciones aprendidas durante la sesión.
4. **`decisions.md`** — registrar decisiones tomadas (formato ADR) y actualizar el índice de decisiones.
5. **`assumptions.md`** — registrar nuevos supuestos y actualizar el estado de los existentes.

**Reglas de actualización:**
- Mantener el **índice** de cada archivo coherente con el contenido nuevo.
- Usar fechas absolutas (formato `AAAA-MM-DD`).
- Ser conciso y factual: registrar lo realizado, lo omitido y lo pendiente.

### 2. Commit y push a Git (último paso)
Solo después de actualizar los 5 archivos:

1. `git add -A`
2. `git commit -m "<resumen de la sesión>"`
3. `git push origin main`

**Repositorio remoto:** `https://github.com/jdrodriguez1000/Foda_Application.git`

**Nota:** si el repositorio no está inicializado, ejecutar primero:
```
git init
git remote add origin https://github.com/jdrodriguez1000/Foda_Application.git
```
