# ADR-<NNNN>: <Titulo de la decision>

> <Una frase con la decision. En presente y en afirmativo.>
>
> Estado: <Propuesto | Aceptado | Rechazado | Superado por ADR-XXXX>
> Fecha: <AAAA-MM-DD>
> Decidido por: <rol, nunca un nombre propio>
> Refs: <PLAN.md seccion X | issue | documento relacionado>

## Contexto

<Que problema resuelve esta decision. Que restricciones existian en el momento
de decidir: plazos, volumen de datos, equipo disponible, dependencias ya
instaladas. Sin esto, la decision no se puede evaluate.>

## Decision

<Que se decide, en una o dos frases, en afirmativo.>

<Si aplica, un fragmento corto de esquema, comando o estructura que fije la
decision sin ambiguedad.>

## Alternativas consideradas

| Alternativa | A favor | En contra | Por que no se eligio |
|---|---|---|---|
| <opcion A> | <ventajas reales> | <costos reales> | <motivo de la decision> |
| <opcion B> | <ventajas reales> | <costos reales> | <motivo de la decision> |

<Toda alternativa razonable va en la tabla. Si solo hay una opcion obvia, no
habia decision que registrar: no hace falta un ADR.>

## Consecuencias

**A favor:**

- <lo que esta decision habilita>
- <lo que se vuelve posible>

**En contra (lo que asumimos):**

- <lo que esta decision hace mas caro o mas dificil>
- <la deuda que estamos aceptando>

**Impacto operativo:**

- <costo de infraestructura, impacto en despliegue, cambios que require>

## Como se verifica

| Aspecto | Como se comprueba | Cuando |
|---|---|---|
| <que se verifica> | <comando, metrica o test> | <cuando se revisa> |

## Notas de implementacion

<Solo si hace falta. Si el ADR se vuelve un tutorial, se recorta.>

---

## Cambio de estado

| Fecha | Estado anterior | Estado nuevo | Motivo |
|---|---|---|---|
| <AAAA-MM-DD> | Propuesto | Aceptado | <motivo> |
