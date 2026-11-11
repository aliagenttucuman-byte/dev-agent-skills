# Mocks, fixtures y dobles de prueba

> Referencia de `dev-kit-testing`. Catalogo de dobles, reglas de mockeo,
> patrones de fixture y anti-patrones de arnes.

---

## 1. El catalogo de dobles

| Doble | Que es | Que verifica | Cuando se usa |
|---|---|---|---|
| **Stub** | objeto que devuelve un valor fijo | nada, solo habilita el camino | el gateway siempre aprueba |
| **Fake** | implementacion real pero simplificada | comportamiento real del sustituto | base de datos en memoria |
| **Mock** | objeto que registra y verifica llamadas | que se llamo, con que argumentos | "se envio el email" |
| **Spy** | objeto real envuelto que registra | camino real + verificacion posterior | verificar que se consulto la cache |
| **Fake clock** | reloj controlado | el paso del tiempo | expiracion, TTL, reintentos |
| **Fake server** | servidor HTTP local | el contrato HTTP completo | integracion de un cliente |

### La jerarquia de preferencia

```text
¿Existe un fake real?  ->  usalo (fake)
¿Se puede usar el valor real con una entrada controlada?  ->  usalo (spy)
¿Solo interesa la forma del dato?  ->  stub
¿Hay que verificar que se llamo?  ->  mock
```

**Preferir el fake sobre el mock** siempre que sea viable: un fake verifica mas
porque se comporta como el sistema real.

---

## 2. La frontera: que se puede mockear

**Si:** el tiempo, la red, el sistema de archivos, la aleatoriedad, el sistema
operativo, la cola de mensajes, los servicios externos, el reloj de arranque.

**No:** la logica de negocio, las funciones del propio modulo, las funciones
del modulo que se quiere probar, el codigo que el test afirma.

**La prueba de fuego:** si el test falla cuando el mock cambia su
comportamiento, el mock es una dependencia legitima. Si el test sigue verde
porque el mock hace lo que el codigo espera, el mock es decoracion.

---

## 3. La regla del `spec`

Un mock sin `spec` acepta cualquier llamada. El codigo puede empezar a llamar
`send_email()` en vez de `send()` y el test sigue verde: el bug llega a
produccion.

```python
from unittest.mock import Mock, patch

# Sin spec: acepta cualquier metodo, el test no detecta cambios de forma
bad = Mock()

# Con spec: si el codigo llama un metodo inexistente, revienta
good = Mock(spec=EmailSender)
```

**Regla:** todo mock de un objeto propio lleva `spec=`. Y el assert es sobre
la llamada, no sobre el retorno:

```python
def test_invitation_email_is_sent_to_invitee(mailer):
    send_invitation(user_id="u-1")

    mailer.send.assert_called_once_with(to="invitee@example.com", template="invite")
```

---

## 4. Patch: donde y como

```python
# Decorador con ruta de importacion completa: el test es legible y el patch
# se resuelve en el punto de uso.
from unittest.mock import patch

@patch("app.services.email.build_message")
def test_welcome_message_contains_name(build_message):
    build_message.return_value = "message"
    send_welcome("ada")

    build_message.assert_called_once_with("ada")
```

**Reglas:**

1. La ruta del patch es **la ruta donde se usa**, no la ruta donde se define.
   Patchear `app.services.email.build_message` cuando el codigo la importa
   con `from ... import build_message` no intercepta nada.
2. Se usa `patch` como decorador o como context manager, nunca dentro de la
   funcion de test.
3. Se patchea lo mas cercano al consumidor: si el modulo A llama a B y B llama
   a C, se patchea B, no C.
4. `autospec=True` cuando el mock debe comportarse como la clase real (valida
   firmas).

---

## 5. El reloj: el mock que mas se olvida

El tiempo es la fuente clasica de tests fragiles. Un test que depende del reloj
real falla de madrugada, pasa en la tarde, y nadie sabe por que.

```python
# Inyectado: el test decide cuando pasa el tiempo
def test_token_expires_after_configured_seconds(clock, token_service):
    token_service.issue("user-1")
    clock.advance(seconds=31)

    assert token_service.validate("user-1") is None
```

**Reglas del reloj:**

1. El reloj se inyecta, no se importa directo en el codigo de negocio.
2. No se usa `time.sleep` para "esperar que pase el tiempo": se avanza el reloj.
3. Si hay que esperar una condicion real (un worker, una promesa), se usa espera
   activa con timeout, no `sleep` de duracion fija.

```python
# Espera activa: falla rapido si no ocurre, en vez de esperar siempre igual
def wait_for(condition, timeout=5.0, interval=0.05):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(interval)
    return False
```

---

## 6. Fixtures: el arnes por capas

### Scope

| Scope | Duracion | Se usa para | Riesgo |
|---|---|---|---|
| `function` (default) | un test | casi todo | ninguno |
| `module` | el archivo | datos caros compartidos | estado compartido entre tests |
| `session` | toda la suite | motor de base, schema | contaminacion entre tests |
| `package` | un directorio | recursos compartidos de un area | baja visibilidad |

**Regla:** `session` solo para recursos caros (motor, compilado). Cualquier
otra cosa que se pueda volver a crear, se crea por test.

### El patron de aislamiento

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def engine():
    """Motor de base: se crea una vez y se destruye al final."""
    from app.db import create_engine_for_tests
    eng = create_engine_for_tests()
    yield eng
    eng.dispose()

@pytest.fixture
def client(engine):
    """Cliente HTTP sobre la base de tests, recreado por test."""
    from app.main import create_app
    with create_app(engine).test_client() as c:
        yield c

@pytest.fixture(autouse=True)
def _reset_state(engine):
    """Limpia entre tests para que el orden no importe."""
    yield
    engine.rollback()
```

### La regla del rollback

Todo test que escribe en base usa una transaccion que se revierte al final.
Consecuencia util: **los tests no dependen del orden**, porque ninguno deja
residuo.

### Fixture vs factory

| | Fixture | Factory |
|---|---|---|
| Que hace | entrega estado listo | construye entidades de dominio |
| Se usa cuando | el test necesita contexto | el test necesita N entidades |
| Ejemplo | `client`, `clock`, `auth_headers` | `order_factory`, `user_factory` |

**Regla:** si un fixture tiene mas de 15 lineas de setup, es una factory.

### El patron de factory

```python
# tests/factories.py
import datetime as dt

def order_factory(total=100, discount_rate=0.0, status="pending"):
    """Crea una orden con defaults validos. Cada test sobreescribe lo que necesita."""
    return {
        "total": total,
        "discount_rate": discount_rate,
        "status": status,
        "created_at": dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
    }
```

**Reglas de factory:**

1. Los defaults son **validos**, no neutrales: el default debe pasar el test.
2. Todos los campos del dominio estan, con un default explicito.
3. Los identificadores y fechas son deterministas: el test no depende de azar.
4. La factory no hace assert: construye, no verifica.

---

## 7. Anti-patrones de arnes

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Mockear la funcion que se prueba | El test verifica que el mock se llamo | mockear la frontera |
| `MagicMock()` sin `spec` | El codigo cambia de forma y el test no falla | `spec=` siempre |
| `patch` con cadena parcial | No intercepta nada y el test pasa siempre | ruta completa de importacion |
| `sleep` para esperar | Test lento y flaky | reloj inyectado o espera activa |
| Fixture `session` que muta | Contamina los tests siguientes | rollback o recrear |
| Setup gigante en un solo lugar | Nadie sabe que necesita cada test | fixtures chicas y factories |
| Datos reales de produccion | Fuga de datos y tests no reproducibles | datos sinteticos |
| Autouse con efectos colaterales | Oculta dependencias que no se ven | autouse solo para aislamiento |
| Mockear lo que se verifica | No se verifica nada | usar fake y afirmar sobre el resultado |
| Reutilizar el mismo mock entre tests | Acopla los tests entre si | un doble por test |
| Base de datos real de desarrollo | El test depende del estado local | base de tests aislada |
