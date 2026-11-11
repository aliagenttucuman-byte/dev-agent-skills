# Migraciones seguras

Playbook de migraciones: como cambiar el schema en produccion sin romper
nada y sin dejar el schema en un estado que nadie puede revertir.

---

## La regla

> **Una migracion sin reversa no es una migracion. Es un cambio irreversible
> disfrazado de script.**

Toda migracion tiene su funcion de reversa, probada, antes de aplicarse.

---

## Los cinco pasos de una migracion de columna

### 1. Agregar la columna, nullable, sin default

```sql
ALTER TABLE orders ADD COLUMN channel text;
```

Instantanea: solo metadata. No reescribe la tabla.

### 2. Backfill por batches

```sql
DO $$
DECLARE
  batch_size integer := 10000;
  last_id bigint := 0;
  updated integer;
BEGIN
  LOOP
    UPDATE orders
    SET channel = 'web'
    WHERE id > last_id
      AND id <= last_id + batch_size
      AND channel IS NULL;

    GET DIAGNOSTICS updated = ROW_COUNT;
    last_id := last_id + batch_size;
    EXIT WHEN updated = 0;
    PERFORM pg_sleep(0.1);   -- respiro entre batches
  END LOOP;
END $$;
```

**Por que el `pg_sleep`:** entre batches se le da chance a la base de atender
otros workloads. Un backfill continuo monopoliza los locks.

**Por que el `id > last_id`:** el indice por `id` hace que cada batch toque
pocas filas, en vez de re-escanear la tabla entera.

### 3. Verificar que no quedan nulls

```sql
SELECT count(*) FROM orders WHERE channel IS NULL;
```

Debe dar 0. Si no lo da, el backfill no termino: no seguir.

### 4. Poner el default

```sql
ALTER TABLE orders ALTER COLUMN channel SET DEFAULT 'web';
```

A partir de aca, las inserciones nuevas ya traen el valor.

### 5. Volver NOT NULL

```sql
ALTER TABLE orders ALTER COLUMN channel SET NOT NULL;
```

**Regla:** este paso bloquea la tabla mientras valida. Con volumen grande, se
hace en ventana de mantenimiento o con `NOT VALID` + `VALIDATE CONSTRAINT`
(que no bloquea escrituras).

---

## Agregar un indice

| Situacion | Comando | Bloquea escrituras |
|---|---|---|
| Tabla chica, sin trafico | `CREATE INDEX` | Si, breve |
| Tabla grande, con trafico | `CREATE INDEX CONCURRENTLY` | No |
| Dentro de una transaccion | `CREATE INDEX` | - |

**Regla:** `CREATE INDEX CONCURRENTLY` **no puede** ir dentro de una
transaccion. En algunos motores aborta la transaccion entera.

**Regla:** verificar que el indice se creo de verdad:

```sql
SELECT indexname FROM pg_indexes WHERE tablename = 'orders';
```

Un `CONCURRENTLY` que falla deja un indice invalido que ocupa espacio y no se
usa. Hay que detectarlo y reconstruirlo.

---

## Renombrar algo

Renombrar una columna o tabla rompe el codigo que la usa. Tres opciones, de
menos a mas invasiva:

| Opcion | Como | Riesgo |
|---|---|---|
| Expandir y migrar | Agregar la columna nueva, copiar, cambiar el codigo, borrar la vieja | Bajo, pero ocupa espacio duplicado |
| Compatibilidad dual | La API acepta ambos nombres durante un tiempo | Medio, complica el codigo |
| Renombrar de una | `ALTER TABLE ... RENAME` | Alto, rompe todo lo que no se actualice en el mismo deploy |

**Regla:** para cambios de API, expandir y migrar. Es la unica opcion que
permite hacer deploy del codigo y del schema por separado.

---

## Borrar una columna

Tres pasos separados por deploys:

1. Deploy 1: dejar de usar la columna en el codigo.
2. Esperar el tiempo maximo de rollback de los deploys anteriores.
3. Deploy 2: `ALTER TABLE ... DROP COLUMN`.

**Regla:** borrar la columna en el mismo deploy que deja de usarla no deja
margen para rollback.

---

## Migraciones que no se pueden deshacer

Algunas operaciones son irreversibles: borrar datos, transformar un tipo que
pierde informacion, agregar una constraint que invalida filas existentes.

**Protocolo:**
1. Snapshot de los datos afectados antes de la migracion.
2. Migracion que valida datos **antes** de aplicar el cambio.
3. Migracion del cambio.
4. Verificacion posterior.

**Regla:** una migracion irreversible se ejecuta con el snapshot verificado
disponible, no con la esperanza de que no haga falta.

---

## Validacion previa

```sql
-- Constraint que todavia no se valida
ALTER TABLE orders ADD CONSTRAINT chk_amount_positive
  CHECK (amount > 0) NOT VALID;

-- Valida sin bloquear escrituras
ALTER TABLE orders VALIDATE CONSTRAINT chk_amount_positive;
```

`NOT VALID` + `VALIDATE CONSTRAINT` es el patron para agregar constraints a
tablas grandes con trafico.

---

## Checklist de aplicacion

- [ ] La migracion tiene su reversa probada
- [ ] Se midio el tiempo sobre una copia con volumen realista
- [ ] Los locks que toma estan identificados
- [ ] La ventana de aplicacion esta definida
- [ ] El snapshot de datos esta disponible (si la migracion es irreversible)
- [ ] Hay un comando de verificacion post-migracion
- [ ] El comando de rollback esta escrito y probado

## Referencias

- `dev-kit-database/templates/schema-review.md` - revision del modelo
- `dev-kit-database/references/multi-tenant.md` - estrategias de aislamiento
