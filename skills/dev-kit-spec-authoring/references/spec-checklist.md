# Checklist de cierre del spec

Revision caso por caso antes de dar la fase 2 por cerrada. Cada punto tiene un
check verificable: si no se puede comprobar, no se da por cumplido.

---

## A. Estructura del contrato

- [ ] `openapi` esta en 3.1.0 y el archivo es YAML valido.
- [ ] `info.title`, `info.version` y `contact.name` (un rol) estan completos.
- [ ] Hay `servers` por ambiente, sin URLs con credenciales.
- [ ] Cada path tiene al menos un `tags` declarado arriba.
- [ ] Cada `operationId` es unico en todo el archivo.
- [ ] No hay endpoints `TRACE` ni endpoints de debug.
- [ ] No hay endpoints fuera del alcance declarado en `CONSTITUTION.md`.

## B. Nombres y convenciones

- [ ] Las rutas estan en plural y en `kebab-case`.
- [ ] Los `operationId` siguen `verboRecurso` en `camelCase`.
- [ ] Los campos de schema usan `snake_case`.
- [ ] Las listas devuelven `{ items, total }` de forma consistente.
- [ ] Los errores usan `application/problem+json` en todos los endpoints.

## C. Modelo de datos

- [ ] `Problem` existe con `type`, `title`, `status`, `detail`, `correlation_id`.
- [ ] Todo schema tiene `required` explicito para los campos obligatorios.
- [ ] Los campos de fecha usan `format: date-time` en ISO 8601.
- [ ] Los identificadores usan `format: uuid`.
- [ ] Los campos enumerados tienen `enum` con todos los valores permitidos.
- [ ] Los campos de texto tienen `maxLength`.
- [ ] Los campos numericos tienen `minimum` y `maximum` cuando corresponde.
- [ ] No hay `additionalProperties: true` en schemas de entrada sin justificar.
- [ ] Todo campo del schema existe en el modelo de datos del plan, o esta
      declarado como pendiente con responsable.

## D. Parametros

- [ ] Toda ruta con identificador declara el parametro `id` en `path`.
- [ ] Los parametros de query tienen `schema` con tipo.
- [ ] `limit` tiene `maximum` explicito y `default`.
- [ ] `offset` tiene `minimum: 0`.
- [ ] Los filtros booleanos usan `type: boolean` y no strings `"true"`.
- [ ] Los filtros de fecha declaran formato y zona horaria en la `description`.
- [ ] Los parametros opcionales son opcionales de verdad (`required` ausente o
      `false`), no "opcionales con valor por defecto obligatorio".

## E. Respuestas

- [ ] Cada operacion declara su respuesta de exito.
- [ ] Cada operacion declara al menos un codigo de error de cliente.
- [ ] Los codigos usados son consistentes en toda la API:
      `400` cuerpo invalido, `401` sin credenciales, `403` sin permiso,
      `404` no existe, `409` conflicto de estado, `422` regla de negocio,
      `429` limite de tasa.
- [ ] Los listados de recursos que se pueden crear declaran `409`.
- [ ] Las operaciones de lectura de recurso individual declaran `404`.
- [ ] El codigo de estado coincide con la semantica del caso de error.
- [ ] Ninguna respuesta de exito devuelve `200` con un cuerpo de error.

## F. Trazabilidad con las historias

- [ ] Cada endpoint tiene al menos una HU que lo requiere.
- [ ] Cada HU tiene al menos un endpoint o esta declarada como accion de UI.
- [ ] La tabla de trazabilidad esta completa en `specs/user-stories.md`.
- [ ] Las HUs que no tienen endpoint dicen por que (accion local, redireccion).

## G. Historias de usuario

- [ ] Todas tienen los tres bloques: CREEMOS QUE / RESULTARA EN / CRITERIOS.
- [ ] Todas tienen entre 3 y 5 criterios de aceptacion.
- [ ] Ningun criterio contiene "deberia", "idealmente", "rapido", "fácil",
      "intuitivo" u otros adjetivos no medibles.
- [ ] Ningun criterio menciona tablas, clases ni librerias.
- [ ] Los criterios con cantidad tienen unidad.
- [ ] Los caminos de error estan cubiertos en al menos una historia por epica.
- [ ] Los criterios referencian datos que existen en el contrato o en las
      reglas de negocio de `CONSTITUTION.md`.

## H. Clarificaciones

- [ ] Permisos por recurso: quien lee, quien escribe, quien aprueba.
- [ ] Comportamiento con lista vacia.
- [ ] Limite maximo de paginacion y orden por defecto.
- [ ] Respuesta cuando una dependencia externa falla.
- [ ] Idempotencia de operaciones de escritura.
- [ ] Comportamiento ante escrituras concurrentes sobre el mismo recurso.
- [ ] Formato de fecha, moneda y zona horaria por defecto.
- [ ] Formato exacto del error de autorizacion fallida.

## I. Coherencia con la constitucion

- [ ] Las restricciones de la seccion 5 de `CONSTITUTION.md` se respetan o
      estan declaradas como excepcion con justificacion.
- [ ] Los servicios externos con costo variable aparecen con su condicion de
      corte.
- [ ] Las prohibiciones no son violadas por el diseno del contrato (por
      ejemplo, no se expone un endpoint que devuelva datos prohibidos).
- [ ] El stack del contrato coincide con el stack permitido.

## J. Cierre

- [ ] El YAML pasa el parser sin errores.
- [ ] No hay `TODO` sin responsable y fecha.
- [ ] El contrato esta versionado junto al codigo.
- [ ] Los cambios de contrato roto se documentan como version mayor.

---

## Como verificar el contrato de forma automatizada

```bash
# el YAML tiene que parsear
python3 -c "import yaml; yaml.safe_load(open('specs/openapi.yaml'))"

# conteo de endpoints declarados
python3 - <<'PY'
import yaml
spec = yaml.safe_load(open("specs/openapi.yaml"))
ops = 0
for path, methods in spec.get("paths", {}).items():
    ops += sum(1 for m in methods if m in {"get", "post", "put", "patch", "delete"})
print(f"endpoints declarados: {ops}")
PY

# ningun operationId repetido
python3 - <<'PY'
import yaml, collections
spec = yaml.safe_load(open("specs/openapi.yaml"))
ids = [op["operationId"] for m in spec.get("paths", {}).values()
       for verb, op in m.items() if verb in {"get", "post", "put", "patch", "delete"}]
dupes = [k for k, v in collections.Counter(ids).items() if v > 1]
print("operationIds duplicados:", dupes or "ninguno")
PY
```

Estos tres checks son el minimo automatizable. El resto se revisa a mano con
esta checklist, y se anota en el registro de la fase.

---

## Errores que aparecen al revisar specs reales

| Error | Como se detecta | Como se corrige |
|---|---|---|
| Endpoint sin `404` | un recurso individual que no declara ausencia | agregar la respuesta de error |
| `limit` sin `maximum` | parametro de paginacion sin tope | agregar `maximum` y `default` |
| Modelo de error por endpoint | cada path con su propio schema de error | unificar en `Problem` |
| `operationId` repetido | dos endpoints con el mismo id | renombrar con el verbo correcto |
| Respuesta 200 con cuerpo de error | schema de exito que no coincide con el recurso | separar exito y error |
| Historia sin endpoint | HU sin `Endpoint` en la tabla de trazabilidad | agregar el endpoint o declarar la accion de UI |
| Criterio con "deberia" | lectura del criterio | reescribir con afirmacion y unidad |
| Fecha sin zona | campo de fecha sin `date-time` | usar `format: date-time` y declarar la zona |
| Schema mas ancho que el modelo | campo en el spec que no existe en el modelo de datos | alinear con el plan o declararlo pendiente |
