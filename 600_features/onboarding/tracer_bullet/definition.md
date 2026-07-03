# Definition — onboarding

> Artefacto de la etapa 1 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `onboarding` (snake_case)
- **Banda:** `tracer_bullet` (D-019; celda = feature × banda)
- **Componente / flujo:** 020 Onboarding (`system_design.md` §5, §8, §15). Consume `contract_data.json` (salida de Discovery/010, simulada como fixture por `D-055`) y produce `map_client_data.json`. Hereda de `Flow` (`flow_base`, CONFORME) y consume `ClientContext` (`client_context`, CONFORME) para resolver rutas.

## Problema / Necesidad
Antes de que Ingestion (030) pueda cargar y validar los datos crudos del cliente, alguien tiene que traducir el contrato de datos acordado con el cliente (`contract_data.json`: jerarquías de producto/geografía, datasets históricos disponibles y su esquema de columnas) en un **mapa canónico** explícito y validado (`map_client_data.json`) que los flujos posteriores puedan consumir sin volver a interpretar el contrato crudo. Hoy no existe ningún componente que haga esta traducción: sin él, cada flujo downstream tendría que re-parsear y re-validar `contract_data.json` por su cuenta, duplicando lógica y arriesgando interpretaciones inconsistentes de a qué nivel de jerarquía corresponde cada columna. Onboarding resuelve esto de forma determinista (§6), sin tocar datos reales ni la capa bronze —esa responsabilidad es de Ingestion (030)—, y reconociendo que el negocio predice **demanda de productos, no ventas**: el contrato admite múltiples tipos de dataset (ventas, inventario, órdenes de compra, devoluciones, promociones, precios) precisamente porque las ventas son una señal parcial/censurada de la demanda real.

## Alcance

**In scope (banda `tracer_bullet`):**
- Un `Flow` concreto `Onboarding` (hereda de `flow_base`) que:
  1. Declara `contract_data.json` como `require` (input, `020_outputs/010_discovery/`) y `map_client_data.json` como `produce` (output, `020_outputs/020_onboarding/`).
  2. Lee y parsea `contract_data.json` con el esquema acordado (ver "Contrato de datos" abajo).
  3. Valida coherencia del contrato ANTES de derivar el mapa: cada miembro de `product_hierarchy.members`/`geography.members` tiene exactamente las claves declaradas en su `levels`; cada `maps_to` de cada `field` apunta a un nivel existente de `product.<level>`/`geography.<level>`, o es `"time"`, `"measure"` o `null`; los enums (`field.type`, `kind`, `source_medium`, `periodicity`) pertenecen a su vocabulario cerrado; cada archivo cumple `period_start ≤ period_end`.
  4. Si el contrato es inconsistente, falla con un error de contrato claro (sin escribir `map_client_data.json`).
  5. Si el contrato es válido, deriva y escribe `map_client_data.json` con, como mínimo: nombres y profundidad de los niveles de producto y de geografía; miembros/valores únicos observados por nivel; inventario de datasets del cliente (tipo `kind`, medio, periodicidad, lista de archivos con sus fechas); esquema de columnas por dataset con su `maps_to`.
- Soporte a jerarquías de **profundidad dinámica**: el número de niveles de producto/geografía se lee de `levels`, no se asume fijo en 4.
- Soporte estructural a multi-dataset (más de un `kind` por cliente) y multi-archivo (un dataset con más de un archivo, incluyendo archivos multi-año).
- Manejo de columnas obligatorias vs. opcionales (`required: true/false`) y de columnas cuyo nombre difiere del nivel al que mapean (resuelto vía `maps_to`, no por coincidencia de nombre).
- El fixture concreto de esta banda (acordado con el humano, ver abajo) usa jerarquías 4+4 niveles, dos datasets (ventas, inventario) y el caso simple pedido por `D-057` (pocos productos, geografía sencilla); el mecanismo es genérico, pero la banda solo se ejercita contra este fixture.

**Out of scope (esta banda; puede o no llegar en `stab_1`):**
- Discovery (010) real: `contract_data.json` es un **fixture fabricado**, no generado por un flujo Discovery real (`D-055`).
- Ingestion (030): lectura de csv/xlsx reales, comparación de datos reales contra el mapa, escritura en `bronze/`.
- Validar que los archivos históricos declarados en `contract_data.json` existan físicamente en disco (Onboarding trabaja solo sobre metadatos del contrato, no sobre los archivos de datos en sí).
- Los `kind` de dataset no ejercitados por el fixture (órdenes de compra, devoluciones, promociones, precios) y los `source_medium` distintos de `csv` (`xlsx`, `database`, `api`): el esquema los admite, pero no hay caso de prueba para ellos en esta banda.
- Uso de LLM (Onboarding es determinista, §6).
- El orquestador `foda run`.

## Contrato de datos `contract_data.json` (fixture acordado, D-055)
Estructura consensuada con el humano, punto por punto, para la banda `tracer_bullet`:

```json
{
  "schema_version": "0.1",
  "client": { "code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail" },
  "product_hierarchy": {
    "levels": ["familia", "categoria", "subcategoria", "clase"],
    "members": [
      { "familia": "Bebidas", "categoria": "Gaseosas", "subcategoria": "Cola",    "clase": "Cola 1.5L" },
      { "familia": "Bebidas", "categoria": "Aguas",    "subcategoria": "Sin gas", "clase": "Agua 600ml" },
      { "familia": "Snacks",  "categoria": "Papas",    "subcategoria": "Fritas",  "clase": "Papas 45g"  }
    ]
  },
  "geography": {
    "levels": ["region", "pais", "ciudad", "sede"],
    "members": [
      { "region": "Andina", "pais": "Colombia", "ciudad": "Bogota",   "sede": "Sede Norte"  },
      { "region": "Andina", "pais": "Colombia", "ciudad": "Medellin", "sede": "Sede Centro" }
    ]
  },
  "historical_data": {
    "datasets": [
      {
        "kind": "ventas",
        "source_medium": "csv",
        "periodicity": "mensual",
        "fields": [
          { "name": "fecha",           "type": "date",    "required": true,  "maps_to": "time" },
          { "name": "sede",            "type": "string",  "required": true,  "maps_to": "geography.sede" },
          { "name": "clase",           "type": "string",  "required": true,  "maps_to": "product.clase" },
          { "name": "cantidad",        "type": "integer", "required": true,  "maps_to": "measure" },
          { "name": "precio_unitario", "type": "number",  "required": false, "maps_to": null }
        ],
        "files": [
          { "name": "ventas_2023_2025.csv", "period_start": "2023-01-01", "period_end": "2025-12-31" }
        ]
      },
      {
        "kind": "inventario",
        "source_medium": "csv",
        "periodicity": "mensual",
        "fields": [
          { "name": "fecha", "type": "date",    "required": true, "maps_to": "time" },
          { "name": "sede",  "type": "string",  "required": true, "maps_to": "geography.sede" },
          { "name": "clase", "type": "string",  "required": true, "maps_to": "product.clase" },
          { "name": "stock", "type": "integer", "required": true, "maps_to": "measure" }
        ],
        "files": [
          { "name": "inventario_2024.csv", "period_start": "2024-01-01", "period_end": "2024-12-31" },
          { "name": "inventario_2025.csv", "period_start": "2025-01-01", "period_end": "2025-12-31" }
        ]
      }
    ]
  }
}
```

**Decisiones de diseño del contrato ya acordadas con el humano (no re-abrir sin GATE):**
1. Jerarquías dinámicas: `levels` es la fuente de verdad de cuántos/cuáles niveles hay (producto y geografía), profundidad variable. Cada miembro debe tener EXACTAMENTE las claves declaradas en su `levels`.
2. Miembros: lista plana de dicts cuyas claves coinciden con `levels`.
3. Esquema por dataset (no por archivo): todos los archivos de un dataset comparten `fields`.
4. Campos: `name` (único en el dataset), `type`, `required` (bool), `maps_to`.
5. **Modelo B — mapeo columna→nivel declarado en el contrato:** `maps_to` ∈ `"product.<level>"` | `"geography.<level>"` | `"time"` | `"measure"` | `null`. Onboarding consume esto; NO adivina el mapeo por nombre de columna.
6. Vocabularios controlados (enums cerrados): `field.type` ∈ {string, integer, number, date, boolean}; `kind` ∈ {ventas, inventario, ordenes_compra, devoluciones, promociones, precios}; `source_medium` ∈ {csv, xlsx, database, api}; `periodicity` ∈ {diaria, semanal, quincenal, mensual, trimestral, semestral, anual}. El fixture solo usa ventas+inventario/csv, pero el contrato admite los demás sin rediseño.
7. Archivos: fechas `YYYY-MM-DD`; validación `period_start ≤ period_end`.

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como **flujo downstream (Ingestion)**, quiero que Onboarding traduzca `contract_data.json` en un `map_client_data.json` con los niveles y la profundidad exactos de producto y geografía declarados en `levels`, para no tener que re-interpretar el contrato crudo. | Para el fixture acordado, `map_client_data.json` refleja 4 niveles de producto (`familia, categoria, subcategoria, clase`) y 4 de geografía (`region, pais, ciudad, sede`), con sus miembros/valores únicos correctos. |
| HU-02 | Como **flujo downstream**, quiero que Onboarding liste el inventario completo de datasets y archivos históricos del cliente (tipo, medio, periodicidad, archivos con sus fechas), para saber qué se espera cargar en Ingestion. | `map_client_data.json` lista los 2 datasets del fixture (ventas, inventario) con su `kind`/`source_medium`/`periodicity` y el número exacto de archivos de cada uno (1 para ventas, 2 para inventario), con sus fechas. |
| HU-03 | Como **flujo downstream**, quiero que Onboarding derive el esquema de columnas de cada dataset con su mapeo `maps_to` explícito, para saber a qué nivel de jerarquía o medida corresponde cada columna sin adivinar por nombre. | `map_client_data.json` expone, por dataset, la lista de columnas con `name`, `type`, `required` y su `maps_to` resuelto (incluye el caso `precio_unitario` con `maps_to: null` y el caso de columnas obligatorias vs. opcionales). |
| HU-04 | Como **operador del harness**, quiero que Onboarding rechace un `contract_data.json` inconsistente (jerarquía/miembros/`maps_to`/enum/fechas inválidas) antes de escribir ningún output, para detectar errores de contrato temprano sin propagar datos corruptos a Ingestion. | Ante un contrato con al menos un tipo de inconsistencia (p. ej. un miembro sin todas las claves de `levels`, o un `maps_to` a un nivel inexistente), Onboarding falla con un error de contrato claro y no crea `map_client_data.json`. |
| HU-05 | Como **desarrollador del harness**, quiero que `Onboarding` se integre como un `Flow` concreto sobre `ClientContext`, para reutilizar la orquestación y resolución de rutas ya construidas en `flow_base`/`client_context`. | `Onboarding` hereda de `Flow`, declara `requires=[contract_data.json]`/`produces=[map_client_data.json]` como `Artifact`, y su `run(ctx)` completa las 4 fases del template method sin reimplementar orquestación propia. |

## Dependencias
- `flow_base` (banda `tracer_bullet`, **CONFORME**): clase base `Flow`, `FlowResult`, `Artifact`, `FlowContractError` (`src/foda/core/flow.py`).
- `client_context` (banda `tracer_bullet`, **CONFORME**): `ClientContext` (`src/foda/core/context.py`), resolución de rutas de `010_inputs`/`020_outputs` por cliente.
- `700_architecture/system_design.md` §5 (modelo de flujos), §6 (determinismo), §7 (estructura de carpetas), §8 (contrato de artefactos), §15 (detalle 020 Onboarding).
- `800_persistence/decisions.md`: D-054 (elección de próxima feature), D-055 (fixture de `contract_data.json` en vez de Discovery real), D-056 (estrategia `tracer_bullet`), D-057 (escalabilidad progresiva, caso simple primero).
- Fixture `contract_data.json` reproducido íntegro en este documento (acordado con el humano), que `spec_writer`/`plan_builder` deben usar como caso base del tracer bullet.

## Riesgos y Supuestos
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** el formato exacto de `map_client_data.json` (nombres de claves, estructura anidada) no está fijado por `system_design.md` más allá de "mapa canónico"; queda a `spec_writer`/`plan_builder` proponerlo explícitamente, respetando NC-2 (simplicidad primero) y cubriendo como mínimo lo listado en HU-01/HU-02/HU-03.
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** el tipo de excepción a usar para "contrato inconsistente" (reutilizar `FlowContractError` de `flow_base` vs. una excepción propia de Onboarding, p. ej. `ContractValidationError`) no está decidido; queda a `spec_writer`/`plan_builder` definirlo explícitamente (NC-6).
- **Supuesto:** "valores únicos por nivel" en HU-01 se refiere a los valores distintos que aparecen en `members` para ese nivel (p. ej. únicos de `familia` = {Bebidas, Snacks}); `spec_writer` debe confirmar esta interpretación o ajustarla.
- **Aclaración de dominio (no es ambigüedad, para que `spec_writer` no la confunda):** Onboarding NO valida que los archivos físicos (csv/xlsx) declarados en `contract_data.json` existan en disco ni que su contenido cumpla el esquema — eso es Ingestion (030). Onboarding solo valida la coherencia INTERNA del propio `contract_data.json` (metadatos).
- **Riesgo:** el fixture de esta banda solo ejercita `kind` ∈ {ventas, inventario} y `source_medium = csv`; el comportamiento de Onboarding ante los demás valores del vocabulario cerrado (órdenes de compra, xlsx, database, api) no está probado en esta banda — se revisará en `stab_1` si el negocio lo requiere antes.
- **Riesgo:** el fixture usa jerarquías de 4 niveles tanto en producto como en geografía; aunque el diseño soporta profundidad dinámica, no hay caso de prueba en esta banda con una profundidad distinta de 4 — queda como candidato de endurecimiento para `stab_1` (coherente con `D-057`).
- **Riesgo:** no se ha decidido si `map_client_data.json` debe ser determinista en el ORDEN de sus listas (p. ej. orden de miembros, orden de datasets); si el test de integración lo requiere, `spec_writer`/`plan_builder` deben fijarlo explícitamente.
