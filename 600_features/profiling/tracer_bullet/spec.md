# Spec — profiling (banda `tracer_bullet`)

> Artefacto de la etapa 2 (`spec_writer`). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables. Cada criterio se **enlaza a una historia de usuario** (`HU-xx`) de `definition.md`. **Requiere aprobación humana** (gate) antes de planear.

## Resumen
Esqueleto vertical mínimo del flujo **040 Profiling** como `Flow` concreto que lee el reporte de su predecesor (`ingestion_report.json`) y produce un `profiling_report.json` mínimo (con `success`), y que **aloja y ejercita el gate de progresión entre flujos** (`D-080` puntos 1-3): `profiling` no corre si `ingestion` no terminó con `success == true`, salvo `--force`.

## Decisiones de Diseño (supuestos abiertos resueltos — NC-6)
Los cuatro supuestos que `definition.md` dejó explícitamente para esta etapa se resuelven aquí, eligiendo la opción más simple consistente con el código existente (NC-2/NC-3). El *cómo* fino es de `plan_builder`; aquí se fija el **contrato de comportamiento**.

- **DS-PROF-1 — Dónde vive el gate: en la capa de despacho de la CLI (`_dispatch_run` en `src/foda/cli.py`), antes de invocar `flow.run(ctx)`.**
  - *Alternativas:* (A) dentro de `Profiling.validate()`; (B) en `_dispatch_run` (elegida); (C) en `orchestrator.resolve_flow`.
  - *Justificación:* el gate es una política de `foda run` (`D-080`: "falla con exit 1, sin escribir nada"), y el flag `--force` es un argumento de la CLI (`run_parser`). Ponerlo en `Profiling.validate()` obligaría a propagar `--force` **dentro** del contrato de `Flow` (`run(ctx)`/`ClientContext`), ampliándolo sin necesidad (contra NC-2/NC-3 y contra la nota de la propia definición). Además, `_dispatch_run` ya es el punto donde hoy se traducen fallos a `stderr` + código 1 **antes** de escribir salida, por lo que la garantía "sin escribir nada" es natural: si el gate no pasa, nunca se llama a `flow.run(ctx)`. `Profiling` queda como un `Flow` mínimo y puro, análogo a `Ingestion`/`Onboarding`.
  - *Nota:* la comprobación de **existencia** de `ingestion_report.json` (que es un `requires` de `Profiling`) sigue viviendo en `Flow.validate()` base (lanza `FlowContractError`), **dentro** de `flow.run`. El gate en `_dispatch_run` es complementario y comprueba el **contenido** (`success`), no la existencia.

- **DS-PROF-2 — Relación predecesor→sucesor: mapa literal explícito en `orchestrator.py`, análogo a `FLOWS`.**
  - Se añade `PREDECESSORS: dict[str, str] = {"profiling": "ingestion"}` (registro literal, sin descubrimiento dinámico, mismo estilo que `FLOWS`).
  - El par `ingestion → onboarding` **no** se incluye: `onboarding` es "todo o nada" y no emite campo `success`; el gate por `success` solo aplica a sucesores de un flujo que puede escribir `success:false` (`ingestion` en adelante), coherente con las consecuencias de `D-080` y su excepción del punto 5. Un flujo sin entrada en `PREDECESSORS` no tiene gate (pasa siempre).
  - La ruta del reporte del predecesor se resuelve reutilizando la maquinaria existente: `resolve_flow("ingestion").produces[0].path(ctx)` → `020_outputs/030_ingestion/ingestion_report.json` (no se hardcodea la ruta relativa; se reusa `ClientContext`).

- **DS-PROF-3 — Formato de `profiling_report.json` y destino de la advertencia de `--force`.**
  - `profiling_report.json` mínimo, mismo estilo de campos de identidad que `ingestion_report.json` (esquema abajo). Campos: `schema_version` (`"0.1"`), `client` (`ctx.name`), `flow` (`"profiling"`), `success` (boolean). El único campo **vinculante** por `definition.md` es `success`; los otros tres se incluyen por consistencia mínima con `ingestion_report`. Serialización determinista: `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)` + newline final (idéntico a `ingestion`/`onboarding`).
  - **Advertencia de `--force`: se emite a `stderr`** (una línea) identificando que se sobrepasó el gate del predecesor (`ingestion`) pese a `success != true`. *Justificación:* `stderr` es el canal estándar para diagnósticos, no contamina `stdout` (que lleva la línea de éxito y las rutas de salida que un script podría parsear), es trivialmente testeable (`capfd`/`capsys`) y **no** amplía el contrato de `Flow` ni el esquema del reporte (poner la advertencia en el reporte exigiría pasar `--force` al flujo; un archivo de log es sobre-ingeniería para un tracer bullet). El exit code lo sigue fijando `flow.run` (0 si `success`).

- **DS-PROF-4 — Propagación del flag `--force`: argumento de `run_parser` → `args.force` → `_dispatch_run`.**
  - Se añade `run_parser.add_argument("--force", action="store_true")` (default `False`). `_dispatch_run(args, clients_root)` ya recibe `args`, así que lee `args.force` directamente y decide bloquear vs. advertir-y-continuar. **No** se toca `ClientContext` ni la firma de `Flow.run` (NC-2/NC-3).
  - Contrato recomendado del evaluador del gate (en `orchestrator.py`, puro salvo lectura del reporte): `evaluate_predecessor_gate(flow_name: str, ctx: ClientContext) -> str | None` → devuelve `None` si el gate pasa (o si el flujo no tiene predecesor registrado), o un **mensaje legible** (motivo, nombrando al predecesor) si no pasa. `_dispatch_run` lo usa así: si el mensaje es `None` → continúa; si no y **sin** `--force` → imprime el motivo a `stderr` y retorna 1 (sin `flow.run`); si no y **con** `--force` → imprime la advertencia a `stderr` y continúa a `flow.run`.

## Contratos de Datos / Artefactos
| Dirección | Artefacto | Ruta (relativa al cliente) | Formato | Esquema / campos |
|---|---|---|---|---|
| requiere | `ingestion_report` | `020_outputs/030_ingestion/ingestion_report.json` | JSON | Reporte de `ingestion`; el gate lee **solo** su campo `success` (boolean). Producido por `Ingestion` (CONFORME). |
| produce | `profiling_report` | `020_outputs/040_profiling/profiling_report.json` | JSON | `schema_version:"0.1"`, `client:str` (=`ctx.name`), `flow:"profiling"`, `success:bool`. |

Ejemplo de `profiling_report.json` (camino feliz):
```json
{
  "client": "acme",
  "flow": "profiling",
  "schema_version": "0.1",
  "success": true
}
```

## Comportamiento Esperado
1. **Integración como `Flow` (HU-01).** `Profiling` hereda de `Flow` (`src/foda/core/flow.py`), define `name = "profiling"`, `requires = [Artifact(ingestion_report, base="outputs", relative="030_ingestion/ingestion_report.json")]` y `produces = [Artifact(profiling_report, base="outputs", relative="040_profiling/profiling_report.json")]`. **No** sobreescribe `run()`: usa el template method base que invoca `load_inputs → validate → execute → write_outputs` en orden. Completa las 4 fases (análogo a `Ingestion`/`Onboarding`).
2. **Registro.** `Profiling` se registra en `FLOWS` (`orchestrator.py`) bajo la clave `"profiling"`, de modo que `resolve_flow("profiling")` devuelve una instancia y `foda status`/`foda run` la reconocen.
3. **Fase `validate` (base).** Comprueba la existencia de `ingestion_report.json` (su único `requires`). Si falta, lanza `FlowContractError` nombrándolo, **antes** de `execute`/`write_outputs` (no se escribe `profiling_report.json`).
4. **Fase `execute`/`write_outputs` (esqueleto).** Cuando el flujo corre, produce `FlowResult(success=True, outputs=[.../profiling_report.json])` y escribe el reporte mínimo determinista. Esta banda **no** calcula salud de datos, **no** lee `bronze/` ni exporta csv/xlsx.
5. **Gate de progresión (`_dispatch_run`, antes de `flow.run`) (HU-02/03/04).** Para `foda run <cliente> --flow profiling`:
   - Se resuelve el predecesor (`ingestion`) vía `PREDECESSORS` y se evalúa `evaluate_predecessor_gate("profiling", ctx)`.
   - **Gate pasa** (`ingestion_report.json` existe y `success == true`): se ejecuta `flow.run(ctx)` con normalidad; exit 0 si `success:true`.
   - **Gate no pasa** (reporte ausente, o `success != true`) y **sin** `--force`: se imprime un mensaje claro a `stderr` que identifica al predecesor `ingestion` y el motivo, se retorna **exit 1** y **no se invoca `flow.run`** (no se escribe `profiling_report.json` ni ningún otro artefacto de profiling).
   - **Gate no pasa** y **con** `--force`: se imprime una **advertencia a `stderr`** (predecesor + `success != true`) y se continúa a `flow.run(ctx)` (el reporte se produce con normalidad; exit 0 si `success:true`).
6. **Sin predecesor registrado.** Para flujos sin entrada en `PREDECESSORS` (p. ej. `onboarding`, `ingestion`), el gate es no-op: `foda run` se comporta como hoy (regresión: la nueva lógica no introduce fricción).

## Casos Límite y Errores
- **`ingestion_report.json` con `success:false`, sin `--force`** → gate bloquea: exit 1, mensaje a `stderr` identificando `ingestion` + motivo, sin escribir nada de profiling (CA-07/CA-08).
- **`ingestion_report.json` con `success:false`, con `--force`** → advertencia a `stderr`, `flow.run` corre, `profiling_report.json` producido, exit 0 (CA-09/CA-10).
- **`ingestion_report.json` ausente, sin `--force`** → gate bloquea igual (no hay reporte del predecesor que reporte `success == true`): exit 1, mensaje claro, sin escribir nada (CA-13).
- **`ingestion_report.json` ausente, con `--force`** → el gate se sobrepasa, pero `Profiling.validate()` base detecta que falta el `requires` y lanza `FlowContractError` → exit 1 igualmente (el `--force` sobrepasa el gate por `success`, no puede fabricar un insumo requerido ausente). Comportamiento documentado, no adicionalmente exigido por una HU.
- **`success:true`, con `--force`** → corre sin bloqueo y **sin** advertencia espuria (la advertencia solo se emite cuando el gate habría fallado) (CA-11).
- **Cliente inexistente** → `_build_client_context` retorna `None` → exit 1 antes de evaluar el gate (comportamiento existente, sin cambios).

## Interfaces / Firmas Públicas
- `class Profiling(Flow)` con `name = "profiling"`, `requires`, `produces` (atributos de clase con `Artifact`), y las 4 fases; `Profiling().run(ctx) -> FlowResult`, **sin** sobreescribir `run`.
- `orchestrator.FLOWS` incluye `"profiling": Profiling`.
- `orchestrator.PREDECESSORS: dict[str, str]` con `{"profiling": "ingestion"}`.
- `orchestrator.evaluate_predecessor_gate(flow_name: str, ctx: ClientContext) -> str | None` (o equivalente): `None` si el gate pasa o no hay predecesor; mensaje legible si no pasa.
- CLI: `foda run <name> --flow <flow> [--force]` (`--force` es `store_true`, default `False`).

## Criterios de Aceptación (verificables)
> Cada criterio lleva un **código `CA-xx`** (único en la feature) y se **enlaza a la(s) `HU-xx`** que satisface. El plan trazará cada `TSK-xx` a un `CA-xx`.

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | `Profiling` es subclase de `Flow`; `Profiling.name == "profiling"`; `requires` es `[Artifact]` con `name=="ingestion_report"`, `base=="outputs"`, `relative=="030_ingestion/ingestion_report.json"`; `produces` es `[Artifact]` con `name=="profiling_report"`, `base=="outputs"`, `relative=="040_profiling/profiling_report.json"`. | HU-01 |
| CA-02 | `Profiling` **no** sobreescribe el template method: `Profiling.run is Flow.run`. Una ejecución invoca las 4 fases `load_inputs → validate → execute → write_outputs` en ese orden. | HU-01 |
| CA-03 | Con `ingestion_report.json` (`success:true`) presente, `Profiling().run(ctx)` devuelve `FlowResult(success=True, outputs=[.../040_profiling/profiling_report.json])`. | HU-01, HU-04, HU-05 |
| CA-04 | Tras esa ejecución existe `020_outputs/040_profiling/profiling_report.json`, parseable como JSON, con `success == true` (boolean) y campos `schema_version=="0.1"`, `client==ctx.name`, `flow=="profiling"`; serialización determinista (`sort_keys`, `indent=2`, newline final). | HU-05 |
| CA-05 | Si `ingestion_report.json` no existe, `Profiling().validate(ctx)` lanza `FlowContractError` nombrando el artefacto ausente, y no se escribe `profiling_report.json` (el fallo ocurre en `validate`, antes de `execute`/`write_outputs`). | HU-01 |
| CA-06 | `foda run <cliente> --flow profiling` con `ingestion_report.json` (`success:true`) y sin `--force` → exit 0, mensaje de completado en `stdout`, y `profiling_report.json` presente. | HU-04 |
| CA-07 | `foda run <cliente> --flow profiling` con `ingestion_report.json` (`success:false`) y sin `--force` → exit 1 y un mensaje a `stderr` que identifica al predecesor `ingestion` y el motivo (predecesor sin `success == true`). | HU-02 |
| CA-08 | En el escenario de CA-07 (gate bloquea sin `--force`) **no** se escribe `profiling_report.json` ni ningún otro artefacto bajo `020_outputs/040_profiling/` (el gate corta antes de `flow.run`). | HU-02 |
| CA-09 | `foda run <cliente> --flow profiling --force` con `ingestion_report.json` (`success:false`) → exit 0 y `profiling_report.json` presente (el flujo corre pese al gate). | HU-03 |
| CA-10 | En el escenario de CA-09, se emite una **advertencia a `stderr`** que indica que se forzó la ejecución sobrepasando el gate del predecesor `ingestion` (por `success != true`). | HU-03 |
| CA-11 | `foda run <cliente> --flow profiling --force` con `ingestion_report.json` (`success:true`) → exit 0, `profiling_report.json` presente y **sin** advertencia de gate en `stderr` (la advertencia solo aparece cuando el gate habría fallado). | HU-03, HU-04 |
| CA-12 | Existe `PREDECESSORS == {"profiling": "ingestion"}`; para un flujo sin entrada allí (p. ej. `foda run <cliente> --flow ingestion`) el gate es no-op y `foda run` se comporta como antes de esta feature (no bloquea por `success`). | HU-02 |
| CA-13 | `foda run <cliente> --flow profiling` con `ingestion_report.json` **ausente** y sin `--force` → exit 1, mensaje claro a `stderr` (predecesor `ingestion` sin reporte con `success == true`) y sin escribir ningún artefacto de profiling. | HU-02 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` debe estar cubierta por **≥ 1** `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02, CA-03, CA-05 |
| HU-02 | CA-07, CA-08, CA-12, CA-13 |
| HU-03 | CA-09, CA-10, CA-11 |
| HU-04 | CA-03, CA-06, CA-11 |
| HU-05 | CA-03, CA-04 |

Todas las HU (HU-01…HU-05) quedan cubiertas por ≥ 1 CA.

## No-Objetivos
- **Lógica de salud de datos** (indicador global %, desglose por tipo de problema, pareto). Diferido a `stab_1`.
- **Lectura/auditoría real de `bronze/`**: esta banda solo consume el reporte JSON del predecesor (y el gate solo lee su `success`).
- **Exportables csv/xlsx** (`foda export --flow profiling`).
- **Comparación contra `client_register.yaml`** (Discovery real no existe).
- **Uso de LLM** (Profiling es determinista, §6).
- **Gate genérico / de flujos anteriores a `ingestion`**: `discovery`/`onboarding` quedan exceptuados (`D-080` punto 5); `PREDECESSORS` contiene solo `profiling → ingestion` en esta banda.
- **Rediseño del orquestador / CLI**: solo se añaden `Profiling` a `FLOWS`, el mapa `PREDECESSORS`, el evaluador del gate y el flag `--force`; no se reestructura `run`/`status`.
- **Punto 4 de `D-080`** (exit code que refleja `success`): ya implementado por T-035, fuera de alcance.
</content>
</invoke>
