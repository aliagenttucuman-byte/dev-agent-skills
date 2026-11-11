# Estructura de proyecto backend por capas

Arbol de referencia para un backend Python con FastAPI. Es un molde, no un
imperativo: se adapta al proyecto, pero se conserva la regla de dependencia.

---

## 1. Arbol completo

```
backend/
├── pyproject.toml                 # deps, ruff, mypy, pytest
├── alembic.ini                    # configuracion de migraciones
├── Dockerfile
├── docker-compose.yml             # postgres + api para local
├── .env.example                   # plantilla de variables (sin secretos)
├── migrations/
│   ├── env.py                     # puente entre alembic y los modelos
│   ├── script.py.mako
│   └── versions/
│       ├── 0001_initial_schema.py
│       └── 0002_add_order_status_index.py
├── src/
│   └── app/
│       ├── main.py                # punto de entrada de la aplicacion
│       ├── api/
│       │   ├── router.py          # incluye los routers por version
│       │   ├── dependencies.py    # proveedores de dependencias
│       │   ├── handlers.py        # manejadores globales de error
│       │   ├── schemas/           # modelos Pydantic de request y response
│       │   │   ├── order.py
│       │   │   └── customer.py
│       │   └── routes/            # un archivo por recurso
│       │       ├── orders.py
│       │       └── customers.py
│       ├── services/              # casos de uso
│       │   ├── order_service.py
│       │   └── customer_service.py
│       ├── domain/
│       │   ├── entities/          # entidades con invariantes
│       │   │   └── order.py
│       │   ├── value_objects/     # value objects
│       │   ├── rules/             # reglas de negocio puras
│       │   └── ports/             # interfaces (Protocol) hacia afuera
│       │       ├── order_repository.py
│       │       └── clock.py
│       ├── infra/
│       │   ├── db/
│       │   │   ├── session.py     # engine, sessionmaker, get_session
│       │   │   ├── base.py        # declarative Base
│       │   │   ├── models.py      # modelos de ORM
│       │   │   └── repositories/  # implementaciones de los puertos
│       │   ├── clients/           # clientes de sistemas externos
│       │   └── messaging/         # publicacion y consumo de eventos
│       ├── core/
│       │   ├── config.py          # Settings con pydantic-settings
│       │   ├── logging.py         # logging estructurado
│       │   ├── errors.py          # jerarquia de errores de dominio
│       │   ├── metrics.py         # instrumentacion de metricas
│       │   └── pagination.py      # helpers de paginacion por cursor
│       └── worker/                # procesos en segundo plano, si aplica
├── tests/
│   ├── unit/                      # dominio y servicios, sin infra
│   ├── integration/               # con base de datos real o contenedor
│   ├── contract/                  # contrato de la API
│   └── e2e/                       # flujo completo
├── scripts/
└── docs/
    ├── adr/                       # decisiones de arquitectura
    └── openapi.json               # generado, no editado a mano
```

---

## 2. Regla de dependencia

```
api  ->  services  ->  domain  <-  infra
 |         |            ^           |
 +---------+------------+-----------+
              core
```

| Capa | Puede importar | NO puede importar |
|---|---|---|
| `domain/` | nada del proyecto | `fastapi`, `sqlalchemy`, `pydantic` |
| `services/` | `domain` | `api`, `infra` (solo puertos) |
| `api/` | `services`, `domain` (schemas de lectura) | `infra` directo (usa dependencias) |
| `infra/` | `domain` (puertos) | `api` |
| `core/` | librerias externas | capas de dominio |

**Como verificar la regla sin depender de la disciplina:**

```python
# test de arquitectura: falla si alguien importa sqlalchemy desde domain
import ast
from pathlib import Path

FORBIDDEN = {"fastapi", "sqlalchemy", "pydantic", "starlette"}


def test_domain_no_importa_framework():
    for path in Path("src/app/domain").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").split(".")[0]]
            else:
                continue
            assert not (set(names) & FORBIDDEN), f"{path} importa {names}"
```

Este test es barato y detecta la violacion antes que el reviewer.

---

## 3. Que vive en cada carpeta

### `domain/entities/`

Entidades con identidad e invariantes. Sin ORM, sin Pydantic.

```python
# src/app/domain/entities/order.py
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from domain.value_objects.money import Money


class Order:
    """Entidad de pedido con sus invariantes de negocio."""

    def __init__(self, customer_id: str, total: Money, status: str, created_at: datetime) -> None:
        self.id = uuid4()
        self.customer_id = customer_id
        self.total = total
        self.status = status
        self.created_at = created_at

    def confirm(self) -> None:
        """Pasa el pedido a confirmado. Lanza si el estado no lo permite."""
        if self.status != "pending":
            raise InvalidStatusTransition(self.status, "confirmed")
        self.status = "confirmed"
```

### `domain/ports/`

Interfaces hacia afuera. `Protocol` de Python alcanza: no hace falta una clase
abstracta.

```python
# src/app/domain/ports/clock.py
from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Fuente de tiempo, inyectable para poder probar sin esperar."""

    def now(self) -> datetime: ...
```

### `services/`

Un archivo por caso de uso agregado. Coordina, no decide las reglas (esas estan
en el dominio).

### `infra/db/models.py`

Los modelos de ORM **no** son las entidades. Son la representacion persistente.

```python
# src/app/infra/db/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(index=True)
    total_amount: Mapped[int] = mapped_column()   # centavos, nunca float
    status: Mapped[str] = mapped_column(index=True)
```

Reglas para los modelos de ORM:

| Regla | Motivo |
|---|---|
| `Mapped[]` con tipo explicito | Sin esto, SQLAlchemy infiere y el tipo se pierde |
| Dinero en enteros o `Decimal` | `float` para dinero pierde precision |
| `to_entity()` y `from_entity()` | Traducen entre persistencia y dominio |
| El `id` es `str` (UUID) en la API | Evita exponer el autoincremento |
| Indices declarados en el modelo | El esquema y los indices no pueden divergir |

### `core/`

Configuracion, logging, metricas, errores base, paginacion. Es la unica carpeta
que se importa desde varias capas.

---

## 4. Nombres de archivo

| Tipo | Convencion | Ejemplo |
|---|---|---|
| Modulo | `snake_case` | `order_service.py` |
| Clase | `PascalCase` | `OrderService` |
| Funcion o metodo | `snake_case` | `create_order` |
| Constante | `SCREAMING_SNAKE_CASE` | `MAX_ITEMS_PER_ORDER` |
| Test | `test_<unidad>.py` | `test_order_service.py` |
| Test de clase | `test_<clase>.py` | `test_order.py` |

---

## 5. Donde NO va cada cosa

| Error comun | Donde va realmente |
|---|---|
| Modelo de ORM devuelto desde el endpoint | Schema de response en `api/schemas/` |
| `datetime.now()` dentro de la logica | `Clock` inyectado, implementado en `infra/` |
| Consulta SQL dentro del servicio | Metodo del repositorio en `infra/db/repositories/` |
| `os.environ` leido dentro de una funcion | `core/config.py` |
| `try/except` generico en el endpoint | Manejador global en `api/handlers.py` |
| Regla de negocio en el schema de Pydantic | Metodo de la entidad en `domain/` |
| Constante de configuracion en un modulo cualquiera | `core/config.py` |

---

## 6. Estructura minima viable

Un proyecto chico no necesita las 20 carpetas. Estas 6 alcanzan:

```
src/app/
├── api/          # router, dependencies, schemas, routes, handlers
├── services/     # casos de uso
├── domain/       # entities, ports
├── infra/db/     # session, models, repositories
├── core/         # config, logging, errors
└── main.py
```

Lo que **no** se negocia: la direccion de la dependencia y la separacion entre
entidad de dominio y modelo de ORM.

---

## 7. Referencia rapida de comandos

```bash
# arrancar en local
uvicorn app.main:app --reload

# lint y formateo
ruff check . --fix && ruff format .

# tipos
mypy src/app

# pruebas
pytest -q
pytest -q -m unit

# migraciones
alembic revision -m "descripcion corta"
alembic upgrade head
alembic downgrade -1

# documentacion de la API en vivo
uvicorn app.main:app --reload   # luego /docs
```

Todos esos comandos usan el paquete instalado en modo editable (`pip install -e .`),
con `src` como raiz de paquetes. El comando exacto de arranque puede variar
segun como se empaquete la aplicacion; lo que no cambia es que el modulo de
entrada sea `app.main:app`.
