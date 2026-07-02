# Spec — <feature>

> Artefacto de la etapa 2 (`spec_writer`). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables. **Requiere aprobación humana** (gate) antes de planear.

## Resumen
<Una frase: qué debe hacer la feature.>

## Contratos de Datos / Artefactos
| Dirección | Artefacto | Formato | Esquema / campos |
|---|---|---|---|
| requiere | <archivo> | YAML/JSON | <campos y tipos> |
| produce | <archivo> | YAML/JSON | <campos y tipos> |

## Comportamiento Esperado
1. <Reglas paso a paso, incluyendo validaciones.>
2. <Qué ocurre si un contrato requerido falta o no valida.>

## Casos Límite y Errores
- <Entradas vacías / faltantes / inconsistentes / duplicadas → estado/error resultante.>

## Interfaces / Firmas Públicas
- <Firmas a nivel de contrato, no de implementación (p. ej. `run(ctx) -> FlowResult`).>

## Criterios de Aceptación (verificables)
1. <Redactado como algo que un test puede comprobar.>

## No-Objetivos
- <Qué queda explícitamente fuera.>
