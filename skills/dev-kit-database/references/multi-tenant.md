# Aislamiento multi-tenant

Comparacion detallada de las tres estrategias, con lo que cada una cuesta de
verdad.

---

## El problema

Un sistema que sirve a mas de un cliente. El dato de un cliente no puede
llegar a otro. Este es el peor tipo de bug posible en un producto
multi-cliente: no se detecta en QA, se detecta en un ticket del cliente, y
arruina la confianza.

---

## Las tres estrategias

### 1. Schema por tenant

Cada tenant tiene su propio schema dentro de la misma base.

```
public
├── tenant_a
│   ├── orders
│   └── customers
└── tenant_b
    ├── orders
    └── customers
```

| Aspecto | Comportamiento |
|---|---|
| Aislamiento | Alto. Cada consulta toca un solo schema |
| Migraciones | Se ejecutan N veces, una por schema |
| Conexiones | El `search_path` cambia por tenant |
| Consultas entre tenants | Imposibles sin federacion |
| Complejidad | Media: el pool de conexiones debe ser por schema |
| Riesgo principal | Olvidar cambiar el `search_path` y consultar el schema equivocado |

**Cuando:** pocos tenants (decenas), requisitos de aislamiento fuertes,
clientes que piden compliance estricto.

### 2. Tabla por tenant

Cada tenant tiene sus propias tablas.

```
orders_tenant_a
orders_tenant_b
```

| Aspecto | Comportamiento |
|---|---|
| Aislamiento | Muy alto. Las tablas ni se ven entre si |
| Migraciones | Se ejecutan N veces, una por tabla |
| Consultas entre tenants | Imposibles |
| Complejidad | Alta: los nombres de tabla son dinamicos |
| Riesgo principal | Inyeccion de identificadores si el nombre de tabla se construye sin validacion |

**Cuando:** muy pocos tenants (unidades de negocio distintas que no comparten
datos), o cuando el aislamiento tiene que ser absoluto.

### 3. Row-level security (RLS)

Un solo schema, una columna `tenant_id` en cada tabla, y la base de datos
filtra.

```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_read ON orders
  FOR SELECT
  USING (tenant_id = current_setting('app.tenant_id')::uuid);

CREATE POLICY tenant_write ON orders
  FOR INSERT
  WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);

CREATE POLICY tenant_update ON orders
  FOR UPDATE
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

| Aspecto | Comportamiento |
|---|---|
| Aislamiento | A nivel de fila, aplicado por la base |
| Migraciones | Una vez, para todos |
| Conexiones | Una sola, con el tenant fijado por transaccion |
| Consultas entre tenants | Posibles (con una policy distinta) |
| Complejidad | Baja en el schema, media en la aplicacion |
| Riesgo principal | No fijar el tenant en la sesion |

**Cuando:** muchos tenants, es el default razonable.

---

## Comparacion

| Criterio | Schema por tenant | Tabla por tenant | RLS |
|---|---|---|---|
| Numero de tenants | Decenas | Muy pocos | Cientos o mas |
| Aislamiento | Alto | Muy alto | Medio (fila) |
| Costo de migracion | N veces | N veces | 1 vez |
| Costo de queries | 1 (con indice) | 1 | 1 |
| Complejidad de codigo | Media | Alta | Media |
| Consultas cross-tenant | No | No | Si |
| Riesgo de fuga | `search_path` | Nombre de tabla | Tenant no fijado |

---

## Implementar RLS correctamente

### Fijar el tenant

```python
from sqlalchemy import text

def set_tenant(session, tenant_id: str) -> None:
    session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": tenant_id})
```

**`SET LOCAL`, nunca `SET`.**

| | `SET LOCAL` | `SET` |
|---|---|---|
| Alcance | La transaccion actual | Toda la sesion |
| Al hacer commit | Se pierde | Persiste |
| Riesgo | Bajo | Una query sin tenant ve datos de otro |

**Con `SET`, si una transaccion termina sin fijar el tenant (por ejemplo,
un error antes del `SET`), la sesion queda con el tenant anterior.** La
siguiente query de otra peticion ve datos ajenos. Es un bug de seguridad
difícil de reproducir.

### El patron completo

```python
def handle_request(tenant_id: str, request):
    with session.begin():
        session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": tenant_id})
        # ... toda la logica de la peticion dentro de la transaccion
        result = do_work(session)
    return result
```

**Regla:** toda la logica que toca datos del tenant va dentro de la
transaccion donde se fijo `SET LOCAL`.

### La policy de INSERT

```sql
CREATE POLICY tenant_write ON orders
  FOR INSERT
  WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
```

**Sin `WITH CHECK`, un tenant puede insertar filas con el `tenant_id` de
otro.** La policy de `SELECT` filtra la lectura, pero no la escritura: la
fila se inserta y queda invisible para su proprio tenant (y visible para el
dueno, que tampoco deberia verla).

### Role de la aplicacion

La policy se aplica al rol que usa la aplicacion. Si el rol tiene
`BYPASSRLS` o es superusuario, las policies no aplican.

**Regla:** la aplicacion se conecta con un rol sin privilegios de superusuario
y sin `BYPASSRLS`.

### Indices

Con RLS, la policy agrega `tenant_id = ?` a cada query. El indice debe
incluir `tenant_id` al principio para que la fila se ubique rapido:

```sql
CREATE INDEX idx_orders_tenant_created ON orders (tenant_id, created_at DESC);
```

---

## Verificar que el aislamiento funciona

El test que no puede faltar:

```python
def test_tenant_cannot_read_other_tenant_data(session):
    with session.begin():
        session.execute(text("SET LOCAL app.tenant_id = :t"), {"t": TENANT_A})
        session.add(Order(tenant_id=TENANT_A, amount=100))

    with session.begin():
        session.execute(text("SET LOCAL app.tenant_id = :t"), {"t": TENANT_B})
        orders = session.query(Order).all()
        assert len(orders) == 0, "El tenant B ve datos del tenant A"
```

**Regla:** este test corre en la pipeline, no solo en QA. Es el unico que
detecta una fuga antes de que la detecte el cliente.

**Regla:** el test de lectura no es suficiente. Hace falta tambien el de
escritura:

```python
def test_tenant_cannot_write_for_other_tenant(session):
    with session.begin():
        session.execute(text("SET LOCAL app.tenant_id = :t"), {"t": TENANT_B})
        session.add(Order(tenant_id=TENANT_A, amount=100))
        # debe fallar con violation de la policy
```

---

## La regla de oro

> **El filtro por tenant se aplica en la base de datos, nunca en el codigo de
> la aplicacion.**

Un `WHERE tenant_id = ?` en la aplicacion se olvida en un endpoint nuevo. Una
policy de la base no se olvida: aplica a todas las consultas, incluidas las
que no existen todavia.

El filtro en el codigo puede ser una capa de defense adicional, pero nunca la
unica.

---

## Anti-patrones

| Anti-patron | Consecuencia |
|---|---|
| `SET` en vez de `SET LOCAL` | Tenant previo persiste en la sesion |
| Policy sin `WITH CHECK` en INSERT | Escritura cruzada entre tenants |
| Rol de la app con `BYPASSRLS` | Las policies no aplican |
| Filtro por tenant solo en el codigo | Un endpoint nuevo lo olvida |
| `tenant_id` sin indice | La policy vuelve cada query lenta |
| Sin test de aislamiento en la pipeline | La fuga se detecta tarde |
| Nombre de tabla construido con input del usuario | Inyeccion de identificadores |
| `search_path` como variable de sesion | Query contra el schema equivocado |

## Referencias

- `dev-kit-database/templates/schema-review.md` - revision del modelo
- `dev-kit-database/references/migraciones.md` - migraciones seguras
