# ESTIMACION.md

> Fase 5 del flujo SDD. Los numeros que hacen posible la decision de avanzar.
> Plantilla para copiar.

## Resumen

**Proyecto:** [nombre]
**Alcance estimado:** [que incluye y que no]
**Periodo de construccion:** [meses]
**Costo total estimado (escenario base):** [moneda] [monto]
**Costo recurrente mensual (operacion):** [moneda] [monto]

---

## 1. Equipo

| Rol | Recursos | Fee por persona por mes | Subtotal mensual | Meses | Subtotal total |
|---|---|---|---|---|---|
| [rol] | [n] | [moneda] | [moneda] | [n] | [moneda] |
| [rol] | [n] | [moneda] | [moneta] | [n] | [moneda] |
| **Total equipo** | | | **[moneda]** | | **[moneda]** |

**Supuestos del calculo:**
- Utilizacion efectiva: [n]% (el resto es overhead, preventa, tiempo entre proyectos)
- Minimo de calendario: [n] personas, [n] meses
- El desarrollo se cobra [mensual / por hito]

---

## 2. Infraestructura

| Servicio | Plan /spec | Cantidad | Costo mensual | Costo anual |
|---|---|---|---|---|
| [servicio] | [plan] | [n] | [moneda] | [moneda] |
| [servicio] | [plan] | [n] | [moneda] | [moneda] |
| **Total infra** | | | **[moneda]** | **[moneda]** |

**Ambientes:** [cuantos y para que]
**Crecimiento esperado:** [como crece el costo con el uso y cuando se dispara]

---

## 3. Consumo de LLM

| Uso | Modelo / proveedor | Tokens estimados por mes | Costo por mes | Costo total periodo |
|---|---|---|---|---|
| [uso: ej. inferencia de API] | [modelo] | [n] | [moneda] | [moneda] |
| [uso: ej. embeddings] | [modelo] | [n] | [moneda] | [moneda] |
| **Total LLM** | | | **[moneda]** | **[moneda]** |

**Supuestos:**
- Tokens por request: [n]
- Requests por mes: [n]
- Cache hit rate: [n]% (reduce el costo)
- **Costo por request promedio:** [moneda]

> El costo de LLM es el que mas sorprende en retrospectiva. Conviene medirlo en
> el primer mes real, no solo estimarlo.

---

## 4. Suscripciones y herramientas

| Herramienta | Plan | Cantidad de licencias | Costo mensual | Costo anual |
|---|---|---|---|---|
| [herramienta] | [plan] | [n] | [moneda] | [moneda] |
| **Total suscripciones** | | | **[moneda]** | **[moneda]** |

---

## 5. Otros costos

| Concepto | Costo | Frecuencia |
|---|---|---|
| [licencias de desarrollo, hardware, viáticos] | [moneda] | [unica / mensual] |

---

## 6. Resumen por escenario

| Componente | Conservador | Base | Optimista |
|---|---|---|---|
| Equipo | [moneda] | [moneda] | [moneda] |
| Infraestructura | [moneda] | [moneda] | [moneda] |
| LLM | [moneda] | [moneda] | [moneda] |
| Suscripciones | [moneda] | [moneda] | [moneda] |
| Otros | [moneda] | [moneda] | [moneda] |
| **TOTAL UNICO (construccion)** | **[moneda]** | **[moneda]** | **[moneda]** |
| **TOTAL RECURRENTE (mensual)** | **[moneda]** | **[moneda]** | **[moneda]** |

**Diferencia entre escenarios:** [que variable cambia y por que]

---

## 7. Punto de equilibrio

**Ingreso necesario para cubrir el costo recurrente mensual:** [moneda]
**Clientes requeridos a ese precio:** [n]
**Escenario base, primer ano:**
- Ingresos: [moneda]
- Costos totales: [moneda]
- Resultado: [moneda]

---

## 8. Supuestos y riesgos

| Supuesto | Confianza | Si es falso |
|---|---|---|
| [supuesto] | [alta/media/baja] | [impacto y ajuste] |

---

## Decision

**Escenario recomendado:** [conservador / base / optimista]
**Costo total:** [moneda]
**Aprobado por:** [rol] **Fecha:** [fecha]

> Este gate lo aprueba el cliente. El agente produce los numeros; la decision
> economica no es suya.
