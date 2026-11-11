---
name: dev-kit-agent-routing
description: "Routing declarativo que decide que agente resuelve un objetivo, con categorias, palabras clave, scoring de confianza y fallback. CARGAR cuando hay que derivar una tarea a un agente, cuando el routing es ambiguo o para auditar por que se eligio un agente."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [routing, agents, taxonomy, orchestration, scoring]
    category: software-development
    related_skills: [dev-kit-agent-team, dev-kit-orchestrator, dev-kit-task-breakdown, dev-kit-sdd-workflow]
---

# Dev Kit - Agent Routing

> **Trigger:** "que agente hace esto", "a quien le asigno esta tarea",
> "como elijo el agente", "el routing falla". Cargar cuando hay que derivar un
> objetivo a un agente concreto.

## Que es esto

El mecanismo que decide, dado un objetivo en lenguaje natural, **que agente
lo resuelve**. De forma explicita, reproducible y auditable.

## Por que hace falta

Con 5 agentes, la intuicion funciona. Con 20, no. Y con 20:

- La misma tarea se resuelve de forma distinta segun quien la mire.
- No hay forma de auditar por que se eligio un agente.
- Los agentes se pisan entre si: el de QA hace backend.

**Regla:** el routing es codigo, no intuicion. Si la decision no esta
registrada, no se puede mejorar ni depurar.

## Taxonomia

| Categoria | Palabras clave | Agente |
|---|---|---|
| **SPEC** | spec, historia de usuario, user story, criterio de aceptacion, contrato, openapi, prd, requerimiento, backlog | `spec` |
| **BACKEND** | api, endpoint, servicio, python, fastapi, sqlalchemy, modelo, orm, migracion, job, tarea asincrona, webhook | `backend` |
| **FRONTEND** | componente, ui, interfaz, react, typescript, vite, hook, store, estado, formulario, css, tailwind, paginacion | `frontend` |
| **BROWSER** | scraping, playwright, selenium, formulario web, automatizacion, click, captura de pantalla, navegacion | `browser` |
| **INFRA** | docker, despliegue, deploy, kubernetes, terraform, pipeline, ci, cd, infraestructura, servidor, dominio, ssl | `infra` |
| **RAG_AI** | rag, embedding, vector, busqueda semantica, chunk, retriev, vectorstore, base de conocimiento, indexacion | `rag` |
| **QA** | test, prueba, caso de prueba, cobertura, regresion, e2e, verificacion, calidad, bug | `qa` |
| **DOCS** | readme, documentacion, adr, changelog, guia, manual, api docs | `docs` |
| **VISION** | imagen, foto, video, ocr, deteccion de objetos, vision, reconocimiento | `vision` |
| **AUDIO** | audio, voz, transcripcion, whisper, tts, sonido, podcast | `audio` |
| **EXTERNAL** | api externa, integracion, webhooks, proveedor, moneda, cotizacion, email | `external` |
| **SECURITY** | seguridad, vulnerabilidad, autenticacion, permisos, roles, amenaza, auditoria de codigo | `security` |

**Regla:** las categorias son transversales a la tecnologia. Un agente resuelve
una categoria, no un lenguaje.

## Scoring de confianza

```python
score = 0.0
for keyword in category.keywords:
    if keyword in goal_normalized:
        score += keyword_weight(keyword)
```

**Como se pondera:**

| Factor | Peso | Por que |
|---|---|---|
| Match exacto de la palabra clave | 1.0 | La senal mas fuerte |
| Match de una raiz (plural, conjugacion) | 0.6 | "endpoint" vs "endpoints" |
| Match de un sinonimo | 0.8 | Varias palabras para el mismo concepto |
| Match en el titulo de la tarea | x2 | El titulo es mas preciso que la descripcion |
| Varias categorias empatan | penalizacion | Ambiguedad real |

**Regla:** la confianza es la confianza del **primer** match, no del total. Un
goal que menciona "test" y "deploy" tiene dos categorias possibles: eso no es
confianza alta, es ambiguedad.

```
confianza = (match_de_la_categoria_ganadora - match_de_la_segunda) / match_de_la_categoria_ganadora
```

**Regla:** con confianza baja, el router no decide: escala. Un agente mal
elegido produce trabajo desperdiciado.

## Umbrales

| Confianza | Accion |
|---|---|
| >= 0.6 | Asignar al agente de la categoria ganadora |
| 0.3 - 0.6 | Asignar, pero marcar la asignacion como `baja_confianza` y pedir confirmacion |
| < 0.3 | Escalar: pedir clarificacion del objetivo antes de asignar |

**Regla:** nunca asignar en silencio con confianza baja. El costo de una
pregunta es de segundos; el costo de una tarea mal asignada, de horas.

## Fallback

Cuando ninguna categoria coincide o la confianza es muy baja:

| Situacion | Fallback |
|---|---|
| Ninguna categoria con match | `spec` (revisar el objetivo antes de decidir) |
| Dos categorias empatadas | La de menor riesgo de equivocacion |
| El goal es demasiado ambiguo | Pedir clarificacion, con opciones concretas |

**Regla:** el fallback devuelve **la duda, no una eleccion a ciegas**. Un
fallback que elige sin decir que no sabe es peor que no tener fallback.

**Regla:** la eleccion de fallback queda registrada con el motivo. Sirve
para descubrir que falta una categoria en la taxonomia.

## Formato de salida

```json
{
  "goal": "agregar endpoint POST /orders con validacion y test",
  "category": "BACKEND",
  "agent": "backend",
  "confidence": 0.72,
  "reasons": [
    "match exacto: 'endpoint' (+1.0)",
    "match exacto: 'validacion' (+1.0)",
    "match de sinonimo: 'post' -> POST (+0.8)"
  ],
  "alternatives": [
    {"category": "QA", "agent": "qa", "confidence": 0.18, "reasons": ["match: 'test'"]}
  ],
  "fallback": null,
  "needs_clarification": false
}
```

**Regla:** las razones son obligatorias. Un routing sin razones no se puede
auditar ni mejorar.

## Como usarlo

```bash
# Un objetivo
python3 scripts/route.py "agregar endpoint POST /orders con validacion"

# Varios, uno por linea
python3 scripts/route.py --file objetivos.txt

# Salida compacta
python3 scripts/route.py --compact "revisar el modelo de datos"

# JSON con categorias custom (para el cliente)
python3 scripts/route.py --taxonomy mi-taxonomia.json "..."
```

## Integracion con el orquestador

El routing se usa en dos momentos:

1. **Al descomponer:** para elegir el agente de cada tarea nueva.
2. **Al escalar:** cuando una tarea falla, para reasignarla a otro agente.

**Regla:** el routing se aplica **una vez** por tarea, al crearla. Reasignar
en cada reintento produce oscillacion: el mismo goal va y viene entre
agentes.

**Regla:** el taxonomia del router y la del orquestador tienen que ser la
misma fuente. Si divergen, el orquestador asigna un agente que el router no
conoce, y el fallback falla.

## Anti-patrones

| Anti-patron | Consecuencia |
|---|---|
| Asignar por intuicion sin registrar | No auditable, no mejora |
| Confianza calculada sobre el total de matches | Un goal con 10 palabras genera confianza alta sin ser claro |
| Fallback que elige en silencio | Se pierde trabajo sin que nadie lo note |
| Sin razones en la salida | No se puede depurar |
| Reasignar en cada reintento | Oscilacion entre agentes |
| Taxonomia duplicada entre router y orquestador | El fallback falla |
| Categorias por tecnologia en vez de por tipo de tarea | Un agente de Python termina haciendo docs |
| Sin umbral de confianza baja | Agentes mal asignados |

## Referencias

- `scripts/route.py` - el router ejecutable
- `templates/routing-result.json` - formato de salida
- `dev-kit-agent-team` - el roster al que rutea
- `dev-kit-orchestrator` - donde se usa el routing
