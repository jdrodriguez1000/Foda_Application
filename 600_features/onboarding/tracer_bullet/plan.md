# Plan de Implementación — onboarding

> Artefacto de la etapa 3 (`plan_builder`). Traduce la `spec.md` **aprobada** (GATE humano superado)
> en un plan de implementación mínimo (NC-2) y en la lista **ordenada** de casos de test que guiarán
> el bucle TDD (red → green → refactor). **No** contiene código ni tests: solo el *cómo* y el *orden*.
>
> Banda: `tracer_bullet`. Fuentes: `spec.md` (esta celda, GATE humano APROBADO — DS-ONB-1…5),
> `definition.md` (HU-01…HU-05), `feature_contract.md` (estrella polar),
> `src/foda/core/flow.py` (`Flow`, `Artifact`, `FlowResult`, `FlowContractError`; CONFORME — se hereda,
> no se toca), `src/foda/core/context.py` (`ClientContext`; CONFORME — resolución de rutas),
> `src/foda/core/scaffold.py` (`create_client`; CONFORME — fixture del árbol de cliente bajo `tmp_path`),
> `700_architecture/system_design.md` (§7 estructura, §8 contrato de artefactos, §9 abstracción `Flow`),
> `800_persistence/decisions.md` (D-021, D-031, D-037, D-042, D-054…D-057), `980_guideline/principles.md`.
>
> **GATE humano al terminar:** este plan y sus casos TDD requieren aprobación del usuario antes de
> invocar `tdd_tester`.

---

## 1. Enfoque Técnico

Slice vertical mínimo (NC-4) y quirúrgico (NC-3): un único módulo nuevo bajo `src/foda/flows/f020_onboarding/`
que define la clase concreta **`Onboarding(Flow)`** (flujo 020, determinista). **No** se toca el core
(`flow.py`, `context.py`, `scaffold.py` están CONFORME y se consumen tal cual; NC-3), ni se amplía
`ClientContext` (DS-ONB-5): la resolución `020_outputs/<flujo>/…` ya la soporta `Artifact` vía
`base="outputs"` + `relative`.

### Clase a producir — `Onboarding(Flow)` (`src/foda/flows/f020_onboarding/onboarding.py`)

Hereda `Flow` y sobreescribe **solo** los 4 hooks del template method (no toca `run`). Contrato:

```python
name = "onboarding"
requires = [Artifact(name="contract_data",   base="outputs", relative="010_discovery/contract_data.json")]
produces = [Artifact(name="map_client_data",  base="outputs", relative="020_onboarding/map_client_data.json")]
```

- **`load_inputs(ctx) -> None`** — resuelve la ruta del `require` (`self.requires[0].path(ctx)`); **si existe**,
  lee y parsea el JSON (`json.loads`) a estado de instancia (p. ej. `self._contract`). Si **no** existe, deja
  el estado sin cargar (no lanza `FileNotFoundError` crudo) para que `validate()` base lo detecte. No escribe en disco.
- **`validate(ctx) -> None`** — (a) `super().validate(ctx)`: existencia física del `require` → `FlowContractError`
  si falta (DS-ONB-5, cubre CA-20); (b) **coherencia de contenido** del contrato ya cargado, en el orden lógico de
  la spec (§Comportamiento 2b), lanzando `FlowContractError` a la **primera** inconsistencia (DS-ONB-1), **sin escribir**:
  `levels` no vacíos (product y geography); cada miembro con **exactamente** las claves de sus `levels`; `field.name`
  único por dataset; `field.required` booleano; enums válidos (`field.type`/`kind`/`source_medium`/`periodicity`);
  cada `maps_to` válido (`null`/`"time"`/`"measure"`/`"product.<level>"`/`"geography.<level>"` con `<level>` existente);
  cada archivo con `period_start`/`period_end` en `YYYY-MM-DD` válidos y `period_start ≤ period_end`.
- **`execute(ctx) -> FlowResult`** — deriva **en memoria** el mapa canónico (DS-ONB-2) desde `self._contract`
  y devuelve `FlowResult(success=True, outputs=[self.produces[0].path(ctx)])`. No escribe en disco.
- **`write_outputs(ctx, result) -> None`** — `path.parent.mkdir(parents=True, exist_ok=True)` y escribe
  `map_client_data.json` con serialización **determinista** (DS-ONB-4): `json.dumps(mapa, ensure_ascii=False,
  indent=2, sort_keys=True)` + salto de línea final.

### Derivación del mapa (helpers privados de la clase, detalle interno; NC-2)

Funciones puras internas (nombres a fijar por el coder; no forman parte del contrato observable):

- **identidad:** copia de `client` (`code`/`name`/`sector`) y `schema_version` propagado del contrato.
- **jerarquía** (aplicada a `product_hierarchy` y a `geography`): `levels` en **orden declarado**; `depth = len(levels)`
  (profundidad **dinámica**, sin hardcode de 4); `member_count = len(members)`; por cada nivel, `unique_values[nivel]` =
  valores **distintos** observados en `members` para esa clave, **ordenados alfabéticamente ascendente** (DS-ONB-3);
  `unique_counts[nivel] = len(unique_values[nivel])`.
- **datasets:** en **orden del contrato**; cada uno con `kind`/`source_medium`/`periodicity`, `file_count = len(files)`,
  `files` (name/period_start/period_end **tal cual**, sin descomponer multi-año) y `fields`
  (name/type/required/**maps_to del contrato**), ambos en orden del contrato.
- **totals:** `dataset_count = len(datasets)`, `file_count = Σ file_count`.

**Determinismo (DS-ONB-4):** el orden semántico (niveles, datasets, files, fields) se preserva en las **listas**;
`sort_keys=True` solo ordena las **claves de objeto**, sin alterar información. Mismo input ⇒ mismo output byte a byte.

**Dependencias de librería:** `json`, `datetime` (validación de fechas con `date.fromisoformat`), `pathlib` — todo
**stdlib** (R1: Python 3.13+). **Cero** dependencias nuevas. Sin JSON Schema/Pydantic (D-042): la validación es
explícita en `validate()`.

### Fixtures de test (viven en `tests/`, no en `src/`)

El `ClientContext` se construye con `create_client(NAME, tmp_path/"clients")` (core CONFORME) +
`ClientContext(NAME, tmp_path/"clients")`; nunca se toca el `clients/` real del repo. El `contract_data.json`
válido (el del §Contratos de Datos de la spec, ventas+inventario, 4+4 niveles) se escribe bajo
`ctx.outputs_dir / "010_discovery/contract_data.json"`. Las variantes (3 niveles, 5 niveles, y contratos
inconsistentes) se derivan mutando el dict base.

---

## 2. Archivos Afectados

> El código **no** vive en `600_features/`; va en `src/foda/…` y `tests/…`.

| Ruta | Acción | Contenido |
|---|---|---|
| `src/foda/flows/__init__.py` | crear | Paquete `flows` (andamiaje; vacío). |
| `src/foda/flows/f020_onboarding/__init__.py` | crear | Paquete del flujo 020 (andamiaje; puede reexportar `Onboarding`). |
| `src/foda/flows/f020_onboarding/onboarding.py` | crear | Clase `Onboarding(Flow)`: `requires`/`produces` + 4 hooks + helpers de derivación y validación. Solo stdlib. |
| `tests/flows/test_onboarding.py` | crear | Suite unit de `Onboarding` (fixture válido + variantes + casos de error), `ClientContext` vía `create_client(...)` bajo `tmp_path`. |
| `tests/integration/test_onboarding_integration.py` | crear | Test de integración end-to-end (`integration_tester`, tras el bucle unit). |

**Notas de infraestructura:** el andamiaje base (`pyproject.toml`, `src/foda/`, `tests/`) ya existe;
`pyproject.toml` usa `pythonpath=["src"]` + `testpaths=["tests"]` (convención sin `__init__.py` en `tests/`).
`tests/flows/` es nuevo (sigue la convención de `tests/core/`).

---

## 3. Dependencias y Contratos

- **Consume:** `foda.core.flow.{Flow, Artifact, FlowResult, FlowContractError}` (CONFORME, se hereda) y
  `foda.core.context.ClientContext` (CONFORME, resolución de rutas). En tests, `foda.core.scaffold.create_client`
  (CONFORME) materializa el árbol §7 bajo `tmp_path`.
- **Entrada:** `contract_data.json` en `020_outputs/010_discovery/` (fixture fabricado; Discovery/010 no se implementa, D-055).
- **Produce:** `map_client_data.json` en `020_outputs/020_onboarding/` (DS-ONB-2) y el módulo `src/foda/flows/f020_onboarding/`.
- **Contrato de errores:** `FlowContractError` para require ausente (base) y **toda** inconsistencia de contenido (DS-ONB-1).
- **Restricciones respetadas:** R1 (Python 3.13+, solo stdlib), D-042 (sin JSON Schema/Pydantic), NC-3 (no se toca el core),
  DS-ONB-4 (determinismo), DS-ONB-5 (hooks/orden de validación; sin ampliar `ClientContext`).

---

## 4. Tareas (atómicas y trazables)

> Cada tarea es **atómica**: **un solo responsable**, **un solo entregable**, y **código y test en tareas separadas**.
> **Estado** inicial `no_implementada` (∈ `no_implementada` | `implementada` | `cancelada_suspendida`); el **responsable
> de cada tarea es su único escritor de estado** (`D-021`). Trazabilidad → `CA-xx` de la spec (o andamiaje justificado).

### 4.1 Tareas de código / andamiaje

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Crear el paquete del flujo: `src/foda/flows/__init__.py` y `src/foda/flows/f020_onboarding/__init__.py` (andamiaje de paquete Python; §7). | Paquete `f020_onboarding` | tdd_coder | no_implementada | andamiaje (CA-11) |
| TSK-02 | Crear `onboarding.py` con `Onboarding(Flow)`: `name`, `requires`/`produces` (Artifacts DS-ONB-5), `load_inputs` (lee/parsea JSON si existe), `validate` que invoca `super().validate` (existencia base), `execute` (mapa mínimo con `client`/`schema_version` + `FlowResult(success=True, outputs=[ruta])`) y `write_outputs` (mkdir + escritura JSON). | `Onboarding` (esqueleto + happy path mínimo) | tdd_coder | no_implementada | CA-01, CA-11, CA-12, CA-20 |
| TSK-03 | Derivación de jerarquías en `execute`: `levels` (orden declarado), `depth = len(levels)` (dinámico), `member_count`, `unique_values` (distintos, alfabéticos) y `unique_counts` por nivel, para `product` y `geography`. | `Onboarding` (jerarquías) | tdd_coder | no_implementada | CA-02, CA-03, CA-04, CA-05, CA-05b |
| TSK-04 | Derivación del inventario de `datasets` en `execute`: por dataset `kind`/`source_medium`/`periodicity`, `file_count`, `files` (name/period_start/period_end tal cual) y `fields` (name/type/required/maps_to del contrato), en orden de contrato. | `Onboarding` (datasets/fields) | tdd_coder | no_implementada | CA-06, CA-07, CA-08, CA-09 |
| TSK-05 | Derivación de `totals` en `execute`: `dataset_count = len(datasets)` y `file_count = Σ file_count`. | `Onboarding` (totals) | tdd_coder | no_implementada | CA-10 |
| TSK-06 | Serialización determinista en `write_outputs` (DS-ONB-4): `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)` + newline final; garantiza igualdad byte a byte entre corridas. | `Onboarding` (write determinista) | tdd_coder | no_implementada | CA-13 |
| TSK-07 | Validación de coherencia de contenido en `validate` (tras `super().validate`), fallando a la primera inconsistencia con `FlowContractError` sin escribir: levels no vacíos; claves de miembro exactas; `field.name` único; `required` booleano; enums; `maps_to` válido; fechas `YYYY-MM-DD` y `period_start ≤ period_end`. | `Onboarding.validate` (contenido) | tdd_coder | no_implementada | CA-14, CA-15, CA-16, CA-17, CA-18, CA-19, CA-21 |
| TSK-08 | Refactor: consolidar/limpiar `onboarding.py` (factorizar helpers de jerarquía/dataset/validación) y la suite, manteniendo todo verde. | Refactor (sin cambio de comportamiento) | tdd_refactor | no_implementada | CA-01…CA-21 |
| TSK-09 | Test de integración end-to-end (`Onboarding().run(ctx)` sobre el fixture real vía core CONFORME; compara `map_client_data.json` contra un esperado fijo; verifica no-escritura en bronze/silver/gold). | `tests/integration/test_onboarding_integration.py` | integration_tester | no_implementada | CA-01, CA-12, CA-13 |

### 4.2 Tareas de test (una por caso del bucle; responsable `tdd_tester`)

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-10 | Helper/fixture: escribe el `contract_data.json` válido (ventas+inventario, 4+4 niveles) bajo `ctx.outputs_dir/"010_discovery/"` y construye `ctx` con `create_client` bajo `tmp_path`. | fixture válido | tdd_tester | no_implementada | andamiaje (CA-01) |
| TSK-11 | Test caso 1: `run(ctx)` escribe `map_client_data.json` en la ruta esperada y devuelve `FlowResult(success=True, outputs=[esa ruta])`; el archivo existe. | test caso 1 | tdd_tester | no_implementada | CA-01 |
| TSK-12 | Test caso 2: `Onboarding` hereda `Flow`, declara `requires`/`produces` correctos y completa las 4 fases sin sobreescribir `run`. | test caso 2 | tdd_tester | no_implementada | CA-11 |
| TSK-13 | Test caso 3: `hierarchies.product.levels == [...]` (orden declarado) y `depth == 4`. | test caso 3 | tdd_tester | no_implementada | CA-02 |
| TSK-14 | Test caso 4: `hierarchies.geography.levels == [...]` y `depth == 4`. | test caso 4 | tdd_tester | no_implementada | CA-03 |
| TSK-15 | Test caso 5: `unique_values`/`unique_counts` por nivel = distintos observados en orden alfabético (p. ej. `familia == ["Bebidas","Snacks"]`, `ciudad == ["Bogota","Medellin"]`). | test caso 5 | tdd_tester | no_implementada | CA-04 |
| TSK-16 | Test caso 6: los 2 datasets aparecen con `kind`/`source_medium`/`periodicity` correctos y en orden de contrato (ventas, luego inventario). | test caso 6 | tdd_tester | no_implementada | CA-06 |
| TSK-17 | Test caso 7: `file_count == 1` (ventas) y `== 2` (inventario); cada `files[*]` refleja name/period_start/period_end del contrato (incl. multi-año 2023→2025). | test caso 7 | tdd_tester | no_implementada | CA-07 |
| TSK-18 | Test caso 8: `fields` expone name/type/required/maps_to por columna, incl. `precio_unitario` con `required=false` y `maps_to=null`. | test caso 8 | tdd_tester | no_implementada | CA-08 |
| TSK-19 | Test caso 9: `maps_to` proviene del contrato, no del nombre (`sede→geography.sede`, `clase→product.clase`, `cantidad`/`stock→measure`, `fecha→time`). | test caso 9 | tdd_tester | no_implementada | CA-09 |
| TSK-20 | Test caso 10: `totals.dataset_count == 2` y `totals.file_count == 3`. | test caso 10 | tdd_tester | no_implementada | CA-10 |
| TSK-21 | Test caso 11: contrato con `product_hierarchy.levels` de **3** niveles y miembros coherentes ⇒ `depth == 3` y niveles en orden (sin hardcode de 4). | test caso 11 | tdd_tester | no_implementada | CA-05 |
| TSK-22 | Test caso 12: contrato con `product_hierarchy.levels` de **5** niveles (`...,"sku"`) y miembros de 5 claves ⇒ `depth == 5`, 5 niveles en orden y `unique_values`/`unique_counts` para los 5 (incl. `sku`). | test caso 12 | tdd_tester | no_implementada | CA-05b |
| TSK-23 | Test caso 13: dos `run(ctx)` con el mismo `contract_data.json` producen `map_client_data.json` idéntico byte a byte. | test caso 13 | tdd_tester | no_implementada | CA-13 |
| TSK-24 | Test caso 14: tras un `run(ctx)` exitoso no existe nada bajo `ctx.bronze_dir`/`silver_dir`/`gold_dir`; el único artefacto es `map_client_data.json`. | test caso 14 | tdd_tester | no_implementada | CA-12 |
| TSK-25 | Test caso 15: `contract_data.json` ausente ⇒ `run(ctx)` lanza `FlowContractError` en `validate` (existencia base) y no crea el output. | test caso 15 | tdd_tester | no_implementada | CA-20 |
| TSK-26 | Test caso 16: `levels == []` (product o geography) ⇒ `FlowContractError`; sin output. | test caso 16 | tdd_tester | no_implementada | CA-14 |
| TSK-27 | Test caso 17: un miembro con claves que no coinciden exactamente con `levels` (falta/sobra) ⇒ `FlowContractError`; sin output. | test caso 17 | tdd_tester | no_implementada | CA-15 |
| TSK-28 | Test caso 18: `maps_to == "product.<level>"`/`"geography.<level>"` con `<level>` inexistente ⇒ `FlowContractError`; sin output. | test caso 18 | tdd_tester | no_implementada | CA-16 |
| TSK-29 | Test caso 19: enum inválido en `type`/`kind`/`source_medium`/`periodicity` ⇒ `FlowContractError`; sin output. | test caso 19 | tdd_tester | no_implementada | CA-17 |
| TSK-30 | Test caso 20: fecha no `YYYY-MM-DD` o `period_start > period_end` ⇒ `FlowContractError`; sin output. | test caso 20 | tdd_tester | no_implementada | CA-18 |
| TSK-31 | Test caso 21: dos `field.name` duplicados en un dataset ⇒ `FlowContractError`; sin output. | test caso 21 | tdd_tester | no_implementada | CA-19 |
| TSK-32 | Test caso 22: ante una inconsistencia de contrato (p. ej. CA-14…CA-19), el fallo ocurre en `validate` (antes de `execute`/`write_outputs`): no queda `map_client_data.json` ni salida parcial. | test caso 22 | tdd_tester | no_implementada | CA-21 |

---

## 5. Estrategia de Test

- **Unit** en `tests/flows/test_onboarding.py`: ejercita `Onboarding` en proceso (sin `subprocess`), rápido y determinista.
  `ClientContext` construido vía `create_client(NAME, tmp_path/"clients")` (core CONFORME). El core `Flow`/`ClientContext`/
  `create_client` **no** se re-testea aquí (tiene sus suites verdes; NC-3): se usa como fixture.
- **Fixtures / datos de prueba:**
  - **Válido** (TSK-10): el `contract_data.json` del §Contratos de Datos de la spec (ventas + inventario, 4+4 niveles,
    archivo multi-año, columna opcional `maps_to=null`), escrito bajo `ctx.outputs_dir/"010_discovery/"`.
  - **Variantes de profundidad** (casos 11–12): mismo esquema con `levels` de 3 y de 5 niveles + miembros coherentes.
  - **Inconsistentes** (casos 16–22): mutaciones puntuales del dict válido (levels vacío, claves de miembro,
    `maps_to` a nivel inexistente, enum inválido, fecha/rango inválido, `field.name` duplicado).
  - **Ausente** (caso 15): no se escribe el `contract_data.json`.
- **Casos de error:** `pytest.raises(FlowContractError)` + aserción de que `produces[0].path(ctx)` **no** existe (sin salida parcial).
- **Determinismo (caso 13):** dos `run(ctx)` y comparación byte a byte (`read_bytes()`), o hash.
- **Integración (`integration_tester`, TSK-09):** end-to-end sobre el fixture real, comparando el JSON producido contra
  un esperado fijo y verificando la invariante de no tocar `bronze/`/`silver/`/`gold/`.
- **Nota D-037:** algún caso puede resolverse "verde directo" si el código de un caso previo ya lo satisface
  (p. ej. caso 2 tras el caso 1). El bucle lo decide caso a caso; aquí solo se enumeran.

---

## 6. Casos de Test (lista ordenada para el bucle TDD)

Orden: **tracer bullet primero** (camino feliz mínimo end-to-end que produce `map_client_data.json`), luego
enriquecimiento del mapa, luego profundidad dinámica y determinismo, y por último los casos de fallo. Deben coincidir
con `stages.tdd.cases[]` de `state.json`. Cada caso = **un** test que falla primero. Trazabilidad al `CA-xx` entre paréntesis.

| id | Descripción (verificable) | Tareas (`TSK-xx`) | Trazabilidad → CA |
|---|---|---|---|
| 1 | `run(ctx)` sobre el fixture válido escribe `map_client_data.json` en `ctx.outputs_dir/"020_onboarding/map_client_data.json"` y devuelve `FlowResult(success=True, outputs=[esa ruta])`; el archivo existe. | TSK-11, TSK-02, TSK-10 | CA-01 |
| 2 | `Onboarding` hereda `Flow`, declara `requires`/`produces` con los `Artifact` esperados y completa las 4 fases sin sobreescribir `run`. | TSK-12, TSK-02 | CA-11 |
| 3 | `hierarchies.product.levels == ["familia","categoria","subcategoria","clase"]` y `depth == 4`. | TSK-13, TSK-03 | CA-02 |
| 4 | `hierarchies.geography.levels == ["region","pais","ciudad","sede"]` y `depth == 4`. | TSK-14, TSK-03 | CA-03 |
| 5 | `unique_values`/`unique_counts` por nivel = distintos observados en orden alfabético (`familia==["Bebidas","Snacks"]`, `ciudad==["Bogota","Medellin"]`). | TSK-15, TSK-03 | CA-04 |
| 6 | Los 2 datasets aparecen con `kind`/`source_medium`/`periodicity` correctos, en orden de contrato (ventas, inventario). | TSK-16, TSK-04 | CA-06 |
| 7 | `file_count == 1` (ventas) y `== 2` (inventario); cada `files[*]` refleja name/period_start/period_end (incl. multi-año 2023→2025). | TSK-17, TSK-04 | CA-07 |
| 8 | `fields` expone name/type/required/maps_to por columna, incl. `precio_unitario` con `required=false` y `maps_to=null`. | TSK-18, TSK-04 | CA-08 |
| 9 | `maps_to` proviene del contrato, no del nombre (`sede→geography.sede`, `clase→product.clase`, `cantidad`/`stock→measure`, `fecha→time`). | TSK-19, TSK-04 | CA-09 |
| 10 | `totals.dataset_count == 2` y `totals.file_count == 3`. | TSK-20, TSK-05 | CA-10 |
| 11 | Contrato con `product_hierarchy.levels` de **3** niveles ⇒ `depth == 3` y niveles en orden (sin hardcode de 4). | TSK-21, TSK-03 | CA-05 |
| 12 | Contrato con `product_hierarchy.levels` de **5** niveles ⇒ `depth == 5`, 5 niveles en orden y `unique_values`/`unique_counts` para los 5 (incl. `sku`). | TSK-22, TSK-03 | CA-05b |
| 13 | Dos `run(ctx)` con el mismo input producen `map_client_data.json` idéntico byte a byte. | TSK-23, TSK-06 | CA-13 |
| 14 | Tras un `run(ctx)` exitoso no existe nada bajo `bronze/`/`silver/`/`gold/`; el único artefacto es `map_client_data.json`. | TSK-24, TSK-02 | CA-12 |
| 15 | `contract_data.json` ausente ⇒ `FlowContractError` en `validate` (existencia base); sin output. | TSK-25, TSK-02 | CA-20 |
| 16 | `levels == []` (product o geography) ⇒ `FlowContractError`; sin output. | TSK-26, TSK-07 | CA-14 |
| 17 | Miembro con claves que no coinciden exactamente con `levels` ⇒ `FlowContractError`; sin output. | TSK-27, TSK-07 | CA-15 |
| 18 | `maps_to` a un `<level>` inexistente ⇒ `FlowContractError`; sin output. | TSK-28, TSK-07 | CA-16 |
| 19 | Enum inválido (`type`/`kind`/`source_medium`/`periodicity`) ⇒ `FlowContractError`; sin output. | TSK-29, TSK-07 | CA-17 |
| 20 | Fecha no `YYYY-MM-DD` o `period_start > period_end` ⇒ `FlowContractError`; sin output. | TSK-30, TSK-07 | CA-18 |
| 21 | Dos `field.name` duplicados en un dataset ⇒ `FlowContractError`; sin output. | TSK-31, TSK-07 | CA-19 |
| 22 | Ante cualquier inconsistencia, el fallo ocurre en `validate` (antes de `execute`/`write_outputs`): no queda salida parcial. | TSK-32, TSK-07 | CA-21 |

### Cobertura CA → caso (los 22 CA quedan cubiertos)

| CA | Caso | CA | Caso | CA | Caso |
|---|---|---|---|---|---|
| CA-01 | 1 | CA-07 | 7 | CA-14 | 16 |
| CA-02 | 3 | CA-08 | 8 | CA-15 | 17 |
| CA-03 | 4 | CA-09 | 9 | CA-16 | 18 |
| CA-04 | 5 | CA-10 | 10 | CA-17 | 19 |
| CA-05 | 11 | CA-11 | 2 | CA-18 | 20 |
| CA-05b | 12 | CA-12 | 14 | CA-19 | 21 |
| CA-06 | 6 | CA-13 | 13 | CA-20 | 15 |
|  |  |  |  | CA-21 | 22 |

---

## 7. Notas y Riesgos (NC-1 / NC-6)

- **Sin puntos abiertos que bloqueen el GATE:** las 5 decisiones de la spec (DS-ONB-1 reutilizar `FlowContractError`;
  DS-ONB-2 esquema de `map_client_data.json`; DS-ONB-3 únicos por nivel = distintos alfabéticos + conteo; DS-ONB-4
  determinismo byte a byte; DS-ONB-5 hooks/orden de validación + `mkdir`) fueron **aprobadas por el humano** con la spec.
  Este plan las implementa sin reabrirlas.
- **Profundidad dinámica (CA-05/CA-05b):** requisito explícito; `depth = len(levels)` y las variantes de 3 y 5 niveles
  garantizan que no se hardcodee 4. Riesgo típico: iterar sobre índices fijos; se cubre con ambos casos límite.
- **Determinismo (CA-13):** único punto sensible de serialización; se centraliza en `write_outputs` (TSK-06) y se
  verifica byte a byte.
- **NC-3 (quirúrgico):** no se toca `flow.py`/`context.py`/`scaffold.py`. Si durante el bucle apareciera la necesidad
  de modificar el core, se **detiene** y se consulta (NC-6): no se asume.
- **Alcance diferido a `stab_1`** (feature_contract): `kind` no ejercitados por el fixture (`ordenes_compra`,
  `devoluciones`, `promociones`, `precios`), `source_medium` ≠ `csv`, mensajes de error enriquecidos y jerarquías más
  variadas. Fuera de esta banda (NC-2).
