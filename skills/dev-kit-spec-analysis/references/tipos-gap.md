# Catalogo de gaps y over-engineering

Referencia extendida de los tipos de defecto de coherencia entre spec, plan y
estimacion. Cada tipo tiene: como se detecta, un ejemplo generico, que
severidad tiene por defecto y cual es la accion.

---

## Parte 1: Gaps (el plan no cubre lo que el spec pide)

### G1 - Historia sin endpoint

**Deteccion:** una HU de `specs/user-stories.md` no tiene ninguna entrada en la
tabla de trazabilidad, y no esta marcada como "accion de UI sin endpoint".

**Ejemplo:** la historia "Exportar el reporte mensual" no tiene ruta de
exportacion en `specs/openapi.yaml`.

**Severidad por defecto:** bloqueante. Sin endpoint, la historia no se puede
implementar ni verificar.

**Accion:** agregar el endpoint al contrato, o reescribir la historia para
declarar que es una accion de UI.

**Vuelve a:** fase 2.

---

### G2 - Endpoint sin historia

**Deteccion:** una ruta del contrato OpenAPI no aparece en ninguna HU.

**Ejemplo:** `GET /internal/health-detailed` existe en el contrato pero ninguna
historia lo requiere.

**Severidad por defecto:** media. Puede ser legitimo (endpoint tecnico), pero
si no esta justificado, es superficie de API que hay que mantener.

**Accion:** si es necesario, agregar una HU tecnica; si no, eliminar el
endpoint del contrato.

**Vuelve a:** fase 2.

---

### G3 - Componente del plan sin historia

**Deteccion:** un modulo, servicio o componente del `PLAN.md` no mapea a
ninguna HU.

**Ejemplo:** el plan incluye un "bus de eventos interno" y ninguna historia
requiere comunicacion asincrona entre servicios.

**Severidad por defecto:** alta. Es trabajo que alguien va a pagar y mantener.

**Accion:** eliminar el componente, o agregar la HU que lo justifica con su
criterio de aceptacion.

**Vuelve a:** fase 4.

---

### G4 - Entidad de datos faltante

**Deteccion:** un campo o schema del contrato OpenAPI no tiene contraparte en
el modelo de datos del plan.

**Ejemplo:** el contrato expone `status` con tres valores posibles y el plan
no define ni la columna ni el enum.

**Severidad por defecto:** bloqueante si el campo es obligatorio; alta si es
opcional.

**Accion:** agregar la entidad al modelo de datos del plan, con su migracion.

**Vuelve a:** fase 4.

---

### G5 - Historia sin plan

**Deteccion:** una HU no tiene ninguna tarea asociada en el breakdown, o no
aparece en ninguna seccion del plan.

**Ejemplo:** la historia "Notificar al supervisor" no tiene ninguna tarea que
la implemente.

**Severidad por defecto:** bloqueante.

**Accion:** agregar la historia al plan con su orden de implementacion.

**Vuelve a:** fase 4.

---

### G6 - Criterio sin cobertura

**Deteccion:** un criterio de aceptacion de una HU no tiene ninguna tarea ni
test que lo verifique.

**Ejemplo:** el criterio "el error indica la causa y el siguiente paso" no
tiene ninguna tarea de validacion ni test asociado.

**Severidad por defecto:** alta. Un criterio sin cobertura no es un criterio:
es una intencion.

**Accion:** agregar la tarea de verificacion, o reducir el criterio a lo que se
puede verificar.

**Vuelve a:** fase 2 si el criterio esta mal escrito; fase 4 si falta la tarea.

---

### G7 - Dependencia no resuelta

**Deteccion:** una HU depende de una decision bloqueante (`D-xx`) que sigue
abierta o que no tiene fecha de cierre.

**Ejemplo:** HU-06 depende de D-02 (canal de notificacion), que sigue abierta
con fecha vencida.

**Severidad por defecto:** bloqueante.

**Accion:** cerrar la decision, o reescribir la HU sin la parte que depende de
ella.

**Vuelve a:** fase 1 (backlog) o fase 2.

---

### G8 - Componente sin costo

**Deteccion:** una pieza del plan no aparece en ninguna linea de la estimacion.

**Ejemplo:** el plan agrega una cola de mensajes; la estimacion no costea el
broker ni su operacion.

**Severidad por defecto:** bloqueante. Sin costo, el gate economico no existe.

**Accion:** agregar el componente a la estimacion, con los tres escenarios.

**Vuelve a:** fase 5.

---

### G9 - Componente sin test

**Deteccion:** una tarea del plan que implementa comportamiento de negocio no
tiene test asociado ni criterio de aceptacion que la cubra.

**Ejemplo:** la tarea "implementar calculo de totales" no tiene test unitario
en el plan.

**Severidad por defecto:** media. Se eleva a alta si la logica maneja dinero,
permisos o estados irreversibles.

**Accion:** agregar la tarea de test con su criterio.

**Vuelve a:** fase 4.

---

### G10 - Endpoint sin control de acceso

**Deteccion:** una ruta del contrato no tiene regla de permiso asociada, y la
tabla de permisos del spec no la cubre.

**Ejemplo:** `POST /x/archive` permite archivar registros y ninguna regla dice
quien puede hacerlo.

**Severidad por defecto:** alta; bloqueante si la operacion es destructiva o
toca datos sensibles.

**Accion:** definir la regla de permiso en la especificacion y en las reglas
de negocio.

**Vuelve a:** fase 2.

---

### G11 - Migracion sin rollback

**Deteccion:** un cambio de esquema en el plan no tiene procedimiento de
reversa, o no es reversible en una transaccion.

**Ejemplo:** agregar una columna obligatoria sin default a una tabla existente
con datos.

**Severidad por defecto:** alta.

**Accion:** agregar el paso de rollback al plan o cambiar el diseño para que
sea reversible.

**Vuelve a:** fase 4.

---

### G12 - Dependencia tecnica ausente

**Deteccion:** el plan llama a un servicio externo, SDK o API que no tiene
cliente, manejo de error ni tiempo de espera definidos.

**Ejemplo:** el plan integrate un servicio de envio de mensajes, pero no
define reintentos, timeout ni que pasa si la dependencia cae.

**Severidad por defecto:** alta.

**Accion:** agregar el cliente, el manejo de fallo y el tiempo de espera al
plan, y su costo a la estimacion.

**Vuelve a:** fase 4 y fase 5.

---

## Parte 2: Over-engineering (el plan tiene lo que el spec no pide)

### O1 - Componente no pedido

**Deteccion:** igual que G3, pero el efecto es el contrario: sobra.

**Ejemplo:** el plan incluye un modulo de permisos con roles granulares, y el
spec solo necesita dos niveles de permiso.

**Severidad por defecto:** alta.

**Accion:** reducir el componente al alcance del spec, o agregar la HU que lo
justifica con su criterio de aceptacion.

**Vuelve a:** fase 4.

---

### O2 - Abstraccion prematura

**Deteccion:** interfaces, factorias o registries con una sola implementacion
prevista.

**Ejemplo:** una interfaz `PaymentProvider` con una unica implementacion
concreta, en un proyecto que tendra una sola pasarela.

**Severidad por defecto:** media. Se eleva si la abstraccion tiene logica
repetida que aun no se ve.

**Accion:** usar la implementacion concreta hasta que exista el segundo caso.

**Vuelve a:** fase 4.

---

### O3 - Endpoint extra

**Deteccion:** rutas del contrato sin HU (el caso O3 de G2, desde el lado del
exceso).

**Severidad por defecto:** media.

**Accion:** eliminar la ruta del contrato.

**Vuelve a:** fase 2.

---

### O4 - Generalizacion sin segundo caso

**Deteccion:** parametros, flags, columnas o variantes de UI que hoy usan un
solo valor.

**Ejemplo:** un campo `modo` con tres valores (`simple`, `avanzado`,
`personalizado`) donde solo se usa `simple`.

**Severidad por defecto:** media.

**Accion:** reducir a lo que se usa, o documentar el caso futuro que lo
justifica en el plan.

**Vuelve a:** fase 4.

---

### O5 - Infraestructura anticipada

**Deteccion:** servicios, colas, clusters o replicacion para un volumen que el
spec no justifica.

**Ejemplo:** el plan despliega tres replicas y una cola distribuida para un
volumen de consultas que cabe en una instancia.

**Severidad por defecto:** alta, porque el costo es recurrente y fijo.

**Accion:** empezar con la arquitectura minima y documentar el umbral de
escala que dispara el crecimiento.

**Vuelve a:** fase 4 y fase 5.

---

### O6 - Capa sin amenaza real

**Deteccion:** validaciones, sanitizaciones o controles que no responden a
ninguna regla de negocio de la constitucion ni a ningun criterio del spec.

**Ejemplo:** un sanitizador de entrada a un campo que el modelo declara como
enum cerrado.

**Severidad por defecto:** baja.

**Accion:** eliminarlo, o documentar la amenaza que mitiga.

**Vuelve a:** fase 4.

---

### O7 - Refactor oportunista

**Deteccion:** cambios a codigo existente que ninguna HU requiere.

**Ejemplo:** el plan renombra un modulo completo y reorganiza imports en cinco
archivos, sin que ninguna HU lo pida.

**Severidad por defecto:** media. Se eleva a alta si el diff crece y sube el
riesgo de la funcionalidad pedida.

**Accion:** sacar el refactor del alcance. Si tiene valor propio, es otra HU.

**Vuelve a:** fase 4.

---

### O8 - Metrica sin consumidor

**Deteccion:** instrumentacion, dashboard o alerta que no tiene un consumidor
declarado.

**Ejemplo:** el plan agrega cinco metricas de negocio y no dice quien las mira
ni para que decision.

**Severidad por defecto:** baja.

**Accion:** declarar el consumidor o sacar la metrica.

**Vuelve a:** fase 4.

---

## Parte 3: como se combines los hallazgos

Un hallazgo puede ser a la vez gap y over-engineering en el mismo componente.
El analisis lo registra con **dos IDs distintos** (uno `G`, otro `O`) porque
las acciones son opuestas.

Ejemplo: el plan tiene un "bus de eventos interno".

| ID | Tipo | Hallazgo | Accion |
|---|---|---|---|
| G3-02 | Gap | componente del plan sin historia que lo requiera | - |
| O1-02 | Over-engineering | el bus no es pedido por ninguna HU | eliminar del plan |

Resolver solo uno de los dos deja el hallazgo abierto.

---

## Parte 4: como se calcula el impacto en la estimacion

| Tipo de hallazgo | Efecto tipico en el costo |
|---|---|
| G4 (entidad faltante) | + trabajo de modelado y migracion |
| G8 (sin costo) | + el componente entero entra a la estimacion |
| G9 (sin test) | + tiempo de QA |
| G12 (dependencia ausente) | + costo del servicio externo o de la resiliency |
| O1 (componente no pedido) | - costo de infraestructura y de mantenimiento |
| O5 (infra anticipada) | - costo recurrente de infraestructura |
| O2 (abstraccion prematura) | - tiempo de implementacion |
| O7 (refactor oportunista) | - tiempo de implementacion, + riesgo |

Cada delta se anota en **los tres escenarios** (conservador, base, optimista) o
se declara explicitamente "a definir" con la razon. Un delta que no se puede
cuantificar tiene que quedar como pendiente, no como cero.

---

## Parte 5: preguntas de control para la revision

Para cada capa, la pregunta que reveals el error:

| Capa | Pregunta de control |
|---|---|
| Spec | "cada endpoint existe porque una historia lo pide?" |
| Spec | "cada criterio de aceptacion es observable por alguien que no escribio el codigo?" |
| Plan | "cada componente del plan hace falta para un criterio del spec?" |
| Plan | "cada componente del plan tiene su costo en la estimacion?" |
| Plan | "hay algo en el plan que es mas sophisticated que lo que el spec necesita?" |
| Estimacion | "el total de la estimacion corresponde al alcance del plan?" |
| Estimacion | "las tres estimaciones se pueden explicar con la misma logica?" |
| Todos | "que pasa si el proyecto se entrega a la mitad?" |
