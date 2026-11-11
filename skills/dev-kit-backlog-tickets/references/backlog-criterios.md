# Criterios de backlog: particion, estimacion y redaccion

Guias de trabajo para el backlog. Cada seccion responde una pregunta concreta
del proceso de conversion de material crudo a backlog jerarquico.

---

## 1. Que es material crudo y como se reconoce

| Tipo de fuente | Que aporta | Ruido tipico |
|---|---|---|
| Acta de reunion | decisiones y pedidos con contexto | opiniones, temas laterales, repeticiones |
| Nota de seguimiento | avances y bloqueos | estado de animo, contexto innecesario |
| Correo | el pedido concreto | historial de cadena, saludos, adjuntos olvidados |
| Transcripcion de una llamada | pedidos mezclados con explicaciones | media hora de contexto para dos lineas utiles |
| Lista de ideas | volumen | ideas sin criterio de exito |

La prueba de que el material es **crudo** y no un backlog: no tiene IDs, no
tiene esfuerzo, no tiene dependencias y mezcla niveles (negocio con tecnico).

---

## 2. Recorte: que se queda y que se va

### Se queda

- Peticiones con un verbo y un objeto ("cargar documentos", "exportar el
  reporte").
- Condiciones explicitamente dichas ("solo para el rol administrador").
- Plazos y fechas mentioned.
- Restricciones ("no puede enviar mail fuera del horario").
- Criterios de exito expresados con numero.

### Se va

| Elemento | Destino real | Razon |
|---|---|---|
| "usemos un microservicio" | plan tecnico | es una propuesta, no un pedido |
| "el sistema deberia ser rapido" | aclaracion con D-xx | no tiene numero |
| "aprovechar que ya existe X" | epica de datos | es contexto |
| "yo lo veo asi" | seccion de supuestos | es una opinion |
| "como siempre dijimos" | no va | no hay fuente verificable |

**Regla del recorte:** si sacando la frase del contexto no queda un verbo y un
objeto, no es una peticion.

---

## 3. Particion: cuando una peticion son varias HUs

### Regla de particion

> **Si las partes se pueden entregar en rondas distintas, son HUs distintas.**

Aplicacion:

| Peticion | Test de particion | Resultado |
|---|---|---|
| "cargar documentos y verlos despues" | cargar y listar se pueden entregar por separado | 2 HUs |
| "integrar pagos y facturacion" | dos sistemas, dos dependencias, dos plazos | 2 HUs |
| "avisar cuando pasa algo" | falta saber que evento y que canal | 1 HU + 1 decision bloqueante |
| "busqueda con filtros" | filtrar por fecha y por estado, ambos en el mismo endpoint | 1 HU |
| "panel con graficos" | cada grafico tiene datos distintos | 3 HUs o 1 epica de 3 HUs |

### Cuando la particion no aplica

Una peticion que no se puede partir pero que es grande **no se achica**: se
marca como XL, se escala, y la epica se reconsidera. Apretar el alcance sin
cambiar el entregable genera una HU que no cumple su propio criterio de
aceptacion.

---

## 4. Estimacion T-shirt: como se decide

### Que se cuenta

La estimacion se hace por **piezas a entregar**, no por dificultad percibida:

| Pieza | Peso tipico |
|---|---|
| Endpoint simple (CRUD, validacion, permiso) | 1 |
| Endpoint con logica de negocio no trivial | 2 |
| Pantalla de listado o formulario | 2 |
| Pantalla con estado asincrono y manejo de errores | 3 |
| Migracion de datos | 2 |
| Integracion con servicio externo | 3 |
| Integracion con pago o servicio de correo | 4 |
| Test e2e del flujo completo | 2 |
| Trabajo de infraestructura o CI | 1 |

Suma de piezas -> tamano:

| Piezas | Tamano |
|---|---|
| 1 | XS |
| 2 a 3 | S |
| 4 a 6 | M |
| 7 a 10 | L |
| mas de 10 | XL (partir) |

### Ajustes al conteo

| Factor | Ajuste |
|---|---|
| Modulo existente con tests | -1 |
| Modulo existente sin tests | +1 |
| Dependencia externa sin sandbox disponible | +2 |
| Patron ya implementado en el proyecto | -1 |
| Requisito que depende de una decision abierta | no estimable todavia |

### Reglas de la estimacion

1. **El tamano se expresa en dias-persona del equipo**, no en "complejidad".
2. **Una HU XL indica una particion fallida.** Se parte y se reestima.
3. **La estimacion se calibra con la evidencia de la ronda anterior.** Si el
   ultimo M resulto ser L, hay que recalibrar la escala, no achicar las HUs.
4. **Una HU sin dependencias y con piezas contadas no se reestima en la
   revision.** Se cambia la estimacion solo con evidencia nueva.

---

## 5. Redaccion de una HU

### El titulo

Verbo + objeto, en infinitivo, sin tecnologia:

| Bien | Mal | Por que |
|---|---|---|
| "Consultar el historial de movimientos" | "Implementar endpoint GET /movements" | el titulo es de negocio |
| "Registrar el resultado de la inspeccion" | "Crear tabla de inspecciones con SQLAlchemy" | la tecnologia no es del backlog |
| "Exportar el reporte mensual" | "Agregar boton de download" | describe la entrega, no el control |

### El cuerpo

Cada HU declara **actor, necesidad, valor, esfuerzo, dependencias**. Si falta
el valor, la HU no esta justificada y hay que volver a la fuente.

### Los criterios de aceptacion en el backlog

En el backlog los criterios pueden estar en forma resumida (el detalle completo
va al archivo de historias de la fase de spec). Pero en el backlog:

- son **3 a 5** lineas observables;
- no tienen tecnologia;
- no se contradicen entre HUs de la misma epica.

### Metadatos obligatorios

| Metadato | Por que |
|---|---|
| ID estable (HU-NN) | las dependencias y las decisiones lo referencian |
| Epica | saber de donde sale |
| Esfuerzo | dimensionar la ronda |
| Prioridad explicita | el orden de lectura no es prioridad |
| Dependencias | construir el grafo |
| Rango de la ronda | saber que se implementa ahora y que queda despues |

---

## 6. Dependencias: como declararlas

| Forma | Se usa cuando | Ejemplo |
|---|---|---|
| `HU-03` | bloqueante directo | HU-05 depende de HU-03 |
| `D-02` | bloqueante por decision abierta | HU-05 depende de D-02 |
| `<servicio>` | dependencia externa | HU-06 depende de pasarela de pagos |
| `ninguna` | la HU es demostrablemente independiente | se escribe igual |

**Regla:** "ninguna" se escribe **siempre**. Una HU sin dependencias declaradas
es indistinguible de una HU con dependencias no registradas, y esa confusion
se paga al final de la ronda.

Tipos de dependencia y su efecto en la ronda:

| Tipo | Efecto |
|---|---|
| Dura | la HU no entra en la ronda hasta que la otra se entrega |
| Blanda | puede entrar, pero se cierra despues |
| De decision | la HU entra solo si la decision se cerro |
| Externa | la HU entra con riesgo de bloqueo externo; se escala si no avanza |

---

## 7. Decisiones bloqueantes: como escribirlas

Una decision bloqueante tiene:

| Campo | Como se redacta |
|---|---|
| Decision | el tema, en pocas palabras: "canal de notificacion" |
| Pregunta | la pregunta concreta con sus opciones: "correo, webhook o in-app" |
| Impacto | que queda sin hacer: "no se pueden escribir los criterios de HU-06" |
| Responsable | el rol que puede responder: "lider tecnico" |
| Fecha limite | la fecha en la que sin respuesta se escala |
| HUs afectadas | los IDs, para que se vea el radio de impacto |

### Escalamiento

Si la fecha limite pasa sin respuesta, la decision **escala** al rol superior.
El orquestador no la responde por su cuenta: decidir por el negocio es una
inversion de responsabilidad que nadie autorizo.

### Distinguir decision bloqueante de duda tecnica

| | Decision bloqueante | Duda tecnica |
|---|---|---|
| Responde | el negocio o el lider tecnico | el arquitecto |
| Se resuelve | en el backlog | en el plan |
| Se registra en | tabla de decisiones | notas del plan |
| Si no se responde | escala | se decide y se avanza |

---

## 8. Puntos sin respaldo suficiente

### Que es un punto sin respaldo

Una mencion en la fuente que **no alcanza** para escribir una HU:

- nombra una funcionalidad sin actor, sin resultado o sin criterio;
- nombra una funcionalidad con contradicciones internas ("que sea rapido" en un
  punto, "sin cache" en otro);
- nombra algo que pertenece a otro sistema;
- nombra una mejora de infraestructura sin impacto de negocio.

### Como se registra

| Columna | Proposito |
|---|---|
| Mension | el termino exacto de la fuente |
| Que dice la fuente | resumen fiel, sin interpretacion |
| Que falta | el dato o la confirmacion puntual |
| Como se resuelve | pregunta a hacer o supuesto a validar |
| Responsable | el rol que responde |

### Cuando se convierte en HU

Un punto pasa de la seccion de "sin respaldo" a HU **solo** cuando:

1. alguien responde la pregunta, o el supuesto se valida; y
2. el resultado se registra en el registro de cambios del backlog.

Nunca se convierte en HU por acumulacion de menciones.

---

## 9. El ajuste a la ronda: 8 a 10 HUs

### Por que ese numero

| Cantidad | Que produce |
|---|---|
| menos de 5 | no es una ronda, es una semana suelta; no se puede balancear |
| 8 a 10 | se puede balancear por rol, revisar con el equipo y medir al cierre |
| mas de 15 | no se prioriza, se ejecuta en orden de lectura; el volumen anula la priorizacion |
| mas de 25 | es un volcado de la fuente, no un backlog |

### Procedimiento de seleccion

1. Filtrar por **epica activa** (la del periodo).
2. Excluir HUs con **decision bloqueante abierta** y fecha vencida.
3. Ordenar por **prioridad explicita** y, a igualdad, por desbloqueo: primero la
   que habilita otras.
4. Completar hasta 10 con las HUs de mayor valor agregado.
5. Registrar el resto en "historias de rondas siguientes" con el motivo.

### Balance por rol

Una ronda de 10 HUs con 10 HUs de backend no es una ronda: es una ronda de un
solo rol y el frontend espera. Si el equipo es parallelo, la ronda tiene que
estar repartida:

| Rol | HUs asignadas tipicas en una ronda de 10 |
|---|---|
| backend | 3 a 4 |
| frontend | 2 a 3 |
| qa | 1 a 2 (suele transversal) |
| devops | 0 a 1 |

Si no se puede balancear, la ronda es de un rol y se declara como tal.

---

## 10. Checklist de la HU antes de darla por buena

- [ ] El titulo tiene verbo y objeto, en infinitivo y sin tecnologia.
- [ ] El actor es un rol, no un nombre.
- [ ] La necesidad se puede trazar a una linea de la fuente.
- [ ] El valor esta escrito (que obtiene el actor).
- [ ] El esfuerzo corresponde a la suma de piezas.
- [ ] No es XL.
- [ ] Las dependencias estan escritas, o dice "ninguna".
- [ ] Los criterios de aceptacion son observables, sin tecnologia.
- [ ] Hay entre 3 y 5 criterios.
- [ ] No contradice otra HU de la misma epica.
- [ ] Esta asignada a una epica con criterio de exito con numero.
