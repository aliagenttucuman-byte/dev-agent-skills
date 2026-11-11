# BACKLOG - <NOMBRE_DEL_PROYECTO>

> **Ronda:** <N> | **Fecha:** <AAAA-MM-DD> | **Owner:** <rol>
> **Fuente de esta ronda:** <acta / correo / nota / pedido> | **Estado:** <borrador | revisado | aprobado>

---

## Metadatos

| Campo | Valor |
|---|---|
| Objetivo del proyecto | <una linea> |
| Epicas activas | <cantidad> |
| HUs en total | <cantidad> |
| Rondas estimadas | <cantidad> |
| Fecha objetivo | <AAAA-MM-DD> |

---

## Resumen de la ronda

| Metrica | Valor |
|---|---|
| Historias en esta ronda | <N> (entre 8 y 10) |
| Distribucion de esfuerzo | XS: <n> | S: <n> | M: <n> | L: <n> | XL: <n> |
| Decisiones bloqueantes abiertas | <n> |
| Puntos sin respaldo | <n> |
| Dependencias externas | <n> |

### Orden de la ronda

| # | HU | Epica | Esfuerzo | Prioridad | Depende de | Bloquea a |
|---|---|---|---|---|---|---|
| 1 | HU-01 | <A> | M | alta | - | HU-04 |
| 2 | HU-02 | <A> | S | alta | - | - |

---

## EPICA A - <Nombre en infinitivo> (<resultado de negocio>)

**OBJETIVO:** <que cambia para el negocio>
**CRITERIO DE EXITO:** <metrica observable, con numero>
**PLAZO:** <fecha o ventana>
**HUS:** HU-01, HU-02, HU-03

### HU-01 - <Verbo + objeto en infinitivo>

| Campo | Valor |
|---|---|
| Actor | <rol> |
| Necesidad | <que quiere> |
| Valor | <que obtiene> |
| Esfuerzo | <XS\|S\|M\|L> |
| Prioridad | <alta\|media\|baja> |
| Depende de | <IDs de HUs o D-xx, o "ninguna"> |
| Bloquea a | <IDs de HUs, o "ninguna"> |
| Endpoint previsto | <si se conoce; si no, "por definir"> |

**Criterios de aceptacion (resumen):**

1. <criterio observable>
2. <criterio observable>
3. <criterio observable>

### HU-02 - <Verbo + objeto en infinitivo>

<misma estructura>

---

## EPICA B - <Nombre en infinitivo> (<resultado de negocio>)

**OBJETIVO:** <que cambia para el negocio>
**CRITERIO DE EXITO:** <metrica observable, con numero>
**PLAZO:** <fecha o ventana>
**HUS:** HU-04, HU-05

### HU-04 - <Verbo + objeto en infinitivo>

<estructura de HU>

---

## Decisiones bloqueantes

> Preguntas sin responder que impiden escribir criterios, elegir implementacion
> o comprometer plazos. Responsable = rol, nunca nombre.

| # | Decision | Pregunta a responder | Impacto si no se decide | Responsable | Fecha limite | HUs afectadas | Estado |
|---|---|---|---|---|---|---|---|
| D-01 | <decision> | <pregunta> | <que se bloquea> | <rol> | <AAAA-MM-DD> | HU-02, HU-05 | abierta |

---

## Puntos sin respaldo suficiente en la fuente

> Menciones que aparecen en el material pero no se especifican lo suficiente
> para convertirlas en una historia. No se inventan: se registran y se preguntan.

| # | Mension | Que dice la fuente | Que falta | Como se resuelve | Responsable | Estado |
|---|---|---|---|---|---|---|
| P-01 | <mencion> | <resumen de la cita> | <que falta saber> | <pregunta a hacer> | <rol> | pendiente / validado / descartado |

---

## Supuestos declarados

> Lo que se asumio para poder avanzar. Un supuesto con responsable es
> legitimo; un supuesto invisible es un gap esperando.

| # | Supuesto | Fundamento | Riesgo si es falso | Responsable | Fecha de validacion | Estado |
|---|---|---|---|---|---|---|
| S-01 | <supuesto> | <por que se asume> | <que se rompe> | <rol> | <AAAA-MM-DD> | pendiente |

---

## Historias de rondas siguientes

> Resumen de lo que quedo fuera de esta ronda, con el motivo. No se borra: se
> registra para que la priorizacion sea explicable.

| # | HU | Epica | Esfuerzo | Motivo de no inclusion |
|---|---|---|---|---|
| HU-11 | <titulo> | <C> | M | <motivo> |

---

## Registro de cambios del backlog

| Fecha | Cambio | Quien (rol) | Motivo |
|---|---|---|---|
| <AAAA-MM-DD> | <que cambio> | <rol> | <motivo> |
