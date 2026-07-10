# Spec — profiling (banda `stab_2`)

> Artefacto de la etapa 2 (`spec_writer`). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables **codificados (`CA-xx`) y enlazados a las historias de usuario (`HU-xx`)** de `definition.md`. **Requiere aprobación humana** (gate) antes de planear.
>
> Banda: `stab_2` ("defectos con score"). Fuentes canónicas: `600_features/profiling/stab_2/definition.md`, `600_features/profiling/stab_1/spec.md` (reporte v0.2 que aquí se enriquece y rediseña), `600_features/ingestion/tracer_bullet/spec.md` (esquema de `ingestion_report.json`, única fuente del bloque estructural y de las rutas a `bronze/`), `700_architecture/system_design.md` (§6 determinismo, §7 estructura de carpetas, §8 contrato de artefactos, §10 medallion, §15 detalle 040 Profiling), `800_persistence/decisions.md` (`D-097`, `D-098`, `D-099`, `D-100`, `D-080`). Código vigente (CONFORME `stab_1`): `src/foda/flows/f040_profiling/profiling.py` (clase `Profiling`), `src/foda/core/flow.py`, `src/foda/core/context.py`.

## Resumen
Endurece el flujo **040 Profiling** para que, además de la salud **estructural** heredada de `stab_1`, haga su **primera lectura determinista del contenido de `bronze/`** (con `pandas`, sin LLM, sin modificar los datos) y mida tres defectos inequívocos a nivel de celda/fila —**nulos** (completitud), **valores centinela** (validez, catálogo por cliente en `profiling_config.yaml`) y **filas duplicadas** (unicidad)—, recomponiendo `global_score` como **media ponderada** de cuatro sub-scores normalizados a `[0,1]` (`structural_score`, `completeness_score`, `validity_score`, `uniqueness_score`), y persistiendo todo en `profiling_report.json` enriquecido (bloque `health` = tablero de scores + bloque hermano `defects` = evidencia), subiendo `schema_version` de `"0.2"` a `"0.3"` de forma determinista byte a byte.

---

## Decisiones humanas ya resueltas (NO se reabren)

Estas resuelven supuestos abiertos que `feature_definer` dejó en `definition.md` (§Riesgos y Supuestos) y ya fueron decididas por el humano:

- **A-020 RESUELTA → SÍ se usa `pandas`** para leer `bronze/` y contar nulos, filas duplicadas y valores centinela. No es una dependencia nueva: `Ingestion` (CONFORME) ya usa `pandas` (`read_csv`/`read_excel`).
- **A-021 RESUELTA → pesos por defecto 25 % cada sub-score (`0.25` × 4), SOBREESCRIBIBLES por cliente** en `profiling_config.yaml` (archivo **vendor-owned**, no editable por el cliente; ver ENMIENDA `DS-PRF2-6`). La spec fija tanto los defaults como el mecanismo de override (`DS-PRF2-1`, `DS-PRF2-6`).

## Decisiones de detalle propuestas para el GATE humano

Las 4 ambigüedades que `definition.md` delegó explícitamente a `spec_writer` (NC-6). Se **proponen** aquí con su razonamiento; el humano las ratifica o ajusta antes de `plan_builder`. Se listan al final en *Puntos de confirmación para el GATE humano*.

1. **`DS-PRF2-1`** — fórmula exacta de `global_score` y normalización de cada sub-score.
2. **`DS-PRF2-5`** — forma exacta de los bloques del reporte (`health` scoreboard + `defects` hermano).
3. **`DS-PRF2-5`** — nuevo `schema_version = "0.3"`.
4. **`DS-PRF2-6`** — formato y ubicación de `profiling_config.yaml`.

---

## DS-PRF2-1 — `global_score` = media ponderada de 4 sub-scores (`D-099`, A-021)

- **Sub-scores** (cada uno `float` en `[0.0, 1.0]`, redondeado a **4 decimales** con `round(x, 4)`):

  | sub-score | fórmula | denominador natural |
  |---|---|---|
  | `structural_score` | idéntico al `global_score` de `stab_1` (`max(0.0, 1.0 − Σ peso[t]×problems_by_type[t] / files_declared)`, pesos `{missing_file:1.0, missing_column:0.5, unexpected_file:0.3, unexpected_column:0.1}`, borde `files_declared==0 ⇒ 1.0`) | archivos declarados |
  | `completeness_score` | `1.0 − null_cells / total_cells` | celdas |
  | `validity_score` | `1.0 − sentinel_cells / total_cells` | celdas |
  | `uniqueness_score` | `1.0 − duplicate_rows / total_rows` | filas |

- **Fórmula del global:** `global_score = round( w_struct·structural_score + w_compl·completeness_score + w_valid·validity_score + w_uniq·uniqueness_score, 4 )`.
- **Pesos:** por defecto `0.25` cada uno (A-021). Sobreescribibles por cliente en el `profiling_config.yaml` **vendor-owned** (`DS-PRF2-6`; no editable por el cliente, integridad del score facturable). **Regla de validación:** si el cliente declara `weights`, debe declarar los 4, cada uno `≥ 0`, y su suma debe ser `1.0` (± `1e-9`); en caso contrario `Profiling` lanza `FlowContractError` nombrando el problema. Si no declara `weights`, se usan los 4 defaults. Los pesos efectivamente usados se **publican** en `health.weights` (auditable).
- **Rango:** cada sub-score y el `global_score` quedan en `[0.0, 1.0]` (media convexa de valores en `[0,1]` con pesos que suman 1). Redondeo a 4 decimales por la misma razón de determinismo byte a byte que en `stab_1` (§6).
- **Bordes de denominador cero (defecto seguro, sin falsos positivos):**
  - `total_cells == 0` (no hay archivos ingeridos, o todos con 0 celdas) ⇒ `completeness_score = 1.0` y `validity_score = 1.0`.
  - `total_rows == 0` ⇒ `uniqueness_score = 1.0`.
  - `files_declared == 0` ⇒ `structural_score = 1.0` (borde heredado de `stab_1`).
- **Principio `D-098`:** solo estos 4 defectos inequívocos alimentan `global_score`. El perfil diagnóstico por columna (outliers, dominancia categórica) es `stab_3` y **no** entra aquí.

**Ejemplo de anclaje.** `structural_score=0.875`, `completeness_score=0.98`, `validity_score=0.95`, `uniqueness_score=0.90`, pesos default `0.25`: `global_score = round(0.25·(0.875+0.98+0.95+0.90), 4) = round(0.25·3.705, 4) = round(0.92625, 4) = 0.9263`.

## DS-PRF2-2 — Lectura de `bronze/` (primera vez, solo lectura, con `pandas`, A-020)

- **Universo de lectura:** solo los archivos **ingeridos**, es decir las entradas de `ingestion_report.datasets[].files[]` con `status == "ingested"` y `bronze_path` no nulo. Su ruta física es `ctx.root / bronze_path` (p. ej. `data/bronze/ventas.csv`). Los archivos `missing`/`rejected` y los `unexpected_file` **no** tienen contenido que auditar: no aportan celdas ni filas; su impacto ya lo captura `structural_score` (separación de dimensiones, `D-099`).
- **Modo de lectura determinista:** `.csv`/`.txt` con `pandas.read_csv` usando el `separator` de la propia entrada del archivo; `.xlsx` con `pandas.read_excel` (primera hoja). En ambos casos se leen los valores **como texto, sin conversión automática de nulos/tokens** (equivalente a `dtype=str`, `keep_default_na=False`, `na_values=[]`), de modo que un token como `"N/A"` o `"NA"` **no** se convierta silenciosamente en `NaN` (si lo hiciera, se contaría como nulo en vez de como centinela). La fila de encabezado es cabecera, no dato.
- **`bronze/` es inalterable** (§10, Estrella Polar de Profiling): Profiling **solo lee**; nunca escribe ni modifica `bronze/`.
- **Determinismo:** misma copia bronze ⇒ mismos conteos ⇒ mismo reporte byte a byte (§6).

## DS-PRF2-3 — Conteos de defectos de contenido (deterministas, por celda/fila)

Sea `F` el conjunto de archivos ingeridos (`DS-PRF2-2`). Para cada archivo `f ∈ F`, tras leerlo como DataFrame `df_f`:

- **Celdas.** `cells(f) = rows(f) × columns(f)` (dimensiones del `df_f` leído). `total_cells = Σ_{f∈F} cells(f)`.
- **Celda nula (completitud).** Una celda es **nula** si es `NaN`/faltante **o** su valor textual, tras recortar espacios (`strip`), es la cadena vacía `""`. Esta definición cubre tanto csv (campo vacío ⇒ `""`) como xlsx (celda vacía ⇒ `NaN`). `null_cells = Σ_{f∈F}` nº de celdas nulas de `df_f`.
- **Celda centinela (validez).** Una celda es **centinela** si **no es nula** y su valor textual **literal** (como se leyó, sin recorte, comparación **exacta y sensible a mayúsculas**) es igual a **algún token del catálogo** (`DS-PRF2-4`). Nulos y centinelas son **mutuamente excluyentes** (una celda vacía nunca es centinela). `sentinel_cells = Σ_{f∈F}` nº de celdas centinela de `df_f`.
- **Fila duplicada (unicidad).** Duplicado = fila **idéntica a una fila anterior dentro del mismo archivo** (semántica `DataFrame.duplicated()` de `pandas`, `keep="first"`, comparando la fila completa con los valores leídos en modo texto). No se comparan filas entre archivos distintos (datasets distintos no son duplicados entre sí). `duplicate_rows = Σ_{f∈F}` nº de filas duplicadas de `df_f`. `total_rows = Σ_{f∈F} rows(f)`.
- **Determinismo del detalle por archivo (`by_file`):** las listas `by_file` se ordenan en el **orden de aparición** de los archivos en `ingestion_report.datasets[].files[]` (orden declarado, ya determinista en `ingestion`), filtrando a los ingeridos. `sort_keys=True` ordena las claves de cada objeto, pero **no** reordena listas: por eso el orden de `by_file` se fija aquí explícitamente.

## DS-PRF2-4 — Catálogo de valores centinela (`profiling_config.yaml`, `D-100`)

- El catálogo vive en el nuevo artefacto por cliente `profiling_config.yaml` (`DS-PRF2-6`), bajo la clave `sentinels`, con **tres cajas**: `numeric`, `non_numeric` (incluye fechas límite tipo `1900-01-01`/`9999-12-31`) y `boolean`.
- **Construcción del catálogo (esta banda):** los tokens de las tres cajas se **unifican** en un único conjunto de tokens comparables. Cada token se compara como **cadena** (`str(token)`; p. ej. el entero YAML `-999` ⇒ `"-999"`). La detección es por **coincidencia exacta de token** (`DS-PRF2-3`), sin normalización numérica ni inferencia semántica (Profiling es determinista, sin LLM, §6). La aplicación de cada caja **por tipo de columna** se difiere a `stab_3` (perfil por columna); en `stab_2` las tres cajas se tratan como un catálogo plano de tokens. **Consecuencia conocida (riesgo aceptado, `definition.md`):** variantes no catalogadas (p. ej. `"-999.0"` frente al token `-999`) **no** se detectan como centinela en esta banda.
- **Comportamiento seguro por defecto:** si `profiling_config.yaml` **no existe**, o existe pero no declara `sentinels` (o las cajas están vacías), el catálogo es **vacío** ⇒ `sentinel_cells = 0` y `validity_score = 1.0`, sin falsos positivos, y Profiling **no falla**.

## DS-PRF2-5 — Enriquecimiento del reporte: `health` (scoreboard) + `defects` (evidencia) + bump a `"0.3"`

- **`schema_version` sube de `"0.2"` a `"0.3"`** (bump aditivo/estructural: hay bloques nuevos y el bloque `health` se rediseña; los campos de identidad `client`/`flow`/`success` se conservan sin cambio de tipo).
- **`health` = tablero de scores** (solo los números de cabecera): `global_score`, `weights` (los 4 pesos efectivos) y los 4 sub-scores `structural_score`, `completeness_score`, `validity_score`, `uniqueness_score`.
- **`defects` = evidencia por dimensión** (bloque hermano de `health`), con **exactamente** 4 sub-bloques:
  - `structural`: el detalle estructural heredado de `stab_1` (`files_declared`, `files_healthy`, `files_with_problems`, `problems_by_type`, `pareto`), **con los mismos valores y semántica que `stab_1`**, **reubicado** desde `health` hacia `defects.structural`.
  - `completeness`: `total_cells`, `null_cells`, `by_file[]` (`{name, rows, columns, cells, null_cells}`).
  - `validity`: `total_cells`, `sentinel_cells`, `catalog_size` (nº de tokens del catálogo unificado), `by_file[]` (`{name, sentinel_cells}`).
  - `uniqueness`: `total_rows`, `duplicate_rows`, `by_file[]` (`{name, rows, duplicate_rows}`).
- **Mapeo de compatibilidad con `stab_1` (riesgo documentado, `definition.md`):**
  - `health.global_score` de `stab_1` (score estructural único) → ahora es `health.structural_score` (mismo cálculo y valor). El nuevo `health.global_score` es la **media ponderada** de los 4 sub-scores.
  - `health.{files_declared, files_healthy, files_with_problems, problems_by_type, pareto}` de `stab_1` → ahora `defects.structural.{…}` (mismos valores, reubicados). Un consumidor de `stab_1` debe re-leer estas rutas; el bump de `schema_version` a `"0.3"` lo señaliza.
- **Serialización determinista (§6):** `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)` + salto de línea final, idéntica a `stab_1`/`Ingestion`. `sort_keys` no reordena listas ⇒ el orden de `pareto` (`DS-PRF-5` de `stab_1`) y de los `by_file` (`DS-PRF2-3`) es el fijado explícitamente.

## DS-PRF2-6 — Artefacto de configuración **vendor-owned** por cliente `profiling_config.yaml` (`D-100`, A-021, ENMIENDA de negocio)

- **Autoría = VENDOR (decisión humana, integridad del score facturable).** El `global_score` de esta banda es el **input de una tarifa contractual** (SaaS + sobrecargo por científico de datos): a menor score, mayor cobro por corregir inconsistencias. Por tanto el catálogo de centinelas y los `weights` que determinan el score son **propiedad del vendor (Triple S)** y **no** deben ser editables por el cliente al que se le factura (conflicto de interés directo: el cliente podría inflar su score bajando pesos o vaciando el catálogo). El archivo se ubica **FUERA del espacio editable del cliente** (`clients/<name>/`), no en `010_inputs/`.
- **Ubicación:** `900_vendor/profiling/<name>/profiling_config.yaml`, un área **vendor-owned** a nivel de proyecto, **por cliente** (los centinelas/pesos pueden variar por cliente), **fuera de `clients/`**. Justificación: (a) queda fuera de `clients/<name>/` ⇒ el cliente no lo edita aunque tenga acceso a su propia carpeta; (b) la numeración `9xx` es coherente con las áreas de gobernanza/meta del vendor ya existentes (`980_guideline`, `990_documents`); (c) el subárbol `profiling/<name>/` mantiene el aislamiento multi-tenant y la convención de prefijo de flujo. El archivo lo crea/gestiona el vendor, no el cliente.
- **Resolución de ruta (impacto en el core, para `plan_builder`):** este artefacto **no** se resuelve por las bases de `ClientContext` (`inputs`/`outputs`/`bronze`/… todas bajo `clients/<name>/`), porque vive fuera de `clients/`. La ruta se deriva del **vendor/project root** más `profiling/<name>/profiling_config.yaml` (con `<name> = ctx.name`). El mecanismo exacto (p. ej. un helper `vendor_config_dir` o un parámetro de resolución) es detalle de `plan_builder`; la spec fija el **contrato observable**: ubicación vendor-owned fuera de `clients/`, por cliente, opcional. Este es un cambio respecto a la versión previa de la spec (que reutilizaba `Artifact(base="inputs")`), y por eso puede requerir un toque mínimo del core (NC-6, marcado para el GATE y para `plan_builder`).
- **Es OPCIONAL:** **no** se declara en `requires` del flujo (si estuviera, `validate` base fallaría al faltar). `Profiling` comprueba su existencia manualmente en `load_inputs`; si falta, usa catálogo vacío y pesos default (`DS-PRF2-4`, `DS-PRF2-1`), sin fallar.
- **Formato (YAML):**
  ```yaml
  # 900_vendor/profiling/<name>/profiling_config.yaml  (VENDOR-OWNED; el cliente no lo edita)
  # Todo el archivo es opcional; cada bloque es opcional.
  sentinels:                 # catálogo de valores centinela (D-100). Ausente ⇒ vacío.
    numeric: [-999, -9999, 9999]
    non_numeric: ["N/A", "n/a", "desconocido", "1900-01-01", "9999-12-31"]
    boolean: ["unknown"]
  weights:                   # pesos del global_score (A-021). Ausente ⇒ 0.25 c/u.
    structural: 0.25
    completeness: 0.25
    validity: 0.25
    uniqueness: 0.25
  ```
- **Validación:** si `weights` está presente debe cumplir la regla de `DS-PRF2-1` (4 claves, `≥ 0`, suma `1.0 ± 1e-9`), so pena de `FlowContractError`. `sentinels` y sus tres cajas son opcionales; una caja ausente equivale a lista vacía. Claves desconocidas se ignoran (tolerancia hacia adelante).

## DS-PRF2-7 — Riesgos con impacto en FACTURACIÓN (reconocidos, NO resueltos aquí; a endurecer en `stab_3`) (NC-6)

Ahora que `global_score` es el input de una tarifa contractual, dos limitaciones **aceptadas** en `stab_2` dejan de ser meramente técnicas y adquieren **impacto económico**. Se reconocen aquí explícitamente (NC-6) y se marcan para endurecer en `stab_3`; **no** se resuelven en esta banda (mantener alcance, NC-2/NC-3):

- **R-BILL-1 — Centinela sin normalización numérica (`-999` vs `-999.0`, `DS-PRF2-4`).** La coincidencia exacta de token no captura variantes numéricas equivalentes. Consecuencia de facturación: centinelas no detectados ⇒ `validity_score` **inflado** ⇒ **subfacturación** (o el efecto inverso si el catálogo no coincide con el formato real del dato). A endurecer en `stab_3` (normalización por tipo de columna).
- **R-BILL-2 — Borde denominador cero ⇒ sub-score `1.0` (`DS-PRF2-1`).** Un archivo vacío o solo-encabezado (0 celdas / 0 filas) puntúa **perfecto** en completitud/validez/unicidad. Consecuencia de facturación: posible **vector de gaming** (entregar datasets mínimos para obtener score alto y pagar tarifa base). A revisar en `stab_3` (p. ej. score neutro condicionado a volumen mínimo, o penalización de datasets triviales).

**Mitigación ya presente en `stab_2`:** el catálogo y los pesos son **vendor-owned** (`DS-PRF2-6`), lo que evita que el cliente manipule directamente los parámetros del score; y el reporte es **auditable y determinista** (pesos efectivos publicados en `health.weights`, evidencia por dimensión en `defects`, reproducibilidad byte a byte). R-BILL-1/2 son vectores **residuales** de nivel de dato (no de configuración) y por eso se difieren a `stab_3`.

---

## Contratos de Datos / Artefactos

| Dirección | Artefacto | Ruta (vía `ClientContext`) | Formato | Notas |
|---|---|---|---|---|
| requiere | `ingestion_report` | `Artifact(base="outputs", relative="030_ingestion/ingestion_report.json")` | JSON | Fuente del bloque estructural y de las rutas `bronze_path` a los archivos ingeridos. Producido por `Ingestion` (CONFORME). |
| requiere (contenido) | archivos ingeridos en `bronze/` | `ctx.root / <bronze_path>` por cada archivo `status=="ingested"` | csv/xlsx | Leídos por primera vez a nivel de contenido, **solo lectura** (§10). No van en `requires` de `validate` (se referencian desde `ingestion_report`). |
| requiere (opcional) | `profiling_config` (**vendor-owned**) | `900_vendor/profiling/<name>/profiling_config.yaml` (fuera de `clients/`; resolución vía vendor/project root, no por bases de `ClientContext`) | YAML | Catálogo de centinelas + pesos, **propiedad del vendor**, no editable por el cliente (integridad del score facturable). Opcional: si falta, catálogo vacío y pesos default (`DS-PRF2-6`). **No** en `requires` de `validate`. |
| produce | `profiling_report` | `Artifact(base="outputs", relative="040_profiling/profiling_report.json")` | JSON | Enriquecido a `schema_version "0.3"`: `health` (scoreboard) + `defects` (evidencia). |

### Entrada — `ingestion_report.json` (campos consumidos)
- `summary.files_declared` (int) → `structural_score` y `defects.structural.files_declared`.
- `datasets[].files[]` con `status`, `inconsistencies`, y para los `status=="ingested"`: `bronze_path` (str, relativo a `ctx.root`), `separator` (str, para csv) → universo de lectura de `bronze/` (`DS-PRF2-2`) y detalle estructural (`DS-PRF-3` de `stab_1`).
- `inconsistencies[]` (top-level, `{type, detail}`) → `defects.structural.problems_by_type` y `pareto`.

**Supuesto de contrato (frontera de alcance, NC-2):** como en `stab_1`, Profiling asume que `ingestion_report.json` cumple el contrato de `ingestion` (flujo CONFORME y determinista) y que los `bronze_path` de los archivos `ingested` existen físicamente en disco. El manejo defensivo de un `ingestion_report.json` corrupto o de una copia bronze ausente pese a estar declarada como `ingested` queda **fuera de alcance** de esta banda; solo la ausencia física del `ingestion_report.json` está cubierta por `validate` base (`CA-24`).

### Salida — `profiling_report.json` v0.3 (esquema propuesto, `DS-PRF2-5`)
```json
{
  "schema_version": "0.3",
  "client": "acme",
  "flow": "profiling",
  "success": true,
  "health": {
    "global_score": 0.9263,
    "weights": {
      "structural": 0.25,
      "completeness": 0.25,
      "validity": 0.25,
      "uniqueness": 0.25
    },
    "structural_score": 0.875,
    "completeness_score": 0.98,
    "validity_score": 0.95,
    "uniqueness_score": 0.9
  },
  "defects": {
    "structural": {
      "files_declared": 4,
      "files_healthy": 3,
      "files_with_problems": 1,
      "problems_by_type": {
        "missing_file": 0,
        "unexpected_file": 0,
        "missing_column": 1,
        "unexpected_column": 0
      },
      "pareto": [
        { "type": "missing_column", "count": 1, "pct": 1.0 }
      ]
    },
    "completeness": {
      "total_cells": 500,
      "null_cells": 10,
      "by_file": [
        { "name": "ventas.csv", "rows": 100, "columns": 5, "cells": 500, "null_cells": 10 }
      ]
    },
    "validity": {
      "total_cells": 500,
      "sentinel_cells": 25,
      "catalog_size": 5,
      "by_file": [
        { "name": "ventas.csv", "sentinel_cells": 25 }
      ]
    },
    "uniqueness": {
      "total_rows": 100,
      "duplicate_rows": 10,
      "by_file": [
        { "name": "ventas.csv", "rows": 100, "duplicate_rows": 10 }
      ]
    }
  }
}
```

---

## Comportamiento Esperado

Ejecución de `Profiling().run(ctx)` (template method heredado de `Flow`: `load_inputs → validate → execute → write_outputs`, **sin** sobreescribir `run`):

1. **`load_inputs(ctx)`.** Parsea `ingestion_report.json`. Si existe `profiling_config.yaml`, lo parsea (catálogo de centinelas + pesos); si no existe, deja catálogo vacío y pesos default. No lee `bronze/` aquí necesariamente (reparto fino a `plan_builder`).
2. **`validate(ctx)`.** `validate` base comprueba la existencia física del único `requires` (`ingestion_report.json`); si falta ⇒ `FlowContractError` nombrándolo, **antes** de `execute`/`write_outputs`; no se escribe `profiling_report.json` (`CA-24`). Si `weights` viola la regla de `DS-PRF2-1` ⇒ `FlowContractError`.
3. **`execute(ctx)` — cálculo determinista (sin LLM):**
   1. **Estructural (heredado `stab_1`):** `files_declared`, `files_healthy`, `files_with_problems`, `problems_by_type`, `pareto`, `structural_score` (misma lógica y valores que `stab_1`).
   2. **Lectura de `bronze/`:** para cada archivo `status=="ingested"`, lee su copia bronze con `pandas` en modo texto sin auto-NA (`DS-PRF2-2`).
   3. **Completitud:** `total_cells`, `null_cells`, `by_file`; `completeness_score` (`DS-PRF2-1`/`DS-PRF2-3`).
   4. **Validez:** `sentinel_cells`, `catalog_size`, `by_file`; `validity_score`. Catálogo vacío ⇒ `sentinel_cells=0`, `validity_score=1.0` (`DS-PRF2-4`).
   5. **Unicidad:** `total_rows`, `duplicate_rows`, `by_file`; `uniqueness_score`.
   6. **`global_score`:** media ponderada de los 4 sub-scores con los pesos efectivos, redondeada a 4 decimales (`DS-PRF2-1`).
   7. Arma el reporte v0.3 en memoria: identidad conservada (`schema_version:"0.3"`, `client`, `flow`, `success`) + `health` + `defects`. `success` refleja la ejecución del flujo (True en el camino normal), **independiente** del `success` de `ingestion` (`CA-25`).
   8. Devuelve `FlowResult(success=True, outputs=[<ruta profiling_report.json>])`.
4. **`write_outputs(ctx, result)`.** Crea la carpeta destino y escribe `profiling_report.json` con serialización determinista (`ensure_ascii=False, indent=2, sort_keys=True` + newline final).

**Invariantes:**
- Profiling **solo lee** `bronze/`; nunca lo modifica.
- Cada sub-score y `global_score` ∈ `[0.0, 1.0]`, redondeados a 4 decimales.
- Nulos y centinelas son mutuamente excluyentes (una celda vacía nunca cuenta como centinela).
- Sin catálogo ⇒ `validity_score == 1.0`.
- `Σ by_file[].null_cells == null_cells`; `Σ by_file[].sentinel_cells == sentinel_cells`; `Σ by_file[].duplicate_rows == duplicate_rows`; `Σ by_file[].cells == total_cells`; `Σ by_file[].rows == total_rows`.
- Mismas entradas (mismo `ingestion_report.json`, mismas copias bronze, mismo `profiling_config.yaml`) ⇒ mismo `profiling_report.json` byte a byte.
- Profiling no falla porque `ingestion_report.success == false`.

---

## Casos Límite y Errores

| Caso | Contexto | Resultado esperado |
|---|---|---|
| Camino feliz | 1 archivo ingerido 100×5, 10 nulos, 25 centinelas (catálogo de 5), 10 filas duplicadas; estructura con 1 `missing_column` sobre 4 declarados | `completeness_score=0.98`, `validity_score=0.95`, `uniqueness_score=0.90`, `structural_score=0.875`, `global_score=0.9263` (pesos default). |
| Sin `profiling_config.yaml` | archivo de config ausente | `sentinel_cells=0`, `validity_score=1.0`, `catalog_size=0`; pesos default; Profiling no falla (`CA-15`, `CA-18`). |
| Catálogo vacío | `profiling_config.yaml` sin `sentinels` o cajas vacías | igual que "sin config" para validez (`validity_score=1.0`). |
| Sin archivos ingeridos | todos `missing`/`rejected`/sobrantes | `total_cells=0` ⇒ `completeness_score=validity_score=1.0`; `total_rows=0` ⇒ `uniqueness_score=1.0`; `structural_score` según estructura; `defects.*.by_file=[]`. |
| Archivo solo con encabezado (0 filas) | `rows=0` | aporta `0` celdas y `0` filas; no rompe denominadores. |
| Nulo vs centinela | celda vacía `""` con `""` NO en catálogo | cuenta como nula, no como centinela; si `""` estuviera en catálogo, sigue contando solo como nula (exclusión mutua, `CA-16`). |
| Centinela con variante | token `-999` en catálogo, celda `"-999.0"` | **no** se detecta como centinela (coincidencia exacta de token, riesgo aceptado `DS-PRF2-4`). |
| Pesos override válidos | `weights` suma `1.0` con reparto no uniforme | `health.weights` refleja el override; `global_score` los usa (`CA-04`). |
| Pesos override inválidos | `weights` no suman `1.0`, o falta una clave, o negativo | `FlowContractError` en `validate` (`DS-PRF2-1`). |
| `ingestion` fallido | `ingestion_report.success=false` | Profiling calcula igual; `profiling_report.success=true` (`CA-25`). |
| Reproducibilidad | dos `run(ctx)` con mismas entradas | `profiling_report.json` byte-idéntico (`CA-21`). |
| `ingestion_report.json` ausente | falta el `requires` | `FlowContractError` en `validate` base; no se escribe `profiling_report.json` (`CA-24`). |

---

## Interfaces / Firmas Públicas

```python
# src/foda/flows/f040_profiling/profiling.py  (clase ya existente; se endurece load_inputs/execute)
class Profiling(Flow):
    name = "profiling"
    requires = [Artifact(name="ingestion_report", base="outputs",
                         relative="030_ingestion/ingestion_report.json")]
    produces = [Artifact(name="profiling_report", base="outputs",
                         relative="040_profiling/profiling_report.json")]
    # profiling_config.yaml NO va en requires (opcional; se comprueba a mano en load_inputs).

    def load_inputs(self, ctx: ClientContext) -> None: ...   # ingestion_report + profiling_config (si existe)
    def execute(self, ctx: ClientContext) -> FlowResult: ...  # estructural + lectura bronze + 4 sub-scores; arma v0.3
    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None: ...  # escribe report determinista
```
- **No** sobreescribe `run()`: usa el template method heredado de `Flow`.
- `FlowContractError`: (a) `ingestion_report.json` ausente (base, sin cambios); (b) `weights` inválidos (`DS-PRF2-1`).
- Nombres de helpers de cálculo y el uso concreto de `pandas`/lector YAML son detalle de `plan_builder`; lo observable es el reporte v0.3 determinista.

---

## Criterios de Aceptación (verificables)
> Cada criterio es traducible a uno o más tests (con `ClientContext` bajo `tmp_path`, un `ingestion_report.json` de fixture con `bronze_path` que apunta a csv de contenido conocido, un `profiling_config.yaml` opcional, aserciones sobre `health`/`defects` y `pytest.raises(FlowContractError)` para los errores duros) y traza a la(s) `HU-xx` que satisface.

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | `profiling_report.json` contiene `health` con **exactamente** las claves `global_score`, `weights`, `structural_score`, `completeness_score`, `validity_score`, `uniqueness_score`; los 4 sub-scores y `global_score` son `float` en `[0.0, 1.0]`. | HU-01 |
| CA-02 | Para entradas de valores conocidos, `health.global_score == round(w_struct·structural_score + w_compl·completeness_score + w_valid·validity_score + w_uniq·uniqueness_score, 4)` (ej.: sub-scores `0.875/0.98/0.95/0.90` con pesos `0.25` ⇒ `0.9263`). | HU-01 |
| CA-03 | Sin `profiling_config.yaml` (o sin bloque `weights`), `health.weights == {structural:0.25, completeness:0.25, validity:0.25, uniqueness:0.25}` y `global_score` es la media aritmética de los 4 sub-scores. | HU-01 |
| CA-04 | Con `weights` válidos en `profiling_config.yaml` (4 claves, `≥0`, suma `1.0`), `health.weights` refleja esos pesos y `global_score` se calcula con ellos; con `weights` inválidos (no suman `1.0`, falta clave o negativo), `run(ctx)` lanza `FlowContractError` y no escribe el reporte. | HU-01, HU-05 |
| CA-05 | `health.structural_score` es igual al `global_score` que `stab_1` calcularía para el mismo `ingestion_report.json` (fórmula ponderada por severidad sobre `files_declared`, borde `files_declared==0 ⇒ 1.0`). | HU-01, HU-06 |
| CA-06 | `defects.completeness.total_cells == Σ(rows×columns)` sobre los archivos `status=="ingested"`; coincide con el valor esperado del fixture. | HU-02 |
| CA-07 | `defects.completeness.null_cells` == nº de celdas nulas (NaN o cadena vacía tras `strip`) sobre los archivos ingeridos; coincide con el fixture de contenido conocido. | HU-02 |
| CA-08 | `health.completeness_score == round(1 − null_cells/total_cells, 4)`, y `== 1.0` cuando `total_cells == 0`. | HU-02 |
| CA-09 | `defects.completeness.by_file` tiene una entrada `{name, rows, columns, cells, null_cells}` por archivo ingerido, en el orden de `ingestion_report.datasets[].files[]`, y `Σ by_file[].null_cells == null_cells`. | HU-02 |
| CA-10 | `defects.uniqueness.total_rows == Σ rows` sobre los archivos ingeridos; coincide con el fixture. | HU-03 |
| CA-11 | `defects.uniqueness.duplicate_rows` == Σ, por archivo, de filas idénticas a una fila anterior del mismo archivo (`DataFrame.duplicated(keep="first")`); coincide con el fixture; `Σ by_file[].duplicate_rows == duplicate_rows`. | HU-03 |
| CA-12 | `health.uniqueness_score == round(1 − duplicate_rows/total_rows, 4)`, y `== 1.0` cuando `total_rows == 0`. | HU-03 |
| CA-13 | Con catálogo no vacío, `defects.validity.sentinel_cells` == nº de celdas **no nulas** cuyo valor textual literal es exactamente igual a algún token del catálogo unificado; coincide con el fixture. | HU-04 |
| CA-14 | `health.validity_score == round(1 − sentinel_cells/total_cells, 4)`, y `== 1.0` cuando `total_cells == 0`. | HU-04 |
| CA-15 | Sin `profiling_config.yaml` (o con catálogo vacío), `defects.validity.sentinel_cells == 0`, `defects.validity.catalog_size == 0` y `health.validity_score == 1.0`. | HU-04, HU-05 |
| CA-16 | Una celda nula **no** se cuenta como centinela aunque la cadena vacía figure en el catálogo (exclusión mutua); y un token numérico `-999` **no** matchea la celda `"-999.0"` (coincidencia exacta de token). | HU-04 |
| CA-17 | Profiling lee el catálogo del artefacto **vendor-owned** `900_vendor/profiling/<name>/profiling_config.yaml` (fuera de `clients/<name>/`, no editable por el cliente), unificando las cajas `numeric`, `non_numeric` y `boolean` en un solo conjunto de tokens; `defects.validity.catalog_size` == nº de tokens de esa unión. Un `profiling_config.yaml` colocado dentro de `clients/<name>/` **no** es leído por el flujo. | HU-05 |
| CA-18 | Si `profiling_config.yaml` **no existe**, `run(ctx)` **no** lanza excepción por ello y completa con catálogo vacío y pesos default. | HU-05 |
| CA-19 | `profiling_report.json` declara `schema_version == "0.3"`. | HU-06 |
| CA-20 | `profiling_report.json` conserva los campos de identidad `client == ctx.name` (str), `flow == "profiling"` y `success` (bool). | HU-06 |
| CA-21 | Dos ejecuciones de `run(ctx)` con las mismas entradas (mismo `ingestion_report.json`, mismas copias bronze, mismo `profiling_config.yaml`) producen un `profiling_report.json` byte-idéntico (`sort_keys=True`, `indent=2`, `ensure_ascii=False`, newline final). | HU-06 |
| CA-22 | El reporte tiene **exactamente** las claves top-level `schema_version`, `client`, `flow`, `success`, `health`, `defects`; y `defects` tiene **exactamente** los sub-bloques `structural`, `completeness`, `validity`, `uniqueness`. | HU-06 |
| CA-23 | `defects.structural` contiene `files_declared`, `files_healthy`, `files_with_problems`, `problems_by_type` (4 claves fijas) y `pareto`, con los mismos valores que `stab_1` calcularía para el mismo `ingestion_report.json`. | HU-06 |
| CA-24 | Si `ingestion_report.json` **no existe**, `run(ctx)` lanza `FlowContractError` en `validate` (base) nombrando el artefacto ausente, y **no** se escribe `profiling_report.json`. | HU-06 |
| CA-25 | Con `ingestion_report.success == false`, `run(ctx)` **no** lanza excepción, devuelve `FlowResult(success=True, …)`, escribe `profiling_report.json` con `success == true` y calcula `health`/`defects` sobre lo disponible. | HU-06 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` queda cubierta por ≥ 1 `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02, CA-03, CA-04, CA-05 |
| HU-02 | CA-06, CA-07, CA-08, CA-09 |
| HU-03 | CA-10, CA-11, CA-12 |
| HU-04 | CA-13, CA-14, CA-15, CA-16 |
| HU-05 | CA-04, CA-15, CA-17, CA-18 |
| HU-06 | CA-05, CA-19, CA-20, CA-21, CA-22, CA-23, CA-24, CA-25 |

Todas las HU (HU-01…HU-06) quedan cubiertas por ≥ 1 CA.

---

## No-Objetivos
- **Perfil diagnóstico por columna** (categórico: distribución/dominancia, columnas constantes, cardinalidad, candidatos a casi-duplicado; numérico: min/max/media/mediana/cuartiles + atípicos IQR/Tukey). Diferido a `stab_3` (`D-097`, `D-101`, `D-102`). Es informativo y **no** penaliza el score (`D-098`).
- **Comparación contra `client_register.yaml`** real (Discovery real no existe como artefacto con datos).
- **Exportables csv/xlsx** (`foda export --flow profiling`).
- **Uso de LLM.** Profiling es determinista (§6); la detección de centinelas es por catálogo de tokens exactos, no por inferencia semántica.
- **Corrección/limpieza de defectos.** Profiling audita y señala, nunca corrige (`D-101`); la corrección es de Cleaning (050).
- **Normalización numérica de tokens centinela** (p. ej. `-999` ≡ `-999.0`) y **aplicación de cajas por tipo de columna**: no se abordan en esta banda (coincidencia exacta de token; unión plana de cajas).
- **Manejo defensivo de un `ingestion_report.json` que viole el contrato de `ingestion`** o de una copia bronze ausente pese a estar declarada `ingested`: fuera de alcance (input CONFORME); solo la ausencia física del `ingestion_report.json` está cubierta (`CA-24`).
- **Modificar el gate de progresión `D-080`** ni la capa de despacho de la CLI: ya implementados; esta banda solo endurece el cálculo interno de `Profiling`.
- **Rediseño del core de rutas** más allá del **mínimo** necesario para resolver el config **vendor-owned** fuera de `clients/` (`900_vendor/profiling/<name>/profiling_config.yaml`, `DS-PRF2-6`): el mecanismo concreto (helper de vendor root) lo fija `plan_builder`; no se amplía `ClientContext`/`Artifact` más de lo imprescindible.

---

## Puntos de confirmación para el GATE humano
Decisiones que el humano ratifica o ajusta antes de `plan_builder`. Las dos primeras (A-020, A-021) ya fueron decididas por el humano y aquí solo se confirma su plasmación; las 4 restantes son las ambigüedades de detalle que `definition.md` delegó a `spec_writer` (NC-6).

1. **A-020 (ya resuelta) — `pandas`** como librería para leer `bronze/` (nulos/duplicados/centinelas). No es dependencia nueva (ya usada por `Ingestion`). ¿Se confirma la plasmación en `DS-PRF2-2`?
2. **A-021 (ya resuelta) — pesos default `0.25` c/u, override por cliente.** ¿Se confirma la regla de validación de `weights` (4 claves, `≥0`, suma `1.0 ± 1e-9`, `FlowContractError` si no) y su publicación en `health.weights`? (`DS-PRF2-1`, `DS-PRF2-6`).
3. **`DS-PRF2-1` — fórmula y normalización.** ¿Se ratifica `global_score` = media ponderada; los 4 denominadores naturales (archivos / celdas / celdas / filas); redondeo a 4 decimales; y los bordes de denominador cero ⇒ sub-score `1.0`?
4. **`DS-PRF2-3`/`DS-PRF2-4` — semántica de detección.** ¿Se acepta: nulo = NaN o `""` tras `strip`; centinela = celda no nula con match **exacto** de token; exclusión mutua nulo/centinela; duplicado = `DataFrame.duplicated(keep="first")` por archivo; unión plana de las 3 cajas del catálogo; sin normalización numérica (riesgo `-999` vs `-999.0` aceptado)?
5. **`DS-PRF2-5` — forma del reporte y `schema_version`.** ¿Se acepta `health` = scoreboard (`global_score`, `weights`, 4 sub-scores) + bloque hermano `defects` con `structural`/`completeness`/`validity`/`uniqueness`, **reubicando** el detalle estructural de `stab_1` de `health` a `defects.structural`, y el bump a `schema_version "0.3"`? (implica que consumidores de `stab_1` re-lean rutas; riesgo documentado).
6. **`DS-PRF2-6` — `profiling_config.yaml` VENDOR-OWNED (ENMIENDA aprobada por negocio).** ¿Se ratifica la ubicación **fuera de `clients/`** en `900_vendor/profiling/<name>/profiling_config.yaml` (vendor-owned, por cliente, no editable por el cliente, motivo = integridad del score facturable), su carácter **opcional** (fuera de `requires`), y que su resolución no use las bases de `ClientContext` sino el vendor/project root (posible toque mínimo del core, a detallar en `plan_builder`)?
7. **`DS-PRF2-7` — Riesgos de facturación reconocidos.** ¿Se acepta reconocer R-BILL-1 (`-999` vs `-999.0`) y R-BILL-2 (denominador cero ⇒ score `1.0`) como riesgos con impacto económico **marcados para endurecer en `stab_3`**, sin resolverlos en `stab_2`?
