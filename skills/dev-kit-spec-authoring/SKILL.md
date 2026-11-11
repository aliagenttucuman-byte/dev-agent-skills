---
name: dev-kit-spec-authoring
description: "Escribir el contrato de API (OpenAPI) y las historias de usuario que definen que se construye, con formato CREEMOS QUE / RESULTARA EN / CRITERIOS DE ACEPTACION. CARGAR cuando hay que definir endpoints, modelar el comportamiento esperado o pasar de material crudo a un contrato verificable."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec, openapi, user-stories, api-design, contracts]
    category: software-development
    related_skills: [dev-kit-project-constitution, dev-kit-backlog-tickets, dev-kit-spec-analysis]
---

# Dev Kit - Autoria de especificacion

> **Trigger:** "definir los endpoints", "escribir el contrato de API", "que
> historias de usuario faltan", "el frontend necesita saber que pedir", "convertir
> este acta en un spec", "que criterios de aceptacion faltan". Cargar cuando
> toca definir **que** se construye, antes de decidir **como**.

## Que es esto

La especificacion es el **contrato** entre lo que se pide y lo que se construye.
Su unidad de verdad es el contrato de API (`specs/openapi.yaml`) y las historias
(`specs/user-stories.md`).

La regla que la sostiene:

> **El spec define el *que*, nunca el *como*.** Si el spec dice "la consulta se
> resuelve con un indice parcial", ya empezo a implementar.

Un buen spec se puede leer sin saber Python ni React. Un spec que necesita
conocer la implementacion para entenderse esta mezclando dos artefactos y los
dos van a quedar mal.

## Backlog vs contrato de API: la diferencia que hay que entender

Es la confusion mas comun del proceso y produce semanas de retrabajo.

| | Backlog | Contrato de API |
|---|---|---|
| Que es | **lenguaje directo** de lo que hay que hacer | **contrato** entre dos partes |
| Para quien | el equipo que prioriza y ejecuta | quien implementa y quien consume |
| Granularidad | una HU puede necesitar 3 endpoints | un endpoint resuelve una HU |
| Lenguaje | "el usuario puede filtrar por fecha" | `GET /operations?from=...&to=...` con su schema |
| Se negocia | si entra en el sprint | no: se implementa o no |
| Formato | HU con CREEMOS QUE / RESULTARA EN / CRITERIOS | YAML OpenAPI validado |
| Verificacion | revision del lider tecnico | validacion de schema + test de contrato |

El flujo correcto es:

```
material crudo
   |
   v
backlog jerarquico      <- lenguaje directo, HUs con criterios
   |
   v
contrato de API         <- endpoints, schemas, errores
   |
   v
plan de implementacion <- como se construye
```

El error tipico es saltar del material crudo directo al OpenAPI: se escriben
endpoints sin historia que los justifique, y aparecen endpoints que no
corresponden a ninguna necesidad. El error opuesto es quedarse en el backlog y
dejar que cada agente invente la forma de la llamada: se construyen tres
clientes distintos para la misma pantalla.

**Regla:** cada endpoint del spec tiene al menos una historia que lo requiere, y
cada historia tiene al menos un endpoint o una accion de UI.

## Anatomia de una historia de usuario

Formato obligatorio, tres bloques:

```
CREEMOS QUE <actor> <necesita> <capacidad> <motivo>
RESULTARA EN <entregable concreto y observable>
CRITERIOS DE ACEPTACION
  1. <criterio observable>
  2. <criterio observable>
  3. <criterio observable>
```

Por que funciona:

- **CREEMOS QUE** separa la hipotesis de la solucion. Escribe la necesidad, no
  la pantalla ni el endpoint.
- **RESULTARA EN** dice que se entrega, no "se mejora la experiencia".
- **CRITERIOS DE ACEPTACION** es lo unico que se usa para verificar. Sin
  criterios, la historia no se puede dar por terminada.

Ejemplo de forma correcta:

```
CREEMOS QUE un operador de un centro de operaciones necesita filtrar el
historial de movimientos por rango de fechas para reconstruir un incident
RESULTARA EN una vista de listado con selector de fechas que limita los
resultados al rango elegido y exporta el resultado filtrado a CSV
CRITERIOS DE ACEPTACION
  1. El rango de fechas es obligatorio y no puede superar 90 dias
  2. El listado muestra como maximo 100 filas por pagina con paginacion
  3. La exportacion a CSV respeta el filtro de fechas aplicado en pantalla
  4. Si no hay resultados, se muestra un estado vacio explicito
```

### Reglas de los criterios de aceptacion

| Regla | Por que | Mal | Bien |
|---|---|---|---|
| 3 a 5 por historia | mas es inmanejable, menos es ambiguo | 8 criterios | 4 criterios |
| observables | un criterio que no se ve, no se verifica | "el sistema es rapido" | "la respuesta llega en menos de 400 ms al percentil 95" |
| verificables por test | si no se puede testear, no se puede hacer | "la UX es intuitiva" | "el error indica la causa y el siguiente paso" |
| independientes del como | el criterio describe comportamiento | "se usa un indice GIN" | "la consulta responde en menos de 400 ms" |
| sinambiguedad de unidad | "maximo" sin unidad no se puede medir | "se muestran maximo N registros" | "se muestran como maximo 100 registros por pagina" |
| positivos y de error | el camino de error es parte del criterio | solo el camino feliz | "si falla, devuelve 409 con codigo `conflict`" |

Plantilla completa: `templates/user-story.md`.

## Anatomia del contrato OpenAPI

`specs/openapi.yaml` describe la superficie HTTP. Reglas de escritura:

### 1. Es una especificacion ejecutable

El YAML se valida en CI. Un contrato que no valida es un documento de texto.

```bash
# validacion del contrato en el pipeline
python3 -c "import yaml,sys; yaml.safe_load(open('specs/openapi.yaml'))"
```

### 2. Los tres bloques obligatorios

```yaml
openapi: 3.1.0
info:
  title: <nombre del servicio>
  version: 1.0.0
paths:
  /<recurso>:
    get:
      summary: <accion>
      operationId: <verboRecurso>
      parameters: [...]
      responses:
        "200": { description: ..., content: { application/json: { schema: ... } } }
        "4XX": { description: ... }
components:
  schemas: {...}
```

### 3. Convenciones de nombres

| Elemento | Convencion | Ejemplo |
|---|---|---|
| Rutas | plural, kebab-case | `/operation-records` |
| `operationId` | verbo + recurso, unico | `listOperationRecords` |
| Campos de schema | `snake_case` | `created_at` |
| Respuesta de lista | objeto con `items` y `total` | `{ "items": [], "total": 0 }` |
| Errores | `application/problem+json` | ver abajo |
| Filtros | query params con `from`, `to`, `limit`, `offset` | `?from=2026-01-01&limit=50` |

### 4. Los errores son parte del contrato

Un endpoint sin modelo de error definido obliga al cliente a adivinar. Se
declara un error unico:

```yaml
components:
  schemas:
    Problem:
      type: object
      required: [type, title, status, detail, correlation_id]
      properties:
        type: { type: string, example: "https://api.example.com/problems/validation" }
        title: { type: string, example: "Error de validacion" }
        status: { type: integer, example: 422 }
        detail: { type: string }
        correlation_id: { type: string }
```

Y se usa en todas las respuestas no exitosas:

```yaml
responses:
  "404":
    description: Recurso no encontrado
    content:
      application/problem+json:
        schema: { $ref: "#/components/schemas/Problem" }
```

### 5. Paginacion, filtros y limites

Toda lista declara su forma de paginar. El default se documenta en el
parametro, no en un wiki:

```yaml
parameters:
  - name: limit
    in: query
    schema: { type: integer, minimum: 1, maximum: 100, default: 50 }
  - name: offset
    in: query
    schema: { type: integer, minimum: 0, default: 0 }
```

Regla: **el maximo de `limit` es parte del contrato**. Un endpoint sin tope de
pagina es un incidente esperando.

### 6. Los endpoints que no se documentan, no existen

Si una HU no tiene endpoint, es porque es una accion de UI sobre datos ya
cargados (un logout, un toggle local). Esa excepcion se escribe en la historia.
Si no, el endpoint falta.

### Plantilla minima

`templates/openapi-minimal.yaml` - un contrato minimo y valido, con un recurso
completo (list + create + error model + pagination). Se copia y se extiende.

## Como se escribe el spec: proceso

1. **Partir de las historias, no de la pantalla.** El contrato se deriva de las
   HUs del backlog, no de una maqueta.
2. **Agrupar endpoints por recurso, no por pantalla.** Una pantalla consume
   varios endpoints; un recurso se expone en varios lugares.
3. **Escribir primero el modelo de error.** Sin error unificado, cada endpoint
   inventa el suyo.
4. **Declarar los limites en el parametro.** `maximum: 100` en el schema, no
   en un comentario.
5. **Marcar lo que no se define.** Un `TODO` con responsable y fecha es
   honesto; un endpoint inventado en silencio no lo es.

## Clarificaciones obligatorias

Antes de dar el spec por cerrado, estas preguntas tienen que estar respondidas
**en el documento**, no en la cabeza de nadie:

| Ambiguedad | Pregunta que la resuelve |
|---|---|
| Permisos | quien puede ver y quien puede escribir cada recurso |
| Datos vacios | que se devuelve cuando la lista no tiene resultados |
| Paginacion | limite maximo, orden por defecto, estabilidad del orden |
| Errores parciales | que pasa si una dependencia falla en una operacion multi-paso |
| Idempotencia | que operaciones se pueden repetir sin efecto duplicado |
| Concurrencia | que pasa si dos operaciones modifican el mismo recurso a la vez |
| Zona y formato | formato de fecha, moneda y zona horaria por defecto |
| Autorizacion fallida | codigo de error y cuerpo exactos |

Cada respuesta se agrega como una seccion **Clarificaciones** al final del
archivo de historias, o como `description` del endpoint afectado.

## Gate de la fase 2

| Check | Como se verifica | Bloqueante |
|---|---|---|
| `specs/openapi.yaml` existe | archivo presente | si |
| El YAML es valido | parser de YAML | si |
| Todas las historias tienen 3 a 5 criterios | conteo automatico del patron | si |
| Cada endpoint tiene historia asociada | tabla de trazabilidad | si |
| Cada historia tiene endpoint o accion de UI | tabla de trazabilidad | si |
| El modelo de error esta declarado | `Problem` en `components.schemas` | si |
| Las listas declaran paginacion y tope | `limit` con `maximum` | si |
| Las ambiguedades de la tabla estan respondidas | seccion de clarificaciones | si |
| No hay `TODO` sin responsable | revision | no |

**Sin contrato de API no hay implementacion.** La razon es concreta: backend y
frontend pueden trabajar en paralelo **solo** despues de que el contrato este
cerrado. Antes de eso, todo trabajo paralelo se tira.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Escribir el spec describiendo pantallas | acopla la API a una UI que va a cambiar | derivar de historias |
| Escribir endpoints sin historias | aparecen endpoints que nadie necesita | tabla de trazabilidad |
| Criterios de aceptacion vagos | nadie puede decir "terminado" | observables y verificables |
| "El sistema debe ser rapido" | no se puede testear | p95 con numero |
| Dejar los errores para despues | cada endpoint inventa su formato | modelo `Problem` primero |
| Sin tope de paginacion | incidente de carga en produccion | `maximum` en el schema |
| Un endpoint por pantalla | la API se rompe con la UI | un recurso, muchas pantallas |
| Especificar el "como" en el spec | el contrato deja de ser estable | behavior, no implementacion |
| 12 criterios en una historia | nadie verifica 12 cosas | 3 a 5, el resto en otra historia |
| Aprobar el spec "de palabra" | el gate no es verificable | checklist con comandos |

## Referencias

- `templates/user-story.md` - plantilla de historia con el formato completo
- `templates/openapi-minimal.yaml` - contrato minimo valido, copiable y extensible
- `references/spec-checklist.md` - checklist de cierre del spec, caso por caso
- `dev-kit-project-constitution` - las restricciones que el spec debe respetar
- `dev-kit-backlog-tickets` - de donde salen las historias que el spec contracta
- `dev-kit-spec-analysis` - verifica que spec, plan y estimacion sean coherentes

### Archivos incluidos en esta skill

| Archivo | Tipo | Para que sirve |
|---|---|---|
| `templates/user-story.md` | template | esqueleto de una historia con sus tres bloques |
| `templates/openapi-minimal.yaml` | template | contrato OpenAPI minimo con recurso, errores y paginacion |
| `references/spec-checklist.md` | referencia | checklist de cierre del spec con casos concretos |
