# Verification — client_context (banda tracer_bullet)

> Artefacto de la etapa 8 (`spec_verifier`). Verifica que lo construido **cumple la
> especificación aprobada** (`spec.md`). Auditoría, no construcción: no se añade
> funcionalidad ni casos; se comprueba cobertura criterio → evidencia y se corre la
> suite completa.
>
> Fuentes: `spec.md`, `definition.md`, `plan.md`, `state.json` de esta celda;
> `src/foda/core/context.py`, `src/foda/core/scaffold.py`,
> `tests/core/test_context.py`, `tests/integration/test_client_context_integration.py`.

---

## Veredicto: **CONFORME**

Los 12 criterios de aceptación (`CA-01`…`CA-12`) de `spec.md` tienen evidencia directa
(test unitario que los cubre, reforzados por los tests de integración de la feature). La
suite completa está en verde (**71 passed**). El alcance de `definition.md` se cumple (in
scope hecho, out of scope respetado) y las decisiones vinculantes (D-1 modo inferido de
`models/latest`; D-2 `clients_root` como parámetro sin re-resolver el cwd; D-3
introspección de artefactos diferida; marcador de existencia = `client.yaml`; excepción
`FileNotFoundError`) se satisfacen. No se detectan huecos bloqueantes.

---

## Matriz de trazabilidad (criterio → evidencia → estado)

| CA | Criterio (resumen) | HU | Evidencia (test) | Estado |
|---|---|---|---|---|
| CA-01 | `ClientContext("ABC", tmp/clients)` sobre cliente creado se construye sin lanzar y expone `name == "ABC"` y `root == tmp/clients/ABC` | HU-01 | `tests/core/test_context.py::test_client_context_construye_sin_lanzar_y_expone_name_y_root`; integración `::test_client_context_resuelve_exactamente_el_arbol_creado_por_create_client` (`ctx.root == client_dir`) | Cubierto |
| CA-02 | `name` sin `client.yaml` (carpeta inexistente) → `FileNotFoundError` | HU-01 | `::test_client_context_lanza_filenotfounderror_si_cliente_no_existe`; integración `::test_fallo_temprano_con_mensaje_claro_si_el_flujo_vecino_recibe_cliente_inexistente` | Cubierto |
| CA-03 | Tras intento fallido, el filesystem bajo `tmp/clients` queda idéntico (nada creado para ese `name`) | HU-01 | `::test_client_context_intento_fallido_no_modifica_filesystem` (snapshot `rglob` antes/después + `not (clients_root/"NOEXISTE").exists()`) | Cubierto |
| CA-04 | Carpeta existe pero sin `client.yaml` → `FileNotFoundError` (marcador = `client.yaml`, no la carpeta) | HU-01 | `::test_client_context_lanza_filenotfounderror_si_carpeta_sin_client_yaml` | Cubierto |
| CA-05 | `inputs_dir == .../ABC/010_inputs` y `outputs_dir == .../ABC/020_outputs` | HU-02 | `::test_client_context_expone_inputs_dir_y_outputs_dir` | Cubierto |
| CA-06 | `bronze_dir`, `silver_dir`, `gold_dir` == `.../ABC/data/{bronze,silver,gold}` | HU-02 | `::test_client_context_expone_bronze_silver_gold_dir` | Cubierto |
| CA-07 | `models_dir == .../ABC/models` | HU-02 | `::test_client_context_expone_models_dir` | Cubierto |
| CA-08 | Las 6 rutas resueltas **existen** en disco para un cliente creado por `create_client` | HU-02 | `::test_client_context_las_6_rutas_existen_en_disco` (6 `.is_dir()`); integración `::test_client_context_resuelve_exactamente_el_arbol_creado_por_create_client` (las 6 rutas == carpetas hoja creadas, 1:1) | Cubierto |
| CA-09 | Cliente sin `models/latest` (aunque `models/` exista vacía) → `is_recurring == False` (NUEVO) | HU-03 | `::test_client_context_is_recurring_false_para_cliente_nuevo`; integración `::test_camino_nuevo_a_recurrente_end_to_end_sobre_el_mismo_cliente` (rama nuevo) | Cubierto |
| CA-10 | Con `models/latest` materializado → `is_recurring == True` (RECURRENTE) | HU-03 | `::test_client_context_is_recurring_true_para_cliente_recurrente`; integración `::test_camino_nuevo_a_recurrente_end_to_end_sobre_el_mismo_cliente` (rama recurrente) | Cubierto |
| CA-11 | `client.yaml` con flag espurio (`mode: recurring`) sin `models/latest` → `is_recurring == False` (no se lee el YAML) | HU-03 | `::test_client_context_is_recurring_ignora_flag_espurio_en_client_yaml` | Cubierto |
| CA-12 | Con `monkeypatch.chdir` a un dir no relacionado, `root` y las 6 rutas siguen bajo `tmp/clients/ABC` (parámetro, no cwd) | HU-04 | `::test_client_context_rutas_dependen_solo_de_clients_root_no_del_cwd` | Cubierto |

**Cobertura HU (spec §Trazabilidad):** HU-01 → CA-01/02/03/04; HU-02 → CA-05/06/07/08;
HU-03 → CA-09/10/11; HU-04 → CA-12 (y CA-01…CA-11, todos construidos con `clients_root`
explícito bajo `tmp_path`). Toda HU queda cubierta por ≥ 1 CA cubierto.

**Integración adicional (system_design):** `::test_client_context_es_superficie_suficiente_para_flow_run_ctx`
(SS9, superficie suficiente para `Flow.run(ctx)`) y
`::test_dos_client_context_bajo_el_mismo_clients_root_quedan_aislados` (SS13,
aislamiento multi-tenant) refuerzan el contrato sin ampliar los CA (no-objetivos: `Flow`
real no se construye, T-015).

---

## Resultado de la suite completa

```
python -m pytest -q  ->  71 passed in 0.44s   (VERDE)
```

Desglose: 12 tests unitarios de `tests/core/test_context.py` (CA-01…CA-12) + 5 tests de
integración de esta feature (`tests/integration/test_client_context_integration.py`) +
54 tests preexistentes de `client_scaffold` y `client_new_cli`. Sin fallos, sin
regresiones.

---

## Cumplimiento de alcance y decisiones vinculantes

**Alcance (`definition.md`):**
- **In scope hecho:** `ClientContext(name, clients_root)` en `src/foda/core/context.py`
  que (1) valida la existencia del cliente vía `client.yaml`, (2) expone las 6 rutas
  resueltas §7 (`inputs_dir`, `outputs_dir`, `bronze_dir`, `silver_dir`, `gold_dir`,
  `models_dir`) más `name`/`root`, y (3) determina el modo nuevo/recurrente inferido del
  disco. `clients_root` recibido como parámetro. Todas las HU (HU-01…HU-04) trazadas a
  ≥1 CA cubierto (NC-5, D-031).
- **Out of scope respetado:** `ClientContext` es de solo lectura (no crea, no modifica, no
  borra — verificado por CA-03 y la ausencia de `mkdir`/`write` en `context.py`); no se
  toca ni se duplica `create_client` (NC-3, se usa solo como fixture); no se implementa
  `Flow`/orquestación; no se parsea el contenido de `client.yaml`; no se valida el patrón
  del nombre; no hay introspección de "qué artefactos existen" (D-3); no se define
  `ClientNotFoundError` ni `enum ClientMode` (NC-2).

**Decisiones vinculantes:**
- **D-1 / DS-CTX-2 — modo inferido del disco:** `is_recurring` es
  `(self.models_dir / "latest").exists()` en `context.py`; **nunca** lee `client.yaml`.
  CA-11 lo verifica explícitamente (flag `mode: recurring` espurio ignorado). ✓
- **D-2 / DS-CTX-3 — `clients_root` como parámetro:** `__init__(name, clients_root)`
  calcula `root = clients_root / name`; no hay `os.getcwd()` ni `Path.cwd()` ni búsqueda
  de `pyproject.toml` en `context.py`. CA-12 (`monkeypatch.chdir`) lo confirma. ✓
- **D-3 — introspección de artefactos diferida:** no existe ninguna superficie de
  introspección de artefactos en `context.py`; correctamente fuera de esta banda. ✓
- **Marcador de existencia = `client.yaml`:** `__init__` comprueba
  `(root / "client.yaml").exists()` (no `root.exists()`). CA-04 (carpeta sin
  `client.yaml` → `FileNotFoundError`) lo verifica. ✓
- **Excepción `FileNotFoundError` (DS-CTX-1):** lanzada con mensaje que incluye el `name`
  y la ruta esperada; testeable con `pytest.raises(FileNotFoundError)`. CA-02, CA-04 y la
  integración (`match="Stark"`) lo confirman. No se introduce excepción propia. ✓

**Restricciones:**
- **Python 3.13+ / solo stdlib (R1):** `context.py` importa únicamente `pathlib`; cero
  dependencias nuevas; no importa `yaml` (no parsea el YAML). ✓
- **LLM aislado / YAML in–JSON out:** no aplican a esta feature (abstracción de lectura
  de filesystem, sin LLM). ✓

---

## Hallazgos / huecos

Ninguno bloqueante. No se detectan criterios parciales ni no cubiertos, ni desviaciones
de alcance o de las decisiones vinculantes. No procede retorno a etapas anteriores.

**F-1 (no bloqueante, observación).** Varios casos del bucle TDD (5, 7, 8, 10, 11, 12)
se resolvieron como "verde directo" sin fase roja genuina (D-037), porque el
comportamiento quedó cubierto como efecto colateral necesario de casos previos (p. ej.
`is_recurring` implementado en el caso 6 ya cubre CA-10/CA-11; la validación de
`client.yaml` del caso 9 ya cubre CA-04). El razonamiento está documentado caso a caso en
`state.json`. No afecta la cobertura observable: cada CA tiene su test explícito y verde;
se registra solo por trazabilidad (P8).

**F-2 (no bloqueante, limitaciones documentadas).** La spec declara dos limitaciones
conocidas heredadas y aceptadas para esta banda: (a) un `models/latest` que sea symlink
roto se evaluaría como inexistente (⇒ NUEVO), ya que `Path.exists()` sigue symlinks —los
tests materializan `latest` como carpeta real; (b) filesystems case-insensitive
(Windows/macOS) heredan la semántica del filesystem sin normalización de mayúsculas. Sin
consumidor que lo requiera hoy; documentado, no bloqueante.

---

## Cierre

Feature `client_context` (banda `tracer_bullet`): **CONFORME**. Se cierra la cadena
SDD/TDD para esta celda. `state.json`: `stages.spec_verifier.status = "done"`,
`status = "done"`, `current_stage = "completed"`.
