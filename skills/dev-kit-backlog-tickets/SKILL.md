---
name: dev-kit-backlog-tickets
description: "Convertir material crudo (actas, notas, correos) en un backlog jerarquico de historias con esfuerzo T-shirt, dependencias y decisiones bloqueantes separadas. CARGAR cuando llega un pedido difuso, hay que priorizar un monton de pedidos o se necesita estructurar lo que el cliente pidio."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [backlog, prioritization, requirements, tickets, estimation]
    category: software-development
    related_skills: [dev-kit-spec-authoring, dev-kit-spec-analysis, dev-kit-task-breakdown]
---

# Dev Kit - Backlog de tickets

> **Trigger:** "convertir estas notas en historias", "priorizar los pedidos",
> "el cliente mando un acta", "que hago primero", "armar el backlog", "esto es
> una sola historia o varias", "estimar el tamano de estas tareas". Cargar
> cuando el material de entrada es **crudo** y hay que convertirlo en backlog
> jerarquico.

## Que es esto

El backlog es la **capa de lenguaje directo** entre lo que alguien pidio y lo que
el equipo va a construir. Toma material crudo (un acta de reunion, notas de un
correo, un mensaje de voz transcrito) y produce una estructura ordenada y
estimable.

Dos reglas sostienen la skill:

1. **Nada se inventa.** Cada historia se apoya en algo de la fuente. Lo que no
   tiene respaldo va a una seccion aparte, no al backlog.
2. **Una ronda son 8 a 10 historias.** Ni 30 (no es una ronda, es un volcado) ni
   3 (no es una ronda, es una semana).

La diferencia con el spec (contrato de API) esta detallada en
`dev-kit-spec-authoring`: el backlog habla en lenguaje directo, el spec en
contrato. Esta skill produce el backlog; el spec se deriva de el.

## La piramide del backlog

```
PROYECTO
  |
  +-- EPICA A  (objetivo de negocio con nombre, plazo y criterio de exito)
  |     |
  |     +-- HU-01   (unidad de valor entregado)
  |     +-- HU-02
  |     +-- HU-03
  |
  +-- EPICA B
        |
        +-- HU-04
        +-- HU-05
```

| Nivel | Que es | Cantidad tipica | Contiene |
|---|---|---|---|
| Epica | un objetivo de negocio con exito medible | 3 a 8 por proyecto | HUs, plazo, criterio de exito |
| Historia (HU) | una unidad de valor entregable y verificable | 8 a 10 por ronda | criterios de aceptacion, esfuerzo, dependencias |
| Tarea | un paso tecnico dentro de una HU | 3 a 8 por HU | archivos, comandos, resultado |

La HU es la **unidad de valor**. No el endpoint, no la pantalla, no el sprint.
Una HU que no se puede entregar sola y no aporta valor por si misma se parte en
dos.

### Epica: la forma de escribirla

```
EPICA A - <nombre en infinitivo> (<resultado de negocio>)
OBJETIVO: <que cambia para el negocio>
CRITERIO DE EXITO: <metrica observable, con numero>
PLAZO: <fecha o ventana>
HUS: HU-01, HU-02, HU-03
```

Un criterio de exito con numero, no adjetivo. "Mas ventas" no es un criterio;
"+15% de operaciones cerradas sin intervencion manual en 60 dias" si.

## De la fuente al backlog: el proceso

### Paso 1 - Inventariar la fuente

Antes de escribir nada, listar **todo** lo que dice el material. Sin filtrar, sin
juzgar. La lista cruda es la que garantiza que no se pierde nada.

Se separa en tres canastas:

| Canasta | Que entra | Destino |
|---|---|---|
| Peticiones explicitas | lo que alguien pide de forma clara | backlog |
| Peticiones implicitas | lo que se deduce del contexto y es inevitable | backlog, marcadas como asumido |
| Mencionado sin detalle | lo que se nombra pero no se especifica | seccion de puntos sin respaldo |

### Paso 2 - Recortar el material crudo a propositos

Un acta de 40 lineas tiene 3 peticiones y 37 comentarios. Se recorta lo que no
produce trabajo:

| Se recorta | Por que |
|---|---|
| Saludos, contexto social, agenda | no produce trabajo |
| Repeticiones del mismo pedido | el segundo no agrega informacion |
| Quejas sin accion asociada | no son peticiones |
| Propuestas tecnicas sueltas | van al plan, no al backlog |
| Detalles de implementacion | van a la HU como contexto, no al criterio |

La prueba de que un elemento es trabajo: **¿de esta linea sale una historia
entregable?** Si no sale, se recorta.

### Paso 3 - Formar las HUs

Cada HU sale de una peticion, con este patron:

```
HU-<NN> - <verbo + objeto, en infinitivo>
ACTOR: <rol>
NECESIDAD: <que quiere>
VALOR: <que obtiene>
ESFUERZO: <S|M|L>
DEPENDENCIAS: <IDs>
```

La operacion mas importante del paso 3 es **partir las peticiones grandes**. Una
peticion que mezcla varias capacidades se parte en varias HUs:

| Peticion cruda | Problem | Como se parte |
|---|---|---|
| "Necesito que los usuarios puedan cargar documentos y verlos despues" | mezcla crear y leer | HU-01 crear y cargar, HU-02 listar y ver |
| "Que se integrate con el sistema de pagos y con el de facturacion" | dos integraciones, dos dependencias | HU-03 integrar pagos, HU-04 integrar facturacion |
| "Que el sistema avise cuando pasa algo" | ambiguedad de canal y evento | HU-05 definir eventos, HU-06 notificar |

Criterio de particion: **si las partes se pueden entregar en rondas
distintas, son HUs distintas.** Si no se pueden, es una sola HU grande.

### Paso 4 - Estimar con T-shirt

| Tamano | Guia | Ejemplo tipico |
|---|---|---|
| XS | menos de medio dia | un endpoint simple con test |
| S | medio a un dia | un endpoint con logica de negocio y tests |
| M | uno a tres dias | una HU con frontend + backend + persistencia |
| L | tres a cinco dias | una HU con integracion externa o migracion de datos |
| XL | mas de cinco dias | **no es una HU: hay que partirla** |

Reglas de estimacion:

- **Una HU XL no es una HU.** El tamano grande indica que la particion quedo mal.
  Partir y reestimar.
- **El tamano es del equipo, no del agente.** Si el equipo son dos personas, un
  dia es un dia-persona, no un dia-reloj.
- **El tamano no depende del nivel de complejidad tecnica**, sino de la cantidad
  de piezas: endpoints, pantallas, tablas, tests, integraciones.
- **La estimacion se revisa con la evidencia.** Si tres HUs XL de la ronda
  anterior resultaron ser M, la ronda esta sobreestimada y hay que ajustar.

### Paso 5 - Detectar dependencias

| Tipo de dependencia | Significado | Como se registra |
|---|---|---|
| Bloqueante dura | la HU no puede empezar hasta que otra termine | `DEPENDE DE: HU-03` |
| Bloqueante blanda | se puede empezar pero no terminar | nota en la HU |
| De datos | necesita un modelo o una migracion | `DEPENDE DE: <epica de datos>` |
| De tercero | necesita un servicio o permiso externo | `DEPENDE DE: <servicio>` |
| De decision | necesita una decision bloqueante cerrada | `DEPENDE DE: D-02` |

Regla: una dependencia de decision se referencia por el **ID de la decision
bloqueante** de la tabla correspondiente. Asi el grafo de dependencias apunta a
algo rastreable.

### Paso 6 - Ajustar a la ronda

Una ronda son **8 a 10 HUs**. Si hay mas, se seleccionan y el resto pasa a la
ronda siguiente con un motivo. Si hay menos, se agrupan con epicas relacionadas
o se subdivide.

Criterio de seleccion de la ronda:

1. Las HUs de la epica mas prioritaria.
2. Las HUs sin dependencias de decision abiertas.
3. Las HUs que desbloquean a otras.
4. Las HUs que cierran el camino critico del valor.

## Las decisiones bloqueantes van aparte

Una **decision bloqueante** es una pregunta sin responder que impide escribir
criterios de aceptacion, elegir implementacion o comprometer un plazo. No es una
tarea ni un pendiente menor.

Van en **tabla propia**, nunca mezcladas con las HUs:

| # | Decision | Pregunta a responder | Impacto si no se decide | Responsable | Fecha limite | HUs afectadas |
|---|---|---|---|---|---|---|
| D-01 | <decision> | <pregunta> | <que se bloquea> | <rol> | <fecha> | HU-01, HU-03 |

Reglas:

- **El responsable es un rol**, nunca un nombre.
- **El impacto es concreto**: "no se pueden escribir los criterios de HU-02" es
  mejor que "afecta al cronograma".
- **La fecha limite es real**: sin fecha, la decision no se toma nunca.
- **Una decision con fecha vencida escala.** El orquestador la sube, no la
  resuelve por su cuenta.

Distinguir decision bloqueante de duda tecnica:

| | Decision bloqueante | Duda tecnica |
|---|---|---|
| Naturaleza | de producto o negocio | de implementacion |
| Quien responde | negocio o lider tecnico | el arquitecto |
| Efecto | bloquea la HU | se resuelve en el plan |
| Donde vive | tabla de decisiones | nota del plan |

## Seccion final: puntos sin respaldo suficiente en la fuente

Esta seccion es la que hace trustworthy el backlog. Registra **todo lo que se
menciono pero no se especifico lo suficiente** para convertirlo en una HU.

| # | Mension | Que dice la fuente | Que falta | Como se resuelve | Responsable |
|---|---|---|---|---|---|
| P-01 | <mencion> | <cita resumida> | <que falta saber> | <pregunta a hacer / supuesto a validar> | <rol> |

Reglas:

- **No se convierte en HU.** Si no hay respaldo, no hay historia.
- **No se descarta en silencio.** Un punto sin registro se pierde y vuelve tres
  rondas despues como una queja.
- **Si se asume algo, se declara como supuesto.** Un supuesto con responsable
  es legitimo; un supuesto invisible es un gap esperando.

Un supuesto tiene tres estados posibles: `supuesto validado`, `supuesto
pendiente` (con fecha) y `supuesto rechazado`.

## Estructura del archivo de backlog

```
BACKLOG
  Metadatos del proyecto y de la ronda
  Resumen de la ronda (conteo, distribucion de esfuerzo)
  EPICA A  ->  HU-01 ... HU-0N
  EPICA B  ->  HU-0N+1 ...
  Tabla de decisiones bloqueantes
  Tabla de puntos sin respaldo suficiente en la fuente
  Supuestos declarados
  Historias de rondas siguientes (resumen)
```

Esqueleto listo para copiar: `templates/backlog.md`.

## Gate de calidad del archivo generado

Se verifica **por estructura y por conteos**, no por sensacion.

| Check | Como se verifica | Bloqueante |
|---|---|---|
| El archivo existe y tiene las 4 secciones | presencia de encabezados | si |
| La ronda tiene entre 8 y 10 HUs | conteo de lineas `HU-` | si |
| Cada HU tiene actor, necesidad, valor y esfuerzo | presencia de los 4 campos | si |
| Ninguna HU tiene tamano XL | revision de la columna de esfuerzo | si |
| Cada HU tiene al menos una dependencia o declara "ninguna" | revision | si |
| La tabla de decisiones bloqueantes existe aunque este vacia | presencia | si |
| Cada decision tiene responsable, fecha limite e HUs afectadas | revision | si |
| La seccion de puntos sin respaldo existe aunque este vacia | presencia | si |
| La suma de HUs de la ronda coincide con el resumen | conteo | si |
| Ninguna HU dice "como se implementa" | revision | no |

El gate es binario por la misma razon que todos los gates: un gate decorativo
genera la sensacion de rigor sin el rigor.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Volcar el acta como backlog | el cliente no lee 40 lineas sin estructura | recortar a 8-10 HUs |
| Inventar requisitos no pedidos | se construye lo que nadie quiere | seccion de puntos sin respaldo |
| Una HU con 12 criterios | nadie verifica 12 cosas | partir en dos HUs |
| Una HU XL | indica particion fallida | partir y reestimar |
| T-shirt por complejidad tecnica | confunde esfuerzo con dificultad | contar piezas a entregar |
| Decisiones mezcladas en las HUs | se pierden y nadie las ve | tabla aparte con ID |
| Dependencias sin ID | no se puede seguir el grafo | referenciar HU o D-xx |
| Sin seccion de puntos sin respaldo | lo no especificado se pierde en silencio | seccion obligatoria |
| Prioridad implicita por orden | el orden de lectura no es prioridad | columna de prioridad explicita |
| Esfuerzo sin unidad ni equipo | "3 dias" de quien | dias-persona del equipo |

## Referencias

- `templates/backlog.md` - esqueleto del archivo de backlog con las 4 secciones
- `references/backlog-criterios.md` - criterios de particion, estimacion y
  redaccion de una HU
- `dev-kit-spec-authoring` - como el backlog se convierte en contrato de API
- `dev-kit-spec-analysis` - coherencia entre backlog, spec y plan
- `dev-kit-task-breakdown` - del backlog al plan y de alla a las tareas

### Archivos incluidos en esta skill

| Archivo | Tipo | Para que sirve |
|---|---|---|
| `templates/backlog.md` | template | esqueleto del backlog con epicas, decisiones y puntos sin respaldo |
| `references/backlog-criterios.md` | referencia | guias de particion, estimacion T-shirt y redaccion |
