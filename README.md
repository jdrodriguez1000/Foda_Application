# Foda_Application

Aplicación FODA desarrollada bajo la metodología **SDD/TDD** del proyecto (ver `CLAUDE.md` y `980_guideline/principles.md`).

Este README describe cómo preparar el entorno y usar la **CLI `foda`** para crear clientes, ejecutar flujos de análisis sobre ellos y consultar su estado.

---

## Requisitos

- **Python 3.13 o superior** (obligatorio; el proyecto declara `requires-python = ">=3.13"` en `pyproject.toml`).
- `pip` y el módulo `venv` (incluidos con Python).

> ⚠️ **Importante:** si creas el entorno virtual con una versión menor a 3.13 (p. ej. 3.12), la instalación del paquete fallará con el error `Package 'foda' requires a different Python`. Verifica siempre la versión antes de instalar.

### Verificar versiones de Python disponibles (Windows)

```powershell
py -0p
```

Esto lista las instalaciones de Python. Asegúrate de tener una `3.13` (o superior).

---

## Configuración inicial del entorno (una sola vez)

Ejecuta estos pasos desde la **raíz del proyecto** (la carpeta que contiene `pyproject.toml`).

### 1. Crear el entorno virtual con Python 3.13

```powershell
py -3.13 -m venv .venv
```

### 2. Activar el entorno virtual

```powershell
# PowerShell en Windows
.venv\Scripts\Activate.ps1
```

```bash
# Git Bash / Linux / macOS
source .venv/Scripts/activate   # Windows (Git Bash)
source .venv/bin/activate       # Linux / macOS
```

### 3. Verificar que el venv usa Python 3.13

```powershell
python --version
# Debe mostrar: Python 3.13.x
```

### 4. Instalar el paquete en modo editable

```powershell
pip install -e .
```

Esto instala el paquete `foda` y sus dependencias (`PyYAML`), y crea el comando **`foda`** en el entorno virtual.

> El punto final (`.`) es obligatorio: indica que se instala el proyecto del directorio actual. El flag `-e` (editable) enlaza el comando al código fuente.

---

## Uso de la CLI

La CLI `foda` ofrece **tres comandos**, pensados para usarse en este orden:

| Comando | Para qué sirve | Cuándo se usa |
|---|---|---|
| `foda client new <cliente>` | **Crea** un cliente nuevo (su carpeta y `client.yaml`). | Una sola vez, al dar de alta un cliente. |
| `foda run <cliente> --flow <flujo>` | **Ejecuta** un flujo de análisis sobre un cliente ya existente y escribe sus artefactos de salida en disco. | Cada vez que quieras producir (o regenerar) los resultados de un flujo. |
| `foda status <cliente>` | **Consulta** qué artefactos de cada flujo ya están en disco y cuáles faltan, sin modificar nada. | En cualquier momento, para saber qué falta por ejecutar o verificar qué se produjo. |

> **Modelo mental:** `client new` prepara el terreno, `run` hace el trabajo (produce artefactos), y `status` es de solo lectura: te dice en qué punto va el cliente. `run` y `status` operan siempre sobre clientes que **ya existen**; nunca crean la carpeta `clients/` (a diferencia de `client new`).

Todos los comandos localizan la **raíz del proyecto** buscando hacia arriba desde el directorio actual el primer ancestro que contenga `pyproject.toml`, así que puedes ejecutarlos desde cualquier subcarpeta del proyecto (con el entorno virtual activado).

---

### `foda client new` — crear un cliente

Con el entorno virtual **activado**, crea un nuevo cliente con:

```powershell
foda client new <NOMBRE_CLIENTE>
```

Ejemplo:

```powershell
foda client new DEMO_ABC
```

Salida esperada (imprime la ruta del cliente creado):

```
C:\...\Foda_Application\clients\DEMO_ABC
```

Se genera la estructura:

```
clients/
└── DEMO_ABC/
    └── client.yaml
```

### Dónde se crea el cliente

La CLI busca la **raíz del proyecto** hacia arriba desde el directorio actual (localiza el primer ancestro que contenga `pyproject.toml`) y crea el cliente en `<raíz>/clients/<NOMBRE>`. La carpeta `clients/` se crea automáticamente si no existe. Puedes ejecutar el comando desde cualquier subcarpeta dentro del árbol del proyecto.

### Códigos de salida y errores (`client new`)

| Situación | Comportamiento | Código |
|---|---|---|
| Cliente creado con éxito | Imprime la ruta en stdout | `0` |
| Nombre de cliente inválido (p. ej. `"a b"`, `".."`, `"-x"`) | Mensaje en stderr | `1` |
| Cliente duplicado (ya existe) | Mensaje en stderr | `1` |
| No se encuentra la raíz del proyecto (sin `pyproject.toml` en ancestros) | Mensaje en stderr | `1` |
| Falta el nombre o subcomando desconocido | Mensaje de uso de argparse | `2` |

---

### `foda run` — ejecutar un flujo sobre un cliente

Ejecuta un **flujo de análisis** sobre un cliente **ya existente**. El flujo lee los artefactos que necesita (`requires`), hace su trabajo y escribe los artefactos que produce (`produces`) en el disco del cliente.

```powershell
foda run <CLIENTE> --flow <NOMBRE_FLUJO>
```

Ejemplo (ejecuta el flujo de _onboarding_ sobre el cliente `DEMO_ABC`):

```powershell
foda run DEMO_ABC --flow onboarding
```

Salida esperada en el camino feliz (confirma el flujo, el cliente y la ruta del artefacto producido):

```
foda: flujo 'onboarding' completado para el cliente 'DEMO_ABC': C:\...\clients\DEMO_ABC\020_outputs\020_onboarding\map_client_data.json
```

**Flujos disponibles hoy:** `onboarding`, `ingestion`. (El registro de flujos vive en `src/foda/orchestrator.py`; añadir un flujo nuevo es agregar una entrada a `FLOWS`, sin tocar la CLI.)

**Cuándo usarlo:** después de crear el cliente y de haber colocado los datos de entrada que el flujo requiere. Para `onboarding`, el flujo espera encontrar `020_outputs/010_discovery/contract_data.json` dentro del cliente; si falta (o está incompleto), `run` **no** escribe nada y termina con un error claro (ver tabla). Puedes volver a ejecutar `run` cuantas veces quieras: regenera los artefactos de salida.

#### Códigos de salida y errores (`run`)

| Situación | Comportamiento | Código |
|---|---|---|
| Flujo ejecutado con éxito | Confirma en stdout flujo, cliente y ruta(s) producida(s) | `0` |
| Flujo desconocido (no está en el registro) | Mensaje en stderr nombrando el flujo | `1` |
| El cliente no existe | Mensaje en stderr nombrando el cliente | `1` |
| Falta un artefacto de entrada requerido por el flujo | Mensaje en stderr (no escribe salida) | `1` |
| No se encuentra la raíz del proyecto | Mensaje en stderr | `1` |
| Falta `<cliente>` o falta `--flow` | Mensaje de uso de argparse | `2` |

> El orden de validación es: **flujo → cliente → ejecución**. Si el flujo es desconocido, `run` falla antes de tocar el disco.

---

### `foda status` — consultar el estado de un cliente

Muestra, **sin modificar nada**, qué artefactos de cada flujo registrado están ya en disco (`[presente]`) y cuáles faltan (`[ausente]`) para un cliente existente. Es una radiografía de solo lectura del avance del cliente.

```powershell
foda status <CLIENTE>
```

Ejemplo:

```powershell
foda status DEMO_ABC
```

Salida esperada (una sección por flujo; para cada artefacto: rol, nombre lógico, marcador de presencia y ruta relativa al cliente):

```
onboarding:
  requires  contract_data     [presente]  020_outputs\010_discovery\contract_data.json
  produces  map_client_data   [ausente]   020_outputs\020_onboarding\map_client_data.json
```

**Cómo leerlo:** un artefacto `requires` en `[ausente]` significa que aún falta un dato de entrada para poder ejecutar ese flujo con `run`. Un artefacto `produces` en `[ausente]` significa que ese flujo todavía no se ha ejecutado (o no completó). En el ejemplo anterior, el cliente tiene su entrada lista pero aún no ha corrido `onboarding`; tras un `foda run DEMO_ABC --flow onboarding` exitoso, un nuevo `status` marcaría **ambos** como `[presente]`.

**Cuándo usarlo:** en cualquier momento, para decidir qué falta por ejecutar o para verificar que un `run` produjo lo esperado.

#### Códigos de salida y errores (`status`)

| Situación | Comportamiento | Código |
|---|---|---|
| Consulta con éxito | Lista los flujos y sus artefactos en stdout | `0` |
| El cliente no existe | Mensaje en stderr nombrando el cliente | `1` |
| No se encuentra la raíz del proyecto | Mensaje en stderr | `1` |
| Falta `<cliente>` | Mensaje de uso de argparse | `2` |

---

## Uso diario del entorno virtual

Una vez hecha la **configuración inicial** (venv creado + `pip install -e .`), esos pasos **no se repiten**. En una terminal nueva solo necesitas activar el entorno y ejecutar el comando.

### Flujo típico en una terminal nueva (validado)

Desde la raíz del proyecto:

```powershell
# 1. Activar el entorno virtual (una vez por terminal)
.venv\Scripts\Activate.ps1

# 2. Crear el cliente (una sola vez por cliente)
foda client new COMPANY_XYZ

# 3. Consultar qué falta por ejecutar (solo lectura)
foda status COMPANY_XYZ

# 4. Ejecutar un flujo sobre el cliente (produce sus artefactos)
foda run COMPANY_XYZ --flow onboarding

# 5. Verificar que el flujo produjo lo esperado
foda status COMPANY_XYZ
```

> ✅ **No necesitas** volver a crear el venv ni reinstalar el paquete: el `.venv` y la instalación editable de `foda` persisten entre sesiones.

**Alternativa sin activar** (invoca el ejecutable del venv directamente, en una sola línea):

```powershell
.venv\Scripts\foda.exe client new COMPANY_XYZ
.venv\Scripts\foda.exe run COMPANY_XYZ --flow onboarding
```

### Activar y desactivar

- **Cada vez que abras una terminal nueva**, debes **activar** el entorno virtual antes de usar `foda`:

  ```powershell
  .venv\Scripts\Activate.ps1
  ```

- Para **desactivarlo**:

  ```powershell
  deactivate
  ```

---

## ¿Cuándo reinstalar el comando `foda`?

La instalación con `pip install -e .` (modo editable) se hace **una sola vez**. Gracias al modo editable, el comando `foda` queda enlazado al código fuente en `src/foda/`.

- ✅ **Cambias la lógica de los comandos** (código en `src/foda/cli.py` u otros módulos): **no necesitas reinstalar.** Los cambios se reflejan de inmediato.
- 🔁 **Debes reinstalar (`pip install -e .`) solo si cambias:**
  - El **entry point** en `pyproject.toml` → `[project.scripts]` (p. ej. renombrar el comando o cambiar `foda.cli:main`).
  - Las **dependencias** del proyecto (`dependencies` en `pyproject.toml`).
  - Metadatos del paquete (nombre, versión, configuración de `setuptools`).

---

## Ejecutar los tests

Con el entorno virtual activado:

```powershell
python -m pytest -q
```

La configuración de pytest (`pyproject.toml`) ya incluye `src` en el `pythonpath` y apunta a `tests/`.
