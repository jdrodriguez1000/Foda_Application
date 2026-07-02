# Spec — <feature>

> Artefacto de la etapa 2 (`spec_writer`). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables. Cada criterio se **enlaza a una historia de usuario** (`HU-xx`) de `definition.md`. **Requiere aprobación humana** (gate) antes de planear.

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
> Cada criterio lleva un **código `CA-xx`** (único en la feature) y se **enlaza a la(s) `HU-xx`** que satisface. El plan trazará cada `TSK-xx` a un `CA-xx`.

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | <...> | HU-01 |
| CA-02 | <...> | HU-01, HU-02 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` debe estar cubierta por **≥ 1** `CA-xx`. Si una HU no tiene criterio, la spec está incompleta.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02 |
| HU-02 | CA-02 |

## No-Objetivos
- <Qué queda explícitamente fuera.>
