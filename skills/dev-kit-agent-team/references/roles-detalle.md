# Alcance detallado por rol

> Entradas, salidas y prohibiciones de cada rol. Complementa la tabla del
> `SKILL.md`; no la reemplaza.

## Como leer esta tabla

- **Entrada**: que necesita el agente para empezar, sin pedir nada mas.
- **Salida**: que artefacto deja, que otro agente puede consumir.
- **Prohibiciones**: acciones que, si aparecen, indican que la tarea estaba
  mal repartida.

---

## orquestador

| | |
|---|---|
| Entrada | objetivo del proyecto, estado del flujo, roster vigente |
| Salida | grafo de tareas, asignaciones, registro de gates, informe de escalamiento |
| Prohibiciones | escribir codigo de negocio, cambiar el alcance del producto, cerrar gates sin evidencia |

Es el unico rol que ve el trabajo completo. No es el mejorcodigo del equipo:
es el que decide a quien se le da el codigo.

## arquitecto

| | |
|---|---|
| Entrada | `CONSTITUTION.md`, alcance acordado, historias de usuario |
| Salida | contrato de API, modelo de datos, `PLAN.md` |
| Prohibiciones | implementar los modulos que diseña, cambiar el alcance sin avisar, cerrar contratos "a ojo" |

Cuando dos disenos son validos, elige uno y deja escrito por que. La eleccion
es la parte cara: la justificacion es la que evita repetir el debate.

## backend senior

| | |
|---|---|
| Entrada | contrato de API, modelo de datos, `PLAN.md` |
| Salida | guia de implementacion backend, revision de codigo backend, regla de transaccion |
| Prohibiciones | escribir frontend, modificar el contrato de API sin pasar por el arquitecto |

## backend dev

| | |
|---|---|
| Entrada | contrato cerrado, tarea con criterio de aceptacion, convenciones del proyecto |
| Salida | codigo, migraciones, tests unitarios, nota de cambios |
| Prohibiciones | cambiar el contrato, decidir el modelo de datos, ampliar el alcance de la tarea |

## frontend senior

| | |
|---|---|
| Entrada | contrato de API, historias de usuario, principios de accesibilidad |
| Salida | jerarquia de componentes, estrategia de estado, guias visuales |
| Prohibiciones | escribir la logica de negocio del servidor, cambiar el contrato de API |

## frontend dev

| | |
|---|---|
| Entrada | contrato cerrado, diseno de interfaz, tareas con criterio de aceptacion |
| Salida | componentes, estilos, formularios, tests de interfaz |
| Prohibiciones | decidir el contrato, tocar el modelo de datos, meter logica de negocio en el cliente |

## devops

| | |
|---|---|
| Entrada | artefactos de aplicacion, requisitos de runtime, restricciones de ambiente |
| Salida | contenedores, pipeline, procedimientos de despliegue y rollback, configuracion de secretos |
| Prohibiciones | cambiar logica de negocio, editar el contrato de API, guardar secretos en el repo |

## qa

| | |
|---|---|
| Entrada | criterios de aceptacion, build ejecutable, plan de pruebas del proyecto |
| Salida | plan de pruebas, reporte de ejecucion, lista de defectos con severidad |
| Prohibiciones | implementar el arreglo del defecto que acaba de reportar, cambiar el criterio de aceptacion |

## agente de navegador

| | |
|---|---|
| Entrada | URL o aplicacion levantada, flujo esperado, que evidencia se busca |
| Salida | capturas, traza del flujo, pasos que fallan |
| Prohibiciones | cambiar el codigo de la aplicacion, atribuir a la UI un fallo de negocio |

## especialista rag-ai

| | |
|---|---|
| Entrada | corpus o fuentes de conocimiento, consultas de ejemplo, metricas esperadas |
| Salida | estrategia de chunking, configuracion de embeddings, evaluacion de relevancia |
| Prohibiciones | decidir el modelo de dominio de la aplicacion, inventar metricas sin medirlas |

## especialista vision

| | |
|---|---|
| Entrada | imagen, documento o captura, pregunta concreta |
| Salida | descripcion estructurada de lo observable, incertidumbres explicitas |
| Prohibiciones | completar informacion que no esta en la imagen, decidir producto |

## especialista audio

| | |
|---|---|
| Entrada | archivo de audio, idioma esperado, resultado que se busca |
| Salida | transcripcion, segmentos, resumen |
| Prohibiciones | inventar fragmentos inaudibles, decidir producto |

## agente de seguridad

| | |
|---|---|
| Entrada | alcance del cambio, superficie expuesta, datos manejados |
| Salida | hallazgos con severidad, correccion propuesta, checklist de pre-despliegue |
| Prohibiciones | cambiar el alcance de la funcionalidad, aceptarse a si mismo el hallazgo |

## redactor de documentacion

| | |
|---|---|
| Entrada | funcionalidad existente, comandos reales del proyecto, decisiones tomadas |
| Salida | README, ADR, runbook, notas de release |
| Prohibiciones | decidir que se implementa, documentar comandos que no se probaron |

---

## Roles que el proyecto puede agregar

El roster no esta cerrado para siempre. Un rol nuevo entra cuando:

1. hay trabajo recurrente que ningun rol existente puede tomar sin salirse de
   su capa,
2. el trabajo tiene un criterio de aceptacion propio,
3. el rol tiene prohibiciones claras.

Sin las tres condiciones, es una tarea del orquestador, no un rol.
