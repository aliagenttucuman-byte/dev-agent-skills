---
name: dev-kit-project-constitution
description: "Definir los principios fundacionales de un proyecto antes de escribir codigo: stack permitido, estandares de calidad, reglas de negocio, restricciones de presupuesto y tiempo, principios de UX y prohibiciones explicitas. CARGAR al arrancar un proyecto nuevo, al evaluar si una propuesta tecnica es admisible o cuando un agente propone algo fuera de politica."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [constitution, principles, governance, gates, planning]
    category: software-development
    related_skills: [dev-kit-sdd-workflow, dev-kit-spec-authoring, dev-kit-cost-estimation]
---

# Dev Kit - Constitucion del proyecto

> **Trigger:** "arrancar un proyecto", "definir principios", "que esta permitido
> usar aca", "el agente propuso una libreria que no corresponde", "cuales son las
> restricciones", "que no se puede hacer en este repo". Cargar ANTES de abrir el
> editor de codigo y ANTES de aprobar cualquier propuesta de stack.

## Que es esto

Una constitucion es el **documento que dice que esta permitido, que no, y con
que limites**, escrito antes de que exista el codigo. No es un wishlist ni una
vision: es un contrato verificable.

La diferencia con una guia de estilos:

| | Guia de estilos | Constitucion |
|---|---|---|
| Responde a | "como se escribe el codigo" | "que se construye y que no" |
| Se viola por | desviacion de formato |decision de diseno fuera de politica |
| Quien la aplica | el linter | el arquitecto y el gate de fase 1 |
| Consecuencia del incumplimiento | el linter falla | la propuesta se rechaza antes de codear |

La constitucion responde a una sola pregunta: **"este proyecto, en este
contexto, con estos limites, se construye asi"**. Por eso es por proyecto y no
universal: lo que es razonable para un sistema transaccional no lo es para un
prototipo de una semana.

## Que NO va aca

Tres cosas que se confunden con la constitucion:

1. **La especificacion funcional.** "Que endpoints existen" es spec, no constitution.
2. **El plan de implementacion.** "Como lo armamos" es plan.
3. **El presupuesto.** "Cuanto cuesta" es estimacion. La constitucion solo fija
   el **limite** que la estimacion tiene que respetar.

Si un parrafo dice "el sistema tiene que permitir registrar ventas", es spec.
Si dice "no se permite guardar datos de clientes en el vector store", es
constitucion.

## Las 8 secciones obligatorias

`CONSTITUTION.md` vive en la raiz del proyecto y tiene exactamente estas
secciones, en este orden. Ninguna es opcional.

| # | Seccion | Pregunta que responde | Owner |
|---|---|---|---|
| 1 | Principios rectores | Que endures ante conflicto entre requisitos | lider tecnico |
| 2 | Stack permitido | Que tecnologias se pueden usar | arquitecto |
| 3 | Estandares de calidad | Que tiene que cumplir cada entrega | lider tecnico |
| 4 | Reglas de negocio | Que es invariante del dominio | analista + arquitecto |
| 5 | Restricciones | Bajo que limites se opera | lider tecnico + negocio |
| 6 | Principios de UX | Como se siente la experiencia | diseno + frontend senior |
| 7 | Prohibiciones | Que esta prohibido, sin excepcion | arquitecto |
| 8 | Proceso de cambio | Como se modifica esta constitution | lider tecnico |

Detalle de cada seccion, con las preguntas guia y los errores tipicos:
`references/secciones-constitution.md`.

Esqueleto listo para copiar: `templates/constitution.md`.

## Seccion 2: stack permitido

El stack se declara como **lista cerrada por capa**, con la desviacion
documentada. "Por defecto se usa lo del kit" no es una politica: es una
ausencia de politica.

| Capa | Permitido | Desviacion permitida |
|---|---|---|
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2 + Pydantic v2 | framework distinto con justificacion escrita |
| Frontend | React 18 + TypeScript 5 + Vite | otro stack con justificacion escrita |
| Datos | PostgreSQL 16 + Alembic | otro motor si no hay transacciones ACID |
| Contenedores | Docker + Compose | orquestacion de plataforma con justificacion |
| CI | GitHub Actions | otro runner por restriccion de red |
| Lint y tipos | ruff + mypy | equivalente que corra igual en CI |
| Tests | pytest + Playwright | equivalente |
| Observabilidad | OpenTelemetry | equivalente |

Reglas de escritura de la tabla:

- **Una fila por capa.** Si una capa no esta en la tabla, no esta permitida.
- **La desviacion se escribe con la condicion que la habilita.** "Se puede usar
  otro ORM si la base ya esta en un motor no transaccional" es utilizable.
  "Se puede usar otro ORM" no lo es.
- **Toda libreria nueva entra por solicitud explicita**, no por defecto. La
  tabla no es una lista de sugerencias: es lo que el agente puede usar sin
  preguntar.

## Seccion 3: estandares de calidad

Los estandares son **umbrales medibles**, no adjetivos. "Codigo de buena
calidad" no es un estandar; "cobertura minima de 70% en el modulo de dominio" si.

| Estandar | Umbral | Como se verifica | Donde corre |
|---|---|---|---|
| Tipos | `mypy --strict` sin errores | comando de lint | CI |
| Formato | `ruff format --check` limpio | comando de lint | CI |
| Tests | cobertura >= 70% en dominio | `pytest --cov` | CI |
| Endpoints | contrato OpenAPI sin deviations | diff contra `specs/openapi.yaml` | CI |
| Migraciones | reversible en una transaccion | `alembic downgrade -1` | CI |
| Latencia | p95 < 400 ms en endpoints de lectura | metricas | staging |
| Errores | formato unico con correlation id | test de contrato | CI |

Regla: **cada estandar tiene un comando o un artefacto que lo prueba.** Un
estandar sin verificacion automatica es una intencion.

## Seccion 4: reglas de negocio

Las reglas de negocio son **invariantes**: afirmaciones que siempre son
verdades, mas alla de la implementacion. Se escriben en forma negable y
comprobable.

| Regla | Tipo | Test que la demuestra |
|---|---|---|
| Una operacion de cierre no puede modificar un periodo cerrado | invariante | test de transaccion |
| Todo alta de registro queda auditada con actor y timestamp | invariante | test de persistencia |
| Un usuario puede tener como maximo N roles activos | invariante | test de validacion |
| El calculo de totales usa aritmetica decimal | invariante | test de redondeo |

Estructura recomendada para cada regla:

```
REGLA: <afirmacion en una linea, en presente>
TIPO: invariante | politica | convencion
PRUEBA: <como se verifica>
```

Una regla que no tiene `PRUEBA` es una preferencia. Las preferencias van a la
seccion de UX o a la guia de estilos, no a las reglas de negocio.

## Seccion 5: restricciones

Las restricciones acotan lo que se puede hacer. Se escriben con **numero y
unidad**, siempre.

| Dimension | Como se expresa | Ejemplo de forma valida |
|---|---|---|
| Presupuesto de infra | tope mensual en moneda | "tope de 400 USD por mes en cloud" |
| Presupuesto de LLM | tope mensual de tokens | "tope de 20M de tokens por mes" |
| Plazo | fecha o ventana | "primera entrega antes del dia 30 del proyecto" |
| Carga | usuarios concurrentes | "soportar 200 usuarios concurrentes" |
| Datos | clasificacion y retencion | "retencion de 90 dias, sin dato sensible" |
| Compliance | marco aplicable | "auditoria de accesos obligatoria" |
| Red | salida a internet | "sin trafico saliente a terceros" |

Regla de formato: **toda restriccion sin unidad es una intencion y no se
acepta.** "Bajo presupuesto" no es una restriccion. "Tope de 400 USD mensuales
en infraestructura, con alerta al 80%" si.

La restriccion de presupuesto se escribe en dos partes: el tope y el
comportamiento cuando se alcanza. Que pasa en el 80%, en el 100%, y quien
decide. Sin eso, el limite se descubre cuando ya se paso.

## Seccion 7: prohibiciones

Las prohibiciones son la parte que mas se subestima y la que mas dano
previene. Se listan de forma explicita y corta.

| Prohibicion | Motivo | Como se detecta |
|---|---|---|
| No loguear datos personales de clientes | exposicion de datos | regla de lint + review |
| No llamar a servicios externos sin capa de cache | costo no acotado | revision de dependencias |
| No persistir secretos en el repo | fuga de credenciales | scanner de secretos |
| No agregar dependencias sin version pineada | builds no reproducibles | lockfile en CI |
| No hacer migraciones destructivas sin plan de rollback | perdida de datos | revision del PR |
| No desactivar los gates de CI | erosiona el proceso | proteccion de rama |

Cada prohibicion tiene **un motivo** y **una forma de deteccion**. Una
prohibicion sin deteccion se convierte en una sugerencia en tres semanas.

## Como se escribe la constitucion

Proceso de una sesion de trabajo, no de un documento que se redacta solo:

1. **Partir de las restricciones reales.** Sin informacion de quien decide
   (negocio, presupuesto, tiempo, compliance), no hay constitucion posible.
   Anotar las que no se conocen como `PENDIENTE` con su responsable.
2. **Cerrar el stack.** Cada capa con su default y su condicion de
   desviacion. Lo que no se decide aca, se decide de hecho en el primer PR.
3. **Fijar umbrales medibles.** Solo los que el proyecto va a medir. Un umbral
   que nadie corre es decorativo.
4. **Escribir las reglas de negocio** con su prueba asociada.
5. **Cerrar las prohibiciones** con motivo y deteccion.
6. **Revisar en sesion de equipo.** Las constituciones se escriben solos y
   fallan.
7. **Versionar el artefacto.** El repositorio es la fuente de verdad.

Orden de trabajo recomendado: restricciones primero, stack segundo, calidad
tercero, reglas de negocio cuarto, prohibiciones quinto. Al reves se escribe
una constitution cruzada, que es un documento decorativo.

## Gate de la fase 1

El gate es binario. Se pasa o no se pasa.

| Check | Como se verifica | Bloqueante |
|---|---|---|
| `CONSTITUTION.md` existe en la raiz | archivo presente | si |
| Tiene las 8 secciones | lectura de encabezados | si |
| Stack permitido con lista cerrada | tabla por capa | si |
| Toda restriccion con unidad | revision de la seccion 5 | si |
| Toda regla de negocio con `PRUEBA` | revision de la seccion 4 | si |
| Toda prohibicion con deteccion | revision de la seccion 7 | si |
| No hay `PENDIENTE` sin responsable | revision | no |
| Revisado por el lider tecnico | registro de revision | si |

**Sin `CONSTITUTION.md` no hay proyecto.** No se abre el backlog, no se
escribe el spec, no se genera codigo. Es la unica fase del flujo que bloquea
el arranque de todas las demas.

Los `PENDIENTE` con responsable no bloquean: bloquea que la decision se tome
sin dueño.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Constitucion copiada de otro proyecto | codifica contexto que no aplica | reescribir desde las restricciones reales |
| Solo stack y linter | no dice que no hacer | agregar prohibiciones con motivo |
| "Usar lo estandar del kit" como politica | deja todo sin decidir | cerrar cada capa con default y condicion |
| Restricciones sin numero | no se puede verificar ni cobrar | poner unidad y comportamiento al alcanzar el tope |
| Reglas de negocio sin prueba | son preferencias disfrazadas | agregar `PRUEBA` o moverlas |
| Prohibiciones sin deteccion | se erosiona en semanas | agregar como se detecta |
| Escribirla despues de arrancar | legitima el codigo ya escrito | no tiene gate de fase 1 |
| Revisarla en cada sprint completa | nadie la usa | versionarla y amendarla por cambio puntual |
| Un documento largo sin owner | se desactualiza en silencio | un owner explicito y fecha de revision |

## Referencias

- `templates/constitution.md` - esqueleto de `CONSTITUTION.md`, copiable tal cual
- `references/secciones-constitution.md` - detalle de cada seccion, preguntas
  guia y errores tipicos
- `dev-kit-sdd-workflow` - donde vive esta fase en el flujo de 9 pasos
- `dev-kit-spec-authoring` - el spec que se deriva de la constitucion
- `dev-kit-cost-estimation` - la estimacion que se mide contra el tope

### Archivos incluidos en esta skill

| Archivo | Tipo | Para que sirve |
|---|---|---|
| `templates/constitution.md` | template | esqueleto de `CONSTITUTION.md` con las 8 secciones |
| `references/secciones-constitution.md` | referencia | guia de escritura seccion por seccion |
