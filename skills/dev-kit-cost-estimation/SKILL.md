---
name: dev-kit-cost-estimation
description: "Estimar el costo real de construir y operar antes de implementar: infraestructura cloud mensual, tokens de LLM, suscripciones recurrentes, fee de equipo por rol y periodo, con escenarios conservador, base y optimista. CARGAR antes de comprometer presupuesto o cuando hay que decidir si un proyecto es rentable."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cost, estimation, budget, llm-tokens, infrastructure]
    category: software-development
    related_skills: [dev-kit-project-constitution, dev-kit-spec-analysis, dev-kit-task-breakdown]
---

# Dev Kit - Estimacion de costos

> **Trigger:** "cuanto va a costar", "estimar la infraestructura", "cuantos tokens
> vamos a gastar", "vale la pena este proyecto", "presupuesto", "costo mensual",
> "cuantas horas de equipo". Cargar **antes de implementar** y antes de
> comprometer un presupuesto con el cliente.

## Que es esto

La estimacion traduce el alcance tecnico a **dinero y tiempo**, antes de
escribir codigo. Su artefacto es `ESTIMACION.md`.

La regla que la sostiene:

> **Una estimacion sin escenario es una adivinanza con formato.** Si no se dice
> en que condiciones el numero es valido, no es un numero: es una aspiracion.

## Las cinco categorias de costo

Todo costo de un proyecto con agentes cae en una de estas cinco. Una estimacion
completa las cubre todas.

| # | Categoria | Que mide | Unidad | Cadencia |
|---|---|---|---|---|
| 1 | **Infraestructura cloud** | compute, base de datos, almacenamiento, red | moneda por mes | mensual |
| 2 | **Tokens de LLM** | consumo de modelos por el runtime de agentes y por el producto | tokens por mes | mensual |
| 3 | **Suscripciones recurrentes** | herramientas de terceros que se pagan todos los meses | moneda por mes | mensual |
| 4 | **Fee de equipo** | horas-persona de cada rol por periodo | moneda por periodo | por ronda / por mes |
| 5 | **Costo de construccion** | lo que cuesta construir antes de operar | moneda | una vez |

La quinta existe porque las otras cuatro son recurrentes: un proyecto puede
ser barato de operar y carisimo de construir, o al reves.

## Categoria 1: infraestructura cloud

Se estima **por componente del plan**, no con un numero global. Cada componente
del `PLAN.md` tiene su linea.

| Componente | Servicio (ejemplo) | Dimension | Supuesto | Costo mensual |
|---|---|---|---|---|
| API backend | <servicio de compute> | vCPU y memoria | <tamano de instancia> por <cantidad> | <moneda> |
| Base de datos | <motor relacional> | almacenamiento y compute | <tamano> con <conexiones> | <moneda> |
| Almacenamiento | <servicio de objetos> | GB | <GB> con crecimiento | <moneda> |
| Red y salida | <servicio de red> | GB transferidos | <GB por mes> | <moneda> |
| Observabilidad | <plataforma de metricas> | series y retencion | <cantidad> | <moneda> |
| Seguridad | <servicio de WAF o secretos> | Politicas | <cantidad> | <moneda> |
| **Subtotal** | | | | **<moneda>** |

**Reglas de la seccion de infra:**

- **Cada supuesto lleva su unidad.** "Una instancia pequena" no es un supuesto
  estimable; "2 vCPU, 4 GB de RAM" si.
- **La region y el plan se nombran.** El mismo servicio cambia de precio segun
  region y tipo de instancia. Sin eso, el numero no es reproducible.
- **El crecimiento va aparte.** Se estima el mes 1 y se proyecta el mes 6 con
  el factor de crecimiento declarado.
- **Los costos fijos que no se usan siguen se pagan.** Un cluster con tres
  replicas se factura completo, se use o no.

### La variable que se olvida: la salida a internet

El trafico de salida (egress) es la partida que mas sorprende, porque no
aparece en ningun calculo de recursos. Se estima aparte:

| Origen | Destino | Volumen mensual estimado | Costo |
|---|---|---|---|
| <servicio> | <otro servicio> | <GB> | <moneda> |
| API | <consumidor externo> | <GB> | <moneda> |

## Categoria 2: tokens de LLM

Se separa en **dos flujos**, porque se comportan distinto:

| Flujo | Quien consume | Como se mide |
|---|---|---|
| **Construccion** | los agentes que escriben codigo, specs y analisis | tokens por tarea completada |
| **Operacion** | los agentes del producto en manos del usuario final | tokens por sesion o por request |

### Formula de construccion

```
tokens_mes = (tareas_por_ronda x rondas_por_mes x tokens_por_tarea) x factor_reintento
```

| Parametro | Como se obtiene |
|---|---|
| tokens por tarea | tokens de entrada (contexto) + tokens de salida (respuesta) por iteracion, por el numero de iteraciones |
| factor de reintento | proporcion de tareas que se reintentan, tipicamente 1.2 a 1.5 |
| rondas por mes | del backlog y del ritmo del equipo |

### Formula de operacion

```
tokens_mes = usuarios_activos x sesiones_por_usuario x requests_por_sesion x tokens_por_request
```

Con un factor de cacheo explícito: si hay cache de contexto, los tokens de
entrada por request bajan de forma importante y eso **se escribe en la
estimacion**, no se descubre en produccion.

### Como se convierte tokens en dinero

| Modelo de uso | Como se costea |
|---|---|
| Tokens de entrada | `tokens_entrada x precio_por_1M_tokens_entrada` |
| Tokens de salida | `tokens_salida x precio_por_1M_tokens_salida` |
| Con cacheo | se costea el precio de cache hit, que es menor |

**Reglas de la seccion de tokens:**

- **Se separa entrada y salida.** tienen precios distintos.
- **Se declara el precio por million de tokens**, con su fuente y su fecha. Los
  precios cambian: una estimacion sin fecha es un numero que expira.
- **Se agrega el overhead de contexto.** El agente reenvia el historial, los
  archivos y el contexto del proyecto en cada iteracion. Un factor de 2 a 4
  sobre el prompt nominal es lo habitual.
- **Se incluye el gasto de los agentes de QA, revision y analisis**, no solo
  del que escribe codigo. Son flujos distintos con costos distintos.

## Categoria 3: suscripciones recurrentes

Herramientas de terceros que el equipo o el producto paga todos los meses.

| Suscripcion | Para que sirve | Plan | Costo mensual | Se cancela si no se usa |
|---|---|---|---|---|
| <herramienta de CI> | pipelines | <plan> | <moneda> | si |
| <servicio de gestion de secretos> | credenciales | <plan> | <moneda> | si |
| <servicio de soporte o<Producto> | operacion | <plan> | <moneda> | si |

**Regla:** cada suscripcion tiene la columna "se cancela si no se usa". Sin esa
columna, las suscripciones se acumulan y nadie las revisa. Se revisan una vez
por trimestre contra el uso real.

## Categoria 4: fee de equipo

El costo del equipo es el mas grande y el que mas subestima.

### Como se calcula

```
fee_equipo = horas_por_rol x tarifa_por_hora x cantidad_de_personas
```

| Rol | Horas por periodo | Tarifa por hora | Personas | Subtotal |
|---|---|---|---|---|
| arquitecto | <h> | <moneda/h> | <n> | <moneda> |
| backend senior | <h> | <moneda/h> | <n> | <moneda> |
| backend dev | <h> | <moneda/h> | <n> | <moneda> |
| frontend senior | <h> | <moneda/h> | <n> | <moneda> |
| frontend dev | <h> | <moneda/h> | <n> | <moneda> |
| qa | <h> | <moneda/h> | <n> | <moneda> |
| devops | <h> | <moneda/h> | <n> | <moneda> |
| lider tecnico | <h> | <moneda/h> | <n> | <moneda> |

**Las horas salen del backlog, no de la intuicion.** El esfuerzo T-shirt de cada
HU se convierte en horas con una tabla de conversion explicita:

| Tamano | Horas (base del equipo) |
|---|---|
| XS | <h> |
| S | <h> |
| M | <h> |
| L | <h> |

Esa tabla de conversion es la que hace auditable la estimacion. Sin ella, las
horas son una opinion.

### El fee de los agentes tambien es costo

Un equipo de agentes no es gratis: consume tokens (categoria 2), ocupa tiempo de
supervision humana y requiere verificacion. La supervision humana es el costo
oculto mas grande del modelo:

| Concepto | Horas por periodo | Como se mide |
|---|---|---|
| Revision de codigo de agentes | <h> | horas reales de la ronda anterior |
| Correccion de desvios | <h> |estry del tiempo real vs planificado |
| Verificacion de entregables | <h> | tiempo de qa |

## Los tres escenarios

Una estimacion sin escenario es una adivinanza. Se producen **tres**, con
supuestos distintos explicitados.

| | Conservador | Base | Optimista |
|---|---|---|---|
| Uso de LLM | alto (reintentos, contexto grande) | medio | bajo (bien cacheado, pocas iteraciones) |
| Crecimiento de datos | alto | medio | bajo |
| Horas de equipo | +30% sobre la tabla | tabla de conversion | -20% |
| Velocidad de entrega | mas rondas | lo planificado | menos rondas |
| Exito del proyecto | con los ajustes que genere el uso real | con los ajustes previstos | con la adopcion prevista |

### Las tres definiciones operativas

- **Conservador:** todo sale peor que lo previsto. Es el escenario con el que
  hay que poder sobrevivir: si el proyecto es viable en el conservador, es
  viable.
- **Base:** el escenario con el que se planifica. Es el unico que se usa para
  comprometer fechas.
- **Optimista:** todo sale mejor. Es el que se usa para evaluar si vale la pena
  invertir mas, nunca para comprometer.

**Regla dura:** el compromiso con el cliente se hace **siempre con el
escenario base**, y se declara que el conservador es el piso. Si se compromete
con el optimista, el proyecto arranca tarde el primer dia.

## Tabla consolidada

```
COSTO MENSUAL RECURRENTE
  Infraestructura cloud ................ <base>
  Tokens de LLM ......................... <base>
  Suscripciones recurrentes ............. <base>
  Fee de equipo (si es recurrente) ...... <base>
  ------------------------------------------------
  TOTAL MENSUAL .......................... <base>

COSTO DE CONSTRUCCION (una vez)
  Fee de equipo de construccion ......... <base>
  Herramientas y licencias de setup ...... <base>
  ------------------------------------------------
  TOTAL DE CONSTRUCCION ................. <base>
```

Con la misma tabla repetida para los tres escenarios, y un total ponderado si
se quiere un unico numero:

```
total_esperado = (conservador x p_conservador) + (base x p_base) + (optimista x p_optimista)
```

Las probabilidades se declaran **y se justifican**. Si no se puede justificar
ninguna distribucion, se usa el escenario base y se dice que la decision se
tomara con ese numero.

## Gate de la fase 5

| Check | Como se verifica | Bloqueante |
|---|---|---|
| `ESTIMACION.md` existe | archivo presente | si |
| Las 5 categorias estan presentes, aunque sea en 0 | revision | si |
| Cada linea de infra tiene su supuesto con unidad | revision | si |
| Tokens de entrada y salida estan separados | revision | si |
| El precio por million de tokens tiene fuente y fecha | revision | si |
| El overhead de contexto esta declarado | revision | si |
| Cada suscripcion dice si se cancela | revision | si |
| Las horas salen de una tabla de conversion | revision | si |
| Los tres escenarios estan completos | revision | si |
| El compromiso usa el escenario base | revision | si |
| El total esta comparado contra el tope de la constitucion | revision | si |
| Si se supera el tope, hay un plan de reduccion | revision | si |

**Sin estimacion aprobada no se implementa.** La decision economica es del
cliente, no del agente: el agente entrega el numero, el cliente decide.

### Cuando el total supera el tope

El tope de la seccion 5 de `CONSTITUTION.md` es vinculante. Cuando la
estimacion lo supera, no se implementa "a ver que pasa": se propone una de estas
salidas, **por escrito**:

| Salida | Que cambia | Que se pierde |
|---|---|---|
| Reducir alcance | se recortan HUs de la ronda | funcionalidad del alcance original |
| Reducir tier de infraestructura | ambiente mas economico | latencia y margen |
| Modelos mas economicos | menos capacidad de razonamiento | calidad en casos complejos |
| Cacheo aggressive | se agrega capa de cache | complejidad tecnica |
| Menos automatizacion | mas trabajo manual | capacidad del equipo |
| Ajustar el plazo | se extiende el calendario | fecha de entrega |
| Cambiar el tope | amendment a la constitucion | margen del cliente |

La opcion por defecto es **reducir alcance**, no subir el tope: el tope
representa una decision que alguien ya tomo.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Un solo numero de total | no se sabe en que condiciones se cumple | tres escenarios |
| Estimar la infra con un promedio | el promedio esconde el pico | estimar por componente |
| Olvidar el trafico de salida | aparece como sorpresa en produccion | linea propia de egress |
| Contar solo el prompt nominal | el contexto real es 2 a 4 veces | factor de overhead declarado |
| No separar entrada y salida | se subestima o se sobreestima | dos columnas |
| Horas inventadas | no hay de donde salen | tabla de conversion desde T-shirt |
| Olvidar el costo de supervisar agentes | el fee real es mayor | linea de supervision |
| Suscripciones sin politica de cancelacion | se acumulan sin revision | columna de cancelacion |
| Precios sin fecha | el numero expira sin avisar | fuente y fecha en cada precio |
| Comprometer con el optimista | el proyecto arranca tarde | comprometer con el base |
| Comparar solo contra el tope | no hay plan si se pasa | plan de reduccion escrito |
| Redondear a un numero redondo | esconde la incertidumbre | dos decimales y supuestos |

## Referencias

- `templates/estimacion.md` - plantilla completa con las 5 categorias y los 3
  escenarios
- `references/supuestos-costo.md` - guias de estimacion por categoria, con los
  supuestos que hay que declarar
- `dev-kit-project-constitution` - el tope de presupuesto que acota la estimacion
- `dev-kit-spec-analysis` - recalcula la estimacion cuando hay gaps
- `dev-kit-task-breakdown` - de donde salen las horas

### Archivos incluidos en esta skill

| Archivo | Tipo | Para que sirve |
|---|---|---|
| `templates/estimacion.md` | template | esqueleto de `ESTIMACION.md` con categorias y escenarios |
| `references/supuestos-costo.md` | referencia | guias de estimacion y supuestos por categoria |
