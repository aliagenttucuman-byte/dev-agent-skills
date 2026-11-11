# Convenciones de API: endpoints, codigos de estado, paginacion e idempotencia

Referencia de contrato para los endpoints de una API REST. Complementa la
seccion de endpoints de `SKILL.md`.

---

## 1. Forma de una URL

```
/api/v1/{recurso}[/{id}][/{sub-recurso}[/{sub-id}]]
```

| Regla | Ejemplo bien | Ejemplo mal |
|---|---|---|
| Sustantivo en plural | `/api/v1/orders` | `/api/v1/order` |
| Verbo solo en la accion no estandar | `POST /api/v1/orders/{id}/cancel` | `POST /api/v1/cancelOrder` |
| Identificador en el path | `GET /api/v1/orders/{order_id}` | `GET /api/v1/getOrder?id=...` |
| Filtros como query | `GET /api/v1/orders?status=pending` | `GET /api/v1/ordersByStatus/pending` |
| Version en el prefijo | `/api/v1/...` | version en el header |
| Anidado maximo dos niveles | `/orders/{id}/items/{item_id}` | `/a/{x}/b/{y}/c/{z}` |

**Regla de anidamiento:** un sub-recurso se anida solo si no existe sin el padre.
Si `/items` se puede consultar por su cuenta, va en `/items`, no en
`/orders/{id}/items`.

---

## 2. Codigos de estado

| Codigo | Cuando se usa | Body |
|---|---|---|
| 200 | Lectura exitosa, o actualizacion sin recurso nuevo | recurso o `null` |
| 201 | Creacion exitosa | recurso creado + header `Location` |
| 202 | Aceptado para procesamiento asincrono | identificador del trabajo |
| 204 | Borrado exitoso, o actualizacion sin contenido | vacio |
| 400 | Error de dominio o peticion malformada | `{"error": {...}}` |
| 401 | Sin credenciales validas | `{"error": {"type": "unauthenticated"}}` |
| 403 | Autenticado pero sin permisos | `{"error": {"type": "forbidden"}}` |
| 404 | Recurso inexistente | `{"error": {"type": "not_found"}}` |
| 409 | Conflicto de estado | `{"error": {"type": "conflict"}}` |
| 422 | Fallo de validacion de esquema | lista de problemas por campo |
| 429 | Rate limit excedido | `{"error": {...}}` + header `Retry-After` |
| 500 | Error inesperado | `{"error": {"type": "internal_error"}}` |

**Regla:** el cliente decide que hacer mirando **solo** el codigo y el campo
`error.type`. Si necesita leer el mensaje para decidir, el contrato esta roto.

---

## 3. Formato de error

```json
{
  "error": {
    "type": "order_status_conflict",
    "message": "El pedido no se puede confirmar en estado 'shipped'.",
    "details": [
      {"field": "status", "issue": "transicion no permitida"}
    ],
    "correlation_id": "req-01H..."
  }
}
```

| Campo | Obligatorio | Contenido |
|---|---|---|
| `type` | si | Identificador estable del tipo de error, en notacion `snake_case` |
| `message` | si | Texto para humanos, sin datos internos |
| `details` | no | Lista de problemas, util en 422 |
| `correlation_id` | si en produccion | Permite correlacionar con el log |

**Regla:** `type` es estable y documentado. Cambiarlo rompe a los clientes.
`message` puede cambiar: es para humanos.

---

## 4. Paginacion

### Por cursor (recomendada para listados que cambian)

```http
GET /api/v1/orders?limit=50&cursor=eyJpZCI6IjAxSD...
```

```json
{
  "data": [...],
  "page": {
    "next_cursor": "eyJpZCI6IjAxSD...",
    "has_more": true
  }
}
```

| Regla | Motivo |
|---|---|
| `limit` con maximo duro (100) | El cliente no puede pedir 100000 filas |
| Cursor opaco (base64 de un token) | El cliente no depende del orden interno |
| El cursor incluye el criterio de orden | Un cursor de otra consulta no aplica |
| Sin `offset` en listados grandes | El offset se ralentiza con la tabla |

### Por offset (solo para paginacion de UI con numero de pagina)

```http
GET /api/v1/orders?limit=50&offset=100
```

**Regla:** offset solo cuando el total importa y el volumen es acotado. En
listados grandes, el offset degrada la consulta y salta registros cuando hay
inserciones.

---

## 5. Idempotencia

Toda operacion de creacion con efecto externo (cobro, envio, email) necesita
poder repetirse sin duplicar el efecto.

```http
POST /api/v1/orders
Idempotency-Key: 8f14e45f-ceea-467a-9c8a-1b2c3d4e5f60
```

```python
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    response: Response,
    request: Request,
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    """Crea un pedido de forma idempotente."""
    key = request.headers.get("Idempotency-Key")
    if key is None:
        raise MissingIdempotencyKey()
    cached = await idempotency_store.get(key)
    if cached is not None:
        response.status_code = status.HTTP_200_OK
        return cached
    order = service.create(OrderDraft.from_schema(payload))
    await idempotency_store.put(key, order, ttl=86400)
    return OrderRead.model_validate(order)
```

| Regla | Motivo |
|---|---|
| La clave la genera el cliente | El servidor no puede adivinar la intencion |
| Se guarda el resultado, no solo el estado | Un reintento devuelve la misma respuesta |
| TTL acotado (24 horas) | El store no crece infinito |
| La clave se asocia al cliente | Un cliente no puede leer el resultado de otro |
| Se rechaza una clave con payload distinto | Detecta uso incorrecto de la clave |

---

## 6. Versionado

| Mecanismo | Cuándo | Ventaja | Costo |
|---|---|---|---|
| Path (`/api/v1`) | Default del proyecto | Claro en logs y en el navegador | Rutas duplicadas |
| Header | APIs publicas | La URL no cambia | Invisible en el navegador |
| Query | Formas simples | Simple | Se olvida en un parametro |

**Regla:** el versionado es por version mayor de contrato. Un cambio compatible
(agregar un campo opcional) **no** requiere version nueva. Un cambio incompatible
(eliminar un campo, cambiar el tipo) requiere version nueva y un periodo de
soporte en paralelo.

---

## 7. Autenticacion y autorizacion

| Mecanismo | Uso | Donde se verifica |
|---|---|---|
| Token JWT (Bearer) | API stateless | Middleware o dependencia |
| Token opaco | API con revocacion | Middleware o dependencia |
| Cookie de sesion | Aplicacion web | Middleware |
| API key | Integraciones servidor a servidor | Dependencia |

```python
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    """Resuelve el usuario autenticado o responde 401."""
    payload = token_service.decode(credentials.credentials)
    user = session.get(UserModel, payload.subject)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="unauthenticated")
    return user
```

**Regla:** la autorizacion por recurso (este usuario puede tocar este pedido)
se verifica **dentro** del caso de uso o en una dependencia que recibe el recurso
ya cargado. Nunca se decide en el frontend.

---

## 8. Versionado del contrato y OpenAPI

```bash
# generar el spec desde el codigo
python -m scripts.export_openapi > docs/openapi.json

# validar que no hay cambios incompatibles contra la version publicada
python -m scripts.check_openapi_compat docs/openapi.json baseline/openapi.json
```

El spec se **genera**, nunca se edita a mano. El pipeline lo publica y el
frontend lo consume como contrato.

---

## 9. Cabeceras de respuesta

| Cabecera | Cuando | Ejemplo |
|---|---|---|
| `Location` | 201 | `/api/v1/orders/abc-123` |
| `Retry-After` | 429 y 503 | `30` |
| `X-Correlation-Id` | Toda respuesta | `req-01H...` |
| `ETag` | Recurso cacheable | `"v3-8f2a"` |
| `RateLimit-Limit` / `RateLimit-Remaining` | Con rate limit | `60`, `42` |

**Regla:** `X-Correlation-Id` viaja en toda respuesta. Es lo que permite unir el
log del servidor con la queja del usuario.
