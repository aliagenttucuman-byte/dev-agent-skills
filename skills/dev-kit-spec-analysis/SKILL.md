---
name: dev-kit-spec-analysis
description: "Analizar la coherencia entre spec, plan y estimacion: detectar gaps (lo que el plan no cubre) y over-engineering (lo que el plan agrega sin pedido), con severidad y reporte formal. CARGAR antes de implementar, cuando algo no cierra entre artefactos o para revisar si un plan esta sobredimensionado."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [analysis, coherence, gaps, review, quality-gate]
    category: software-development
    related_skills: [dev-kit-spec-authoring, dev-kit-cost-estimation, dev-kit-task-breakdown]
---

# Dev Kit - Analisis de coherencia

> **Trigger:** "revisar si el plan cubre el spec", "falta algo de lo que
> pedimos", "esto esta sobredimensionado", "no me cierra la estimacion", "el
> plan tiene cosas que no pidimos", "gap entre backlog y plan". Cargar **antes
> de implementar**, y cada vez que se toque uno de los tres artefactos.

## Que es esto

El analisis compara **tres capas** de artefactos y busca dos familias de
defecto que se cancelan entre si:

| Defecto | Direccion | Que significa | Impacto |
|---|---|---|---|
| **Gap** | spec -> plan | el plan no cubre algo que el spec pide | se construye incompleto |
| **Over-engineering** | plan -> spec | el plan tiene algo que el spec no pide | se construye de mas |

Los dos errores tienen la misma raiz: **nadie comparo los artefactos entre si**.
Cada uno esta bien escrito en su propio mundo y mal en el ensemble.

El analisis tambien cubre la tercera capa, la estimacion: si el plan incluye
un componente que la estimacion no costea, el gate economico es decorativo.

## Las tres capas y que se compara

```
CONSTITUCION.md   que esta permitido, con que limites
        |
        v
specs/            QUE se construye: contrato OpenAPI + historias
        |
        v
PLAN.md           COMO se construye: componentes, orden, dependencias
        |
        v
ESTIMACION.md     CUANTO cuesta: infra, tokens, equipo, tiempo
```

| Comparacion | Direccion | Tipo de defecto |
|---|---|---|
| spec vs plan | plan debe cubrir spec | gap |
| spec vs plan | plan no debe exceder spec | over-engineering |
| plan vs estimacion | todo componente del plan tiene costo | gap economico |
| spec vs estimacion | el costo de la estimacion corresponde al alcance del spec | gap + over-engineering |
| constitution vs todo | nada contradice las politicas | violacion |

## Tipos de gap que hay que buscar

No todos los gaps son del mismo tipo. Cada tipo se detecta de una forma
distinta:

| # | Tipo de gap | Como se detecta | Ejemplo generico |
|---|---|---|---|
| G1 | **Historia sin endpoint** | HU de la lista sin entrada en la tabla de trazabilidad | HU de exportacion sin ruta de exportacion |
| G2 | **Endpoint sin historia** | ruta en el spec sin HU que la requiera | ruta de health check que nadie pidio |
| G3 | **Componente del plan sin historia** | modulo del plan que no mapea a ninguna HU | servicio de bus de eventos para un flujo sin eventos |
| G4 | **Entidad de datos faltante** | campo del contrato sin modelo de datos en el plan | campo de estado sin columna ni enum |
| G5 | **Historia sin plan** | HU sin ninguna tarea que la implemente | HU de notificaciones sin tarea asociada |
| G6 | **Criterio sin cobertura** | criterio de aceptacion sin test ni tarea | "el error indica la causa" sin nadie que lo verifique |
| G7 | **Dependencia no resuelta** | HU que depende de D-xx aun abierta | la decision se cerro a medias |
| G8 | **Componente sin costo** | pieza del plan ausente de la estimacion | cola de mensajes sin coste de broker |
| G9 | **Componente sin test** | tarea sin test ni criterio verificable | endpoint nuevo sin cobertura |
| G10 | **Endpoint sin control de acceso** | ruta sin regla de permiso en la especificacion | ruta de escritura sin politica |
| G11 | **Migracion sin rollback** | cambio de esquema sin plan de reversa | columna obligatoria sin default |
| G12 | **Dependencia tecnica ausente** | integracion externa no declarada en el plan | llamada a un servicio sin cliente ni manejo de error |

## Tipos de over-engineering

| # | Tipo | Como se detecta | Por que es un problema |
|---|---|---|---|
| O1 | **Componente no pedido** | modulo del plan sin HU asociada | costo sin valor |
| O2 | **Abstraccion prematura** | interfaz o factoria con una sola implementacion | complejidad que alguien tiene que mantener |
| O3 | **Endpoint extra** | ruta en el spec sin historia | superficie de API que hay que documentar y sostener |
| O4 | **Generalizacion sin segundo caso** | parametro, flag o tabla que solo usa un caso | se mantiene sin uso |
| O5 | **Infraestructura anticipada** | servicio, cola o cluster para volumen que no existe | costo fijo antes de tener demanda |
| O6 | **Seguridad o validacion sin amenaza** | capa que no responde a ninguna regla de negocio | trabajo sin criterio de exito |
| O7 | **Refactor oportunista** | cambio no pedido a codigo existente | ensancha el diff y el riesgo |
| O8 | **Metrica sin consumidor** | instrumentacion que nadie mira | costo de observabilidad sin retorno |

## Tabla de severidad

La severidad define la accion. No es decorativa: determina a que fase se vuelve.

| Severidad | Definicion | Accion | Vuelve a |
|---|---|---|---|
| **Bloqueante** | impide construir o impide decidir | no se implementa nada | fase 2, 4 o 5 segun corresponda |
| **Alta** | produce trabajo incorrecto o una decision costosa | se corrige antes de implementar | fase 4 o 5 |
| **Media** | afecta calidad, mantenibilidad o precision | se corrige en la misma ronda | fase 4 |
| **Baja** | mejora la claridad sin cambiar el resultado | se anota y se sigue | - |

Criterios de asignacion:

| Severidad | Se asigna cuando |
|---|---|
| Bloqueante | falta un endpoint de una historia; hay una decision bloqueante abierta que afecta la implementacion; la estimacion no cubre un componente del plan; hay una violacion de la constitucion |
| Alta | hay trabajo de mas que el equipo va a pagar; falta un criterio de aceptacion con verificacion; una migracion no es reversible; falta control de acceso en un endpoint sensible |
| Media | falta un test de un componente no critico; hay un parametro sin usar; el criterio esta ambiguo pero se puede interpretar |
| Baja | falta un comentario; la nomenclatura es inconsistente; la documentacion esta desactualizada |

**Regla:** el criterio de severidad no es "que tan grave se siente" sino "que
pase si no se corrige". Si un gap bloqueante se puede ignorar sin consecuencias,
no era bloqueante.

## Proceso de analisis

1. **Cargar los tres artefactos.** Si falta alguno, el analisis no se puede
   hacer y eso mismo es un hallazgo bloqueante.
2. **Construir la matriz de trazabilidad.** Filas: historias. Columnas: endpoints,
   componentes del plan, tareas, costos. Cada celda se llena con el ID o con `-`.
3. **Buscar en las dos direcciones.** Filas con celdas vacias hacia el plan son
   gaps. Columnas con celdas vacias hacia las historias son over-engineering.
4. **Verificar la cobertura de criterios.** Cada criterio de aceptacion tiene
   una tarea o un test que lo cubre.
5. **Clasificar y severizar** cada hallazgo.
6. **Emitir el reporte** con la accion de cada hallazgo.
7. **Recalcular el impacto en la estimacion.** Un gap G8 (componente sin costo)
   o un over-engineering O1 modifican el total.

### La matriz de trazabilidad

Es la herramienta central. Se arma en Markdown plano:

| Historia | Endpoints | Componentes del plan | Tareas | Costo | Test | Estado |
|---|---|---|---|---|---|---|
| HU-01 | `GET /x`, `POST /x` | `api/x.py`, `service/x.py` | T-01, T-02 | infra + 1d | `test_x.py` | completa |
| HU-02 | `POST /x/export` | `service/export.py` | T-03 | infra + 2d | - | **G6** |

La lectura de la matriz:

- **Celda vacia en la columna de endpoints** -> G1.
- **Celda vacia en la columna de componentes** -> G5.
- **Celda vacia en la columna de tareas** -> G5 o G6.
- **Celda vacia en la columna de costo** -> G8.
- **Fila con endpoint sin HU** -> O3.
- **Componente sin fila** -> O1.
- **Historia sin test** -> G9.

## Formato del reporte

`REPORT-GAPS.md`, con esta estructura exacta:

```
1. Resumen ejecutivo   (numeros: hallazgos por severidad, veredicto)
2. Alcance             (que artefactos se compararon y que version)
3. Tabla de hallazgos   (una fila por hallazgo, con IDs)
4. Detalle por hallazgo (un bloque por hallazgo)
5. Matriz de trazabilidad
6. Impacto en la estimacion
7. Acciones pendientes  (tabla con responsable, fase destino y fecha)
```

Cada bloque de detalle de hallazgo:

```
ID:        G3-01
Tipo:      Gap - componente del plan sin historia
Severidad: Alta
Hallazgo:  El modulo de notifications no mapea a ninguna HU.
Evidencia: PLAN.md seccion 4, componente "notifications"
           specs/user-stories.md no contiene ninguna HU relacionada.
Impacto:   Se construye y se mantiene un modulo que no aporta valor al
           alcance acordado, con su costo de infraestructura asociado.
Accion:    Eliminar el componente del plan, o agregar la HU que lo justifica
           con su criterio de aceptacion.
Destino:   Fase 4 (plan)
```

Plantilla: `templates/gap-report.md`.

### El veredicto

El reporte cierra con un veredicto explicito, porque sin el el analisis no
cierra:

| Veredicto | Condicion | Efecto |
|---|---|---|
| **APTO PARA IMPLEMENTAR** | cero hallazgos bloqueantes y cero altas | se pasa a la fase de tareas |
| **APTO CON RESERVAS** | cero bloqueantes, hay altas o medias | se implementa, con las altas corregidas en la misma ronda |
| **NO APTO** | hay al menos un bloqueante | no se implementa nada |

**El veredicto no se escribe a mano: se deduce de la tabla de severidad.**
Cero bloqueantes es un precondition en todos los casos.

## Gate de la fase 6

| Check | Como se verifica | Bloqueante |
|---|---|---|
| `REPORT-GAPS.md` existe | archivo presente | si |
| Se compararon los tres artefactos | seccion de alcance | si |
| La matriz de trazabilidad esta completa | tabla presente y sin celdas inexplicadas | si |
| Cada hallazgo tiene ID, tipo, severidad, evidencia y accion | revision | si |
| Todo hallazgo bloqueante tiene destino de fase | revision | si |
| El veredicto coincide con la tabla de severidad | recomputo | si |
| La seccion de impacto en la estimacion esta completa | revision | si |
| Las acciones pendientes tienen responsable y fecha | revision | no |

**Si hay gaps, se vuelve a spec, plan o estimacion. Nunca a implementacion.**
Este es el gate que evita la trapezio de mas comun: el equipo encuentra un gap
durante la implementacion, y lo resuelve improvisando en codigo. Lo que se
gana en una tarde de codigo se pierde en un sistema que no coincide con su
spec.

### Que se vuelve a corregir

| Tipo de hallazgo | Fase a la que se vuelve |
|---|---|
| G1, G2, G6, G10 (contrato incompleto o mal) | fase 2 (spec) |
| G3, G4, G5, G9, G11, G12 (plan incompleto) | fase 4 (plan) |
| G8, y todo lo de la seccion de impacto | fase 5 (estimacion) |
| O1 a O8 | fase 4 (plan), y el impacto vuelve a la fase 5 |
| Violacion de la constitucion | fase 1 (constitucion) |

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Analizar un solo artefacto | no hay comparacion, no hay analisis | los tres o se declara bloqueante |
| Listar hallazgos sin accion | el reporte no sirve para avanzar | cada hallazgo dice que hacer y donde |
| Severidad por tamano del cambio | un cambio grande puede ser trivial | severidad por consecuencia |
| Tratar over-engineering como "mejora" | el cliente no lo pidio y lo paga | se recorta o se justifica |
| Resolver gaps en codigo | el spec queda mintiendo | volver a la fase correspondiente |
| Veredicto optimista | "no hay gaps" sin matriz | la matriz es la prueba |
| Reporte largo sin resumen | nadie lo lee | resumen con numeros arriba |
| Solo hay gaps, no hay over-engineering | la revision es a una sola direccion | revisar las dos direcciones |
| Analizar y no reestimar | el costo cambio y nadie lo sabe | recalcular en la seccion de impacto |

## Referencias

- `templates/gap-report.md` - plantilla del reporte con todas sus secciones
- `references/tipos-gap.md` - catalogo extendido de gaps y over-engineering con
  ejemplos de deteccion
- `dev-kit-spec-authoring` - la capa de spec que se analiza
- `dev-kit-cost-estimation` - la capa de costo que se recalcula
- `dev-kit-task-breakdown` - la fase que se abre si el veredicto es APTO

### Archivos incluidos en esta skill

| Archivo | Tipo | Para que sirve |
|---|---|---|
| `templates/gap-report.md` | template | esqueleto del `REPORT-GAPS.md` con las 7 secciones |
| `references/tipos-gap.md` | referencia | catalogo de gaps y over-engineering con deteccion y accion |
