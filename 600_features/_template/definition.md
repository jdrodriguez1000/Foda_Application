# Definition — <feature>

> Artefacto de la etapa 1 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `<feature>` (snake_case)
- **Componente / flujo:** <a qué parte de `system_design.md` pertenece>

## Problema / Necesidad
<Qué carencia resuelve esta feature.>

## Alcance
**In scope:**
- <...>

**Out of scope:**
- <...>

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`. | <qué debe ser cierto al terminar> |
| HU-02 | Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`. | <...> |

## Dependencias
- <Otras features / artefactos / flujos requeridos.>

## Riesgos y Supuestos
- <Conocidos al momento de definir.>
