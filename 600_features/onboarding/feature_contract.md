# Feature Contract — onboarding

> Artefacto **a nivel feature** (por encima de las bandas), creado por `feature_definer` en el paso *Definir*.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de iniciar la primera banda** (`D-030`).
> **Una feature tiene un solo `feature_contract`**, aunque recorra varias bandas (`tracer_bullet → stab_n`).

## Estrella Polar
El flujo **020 Onboarding** lee de forma determinista `contract_data.json` (salida de Discovery/010) y produce `map_client_data.json`: el mapa canónico del cliente (jerarquías de producto y geografía, inventario de datasets/archivos históricos y el mapeo columna→nivel), validado contra el contrato, sin tocar datos reales ni la capa bronze, de modo que Ingestion (030) y los flujos posteriores puedan apoyarse en un mapa confiable de la estructura de datos del cliente.

## Definición de "Terminado" (feature completa)
Condiciones que deben cumplirse para considerar la feature **terminada** (no una banda suelta, sino el total):
- Onboarding hereda de `Flow` (`flow_base`, CONFORME) y produce `map_client_data.json` a partir de `contract_data.json` para cualquier cliente cuyo contrato cumpla el esquema acordado (jerarquías dinámicas de producto/geografía, multi-dataset, multi-archivo, columnas obligatorias/opcionales, `maps_to` declarado).
- El mapa canónico deriva correctamente, para cualquier profundidad de jerarquía (no solo 4 niveles): nombres y profundidad de niveles de producto/geografía, miembros/valores únicos por nivel, inventario de datasets del cliente (tipo, medio, periodicidad, archivos), y el esquema de columnas por dataset con su mapeo `maps_to`.
- Onboarding valida la coherencia del contrato antes de derivar el mapa (`maps_to` apunta a niveles existentes, miembros con las claves exactas de `levels`, enums válidos de `type`/`kind`/`source_medium`/`periodicity`, fechas `period_start ≤ period_end`) y falla con mensaje claro de contrato si el `contract_data.json` es inconsistente.
- Onboarding NO valida datos reales (csv/xlsx) ni escribe en `bronze/`: solo opera sobre los metadatos del contrato. Esa responsabilidad es de Ingestion (030).
- El dominio de negocio queda reflejado: el contrato admite múltiples tipos de dataset (ventas, inventario, órdenes de compra, devoluciones, promociones, precios) porque se predice demanda, no ventas; el mapa resultante no asume que "ventas" sea el único dataset posible.

## Alcance Total
**In scope (toda la feature, a través de sus bandas):**
- Lectura y parseo de `contract_data.json` (input de `020_outputs/010_discovery/`).
- Validación de coherencia del contrato (jerarquías, `maps_to`, enums, fechas) antes de derivar el mapa.
- Derivación determinista de `map_client_data.json` (output en `020_outputs/020_onboarding/`): niveles/miembros de producto y geografía, inventario de datasets/archivos, esquema de columnas por dataset con `maps_to`.
- Integración con `Flow`/`ClientContext` (herencia de `Flow`, resolución de rutas vía `ctx`).
- Soporte a jerarquías de profundidad dinámica (no fija en 4 niveles).
- Soporte a los 6 `kind` de dataset y a los enums cerrados de `type`/`source_medium`/`periodicity` declarados en el contrato, aunque el fixture de la banda inicial solo ejercite un subconjunto.

**Out of scope (nunca, o en otra feature):**
- Discovery (010): la generación real de `contract_data.json` vía cuestionarios/LLM. En esta feature `contract_data.json` es un fixture fabricado (`D-055`).
- Ingestion (030): carga real de csv/xlsx, validación de datos reales contra el mapa, escritura en `bronze/`.
- Cualquier uso de LLM (Onboarding es determinista según `system_design.md` §6).
- El orquestador (`foda run`).
- Persistencia en base de datos o fuentes `database`/`api` reales (el contrato las admite como enum, pero no se implementa lectura real de esos medios en esta feature).

## Bandas Previstas (eje vertical)
Qué endurece cada banda hacia la estrella polar (crear **solo** las que se necesiten; `D-029`):

| Banda | Qué aporta / endurece |
|---|---|
| `tracer_bullet` | Slice vertical mínimo end-to-end (NC-4): caso más simple de jerarquía (pocos productos, geografía sencilla, el fixture acordado con el humano) → deriva `map_client_data.json` completo y válido para ese fixture. Soporta ya profundidad dinámica de niveles (no hardcodea 4) y multi-dataset/multi-archivo, pero se ejercita solo con el fixture de ventas+inventario (`D-057`). |
| `stab_1` *(prevista, no iniciada)* | Endurecimiento con jerarquías más profundas/variadas, más `kind` de dataset (órdenes de compra, devoluciones, promociones, precios), validación de contrato más exhaustiva (mensajes de error enriquecidos, más casos de inconsistencia) y casos límite no cubiertos por el fixture inicial. |

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **por celda** viven en el `spec.md` de cada banda.
1. Dado un `contract_data.json` válido conforme al esquema acordado, Onboarding produce un `map_client_data.json` que refleja fielmente los niveles/miembros de producto y geografía, el inventario de datasets/archivos, y el esquema de columnas con su `maps_to`, para cualquier profundidad de jerarquía declarada en `levels`.
2. Dado un `contract_data.json` inconsistente (p. ej. `maps_to` apunta a un nivel inexistente, un miembro no tiene las claves de `levels`, un enum inválido, o `period_start > period_end`), Onboarding falla con un error de contrato claro, sin producir `map_client_data.json`.
3. Onboarding no lee ni escribe archivos csv/xlsx de datos reales, ni toca `bronze/`, `silver/` o `gold/`.
4. Onboarding se integra como un `Flow` concreto (hereda de `flow_base`), consumiendo `ClientContext` para resolver rutas de `contract_data.json` (input) y `map_client_data.json` (output).

## Dependencias
- `flow_base` (banda `tracer_bullet`, CONFORME): provee la clase base `Flow`, `FlowResult`, `Artifact`, `FlowContractError`.
- `client_context` (banda `tracer_bullet`, CONFORME): resolución de rutas por cliente.
- `700_architecture/system_design.md` §5, §6, §8, §15 (flujo 020 Onboarding).
- `800_persistence/decisions.md` D-054, D-055, D-056, D-057.
- Fixture `contract_data.json` acordado con el humano (esquema y ejemplo concreto en `definition.md`).

## Relación con Hitos de Producto
- Primer flujo concreto real del pipeline (010–140) construido sobre `flow_base`/`client_context`. Contribuye al hito emergente **MVP** del camino "cliente nuevo" (`Discovery → Onboarding → Ingestion → …`, §12), aunque Discovery se simula por ahora vía fixture (`D-055`).
