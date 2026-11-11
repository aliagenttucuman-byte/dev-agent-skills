# Concurrencia y cancelacion

Referencia de los mecanismos de `asyncio` para controlar el fan-out, limites y
cancelacion.

---

## TaskGroup: el default

`TaskGroup` es la forma correcta de "varias tareas en paralelo, todas o
nada". Resuelve tres problemas a la vez: cancela las sisters si una falla,
espera a que terminen de verdad y agrega las excepciones.

```python
import asyncio
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")


async def todas_o_nada(operaciones: list[Awaitable[T]]) -> list[T]:
    async with asyncio.TaskGroup() as grupo:
        tareas = [grupo.create_task(op) for op in operaciones]
    return [t.result() for t in tareas]
```

**Comportamiento:**

- Si una tarea lanza excepcion, `TaskGroup` cancela el resto.
- Al salir del `with`, espera a que todas terminen.
- Si una sola falla, propaga la excepcion original.
- Si fallan varias, propaga un `ExceptionGroup`.

**Cuando no usarlo:** cuando se quiere el mejor resultado posible y seguir con
los que si funcionaron. Ahi va `gather(return_exceptions=True)`.

---

## gather: dos modos

```python
import asyncio

# Modo 1: todo o nada. La primera exception cancela el resto.
resultados = await asyncio.gather(*operaciones)

# Modo 2: mejor esfuerzo. Cada exception vuelve como resultado.
resultados = await asyncio.gather(*operaciones, return_exceptions=True)

for indice, resultado in enumerate(resultados):
    if isinstance(resultado, Exception):
        logger.warning("operacion fallida", extra={"indice": indice})
        continue
    procesar(resultado)
```

El modo 2 requiere manejar la exception explicitamente: no se propaga, queda
dentro de la lista. Es util para procesamientos batch donde un elemento
fallido no debe tirar abajo los demas.

---

## Semoforo: el limite de concurrencia

```python
import asyncio
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")


async def con_limite(
    items: list[str],
    operacion: Awaitable[T],
    limite: int = 20,
) -> list[T]:
    """Ejecuta la operacion con como maximo `limite` items en vuelo."""
    semaforo = asyncio.Semaphore(limite)

    async def con_semaforo(item: str) -> T:
        async with semaforo:
            return await operacion

    return await asyncio.gather(*(con_semaforo(item) for item in items))
```

**El limite se deriva del recurso escaso:**

| Recurso | Limite tipico |
|---|---|
| Pool de conexiones de base de datos | 10-20 |
| Pool HTTP del cliente | Segun `max_connections` |
| Threads del servidor | Cantidad de cores x multiplicador |
| Rate limit de un API externo | El del API |

Si la base tiene pool de 10 y la app abre 50 conexiones, las 40 restantes
esperan en el servidor de la base: la latencia sube y el throughput no.

---

## Cancelacion: como se propaga

```
cancelar tarea_padre
   |
   +-> await en la tarea_padre se cancela
          |
          +-> await en la tarea_hija se cancela
                 |
                 +-> await en la tarea_nieta se cancela
```

La cancelacion se propaga hacia abajo por la cadena de `await`. Lo que **no**
se propaga:

- El trabajo creado con `create_task` sin esperar.
- El codigo que captura `CancelledError` y no lo re-lanza.
- Los `finally` que tardan demasiado (la cancelacion espera a que terminen).

```python
# MAL: la cancelacion se pierde
try:
    await operacion()
except asyncio.CancelledError:
    pass

# BIEN: la cancelacion sigue su curso
try:
    await operacion()
except asyncio.CancelledError:
    logger.info("cancelado")
    raise
```

---

## Shield: proteger trabajo critico

`shield` evita que la cancelacion alcance una operacion, pero la tarea externa
si se cancela.

```python
import asyncio
from asyncio import CancelledError, shield


async def guardar_estado() -> None:
    await escribir_en_base()


async def operacion_critica() -> None:
    try:
        await shield(guardar_estado())
    except CancelledError:
        logger.warning("cancelado durante el guardado")
        raise
```

**Ojo:** `shield` crea una tarea interna. Si no se espera a que termine, el
trabajo protegido se pierde igual. Para un guardado critico, se usa `shield`
con `await` y se acepta que la cancelacion espere.

---

## AnyIO: la alternativa portable

`anyio` ofrece la misma API sobre asyncio y trio, y agrega cancel scopes.

```python
import anyio


async def main() -> None:
    async with anyio.create_task_group() as grupo:
        grupo.start_soon(tarea, "a")
        grupo.start_soon(tarea, "b")


anyio.run(main)
```

**Ventaja:** el codigo queda portable entre backends de event loop.
**Desventaja:** una dependencia extra, y el ecosistema es mas chico.

El default del kit es `asyncio` puro. Se usa `anyio` cuando el proyecto ya lo
tiene o cuando se necesita `trio` (HTTP/2, streaming avanzado).

---

## collect: agrupar por tipo de resultado

```python
import asyncio
from typing import TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=Exception)


async def particionar(
    operaciones: list[Awaitable[T]],
) -> tuple[list[T], list[E]]:
    """Separa los resultados exitosos de las excepciones."""
    resultados = await asyncio.gather(*operaciones, return_exceptions=True)
    ok: list[T] = []
    errores: list[E] = []
    for resultado in resultados:
        if isinstance(resultado, Exception):
            errores.append(resultado)
        else:
            ok.append(resultado)
    return ok, errores
```

---

## Checklist de concurrencia

- [ ] Cada operacion de I/O externa tiene timeout
- [ ] El fan-out tiene limite de concurrencia
- [ ] Cada `create_task` tiene referencia y se cancela al apagar
- [ ] `CancelledError` se re-lanza, nunca se traga
- [ ] Las tareas de background loguean sus exceptions
- [ ] El lifespan cancela las tareas en el `finally`
- [ ] Los tests cubren exito, exception, timeout y cancelacion
- [ ] Ningun test usa `time.sleep` ni `await asyncio.sleep` con valor alto
