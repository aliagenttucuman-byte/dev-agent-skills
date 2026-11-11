# Estructura del scaffold

> Referencia de `dev-kit-project-bootstrap`. Que genera `scripts/scaffold.py` y
> por que esta armado asi.

## Que genera

```
<nombre>/
├── app/                          # backend
│   ├── main.py                   # factory de la app y lifespan
│   ├── core/
│   │   ├── config.py             # configuracion por entorno (pydantic-settings)
│   │   └── logging.py            # logging estructurado JSON
│   ├── api/
│   │   ├── router.py             # router raiz
│   │   └── v1/
│   │       └── health.py         # health check
│   ├── domain/                   # logica de negocio (vacia, se llena en el proyecto)
│   └── infrastructure/           # adaptadores externos (vacia, se llena en el proyecto)
├── tests/
│   ├── conftest.py               # fixture del cliente de test
│   └── test_health.py            # test de ejemplo que pasa
├── frontend/                     # React + TypeScript + Vite
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts            # proxy /api hacia el backend
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       └── App.tsx
├── .github/workflows/ci.yml      # pipeline de calidad
├── .gitignore
├── .env.example                  # variables de entorno con valores de ejemplo
├── Dockerfile
├── docker-compose.yml            # api + postgres
├── mypy.ini
├── pyproject.toml                # dependencias + config de ruff
├── ruff.toml
└── README.md
```

## Por que esta estructura

### `core` separado de `api`

`core` tiene lo que no depende de la capa HTTP: configuracion, logging,
excepciones. `api` tiene lo que traduce HTTP a dominio.

**Beneficio:** los tests de dominio no necesitan el framework HTTP, y la
configuracion no se importa desde un router.

### `domain` e `infrastructure` vacios

El scaffold no inventa arquitectura de dominio. Deja las carpetas para que el
proyecto las llene segun su complejidad.

**Por que:** un proyecto simple no necesita capas; uno complejo las necesita
desde el inicio. El scaffold no sabe cual es el caso, asi que no decide.

**Nota:** `domain` e `infrastructure` se pueden borrar si el proyecto no las
usa. Borrarlas es una decision valida.

### `api/v1/`

El versionado en la URL desde el arranque. Cuando aparezca la v2, la v1 sigue
funcionando.

**Nota:** si el proyecto no va a tener v2, `v1` es ruido y se puede quitar.
Cambiarlo despues es mas caro que no ponerlo.

### La carpeta `tests` al mismo nivel que `app`

Es el layout `src`-less: `app` es el paquete importable, `tests` esta al lado.
El `pyproject.toml` declara `packages = ["app"]`.

**Por que:** evita el `src/` cuando no hay nada mas que empaquetar. Para
librerias publicas, `src/` si es lo correcto.

### Health check en `api/v1/health.py`

Un endpoint `/health` desde el arranque. Es lo primero que necesita un
orquestador de despliegue, y sin el, cada despliegue lo agrega a mano.

**Regla:** `/health` no verifica dependencias. Solo responde que el proceso
esta vivo. Un health check que consulta la base de datos y falla cuando la
base esta lenta reinicia el servicio en cascada.

**Regla:** para verificar dependencias, un endpoint separado (`/ready`).

### Vite con proxy a `/api`

El frontend llama a `/api/...` en desarrollo y el proxy lo reenvia al
backend. En produccion, el mismo path lo sirve el reverse proxy.

**Beneficio:** la URL de la API es la misma en desarrollo y en produccion.
Sin proxy, el frontend usaria una URL distinta en cada entorno y habria que
recompilar.

## Configuracion por entorno

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    environment: str = "development"
    database_url: str = "..."
```

**Reglas:**
- Toda variable de entorno tiene default seguro o no tiene default (y es
  obligatoria en produccion).
- `.env` esta en `.gitignore`. `.env.example` esta versionado.
- Los secretos (claves de API) no tienen default en el codigo.

**Por que `.env.example` versionado:** quien clona el repo sabe que variables
existen sin ver los valores de nadie.

## El pipeline de calidad

El `ci.yml` generado corre, en orden:

1. `ruff check` - lint
2. `ruff format --check` - formato
3. `mypy app` - tipos
4. `pytest` - tests con cobertura
5. `docker build` - imagen

**Regla:** el build de la imagen va despues de los tests, y en un job
separado que `needs` al de calidad. Si los tests fallan, no se construye la
imagen.

**Regla:** el `cache: pip` esta configurado. Sin el, cada ejecucion reinstala
todo y el pipeline tarda minutos sin agregar valor.

## Lo que el scaffold NO hace

| No hace | Por que |
|---|---|
| Instalar dependencias | El proyecto puede usar otro gestor |
| Crear el repositorio git | Cada equipo tiene su flujo |
| Configurar migraciones | El motor de migraciones depende de la decision del proyecto |
| Configurar despliegue | Depende de la infraestructura destino |
| Escribir el `.pre-commit-config.yaml` | Es una preferencia del equipo, no un default |

Estos se agregan como pasos siguientes, no como parte del scaffold.

## Uso

```bash
# Generar el proyecto
python3 scripts/scaffold.py --name mi-proyecto --out .

# Ver que se crearia, sin escribir
python3 scripts/scaffold.py --name mi-proyecto --out . --dry-run

# Solo backend, sin frontend
python3 scripts/scaffold.py --name mi-proyecto --out . --stack python-only

# Sobrescribir archivos existentes
python3 scripts/scaffold.py --name mi-proyecto --out . --force
```

**Regla:** `--force` no es la opcion normal. Si el proyecto ya existe, el
scaffold no debe pisar trabajo. El error tipico es re-ejecutar el bootstrap
sobre un proyecto con codigo y perder cambios.

## Verificacion despues de generar

```bash
cd mi-proyecto
pip install -e ".[dev]"
ruff check . && mypy app && pytest
```

Los tres tienen que pasar antes de escribir la primera feature. Un scaffold
que no pasa su propio pipeline no sirve de punto de partida.

## Referencias

- `dev-kit-project-bootstrap/scripts/scaffold.py` - el generador
- `dev-kit-backend-stack` - convenciones del backend una vez generado
- `dev-kit-ci-cd` - como evolucionar el pipeline generado
