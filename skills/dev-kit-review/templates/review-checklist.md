# Checklist de review por tipo de cambio

> Usar segun el tipo de cambio. Marcar cada item revisado.
> Referencia de `dev-kit-review`.

---

## Logica de negocio

- [ ] Cada criterio de aceptacion de la historia tiene un test que lo cubre
- [ ] Los casos borde estan manejados: vacio, null, limite, duplicado
- [ ] Las decisiones de negocio estan en un solo lugar, no duplicadas
- [ ] Los errores de negocio se distinguen de los errores tecnicos
- [ ] El comportamiento por defecto esta definido explicitamente
- [ ] No hay logica condicional anidada de mas de 3 niveles
- [ ] Las constantes magicas tienen nombre

**Error tipico:** el caso donde el dato viene de otro sistema con formato
distinto se asume que nunca pasa.

---

## API / contrato

- [ ] Los codigos de error estan documentados, no solo los 200
- [ ] La paginacion tiene limite maximo definido
- [ ] Los campos son opcionales de forma explicita (y con default documentado)
- [ ] No se rompio un campo que alguien mas consume (compatibilidad)
- [ ] Los timestamps tienen zona horaria definida
- [ ] La idempotencia esta resuelta donde aplica (POST que se puede repetir)
- [ ] El nombre del recurso es consistente con el resto de la API
- [ ] El esquema de request y response esta validado en runtime

**Error tipico:** cambiar el nombre de un campo y actualizar solo el backend.

---

## Base de datos / migracion

- [ ] La migracion tiene rollback
- [ ] La migracion no bloquea tablas grandes por mucho tiempo
- [ ] Los indices nuevos tienen una justificacion (query que los necesita)
- [ ] Las columnas nuevas son nullable o tienen default
- [ ] La migracion es idempotente o se documenta que no lo es
- [ ] Hay backfill definido si la migracion cambia datos existentes
- [ ] El tiempo estimado de la migracion esta cuantificado

**Error tipico:** agregar columna NOT NULL sin default a una tabla con datos.

---

## Seguridad

- [ ] Ningun secreto en el codigo, en la config o en el pipeline
- [ ] Los inputs externos se validan (tipo, rango, formato, longitud)
- [ ] La autorizacion aplica a todos los endpoints tocados
- [ ] Los datos sensibles no van a los logs
- [ ] No se exponen datos internos en los mensajes de error
- [ ] Las dependencias nuevas no tienen vulnerabilidades conocidas
- [ ] Los CORS no quedaron en `*` con credenciales
- [ ] Hay rate limiting en los endpoints expuestos

**Error tipico:** el endpoint nuevo no tiene verificacion de propiedad: un
usuario autenticado puede leer datos de otro.

---

## Performance

- [ ] Las consultas a base de datos usan indice donde corresponde
- [ ] No hay N+1 en listados (se ve en el numero de queries)
- [ ] La paginacion se aplica en la base, no despues de traer todo
- [ ] Los payloads no son enormes sin necesidad
- [ ] Lo que se llama seguido esta cacheado, o se justifico por que no
- [ ] Las operaciones pesadas no bloquean el request

**Error tipico:** el listado funciona con 100 filas y falla con 100.000.

---

## Refactor

- [ ] El comportamiento observable es identico antes y despues
- [ ] Los tests existentes siguen pasando sin modificarlos
- [ ] No se mezclo refactor con cambio de comportamiento
- [ ] Los nombres nuevos son mejores que los viejos de forma objetiva
- [ ] No hay codigo muerto que se dejo a proposito

**Error tipico:** el refactor "de paso" cambia un comportamiento y nadie lo nota
porque los tests no cubrian ese caso.

---

## UI

- [ ] Los estados de carga, vacio y de error estan implementados
- [ ] El estado de error dice que hacer, no solo que fallo
- [ ] La navegacion por teclado funciona
- [ ] Los contrastes cumplen el estandar de accesibilidad
- [ ] Los formularios validan y muestran el error en el campo
- [ ] Las imagenes y los iconos tienen texto alternativo
- [ ] El layout no se rompe con contenido largo o en pantalla chica

**Error tipico:** el estado de carga nunca se vio porque en desarrollo siempre
habia datos.

---

## Infra / CI

- [ ] Los secretos vienen del secret store, no del archivo
- [ ] Los permisos del pipeline son los minimos
- [ ] Los recursos tienen limites (memoria, cpu, tiempo)
- [ ] El costo mensual estimado esta documentado
- [ ] El pipeline falla antes de llegar al deploy si los tests fallan
- [ ] El rollback esta documentado y es ejecutable

**Error tipico:** el job de deploy tiene permisos de administrador porque era
la forma mas rapida de hacerlo andar.

---

## Documentacion

- [ ] El doc coincide con el codigo actual
- [ ] Los ejemplos del README se ejecutan de verdad
- [ ] La estructura de carpetas del doc coincide con la real
- [ ] Se documento el "por que", no solo el "como"

**Error tipico:** el ejemplo del README quedo viejo y nadie lo prueba porque el
test no lo corre.

---

## General (siempre)

- [ ] El alcance del cambio corresponde al ticket
- [ ] No hay reformateo mezclado con cambios de logica
- [ ] No hay archivos generados ni secretos en el commit
- [ ] Los mensajes de commit explican el por que
- [ ] Los errores nuevos son accionables
