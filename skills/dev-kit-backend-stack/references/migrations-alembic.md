# Migraciones Alembic: flujo operativo y casos que rompen en produccion

Guia de detalle para el manejo de migraciones en un backend con SQLAlchemy.
Complementa la seccion de migraciones de `SKILL.md`.

---

## 1. Ciclo de vida de una migracion

```
1. Modificar el modelo en el codigo
2. alembic revision -m "descripcion"
3. alembic upgrade head        # en base local, SIEMPRE antes de push
4. pytest -q                  # la migracion no rompe los tests
5. push                       # el pipeline aplica la migracion
```

El orden importa: **el modelo cambia y la migracion se genera en el mismo
commit**. Un modelo sin migracion deja la base desincronizada; una migracion sin
modelo deja columnas huerfanas.

---

## 2. Estructura de una migracion

```python
# migrations/versions/0002_add_order_status_index.py
"""add order status index

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-15
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Aplica el cambio."""
    op.create_index(
        "ix_orders_status",
        "orders",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Revierte el cambio."""
    op.drop_index("ix_orders_status", table_name="orders")
```

| Regla | Motivo |
|---|---|
| `revision` es un id corto y legible | El historial se lee |
| `down_revision` apunta al anterior | Alembic arma el grafo |
| `upgrade` y `downgrade` siempre | Sin vuelta atras, un error de despliegue no se revierte |
| `op.*` en vez de SQL crudo | Alembic puede dialectos distintos |
| Nunca editar una migracion aplicada | El historial debe ser inmutable |

---

## 3. Operaciones comunes

### Crear tabla

```python
def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("total_amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
```

### Agregar columna con default

```python
def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("channel", sa.String(length=32), nullable=True),
    )
```

Agregar una columna `NOT NULL` sin default a una tabla grande reescribe la tabla
entera. El camino seguro en tres pasos:

```python
# Paso 1 (migracion A): agregar nullable
op.add_column("orders", sa.Column("channel", sa.String(length=32), nullable=True))

# Paso 2: despliegue del codigo que escribe en la columna nueva

# Paso 3 (migracion B, dias despues): volver NOT NULL
op.alter_column("orders", "channel", nullable=False)
```

### Renombrar columna

Renombrar y renombrar al reves se pierde informacion. Alembic lo pide
explicitamente:

```python
def upgrade() -> None:
    op.alter_column("orders", "total", new_column_name="total_amount")
    op.alter_column("orders", "total_amount", type_=sa.Integer())
```

### Cambiar tipo

```python
def upgrade() -> None:
    op.alter_column(
        "orders",
        "total_amount",
        type_=sa.Numeric(precision=12, scale=2),
        existing_type=sa.Integer(),
        postgresql_using="total_amount::numeric",
    )
```

El `postgresql_using` es obligatorio cuando la conversion no es implicita. Sin
el, la migracion falla en PostgreSQL con un error de tipo.

---

## 4. Migraciones que no bloquean

Una migracion que toma un lock de escritura sobre una tabla grande corta el
servicio durante el despliegue. Estas son las tres que hay que evitar:

| Operacion | Problema | Alternativa sin lock |
|---|---|---|
| `ALTER TABLE ... ADD COLUMN NOT NULL DEFAULT x` | Reescribe la tabla | Agregar nullable, luego default en dos pasos |
| `ALTER TABLE ... ALTER COLUMN TYPE` | Reescribe la tabla | Columna nueva + migracion de datos + drop |
| `CREATE INDEX` sin `CONCURRENTLY` | Lock de escritura | `CREATE INDEX CONCURRENTLY` (fuera de transaccion) |

```python
# Indice concurrente: requiere autocommit, Alembic lo maneja con autocommit_block()
from alembic import op
from contextlib import contextmanager


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("CREATE INDEX CONCURRENTLY ix_orders_status ON orders (status)")
```

**Regla:** toda migracion que toque una tabla grande se ensaya con el volumen
real antes de llegar a produccion. El tiempo de lock se multiplica por el
numero de filas.

---

## 5. Migraciones de datos

Cuando hay que mover datos, la migracion hace **solo** la transformacion
estructural. La logica de negocio complexa va en un script de datos con version
propia.

```python
def upgrade() -> None:
    # Cambio estructural: un solo paso, reversible.
    op.add_column("orders", sa.Column("total_amount", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE orders SET total_amount = CAST(total_cents AS INTEGER) WHERE total_cents IS NOT NULL"
    )
    op.alter_column("orders", "total_amount", nullable=False)
```

Reglas para migraciones de datos:

| Regla | Motivo |
|---|---|
| Idempotentes | Una migracion reintentada no debe duplicar datos |
| En bloques acotados si la tabla es grande | Evita transacciones largas |
| Con `WHERE` sobre el subconjunto no migrado | Permite reintentar |
| Con backup verificado antes | El `downgrade` no restaura datos perdidos |
| Con contador de avance | Para saber cuanto falta |

---

## 6. El gate del pipeline

El pipeline de despliegue tiene que garantizar que el esquema esta en la version
esperada antes de que corra el codigo nuevo.

```bash
# 1. Estado actual de la base
alembic current

# 2. Aplicar migraciones pendientes
alembic upgrade head

# 3. Verificar que no quedo ninguna pendiente
alembic current
alembic heads
```

**Regla de despliegue:** el codigo que depende de una columna nueva se despliega
**despues** de la migracion que crea la columna. Y el codigo que todavia escribe
en la columna vieja se retira **despues** de que todos los clientes esten en la
version nueva. Ese es el patron *expand and contract*:

```
Fase 1 (expand)   -> agregar columna nueva, nullable, con default
Fase 2 (migrate)  -> desplegar codigo que escribe en ambas
Fase 3 (backfill) -> migrar los datos historicos
Fase 4 (contract) -> quitar la columna vieja
```

Cada fase es un despliegue independiente y reversible.

---

## 7. Errores que rompen produccion

| Error | Sintoma | Prevencion |
|---|---|---|
| Editar una migracion aplicada | `alembic` no reconoce el historial | Migraciones inmutables |
| `downgrade` que pierde datos | La reversa no restaura | Backfill antes de borrar |
| Indice faltante en una columna muy consultada | Consulta lenta en produccion | Indice en la migracion, no despues |
| `NOT NULL` en tabla grande | Lock de escritura | Nullable primero, `NOT NULL` despues |
| `create_all()` usado en produccion | El esquema real difiere del del repo | Solo Alembic |
| Migracion aplicada a mano | El historial local y el remoto divergen | Nunca `alembic stamp` a mano |
| Enumeracion nueva en el codigo sin migracion | La base rechaza el valor | Migracion primero, codigo despues |

---

## 8. Multiples entornos

| Entorno | Como se aplica | Quien la aplica |
|---|---|---|
| Local | `alembic upgrade head` a mano | El desarrollador |
| CI | Base efimera, se migra y se prueba | El pipeline |
| Staging | `alembic upgrade head` en el deploy | El pipeline |
| Produccion | `alembic upgrade head` en el deploy | El pipeline, con backup previo |

**Regla:** la migracion se aplica **siempre** con el mismo comando y desde el
mismo pipeline. Un paso manual en produccion es un paso que se olvida.

---

## 9. Verificacion local de una migracion

```bash
# Aplicar y revertir en cadena
alembic upgrade head
alembic downgrade base

# Ver el SQL que genera, sin aplicarlo
alembic upgrade head --sql

# Ver el historial
alembic history --verbose
alembic current

# Detectar divergencia entre modelos y migraciones
alembic check
```

`alembic check` es el comando clave: detecta si el modelo en el codigo tiene
cambios que ninguna migracionTodavia refleja. Corre en el pipeline antes de
construir la imagen.
