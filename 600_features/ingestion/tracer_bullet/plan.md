# Plan de Implementación — ingestion

> Artefacto de la etapa 3 (`plan_builder`). Traduce la `spec.md` **aprobada** (GATE humano superado)
> en un plan de implementación mínimo (NC-2) y en la lista **ordenada** de casos de test que guiarán
> el bucle TDD (red → green → refactor). **No** contiene código ni tests: solo el *cómo* y el *orden*.
>
> **RE-PLAN (DS-ING-8).** Esta versión regenera el plan anterior tras la **enmienda DS-ING-8** de la
> spec (aprobada por el humano): el **reparto de responsabilidad** entre los dos artefactos de entrada.
> Cambia **solo** la fuente de expectativas y las tareas/casos que la anclan; el resto del plan anterior
> se conserva íntegro (NC-3, cambio quirúrgico). Reparto DS-ING-8:
> - **`contract_data.json` = fuente del CONJUNTO de archivos esperados** (`historical_data.datasets[]`,
>   `...files[].name`) y de `summary.datasets_declared`/`summary.files_declared`. Ahora **se parsea y se usa**.
> - **`map_client_data.json` = fuente de las COLUMNAS esperadas por dataset** (`fields[]` con `name`/`required`),
>   emparejando dataset por `kind`.
> - **Sin** chequeo de coherencia mapa↔contrato; el vocabulario cerrado de inconsistencias no cambia.
>
> Banda: `tracer_bullet`. Fuentes: `spec.md` (esta celda, GATE humano APROBADO — DS-ING-1…8, incluidas
> las dos decisiones cerradas por el humano: landing en `010_inputs/030_ingestion/` reutilizando
> `base="inputs"` y `openpyxl` como dependencia), `definition.md` (HU-01…HU-06), `feature_contract.md`,
> `src/foda/core/flow.py` (`Flow`, `Artifact`, `FlowResult`, `FlowContractError`; CONFORME — se hereda,
> no se toca), `src/foda/core/context.py` (`ClientContext`, incluye `bronze_dir`/`inputs_dir`; CONFORME),
> `src/foda/core/scaffold.py` (`create_client`; CONFORME — árbol de cliente bajo `tmp_path`),
> `src/foda/flows/f020_onboarding/onboarding.py` (referencia de estilo de un `Flow` concreto; CONFORME),
> `700_architecture/system_design.md` (§7 estructura, §8 contrato de artefactos, §9 abstracción `Flow`,
> §10 medallion, §15 detalle 030), `800_persistence/decisions.md`, `980_guideline/principles.md`.
>
> **GATE humano al terminar:** este plan y sus casos TDD requieren aprobación del usuario antes de
> invocar `tdd_tester`.

---

## 1. Enfoque Técnico

Slice vertical mínimo (NC-4) y quirúrgico (NC-3): un único módulo nuevo bajo `src/foda/flows/f030_ingestion/`
que define la clase concreta **`Ingestion(Flow)`** (flujo 030, determinista, sin LLM). **No** se toca el
core (`flow.py`, `context.py`, `scaffold.py` están CONFORME y se consumen tal cual; NC-3), **ni** se amplía
`ClientContext`/`Artifact._BASE_TO_DIR_ATTR` (DS-ING-4): el *landing* de datos crudos se resuelve reutilizando
`ctx.inputs_dir / "030_ingestion"` (base lógica `inputs` ya existente) y la salida bronze reutiliza
`ctx.bronze_dir`. Se añade **una** dependencia de terceros: `openpyxl` (lectura `.xlsx`, aprobada por el humano).

### Clase a producir — `Ingestion(Flow)` (`src/foda/flows/f030_ingestion/ingestion.py`)

Hereda `Flow` y sobreescribe **solo** los 4 hooks del template method (no toca `run`). Contrato observable
(spec §Interfaces):

```python
name = "ingestion"
requires = [
    Artifact(name="contract_data",   base="outputs", relative="010_discovery/contract_data.json"),
    Artifact(name="map_client_data", base="outputs", relative="020_onboarding/map_client_data.json"),
]
produces = [
    Artifact(name="ingestion_report", base="outputs", relative="030_ingestion/ingestion_report.json"),
]
```

- **`load_inputs(ctx) -> None`** — resuelve las rutas de los dos `requires`; para cada uno, **si existe**, lee
  y parsea el JSON (`json.loads`) a estado de instancia (`self._contract`, `self._map`). Si alguno **no** existe,
  deja ese estado sin cargar para que `validate()` base lo detecte. **Ambos artefactos se parsean y se usan**
  (DS-ING-8): del **contrato** saldrán los archivos esperados; del **mapa**, las columnas esperadas. No escribe
  en disco. Los archivos crudos del landing **no** se leen aquí (se leen en `execute`, no son `requires`
  estáticos: DS-ING-4).
- **`validate(ctx) -> None`** — invoca **solo** `super().validate(ctx)`: existencia física de los dos `requires`
  → `FlowContractError` si falta alguno (DS-ING-1, cubre CA-21), **antes** de `execute`, sin salida. **No** valida
  datos aquí (las inconsistencias de datos son soft-report en `execute`).
- **`execute(ctx) -> FlowResult`** — deriva **en memoria** (sin LLM, sin escribir en disco):
  1. Del **contrato** (`self._contract`, **fuente del conjunto de archivos esperados** — DS-ING-8, spec §Entrada
     contract_data.json): la lista ordenada de datasets con `kind`/`source_medium` bajo `historical_data.datasets[]`
     y sus `files[].name` (**archivos esperados** = unión de `historical_data.datasets[].files[].name`;
     `datasets_declared` = `len(historical_data.datasets)`; `files_declared` = nº total de esos `files[].name`).
  2. Del **mapa** (`self._map`, **fuente de las columnas esperadas por dataset** — DS-ING-8, spec §Entrada
     map_client_data.json): por dataset, sus `fields[]` (**columnas esperadas** = `field.name`; **requeridas** =
     las de `required == true`). El dataset del mapa se **empareja** con el dataset homólogo del contrato **por
     `kind`** (contrato y mapa se mantienen coherentes; DS-ING-7/DS-ING-8). **No** hay chequeo de coherencia
     mapa↔contrato (DS-ING-8): cada fuente alimenta su propia dimensión de validación.
  3. Del **landing** (`ctx.inputs_dir / "030_ingestion"`): el conjunto de **archivos presentes** (`iterdir` si la
     carpeta existe; conjunto vacío si no existe — no es error, DS-ING-4).
  4. **Chequeo del conjunto de archivos (contra el contrato, HU-02):** por cada archivo esperado del contrato (en
     orden declarado): esperado-no-presente → `status="missing"` + inconsistencia `missing_file` (no se copia).
     Esperado-y-presente → lee el archivo (detecta separador entre `,`/`;`/`|` para delimitados; primera hoja para
     `.xlsx`), cuenta `rows` (datos, sin cabecera) y `columns` (cabecera), y valida columnas **contra el mapa**
     (DS-ING-3 / DS-ING-8): requerida (`required == true`) ausente → `missing_column`; columna presente no declarada
     en `fields` → `unexpected_column`. ≥1 inconsistencia de columna → `status="rejected"` (no se copia); si no →
     `status="ingested"`.
  5. **Archivos presentes no declarados** por ningún dataset **del contrato** → `unexpected_files` (orden
     alfabético) + inconsistencia `unexpected_file` (no se copia).
  6. Arma el reporte en memoria (esquema DS-ING-2, orden determinista DS-ING-6) y el **plan de copia** (rutas
     `ctx.bronze_dir / <name>` de los `ingested`). Devuelve
     `FlowResult(success=(<sin inconsistencias>), outputs=[<ruta reporte>] + [<rutas bronze de los ingested>])`.
- **`write_outputs(ctx, result) -> None`** — `mkdir(parents=True, exist_ok=True)` de `ctx.bronze_dir` y de la
  carpeta del reporte; copia **byte a byte** (binario) cada archivo `ingested` del landing a `ctx.bronze_dir / <name>`
  (DS-ING-6, HU-04); escribe `ingestion_report.json` con serialización **determinista** (DS-ING-6):
  `json.dumps(reporte, ensure_ascii=False, indent=2, sort_keys=True)` + salto de línea final. El reporte se escribe
  **siempre** que se llegó a `execute` (haya o no inconsistencias).

### Helpers privados de lectura (detalle interno; NC-2; nombres a fijar por el coder)

Funciones puras internas, **no** forman parte del contrato observable:

- **`_detect_separator(header_line) -> str`** (delimitados): entre `,`/`;`/`|`, elige el que aparece en la línea de
  cabecera con **mayor** número de ocurrencias. En el fixture cada archivo tiene un único separador inequívoco con
  ≥2 columnas (sin empates). *Caso límite fuera del fixture (documentado, NC-6):* archivo de una sola columna sin
  ningún separador → no lo fabrica esta banda; se difiere a `stab_1`.
- **`_read_delimited(path) -> (separator, header, row_count)`**: detecta separador, parsea con `csv.reader` usando
  ese `delimiter`, toma la primera fila como cabecera (`columns = len(header)`), cuenta filas de datos **no vacías**
  (ignora líneas totalmente en blanco, p. ej. newline final). Cubre `.csv` y `.txt` indistintamente (la extensión
  no determina el separador; DS-ING-7).
- **`_read_xlsx(path) -> (None, header, row_count)`**: `openpyxl.load_workbook(path, read_only=True, data_only=True)`,
  primera hoja (`wb.worksheets[0]`); primera fila con contenido = cabecera; `separator = None`; cuenta filas de datos
  con al menos una celda no vacía.
- **`_validate_columns(header, fields) -> list[inconsistencia]`**: (a) todo `field.name` con `required == true`
  ausente de `header` → `missing_column`; (b) toda columna de `header` no declarada como algún `field.name` →
  `unexpected_column`; (c) `required == false` ausente → **no** es inconsistencia (CA-10). Los `fields` provienen
  del dataset homólogo del **mapa** (DS-ING-8).
- **`_copy_bytes(src, dst)`**: copia binaria fiel (`dst.write_bytes(src.read_bytes())` o `shutil.copyfile`), sin
  re-serializar ni normalizar (DS-ING-6, HU-04).

**Fuente de expectativas (DS-ING-8, reparto aprobado por el humano):** las **expectativas de archivos** (nombres y
nº de archivos, `datasets_declared`/`files_declared`) se derivan de **`contract_data.json`**
(`historical_data.datasets[].files[].name`); las **expectativas de columnas** (esperadas y requeridas) se derivan de
**`map_client_data.json`** (`fields[]`), emparejando dataset por `kind`. **Ambos** artefactos se parsean en
`load_inputs` y se usan en `execute`. **No** se comprueba coherencia mapa↔contrato: cada fuente alimenta su propia
dimensión de validación (archivos ↔ contrato; columnas ↔ mapa). *(Sustituye la decisión previa "todas las
expectativas salían solo del mapa"; DS-ING-8, NC-6.)*

**Dependencias de librería:** `json`, `csv`, `pathlib`, `shutil` — **stdlib** (R1) — más **`openpyxl`** (única
dependencia nueva, aprobada). Sin pandas, sin JSON Schema/Pydantic. `openpyxl` ya está instalado en el entorno
(`3.1.5`), por lo que los tests xlsx pueden correr; se declara además en `pyproject.toml` para hacerla explícita.

### Fixtures de test (viven en `tests/`, no en `src/`)

El `ClientContext` se construye con `create_client(NAME, tmp_path/"clients")` (core CONFORME) +
`ClientContext(NAME, tmp_path/"clients")`; nunca se toca el `clients/` real (además `clients/` está en `.gitignore`).
El fixture del tracer (DS-ING-7) escribe, bajo el `ctx` temporal, un **`contract_data.json` y un
`map_client_data.json` coherentes entre sí** (misma lista de archivos y mismos datasets por `kind`; DS-ING-8) más los
archivos crudos del landing:

- `ctx.outputs_dir / "010_discovery/contract_data.json"` — contrato fabricado (require físico; **fuente de los
  archivos esperados**, DS-ING-8): `historical_data.datasets[]` con `kind`/`source_medium` y `files[].name` de los 3
  datasets del fixture; contenido alineado con el esquema de `onboarding` (D-055/D-058).
- `ctx.outputs_dir / "020_onboarding/map_client_data.json"` — mapa canónico fabricado (**fuente de las columnas
  esperadas**, DS-ING-8): los 3 datasets del fixture con su `kind` y sus `fields[]` (`name`/`required`).
- `ctx.inputs_dir / "030_ingestion/<archivo>"` — los archivos crudos del landing.

Como contrato y mapa se mantienen **coherentes** (misma lista de archivos y columnas), el reparto DS-ING-8 **no
altera** el resultado esperado del caso feliz.

Composición del fixture (DS-ING-7), archivos crudos con conteos **conocidos** (los valores exactos los fija el
`tdd_tester`; aquí se fija la estructura):

| dataset (`kind`) | `source_medium` | archivo landing | separador | columnas (cabecera) | filas de datos |
|---|---|---|---|---|---|
| `ventas` | `csv` | `ventas.csv` | `,` (coma) | `fecha,sede,clase,cantidad,precio_unitario` (5) | p. ej. 3 |
| `inventario` | `csv` | `inventario_2024.txt` | `;` (punto y coma) | `fecha;sede;clase;stock` (4) | p. ej. 2 |
| `inventario` | `csv` | `inventario_2025.csv` | `\|` (barra vertical) | `fecha\|sede\|clase\|stock` (4) | p. ej. 2 |
| `precios` | `xlsx` | `precios.xlsx` | `null` (Excel) | `clase,precio,moneda` (3) | p. ej. 3 |

> En el **contrato**, estos cuatro `files[].name` se reparten en sus datasets (`ventas`→`ventas.csv`;
> `inventario`→`inventario_2024.txt`, `inventario_2025.csv`; `precios`→`precios.xlsx`). En el **mapa**, cada dataset
> (`ventas`/`inventario`/`precios`) declara sus `fields[]`. Ambos coherentes.

Variantes derivadas por mutación puntual del fixture base (subconjuntos y mutaciones, como en `onboarding`):
- **Mínimo/tracer** (casos 1–3): un único dataset `ventas` con `ventas.csv` (coma), columnas correctas
  (declarado en el contrato + `fields` en el mapa).
- **Faltante** (caso 11): se declara un archivo en el **contrato** que no se deposita en el landing.
- **Sobrante** (caso 12): se deposita en el landing un archivo **no declarado en el contrato** por ningún dataset.
- **Columna requerida ausente** (caso 13): se quita del archivo una columna `required=true` **según el mapa**.
- **Columna no declarada** (caso 14): se añade a la cabecera una columna fuera de los `fields` **del mapa** (renombrado).
- **Columna opcional ausente** (caso 15): se quita `precio_unitario` (`required=false` en el mapa) de `ventas.csv`.
- **Landing vacío** (opcional, apoyo de caso 11): no se deposita ningún archivo.

---

## 2. Archivos Afectados

> El código **no** vive en `600_features/`; va en `src/foda/…` y `tests/…`.

| Ruta | Acción | Contenido |
|---|---|---|
| `pyproject.toml` | modificar | Añadir `openpyxl` a `[project].dependencies` (dependencia de lectura `.xlsx`, DS-ING-7). |
| `src/foda/flows/f030_ingestion/__init__.py` | crear | Paquete del flujo 030 (andamiaje; puede reexportar `Ingestion`). |
| `src/foda/flows/f030_ingestion/ingestion.py` | crear | Clase `Ingestion(Flow)`: `requires`/`produces` + 4 hooks + helpers de lectura/validación/copia. Stdlib + `openpyxl`. |
| `tests/flows/test_ingestion.py` | crear | Suite unit de `Ingestion` (fixture DS-ING-7 + variantes), `ClientContext` vía `create_client(...)` bajo `tmp_path`. |
| `tests/integration/test_ingestion_integration.py` | crear | Test de integración end-to-end (`integration_tester`, tras el bucle unit). |

**Notas de infraestructura:** el andamiaje base (`pyproject.toml`, `src/foda/`, `tests/`) ya existe. `src/foda/flows/`
y `src/foda/flows/__init__.py` **ya existen** (creados por `onboarding`): esta feature solo añade el subpaquete
`f030_ingestion/`. `tests/flows/` ya existe. `pyproject.toml` usa `pythonpath=["src"]` + `testpaths=["tests"]`.
`openpyxl` ya está instalado en el entorno (`3.1.5`); si un entorno limpio no lo tuviera, se instala con
`pip install -e .` tras el cambio de `pyproject.toml` (acción de entorno, no de código).

---

## 3. Dependencias y Contratos

- **Consume:** `foda.core.flow.{Flow, Artifact, FlowResult, FlowContractError}` (CONFORME, se hereda) y
  `foda.core.context.ClientContext` (CONFORME, resolución de rutas: `inputs_dir`, `outputs_dir`, `bronze_dir`).
  En tests, `foda.core.scaffold.create_client` (CONFORME) materializa el árbol §7 bajo `tmp_path`.
- **Entrada (DS-ING-8):** `contract_data.json` (`020_outputs/010_discovery/`) — **fuente de los archivos esperados**
  (`historical_data.datasets[].files[].name`, `datasets[]`) — y `map_client_data.json` (`020_outputs/020_onboarding/`)
  — **fuente de las columnas esperadas** (`fields[]`). Ambos son fixtures fabricados (Discovery/010 no se implementa;
  `map_client_data.json` lo produce `onboarding`, CONFORME, pero aquí se fabrica para aislar la feature) y **coherentes
  entre sí**. Archivos crudos del landing en `010_inputs/030_ingestion/` (nombres dinámicos, **no** son `requires`
  estáticos; DS-ING-4).
- **Produce:** `ingestion_report.json` (`020_outputs/030_ingestion/`, DS-ING-2), copias byte-a-byte en `data/bronze/`
  (DS-ING-6) y el módulo `src/foda/flows/f030_ingestion/`.
- **Contrato de errores:** `FlowContractError` **solo** para `contract_data.json`/`map_client_data.json` ausente
  (base). Inconsistencias de datos → reporte (soft-report, DS-ING-1), **nunca** excepción.
- **Nueva dependencia:** `openpyxl` (lectura `.xlsx`, DS-ING-7, aprobada por el humano) declarada en `pyproject.toml`.
- **Restricciones respetadas:** R1 (Python 3.13+; stdlib + `openpyxl`), NC-3 (no se toca el core ni se amplía
  `ClientContext`/`Artifact`), DS-ING-6 (fidelidad byte a byte + determinismo), DS-ING-8 (reparto contrato/mapa),
  invariantes (no toca `silver/`/`gold/`, no usa LLM, no transforma datos).

---

## 4. Tareas (atómicas y trazables)

> Cada tarea es **atómica**: **un solo responsable**, **un solo entregable**, y **código y test en tareas separadas**.
> **Estado** inicial `no_implementada` (∈ `no_implementada` | `implementada` | `cancelada_suspendida`); el **responsable
> de cada tarea es su único escritor de estado** (`D-021`). Trazabilidad → `CA-xx` de la spec (o andamiaje justificado).

### 4.1 Tareas de código / andamiaje (responsable `tdd_coder` / `tdd_refactor` / `integration_tester`)

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Añadir `openpyxl` a `[project].dependencies` de `pyproject.toml` (dependencia de lectura `.xlsx`, DS-ING-7). | `pyproject.toml` actualizado | tdd_coder | no_implementada | andamiaje (CA-04) |
| TSK-02 | Crear el subpaquete del flujo: `src/foda/flows/f030_ingestion/__init__.py` (andamiaje de paquete Python; §7). | Paquete `f030_ingestion` | tdd_coder | no_implementada | andamiaje (CA-20) |
| TSK-03 | Crear `ingestion.py` con `Ingestion(Flow)`: `name`, `requires`/`produces` (Artifacts spec §Interfaces), `load_inputs` (parsea **contract + map** si existen; DS-ING-8), `validate` (solo `super().validate`), `execute` (lee un archivo **coma**, cuenta rows/columns, valida columnas contra el mapa, arma reporte + plan de copia, `FlowResult`) y `write_outputs` (mkdir + copia byte a byte + escritura JSON determinista). Camino feliz mínimo (dataset comma). | `Ingestion` (esqueleto + tracer comma) | tdd_coder | no_implementada | CA-14, CA-01, CA-15, CA-11, CA-20 |
| TSK-04 | Lectura de delimitados con separador `;` (punto y coma): `_detect_separator`/`_read_delimited` reconocen `;`. | `Ingestion` (lector `;`) | tdd_coder | no_implementada | CA-02 |
| TSK-05 | Lectura de delimitados con separador `\|` (barra vertical): `_detect_separator`/`_read_delimited` reconocen `\|`. | `Ingestion` (lector `\|`) | tdd_coder | no_implementada | CA-03 |
| TSK-06 | Lectura de `.xlsx` con `openpyxl` (`_read_xlsx`): primera hoja, cabecera, conteo de filas; `separator=null`. | `Ingestion` (lector xlsx) | tdd_coder | no_implementada | CA-04 |
| TSK-07 | Fidelidad de copia a bronze: `_copy_bytes` copia byte a byte preservando formato/separador/extensión (delimitado `\|` y `.xlsx`). | `Ingestion` (copia fiel) | tdd_coder | no_implementada | CA-11, CA-12 |
| TSK-08 | Chequeo del conjunto de archivos **contra `contract_data.json`** (DS-ING-8): `missing_file` (declarado en el contrato no presente, `status="missing"`, no copia) y `unexpected_file` (presente no declarado en el contrato → `unexpected_files`, no copia); `success=False` si aplica. | `Ingestion` (chequeo de archivos vs. contrato) | tdd_coder | no_implementada | CA-05, CA-06, CA-07 |
| TSK-09 | Validación de columnas **contra `map_client_data.json`** (`_validate_columns`, dataset homólogo por `kind`; DS-ING-8): `missing_column` (requerida ausente), `unexpected_column` (columna no declarada en `fields`), opcional ausente **no** es inconsistencia; `rejected` no se copia. | `Ingestion` (validación columnas vs. mapa) | tdd_coder | no_implementada | CA-08, CA-09, CA-10 |
| TSK-10 | Reporte y summary: `summary` (`datasets_declared`/`files_declared` **derivados del contrato**, DS-ING-8; `files_ingested`/`files_with_inconsistencies`), `inconsistencies[].type` de vocabulario cerrado + `detail`, y `success == (sin inconsistencias)` con reporte escrito siempre. | `Ingestion` (reporte/summary/success) | tdd_coder | no_implementada | CA-16, CA-17, CA-18, CA-19 |
| TSK-11 | Determinismo: serialización JSON `sort_keys=True`+`indent=2`+newline y orden estable (datasets en orden declarado contrato/mapa coherentes, files por contrato, `unexpected_files` alfabético) ⇒ reporte y copias byte-idénticos entre corridas. | `Ingestion` (determinismo) | tdd_coder | no_implementada | CA-13 |
| TSK-12 | Refactor: consolidar/limpiar `ingestion.py` (factorizar helpers de lectura/validación/reporte) y la suite, manteniendo todo verde. | Refactor (sin cambio de comportamiento) | tdd_refactor | no_implementada | CA-01…CA-21 |
| TSK-13 | Test de integración end-to-end (`Ingestion().run(ctx)` sobre el fixture DS-ING-7 completo vía core CONFORME; compara `ingestion_report.json` contra un esperado fijo, verifica copias en bronze byte-idénticas y no-escritura en `silver/`/`gold/`). | `tests/integration/test_ingestion_integration.py` | integration_tester | no_implementada | CA-13, CA-18, CA-11 |

### 4.2 Tareas de test (una por caso del bucle; responsable `tdd_tester`)

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-14 | Helper/fixture DS-ING-7: escribe `contract_data.json` (con `historical_data.datasets[].files[].name`, **fuente de archivos**) + `map_client_data.json` (con `fields[]`, **fuente de columnas**) **coherentes entre sí** bajo `ctx.outputs_dir` y los archivos crudos bajo `ctx.inputs_dir/"030_ingestion"`; construye `ctx` con `create_client` bajo `tmp_path`. Expone helpers de subconjunto/mutación. | fixture DS-ING-7 | tdd_tester | no_implementada | andamiaje (CA-01) |
| TSK-15 | Test caso 1: `run(ctx)` sobre fixture mínimo escribe `ingestion_report.json` en `ctx.outputs_dir/"030_ingestion/ingestion_report.json"` y lo incluye en `FlowResult.outputs`. | test caso 1 | tdd_tester | no_implementada | CA-14 |
| TSK-16 | Test caso 2: `Ingestion` hereda `Flow`, declara `requires=[contract_data, map_client_data]`/`produces=[ingestion_report]` como `Artifact(base="outputs",...)` y completa las 4 fases sin sobreescribir `run`. | test caso 2 | tdd_tester | no_implementada | CA-20 |
| TSK-17 | Test caso 3: para `ventas.csv` (coma) el reporte registra `rows`/`columns` correctos y `separator == ","`. | test caso 3 | tdd_tester | no_implementada | CA-01 |
| TSK-18 | Test caso 4: para `inventario_2024.txt` (`;`) el reporte registra `rows`/`columns` correctos y `separator == ";"`. | test caso 4 | tdd_tester | no_implementada | CA-02 |
| TSK-19 | Test caso 5: para `inventario_2025.csv` (`\|`) el reporte registra `rows`/`columns` correctos y `separator == "\|"`. | test caso 5 | tdd_tester | no_implementada | CA-03 |
| TSK-20 | Test caso 6: para `precios.xlsx` el reporte registra `rows`/`columns` correctos (primera hoja) y `separator == null`. | test caso 6 | tdd_tester | no_implementada | CA-04 |
| TSK-21 | Test caso 7: el reporte expone, por archivo, `name`, `rows` y `columns`. | test caso 7 | tdd_tester | no_implementada | CA-15 |
| TSK-22 | Test caso 8: para cada archivo válido existe en `ctx.bronze_dir/<name>` una copia **byte a byte idéntica** al original del landing. | test caso 8 | tdd_tester | no_implementada | CA-11 |
| TSK-23 | Test caso 9: la copia en bronze conserva formato/separador/extensión (el `\|` sigue `\|`; el `.xlsx` idéntico). | test caso 9 | tdd_tester | no_implementada | CA-12 |
| TSK-24 | Test caso 10: presentes == **declarados en el contrato** ⇒ sin `missing_file`/`unexpected_file`, `unexpected_files == []`, `summary.files_ingested == summary.files_declared`. | test caso 10 | tdd_tester | no_implementada | CA-05 |
| TSK-25 | Test caso 11: archivo **declarado en el contrato** no presente ⇒ `status=="missing"` + `missing_file`; sin copia en `ctx.bronze_dir`; `success == False`. | test caso 11 | tdd_tester | no_implementada | CA-06 |
| TSK-26 | Test caso 12: archivo presente **no declarado en el contrato** ⇒ en `unexpected_files` + `unexpected_file`; no se copia; `success == False`. | test caso 12 | tdd_tester | no_implementada | CA-07 |
| TSK-27 | Test caso 13: archivo sin una columna `required==true` **según el mapa** ⇒ `status=="rejected"` + `missing_column`; no se copia; `success == False`. | test caso 13 | tdd_tester | no_implementada | CA-08 |
| TSK-28 | Test caso 14: archivo con columna no declarada en los `fields` **del mapa** ⇒ `status=="rejected"` + `unexpected_column`; no se copia; `success == False`. | test caso 14 | tdd_tester | no_implementada | CA-09 |
| TSK-29 | Test caso 15: archivo al que le falta una columna `required==false` **según el mapa** (p. ej. `precio_unitario`) ⇒ **no** hay inconsistencia; queda `ingested`. | test caso 15 | tdd_tester | no_implementada | CA-10 |
| TSK-30 | Test caso 16: cada inconsistencia tiene `type` del vocabulario cerrado (`missing_file`/`unexpected_file`/`missing_column`/`unexpected_column`) y un `detail` legible no vacío. | test caso 16 | tdd_tester | no_implementada | CA-16 |
| TSK-31 | Test caso 17: `summary` reporta `datasets_declared`/`files_declared` (**del contrato**, DS-ING-8), `files_ingested`, `files_with_inconsistencies`, coherentes con el detalle por archivo. | test caso 17 | tdd_tester | no_implementada | CA-17 |
| TSK-32 | Test caso 18: `FlowResult.success == True` sii el reporte no registra ninguna inconsistencia; en caso contrario `False` y el reporte se escribe igualmente. | test caso 18 | tdd_tester | no_implementada | CA-19 |
| TSK-33 | Test caso 19: inconsistencia parcial (unos válidos, otro inválido) ⇒ los válidos se copian a `ctx.bronze_dir`, el inválido no; el reporte refleja ambos; `success == False`. | test caso 19 | tdd_tester | no_implementada | CA-18 |
| TSK-34 | Test caso 20: dos `run(ctx)` con las mismas entradas ⇒ `ingestion_report.json` byte-idéntico y copias en bronze byte-idénticas (determinismo). | test caso 20 | tdd_tester | no_implementada | CA-13 |
| TSK-35 | Test caso 21: `contract_data.json` ausente ⇒ `run(ctx)` lanza `FlowContractError` en `validate` (base) antes de tocar bronze; no se escribe `ingestion_report.json` ni copia alguna. | test caso 21 | tdd_tester | no_implementada | CA-21 |
| TSK-36 | Test caso 22: `map_client_data.json` ausente ⇒ `run(ctx)` lanza `FlowContractError` en `validate` (base); no se escribe reporte ni copia alguna. | test caso 22 | tdd_tester | no_implementada | CA-21 |

---

## 5. Estrategia de Test

- **Unit** en `tests/flows/test_ingestion.py`: ejercita `Ingestion` en proceso (sin `subprocess`), rápido y
  determinista. `ClientContext` construido vía `create_client(NAME, tmp_path/"clients")` (core CONFORME). El core
  `Flow`/`ClientContext`/`create_client` **no** se re-testea aquí (suites verdes; NC-3): se usa como fixture.
- **Fixtures / datos de prueba (TSK-14):** el fixture DS-ING-7 (contrato + mapa **coherentes**, DS-ING-8, + 4 archivos
  crudos: `ventas.csv` coma, `inventario_2024.txt` `;`, `inventario_2025.csv` `\|`, `precios.xlsx`) con conteos de
  filas/columnas **conocidos**; los `.csv`/`.txt` se escriben como texto, el `.xlsx` se fabrica con `openpyxl` en el
  propio test. Variantes por mutación puntual (subconjunto mínimo, faltante en contrato, sobrante vs. contrato,
  columna requerida ausente vs. mapa, columna no declarada vs. mapa, opcional ausente, landing vacío).
- **Casos de error de contrato:** `pytest.raises(FlowContractError)` + aserción de que `produces[0].path(ctx)`
  **no** existe y `ctx.bronze_dir` no contiene copias (sin salida parcial).
- **Inconsistencias de datos:** se verifican por aserción sobre `ingestion_report.json` (status/inconsistencies/
  summary/success) y sobre el contenido de `ctx.bronze_dir` — **nunca** con excepción (DS-ING-1).
- **Reparto DS-ING-8:** los casos de conjunto de archivos (10–12) mutan el **contrato**; los de columnas (13–15)
  mutan el archivo respecto a los `fields` **del mapa**. No existe caso de "coherencia mapa↔contrato" (no se chequea).
- **Copia byte a byte (casos 8, 9):** `Path.read_bytes()` del origen vs. destino, y comprobación de extensión.
- **Determinismo (caso 20):** dos `run(ctx)` y comparación byte a byte (`read_bytes()`) del reporte y de las copias.
- **Integración (`integration_tester`, TSK-13):** end-to-end sobre el fixture completo, comparando el
  `ingestion_report.json` producido contra un esperado fijo, verificando copias en bronze byte-idénticas y la
  invariante de no tocar `silver/`/`gold/`.
- **Nota D-037:** algún caso puede resolverse "verde directo" si el código de un caso previo ya lo satisface
  (p. ej. caso 3 tras el caso 1, o caso 7 tras casos 3–6). El bucle lo decide caso a caso; aquí solo se enumeran.

---

## 6. Casos de Test (lista ordenada para el bucle TDD)

Orden: **tracer bullet primero** (camino feliz mínimo end-to-end con un dataset coma que produce el reporte y
copia a bronze), luego los tres separadores restantes + xlsx (endurecimiento de lectura), luego fidelidad de copia,
luego chequeos de conjunto de archivos (contra el **contrato**) y de columnas (contra el **mapa**) — inconsistencias
soft-report —, luego summary/success/parcial, determinismo y, por último, los fallos duros de contrato. Deben
coincidir con `stages.tdd.cases[]` de `state.json`. Cada caso = **un** test que falla primero. Trazabilidad al
`CA-xx` entre paréntesis.

| id | Descripción (verificable) | Tareas (`TSK-xx`) | Trazabilidad → CA |
|---|---|---|---|
| 1 | `run(ctx)` sobre el fixture mínimo (dataset `ventas`/`ventas.csv` coma) escribe `ingestion_report.json` en `ctx.outputs_dir/"030_ingestion/ingestion_report.json"` y lo incluye en `FlowResult.outputs`. | TSK-15, TSK-03, TSK-14 | CA-14 |
| 2 | `Ingestion` hereda `Flow`, declara `requires=[contract_data, map_client_data]`/`produces=[ingestion_report]` y completa las 4 fases sin sobreescribir `run`. | TSK-16, TSK-03, TSK-02 | CA-20 |
| 3 | Para `ventas.csv` (coma) el reporte registra `rows`/`columns` correctos y `separator == ","`. | TSK-17, TSK-03 | CA-01 |
| 4 | Para `inventario_2024.txt` (`;`) el reporte registra `rows`/`columns` correctos y `separator == ";"`. | TSK-18, TSK-04 | CA-02 |
| 5 | Para `inventario_2025.csv` (`\|`) el reporte registra `rows`/`columns` correctos y `separator == "\|"`. | TSK-19, TSK-05 | CA-03 |
| 6 | Para `precios.xlsx` el reporte registra `rows`/`columns` correctos (primera hoja) y `separator == null`. | TSK-20, TSK-06 | CA-04 |
| 7 | El reporte expone, por archivo, `name`, `rows` y `columns`. | TSK-21, TSK-03 | CA-15 |
| 8 | Para cada archivo válido existe en `ctx.bronze_dir/<name>` una copia byte a byte idéntica al original. | TSK-22, TSK-07 | CA-11 |
| 9 | La copia en bronze conserva formato/separador/extensión (el `\|` sigue `\|`; el `.xlsx` idéntico). | TSK-23, TSK-07 | CA-12 |
| 10 | Presentes == **declarados en `contract_data.json`** ⇒ sin `missing_file`/`unexpected_file`, `unexpected_files == []`, `summary.files_ingested == summary.files_declared`. | TSK-24, TSK-08 | CA-05 |
| 11 | Archivo **declarado en `contract_data.json`** no presente ⇒ `status=="missing"` + `missing_file`; sin copia en bronze; `success == False`. | TSK-25, TSK-08 | CA-06 |
| 12 | Archivo presente **no declarado en `contract_data.json`** ⇒ en `unexpected_files` + `unexpected_file`; no se copia; `success == False`. | TSK-26, TSK-08 | CA-07 |
| 13 | Archivo sin una columna `required==true` **según `map_client_data.json`** (dataset homólogo por `kind`) ⇒ `status=="rejected"` + `missing_column`; no se copia; `success == False`. | TSK-27, TSK-09 | CA-08 |
| 14 | Archivo con columna no declarada en los `fields` del dataset homólogo de **`map_client_data.json`** ⇒ `status=="rejected"` + `unexpected_column`; no se copia; `success == False`. | TSK-28, TSK-09 | CA-09 |
| 15 | Archivo al que le falta una columna `required==false` **según `map_client_data.json`** (`precio_unitario`) ⇒ **no** es inconsistencia; queda `ingested`. | TSK-29, TSK-09 | CA-10 |
| 16 | Cada inconsistencia tiene `type` del vocabulario cerrado y un `detail` legible no vacío. | TSK-30, TSK-10 | CA-16 |
| 17 | `summary` reporta `datasets_declared`/`files_declared` (**del contrato**, DS-ING-8)/`files_ingested`/`files_with_inconsistencies` coherentes con el detalle. | TSK-31, TSK-10 | CA-17 |
| 18 | `success == True` sii sin inconsistencias; en caso contrario `False` y el reporte se escribe igualmente. | TSK-32, TSK-10 | CA-19 |
| 19 | Inconsistencia parcial (3 válidos, 1 inválido) ⇒ los válidos se copian, el inválido no; reporte refleja ambos; `success == False`. | TSK-33, TSK-08, TSK-09 | CA-18 |
| 20 | Dos `run(ctx)` con las mismas entradas ⇒ `ingestion_report.json` y copias en bronze byte-idénticos. | TSK-34, TSK-11 | CA-13 |
| 21 | `contract_data.json` ausente ⇒ `FlowContractError` en `validate` (base); sin reporte ni copia. | TSK-35, TSK-03 | CA-21 |
| 22 | `map_client_data.json` ausente ⇒ `FlowContractError` en `validate` (base); sin reporte ni copia. | TSK-36, TSK-03 | CA-21 |

### Cobertura CA → caso (los 21 CA quedan cubiertos)

| CA | Caso | CA | Caso | CA | Caso |
|---|---|---|---|---|---|
| CA-01 | 3 | CA-08 | 13 | CA-15 | 7 |
| CA-02 | 4 | CA-09 | 14 | CA-16 | 16 |
| CA-03 | 5 | CA-10 | 15 | CA-17 | 17 |
| CA-04 | 6 | CA-11 | 8 | CA-18 | 19 |
| CA-05 | 10 | CA-12 | 9 | CA-19 | 18 |
| CA-06 | 11 | CA-13 | 20 | CA-20 | 2 |
| CA-07 | 12 | CA-14 | 1 | CA-21 | 21, 22 |

---

## 7. Notas y Riesgos (NC-1 / NC-6)

- **Sin puntos abiertos que bloqueen el GATE:** las decisiones de la spec (DS-ING-1…8) fueron **aprobadas por el
  humano**, incluidas las dos que estaban marcadas discutibles (landing en `010_inputs/030_ingestion/` reutilizando
  `base="inputs"` y `openpyxl` como dependencia) y el reparto **DS-ING-8**. Este re-plan las **materializa** sin
  reabrir ninguna: **no introduce ninguna decisión nueva** que requiera GATE. La aprobación humana pendiente es la de
  este plan como artefacto.
- **DS-ING-8 (reparto contrato/mapa, ya aprobado):** sustituye la aclaración previa de este plan ("la fuente de
  expectativas es solo `map_client_data.json`"). Ahora **`contract_data.json` = archivos esperados**
  (`historical_data.datasets[].files[].name`, `datasets[]`) y **`map_client_data.json` = columnas esperadas**
  (`fields[]`), emparejando dataset por `kind`, **sin** chequeo de coherencia mapa↔contrato. El fixture mantiene ambos
  coherentes, por lo que el resultado del caso feliz no cambia; lo que cambia es **de qué artefacto** se deriva cada
  expectativa (relevante para las variantes de los casos 10–15 y para `summary`, casos 17).
- **Detección de separador (DP, NC-6):** entre `,`/`;`/`|` se elige el de **mayor** número de ocurrencias en la
  cabecera. El fixture no tiene empates ni archivos de una sola columna; el caso de archivo sin separador (columna
  única) queda **fuera de alcance** de esta banda y se difiere a `stab_1`.
- **`openpyxl` ya instalado (`3.1.5`):** los tests xlsx corren en este entorno. En un entorno limpio se instala con
  `pip install -e .` tras `pyproject.toml` (acción de entorno, no de código; no bloquea el bucle).
- **NC-3 (quirúrgico):** no se toca `flow.py`/`context.py`/`scaffold.py` ni se amplía `ClientContext`/`Artifact`.
  Si durante el bucle apareciera la necesidad de modificar el core, se **detiene** y se consulta (NC-6): no se asume.
- **Alcance diferido a `stab_1`** (spec, No-Objetivos): comparación contra `client_register`, medios `database`/`api`,
  validación de **tipos** de columna, profiling/cleaning, descargables del reporte, `kind` no ejercitados y
  combinaciones separador×extensión redundantes. Fuera de esta banda (NC-2).
