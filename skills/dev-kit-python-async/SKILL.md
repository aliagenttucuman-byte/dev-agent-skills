---
name: dev-kit-python-async
description: "Programacion asincrona profesional en Python: asyncio, TaskGroup, cancelacion, timeouts, concurrencia controlada, evitar bloqueos en el event loop, comunicacion entre tareas, pruebas con pytest-asyncio y conexion con pools de hilos y procesos. CARGAR cuando hay que implementar o revisar codigo async, resolver timeouts, cancelar tareas, limitar concurrencia, evitar que una funcion bloqueante Rompa el event loop o testear codigo asincrono."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [python, async, asyncio, concurrencia, timeouts, pytest-asyncio]
    category: software-development
    related_skills: [dev-kit-backend-stack, dev-kit-python-tooling, dev-kit-testing, dev-kit-observability]
---

# Dev Kit - Python Async

> **Trigger:** "implementar async", "await", "asyncio", "TaskGroup", "timeout",
> "cancelar tarea", "concurrencia", "el event loop se bloquea", "testear async".
> Cargar esta skill ANTES de escribir la primera corrutina.

## Que es esto

El contrato de como se escribe codigo asincrono que no se cuelga, no pierde
tareas y no bloquea a los demas. Async no es "codigo mas rapido": es codigo
que puede atender muchas operaciones simultaneas sin Threads.

La premisa central: **async es cooperativo**. El event loop solo avanza cuando
alguien hace `await`. Un `await` sobre una operacion que devuelve rapido no
cede el control, y un `time.sleep()` lo congela por completo. Casi todos los
bugs de async son variaciones de esta regla.

## Las cuatro reglas

1. **Nunca bloquear el event loop.** Cada operacion de I/O se hace `await`.
2. **Toda corrutina tiene un timeout.** Una llamada a un servicio externo sin
   timeout es una bomba de reloj.
3. **Toda tarea creada tiene un propietario.** Si nadie la espera ni la cancela, se
   pierde en el GC o queda colgada para siempre.
4. **Los errores se capturan en el borde.** Una exception en una tarea sin
   manejar se pierde silenciosamente.

## Workflow

| Paso | Que hace | Artefacto | Gate |
|---|---|---|---|
| 1. Decidir sync o async | Elegir el modelo antes de escribir | decision registrada | El criterio esta aplicado |
| 2. Estructura | Anadir `async`/`await` donde corresponde | corrutina | Cero llamadas bloqueantes |
| 3. Timeout | Poner timeout en toda I/O externa | timeout explicito | Ninguna llamada externa sin timeout |
| 4. Cancelacion | Definir quien cancela a quien | propagacion correcta | Cancelar no deja tareas huerfanas |
| 5. Concurrencia | Limitar la concurrencia | semaforo o gather acotado | No se lanza un numero ilimitado |
| 6. Errores | Manejar en el borde | exception logueada | Ninguna exception se pierde |
| 7. Probar | Tests async deterministas | suite async | Tests pasan y no cuelgan |

### Paso 1 - Decidir sync o async

| Situacion | Modelo | Razon |
|---|---|---|
| I/O de red con muchas operaciones simultaneas | async | Libera el hilo mientras espera |
| I/O de disco pequeno | sync | El overhead de async no se paga |
| CPU-bound (calculo puro, compresion, cifrado) | sync en pool | async no acelera CPU |
| Codigo existente sync que no va a crecer | sync | Migrar es costo sin retorno |

**Regla:** no se convierte a async "porque es moderno". El retorno aparece
cuando hay concurrencia real: cientos de llamadas a servicios externos.

Si el numero de operaciones concurrentes es menor a ~10, sync con un pool de
hilos es mas simple y tan rapido.

### Paso 2 - Estructura: donde va el `async`

```python
import asyncio
from typing import Awaitable, Callable


async def obtener_pedidos(pedido_id: str) -> dict[str, object]:
    async with cliente.get(f"/pedidos/{pedido_id}") as respuesta:
        respuesta.raise_for_status()
        return respuesta.json()


async def obtener_varios(ids: list[str]) -> list[dict[str, object]]:
    return await asyncio.gather(*(obtener_pedidos(id) para id in ids))
```

**Reglas:**

- `async def` solo si la funcion **efectivamente** hace `await`. Una funcion
  `async` sin `await` es un bug de rendimiento: el caller paga el costo de
  Scheduling sin obtener concurrencia.
- `await` solo sobre `Awaitable`. Un `await` sobre un valor plano es un error
  de tipos.
- Las funciones que "quiza" son awaitables usan `Awaitable[T]` en la firma, no
  `Coroutine`.

```python
# MAL: la funcion es async pero no hace await
async def obtener_config() -> dict:
    return {"timeout": 30}          # sin await: no hay concurrencia

# BIEN: el caller decide si espera
def obtener_config() -> dict:
    return {"timeout": 30}
```

### Paso 3 - Timeout en toda I/O externa

Este es el paso que mas se saltea y el que mas caro sale.

```python
import asyncio
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")

TIMEOUT_Llamada = 10.0
TIMEOUT_CONSULTA = 30.0


async def con_timeout(operacion: Awaitable[T], segundos: float) -> T:
    """Ejecuta la operacion con timeout. Cancela la operacion al expirar."""
    return await asyncio.timeout(segundos)(operacion)
```

En Python 3.11+ la forma moderna es `asyncio.timeout`:

```python
async def consultar(servicio: str) -> bytes:
    async with asyncio.timeout(TIMEOUT_CONSULTA):
        return await cliente.get(servicio)
```

En 3.10 o anterior, `asyncio.wait_for`.

**Reglas:**

- Timeout por operacion, no global. Un timeout global de 30s esconde que una
  llamada deberia tener 3s.
- El timeout cancela la operacion subyacente. No hay que "limpiar" a mano: el
  `context manager` se encarga.
- `asyncio.TimeoutError` se maneja explicitamente. Un timeout sin manejar sube
  como error generico y se confunde con un fallo del servicio.

```python
from asyncio import TimeoutError as AsyncioTimeoutError

try:
    async with asyncio.timeout(TIMEOUT_Llamada):
        resultado = await llamar()
except AsyncioTimeoutError:
    logger.warning("timeout en llamada externa", extra={"servicio": nombre})
    raise ErrorServicioNoDisponible(nombre) from None
```

### Paso 4 - Cancelacion: el patron que casi todos hacen mal

La cancelacion se propaga: cuando una corrutina es cancelada, toda la cadena
`await` se cancela. Lo que no se propaga es el trabajo "huerfano" creado con
`asyncio.create_task`.

```python
import asyncio
from collections.abc import Coroutine
from typing import Any


async def procesar_varios(items: list[str]) -> list[Any]:
    """Procesa items en paralelo, cancelando todo si uno falla."""
    tareas = [asyncio.create_task(procesar(item)) for item in items]
    try:
        return await asyncio.gather(*tareas)
    except Exception:
        # Si uno falla, los demas siguen corriendo: hay que cancelarlos.
        for tarea in tareas:
            tarea.cancel()
        # gather con return_exceptions=True espera a que terminen de verdad.
        await asyncio.gather(*tareas, return_exceptions=True)
        raise
```

En Python 3.11+ esto ya lo hace `asyncio.TaskGroup`:

```python
import asyncio


async def procesar_varios(items: list[str]) -> list[object]:
    async with asyncio.TaskGroup() as grupo:
        tareas = [grupo.create_task(procesar(item)) for item in items]
    return [t.result() for t in tareas]
```

`TaskGroup` cancela automaticamente todas las tareas sisters si una falla, y
espera a que terminen. Es el default para "varias tareas en paralelo, todas o
nada".

**Reglas:**

- `TaskGroup` es el default para concurrencia con fallo acoplado.
- `gather(..., return_exceptions=True)` cuando se quiere el mejor resultado
  posible, no todo-o-nada.
- Nunca se deja una `create_task` sin referencia. La tarea se pierde cuando el
  garbage collector la recoge, y su exception nunca se reporta.
- El bloque `finally` con `shield` protege trabajo critico de la cancelacion:

```python
from asyncio import CancelledError, shield

try:
    await shield(guardar_estado())
except CancelledError:
    logger.warning("cancelado durante guardado de estado")
    raise
```

- `CancelledError` **no** se traga. Si se captura y no se re-lanza, la
  cancelacion se pierde y el proceso no puede detenerse limpiamente.

```python
# MAL
except CancelledError:
    pass

# BIEN
except CancelledError:
    raise
```

### Paso 5 - Concurrencia controlada

`asyncio.gather` sobre una lista de 10.000 elementos lanza 10.000 conexiones
simultaneas. Eso no es concurrencia: es un ataque de denegacion de servicio
contra uno mismo.

```python
import asyncio
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")

LIMITE_CONCURRENCIA = 20


async def con_limite(
    items: list[str],
    operacion: Awaitable[T],
    limite: int = LIMITE_CONCURRENCIA,
) -> list[T]:
    """Ejecuta la operacion con como maximo `limite` en vuelo."""
    semaforo = asyncio.Semaphore(limite)

    async def con_semaforo(item: str) -> T:
        async with semaforo:
            return await operacion

    return await asyncio.gather(*(con_semaforo(item) for item in items))
```

**Reglas:**

- El limite se define segun el recurso escaso: conexiones de base de datos,
  slots del pool HTTP, threads del servidor. El default es 10-20.
- El limite de concurrencia de la base de datos es el que manda. Si la base
  tiene un pool de 10, la aplicacion no abre mas de 10 conexiones.
- `gather` sin limite esta bien solo cuando la lista es corta y conocida.

```python
# MAL
await asyncio.gather(*(procesar(item) for item in items))  # 10.000 de golpe

# BIEN
async with asyncio.Semaphore(20) as sem:
    await asyncio.gather(*(procesar_con_semaforo(i, sem) for i in items))
```

### Paso 6 - Errores en el borde

Una exception en una tarea sin recuperar se pierde. El traceback aparece en el
log como "Task exception was never retrieved", tarde y sin contexto.

```python
import asyncio
import logging

logger = logging.getLogger(__name__)


async def lanzar_en_background(corrutina: Coroutine) -> None:
    """Lanza una tarea y loguea cualquier fallo, sin tragarselo."""
    async def envoltura() -> None:
        try:
            await corrutina
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("fallo en tarea de background")
    await asyncio.create_task(envoltura())
```

En el lifespan de la aplicacion, todas las tareas de background se registran y
se cancelan al apagar:

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator


@asynccontextmanager
async def lifespan(app: object) -> AsyncIterator[None]:
    tareas = [asyncio.create_task(worker()) for worker in workers()]
    try:
        yield
    finally:
        for tarea in tareas:
            tarea.cancel()
        await asyncio.gather(*tareas, return_exceptions=True)
```

**Reglas:**

- El `finally` del lifespan siempre cancela las tareas. Sin eso, el proceso
  no termina y el reinicio del contenedor cuelga.
- `except Exception` loguea y no re-lanza en tareas de background: la tarea
  muere, el proceso sigue.
- `except asyncio.CancelledError: raise` antes de cualquier `except Exception`.
  En Python 3.8+ `CancelledError` hereda de `BaseException`, no de
  `Exception`, asi que `except Exception` no lo captura. Aun asi, el orden
  explicito documenta la intencion.

### Paso 7 - Probar codigo asincrono

```python
import pytest
from collections.abc import AsyncIterator

from mi_app.clients import Cliente


@pytest.fixture
async def cliente() -> AsyncIterator[Cliente]:
    """Fixture async: se crea, se usa y se destruye correctamente."""
    instancia = Cliente(url="http://localhost:PUERTO_DE_TEST")
    async with instancia:
        yield instancia
```

```python
# tests/test_pedidos.py
import pytest

from mi_app.servicios import PedidoNoEncontrado, obtener_pedido


@pytest.mark.asyncio
async def test_devuelve_pedido(cliente) -> None:
    pedido = await obtener_pedido(cliente, "123")
    assert pedido.id == "123"


@pytest.mark.asyncio
async def test_pedido_inexistente(cliente) -> None:
    with pytest.raises(PedidoNoEncontrado):
        await obtener_pedido(cliente, "inexistente")
```

La configuracion del plugin:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

**Reglas:**

- `asyncio_mode = "auto"` evita el decorador `@pytest.mark.asyncio` en cada
  test. Con `auto`, todos los tests async se reconocen.
- `asyncio_default_fixture_loop_scope = "function"`: cada test tiene su propio
  event loop. Es lo que evita el estado compartido entre tests.
- **Nunca** se hace `time.sleep()` dentro de un test async: congela el event
  loop y el test pasa sin probar nada.
- Para esperar, se usa `await asyncio.sleep(0)` para ceder el control, o mejor
  un evento explicito:

```python
import asyncio

evento = asyncio.Event()
await evento.wait()          # espera real
evento.set()                # libera
```

- El timeout se usa para detectar deadlocks, no para hacer que el test pase:

```python
with pytest.raises(asyncio.TimeoutError):
    async with asyncio.timeout(5):
        await operacion_que_deberia_cargar()
```

- Los mocks de I/O se reemplazan con fakes reales, no con `AsyncMock` en todo.
  Un `AsyncMock` que devuelve un `MagicMock` esconde los errores de tipo.
- Para probar cancelacion:

```python
@pytest.mark.asyncio
async def test_cancela_tareas_al_cancelar() -> None:
    tarea = asyncio.create_task(espera_larga())
    await asyncio.sleep(0)     # deja que arranque
    tarea.cancel()
    with pytest.raises(asyncio.CancelledError):
        await tarea
```

Los patrones completos, con el fake de reloj y el fan-out controlado, estan en
`references/pruebas-async.md`.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| `time.sleep()` en codigo async | Congela todo el event loop | `await asyncio.sleep()` |
| `time.sleep()` en un test async | El test pasa sin probar nada | `await asyncio.sleep(0)` o un `Event` |
| Llamada HTTP sin timeout | La tarea queda colgada para siempre | `asyncio.timeout` |
| `gather` sobre 10.000 items | Abre 10.000 conexiones | `Semaphore` |
| `create_task` sin referencia | La tarea se pierde en el GC | Referencia o `TaskGroup` |
| `except CancelledError: pass` | La cancelacion se pierde | `raise` |
| `except Exception: pass` | Errores invisibles | Loguear con contexto |
| `async def` sin `await` | Costo de scheduling sin beneficio | Dejar sync |
| `run_until_complete` en el lifespan | Crea un loop anidado | `await` directo |
| `loop.run_in_executor` para I/O | Oculta el problema de bloqueo | `await` nativo |
| Fire-and-forget sin LOGGER | La exception se pierde en silencio | Envoltura con log |
| Threads para I/O masiva | Escala mal y complica el codigo | async con `Semaphore` |
| `asyncio.run()` en codigo existente | No se puede llamar dos veces | Un solo loop por proceso |
| `shield` para "ignorar" cancelacion | Deja trabajo huerfano | `shield` solo para guardado critico |

## Referencias

### Skills relacionadas

- `dev-kit-backend-stack` - donde viven los casos de uso async en la arquitectura por capas.
- `dev-kit-python-tooling` - pytest, ruff y mypy configurados correctamente.
- `dev-kit-testing` - estrategia general de tests y mocks.
- `dev-kit-observability` - metricas de latencia y errores en codigo async.

### Archivos de esta skill

- `references/pruebas-async.md` - patrones de testing asincrono con fakes y reloj controlado.
- `references/concurrencia-y-cancellation.md` - TaskGroup, semaforos, cancelacion y fan-out.
