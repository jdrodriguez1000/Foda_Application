# Spec — onboarding

> Artefacto de la etapa 2 (`spec_writer`). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables **codificados (`CA-xx`) y enlazados a las historias de usuario (`HU-xx`)** de `definition.md`. **Requiere aprobación humana** (gate) antes de planear.
>
> Banda: `tracer_bullet`. Fuentes canónicas: `600_features/onboarding/tracer_bullet/definition.md`, `600_features/onboarding/feature_contract.md`, `700_architecture/system_design.md` (§5, §6, §7, §8, §9, §15), `800_persistence/decisions.md` (D-054, D-055, D-056, D-057). Código reutilizado (CONFORME): `src/foda/core/flow.py` (`Flow`, `Artifact`, `FlowResult`, `FlowContractError`) y `src/foda/core/context.py` (`ClientContext`).

## Resumen
Un `Flow` concreto **`Onboarding`** (flujo 020, determinista, hereda de `flow_base`) que lee y valida la coherencia interna de `contract_data.json` (metadatos del cliente: jerarquías de producto/geografía de profundidad dinámica, inventario de datasets/archivos históricos y el mapeo `maps_to` columna→nivel) y, si el contrato es coherente, deriva de forma **reproducible byte a byte** el mapa canónico `map_client_data.json`; si el contrato es inconsistente, falla con `FlowContractError` sin escribir salida, y **nunca** toca datos reales ni las capas `bronze/`/`silver/`/`gold/`.

---

## Decisiones formalizadas por spec_writer

La `definition.md` delegó a esta etapa cuatro puntos abiertos (forma de `map_client_data.json`, tipo de excepción, interpretación de "valores únicos por nivel", determinismo del orden). Se resuelven aquí con su razonamiento (NC-1/NC-2/NC-6) y quedan listados abajo como **puntos del GATE humano**. Ninguno se asume en silencio.

### DS-ONB-1 — Excepción de contrato: reutilizar `FlowContractError`
- **Decisión:** ante **cualquier** inconsistencia del contrato, `Onboarding` lanza **`FlowContractError`** (la excepción canónica ya definida en `src/foda/core/flow.py`, CONFORME), con un mensaje claro que nombra el problema concreto. **No** se crea una excepción nueva.
- **Razón:** `FlowContractError` es exactamente "el flujo declaró un requisito de entrada y el contrato se violó" (§8/§9). La ausencia **física** del artefacto ya la modela `Flow.validate()` base con esta misma excepción; extender su uso a las inconsistencias de **contenido** del contrato mantiene un único tipo de dominio capturable con `pytest.raises(FlowContractError)` (NC-2 simplicidad, NC-3 cambios quirúrgicos). No hay un segundo tipo de error que justifique una jerarquía propia (NC-2).
- **Alternativa descartada:** una `ContractValidationError` propia de Onboarding. Descartada por no aportar distinción útil a ningún consumidor en esta banda y duplicar el concepto ya cubierto por `FlowContractError`.

### DS-ONB-2 — Esquema de `map_client_data.json` (mapa canónico)
- **Decisión:** `system_design.md` no fija el esquema; se propone la forma mínima (NC-2) que cubre HU-01/HU-02/HU-03 y lo que Ingestion (030) necesitará consumir. Ver **Contratos de Datos** abajo (esquema + ejemplo derivado del fixture). Contiene: identidad del cliente; por jerarquía (`product`, `geography`) los `levels` en orden declarado, `depth`, `unique_values` y `unique_counts` por nivel y `member_count`; `datasets` (inventario con `kind`/`source_medium`/`periodicity`, `file_count`, `files` con fechas y `fields` con `name`/`type`/`required`/`maps_to`); y `totals` (`dataset_count`, `file_count`).
- **Razón:** es la superficie mínima verificable que refleja fielmente el contrato sin reinterpretarlo, evitando que cada flujo downstream re-parsee `contract_data.json`.

### DS-ONB-3 — "Valores únicos por nivel"
- **Decisión:** para cada nivel de producto y de geografía, el conjunto de valores **distintos** que aparecen en `members` para esa clave. Se reporta por nivel tanto la lista ordenada (`unique_values`) como el conteo (`unique_counts`). Ej. con los 3 miembros de producto del fixture: `familia`→{Bebidas, Snacks} (2), `categoria`→{Aguas, Gaseosas, Papas} (3), `subcategoria`→3, `clase`→3.
- **Razón:** interpretación confirmada del supuesto de `definition.md`; es lo que un downstream necesita para conocer la cardinalidad real observada por nivel.

### DS-ONB-4 — Determinismo del output (reproducible byte a byte)
- **Decisión:** mismo `contract_data.json` de entrada ⇒ mismo `map_client_data.json` de salida, **byte a byte**. Orden estable:
  - **niveles** (`levels` y las claves de `unique_values`/`unique_counts`): en el **orden declarado** en `levels` (no alfabético);
  - **valores únicos** por nivel: en **orden alfabético ascendente**;
  - **datasets**: en el **orden en que aparecen** en el contrato; **files** y **fields** de cada dataset: en su orden del contrato;
  - **serialización:** JSON con `indent=2`, `ensure_ascii=False`, **claves de objeto ordenadas de forma estable** (p. ej. `sort_keys=True`) y un salto de línea final. Como `unique_values`/`unique_counts` conservan el orden semántico en la lista `levels`, ordenar las claves de objeto no altera la información.
- **Razón:** el determinismo (§6) es requisito para que el test de integración compare el output contra un esperado fijo y para reproducibilidad entre corridas.

### DS-ONB-5 — Ubicación de artefactos y hooks del `Flow`
- **Decisión (sin cambios al core, confirmada con el humano):** `Onboarding` declara
  - `requires = [Artifact(name="contract_data", base="outputs", relative="010_discovery/contract_data.json")]`
  - `produces = [Artifact(name="map_client_data", base="outputs", relative="020_onboarding/map_client_data.json")]`
  La resolución `020_outputs/<flujo>/` ya la soporta `Artifact` vía `base="outputs"` + `relative`; **no** se amplía `ClientContext`.
- **Orden de validación (respeta el template method `load_inputs → validate → execute → write_outputs`):**
  - `load_inputs(ctx)` lee y parsea `contract_data.json` a estado de la instancia **solo si el archivo existe**; si no existe, deja el estado sin cargar para que `validate()` base lo detecte (no lanza `FileNotFoundError` crudo).
  - `validate(ctx)` invoca primero `super().validate(ctx)` (existencia física del `require` → `FlowContractError` si falta) y **luego** valida la coherencia de **contenido** del contrato ya cargado (reglas abajo), lanzando `FlowContractError` ante la primera inconsistencia. No escribe en disco.
  - `execute(ctx)` deriva el mapa canónico en memoria y devuelve `FlowResult(success=True, outputs=[<ruta de map_client_data.json>])`.
  - `write_outputs(ctx, result)` crea la carpeta destino con `path.parent.mkdir(parents=True, exist_ok=True)` y escribe `map_client_data.json` (serialización determinista de DS-ONB-4).
- **Razón:** valida antes de derivar (feature contract) y garantiza que ninguna inconsistencia produzca output (HU-04). No toca `bronze/`/`silver/`/`gold/` ni datos reales (feature CA-3).

---

## Contratos de Datos / Artefactos

| Dirección | Artefacto | Ruta (vía `ClientContext`) | Formato |
|---|---|---|---|
| requiere | `contract_data` | `Artifact(base="outputs", relative="010_discovery/contract_data.json")` → `ctx.outputs_dir / "010_discovery/contract_data.json"` | JSON |
| produce | `map_client_data` | `Artifact(base="outputs", relative="020_onboarding/map_client_data.json")` → `ctx.outputs_dir / "020_onboarding/map_client_data.json"` | JSON |
| produce (módulo) | `src/foda/flows/f020_onboarding/` | módulo Python (clase `Onboarding(Flow)`) | — |

### Entrada — `contract_data.json` (esquema esperado)
Estructura acordada con el humano (D-055), reproducida en `definition.md`. Campos y tipos:
- `schema_version`: string.
- `client`: `{ code: string, name: string, sector: string }`.
- `product_hierarchy` y `geography`: `{ levels: [string, …] (no vacío), members: [ {<clave por cada level>: string}, … ] }`.
- `historical_data.datasets`: lista de `{ kind, source_medium, periodicity, fields: [{ name, type, required, maps_to }], files: [{ name, period_start, period_end }] }`.

**Vocabularios cerrados (enums):**
- `field.type` ∈ {`string`, `integer`, `number`, `date`, `boolean`}.
- `kind` ∈ {`ventas`, `inventario`, `ordenes_compra`, `devoluciones`, `promociones`, `precios`}.
- `source_medium` ∈ {`csv`, `xlsx`, `database`, `api`}.
- `periodicity` ∈ {`diaria`, `semanal`, `quincenal`, `mensual`, `trimestral`, `semestral`, `anual`}.
- `maps_to` ∈ {`"product.<level>"` (level ∈ `product_hierarchy.levels`), `"geography.<level>"` (level ∈ `geography.levels`), `"time"`, `"measure"`, `null`}.

### Salida — `map_client_data.json` (esquema propuesto, DS-ONB-2)
```json
{
  "schema_version": "0.1",
  "client": { "code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail" },
  "hierarchies": {
    "product": {
      "levels": ["familia", "categoria", "subcategoria", "clase"],
      "depth": 4,
      "member_count": 3,
      "unique_values": {
        "familia": ["Bebidas", "Snacks"],
        "categoria": ["Aguas", "Gaseosas", "Papas"],
        "subcategoria": ["Cola", "Fritas", "Sin gas"],
        "clase": ["Agua 600ml", "Cola 1.5L", "Papas 45g"]
      },
      "unique_counts": { "familia": 2, "categoria": 3, "subcategoria": 3, "clase": 3 }
    },
    "geography": {
      "levels": ["region", "pais", "ciudad", "sede"],
      "depth": 4,
      "member_count": 2,
      "unique_values": {
        "region": ["Andina"],
        "pais": ["Colombia"],
        "ciudad": ["Bogota", "Medellin"],
        "sede": ["Sede Centro", "Sede Norte"]
      },
      "unique_counts": { "region": 1, "pais": 1, "ciudad": 2, "sede": 2 }
    }
  },
  "datasets": [
    {
      "kind": "ventas",
      "source_medium": "csv",
      "periodicity": "mensual",
      "file_count": 1,
      "files": [
        { "name": "ventas_2023_2025.csv", "period_start": "2023-01-01", "period_end": "2025-12-31" }
      ],
      "fields": [
        { "name": "fecha",           "type": "date",    "required": true,  "maps_to": "time" },
        { "name": "sede",            "type": "string",  "required": true,  "maps_to": "geography.sede" },
        { "name": "clase",           "type": "string",  "required": true,  "maps_to": "product.clase" },
        { "name": "cantidad",        "type": "integer", "required": true,  "maps_to": "measure" },
        { "name": "precio_unitario", "type": "number",  "required": false, "maps_to": null }
      ]
    },
    {
      "kind": "inventario",
      "source_medium": "csv",
      "periodicity": "mensual",
      "file_count": 2,
      "files": [
        { "name": "inventario_2024.csv", "period_start": "2024-01-01", "period_end": "2024-12-31" },
        { "name": "inventario_2025.csv", "period_start": "2025-01-01", "period_end": "2025-12-31" }
      ],
      "fields": [
        { "name": "fecha", "type": "date",    "required": true, "maps_to": "time" },
        { "name": "sede",  "type": "string",  "required": true, "maps_to": "geography.sede" },
        { "name": "clase", "type": "string",  "required": true, "maps_to": "product.clase" },
        { "name": "stock", "type": "integer", "required": true, "maps_to": "measure" }
      ]
    }
  ],
  "totals": { "dataset_count": 2, "file_count": 3 }
}
```
> Nota: el `schema_version` de salida puede propagarse desde el contrato de entrada. El orden mostrado de las claves de objeto es ilustrativo; la serialización real usa claves ordenadas de forma estable (DS-ONB-4). El contenido semántico (listas y valores) es lo verificable.

---

## Comportamiento Esperado

Ejecución de `Onboarding().run(ctx)`:

1. **`load_inputs(ctx)`** — lee `contract_data.json` (ruta del `require`) y lo parsea a estado de la instancia **si existe**. Si no existe, no carga nada (deja que la fase 2 lo detecte). No escribe en disco.
2. **`validate(ctx)`** —
   - **2a. Existencia (base):** `super().validate(ctx)` comprueba que el `require` exista; si falta → `FlowContractError` (antes de `execute`), sin salida.
   - **2b. Coherencia de contenido** (solo si 2a pasó), en este orden lógico; a la **primera** violación lanza `FlowContractError` con mensaje que nombra el problema, **sin escribir** `map_client_data.json`:
     - `product_hierarchy.levels` y `geography.levels` **no vacíos**.
     - Cada miembro de `members` tiene **exactamente** las claves declaradas en su `levels` (ni de más, ni de menos).
     - En cada dataset, `field.name` **único** dentro del dataset.
     - `field.required` es booleano.
     - Enums válidos: `field.type`, `kind`, `source_medium`, `periodicity` pertenecen a su vocabulario cerrado.
     - Cada `field.maps_to` es válido: `null`, `"time"`, `"measure"`, o `"product.<level>"`/`"geography.<level>"` con `<level>` **existente** en los `levels` respectivos.
     - Cada archivo: `period_start` y `period_end` son fechas `YYYY-MM-DD` válidas y `period_start ≤ period_end`.
3. **`execute(ctx)`** — deriva en memoria el mapa canónico (identidad del cliente; jerarquías con niveles en orden, valores únicos y conteos; inventario de datasets con esquema; totales) y devuelve `FlowResult(success=True, outputs=[<ruta de map_client_data.json>])`.
4. **`write_outputs(ctx, result)`** — crea la carpeta destino (`mkdir(parents=True, exist_ok=True)`) y escribe `map_client_data.json` de forma determinista (DS-ONB-4).
5. **`run` devuelve** el `FlowResult` de `execute`.

**Invariantes:**
- Onboarding **no** lee ni escribe csv/xlsx de datos reales, ni `bronze/`/`silver/`/`gold/`; solo opera sobre metadatos y escribe un único JSON bajo `020_outputs/020_onboarding/`.
- Ante cualquier fallo de validación, **no** queda `map_client_data.json` en disco.
- Profundidad de jerarquía **dinámica**: se deriva de `levels`, sin asumir 4 niveles.

---

## Casos Límite y Errores

| Caso | Contexto | Resultado esperado |
|---|---|---|
| Contrato válido (fixture) | fixture acordado (ventas + inventario, 4+4 niveles) | `map_client_data.json` correcto y completo; `FlowResult(success=True)`. |
| Profundidad ≠ 4 | `product_hierarchy.levels` de 3 niveles (o geografía de 2) con miembros coherentes | mapa con `depth` = 3 y niveles en orden; sin hardcode de 4. |
| Archivo multi-año | dataset con archivo `period_start/period_end` que cruza varios años (p. ej. 2023-01-01 → 2025-12-31) | reflejado tal cual en `files`; no se descompone por año. |
| Multi-dataset / multi-archivo | 2 datasets, uno con 2 archivos | `file_count` por dataset (1 y 2); `totals.file_count = 3`; `totals.dataset_count = 2`. |
| Columna opcional / `maps_to: null` | `precio_unitario` con `required=false`, `maps_to=null` | reflejada en `fields` con `required=false` y `maps_to=null`; contrato válido. |
| `levels` vacío | `product_hierarchy.levels = []` (o geografía) | `FlowContractError`; sin salida. |
| Miembro incoherente con `levels` | un miembro con una clave de menos o de más respecto a `levels` | `FlowContractError`; sin salida. |
| `maps_to` a nivel inexistente | `maps_to = "product.marca"` con `marca ∉ levels` | `FlowContractError`; sin salida. |
| Enum inválido | `type`/`kind`/`source_medium`/`periodicity` fuera del vocabulario | `FlowContractError`; sin salida. |
| `name` duplicado | dos `field.name` iguales en un dataset | `FlowContractError`; sin salida. |
| Fecha inválida / rango invertido | fecha no `YYYY-MM-DD`, o `period_start > period_end` | `FlowContractError`; sin salida. |
| `contract_data.json` ausente | el `require` no existe en disco | `FlowContractError` en `validate` base (fase 2a); sin salida. |
| Reproducibilidad | dos `run(ctx)` con el mismo input | `map_client_data.json` idéntico byte a byte. |

---

## Interfaces / Firmas Públicas

```python
# src/foda/flows/f020_onboarding/onboarding.py  (nombre de módulo a fijar por plan_builder)
from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowContractError, FlowResult


class Onboarding(Flow):
    """Flujo 020: deriva map_client_data.json desde contract_data.json (determinista)."""

    name = "onboarding"
    requires = [Artifact(name="contract_data", base="outputs",
                         relative="010_discovery/contract_data.json")]
    produces = [Artifact(name="map_client_data", base="outputs",
                         relative="020_onboarding/map_client_data.json")]

    def load_inputs(self, ctx: ClientContext) -> None: ...
    def validate(self, ctx: ClientContext) -> None: ...      # super().validate() + coherencia de contenido
    def execute(self, ctx: ClientContext) -> FlowResult: ...
    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None: ...
```
- **No** sobreescribe `run()`: usa el template method heredado de `Flow`.
- **Contrato de errores:** `FlowContractError` para require ausente (base) y para toda inconsistencia de contenido (DS-ONB-1).
- Los nombres exactos de módulo/archivo y la firma interna de helpers son detalle de `plan_builder`; lo observable es la clase `Onboarding(Flow)` con esos `requires`/`produces` y los 4 hooks sobreescritos.

---

## Criterios de Aceptación (verificables)
> Cada criterio es traducible a uno o más tests (usando el fixture acordado y/o variantes, un `ClientContext` bajo `tmp_path`, y `pytest.raises(FlowContractError)` para los errores) y traza a la(s) `HU-xx` que satisface. Cumple D-031 (trazabilidad codificada HU→CA).

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | Dado el fixture válido, `Onboarding().run(ctx)` escribe `map_client_data.json` en `ctx.outputs_dir / "020_onboarding/map_client_data.json"` y devuelve `FlowResult(success=True, outputs=[esa ruta])`; el archivo existe en disco. | HU-01, HU-05 |
| CA-02 | En el mapa, `hierarchies.product.levels == ["familia","categoria","subcategoria","clase"]` (orden declarado) y `hierarchies.product.depth == 4`. | HU-01 |
| CA-03 | En el mapa, `hierarchies.geography.levels == ["region","pais","ciudad","sede"]` y `hierarchies.geography.depth == 4`. | HU-01 |
| CA-04 | Los valores únicos por nivel son los distintos observados en `members`, en orden alfabético ascendente: p. ej. `product.unique_values.familia == ["Bebidas","Snacks"]` con `unique_counts.familia == 2`, y `geography.unique_counts.ciudad == 2` (`["Bogota","Medellin"]`). | HU-01 |
| CA-05 | Dado un contrato cuya `product_hierarchy.levels` tiene profundidad ≠ 4 (p. ej. 3 niveles) con miembros coherentes, el mapa refleja `depth` = 3 y esos niveles en orden, sin asumir 4 niveles. | HU-01 |
| CA-06 | El mapa lista los 2 datasets del fixture con su `kind`/`source_medium`/`periodicity` correctos y en el orden del contrato (ventas, luego inventario). | HU-02 |
| CA-07 | El mapa refleja `file_count == 1` para ventas y `file_count == 2` para inventario, con cada `files[*].name`/`period_start`/`period_end` del contrato (incluye el archivo multi-año de ventas 2023-01-01→2025-12-31). | HU-02 |
| CA-08 | Para cada dataset, `fields` expone cada columna con `name`/`type`/`required`/`maps_to`, incluido `precio_unitario` con `required=false` y `maps_to=null`. | HU-03 |
| CA-09 | El `maps_to` de cada columna se toma del contrato, no del nombre: `sede` → `"geography.sede"`, `clase` → `"product.clase"`, `cantidad`/`stock` → `"measure"`, `fecha` → `"time"`. | HU-03 |
| CA-10 | `totals.dataset_count == 2` y `totals.file_count == 3` (suma de archivos de todos los datasets). | HU-02 |
| CA-11 | `Onboarding` hereda de `Flow`, declara `requires` con `Artifact(base="outputs", relative="010_discovery/contract_data.json")` y `produces` con `Artifact(base="outputs", relative="020_onboarding/map_client_data.json")`, y completa las 4 fases del template method sin sobreescribir `run`. | HU-05 |
| CA-12 | Tras un `run(ctx)` exitoso, no existe ningún archivo ni carpeta creada bajo `ctx.bronze_dir`/`ctx.silver_dir`/`ctx.gold_dir`; el único artefacto escrito es `map_client_data.json` bajo `020_outputs/020_onboarding/`. | HU-05 |
| CA-13 | Dos ejecuciones de `run(ctx)` con el mismo `contract_data.json` producen un `map_client_data.json` idéntico byte a byte (output determinista). | HU-01 |
| CA-14 | Con `product_hierarchy.levels == []` (o `geography.levels == []`), `run(ctx)` lanza `FlowContractError` y no se crea `map_client_data.json`. | HU-04 |
| CA-15 | Con un miembro cuyas claves no coinciden exactamente con `levels` (falta una o sobra una), `run(ctx)` lanza `FlowContractError` y no se crea el output. | HU-04 |
| CA-16 | Con un `field.maps_to == "product.<level>"` (o `"geography.<level>"`) cuyo `<level>` no existe en los `levels` respectivos, `run(ctx)` lanza `FlowContractError` y no se crea el output. | HU-04 |
| CA-17 | Con un enum inválido en `field.type`, `kind`, `source_medium` o `periodicity`, `run(ctx)` lanza `FlowContractError` y no se crea el output. | HU-04 |
| CA-18 | Con un archivo cuyo `period_start > period_end` (o una fecha no `YYYY-MM-DD`), `run(ctx)` lanza `FlowContractError` y no se crea el output. | HU-04 |
| CA-19 | Con dos `field.name` duplicados dentro de un mismo dataset, `run(ctx)` lanza `FlowContractError` y no se crea el output. | HU-04 |
| CA-20 | Si `contract_data.json` no existe en disco, `run(ctx)` lanza `FlowContractError` en `validate` (existencia base) antes de derivar, y no se crea `map_client_data.json`. | HU-04, HU-05 |
| CA-21 | Ante cualquier inconsistencia de contrato (CA-14…CA-19), el fallo ocurre en `validate` (antes de `execute`/`write_outputs`): no queda `map_client_data.json` ni salida parcial en disco. | HU-04 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` queda cubierta por ≥ 1 `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02, CA-03, CA-04, CA-05, CA-13 |
| HU-02 | CA-06, CA-07, CA-10 |
| HU-03 | CA-08, CA-09 |
| HU-04 | CA-14, CA-15, CA-16, CA-17, CA-18, CA-19, CA-20, CA-21 |
| HU-05 | CA-01, CA-11, CA-12, CA-20 |

---

## No-Objetivos
- **Discovery (010) real:** `contract_data.json` es un fixture fabricado (D-055); Onboarding no genera cuestionarios ni usa LLM.
- **Ingestion (030):** lectura de csv/xlsx reales, comparación de datos reales contra el mapa, escritura en `bronze/`/`silver/`/`gold/`.
- **Validar existencia física de los archivos históricos** declarados en `files` (Onboarding valida solo metadatos del contrato, no el disco de datos).
- **`kind` no ejercitados por el fixture** (`ordenes_compra`, `devoluciones`, `promociones`, `precios`) y `source_medium` ≠ `csv` (`xlsx`, `database`, `api`): el esquema los admite (enum), pero no hay caso de prueba en esta banda (candidatos a `stab_1`).
- **Uso de LLM** (Onboarding es determinista, §6).
- **Orquestador `foda run`** y ampliación de `ClientContext`.
- **Validación con JSON Schema/Pydantic:** la validación es explícita en `validate()`, sin framework de esquema (coherente con D-042).

---

## Puntos de confirmación para el GATE humano
Decisiones tomadas por `spec_writer` (delegadas por `definition.md`) que el humano valida o ajusta antes de `plan_builder`:
1. **DS-ONB-1 — excepción:** ¿se acepta reutilizar `FlowContractError` para toda inconsistencia de contrato (contenido), en vez de crear una `ContractValidationError` propia?
2. **DS-ONB-2 — esquema de `map_client_data.json`:** ¿se acepta la forma propuesta (`client`, `hierarchies.{product,geography}` con `levels`/`depth`/`member_count`/`unique_values`/`unique_counts`, `datasets` con `file_count`/`files`/`fields`, `totals`)?
3. **DS-ONB-3 — "valores únicos por nivel":** ¿se acepta reportar por nivel la lista alfabética (`unique_values`) más el conteo (`unique_counts`)?
4. **DS-ONB-4 — determinismo:** ¿se acepta el criterio de orden (niveles en orden declarado, únicos alfabéticos, datasets/files/fields en orden de contrato, JSON con claves ordenadas + `indent=2` + newline final) y la garantía byte a byte?
5. **DS-ONB-5 — hooks/orden de validación:** ¿se acepta que `load_inputs` cargue solo si el archivo existe y que `validate()` haga `super().validate()` (existencia) y luego la validación de contenido, fallando a la primera inconsistencia; y que `write_outputs` cree la carpeta destino con `mkdir(parents=True, exist_ok=True)`?
