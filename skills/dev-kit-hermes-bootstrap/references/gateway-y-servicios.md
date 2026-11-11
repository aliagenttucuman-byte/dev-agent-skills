# Gateway y servicios

Como dejar el gateway andando de forma durable en cada sistema operativo.

---

## El problema

El gateway es el proceso que recibe mensajes de los canales (Telegram,
WhatsApp, Discord) y los despacha al agente. Si corre en primer plano, muere
al cerrar la terminal. Si corre con `nohup`, tampoco sobrevive al cierre de
sesion ni al reinicio.

La solucion es el servicio del sistema: el sistema operativo lo reinicia si
muere y lo arranca en el boot.

---

## Comandos

```bash
hermes gateway install     # instala como servicio del sistema
hermes gateway start       # arranca el servicio
hermes gateway stop        # detiene el servicio
hermes gateway status      # estado: running / stopped / not installed
hermes gateway uninstall   # desinstala el servicio
hermes gateway restart     # reinicia
```

**El orden correcto es install -> start -> status.** Un `start` sin `install`
deja el proceso corriendo en foreground o con `nohup`, que es exactamente lo
que no se quiere.

---

## Linux: systemd

### Servicio de usuario (default)

```bash
hermes gateway install
systemctl --user status hermes-gateway
systemctl --user enable hermes-gateway
```

El servicio de usuario vive en `~/.config/systemd/user/`.

### El detalle del linger

Sin linger, systemd detiene los servicios de usuario cuando el usuario cierra
sesion. Con linger, sobreviven.

```bash
loginctl enable-linger $USER
```

Sin esto, el gateway arranca, funciona mientras la sesion esta abierta y
desaparece. Es el fallo mas comun en un servidor con sesion SSH.

### Logs

```bash
journalctl --user -u hermes-gateway -f        # seguir en vivo
journalctl --user -u hermes-gateway -n 100    # ultimas 100 lineas
journalctl --user -u hermes-gateway --since "1 hour ago"
```

### Servicio de sistema (opcional)

```bash
sudo hermes gateway install --system
```

Requiere privilegios. Se usa cuando el gateway debe correr como un servicio
del sistema, compartido por varios usuarios o con permisos distintos.

### Editar la unidad

```bash
systemctl --user cat hermes-gateway      # ver la unidad
systemctl --user edit hermes-gateway     # editar sin pisar el original
```

### Variables de entorno

El servicio necesita las credenciales de los canales. Opciones, en orden de
preferencia:

1. `~/.hermes/.env` — el runtime lo lee solo. Es la opcion por defecto.
2. `EnvironmentFile=` en la unidad — para variables que no son credenciales de
   Hermes.
3. `systemctl --user import-environment` — poco recomendado: es por sesion.

---

## macOS: launchd

### Instalacion

```bash
hermes gateway install
hermes gateway start
hermes gateway status
```

Hermes genera el plist en:

```
~/Library/LaunchAgents/ai.hermes.gateway.plist
```

Con perfiles, el nombre lleva el sufijo del perfil:
`ai.hermes.gateway-<perfil>.plist`.

### Verificar

```bash
launchctl list | grep hermes
hermes gateway status
```

### Detener bien: bootout, no kill

```bash
# MAL: launchd lo levanta de nuevo porque KeepAlive esta activo
kill <pid>

# BIEN: descarga el servicio
launchctl bootout gui/$(id -u)/ai.hermes.gateway
```

El `KeepAlive` de launchd hace que el proceso reaparezca si se cae. Es el
comportamiento deseado cuando el proceso se cae solo, y no cuando el
administrador quiere detenerlo.

### Logs

```bash
# El plist define la ruta de los logs
tail -f ~/.hermes/logs/gateway.log
```

### El PATH de launchd

launchd arranca con un PATH minimo (`/usr/bin:/bin:/usr/sbin:/sbin`). Las
herramientas instaladas por Homebrew, nvm o cargo **no estan disponibles**.

Hermes lo resuelve capturando el PATH del shell del usuario al generar el
plist. Si se regenera el plist desde un shell no interactivo, el PATH puede
quedar incompleto y el gateway falla con "comando no encontrado".

```bash
# Regenerar el plist desde un shell interactivo con el PATH completo
hermes gateway uninstall
hermes gateway install
```

---

## Windows: Scheduled Task

```powershell
hermes gateway install
hermes gateway start
hermes gateway status
```

En Windows el servicio se registra como una tarea programada. Para verla:

```powershell
Get-ScheduledTask | Where-Object { $_.TaskName -like "*hermes*" }
```

Para el gateway de una sesion interactiva, la tarea corre como el usuario
actual. Para que arranque sin login, hay que configurarla con la opcion de
ejecutar "whether the user is logged on or not", que requiere credenciales.

### Alternativa en Windows: NSSM o WinSW

Si se necesita mas control (reinicio automatico, logs rotados, dependencia de
otros servicios), un wrapper como NSSM da mas control que la tarea
programada:

```powershell
nssm install hermes-gateway "C:\ruta\venv\Scripts\python.exe" "C:\ruta\gateway\run.py"
nssm set hermes-gateway AppStdout "C:\logs\hermes.out.log"
nssm set hermes-gateway AppStderr "C:\logs\hermes.err.log"
nssm set hermes-gateway AppExit Default Restart
nssm start hermes-gateway
```

---

## WSL2

```bash
# Sin systemd, el gateway corre con nohup y muere al cerrar la sesion
sudo tee /etc/wsl.conf > /dev/null <<'EOF'
[boot]
systemd=true
EOF

# Reiniciar desde PowerShell
wsl --shutdown

# Verificar
systemctl is-system-running
```

**Sintoma exacto:** el gateway anduvo toda la sesion, y al abrir WSL de nuevo
el proceso no esta. No hay error en ningun lado: no hay log porque el proceso
nunca arranco.

---

## Multiples perfiles

Cada perfil tiene su propio servicio, su propio home y su propio estado:

```bash
hermes --profile coder gateway install
hermes --profile coder gateway start
hermes --profile coder gateway status
```

Los servicios conviven: los labels llevan el sufijo del perfil.

---

## Multiples canales

Un solo gateway atiende todos los canales configurados. Los tokens van en
`~/.hermes/.env`:

```bash
TELEGRAM_BOT_TOKEN=...
WHATSAPP_...
DISCORD_BOT_TOKEN=...
```

El gateway se **instala una vez** y despues se configuran los canales. Si se
configura un canal antes de instalar el servicio, la configuracion se pierde
al reiniciar.

---

## Checklist de gateway

- [ ] `hermes gateway install` ejecutado
- [ ] `hermes gateway start` ejecutado
- [ ] `hermes gateway status` dice "running"
- [ ] `loginctl enable-linger $USER` en Linux
- [ ] `systemd=true` en `/etc/wsl.conf` si es WSL2
- [ ] Los tokens de los canales en `~/.hermes/.env`
- [ ] Los logs se ven en el destino correcto
- [ ] Probado el reinicio: si la maquina se apaga y prende, el gateway vuelve
