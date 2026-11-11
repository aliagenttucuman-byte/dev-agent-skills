# PLAN.md

> Fase 4 del flujo SDD. Define COMO se construye. Plantilla para copiar.

## Resumen

**Que se construye:** [una frase]
**Para quien:** [el usuario o el sistema]
**Que no incluye:** [los limites explicitos del alcance]

---

## Arquitectura

### Componentes

| Componente | Responsabilidad | Tecnologia | Interfaz |
|---|---|---|---|
| [nombre] | [que hace, en una linea] | [stack] | [API / cola / archivo / evento] |

### Diagrama de flujo

```
[entrada] -> [componente] -> [proceso] -> [salida]
                |
                +-> [dependencia externa]
```

### Decisiones de arquitectura

| # | Decision | Alternativas consideradas | Motivo | Impacto |
|---|---|---|---|---|
| D1 | [que se decide] | [A / B / C] | [por que] | [que habilita o bloquea] |

> Toda decision con mas de una alternativa razonable va aca. Sin esta tabla, la
> decision existe pero no se puede revisar.

---

## Modelo de datos

| Entidad | Campos clave | Relaciones | Volumen estimado |
|---|---|---|---|
| [nombre] | [campo: tipo] | [relacion con otra entidad] | [orden de magnitud] |

**Indices previstos:** [cuales y por que]
**Migraciones:** [cuantas, que estrategia de rollback]

---

## Dependencias

| Dependencia | Version | Para que | Alternativa si falla |
|---|---|---|---|
| [libreria o servicio] | [rango] | [motivo] | [plan B] |

**Dependencias externas que pueden fallar:** [lista con que se hace si no estan]

---

## Orden de implementacion

| Paso | Que se construye | Depende de | Agente sugerido | Entregable verificable |
|---|---|---|---|---|
| 1 | [que] | [pasos previos] | [rol] | [endpoint, componente, script] |
| 2 | [que] | [paso 1] | [rol] | [entregable] |

**Paralelizable:** [pasos que pueden ir en paralelo, y por que no hay conflicto]
**Secuencial obligatorio:** [pasos con dependencia dura]

---

## Estrategia de testing

| Nivel | Que cubre | Cantidad aproximada | Comando |
|---|---|---|---|
| Unitario | [logica de negocio] | [n] | [comando] |
| Integracion | [contratos entre componentes] | [n] | [comando] |
| E2E | [recorridos criticos] | [n] | [comando] |

**Criterios de aceptacion sin cobertura automatizada:** [cuales y como se verifican]

---

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigacion | Plan de contingencia |
|---|---|---|---|---|
| [riesgo] | [alta/media/baja] | [alto/medio/bajo] | [que se hace para evitarlo] | [que se hace si ocurre] |

---

## Fuera de alcance

- [feature que se decide no incluir, con el motivo]

## Preguntas abiertas

| Pregunta | Impacto | Quien decide | Estado |
|---|---|---|---|
| [pregunta] | [que se decide con la respuesta] | [rol] | abierta |

---

## Estimacion asociada

Ver `ESTIMACION.md`. Los tres escenarios van ahi; aca solo se referencia el
escenario base y el costo de infra mensual.
