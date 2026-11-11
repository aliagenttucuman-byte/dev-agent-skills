---
name: dev-kit-task-breakdown
description: "Convierte un PLAN.md en un TASKS.md asignable a agentes. Una tarea = un agente = un resultado verificable, con contexto explicito obligatorio. CARGAR cuando hay que partir un plan en tareas, escribir el backlog de ejecucion o preparar el trabajo para repartir entre agentes."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tasks, breakdown, planning, assignment, context]
    category: software-development
    related_skills: [dev-kit-sdd-workflow, dev-kit-agent-team, dev-kit-agent-routing, dev-kit-project-bootstrap]
---

# Dev Kit - Task Breakdown

> **Trigger:** "partir el plan en tareas", "escribir TASKS.md", "que tarea hace
> cada agente", "el plan es muy grande para una tarea", "que contexto le paso al
> agente". Cargar esta skill ANTES de repartir trabajo entre agentes.

## Que es esto

El procedimiento que convierte un plan aprovado en una lista de tareas que un
agente puede ejecutar **sin preguntar nada**.

No es descomposicion academica. Es un contrato de ejecucion: cada fila de
`TASKS.md` es una unidad de trabajo con un responsable, un contexto y una
prueba de que salio bien.

La regla que lo gobierna:

> **Una tarea = un agente = un resultado verificable.** Si el resultado no se
> puede comprobar con un comando, no es una tarea: es una intencion.

## La regla de las tres partes

Una fila de `TASKS.md` solo es una tarea si tiene las tres:

| Parte | Que es | Si falta |
|---|---|---|
| **Responsable** | un unico rol, no un equipo | dos agentes tocan el mismo codigo |
| **Contexto** | lo que el agente necesita saber para arrancar | el agente pierde el intento adivinando |
| **Criterio verificable** | el comando o la prueba que demuestra el resultado | no hay forma de saber si salio bien |

**Regla del contexto:** el agente arranca con lo que dice la tarea. Si necesita
preguntar, la tarea estaba incompleta. Si el agente **supone** algo que no
decia la tarea, el supuesto era contexto que faltaba y el resultado no es
confiable.

## 1. De PLAN.md a TASKS.md

El plan dice **como se construye**. El breakdown dice **quien hace cada parte**.

| Artefacto | Pregunta que responde | Unidad |
|---|---|---|
| `PLAN.md` | como se construye | componente o paso |
| `TASKS.md` | quien hace que | una tarea con resultado verificable |

El paso del plan al breakdown tiene tres movimientos:

1. **Recortar:** el plan puede traer pasos de 30 lineas. Una tarea que no cabe
   en un commit revisable se parte.
2. **Asignar:** cada tarea va a un unico dueno de capa.
3. **Anclar:** cada tarea declara de donde saca su contexto.

### El filtro de tamaño

| Senal | Que hacer |
|---|---|
| La tarea toca mas de 3 carpetas | partir por capa o por endpoint |
| La tarea tiene mas de 3 criterios de aceptacion | puede ser dos tareas |
| El resultado son mas de 10 archivos nuevos | partir por componente |
| La tarea dice "implementar el modulo X" | partir por caso de uso |
| La tarea no tiene comando de verificacion | no es una tarea todavia |

**Regla:** una tarea que un agente no puede entregar en una sesion de trabajo
concentrado esta mal partida. Es preferible un DAG de 8 tareas que un bloque
de 3 tareas gigantes.

### El filtro de una capa

Una tarea pertenece a **una sola capa**. Si necesita tocar dos, son dos tareas
con un handoff.

| Cruza capas | Se parte en |
|---|---|
| contrato + implementacion | una tarea de contrato (arquitecto) y una de implementacion |
| backend + frontend | una tarea de backend y una de frontend, unidas por el contrato |
| codigo + despliegue | una de codigo y una de pipeline |
| logica + tests | **no se parte**: los tests van con la logica |

La excepcion importante: **los tests nunca son una tarea aparte**. La
implementacion incluye sus pruebas. Una tarea sin pruebas es una tarea a medio
hacer.

## 2. Que contexto viaja (obligatorio)

El contexto es lo que hace que la tarea sea ejecutable sin depender de la
memoria de una conversacion anterior. Viaja en la tarea, escrito.

### Los seis campos obligatorios

| Campo | Que lleva | Ejemplo |
|---|---|---|
| **Objetivo** | una frase: que queda distinto al terminar | "el endpoint de listar pedidos devuelve paginado por cursor" |
| **Punto de partida** | el artefacto del que sale: contrato, plan, ADR | `specs/openapi.yaml` seccion Pedidos |
| **Alcance** | que archivos o modulos toca | `src/app/api/routes/orders.py`, `src/app/services/order_service.py` |
| **Restricciones** | las reglas del proyecto que aplican | "regla de dependencia: `api` no importa `infra` directo" |
| **Fuera de alcance** | lo que NO debe tocar | "no cambiar el contrato de `POST /pedidos`" |
| **Criterio de aceptacion** | comandos verificables | `pytest -q tests/unit/test_order_service.py` |

### Que NO viaja

- El historial de una conversacion: se entrega el resumen y el artefacto.
- Decisiones de producto no escritas: si no esta en el plan o en un ADR, no es
  contexto, es rumor.
- Credenciales, tokens o datos de negocio de terceros.
- Supuestos del agente anterior que no se verificaron.

### La prueba del arranque en frio

> **Si un agente nuevo, sin historial y sin acceso a la conversacion, puede
> ejecutar la tarea y pasar su criterio de aceptacion, la tarea esta completa.**

Si hay que responder una pregunta para empezar, esa respuesta va en la tarea.
Se responde antes de asignar, no durante.

## 3. El formato de TASKS.md

Cada tarea es una seccion con campos fijos. El formato tabular del indice va
arriba; el detalle va abajo.

### Indice tabular

```markdown
| ID | Tarea | Capa | Responsable | Depende de | Criterio de aceptacion | Estado |
|----|-------|------|-------------|------------|------------------------|--------|
| T-01 | Modelo de dominio de Pedido | dominio | backend senior | - | `pytest -q tests/unit/test_pedido.py` | pendiente |
| T-02 | Repositorio de Pedido en SQLAlchemy | datos | backend dev | T-01 | `pytest -q tests/integration/test_pedido_repo.py` | bloqueada |
| T-03 | Endpoint de listar pedidos | implementacion | backend dev | T-02 | `pytest -q tests/contract/test_pedidos.py` | bloqueada |
| T-04 | Cliente HTTP de pedidos | frontend | frontend dev | T-03 | `npm run test -- pedidos` | bloqueada |
| T-05 | Pantalla de lista de pedidos | implementacion | frontend dev | T-04 | `npx playwright test pedidos.spec.ts` | bloqueada |
| T-06 | Revision cruzada de la feature | verificacion | qa | T-05 | <checklist de criterios de la HU> | bloqueada |
```

### Detalle de cada tarea

```markdown
## T-01 - Modelo de dominio de Pedido

| Campo | Valor |
|---|---|
| Objetivo | La entidad Pedido existe con sus invariantes y transiciones de estado |
| Capa | dominio |
| Responsable | backend senior |
| Depende de | - |
| Punto de partida | `specs/openapi.yaml` (Pedidos), `PLAN.md` seccion Modelo de datos |
| Alcance | `src/app/domain/entities/pedido.py`, `src/app/domain/rules/pedido_rules.py` |
| Fuera de alcance | la tabla del ORM, la API, los endpoints |
| Restricciones | la entidad no importa el framework; los id son `str` (UUID) |
| Criterio de aceptacion | `pytest -q tests/unit/test_pedido.py` pasa con 6 casos |
| Tamano | pequeno |
```

Plantilla completa: `templates/tasks.md`.

### Los campos, uno por uno

| Campo | Regla |
|---|---|
| ID | `T-NN`, correlativo, sin reutilizar |
| Tarea | el sustantivo del resultado, no la accion: "Modelo de Pedido", no "Crear modelo" |
| Capa | una de: producto, contrato, diseno, implementacion, datos, verificacion, operacion |
| Responsable | un unico rol del roster |
| Depende de | IDs de tareas, o `-` |
| Criterio de aceptacion | el comando, no la descripcion |
| Estado | pendiente / bloqueada / en curso / hecha / rechazada |
| Tamano | pequeno / medio / grande (guia de reparto, no estimacion formal) |

## 4. Dependencias y orden

### Del plan al DAG

Las dependencias salen del plan, no de la intuicion. En el plan hay una tabla
de orden de implementacion: esa tabla es la fuente.

```markdown
| Paso | Que se construye | Depende de | Entregable verificable |
|---|---|---|---|
| 1 | Esquema y reglas de Pedido | - | entidad + tests unitarios |
| 2 | Migracion inicial | 1 | migracion reversible |
| 3 | Repositorio | 1, 2 | repositorio + test de integracion |
```

Al convertir, cada paso del plan puede dar lugar a varias tareas, pero **una
tarea nunca puede depender de algo posterior**.

### Las tres clases de dependencia

| Clase | Que es | Que exige |
|---|---|---|
| **Dura** | sin esto no se puede empezar | dependencia fuerte, orden total |
| **De contrato** | hace falta la forma, no la implementacion | se puede trabajar en paralelo si el contrato esta cerrado |
| **De convencion** | conviene respetar el estilo, no bloquea | se resuelve leyendo el codigo existente |

**Regla:** la dependencia blanda no va en la columna "Depende de". Va en
"Restricciones". Si todo esta bloqueado por todo, el DAG no dice nada.

### Paralelismo real

Dos tareas pueden ir en paralelo si:

1. No tocan los mismos archivos.
2. La dependencia entre ellas es de contrato, no de codigo.
3. El contrato que las une esta cerrado y versionado.

| Situacion | Paralelizables |
|---|---|
| Backend y frontend con el OpenAPI cerrado | si |
| Backend y frontend sin contrato cerrado | no |
| Dos tareas del mismo modulo | no |
| Tarea de tests y tarea de codigo | no: van juntas |

### Cycles

Un ciclo en el DAG significa que la descomposicion esta mal: hay dos tareas que
se necesitan mutuamente. Se rompe uniendo las dos en una sola tarea, o
introduciendo el artefacto que las separa.

```
T-01 <-> T-02   # cycle: T-02 necesita el esquema de T-01,
                 #        T-01 necesita la tabla de T-02
```

## 5. Criterio de aceptacion verificable

El criterio de aceptacion es lo que separa "hecho" de "hecho de verdad".

| Forma | Es valido |
|---|---|
| `pytest -q tests/unit/test_pedido.py` | si |
| `npm run lint && npm run typecheck` | si |
| `curl` al endpoint con la respuesta esperada | si |
| "el codigo compila" | no: no prueba el comportamiento |
| "el endpoint funciona" | no: no hay forma de comprobarlo |
| "las pruebas pasan" | no: sin el comando no se sabe cuales |
| "se sigue el estilo del proyecto" | no: no es automatizable |

**Regla:** el criterio nombra el comando y lo que ese comando prueba. El agente
no decide si el criterio se cumplio: lo ejecuta y lee el codigo de salida.

### Del criterio a la historia

Cada criterio de aceptacion de la historia debe estar cubierto por al menos
un criterio de tarea. Si un criterio de la historia no aparece en ninguna
tarea, o la historia esta incompleta o el breakdown la perdio.

```markdown
| Criterio de la HU | Criterio de la tarea que lo cubre |
|---|---|
| "el listado pagina por cursor" | T-03 `pytest -q tests/contract/test_pedidos.py` |
| "el total no se redondea" | T-01 `pytest -q tests/unit/test_pedido.py` |
```

## 6. Como se usa

1. **Leer el plan** y extraer la tabla de orden de implementacion.
2. **Recortar** cada paso en tareas que quepan en una sesion y en una capa.
3. **Asignar** cada tarea al dueno de su capa segun el roster.
4. **Anclar** cada tarea con los seis campos de contexto.
5. **Anclar** cada criterio al comando que lo prueba.
6. **Cruzar** criterios de tareas contra criterios de las historias.
7. **Verificar** que no hay ciclos y que no hay dos tareas en la misma capa sobre
   los mismos archivos.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Tarea "implementar el modulo de pedidos" | no hay resultado verificable | partir por caso de uso |
| Tarea sin comando de aceptacion | no se sabe si salio bien | todo criterio es un comando |
| Tarea sin contexto | el agente adivina y falla | los seis campos obligatorios |
| Dos agentes en la misma tarea | conflicto silencioso | un responsable por tarea |
| Tarea que toca dos capas | se pierde la revision cruzada | partir con handoff |
| Tests como tarea aparte | el codigo llega sin pruebas | los tests van con la logica |
| Dependencias blandas como bloqueos | el DAG dice que todo espera a todo | dependencias blandas a "Restricciones" |
| Tareas sin tamano | no se sabe como repartirlas | pequeno / medio / grande |
| Numeros de tarea reutilizados | se rompen las referencias | correlativos, sin reciclar |
| Estimar en horas dentro de la tarea | se confunde el tamano con el esfuerzo | usar el campo Tamano |
| Agregar alcance durante la ejecucion | el trabajo crece sin reestimacion | "Fuera de alcance" explicito |
| Breakpoint de plan no cubierto | la historia se pierde en el camino | cruzar criterios de HU contra tareas |

## Referencias

### Skills relacionadas

- `dev-kit-sdd-workflow` - fase de tareas dentro del flujo completo.
- `dev-kit-agent-team` - roster que define el dueno de cada capa.
- `dev-kit-agent-routing` - decide el agente cuando la tarea no trae responsable.
- `dev-kit-project-bootstrap` - genera el proyecto donde se ejecutan las tareas.

### Archivos de esta skill

| Archivo | Contenido |
|---|---|
| `templates/tasks.md` | esqueleto de TASKS.md con indice tabular y detalle por tarea |
| `references/breakdown-criterios.md` | filtros de particion, dependencias y casos borde |
