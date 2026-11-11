# REPORTE DE GAPS - <NOMBRE_DEL_PROYECTO>

> Analisis de coherencia entre spec, plan y estimacion.
> **Fecha:** <AAAA-MM-DD> | **Analista:** <rol> | **Version de artefactos:** <spec / plan / estimacion>

---

## 1. Resumen ejecutivo

| Severidad | Cantidad | Fase a la que vuelve |
|---|---|---|
| Bloqueante | <n> | <fase> |
| Alta | <n> | <fase> |
| Media | <n> | <fase> |
| Baja | <n> | - |
| **Total** | **<n>** | |

**Veredicto:** <APTO PARA IMPLEMENTAR | APTO CON RESERVAS | NO APTO>

**Razon del veredicto:** <una o dos frases que citan los hallazgos que lo
determinan>

**Resumen en una linea:** <que falta y que sobra, en una frase>

---

## 2. Alcance

| Artefacto | Ruta | Version | Estado |
|---|---|---|---|
| Constitucion | `CONSTITUTION.md` | <v> | <vigente / desactualizada> |
| Spec de API | `specs/openapi.yaml` | <v> | <vigente / desactualizada> |
| Historias | `specs/user-stories.md` | <v> | <vigente / desactualizada> |
| Plan | `PLAN.md` | <v> | <vigente / desactualizada> |
| Estimacion | `ESTIMACION.md` | <v> | <vigente / desactualizada> |

**Fuera de alcance:** <que no se comparo y por que>

---

## 3. Tabla de hallazgos

| ID | Tipo | Severidad | Hallazgo | Evidencia | Accion | Destino |
|---|---|---|---|---|---|---|
| G1-01 | Gap - <subtipo> | Bloqueante | <una linea> | <archivo y seccion> | <que hacer> | fase <n> |
| O1-01 | Over-engineering - <subtipo> | Alta | <una linea> | <archivo y seccion> | <que hacer> | fase <n> |

---

## 4. Detalle por hallazgo

### G1-01 - <titulo>

```
ID:        <ID>
Tipo:      Gap - <subtipo>
Severidad: <Bloqueante|Alta|Media|Baja>
Hallazgo:  <que se observo, en una frase>
Evidencia: <archivo, seccion y linea o fragmento>
Impacto:   <que pasa si no se corrige>
Accion:    <que hacer, en imperativo>
Destino:   fase <n> - <que artefacto se modifica>
```

### O1-01 - <titulo>

```
ID:        <ID>
Tipo:      Over-engineering - <subtipo>
Severidad: <Bloqueante|Alta|Media|Baja>
Hallazgo:  <que se observo, en una frase>
Evidencia: <archivo, seccion y linea o fragmento>
Impacto:   <que pasa si no se corrige>
Accion:    <que hacer, en imperativo>
Destino:   fase <n> - <que artefacto se modifica>
```

---

## 5. Matriz de trazabilidad

| Historia | Endpoints | Componentes del plan | Tareas | Costo | Test | Estado |
|---|---|---|---|---|---|---|
| HU-01 | <rutas> | <componentes> | <tareas> | <costo> | <tests> | completa / gap |
| HU-02 | <rutas> | <componentes> | <tareas> | <costo> | <tests> | completa / gap |

| Componente del plan | Historia | Estado |
|---|---|---|
| <componente> | - | over-engineering |

---

## 6. Impacto en la estimacion

| Hallazgo | Efecto sobre el costo | Delta estimado | Escenario afectado |
|---|---|---|---|
| <ID> | <infra / tokens / equipo / tiempo> | <+/- valor o "a definir"> | <conservador / base / optimista> |

**Totales antes y despues:**

| Concepto | Antes | Delta | Despues |
|---|---|---|---|
| Infraestructura mensual | <valor> | <delta> | <valor> |
| Tokens de LLM por mes | <valor> | <delta> | <valor> |
| Suscripciones recurrentes por mes | <valor> | <delta> | <valor> |
| Fee de equipo por ronda | <valor> | <delta> | <valor> |
| **Total mensual** | <valor> | <delta> | <valor> |

---

## 7. Acciones pendientes

| # | Accion | Hallazgo | Responsable | Fase destino | Fecha limite | Estado |
|---|---|---|---|---|---|---|
| 1 | <accion> | <ID> | <rol> | <n> | <AAAA-MM-DD> | abierta |

**Regla de cierre:** un hallazgo se cierra cuando el artefacto de destino esta
actualizado y la matriz de trazabilidad lo refleja. No se cierra por acuerdo.
