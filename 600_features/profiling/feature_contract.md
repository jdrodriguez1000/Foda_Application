# Feature Contract — profiling

> Artefacto **a nivel feature** (por encima de las bandas), creado por `feature_definer` en el paso *Definir*.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de iniciar la primera banda** (`D-030`).
> **Una feature tiene un solo `feature_contract`**, aunque recorra varias bandas (`tracer_bullet → stab_n`).

## Estrella Polar
El flujo **040 Profiling** calcula, de forma determinista, la **salud de los datos** cargados en `bronze/` por Ingestion (030) — productos con periodicidad menor a la mínima, faltantes, duplicados, inconsistentes, desactualizados, incompletos — y entrega un **indicador global (%)**, un **desglose por tipo de problema** y un **pareto**, descargable en csv/excel, de modo que el DS sepa, antes de limpiar (050), qué tan confiables son los datos crudos del cliente.

## Definición de "Terminado" (feature completa)
Condiciones que deben cumplirse para considerar la feature **terminada** (no una banda suelta, sino el total):
- Profiling hereda de `Flow` (`flow_base`, CONFORME), consume los datos de `bronze/` producidos por Ingestion y produce un informe de salud (JSON) que documenta, como mínimo: indicador global de salud (%), desglose por tipo de problema (faltantes, duplicados, inconsistentes, desactualizados, incompletos, periodicidad menor a la mínima) y un pareto de los productos/datasets más problemáticos.
- El informe es descargable en csv/xlsx (`export`, §10 de `system_design.md`).
- Profiling respeta el **gate de progresión entre flujos** (`D-080`): no se ejecuta si su predecesor (`ingestion`) no terminó con `success == true` en su reporte, salvo que se invoque explícitamente con `--force`; si no hay gate superado, `foda run` falla limpio (exit 1, sin escribir nada).
- Profiling es 100% determinista (sin LLM) y no transforma ni limpia los datos: solo los **audita**; limpieza es responsabilidad de Cleaning (050).

## Alcance Total
**In scope (toda la feature, a través de sus bandas):**
- Un `Flow` concreto `Profiling` (hereda de `flow_base`) que declara `requires` (datos en `bronze/`, `ingestion_report.json`) y `produces` (informe de salud JSON en `020_outputs/040_profiling/`).
- Cálculo del indicador global de salud (%) y desglose por tipo de problema (faltantes, duplicados, inconsistentes, desactualizados, incompletos, periodicidad menor a la mínima).
- Cálculo de un pareto de los productos/datasets con más problemas.
- Exportación del informe a csv/xlsx (`foda export --flow profiling`).
- El **gate de progresión entre flujos** (`D-080`, puntos 1-3): Profiling no corre si `ingestion_report.json` no tiene `success == true`, salvo `--force`; falla limpio si no hay OK.

**Out of scope (nunca, o en otra feature):**
- Discovery (010): `client_register.yaml` real (la comparación de salud contra periodicidad/expectativas declaradas en Discovery se difiere mientras ese artefacto no exista con datos reales).
- Cleaning (050): limpieza/transformación de los datos; Profiling solo audita, nunca modifica `bronze/` ni produce `silver/`.
- Cualquier uso de LLM (Profiling es determinista según `system_design.md` §6).
- El gate de progresión (`D-080`) para flujos anteriores a `ingestion` (`discovery`/`onboarding` quedan exceptuados por decisión vigente, D-080 punto 5).
- El orquestador (`foda run`) en sí mismo — solo se le añade el chequeo de gate y el flag `--force` que ya forman parte de esta feature, sin rediseñarlo.

## Bandas Previstas (eje vertical)
Qué endurece cada banda hacia la estrella polar (crear **solo** las que se necesiten; `D-029`):

| Banda | Qué aporta / endurece |
|---|---|
| `tracer_bullet` | Slice vertical mínimo end-to-end (NC-4): esqueleto de `Profiling` como `Flow` concreto que lee `ingestion_report.json` (el reporte de su predecesor) y produce su propio `profiling_report.json` mínimo (con al menos un campo `success`), SIN la lógica pesada de salud de datos (indicador de salud, desglose por tipo de problema, pareto, descargables csv/xlsx) — todo eso queda diferido a una banda posterior. Esta banda es, ante todo, el **anfitrión y caso de uso concreto** que implementa y ejercita el **gate de progresión entre flujos** (`D-080`, puntos 1-3, T-036): `profiling` no corre si `ingestion_report.json` no tiene `success == true`, salvo `--force`, y falla limpio (exit 1, sin escribir nada) si el gate no se supera. |
| `stab_1` *(en curso, T-039, D-088/D-089)* | Endurecimiento: cálculo real de la salud **ESTRUCTURAL** del ingreso, derivada **únicamente** de `ingestion_report.json` (sin leer `bronze/`): `global_score`, conteos (`files_declared`/`files_healthy`/`files_with_problems`), desglose `problems_by_type` y ranking `pareto`. Enriquece `profiling_report.json` con un bloque `health` y sube `schema_version` a `"0.2"`. Diferido a bandas posteriores: salud a nivel de datos/celda (leer `bronze/`: nulos, duplicados, tipos, rangos — `stab_2`), comparación contra `client_register.yaml` real, exportables csv/xlsx. |

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **por celda** viven en el `spec.md` de cada banda.
1. Dado un cliente con datos cargados en `bronze/` por Ingestion, Profiling calcula y reporta el indicador global de salud (%), el desglose por tipo de problema y el pareto de datasets/productos más problemáticos.
2. El informe de salud es exportable a csv/xlsx sin alterar su contenido.
3. Profiling nunca se ejecuta si su predecesor (`ingestion`) no terminó con `success == true`, salvo invocación explícita con `--force`; en ese caso `foda run` falla limpio (exit 1) sin escribir ningún artefacto de Profiling.
4. Profiling no transforma ni limpia los datos de `bronze/`: es un flujo de solo lectura/auditoría.
5. Profiling se integra como un `Flow` concreto (hereda de `flow_base`), consumiendo `ClientContext` para resolver rutas de entrada/salida.

## Dependencias
- `flow_base` (banda `tracer_bullet`, CONFORME): clase base `Flow`, `FlowResult`, `Artifact`, `FlowContractError`.
- `client_context` (banda `tracer_bullet`, CONFORME): resolución de rutas por cliente.
- `ingestion` (banda `tracer_bullet`, CONFORME): produce `ingestion_report.json` (con campo `success`) y la copia inmutable en `bronze/` que Profiling debe auditar en bandas futuras.
- `flow_orchestrator` (banda `tracer_bullet`, CONFORME): CLI `foda run`/`foda status`; el gate de progresión (`D-080`) y el flag `--force` de esta feature se materializan sobre esa capa de despacho.
- `700_architecture/system_design.md` §5, §6, §7, §8, §10, §15 (flujo 040 Profiling, capas medallion, exportables).
- `800_persistence/decisions.md`: `D-080` (gate de progresión + exit code), `D-079`/`D-081` (política de ramas y PR).

## Relación con Hitos de Producto
- Cuarto flujo concreto real del pipeline (010–140), tras `ingestion`. En esta banda `tracer_bullet` contribuye sobre todo al **hito de gobernanza** del gate de progresión entre flujos (`D-080`, T-036), dejando además el esqueleto vertical del flujo 040 listo para endurecerse en `stab_1` hacia el hito emergente **MVP** del camino "cliente nuevo" (`Discovery → Onboarding → Ingestion → Profiling → …`, §12).
