# Foda_Application

Aplicación FODA desarrollada bajo la metodología **SDD/TDD** del proyecto (ver `CLAUDE.md` y `980_guideline/principles.md`).

Este README describe cómo preparar el entorno y usar la **CLI `foda`** para crear clientes.

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

### Códigos de salida y errores

| Situación | Comportamiento | Código |
|---|---|---|
| Cliente creado con éxito | Imprime la ruta en stdout | `0` |
| Nombre de cliente inválido (p. ej. `"a b"`, `".."`, `"-x"`) | Mensaje en stderr | `1` |
| Cliente duplicado (ya existe) | Mensaje en stderr | `1` |
| No se encuentra la raíz del proyecto (sin `pyproject.toml` en ancestros) | Mensaje en stderr | `1` |
| Falta el nombre o subcomando desconocido | Mensaje de uso de argparse | `2` |

---

## Uso diario del entorno virtual

Una vez hecha la **configuración inicial** (venv creado + `pip install -e .`), esos pasos **no se repiten**. En una terminal nueva solo necesitas activar el entorno y ejecutar el comando.

### Flujo típico en una terminal nueva (validado)

Desde la raíz del proyecto:

```powershell
# 1. Activar el entorno virtual (una vez por terminal)
.venv\Scripts\Activate.ps1

# 2. Crear el cliente
foda client new COMPANY_XYZ
```

> ✅ **No necesitas** volver a crear el venv ni reinstalar el paquete: el `.venv` y la instalación editable de `foda` persisten entre sesiones.

**Alternativa sin activar** (invoca el ejecutable del venv directamente, en una sola línea):

```powershell
.venv\Scripts\foda.exe client new COMPANY_XYZ
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
