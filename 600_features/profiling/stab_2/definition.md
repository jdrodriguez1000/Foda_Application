# Definition — profiling (banda `stab_2`)

> Artefacto de la etapa 1 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `profiling` (snake_case)
- **Banda:** `stab_2` (D-019; celda = feature × banda)
- **Componente / flujo:** 040 Profiling (`system_design.md` §5, §6, §8, §10, §15). Endurece la banda `stab_1` (**CONFORME**, cerrada en `main`, merge `754d931`), que calculó la salud **estructural** del ingreso usando **únicamente** `ingestion_report.json` (sin leer `bronze/`). Esta banda le da a `Profiling` su primera lectura del **contenido** de los datos.

## Problema / Necesidad
`stab_1` cerró el análisis "de metadatos" (qué archivos/columnas llegaron según lo que `Ingestion` ya reportó), pero deliberadamente no leyó el contenido de `bronze/`: no sabe si hay celdas vacías, filas repetidas o valores "trampa" (centinela) que contaminan el dato. Tras cerrar `stab_1` en `main`, el humano decidió (`D-097`) repartir ese endurecimiento pendiente en dos bandas: `stab_2` = **"defectos con score"** (esta banda: nulos, duplicados, centinelas — defectos inequívocos que SÍ penalizan el score) y `stab_3` = **"perfil diagnóstico por columna"** (informativo, NO penaliza el score — diferido, backlog T-041).

El principio transversal que rige esta separación es `D-098`: solo los defectos **inequívocos** (esta banda) alimentan `global_score`; los hallazgos **ambiguos** (outliers, dominancia categórica — `stab_3`) solo se reportan.

Como el `global_score` de `stab_1` es de una sola dimensión (denominador: archivos) y no es commensurable con conteos a nivel de celda/fila, esta banda también **rediseña `global_score`** a un modelo multi-dimensión (`D-099`): media ponderada de 4 sub-scores normalizados a [0,1], cada uno con su propio denominador natural.

## Alcance

**In scope (banda `stab_2`):**
- **Primera lectura del contenido de `bronze/`** (a diferencia de `stab_1`, que solo leía `ingestion_report.json`): Profiling abre los datasets ya cargados por Ingestion para auditarlos, sin modificarlos (solo lectura, consistente con la Estrella Polar de la feature).
- **Detección de valores faltantes/nulos**: conteo de celdas nulas sobre el total de celdas, para derivar `completeness_score`.
- **Detección de filas duplicadas**: conteo de filas duplicadas sobre el total de filas, para derivar `uniqueness_score`.
- **Detección de valores centinela**: comparación determinista contra un catálogo de tokens (p. ej. `-999`, `"N/A"`, `9999-12-31`) para derivar `validity_score`.
- **Nuevo artefacto de configuración por cliente `profiling_config.yaml`** (`D-100`): archivo propio (NO dentro de `client.yaml`), con las cajas `numeric`, `non_numeric` (incluye fechas límite tipo `1900-01-01`/`9999-12-31`) y `boolean`. Si el cliente no lo define, Profiling corre igual con catálogo vacío (comportamiento seguro por defecto: `validity_score = 1.0`, sin falsos positivos).
- **Rediseño de `global_score` a modelo multi-dimensión** (`D-099`): media ponderada de 4 sub-scores normalizados a [0,1]:
  - `structural_score`: el `global_score` de `stab_1` (denom: archivos), reinterpretado como una dimensión más (cambia de significado respecto a `stab_1`, debe documentarse explícitamente).
  - `completeness_score` = 1 − celdas_nulas / celdas_totales.
  - `validity_score` = 1 − celdas_centinela / celdas_totales.
  - `uniqueness_score` = 1 − filas_duplicadas / filas_totales.
  - `global_score` = Σ(peso_dimensión × sub_score). **Los pesos exactos y su exposición en la spec quedan pendientes de definición en el GATE de `spec_writer`** (punto de partida igualitario, ver A-021).
- **Enriquecimiento de `profiling_report.json`**: bloque `health` rediseñado (los 4 sub-scores + `global_score` recompuesto) más nuevos bloques que reporten el detalle de los defectos detectados a nivel de celda/fila (nulos, duplicados, centinelas) — la forma exacta de esos bloques queda para `spec_writer`.
- Bump de `schema_version` (valor exacto a fijar por `spec_writer`, siguiendo el patrón aditivo de `stab_1`: `"0.1"` → `"0.2"`).
- Determinismo byte a byte del `profiling_report.json` enriquecido (mismas entradas ⇒ mismo reporte), consistente con `stab_1` y con `system_design.md` §6.

**Out of scope (esta banda; diferido explícitamente):**
- **Perfil diagnóstico por columna** (categórico: distribución/dominancia, columnas constantes, cardinalidad, candidatos a casi-duplicado; numérico: min/max/media/mediana/cuartiles + atípicos): diferido a `stab_3` (`D-097`, `D-101`, `D-102`). Es informativo, no penaliza el score (`D-098`).
- **Comparación contra `client_register.yaml`** real (Discovery real aún no existe como artefacto con datos).
- **Exportables csv/xlsx** (`foda export --flow profiling`).
- **Uso de LLM** (Profiling es determinista, `system_design.md` §6). En particular, la detección de centinelas es por catálogo de tokens, no por inferencia semántica.
- **Corrección/limpieza de los defectos detectados**: Profiling audita y señala, nunca corrige (`D-101`); la corrección es responsabilidad de Cleaning (050).
- El gate de progresión `D-080` (puntos 1-3), ya implementado en `tracer_bullet`: esta banda no lo modifica.

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como **DS (data scientist) que va a limpiar los datos (050)**, quiero un `global_score` que combine salud estructural, completitud, validez y unicidad en un solo indicador, para saber de un vistazo qué tan confiable es el contenido del dato, no solo su estructura. | Dado un cliente con datos en `bronze/`, `profiling_report.json` incluye en `health.global_score` una media ponderada determinista de los 4 sub-scores (`structural_score`, `completeness_score`, `validity_score`, `uniqueness_score`), cada uno en [0,1], calculada según la fórmula que fije `spec_writer` en el GATE. |
| HU-02 | Como **DS**, quiero saber qué proporción de celdas están vacías/nulas, para dimensionar el esfuerzo de imputación antes de `cleaning`. | `profiling_report.json` reporta el conteo de celdas nulas y el `completeness_score` derivado (1 − celdas_nulas/celdas_totales), coherente con el contenido real de `bronze/`. |
| HU-03 | Como **DS**, quiero saber cuántas filas están duplicadas, para decidir si deduplicar antes de análisis posteriores. | `profiling_report.json` reporta el conteo de filas duplicadas y el `uniqueness_score` derivado (1 − filas_duplicadas/filas_totales), coherente con el contenido real de `bronze/`. |
| HU-04 | Como **DS**, quiero que Profiling detecte valores centinela (p. ej. `-999`, `"N/A"`) usando el catálogo propio de mi cliente, para no confundir esos valores "trampa" con datos válidos en análisis posteriores. | `profiling_report.json` reporta el conteo de celdas con valor centinela y el `validity_score` derivado, usando el catálogo de `profiling_config.yaml` del cliente (o catálogo vacío, `validity_score == 1.0`, si el cliente no define el archivo). |
| HU-05 | Como **administrador de un cliente**, quiero poder declarar en un archivo propio (`profiling_config.yaml`) los valores centinela específicos de mis datos, para que Profiling los detecte sin necesitar cambios de código por cliente. | Existe un artefacto `profiling_config.yaml` por cliente con las cajas `numeric`/`non_numeric`/`boolean`; si el archivo no existe, Profiling corre igual (comportamiento seguro por defecto, sin fallar). |
| HU-06 | Como **operador/flujo downstream del harness**, quiero que el `profiling_report.json` enriquecido siga siendo un artefacto versionado y determinista, para poder consumirlo de forma confiable en integraciones futuras (`stab_3`, exportables, `cleaning`, evaluación offline). | `profiling_report.json` declara un `schema_version` bumpeado de forma aditiva, conserva los campos de identidad y el bloque `health` ya existentes de `stab_1` (reinterpretando `structural_score` según corresponda), y dos ejecuciones con las mismas entradas producen el mismo reporte byte a byte. |

## Dependencias
- `profiling` (banda `stab_1`, **CONFORME**, cerrada en `main`, merge `754d931`): `Flow` concreto `Profiling`, bloque `health` con `global_score` estructural (`src/foda/flows/f040_profiling/profiling.py`), que esta banda reinterpreta como `structural_score` dentro del nuevo modelo multi-dimensión.
- `ingestion` (banda `tracer_bullet`, **CONFORME**): produce `ingestion_report.json` y la copia inmutable en `bronze/` que esta banda audita por primera vez a nivel de contenido.
- `flow_base` / `client_context` (banda `tracer_bullet`, **CONFORME**): infraestructura de `Flow`/`ClientContext`, sin cambios.
- `700_architecture/system_design.md` §6 (determinismo), §8 (contrato de artefactos), §10 (capas medallion, `bronze` inalterable por Triple S), §15 (detalle 040 Profiling).
- `800_persistence/decisions.md`: `D-088`/`D-089` (alcance base `stab_1`), `D-097` (reparto de bandas `stab_2`/`stab_3`), `D-098` (principio "defectos con score" vs. "perfil diagnóstico"), `D-099` (modelo multi-dimensión del `global_score`), `D-100` (`profiling_config.yaml`), `D-080` (gate de progresión, ya implementado, no se toca aquí).

## Riesgos y Supuestos
- **A-020 (supuesto abierto, NO decidido en silencio, NC-6):** leer el contenido de `bronze/` (nulos, duplicados, centinelas) requiere una librería de manejo tabular; `pandas` es la candidata natural (ya usada en el ecosistema Python de análisis de datos y coherente con el resto del harness), pero **no ha sido confirmada explícitamente** como dependencia para esta banda. `spec_writer`/`plan_builder` deben decidirlo explícitamente y dejarlo documentado (no asumirlo).
- **A-021 (supuesto abierto, NO decidido en silencio, NC-6):** los pesos de la media ponderada de `global_score` (`D-099`) se asumen **igualitarios** (25% cada sub-score) como punto de partida, pendientes de afinar con datos reales; `spec_writer` debe fijar el valor exacto (o dejarlo configurable) y documentarlo explícitamente en el GATE, no asumirlo tácitamente.
- **Pendiente de definición explícita para el GATE de `spec_writer` (no se resuelve aquí, NC-6):**
  1. Fórmula exacta y pesos de la media ponderada de `global_score` (ver A-021).
  2. Forma exacta de los nuevos bloques del reporte que documentan nulos/duplicados/centinelas (nombres de claves, si van dentro de `health` o en bloques hermanos nuevos).
  3. Valor exacto del nuevo `schema_version` (se asume bump aditivo desde `"0.2"`, siguiendo el patrón de `stab_1`, pero el valor final lo fija `spec_writer`).
  4. Formato exacto y ubicación de `profiling_config.yaml` dentro de la estructura de carpetas por cliente (`010_inputs`/`020_outputs`, `system_design.md` §9).
  5. Confirmación de `pandas` como dependencia (ver A-020).
- **Aclaración de dominio (no es ambigüedad, para que `spec_writer` no la confunda):** esta banda lee el **contenido** de `bronze/` por primera vez, pero **nunca lo modifica** (Profiling sigue siendo de solo lectura/auditoría, `feature_contract.md`); la corrección de nulos/duplicados/centinelas es responsabilidad de Cleaning (050). El perfil diagnóstico por columna (categórico/numérico, atípicos) es explícitamente `stab_3`, no esta banda.
- **Riesgo:** el catálogo de valores centinela de `profiling_config.yaml` es determinista por tokens exactos, no por inferencia; si el cliente usa variantes no catalogadas (p. ej. `-999.0` vs `-999`), esos casos no se detectarán como centinela en esta banda (posible refinamiento futuro, no se aborda aquí).
- **Riesgo:** el cambio de significado de `structural_score` (antes `global_score` único de `stab_1`) puede confundir a consumidores que ya integraron el reporte de `stab_1`; debe documentarse claramente el mapeo en `spec.md` (mismo tipo de riesgo ya identificado y aceptado en `stab_1` respecto a `tracer_bullet`).
