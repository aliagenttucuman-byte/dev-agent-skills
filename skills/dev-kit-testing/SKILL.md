---
name: dev-kit-testing
description: "Estrategia de testing en piramide con gates por nivel, que testear y que no, naming de tests, fixtures y mocks sin acoplamiento, cobertura util frente a cobertura de vanidad, tests de contrato y ciclo TDD. CARGAR cuando hay que definir la suite, escribir tests, revisar cobertura o decidir si un cambio esta suficientemente probado."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [testing, pytest, playwright, tdd, coverage]
    category: software-development
    related_skills: [dev-kit-code-quality, dev-kit-ci-cd, dev-kit-review, dev-kit-backend-stack]
---

# Dev Kit - Testing

> **Trigger:** "definir la suite de tests", "que testear y que no", "faltan tests",
> "la cobertura subio pero igual hay bugs", "escribo el test primero",
> "los tests se rompen en cada cambio".
> Cargar esta skill ANTES de escribir la primera linea de test.

Una politica de testing **verificable por comandos**. El error clasico no es
testear poco: es **testear lo que no importa**. Si un test no falla al romperse
el comportamiento, no es un test: es decoracion.

## La piramide: que cubre cada nivel

| Nivel | Que protege | Proporcion | Velocidad | Gate |
|---|---|---|---|---|
| Unitario | logica de negocio pura, reglas, calculos | ~70% | milisegundos | no baja la linea base |
| Integracion | contrato con DB, ORM, migraciones, colas | ~20% | segundos | falla si el contrato deriva |
| E2E | flujos de usuario, camino critico | ~10% | minutos | smoke por release |
| Contract | forma del dato entre servicios | transversal | segundos | bloquea despliegue |

**Regla de reparto:** si el ratio unitario cae bajo 60%, el problema no es
falta de tests: es que la logica esta pegada a la infraestructura y no se puede
testear sin levantar todo. Se resuelve extrayendo logica.

### Que se testea y que no

| Se testea | No se testea | Por que |
|---|---|---|
| Reglas de negocio y casos borde | getters, setters, `__repr__` | prueban el lenguaje, no el producto |
| Validacion de entrada y rechazos | imports, constantes | el compilador ya lo cubre |
| Serializacion y desserializacion | funciones de una linea sin rama | una rama, un caso |
| Permisos: quien puede hacer que | el framework HTTP | el framework ya tiene sus tests |
| Migraciones: apply y rollback | la existencia de la tabla | el motor lo garantiza |
| Integraciones con request y response | mocks del motor de base | probarias el mock |
| Caminos de error | el texto exacto del log | el texto cambia, el comportamiento no |

**La pregunta de decision:** "si esta linea cambia, el producto se rompe de una
forma que el usuario nota?" Si es no, no merece test unitario. Si es si y la
logica es pura, merece uno.

**La excepcion:** el codigo que maneja dinero, permisos o datos personales se
testea aunque parezca trivial: ahi una linea mal puesta es un incidente.

## Workflow

| Paso | Que hace | Artefacto | Gate |
|---|---|---|---|
| 1. Mapear riesgo | Listar reglas de negocio y flujos criticos | tabla riesgo -> nivel | Cada regla critica tiene nivel |
| 2. Planear | Definir que test se escribe por regla | `templates/test-plan.md` | El plan esta en el PR |
| 3. Armar el arnes | Fixtures, factories, helpers | `conftest.py`, `tests/factories.py` | El arnes corre en 1 comando |
| 4. Implementar | Tests por nivel, TDD si aplica | archivos de test | verdes antes del push |
| 5. Blindar en CI | Gates por nivel con umbral | tabla de gates | Cada gate corre en CI |
| 6. Auditar | Detectar tests sin valor y fragiles | reporte de auditoria | Cada test tiene criterio |

### Paso 1 - Mapear riesgo antes de testear

Tres columnas: **regla de negocio**, **como falla si se rompe**, **nivel de
test**. La columna del medio manda: si nadie describe el fallo, la regla no
importa y no se testea.

```text
regla                      | fallo si se rompe                     | nivel
descuento maximo por orden | cliente paga de mas, perdida de dinero | unitario + integracion
token expira a los 30 min  | sesion abierta indefinidamente         | integracion + e2e
```

### Paso 2 - El plan de test va en el PR

El artefacto es `templates/test-plan.md`. Un PR sin plan de test no tiene scope de
verificacion: el revisor no sabe que se espera que rompa.

### Paso 3 - Naming: el nombre del test es la especificacion

El nombre se lee como frase y dice **comportamiento**, no **metodo**.

| Nivel | Convencion | Ejemplo |
|---|---|---|
| Unitario | `test_<unidad>_<resultado>_<condicion>` | `test_discount_capped_at_max_when_limit_exceeded` |
| Unitario (error) | `test_<unidad>_raises_<error>_when_<condicion>` | `test_checkout_raises_payment_error_on_timeout` |
| Integracion | `test_<servicio>_<operacion>_<resultado>` | `test_orders_api_creates_order` |
| E2E | `test_<rol>_<flujo>_<resultado>` | `test_buyer_completes_checkout` |
| Contract | `test_<consumidor>_accepts_<productor>_contract` | `test_billing_accepts_orders_contract` |

**Regla:** si el nombre no dice que se espera, el test no tiene criterio de
aceptacion y no falla cuando el comportamiento se rompe.

```python
# Bien: dice unidad, resultado y condicion
def test_discount_capped_at_max_when_limit_exceeded(order_factory):
    order = order_factory(total=10_000, discount_rate=0.5)

    total = apply_discount(order)

    assert total == order.total - order.discount_cap

# Mal: dice que se llama a la funcion
def test_apply_discount():
    ...
```

### Paso 4 - Fixtures y factories: el arnes

| Pieza | Que es | Cuando se usa |
|---|---|---|
| Fixture | estado compartido y barato (reloj, config, cliente HTTP) | datos de cortesia, cleanup automatico |
| Factory | constructor de datos de dominio con defaults validos | un test necesita N entidades |
| Builder | constructor stepwise para casos complejos | el caso tiene muchas variantes |

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

**Reglas del arnes:**

1. Un fixture de scope `session` solo para lo que es costoso (motor, schema).
2. Todo lo que escribe en base usa una transaccion que se revierte al final.
3. Los tests no dependen del orden: cada test arma su propio estado.
4. Si un fixture tiene mas de 15 lineas de setup, es una factory.
5. El nombre del fixture se lee como sustantivo, no como verbo.

### Paso 5 - Mocks: la frontera, nunca el interior

Mockear es sustituir un **recurso externo** por algo controlado: el tiempo, la
red, el sistema de archivos, la aleatoriedad, la cola, el servicio externo.
**Nunca se mockea la propia logica**: un test que mockea la funcion que quiere
probar verifica que el mock se llamo.

| Tipo | Que reemplaza | Ejemplo |
|---|---|---|
| Stub | respuesta fija | el gateway de pago siempre aprueba |
| Fake | implementacion simple pero real | una base de datos en memoria |
| Mock | verifica como se uso | el email: seCerro que se llamo una vez |
| Spy | registra como se uso | espiar el cliente HTTP |

```python
# El tiempo SI se controla: es la fuente clasica de tests fragiles
def test_token_expires_after_configured_seconds(fixed_clock, token_service):
    token_service.issue("user-1")
    fixed_clock.advance(seconds=31)

    assert token_service.validate("user-1") is None

# El error NO se mockea: se simula la condicion con la que el sistema falla
def test_checkout_fails_when_gateway_unavailable(gateway_offline, cart):
    with pytest.raises(PaymentUnavailable):
        checkout(cart)

    assert cart.status == "not_charged"
```

**Reglas de mocks:**

1. Un mock por test, como maximo dos. Si hay tres, el test prueba la
   orquestacion, no el comportamiento.
2. El mock nunca devuelve `MagicMock()` generico: se configura con `spec=` para
   que el test falle si el codigo cambia la forma del dato.
3. No se mockea lo que se quiere verificar: si el test verifica el email, usa
   el fake de cola.
4. `patch` se usa como decorador con ruta de importacion completa.

### Paso 6 - Cobertura util frente a cobertura de vanidad

La cobertura de lineas mide **codigo ejecutado**, no **comportamiento
verificado**: se sube con tests que no verifican nada, o con codigo muerto.

| Metrica | Que mide | Veredicto |
|---|---|---|
| Cobertura de lineas | lineas ejecutadas | piso minimo, no objetivo |
| Cobertura de ramas | caminos condicionales | util si apunta a reglas |
| Tests sin asercion | tests que no afirman nada | el peor caso, siempre |
| Mutacion sobreviviente | tests que no matan el bug | la que si importa |

**La metrica que manda: mutacion sobreviviente.** Si un test sigue verde al
cambiar el codigo a algo incorrecto, ese test no protege nada.

```bash
# cobertura como piso, no como meta
pytest --cov=src --cov-report=term-missing --cov-fail-under=<LINEA_BASE>

# deteccion de tests que no afirman nada
ruff check --select PT, S101 tests/
```

**Regla:** la linea base de cobertura sube, nunca baja. Un cambio que la reduce
se rechaza o se acompaña de un ADR explicando por que.

### Paso 7 - Tests de contrato: donde se rompen los sistemas

El contrato es la forma del dato que cruza la frontera. El **productor**
publica un JSON Schema o un OpenAPI; el **consumidor** define el minimo que
necesita y lo ejecuta contra el productor.

El test del consumidor evita la rotura clasica: el productor cambia un campo,
el consumidor no actualiza, y el error aparece en produccion.

**Regla:** el contrato se versiona. Un cambio incompatible es una version
nueva, no una sorpresa. El test de contrato bloquea el despliegue del productor
cuando el contrato deriva.

### Paso 8 - TDD: el ciclo

```text
ROJO     -> escribe el test que falla. Si pasa, el test no prueba nada.
VERDE    -> implementa lo minimo para que pase. Nada mas.
REFACTOR -> limpia el codigo en verde. Si el test se rompe, la limpieza rompio comportamiento.
```

La disciplina que mas valor aporta es la primera: **un test que pasa al
escribirse no prueba el comportamiento nuevo.** Si falla antes de implementar,
la especificacion esta escrita.

**Reglas del TDD en equipo:**

1. Test e implementacion van en el mismo PR: no hay PR de tests "para despues",
   porque despues nunca llega y el test se escribe contra el codigo viejo.
2. Si un test falla por una razon que no es la esperada, se arregla el test
   antes de implementar.
3. El rojo queda en el historial: test e implementacion no se escriben juntos
   sin evidencia intermedia.

### Gates de testing

| Gate | Que mide | Comando | Si falla |
|---|---|---|---|
| T1 Unitarios | tests rojos | `pytest tests/unit -q` | bloquea el pipeline |
| T2 Integracion | contrato con DB y migraciones | `pytest tests/integration -q` | bloquea el pipeline |
| T3 E2E smoke | flujos criticos | `playwright test --project=smoke` | bloquea el release |
| T4 Cobertura | delta contra linea base | `pytest --cov=src --cov-fail-under=<BASE>` | bloquea el pipeline |
| T5 Higiene de test | tests sin asercion, `sleep`, orden | `ruff check --select PT, S101 tests/` | bloquea el pipeline |
| T6 Flakiness | test que falla sin cambio | reintento x3 | bloquea el pipeline |
| T7 Contrato | derivacion del contrato | `pytest tests/contract -q` | bloquea el despliegue |
| T8 Tiempo | duracion de la suite | `pytest --durations=10` | avisa, hasta tener linea base |

**Regla de velocidad:** la suite unitaria corre en menos de 60 segundos. Una
suite de 5 minutos no se ejecuta antes de cada push: se deja de ejecutar. Una
suite lenta se paga como bugs.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| "Testeamos todo para que no falle nada" | Se testea el lenguaje, no el producto | aplicar la tabla de que se testea |
| Cobertura como objetivo | Se sube ejecutando codigo sin verificar | cobertura como piso, mutacion como verdad |
| Test que no falla al romperse | No protege nada | testear primero en rojo |
| Mockear la propia logica | Verifica que el mock se llamo | mockear solo la frontera |
| `MagicMock()` sin `spec` | El codigo cambia de forma y el test no falla | `spec=` siempre, con assert de llamadas |
| Tests que dependen del orden | Fallan en CI y no en local | cada test arma su estado |
| `time.sleep` para esperar | Test lento y flaky | reloj inyectado o espera activa |
| `setup` gigante compartido | Nadie sabe que necesita cada test | factories y fixtures chicas |
| PR de tests "para despues" | Se escriben contra el codigo viejo | test e implementacion en el mismo PR |
| Snapshot de HTML sin revision | El snapshot cambia y se acepta a ciegas | snapshot solo con revision explicita |
| E2E para todo | Suite larga, se deja de correr | E2E solo para caminos criticos |
| Mockear el reloj por test | Tests acoplados a la implementacion | un solo reloj inyectable |
| Testear getters | Ruido que oculta falta de cobertura real | sin tests de codigo sin rama |
| Un test, quince asserts | Cuando falla, no se sabe que se rompio | un comportamiento por test |
| Ignorar el test que "siempre fallo" | Es el que encuentra el bug | investigarlo o borrarlo con justificacion |

## Referencias

- `templates/test-plan.md` - plan de test por PR: reglas, nivel, casos y criterio
- `references/estrategia-por-nivel.md` - que nivel cubre que riesgo y como escala
  la suite sin que se vuelva lenta
- `references/mocks-y-fixtures.md` - dobles de prueba, reglas de mockeo, fixtures
