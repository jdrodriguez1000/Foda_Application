# Verification — <feature>

> Artefacto de la etapa 8 (`spec_verifier`). Verifica que lo construido **cumple la spec aprobada**. Cierra la feature o la marca como no conforme.

## Veredicto
**<CONFORME | NO CONFORME>**

## Matriz de Trazabilidad
| Criterio de aceptación (spec) | Evidencia (test / comportamiento) | Estado |
|---|---|---|
| <criterio 1> | <test_x / comportamiento> | cubierto / parcial / no cubierto |

## Resultado de la Suite
- <Conteo de tests, verde/rojo.>

## Cumplimiento de Alcance y Restricciones
- **Alcance (`definition.md`):** <in scope hecho, out of scope respetado.>
- **Restricciones (R1–R9):** <Python 3.13+, YAML in / JSON out, LLM aislado, etc.>

## Hallazgos / Huecos
- <Si NO CONFORME: qué falta y **etapa de retorno recomendada** (`spec_writer`, `plan_builder`, bucle TDD o `integration_tester`).>
