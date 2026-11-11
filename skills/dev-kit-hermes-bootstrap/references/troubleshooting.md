# Troubleshooting del bootstrap

Diagnostico por sintoma. Cada entrada tiene el sintoma observable, la causa mas
probable y la verificacion.

---

## Diagnostico: el orden correcto

Antes de buscar el sintoma exacto, estos cuatro pasos descartan el 80% de los
casos:

```bash
# 1. El CLI existe y responde
hermes --version

# 2. La configuracion esta completa
hermes doctor

# 3. El estado del gateway
hermes gateway status

# 4. Los logs del ultimo intento
tail -50 ~/.hermes/logs/errors.log
tail -50 ~/.hermes/logs/gateway.log
```

Si `hermes doctor` reporta errores, se arreglan antes de seguir. Todo lo de
esta pagina es para cuando doctor pasa y el problema es otro.

---

## Instalacion

### `curl: (7) Failed to connect`

| Causa | Verificacion | Solucion |
|---|---|---|
| Sin salida a internet | `ping 8.8.8.8` | Proxy o firewall |
| Corporate proxy | `env \| grep -i proxy` | Exportar `HTTPS_PROXY` |
| DNS | `nslookup raw.githubusercontent.com` | Cambiar DNS |

### `error: command 'gcc' failed` (Linux)

```bash
sudo apt install -y build-essential python3-dev
```

### `ModuleNotFoundError: No module named '_ssl'` (Linux)

```bash
sudo apt install -y python3-dev libssl-dev
```

### `error: externally-managed-environment` (macOS)

El Python del sistema esta protegido. Usar un venv:

```bash
python3 -m venv .venv && source .venv/bin/activate
```

### `hermes: command not found` despues de instalar

```bash
# Verificar donde quedo
ls -la ~/.local/bin/hermes

# Agregar al PATH de forma permanente
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

En macOS con zsh, el archivo es `~/.zshrc`.

### La instalacion quedo con permisos de root (Linux)

Si el instalador corrio con `sudo`, los archivos quedaron con el dueno
equivocado. Reinstalar como usuario normal:

```bash
sudo rm -rf ~/.local/bin/hermes ~/.hermes
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### En Windows: nada se instaló

El script bash no corre en Windows nativo. Usar el de PowerShell:

```powershell
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

---

## Configuracion

### `hermes doctor` reporta "no provider configured"

```bash
hermes model        # selector interactivo
hermes setup model  # wizard de modelo
```

### El modelo responde con error de autenticacion

| Sintoma | Causa | Solucion |
|---|---|---|
| 401 en Anthropic | `ANTHROPIC_API_KEY` invalida o con typo | Verificar la variable |
| 401 con prefijo `sk-ant-` | La clave tiene espacios al final | Sin espacios ni comillas |
| 401 en OpenRouter | `OPENROUTER_API_KEY` ausente | Exportar la variable |
| 429 | Limite de tasa | Cambiar de modelo o esperar |
| 404 en modelo custom | Nombre del modelo incorrecto | Verificar el nombre exacto del provider |

**Verificar la variable sin imprimirla:**

```bash
# Muestra solo si esta definida y cuanto mide
if [ -n "$ANTHROPIC_API_KEY" ]; then echo "definida (${#ANTHROPIC_API_KEY} chars)"; else echo "NO DEFINIDA"; fi
```

### La API key se cambio y sigue el error viejo

La clave vive en `~/.hermes/.env`, que se carga al arrancar. Despues de
cambiarla:

```bash
hermes gateway restart
```

### El YAML de config no parsea (Windows)

Casi siempre es el BOM:

```powershell
$path = "$env:USERPROFILE\.hermes\config.yaml"
$bytes = [System.IO.File]::ReadAllBytes($path)
if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF) {
    $text = [System.IO.File]::ReadAllText($path)
    [System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding $false))
}
```

El sintoma real es un error de YAML que no menciona el BOM y apunta a una
linea que parece correcta.

---

## Gateway

### `hermes gateway status` dice "not installed"

```bash
hermes gateway install
hermes gateway start
hermes gateway status
```

### El gateway anduvo y desaparecio (Linux)

```bash
loginctl show-user $USER | grep Linger
# Si no dice Linger=yes:
loginctl enable-linger $USER
```

### El gateway anduvo y desaparecio (WSL2)

```bash
cat /etc/wsl.conf
# Debe tener:
# [boot]
# systemd=true
# Despues: wsl --shutdown desde PowerShell
```

### El gateway arranca y se cae en loop (macOS)

```bash
launchctl list | grep hermes
tail -50 ~/.hermes/logs/gateway.log
```

Causa tipica: el PATH del plist esta incompleto. launchd arranca con un PATH
minimo. Regenerar el plist desde un shell interactivo:

```bash
hermes gateway uninstall
hermes gateway install
```

### `kill` no detiene el gateway (macOS)

launchd lo levanta de nuevo por `KeepAlive`. Usar `bootout`:

```bash
launchctl bootout gui/$(id -u)/ai.hermes.gateway
```

### El gateway no recibe mensajes de un canal

1. El token esta en `~/.hermes/.env` con el nombre exacto de la variable.
2. El gateway se reinicio despues de cambiar el token.
3. Los logs muestran el error de autenticacion del canal:

```bash
grep -i "telegram\|discord\|whatsapp" ~/.hermes/logs/gateway.log | tail -20
```

---

## Terminal y TUI

### En Windows Terminal, Alt+Enter no inserta newline

Es el comportamiento esperado de Windows Terminal. Usar `Ctrl+Enter`.

Efecto colateral: `Ctrl+J` tambien inserta newline en Windows.

### La TUI no arranca

```bash
node --version   # debe ser 22 o superior
hermes --tui
```

Si falta Node:

```bash
# Linux
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install -y nodejs

# macOS
brew install node@22
```

### La TUI se ve con caracteres raros

```bash
locale         # debe incluir UTF-8
echo $LANG
```

En WSL: `export LANG=C.UTF-8`.

---

## Skills

### `hermes skills list` no muestra las del kit

```bash
# Verificar donde las busca
hermes skills list
ls ~/.hermes/skills/

# Si existen pero no aparecen, revisar el frontmatter:
head -12 ~/.hermes/skills/<nombre>/SKILL.md
```

Los tres requisitos del frontmatter:

1. El archivo arranca con `---`.
2. Tiene `name:` que coincide exactamente con el nombre de la carpeta.
3. Tiene `description:` con contenido.

### El kit no instala nada

```bash
# Con SKILLS_SRC explicito
SKILLS_SRC=/ruta/a/dev-agent-skills/skills ./scripts/install.sh --target ~/.hermes/skills
```

En Windows sin bash: copiar la carpeta directamente.

### Un skill tiene un puntero roto

```bash
python3 scripts/scan_clean.py --strict
```

El scanner reporta los punteros a `references/`, `templates/` y `scripts/` que
no existen.

---

## Performance

### El agente responde lento

| Causa | Verificacion | Solucion |
|---|---|---|
| Contexto grande | `hermes status` muestra el tamano | `/compact` o iniciar sesion nueva |
| Modelo muy grande | Config | Bajar a un modelo mas chico |
| MCP server lento | Logs de arranque | Deshabilitar el MCP que no se use |
| Herramientas pesadas | Prompt de sistema | Revisar `enabled_toolsets` |

### Mucho consumo de tokens

```bash
hermes stats
```

Un agente con memoria habilitada reinyecta el perfil de usuario en cada
turno. Si no aporta, se desactiva:

```bash
hermes config set memory.user_profile_enabled false
```

---

## Cuando nada de esto aplica

```bash
hermes doctor --fix
hermes logs --level ERROR --follow
hermes config show
hermes status
```

Y si sigue sin resolverse, el reporte de bug necesita: version de Hermes
(`hermes --version`), version de Python, version de Node, SO, la salida
completa de `hermes doctor` y el error literal (no parafraseado).
