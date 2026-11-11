# Estados y transiciones del orquestador

Referencia de `dev-kit-orchestrator`. La maquina de estados completa, las
reglas de reintento y el formato de escalamiento.

---

## La maquina de estados

```
    +--------+
    |  IDLE  |<----------------------+
    +--------+                       |
        |                            | reset()
        | receive_goal()             |
        v                            |
   +--------------+                  |
   | DECOMPOSING  |                  |
   +--------------+                  |
     |         |                    |
     | ok      | error               |
     v         v                    |
 +--------+  +--------+              |
 |ASSIGNING|  | FAILED |------------+
 +--------+  +--------+
     | ok      | error
     v         v
 +---------+  +--------+
 |EXECUTING|  | FAILED |----------------+
 +---------+  +--------+                |
     |         |                       |
     |         | unrecoverable         |
     |         +-----------------------+
     | all batches complete
     v
 +----------+
 |VERIFYING |
 +----------+
     |    |
     | ok | gaps found
     v    +--------------> EXECUTING
 +------+               (iteracion, max 3)
 | DONE |
 +------+
```

---

## Los estados

| Estado | Que esta pasando | Salida valida |
|---|---|---|
| `idle` | Sin objetivo. Espera | `receive_goal()` |
| `decomposing` | Analiza el goal y arma el grafo de tareas | `decomposition_ok()`, `decomposition_failed()` |
| `assigning` | Mapea cada tarea a un agente | `all_assigned()`, `assignment_failed()` |
| `executing` | Corre los batches del plan | `all_batches_complete()`, `unrecoverable_failure()` |
| `verifying` | Verifica que el resultado cumple los criterios | `verification_passed()`, `gaps_found()` |
| `done` | Entrega completa | `reset()` |
| `failed` | Fallo no recuperable | `reset()` despues de intervencion humana |

## Las transiciones validas

| Desde | Hacia | Condicion |
|---|---|---|
| `idle` | `decomposing` | Llego un goal |
| `decomposing` | `assigning` | El grafo es valido (sin ciclos, todas las tareas con output) |
| `decomposing` | `failed` | No se pudo descomponer en tareas con output verificable |
| `assigning` | `executing` | Toda tarea tiene exactamente un agente asignado |
| `assigning` | `failed` | Hay una tarea sin agente posible |
| `executing` | `verifying` | Todos los batches completos |
| `executing` | `failed` | Fallo no recuperable pese a los reintentos |
| `verifying` | `done` | Todos los criterios cumplidos |
| `verifying` | `executing` | Hay gaps y se puede iterar (max 3 iteraciones) |
| `verifying` | `failed` | Hay gaps y se agotaron las iteraciones |
| `done` / `failed` | `idle` | `reset()` |

**Regla:** toda transicion se persiste antes de ejecutar la siguiente accion.
Si el proceso se cae a mitad, el estado se puede recuperar.

---

## Iteracion en VERIFYING

El maximo es 3 ciclos de `verifying -> executing -> verifying`.

**Por que 3:** mas de 3 iteraciones casi siempre significa que el problema no
es de ejecucion sino de especificacion. Un cuarto ciclo es trabajo desperdiciado.

**Regla:** en la tercera iteracion fallida, el estado pasa a `failed` y se
escala. El tiempo de quien espera vale mas que el orgullo del sistema.

---

## Politica de reintentos

| Intentos | Accion |
|---|---|
| 1 | Reintento con el mismo agente y el mismo contexto |
| 2 | Reintento con el mismo agente y contexto enriquecido |
| 3 | Reintento con un agente alternativo de la misma especialidad |
| 4 | Diagnostico: el orquestador revisa que fallo |
| 5 | Escalamiento a la persona responsable |

### Reintento por tipo de fallo

| Tipo de fallo | Estrategia |
|---|---|
| `agent_error` | Mismo agente. Si vuelve a fallar, agente alternativo |
| `context_missing` | Enriquecer el contexto con lo que faltaba y reintentar con el mismo agente |
| `dependency_failed` | No reintentar: esperar a que la dependencia se complete |
| `spec_ambiguous` | Escalar al orquestador para que se tome una decision, no reintentar |
| `verification_fail` | Crear una tarea de correccion explicita, no reintentar la misma |
| `timeout` | Descomponer en tareas mas chicas y reintentar |
| `conflict` | Serializar: esperar a que se libere el recurso en conflicto |

**Regla:** un fallo de verificacion NO se reintenta con la misma tarea. Se
crea una tarea nueva con el gap explicito. Reintentar lo mismo produce el
mismo resultado.

---

## Formato de escalamiento

Cuando el orquestador no puede continuar, escala con esta estructura. El
formato importa: el que recibe la escalacion tiene que poder actuar sin
investigar.

```yaml
escalation:
  run_id: "<id del run>"
  goal: "<objetivo original>"
  state: failed
  attempts: 3
  failure_type: "<tipo de la taxonomia>"
  error: "<mensaje del ultimo intento>"

  task:
    id: T3
    subject: "<subject>"
    assigned_to: "<rol>"
    expected_output: "<que debia producir>"
    acceptance: "<criterio de aceptacion>"

  what_was_tried:
    - "intento 1: <agente> - <resultado>"
    - "intento 2: <agente> - <resultado>"
    - "intento 3: <agente> - <resultado>"

  blocks: [T4, T5]        # tareas que dependen de esta
  evidence:
    - "<ruta del log o artefacto>"

  decision_needed: "<la decision puntual que se necesita>"
  options:
    - "<opcion A>"
    - "<opcion B>"
```

**Regla:** `decision_needed` es una sola pregunta con opciones concretas, no
un informe. "El agente no pudo implementar T3 porque no sabe cual es el
contrato. Opcion A: le pasamos el contrato de la fase 2. Opcion B: la
implementamos a mano."

**Regla:** nunca escalar sin `what_was_tried`. Reintentar lo mismo que ya se
intento es la forma de perder el tiempo de todos.

---

## Persistencia del estado

El estado se guarda despues de cada transicion, no al final del run.

```python
def transition(self, new_state: State, data: dict | None = None) -> None:
    self.state = new_state
    self.store.save_checkpoint({
        "state": new_state,
        "task_graph": self.task_graph.serialize(),
        "results": self.results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
```

**Por que en cada transicion:** si el proceso se cae en `executing`, se
retoma desde el ultimo batch completado, no desde cero. Retomar desde cero
repite trabajo ya hecho y puede tener efectos secundarios.

**Regla:** al iniciar un run, se carga el checkpoint. Las tareas en estado
`completed` no se re-ejecutan.

---

## Control manual de subtareas

El operador puede pausar o cancelar una tarea en ejecucion.

| Accion | Efecto |
|---|---|
| `pause` | La tarea no se ejecuta en el proximo ciclo. Queda en `paused` |
| `resume` | Vuelve a `active` y se ejecuta en el proximo ciclo |
| `cancel` | La tarea queda en `cancelled` y no se ejecuta nunca |
| `retry` | Limpia `result` y `error`, vuelve a `pending` |

**Regla:** antes de cada batch, se lee el `control_state` de cada tarea y se
excluyen las que estan `paused` o `cancelled`. Una tarea cancelada queda
marcada como tal en el registro, para que no parezca que se olvido.

---

## Referencias

- `dev-kit-orchestrator/templates/task-graph.yaml` - formato del grafo
- `dev-kit-task-breakdown` - como se construye el grafo
- `dev-kit-agent-routing` - como se asigna el agente
