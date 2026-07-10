# Plan de prueba humano (gate `human_test`) — profiling `stab_1` (T-039)

> Etapa terminal `human_test` (D-079/D-081). El humano ejecuta las 7 pruebas de
> punta a punta vía la CLI. **Si las 7 son exitosas, se aprueba/mergea el PR #2**
> (`gh pr merge 2 --merge --delete-branch`) y la feature queda cerrada en `main`.
> Si alguna falla, se documenta el hallazgo y se reabre el ciclo antes del merge.
>
> PR: https://github.com/jdrodriguez1000/Foda_Application/pull/2
> Los valores de `global_score`, conteos, `pareto` y `problems_by_type` de los
> casos 1–6 fueron verificados ejecutando la cadena real en un entorno aislado;
> los mensajes/exit-codes de la CLI (casos 2 y 7) provienen de `src/foda/cli.py`
> y `src/foda/orchestrator.py`.

## Conceptos previos (rutas de un cliente)

Profiling **no** analiza los CSV crudos: su única fuente es `ingestion_report.json`.
La cadena a ejercer es **Onboarding → Ingestion → Profiling**. Rutas dentro de
`clients/<cliente>/`:

| Artefacto | Ruta | Quién lo pone |
|---|---|---|
| `contract_data.json` (semilla) | `020_outputs/010_discovery/contract_data.json` | **Humano** (Discovery no automatizado) |
| Archivos de landing (CSV) | `010_inputs/030_ingestion/` | **Humano** |
| `map_client_data.json` | `020_outputs/020_onboarding/` | flujo `onboarding` |
| `ingestion_report.json` | `020_outputs/030_ingestion/` | flujo `ingestion` |
| `profiling_report.json` ← **lo que validamos** | `020_outputs/040_profiling/` | flujo `profiling` |

**Gate de progresión (D-080):** `profiling` solo corre si `ingestion_report.success == true`.
Al inyectar problemas, ingestion queda `success:false` y hace falta `--force` para que
profiling corra igual (comportamiento `DS-PRF-6`).

**Cómo invocar la CLI:** se usa `foda …`. Si `foda` no está en el PATH, anteponer:
```powershell
PYTHONPATH=src python -c "from foda.cli import main; import sys; sys.exit(main(sys.argv[1:]))" run <cliente> --flow <flujo>
```

**Fórmula de `global_score`** (pesos: `missing_file`=1.0, `missing_column`=0.5,
`unexpected_file`=0.3, `unexpected_column`=0.1):
`score = max(0.0, 1 − Σ(peso×conteo) / files_declared)`, redondeado a 4 decimales;
si `files_declared==0` ⇒ `1.0`.

## Procedimiento reutilizable: "sembrar un cliente"

Cada caso parte de la misma semilla (se reusa `DEMO_1` como plantilla: contrato
válido con 3 archivos declarados — `ventas_2023_2025.csv`, `inventario_2024.csv`,
`inventario_2025.csv`). NOTA: `clients/` está en `.gitignore`; los clientes de
prueba no se commitean.

```powershell
# <NOMBRE> = nombre del cliente del caso (p.ej. piloto_a)
foda client new <NOMBRE>
New-Item -ItemType Directory -Force clients\<NOMBRE>\020_outputs\010_discovery | Out-Null
Copy-Item clients\DEMO_1\020_outputs\010_discovery\contract_data.json `
          clients\<NOMBRE>\020_outputs\010_discovery\contract_data.json -Force
Copy-Item clients\DEMO_1\010_inputs\030_ingestion\*.csv `
          clients\<NOMBRE>\010_inputs\030_ingestion\ -Force
```

---

## CASO 1 — Camino feliz (todo sano, `global_score = 1.0`)
**Cubre:** CA-01, CA-06…CA-09, CA-12, CA-17, CA-18, CA-19, CA-20.
**Entrada:** cliente `piloto_a` sembrado, sin mutaciones.
**Pasos:**
```powershell
foda run piloto_a --flow onboarding
foda run piloto_a --flow ingestion
foda run piloto_a --flow profiling          # el gate pasa: NO necesita --force
Get-Content clients\piloto_a\020_outputs\040_profiling\profiling_report.json
```
**Esperado:** los 3 `run` en exit 0; `ingestion.success:true`, `files_declared:3`,
`files_ingested:3`; y `profiling_report.json` exactamente:
```json
{
  "client": "piloto_a",
  "flow": "profiling",
  "health": {
    "files_declared": 3, "files_healthy": 3, "files_with_problems": 0,
    "global_score": 1.0, "pareto": [],
    "problems_by_type": { "missing_column": 0, "missing_file": 0, "unexpected_column": 0, "unexpected_file": 0 }
  },
  "schema_version": "0.2",
  "success": true
}
```
✅ Verifica: `schema_version=="0.2"`, bloque `health` con 6 claves, `client=="piloto_a"`, `flow=="profiling"`, `pareto==[]`.

---

## CASO 2 — `missing_column` + gate + `--force` (`score = 0.8333`)
**Cubre:** CA-02, CA-08, CA-11, CA-13, CA-16, CA-22, y el gate de la CLI.
**Entrada:** cliente `piloto_b` sembrado; eliminar por completo la columna `cantidad`
(la 4ª) de `ventas_2023_2025.csv` (cabecera + 3 filas). Cabecera final:
`fecha,sede,clase,precio_unitario`.
**Pasos:**
```powershell
foda run piloto_b --flow onboarding
foda run piloto_b --flow ingestion          # ingestion.success = false
foda run piloto_b --flow profiling          # SIN --force: el gate BLOQUEA
foda run piloto_b --flow profiling --force  # CON --force: corre igual
Get-Content clients\piloto_b\020_outputs\040_profiling\profiling_report.json
```
**Esperado:**
- `ingestion`: `success:false`, un `missing_column`; el comando sale **exit 1** con `finalizó SIN éxito`.
- `profiling` sin `--force`: **exit 1**, stderr `foda: El reporte de 'ingestion' no tiene success == true.`, no escribe reporte.
- `profiling` con `--force`: stderr `foda: --force sobrepasó el gate del predecesor: …`, luego `flujo 'profiling' completado`, **exit 0**.
- `health`: `files_declared:3, files_healthy:2, files_with_problems:1, global_score:0.8333, pareto:[{count:1,pct:1.0,type:"missing_column"}], problems_by_type.missing_column:1` (resto 0).

✅ Verifica: `0.8333 == round(1 − 0.5/3, 4)`; profiling **no falla** por ingestion fallido (`success:true`).

---

## CASO 3 — `unexpected_file` (`score = 0.9`)
**Cubre:** CA-10, CA-15.
**Entrada:** cliente `piloto_c` sembrado; añadir un archivo no declarado:
```powershell
Set-Content clients\piloto_c\010_inputs\030_ingestion\extra_no_declarado.csv "a,b`n1,2"
```
**Pasos:**
```powershell
foda run piloto_c --flow onboarding
foda run piloto_c --flow ingestion          # success = false (sobrante)
foda run piloto_c --flow profiling --force
Get-Content clients\piloto_c\020_outputs\040_profiling\profiling_report.json
```
**Esperado — `health`:** `files_declared:3, files_healthy:3, files_with_problems:0,
global_score:0.9, pareto:[{count:1,pct:1.0,type:"unexpected_file"}],
problems_by_type.unexpected_file:1` (resto 0).

✅ Verifica: `files_declared` sigue en **3** (el sobrante no es declarado); score `0.9 = 1 − 0.3/3`.

---

## CASO 4 — `missing_file` (`score = 0.6667`)
**Cubre:** CA-08, peso máximo.
**Entrada:** cliente `piloto_d` sembrado; borrar un archivo declarado:
```powershell
Remove-Item clients\piloto_d\010_inputs\030_ingestion\inventario_2025.csv
```
**Pasos:**
```powershell
foda run piloto_d --flow onboarding
foda run piloto_d --flow ingestion
foda run piloto_d --flow profiling --force
Get-Content clients\piloto_d\020_outputs\040_profiling\profiling_report.json
```
**Esperado — `health`:** `files_declared:3, files_healthy:2, files_with_problems:1,
global_score:0.6667, pareto:[{count:1,pct:1.0,type:"missing_file"}],
problems_by_type.missing_file:1` (resto 0).

✅ Verifica: `0.6667 == round(1 − 1.0/3, 4)`.

---

## CASO 5 — Clamp a `0.0` (todos los declarados ausentes)
**Cubre:** CA-03 (score nunca negativo).
**Entrada:** cliente `piloto_e` sembrado; borrar los 3 CSV del landing:
```powershell
Remove-Item clients\piloto_e\010_inputs\030_ingestion\*.csv
```
**Pasos:**
```powershell
foda run piloto_e --flow onboarding
foda run piloto_e --flow ingestion
foda run piloto_e --flow profiling --force
Get-Content clients\piloto_e\020_outputs\040_profiling\profiling_report.json
```
**Esperado — `health`:** `files_declared:3, files_healthy:0, files_with_problems:3,
global_score:0.0, pareto:[{count:3,pct:1.0,type:"missing_file"}],
problems_by_type.missing_file:3` (resto 0).

✅ Verifica: penalización = 1.0×3/3 = 1.0 ⇒ `max(0.0, 1−1) = 0.0` (clamp).

---

## CASO 6 — Determinismo byte a byte (CA-21)
**Entrada:** el cliente `piloto_a` del Caso 1.
**Pasos:**
```powershell
$antes = Get-FileHash clients\piloto_a\020_outputs\040_profiling\profiling_report.json
foda run piloto_a --flow profiling
$despues = Get-FileHash clients\piloto_a\020_outputs\040_profiling\profiling_report.json
$antes.Hash -eq $despues.Hash
```
**Esperado:** `True` (mismo SHA-256; reporte byte-idéntico).

---

## CASO 7 — Error duro: sin `ingestion_report.json` (CA-23)
**Entrada:** cliente recién creado, sin correr ingestion:
```powershell
foda client new piloto_vacio
```
**Pasos:**
```powershell
foda run piloto_vacio --flow profiling           # sin --force
foda run piloto_vacio --flow profiling --force   # con --force
```
**Esperado:**
- Sin `--force`: **exit 1**, stderr `foda: El reporte de 'ingestion' no existe (se esperaba con success == true).`
- Con `--force`: advertencia del gate a stderr y luego **exit 1** con `FlowContractError`:
  `foda: Artefacto(s) requerido(s) ausente(s): 'ingestion_report' (…\020_outputs\030_ingestion\ingestion_report.json)`.
- En ninguno de los dos se crea `piloto_vacio\020_outputs\040_profiling\profiling_report.json`.

---

## Resumen y criterio de aprobación

| Caso | Escenario | `global_score` | Señal clave |
|---|---|---|---|
| 1 | Todo sano | 1.0 | schema `0.2`, bloque `health`, `pareto []` |
| 2 | `missing_column` | 0.8333 | gate bloquea sin `--force`; profiling no falla |
| 3 | `unexpected_file` | 0.9 | `files_declared` sigue en 3 |
| 4 | `missing_file` | 0.6667 | peso 1.0 |
| 5 | Todos ausentes | 0.0 | clamp, no negativo |
| 6 | Rerun | — | byte-idéntico |
| 7 | Sin ingestion | — | `FlowContractError`, no escribe |

**Criterio de aprobación del gate `human_test`:** si los 7 casos producen la salida
esperada, el humano aprueba y mergea el **PR #2**
(`gh pr merge 2 --merge --delete-branch`), avanzando `state.json` a `merge_to_main`
y cerrando la feature en `main`.
