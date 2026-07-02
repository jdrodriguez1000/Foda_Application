# Plan — <feature>

> Artefacto de la etapa 3 (`plan_builder`). Define el **cómo** de la implementación, descompone el trabajo en **tareas atómicas codificadas y trazables** (`TSK-xx → CA-xx`) y **enumera los casos de test** que guiarán el bucle TDD. **Requiere aprobación humana** (gate) antes de arrancar el bucle.

## Enfoque Técnico
<Módulos, clases, funciones; cómo respeta la abstracción `Flow`/`ClientContext` cuando aplica.>

## Archivos Afectados
- `src/foda/<...>` — <a crear/modificar>
- `tests/<...>` — <a crear/modificar>

## Tareas
> Cada tarea lleva un **código `TSK-xx`** y es **atómica**. Reglas de partición (obligatorias):
> 1. **Un solo responsable** por tarea — si intervienen dos, se parte en dos tareas (uno por responsable).
> 2. **Un solo entregable** por tarea — si produce dos entregables, se parte en dos tareas.
> 3. **Codificar ≠ testear** — una tarea no mezcla código de producción y test; van en tareas separadas.
>
> **Responsable** ∈ `{tdd_tester, tdd_coder, tdd_refactor, integration_tester, humano}` (exactamente uno).
> **Estado** ∈ `no_implementada` | `implementada` | `cancelada_suspendida`. El **responsable es el único que actualiza el estado** de su tarea (Single Writer, `D-021`).
> **Trazabilidad:** cada tarea apunta al `CA-xx` de la spec que ayuda a cumplir (o a un entregable de andamiaje justificado).

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | <acción única y concreta> | <un entregable> | tdd_tester | no_implementada | CA-01 |
| TSK-02 | <acción única y concreta> | <un entregable> | tdd_coder | no_implementada | CA-01 |

## Dependencias y Contratos
- <Artefactos / features consumidos o producidos.>

## Estrategia de Test
- **Unit:** <qué se cubre con unit tests.>
- **Integración:** <qué se deja para `integration_tester`.>
- **Fixtures / datos de prueba:** <necesarios.>

## Casos de Test (bucle TDD)
Ordenados de simple a complejo. Deben coincidir con `stages.tdd.cases[]` de `state.json`. Cada caso agrupa sus tareas de test y código (por eso enlaza a `TSK-xx`).

| id | Descripción (verificable) | Tareas (`TSK-xx`) | Trazabilidad → CA |
|---|---|---|---|
| 1 | <...> | TSK-01, TSK-02 | CA-01 |
| 2 | <...> | TSK-03, TSK-04 | CA-02 |
