# Definition — profiling (banda `stab_1`)

> Artefacto de la etapa 1 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `profiling` (snake_case)
- **Banda:** `stab_1` (D-019; celda = feature × banda)
- **Componente / flujo:** 040 Profiling (`system_design.md` §5, §6, §8, §10, §15). Endurece la banda `tracer_bullet` (CONFORME, mergeada en `main`), que dejó `Profiling` como `Flow` concreto que escribe un `profiling_report.json` mínimo (`{success}`) y aloja el gate de progresión `D-080`. Esta banda le da a `Profiling` su primer valor analítico real.

## Problema / Necesidad
La banda `tracer_bullet` de `profiling` es deliberadamente hueca: produce un `profiling_report.json` con un único campo `success`, sin calcular nada sobre la salud de los datos que Ingestion (030) cargó. Tras cerrar `tracer_bullet` en `main` (`D-087`), el humano evaluó las bifurcaciones disponibles (profundidad sobre `profiling`, amplitud hacia `cleaning`, núcleo LLM en `discovery`, o consolidación) y eligió **profundidad** (`D-088`): construir el primer valor analítico tangible y determinista del proyecto, dando además terreno concreto para un futuro bucle de evaluación offline.

Dentro de "profundidad", se acotó el alcance a la **Opción A** (`D-089`, de 3 presentadas al humano): calcular la salud **ESTRUCTURAL** del ingreso de datos usando **únicamente** `ingestion_report.json` como fuente — sin leer el contenido de `bronze/` (eso es "salud a nivel de datos/celda": nulos, duplicados, tipos, rangos), sin comparar contra `client_register.yaml` (Discovery real aún no existe) y sin exportables ni LLM. Esta banda responde, pues, a la pregunta: *dado lo que `Ingestion` ya reportó sobre archivos y columnas esperados/presentes, ¿qué tan sana está estructuralmente la carga de un cliente?*

## Alcance

**In scope (banda `stab_1`):**
- Cálculo de la salud **ESTRUCTURAL** del ingreso, derivada **exclusivamente** de `ingestion_report.json` (ningún acceso a `bronze/` ni a los archivos crudos del cliente).
- Un indicador `global_score` (número que resume la salud estructural global). **La fórmula exacta queda pendiente de definición en el GATE de `spec_writer`** (`D-089`), no se fija en esta etapa.
- Conteos: número de archivos declarados (`files_declared`), archivos sanos (`files_healthy`) y archivos con problemas (`files_with_problems`), derivados de `ingestion_report.json`.
- Desglose `problems_by_type`: agrupación de los problemas detectados por `Ingestion` según su tipo (vocabulario cerrado ya existente en `ingestion_report.json`: `missing_file`, `unexpected_file`, `missing_column`, `unexpected_column`).
- Ranking `pareto`: los tipos de problema (o, según decida `spec_writer`, los archivos/datasets) ordenados por frecuencia, para identificar rápidamente dónde se concentran los problemas.
- Enriquecimiento de `profiling_report.json`: se añade un nuevo bloque `health` que contiene `global_score`, los conteos, `problems_by_type` y `pareto`.
- Actualización de `schema_version` del reporte de `"0.1"` a `"0.2"` (bump aditivo: el bloque `health` es nuevo, los campos de identidad ya existentes de `tracer_bullet` — `client`, `flow`, `success` — se conservan).
- Determinismo byte a byte del `profiling_report.json` enriquecido (mismas entradas ⇒ mismo reporte), consistente con el resto del harness (§6 `system_design.md`).

**Out of scope (esta banda; diferido explícitamente):**
- **Salud a nivel de datos/celda**: lectura del contenido de `bronze/` (nulos, duplicados, tipos, rangos, inconsistencias temporales, periodicidad menor a la mínima calculada sobre datos reales). Diferido a `stab_2` (`D-089`).
- **Comparación contra `client_register.yaml`** real (Discovery real aún no existe como artefacto con datos).
- **Exportables csv/xlsx** (`foda export --flow profiling`).
- **Uso de LLM** (Profiling es determinista, `system_design.md` §6).
- El gate de progresión `D-080` (puntos 1-3) ya implementado en `tracer_bullet`: esta banda no lo modifica, solo se apoya en su resultado (`ingestion_report.json` con `success`) como fuente de datos.

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como **DS (data scientist) que va a limpiar los datos (050)**, quiero un indicador único `global_score` que resuma la salud estructural del ingreso de un cliente, para saber de un vistazo qué tan confiable fue la carga antes de invertir tiempo en `cleaning`. | Dado un `ingestion_report.json` de un cliente, `profiling_report.json` incluye en `health.global_score` un valor numérico determinista, calculado según la fórmula que fije `spec_writer` en el GATE. |
| HU-02 | Como **DS**, quiero conocer cuántos archivos fueron declarados, cuántos llegaron sanos y cuántos tuvieron problemas, para dimensionar el tamaño del esfuerzo de limpieza. | `profiling_report.json` incluye en `health` los conteos `files_declared`, `files_healthy` y `files_with_problems`, coherentes entre sí y con el detalle de `ingestion_report.json`. |
| HU-03 | Como **DS**, quiero ver los problemas del ingreso agrupados por tipo, para identificar patrones sistemáticos (p. ej. si predominan columnas faltantes vs. archivos faltantes). | `profiling_report.json` incluye en `health.problems_by_type` el conteo de problemas por cada tipo del vocabulario cerrado de `ingestion_report.json` (`missing_file`, `unexpected_file`, `missing_column`, `unexpected_column`), coherente con las inconsistencias reportadas por `Ingestion`. |
| HU-04 | Como **DS**, quiero un ranking de los problemas más frecuentes (pareto), para priorizar qué atacar primero en `cleaning`. | `profiling_report.json` incluye en `health.pareto` una lista ordenada de forma determinista por frecuencia descendente, sin pérdida de información respecto a `problems_by_type`. |
| HU-05 | Como **operador/flujo downstream del harness**, quiero que el `profiling_report.json` enriquecido siga siendo un artefacto versionado y determinista, para poder consumirlo de forma confiable en integraciones futuras (exportables, `cleaning`, evaluación offline). | `profiling_report.json` declara `schema_version == "0.2"`, conserva los campos de identidad ya existentes (`client`, `flow`, `success`) junto al nuevo bloque `health`, y dos ejecuciones con las mismas entradas producen el mismo reporte byte a byte. |

## Dependencias
- `profiling` (banda `tracer_bullet`, **CONFORME**, mergeada en `main`): `Flow` concreto `Profiling`, gate de progresión `D-080`, y el `profiling_report.json` mínimo (`schema_version:"0.1"`, `client`, `flow`, `success`) que esta banda enriquece (`src/foda/flows/f040_profiling/profiling.py`, si ese es el módulo — confirmar ubicación exacta en `spec_writer`/`plan_builder`).
- `ingestion` (banda `tracer_bullet`, **CONFORME**): produce `ingestion_report.json`, única fuente de esta banda. En particular su lista top-level `inconsistencies[]` (`{type, detail}`, vocabulario cerrado de 4 tipos) y su `summary` (`files_declared`, `files_ingested`, `files_with_inconsistencies`, etc., ver `600_features/ingestion/tracer_bullet/spec.md` §DS-ING-2/DS-ING-9).
- `flow_base` / `client_context` (banda `tracer_bullet`, **CONFORME**): infraestructura de `Flow`/`ClientContext` ya usada por `Profiling`, sin cambios.
- `700_architecture/system_design.md` §6 (determinismo), §8 (contrato de artefactos), §10 (capas medallion), §15 (detalle 040 Profiling).
- `800_persistence/decisions.md`: `D-088` (elección de profundidad sobre `profiling`), `D-089` (alcance base de esta banda: Opción A, salud estructural), `D-080` (gate de progresión, ya implementado, no se toca aquí).

## Riesgos y Supuestos
- **Pendiente de definición explícita para el GATE de `spec_writer` (`D-089`, ya identificado, no se resuelve aquí):**
  1. **Fórmula exacta de `global_score`** (qué peso tiene cada tipo de problema, si es puramente proporcional a `files_healthy/files_declared` o pondera por severidad de tipo de problema, rango 0–100 o 0.0–1.0).
  2. **Comportamiento cuando `ingestion_report.success == false`**: ¿la salud estructural se calcula igual (reflejando fielmente los problemas detectados) o se "degrada" adicionalmente por el solo hecho de que `ingestion` marcó fallo global?
  3. **Definición precisa de "archivo sano"** (¿un archivo con `status == "ingested"` y sin ninguna inconsistencia asociada, o basta con no estar en `missing`/`rejected`?), necesaria para calcular `files_healthy` de forma inequívoca.
  4. **Composición exacta de `pareto`**: ¿ranking sobre los 4 tipos de problema (`problems_by_type`) o sobre archivos/datasets individuales con problemas? `D-089` menciona "ranking por frecuencia con count y pct" pero no fija la unidad de agrupación (tipo vs. archivo); `spec_writer` debe decidirlo y documentarlo (NC-6).
- **Aclaración de dominio (no es ambigüedad, para que `spec_writer` no la confunda):** esta banda **no** lee `bronze/`, **no** compara contra `client_register.yaml`, **no** exporta csv/xlsx y **no** usa LLM; eso es explícitamente `stab_2` o una banda/feature posterior. El propósito único de esta banda es calcular salud **estructural** (a partir de metadatos ya producidos por `ingestion`) y enriquecer el reporte existente.
- **Riesgo:** el vocabulario cerrado de 4 tipos de problema (`missing_file`, `unexpected_file`, `missing_column`, `unexpected_column`) proviene de `ingestion` (banda `tracer_bullet` de esa feature); si ese vocabulario cambia en una banda futura de `ingestion`, `problems_by_type`/`pareto` de esta banda tendrían que revisarse (no se aborda aquí).
- **Riesgo:** el bump de `schema_version` a `"0.2"` es aditivo (no elimina campos existentes), pero cualquier consumidor externo del `profiling_report.json` de `tracer_bullet` que asuma `schema_version == "0.1"` de forma estricta debería revisarse; no se conocen tales consumidores hoy (el reporte solo se ha consumido en tests).
