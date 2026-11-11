# Entornos y dependencias en Python

Como elegir el gestor de paquetes y resolver conflictos sin perder el
entorno reproducible.

---

## Criterio de decision

| Situacion | Herramienta | Por que |
|---|---|---|
| Proyecto nuevo | `uv` | Resuelve y bloquea en un paso, muy rapido |
| Proyecto existente con `requirements.txt` | `pip` + `pip-tools` | No obliga a migrar de golpe |
| Base de codigo corporativa con constraints | `pipenv` | Los constraints son.first-class |
| Script sin dependencias | stdlib + `venv` | Nada que instalar |
| Entorno compartido entre servicios | Docker | Aislamiento completo |

El default del kit es `uv`, compatible con `pip` y `venv`. Un proyecto que usa
`pip` no es un problema: `pip` instala lo que `uv` bloqueo.

---

## uv: el camino por defecto

```bash
uv init --package nombre-proyecto     # proyecto con src/ layout
uv add fastapi pydantic                # dependencia de runtime
uv add --dev pytest ruff mypy         # dependencia de desarrollo
uv sync --all-extras                  # instala todo en .venv
uv sync --frozen                      # reproduce el lockfile exacto
uv lock                               # regenera uv.lock
uv run pytest                         # ejecuta en el venv del proyecto
uv pip list                           # lo que quedo instalado
uv venv --python 3.12                 # venv con version especifica
```

`uv run` es el comando que hay que usar siempre que el proyecto tenga venv: no
depende de que el shell este activado. Un developer con `pip` global
instala en el venv equivocado sin darse cuenta.

### Grupos de dependencias

```toml
[dependency-groups]
dev = ["pytest>=8.3", "ruff>=0.7", "mypy>=1.13"]
docs = ["mkdocs>=1.6", "mkdocstrings>=0.26"]
```

Los grupos son de `uv` y se instalan con `uv sync --group dev`. Los extras
(`[project.optional-dependencies]`) son parte del paquete publicado: se
instalan con `pip install .[dev]` por cualquiera que lo consuma. La diferencia
importa: un extra es una promise publica del paquete.

---

## pip + pip-tools: migracion suave

Para un proyecto existente con `requirements.txt`:

```bash
pip install pip-tools
pip-compile requirements.in --output-file requirements.txt
pip-sync requirements.txt
```

La convencion: `requirements.in` tiene las dependencias directas (a mano),
`requirements.txt` tiene el arbol completo con versiones pineadas (generado).
Solo se edita `.in`.

```bash
# actualizar una dependencia
pip-compile --upgrade-package fastapi requirements.in
```

---

## Conflictos de dependencias

El conflicto mas comun: dos paquetes piden versiones incompatibles de una
transitiva.

```bash
# Ver que pide cada paquete
pipdeptree --graph | head -50
pip show <paquete> | grep Requires
```

Cuatro salidas, en orden de preferencia:

1. **Actualizar el paquete que impone el conflicto.** Si `A` es viejo y `B` ya
  soporta la version nueva, actualizar `A` es la respuesta.
2. **Cambiar de variante del paquete.** Muchas librerias publican variantes
   (`foo` y `foo-fast`, `foo-core`) con pins distintos.
3. **Acotar la version.** `numpy>=1.26,<2.0` — funciona hasta que la segunda
   transitiva cambien.
4. **Vendorizar.** Solo cuando las otras tres fallaron y la dependencia es
   pequena. Se documenta el motivo en el PR.

Lo que no se hace: `pip install --no-deps` para "resolver" un conflicto. Eso
instala un entorno que va a fallar en runtime, en la parte mas cara.

---

## Venv siempre en el proyecto

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows (PowerShell)
```

Nunca se instala en el Python del sistema. El Python del sistema pertenece al
SO y a otros proyectos; actualizar un paquete ahi rompe cosas que no tienen
relacion.

En macOS, el Python del sistema tiene restricciones de permisos (`EXTERNALLY-
MANAGED`). El venv no las tiene. Es otra razon para usar venv siempre.

```bash
# desactivar
deactivate
```

---

## Variables de entorno y secretos

```python
# core/config.py
from pydantic import BaseModel, SettingsConfigDict


class Configuracion(BaseModel):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    api_key: str
    debug: bool = False
```

- `.env` esta en `.gitignore` desde el primer commit.
- `.env.example` versiona las claves sin valores.
- En CI, las variables vienen de los secrets del repositorio.
- En produccion, del secret manager. Nunca del `.env` en el repo.

---

## Checklist de entorno

- [ ] `.venv/` en `.gitignore`
- [ ] `.env` en `.gitignore`, `.env.example` versionado
- [ ] `uv.lock` o `requirements.txt` versionado
- [ ] `requires-python` declarado
- [ ] Comandos canonicos en `Makefile` o `justfile`
- [ ] `python -m venv` documentado para quien no usa `uv`
- [ ] La CI instala con `--frozen` y cache por lockfile
