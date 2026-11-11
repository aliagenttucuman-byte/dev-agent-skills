# Patrones de tipado en Python

Los patrones que resuelven la mayoria de los errores de tipos en un proyecto
real. Cada uno responde a un problema concreto.

---

## 1. `Protocol` en vez de herencia

**Problema:** la logica de negocio depende de un repositorio concreto y queda
imposible de testear sin base de datos.

```python
# domain/ports/user_repository.py
from typing import Protocol
from uuid import UUID


class UserRepository(Protocol):
    """Contrato de persistencia de usuarios. No lo implementa nadie en el dominio."""

    async def get_by_id(self, user_id: UUID) -> "User | None": ...

    async def save(self, user: "User") -> None: ...

    async def list_active(self, limit: int = 50) -> list["User"]: ...
```

La implementacion real vive en `infra/` y hereda de `Protocol` solo si quiere
documentar la dependencia; no hace falta.

```python
# infra/repositories/sqlalchemy_user_repository.py
class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        ...
```

**Por que:** el dominio depende de la interfaz, no de la infraestructura. La
regla de dependencia de `dev-kit-backend-stack` se cumple de verdad.

---

## 2. Genéricos con `TypeVar` y `ParamSpec`

**Problema:** un helper que devuelve "lo mismo que le pasaron" pierde el tipo al
cruzar la frontera.

```python
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def con_reintentos(
    operacion: Callable[P, R],
    intentos: int = 3,
) -> Callable[P, R]:
    """Ejecuta la operacion reintentando ante excepcion transitoria."""

    def envoltura(*args: P.args, **kwargs: P.kwargs) -> R:
        ultimo_error: Exception | None = None
        for _ in range(intentos):
            try:
                return operacion(*args, **kwargs)
            except TimeoutError as exc:
                ultimo_error = exc
        assert ultimo_error is not None
        raise ultimo_error

    return envoltura
```

`ParamSpec` conserva los argumentos, `TypeVar` conserva el retorno. Sin esto,
el helper devuelve `Any` y se pierde todo el tracking en la capa de arriba.

---

## 3. `TypedDict` para payloads que cruzan el borde

**Problema:** un dict que viene de un JSON externo no se valida en runtime y
se descubre el error tarde.

```python
from typing import TypedDict


class PayloadEvento(TypedDict):
    event_id: str
    tipo: str
    payload: dict[str, object]


def procesar(datos: PayloadEvento) -> None:
    ...
```

`TypedDict` documenta la forma sin validar en runtime. Cuando el payload viene
de la red, se valida con Pydantic en el borde y recien ahi se convierte al
`TypedDict` interno.

---

## 4. `Literal` para valores cerrados

**Problema:** un `str` para el estado de un pedido deja pasar cualquier valor.

```python
from typing import Literal

EstadoPedido = Literal["pendiente", "pagado", "enviado", "cancelado"]
```

Se combina bien con `Enum` cuando se necesita comportamiento (metodos,
serializacion). `Literal` cuando solo se necesita restringir el dominio.

---

## 5. `NewType` para no mezclar identificadores

**Problema:** pasar un `int` de usuario donde se espera un `int` de pedido compila
sin error y rompe en produccion.

```python
from typing import NewType

UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)


def crear_pedido(usuario: UserId, total: int) -> OrderId:
    ...
```

El costo es una llamada extra al construir. El beneficio: el error aparece en
la llamada, no en la linea 400.

---

## 6. `overload` para APIs con variantes de retorno

**Problema:** una funcion que devuelve `str` o `None` segun la entrada, y el
llamador tiene que adivinar.

```python
from typing import Literal, overload


@overload
def leer_config(ruta: str, *, con_default: Literal[True]) -> str: ...
@overload
def leer_config(ruta: str, *, con_default: Literal[False]) -> str | None: ...
def leer_config(ruta: str, *, con_default: bool = False) -> str | None:
    ...
```

El cuerpo real no se tipa con `overload` (se descarta en runtime).

---

## 7. Narrowing por `isinstance` y `match`

```python
def procesar(evento: Evento) -> str:
    match evento:
        case Creado(id=identificador):
            return f"creado:{identificador}"
        case Actualizado(campo="estado"):
            return "actualizado:estado"
        case _:
            return "desconocido"
```

El narrowing por `isinstance` funciona con `assert` para que el tipo se estreche:

```python
from typing import cast

if not isinstance(valor, str):
    raise TypeError(f"se esperaba str, se recibio {type(valor).__name__}")

# a partir de aca, valor es str
```

`cast` es la alternativa cuando el chequeo ya ocurrio antes y mypy no lo sabe.
Es una afirmacion al verificador de tipos: usarla sin evidencia es una
mentira silenciosa.

---

## 8. `TYPE_CHECKING` para imports de tipos

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class RepositorioOrden:
    def __init__(self, session: "AsyncSession") -> None:
        self._session = session
```

El import real solo se resuelve al analizar, no al ejecutar. Evita arrastrar
dependencias pesadas en el arranque y evita ciclos de import.

---

## 9. `@dataclass(frozen=True)` para entidades

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class LineaPedido:
    producto_id: str
    cantidad: int
    precio_unitario: Decimal

    @property
    def subtotal(self) -> Decimal:
        return self.precio_unitario * self.cantidad
```

`frozen=True` hace la entidad inmutable (hashable si todos los campos lo son),
`slots=True` reduce memoria y hace fallar temprano ante atributos dinamicos.

---

## 10. `Never` para funciones que no retornan

```python
from typing import Never


def fallar(mensaje: str) -> Never:
    raise RuntimeError(mensaje)


def procesar(valor: int) -> str:
    if valor < 0:
        fallar("valor negativo")
    return str(valor)
```

`Never` le dice a mypy que despues del `if` el `valor` es `int` y no
`int | None`. Sin esto, el `return str(valor)` de abajo se marca como
alcanzable con `None`.

---

## Chequeo rapido de donde fallan los tipos

| Sintoma | Causa probable | Patron a aplicar |
|---|---|---|
| Todo es `Any` | Falta `strict = true` | Seccion 4 de esta skill |
| "Argument has incompatible type" con dict | Falta `TypedDict` | Seccion 3 |
| "Returning Any" | Funcion sin anotacion | Anotar explicito |
| "Unused type: ignore" | El error ya no existe | Borrar el ignore |
| "Unreachable" | Rama muerta | Revisar la logica, no silenciar |
| Import cycle | Import de runtime entre modulos | `TYPE_CHECKING` |
