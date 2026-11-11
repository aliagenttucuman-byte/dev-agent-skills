# TASKS.md

> Fase 7 del flujo SDD. Convierte `PLAN.md` en tareas asignables a agentes.
> Plantilla para copiar. Una tarea = un agente = un resultado verificable.

## Resumen

**Plan de origen:** `PLAN.md` (<version o fecha>)
**Contrato de referencia:** `<ruta del openapi.yaml>`
**Roster:** `<ruta del roster.md>`
**Total de tareas:** <N>

| Tamano | Cantidad | Que significa |
|---|---|---|
| pequeno | <n> | cabe en una sesion de trabajo; toca 1-2 carpetas |
| medio | <n> | toca 2-3 carpetas o un modulo completo |
| grande | <n> | suele indicar que hay que partirla mas |

---

## Indice de tareas

| ID | Tarea | Capa | Responsable | Depende de | Criterio de aceptacion | Tamano | Estado |
|----|-------|------|-------------|------------|------------------------|--------|--------|
| T-01 | <sustantivo del resultado> | <capa> | <rol> | - | `<comando>` | pequeno | pendiente |
| T-02 | <sustantivo del resultado> | <capa> | <rol> | T-01 | `<comando>` | pequeno | bloqueada |
| T-03 | <sustantivo del resultado> | <capa> | <rol> | T-02 | `<comando>` | medio | bloqueada |

Capa: `producto` / `contrato` / `diseno` / `implementacion` / `datos` /
`verificacion` / `operacion`.

Estado: `pendiente` / `bloqueada` / `en curso` / `hecha` / `rechazada`.

---

## Grafo de dependencias

```
T-01  ->  T-02  ->  T-03
                 \->  T-04  ->  T-05
```

**Paralelizables:** <tareas que pueden ir a la vez y por que no chocan>
**Secuencia obligatoria:** <tareas con dependencia dura>

---

## Tarea T-01 - <Sustantivo del resultado>

| Campo | Valor |
|---|---|
| Objetivo | <una frase: que queda distinto al terminar> |
| Capa | <capa> |
| Responsable | <un unico rol> |
| Depende de | - |
| Punto de partida | <artefacto: contrato, plan, ADR> |
| Alcance | <archivos o modulos que toca> |
| Fuera de alcance | <lo que NO debe tocar> |
| Restricciones | <reglas del proyecto que aplican> |
| Criterio de aceptacion | `<comando>` <que prueba ese comando> |
| Tamano | pequeno |

### Subpuntos verificables

| # | Subpunto | Como se comprueba |
|---|---|---|
| 1 | <que debe quedar hecho> | `<comando>` o `<assertion>` |
| 2 | <que debe quedar hecho> | `<comando>` o `<assertion>` |

### Notas de entrega

<Contexto no obvio que no se deduce del codigo. Omitir si no hay.>

---

## Tarea T-02 - <Sustantivo del resultado>

<Copiar el bloque de la tarea T-01 y completar los campos.>

---

## Cobertura de criterios de aceptacion

Cada criterio de la historia debe aparecer en al menos una tarea.

| Historia | Criterio | Tarea que lo cubre | Comando |
|---|---|---|---|
| <HU-NN> | <criterio observable> | T-0N | `<comando>` |

**Criterios sin cubrir:** <ninguno, o la lista de los que faltan>

---

## Fuera de alcance del breakdown

- <feature o parte del plan que no se taskea, con el motivo>

## Preguntas abiertas

| Pregunta | Impacto | Quien decide | Estado |
|---|---|---|---|
| <pregunta> | <que se decide con la respuesta> | <rol> | abierta |
