# Definition — client_context

> Artefacto de la etapa 1 (`feature_definer`). Define **qué** se va a construir y **por qué**, expresado como **historias de usuario codificadas**. No describe el *cómo*.

## Feature
- **Nombre:** `client_context` (snake_case)
- **Banda:** `tracer_bullet` (D-019; celda = feature × banda)
- **Componente / flujo:** Abstracción común de flujo (`system_design.md` §9, `ClientContext`), consumida por `Flow.run(ctx: ClientContext)`. Relacionada con §7 (estructura de carpetas), §12 (caminos de ejecución nuevo vs. recurrente) y §13 (multi-tenant y aislamiento por cliente). Es la contraparte de LECTURA de `client_scaffold` (que CREA la carpeta del cliente); `client_context` la RESUELVE y la ORIENTA.

## Problema / Necesidad
`create_client` (feature `client_scaffold`, CONFORME) ya sabe **crear** el árbol de carpetas de un cliente nuevo, y `foda client new <NAME>` (feature `client_new_cli`, CONFORME) ya lo expone por CLI. Pero **ningún componente sabe todavía resolver ni orientar** ese árbol una vez creado: dado el nombre de un cliente, nada en el código responde hoy "¿existe este cliente?", "¿dónde están sus carpetas de inputs/outputs/data/models?" ni "¿es un cliente nuevo (sin modelo entrenado) o recurrente (con modelo vigente)?". `system_design.md` §9 define `ClientContext` como la abstracción que resuelve exactamente esto para que cualquier flujo (`Flow.run(ctx: ClientContext)`) opere sin conocer la estructura interna de `clients/<NAME>/`. Esta feature construye esa abstracción, siguiente eslabón del orden de construcción abajo-hacia-arriba (`client_scaffold → client_context → flow_base → flujos`, D-016), y es requisito de `flow_base` (T-015).

## Alcance

**In scope:**
- Un `ClientContext` (ubicación sugerida: `src/foda/core/context.py`) que, dado un cliente **ya creado**:
  1. **Valida su existencia**: comprueba que `clients_root/<name>/client.yaml` existe; si no, falla con un error claro (cliente inexistente), sin crear ni modificar nada en el filesystem.
  2. **Expone las rutas resueltas** de la carpeta del cliente según `system_design.md` §7: `010_inputs/`, `020_outputs/`, `data/bronze`, `data/silver`, `data/gold`, `models/`.
  3. **Determina el modo nuevo vs. recurrente** de forma determinista, inferido del disco (ver Riesgos y Supuestos, decisión vinculante D-1).
- `clients_root` se recibe como **parámetro** de `ClientContext` (mismo patrón que `create_client(name, clients_root)`); el core no re-resuelve la raíz del proyecto por su cuenta (ver decisión vinculante D-2).

**Out of scope:**
- Creación o modificación de carpetas de cliente — eso ya lo hace `create_client` (`client_scaffold`, CONFORME); `ClientContext` es de solo lectura sobre el filesystem.
- Validación de contratos de artefactos entre flujos (§8) — responsabilidad de `flow_base` y de cada flujo concreto.
- Ejecución u orquestación de flujos (`Flow.run`, secuencias de §12) — features posteriores (`flow_base`, T-015, y flujos concretos).
- Resolución de la raíz del proyecto (búsqueda de `pyproject.toml` hacia arriba desde el cwd) — vive en la capa CLI/orquestador, reutilizando lo ya construido en `client_new_cli` (NC-3, no duplicar).
- **Introspección de "qué artefactos concretos ya existen"** para un cliente (§9) — queda **fuera de esta banda** (ver decisión vinculante D-3). Se añadirá en una banda posterior, cuando `flow_base` realmente la consuma.
- Subcomandos CLI nuevos, salvo el mínimo que un tracer de integración pudiera requerir (a criterio de `spec_writer`/`plan_builder`).

## Historias de Usuario
> Cada historia lleva un **código `HU-xx`** (único en la feature) para **trazabilidad end-to-end**: la spec enlaza cada `CA-xx` a una `HU-xx`, y el plan enlaza cada `TSK-xx` a un `CA-xx`. Formato: *Como `<rol>`, quiero `<objetivo>`, para `<beneficio>`*.

| ID | Historia de usuario | Criterio(s) de aceptación (alto nivel, verificable) |
|---|---|---|
| HU-01 | Como **flujo/orquestador**, quiero validar que un cliente exista antes de operar sobre él, para evitar operar sobre un cliente inexistente o dejar estado espurio en el filesystem. | Construir un `ClientContext` para un nombre cuyo `clients_root/<name>/client.yaml` **no existe** falla con un error claro (tipo de excepción explícito), y no crea ni modifica ninguna carpeta ni archivo. |
| HU-02 | Como **flujo**, quiero obtener las rutas resueltas de las carpetas de un cliente existente, para leer/escribir sus artefactos sin conocer ni reimplementar la estructura interna de `clients/<NAME>/`. | Construir un `ClientContext` para un cliente existente expone rutas correctas y coherentes con `system_design.md` §7 para `010_inputs/`, `020_outputs/`, `data/bronze`, `data/silver`, `data/gold` y `models/`. |
| HU-03 | Como **orquestador/flujo**, quiero saber si un cliente es "nuevo" o "recurrente", para poder seleccionar la secuencia de flujos correcta (§12: pipeline completo vs. pipeline mensual que reutiliza el modelo). | Un cliente **sin** `models/latest` se determina como `nuevo`; un cliente **con** `models/latest` se determina como `recurrente`; la determinación es puramente función del disco, sin leer ningún flag de `client.yaml`. |
| HU-04 | Como **desarrollador del harness**, quiero que `ClientContext` reciba `clients_root` ya resuelto como parámetro (no que lo re-resuelva buscando `pyproject.toml`), para poder testear el core de forma aislada con `tmp_path`, sin acoplarlo al cwd real. | La firma de construcción de `ClientContext` acepta `clients_root: Path` explícito; ningún test del core depende del directorio de trabajo del proceso que ejecuta pytest. |

## Dependencias
- **`client_scaffold`** (banda `tracer_bullet`, **CONFORME**): provee `create_client(name, clients_root) -> Path` en `src/foda/core/scaffold.py`. La estructura de carpetas que crea (`client.yaml`, `010_inputs/`, `020_outputs/`, `data/{bronze,silver,gold}/`, `models/`) es la que `ClientContext` debe resolver. `client_context` no depende de ningún trabajo pendiente de `client_scaffold`.
- **`client_new_cli`** (banda `tracer_bullet`, **CONFORME**): delegó explícitamente en esta feature `ClientContext` y la resolución de rutas de cliente existente (ver su `feature_contract.md`). No hay trabajo pendiente de esa feature del que dependa esta.
- `700_architecture/system_design.md` §7 (estructura de carpetas), §9 (abstracción común de flujo, `ClientContext`), §12 (nuevo vs. recurrente), §13 (multi-tenant y aislamiento por cliente).

## Riesgos y Supuestos
- **Decisión vinculante D-1 (modo nuevo/recurrente inferido del disco):** RECURRENTE ⇔ existe un modelo entrenado vigente (`models/latest`); NUEVO ⇔ no existe. Refleja §12 y R9 (el recurrente reutiliza el modelo y salta Modelling). No se usa un flag editable en `client.yaml` para evitar estado que alguien deba mantener sincronizado con la realidad. Acordada explícitamente con el humano; no debe reabrirse sin autorización.
- **Decisión vinculante D-2 (`clients_root` como parámetro):** el core recibe `clients_root` ya resuelto y NO re-resuelve buscando `pyproject.toml` por su cuenta; esa resolución hacia arriba desde el cwd (con marcador `pyproject.toml`) vive en la capa CLI/orquestador, reutilizando lo ya construido en `client_new_cli` (NC-3, no duplicar). Mantiene el core testeable con `tmp_path` y sin efectos del cwd. Mismo patrón que `create_client(name, clients_root)`. Acordada explícitamente con el humano.
- **Decisión vinculante D-3 (introspección de artefactos diferida):** la capacidad de saber qué artefactos concretos se han generado ya para un cliente (§9, "qué artefactos ya existen") queda **fuera de esta banda**. Se añadirá en una pieza posterior, cuando `flow_base` (T-015) realmente la consuma. No se construye superficie sin consumidor todavía (NC-2). Acordada explícitamente con el humano.
- **Aclaración de dominio (no es una ambigüedad, se documenta para que `spec_writer` no la confunda):** "nuevo vs. recurrente" (¿el cliente ya tiene modelo o hay que construirle uno?) es un concepto **distinto** de "reanudar el trabajo donde se dejó" (¿qué pasos ya se hicieron?). Un cliente con limpieza (`Cleaning`) hecha pero sin modelo entrenado sigue siendo correctamente "nuevo". La reanudación se apoya en los artefactos ya presentes en disco (idempotencia/reanudación, principio de diseño §2.5 de `system_design.md`) y corresponde a la introspección diferida (D-3), no al modo nuevo/recurrente (D-1).
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** el tipo de excepción concreto para "cliente inexistente" (p. ej. `ValueError` vs. una excepción propia `ClientNotFoundError`) no está fijado por `system_design.md` ni por ninguna decisión previa; queda a `spec_writer`/`plan_builder` definirlo explícitamente (NC-6, no asumir en silencio).
- **Supuesto (punto de confirmación para el GATE de `spec_writer`):** la forma exacta de exponer el modo (`is_recurring: bool`, un enum `ClientMode`, o un método) no está fijada; queda a `spec_writer`/`plan_builder` decidirla, respetando NC-2 (simplicidad primero).
- **Riesgo:** si en el futuro cambia la convención de `models/latest` (p. ej. deja de ser un puntero/symlink y pasa a ser otro mecanismo), la lógica de detección de modo de `ClientContext` deberá actualizarse; hoy no hay ninguna capa de abstracción intermedia adicional sobre esa convención (D-011).
