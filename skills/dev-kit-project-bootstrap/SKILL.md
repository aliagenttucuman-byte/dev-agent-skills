---
name: dev-kit-project-bootstrap
description: "Genera el scaffold de un proyecto nuevo: backend Python/FastAPI, frontend React/TypeScript, Docker, CI y estructura de tests lista para arrancar. CARGAR cuando arranca un proyecto desde cero o hay que crear la base de un repositorio nuevo."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [bootstrap, scaffold, project-setup, template, tooling]
    category: software-development
    related_skills: [dev-kit-sdd-workflow, dev-kit-task-breakdown, dev-kit-documentation, dev-kit-ci-cd, dev-kit-backend-stack]
---

# Dev Kit - Project Bootstrap

> **Trigger:** "arrancar un proyecto nuevo", "crear la estructura base",
> "generar el scaffold", "un repo vacio, por donde empiezo". Cargar esta skill
> ANTES de crear la primera carpeta del proyecto.

## Que es esto

El procedimiento para levantar la base de un proyecto en minutos, con la
estructura, los comandos y los gates ya puestos, para que el trabajo real
arranque en la primera tarea.

No es un generador de codigo de negocio. El scaffold produce **laanda
infraestructura, no la aplicacion**.

La regla que lo gobierna:

> **El scaffold no decide nada del producto.** Todo lo que el scaffold genera
> se puede reemplazar en un commit. Lo unico que no se puede reemplazar sin
> costo es la estructura de carpetas y la disciplina de los comandos.

## Que genera el scaffold

| Bloque | Contenido | Por que |
|---|---|---|
| **Raiz** | `README.md`, `Makefile`, `.gitignore`, `.env.example`, `CONSTITUTION.md` | los puntos de entrada del proyecto |
| **Backend** | `backend/` con FastAPI por capas, config, health check, tests | el servidor y su dominio |
| **Frontend** | `frontend/` con React + TypeScript + Vite, router, cliente HTTP | la aplicacion web |
| **Datos** | migraciones Alembic y modelo base | el esquema versionado |
| **Infra** | `Dockerfile` por servicio y `docker-compose.yml` | el entorno local reproducible |
| **CI** | workflow de GitHub Actions con lint, tipos y tests | los gates desde el primer commit |
| **Docs** | `docs/adr/` con el indice y `docs/` | el lugar de las decisiones |

## 1. Requisitos antes de arrancar

El scaffold se ejecuta **despues** de la constitution, no antes. Sin estas
decisiones, el scaffold genera un proyecto que hay que rehacer.

| Requisito | Artefacto | Sin el, el scaffold genera |
|---|---|---|
| Stack definido | `CONSTITUTION.md` | el stack por defecto, que puede no ser el del cliente |
| Alcance inicial | una frase del problema | un esqueleto vacio sin criterio |
| Nombre del proyecto | un nombre en kebab-case | `mi-proyecto` |

**Regla:** si el proyecto ya tiene codigo, **no** se usa el scaffold. Se usa la
habilidad de documentacion y de breakdown. El scaffold es para terreno vacio.

## 2. Como se usa el script

El generador es un script ejecutable, sin dependencias externas: solo la
biblioteca estandar de Python.

```bash
# genera el proyecto en ./mi-proyecto
python3 scripts/scaffold.py --name mi-proyecto

# genera en otra ruta, con los modulos opcionales
python3 scripts/scaffold.py --name mi-proyecto --out ./workspace --with frontend --with ci

# sin frontend (proyecto solo de API)
python3 scripts/scaffold.py --name mi-proyecto --without frontend

# lista lo que se generaria, sin escribir nada
python3 scripts/scaffold.py --name mi-proyecto --dry-run

# ayuda
python3 scripts/scaffold.py --help
```

### Opciones

| Opcion | Default | Que hace |
|---|---|---|
| `--name` | obligatorio | nombre del proyecto en kebab-case |
| `--out` | `.` | directorio donde se crea la carpeta del proyecto |
| `--with` | todos | modulos a incluir, repetible: `backend`, `frontend`, `docker`, `ci`, `docs`, `data` |
| `--without` | ninguno | modulos a excluir |
| `--dry-run` | apagado | imprime el arbol sin escribir archivos |
| `--force` | apagado | sobrescribe archivos existentes del mismo nombre |
| `--quiet` | apagado | imprime solo el resumen |

**Regla:** el script nunca sobreescribe sin `--force`, y con `--force` avisa
que archivos reemplazo. Un scaffold que pisa trabajo previo es un incidente.

### Que produce

```text
mi-proyecto/
├── README.md
├── Makefile
├── CONSTITUTION.md
├── .gitignore
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── migrations/
│   │   ├── env.py
│   │   └── versions/
│   ├── src/app/
│   │   ├── main.py
│   │   ├── api/{router.py,dependencies.py,handlers.py,schemas/,routes/}
│   │   ├── services/
│   │   ├── domain/{entities/,rules/,ports/}
│   │   ├── infra/db/{session.py,base.py,models.py,repositories/}
│   │   └── core/{config.py,logging.py,errors.py}
│   └── tests/{unit/,integration/,contract/}
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── src/{main.tsx,App.tsx,api/client.ts,components/,pages/}
├── data/
│   └── seed.sql
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── docs/
│   ├── adr/README.md
│   └── adr/0001-plantilla.md
└── .github/workflows/ci.yml
```

### Los comandos que deja puestos

El `Makefile` generado es la interfaz del proyecto. Se documenta en el README
y se usa igual en local y en CI.

```bash
make install     # instala dependencias de backend y frontend
make up          # levanta el entorno con Docker
make down        # lo baja
make test        # pruebas unitarias e integracion del backend
make lint        # lint y formato
make typecheck   # verificacion de tipos
make migrate     # aplica migraciones
make smoke       # verifica que el proyecto arranca
make ci          # lo que corre el pipeline, en el mismo orden
```

**Regla:** `make ci` y el workflow de CI ejecutan **exactamente** los mismos
comandos, en el mismo orden. Si divergen, el pipeline verde no significa nada.

### Verificacion del scaffold

```bash
# 1. generar
python3 scripts/scaffold.py --name demo --out /tmp/demo

# 2. el arbol tiene lo minimo
test -f /tmp/demo/backend/src/app/main.py
test -f /tmp/demo/frontend/src/main.tsx
test -f /tmp/demo/docker/docker-compose.yml
test -f /tmp/demo/.github/workflows/ci.yml

# 3. el python generado compila
python3 -m compileall -q /tmp/demo/backend/src

# 4. el script es idempotente en modo seco
python3 scripts/scaffold.py --name demo --dry-run
```

## 3. La estructura que genera el backend

El backend usa la regla de dependencia por capas, que es la que el resto del
kit da por buena.

```
api  ->  services  ->  domain  <-  infra
 |         |            ^           |
 +---------+------------+-----------+
              core
```

| Carpeta | Que contiene | NO puede importar |
|---|---|---|
| `api/` | rutas, schemas, dependencias, manejadores | `infra` directo |
| `services/` | casos de uso | `api` |
| `domain/` | entidades, reglas, puertos | framework ni ORM |
| `infra/` | ORM, repositorios, clientes externos | `api` |
| `core/` | config, logging, errores | capas de dominio |

**Regla:** el scaffold incluye un test de arquitectura que falla si alguien
importa el framework desde `domain/`. Es barato y atrapa la violacion antes
que el reviewer.

## 4. La estructura que genera el frontend

| Carpeta | Que contiene |
|---|---|
| `src/api/` | el cliente HTTP y los tipos de la respuesta |
| `src/components/` | componentes reutilizables, sin logica de negocio |
| `src/pages/` | una pagina por ruta |
| `src/hooks/` | hooks con estado de servidor |
| `src/types/` | tipos compartidos con el contrato |

**Regla:** el frontend no define tipos a mano si el contrato los define. El
cliente HTTP tipa las respuestas desde el esquema de la API.

## 5. Personalizacion

El scaffold es un **molde**, no un dogma. Los puntos de desvio documentados:

| Desvio | Como se hace | Que hay que actualizar |
|---|---|---|
| Otro stack de backend | editar `backend/pyproject.toml` y `src/app/main.py` | `README.md`, `Makefile` |
| Sin frontend | `--without frontend` | `Makefile`, `docker-compose.yml` |
| Sin Docker | `--without docker` | `README.md` |
| Otro pipeline | editar `.github/workflows/ci.yml` | `README.md` |
| Monorepo con mas paquetes | replicar el patron de `backend/` | `Makefile` |

**Regla:** cualquier desvio se escribe en `CONSTITUTION.md` y en el ADR
correspondiente. Un desvio no documentado vuelve a ser debate en tres meses.

## 6. Orden recomendado

```text
1. CONSTITUCION     que esta permitido y con que limites
2. BOOTSTRAP        la estructura base, con comandos y gates   <- esta skill
3. SMOKE            el proyecto arranca y responde
4. SPEC            el contrato de la API
5. PLAN            como se construye
6. TAREAS          quien hace cada parte
7. IMPLEMENTAR     construir contra el contrato
```

**Regla:** el bootstrap no reemplaza las fases 1, 4, 5 y 6. Genera la
estructura; el trabajo de verdad sigue el flujo completo.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Scaffold sin constitution | el stack se decide por defecto y despues se pelea | constitution primero |
| Scaffold sobre un proyecto con codigo | se pisa trabajo real | usar breakdown, no scaffold |
| Inventar el dominio en el scaffold | el scaffold no sabe de que trata el negocio | entidades vacias, el dominio se diseña aparte |
| Saltar el smoke test | el proyecto no arranca y nadie lo nota | `make smoke` en el primer commit |
| `make ci` distinto del pipeline | el CI verde no significa nada | los mismos comandos en el mismo orden |
| Secret en `.env.example` | el secreto se versiona | solo nombres de variable |
| Un solo `.env` sin ejemplo | nadie sabe que variables hay | `.env.example` con la lista completa |
| Contenedores con la base de datos en el repo | datos de prueba versionados | la base vive en un contenedor aparte |
| Migraciones sin `downgrade` | no se puede revertir | toda migracion es reversible |
| Sin test de arquitectura | la regla de dependencia se rompe en silencio | el test viene en el scaffold |
| Personalizar sin registrar el desvio | el desvio se debate de nuevo | ADR y constitution |

## Referencias

### Skills relacionadas

- `dev-kit-sdd-workflow` - el flujo completo donde el bootstrap es el paso 2.
- `dev-kit-task-breakdown` - las tareas que se ejecutan sobre el scaffold.
- `dev-kit-documentation` - el README y los ADRs que el scaffold inicializa.
- `dev-kit-backend-stack` - convenciones detalladas del backend generado.
- `dev-kit-ci-cd` - el pipeline que el scaffold deja configurado.

### Archivos de esta skill

| Archivo | Contenido |
|---|---|
| `scripts/scaffold.py` | generador ejecutable del proyecto, sin dependencias externas |
| `references/estructura-scaffold.md` | que genera cada bloque, por que y como adaptarlo |
