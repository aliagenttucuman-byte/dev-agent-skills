---
name: dev-kit-code-quality
description: "Estandares de codigo verificables con lint y format automaticos, type hints estrictos, pre-commit y gates de calidad con umbral medible. CARGAR cuando hay que definir reglas de codigo, configurar ruff y mypy, montar pre-commit o decidir que bloquea un merge."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-quality, lint, typing, pre-commit, gates]
    category: software-development
    related_skills: [dev-kit-testing, dev-kit-ci-cd, dev-kit-review, dev-kit-backend-stack, dev-kit-frontend-stack]
---

# Dev Kit - Calidad de Codigo

> **Trigger:** "definir reglas de codigo", "configurar ruff", "mypy en modo estricto",
> "armar pre-commit", "que bloquea el merge", "la calidad del codigo cayo".
> Cargar esta skill ANTES de escribir la primera linea de un modulo nuevo.

## Que es esto

Un contrato de calidad **verificable por comandos**. No una guia de estilo: la guia
se escribe en el codigo y la verifica una herramienta. Esta skill define tres
cosas y nada mas:

1. Que reglas aplican a cada lenguaje.
2. Que comando prueba cada regla.
3. Que umbral bloquea el merge.

Si una regla no tiene comando, no es una regla: es una sugerencia. Si un comando no
tiene umbral, no es un gate: es un script que corre.

## El contrato de calidad

| Dimension | Herramienta | Comando | Umbral que bloquea |
|---|---|---|---|
| Formato | ruff | `ruff format --check .` | 0 diferencias |
| Lint | ruff | `ruff check .` | 0 errores |
| Tipos (Python) | mypy | `mypy src` (strict) | 0 errores |
| Tipos (TS) | tsc | `tsc --noEmit` | 0 errores |
| Complejidad | radon / complexipy | ver seccion de complejidad | sin funciones clase B o peor |
| Tests | pytest | `pytest -q` | 0 fallos |
| Cobertura | coverage | `pytest --cov=src --cov-report=term` | no baja de la linea base |
| Secretos | gitleaks | `gitleaks detect --no-git` | 0 filtraciones |
| Formatos | pre-commit-hooks | `pre-commit run --all-files` | 0 fallos |

**Regla:** la linea base de cobertura sube, nunca baja. Un cambio que la reduce se
rechaza o se acompaña de un ADR que explique por que.

## Workflow

| Paso | Que hace | Artefacto | Gate |
|---|---|---|---|
| 1. Inventariar | Detecta lenguaje, framework y herramientas ya instaladas | tabla de herramientas | No se agrega una herramienta que ya existe |
| 2. Configurar | Escribe la configuracion de lint, format y tipos | `ruff-config.toml`, seccion de mypy/tsc | El comando corre y falla si hay un error de verdad |
| 3. Blindar local | Instala pre-commit con los mismos hooks que CI | `templates/pre-commit-config.yaml` | `pre-commit run --all-files` verde |
| 4. Medir | Calcula complejidad y nesting del codigo existente | reporte de complejidad | Todo el codigo nuevo queda bajo el umbral |
| 5. Publicar gates | Convierte cada dimension en un gate de CI | tabla de gates | El gate corre en CI y falla el pipeline |

### Paso 1 - Inventariar antes de configurar

No se instala nada sin ver que hay. El orden evita el conflicto clasico: el repo
ya tiene un formateador y el equipo agrega otro que lo deshace.

```bash
# Python
python -m pip list | grep -Ei "ruff|mypy|black|flake8|isort|pylint"
ls pyproject.toml setup.cfg .ruff.toml mypy.ini 2>/dev/null
# TypeScript / Frontend
node -v && npm ls --depth=0 | grep -Ei "eslint|prettier|typescript|vitest"
```

Salida esperada: una lista de herramientas en uso y una de herramientas
propuestas, con la razon de cada alta.

### Paso 2 - ruff: lint y format

ruff reemplaza el par formateador + linter con una sola herramienta y una sola
configuracion. Es el default del stack.

```bash
ruff check . --fix          # autofix seguro y opinion de formato
ruff format .               # formateo de archivos
ruff check . --statistics   # que regla falla mas
ruff rule NAME              # que hace la regla y como se desactiva
```

Reglas que se activan siempre en un proyecto de producto:

| Familia | Que atrapa | Ejemplo |
|---|---|---|
| `E`, `W` | errores de estilo y warnings de pycodestyle | linea en blanco al final |
| `F` | errores de pyflakes | variable importada sin usar |
| `I` | orden de imports | imports sin ordenar |
| `B` | bugs comunes | mutable default, f-string sin placeholders |
| `SIM` | codigo simplificable | `if x == True` |
| `C4` | comprehension innecesaria | `list()` en un for |
| `UP` | sintaxis moderna | `Optional[X]` en vez de `X \| None` |
| `N` | nombres | `variables` en snake_case |
| `ANN` | anotaciones faltantes | funcion sin tipo de retorno |
| `S` | banda de seguridad | `hashlib.md5` para passwords |
| `PTH` | uso de `os.path` | preferir `pathlib` |
| `RUF` | reglas deopinion propia | imports sin usar en `__init__` |

La configuracion completa esta en `templates/ruff-config.toml`.

**Regla de desactivacion:** una regla se desactiva con `# noqa: RULE` **y** un
comentario que diga por que. Un `# noqa` sin justificacion es una regla rota.

### Paso 3 - Type hints estrictos

Un tipado " suave" no sirve: o tipa todo, o no tipa nada. La diferencia entre
`Any` y un tipo real es la diferencia entre "el compilador ayuda" y "el compilador
calla".

```ini
# mypy.ini (o seccion [tool.mypy] de pyproject.toml)
[tool.mypy]
python_version = "3.12"
strict = True
warn_unreachable = True
disallow_untyped_defs = True
disallow_any_unimported = True
no_implicit_optional = True
check_untyped_defs = True
warn_unused_ignores = True
```

En TypeScript el equivalente es `strict: true` en `tsconfig.json` mas
`noUncheckedIndexedAccess: true`, que obliga a chequear el acceso a indices.

| Situacion | Que hacer |
|---|---|
| Funcion publica | Anotacion completa en argumentos y retorno |
| Funcion interna corta | Anotacion de argumentos; el retorno se infiere |
| `Any` explicito | Solo en frontera con codigo no tipado, con `# type: ignore` acotado |
| `cast` | Preferir un chequeo de tipo (`isinstance`) sobre `cast` |
| `# type: ignore` | Con codigo de error: `# type: ignore[arg-type]` |

**Gate de tipos:** `mypy src` con `strict = True` en modo CI. Un error de tipos
nunca se ignora en silencio: se arregla o se documenta el porque en el PR.

### Paso 4 - Pre-commit: el gate que corre antes del push

Pre-commit replica en la maquina del equipo los gates de CI. Un hook que falla en
el hook y no en el pipeline significa que el equipo aprendio a saltarselo.

```bash
pip install pre-commit
pre-commit install          # engancha el hook al commit
pre-commit run --all-files # corre todo sobre el repo
```

El archivo base esta en `templates/pre-commit-config.yaml`. El orden importa:
formateo antes de lint, lint antes de tipos, tipos antes de tests.

### Paso 5 - Gates de calidad

Un gate se define por tres cosas: **que mide**, **como se ejecuta** y **que
pasa si falla**. Sin la tercera, no es un gate.

| Gate | Medida | Comando | Si falla |
|---|---|---|---|
| G1 Formato | diff contra el canon | `ruff format --check .` | bloquea el commit |
| G2 Lint | errores por regla | `ruff check .` | bloquea el commit |
| G3 Tipos | errores de tipado | `mypy src` | bloquea el pipeline |
| G4 Complejidad | clases de complejidad | `radon cc -s -n B src` | bloquea el pipeline |
| G5 Tests | tests rojos | `pytest -q` | bloquea el pipeline |
| G6 Secretos | filtraciones | `gitleaks detect --no-git` | bloquea el pipeline |
| G7 Cobertura | delta contra la linea base | `pytest --cov=src` | bloquea el pipeline |
| G8 Build | artefacto construible | comando de build | bloquea el pipeline |

Los gates G3 a G8 corren en CI (`dev-kit-ci-cd` los cablea). Los gates G1 y G2
corren en pre-commit. La duplicacion es intencional: la velocidad local evita el
ciclo largo de CI.

## Metricas de complejidad

La complejidad no se mide por opinion. Se mide y se pone un techo.

| Metrica | Como se calcula | Umbral | Por que |
|---|---|---|---|
| Complejidad ciclomatica | numero de caminos de ejecucion (`radon cc`) | 10 (clase B) | mas de 10 caminos = mas de 10 casos de test |
| Deep nesting | niveles de indentacion | 4 niveles | la logica anidada esconde condiciones |
| Longitud de funcion | lineas por funcion | 50 lineas | funciones cortas se testean |
| Cantidad de argumentos | parametros por funcion | 5 | muchos argumentos = un objeto de dominio |
| Acoplamiento | imports por modulo | 15 | modulo que importa todo no se testea aislado |
| Duplicacion | bloques repetidos (ruff no, `ruff` + revision) | 3 lineas repetidas | el copy-paste es deuda sin dueño |

```bash
radon cc -s -n A src          # solo lo que supera A
radon raw -s src              # lineas, complejidad, volumen por archivo
complexipy src                # alternativas si no se quiere radon
```

**Como bajar la complejidad, en orden de costo:**

1. Extraer la condicion a una funcion con nombre (`is_eligible(order)`).
2. Aplicar early return: el caso raro se va primero, el camino feliz queda plano.
3. Reemplazar la cascada de `if` por una tabla de reglas.
4. Partir la funcion en dos cuando cada mitad tiene su propio nombre.
5. En el ultimo caso, un patron (Strategy, Policy) - con ADRs, porque aca el costo
   de legibilidad sube.

**Regla:** un refactor que sube la complejidad ciclomatica total del modulo para
bajar la de una funcion no es un improvement. Se mide antes y despues.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| "El lint lo hacemos al final" | Se acumulan cientos de errores y nadie los arregla | Activar el formateo en el primer commit |
| Agregar un formateador sin revisar el existente | Dos formateadores se pelean en cada commit | Inventariar primero |
| `# noqa` sin justificacion | La regla queda rota en silencio | Comentario con el porque, o no desactivar |
| `mypy` sin `strict` | "Tipado" que no detecta nada | `strict = True` en CI |
| Cobertura como objetivo | Se testea para cubrir lineas, no comportamiento | Cobertura como piso, no como meta |
| Ignorar errores de tipos con `Any` en cascada | El `Any` se propaga y borra todo el valor | `Any` solo en la frontera |
| Gate que no falla | Da sensacion de rigor sin rigor | Cada gate declara su comando y su umbral |
| Medicion sin umbral | La metrica se reporta y no se usa | Umbral por metrica, o no se mide |
| Formato aplicado sobre codigo con errores | El formateo genera un diff gigante | Formatear despues de que los tests pasen |
| Excepciones sin fecha ni responsable | Nadie vuelve a mirarlas | Excepcion con ADR y fecha de revision |

## Referencias

- `templates/pre-commit-config.yaml` - configuracion base de pre-commit, con el
  orden de hooks correcto
- `templates/ruff-config.toml` - configuracion de ruff: reglas activadas, ignores
  justificados y `per-file-ignores` para tests
- `references/gates-calidad.md` - como se implementa cada gate, como se escala una
  excepcion y como se mide la linea base de cobertura
- `references/metricas-complejidad.md` - calculo de complejidad ciclomatica, deep
  nesting y las recetas de refactor ordenadas por costo

### Archivos de esta skill

- `templates/pre-commit-config.yaml` - hooks de pre-commit listos para copiar
- `templates/ruff-config.toml` - configuracion de ruff lista para `pyproject.toml`
- `references/gates-calidad.md` - detalle de implementacion de los gates G1 a G8
- `references/metricas-complejidad.md` - guia de complejidad y refactor
