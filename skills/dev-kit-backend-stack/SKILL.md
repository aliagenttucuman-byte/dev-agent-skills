---
name: dev-kit-backend-stack
description: "Convenciones del backend en Python con FastAPI, SQLAlchemy y Pydantic. Estructura de proyecto por capas, convenciones de endpoints, manejo de errores, validacion, migraciones Alembic, configuracion por entorno e inyeccion de dependencias. CARGAR cuando hay que crear o revisar un servicio backend, definir endpoints o estructurar un proyecto de API."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [backend, fastapi, python, sqlalchemy, api]
    category: software-development
    related_skills: [dev-kit-code-quality, dev-kit-database, dev-kit-security, dev-kit-testing, dev-kit-observability]
---

# Dev Kit - Stack Backend

> **Trigger:** "crear un backend", "definir endpoints", "estructurar el proyecto
> Python", "como organizo las capas", "migraciones Alembic", "manejo de errores
> en la API". Cargar esta skill ANTES de escribir el primer endpoint.

## Que es esto

El contrato de como se construye el backend. No elige el stack: lo declara y
documenta como desviarse. El default es Python con FastAPI, SQLAlchemy 2 y
Pydantic 2.

Tres decisiones sostienen todo lo demas:

1. **Las capas no se cruzan.** La capa de presentacion no toca la base de datos.
2. **El dominio no depende del framework.** Las reglas de negocio se prueban sin
   levantar el servidor.
3. **La configuracion viene del entorno.** Ningun valor de despliegue esta en el
   codigo.

## Capas y su responsabilidad

| Capa | Carpeta | Responsabilidad | Puede importar de |
|---|---|---|---|
| Presentacion | `api/` | HTTP: parsear, responder, delegar | application, schemas |
| Aplicacion | `services/` | Casos de uso: orquestar dominio y I/O | domain, ports |
| Dominio | `domain/` | Reglas de negocio, entidades, invariantes | nada |
| Infraestructura | `infra/` | Base de datos, clientes externos, colas | domain, ports |
| Nucleo | `core/` | Config, logging, dependencias, errores base | nada |
| Tests | `tests/` | Pruebas por capa | lo que prueban |

La regla de dependencia apunta hacia adentro: `api -> services -> domain`. El
dominio no importa nada del framework. Si un archivo de `domain/` importa
`fastapi`, la arquitectura esta rota.

El arbol completo esta en `templates/project-layout.md`.

## Workflow

| Paso | Que hace | Artefacto | Gate |
|---|---|---|---|
| 1. Ubicar | Decide en que capa vive la funcionalidad nueva | capa asignada | La capa no depende hacia afuera |
| 2. Modelar | Define el contrato con Pydantic | schema de request y response | Sin `dict` sin tipar |
| 3. Implementar | Escribe el caso de uso en `services/` | funcion de servicio | Pruebla sin HTTP ni DB |
| 4. Persistir | Agrega el repositorio en `infra/` | repositorio | Queries en la capa de infra |
| 5. Exponer | Conecta el endpoint en `api/` | ruta | Respuesta tipada, errores tipados |
| 6. Verificar | Corre lint, tipos y pruebas | reporte | Los tres verdes |

### Paso 1 - Decidir la capa antes de escribir

El criterio de decision, en orden:

| Si la funcionalidad es... | Va en |
|---|---|
| Regla de negocio que vale independiente del HTTP | `domain/` |
| Caso de uso que coordina dominio y mas de un puerto | `services/` |
| Traduccion entre HTTP y el caso de uso | `api/` |
| Consulta o escritura a la base de datos | `infra/` |
| Configuracion, logging, metrica transversal | `core/` |

**Regla:** si dudas entre dos capas, es que falta un puerto (interfaz) en
`domain/ports/`. La duda se resuelve definiendo el contrato, no moviendo el
codigo.

### Paso 2 - Modelos Pydantic

Un schema por operacion. El schema de request y el de response son distintos
objetos, aunque compartan campos.

```python
# api/schemas/order.py
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    """Payload de creacion de un pedido."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    customer_id: str = Field(min_length=1, max_length=64)
    items: list[OrderItemCreate] = Field(min_length=1, max_length=100)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    notes: str | None = Field(default=None, max_length=500)


class OrderItemCreate(BaseModel):
    product_id: str = Field(min_length=1, max_length=64)
    quantity: int = Field(ge=1, le=999)
    unit_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class OrderRead(BaseModel):
    """Respuesta de lectura de un pedido."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    status: str
    total: Decimal
    created_at: datetime
```

| Regla | Motivo |
|---|---|
| `extra="forbid"` en requests | Un campo desconocido es un error del cliente, no se ignora |
| `from_attributes=True` en responses | Permite construir desde el modelo de ORM |
| Limites explicitos (`min_length`, `ge`, `max_length`) | La validacion ocurre en el borde, no en el dominio |
| Sin `dict[str, Any]` sin tipar | Un contrato sin tipos no es un contrato |
| El response nunca expone la entidad de ORM | La API es un contrato publico, no la base de datos |

### Paso 3 - Casos de uso en la capa de aplicacion

```python
# services/order_service.py
from domain.ports import OrderRepository
from domain.entities import Order


class OrderService:
    """Casos de uso sobre pedidos."""

    def __init__(self, orders: OrderRepository, clock: Clock) -> None:
        self._orders = orders
        self._clock = clock

    def create(self, command: OrderDraft) -> Order:
        """Crea un pedido validando las reglas de negocio del dominio."""
        if command.customer_id in self._orders.blocked_customers():
            raise CustomerBlocked(command.customer_id)
        order = Order.create(command, now=self._clock.now())
        self._orders.save(order)
        return order
```

El servicio no importa `fastapi` ni `sqlalchemy`. Se instancia en la capa de
infra y se inyecta en el endpoint.

### Paso 4 - Repositorios y puertos

El dominio define la interfaz, la infraestructura la implementa. La inversion de
dependencia permite probar el dominio sin base de datos.

```python
# domain/ports/order_repository.py
from typing import Protocol
from domain.entities import Order


class OrderRepository(Protocol):
    """Contrato de persistencia de pedidos."""

    def save(self, order: Order) -> None: ...
    def get(self, order_id: str) -> Order | None: ...
    def blocked_customers(self) -> set[str]: ...
```

```python
# infra/db/repositories/order_repository.py
from sqlalchemy.orm import Session
from infra.db.models import OrderModel


class SqlAlchemyOrderRepository:
    """Implementacion del puerto de pedidos sobre PostgreSQL."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, order: Order) -> None:
        self._session.add(OrderModel.from_entity(order))
        self._session.flush()

    def get(self, order_id: str) -> Order | None:
        model = self._session.get(OrderModel, order_id)
        return model.to_entity() if model else None
```

### Paso 5 - Endpoints

Convenciones que se aplican a toda ruta:

| Convencion | Regla |
|---|---|
| Verbo y recurso | `POST /orders`, `GET /orders/{order_id}`, no `POST /createOrder` |
| Prefijo de version | `/api/v1` en el router, no en cada ruta |
| Respuesta | Modelo Pydantic de response, nunca el modelo de ORM |
| Codigo de exito | 200 para lectura, 201 con `Location` para creacion, 204 para borrado |
| Errores | Formato de error estandar, generado por el manejador global |
| Idempotencia | `Idempotency-Key` en operaciones de creacion con efecto externo |
| Paginacion | `limit` y `cursor` con limite maximo duro |

```python
# api/routes/orders.py
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    """Crea un pedido."""
    order = service.create(OrderDraft.from_schema(payload))
    return OrderRead.model_validate(order)
```

El endpoint es delgado: traduce, no decide. Si aparece una regla de negocio en
un endpoint, esa regla va al servicio.

### Paso 6 - Manejo de errores

Tres categorias, tres respuestas. El cliente distingue un error de validacion de
un error de servidor por el codigo y por el tipo del campo `error`.

| Categoria | Codigo | Donde se detecta | Formato |
|---|---|---|---|
| Validacion | 422 | Pydantic, automatico | lista de campos con problema |
| Dominio | 400 - 409 | excepcion de dominio | tipo de error y mensaje |
| Inesperado | 500 | cualquier otra excepcion | mensaje generico, detalle en el log |

```python
# core/errors.py
class DomainError(Exception):
    """Error de negocio con codigo estable para el cliente."""

    status_code = 400
    error_type = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class CustomerBlocked(DomainError):
    status_code = 403
    error_type = "customer_blocked"
```

```python
# api/handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse


@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"type": exc.error_type, "message": exc.message}},
    )
```

**Regla critica:** el 500 nunca expone el detalle interno. La traza va al log
(con correlation ID), no al cuerpo de la respuesta.

### Paso 7 - Configuracion por entorno

```python
# core/config.py
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion leida del entorno, validada al arrancar."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    environment: str = Field(default="development")
    database_url: str
    log_level: str = Field(default="INFO")
    cors_origins: list[str] = Field(default_factory=list)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

| Regla | Motivo |
|---|---|
| Todo valor de despliegue viene del entorno | El mismo artefacto sirve para todos los ambientes |
| Sin default para secretos | Un default inseguro es un default que se usa |
| Validar al arrancar, no en la primera peticion | Falla rapido y visible |
| `lru_cache` en el getter | Se lee una vez |
| `.env` solo en local, nunca versionado | Ver `dev-kit-security` |

### Paso 8 - Inyeccion de dependencias

```python
# api/dependencies.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from core.config import Settings, get_settings
from infra.db.session import get_session
from services.order_service import OrderService
from infra.db.repositories.order_repository import SqlAlchemyOrderRepository


def get_order_service(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> OrderService:
    repository = SqlAlchemyOrderRepository(session)
    return OrderService(repository, clock=SystemClock(settings))
```

| Regla | Motivo |
|---|---|
| `Depends` en el borde, nunca en el dominio | El dominio no conoce el contenedor |
| Dependencias tipadas con `Annotated` | El tipo es la documentacion |
| Una dependencia, una responsabilidad | Un `get_everything` no se puede probar |
| Dependencias lentas con cache | `get_current_user` no se recalcula por request si no cambia |
| Sobrescritura en tests | `app.dependency_overrides[...]` permite tests sin infra |

### Paso 9 - Migraciones Alembic

```bash
alembic init -t generic migrations       # una vez
alembic revision -m "add order status index"
alembic upgrade head
alembic downgrade -1
alembic current
alembic history --verbose
```

| Regla | Motivo |
|---|---|
| Una migracion, un cambio | Dos cambios en una migracion no se pueden revertir por separado |
| Nunca editar una migracion ya aplicada | El historial debe ser inmutable |
| `downgrade` obligatorio | Una migracion sin vuelta atras es irreversible por accidente |
| Migraciones en el pipeline de despliegue | El esquema se actualiza antes que el codigo |
| `op.create_index` explicito | Los indices no se crean solos con la columna |

Detalle operativo en `references/migrations-alembic.md`.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Logica de negocio en el endpoint | La regla no se puede probar sin HTTP | Mover al servicio |
| Importar `fastapi` en `domain/` | El dominio queda atado al framework | Definir puertos en `domain/ports/` |
| Devolver el modelo de ORM | La API queda atada al esquema de la base | Schema de response |
| `except Exception: pass` | Se tragan errores reales | Dejar subir o loguear con contexto |
| Detalle de la traza en el 500 | Filtra rutas, versiones y datos | Log interno, respuesta generica |
| `Base.metadata.create_all()` en produccion | Pierde migraciones y el control de cambios | Solo Alembic |
| Configuracion con default en secretos | El default inseguro se usa por inercia | Sin default, falla al arrancar |
| Transaccion abierta durante `await` | La conexion se mantiene bloqueada | Transaccion corta, sin I/O de red dentro |
| Un repositorio gigante con 30 metodos | Se testea todo junto | Un repositorio por agregado |
| `dict` como contrato entre capas | Nada verifica la forma del dato | Modelo tipado en el borde |

## Referencias

- `templates/project-layout.md` - arbol de proyecto completo, con la regla de
  dependencia por capa y donde vive cada cosa
- `references/migrations-alembic.md` - flujo de migraciones, casos que rompen en
  produccion y como hacer migraciones que no bloquean
- `references/api-conventions.md` - convenciones de endpoints, codigos de estado,
  paginacion por cursor e idempotencia

### Archivos de esta skill

- `templates/project-layout.md` - estructura de proyecto backend por capas
- `references/migrations-alembic.md` - guia operativa de migraciones
- `references/api-conventions.md` - convenciones de API y errores
