# Pipeline de CI para Python

Estructura de referencia. Ajustar versiones y pasos al proyecto, pero
mantener el orden: lo mas rapido falla primero.

---

## Orden de las etapas

```
install -> lint -> format -> types -> test
```

- `install` con cache: sin cache, es el paso mas lento y siempre cambia.
- `lint` y `format`: segundos, detectan la mayoria de los errores triviales.
- `types`: segundos a minutos, detecta errores de contrato.
- `test`: minutos, lo mas caro.

Si un cambio rompe lint y un test, el pipeline debe reportar lint primero.
Cada etapa posterior depende de que la anterior pase.

---

## Workflow de referencia

```yaml
name: ci

on:
  pull_request:
  push:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  quality:
    name: lint-types-${{ matrix.python-version }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.5"
          enable-cache: true

      - run: uv sync --all-extras --frozen

      - name: ruff lint
        run: ruff check . --output-format=github

      - name: ruff format
        run: ruff format --check .

      - name: mypy
        run: mypy src

      - name: pyright
        run: pyright src

      - name: pytest
        run: pytest -q --cov=src --cov-report=xml --cov-fail-under=80

  matrix-os:
    name: tests-${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.5"
          enable-cache: true

      - run: uv sync --all-extras --frozen

      - name: pytest
        run: pytest -q -m "not slow"

  package:
    name: package
    runs-on: ubuntu-latest
    needs: [quality, matrix-os]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.5"
      - run: uv sync --all-extras --frozen
      - run: uv build
      - name: verificar instalacion limpia
        run: |
          python -m venv .venv-verify
          .venv-verify/bin/python -m pip install dist/*.whl
          .venv-verify/bin/python -c "import REEMPLAZAR_paquete; print('ok')"
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

---

## Decisiones y su porque

### `concurrency` con `cancel-in-progress`

Si se empuja un commit mientras corre el pipeline, el anterior se cancela. Sin
esto, se acumulan runs que consumen minutos de runner y nadie mira el
resultado viejo.

### `fail-fast: false`

En la matriz de versiones de Python, un fallo en 3.13 no dice nada sobre 3.12.
Con `fail-fast: true` se cancela el resto y se pierde informacion. Se quiere
ver todos los fallos de una vez.

### `--output-format=github`

ruff sabe anotar el PR inline cuando el formato de salida es `github`. Sin eso,
el resultado aparece como un bloque de texto en el log.

### `--frozen` y no `uv sync`

En CI se verifica el lockfile, no se re-resuelven las dependencias. Si el
lockfile esta desactualizado respecto a `pyproject.toml`, el pipeline falla y
eso es intencional: obliga a correr `uv lock` y commitear el lockfile.

### Cache de uv

`enable-cache: true` cachea el entorno de uv, no el binario. Es la diferencia
entre 60 segundos y 4 minutos de install.

### Verificar el paquete instalado

El paso `package` instala el wheel en un venv limpio e importa el paquete. Es
la unica forma de detectar que falta un archivo en el `packages = [...]` de
`pyproject.toml`, o que un entrypoint apunta a un modulo que no se publico.

---

## Gates y cuando relajarlos

No se relajan gates en CI. Se relajan con una exception explicita y con fecha.

```yaml
# Excepcion temporal y documentada
- name: mypy
  run: mypy src
  continue-on-error: true # TODO(equipo): fix de strict en modulo X, issue #123
```

Un `continue-on-error` sin issue referenciado es deuda invisible. El gate real
vuelve cuando el issue se cierra.

---

## Test de contrato del pipeline

El pipeline se testea como codigo. Un workflow roto se descubre cuando se
necesita, que es tarde.

```bash
# act: correr el workflow localmente antes de pushear
act -j quality --matrix python-version=3.12

# actionlint: validacion estatica del YAML
actionlint .github/workflows/ci.yml
```

`actionlint` detecta errores que YAML no ve: expresiones mal escritas,
`needs` a jobs inexistentes, `if` con sintaxis invalida.

---

## Cache de pip alternativa

Si el proyecto usa `pip` en vez de `uv`:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
    cache: pip
    cache-dependency-path: requirements/*.txt
```

El cache se invalida por el hash del lockfile. Si el lockfile no existe, el
cache no se invalida nunca y se sirve un entorno viejo: peor que no tener
cache.
