---
name: dev-kit-python-tooling
description: "Tooling profesional de Python: pyproject.toml, gestion de entornos y dependencias, ruff para lint y format, mypy y pyright en modo estricto, pre-commit, packaging, versionado y CI. CARGAR cuando hay que configurar un proyecto Python desde cero, agregar una dependencia, fightar un error de tipos, armar el pipeline de calidad o publicar un paquete."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [python, tooling, pyproject, ruff, mypy, pyright, ci, packaging]
    category: software-development
    related_skills: [dev-kit-backend-stack, dev-kit-code-quality, dev-kit-ci-cd, dev-kit-testing]
---

# Dev Kit - Tooling Python

> **Trigger:** "configurar Python", "agregar una dependencia", "pyproject",
> "ruff", "mypy estricto", "error de tipos", "armar el CI de Python", "publicar
> un paquete". Cargar esta skill ANTES de crear `pyproject.toml` o de tocar la
> configuracion de lint y tipos.

## Que es esto

El contrato de como se equipa un proyecto Python para que sobreviva a seis
meses y a tres personas. No es un tutorial de Python: es la capa de
herramientas que hace que el codigo sea verificable automaticamente.

La premisa: **cada error que un humano tiene que encontrar leyendo codigo es
un error que una herramienta deberia haber encontrado antes.** Ruff, mypy y
pyright cubren clases distintas de defectos:

| Herramienta | Encuentra | No encuentra |
|---|---|---|
| ruff | estilo, imports, bugs triviales, complejidad | tipos, logica |
| mypy | tipos, firmas, incompatibilidades | estilo, logica |
| pyright | tipos mas rapido, inferencia mas lista | estilo, logica |
| pytest | comportamiento, regresiones | tipos, estilo |
| bandit | patrones inseguros | todo lo demas |

Una herramienta sola no alcanza. El gate real es la interseccion.

## Workflow

| Paso | Que hace | Artefacto | Gate |
|---|---|---|---|
| 1. Fijar la toolchain | Python y gestor de paquetes declarados | `pyproject.toml` | Un solo lugar declara versiones |
| 2. Entorno reproducible | Todo se instala con un comando | lockfile | Clone limpio levanta igual |
| 3. Lint y format | ruff, una sola config | `ruff.toml` | `ruff check` limpio |
| 4. Tipos | mypy y pyright en strict | `mypy.ini` / `pyrightconfig.json` | Cero errores sin `ignore` nuevo |
| 5. Gate local | pre-commit corre lo mismo que CI | `.pre-commit-config.yaml` | No hay commit con lint roto |
| 6. Empaquetado | El proyecto se instala en otros entornos | `pyproject.toml` build-system | `pip install .` funciona |

### Paso 1 - Fijar la toolchain

Todo se declara en `pyproject.toml`. Nada de `setup.py`, nada de `setup.cfg`
paralelo, nada de versiones sueltas en el README.

```toml
# pyproject.toml
[project]
name = "servicio-pedidos"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "pydantic>=2.9",
    "sqlalchemy>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "ruff>=0.7",
    "mypy>=1.13",
    "pyright>=1.1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/servicio_pedidos"]
```

**Reglas:**

- `requires-python` es una cota, no una sugerencia. Si el codigo usa `match` o
  `X | Y` en anotaciones, la cota es `>=3.10`.
- Las dependencias de desarrollo van en `[project.optional-dependencies]`, no en
  `requirements-dev.txt`.
- `src/` layout, no import desde la raiz. Con `src/` el paquete instalado y el
  del repo no se confunden, y los tests importan lo que se va a publicar.
- El `build-backend` se declara una vez. Todo lo que no sea paquete distribuible
  (servicios, apps internas) puede usar `uv` o `pip install -e .` sin build
  backend, pero se documenta cual de los dos es.

La plantilla completa, con extras para el packeteo y los entrypoints, esta en
`templates/pyproject.toml`.

### Paso 2 - Entorno reproducible

El criterio de decision:

| Situacion | Herramienta | Comando |
|---|---|---|
| Proyecto nuevo, velocidad y lockfile | `uv` | `uv init` / `uv add` / `uv sync` |
| Proyecto existente con `requirements.txt` | `pip` + `pip-tools` | `pip-compile` |
| EcOSistema corporativo con constraints | `pip` + `pipenv` | `pipenv install` |
| Solo un script sin dependencias | stdlib | `python -m venv` |

El default del kit es `uv`: resuelve y bloquea en un solo archivo, y es
compatible con `pip` y `venv` estandar.

```bash
# Instalar todo el proyecto, incluido el grupo dev, en un venv local
uv sync --all-extras

# Agregar una dependencia de runtime
uv add httpx

# Agregar una dependencia de desarrollo
uv add --dev pytest-cov

# Reproducir el lockfile exacto
uv sync --frozen
```

**Reglas:**

- El lockfile se versiona. Sin lock, "funciona en mi maquina" es la unica verdad.
- El venv vive dentro del proyecto (`.venv/`), nunca en una ruta global.
- `.venv/` y `__pycache__/` estan en `.gitignore` desde el primer commit.
- Un `Makefile` o `justfile` con los comandos canonicos evita que cada
  developer memorice flags distintos:

```make
.PHONY: install lint type test check
install:
	uv sync --all-extras
lint:
	ruff check . && ruff format --check .
type:
	mypy src && pyright src
test:
	pytest -q
check: lint type test
```

### Paso 3 - Lint y format con ruff

ruff reemplaza flake8, isort, black, pylint y varios mas, en un solo binario
nativo. Es el default del kit sin discusion.

```toml
# pyproject.toml
[tool.ruff]
target-version = "py312"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8 naming
    "UP",   # pyupgrade
    "B",    # bugbear
    "A",    # builtin shadowing
    "C4",   # comprehensions
    "SIM",  # simplify
    "RUF",  # ruff specific
    "S",    # bandit
    "ANN",  # missing annotations
    "ASYNC",
    "T20",  # print() en codigo de produccion
]
ignore = [
    "ANN101",  # self no necesita anotacion
    "ANN102",  # cls no necesita anotacion
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "ANN", "T20"]
"scripts/**" = ["T20"]

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "parents"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

**Reglas:**

- El set de `select` es explicito. La Implicitamente `select = ["E", "F"]` es
  insuficiente y no escala.
- `ANN` obliga a anotar. Una funcion sin anotacion de retorno no pasa el gate.
- `T20` prohibe `print()` en codigo de produccion: se usa logging. Los tests
  y scripts se exceptuan explicitamente por path, no globalmente.
- `per-file-ignores` por path exacto. No se desactivan reglas globalmente para
  tapar un archivo problematico.
- `ruff format` decide el formato. No se discute formato en el code review:
  el formateador ya decidio.

```bash
ruff check .              # lint
ruff check . --fix       # lint + autofix seguro
ruff format .            # formatear
ruff format --check .    # gate: solo verifica
```

### Paso 4 - Tipos en modo estricto

El error de tipos mas caro no es el que aparece: es el que no aparece porque
todo esta en `Any`.

**mypy**, con configuracion estricta:

```ini
# mypy.ini
[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true
warn_unused_ignores = true
show_error_codes = true
files = src, tests

[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
```

**pyright**, con el mismo criterio:

```json
// pyrightconfig.json
{
  "include": ["src", "tests"],
  "pythonVersion": "3.12",
  "typeCheckingMode": "strict",
  "reportMissingTypeStubs": "warning",
  "reportPrivateUsage": "none"
}
```

**Reglas:**

- `strict = true` en mypy. `warn_unused_ignores = true` es lo que hace util el
  `ignore`: si el error ya no existe, el `ignore` sobrante falla el build.
- `warn_unreachable = true` detecta codigo muerto: un `return` despues de un
  `raise`, o un `else` que nunca se cumple.
- Los tests se exceptuan de `disallow_untyped_defs`, pero no de la verificacion
  de tipos en si. Un fixture mal tipado rompe los tests de forma confusa.
- `Any` explicito se permite con `# type: ignore[no-any-return]` y una
  justificacion. `Any` implícito (no anotado) no pasa el gate.
- `TYPE_CHECKING` para imports que solo existen en tiempo de analisis:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
```

**El orden importa:** `ruff` primero (rapido, corrige solo), despues `mypy`,
despues `pyright`. Si los tres fallan a la vez, el ruido del formateador tapa
el error de tipos real.

```bash
mypy src && pyright src
```

Los patrones de tipos que resuelven el 90% de los casos estan en
`references/patrones-de-tipos.md`.

### Paso 5 - Gate local con pre-commit

El gate que corre antes del push es el que de verdad previene. Si el CI es el
unico lugar donde se detecta el error, el ciclo de feedback es de minutos.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        files: ^src/
        additional_dependencies: [sqlalchemy, pydantic, fastapi]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

**Reglas:**

- Los hooks corren sobre lo staged, no sobre todo el repo. Es la diferencia
  entre un gate de 2 segundos y uno de 40.
- `mypy` en pre-commit recibe las dependencias del proyecto en
  `additional_dependencies`. Sin eso, el hook falla por imports no resueltos y
  el equipo lo desactiva.
- `detect-private-key` es obligatorio en cualquier repositorio.
- El hook de `mypy` no debe hacer el proyecto entero: es lento. Se limita a los
  archivos tocados.

```bash
pre-commit install        # enganchar el hook al commit
pre-commit run --all-files # correr todo sobre el repo
```

### Paso 6 - Empaquetado y versionado

Un proyecto que se usa como libreria tiene que ser instalable por otros.

```bash
# Verificacion local del paquete, sin publicarlo
uv build
pip install dist/*.whl

# Publicacion
uv publish --check-url
```

**Reglas:**

- El paquete se prueba instalado, no desde el repo. Un `pip install .` en un
  venv limpio antes de cada release.
- La version sigue semver, y la version se incrementa sola en el commit de
  release, no a mano.
- Los entrypoints se declaran explicitamente:

```toml
[project.scripts]
mi-cli = "servicio_pedidos.cli:main"
```

- El changelog se genera desde los commits con `conventional commits` + `git-cliff`
  o similar, no se escribe a mano.

### Paso 7 - CI de Python

El pipeline de Python tiene cuatro etapas, y el orden importa: lo mas rapido
falla primero.

```yaml
# .github/workflows/ci.yml
name: ci
on:
  pull_request:
  push:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.5"
      - run: uv sync --all-extras --frozen
      - run: ruff check .
      - run: ruff format --check .
      - run: mypy src
      - run: pyright src
      - run: pytest -q --cov=src --cov-report=term-missing --cov-fail-under=80
```

**Reglas:**

- La matriz de versiones de Python es parte del contrato: si el proyecto dice
  `requires-python = ">=3.12"`, el CI prueba 3.12 y la siguiente.
- `--frozen` en CI: el CI verifica el lockfile, no lo re-resuelve. Si el
  lockfile esta desactualizado, el CI falla y eso es intencional.
- La cobertura tiene umbral (`--cov-fail-under`), no es un numero decorativo.
- Los jobs de lint, tipos y tests pueden correr en paralelo: son independientes
  y aceleran el feedback.

El pipeline completo, con matriz de SO para tests que dependen del path del
sistema, esta en `references/ci-python.md`.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| `requirements.txt` sin lock | "Funciona en mi maquina" | `uv sync --frozen` en CI |
| `setup.py` + `setup.cfg` + `pyproject.toml` | Tres fuentes de verdad | Solo `pyproject.toml` |
| `mypy` sin `strict` | Todo termina en `Any` | `strict = true` |
| `# type: ignore` sin codigo de error | Oculta errores de otros tipos | `# type: ignore[no-any-return]` |
| `warn_unused_ignores` desactivado | Los ignores se acumulan muertos | Dejarlo en `true` |
| Desactivar regla de ruff globalmente | Se pierde en todo el repo | `per-file-ignores` por path |
| `print()` en produccion | Sin nivel, sin contexto, no se redirige | `logging` con `structlog` |
| Formatear en el code review | Discusiones sin contenido | `ruff format` decide |
| Instalar en el Python del sistema | Rompe el SO y los otros proyectos | venv en el proyecto |
| `pip install -r requirements.txt` en el CI | No respeta el lock | `uv sync --frozen` |
| Tests que dependen del orden de ejecucion | Fallan en CI y no local | `pytest-randomly` o `-p no:randomly` explicito |
| Sin `target-version` en ruff | Reglas nuevas se activan solas | Fijar la version objetivo |

## Referencias

### Skills relacionadas

- `dev-kit-backend-stack` - arquitectura por capas del backend Python.
- `dev-kit-code-quality` - contrato de calidad transversal y metricas de complejidad.
- `dev-kit-testing` - estrategia de tests, fixtures y mocks.
- `dev-kit-ci-cd` - promocion, rollback y seguridad del pipeline.

### Archivos de esta skill

- `templates/pyproject.toml` - plantilla completa de proyecto Python.
- `references/patrones-de-tipos.md` - patrones de tipado que resuelven los casos recurrentes.
- `references/ci-python.md` - pipeline de CI de Python con matriz y cobertura.
- `references/entornos-y-dependencias.md` - como elegir gestor y resolver conflictos.
