# Definition — ingestion

> Artefacto de la etapa 1 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `ingestion` (snake_case)
- **Banda:** `tracer_bullet` (D-019; celda = feature × banda)
- **Componente / flujo:** 030 Ingestion (`system_design.md` §5, §6, §8, §10, §15). Sigue a Onboarding (020) en el camino "cliente nuevo" (§12). Hereda de `Flow` (`flow_base`, CONFORME) y consume `ClientContext` (`client_context`, CONFORME).

## Problema / Necesidad
Onboarding (020) ya traduce `contract_data.json` en un mapa canónico (`map_client_data.json`), pero ningún componente ha tocado todavía los **datos reales** del cliente. Antes de que Profiling (040) pueda calcular la salud de los datos, o Cleaning (050) pueda limpiarlos, alguien tiene que: (a) cargar los archivos crudos históricos (csv/txt/xlsx) que el cliente entregó, (b) verificar de forma determinista que coinciden en número y estructura con lo que el contrato/mapa declaran, y (c) si son correctos, dejar una copia **inmutable** de esos datos en la capa bronze, para que ningún flujo posterior pueda alterar el original y cualquier reproceso pueda partir siempre de la misma fuente fiel. Sin Ingestion, no existe ese punto único, auditado y determinista de entrada de datos reales al sistema; cada flujo downstream tendría que leer y validar los archivos crudos por su cuenta, duplicando lógica y arriesgando que bronze no sea realmente una copia fiel del original. Ingestion resuelve esto de forma determinista (§6), sin usar LLM y sin transformar los datos (eso es Cleaning, no Ingestion).

## Alcance

**In scope (banda `tracer_bullet`):**
- Un `Flow` concreto `Ingestion` (hereda de `flow_base`) que:
  1. Declara como `requires`: `contract_data.json` (`020_outputs/010_discovery/`), `map_client_data.json` (`020_outputs/020_onboarding/`), y los archivos de datos crudos del cliente.
  2. Declara como `produces`: la copia inmutable en `data/bronze/` y el reporte de carga JSON en `020_outputs/030_ingestion/`.
  3. Completa las 4 fases del template method de `Flow` (`load_inputs → validate → execute → write_outputs`).
- Formatos de entrada soportados: **CSV**, **TXT** y **Excel (`.xlsx`)**. Los archivos delimitados (csv/txt) deben soportarse con separador **coma (`,`)**, **punto y coma (`;`)** o **barra vertical (`|`)**.
- Validación, antes de copiar a bronze:
  a. **Número de archivos:** los archivos históricos presentes coinciden con los declarados en `contract_data.json` (`historical_data.datasets[].files[]`), re-confirmados por `map_client_data.json`.
  b. **Columnas esperadas:** cada archivo tiene las columnas/estructura declaradas en `map_client_data.json` (esquema por dataset derivado de los `fields` del contrato).
- Copia inmutable de los archivos válidos a `clients/<CLIENTE>/data/bronze/`, fiel al original (sin transformación).
- Reporte de carga (JSON) en `020_outputs/030_ingestion/` que informa, como mínimo: archivos cargados, número de filas y columnas cargadas por archivo, e inconsistencias detectadas.
- Fixtures fabricados por esta banda (análogo a D-055 en Onboarding): un `contract_data.json` y un `map_client_data.json` coherentes entre sí (alineados con el esquema ya acordado en `onboarding`), más los archivos de datos reales (csv/txt/xlsx, ejercitando los tres separadores) a ingerir.

**Out of scope (esta banda; puede o no llegar en `stab_1`):**
- Discovery (010) real y comparación contra `client_register` (aún no existe ese artefacto; la validación queda diferida a una banda futura).
- Medios `database` y `api` (el vocabulario `source_medium` del contrato los admite, pero no se implementa lectura de esos medios en esta banda).
- Profiling (040): calcular salud de los datos (faltantes, duplicados, periodicidad, pareto) NO es responsabilidad de Ingestion.
- Cleaning (050): limpieza/transformación de datos; bronze es copia fiel e inalterable, nunca se modifica.
- Uso de LLM (Ingestion es determinista, §6).
- Validación de **tipos de dato** de las columnas (más allá de su presencia/nombre) — ver supuesto abierto abajo.
- Descargables (export csv/xlsx) del reporte de carga.

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como **flujo downstream (Profiling/Cleaning)**, quiero que Ingestion cargue los archivos crudos csv/txt/xlsx del cliente detectando correctamente el separador (coma, punto y coma o barra vertical) en los delimitados, para poder confiar en que el contenido se leyó de forma completa y correcta. | Para el fixture acordado, Ingestion lee correctamente al menos un archivo por cada combinación de formato/separador ejercitada (csv coma, csv/txt punto y coma, csv/txt barra vertical, xlsx), sin pérdida ni corrupción de filas/columnas. |
| HU-02 | Como **operador del harness**, quiero que Ingestion verifique que el número de archivos históricos presentes coincide con los declarados en `contract_data.json`/`map_client_data.json` antes de tocar bronze, para detectar archivos faltantes o sobrantes temprano. | Ante un conjunto de archivos crudos con un archivo faltante o uno sobrante respecto al contrato, Ingestion detecta y reporta la inconsistencia, sin copiar a bronze el dataset afectado. |
| HU-03 | Como **operador del harness**, quiero que Ingestion verifique que cada archivo tiene las columnas/estructura declaradas en `map_client_data.json` antes de copiarlo a bronze, para detectar archivos con esquema incorrecto temprano. | Ante un archivo con una columna faltante o con nombre distinto al esperado, Ingestion detecta y reporta la inconsistencia, sin copiar ese archivo a bronze. |
| HU-04 | Como **científico de datos (DS)**, quiero que los archivos válidos se copien de forma fiel e inmutable a `bronze/`, para tener siempre una fuente original intacta desde la cual reprocesar sin depender de la carpeta de origen del cliente. | Para el fixture acordado, los archivos válidos aparecen en `clients/<CLIENTE>/data/bronze/` con contenido idéntico al original (mismas filas/columnas/valores), sin ninguna transformación. |
| HU-05 | Como **científico de datos (DS)**, quiero un reporte de carga en JSON con los archivos cargados, filas/columnas por archivo e inconsistencias detectadas, para poder revisar de un vistazo qué se cargó y corregir el origen de datos si hay errores. | El reporte de carga (`020_outputs/030_ingestion/`) generado para el fixture lista, por archivo, su nombre, número de filas, número de columnas, y —si aplica— la(s) inconsistencia(s) detectada(s) en un formato legible. |
| HU-06 | Como **desarrollador del harness**, quiero que `Ingestion` se integre como un `Flow` concreto sobre `ClientContext`, para reutilizar la orquestación y resolución de rutas ya construidas en `flow_base`/`client_context`. | `Ingestion` hereda de `Flow`, declara `requires`/`produces` como `Artifact`, y su `run(ctx)` completa las 4 fases del template method sin reimplementar orquestación propia. |

## Dependencias
- `flow_base` (banda `tracer_bullet`, **CONFORME**): clase base `Flow`, `FlowResult`, `Artifact`, `FlowContractError` (`src/foda/core/flow.py`).
- `client_context` (banda `tracer_bullet`, **CONFORME**): `ClientContext` (`src/foda/core/context.py`), incluye `bronze_dir`.
- `onboarding` (banda `tracer_bullet`, **CONFORME**): produce `map_client_data.json`; su fixture de `contract_data.json` (`600_features/onboarding/tracer_bullet/definition.md`, sección "Contrato de datos") se reutiliza/alinea aquí para mantener consistencia entre features.
- `700_architecture/system_design.md` §5 (modelo de flujos), §6 (determinismo), §7 (estructura de carpetas), §8 (contrato de artefactos), §10 (capas medallion), §15 (detalle 030 Ingestion).
- `800_persistence/decisions.md`: decisiones vigentes de `flow_base`, `client_context` y `onboarding` (D-047..D-067).

## Riesgos y Supuestos
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** el formato exacto del reporte de carga (nombres de claves, estructura anidada) no está fijado por `system_design.md` más allá de "reporte de carga"; queda a `spec_writer`/`plan_builder` proponerlo explícitamente, respetando NC-2 y cubriendo como mínimo lo listado en HU-05.
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** el tipo de excepción/mecanismo a usar para reportar inconsistencias (¿se reutiliza `FlowContractError` de `flow_base`, se define una excepción propia de Ingestion, o las inconsistencias se acumulan en el reporte de carga sin levantar excepción y el flujo continúa con los datasets válidos?) no está decidido; queda a `spec_writer`/`plan_builder` definirlo explícitamente (NC-6).
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** el alcance de la validación de columnas se limita en esta banda a **presencia/nombre** de columnas (no tipos de dato); `spec_writer` debe confirmar esta interpretación o ajustarla si el humano decide lo contrario.
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** de dónde salen físicamente los archivos crudos de entrada del fixture. `clients/` está hoy vacío (no hay cliente físico ni carpeta de "landing"/staging definida en `system_design.md` para depositar los archivos crudos antes de ingerir). `spec_writer`/`plan_builder` deben definir explícitamente esa ubicación de origen (p. ej. una carpeta de staging bajo el fixture de test, distinta de `bronze/`) antes de implementar.
- **Supuesto:** el comportamiento ante una inconsistencia parcial (p. ej. 2 de 3 datasets son válidos, 1 no) — si Ingestion copia a bronze los datasets válidos y solo reporta el/los inválido(s), o si aborta todo el flujo ante cualquier inconsistencia — no está decidido; queda a `spec_writer`/`plan_builder` definirlo explícitamente (NC-6).
- **Aclaración de dominio (no es ambigüedad, para que `spec_writer` no la confunda):** Ingestion NO calcula salud de los datos (eso es Profiling, 040) ni limpia/transforma (eso es Cleaning, 050); bronze es una copia fiel e inalterable del original.
- **Riesgo:** la comparación contra `client_register` (mencionada en `system_design.md` §15 para Ingestion) queda diferida porque ese artefacto de Discovery (010) aún no existe; se revisará en `stab_1` cuando Discovery se construya.
- **Riesgo:** el fixture de esta banda debe ejercitar csv, txt y xlsx con los tres separadores para delimitados; si alguna combinación resulta redundante o inviable de fabricar, `spec_writer`/`plan_builder` deben documentar explícitamente cuál se omite y por qué (NC-6), en vez de omitirla en silencio.
- **Riesgo:** el negocio predice demanda de productos, no ventas; el fixture debe, como en Onboarding, incluir al menos un `kind` de dataset distinto de "ventas" (p. ej. inventario) para no sesgar la validación hacia un único tipo de dataset.
