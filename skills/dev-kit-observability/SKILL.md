---
name: dev-kit-observability
description: "Logging estructurado, metricas, health checks y trazabilidad distribuida para saber que esta pasando en produccion sin depender de los usuarios. CARGAR al instrumentar un servicio, cuando hay que diagnosticar un incidente o cuando se define que se monitorea."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [observability, logging, metrics, tracing, slo, monitoring]
    category: software-development
    related_skills: [dev-kit-backend-stack, dev-kit-ci-cd, dev-kit-incident-response, dev-kit-database]
---

# Dev Kit - Observability

> **Trigger:** "no se que esta pasando en produccion", "instrumentar el
> servicio", "agregar logs", "definir que monitorear", "las alertas saltan
> mucho". Cargar antes de desplegar a produccion, no despues.

## Que es esto

Los tres Signals, mas lo que hace falta para que sirvan: logs estructurados,
metricas y trazas. Y las reglas para no generar ruido.

## El principio

> **Un log que nadie lee es un costo. Una alerta que no requiere accion es
> ruido. Los dos juntos hacen que la observabilidad se ignoren.**

La observabilidad que no cambia una decision es un gasto.

## Los tres signals

| Signal | Que es | Pregunta que responde | Donde se mira |
|---|---|---|---|
| **Logs** | Eventos discretos con contexto | Que paso en este caso puntual | Buscar un request especifico |
| **Metricas** | Agregados numericos en el tiempo | Como esta el sistema ahora | Graficos y alertas |
| **Trazas** | El camino de una operacion entre servicios | Donde se fue el tiempo | waterfall de un request |

**Regla:** los logs explican el "que", las metricas el "como", las trazas el
"donde".

**Regla:** no se empieza por trazas distribuidas. Se empieza por logs
estructurados y metricas basicas. Las trazas tienen costo de instrumentacion y
de infraestructura.

## Logs

### Estructurados, no texto libre

```python
logger.info("order_created", order_id=order.id, customer_id=customer.id, total=order.total)
```

```json
{
  "ts": "2026-03-14T10:22:31.482Z",
  "level": "INFO",
  "logger": "app.domain.orders",
  "message": "order_created",
  "order_id": "a1b2",
  "customer_id": "c9d8",
  "total": 150.0,
  "correlation_id": "req-8f2a"
}
```

**Por que JSON:** un log de texto libre obliga a parsear con regex para
encontrar un campo. Con JSON, el filtro es un campo igual a un campo de
cualquier base de datos.

**Regla:** el `message` es el evento (un verbo y un sustantivo, en snake_case):
`order_created`, `payment_failed`, `user_invited`. No es una frase.

**Regla:** los atributos van como campos, no interpolados en el mensaje.
`logger.info(f"Order {oid} created")` no se puede filtrar.

### Niveles

| Nivel | Cuando | Ejemplo |
|---|---|---|
| `DEBUG` | Detalle de diagnostico, desactivado en produccion por defecto | Valores intermedios de un calculo |
| `INFO` | Un evento de negocio relevante | `order_created` |
| `WARNING` | Algo raro pero el sistema se recupero | Retry de un servicio externo, valor fuera de rango |
| `ERROR` | La operacion fallo | Excepcion no manejada, dependencia caida |
| `CRITICAL` | El servicio no puede seguir | Base de datos inaccesible |

**Regla:** `ERROR` es para fallos que requieren accion. Si nadie va a mirar,
es `WARNING` o no es log.

**Regla:** un error esperado (un 404 de un recurso que no existe) no es un
error: es `INFO`. Si se loguea como error, el contador de errores no sirve
para detectar problemas reales.

### Que NO loggear

| No loggear | Por que |
|---|---|
| Contrasenas, tokens, claves de API | Un log se copia, se indexa, se comparte |
| Datos personales identificables | Requisito legal y de confianza |
| El cuerpo completo de un request | Ruido y riesgo |
| Cartas de credenciales | Igual que las contrasenas |
| Passwords hasheados | Tambien son credenciales |
| El contenido de un LLM con datos de usuario | Puede contener lo que el usuario escribio |

**Regla:** la sanitizacion es del framework de logging, no del sitio de llamada. Si
cada llamada tiene que acordarse de no loggear el token, tarde o temprano uno
se olvida.

```python
class SensitiveFilter(logging.Filter):
    """Redacta campos sensibles antes de serializar."""

    SENSITIVE = {"password", "token", "api_key", "authorization", "secret", "ssn", "credit_card"}

    def filter(self, record: logging.LogRecord) -> bool:
        for key in list(record.__dict__):
            if key.lower() in self.SENSITIVE:
                record.__dict__[key] = "<redacted>"
        return True
```

### Contexto

```python
# Contexto por peticion: se inyecta una vez y viaja a todos los logs
logger = logging.getLogger(__name__)
logger.info("request_completed", duration_ms=duration, status=200)
```

**Regla:** todo log de una operacion lleva el `correlation_id`. Es lo que
permite reconstruir el camino de un caso.

**Regla:** el contexto se pasa por parametro explicito o por un context
manager, no por una variable global. Una variable global no es segura con
hilos, y con async la mezcla los contextos entre tareas.

## Metricas

### Las cuatro que todo servicio necesita

| Metrica | Tipo | Que dice |
|---|---|---|
| `requests_total` | counter | Volumen de requests, por ruta y estado |
| `request_duration_seconds` | histogram | Latencia, por ruta |
| `errors_total` | counter | Errores, por tipo |
| `build_info` | gauge | Version desplegada (1 = la actual) |

**Regla:** toda metrica lleva labels de baja cardinalidad: ruta, metodo,
estado. **Nunca** el id del usuario, el id del recurso o un mensaje de error
como label. Eso explota la cardinalidad y revienta la base de metricas.

```python
# MAL: cardinalidad ilimitada
REQUEST_COUNT.labels(user_id=uid).inc()

# BIEN: cardinalidad acotada
REQUEST_COUNT.labels(route="/orders", method="POST", status="200").inc()
```

**Regla:** las rutas se agrupan por patron, no por id. `/orders/123` y
`/orders/456` son la misma ruta: `/orders/:id`. Con el id, cada request crea
una serie nueva.

### Saturation

Las metricas de saturacion dicen si el sistema esta por llegar a su limite:

| Metrica | Tipo | Limite |
|---|---|---|
| `queue_depth` | gauge | Longitud de la cola |
| `active_requests` | gauge | Requests en curso |
| `connection_pool_used` | gauge | Conexiones ocupadas del pool |
| `db_connections_active` | gauge | Conexiones activas |

**Regla:** el pool de conexiones es el limite duro mas comun. Un pool de 20
conexiones y 50 requests concurrentes significa que 30 requests esperan. El
tiempo de espera es la metrica, no el tiempo de la query.

## Health checks

### Liveness vs readiness

| Endpoint | Pregunta | Si falla |
|---|---|---|
| `/health` (liveness) | El proceso esta vivo? | Reiniciar el proceso |
| `/ready` (readiness) | Puede atender requests? | Sacar de balanceo |

**Regla dura:** `/health` NO verifica dependencias. Un health check que
consulta la base de datos y falla cuando la base esta lenta hace que el
orquestador reinicie todos los servicios en cascada, empeorando la caida.

**Regla:** la diferencia entre liveness y readiness es la diferencia entre
"reiniciar esto" y "no mandarle trafico". Confundirlos causa outages
cascada, que son el peor incidente posible.

```python
@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness: solo verifica que el proceso responde."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(session: Session = Depends(get_session)) -> dict[str, str]:
    """Readiness: verifica que las dependencias criticas responden."""
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="base de datos no disponible")
    return {"status": "ready"}
```

**Regla:** el timeout del health check es corto (1-2 segundos). Un health
check lento es un health check que miente.

## Trazas

### Cuando vale la pena

| Situacion | Trazas |
|---|---|
| Un solo servicio | No. Los logs bastan |
| Varios servicios que se hablan | Si |
| El tiempo se reparte entre llamadas a servicios externos | Si |
| Debug de una operacion larga | Si |
| Monitoreo de SLA con multiples pasos | Si |

### El patron

```python
with tracer.start_as_current_span("process_order") as span:
    span.set_attribute("order.id", order.id)
    span.set_attribute("order.total", order.total)

    with tracer.start_as_current_span("charge_payment"):
        payment = payments.charge(order)
```

**Regla:** el span tiene un nombre de operacion de negocio, no de funcion
tecnica. `process_order` es util; `do_thing_v2` no.

**Regla:** los atributos del span son de bajo volumen y sin datos personales.

**Regla:** el trace id se propaga en el header `traceparent` y aparece en los
logs. Sin eso, el trace y los logs son dos mundos separados.

## SLOs

### Definir el SLO antes de la alerta

```yaml
slo:
  availability:
    target: 99.9%        # sobre 30 dias
    window: 30d
  latency:
    target: 95%           # percentil
    threshold: 500ms
```

**Regla:** la alerta se dispara cuando se rompe el SLO, no cuando una metrica
cruza un umbral arbitrario.

**Regla:** se alerta sobre la tasa de error (una fraccion del total), no
sobre el conteo absoluto. Con trafico variable, un conteo de 100 errores es
malo a las 3 de la manana y es normal a las 11.

### Error budget

```yaml
error_budget:
  total_minutes: 43.8    # 0.1% de 30 dias
  consumed: 12.0
  remaining: 31.8
```

**Regla:** cuando el presupuesto de error esta consumido, se frena la
entrega de cambios y se prioriza la estabilidad. Es la unica forma de que el
SLO sea real.

## Alertas accionables

### La prueba

> **Si la alerta no dice que hacer, no es una alerta. Es un ruido con paging.**

```yaml
alerts:
  - name: TasaDeErrorAlta
    expr: |
      sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
      /
      sum(rate(http_requests_total[5m])) by (service)
      > 0.02
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "Tasa de error 5xx de {service} por encima del 2%"
      description: "El SLO de disponibilidad se va a romper. Revisar el dashboard de errores y el ultimo deploy."
      runbook: "https://runbooks.example.com/high-error-rate"
```

**Regla:** la anotacion dice que hacer y donde esta el runbook.

**Regla:** `for:` evita el flapping. Un pico de 30 segundos no deserve waking
up a alguien.

### Severidad

| Severidad | Que significa | Quien atiende |
|---|---|---|
| `critical` | El servicio esta caido o degradado | Inmediato, 24/7 |
| `warning` | SLO en riesgo, o sintoma temprano | Horario laboral |
| `info` | Informativo, se ve en el tablero | Nadie, se consulta |

**Regla:** las paginas solo las alertas `critical`. Si todo es critical, nada
es critical y el equipo se habitua a ignorar el paging.

## Anti-patrones

| Anti-patron | Consecuencia |
|---|---|
| Log de texto libre | No se puede filtrar por campo |
| Loggear la excepcion sin contexto | No se sabe que fallo ni donde |
| Loggear datos sensibles | Fuga de datos |
| `logger.error` para todo | El contador de errores no sirve |
| Labels con id de usuario | Explosion de cardinalidad |
| Labels con la ruta sin parametrizar | Una serie por request |
| `/health` que consulta la base | Outage en cascada |
| Confundir liveness con readiness | Reinicios innecesarios |
| Alerta por conteo absoluto | Falsa alarma con trafico variable |
| Alerta sin runbook | El paging no sirve para nada |
| Alerta sin `for:` | Flapping |
| Trazas sin propagar el trace id | Logs y trazas desconectados |
| Instrumentar antes de saber que se va a medir | Gasto sin pregunta que responder |

## Referencias

- `templates/logger.py` - implementacion de logging estructurado con correlation id
- `dev-kit-backend-stack` - donde se integra la instrumentacion
- `dev-kit-ci-cd` - el deploy que verifica la salud
