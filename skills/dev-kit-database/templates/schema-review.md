# Checklist de revision de modelo de datos

> Referencia de `dev-kit-database`. Para revisar un modelo antes de
> implementarlo o antes de una migracion.

## Entidades y relaciones

- [ ] El diagrama de entidades esta escrito y es la fuente de verdad
- [ ] Cada entidad tiene su identidad y su clave primaria
- [ ] Las relaciones many-to-many tienen tabla de asociacion
- [ ] Se documento que entidades son agregados (se cargan y guardan juntas)

## Columnas

- [ ] Toda columna tiene tipo explicito, no hay depender del default
- [ ] El dinero es `numeric`, nunca `float`
- [ ] Las fechas usan `timestamptz`
- [ ] Las columnas booleanas se llaman con afirmacion (`is_`, `has_`, `can_`)
- [ ] Las columnas de texto que en realidad son enums usan `text` + `CHECK`
- [ ] `jsonb` solo para datos que no se consultan ni se agregan en SQL
- [ ] Toda columna tiene una regla de null que refleja la regla de negocio

## Tablas

- [ ] Toda tabla tiene `created_at`
- [ ] Las tablas que se actualizan tienen `updated_at`
- [ ] Los nombres siguen la convencion (`snake_case`, plural)
- [ ] Las tablas de asociacion tienen su clave compuesta definida

## Relaciones

- [ ] Toda FK declara su `ON DELETE` de forma explicita
- [ ] Las cascadas solo se usan donde el hijo no tiene vida propia
- [ ] Los indices existen sobre las FK que se usan en joins
- [ ] No hay FK entre tablas que se borran juntas (usar junction table)

## Indices

- [ ] Cada indice tiene una justificacion (la consulta que lo necesita)
- [ ] Los indices compuestos estan ordenados por selectividad
- [ ] Los indices unicos Sonn los que deben ser unicos
- [ ] Los indices parciales cubren solo las filas que se consultan en caliente
- [ ] No hay indice sobre una columna que nunca se filtra

## Consultas

- [ ] Las consultas frecuentes tienen indice que las cubre
- [ ] No hay N+1 en los listados
- [ ] La paginacion aplica el limite en la base de datos
- [ ] El `ORDER BY` de una consulta paginada es determinista
- [ ] El limite maximo de pagina esta definido y se aplica

## Transacciones

- [ ] Las operaciones multi-escritura estan en una transaccion
- [ ] Las transacciones no cruzan llamadas a servicios externos
- [ ] Se usa `flush()` cuando se necesita el id antes del commit
- [ ] El nivel de aislamiento es el que corresponde al caso de uso

## Migraciones

- [ ] La migracion tiene su reversa
- [ ] La migracion hace un solo cambio
- [ ] Los cambios de datos usan backfill por batches
- [ ] Las columnas nuevas se agregan nullable y se vuelven `NOT NULL` despues
- [ ] Se midio el tiempo estimado sobre una copia con volumen realista
- [ ] Los indices grandes se crean con `CONCURRENTLY`

## Rendimiento esperado

- [ ] Se estimo el volumen de filas de las tablas principales
- [ ] Se definio el criterio de particionado si aplica
- [ ] Las consultas de reporte mas pesadas tienen plan de optimizacion

## Seguridad de los datos

- [ ] Las columnas con datos sensibles estan identificadas
- [ ] Los datos sensibles no se loguean
- [ ] El cifrado en reposo aplica a las columnas que lo necesitan
- [ ] El acceso por rol esta definido si hay mas de un tipo de usuario

## Multi-tenant (si aplica)

- [ ] La estrategia de aislamiento esta decidida y documentada
- [ ] El filtro por tenant se aplica en la base, no en el codigo
- [ ] Las policies de `INSERT` tienen `WITH CHECK`
- [ ] El tenant se fija con `SET LOCAL` dentro de una transaccion
- [ ] Existe un test que verifica que un tenant no ve datos de otro

## Anti-patrones a detectar

- [ ] Ninguna columna `float` para dinero
- [ ] Ningun `timestamp` sin zona horaria
- [ ] Ninguna FK sin `ON DELETE` explicito
- [ ] Ningun `jsonb` con campos que se consultan
- [ ] Ninguna migracion sin reversa
- [ ] Ningun `UPDATE` masivo sin batches
- [ ] Ningun endpoint que devuelva la tabla completa

## Referencias

- `dev-kit-database/references/migraciones.md` - playbook de migraciones seguras
- `dev-kit-database/references/multi-tenant.md` - estrategias de aislamiento
