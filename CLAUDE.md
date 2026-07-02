# CLAUDE.md — Instrucciones del Proyecto Foda_Application

Este archivo define los protocolos obligatorios que todo agente debe seguir al trabajar en este proyecto.

---

## Índice
1. [Protocolo de Inicio de Sesión](#1-protocolo-de-inicio-de-sesión)
2. [Protocolo de Cierre de Sesión](#2-protocolo-de-cierre-de-sesión)

---

## 1. Protocolo de Inicio de Sesión

Al comenzar **cada** sesión, el agente debe ejecutar estos pasos **en orden**:

### 1.1 Lectura obligatoria
Leer **siempre** los siguientes archivos de `800_persistence/`:
- `progress.md` — para saber cómo va el proyecto (avance, realizado y próximo).
- `tasks.md` — para saber las tareas hechas y pendientes.

> **Regla de lectura:** estos archivos se leen **usando el índice**. Primero se revisa el índice del archivo, se identifican las secciones relevantes y se leen solo esas secciones. No leer el archivo completo salvo que sea estrictamente necesario.

### 1.2 Lectura a demanda
Los otros tres archivos se leen **solo cuando la tarea lo requiera**:
- `lessons.md` — cuando se necesite consultar lecciones aprendidas.
- `decisions.md` — cuando se necesite conocer o revisar decisiones tomadas.
- `assumptions.md` — cuando se necesite validar o consultar supuestos.

> **Regla de lectura:** al igual que en la lectura obligatoria, estos archivos también se consultan **usando el índice** para ir directo a la sección necesaria, sin leer todo el contenido.

### 1.3 Confirmación
Tras la lectura, el agente debe tener claro: el estado actual del proyecto, la próxima tarea a realizar y cualquier bloqueo registrado, antes de proponer o ejecutar acciones.

---

## 2. Protocolo de Cierre de Sesión

Al finalizar **cada** sesión, el agente debe **actualizar los 5 archivos** de `800_persistence/` con lo realizado y trabajado durante la sesión:

1. **`progress.md`** — actualizar el estado general, métricas de avance, lo realizado, lo en progreso y lo próximo; añadir entrada al historial de actualizaciones con la fecha.
2. **`tasks.md`** — mover a completadas las tareas terminadas, actualizar las en progreso y registrar nuevas tareas pendientes.
3. **`lessons.md`** — registrar cualquier lección aprendida durante la sesión.
4. **`decisions.md`** — registrar las decisiones tomadas durante la sesión (formato ADR) y actualizar el índice de decisiones.
5. **`assumptions.md`** — registrar nuevos supuestos y actualizar el estado (validado / pendiente / invalidado) de los existentes.

> **Reglas de actualización:**
> - Mantener el **índice** de cada archivo coherente con el contenido nuevo.
> - Usar fechas absolutas (formato `AAAA-MM-DD`).
> - Ser conciso y factual: registrar lo efectivamente realizado, lo omitido y lo pendiente.

### 2.1 Commit y push a Git
Tras actualizar los 5 archivos, el protocolo de cierre **finaliza** publicando los cambios en el repositorio remoto:

1. Agregar los cambios: `git add -A`
2. Crear el commit con un mensaje descriptivo de lo trabajado en la sesión: `git commit -m "<resumen de la sesión>"`
3. Hacer push al repositorio remoto:
   - **Repositorio:** `https://github.com/jdrodriguez1000/Foda_Application.git`
   - Comando: `git push origin <rama>` (por defecto `main`).

> **Notas:**
> - Si el repositorio aún no está inicializado, inicializarlo y configurar el remoto:
>   `git init` → `git remote add origin https://github.com/jdrodriguez1000/Foda_Application.git`
> - El commit y push son el **último paso** del cierre de sesión: solo se ejecutan después de haber actualizado los 5 archivos de persistencia.
