---
name: dev-kit-agent-team
description: "Roster de agentes con rol, especialidad, alcance, limites por capa y reglas de handoff. CARGAR cuando hay que decidir que agente hace cada parte del trabajo, repartir tareas entre agentes o corregir solapamientos entre roles."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [agents, roster, roles, handoff, equipos]
    category: software-development
    related_skills: [dev-kit-agent-routing, dev-kit-orchestrator, dev-kit-task-breakdown, dev-kit-sdd-workflow]
---

# Dev Kit - Equipo de Agentes

> **Trigger:** "definir el equipo de agentes", "que agente hace cada parte",
> "a quien le toca esto", "los agentes se pisan el trabajo". Cargar esta skill
> ANTES de repartir tareas entre agentes.

## Que es esto

Un **roster**: la lista de roles del equipo, que puede hacer cada uno, que no
debe hacer, y a quien escala cuando el trabajo se sale de su capa.

El roster no es un organigrama decorativo: es un **contrato de alcance**.
Define el limite de cada agente para que:

- dos agentes no toquen la misma capa sin coordinarse,
- cada tarea tenga un solo responsable,
- los cruces de capa se escalen en vez de improvisarse.

La regla que lo sostiene:

> **Un agente, una capa.** Un agente que trabaja dos capas anula la revision
> cruzada: el error pasa de una capa a la otra sin que nadie lo mire.

## El roster

| Rol | Especialidad | Que puede hacer | Que NO debe hacer | Cuando escalarle |
|---|---|---|---|---|
| **orquestador** | coordinacion | partir el objetivo, construir el DAG, asignar agentes, correr gates, reintentar | escribir codigo de negocio, decidir alcance de producto | el objetivo no se puede partir en tareas con criterio verificable |
| **arquitecto** | diseno y contratos | escribir el contrato de API, definir limites de modulo, elegir patron, revisar el diseno | implementar modulos, corregir errores de logica | hay dos disenos validos y hay que elegir uno; el contrato no cierra |
| **backend senior** | diseno backend | definir modelo de dominio, reglas de transaccion, forma de la API interna, revisar cambios de backend | escribir frontend, tocar el pipeline de despliegue | dos endpoints con el mismo dato y no hay dueña de la fuente |
| **backend dev** | implementacion backend | escribir servicios, endpoints, migraciones y tests unitarios | cambiar el contrato de API, decidir el modelo de datos | el contrato no cubre el caso, o el modelo de datos no soporta la entidad |
| **frontend senior** | diseno frontend | definir jerarquia de componentes, estrategia de estado, accesibilidad, sistema visual | escribir la logica de negocio del servidor | la API no expone lo que la pantalla necesita |
| **frontend dev** | implementacion frontend | escribir componentes, estilos, formularios y tests de interfaz | decidir el contrato de API, tocar el modelo de datos | el contrato llega con un hueco y no se puede cerrar sin cambios |
| **devops** | operacion | contenedores, CI/CD, ambientes, despliegue, secretos, observabilidad | cambiar logica de negocio, editar el contrato de API | el despliegue falla por una razon que no es de infraestructura |
| **qa** | verificacion | escribir y correr pruebas, definir el plan de pruebas, reportar defectos, validar criterios de aceptacion | implementar el arreglo del defecto que acaba de reportar | el defecto toca varias capas y no se sabe en cual arranco |
| **agente de navegador** | interaccion web | navegar, capturar evidencia de pantalla, hacer QA exploratorio, automatizar flujos de UI | cambiar el codigo de la aplicacion para que el flujo pase | el flujo falla por logica de negocio y no por la UI |
| **especialista rag-ai** | recuperacion y modelos | chunking, embeddings, busqueda, evaluacion de relevancia, prompts | decidir el modelo de dominio de la aplicacion | la calidad de la respuesta depende del modelo y no del prompt |
| **especialista vision** | imagen | interpretar capturas, diagramas y documentos escaneados | inventar datos que no estan en la imagen | la imagen es ambigua y hay que decidir con criterio de producto |
| **especialista audio** | sonido | transcribir, diarizar y resumir audio | tomar decisiones de producto sobre el contenido | el audio es ambiguo o tiene ruido y no se puede segmentar |
| **agente de seguridad** | riesgo | auditar permisos, datos sensibles, dependencias y superficie de ataque | cambiar el alcance de una funcionalidad | un cambio abre un riesgo que el proyecto no puede aceptar |
| **redactor de documentacion** | comunicacion | escribir README, ADRs, runbooks y mensajes de release | decidir que se implementa | la funcionalidad existe pero su uso no esta documentado |

## La regla de limites: un agente no trabaja dos capas

Las capas son los niveles de un cambio. Cada capa tiene un dueno por defecto.

| Capa | Que se decide | Dueno por defecto | El dueno NUNCA hace |
|---|---|---|---|
| producto y alcance | que problema se resuelve y con que limites | arquitecto | implementar |
| contrato | forma de la API, modelo de datos, esquema de eventos | arquitecto | escribir la logica que lo cumple |
| diseno de codigo | estructura de modulos, patrones, fronteras | backend senior o frontend senior | escribir el codigo final |
| implementacion | el codigo que cumple el contrato | backend dev o frontend dev | cambiar el contrato |
| datos | esquema, indices, migraciones | backend dev con devops | decidir que dato se guarda sin consultar la especificacion |
| verificacion | pruebas, evidencia, checklist de criterios | qa | implementar el arreglo |
| operacion | despliegue, pipeline, monitoring, rollback | devops | cambiar la logica de negocio |

Dos reglas que se derivan de la tabla:

1. **Si la tarea atraviesa dos capas, no es una tarea: son dos tareas con un
   handoff.** La primera termina en un artefacto que la segunda consume.
2. **Si un agente necesita tocar dos capas en el mismo momento, el plan esta
   mal.** Se divide o se escala.

## Reglas de handoff

Un handoff es un traspaso explicito de trabajo entre agentes. No es "segui con
el endpoint de pedidos": es un paquete de informacion.

### Que viaja (obligatorio)

| Campo | Obligatorio | Que lleva |
|---|---|---|
| Objetivo | si | una frase: que queda distinto al terminar |
| Contexto | si | donde encaja el trabajo, que modulos toca, que reglas del proyecto aplica |
| Artefactos previos | si | el contrato, la especificacion o el plan del que depende, con su version |
| Criterio de aceptacion | si | comandos verificables: que test tiene que pasar, que lint, que arranque |
| Fuera de alcance | si | que NO debe tocar el agente receptor |
| Estado | no | en que quedo, intentos previos, errores ya vistos |

### Que NO viaja

- Historiales de conversacion completa: se entrega el resumen y el artefacto.
- Decisiones de producto que no estan escritas: si no esta escrito, no es
  contexto, es rumor.
- Credenciales, tokens o datos de negocio de terceros.

### Formato del traspaso

El receptor tiene que poder **empezar sin preguntar nada**. Si necesita una
respuesta para arrancar, falta contexto: eso no es un handoff, es una
interrupcion. Se responde antes de asignar.

## Cuando un agente NO es el indicado

Señales concretas que obligan a cambiar de agente o a escalar:

| Señal | Agente correcto | Accion |
|---|---|---|
| La tarea no tiene criterio de aceptacion verificable | orquestador | replantear la tarea antes de asignarla |
| El agente pide acceso a un contrato que no existe | arquitecto | cerrar el contrato primero |
| El agente propone cambiar el contrato a mitad de camino | arquitecto | detener la tarea, abrir un cambio de contrato |
| El fallo aparece en dos capas a la vez | orquestador | partir el fallo y asignar a cada dueno |
| El agente escribe codigo de otra capa "para cerrar antes" | orquestador | revertir ese fragmento y reasignar |
| La tarea pide una capacidad que el rol no tiene | orquestador | reasignar o agregar el rol al roster |
| El agente repite el mismo error tras varios intentos | orquestador | cambiar de estrategia, no reintentar igual |
| El resultado cumple el codigo pero no los criterios | qa | reprobar, no dar por entregado |

## Como se usa en el flujo

1. **Armar el roster** antes de la fase de tareas, con `templates/roster.md`.
2. **Repartir** cada historia al dueno de su capa. Una historia puede tener
   varios duenos, pero cada tarea tiene uno solo.
3. **Verificar los limites** antes de ejecutar: ningun agente con dos capas.
4. **Entregar** cada tarea con el paquete de handoff de `templates/handoff.md`.
5. **Escalar** siguiendo la tabla, no improvisando.

El roster se cruza con el routing declarativo de `dev-kit-agent-routing`: el
routing elige **a quien** le toca, el roster define **que puede** hacer esa
persona y hasta donde.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Un agente que hace de todo | Se pierde la revision cruzada y nadie detecta el error | Un agente, una capa |
| "El frontend tambien toca la API para no esperar" | Dos fuentes de verdad para el contrato | Contrato primero, handoff despues |
| Handoff de una linea ("segui con el modulo X") | El receptor arranca sin contexto y desperdicia el intento | Paquete de handoff completo |
| Tarea asignada sin criterio de aceptacion | No hay forma de saber si salio bien | Criterio verificable o no es tarea |
| Asignar por disponibilidad y no por capa | El agente hace lo que sabe, no lo que le toca | Asignar por dueno de capa |
| Escalar solo cuando ya fallo | Se pierde el criterio de la capa | Escalar cuando el contrato no alcanza |
| Dos agentes modificando el mismo artefacto | Conflicto silencioso | Un dueno por artefacto |
| Ampliar el alcance dentro de la tarea | El trabajo crece sin estimacion | Fuera de alcance, en el handoff |
| Roster con roles que no existen en el proyecto | Trabajo asignado a nadie | Rol minimo: dueno real por capa |
| Medir al equipo por volumen de codigo | Se premia el exceso | Medir por criterios cumplidos |

## Referencias

### Skills relacionadas

- `dev-kit-agent-routing` - decide que agente toma cada objetivo.
- `dev-kit-orchestrator` - ejecuta el ciclo de tareas sobre el roster.
- `dev-kit-task-breakdown` - produce las tareas que despues se reparten.
- `dev-kit-sdd-workflow` - fase de tareas dentro del flujo completo.

### Archivos de esta skill

| Archivo | Contenido |
|---|---|
| `templates/roster.md` | plantilla del roster por proyecto, con capas y duenos |
| `templates/handoff.md` | paquete de traspaso entre agentes, listo para copiar |
| `references/roles-detalle.md` | alcance detallado por rol: entradas, salidas y prohibiciones |
| `references/escalamiento.md` | criterios de escalamiento, rutas y formato del aviso |
