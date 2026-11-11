---
name: dev-kit-ci-cd
description: "Pipeline de entrega continua con etapas, gates obligatorios, matriz de versiones, cache de dependencias, artefactos inmutables, promocion entre ambientes, rollback y seguridad del pipeline. CARGAR al crear o revisar el pipeline, cuando un gate falla en CI, al definir la estrategia de despliegue o cuando hay que promover una version entre ambientes."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ci-cd, pipeline, gates, deployment, rollback]
    category: software-development
    related_skills: [dev-kit-code-quality, dev-kit-testing, dev-kit-security, dev-kit-observability, dev-kit-database]
---

# Dev Kit - CI/CD

> **Trigger:** "crear el pipeline", "el gate falla en CI", "definir como se
> despliega", "promover a staging", "como hago rollback", "los secretos se
> filtraron en el pipeline". Cargar ANTES de escribir el workflow.

Un pipeline es una cadena de etapas con gates. Cada gate responde a tres
preguntas: **que mide**, **como se ejecuta** y **que pasa si falla**. Un gate
sin la tercera pregunta no es un gate: es decoracion que cuesta minutos y no
protege nada.

## La regla que gobierna todo

> **El artefacto que cruzo los gates es el unico que se despliega. Nunca se
> reconstruye en el paso de despliegue.**

Si el despliegue vuelve a compilar, el software que llega al ambiente no es el
que los gates verificaron. La diferencia entre "probamos lo que se despliega" y
"probamos algo parecido" es la diferencia entre un pipeline y un adorno.

## Etapas del pipeline

| # | Etapa | Que hace | Comando de referencia |
|---|---|---|---|
| 0 | checkout | baja el commit exacto | `actions/checkout@v4` |
| 1 | install | resuelve dependencias contra el lockfile | `pip install -r requirements.txt` |
| 2 | lint | formato y reglas estaticas | `ruff format --check .` |
| 3 | typecheck | verificacion de tipos | `mypy src` |
| 4 | test | suite completa | `pytest -q` |
| 5 | build | empaqueta el software | `docker build -t $IMAGE .` |
| 6 | scan | imagen y dependencias | `trivy image $IMAGE` |
| 7 | deploy | publica el artefacto | `deploy.sh $ENV $TAG` |
| 8 | verify | smoke test y health check | `curl -fsS $HEALTH_URL` |

**Regla:** las etapas 0 a 6 corren en cada push y en cada PR. Las etapas 7 y 8
corren por ambiente, con el artefacto producido en 5. La etapa 8 es la unica
que decide si la promocion sigue.

## Gates entre etapas

Los gates de codigo (`dev-kit-code-quality` los define como G1 a G8) se cablean
aca. Lo que se agrega es el gate de orquestacion: **cada etapa solo arranca si
la anterior quedo en verde**.

| Gate | Mide | Si falla |
|---|---|---|
| C1 lint | formato y reglas | bloquea el pipeline |
| C2 typecheck | errores de tipos | bloquea el pipeline |
| C3 test | tests rojos | bloquea el pipeline |
| C4 coverage | delta contra la linea base | bloquea el pipeline, sube y nunca baja |
| C5 secrets | filtraciones en el diff | bloquea el pipeline |
| C6 build | el artefacto se construye | bloquea el pipeline |
| C7 scan | vulnerabilidades de la imagen | bloquea o exige excepcion con fecha |
| C8 verify | health check y smoke del ambiente | hace rollback |

```yaml
# El encadenamiento se declara con needs. Es el unico mecanismo valido.
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: [{ run: "ruff check ." }]
  typecheck:
    needs: lint          # gate: sin lint verde, typecheck no arranca
    runs-on: ubuntu-latest
    steps: [{ run: "mypy src" }]
  test:
    needs: typecheck
    runs-on: ubuntu-latest
    steps: [{ run: "pytest -q" }]
  build:
    needs: test
    runs-on: ubuntu-latest
    steps: [{ run: "docker build -t $IMAGE_NAME:$IMAGE_TAG ." }]
```

**Regla:** un gate con `continue-on-error: true` o con `if: always()` es un
gate decorativo. Si se necesita tolerancia a fallos, se declara sobre una
etapa **no bloqueante** (por ejemplo, un reporte de cobertura), nunca sobre un
gate de seguridad.

**Regla:** el pipeline falla rapido. La primera etapa roja corta el resto. En
una matriz se evalua cada version por separado y se reporta el detalle de
todas.

## Matriz de versiones

La matriz responde a una pregunta: **contra que versiones tiene que funcionar
el proyecto?** Ni una mas.

| Eje | Valores tipicos | Cuando se agrega |
|---|---|---|
| version de lenguaje | 3.11, 3.12, 3.13 | el proyecto declara soporte multi-version |
| sistema operativo | linux, macos, windows | hay codigo sensible a la plataforma |
| base de datos | 15, 16 | el proyecto depende de comportamiento versionado |
| navegador | chromium, firefox, webkit | hay pruebas end-to-end |

```yaml
strategy:
  fail-fast: false        # una version rota no oculta las demas
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
    include:
      - python-version: "3.12"
        coverage: true    # solo la version de referencia mide cobertura
```

**Regla:** `fail-fast: false` cuando la matriz tiene mas de un valor. Con
`fail-fast: true` el pipeline muere en la primera combinacion y el equipo se
queda sin informacion sobre el resto.

**Regla:** la cobertura se mide en **una sola** combinacion de la matriz.
Medir cobertura en cada version multiplica el tiempo por nada.

**Regla:** el numero de combinaciones se mantiene pequeno. Si la matriz tarda
mas de 15 minutos en total, se divide en jobs paralelos en vez de agrandarla.

## Cache de dependencias

El cache acelera la instalacion, pero **es estado no confiable**: se comparte
entre ramas y hay que aislarlo.

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: pip
    cache-dependency-path: requirements.txt
```

| Regla | Motivo |
|---|---|
| la clave incluye el hash del lockfile | si no, el cache sirve dependencias viejas |
| nunca cachear `node_modules` ni `.venv` | el arbol instalado depende del sistema y se corrompe |
| nunca cachear credenciales ni `.env` | el cache es legible por otras ramas |

**Regla:** el cache acelera, pero el pipeline debe ser **correcto sin cache**.
Si un pipeline solo pasa porque el cache esta tibio, el cache es un gate
falso.

## Artefactos

Un artefacto es cualquier salida que un ambiente consume: imagen, paquete,
bundle o binario.

| Regla | Motivo |
|---|---|
| el artefacto se nombra con el commit y la version | sin nombre no hay rollback |
| se versiona por digest, no por tag mutable | un tag se puede reescribir |
| tiene retencion explicita y publica su digest | para saber que se desplego y cuanto se guarda |

```bash
# Nombre del artefacto: una variable, una fuente de verdad.
IMAGE_NAME="$REGISTRY/$SERVICE"
IMAGE_TAG="$(git rev-parse --short HEAD)"
echo "$IMAGE_NAME:$IMAGE_TAG" > image_ref.txt
```

**Regla:** el artefacto se **construye una vez** y se **promociona** por
ambientes. Reconstruir por ambiente hace que staging y produccion corran
codigo distinto, que es justo el fallo que el pipeline deberia evitar.

## Promocion entre ambientes

| Ambiente | Quien despliega | Como se llega | Requisito para avanzar |
|---|---|---|---|
| dev | cualquiera con push | automatico al mergear | pipeline verde |
| staging | automatico tras merge | automatico | pipeline verde y datos sinteticos |
| prod | con aprobacion | manual o por politica | staging verificado y aprobacion |

```text
commit -> pipeline verde -> dev -> (verificado) -> staging -> (aprobado) -> prod
```

**Regla:** la promocion es **el mismo artefacto**, con el mismo digest, en
todos los ambientes. Solo cambian la configuracion.

**Regla:** cada ambiente declara sus propias variables y secretos. La
configuracion viaja por ambiente, nunca dentro de la imagen: una imagen con la
configuracion horneada obliga a reconstruir por ambiente.

**Regla:** las migraciones de base de datos son un paso **separado** y
**anterior** al despliegue de la aplicacion, con estrategia *expand/contract*:
se agrega el schema compatible con la version vieja, se despliega el codigo
nuevo y recien despues se elimina el schema viejo. Un deploy que cambia el
schema y el codigo a la vez no tiene rollback posible.

## Rollback

| Decision | Valor por defecto |
|---|---|
| objetivo de tiempo | menor a 10 minutos |
| mecanismo | redeploy del digest anterior, verificado |
| disparador | health check en rojo o error rate sobre el presupuesto |
| verificacion posterior | health check en verde y smoke test |
| alcance | rollback de aplicacion, no de esquema |

**Regla:** el rollback es **un comando**, no una secuencia improvisada. Si
desplegar requiere cinco pasos y revertir requiere ocho, en incidente se
revierte mal.

```bash
# Rollback: redeploy del digest anterior, con verificacion posterior.
set -euo pipefail
"$DEPLOY_SCRIPT" "$ENVIRONMENT" "$(cat previous_digest.txt)"
curl -fsS "$HEALTH_URL" > /dev/null
```

**Regla:** el rollback se **prueba antes de necesitarlo**. Un rollback que
nunca se ejecuto en un ambiente de prueba no es un plan de rollback, es una
esperanza.

**Regla:** si el cambio incluye migracion incompatible con la version anterior,
el rollback de aplicacion no aplica. Por eso *expand/contract* es la regla.

## Seguridad del pipeline

| Riesgo | Control |
|---|---|
| secretos expuestos en logs | secretos de ambiente, nunca `echo` de un valor |
| permisos excessive | `permissions:` minimos por job, `contents: read` por defecto |
| workflow inyectado por un PR | el PR no puede modificar el workflow que lo ejecuta |
| action de terceros comprometida | version fijada, idealmente por hash de commit |
| runner comprometido | runners efimeros, nunca repos con pull request de forks |
| artefacto alterado | verificacion de digest antes de promover |

```yaml
permissions:
  contents: read          # minimo global; cada job amplia si lo necesita
  pull-requests: write    # solo en el job que comenta el resultado
```

**Regla:** `pull_request_target` no se usa junto con checkout del codigo del
PR. Esa combinacion ejecuta codigo de un contributor externo con los permisos
del repositorio.

**Regla:** los secretos llegan al pipeline por identidad temporal de la
ejecucion, no por llaves permanentes almacenadas: una llave permanente es una
deuda sin fecha de vencimiento.

**Regla:** el pipeline nunca imprime el valor de un secreto. Para verificar
que existe, se imprime solo su presencia y su alcance.

## Pipeline como codigo

| Regla | Motivo |
|---|---|
| el pipeline vive en el repositorio, versionado | un pipeline en la interfaz no se revisa |
| todo cambio del pipeline requiere PR | un pipeline auto-modificado es una puerta trasera |
| el PR que toca el pipeline exige revisor con permiso de escritura | el pipeline ejecuta codigo con permisos |
| las acciones se fijan a una version o a un hash | una etiqueta movil cambia de contenido |

**Regla:** los checks requeridos se configuran como **branch protection** en
la rama principal: el merge se bloquea hasta que los gates esten en verde. Un
gate que no esta en la lista de checks requeridos no es un gate: es un
informe.

**Regla:** el pipeline tiene un modo de ejecucion local documentado
(`./scripts/ci-local.sh`, mismo orden y mismos comandos), para que el equipo
reproduzca en su maquina lo que corre el servidor.

**Regla:** el tiempo total del pipeline se mide y se reporta. Un pipeline que
supera los 15 minutos deja de ejecutarse completo por el equipo y sus gates
dejan de proteger.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| reconstruir en el paso de deploy | se despliega algo distinto a lo probado | promover el mismo artefacto |
| gate con `continue-on-error` | el gate es decorativo | mover la tolerancia a una etapa de reporte |
| `if: always()` en etapas criticas | el pipeline sigue sin condiciones | encadenar con `needs` |
| matriz que mide cobertura en cada version | tiempo multiplicado sin valor | una sola combinacion mide cobertura |
| cache con clave sin hash del lockfile | dependencias viejas, fallo elusive | incluir el hash en la clave |
| cachear `.env` o credenciales | fuga de secretos | cachear solo dependencias |
| artefacto con tag mutable | no se sabe que version se desplego | versionar por digest |
| deploy a produccion sin aprobacion | el error llega a los usuarios | gate de aprobacion por ambiente |
| migracion y codigo en el mismo deploy | no hay rollback posible | estrategia *expand/contract* |
| rollback improvisado | en incidente se revierte mal | un comando, probado |
| `pull_request_target` con checkout del PR | codigo externo con permisos internos | workflow separado y sin secrets |
| acciones por rama flotante | el contenido cambia sin aviso | fijar version o hash |
| secrets impresos en logs | la fuga llega al historial | verificar presencia, no valor |

## Referencias

- `templates/github-actions-ci.yml` - pipeline de CI: lint, typecheck, test en
  matriz, build y publicacion del artefacto
- `templates/github-actions-deploy.yml` - promocion por ambientes con
  aprobacion, verificacion y rollback
- `references/promocion-y-rollback.md` - promocion, expand/contract y playbook
  de rollback
- `references/seguridad-del-pipeline.md` - secretos, permisos y checklist
