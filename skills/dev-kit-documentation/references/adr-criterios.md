# Criterios de ADR: redaccion, ciclo de vida y casos borde

> Referencia de apoyo para `dev-kit-documentation`. Define cuando se escribe un
> ADR, como se redacta y que hacer con los casos que no encajan en el flujo
> normal.

---

## 1. La pregunta de admision

Un ADR se escribe cuando la respuesta a esta pregunta es "si":

> **¿Hay al menos dos alternativas razonables, y alguien va a cuestionar la
> eleccion dentro de seis meses?**

Si no hay alternativa razonable, no hay decision que registrar. Si nadie va a
cuestionarla, no hay nada que preservar.

Tres casos limite que se resuelven asi:

| Caso | Que hacer | Por que |
|---|---|---|
| Hay una sola alternativa viable | No ADR: una nota en el plan | No hubo decision, hubo descripcion |
| Hay alternativas pero son variaciones de lo mismo | No ADR: registrar la variante elegida en el codigo | El ADR no aporta informacion |
| Hay alternativas y el impacto es alto | ADR completo | Aca si hay criterio que perder |

---

## 2. Seccion Contexto: que datos no pueden faltar

El Contexto es lo que se pierde con el tiempo. Un ADR sin contexto obliga a
adivinar las restricciones del momento, y las restricciones son justo lo que
explica la decision.

| Dato | Ejemplo de porque importa |
|---|---|
| Escala o volumen esperado | justifica un indice, un cache o no |
| Restriccion de tiempo | justifica un atajo tecnico con deuda |
| Dependencias ya instaladas | justifica "usar lo que hay" |
| Tamano del equipo | justifica evitar una tecnologia pesada |
| Requisito del cliente | justifica lo que un alternativa tecnica no lograria |

**Regla:** el Contexto se escribe sin justificar la decision. Si el Contexto ya
dice "por eso elegimos X", es un ADR mal escrito: el Contexto describe el
problema, la Decision describe la solucion.

---

## 3. Alternativas: el requisito de las tres filas

Una tabla de alternativas con una sola fila (la elegida) es una decision sin
criterio. Se exigen al menos:

1. La alternativa elegida.
2. Al menos una alternativa real, con su motivo de descarte.
3. La opcion por defecto (la que se hace si nadie decide): no hacer nada, usar
   lo que ya existe, resolverlo a mano.

La tercera fila es la que mas se omite y la que mas importa: es la que
documenta el costo de no decidir.

| Fila | Que aporta |
|---|---|
| <opcion A> (la elegida) | lo que se acepta a cambio |
| <opcion B> | por que se descarta |
| No hacer nada / resolverlo a mano | el costo de no decidir, que suele ser el mayor |

---

## 4. Consecuencias: la honestidad es el gate

Un ADR que solo lista beneficios no es un ADR: es propaganda. El gate para
aceptar un ADR es que la seccion **En contra** tenga al menos un elemento real.

| Comprobacion | Si falla |
|---|---|
| Hay al menos una consecuencia negativa | no se acepta: se pidio mas analisis |
| Las consecuencias negativas son concretas | no se acepta: "es mas complejo" no es una consecuencia |
| Hay impacto operativo si aplica | no se acepta: el costo hidden aparece en produccion |

Ejemplos de consecuencias negativas validas:

- "El cliente tendra que esperar la regeneracion del indice de 40 minutos."
- "Un cambio de esquema requiere ventana de mantenimiento."
- "El equipo tiene que aprender una libreria nueva."
- "No se puede migrar a la version nueva sin reescribir el modulo X."

---

## 5. Ciclo de vida: las transiciones validas

```
Propuesto ---> Aceptado ---> (Superado por ADR-XXXX)
    |              |
    |              +---> (no se edita el cuerpo)
    +---> Rechazado
```

| Transicion | Cuando | Quien |
|---|---|---|
| Propuesto -> Aceptado | la decision se tomo y se puede ejecutar | quien decide la capa |
| Propuesto -> Rechazado | se considero y no se adopto | quien decide la capa |
| Aceptado -> Superado por | otra decision la reemplaza | autor del ADR nuevo |
| Propuesto -> Propuesto | se amplia el contexto mientras se discute | cualquiera |

**Transiciones prohibidas:**

- Aceptado -> Propuesto (se pierde la decision vigente).
- Aceptado -> Aceptado con cuerpo editado (se pierde la historia).
- Superado -> Aceptado (un ADR superado no vuelve: se escribe uno nuevo).

### Cuando un ADR aceptado se equivoca

El error se corrige asi:

1. Se escribe el ADR nuevo con el estado `Propuesto`.
2. Se marca el ADR viejo como `Superado por ADR-XXXX`.
3. Se actualiza el indice de ADRs con los dos estados.
4. Se registra en el changelog si el cambio tiene impacto externo.

**Regla:** el cuerpo del ADR viejo no se toca jamas. Es el registro de lo que se
creia entonces, con la informacion disponible entonces.

---

## 6. Numeracion y ciclo de vida del indice

| Regla | Valor | Motivo |
|---|---|---|
| Numeracion | correlativa, de 4 digitos, sin reutilizar | un numero reutilizado rompe las referencias |
| Nombre | `NNNN-titulo-en-kebab-case.md` | orden alfabetico coincide con orden cronologico |
| Indice | `docs/adr/README.md` | sin indice, los ADRs son un archivo muerto |
| Referencia en el cuerpo | `ADR-0007` | el formato fijo permite buscarlo |

Formato del indice:

```markdown
# Registros de decisiones de arquitectura

| # | Titulo | Estado | Fecha | Resumen |
|---|---|---|---|---|
| 0001 | <titulo> | Aceptado | <fecha> | <una linea> |
| 0002 | <titulo> | Superado por ADR-0004 | <fecha> | <una linea> |
```

---

## 7. ADR y otros artefactos: quien escribe que

| Contenido | Donde vive | No va en el ADR |
|---|---|---|
| El porque de una decision | ADR | |
| La forma de la API | contrato OpenAPI | |
| El codigo | codigo | |
| El detalle de implementacion | codigo y docstring | |
| Un comando de operacion | runbook | |
| Un incidente | postmortem | |
| El cronograma | plan o backlog | |

**Regla:** el ADR no duplica lo que ya existe en otro artefacto. Enlaza.

---

## 8. Casos borde frecuentes

### Decision que ya se tomo sin ADR

Si el equipo ya decidio y no hay ADR, se escribe retrospectivo con estado
`Aceptado`, declarando en el Contexto que la decision ya estaba en marcha. Es
mejor un ADR imperfecto que ninguna memoria de por que.

### Decision que se toma en una reunion

Se documenta igual. El formato no depende del canal: lo que importa es que
existan alternativas y consecuencias registradas.

### Decision que aplica a un solo servicio

Tambien se documenta. El alcance se define en el Contexto ("aplica al servicio
de X"), no omitiendo el ADR.

### Decision que cambia por proyecto

Se escribe un ADR por proyecto, o un ADR base del kit que cada proyecto
adapta. Lo que no se hace es un ADR generico sin dueno: nadie lo actualiza.

### Decision sobre tooling, no sobre el producto

Va en un ADR igual, pero el Contexto menciona que es una decision de flujo de
trabajo del equipo, no de arquitectura del software.

---

## 9. Checklist antes de aceptar un ADR

- [ ] El titulo dice que se decide, no solo el tema.
- [ ] El Contexto describe restricciones, no la solucion.
- [ ] La Decision esta en afirmativo y es inequivoca.
- [ ] Hay al menos dos filas en alternativas, mas la de "no hacer nada".
- [ ] La seccion En contra tiene al menos un elemento concreto.
- [ ] El impacto operativo esta evaluado.
- [ ] Hay un criterio de verificacion para la decision.
- [ ] El ADR cabe en una pagina.
- [ ] No hay nombres de personas: solo roles.
- [ ] El indice de ADRs esta actualizado con el nuevo estado.
