# Pruebas de codigo asincrono

Los tests async fallan de formas que los sync no fallan. Esta referencia
cubre los patrones que hacen la suite determinista.

---

## El problema del event loop y la latencia real

Un test que hace `await asyncio.sleep(1)` tarda un segundo real. Con cien tests,
el pipeline tarda casi dos minutos en dormir. La solucion es no dormir: se
controla el reloj.

```python
import asyncio
from collections.abc import AsyncIterator
from typing import Any


class RelojFalso:
    """Reloj virtual para tests async: el tiempo avanza solo lo que se pide."""

    def __init__(self) -> None:
        self._pendientes: list[tuple[float, asyncio.Future[None]]] = []
        self._tiempo = 0.0

    def advance(self, segundos: float) -> None:
        self._tiempo += segundos
        resueltos = [f for t, f in self._pendientes if t <= self._tiempo]
        self._pendientes = [(t, f) for t, f in self._pendientes if t > self._tiempo]
        for futuro in resueltos:
            if not futuro.done():
                futuro.set_result(None)

    async def sleep(self, segundos: float) -> None:
        if segundos <= 0:
            await asyncio.sleep(0)
            return
        futuro: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._pendientes.append((self._tiempo + segundos, futuro))
        await futuro

    async def wait_for(self, segundos: float) -> None:
        """Espera un 'tick' sin avanzar el reloj virtual."""
        await asyncio.sleep(0)
```

El principio: el componente bajo test recibe el reloj por inyectacion, no
llama a `asyncio.sleep` directamente.

```python
# app/reloj.py
import asyncio
from collections.abc import Awaitable
from typing import Protocol


class Reloj(Protocol):
    async def sleep(self, segundos: float) -> None: ...


class RelojReal:
    async def sleep(self, segundos: float) -> None:
        await asyncio.sleep(segundos)
```

Con la inyeccion, el test avanza el reloj virtual al instante.

---

## Fixture async: el ciclo de vida correcto

```python
import pytest
from collections.abc import AsyncIterator

from mi_app.cliente import Cliente


@pytest.fixture
async def cliente() -> AsyncIterator[Cliente]:
    """Crea el cliente, lo usa y lo destruye sin leaks."""
    instancia = Cliente(url="http://test.invalid")
    await instancia.conectar()
    try:
        yield instancia
    finally:
        await instancia.cerrar()
```

**Reglas:**

- El `finally` con cleanup es obligatorio. Un fixture que no limpia deja
  conexiones abiertas y el siguiente test falla por un motivo que no parece
  relacionado.
- `pytest_asyncio.fixture` explicito si no se usa `asyncio_mode = "auto"`.
- Un fixture de scope mayor que `function` con estado mutable comparte estado
  entre tests. Con `asyncio_default_fixture_loop_scope = "function"`, cada
  test tiene su loop: un fixture de scope `session` con conexiones abiertas
  falla.

---

## Los cuatro estados de una operacion asincrona

Una llamada que falla tiene cuatro resultados posibles, y el test debe cubrir
los cuatro:

| Estado | Como se provoca | Que se verifica |
|---|---|---|
| Exito | El fake responde bien | El valor devuelto |
| Exception | El fake lanza | Se propaga el error correcto |
| Timeout | El fake no responde | Se lanza `TimeoutError` |
| Cancelacion | Se cancela la tarea | Se lanza `CancelledError` |

```python
import asyncio

import pytest

from mi_app.servicios import ErrorTimeout


class ClienteQueNoResponde:
    async def get(self, url: str) -> bytes:
        await asyncio.Event().wait()   # nunca retorna
        raise AssertionError("inalcanzable")


@pytest.mark.asyncio
async def test_timeout_cuando_el_servicio_no_responde() -> None:
    with pytest.raises(ErrorTimeout):
        async with asyncio.timeout(0.1):
            await ClienteQueNoResponde().get("/x")
```

---

## Probar cancelacion

```python
import asyncio

import pytest


@pytest.mark.asyncio
async def test_la_cancelacion_se_propaga() -> None:
    tarea = asyncio.create_task(espera_larga())
    await asyncio.sleep(0)          # deja que la tarea arranque
    tarea.cancel()

    with pytest.raises(asyncio.CancelledError):
        await tarea


@pytest.mark.asyncio
async def test_cancelar_una_tarea_las_sisters() -> None:
    """Si una falla, las demas se cancelan. TaskGroup lo garantiza."""
    terminadas: list[str] = []

    async def lenta(nombre: str) -> None:
        try:
            await asyncio.sleep(10)
            terminadas.append(nombre)
        except asyncio.CancelledError:
            raise

    async def falla() -> None:
        await asyncio.sleep(0)
        raise RuntimeError("boom")

    with pytest.raises(ExceptionGroup):
        async with asyncio.TaskGroup() as grupo:
            grupo.create_task(lenta("a"))
            grupo.create_task(lenta("b"))
            grupo.create_task(falla())

    assert terminadas == []   # ninguna sister completo
```

`ExceptionGroup` es el error que `TaskGroup` levanta cuando falla mas de una
tarea. Con una sola, levanta la exception original.

---

## Probar el limite de concurrencia

El limite de concurrencia es logica de negocio, no un detalle de la libreria.
Se testea.

```python
import asyncio

import pytest

from mi_app.fanout import procesar_con_limite


class Rastreador:
    """Registra cuantos items estan en vuelo al mismo tiempo."""

    def __init__(self) -> None:
        self.maximo_simultaneo = 0
        self._actuales = 0

    async def procesar(self, item: int) -> int:
        self._actuales += 1
        self.maximo_simultaneo = max(self.maximo_simultaneo, self._actuales)
        try:
            await asyncio.sleep(0.01)
            return item
        finally:
            self._actuales -= 1


@pytest.mark.asyncio
async def test_respeta_el_limite_de_concurrencia() -> None:
    rastreador = Rastreador()
    resultados = await procesar_con_limite(
        list(range(50)),
        rastreador.procesar,
        limite=5,
    )

    assert len(resultados) == 50
    assert rastreador.maximo_simultaneo <= 5
```

---

## Mockear sin perder los tipos

`AsyncMock` devuelve `MagicMock` en cualquier posicion y esconde errores de
tipo. El patron correcto: un fake con la misma firma.

```python
from dataclasses import dataclass


@dataclass
class RespuestaFalsa:
    codigo: int
    cuerpo: bytes

    def raise_for_status(self) -> None:
        if self.codigo >= 400:
            raise RuntimeError(f"error {self.codigo}")


class ClienteFalso:
    def __init__(self, respuestas: dict[str, RespuestaFalsa]) -> None:
        self._respuestas = respuestas
        self.llamadas: list[str] = []

    async def get(self, url: str) -> RespuestaFalsa:
        self.llamadas.append(url)
        return self._respuestas[url]
```

El fake declara tipos reales. Si la firma del cliente cambia, el fake deja de
cumplir el `Protocol` y el type checker lo dice.

---

## Evitar las trampas comunes

| Trampa | Sintoma | Correccion |
|---|---|---|
| `await asyncio.sleep(0.1)` para "dar tiempo" | Tests lentos y flaky | `await asyncio.sleep(0)` o `Event` |
| Fixture sin `finally` | Fuga de recursos | Cleanup garantizado |
| `AsyncMock` en todo | Errores de tipo ocultos | Fake con la firma real |
| Testear `asyncio.sleep` | No se puede verificar | Reloj inyectado |
| Orden de tests dependiente | Falla solo en CI | Un test, un escenario |
| `event_loop` fixture propio | Loop distinto al de pytest | `asyncio_mode = auto` |

---

## Configuracion recomendada

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
addopts = ["-ra", "--strict-markers"]
```

Con `asyncio_mode = "auto"` no hace falta `@pytest.mark.asyncio` en cada test.
Los tests sync y async conviven en la misma suite sin conflicto.
