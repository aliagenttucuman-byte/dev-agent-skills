---
name: dev-kit-hermes-bootstrap
description: "Instalar, configurar y verificar el runtime de agentes Hermes en Linux, macOS y Windows: instalacion por plataforma, seleccion de provider y modelo, configuracion de memoria, gateway durable como servicio del sistema, verificacion con hermes doctor y troubleshooting de quirks por sistema operativo. CARGAR cuando hay que levantar Hermes en una maquina nueva, configurar un provider, dejar el gateway andando en background, resolver un problema de instalacion o de terminal en Windows o macOS."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [bootstrap, instalacion, hermes, gateway, provider, windows, macos]
    category: devops
    related_skills: [dev-kit-ci-cd, dev-kit-observability, dev-kit-security, dev-kit-project-bootstrap]
---

# Dev Kit - Bootstrap de Hermes

> **Trigger:** "instalar Hermes", "levantar Hermes", "configurar el provider",
> "que el gateway quede corriendo", "Hermes en Windows", "Hermes en macOS",
> "hermes doctor", "el agente no arranca". Cargar esta skill ANTES de
> instalar o configurar el runtime.

## Que es esto

El contrato de como se levanta un runtime de agentes funcional en una maquina
limpia. El kit de skills es el activo vendible, pero sin el runtime no hay
agente: esta skill cubre el "despues" de la instalacion.

**La premisa:** la instalacion del CLI no es el producto. El producto es que el
agente quede **andando, verificado y durable** al terminar el proceso. Un
gateway que muere al cerrar la terminal es una demo, no una instalacion.

## Los tres estados finales

Un bootstrap completo deja el runtime en uno de estos tres estados, y cada uno
tiene su verificacion:

| Estado | Que significa | Como se verifica |
|---|---|---|
| **Instalado** | El CLI existe y responde | `hermes --version` |
| **Configurado** | Hay provider, modelo y credenciales | `hermes doctor` sin errores |
| **Durable** | El gateway sobrevive al cierre de sesion | `hermes gateway status` con servicio activo |

El tercero es el que casi nunca se completa y es el que hace la diferencia
entre un PoC y un producto.

## Workflow

| Paso | Que hace | Artefacto | Gate |
|---|---|---|---|
| 1. Precheck | Verificar SO, runtime y espacio | reporte de precheck | Todo lo requerido esta |
| 2. Instalar | Instalador oficial de la plataforma | CLI funcional | `hermes --version` responde |
| 3. Configurar | Provider, modelo y credenciales | config persistida | `hermes doctor` sin errores |
| 4. Verificar | Chequeo de dependencias | salida de doctor | Cero errores |
| 5. Durable | Gateway como servicio del sistema | servicio activo | `hermes gateway status` |
| 6. Kit | Instalar las skills del producto | skills cargadas | `hermes skills list` las ve |
| 7. Smoke | Prueba de extremo a extremo | mensaje de respuesta | El agente responde |

### Paso 1 - Precheck

Antes de instalar, verificar que la maquina tiene lo necesario. Es mas barato
fallar aca que a mitad de la instalacion.

| Requisito | Linux | macOS | Windows |
|---|---|---|---|
| Python | 3.11+ | 3.11+ | 3.11+ |
| Node | 22+ (para el TUI) | 22+ | 22+ |
| Git | `git --version` | `git --version` | `git --version` |
| uv | recomendado | recomendado | recomendado |
| Compiladores | `build-essential` | Xcode CLT | Visual C++ Build Tools |
| Path | `~/.local/bin` en PATH | `/opt/homebrew/bin` en PATH | `%LOCALAPPDATA%\hermes` |

```bash
# Linux
python3 --version && node --version && git --version && uv --version

# macOS: si falta Homebrew, el instalador lo detecta
command -v brew || echo "falta homebrew"

# Windows (PowerShell)
python --version; node --version; git --version; uv --version
```

**Reglas:**

- Python 3.11 es el minimo verificado. 3.12 y 3.13 funcionan.
- En Linux, `build-essential` y `python3-dev` hacen falta para compilar
  dependencias que no tienen wheel para la plataforma. Sin ellos, la
  instalacion falla con un error de compilacion poco descriptivo.
- En macOS, Xcode Command Line Tools: `xcode-select --install`. Sin eso
  fallan paquetes que necesitan compilar.
- El directorio de instalacion tiene que estar en el PATH **antes** de
  instalar: si no, el CLI queda inaccesible.

### Paso 2 - Instalar (por plataforma)

**Linux y macOS:**

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

El instalador oficial detecta el SO, instala Python y Node si faltan, crea el
entorno virtual y deja el CLI en el PATH.

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

**El instalador bash detecta Windows y se niega a correr:**

```
Windows detected. Please use the PowerShell installer:
  irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

Esto es intencional: en Windows el layout del entorno virtual es distinto
(`venv/Scripts/activate` + `python.exe`, no `venv/bin/activate`) y el
instalador bash no lo contempla.

**Flags utiles del instalador de Windows:**

```powershell
.\install.ps1 -NoVenv      # sin entorno virtual, usa el Python del sistema
.\install.ps1 -SkipSetup   # instala pero no lanza el wizard
.\install.ps1 -HermesHome "D:\hermes"   # directorio de datos custom
```

**Reglas:**

- Instalar con el instalador oficial, no clonar el repo a mano. El instalador
  maneja el PATH, el venv y la version de Python.
- Verificar siempre antes de seguir:

```bash
hermes --version
```

### Paso 3 - Configurar provider y modelo

```bash
hermes setup          # wizard completo
hermes setup model    # solo modelo y provider
hermes model          # selector interactivo de provider
hermes login          # login OAuth (nous, openai-codex)
```

Los providers usan variables de entorno, que viven en `~/.hermes/.env`:

| Provider | Variable | Como se autentica |
|---|---|---|
| OpenRouter | `OPENROUTER_API_KEY` | API key |
| Anthropic | `ANTHROPIC_API_KEY` | API key |
| OpenAI | `OPENAI_API_KEY` | API key o OAuth |
| Google Gemini | `GOOGLE_API_KEY` o `GEMINI_API_KEY` | API key |
| DeepSeek | `DEEPSEEK_API_KEY` | API key |
| MiniMax | `MINIMAX_API_KEY` | API key |
| Local (Ollama, llama.cpp, vLLM) | ninguna | endpoint local |

**Reglas:**

- Las credenciales van en `~/.hermes/.env`, que **nunca** se versiona. El
  archivo ya esta en el `.gitignore` interno del runtime.
- `hermes model` permite cambiar de provider en caliente, sin reiniciar. Es la
  forma de comparar modelos sin tocar configuracion.
- Para un provider que no sea de la lista, se configura a mano:

```yaml
# ~/.hermes/config.yaml
model:
  provider: custom
  default: <nombre-del-modelo>
  base_url: <endpoint>
  api_key: <clave>
```

**Nunca pegar la clave en un archivo que se versione.** Si el `.env` se
compartió por error, la clave se rota: no se "limpia" el repo.

### Paso 4 - Verificar con hermes doctor

```bash
hermes doctor
hermes doctor --fix    # corrige lo que se puede corregir solo
```

`hermes doctor` revisa: el CLI y su venv, la configuracion, el provider y sus
credenciales, las dependencias del sistema, los MCP servers configurados y el
estado del gateway.

**Regla:** el bootstrap no termina hasta que `hermes doctor` no reporta
errores. Los warnings se anotan y se siguen; los errores bloquean.

### Paso 5 - Dejar el gateway durable

Esta es la parte que distingue una instalacion de una demo.

```bash
hermes gateway install     # instala como servicio del sistema
hermes gateway start       # arranca
hermes gateway status      # verifica
hermes gateway uninstall   # desinstala
```

**Como funciona en cada sistema:**

| Sistema | Mecanismo | Archivo |
|---|---|---|
| Linux | systemd (user o system) | unidad de systemd |
| macOS | launchd | `~/Library/LaunchAgents/*.plist` |
| Windows | Scheduled Task | tarea programada de Windows |

**WSL2 es el caso especial:** systemd requiere `systemd=true` en `/etc/wsl.conf`:

```ini
# /etc/wsl.conf
[boot]
systemd=true
```

Sin esa linea, `hermes gateway install` cae a un proceso `nohup` que **muere
al cerrar la sesion de WSL**. Es el fallo mas comun en Windows.

**Reglas:**

- El gateway se instala como servicio **antes** de configurar los canales. Si
  no, se pierde la configuracion al reiniciar.
- Con multiples canales (Telegram, WhatsApp, Discord), cada uno se configura
  con su token en `~/.hermes/.env`.
- `hermes gateway status` es la verificacion. Si no dice "running", el proceso
  no va a sobrevivir.
- Para un gateway que debe arrancar en el boot del sistema, hay que usar la
  variante de system-level, que requiere permisos de administrador.

### Paso 6 - Instalar el kit de skills

El runtime ya andando, se instala el kit:

```bash
# Con el kit completo
./scripts/install.sh --target ~/.hermes/skills --profile standard

# Verificacion
hermes skills list
```

El perfil `minimal` instala solo el spine de metodologia (8 skills). `standard`
agrega agentes e ingenieria. `full` agrega las verticales.

En Windows, el instalador es bash: se necesita WSL o git-bash. Si no hay
ninguno, se copia la carpeta de skills directamente:

```powershell
Copy-Item -Path .\skills\* -Destination "$env:USERPROFILE\.hermes\skills" -Recurse -Force
```

### Paso 7 - Smoke test

```bash
# 1. El CLI responde
hermes --version

# 2. La configuracion esta completa
hermes doctor

# 3. El gateway esta vivo
hermes gateway status

# 4. El agente responde
hermes chat -q "Respondé con la palabra: OK"

# 5. Las skills se cargan
hermes skills list
```

Los cinco tienen que pasar. Si el cuarto falla, el problema es de provider o de
credenciales, no de instalacion.

## Quirks por sistema operativo

### Windows nativo

| Quirk | Detalle | Workaround |
|---|---|---|
| Instalador | No hay `install.sh` | `irm ... install.ps1 \| iex` |
| Venv | `venv/Scripts/activate` + `python.exe` | No usar `venv/bin/activate` |
| Salto de linea | `Alt+Enter` no inserta newline | Usar `Ctrl+Enter` |
| BOM UTF-8 | Rompe el parseo del YAML de config | Re-guardar sin BOM |
| Permisos | POSIX mode bits no se aplican | No confiar en `0o600` |
| Symlinks | Requieren permisos elevados | Evitarlos en tests |
| Tests del repo | `run_tests.sh` busca venvs POSIX | Correr pytest directo |
| PATH | El CLI queda en `%LOCALAPPDATA%\hermes` | Verificar que esta en PATH |

**El detalle del BOM:** Windows Terminal y algunos editores Windows escriben
UTF-8 **con BOM**. El parser YAML de la configuracion no lo tolera y falla con
un error que no menciona el BOM. La solucion es re-guardar el archivo como
UTF-8 sin BOM.

```powershell
# Verificar y quitar el BOM
$bytes = [System.IO.File]::ReadAllBytes("$env:USERPROFILE\.hermes\config.yaml")
$bytes[0..2] -eq 0xEF,0xBB,0xBF   # True = tiene BOM
```

### macOS

| Quirk | Detalle | Workaround |
|---|---|---|
| Python del sistema | Restricciones `EXTERNALLY-MANAGED` | Usar venv siempre |
| Compiladores | Faltan sin Xcode CLT | `xcode-select --install` |
| Homebrew | Ruta `/opt/homebrew/bin` en Apple Silicon | Verificar PATH |
| Gateway | launchd, no systemd | `hermes gateway install` lo maneja |
| Permisos | POSIX mode bits si se aplican | Normal |

**Gateway en macOS:** Hermes genera el plist en
`~/Library/LaunchAgents/`. Para verificarlo:

```bash
launchctl list | grep hermes
hermes gateway status
```

El `KeepAlive` de launchd hace que el proceso reaparezca si se cae. Para
detenerlo hay que hacer `bootout`, no `kill`: si se hace `kill`, launchd lo
levanta de nuevo.

### WSL2

| Quirk | Detalle | Workaround |
|---|---|---|
| systemd | Requiere `systemd=true` en `/etc/wsl.conf` | Editar y reiniciar WSL |
| Gateway sin systemd | Cae a `nohup`, muere al cerrar | Activar systemd |
| Paths | Windows y Linux ven archivos distintos | Trabajar en `/home`, no en `/mnt/c` |

### Linux

| Quirk | Detalle | Workaround |
|---|---|---|
| Compiladores | Faltan `build-essential`, `python3-dev` | `sudo apt install build-essential python3-dev` |
| systemd de usuario | Requiere login persistente | `loginctl enable-linger $USER` |
| Instalador como root | El instalador rehuye root | Instalar como usuario normal |

**`loginctl enable-linger`:** sin esto, los servicios de usuario de systemd
se detienen cuando el usuario cierra sesion. Es el equivalente Linux del
problema de WSL2.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Instalar el CLI pero no el gateway | El agente muere al cerrar la terminal | `hermes gateway install` |
| Dejar el gateway en `nohup` | No sobrevive al cierre de sesion | Servicio del sistema |
| `setup` sin `doctor` | Seems bien hasta que falla en produccion | `hermes doctor` antes de cerrar |
| Credenciales en `config.yaml` versionado | Fuga de claves | Solo en `~/.hermes/.env` |
| Instalar como root en Linux | Archivos con el dueno equivocado | Usuario normal |
| Ignorar el BOM en Windows | El YAML no parsea y el error no lo dice | UTF-8 sin BOM |
| `Alt+Enter` en Windows Terminal | No inserta newline | `Ctrl+Enter` |
| Instalar skills sin verificar | Un puntero roto no se ve hasta que se usa | `hermes skills list` + smoke |
| Clonar el repo a mano | El PATH y el venv quedan mal | Instalador oficial |
| WSL2 sin systemd | El gateway muere al cerrar | `systemd=true` en `/etc/wsl.conf` |
| Sin `loginctl enable-linger` | El servicio muere al desloguearse | Habilitar linger |
| `kill` al proceso de launchd | launchd lo levanta de nuevo | `launchctl bootout` |

## Referencias

### Skills relacionadas

- `dev-kit-security` - baseline de secretos, de credenciales y de superficie expuesta.
- `dev-kit-observability` - logs y metricas del servicio una vez andando.
- `dev-kit-ci-cd` - automatizar la instalacion en una maquina limpia.
- `dev-kit-project-bootstrap` - bootstrap de un proyecto de software, no del runtime.

### Archivos de esta skill

- `references/instalacion-por-plataforma.md` - comandos exactos y flags por sistema.
- `references/gateway-y-servicios.md` - systemd, launchd, Scheduled Tasks y WSL2.
- `references/troubleshooting.md` - diagnostico por sintoma, con el error exacto.
