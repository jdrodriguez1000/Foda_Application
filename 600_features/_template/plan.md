# Plan — <feature>

> Artefacto de la etapa 3 (`plan_builder`). Define el **cómo** de la implementación y **enumera los casos de test** que guiarán el bucle TDD. **Requiere aprobación humana** (gate) antes de arrancar el bucle.

## Enfoque Técnico
<Módulos, clases, funciones; cómo respeta la abstracción `Flow`/`ClientContext` cuando aplica.>

## Archivos Afectados
- `src/foda/<...>` — <a crear/modificar>
- `tests/<...>` — <a crear/modificar>

## Orden de Trabajo
1. <Secuencia de pasos de implementación, del más básico al más completo.>

## Dependencias y Contratos
- <Artefactos / features consumidos o producidos.>

## Estrategia de Test
- **Unit:** <qué se cubre con unit tests.>
- **Integración:** <qué se deja para `integration_tester`.>
- **Fixtures / datos de prueba:** <necesarios.>

## Casos de Test (bucle TDD)
Ordenados de simple a complejo. Deben coincidir con `stages.tdd.cases[]` de `state.json`.

| id | Descripción (verificable) |
|---|---|
| 1 | <...> |
| 2 | <...> |
