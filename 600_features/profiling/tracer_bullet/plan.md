# Plan — profiling (banda `tracer_bullet`)

> Artefacto de la etapa 3 (`plan_builder`). Define el **cómo** de la implementación, descompone el trabajo en **tareas atómicas codificadas y trazables** (`TSK-xx → CA-xx`) y **enumera los casos de test** que guiarán el bucle TDD. **Requiere aprobación humana** (gate) antes de arrancar el bucle.

## Enfoque Técnico

Dos piezas, coherentes con las cuatro decisiones de diseño fijadas por la spec (DS-PROF-1..4). Cambios **quirúrgicos** (NC-2/NC-3): no se reestructura `run`/`status`, no se toca `ClientContext` ni la firma de `Flow.run`, no se amplía `Artifact`.

### A. `Profiling(Flow)` — esqueleto vertical del flujo 040
Nuevo módulo `src/foda/flows/f040_profiling/profiling.py`, calcado del patrón de `src/foda/flows/f030_ingestion/ingestion.py` (mismo estilo de `Artifact` para `requires`/`produces`, misma serialización determinista, mismo reparto `execute` arma en memoria / `write_outputs` persiste).

- Atributos de clase:
  - `name = "profiling"`.
  - `requires = [Artifact("ingestion_report", base="outputs", relative="030_ingestion/ingestion_report.json")]`.
  - `produces = [Artifact("profiling_report", base="outputs", relative="040_profiling/profiling_report.json")]`.
- **No** se sobreescribe `run()`: hereda el template method base (`load_inputs → validate → execute → write_outputs`). La existencia del `requires` la comprueba `Flow.validate()` base (lanza `FlowContractError`); no se sobreescribe `validate` (a diferencia de `Ingestion`, aquí no hace falta, NC-2).
- `execute(ctx)`: arma en memoria el reporte mínimo `{"schema_version": "0.1", "client": ctx.name, "flow": "profiling", "success": True}` (esta banda no lee `bronze/`, no calcula salud de datos) y devuelve `FlowResult(success=True, outputs=[self.produces[0].path(ctx)])`. Guarda el reporte en estado de instancia (`self._report`), igual que `Ingestion`.
- `write_outputs(ctx, result)`: `path.parent.mkdir(parents=True, exist_ok=True)` y escribe con `json.dumps(self._report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"` (idéntico a `Ingestion.write_outputs`, sin la parte de copia a bronze).

### B. Gate de progresión entre flujos (`D-080` puntos 1-3)
- **`orchestrator.py`** (registro literal, estilo `FLOWS`, sin descubrimiento dinámico):
  - `FLOWS` gana la entrada `"profiling": Profiling`.
  - Nuevo mapa `PREDECESSORS: dict[str, str] = {"profiling": "ingestion"}` (DS-PROF-2). Un flujo sin entrada → sin gate.
  - Nueva función pura (salvo lectura del reporte) `evaluate_predecessor_gate(flow_name: str, ctx: ClientContext) -> str | None` (DS-PROF-4):
    - Si `flow_name` no está en `PREDECESSORS` → `None` (no-op).
    - Resuelve la ruta del reporte del predecesor con `resolve_flow(<pred>).produces[0].path(ctx)` (no se hardcodea la ruta relativa, DS-PROF-2).
    - Si el reporte no existe → mensaje legible que nombra al predecesor (`ingestion`) y el motivo (sin reporte con `success == true`).
    - Si existe: lo parsea y lee **solo** `success`; si `success != true` → mensaje legible (predecesor + motivo); si `success == true` → `None`.
- **`cli.py`** (DS-PROF-1/DS-PROF-4): el gate vive en `_dispatch_run`, **antes** de `flow.run(ctx)`:
  - `run_parser.add_argument("--force", action="store_true")` (default `False`) → `args.force`.
  - Tras resolver el flujo y construir `ctx`, y **antes** de `flow.run(ctx)`: `msg = evaluate_predecessor_gate(args.flow, ctx)`.
    - `msg is None` → continúa a `flow.run(ctx)` como hoy (camino feliz / flujo sin predecesor).
    - `msg` y **sin** `--force` → imprime `msg` a `stderr`, `return 1` (no se invoca `flow.run`, no se escribe nada de profiling).
    - `msg` y **con** `--force` → imprime una **advertencia a `stderr`** (una línea: se forzó sobrepasando el gate del predecesor `ingestion`) y continúa a `flow.run(ctx)`.
  - El exit code del camino que continúa lo sigue fijando la lógica existente (`result.success`, T-035). El resto de `_dispatch_run` (traducción de `FlowContractError`, cliente inexistente) no cambia: el caso "reporte ausente + `--force`" cae en `flow.run` → `Flow.validate()` base lanza `FlowContractError` → exit 1 ya traducido.

## Archivos Afectados
- `src/foda/flows/f040_profiling/__init__.py` — **crear** (paquete del flujo 040, vacío, como `f030_ingestion/__init__.py`).
- `src/foda/flows/f040_profiling/profiling.py` — **crear** (`Profiling(Flow)`).
- `src/foda/orchestrator.py` — **modificar** (import de `Profiling`; entrada en `FLOWS`; mapa `PREDECESSORS`; función `evaluate_predecessor_gate`).
- `src/foda/cli.py` — **modificar** (`--force` en `run_parser`; wiring del gate en `_dispatch_run`; import de `evaluate_predecessor_gate`).
- `tests/flows/test_profiling.py` — **crear** (unit del `Flow` `Profiling`, CA-01..CA-05).
- `tests/test_orchestrator.py` — **modificar** (registro `"profiling"`, `PREDECESSORS`, `evaluate_predecessor_gate`).
- `tests/cli/test_profiling_gate_cli.py` — **crear** (gate + `--force` vía `main(argv)`, CA-06..CA-13 y borde documentado).
- `tests/integration/test_profiling_integration.py` — **crear** (end-to-end, responsabilidad de `integration_tester`).

> El código de producción vive en `src/foda/…` y los tests en `tests/…`; **nada** de código o test se escribe bajo `600_features/`.

## Tareas
> `TSK-xx` atómicas. Reglas: un solo responsable, un solo entregable, codificar ≠ testear. **Estado** inicial `no_implementada`; el responsable es su único escritor (`D-021`).

| ID | Descripción (atómica) | Entregable | Responsable | Estado | Trazabilidad → CA |
|---|---|---|---|---|---|
| TSK-01 | Test: `Profiling` es subclase de `Flow` con `name`/`requires`/`produces` correctos | Test en `tests/flows/test_profiling.py` | tdd_tester | no_implementada | CA-01 |
| TSK-02 | Código: crear paquete `f040_profiling` y clase `Profiling(Flow)` con atributos `name`/`requires`/`produces` | `src/foda/flows/f040_profiling/{__init__,profiling}.py` | tdd_coder | no_implementada | CA-01 |
| TSK-03 | Test: `Profiling.run is Flow.run` (no sobreescribe) y las 4 fases se invocan en orden | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-02 |
| TSK-04 | Test: `run(ctx)` con `ingestion_report` (`success:true`) devuelve `FlowResult(success=True, outputs=[…/profiling_report.json])` | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-03 |
| TSK-05 | Código: `Profiling.execute(ctx)` arma el reporte mínimo en memoria y devuelve el `FlowResult` | `profiling.py::execute` | tdd_coder | no_implementada | CA-03 |
| TSK-06 | Test: el `profiling_report.json` existe, es JSON parseable, `success==true` y `schema_version`/`client`/`flow` correctos; serialización determinista | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-04 |
| TSK-07 | Código: `Profiling.write_outputs(ctx, result)` crea la carpeta y escribe el reporte determinista (`sort_keys`, `indent=2`, newline) | `profiling.py::write_outputs` | tdd_coder | no_implementada | CA-04 |
| TSK-08 | Test: sin `ingestion_report.json`, `Profiling().validate(ctx)` lanza `FlowContractError` nombrando el artefacto y no se escribe el reporte | Test en `test_profiling.py` | tdd_tester | no_implementada | CA-05 |
| TSK-09 | Test: `resolve_flow("profiling")` devuelve una instancia de `Profiling` (registro en `FLOWS`) | Test en `tests/test_orchestrator.py` | tdd_tester | no_implementada | CA-06 |
| TSK-10 | Código: registrar `"profiling": Profiling` en `FLOWS` (import incluido) | `src/foda/orchestrator.py` | tdd_coder | no_implementada | CA-06 |
| TSK-11 | Test: `PREDECESSORS == {"profiling": "ingestion"}` y `evaluate_predecessor_gate` devuelve `None` para un flujo sin predecesor (p. ej. `ingestion`) | Test en `test_orchestrator.py` | tdd_tester | no_implementada | CA-12 |
| TSK-12 | Código: mapa `PREDECESSORS` + `evaluate_predecessor_gate` (esqueleto: `None` si no hay predecesor registrado) | `orchestrator.py` | tdd_coder | no_implementada | CA-12 |
| TSK-13 | Test: `evaluate_predecessor_gate("profiling", ctx)` devuelve `None` cuando `ingestion_report.json` existe con `success:true` | Test en `test_orchestrator.py` | tdd_tester | no_implementada | CA-06 |
| TSK-14 | Código: `evaluate_predecessor_gate` resuelve la ruta del reporte del predecesor y devuelve `None` si `success == true` | `orchestrator.py::evaluate_predecessor_gate` | tdd_coder | no_implementada | CA-06 |
| TSK-15 | Test: devuelve un mensaje que nombra a `ingestion` cuando `ingestion_report.json` tiene `success:false` | Test en `test_orchestrator.py` | tdd_tester | no_implementada | CA-07 |
| TSK-16 | Código: `evaluate_predecessor_gate` devuelve mensaje legible (predecesor + motivo) si `success != true` | `orchestrator.py::evaluate_predecessor_gate` | tdd_coder | no_implementada | CA-07 |
| TSK-17 | Test: devuelve un mensaje cuando `ingestion_report.json` está ausente | Test en `test_orchestrator.py` | tdd_tester | no_implementada | CA-13 |
| TSK-18 | Código: `evaluate_predecessor_gate` devuelve mensaje si el reporte del predecesor no existe | `orchestrator.py::evaluate_predecessor_gate` | tdd_coder | no_implementada | CA-13 |
| TSK-19 | Test CLI: `foda run <c> --flow profiling` con `success:true` y sin `--force` → exit 0, `stdout` de completado, reporte presente | Test en `tests/cli/test_profiling_gate_cli.py` | tdd_tester | no_implementada | CA-06 |
| TSK-20 | Código: `_dispatch_run` llama `evaluate_predecessor_gate` antes de `flow.run`; si `None` continúa | `src/foda/cli.py::_dispatch_run` | tdd_coder | no_implementada | CA-06 |
| TSK-21 | Test CLI: `success:false` sin `--force` → exit 1, `stderr` nombra `ingestion`+motivo, y **no** se escribe ningún artefacto bajo `040_profiling/` | Test en `test_profiling_gate_cli.py` | tdd_tester | no_implementada | CA-07, CA-08 |
| TSK-22 | Código: `run_parser.add_argument("--force", action="store_true")` (default `False`) | `cli.py::_build_parser` | tdd_coder | no_implementada | CA-07 |
| TSK-23 | Código: `_dispatch_run` — si hay mensaje de gate y **sin** `--force` → `stderr` + `return 1` (antes de `flow.run`) | `cli.py::_dispatch_run` | tdd_coder | no_implementada | CA-07, CA-08 |
| TSK-24 | Test CLI: `--force` con `success:false` → exit 0, reporte presente, y advertencia de gate en `stderr` | Test en `test_profiling_gate_cli.py` | tdd_tester | no_implementada | CA-09, CA-10 |
| TSK-25 | Código: `_dispatch_run` — si hay mensaje de gate y **con** `--force` → advertencia a `stderr` (una línea) y continúa a `flow.run` | `cli.py::_dispatch_run` | tdd_coder | no_implementada | CA-09, CA-10 |
| TSK-26 | Test CLI: `--force` con `success:true` → exit 0, reporte presente, **sin** advertencia de gate en `stderr` | Test en `test_profiling_gate_cli.py` | tdd_tester | no_implementada | CA-11 |
| TSK-27 | Test CLI: `foda run <c> --flow ingestion` (flujo sin predecesor) → gate no-op, comportamiento igual al previo a esta feature | Test en `test_profiling_gate_cli.py` | tdd_tester | no_implementada | CA-12 |
| TSK-28 | Test CLI: `--flow profiling` con `ingestion_report.json` ausente y sin `--force` → exit 1, `stderr` claro, sin artefacto de profiling | Test en `test_profiling_gate_cli.py` | tdd_tester | no_implementada | CA-13 |
| TSK-29 | Test CLI (borde documentado): `--flow profiling --force` con `ingestion_report.json` ausente → el gate se sobrepasa pero `Flow.validate` lanza `FlowContractError` → exit 1 | Test en `test_profiling_gate_cli.py` | tdd_tester | no_implementada | CA-05 |
| TSK-30 | Refactor final de módulo `profiling.py` y del wiring del gate (`orchestrator.py`/`cli.py`) sin cambiar comportamiento | Diff de refactor + suite verde | tdd_refactor | no_implementada | CA-01..CA-13 |
| TSK-31 | Test de integración end-to-end: gate + ejecución de `profiling` vía CLI sobre cliente temporal real | `tests/integration/test_profiling_integration.py` | integration_tester | no_implementada | CA-06..CA-13 |
| TSK-32 | Prueba humana end-to-end de la feature vía CLI (gate `human_test`) | Veredicto humano | humano | no_implementada | CA-01..CA-13 |

> **Sobre las tareas de código faltantes por caso.** Los casos 2 (CA-02), 14 (CA-11), 15 (CA-12 CLI), 16 (CA-13 CLI) y 17 (borde) **no** llevan tarea-código propia: su verde se alcanza sin producción nueva. CA-02 se satisface por herencia (`Profiling` no sobreescribe `run`); CA-11/CA-12-CLI/CA-13-CLI/borde quedan cubiertos por la lógica ya construida en TSK-14/16/18/20/23/25 y por la traducción de `FlowContractError` ya existente en `_dispatch_run`. Son tareas de **test que confirman** comportamiento ya presente (NC-3: no se añade código sin test que lo exija, pero tampoco código que ningún caso nuevo requiera).

## Dependencias y Contratos
- **Consume:** `ingestion_report.json` (`020_outputs/030_ingestion/`), producido por `Ingestion` (CONFORME). El gate lee **solo** su campo `success`.
- **Produce:** `profiling_report.json` (`020_outputs/040_profiling/`), esquema `{schema_version:"0.1", client:str, flow:"profiling", success:bool}`.
- **Reutiliza sin ampliar:** `Flow`/`FlowResult`/`Artifact`/`FlowContractError` (`core/flow.py`), `ClientContext` (`core/context.py`), `resolve_flow`/`FLOWS` (`orchestrator.py`), `_dispatch_run`/`_build_client_context` (`cli.py`).
- **No modifica:** `ClientContext`, la firma de `Flow.run`, ni el esquema de `ingestion_report.json`.

## Estrategia de Test
- **Unit (`tests/flows/test_profiling.py`):** `Profiling` como `Flow` — atributos, no-override de `run`, orden de las 4 fases, camino feliz (`execute`/`write_outputs`), `FlowContractError` por `requires` ausente (CA-01..CA-05). Fixtures: cliente temporal (`create_client` + `ClientContext` sobre `tmp_path`) e `ingestion_report.json` fabricado con `success:true`/`success:false`, en el espíritu de `tests/flows/test_ingestion.py`.
- **Unit (`tests/test_orchestrator.py`):** registro `"profiling"` en `FLOWS`, `PREDECESSORS`, y `evaluate_predecessor_gate` en sus cuatro ramas (sin predecesor / `success:true` / `success:false` / reporte ausente).
- **CLI (`tests/cli/test_profiling_gate_cli.py`):** el gate + `--force` extremo a extremo vía `main(argv)` bajo proyecto+cliente temporal (mismo patrón que `tests/cli/test_flow_orchestrator_cli.py`): `capsys`/`capfd` para `stdout`/`stderr`, exit codes, y presencia/ausencia de `profiling_report.json` en disco. Cubre CA-06..CA-13 y el borde documentado (ausente + `--force`).
- **Integración (`integration_tester`, fuera del bucle rojo/verde):** flujo real punta a punta y coherencia entre las capas (CA-06..CA-13).
- **Fixtures / datos de prueba:** helper local que fabrica un `ingestion_report.json` mínimo (`{schema_version, client, flow:"ingestion", success:<bool>}`) en `020_outputs/030_ingestion/` del cliente temporal; no se depende de correr `Ingestion` real (aislamiento de unidad).

## Casos de Test (bucle TDD)
Ordenados de simple a complejo. Coinciden con `stages.tdd.cases[]` de `state.json`. Cada caso agrupa sus tareas de test y código.

| id | Descripción (verificable) | Tareas (`TSK-xx`) | Trazabilidad → CA |
|---|---|---|---|
| 1 | `Profiling` es subclase de `Flow` con `name=="profiling"`, `requires` = `[ingestion_report @ 030_ingestion/ingestion_report.json]` y `produces` = `[profiling_report @ 040_profiling/profiling_report.json]` | TSK-01, TSK-02 | CA-01 |
| 2 | `Profiling.run is Flow.run` (no sobreescribe el template method) y una ejecución invoca `load_inputs → validate → execute → write_outputs` en ese orden | TSK-03 | CA-02 |
| 3 | Con `ingestion_report.json` (`success:true`) presente, `Profiling().run(ctx)` devuelve `FlowResult(success=True, outputs=[…/040_profiling/profiling_report.json])` | TSK-04, TSK-05 | CA-03 |
| 4 | Tras esa ejecución existe `profiling_report.json`, parseable, con `success==true`, `schema_version=="0.1"`, `client==ctx.name`, `flow=="profiling"` y serialización determinista | TSK-06, TSK-07 | CA-04 |
| 5 | Sin `ingestion_report.json`, `Profiling().validate(ctx)` lanza `FlowContractError` nombrando el artefacto ausente y no se escribe `profiling_report.json` | TSK-08 | CA-05 |
| 6 | `resolve_flow("profiling")` devuelve una instancia de `Profiling` (registro en `FLOWS`) | TSK-09, TSK-10 | CA-06 |
| 7 | `PREDECESSORS == {"profiling": "ingestion"}`; `evaluate_predecessor_gate` devuelve `None` para un flujo sin predecesor registrado | TSK-11, TSK-12 | CA-12 |
| 8 | `evaluate_predecessor_gate("profiling", ctx)` devuelve `None` cuando `ingestion_report.json` existe con `success:true` | TSK-13, TSK-14 | CA-06 |
| 9 | `evaluate_predecessor_gate("profiling", ctx)` devuelve un mensaje que nombra a `ingestion` cuando `ingestion_report.json` tiene `success:false` | TSK-15, TSK-16 | CA-07 |
| 10 | `evaluate_predecessor_gate("profiling", ctx)` devuelve un mensaje cuando `ingestion_report.json` está ausente | TSK-17, TSK-18 | CA-13 |
| 11 | CLI: `foda run <c> --flow profiling` con `success:true` y sin `--force` → exit 0, `stdout` de completado, `profiling_report.json` presente | TSK-19, TSK-20 | CA-06 |
| 12 | CLI: `success:false` sin `--force` → exit 1, `stderr` nombra `ingestion`+motivo, y **no** se escribe ningún artefacto bajo `040_profiling/` | TSK-21, TSK-22, TSK-23 | CA-07, CA-08 |
| 13 | CLI: `--force` con `success:false` → exit 0, `profiling_report.json` presente, y advertencia de gate en `stderr` | TSK-24, TSK-25 | CA-09, CA-10 |
| 14 | CLI: `--force` con `success:true` → exit 0, reporte presente, **sin** advertencia de gate en `stderr` | TSK-26 | CA-11 |
| 15 | CLI: `foda run <c> --flow ingestion` (flujo sin predecesor) → gate no-op, comportamiento igual al previo a la feature | TSK-27 | CA-12 |
| 16 | CLI: `--flow profiling` con `ingestion_report.json` ausente y sin `--force` → exit 1, `stderr` claro, sin artefacto de profiling | TSK-28 | CA-13 |
| 17 | CLI (borde documentado): `--flow profiling --force` con `ingestion_report.json` ausente → gate sobrepasado pero `Flow.validate` lanza `FlowContractError` → exit 1 | TSK-29 | CA-05 |

> Tras el bucle: `tdd_refactor` (TSK-30), `integration_tester` (TSK-31) y el gate humano `human_test` (TSK-32) cierran la feature antes del PR/merge.
