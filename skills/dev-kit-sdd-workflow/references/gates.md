# Gates del flujo SDD

Referencia de `dev-kit-sdd-workflow`. Un gate que se puede saltar no es un
gate. Cada gate de esta lista dice **que bloquea** y **como se verifica**.

---

## La forma de un gate

```
GATE: <que se bloquea>
  Se verifica: <artefacto o comando>
  Pasa cuando: <condicion observable>
  Si falla:   <a que fase se vuelve>
```

Si un gate no se puede escribir en esta forma, no es un gate: es una buena
intencion.

---

## Gate 1 - Constitucion

**Bloquea:** pasar a especificar.
**Se verifica:** existe `CONSTITUTION.md` con las 6 secciones obligatorias
rellenadas (stack, calidad, reglas de negocio, restricciones, UX,
prohibiciones).
**Pasa cuando:** ninguna seccion dice "pendiente" ni "a definir".
**Si falla:** se completa la constitucion.

---

## Gate 2 - Contrato

**Bloquea:** escribir codigo.
**Se verifica:** `specs/openapi.yaml` valida contra el schema de OpenAPI.
**Pasa cuando:** el parser no reporta errores y cada operacion tiene al menos
un response documentado.
**Si falla:** se corrige el spec.

**Nota:** el validador de OpenAPI es la unica forma objetiva de verificar este
gate. "Se ve bien" no es un criterio.

---

## Gate 3 - Criterios verificables

**Bloquea:** pasar a planear.
**Se verifica:** cada historia en `specs/user-stories.md` tiene entre 3 y 5
criterios de aceptacion, y cada criterio se puede convertir en un test.
**Pasa cuando:** no hay criterios como "el sistema funciona correctamente" o
"la experiencia es buena".
**Si falla:** se reescriben los criterios.

**Prueba de conversibilidad:** si no podes escribir el test a partir del
criterio, el criterio no sirve.

---

## Gate 4 - Clarificaciones

**Bloquea:** pasar a planear.
**Se verifica:** la seccion `## Clarificaciones` existe y cada ambiguedad
detectada tiene respuesta o decision asumida con justificacion.
**Pasa cuando:** no quedan preguntas abiertas sin dueño.
**Si falla:** se responde o se escala.

---

## Gate 5 - Cobertura del plan

**Bloquea:** pasar a implementar.
**Se verifica:** cada historia del spec tiene al menos una tarea en
`TASKS.md` que la implementa, y cada endpoint del OpenAPI esta mapeado a una
tarea.
**Pasa cuando:** la matriz historia -> tarea esta completa en ambas
direcciones.
**Si falla:** se vuelve a la fase 2 o 4.

---

## Gate 6 - Sin over-engineering

**Bloquea:** pasar a implementar.
**Se verifica:** cada componente del plan se puede trazar a una historia o a un
requisito tecnico explicito (seguridad, performance, compliance).
**Pasa cuando:** no hay componente sin origen justificado.
**Si falla:** se saca del plan o se documenta el requisito que lo origina.

---

## Gate 7 - Estimacion

**Bloquea:** comprometer presupuesto.
**Se verifica:** `ESTIMACION.md` tiene los 3 escenarios y el total por escenario.
**Pasa cuando:** hay una decision registrada (aprobar / ajustar / descartar).
**Si falla:** se completa la estimacion.

**Nota:** este gate lo aprueba el cliente, no el agente. El agente produce el
numero; la decision es del cliente.

---

## Gate 8 - Checklist de implementacion

**Bloquea:** la primera linea de codigo.
**Se verifica:** todos los items de `CHECKLIST.md` en verde.
**Pasa cuando:** ningun item sin check.
**Si falla:** se resuelve el item pendiente.

---

## Gate 9 - Criterio cubierto

**Bloquea:** dar por entregado.
**Se verifica:** cada criterio de aceptacion tiene un test o una verificacion
que lo cubre, y ese test pasa.
**Pasa cuando:** la cobertura de criterios es total.
**Si falla:** se agrega el test faltante o se corrige el codigo.

---

## Gate 10 - Revision

**Bloquea:** merge.
**Se verifica:** la revision del `dev-kit-review` esta completa y no hay
comentarios de severidad bloqueante abiertos.
**Pasa cuando:** el revisor aprueba.
**Si falla:** se resuelven los bloqueantes.

---

## Gates entre agentes (handoff)

Cuando una tarea pasa de un agente a otro, hay un gate implicito:

**El agente receptor debe poder ejecutar sin preguntar.** Si necesita
preguntar algo, la tarea venia incompleta: el gate de la fase anterior fallo
y se deberia haber detectado ahi.

Verificacion practica: el handoff incluye contexto, artefactos previos y
criterio de aceptacion. Con eso, el agente receptor arranca.
