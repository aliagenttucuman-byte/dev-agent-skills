# Anti-patrones extendidos

Casos reales del uso del flujo con agentes, con el sintoma, la causa y el
arranque de la correccion.

---

## 1. El God Task

**Sintoma:** una tarea dice "implementar el modulo de pagos".

**Causa:** no se descompuso. El plan no esta en tareas, o la descomposicion
llego hasta el modulo y se quedo.

**Por que falla:** no hay output verificable. Cuando termine, no se puede
saber si esta bien. Se revisa entero, que es lo mas caro que hay.

**Arranque:** partir por endpoint o por caso de uso, hasta que cada tarea
tenga un resultado que se pueda mirar.

```
MAL:  T1: [backend] "implementar el modulo de pagos"
BIEN: T1: [backend] "POST /payments: validar payload, persistir, responder 201"
     T2: [backend] "GET /payments/{id}: responder 200 con el pago o 404"
```

---

## 2. El contexto que no viaja

**Sintoma:** el agente reimplementa algo que ya existe, o rompe una convencion
sin saber que existia.

**Causa:** la tarea no dice que hay.

**Por que falla:** el agente no tiene acceso a la sesion del otro agente. Lo
que no se dice, no se sabe.

**Arranque:** toda tarea lleva contexto explicito: archivos involved, decisiones
tomadas, convenciones vigentes, criterio de aceptacion.

---

## 3. El contrato improvisado en codigo

**Sintoma:** el frontend llama a un endpoint que el backend no tiene, o al
contrario.

**Causa:** backend y frontend arrancaron en paralelo sin cerrar el contrato.

**Por que falla:** el contrato de API es el punto de contacto entre las dos
capas. Sin el cerrado, cada uno asume.

**Arranque:** cerrar el contrato en la fase de planear. Despues, paralelismo.

---

## 4. Paralelizar sin contrato

**Sintoma:** dos agentes worked en el mismo archivo, o el merge se rompe.

**Causa:** se lanzo trabajo en paralelo sobre recursos compartidos.

**Por que falla:** el paralelismo multiplica velocidad y tambien divergencia.

**Arranque:** paralelizar cuando (a) no hay dependencia de datos, (b) no
comparten estado mutable, (c) el riesgo de conflicto es bajo.

---

## 5. La verificacion superficial

**Sintoma:** "compila, esta listo".

**Causa:** se confundio ejecucion con verificacion.

**Por que falla:** compilar no prueba comportamiento. El codigo puede compilar
y no cumplir un solo criterio de aceptacion.

**Arranque:** la verificacion final referencia cada criterio de aceptacion y
confirma que esta cubierto.

---

## 6. Saltar la estimacion

**Sintoma:** tres meses de trabajo y el proyecto no era rentable.

**Causa:** la fase 5 se salto porque "era un proyecto chico".

**Por que falla:** el costo real aparece cuando ya se gastó. La estimacion
temprana es la unica que puede cambiar la decision.

**Arranque:** estimar antes de implementar, siempre. El numero se puede
refinar; la ausencia del numero no se puede recuperar.

---

## 7. La spec que describe la solucion

**Sintoma:** el spec dice "tabla de facturas con estos campos".

**Causa:** se started por el como, no por el que.

**Por que falla:** la spec se vuelve rigida: cambiar el modelo de datos exige
cambiar el spec, y el equipo no lo hace porque "ya estaba aprobado".

**Arranque:** la spec describe el comportamiento observable y los datos
necesarios. La estructura fisica es decision de la fase 4.

---

## 8. El gate decorativo

**Sintoma:** el checklist existe, todo marcado en verde, y el proyecto igual
salio mal.

**Causa:** los items no son verificables. "El codigo es de calidad" no se
puede checkear.

**Por que falla:** un gate que no se puede verificar se marca en verde por
inercia. Da la sensacion de rigor sin el rigor, que es peor que no tener gate.

**Arranque:** cada item del checklist tiene un comando o un artefacto que lo
prueba. Si no, no entra al checklist.

---

## 9. La hu con demasiados criterios

**Sintoma:** la historia tiene 12 criterios, 6 de ellos en BDD estricto, y
nadie sabe cual es el importante.

**Causa:** se aplico el formato de contrato de API a un backlog de sprint.

**Por que falla:** en el backlog, el volumen de criterios no agrega
informacion: agrega ruido y vuelve la historia dificil de estimar.

**Arranque:** backlog = 3 criterios en lenguaje directo. Contrato de API =
BDD estricto, porque ahi cada criterio se traduce en un test.

---

## 10. La hu que no es una hu

**Sintoma:** una historia dice "definir la estrategia de datos" o
"configurar el ambiente de pruebas".

**Causa:** se metieron decisiones en el backlog.

**Por que falla:** una decision no se implementa: se toma. No tiene criterio
de aceptacion, no se puede testear, no se puede cerrar.

**Arranque:** las decisiones van en una tabla aparte de "decisiones
bloqueantes", con su responsable.

---

## 11. La tarea sin criterio de aceptacion

**Sintoma:** el agente entrega y hay que revisar todo a mano.

**Causa:** la tarea no dice como se sabe que esta terminada.

**Arranque:** toda tarea tiene un criterio de aceptacion observable.

---

## 12. Confiar en que el agente se acuerde

**Sintoma:** la segunda vez que se hace la misma tarea, el agente lo hace
distinto, o peor.

**Causa:** el aprendizaje quedo en la sesion en vez de quedar en el artefacto.

**Por que falla:** la sesion no sobrevive, no se versiona, no se comparte.

**Arranque:** el aprendizaje va al artefacto (skill, checklist, template) o no
existe. Este es el principio del loop de realimentacion del kit.

---

## 13. La suite de tests que no falla nunca

**Sintoma:** 400 tests, todo verde, y el producto sigue roto.

**Causa:** los tests verifican la implementacion, no el comportamiento. Cambia
el codigo, cambian los tests, siguen verdes.

**Arranque:** un test que verifica el comportamiento se escribe antes que el
codigo. Si se escribe despues, verifica lo que hay, no lo que deberia.

---

## 14. El dashboard que nadie mira

**Sintoma:** un panel con 14 metricas y nadie lo consulta.

**Causa:** se construyo la visualizacion antes de saber que decision habilita.

**Arranque:** definir primero que decision se toma con esa metrica. Si no hay
decision, no hay metrica que valga la pena mostrar.
