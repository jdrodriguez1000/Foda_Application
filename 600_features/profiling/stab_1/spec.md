# Spec — profiling (banda `stab_1`)

> Artefacto de la etapa 2 (`spec_writer`). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables **codificados (`CA-xx`) y enlazados a las historias de usuario (`HU-xx`)** de `definition.md`. **Requiere aprobación humana** (gate) antes de planear.
>
> Banda: `stab_1`. Fuentes canónicas: `600_features/profiling/stab_1/definition.md`, `600_features/profiling/feature_contract.md`, `600_features/profiling/tracer_bullet/spec.md` (reporte v0.1 que aquí se enriquece), `600_features/ingestion/tracer_bullet/spec.md` (esquema de `ingestion_report.json`, única fuente), `700_architecture/system_design.md` (§6, §8, §15), `800_persistence/decisions.md` (`D-088`, `D-089`, `D-080`). Código vigente (CONFORME): `src/foda/flows/f040_profiling/profiling.py` (clase `Profiling`), `src/foda/core/flow.py`, `src/foda/core/context.py`.

## Resumen
Endurece el flujo **040 Profiling** para que calcule, de forma **determinista** y usando **únicamente** `ingestion_report.json` (sin leer `bronze/`), la **salud estructural** del ingreso —`global_score`, conteos de archivos, `problems_by_type` y `pareto`— y la persista como un nuevo bloque `health` dentro de `profiling_report.json`, subiendo `schema_version` de `"0.1"` a `"0.2"` y conservando los campos de identidad ya existentes.

---

## Decisiones de Diseño (contexto: 7 acordadas con el humano + sub-decisiones delegadas)

Las **7 decisiones acordadas con el humano** (que resuelven los supuestos abiertos que dejó `feature_definer` en `definition.md` §Riesgos y Supuestos) son la base de esta spec y **no se reabren**. Se transcriben como decisiones formalizadas (`DS-PRF-*`). Las **sub-decisiones de detalle** delegadas explícitamente a `spec_writer` (redondeo, borde de 0 archivos, desempate y esquema de `pareto`) se resuelven aquí con su razonamiento (NC-1/NC-6) y se listan al final como **puntos del GATE humano** (junto con la ratificación pendiente de la fórmula, ver `DS-PRF-2`). Ninguna se asume en silencio.

### DS-PRF-1 — Alcance = solo estructural (vocabulario cerrado de 4 tipos)
- Los únicos problemas considerados son los **4 tipos** del vocabulario heredado de `ingestion`: `missing_file`, `unexpected_file`, `missing_column`, `unexpected_column`. El análisis a nivel de celda/contenido (duplicados, nulos, tipos, rangos) queda **explícitamente fuera** (diferido a `stab_2`, `D-089`). Profiling **no** lee `bronze/`, **no** compara contra `client_register.yaml`, **no** exporta csv/xlsx y **no** usa LLM.

### DS-PRF-2 — `global_score` = ponderado por severidad (propuesta canónica, pendiente de RATIFICACIÓN en el GATE)
- **Pesos** (penalización por cada ocurrencia de problema, por tipo):

  | tipo | peso |
  |---|---|
  | `missing_file` | 1.0 |
  | `missing_column` | 0.5 |
  | `unexpected_file` | 0.3 |
  | `unexpected_column` | 0.1 |

- **Fórmula:**
  - `penalización_total = Σ ( peso[tipo] × conteo[tipo] )` sobre los 4 tipos (los conteos son los de `problems_by_type`, ver `DS-PRF-4`).
  - `global_score = max(0.0, 1.0 − penalización_total / files_declared)`.
- **Rango y tipo:** `global_score` es un `float` en `[0.0, 1.0]` (nunca negativo por el `max(0.0, …)`; nunca > 1.0 porque la penalización es ≥ 0). **Sub-decisión delegada (redondeo/determinismo):** se **redondea a 4 decimales** con la semántica de `round(x, 4)` de Python. Justificación: 4 decimales bastan para discriminar penalizaciones finas (peso mínimo 0.1 sobre denominadores realistas) sin arrastrar ruido de coma flotante que rompa el determinismo byte a byte (§6). Es una decisión verificable (`CA-05`).
- **Borde `files_declared == 0` (sub-decisión delegada):** `global_score = 1.0`. Justificación: sin archivos declarados no hay línea base estructural que penalizar; la división por cero se evita fijando el score neutro máximo. Nota: si en ese estado existieran `unexpected_file` (archivos sobrantes), `problems_by_type`/`pareto` **sí** los reportan, pero el `global_score` permanece en `1.0` (el score solo se normaliza contra lo declarado). Comportamiento verificable (`CA-04`).
- **RATIFICACIÓN pendiente (NC-6):** los pesos, la fórmula, el redondeo a 4 decimales y el valor `1.0` del borde de 0 archivos están **acordados pero pendientes de ratificación** en el GATE humano posterior a esta etapa. Se documentan aquí como la **propuesta canónica** de la spec. Ver *Puntos de confirmación para el GATE humano*.

### DS-PRF-3 — Conteos de archivos (descriptivos, independientes del score)
- `files_declared` = número de archivos **declarados** en el ingreso = `ingestion_report.summary.files_declared` (que en `ingestion` = nº de `historical_data.datasets[].files[].name` del contrato). Los `unexpected_file` **NO** son archivos declarados: **no** cuentan en `files_declared`.
- `files_healthy` = archivos **declarados** con **CERO** problemas de cualquier tipo.
- `files_with_problems` = archivos **declarados** con **al menos un** problema.
- **Derivación canónica (lectura sin ambigüedad):** los conteos por archivo se derivan iterando `ingestion_report.datasets[].files[]` (los archivos declarados): un archivo declarado es **sano** si su `status == "ingested"` **y** su lista `inconsistencies` está vacía; en caso contrario es **con problemas** (cubre `status ∈ {"missing","rejected"}` y/o `inconsistencies ≠ []`, es decir `missing_file`/`missing_column`/`unexpected_column` asociados a ese archivo). Los `unexpected_file` viven en `ingestion_report.unexpected_files[]` (sin archivo declarado propio) y por eso quedan fuera de este conteo, aunque **sí** penalizan el score (`DS-PRF-2`) y **sí** cuentan en `problems_by_type` (`DS-PRF-4`).
- **Invariante:** `files_healthy + files_with_problems == files_declared` (los `unexpected_file` no rompen la identidad porque no entran en ninguno de los tres términos). Verificable (`CA-09`, `CA-10`).

### DS-PRF-4 — `problems_by_type` (conteo agregado por tipo)
- Objeto con **exactamente las 4 claves** del vocabulario cerrado, cada una un entero ≥ 0 = nº de ocurrencias de ese tipo. Las claves con cero ocurrencias se incluyen igualmente (esquema estable y completo).
- **Fuente canónica:** la lista **top-level `ingestion_report.inconsistencies[]`** (`{type, detail}`), que por diseño de `ingestion` (DS-ING-9) **agrega TODAS** las inconsistencias del run (de archivo y de columna). `problems_by_type[tipo]` = nº de entradas de esa lista con ese `type`. Verificable (`CA-11`, `CA-12`).

### DS-PRF-5 — `pareto` (ranking por TIPO, con desempate determinista) — esquema delegado a `spec_writer`
- **Unidad de ranking:** el **tipo de problema** (no el archivo/dataset). Se resuelve así la ambigüedad "tipo vs. archivo" que `definition.md` dejó abierta (§Riesgos, punto 4), en línea con la decisión 5 acordada.
- **Contenido:** lista ordenada que incluye **solo los tipos con `count ≥ 1`** (los tipos sin ocurrencias no aparecen en el pareto; sí figuran con 0 en `problems_by_type`).
- **Orden (determinista):** por `count` **descendente**; **desempate** por `type` en **orden alfabético ascendente**. Verificable (`CA-13`, `CA-14`).
- **Esquema de cada entrada (sub-decisión delegada):** `{ "type": <str>, "count": <int>, "pct": <float> }`, donde `pct = round(count / Σ(problems_by_type), 4)` es la fracción que ese tipo representa sobre el **total de ocurrencias de problemas** del run. Justificación: un "pareto" sin cuota relativa es solo una lista ordenada; `count` da la frecuencia y `pct` la contribución relativa (coherente con la "estrella polar" del `feature_contract`, que menciona *count y pct*), sin duplicar información. Cuando `Σ(problems_by_type) == 0` el pareto es `[]` (no hay división). **Sin pérdida de información respecto a `problems_by_type`:** `Σ(pareto[].count) == Σ(problems_by_type)`. Verificable (`CA-15`, `CA-16`, `CA-17`). Este esquema se marca para confirmación en el GATE.

### DS-PRF-6 — `ingestion_report.success == false`: profiling calcula igual, no falla
- Profiling **calcula la salud sobre lo disponible** aunque `ingestion_report.success == false`; el `global_score` bajo comunica la mala salud. Profiling **NO** falla por ello: produce su reporte con normalidad. El campo `profiling_report.success` refleja que **el flujo Profiling se ejecutó correctamente** (leyó el reporte del predecesor y emitió el suyo), **independiente** del `success` de `ingestion` y **independiente** del `global_score`. Verificable (`CA-22`).
- Nota de gobernanza (fuera de alcance de esta banda): el **gate de progresión** `D-080` (que decide si `foda run --flow profiling` llega a ejecutar el flujo según el `success` de `ingestion`) vive en la capa de despacho de la CLI y **ya** se implementó en `tracer_bullet`; esta banda **no** lo modifica. `DS-PRF-6` se refiere al comportamiento **dentro** de `Profiling.run(ctx)`, una vez que el flujo sí corre.

### DS-PRF-7 — Enriquecimiento aditivo del reporte + bump de `schema_version`
- Se añade a `profiling_report.json` un bloque `health` con: `global_score`, `files_declared`, `files_healthy`, `files_with_problems`, `problems_by_type`, `pareto`.
- `schema_version` sube de `"0.1"` a `"0.2"` (bump **aditivo**: el bloque `health` es nuevo; los campos de identidad ya existentes de `tracer_bullet` —`client`, `flow`, `success`— se **conservan** sin cambios de tipo ni de valor). Verificable (`CA-18`, `CA-19`, `CA-20`).
- Determinismo byte a byte (§6): serialización `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)` + salto de línea final, idéntica a la ya usada por `Profiling` (tracer_bullet) e `Ingestion`. Como `sort_keys` **no** reordena listas, el orden de `pareto` es el fijado en `DS-PRF-5`. Verificable (`CA-21`).

---

## Contratos de Datos / Artefactos

| Dirección | Artefacto | Ruta (vía `ClientContext`) | Formato | Notas |
|---|---|---|---|---|
| requiere | `ingestion_report` | `Artifact(base="outputs", relative="030_ingestion/ingestion_report.json")` | JSON | Única fuente de esta banda. Producido por `Ingestion` (CONFORME). |
| produce | `profiling_report` | `Artifact(base="outputs", relative="040_profiling/profiling_report.json")` | JSON | Enriquecido a `schema_version "0.2"` con bloque `health`. |

### Entrada — `ingestion_report.json` (campos consumidos por Profiling)
De todo el esquema de `ingestion` (ver `600_features/ingestion/tracer_bullet/spec.md`, DS-ING-2/DS-ING-9), Profiling consume **solo**:
- `summary.files_declared` (int) → `files_declared`.
- `datasets[].files[]` con `status` (∈ `{"ingested","rejected","missing"}`) e `inconsistencies` (lista, posiblemente vacía) → conteos `files_healthy` / `files_with_problems` (`DS-PRF-3`).
- `inconsistencies[]` (top-level, cada una `{type, detail}`; `type` ∈ vocabulario cerrado de 4) → `problems_by_type` y `pareto` (`DS-PRF-4`, `DS-PRF-5`).

`profiling_report.json` se calcula sobre lo que el reporte declare; **no** se leen `bronze/` ni los archivos crudos.

**Supuesto de contrato (frontera de alcance, NC-2):** Profiling asume que `ingestion_report.json` cumple el contrato de `ingestion` (esquema DS-ING-2/DS-ING-9: presencia de `summary.files_declared`, `datasets[].files[]` y la lista top-level `inconsistencies[]`), ya que lo produce un flujo **CONFORME y determinista**. El manejo defensivo de un `ingestion_report.json` que viole ese contrato (JSON corrupto, campos ausentes) queda **fuera de alcance** de esta banda; la ausencia **física** del archivo sí está cubierta por `validate` base (ver *Comportamiento*, y `CA-23`).

### Salida — `profiling_report.json` v0.2 (esquema propuesto, `DS-PRF-7`)
```json
{
  "schema_version": "0.2",
  "client": "acme",
  "flow": "profiling",
  "success": true,
  "health": {
    "global_score": 0.875,
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
  }
}
```
- `client` (str, `= ctx.name`), `flow` (`"profiling"`), `success` (bool), `schema_version` (`"0.2"`): campos de identidad conservados de `tracer_bullet` (`DS-PRF-7`).
- `health.global_score` (float en `[0.0,1.0]`, redondeado a 4 decimales, `DS-PRF-2`).
- `health.files_declared`/`files_healthy`/`files_with_problems` (int, `DS-PRF-3`).
- `health.problems_by_type` (objeto con las 4 claves fijas → int ≥ 0, `DS-PRF-4`).
- `health.pareto` (lista de `{type:str, count:int, pct:float}` ordenada, solo tipos con `count ≥ 1`, `DS-PRF-5`).

**Ejemplo de cálculo (anclaje de `global_score`).** Con `files_declared = 4` y una sola ocurrencia `missing_column`: `penalización_total = 0.5 × 1 = 0.5`; `global_score = max(0.0, 1.0 − 0.5/4) = 1.0 − 0.125 = 0.875`. Con `files_declared = 4` y `{missing_file:1, missing_column:1, unexpected_file:1, unexpected_column:1}`: `penalización_total = 1.0 + 0.5 + 0.3 + 0.1 = 1.9`; `global_score = max(0.0, 1.0 − 1.9/4) = 0.525`. Con `files_declared = 1` y `{missing_file:1, unexpected_file:2}`: `penalización_total = 1.0 + 0.6 = 1.6`; `global_score = max(0.0, 1.0 − 1.6/1) = max(0.0, −0.6) = 0.0` (clamp).

---

## Comportamiento Esperado

Ejecución de `Profiling().run(ctx)` (template method heredado de `Flow`: `load_inputs → validate → execute → write_outputs`, **sin** sobreescribir `run`):

1. **`load_inputs(ctx)` / `validate(ctx)`.** `validate` base comprueba la existencia física del único `requires` (`ingestion_report.json`). Si falta → `FlowContractError` nombrándolo, **antes** de `execute`/`write_outputs`; no se escribe `profiling_report.json` (`CA-23`). Profiling parsea `ingestion_report.json` (en `load_inputs` o al inicio de `execute`; el reparto fino es de `plan_builder`).
2. **`execute(ctx)` — cálculo de salud estructural (determinista, sin LLM, sin leer `bronze/`):**
   1. `files_declared = summary.files_declared`.
   2. Recorre `datasets[].files[]` y clasifica cada archivo declarado en **sano** (`status == "ingested"` y `inconsistencies == []`) o **con problemas** (resto). Acumula `files_healthy` y `files_with_problems` (`DS-PRF-3`).
   3. Cuenta ocurrencias por tipo sobre la lista top-level `inconsistencies[]` → `problems_by_type` (4 claves fijas, `DS-PRF-4`).
   4. `penalización_total = Σ peso[tipo]×problems_by_type[tipo]`; `global_score = max(0.0, 1.0 − penalización_total/files_declared)` redondeado a 4 decimales; si `files_declared == 0` → `global_score = 1.0` (`DS-PRF-2`).
   5. Construye `pareto` (tipos con `count ≥ 1`, orden `count` desc / `type` asc, cada entrada `{type,count,pct}`; `[]` si no hay problemas) (`DS-PRF-5`).
   6. Arma el reporte v0.2 en memoria: identidad conservada (`schema_version:"0.2"`, `client`, `flow`, `success`) + bloque `health`. `success` refleja la ejecución del flujo (True en el camino normal), **independiente** del `success` de `ingestion` (`DS-PRF-6`).
   7. Devuelve `FlowResult(success=True, outputs=[<ruta profiling_report.json>])`.
3. **`write_outputs(ctx, result)`.** Crea la carpeta destino y escribe `profiling_report.json` con serialización determinista (`ensure_ascii=False, indent=2, sort_keys=True` + newline final) (`DS-PRF-7`).

**Invariantes:**
- Profiling **no** lee `bronze/` ni archivos crudos; su única fuente es `ingestion_report.json`.
- `files_healthy + files_with_problems == files_declared`.
- `Σ(pareto[].count) == Σ(problems_by_type)` (sin pérdida de información).
- Mismas entradas ⇒ mismo `profiling_report.json` byte a byte.
- Profiling no falla porque `ingestion_report.success == false`.

---

## Casos Límite y Errores

| Caso | Contexto (`ingestion_report.json`) | Resultado esperado (`health`) |
|---|---|---|
| Camino feliz parcial (fixture) | `files_declared=4`, 3 ingested, 1 con `missing_column` | `files_healthy=3`, `files_with_problems=1`, `problems_by_type.missing_column=1` (resto 0), `global_score=0.875`, `pareto=[{missing_column,1,1.0}]`. |
| Todos sanos | `files_declared=N>0`, sin inconsistencias | `files_healthy=N`, `files_with_problems=0`, `problems_by_type` todo 0, `global_score=1.0`, `pareto=[]`. |
| Todos con problemas | `files_declared=N>0`, cada declarado con ≥1 problema | `files_healthy=0`, `files_with_problems=N`, `global_score` según fórmula (posible clamp a `0.0`). |
| 0 archivos declarados | `summary.files_declared=0` | `files_declared=0`, `files_healthy=0`, `files_with_problems=0`, `global_score=1.0` (borde, `DS-PRF-2`), invariante se mantiene. |
| Solo `unexpected_file` | `files_declared=M`, k `unexpected_file`, declarados todos sanos | no cuentan en `files_declared`/`files_healthy`; `problems_by_type.unexpected_file=k`; penalizan `global_score` (`−0.3k/M`); aparecen en `pareto`. |
| `ingestion` fallido | `ingestion_report.success=false` | Profiling calcula igual; `profiling_report.success=true`; `global_score` bajo refleja la mala salud (`DS-PRF-6`). |
| Empate en pareto | dos tipos con el mismo `count` | orden por `type` alfabético ascendente entre ellos (`DS-PRF-5`). |
| Reproducibilidad | dos `run(ctx)` con el mismo `ingestion_report.json` | `profiling_report.json` byte-idéntico. |
| `ingestion_report.json` ausente | falta el `requires` | `FlowContractError` en `validate` base; no se escribe `profiling_report.json`. |

---

## Interfaces / Firmas Públicas

```python
# src/foda/flows/f040_profiling/profiling.py  (clase ya existente; se endurece execute())
class Profiling(Flow):
    name = "profiling"
    requires = [Artifact(name="ingestion_report",  base="outputs", relative="030_ingestion/ingestion_report.json")]
    produces = [Artifact(name="profiling_report", base="outputs", relative="040_profiling/profiling_report.json")]

    def load_inputs(self, ctx: ClientContext) -> None: ...   # parsea ingestion_report.json
    def execute(self, ctx: ClientContext) -> FlowResult: ...  # calcula health, arma reporte v0.2
    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None: ...  # escribe report determinista
```
- **No** sobreescribe `run()`: usa el template method heredado de `Flow`.
- `FlowContractError` **solo** para el `requires` (`ingestion_report.json`) ausente (comportamiento base, sin cambios).
- Nombres exactos de helpers de cálculo son detalle de `plan_builder`; lo observable es el bloque `health` y el reporte v0.2 determinista.

---

## Criterios de Aceptación (verificables)
> Cada criterio es traducible a uno o más tests (con `ClientContext` bajo `tmp_path`, un `ingestion_report.json` de fixture con conteos conocidos, aserciones sobre el `health` resultante y `pytest.raises(FlowContractError)` para el error duro) y traza a la(s) `HU-xx` que satisface (D-031).

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | Tras `run(ctx)`, `profiling_report.json` contiene `health.global_score` como `float` en `[0.0, 1.0]`. | HU-01 |
| CA-02 | Para un `ingestion_report.json` de conteos conocidos, `health.global_score == round(max(0.0, 1.0 − (Σ peso[t]×problems_by_type[t]) / files_declared), 4)` con pesos `{missing_file:1.0, missing_column:0.5, unexpected_file:0.3, unexpected_column:0.1}` (ej.: 1 `missing_column` sobre `files_declared=4` ⇒ `0.875`). | HU-01 |
| CA-03 | Cuando `penalización_total > files_declared`, `health.global_score == 0.0` (clamp por `max(0.0, …)`, nunca negativo). | HU-01 |
| CA-04 | Cuando `ingestion_report.summary.files_declared == 0`, `health.global_score == 1.0` (borde definido, sin división por cero). | HU-01 |
| CA-05 | `health.global_score` está redondeado a **4 decimales** (`round(x,4)`); dos entradas idénticas dan exactamente el mismo valor. | HU-01, HU-05 |
| CA-06 | `health.files_declared == ingestion_report.summary.files_declared`. | HU-02 |
| CA-07 | `health.files_healthy` == nº de archivos de `datasets[].files[]` con `status == "ingested"` y `inconsistencies == []`; coincide con el valor esperado del fixture. | HU-02 |
| CA-08 | `health.files_with_problems` == nº de archivos de `datasets[].files[]` con `status != "ingested"` **o** `inconsistencies != []`; coincide con el valor esperado del fixture. | HU-02 |
| CA-09 | Se cumple la invariante `health.files_healthy + health.files_with_problems == health.files_declared`. | HU-02 |
| CA-10 | Un `ingestion_report.json` con ≥1 `unexpected_file` **no** incrementa `health.files_declared` (los sobrantes no son declarados), pero **sí** aporta a `problems_by_type.unexpected_file` y reduce `global_score`. | HU-02, HU-03, HU-01 |
| CA-11 | `health.problems_by_type` tiene **exactamente** las 4 claves `missing_file`, `unexpected_file`, `missing_column`, `unexpected_column`, cada una un `int ≥ 0` igual al nº de ocurrencias de ese `type` en la lista top-level `ingestion_report.inconsistencies[]`. | HU-03 |
| CA-12 | Para un `ingestion_report.json` sin inconsistencias, `health.problems_by_type` tiene las 4 claves con valor `0`. | HU-03 |
| CA-13 | `health.pareto` está ordenado por `count` **descendente**; para un fixture con distintos conteos, el orden coincide con el esperado. | HU-04 |
| CA-14 | Ante empate de `count`, las entradas de `health.pareto` se ordenan por `type` en orden **alfabético ascendente** (desempate determinista). | HU-04 |
| CA-15 | `health.pareto` incluye **solo** los tipos con `count ≥ 1`, y `Σ(pareto[].count) == Σ(problems_by_type.values())` (sin pérdida de información respecto a `problems_by_type`). | HU-04 |
| CA-16 | Cada entrada de `health.pareto` tiene las claves `type` (str del vocabulario cerrado), `count` (int ≥ 1) y `pct` (float), con `pct == round(count / Σ(problems_by_type.values()), 4)`. | HU-04 |
| CA-17 | Para un `ingestion_report.json` sin inconsistencias, `health.pareto == []`. | HU-04 |
| CA-18 | `profiling_report.json` declara `schema_version == "0.2"`. | HU-05 |
| CA-19 | `profiling_report.json` conserva los campos de identidad `client == ctx.name` (str), `flow == "profiling"` y `success` (bool). | HU-05 |
| CA-20 | `profiling_report.json` contiene un objeto `health` con **exactamente** las claves `global_score`, `files_declared`, `files_healthy`, `files_with_problems`, `problems_by_type`, `pareto`. | HU-05, HU-01, HU-02, HU-03, HU-04 |
| CA-21 | Dos ejecuciones de `run(ctx)` con el mismo `ingestion_report.json` producen un `profiling_report.json` byte-idéntico (serialización `sort_keys=True`, `indent=2`, `ensure_ascii=False`, newline final). | HU-05 |
| CA-22 | Con `ingestion_report.success == false`, `run(ctx)` **no** lanza excepción, devuelve `FlowResult(success=True, …)`, escribe `profiling_report.json` con `success == true` y un bloque `health` calculado sobre lo disponible (el `global_score` bajo comunica la mala salud). | HU-01, HU-02 |
| CA-23 | Si `ingestion_report.json` **no existe**, `run(ctx)` lanza `FlowContractError` en `validate` (base) nombrando el artefacto ausente, y **no** se escribe `profiling_report.json`. | HU-05 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` queda cubierta por ≥ 1 `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02, CA-03, CA-04, CA-05, CA-10, CA-20, CA-22 |
| HU-02 | CA-06, CA-07, CA-08, CA-09, CA-10, CA-20, CA-22 |
| HU-03 | CA-10, CA-11, CA-12, CA-20 |
| HU-04 | CA-13, CA-14, CA-15, CA-16, CA-17, CA-20 |
| HU-05 | CA-05, CA-18, CA-19, CA-20, CA-21, CA-23 |

Todas las HU (HU-01…HU-05) quedan cubiertas por ≥ 1 CA.

---

## No-Objetivos
- **Salud a nivel de datos/celda** (leer `bronze/`: nulos, duplicados, tipos, rangos, periodicidad sobre datos reales). Diferido a `stab_2` (`D-089`).
- **Comparación contra `client_register.yaml`** real (Discovery real no existe como artefacto con datos).
- **Exportables csv/xlsx** (`foda export --flow profiling`).
- **Uso de LLM** (Profiling es determinista, §6).
- **Modificar el gate de progresión `D-080`** ni la capa de despacho de la CLI (`--force`): ya implementados en `tracer_bullet`; esta banda solo endurece el cálculo interno de `Profiling`.
- **Ampliar el vocabulario de tipos de problema** más allá de los 4 heredados de `ingestion`.
- **Manejo defensivo de un `ingestion_report.json` que viole el contrato de `ingestion`** (JSON corrupto o campos ausentes): fuera de alcance (input es un artefacto CONFORME); solo su ausencia física está cubierta (`CA-23`).
- **Ampliación de `ClientContext`/`Artifact`** (no se toca el core).

---

## Puntos de confirmación para el GATE humano
Decisiones que el humano ratifica o ajusta antes de `plan_builder`. Las 7 primeras ya fueron **acordadas** con el humano (aquí se confirma su plasmación exacta); las sub-decisiones delegadas se proponen y quedan a ratificación (NC-6).

1. **`DS-PRF-2` — fórmula y pesos de `global_score` (RATIFICACIÓN pendiente):** ¿se ratifican los pesos `{missing_file:1.0, missing_column:0.5, unexpected_file:0.3, unexpected_column:0.1}`, la fórmula `max(0.0, 1.0 − penalización_total/files_declared)`, el **redondeo a 4 decimales** y el borde `files_declared==0 ⇒ global_score=1.0`?
2. **`DS-PRF-5` — esquema de `pareto` (sub-decisión delegada):** ¿se acepta que cada entrada sea `{type, count, pct}` con `pct` = cuota sobre el total de ocurrencias (4 decimales), que el pareto liste **solo** tipos con `count ≥ 1` y que el desempate sea alfabético ascendente por `type`?
3. **`DS-PRF-3` — derivación de `files_healthy`/`files_with_problems`:** ¿se acepta la lectura canónica "archivo sano = `status=="ingested"` y `inconsistencies==[]`" sobre `datasets[].files[]`, con `unexpected_file` excluido de `files_declared` pero penalizando el score?
4. **`DS-PRF-4` — `problems_by_type` con las 4 claves fijas** derivadas de la lista top-level `ingestion_report.inconsistencies[]`: ¿conforme?
5. **`DS-PRF-6` — `ingestion` fallido:** ¿se confirma que Profiling calcula la salud igual y `profiling_report.success` refleja la ejecución del flujo (no el `success` de `ingestion`)?
6. **`DS-PRF-7` — bump aditivo a `schema_version "0.2"`** conservando `client`/`flow`/`success`: ¿conforme?
