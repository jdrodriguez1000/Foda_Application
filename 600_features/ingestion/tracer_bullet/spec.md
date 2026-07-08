# Spec — ingestion

> Artefacto de la etapa 2 (`spec_writer`). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables **codificados (`CA-xx`) y enlazados a las historias de usuario (`HU-xx`)** de `definition.md`. **Requiere aprobación humana** (gate) antes de planear.
>
> Banda: `tracer_bullet`. Fuentes canónicas: `600_features/ingestion/tracer_bullet/definition.md`, `600_features/ingestion/feature_contract.md`, `700_architecture/system_design.md` (§5, §6, §7, §8, §9, §10, §15), `800_persistence/decisions.md` (D-047..D-067, esp. D-058/D-059 del contrato). Código reutilizado (CONFORME): `src/foda/core/flow.py` (`Flow`, `Artifact`, `FlowResult`, `FlowContractError`) y `src/foda/core/context.py` (`ClientContext`, incluye `bronze_dir`).

## Resumen
Un `Flow` concreto **`Ingestion`** (flujo 030, determinista, hereda de `flow_base`) que, dado `contract_data.json` (**fuente de verdad del conjunto de archivos esperados**), `map_client_data.json` (**fuente de las columnas esperadas por dataset**) y los archivos de datos crudos del cliente depositados en un *landing* conocido, lee cada archivo (csv/txt delimitados por `,`/`;`/`|`, o `.xlsx`) detectando el separador, valida de forma determinista que el conjunto de archivos (contra el contrato) y las columnas (contra el mapa, por **nombre/presencia**) coinciden con lo declarado, copia **byte a byte** a `data/bronze/` los archivos válidos (sin transformarlos) y produce un **reporte de carga JSON** (`020_outputs/030_ingestion/ingestion_report.json`) con, por archivo, filas/columnas y las inconsistencias detectadas — sin usar LLM y sin tocar `silver/`/`gold/`.

---

## Decisiones formalizadas por spec_writer

La `definition.md` delegó a esta etapa ocho puntos abiertos. Se resuelven aquí con su razonamiento (NC-1/NC-2/NC-6) y quedan listados al final como **puntos del GATE humano**. Ninguno se asume en silencio.

### DS-ING-1 — Mecanismo ante inconsistencias: soft-report, sin abortar
- **Decisión:** las inconsistencias de **datos** (archivo declarado faltante, archivo presente no declarado, columna requerida ausente, columna no declarada presente) **no** lanzan excepción: se **acumulan en el reporte de carga** y el flujo **continúa** con los datasets/archivos válidos. `FlowContractError` se reserva **exclusivamente** para la ausencia física de los **artefactos de contrato requeridos** (`contract_data.json`, `map_client_data.json`), que ya modela `Flow.validate()` base. `FlowResult.success` es `False` si el reporte registra ≥ 1 inconsistencia, `True` si no hay ninguna (§9: "FlowResult encapsula estado (éxito/inconsistencias)").
- **Razón:** HU-05 exige un reporte que **liste** las inconsistencias detectadas; HU-02/HU-03 piden "detecta y reporta … sin copiar a bronze el afectado" (implican que los válidos **sí** se copian). Abortar con excepción a la primera inconsistencia impediría emitir el reporte y contradiría esas HU. En cambio, un `contract_data.json`/`map_client_data.json` **ausente** sí es una violación dura del contrato de entrada del flujo (semántica exacta de `FlowContractError`, coherente con `onboarding`/`flow_base`), porque sin ellos no hay esquema contra el cual validar nada.
- **Alternativa descartada:** reutilizar `FlowContractError` (o una excepción propia) para inconsistencias de datos. Descartada porque abortaría antes de escribir el reporte (rompe HU-05) y no permitiría copia parcial (rompe HU-02/HU-03/HU-04).

### DS-ING-2 — Esquema del reporte de carga (`ingestion_report.json`)
- **Decisión:** `system_design.md` no fija el esquema; se propone la forma mínima (NC-2) que cubre HU-05. Ver **Contratos de Datos** abajo (esquema + ejemplo). Contiene: identidad del cliente; `summary` con conteos; `datasets` (en el orden del mapa) y por dataset sus `files` con `name`/`status`/`rows`/`columns`/`separator`/`bronze_path`/`inconsistencies`; `unexpected_files` (nombres de archivos presentes no declarados); y una lista **top-level `inconsistencies[]`** que **agrega todas** las inconsistencias del run con `type`+`detail` (**enmienda DS-ING-9**, ver abajo). `success` refleja DS-ING-1.
- **Razón:** superficie mínima verificable que responde "qué se cargó, con cuántas filas/columnas, y qué falló" de un vistazo (HU-05), sin duplicar información ni añadir campos no pedidos.

### DS-ING-9 — Enmienda de DS-ING-2: lista top-level `inconsistencies[]` (decisión del humano, ADR D-078)
- **Decisión:** el reporte gana una lista **top-level `inconsistencies[]`** que **agrega todas** las inconsistencias del run (de archivo —`missing_file`, `unexpected_file`— y de columna —`missing_column`, `unexpected_column`—), cada una con `type` (vocabulario cerrado de 4) y `detail` legible no vacío. Esto da un **hogar estructural** a `unexpected_file`, que corresponde a un archivo **sobrante** sin dataset propio y por tanto no cabía en `datasets[].files[].inconsistencies`. La lista `unexpected_files` (nombres, orden alfabético) se conserva; las inconsistencias de columna siguen **además** anidadas en `datasets[].files[].inconsistencies`. Es **aditivo**: no elimina ni renombra campos previos. **CA-16 se verifica sobre esta lista top-level.**
- **Razón:** salda la contradicción entre el vocabulario cerrado de 4 tipos (incl. `unexpected_file`) + el comportamiento de `execute` ("+ inconsistencia `unexpected_file`") + CA-16, y el esquema previo que solo anidaba inconsistencias por archivo. Toca un esquema ya aprobado en GATE, por eso se formaliza como decisión explícita (ADR D-078, NC-6), no como cambio silencioso.

### DS-ING-3 — Alcance de validación de columnas: presencia/nombre, no tipos
- **Decisión:** en esta banda la validación de columnas es **solo por nombre/presencia**: (a) toda columna cuyo `field.required == true` en el esquema del dataset debe estar presente en la cabecera del archivo; (b) toda columna presente en el archivo debe estar declarada como algún `field.name` del dataset (no se admiten columnas desconocidas); (c) los `field.required == false` (p. ej. `precio_unitario`) **pueden** estar ausentes sin ser inconsistencia. **No** se validan tipos de dato ni contenido de celdas.
- **Razón:** el tracer_bullet es un slice mínimo (NC-2/NC-4); la validación de tipos por columna está explícitamente diferida a `stab_1` (feature_contract, tabla de bandas). Una columna "renombrada" se detecta igual: aparece como columna requerida ausente + columna no declarada presente.

### DS-ING-4 — Origen físico de los archivos crudos: landing en `010_inputs/030_ingestion/`
- **Decisión:** el DS deposita los archivos crudos en `clients/<CLIENTE>/010_inputs/030_ingestion/<nombre_archivo>`, resuelto vía `ctx.inputs_dir / "030_ingestion"`. **No** se amplía `ClientContext` ni `Artifact._BASE_TO_DIR_ATTR` (NC-3): se reutiliza la base lógica `inputs` ya existente. Los archivos crudos **no** se declaran como `Artifact` estáticos en `requires` (sus nombres son dinámicos, provienen del contrato): su presencia se valida **dentro del flujo** y se reporta como inconsistencia (DS-ING-1), no como existencia de require base.
- **Razón:** minimiza el cambio (no toca el core) y respeta la convención de numeración `010_inputs/<flujo>/` (§7). Es un *staging* de entrada del flujo, distinto de `bronze/` (que es la **salida** inmutable). Si el landing no existe o está vacío, se reportan todos los archivos declarados como `missing` (no es `FlowContractError`).
- **Alternativa descartada:** una base nueva `landing` bajo `data/` que exigiría ampliar `_BASE_TO_DIR_ATTR` y `ClientContext`. Descartada por sobre-ingeniería para el tracer_bullet (NC-2/NC-3); candidata a revisión en `stab_1` si el negocio lo pide.
- **Salvedad para el GATE:** §7 describe `010_inputs` como "YAML: decisiones humanas"; aquí se depositan además datos crudos (csv/txt/xlsx) del cliente. Es una extensión menor de esa convención que se marca para validación humana.

### DS-ING-5 — Inconsistencia parcial: copia parcial + reporte; unidad = archivo
- **Decisión:** la unidad de copia es el **archivo**. Un archivo se copia a `bronze/` **si y solo si** está declarado en el contrato, está presente en el landing y pasa la validación de columnas (DS-ING-3). Los archivos inválidos (faltantes, no declarados, o con columnas incorrectas) **no** se copian; todos —válidos e inválidos— quedan documentados en el reporte. No se aborta el flujo por una inconsistencia parcial.
- **Razón:** HU-04 quiere una fuente inmutable desde la cual reprocesar; bloquear todo por un dataset erróneo desperdiciaría los datos válidos y contradice HU-02/HU-03 ("sin copiar … el afectado", implicando que el resto sí). La granularidad por archivo es la más fina coherente con el reporte por archivo (HU-05).

### DS-ING-6 — Copia fiel byte a byte + determinismo del reporte y hooks
- **Decisión (fidelidad):** la copia a `bronze/` es **byte a byte** del archivo de origen (copia binaria; no se re-serializa ni se normaliza). La **lectura** para contar filas/columnas y validar columnas es independiente de la copia: leer para reportar, copiar los bytes originales para bronze. Así la copia es idéntica al original (HU-04) preservando formato, separador y extensión.
- **Decisión (determinismo, §6):** mismas entradas ⇒ mismo `ingestion_report.json` byte a byte y mismas copias en bronze. Orden estable: `datasets` en el orden del mapa; `files` de cada dataset en el orden declarado en el contrato/mapa; `unexpected_files` en orden alfabético ascendente; serialización JSON con `indent=2`, `ensure_ascii=False`, `sort_keys=True` y salto de línea final.
- **Decisión (hooks, respeta el template method `load_inputs → validate → execute → write_outputs`):**
  - `load_inputs(ctx)` lee y parsea `contract_data.json` y `map_client_data.json` a estado de la instancia **solo si existen**; si faltan, deja el estado sin cargar para que `validate()` base lo detecte.
  - `validate(ctx)` invoca `super().validate(ctx)` (existencia física de los `requires` → `FlowContractError` si falta alguno). **No** valida datos aquí (eso es soft-report en `execute`).
  - `execute(ctx)` lee cada archivo del landing, detecta separador / lee xlsx, cuenta filas (de datos, sin cabecera) y columnas, valida columnas (DS-ING-3), arma el reporte en memoria (DS-ING-2) y el plan de copia (DS-ING-5), y devuelve `FlowResult(success=<sin inconsistencias>, outputs=[<ruta reporte>] + <rutas bronze de archivos válidos>)`.
  - `write_outputs(ctx, result)` crea las carpetas destino (`mkdir(parents=True, exist_ok=True)`), copia byte a byte los archivos válidos a `ctx.bronze_dir` y escribe `ingestion_report.json`.
- **Razón:** consistencia con el patrón ya usado en `onboarding` (DS-ONB-4/DS-ONB-5) y con §9; garantiza reproducibilidad para el test de integración.

### DS-ING-7 — Fixture del tracer_bullet (composición y dependencia)
- **Decisión (composición, análoga a D-055):** el fixture provee un `contract_data.json` + `map_client_data.json` coherentes entre sí (alineados con el esquema de `onboarding`, D-058) y los archivos crudos en el landing. Ejercita **los tres separadores + xlsx + extensión `.txt`** y **≥ 2 `kind` distintos de "ventas"**:

  | dataset (`kind`) | `source_medium` | archivo | formato / separador |
  |---|---|---|---|
  | `ventas` | `csv` | `ventas.csv` | delimitado por coma `,` |
  | `inventario` | `csv` | `inventario_2024.txt` | delimitado por punto y coma `;` |
  | `inventario` | `csv` | `inventario_2025.csv` | delimitado por barra vertical `|` |
  | `precios` | `xlsx` | `precios.xlsx` | Excel `.xlsx` |

  - `source_medium` codifica el **medio** (`csv` = texto delimitado; `xlsx` = Excel); el **separador** de los delimitados (`,`/`;`/`|`) y la extensión (`.csv`/`.txt`) se detectan al leer, no se declaran en el contrato. Un dataset con `source_medium="csv"` puede tener archivos `.csv` y `.txt` con distintos separadores.
- **Combinaciones omitidas (documentadas, NC-6):** `database` y `api` (fuera de alcance de la banda); combinaciones exhaustivas separador×extensión más allá de las cuatro rutas de lectura (coma, punto y coma, barra vertical, xlsx) son redundantes y no se fabrican (NC-2).
- **Dependencia nueva:** leer `.xlsx` requiere una librería (p. ej. `openpyxl`). Se marca para el GATE por introducir una dependencia de terceros al proyecto.

### DS-ING-8 — Reparto de responsabilidad entre `contract_data.json` y `map_client_data.json` (aprobado tras el GATE del plan)
- **Decisión:** las **expectativas de validación** se derivan de **ambos** artefactos con este reparto exacto:
  - **`contract_data.json` = fuente de verdad del CONJUNTO de archivos esperados** (nombres y número). La lista de archivos esperados y los conteos `summary.files_declared`/`summary.datasets_declared` se derivan de `contract_data.json` (`historical_data.datasets[]` y `historical_data.datasets[].files[].name`). Esto implica que `contract_data.json` **se parsea** en `load_inputs` (ya no basta con comprobar su existencia).
  - **`map_client_data.json` = fuente de las COLUMNAS esperadas por dataset** (las `fields[]` con `name`/`required`): las columnas esperadas y las requeridas de cada dataset salen del mapa.
  - **NO hay chequeo de coherencia mapa↔contrato:** no se verifica que ambos coincidan entre sí ni se añade un tipo de inconsistencia nuevo por divergencia. El vocabulario cerrado de inconsistencias se mantiene: `missing_file`, `unexpected_file`, `missing_column`, `unexpected_column`.
- **Razón:** el humano aprobó este reparto tras el GATE del plan. Alinea la spec con la HU-02 de `definition.md`, que ancla el "número de archivos" al contrato (`historical_data.datasets[].files[]`) y las columnas al mapa (`fields`). El contrato es el compromiso del cliente sobre *qué archivos* envía; el mapa (derivado por `onboarding`) es el esquema canónico de *qué columnas* tiene cada dataset.
- **Sustitución de decisión previa (constancia, NC-6):** este reparto **reemplaza** la decisión anterior por la cual *todas* las expectativas (archivos y columnas) se derivaban **solo** de `map_client_data.json` y `contract_data.json` se comprobaba únicamente su existencia. Ninguna otra decisión (DS-ING-1..7) se reabre: DS-ING-1 (soft-report y `FlowContractError` solo por ausencia física de `contract_data.json`/`map_client_data.json`), DS-ING-2..7 permanecen vigentes tal cual. El fixture (DS-ING-7) mantiene `contract_data.json` y `map_client_data.json` **coherentes entre sí** (misma lista de archivos y columnas), por lo que el reparto no altera el resultado esperado del caso feliz.
- **Emparejamiento dataset contrato↔mapa:** dado que ambos se mantienen coherentes (mismo orden y mismos `kind`), un archivo esperado (del contrato) se valida contra las columnas del dataset homólogo del mapa. El emparejamiento por `kind`/orden declarado es detalle de `plan_builder`; lo observable es que los archivos esperados provienen del contrato y sus columnas esperadas del mapa.

---

## Contratos de Datos / Artefactos

| Dirección | Artefacto | Ruta (vía `ClientContext`) | Formato |
|---|---|---|---|
| requiere | `contract_data` | `Artifact(base="outputs", relative="010_discovery/contract_data.json")` | JSON |
| requiere | `map_client_data` | `Artifact(base="outputs", relative="020_onboarding/map_client_data.json")` | JSON |
| requiere (no estático) | archivos crudos | `ctx.inputs_dir / "030_ingestion" / <nombre>` (nombres dinámicos del contrato; validados en el flujo) | csv/txt/xlsx |
| produce | `ingestion_report` | `Artifact(base="outputs", relative="030_ingestion/ingestion_report.json")` | JSON |
| produce (dinámico) | copias inmutables | `ctx.bronze_dir / <nombre>` (una por archivo válido; rutas en `FlowResult.outputs`) | csv/txt/xlsx (byte a byte) |
| produce (módulo) | `src/foda/flows/f030_ingestion/` | módulo Python (clase `Ingestion(Flow)`) | — |

### Entrada — `contract_data.json` (esquema consumido; **fuente de los archivos esperados**, DS-ING-8)
Fixture que simula la salida de Discovery (010). Ingestion consume, por dataset bajo `historical_data.datasets[]`: `kind`, `source_medium`, `periodicity` y `files[].name`. La lista de **archivos esperados** = la unión de `historical_data.datasets[].files[].name`; el conteo `summary.files_declared` = nº total de esos archivos y `summary.datasets_declared` = `len(historical_data.datasets)`. El **medio** de lectura de un archivo (`source_medium`) proviene del dataset del contrato al que pertenece. (El separador concreto de los delimitados y la extensión se detectan al leer, no se declaran; DS-ING-7.)

### Entrada — `map_client_data.json` (esquema consumido; **fuente de las columnas esperadas**, DS-ING-8)
Producido por `onboarding` (CONFORME). Ingestion consume, por dataset: `kind` (para emparejar con el dataset homólogo del contrato) y `fields[]` con `name`/`required`. La lista de **columnas esperadas** de un archivo = los `field.name` del dataset homólogo en el mapa; las **requeridas** = aquellos con `required == true`. Ingestion **no** deriva de aquí la lista de archivos esperados (esa sale del contrato).

### Salida — `ingestion_report.json` (esquema propuesto, DS-ING-2)
```json
{
  "schema_version": "0.1",
  "client": { "code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail" },
  "flow": "ingestion",
  "success": false,
  "summary": {
    "datasets_declared": 3,
    "files_declared": 4,
    "files_ingested": 3,
    "files_with_inconsistencies": 1
  },
  "datasets": [
    {
      "kind": "ventas",
      "source_medium": "csv",
      "files": [
        {
          "name": "ventas.csv",
          "status": "ingested",
          "rows": 12,
          "columns": 5,
          "separator": ",",
          "bronze_path": "data/bronze/ventas.csv",
          "inconsistencies": []
        }
      ]
    },
    {
      "kind": "inventario",
      "source_medium": "csv",
      "files": [
        { "name": "inventario_2024.txt", "status": "ingested", "rows": 6, "columns": 4, "separator": ";", "bronze_path": "data/bronze/inventario_2024.txt", "inconsistencies": [] },
        { "name": "inventario_2025.csv", "status": "rejected", "rows": 6, "columns": 3, "separator": "|", "bronze_path": null,
          "inconsistencies": [ { "type": "missing_column", "detail": "falta la columna requerida 'stock'" } ] }
      ]
    },
    {
      "kind": "precios",
      "source_medium": "xlsx",
      "files": [
        { "name": "precios.xlsx", "status": "ingested", "rows": 9, "columns": 3, "separator": null, "bronze_path": "data/bronze/precios.xlsx", "inconsistencies": [] }
      ]
    }
  ],
  "unexpected_files": [],
  "inconsistencies": []
}
```
- `status` ∈ {`ingested`, `rejected`, `missing`}. `rows` = filas de datos (sin cabecera); `columns` = nº de columnas de la cabecera. `separator` ∈ {`,`,`;`,`|`, `null` para xlsx}. `bronze_path` = ruta relativa al cliente si se copió, `null` si no.
- `inconsistencies[].type` ∈ vocabulario cerrado: `missing_file`, `unexpected_file`, `missing_column`, `unexpected_column`. `detail` = texto legible.
- `unexpected_files` = lista (orden alfabético) de nombres de archivos presentes en el landing no declarados por ningún dataset.
- **`inconsistencies` (top-level, DS-ING-9)** = lista que **agrega todas** las inconsistencias del run (de archivo y de columna), cada una `{type, detail}` con `type` del vocabulario cerrado de 4 y `detail` no vacío. Da hogar estructural a `unexpected_file` (archivo sobrante sin dataset propio). Las de columna quedan **además** anidadas en `datasets[].files[].inconsistencies`. Es la lista sobre la que se verifica CA-16.

---

## Comportamiento Esperado

Ejecución de `Ingestion().run(ctx)`:

1. **`load_inputs(ctx)`** — lee y **parsea** `contract_data.json` (de donde saldrán los archivos esperados) y `map_client_data.json` (de donde saldrán las columnas esperadas) —rutas de `requires`— **si existen**. No escribe en disco (DS-ING-8).
2. **`validate(ctx)`** — `super().validate(ctx)` comprueba la existencia física de **ambos** `requires`; si falta alguno → `FlowContractError` (antes de `execute`), sin salida (ni reporte ni bronze). No valida datos aquí.
3. **`execute(ctx)`** — deriva, sin usar LLM:
   - Conjunto de archivos **esperados** = `∪ historical_data.datasets[].files[].name` **del contrato** (`contract_data.json`, DS-ING-8); conjunto **presentes** = archivos en `ctx.inputs_dir / "030_ingestion"`.
   - **Chequeo de archivos (HU-02):** esperado-no-presente → `status="missing"` + inconsistencia `missing_file` (no se copia). Presente-no-esperado → entra en `unexpected_files` + inconsistencia `unexpected_file` (no se copia).
   - Por cada archivo **esperado y presente**: lo lee (detecta separador entre `,`/`;`/`|` para delimitados; primera hoja para xlsx), cuenta `rows`/`columns`, y valida columnas contra las **columnas esperadas del mapa** (`map_client_data.json`, dataset homólogo por `kind`; DS-ING-3 / DS-ING-8): requerida (`required == true`) ausente → `missing_column`; columna presente no declarada en `fields` → `unexpected_column`. Si hay ≥ 1 inconsistencia de columna → `status="rejected"` (no se copia); si no → `status="ingested"` (se copia).
   - **Sin chequeo de coherencia mapa↔contrato** (DS-ING-8): no se compara el contrato contra el mapa; cada fuente alimenta su propia dimensión de validación.
   - Arma el reporte en memoria (DS-ING-2, orden determinista DS-ING-6) y devuelve `FlowResult(success=(sin inconsistencias), outputs=[<ruta reporte>] + <rutas bronze de los ingested>)`.
4. **`write_outputs(ctx, result)`** — crea carpetas destino; copia **byte a byte** a `ctx.bronze_dir` cada archivo `ingested`; escribe `ingestion_report.json` (serialización determinista). El reporte se escribe **siempre** que se llegó a `execute` (haya o no inconsistencias).
5. **`run` devuelve** el `FlowResult` de `execute`.

**Invariantes:**
- Ingestion **no** transforma datos: bronze es copia byte a byte del original.
- Ingestion **no** escribe en `silver/`/`gold/` ni usa LLM.
- Ante `contract_data.json`/`map_client_data.json` ausente, **no** se escribe reporte ni copia alguna (falla en `validate` base).
- Un archivo inválido nunca llega a `bronze/`; los válidos del mismo lote sí (copia parcial, DS-ING-5).

---

## Casos Límite y Errores

| Caso | Contexto | Resultado esperado |
|---|---|---|
| Lote completo y válido (fixture) | 4 archivos declarados = 4 presentes, columnas correctas | los 4 copiados a bronze; reporte sin inconsistencias; `success=True`. |
| Separador coma / punto y coma / barra vertical | `ventas.csv` (`,`), `inventario_2024.txt` (`;`), `inventario_2025.csv` (`|`) | `rows`/`columns` correctos por archivo; `separator` reportado. |
| Excel `.xlsx` | `precios.xlsx` | leído (primera hoja); `rows`/`columns` correctos; `separator=null`. |
| Archivo declarado faltante | un `files[].name` no está en el landing | `status="missing"` + `missing_file`; no en bronze; `success=False`. |
| Archivo presente no declarado | un archivo extra en el landing | en `unexpected_files` + `unexpected_file`; no en bronze; `success=False`. |
| Columna requerida ausente | archivo sin una columna `required=true` | `status="rejected"` + `missing_column`; no en bronze; `success=False`. |
| Columna no declarada presente (renombrada) | archivo con columna fuera de `fields` | `status="rejected"` + `unexpected_column`; no en bronze; `success=False`. |
| Columna opcional ausente | falta `precio_unitario` (`required=false`) | **no** es inconsistencia; archivo `ingested` si el resto valida. |
| Inconsistencia parcial | 3 archivos válidos, 1 inválido | 3 copiados a bronze, 1 no; reporte refleja ambos; `success=False`. |
| Landing vacío / inexistente | ningún archivo presente | todos los declarados `missing`; reporte escrito; bronze vacío; `success=False`. |
| Copia fiel | archivo delimitado por `|` | copia en bronze byte-idéntica, sigue delimitada por `|`. |
| `contract_data.json` ausente | falta el require | `FlowContractError` en `validate` base; sin reporte ni bronze. |
| `map_client_data.json` ausente | falta el require | `FlowContractError` en `validate` base; sin reporte ni bronze. |
| Reproducibilidad | dos `run(ctx)` con las mismas entradas | reporte y copias byte-idénticos. |

---

## Interfaces / Firmas Públicas

```python
# src/foda/flows/f030_ingestion/ingestion.py  (nombre de módulo a fijar por plan_builder)
from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowContractError, FlowResult


class Ingestion(Flow):
    """Flujo 030: carga y valida datos crudos, copia inmutable a bronze y emite reporte de carga."""

    name = "ingestion"
    requires = [
        Artifact(name="contract_data",   base="outputs", relative="010_discovery/contract_data.json"),
        Artifact(name="map_client_data", base="outputs", relative="020_onboarding/map_client_data.json"),
    ]
    produces = [
        Artifact(name="ingestion_report", base="outputs", relative="030_ingestion/ingestion_report.json"),
    ]

    def load_inputs(self, ctx: ClientContext) -> None: ...
    def validate(self, ctx: ClientContext) -> None: ...      # solo super().validate(): existencia de requires
    def execute(self, ctx: ClientContext) -> FlowResult: ...  # lee, valida datos (soft), arma reporte + plan de copia
    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None: ...  # copia a bronze + escribe reporte
```
- **No** sobreescribe `run()`: usa el template method heredado de `Flow`.
- **Contrato de errores:** `FlowContractError` **solo** para require de contrato ausente (base). Inconsistencias de datos → reporte (DS-ING-1), nunca excepción.
- Los archivos crudos **no** figuran en `requires` (nombres dinámicos): se validan en `execute` y se reportan como inconsistencias.
- Nombres exactos de módulo/helpers y la librería de lectura xlsx son detalle de `plan_builder`; lo observable es `Ingestion(Flow)` con esos `requires`/`produces`, la copia a bronze y el reporte.

---

## Criterios de Aceptación (verificables)
> Cada criterio es traducible a uno o más tests (usando el fixture acordado y/o variantes, un `ClientContext` bajo `tmp_path`, `pytest.raises(FlowContractError)` para los errores duros y aserciones sobre `ingestion_report.json` / contenido de `bronze/`) y traza a la(s) `HU-xx` que satisface. Cumple D-031 (trazabilidad codificada HU→CA).

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | Dado el fixture, tras `run(ctx)` el reporte registra para el archivo delimitado por **coma** (`ventas.csv`) el nº correcto de `rows` (filas de datos, sin cabecera) y `columns`, y `separator == ","`. | HU-01 |
| CA-02 | El reporte registra `rows`/`columns` correctos y `separator == ";"` para el archivo `.txt` delimitado por **punto y coma** (`inventario_2024.txt`). | HU-01 |
| CA-03 | El reporte registra `rows`/`columns` correctos y `separator == "|"` para el archivo delimitado por **barra vertical** (`inventario_2025.csv`). | HU-01 |
| CA-04 | El reporte registra `rows`/`columns` correctos y `separator == null` para el archivo **`.xlsx`** (`precios.xlsx`), leído de su primera hoja. | HU-01 |
| CA-05 | Dado un lote cuyos archivos presentes coinciden exactamente con los **declarados en `contract_data.json`** (`historical_data.datasets[].files[].name`), el reporte no registra inconsistencias `missing_file`/`unexpected_file`, `unexpected_files == []`, y `summary.files_ingested == summary.files_declared`. | HU-02 |
| CA-06 | Si un archivo **declarado en `contract_data.json`** (`historical_data.datasets[].files[].name`) no está en el landing, su entrada tiene `status == "missing"` con inconsistencia `missing_file`; no existe copia suya en `ctx.bronze_dir`; `FlowResult.success == False`. | HU-02 |
| CA-07 | Si hay un archivo presente en el landing **no declarado en `contract_data.json`** (no figura en ningún `historical_data.datasets[].files[].name`), aparece en `unexpected_files` con inconsistencia `unexpected_file`, no se copia a `ctx.bronze_dir`, y `success == False`. | HU-02 |
| CA-08 | Si un archivo presente carece de una columna con `required == true` **según `map_client_data.json`** (dataset homólogo por `kind`), su entrada tiene `status == "rejected"` con inconsistencia `missing_column`; no se copia a `ctx.bronze_dir`; `success == False`. | HU-03 |
| CA-09 | Si un archivo presente tiene una columna **no declarada en los `fields` del dataset homólogo de `map_client_data.json`** (p. ej. columna renombrada), su entrada tiene `status == "rejected"` con inconsistencia `unexpected_column`; no se copia a `ctx.bronze_dir`; `success == False`. | HU-03 |
| CA-10 | Si a un archivo válido le falta una columna con `required == false` **según `map_client_data.json`** (p. ej. `precio_unitario`), **no** se registra inconsistencia por ello y el archivo se marca `ingested`. | HU-03 |
| CA-11 | Para cada archivo válido (declarado, presente, columnas correctas), existe en `ctx.bronze_dir / <nombre>` una copia **byte a byte idéntica** al archivo de origen del landing. | HU-04 |
| CA-12 | La copia en bronze conserva formato/separador/extensión sin transformación: el archivo `|` sigue delimitado por `|` y el `.xlsx` se copia como `.xlsx` idéntico. | HU-04 |
| CA-13 | Dos ejecuciones de `run(ctx)` con las mismas entradas producen copias en bronze byte-idénticas y un `ingestion_report.json` byte-idéntico (determinismo). | HU-04, HU-01 |
| CA-14 | `run(ctx)` escribe `ingestion_report.json` en `ctx.outputs_dir / "030_ingestion/ingestion_report.json"` y lo incluye en `FlowResult.outputs`. | HU-05 |
| CA-15 | El reporte expone, por archivo, `name`, `rows` y `columns`. | HU-05 |
| CA-16 | Las inconsistencias de la lista top-level `inconsistencies[]` del reporte (DS-ING-9) tienen cada una un `type` del vocabulario cerrado (`missing_file`, `unexpected_file`, `missing_column`, `unexpected_column`) y un `detail` legible no vacío. | HU-05 |
| CA-17 | `summary` reporta `datasets_declared` (= `len(historical_data.datasets)` del contrato), `files_declared` (= nº de `historical_data.datasets[].files[].name` del contrato, DS-ING-8), `files_ingested` y `files_with_inconsistencies`, con conteos coherentes con el detalle por archivo. | HU-05 |
| CA-18 | Ante inconsistencia parcial (unos archivos válidos, otros no), los válidos se copian a `ctx.bronze_dir` y los inválidos no; el reporte refleja ambos estados; `success == False`. | HU-02, HU-03, HU-04 |
| CA-19 | `FlowResult.success == True` si y solo si el reporte no registra ninguna inconsistencia; en caso contrario es `False`, y el reporte se escribe igualmente. | HU-05 |
| CA-20 | `Ingestion` hereda de `Flow`, declara `requires=[contract_data, map_client_data]` y `produces=[ingestion_report]` como `Artifact(base="outputs", ...)`, y completa las 4 fases del template method sin sobreescribir `run`. | HU-06 |
| CA-21 | Si falta `contract_data.json` **o** `map_client_data.json` en disco, `run(ctx)` lanza `FlowContractError` en `validate` (base) antes de tocar bronze; no se escribe `ingestion_report.json` ni copia alguna. | HU-06, HU-05 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` queda cubierta por ≥ 1 `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02, CA-03, CA-04, CA-13 |
| HU-02 | CA-05, CA-06, CA-07, CA-18 |
| HU-03 | CA-08, CA-09, CA-10, CA-18 |
| HU-04 | CA-11, CA-12, CA-13, CA-18 |
| HU-05 | CA-14, CA-15, CA-16, CA-17, CA-19, CA-21 |
| HU-06 | CA-20, CA-21 |

---

## No-Objetivos
- **Comparación contra `client_register` (Discovery 010):** DIFERIDA — ese artefacto aún no existe; se revisará en `stab_1` (definition.md, feature_contract).
- **Medios `database` y `api`:** el vocabulario `source_medium` los admite, pero no se implementa su lectura en esta banda.
- **Validación de tipos de dato** de columnas (solo presencia/nombre en esta banda; tipos → `stab_1`, DS-ING-3).
- **Profiling (040):** salud de los datos (faltantes, duplicados, periodicidad, pareto) NO es de Ingestion.
- **Cleaning (050):** limpieza/transformación; bronze es copia fiel e inalterable.
- **Descargables (export csv/xlsx)** del reporte de carga.
- **Uso de LLM** (Ingestion es determinista, §6).
- **`kind` no ejercitados por el fixture** (`ordenes_compra`, `devoluciones`, `promociones`) y combinaciones separador×extensión redundantes (DS-ING-7).
- **Ampliación de `ClientContext`/`Artifact`** (no se toca el core; DS-ING-4).
- **Discovery (010) real:** `contract_data.json` es un fixture fabricado.

---

## Puntos de confirmación para el GATE humano
Decisiones tomadas por `spec_writer` (delegadas por `definition.md`) que el humano valida o ajusta antes de `plan_builder`:
1. **DS-ING-1 — mecanismo ante inconsistencias:** ¿se acepta que las inconsistencias de **datos** se acumulen en el reporte sin abortar (soft-report) y que `FlowContractError` quede reservado solo a `contract_data.json`/`map_client_data.json` ausentes, con `FlowResult.success=False` si hay inconsistencias?
2. **DS-ING-2 — esquema del reporte (`ingestion_report.json`):** ¿se acepta la forma propuesta (`client`, `summary`, `datasets[].files[]` con `status`/`rows`/`columns`/`separator`/`bronze_path`/`inconsistencies`, `unexpected_files`, `success`)?
3. **DS-ING-3 — validación de columnas:** ¿se confirma que en esta banda es solo por **nombre/presencia** (requeridas presentes, sin columnas desconocidas), sin validar tipos de dato?
4. **DS-ING-4 — landing de archivos crudos:** ¿se acepta depositarlos en `010_inputs/030_ingestion/` reutilizando `base="inputs"` (sin ampliar el core), aun siendo datos crudos y no YAML humano?
5. **DS-ING-5 — inconsistencia parcial:** ¿se acepta copia parcial (unidad = archivo: solo se copian los declarados+presentes+válidos) en vez de abortar todo?
6. **DS-ING-6 — fidelidad y determinismo:** ¿se acepta copia byte a byte a bronze (sin re-serializar) y reporte determinista (orden estable + `sort_keys` + `indent=2` + newline)?
7. **DS-ING-7 (fixture):** ¿se acepta la composición propuesta (ventas/coma, inventario/`;`+`|`, precios/xlsx; `.txt` incluido; ≥2 kind ≠ ventas) y las combinaciones omitidas (`database`/`api`, separador×extensión redundantes)?
8. **DS-ING-7 (dependencia):** ¿se autoriza introducir una librería de lectura `.xlsx` (p. ej. `openpyxl`) como dependencia del proyecto?
9. **client_register DIFERIDO** (constancia, no requiere decisión): la comparación contra `client_register` queda fuera de esta banda.
10. **DS-ING-8 — reparto de responsabilidad `contract_data.json`↔`map_client_data.json` (YA APROBADO por el humano tras el GATE del plan):** los archivos esperados y `summary.files_declared`/`datasets_declared` se derivan de `contract_data.json` (`historical_data.datasets[].files[].name`, `datasets[]`), y las columnas esperadas/requeridas de `map_client_data.json` (`fields[]`); **sin** chequeo de coherencia mapa↔contrato. Este reparto **reemplaza** la decisión previa "solo mapa". Al integrarse este cambio, la spec debe re-planificarse (`plan_builder` vuelve a ejecutarse).
