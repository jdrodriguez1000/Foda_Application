# Spec — flow_orchestrator

> Artefacto de la etapa 2 (`spec_writer`). Especifica el **comportamiento observable**: entradas, salidas, contratos, casos límite y criterios de aceptación verificables **codificados (`CA-xx`) y enlazados a las historias de usuario (`HU-xx`)** de `definition.md`. **Requiere aprobación humana** (gate) antes de planear.
>
> Banda: `tracer_bullet`. Fuentes canónicas: `600_features/flow_orchestrator/tracer_bullet/definition.md`, `600_features/flow_orchestrator/feature_contract.md`, `600_features/client_new_cli/tracer_bullet/spec.md` (estilo de CLI, códigos de salida, traducción de excepciones), `src/foda/cli.py`, `src/foda/core/flow.py`, `src/foda/core/context.py`, `src/foda/flows/f020_onboarding/onboarding.py`, `700_architecture/system_design.md` (§4, §11), `800_persistence/decisions.md` (D-021, D-062).

## Resumen
Añade a la CLI `foda` los subcomandos `foda run <cliente> --flow <flujo>` (resuelve el cliente con `ClientContext`, resuelve `<flujo>` a una instancia de `Flow` vía un registro explícito nombre→flujo, y delega en `Flow.run(ctx)`) y `foda status <cliente>` (introspecciona en disco, vía `Artifact.exists(ctx)`, qué artefactos `requires`/`produces` de cada flujo registrado existen), traduciendo los errores esperables (cliente inexistente, flujo desconocido, `FlowContractError`) a mensajes claros en `stderr` + código de salida ≠ 0, sin traceback crudo y con el mismo estilo que `client_new_cli`.

---

## Decisiones formalizadas por spec_writer

La `definition.md` delegó explícitamente tres puntos de confirmación a esta etapa. Se resuelven así (razonamiento en cada punto, NC-1/NC-6). Todos quedan listados abajo como **puntos del GATE humano**; no se asumen en silencio.

### DS-ORQ-1 — Mecanismo de resolución de flujo por nombre (punto de confirmación 1)
- **Decisión:** un **registro literal a nivel de módulo** — un diccionario `FLOWS: dict[str, type[Flow]] = {"onboarding": Onboarding}` — expuesto en un módulo nuevo `src/foda/orchestrator.py`, junto con una función pública `resolve_flow(name: str) -> Flow` que devuelve una **instancia** del flujo (`FLOWS[name]()`), y una forma de iterar los flujos registrados para `foda status` (iterar `FLOWS`). **Ambos** subcomandos (`run` y `status`) resuelven flujos a través de este único registro; **añadir un flujo nuevo = añadir una entrada al diccionario**, sin tocar la lógica de `run`/`status` (HU-05).
- **Razón:** es la solución más simple que satisface HU-05 (NC-2, E4). Hoy existe **un solo** flujo concreto real (`Onboarding`), por lo que una infraestructura de registro con descubrimiento dinámico, decoradores o *entry points* sería sobre-diseño sin necesidad demostrada. Un diccionario literal es explícito, trazable y extensible con una línea. Alternativa descartada: hardcodear el `if flujo == "onboarding"` dentro de `run`/`status` — viola HU-05 (obligaría a tocar la lógica de cada comando por cada flujo nuevo).
- **Ubicación (`src/foda/orchestrator.py`, módulo nuevo, fuera de `core/`):** el registro importa `Onboarding` de `src/foda/flows/`; colocarlo en `core/` haría que `core` dependa de flujos concretos (dependencia invertida no deseada; `core` debe permanecer agnóstico de flujos). Un módulo de orquestación de nivel superior mantiene la dirección de dependencias correcta y es reutilizable e independientemente testeable por `run` y `status`.

### DS-ORQ-2 — Excepción para "flujo desconocido" (punto de confirmación 2)
- **Decisión:** `resolve_flow(name)` lanza **`ValueError`** cuando `name` no está en `FLOWS`, con un mensaje que nombra el flujo pedido y, opcionalmente, los registrados. La CLI captura ese `ValueError` y lo traduce a `stderr` + código `1`.
- **Razón:** reutiliza exactamente el patrón ya establecido en `client_new_cli` (nombre de cliente inválido → `ValueError` → `stderr` + código `1`), sin introducir una excepción propia (NC-2). "Flujo desconocido" es semánticamente un valor de entrada inválido, análogo a "nombre de cliente inválido". Alternativa descartada: una excepción propia `UnknownFlowError` — añade una clase sin beneficio observable dado un único punto de resolución centralizado.

### DS-ORQ-3 — Formato de salida de `foda status` (punto de confirmación 3)
- **Decisión:** **texto plano legible**, determinista, una sección por flujo registrado; dentro de cada flujo, una línea por artefacto (primero `requires`, luego `produces`) con: rol (`requires`/`produces`), nombre lógico del artefacto, marcador de existencia (`[presente]` / `[ausente]`) y ruta relativa al `root` del cliente. Salida por `stdout`, código `0`. Formato de referencia (a fijar en `plan_builder`, estable para tests por subcadenas):

  ```
  onboarding:
    requires  contract_data     [presente]  020_outputs/010_discovery/contract_data.json
    produces  map_client_data   [ausente]   020_outputs/020_onboarding/map_client_data.json
  ```

- **Razón:** cubre exactamente lo que pide HU-03 (para cada flujo, si sus artefactos de entrada/salida existen o no) con la mínima estructura (NC-2), es legible para el DS y sus subcadenas (nombre del flujo, nombre del artefacto, `presente`/`ausente`) son verificables en tests sin fijar un layout rígido de columnas. Alternativa descartada (por ahora): salida JSON estructurada — útil para tooling, pero HU-03 pide legibilidad para un humano y no hay consumidor de máquina en esta banda (E4). `foda status` **solo comprueba existencia en disco** (`Artifact.exists(ctx)`); **no** lee ni valida contenido (aclaración de dominio de `definition.md`).

### DS-ORQ-4 — Orden de validación y códigos de salida en `foda run` (concreción testeable)
- **Decisión (orden):** en `foda run`, primero se **resuelve el flujo por nombre** (`resolve_flow`, operación pura sin disco); luego se construye `ClientContext(cliente, clients_root)` (puede lanzar `FileNotFoundError`); luego se ejecuta `flow.run(ctx)` (puede lanzar `FlowContractError`). Fallar primero en el flujo desconocido evita tocar disco ante un error de tipeo del nombre del flujo.
- **Decisión (códigos):** `0` = éxito; `1` = errores semánticos (flujo desconocido, cliente inexistente, `FlowContractError`, y raíz de proyecto no encontrada); `2` = errores de parseo de `argparse` (falta `<cliente>` o `--flow`), por convención propia de `argparse`. Coherente con `client_new_cli` (DS-CLI-1/3).
- **Razón:** la `definition.md` solo exige "≠ 0" en error; aquí se concreta para hacerlo testeable, reutilizando la convención ya vigente en la CLI. La resolución de la raíz del proyecto (marcador `pyproject.toml` hacia arriba desde el cwd) se reutiliza tal cual de `client_new_cli` (`_find_project_root`); a diferencia de `client new`, `run`/`status` **no** crean `<raíz>/clients/` (son operaciones de lectura/ejecución sobre clientes ya existentes).

---

## Contratos de Datos / Artefactos

| Dirección | Artefacto | Formato | Esquema / campos |
|---|---|---|---|
| requiere | `foda.core.context.ClientContext(name: str, clients_root: Path)` | clase Python (CONFORME) | Éxito → objeto con `name`, `root`, `inputs_dir`, `outputs_dir`, … Error → `FileNotFoundError` si no existe `clients_root/<name>/client.yaml`. No se reimplementa. |
| requiere | `foda.core.flow.Flow.run(ctx) -> FlowResult` | método Python (CONFORME) | Ejecuta `load_inputs → validate → execute → write_outputs`; devuelve `FlowResult(success: bool, outputs: list[Path])`; puede lanzar `FlowContractError` (artefacto requerido ausente). No se reimplementa. |
| requiere | `foda.core.flow.Artifact.exists(ctx) -> bool` y `.path(ctx) -> Path` | métodos Python (CONFORME) | Base de la introspección de `foda status`. |
| requiere | `foda.flows.f020_onboarding.onboarding.Onboarding` | clase `Flow` (CONFORME) | Único flujo registrado en esta banda. `requires = [contract_data → 020_outputs/010_discovery/contract_data.json]`; `produces = [map_client_data → 020_outputs/020_onboarding/map_client_data.json]`. |
| requiere | `pyproject.toml` (marcador de raíz) | archivo | Su existencia localiza `<raíz>` hacia arriba desde el cwd (D-C, reutilizado de `client_new_cli`). No se parsea su contenido. |
| produce | `src/foda/orchestrator.py` | módulo Python (nuevo) | Expone `FLOWS: dict[str, type[Flow]]` (registro literal `{"onboarding": Onboarding}`) y `resolve_flow(name: str) -> Flow` (instancia; `ValueError` si desconocido). Único punto de resolución nombre→flujo, reutilizado por `run` y `status`. |
| modifica | `src/foda/cli.py` | módulo Python (existente) | Añade subparsers `run` (`<cliente>` posicional + `--flow` requerido) y `status` (`<cliente>` posicional) al parser existente; añade el despacho a `run`/`status` en `main`. Cambio quirúrgico (NC-3): no altera el subcomando `client new` existente. |
| produce | salida de `foda run` | stdout / stderr / exit code | Éxito → confirmación legible por `stdout` (nombra flujo, cliente y ruta(s) de salida producida(s)), exit `0`, artefacto(s) de `produces` escrito(s) en disco por el flujo. Error → mensaje claro por `stderr` (sin traceback), exit `≠ 0`. |
| produce | salida de `foda status` | stdout / stderr / exit code | Éxito → listado de texto plano (DS-ORQ-3) por `stdout`, exit `0`, **sin efectos en disco**. Error (cliente inexistente) → mensaje claro por `stderr` (sin traceback), exit `1`. |

> **Nota:** `flow_orchestrator` **no define artefactos de datos propios** (no hay YAML/JSON nuevo). Sus "contratos" son las firmas Python de las features CONFORMES que consume y los flujos que dispara. Esto es coherente con D-021 (Single Writer Rule): el estado es el disco de artefactos de los flujos, no un manifiesto propio del orquestador.

---

## Comportamiento Esperado

### `foda run <cliente> --flow <flujo>`
1. **Parsear** `argv`: comando `run`, posicional `<cliente>`, opción requerida `--flow <flujo>`. Si falta `<cliente>` o `--flow`, `argparse` imprime *usage* a `stderr` y termina con código `2`.
2. **Resolver la raíz del proyecto** (marcador `pyproject.toml` hacia arriba desde el cwd; `_find_project_root`). Si no se encuentra → mensaje claro a `stderr`, código `1`, sin tocar disco. `clients_root = <raíz>/clients` (no se crea).
3. **Resolver el flujo** con `resolve_flow(<flujo>)` (pura, sin disco). Si `<flujo>` no está en `FLOWS` → `ValueError` → traducir a `stderr` (mensaje que nombra el flujo desconocido) + código `1`, sin tocar disco (DS-ORQ-2/4).
4. **Construir `ClientContext(<cliente>, clients_root)`**. Si el cliente no existe → `FileNotFoundError` → traducir a `stderr` (mensaje que nombra el cliente) + código `1`, sin escribir en disco (DS-ORQ-4).
5. **Ejecutar `flow.run(ctx)`.** Si un artefacto requerido falta → `FlowContractError` (lanzado por `Flow.validate`) → traducir a `stderr` (mensaje que nombra el/los artefacto(s) ausente(s)) + código `1`, **antes** de escribir cualquier salida.
6. **Traducir el éxito:** si `flow.run` retorna sin excepción, imprimir por `stdout` una confirmación legible que nombre el flujo, el cliente y la(s) ruta(s) de `FlowResult.outputs`; retornar `0`. El/los artefacto(s) de `produces` quedan escritos en disco (los escribe el propio flujo, no el orquestador).
7. **Sin decisiones silenciosas:** ninguna excepción esperable se traga sin mensaje; ningún traceback crudo se expone al usuario.

### `foda status <cliente>`
1. **Parsear** `argv`: comando `status`, posicional `<cliente>`. Si falta `<cliente>`, `argparse` → *usage* a `stderr`, código `2`.
2. **Resolver la raíz** e igual que en `run`; `clients_root = <raíz>/clients` (no se crea).
3. **Construir `ClientContext(<cliente>, clients_root)`.** Si el cliente no existe → `FileNotFoundError` → `stderr` + código `1` (mismo estilo que `run`), sin efectos en disco.
4. **Introspeccionar:** para cada `(nombre, flujo)` de `FLOWS`, instanciar el flujo y, para cada `Artifact` en `flujo.requires` y en `flujo.produces`, evaluar `artifact.exists(ctx)` e imprimir su rol, nombre, marcador `[presente]`/`[ausente]` y ruta relativa (DS-ORQ-3). Retornar `0`.
5. `foda status` **no** ejecuta ninguna lógica de flujo, **no** lee ni valida contenido de artefactos, y **no** escribe nada en disco: solo comprueba existencia.

### Resolución de flujos (`src/foda/orchestrator.py`)
- `FLOWS` es el **único** punto donde se declara qué nombre corresponde a qué clase `Flow`. `resolve_flow(name)` es el **único** camino de instanciación por nombre, reutilizado por `run` y `status`. Registrar un flujo nuevo = añadir una entrada a `FLOWS`, sin editar `cli.py`/`run`/`status`.

---

## Casos Límite y Errores
| Caso | Entrada / Contexto | Resultado esperado |
|---|---|---|
| Run — happy path | `run ABC --flow onboarding`, cliente `ABC` con `contract_data.json` presente | Ejecuta `Onboarding.run`, escribe `020_outputs/020_onboarding/map_client_data.json`; confirmación por `stdout`; exit `0`. |
| Run — flujo desconocido | `run ABC --flow inexistente` | `ValueError` → `stderr` (nombra el flujo), sin traceback; exit `1`; sin tocar disco. |
| Run — cliente inexistente | `run GHOST --flow onboarding` | `FileNotFoundError` → `stderr` (nombra el cliente), sin traceback; exit `1`; sin escribir en disco. |
| Run — artefacto requerido faltante | `run ABC --flow onboarding` con `ABC` existente pero **sin** `contract_data.json` | `FlowContractError` → `stderr` (nombra el/los artefacto(s)), sin traceback; exit `1`; **no** se escribe `map_client_data.json`. |
| Run — falta `--flow` o `<cliente>` | `run ABC` / `run --flow onboarding` / `run` | `argparse` → *usage* a `stderr`; exit `2`. |
| Run — sin marcador de proyecto | cwd sin `pyproject.toml` en él ni ancestros | Mensaje claro a `stderr`; exit `1`; nada en disco. |
| Status — cliente existente | `status ABC` con `ABC` existente | Lista, para `onboarding`, `contract_data` y `map_client_data` con `[presente]`/`[ausente]` según disco; exit `0`; sin efectos en disco. |
| Status — cliente inexistente | `status GHOST` | `FileNotFoundError` → `stderr` (nombra el cliente), sin traceback; exit `1`. |
| Status — falta `<cliente>` | `status` | `argparse` → *usage* a `stderr`; exit `2`. |

**Limitaciones conocidas (banda `tracer_bullet`):**
- Solo hay **un** flujo registrado (`onboarding`); el registro `FLOWS` queda diseñado genéricamente pero solo se ejercita con un flujo real (riesgo documentado en `definition.md`). Los tests de HU-05 usan un flujo falso para verificar la extensibilidad sin un segundo flujo real.
- `foda status` reporta con fidelidad solo si el flujo declara bien su `requires`/`produces` (lo hace `Onboarding`); flujos futuros mal declarados reportarían información incompleta (no es riesgo de esta feature).

---

## Interfaces / Firmas Públicas
```python
# src/foda/orchestrator.py  (módulo nuevo)
FLOWS: dict[str, type[Flow]] = {"onboarding": Onboarding}

def resolve_flow(name: str) -> Flow:
    """Devuelve una instancia del flujo registrado bajo `name`.
    Lanza ValueError si `name` no está en FLOWS (flujo desconocido).
    Único punto de resolución nombre→flujo, reutilizado por `run` y `status`."""

# src/foda/cli.py  (existente; se extiende sin tocar `client new`)
def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la CLI `foda`. Además de `client new`, despacha:
      - `run <cliente> --flow <flujo>`: resuelve <flujo> (resolve_flow) y
        <cliente> (ClientContext), delega en Flow.run(ctx); traduce
        ValueError/FileNotFoundError/FlowContractError a stderr + código 1;
        imprime confirmación y devuelve 0 en éxito.
      - `status <cliente>`: resuelve <cliente> (ClientContext) e imprime, por
        cada flujo de FLOWS, la existencia en disco de sus requires/produces;
        devuelve 0. Cliente inexistente → stderr + código 1.
    Devuelve el código de salida del proceso."""
```
- **Contrato de errores de la CLI:** no define excepciones propias (NC-2); consume `ValueError` (flujo desconocido, vía `resolve_flow`), `FileNotFoundError` (cliente inexistente, vía `ClientContext`) y `FlowContractError` (artefacto faltante, vía `Flow.run`), y los traduce a `(mensaje en stderr, código 1)`. Los errores de parseo son de `argparse` (código `2`).
- **Delegación estricta (C-5 del feature_contract):** el orquestador **no** reimplementa lógica de flujo ni de rutas: toda ejecución pasa por `Flow.run(ctx)` y toda resolución de rutas por `ClientContext`/`Artifact`.
- **Testabilidad:** `main(argv)` acepta `argv` inyectable y devuelve `int`; los tests invocan `main(["run","ABC","--flow","onboarding"])` / `main(["status","ABC"])` bajo un `tmp_path` (con `pyproject.toml` marcador, `clients/ABC/client.yaml` y artefactos sembrados) y `monkeypatch.chdir`, verificando código, salida capturada y efectos en disco, sin subproceso.

---

## Criterios de Aceptación (verificables)
> Cada criterio es traducible a uno o más tests (invocando `main(argv)` o `resolve_flow` bajo un proyecto/cliente temporal) y traza a la(s) `HU-xx` que satisface. Convención de tests: `tmp_path` con `pyproject.toml` marcador; cliente sembrado en `clients/ABC/` con `client.yaml`; `monkeypatch.chdir` al proyecto.

| ID | Criterio de aceptación (redactado como algo que un test puede comprobar) | Trazabilidad → HU |
|---|---|---|
| CA-01 | Con un cliente `ABC` existente cuyo `020_outputs/010_discovery/contract_data.json` está presente y es válido, `main(["run","ABC","--flow","onboarding"])` devuelve `0` y deja escrito `clients/ABC/020_outputs/020_onboarding/map_client_data.json` en disco. | HU-01 |
| CA-02 | En el camino de éxito de CA-01, la salida capturada en `stdout` contiene una confirmación legible que menciona el flujo `onboarding`, el cliente `ABC` y la ruta del artefacto producido (`map_client_data.json`). | HU-01 |
| CA-03 | El orquestador no reimplementa lógica de flujo: con `Onboarding.run` (o `flow.run`) espiado/monkeypatcheado, `main(["run","ABC","--flow","onboarding"])` lo invoca exactamente una vez con un `ctx` cuyo `name == "ABC"`, sin derivar el mapa por su cuenta. | HU-01, HU-05 |
| CA-04 | `main(["run","ABC","--flow","inexistente"])` devuelve `1`, escribe en `stderr` un mensaje que menciona el flujo desconocido (`inexistente`), la salida no contiene `"Traceback"`, y no se escribe ningún artefacto de salida en disco. | HU-02, HU-05 |
| CA-05 | Con un cliente que no existe, `main(["run","GHOST","--flow","onboarding"])` devuelve `1`, escribe en `stderr` un mensaje que menciona que el cliente no existe, la salida no contiene `"Traceback"`, y no se crea/escribe ningún artefacto. | HU-02 |
| CA-06 | Con un cliente `ABC` existente pero **sin** su `contract_data.json` requerido, `main(["run","ABC","--flow","onboarding"])` devuelve `1`, escribe en `stderr` un mensaje que refleja el `FlowContractError` (artefacto requerido ausente), la salida no contiene `"Traceback"`, y **no** se escribe `map_client_data.json`. | HU-02 |
| CA-07 | Con un cliente `ABC` existente, `main(["status","ABC"])` devuelve `0` y su `stdout` lista el flujo `onboarding` incluyendo sus artefactos `contract_data` y `map_client_data`, cada uno con un marcador de existencia (`presente`/`ausente`). | HU-03 |
| CA-08 | `foda status` refleja la realidad del disco: para `ABC` con `contract_data.json` presente y `map_client_data.json` ausente, el `stdout` marca `contract_data` como presente y `map_client_data` como ausente; tras un `main(["run","ABC","--flow","onboarding"])` exitoso, un nuevo `main(["status","ABC"])` marca **ambos** como presentes. | HU-03 |
| CA-09 | Con un cliente que no existe, `main(["status","GHOST"])` devuelve `1`, escribe en `stderr` un mensaje que menciona que el cliente no existe (mismo estilo que `run`), y la salida no contiene `"Traceback"`. | HU-04 |
| CA-10 | Existe un registro explícito `FLOWS` (mapeo nombre→clase `Flow`) y una función `resolve_flow(name)` tal que `resolve_flow("onboarding")` devuelve una instancia de `Onboarding` (subclase de `Flow`), y `resolve_flow(<nombre no registrado>)` lanza `ValueError`. | HU-05 |
| CA-11 | Un flujo falso registrado en `FLOWS` (p. ej. añadiendo `{"fake": FakeFlow}`) es descubierto por **ambos** comandos sin modificar la lógica de `run`/`status`: `main(["status","ABC"])` lista `fake` con sus artefactos, y `main(["run","ABC","--flow","fake"])` despacha a `FakeFlow.run`. | HU-05 |
| CA-12 | `foda run` y `foda status` no crean `<raíz>/clients/` ni ningún directorio de cliente: ante un cliente inexistente (CA-05/CA-09) el árbol de `clients/` permanece sin la carpeta del cliente pedido. | HU-02, HU-04 |
| CA-13 | Errores de parseo de argumentos terminan con código `2` (convención de `argparse`): `main(["run","ABC"])` (falta `--flow`), `main(["run"])` (falta `<cliente>`) y `main(["status"])` (falta `<cliente>`) provocan salida de `argparse` a `stderr` con código de salida `2`. | HU-02, HU-04 |
| CA-14 | Existe una suite de tests de la CLI de orquestación (independiente de la de `client_new_cli`) que ejercita en verde: `run` happy path (CA-01/CA-02/CA-03), los tres errores de `run` (CA-04/CA-05/CA-06), `status` (CA-07/CA-08), el error de `status` (CA-09) y la resolución/registro de flujos (CA-10/CA-11). | HU-01, HU-02, HU-03, HU-04, HU-05 |

### Trazabilidad HU → Spec (cobertura)
> Toda `HU-xx` de `definition.md` queda cubierta por ≥ 1 `CA-xx`.

| HU | Cubierta por |
|---|---|
| HU-01 | CA-01, CA-02, CA-03, CA-14 |
| HU-02 | CA-04, CA-05, CA-06, CA-12, CA-13, CA-14 |
| HU-03 | CA-07, CA-08, CA-14 |
| HU-04 | CA-09, CA-12, CA-13, CA-14 |
| HU-05 | CA-03, CA-04, CA-10, CA-11, CA-14 |

---

## No-Objetivos
- `foda run --from/--to` (rangos de flujos encadenados) y `foda run --pipeline new/recurring` (pipelines completos): fuera de esta banda (y de esta feature, según `feature_contract`).
- `foda export` (descarga de artefactos a csv/xlsx).
- Construir o implementar flujos nuevos (Discovery, Ingestion, Profiling, …): el orquestador solo dispara flujos ya construidos; hoy solo `onboarding`.
- Un manifiesto/archivo de estado de ejecución separado de los artefactos en disco (descartado por D-021, Single Writer Rule): `foda status` introspecciona el disco, no lee estado propio.
- Validar el **contenido** de los artefactos en `foda status` (eso es responsabilidad de `Flow.validate` al correr, no del orquestador).
- Ejecución concurrente/paralela de flujos.
- Descubrimiento dinámico de flujos (decoradores, *entry points*, escaneo de paquetes): sobre-diseño para un único flujo (NC-2); el registro literal `FLOWS` basta.
- Salida estructurada (JSON) de `foda status`: no hay consumidor de máquina en esta banda.
- Modificar el subcomando `client new` existente o crear una CLI paralela (NC-3): se extiende `src/foda/cli.py` in situ.

---

## Puntos de confirmación para el GATE humano
Decisiones tomadas por `spec_writer` (delegadas por la `definition.md`) que el humano valida o ajusta antes de `plan_builder`:
1. **DS-ORQ-1 — resolución de flujo:** ¿se acepta un **registro literal** `FLOWS = {"onboarding": Onboarding}` + `resolve_flow(name)` en un módulo nuevo `src/foda/orchestrator.py` (fuera de `core/` para no invertir dependencias), como mecanismo mínimo que satisface HU-05, en vez de un registro dinámico?
2. **DS-ORQ-2 — flujo desconocido:** ¿se acepta reutilizar `ValueError` (patrón de `client_new_cli`) traducido a `stderr` + código `1`, en lugar de una excepción propia `UnknownFlowError`?
3. **DS-ORQ-3 — formato de `foda status`:** ¿se acepta **texto plano** (una sección por flujo; por artefacto: rol, nombre, `[presente]`/`[ausente]`, ruta relativa) en vez de JSON estructurado?
4. **DS-ORQ-4 — orden y códigos:** ¿se acepta resolver primero el flujo (sin disco) y luego el cliente, y la convención `0` éxito / `1` error semántico (flujo desconocido, cliente inexistente, `FlowContractError`, raíz no encontrada) / `2` parseo de `argparse`?
5. **`run`/`status` no crean `clients/`:** ¿se acepta que, a diferencia de `client new`, `run`/`status` **no** creen `<raíz>/clients/` ni carpetas de cliente (son operaciones de lectura/ejecución sobre clientes existentes)?
6. **Ubicación del módulo:** ¿se acepta crear `src/foda/orchestrator.py` como módulo nuevo (vs. embeber el registro en `cli.py`)? Se propone módulo aparte para que `run` y `status` lo compartan y sea testeable de forma independiente (CA-10).
