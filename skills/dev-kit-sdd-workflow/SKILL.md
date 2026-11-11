---
name: dev-kit-sdd-workflow
description: "Flujo de Spec-Driven Development de 9 fases para equipos de agentes de IA. Define que se construye antes de escribir codigo, con artefacto verificable por fase y gates que impiden avanzar sin evidencia. CARGAR cuando un proyecto nuevo arranca o hay que decidir si una feature se implementa."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sdd, methodology, workflow, spec, planning]
    category: software-development
    related_skills: [dev-kit-project-constitution, dev-kit-spec-authoring, dev-kit-backlog-tickets, dev-kit-spec-analysis, dev-kit-cost-estimation, dev-kit-task-breakdown]
---

# Dev Kit - Flujo SDD

> **Trigger:** "arrancar un proyecto nuevo", "armar una feature", "que pasos
> seguimos", "no se que hacer primero". Cargar esta skill ANTES de abrir un
> editor de codigo.

## Que es esto

Un flujo de 9 fases que separa **decidir** de **construir**. Cada fase produce
un artefacto escrito. El agente no avanza de fase sin ese artefacto.

La regla que lo sostiene:

> **Ejecutado no es lo mismo que entregado, y entregado no es lo mismo que
> verificado.** Cada fase tiene su propia verificacion.

No es metodologia de escritorio: estaoptimizada para un equipo de agentes que
trabaja en paralelo y necesita poder retomar desde donde quedo.

## El flujo

```
CONSTITUCION  ->  PRINCIPIOS: que esta permitido, que no, con que limites
      |
   SPECIFICAR   ->  QUE se construye: contrato OpenAPI + historias
      |
  CLARIFICAR    ->  QUE queda sin ambiguedad
      |
    PLANEAR     ->  COMO se construye: arquitectura, stack, orden
      |
   ESTIMAR      ->  CUANTO cuesta: infra, tokens, equipo, tiempo
      |
    ANALIZAR    ->  COHERENCIA: spec vs plan vs estimacion
      |
     TAREAS      ->  QUIEN hace que: breakdown asignable
      |
  CHECKLIST     ->  LISTO para codear: gates verificados
      |
 IMPLEMENTAR    ->  construir contra los contratos, no improvisar
```

## Las 9 fases en detalle

### 1. CONSTITUCION

**Skill:** `dev-kit-project-constitution`
**Artefacto:** `CONSTITUTION.md`

Define los limites del proyecto antes de existir el codigo: stack permitido,
estandares de calidad, reglas de negocio, restricciones de presupuesto y
tiempo, principios de UX.

**Gate:** sin `CONSTITUTION.md` no hay proyecto. Es el contrato que todos los
agentes respetan y contra el que se mide el "hecho a medida".

### 2. ESPECIFICAR

**Skill:** `dev-kit-spec-authoring`
**Artefacto:** `specs/openapi.yaml` + `specs/user-stories.md`

Define el **que**, nunca el como. El contrato de API va primero; el codigo
despues.

**Gate:** OpenAPI primero. Si no hay spec, no se codea.

### 3. CLARIFICAR

**Artefacto:** seccion "Clarificaciones" del spec.

Revisa ambiguedades: permisos, datos vacios, limites de paginacion, errores
parciales, que pasa si una dependencia falla.

**Gate:** una ambiguedad sin resolver en spec cuesta mucho mas de lo que cuesta
resolverla ahora.

### 4. PLANEAR

**Skill:** `writing-plans` (del kit base) o equivalente
**Artefacto:** `PLAN.md`

Define el **como**: componentes, dependencias y versiones, orden de
implementacion, riesgos y mitigaciones.

**Regla critica:** los contratos de API se firman aqui. Backend y frontend
pueden trabajar en paralelo **solo** despues de que los contratos esten
cerrados.

### 5. ESTIMAR

**Skill:** `dev-kit-cost-estimation`
**Artefacto:** `ESTIMACION.md`

Costo real de infra, tokens de LLM, suscripciones recurrentes y fee de equipo,
antes de tocar codigo.

**Gate:** sin estimacion aprobada no se implementa. La decision economica es
del cliente, no del agente.

### 6. ANALIZAR

**Skill:** `dev-kit-spec-analysis`
**Artefacto:** `REPORT-GAPS.md`

Coherencia entre las tres capas:

- ¿El plan cubre TODAS las historias del spec?
- ¿Hay funcionalidad en el plan que no existe en el spec? (over-engineering)
- ¿Falta algun endpoint para alguna historia?
- ¿El modelo de datos soporta todas las entidades?
- ¿La estimacion cubre todo el plan?

**Gate:** si hay gaps, se vuelve a la fase 2, 4 o 5. No a implementacion.

### 7. TAREAS

**Skill:** `dev-kit-task-breakdown`
**Artefacto:** `TASKS.md`

Convierte el plan en tareas concretas: una tarea = un agente = un resultado
verificable.

### 8. CHECKLIST

**Artefacto:** `CHECKLIST.md`

Verifica, antes de codear:

- [ ] `CONSTITUTION.md` existe y es coherente con el plan
- [ ] `openapi.yaml` valida
- [ ] Todas las historias tienen criterios de aceptacion verificables
- [ ] `PLAN.md` cubre todas las historias
- [ ] `ESTIMACION.md` existe y esta aprobada
- [ ] No hay gaps abiertos del analisis
- [ ] El entorno de desarrollo levanta y el smoke test pasa
- [ ] Los comandos de build/test/lint están documentados

**Gate:** un item sin check es un item sin verificar.

### 9. IMPLEMENTAR

Ejecutar contra los contratos. Si aparece un gap de diseno, **volver a la fase
4** (diseño), no improvisar en codigo.

## Como se coordina con el orquestador

El flujo SDD es el **mapa de ruta**; el orquestador es el **conductor**. No son
lo mismo:

- El SDD decide en que fase estamos y que artefacto falta.
- El orquestador decide que agente ejecuta la siguiente tarea, en que orden, y
  como maneja un fallo.

Regla: el orquestador **no implementa codigo de negocio**. Si se lo ve
escribiendo logica de dominio, la descomposicion esta mal.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Empezar por el codigo | Se descubre tarde que el problema estaba mal planteado | Fase 2 primero |
| Saltar la fase 5 | Se descubre tarde que no es rentable | Estimar antes de codear |
| Un solo agente hace todo | Se pierde la revision cruzada | Descomponer por capa |
| Contrato de API improvisado en codigo | Backend y frontend divergen | Cerrar contratos en fase 4 |
| Paralelizar backend y frontend sin contrato | Trabajo incompatible, se tira | Gate de DESIGN |
| "Implementar todo el modulo X" | No hay output verificable | Partir por endpoint |
| Tarea sin contexto | El agente no sabe que ya existe | Contexto explicito en la tarea |
| Verificacion superficial | "compila" no es "cumple los criterios" | Referenciar cada criterio |

## Checklist de calidad de una HU

Una historia de usuario esta bien si:

- [ ] Arranca con una hipotesis validable, no con una descripcion tecnica
- [ ] Describe el entregable concreto
- [ ] Tiene entre 3 y 5 criterios de aceptacion
- [ ] Los criterios son observables y verificables por test
- [ ] Tiene responsable y dependencias identificadas

Formato completo: `dev-kit-backlog-tickets`.

## Referencias

- `references/fases-detalle.md` - detalle por fase con entradas, salidas y gates
- `references/gates.md` - los gates y como verificarlos sin ambiguedad
- `references/anti-patrones.md` - anti-patrones extendidos con casos reales
- `templates/checklist-implementacion.md` - checklist de la fase 8, copiable
- `templates/plan.md` - esqueleto de `PLAN.md`
