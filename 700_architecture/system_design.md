# System Design — Foda_Application

> Documento de diseño de arquitectura del sistema. Describe **qué** construimos y **cómo** se organiza, antes de escribir código. Es un documento vivo: el flujo y el alcance se irán afinando.

**Versión:** 0.2 (validado con el usuario sección por sección) · **Fecha:** 2026-07-01

---

## Índice
1. [Contexto y Objetivo](#1-contexto-y-objetivo)
2. [Principios de Diseño](#2-principios-de-diseño)
3. [Restricciones y Decisiones Base](#3-restricciones-y-decisiones-base)
4. [Visión General de la Arquitectura](#4-visión-general-de-la-arquitectura)
5. [Modelo de Flujos (Pipeline)](#5-modelo-de-flujos-pipeline)
6. [Clasificación por Determinismo (uso de LLM)](#6-clasificación-por-determinismo-uso-de-llm)
7. [Estructura de Carpetas](#7-estructura-de-carpetas)
8. [Contrato de Artefactos entre Flujos](#8-contrato-de-artefactos-entre-flujos)
9. [Abstracción Común de un Flujo](#9-abstracción-común-de-un-flujo)
10. [Capas Medallion (bronze / silver / gold)](#10-capas-medallion-bronze--silver--gold)
11. [Interfaz CLI](#11-interfaz-cli)
12. [Caminos de Ejecución: Nuevo vs. Recurrente](#12-caminos-de-ejecución-nuevo-vs-recurrente)
13. [Multi-tenant y Aislamiento por Cliente](#13-multi-tenant-y-aislamiento-por-cliente)
14. [Encapsulamiento del LLM](#14-encapsulamiento-del-llm)
15. [Detalle Flujo por Flujo](#15-detalle-flujo-por-flujo)
16. [Puntos Abiertos y Futuro](#16-puntos-abiertos-y-futuro)

---

## 1. Contexto y Objetivo

**Sabbia Solutions & Services (Triple S)** ofrece planeación de demanda con modelos de machine learning. Hoy es un servicio 100% manual: cada científico de datos (DS) atiende un máximo de ~4 clientes ejecutando scripts en terminal, lo que **impide escalar**.

**Objetivo del sistema:** pasar de *servicio* a **Service as a Software (SaaSw)**, automatizando entre el **85% y el 95%** del trabajo del DS mediante procesos deterministas y agentes de IA especializados, de modo que el DS pase de *ejecutor* a **revisor y aprobador** de las predicciones. La aplicación replica la lógica del DS como un "gemelo digital" del negocio del cliente.

> **Nota clave del dominio:** predecimos la **demanda de productos**, no las ventas.

---

## 2. Principios de Diseño

1. **Determinista por defecto, LLM solo donde aporta.** El núcleo es Python puro y reproducible. El LLM se aísla en pasos concretos (lenguaje natural o juicio) y nunca atraviesa el core de cálculo.
2. **Artefactos como contrato entre flujos.** Cada flujo consume artefactos del flujo anterior y produce los suyos, con dos naturalezas:
   - **YAML = decisión humana / configuración** (revisable y editable por el DS).
   - **JSON = resultado de máquina** (auto-generado; sirve de entrada a otros flujos).
3. **Aislamiento por cliente en disco.** Multi-tenant simple, sin base de datos por ahora.
4. **CLI como única interfaz.** Sin frontend por ahora.
5. **Idempotencia y reanudación.** Un flujo puede correrse solo, repetirse o reanudarse sin corromper el estado.
6. **Escalabilidad estructural.** Agregar productos, sedes o clientes nuevos no requiere rediseño.

---

## 3. Restricciones y Decisiones Base

| # | Restricción / Decisión | Valor |
|---|---|---|
| R1 | Lenguaje | Python 3.13+ |
| R2 | Interfaz | CLI (sin frontend) |
| R3 | Entrada de configuración | Archivos **YAML** |
| R4 | Salida de resultados | Archivos **JSON** |
| R5 | Datos crudos del cliente | Archivos **csv / xlsx** → capa bronze |
| R6 | Persistencia | Sistema de archivos, **carpeta por cliente** (sin BD) |
| R7 | Multi-tenant | Un DS maneja muchos clientes |
| R8 | LLM | Uso selectivo, lo más determinista posible |
| R9 | Modelo por cliente | Nuevo: se genera; Recurrente: se reutiliza |

---

## 4. Visión General de la Arquitectura

El sistema es un **pipeline de flujos secuenciales** donde cada flujo:
- lee **inputs** (YAML de decisiones humanas + JSON de flujos anteriores),
- ejecuta un **núcleo determinista** (con paso LLM opcional y aislado),
- escribe **outputs** (JSON) y, cuando aplica, **datasets** en las capas medallion.

```
          ┌─────────────────────────────────────────────────────┐
   CLI ──▶ │  Orquestador  ──▶  Flow.run(ClientContext)          │
          │                     ├─ load_inputs   (YAML + JSON)   │
          │                     ├─ validate      (contratos)     │
          │                     ├─ execute       (Python [+LLM]) │
          │                     └─ write_outputs (JSON + data/)  │
          └─────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    clients/<CLIENTE>/  (aislamiento en disco)
```

Componentes de código:
- **`cli`** — punto de entrada; interpreta comandos y despacha al orquestador.
- **`core`** — abstracciones comunes: `Flow`, `ClientContext`, validación de contratos, resolución de rutas.
- **`flows`** — un módulo por flujo; contiene la lógica específica.
- **`llm`** — clientes LLM encapsulados detrás de una interfaz estable.

---

## 5. Modelo de Flujos (Pipeline)

| # | Flujo | Propósito | Artefacto(s) principal(es) | Capa |
|---|---|---|---|---|
| 010 | **Discovery** | Entender el problema y los datos del cliente | `client_register.yaml`, `business_hypothesis.md`, `contract_data.json` | — |
| 020 | **Onboarding** | Mapear la estructura de datos del cliente | `map_client_data.json` | — |
| 030 | **Ingestion** | Cargar y validar datos crudos | copia inmutable | 🥉 bronze |
| 040 | **Profiling** | Determinar salud de los datos + pareto | informe de salud | — |
| 050 | **Cleaning** | Limpiar datos según reglas | `data_cleaner.yaml` (in), `data_cleaning.json` (out) | 🥈 silver |
| 060 | **Derivation** | Calcular demanda histórica agregada | `data_derivation.json` | 🥇 gold |
| 070 | **Exploration** | EDA + validar hipótesis + proponer features | `exploration.json`, `feature_engineering.yaml` | — |
| 080 | **Featuring** | Generar variables nuevas | `feature_engineering.json` | 🥇 gold |
| 090 | **Modelling** | Torneo de modelos y selección | `modelling.json`, `best_model.pkl` | — |
| 100 | **Inferences** | Predecir demanda (+ MAPE) | `inferences.json` | 🥇 gold |
| 110 | **Simulation** | Montecarlo: optimista/moderado/pesimista | `simulation.json` | 🥇 gold |
| 115 | **Scenarios** | "¿Qué pasa si…?" *(por definir)* | *(por definir)* | — |
| 120 | **Reporting** | Informes financieros (margen, costo oportunidad) | `reporting.json` | — |
| 130 | **Monitoring** | Seguimiento de calidad de predicciones | `monitoring.json` | 🥇 gold |
| 140 | **Alerting** | Alertas por desviación significativa | `alerting.json` | — |

> La numeración `0X0` deja espacio para flujos intermedios futuros (p. ej. Scenarios como 115).

---

## 6. Clasificación por Determinismo (uso de LLM)

| Flujo | Núcleo | Uso de LLM |
|---|---|---|
| Discovery | Generar documentos desde cuestionarios | 🔵 **LLM central** |
| Onboarding | Mapear estructura desde contrato | ⚫ determinista (LLM opcional) |
| Ingestion | Cargar csv/xlsx, validar vs contrato, copiar a bronze | ⚫ determinista |
| Profiling | Métricas de salud + pareto | ⚫ determinista |
| Cleaning | Aplicar reglas de `data_cleaner.yaml` | ⚫ determinista (LLM *propone* el yaml) |
| Derivation | Agregar demanda por periodicidad | ⚫ determinista |
| Exploration | EDA + validación de hipótesis + propuesta de features | 🔵 **híbrido** |
| Featuring | Aplicar `feature_engineering.yaml` | ⚫ determinista |
| Modelling | Torneo de modelos ML | ⚫ determinista (LLM narra recomendación) |
| Inferences | Predecir con `best_model.pkl` | ⚫ determinista |
| Simulation | Montecarlo | ⚫ determinista |
| Reporting | Cálculos financieros | ⚫ determinista (LLM narra) |
| Monitoring / Alerting | Comparaciones y umbrales | ⚫ determinista |

**Consecuencia:** el LLM queda aislado en Discovery y Exploration (y como narrativa opcional en Modelling/Reporting). El core de cálculo es 100% determinista → testeable y reproducible.

---

## 7. Estructura de Carpetas

**Decisión:** `010_inputs` y `020_outputs` se **anidan dentro de cada cliente**; las capas medallion (`data/`) se mantienen **separadas** de los artefactos de configuración.

```
Foda_Application/
├── src/foda/                      # paquete Python de la aplicación
│   ├── cli.py                     # punto de entrada CLI
│   ├── core/                      # Flow, ClientContext, contratos, rutas
│   ├── flows/                     # un módulo por flujo
│   │   ├── f010_discovery/
│   │   ├── f030_ingestion/
│   │   └── …
│   └── llm/                       # clientes LLM encapsulados
│
├── clients/                       # ← aislamiento multi-tenant
│   └── ABC/                       # una carpeta por cliente
│       ├── client.yaml            # identidad y configuración del cliente
│       ├── 010_inputs/            # entradas por flujo (YAML: decisiones humanas)
│       │   ├── 010_discovery/     #   cuestionarios respondidos
│       │   ├── 050_cleaning/      #   data_cleaner.yaml
│       │   └── 070_exploration/   #   ajustes humanos a features
│       ├── 020_outputs/           # salidas por flujo (JSON: resultados de máquina + descargables csv/xlsx)
│       │   ├── 010_discovery/     #   contract_data.json, client_register.yaml, business_hypothesis.md
│       │   ├── 040_profiling/     #   informe de salud (+ export csv/xlsx)
│       │   └── …
│       ├── data/                  # capas medallion (datasets)
│       │   ├── bronze/            #   csv/xlsx originales del cliente, INALTERABLES
│       │   ├── silver/            #   datos limpios
│       │   └── gold/              #   derivados / features / inferencias / simulación
│       └── models/                # modelos VERSIONADOS (no se sobrescriben)
│           ├── 2026-07_v1/        #   best_model.pkl + metadatos de esa versión
│           └── latest → 2026-07_v1  #   puntero a la versión vigente
│
├── 700_architecture/              # este documento y diseño
├── 800_persistence/               # seguimiento del proyecto
└── 990_documents/                 # documentos de negocio (workflow, estado actual)
```

**Convención de numeración:** cada flujo usa un prefijo (`010_discovery`, `020_onboarding`, …) que se repite en `010_inputs/`, `020_outputs/` y `src/foda/flows/`. Facilita orden y trazabilidad.

---

## 8. Contrato de Artefactos entre Flujos

Cada flujo declara qué **requiere** (inputs) y qué **produce** (outputs). Un flujo no arranca si sus artefactos requeridos no existen o no validan.

| Flujo | Requiere (inputs) | Produce (outputs) |
|---|---|---|
| Discovery | cuestionarios (010_inputs) | `client_register.yaml`, `business_hypothesis.md`, `contract_data.json` |
| Onboarding | `contract_data.json` | `map_client_data.json` |
| Ingestion | `contract_data.json`, `map_client_data.json`, csv/xlsx | datos en `bronze/`, reporte de carga |
| Profiling | datos `bronze/`, `client_register.yaml` | informe de salud (JSON) + pareto |
| Cleaning | datos `bronze/`, `data_cleaner.yaml` | datos en `silver/`, `data_cleaning.json` |
| Derivation | datos `silver/`, `contract_data.json` (periodicidad) | datos en `gold/`, `data_derivation.json` |
| Exploration | datos `gold/`, `business_hypothesis.md` | `exploration.json`, `feature_engineering.yaml` |
| Featuring | datos `gold/`, `feature_engineering.yaml` | datos en `gold/`, `feature_engineering.json` |
| Modelling | datos `gold/` (features) | `modelling.json`, modelo versionado en `models/<versión>/best_model.pkl` |
| Inferences | modelo vigente (`models/latest`), features `gold/` | `inferences.json` (+ MAPE), predicciones `gold/` |
| Simulation | `inferences.json`, `simulation.json` (reglas) | demanda simulada `gold/`, escenarios |
| Reporting | resultados de simulation | `reporting.json` |
| Monitoring | predicciones vs demanda real | `monitoring.json` |
| Alerting | `monitoring.json`, umbrales | `alerting.json` |

> **Ciclo propuesta → aprobación:** artefactos YAML como `data_cleaner.yaml` y `feature_engineering.yaml` pueden ser **propuestos por un agente** y luego **revisados/editados por el DS** antes de convertirse en input del siguiente flujo. Este es el punto donde vive el "human-in-the-loop".

> **Dependencias multi-flujo:** la tabla anterior muestra la dependencia principal de cada flujo, pero un flujo **puede requerir artefactos de más de un flujo atrás** (p. ej. Reporting necesitará `contract_data.json` para precios/costos, no solo la salida de Simulation). El conjunto exacto de `requires` se declarará y validará formalmente al construir cada flujo.

> **Descargables (`export`):** los artefactos exportables a csv/xlsx (Profiling, Reporting, etc.) se guardan **dentro de `020_outputs/<flujo>/`**, junto al JSON del flujo. No hay carpeta `exports/` separada.

---

## 9. Abstracción Común de un Flujo

Todos los flujos implementan el mismo contrato, garantizando consistencia:

```python
class Flow:
    name: str
    requires: list[Artifact]     # artefactos de entrada obligatorios
    produces: list[Artifact]     # artefactos de salida

    def run(self, ctx: ClientContext) -> FlowResult:
        self.load_inputs(ctx)    # 1. lee YAML (010_inputs) + JSON upstream (020_outputs)
        self.validate(ctx)       # 2. verifica que existan/validen los artefactos requeridos
        result = self.execute(ctx)  # 3. núcleo determinista (+ paso LLM opcional aislado)
        self.write_outputs(ctx, result)  # 4. escribe JSON (020_outputs) y datasets (data/)
        return result
```

- **`ClientContext`** resuelve: qué cliente, si es nuevo/recurrente, rutas de inputs/outputs/data/models, y qué artefactos ya existen.
- **`FlowResult`** encapsula estado (éxito/inconsistencias) y rutas de artefactos generados.
- La **validación de contratos** es previa a `execute()`: si falta un artefacto requerido, el flujo falla temprano y con mensaje claro (p. ej. Ingestion detecta inconsistencia vs `client_register` → informa al DS).

---

## 10. Capas Medallion (bronze / silver / gold)

| Capa | Contenido | Escrito por | Regla |
|---|---|---|---|
| 🥉 **bronze** | csv/xlsx originales del cliente | Ingestion | **Inalterable** por Triple S; copia fiel de lo recibido |
| 🥈 **silver** | datos limpios y consistentes | Cleaning | Deriva de bronze aplicando `data_cleaner.yaml` |
| 🥇 **gold** | demanda derivada, features, inferencias, simulación | Derivation, Featuring, Inferences, Simulation, Monitoring | Datos listos para consumo/modelado |

Las capas son **datasets** (no artefactos de configuración) y por eso viven en `data/`, separadas de `010_inputs`/`020_outputs`.

---

## 11. Interfaz CLI

```
foda client new ABC                      # crea el esqueleto de carpetas de un cliente
foda client list                         # lista clientes existentes

foda run ABC --flow discovery            # ejecuta un flujo concreto
foda run ABC --from ingestion --to reporting   # ejecuta un rango de flujos
foda run ABC --pipeline new              # pipeline completo de cliente nuevo
foda run ABC --pipeline recurring        # pipeline mensual (reutiliza best_model.pkl)

foda status ABC                          # muestra qué flujos se han ejecutado y qué artefactos existen
foda export ABC --flow profiling --format xlsx   # descarga un output a csv/excel
```

El CLI solo **orquesta**; toda la lógica vive en los flujos. Los flujos son descubribles por su nombre/prefijo.

---

## 12. Caminos de Ejecución: Nuevo vs. Recurrente

**Cliente nuevo** (objetivo: obtener `best_model.pkl` y primeras predicciones):
```
Discovery → Onboarding → Ingestion → Profiling → Cleaning → Derivation
          → Exploration → Featuring → Modelling → Inferences → Simulation → Reporting
```

**Cliente recurrente** (objetivo: predicción mensual con el modelo ya existente):
```
Ingestion → Cleaning → Derivation → Featuring → Inferences (reusa best_model.pkl, SALTA Modelling)
          → Simulation → Reporting → Monitoring → Alerting
```

El `ClientContext` marca el modo; el orquestador selecciona la secuencia de flujos correspondiente.

---

## 13. Multi-tenant y Aislamiento por Cliente

- **Identidad del cliente = nombre de carpeta + `client.yaml`** (sin registro central por ahora).
- Cada cliente es una carpeta independiente bajo `clients/`; no hay estado compartido entre clientes.
- Un DS opera múltiples clientes ejecutando el CLI con distintos identificadores.
- **Escalabilidad futura:** el modelo de carpeta-por-cliente puede migrar a base de datos u object storage sin cambiar la interfaz de `ClientContext` (las rutas se resuelven detrás de esa abstracción).

---

## 14. Encapsulamiento del LLM

- Todo acceso a LLM pasa por el módulo `src/foda/llm/` detrás de una interfaz estable (p. ej. `generate_document(prompt, context) -> str/dict`).
- **Proveedor por defecto: API de Anthropic (Claude).** La elección de proveedor/modelo queda detrás de la interfaz de `src/foda/llm/`, de modo que pueda cambiarse sin tocar los flujos.
- Los flujos deterministas **no** conocen al LLM; los flujos que lo usan (Discovery, Exploration) invocan la interfaz y **validan la salida** antes de escribir artefactos.
- Beneficios: el core es testeable sin LLM; se puede cambiar de proveedor/modelo sin tocar los flujos; las salidas del LLM se normalizan a los contratos YAML/JSON.

---

## 15. Detalle Flujo por Flujo

> Resumen operativo de cada flujo. El detalle fino de reglas y esquemas de artefactos se especificará al construir cada uno.

### 010 Discovery
Entrevistas a ≥3 stakeholders de áreas distintas (planeación, comercialización, logística) con cuestionario estandarizado; reunión con el área de sistemas para entender la estructura de datos. Un agente LLM redacta la problemática y la estructura de datos, e identifica comportamiento del negocio (festivos, clima, promociones). **Salidas:** `client_register.yaml`, `business_hypothesis.md`, `contract_data.json`.

### 020 Onboarding
Mapea la estructura de datos del cliente según `contract_data.json`: número exacto de archivos históricos, parámetros de producto (familia/categoría/subcategoría/clase) y geografía (región/país/ciudad/sede). **Salida:** `map_client_data.json`.

### 030 Ingestion
Lee `contract_data.json` y `map_client_data.json` para saber el medio de obtención (csv, base de datos, API). Carga la información, la compara con `client_register` y, si hay inconsistencias, informa al DS. Si es correcta, copia inmutable a **bronze**.

### 040 Profiling
Calcula la **salud de los datos**: productos con periodicidad menor a la mínima, faltantes, duplicados, inconsistentes, desactualizados, incompletos. Entrega indicador global (%) + desglose por tipo de problema + **pareto**. Descargable en csv/excel.

### 050 Cleaning
Aplica reglas de `data_cleaner.yaml` (imputación por media/mediana/moda/fecha cercana, eliminación de duplicados/inconsistentes, etc.). **Salidas:** datos en **silver** + `data_cleaning.json` (documentación reproducible).

### 060 Derivation
Calcula la demanda histórica agregada según la periodicidad de `contract_data.json` (semanal…anual) por sede. **Salidas:** datos en **gold** + `data_derivation.json`.

### 070 Exploration
EDA + validación de hipótesis de `business_hypothesis.md` + estudio de correlación con la demanda para proponer variables nuevas. **Salidas:** `exploration.json`, `feature_engineering.yaml`.

### 080 Featuring
Genera variables a partir de las existentes según `feature_engineering.yaml` (p. ej. día de semana, mes, año). **Salidas:** features en **gold** + `feature_engineering.json`.

### 090 Modelling
Torneo de campeones: entrena varios modelos sobre gold, compara resultados y variables explicativas. El DS **selecciona** el modelo (human-in-the-loop). **Salidas:** `modelling.json`, `best_model.pkl`.

### 100 Inferences
Predice la demanda con `best_model.pkl`. Cada predicción incluye su **MAPE**. **Salidas:** `inferences.json` + predicciones en **gold**.

### 110 Simulation
Montecarlo sobre las inferencias aplicando la desviación de cada periodo → optimista/moderado/pesimista + demanda simulada + inventario de seguridad. Puede incluir lead time, TRM, inflación. **Salidas:** demanda simulada en **gold**.

### 115 Scenarios *(por definir)*
Responde "¿qué pasa si…?" usando inferences + simulation. Entradas, reglas y artefactos se definirán más adelante.

### 120 Reporting
Informes financieros: precio/costo unitario, costo de seguridad, margen bruto esperado, costo de oportunidad. **Salida:** `reporting.json`, descargable.

### 130 Monitoring
Monitorea la calidad de las predicciones a lo largo del tiempo. **Salida:** `monitoring.json`.

### 140 Alerting
Compara demanda real vs simulada y alerta cuando la desviación supera el umbral definido. **Salida:** `alerting.json`.

---

## 16. Puntos Abiertos y Futuro

- **Scenarios (115):** definir entradas, reglas y artefactos.
- **Medio de ingestión múltiple:** hoy csv/xlsx; el diseño contempla BD/API como extensión.
- **Persistencia:** carpeta-por-cliente ahora; posible migración a BD/object storage detrás de `ClientContext`.
- **Esquemas formales de artefactos:** definir JSON Schema / modelos (p. ej. Pydantic) por artefacto al construir cada flujo.
- **Orquestación avanzada:** hoy secuencial vía CLI; a futuro podría incorporarse un orquestador de tareas si se requiere paralelismo o agendamiento.
- **Registro central de clientes:** opcional si el número de clientes crece.
```
