---
name: dev-kit-orchestrator
description: "Loop de orquestacion con agentes: estados, descomposicion en tareas verificables, DAG con batches paralelos, reintentos, escalamiento y gates entre fases. CARGAR cuando hay que ejecutar un plan con varios agentes, coordinar trabajo en paralelo o diagnosticar un fallo de una tanda de agentes."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [orchestration, agents, dag, workflow, retries]
    category: software-development
    related_skills: [dev-kit-agent-team, dev-kit-agent-routing, dev-kit-task-breakdown, dev-kit-sdd-workflow]
---

# Dev Kit - Orquestador

> **Trigger:** "ejecuta el plan con los agentes", "coordina a los agentes en
> paralelo", "uno de los agentes fallo", "reparte el trabajo en el DAG",
> "que estado tiene la ejecucion". Cargar esta skill ANTES de correr una tanda
> de tareas con varios agentes.

## Que es esto

El procedimiento que convierte un plan aprobado en **ejecucion coordinada**:
parte el objetivo, arma el grafo de dependencias, reparte los batches
paralelos, corre los agentes, verifica cada resultado y decide que hacer
cuando algo falla.

Su artefacto es el grafo de tareas (`templates/task-graph.yaml`) mas el registro
de ejecucion con el estado final de cada nodo.

La regla que lo gobierna:

> **El orquestador no implementa codigo de negocio.** Coordina, verifica y
> escala. Si escribe la funcionalidad, se pierde la revision cruzada y el
> resultado no lo hizo el agente responsable de esa capa.

## La regla dura

| El orquestador SI | El orquestador NO |
|---|---|
| parte el objetivo en tareas | escribe la funcion que la tarea pide |
| construye el DAG y los batches | implementa un caso borde "para avanzar" |
| asigna cada tarea a un agente del roster | hace el trabajo de otro rol |
| corre el comando de verificacion | decide que el criterio se cumplio sin correrlo |
| reintenta, escala o descarta | improvisa alcance nuevo |
| escribe el estado y la evidencia | declara entregado sin evidencia |

**Como se verifica:** si el diff del orquestador toca archivos de la aplicacion,
el gate G6 falla y el fragmento se revierte.

## 1. Los siete estados

El loop es una maquina de estados explicita. Cada estado tiene entrada, accion y
salida. El grafo completo esta en `references/estados-y-transiciones.md`.

| Estado | Entrada | Accion | Salida |
|---|---|---|---|
| `idle` | objetivo sin procesar | leer objetivo, plan y roster | objetivo normalizado |
| `decomposing` | objetivo normalizado | partir en tareas con criterio verificable | lista de tareas |
| `assigning` | lista de tareas | mapear cada tarea a un agente | DAG con batches |
| `executing` | DAG con batches | correr los batches, un agente por nodo | resultados con evidencia |
| `verifying` | resultados de ejecucion | correr el criterio de aceptacion de cada nodo | pass/fail por nodo |
| `done` | todos los nodos en pass | consolidar el resultado y el reporte | entregable |
| `failed` | nodo irrecuperable o gate roto | cortar el batch, escalar | escalamiento o replanificacion |

### Las transiciones validas

```
idle -> decomposing -> assigning -> executing -> verifying -> done
                                  |            |           |
                                  +---> failed <-+---------+
```

| Transicion | Condicion |
|---|---|
| `executing -> verifying` | al menos un nodo del batch termino con salida |
| `verifying -> executing` | hay nodos en fail reintentables y quedan intentos |
| `verifying -> assigning` | hace falta partir una tarea en dos |
| `verifying -> failed` | un nodo agoto sus reintentos o un gate se rompio |
| `failed -> decomposing` | el fallo fue de descomposicion, no del agente |

**Regla:** `failed` no es terminal: es una pausa con escalamiento. El loop vuelve
a entrar por `decomposing`, `assigning` o `executing` segun la causa que
seccion 6 clasifique.

## 2. Reglas de descomposicion

**Regla 1: una tarea = un agente = un output verificable.** Si el resultado no
se comprueba con un comando, no es una tarea: es una intencion.

**Regla 2: el contexto es explicito.** Cada tarea lleva los seis campos de
contexto (objetivo, punto de partida, alcance, restricciones, fuera de alcance,
criterio de aceptacion). El agente arranca con lo que dice la tarea, sin
historial de conversacion.

**Regla 3: granularidad homogenea.** El tamano se decide por **cantidad de
criterios de aceptacion**, no por horas estimadas. Una tarea con 4 criterios
suele esconder dos tareas: se parte por criterio.

| Tamano | Volumen | Se usa cuando |
|---|---|---|
| pequeno | un archivo o una funcion, un criterio | hay mucho trabajo independiente |
| medio | un modulo o un endpoint con sus pruebas | es el tamano por defecto |
| grande | mas de 3 carpetas o 3 criterios | casi siempre esta mal partido |

Si una tarea toca dos capas, necesita un artefacto que aun no existe, no tiene
comando de verificacion o pisa los archivos de otra tarea abierta, se parte o
se serializa.

## 3. Construccion del DAG

El DAG sale de las dependencias declaradas en `TASKS.md`. El orquestador lo
ordena con **Kahn por niveles**: en cada ronda sale todo nodo cuyas
dependencias ya salieron. Cada ronda es un **batch** y todos sus nodos son
paralelizables.

```python
def topological_batches(tasks):
    """Kahn por niveles: cada batch es un conjunto paralelizable.
    tasks: dicts con "id" y "depends_on". Levanta ValueError si hay ciclo.
    """
    remaining = {t["id"]: set(t.get("depends_on", [])) for t in tasks}
    done, batches = set(), []
    while remaining:
        ready = sorted(t for t, deps in remaining.items() if not deps - done)
        if not ready:
            raise ValueError("ciclo detectado en: " + ",".join(sorted(remaining)))
        batches.append(ready)
        done.update(ready)
        for t in ready:
            remaining.pop(t)
    return batches
```

### Las tres validaciones antes de ejecutar

| Validacion | Error si | Como se corrige |
|---|---|---|
| sin ciclos | Kahn no puede ordenar | unir las dos tareas en conflicto |
| sin dependencias colgantes | un id depende de algo inexistente | corregir el id o crear el nodo |
| sin solapamiento de archivos | dos nodos del mismo batch tocan el mismo archivo | serializar o separar el alcance |

Un DAG invalido no se ejecuta "a ver que pasa". Se devuelve a `assigning`.

### Los batches

- Un batch no puede tener dos nodos que toquen el mismo archivo, ni dos nodos
  de la misma capa que produzcan el mismo artefacto.
- Si un batch tiene mas nodos que los slots de ejecucion disponibles, se divide
  en sublotes por orden de dependencia, sin cambiar el DAG.

## 4. Gates entre fases

Un gate es una condicion verificable que no se puede saltar. Si falla, el loop
vuelve al estado anterior con la evidencia del fallo.

| Gate | Entre | Se comprueba con | Si falla |
|---|---|---|---|
| **G1 - descompuesto** | `decomposing` y `assigning` | 6 campos de contexto y 1 comando de aceptacion por tarea | volver a `decomposing` |
| **G2 - asignado** | `assigning` y `executing` | un unico agente del roster por tarea, dentro de su capa | reasignar o partir |
| **G3 - grafo valido** | `assigning` y `executing` | sin ciclos, sin deps colgantes, sin solapamiento en el batch | volver a `assigning` |
| **G4 - ejecucion** | `executing` y `verifying` | cada nodo termino con salida y evidencia adjunta | reintentar o clasificar el fallo |
| **G5 - verificacion** | `verifying` y `done` | todos los criterios de aceptacion en pass | reintentar, escalar o `failed` |
| **G6 - entrega** | `done` | el diff no lo escribio el orquestador | deshacer el fragmento del orquestador |

**G6 protege la regla dura.** El orquestador comprueba, antes de entregar, que
ningun archivo de la aplicacion fue modificado por el propio orquestador.

## 5. Politica de reintentos

El reintento no es "volver a correr lo mismo". Es **correr de nuevo con una
variable cambiada**.

| Regla | Valor |
|---|---|
| intentos maximos por nodo | 3 |
| secuencia de espera | 5s, 20s, 60s, con jitter aleatorio |
| reintento identico | prohibido: si la entrada y la estrategia no cambian, es tiempo quemado |
| alcance del reintento | mas pequeno que el original, nunca mas grande |
| evidencia que se adjunta | salida del comando, error literal, ultimo estado del nodo |

**Regla del tercer fallo:** al tercer intento fallido el nodo no se reintenta
mas. Pasa a `failed` con la evidencia acumulada y se escala.

## 6. Taxonomia de fallos

Todo fallo de `executing` o `verifying` se clasifica antes de decidir. La
clasificacion determina si se reintenta, se escala o se descarta.

| Tipo | Senal tipica | Reintento | Accion | Dueño |
|---|---|---|---|---|
| **error de agente** | excepcion, herramienta caida, sintaxis invalida | si | reintentar con el error literal | agente |
| **contexto faltante** | el agente pregunta o asume un supuesto | no | reconstruir el handoff y reasignar | orquestador |
| **dependencia fallida** | un nodo previo quedo en fail | no | bloquear los dependientes y esperar | orquestador |
| **spec ambigua** | dos interpretaciones validas del requisito | no | escalar con el caso concreto | arquitectura |
| **verificacion fallida** | el criterio de aceptacion no pasa | si | cambiar la estrategia, no repetir el intento | agente |
| **timeout** | se supero el limite de tiempo del nodo | si, una vez | partir la tarea en dos, mas chica | orquestador |
| **conflicto** | dos agentes escribieron el mismo archivo | no | serializar, revertir el segundo y reasignar | orquestador |

Los cuatro tipos sin reintento se corrigen antes de volver a correr. El
`timeout` se reintenta una sola vez y con alcance menor. `verificacion fallida`
deja de reintentarse en el tercer fallo.

### Formato del escalamiento

El escalamiento no es una queja: es un paquete con evidencia. Los diez campos
obligatorios estan en `references/estados-y-transiciones.md`.

```
ESCALAMIENTO
- Desde:      <rol de origen>       - A:      <rol de destino>
- Tarea:      <id>                  - Tipo:   <tipo de fallo>
- Sintoma:    <que se observa>      - Esperado: <que deberia pasar>
- Evidencia:  <salida del comando>  - Intentos: <n> de <max>
- Impacto:    <que queda bloqueado> - Propuesta: <opcion A> | <opcion B>
```

## 7. El registro de ejecucion

Cada nodo deja una linea. Sin registro no hay verificacion, y sin verificacion
no hay entrega. El formato completo esta en `templates/task-graph.yaml`.

```yaml
run_id: <id de la corrida>
state: executing
batches:
  - batch: 1
    nodes:
      - id: T-01
        agent: backend dev
        state: done
        attempts: 1
        verification: "pytest -q tests/unit/test_pedido.py"
        result: pass
        evidence: "6 passed in 0.42s"
      - id: T-02
        agent: backend dev
        state: failed
        attempts: 3
        failure_type: verificacion
        evidence: "E   AssertionError: expected 2 rows, got 1"
        escalation: <id del escalamiento>
```

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| El orquestador escribe la funcionalidad | se pierde la revision cruzada y el gate G6 | asignar la tarea y esperar |
| Correr todo en paralelo sin DAG | dos agentes escriben el mismo archivo | construir el DAG y sus batches |
| Reintentar identico | quema tiempo con la misma variable | cambiar estrategia o escalar |
| Declarar un nodo en pass sin correr el comando | el fallo aparece en produccion | el pass se lee del codigo de salida |
| Aceptar "deberia funcionar" como evidencia | no hay forma de comprobarlo | exigir la salida del comando |
| Ignorar el ciclo en el DAG | el loop nunca avanza | unir las tareas en conflicto |
| Ampliar la tarea en caliente | el trabajo crece sin control | "Fuera de alcance" explicito |
| Escalar sin evidencia | nadie puede decidir sin ver el fallo | adjuntar la salida literal |
| Confundir timeout con error | se reintenta algo que no es reintentable | clasificar antes de actuar |
| Marcar el lote completo en fail por un nodo | se descarta trabajo valido | clasificar nodo por nodo |
| Escalar al mismo rol tres veces | la escalacion anterior no se leyo | cambiar de dimension de escalamiento |
| Saltarse un gate "porque esta casi listo" | un gate decorativo no es un gate | correr el gate o devolver el estado |

## Referencias

### Skills relacionadas

- `dev-kit-agent-team` - roster que define quien puede hacer cada tarea.
- `dev-kit-agent-routing` - decide el agente cuando la tarea no trae responsable.
- `dev-kit-task-breakdown` - produce las tareas y el DAG que el orquestador ejecuta.
- `dev-kit-sdd-workflow` - flujo completo donde vive la fase de ejecucion.

### Archivos de esta skill

| Archivo | Contenido |
|---|---|
| `templates/task-graph.yaml` | formato del DAG de tareas y del registro de ejecucion |
| `references/estados-y-transiciones.md` | maquina de estados completa, transiciones y reglas de reintento |
