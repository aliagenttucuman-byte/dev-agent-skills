# Roster de agentes - <nombre del proyecto>

> Plantilla del roster. Copiar y completar. Un roster sin capa con dueno
> asignado no esta listo: es una lista de nombres.

## 1. Principios aplicados

- Un agente, una capa. Nadie cubre dos capas a la vez.
- Una tarea, un responsable.
- El que no puede cerrar el trabajo decide a quien se escala.
- Roster minimo: el que existe en el proyecto. Si un rol no existe, se omite.

## 2. Roster

| Rol | Especialidad | Puede hacer | No debe hacer | Escala a |
|---|---|---|---|---|
| orquestador | coordinacion | partir objetivos, construir el DAG, asignar, correr gates | escribir codigo de negocio | lider tecnico |
| arquitecto | diseno y contratos | escribir contratos de API, definir limites de modulo, elegir patron | implementar modulos | lider tecnico |
| backend senior | diseno backend | modelo de dominio, reglas de transaccion, revision de codigo backend | escribir frontend | arquitecto |
| backend dev | implementacion backend | servicios, endpoints, migraciones, tests unitarios | cambiar el contrato de API | backend senior |
| frontend senior | diseno frontend | jerarquia de componentes, estrategia de estado, accesibilidad | escribir logica de negocio del servidor | arquitecto |
| frontend dev | implementacion frontend | componentes, estilos, formularios, tests de interfaz | decidir el contrato de API | frontend senior |
| devops | operacion | contenedores, CI/CD, ambientes, despliegue, secretos | cambiar logica de negocio | lider tecnico |
| qa | verificacion | plan de pruebas, ejecucion, reporte de defectos, validacion de criterios | implementar el arreglo | lider tecnico |
| agente de navegador | interaccion web | navegar, capturar evidencia, QA exploratorio | cambiar codigo de la aplicacion | qa |
| especialista rag-ai | recuperacion y modelos | chunking, embeddings, busqueda, evaluacion | decidir el modelo de dominio | arquitecto |
| especialista vision | imagen | interpretar capturas y diagramas | inventar datos ausentes | arquitecto |
| especialista audio | sonido | transcribir, diarizar, resumir | decidir sobre el contenido | arquitecto |
| agente de seguridad | riesgo | auditar permisos, datos sensibles, dependencias | cambiar alcance | lider tecnico |
| redactor de documentacion | comunicacion | README, ADRs, runbooks, notas de release | decidir que se implementa | lider tecnico |

> Roles que no apliquen al proyecto: eliminar la fila. Un roster inflado
> confunde el routing.

## 3. Mapa de capas y duenos

| Capa | Que se decide | Dueno | Artefacto que deja |
|---|---|---|---|
| producto y alcance | que problema se resuelve y con que limites | arquitecto | `CONSTITUTION.md` |
| contrato | forma de la API, modelo de datos, esquema de eventos | arquitecto | contrato de API y modelo de datos |
| diseno de codigo | estructura de modulos y fronteras | backend senior / frontend senior | `PLAN.md` |
| implementacion | el codigo que cumple el contrato | backend dev / frontend dev | diff + tests |
| datos | esquema, indices, migraciones | backend dev con devops | migraciones |
| verificacion | pruebas y evidencia | qa | reporte de pruebas |
| operacion | despliegue, pipeline, monitoring, rollback | devops | pipeline y runbook |

## 4. Contratos firmados

| Contrato | Version | Dueno | Estado | Depende de |
|---|---|---|---|---|
| contrato de API | - | arquitecto | abierto | `CONSTITUTION.md` |
| modelo de datos | - | arquitecto | abierto | contrato de API |

> Regla: backend y frontend pueden trabajar en paralelo **solo** despues de que
> los contratos de esta tabla estan cerrados.

## 5. Reglas de handoff

Reglas vigentes para este proyecto:

- Paquete minimo de traspaso: objetivo, contexto, artefactos previos,
  criterio de aceptacion, fuera de alcance.
- El receptor arranca sin preguntar. Si necesita una respuesta, falta
  contexto: se completa antes de asignar.
- No se transcribe historial de conversacion: se entrega resumen y artefacto.

## 6. Criterios de escalamiento

| Situacion | A quien | Que se entrega |
|---|---|---|
| el contrato no cubre el caso | arquitecto | caso concreto y esperado |
| el fallo aparece en dos capas | orquestador | capas involucradas y ultimo artefacto bueno |
| el agente repite el mismo error | orquestador | intentos, error y salida exacta |
| el cambio abre un riesgo no aceptable | agente de seguridad | riesgo y severidad |

## 7. Roles fuera de alcance

Lista explicita de lo que este equipo NO hace, para que nadie lo asuma:

- (completar)

## 8. Registro de cambios del roster

| Fecha | Cambio | Motivo |
|---|---|---|
| - | roster inicial | - |
