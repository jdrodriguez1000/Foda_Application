# Feature Contract — ingestion

> Artefacto **a nivel feature** (por encima de las bandas), creado por `feature_definer` en el paso *Definir*.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de iniciar la primera banda** (`D-030`).
> **Una feature tiene un solo `feature_contract`**, aunque recorra varias bandas (`tracer_bullet → stab_n`).

## Estrella Polar
El flujo **030 Ingestion** carga de forma determinista los archivos de datos crudos históricos del cliente (csv/txt/xlsx), los valida contra la estructura declarada en `contract_data.json`/`map_client_data.json` y, si son correctos, los copia de forma **inmutable** a la capa **bronze**, produciendo un **reporte de carga** que informa qué se cargó y qué inconsistencias se detectaron — siendo el primer flujo del pipeline que toca datos reales del cliente (no solo metadatos), de modo que Profiling (040) y los flujos posteriores puedan apoyarse en una copia fiel y auditada de los datos originales.

## Definición de "Terminado" (feature completa)
Condiciones que deben cumplirse para considerar la feature **terminada** (no una banda suelta, sino el total):
- Ingestion hereda de `Flow` (`flow_base`, CONFORME) y produce una copia inmutable en `bronze/` + un reporte de carga JSON, para cualquier cliente cuyo `contract_data.json`/`map_client_data.json` describan correctamente sus archivos.
- Soporta los medios de obtención declarados en el vocabulario `source_medium` del contrato (`csv`, `xlsx`, `database`, `api`), aunque cada medio se incorpore de forma incremental por banda.
- Valida, antes de copiar a bronze: número de archivos esperados vs. presentes, y columnas/estructura esperada por archivo, usando `contract_data.json`/`map_client_data.json` como fuente de verdad; en una banda futura también contra `client_register` (Discovery real).
- El reporte de carga documenta, como mínimo, archivos cargados, filas/columnas por archivo e inconsistencias detectadas, de forma clara para que el DS pueda corregir el origen de datos.
- Ingestion es 100% determinista (sin LLM) y no transforma ni limpia los datos: bronze es copia fiel e inalterable del original; limpieza es responsabilidad de Cleaning (050).

## Alcance Total
**In scope (toda la feature, a través de sus bandas):**
- Un `Flow` concreto `Ingestion` (hereda de `flow_base`) que declara `requires` (`contract_data.json`, `map_client_data.json`, archivos crudos) y `produces` (copia en `bronze/`, reporte de carga JSON).
- Lectura de archivos delimitados (csv/txt, con separadores `,`/`;`/`|`) y Excel (`.xlsx`).
- Validación de número de archivos y de columnas/esquema esperado contra el contrato/mapa.
- Copia inmutable a `clients/<CLIENTE>/data/bronze/`.
- Reporte de carga JSON con archivos cargados, filas/columnas por archivo e inconsistencias.
- Incorporación futura de medios `database`/`api` y de la comparación contra `client_register` real (Discovery).

**Out of scope (nunca, o en otra feature):**
- Discovery (010): generación real de `contract_data.json`/`client_register`.
- Profiling (040): cálculo de salud de los datos (faltantes, duplicados, periodicidad, pareto).
- Cleaning (050): limpieza/transformación de datos; bronze nunca se modifica.
- Cualquier uso de LLM (Ingestion es determinista según `system_design.md` §6).
- El orquestador (`foda run`).

## Bandas Previstas (eje vertical)
Qué endurece cada banda hacia la estrella polar (crear **solo** las que se necesiten; `D-029`):

| Banda | Qué aporta / endurece |
|---|---|
| `tracer_bullet` | Slice vertical mínimo end-to-end (NC-4): carga y valida csv/txt (separadores coma, punto y coma, barra vertical) y xlsx de un fixture fabricado, valida nº de archivos y columnas contra `contract_data.json`/`map_client_data.json`, copia a bronze y emite el reporte de carga. Medios `database`/`api` y comparación contra `client_register` real quedan diferidos. |
| `stab_1` *(prevista, no iniciada)* | Endurecimiento: comparación contra `client_register` real (cuando exista Discovery), validación de tipos de dato por columna (no solo presencia/nombre), medios adicionales (`database`/`api`) si el negocio los requiere, más casos de inconsistencia y mensajes enriquecidos. |

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **por celda** viven en el `spec.md` de cada banda.
1. Dado un conjunto de archivos crudos que coincide en número y esquema con lo declarado en `contract_data.json`/`map_client_data.json`, Ingestion los copia fielmente a `bronze/` y produce un reporte de carga que documenta lo cargado (archivos, filas, columnas) sin inconsistencias.
2. Dado un conjunto de archivos crudos con al menos una inconsistencia (archivo faltante/sobrante, columna faltante/distinta), Ingestion detecta y reporta la inconsistencia de forma clara, sin corromper `bronze/` con datos inválidos.
3. Ingestion no transforma, limpia ni normaliza los datos: el contenido copiado a `bronze/` es idéntico byte-a-byte (o equivalente fiel) al original.
4. Ingestion se integra como un `Flow` concreto (hereda de `flow_base`), consumiendo `ClientContext` para resolver rutas de entrada/salida.

## Dependencias
- `flow_base` (banda `tracer_bullet`, CONFORME): clase base `Flow`, `FlowResult`, `Artifact`, `FlowContractError`.
- `client_context` (banda `tracer_bullet`, CONFORME): resolución de rutas por cliente (incluye `bronze_dir`).
- `onboarding` (banda `tracer_bullet`, CONFORME): produce `map_client_data.json`; su fixture de `contract_data.json` se reutiliza/alinea aquí.
- `700_architecture/system_design.md` §5, §6, §7, §8, §10, §15 (flujo 030 Ingestion, capas medallion).
- `800_persistence/decisions.md` (decisiones vigentes de las features previas: D-047..D-067).

## Relación con Hitos de Producto
- Tercer flujo concreto real del pipeline (010–140), tras `onboarding`. Contribuye al hito emergente **MVP** del camino "cliente nuevo" (`Discovery → Onboarding → Ingestion → …`, §12): es el primer flujo que toca datos reales del cliente, habilitando Profiling/Cleaning/Derivation aguas abajo.
