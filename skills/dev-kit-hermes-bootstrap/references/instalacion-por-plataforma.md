# Instalacion por plataforma

Comandos exactos y flags por sistema operativo. Todos verificados contra el
instalador oficial del runtime.

---

## Tabla resumen

| | Linux | macOS | Windows |
|---|---|---|---|
| Instalador | `install.sh` | `install.sh` | `install.ps1` |
| Python minimo | 3.11 | 3.11 | 3.11 |
| Node | 22+ | 22+ | 22+ |
| Compiladores | `build-essential` `python3-dev` | Xcode CLT | VC++ Build Tools |
| Home del runtime | `~/.hermes` | `~/.hermes` | `%LOCALAPPDATA%\hermes` |
| PATH del CLI | `~/.local/bin` | `~/.local/bin` | `%LOCALAPPDATA%\hermes` |

---

## Linux

### Instalacion

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### Precheck

```bash
# Distribucion y version
cat /etc/os-release | head -3

# Dependencias de sistema
sudo apt update && sudo apt install -y build-essential python3-dev git curl

# Herramientas de lenguaje
python3 --version   # 3.11 o superior
node --version      # 22 o superior
uv --version
```

### Verciones comunes de error

| Error | Causa | Solucion |
|---|---|---|
| `error: command 'gcc' failed` | Faltan compiladores | `sudo apt install build-essential python3-dev` |
| `ModuleNotFoundError: No module named '_ssl'` | Python sin dev headers | `sudo apt install python3-dev` |
| `hermes: command not found` | El PATH no incluye el directorio | `export PATH="$HOME/.local/bin:$PATH"` y agregar al `.bashrc` |
| `Permission denied` al ejecutar | El instalador corrió como root | Reinstalar como usuario normal |
| El gateway muere al desloguearse | Falta linger | `loginctl enable-linger $USER` |

### linger: el detalle que se olvida

```bash
# Sin linger, los servicios de usuario de systemd mueren al cerrar sesion
loginctl enable-linger $USER

# Verificar
loginctl show-user $USER | grep Linger
```

Con `linger` activo, los servicios de usuario sobreviven al cierre de sesion
y al reinicio de la maquina.

---

## macOS

### Instalacion

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### Precheck

```bash
# Herramientas de compilacion (sin esto fallan varios paquetes)
xcode-select --install

# Homebrew (ruta distinta segun arquitectura)
command -v brew || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"   # Apple Silicon

python3 --version
node --version
```

### Particularidades

| Tema | Detalle |
|---|---|
| Python del sistema | Tiene marca `EXTERNALLY-MANAGED`: `pip install` global falla. El venv no tiene ese problema. |
| Ruta de Homebrew | `/opt/homebrew/bin` en Apple Silicon, `/usr/local/bin` en Intel. |
| Gatekeeper | Puede pedir permiso para ejecutar binarios descargados. |
| Case-insensitive | El sistema de archivos no distingue mayusculas: `File.md` y `file.md` son el mismo. Rompe builds que asumen Linux. |

### El detalle del Python del sistema

```bash
$ pip3 install algo
error: externally-managed-environment
```

Es intencional: macOS protege el Python del sistema. La respuesta correcta es
un venv, no `sudo pip3 install`.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## Windows

### Instalacion (PowerShell)

```powershell
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

O descargando el script para ver los flags:

```powershell
.\install.ps1 -NoVenv
.\install.ps1 -SkipSetup
.\install.ps1 -HermesHome "D:\hermes"
.\install.ps1 -InstallDir "D:\hermes\hermes-agent"
```

### Precheck

```powershell
python --version    # 3.11 o superior
node --version      # 22 o superior
git --version
uv --version
```

Si no hay Python, el instalador puede bajarlo con `uv`. Si hay que compilar
paquetes, hace falta Visual C++ Build Tools.

### El script bash se niega a correr

```
Windows detected. Please use the PowerShell installer:
  irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

No es un bug: es la deteccion de plataforma del instalador oficial. El layout
del entorno virtual en Windows es `venv/Scripts/activate` con `python.exe`, y
el instalador bash asume `venv/bin/activate`.

### BOM UTF-8: el fallo invisible

Muchos editores de Windows guardan con BOM. El parser YAML de la configuracion
no lo tolera:

```powershell
# Detectar
$path = "$env:USERPROFILE\.hermes\config.yaml"
$bytes = [System.IO.File]::ReadAllBytes($path)
if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    Write-Host "TIENE BOM - hay que quitarlo"

    # Quitar el BOM re-guardando el contenido
    $text = [System.IO.File]::ReadAllText($path)
    [System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "BOM eliminado"
}
```

El sintoma real es un error de parseo YAML que no menciona el BOM, y el
mensaje apunto a la linea equivocada.

### Terminal: Alt+Enter no inserta newline

Windows Terminal intercepta `Alt+Enter` y lo envia al shell. En Hermes, el
shortcut que inserta un newline real es `Ctrl+Enter`. Efecto colateral
inevitable: `Ctrl+J` tambien inserta newline en Windows.

En git-bash el comportamiento es el de POSIX: `Alt+Enter` funciona.

---

## WSL2

WSL2 no es "Windows con Linux": es una maquina Linux con una capa de
traduccion de archivos.

| Tema | Detalle |
|---|---|
| Systemd | Requiere `systemd=true` en `/etc/wsl.conf` y reiniciar WSL |
| Gateway sin systemd | Cae a `nohup` y muere al cerrar la sesion |
| Paths | `/mnt/c/...` es lento; trabajar en `/home/...` |
| Performance | El acceso a archivos de Windows desde WSL es orders of magnitud mas lento |

### Activar systemd

```bash
# Crear o editar /etc/wsl.conf
sudo tee /etc/wsl.conf > /dev/null <<'EOF'
[boot]
systemd=true
EOF

# Reiniciar WSL desde PowerShell
wsl --shutdown
```

### Verificar

```bash
# Si esto imprime "running", systemd esta activo
systemctl is-system-running

# El gateway debe verse como servicio
systemctl --user status hermes-gateway
```

---

## Instalacion desatendida (CI / imagen de maquina)

Para una maquina virtual efimera, el bootstrap tiene que ser no interactivo:

```bash
set -euo pipefail

curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

export PATH="$HOME/.local/bin:$PATH"
hermes --version

# El setup interactivo se saltea: la configuracion se inyecta por archivo
mkdir -p "$HOME/.hermes"
cat > "$HOME/.hermes/.env" <<EOF
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
EOF

cat > "$HOME/.hermes/config.yaml" <<'EOF'
model:
  provider: anthropic
  default: claude-sonnet-4
EOF

hermes doctor
hermes chat -q "respond: OK"
```

El punto clave: `hermes setup` es interactivo y **no** sirve para una
instalacion desatendida. La configuracion se escribe como archivo.

### Instalacion idempotente

```bash
# Reejecutar el instalador es seguro: detecta la instalacion existente
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- --force
```

### Instalacion en Docker

```dockerfile
FROM python:3.12-slim

ARG APP_USER=appuser
ARG APP_HOME=/opt/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Usuario sin privilegios: el runtime no necesita root y no deberia tenerlo.
RUN useradd --create-home --shell /bin/bash ${APP_USER}

USER ${APP_USER}
WORKDIR ${APP_HOME}

RUN curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

ENV PATH="${APP_HOME}/.local/bin:${PATH}"

ENTRYPOINT ["hermes"]
CMD ["chat"]
```

En Docker no hace falta gateway: el contenedor es el proceso. El gateway
como servicio es para maquinas con session persistente.
