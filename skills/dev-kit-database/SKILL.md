---
name: dev-kit-database
description: "Modelado de datos, indices, migraciones, transacciones y aislamiento multi-tenant. CARGAR al disenar el modelo de datos de un proyecto, cuando una consulta va lenta, al agregar una migracion o cuando hay que decidir como separar datos de distintos clientes."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [database, sql, postgres, migrations, modeling, multi-tenant]
    category: software-development
    related_skills: [dev-kit-backend-stack, dev-kit-security, dev-kit-ci-cd, dev-kit-testing]
---

# Dev Kit - Database

> **Trigger:** "modelo de datos", "agregar una tabla", "la consulta va lenta",
> "migracion", "aislar datos de clientes", "N+1". Cargar cuando el dato es el
> problema.

## Que es esto

Los patrones de modelado y acceso a datos que sostienen un sistema en
produccion. No la teoria relacional: las decisiones concretas que se toman
una y otra vez y que hay que volver a tomar bien.

## La regla que gobierna todo

> **El modelo de datos es la parte del sistema que mas caro sale cambiar.**

Por eso se decide temprano, con la informacion que hay, y se cambia con
migraciones, no editando el schema a mano.

## Modelado

### Empezar por las entidades, no por las tablas

Antes de definir columnas, escribir las entidades del dominio y como se
relacionan. El diagrama de entidades va en el doc del modelo de datos.

| Pregunta | Por que importa |
|---|---|
| Que es una identidad (tiene id propio)? | No todo es una entidad |
| Que es un atributo y que es una entidad? | Un "cliente" guardado como texto no se puede consultar |
| Que atributos son opcionales de verdad? | `NULL` opcional != opcional de negocio |
| Que entidades nunca se borran? | Cambia el diseno del borrado |

### Normalizacion, con criterio

| Forma | Regla | Cuando |
|---|---|---|
| 1NF | Un valor por columna | Siempre |
| 2NF | Sin dependencias parciales de la clave compuesta | Si hay claves compuestas |
| 3NF | Sin dependencias transitivas | Default |
| Desnormalizacion | A proposito, con el costo anotado | Cuando se mesure el problema |

**Regla:** desnormalizar es una decision que se toma con una medicion, no con
intuicion. Si se desnormaliza, se anota en el doc del modelo por que y que
proceso mantiene la consistencia.

### Nombres

| Elemento | Convencion | Ejemplo |
|---|---|---|
| Tabla | `snake_case`, plural | `order_items` |
| Columna | `snake_case` | `created_at` |
| PK | `id` (o `<recurso>_id`) | `id` |
| FK | `<recurso>_id` | `customer_id` |
| Indice | `idx_<tabla>_<columnas>` | `idx_order_items_order_id` |
| Unique | `uq_<tabla>_<columnas>` | `uq_users_email` |
| Timestamps | `created_at`, `updated_at` | - |

**Regla:** toda tabla tiene `created_at`. Sin excepcion, salvo tablas de
asociacion puras.

**Regla:** los booleanos se llaman con afirmacion: `is_active`, `has_expired`,
`can_delete`. No `active`, `expired`.

### Tipo de columna

| Dato | Tipo | Nota |
|---|---|---|
| Texto | `text` | `varchar(n)` solo si el limite es una regla de negocio real |
| Entero | `integer` / `bigint` | `serial` solo si el ID no se importa de otro lado |
| Decimal | `numeric(12,2)` | **Nunca `float` para dinero** |
| Booleano | `boolean` | - |
| Fecha y hora | `timestamptz` | **Con zona horaria, siempre** |
| JSON | `jsonb` | Para datos estructurados que no se consultan |
| UUID | `uuid` | Cuando el ID se genera del lado del cliente |
| Dinero | `numeric` + `currency` (char 3) | - |

**Regla:** `timestamptz`, no `timestamp`. Un `timestamp` sin zona en un sistema
con equipos en distintas zonas es una bomba de reloj.

**Regla:** el dinero es `numeric`. Un `float` con operaciones acumuladas
introduce errores que aparecen en el cierre contable.

**Regla:** `jsonb` es para datos que no se filtran ni se agregan en SQL. Si
necesitas consultar un campo, es una columna.

### Claves foraneas y borrado

| Decision | Opcion | Consecuencia |
|---|---|---|
| FK con borrado | `ON DELETE CASCADE` | Se borra el hijo con el padre |
| FK con borrado | `ON DELETE SET NULL` | El hijo queda huerfano |
| FK con borrado | `ON DELETE RESTRICT` | Falla si hay hijos (default, explicito) |
| FK sin borrado | Sin accion | Falla siempre |

**Regla:** `ON DELETE` explicito en toda FK. El default de la base de datos
varia entre motores y versiones, y nadie recuerda cual es.

**Regla:** borrar en cascada solo cuando el hijo no tiene vida propia. Una
fila de historial que se borra en cascada con la transaccion es un bug.

## Indices

### Cuando indexar

| Indexar | No indexar |
|---|---|
| Columnas usadas en `WHERE` de consultas frecuentes | Columnas con muy pocos valores distintos (booleano) |
| Columnas de join | Columnas que se escriben mucho y no se leen |
| `ORDER BY` junto a `WHERE` | Todas las columnas |
| Llave foranea (para joins y cascadas) | - |

### Indices compuestos

El orden de las columnas importa: el indice `(a, b)` sirve para filtrar por
`a`, o por `a` y `b`. **No** sirve para filtrar solo por `b`.

**Regla:** el indice se crea en el orden en que se filtra: primero el criterio
mas selectivo.

**Regla:** un indice sobre una FK que no se usa en joins es solo costo de
escritura.

### Indices unicos y parciales

```sql
-- Unico: garantiza que no haya dos filas iguales
CREATE UNIQUE INDEX uq_users_email ON users (lower(email));

-- Parcial: solo indexa las filas que importan
CREATE INDEX idx_orders_pending ON orders (created_at)
WHERE status = 'pending';
```

El indice parcial es el indice correcto cuando solo una fraccion de las filas
se consulta en caliente.

## Consultas

### N+1

El problema mas comun de performance en backend.

```python
# MAL: 1 query + N queries
orders = session.query(Order).all()
for order in orders:
    order.customer_name = session.query(Customer).get(order.customer_id).name  # N queries

# BIEN: 1 query con join
orders = session.query(Order).join(Customer).all()
```

**Como se detecta:** mirar el log de queries. Si el numero de queries crece
con el numero de filas, hay N+1.

**Como se previene:** cargar las relaciones de forma explicita (`joinedload`,
`selectinload`) segun el caso de uso. `joinedload` para relaciones uno-a-uno
y muchas-a-uno. `selectinload` para uno-a-muchos, porque el join con
colecciones multiplica filas.

### Paginacion

```python
# Con offset: simple, pero la pagina N es lenta si hay muchas filas
query.offset(10000).limit(20)

# Con cursor: escala, pero necesita un orden estable
query.filter(Order.id < last_id).order_by(Order.id.desc()).limit(20)
```

**Regla:** usar offset hasta que el volumen lo JUSTifique. Cursor cuando la
tabla crece y la pagina profunda se usa de verdad.

**Regla:** el `ORDER BY` de una consulta paginada debe ser determinista. Sin
una columna de desempate, dos filas con el mismo valor pueden aparecer en
paginas distintas y aparecer duplicadas.

**Regla:** el limite maximo de pagina es obligatorio. Sin tope, un cliente
pide `?limit=1000000`.

### Transacciones

```python
with session.begin():
    order = Order(...)
    session.add(order)
    session.flush()          # fuerza el INSERT para obtener el id
    session.add(OrderItem(order_id=order.id, ...))
```

**Regla:** la transaccion es la unidad de negocio, no la unidad de codigo.
Si una operacion necesita dos escrituras, van en la misma transaccion o en
ninguna.

**Regla:** la transaccion no cruza una llamada a un servicio externo. Un
`await` a una API dentro de una transaccion mantiene los locks abiertos
durante la latencia de la red.

**Regla:** `flush()` y `commit()` son distintos. `flush` escribe en la sesion
y hace disponible el id; `commit` confirma. Confundirlos produce el error
clasico de "objeto no associated with an active session".

## Migraciones

### Reglas

| Regla | Por que |
|---|---|
| Toda migracion tiene su reversa | Sin rollback, un deploy fallido deja el schema inconsistente |
| Una migracion, un cambio | Dos cambios en una se revierten juntos y mal |
| Las migraciones son append-only | Editar una ya aplicada rompe el estado de los demas |
| Nunca edites datos a mano en produccion | Queda fuera del historial y del rollback |
| Los cambios de datos grandes van en batches | Un `UPDATE` masivo bloquea |

### Agregar una columna

```sql
-- 1. Agregar nullable
ALTER TABLE orders ADD COLUMN channel text;

-- 2. Backfill por batches
UPDATE orders SET channel = 'web' WHERE channel IS NULL AND id BETWEEN 1 AND 10000;

-- 3. Poner el default y volver NOT NULL
ALTER TABLE orders ALTER COLUMN channel SET DEFAULT 'web';
ALTER TABLE orders ALTER COLUMN channel SET NOT NULL;
```

**Regla:** agregar la columna nullable, hacer el backfill por batches, y solo
despues volverla `NOT NULL`. En tres pasos, no en uno.

### Locks

| Operacion | Lock |
|---|---|
| `CREATE INDEX` (sin `CONCURRENTLY`) | Bloquea escrituras |
| `CREATE INDEX CONCURRENTLY` | No bloquea escrituras, pero no va dentro de una transaccion |
| `ALTER TABLE ... ADD COLUMN` con default no volátil | Reescribe la tabla en versiones viejas |
| `ALTER TABLE ... ADD COLUMN` sin default | Metadata solamente, instantanea |

**Regla:** toda migracion sobre tabla de produccion con datos se prueba
primero contra una copia con volumen realista. El tiempo de bloqueo escala
con el tamaño de la tabla.

## Aislamiento multi-tenant

Tres estrategias, con su costo real.

| Estrategia | Aislamiento | Costo | Cuando |
|---|---|---|---|
| **Schema por tenant** | Alto | Un schema por tenant: migraciones N veces, conexiones por tenant | Pocos tenants grandes, requisitos fuertes de aislamiento |
| **Tabla por tenant** | Muy alto | Tablas por tenant: queries dinamicas, mantenimiento | Muy pocos tenants |
| **Row-level security** | Medio (fila) | Policy en la base, un solo schema | Muchos tenants, el default razonable |

### Row-level security: la opcion por defecto

```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.tenant_id')::uuid);

CREATE POLICY tenant_isolation_write ON orders
  FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
```

```python
# La sesion DEBE fijar el tenant antes de cualquier query
session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": tenant_id})
```

**Regla dura:** `SET LOCAL` dentro de una transaccion. Con `SET` (sin `LOCAL`)
el valor se mantiene entre transacciones y una consulta sin tenant definido
ve datos de otro tenant.

**Regla:** la policy de `INSERT` con `WITH CHECK` es obligatoria. Sin ella, un
tenant puede insertar filas con el `tenant_id` de otro.

**Regla:** el filtro por tenant se aplica en la base, no en el codigo. Un
`WHERE tenant_id = ?` en la aplicacion se olvida; la policy no se olvida.

**Por que importa:** el error de aislamiento entre tenants es el peor error
posible en un producto multi-cliente. No se detecta en QA, se detecta en un
ticket del cliente.

## Anti-patrones

| Anti-patron | Consecuencia |
|---|---|
| `float` para dinero | Errores de redondeo en el cierre |
| `timestamp` sin zona horaria | Datos incoherentes entre equipos |
| Editar migraciones ya aplicadas | El estado del schema deja de ser reproducible |
| Migracion sin reversa | Un deploy fallido no se puede revertir |
| `UPDATE` masivo en una transaccion | Bloquea la tabla por minutos |
| `jsonb` para datos que se consultan | No se puede indexar ni agregar en SQL |
| FK sin `ON DELETE` explicito | Comportamiento distinto entre entornos |
| Filtro por tenant en el codigo | Un `WHERE` olvidado y datos cruzados |
| `SET` sin `LOCAL` para el tenant | Fuga de datos entre transacciones |
| N+1 en listados | El endpoint escala al reves del numero de filas |
| Indice en columnas que no se leen | Costo de escritura sin beneficio |
| `limit` sin tope maximo | Un cliente pide un millon de filas |
| `ORDER BY` no determinista en paginacion | Filas duplicadas o perdidas entre paginas |

## Referencias

- `templates/schema-review.md` - checklist de revision de un modelo de datos
- `references/migraciones.md` - playbook de migraciones seguras
- `references/multi-tenant.md` - comparacion detallada de estrategias de aislamiento
