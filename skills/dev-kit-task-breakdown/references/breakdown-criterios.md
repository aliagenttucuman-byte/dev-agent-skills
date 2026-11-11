# Criterios de breakdown: particion, dependencias y casos borde

> Referencia de apoyo para `dev-kit-task-breakdown`. Detalla como se recorta un
> plan en tareas, como se construyen las dependencias y que hacer con los casos
> que no encajan en el flujo normal.

---

## 1. Los tres filtros de particion

Una tarea sale de un paso del plan. Se aplica un filtro por dimension. Si
falla cualquiera, la tarea se parte.

### Filtro de tamano

| Senal | Umbral | Por que |
|---|---|---|
| Archivos nuevos o modificados | mas de 6 | el review se vuelve inmanejable |
| Carpetas tocadas | mas de 2 | probabilidad de cruzar capas |
| Criterios de aceptacion | mas de 3 | suele esconder dos resultados |
| Lineas de logica de negocio | mas de 200 | no entra en una sesion |
| Tareas de un mismo PR | mas de 3 | el PR deja de ser revisable |

### Filtro de capa

Cada tarea pertenece a una sola capa del roster:

```
producto -> contrato -> diseno -> implementacion -> datos
                                   |
                                   v
                             verificacion -> operacion
```

| Si la tarea toca | Se parte en |
|---|---|
| contrato y diseno | una tarea de contrato y una de diseno |
| diseno e implementacion | una tarea de diseno (senior) y una de implementacion (dev) |
| implementacion y datos | la migracion va con la tarea de datos, no con la de endpoint |
| implementacion y verificacion | **no se parte**: los tests van con la logica |

### Filtro de heterogeneidad

Si dos tareas del mismo bloque podrian intercambiarse sin romper nada, estan
mal separadas: les falta un contexto que las diferencia.

```markdown
# mal: dos tareas intercambiables
T-01: Implementar servicio de pedidos
T-02: Implementar servicio de clientes

# bien: cada una con su resultado
T-01: Servicio de creacion de pedido con validacion de stock
T-02: Servicio de consulta de cliente con resolucion de direccion
```

---

## 2. Construccion del DAG

### De donde salen las dependencias

Las dependencias se leen del plan, no se inventan. Fuentes validas, en orden de
autoridad:

1. La tabla de orden de implementacion del `PLAN.md`.
2. El contrato de API: si un endpoint consume otro, esa es una dependencia
   dura; si solo comparte esquema, es de contrato.
3. La migracion: una tarea que usa una tabla nueva depende de la migracion.

### Clasificacion de cada arista

| Tipo | Se rompe si | Como se mitiga |
|---|---|---|
| **Dura** | el artefacto no existe | se planifica la entrega primero |
| **De contrato** | el contrato cambia | se versiona el contrato y ambos lados lo citan |
| **De convencion** | el estilo cambia | va a "Restricciones", no bloquea |

### Paralelismo: la prueba de los tres requisitos

Dos tareas van en paralelo si se cumple **todo** esto:

1. Los conjuntos de archivos que tocan no se solapan.
2. La dependencia entre ellas es de contrato, no de codigo.
3. El contrato que las une esta cerrado y versionado.

| Escenario | Paralelizables |
|---|---|
| Backend y frontend con OpenAPI cerrado | si |
| Backend y frontend con OpenAPI abierto | no |
| Dos endpoints que no se tocan | si |
| Dos tareas del mismo paquete | no |
| Una tarea de codigo y una de pipeline | si, si el pipeline no necesita el codigo |
| Una migracion y el endpoint que la usa | no: dependencia dura |

### Detectar y romper un ciclo

```
T-01 (esquema) <-> T-02 (repositorio)
```

El ciclo aparece cuando dos tareas se necesitan mutuamente. Causa tipica: se
partio por el orden equivocado. Se rompe de dos formas:

| Forma | Cuando |
|---|---|
| Unir en una sola tarea | las dos partes son inseparables y de la misma capa |
| Introducir un artefacto intermedio | hace falta un contrato que las separe |

Un ciclo **nunca** se rompe "poniendo una dependencia mas fuerte" sobre el
papel: el ciclo es real, es un problema de particion.

---

## 3. El campo Contexto: los seis campos en detalle

### Objetivo

Una frase en presente, con un verbo observable: "el endpoint X devuelve Y
paginado por cursor". No "mejorar el manejo de pedidos".

**Prueba:** si el objetivo se puede lograr de dos maneras distintas, todavia
esta demasiado vago.

### Punto de partida

El artefacto del que sale la tarea, con su version o fecha:

| Tipo de artefacto | Ejemplo de referencia |
|---|---|
| Contrato de API | `specs/openapi.yaml` (recurso Pedidos) |
| Plan | `PLAN.md` seccion Modelo de datos |
| ADR | `docs/adr/0002-migraciones.md` |
| Constitucion | `CONSTITUTION.md` seccion Estandares de calidad |
| Codigo existente | `src/app/domain/entities/pedido.py` |

Si no hay artefacto de partida, la tarea no tiene ancla: el agente arranca
adivinando el criterio.

### Alcance

Los archivos o modulos que la tarea toca. Se lista de forma explicita para que
otro agente no los toque en paralelo y para que el reviewer sepa donde mirar.

```markdown
**Alcance:**
- `src/app/domain/entities/pedido.py` (nuevo)
- `src/app/domain/rules/pedido_rules.py` (nuevo)
- `tests/unit/test_pedido.py` (nuevo)
```

### Fuera de alcance

Lo que el agente NO debe tocar. Es el campo que mas se olvida y el que mas
previene conflictos:

```markdown
**Fuera de alcance:**
- el modelo de ORM en `infra/db/models.py` (va en T-02)
- el contrato de `POST /pedidos` (cerrado, no se modifica)
- la migracion de esquema (va en T-04)
```

### Restricciones

Las reglas del proyecto que aplican, copiadas de la constitucion o del ADR
relevante. No las reglas generales del equipo: solo las que tocan esta tarea.

### Criterio de aceptacion

El comando y que prueba. Si hay varios comandos, se listan todos en la tabla
de subpuntos verificables.

---

## 4. Tamano: guia de reparto, no estimacion

El campo `Tamano` no es una estimacion de horas. Es una guia para decidir como
se reparte la carga entre agentes.

| Tamano | Criterio | Reparto |
|---|---|---|
| pequeno | 1 sesion, 1-2 carpetas, 1 comando | un agente, sin interrupciones |
| medio | 2-3 carpetas o un modulo completo | un agente, revisar al terminar |
| grande | mas de 3 carpetas o varias capas | partir antes de asignar |

**Regla:** una tarea `grande` en `TASKS.md` es una tarea mal partida. El
breakdown se revisa hasta que ninguna quede `grande`.

La estimacion formal de esfuerzo vive en el artefacto de estimacion del
proyecto, no en el breakdown.

---

## 5. Casos borde

### El plan no tiene tabla de orden

Se construye el DAG desde el contrato y las dependencias tecnicas evidentes
(la migracion antes del endpoint, el endpoint antes del frontend). Si aun asi
queda ambiguo, la pregunta va al plan: no se inventa el orden.

### Una historia muy grande

Se parte por caso de uso, no por capa completa. El criterio de corte es el
**escenario de usuario**: cada tarea cubre un escenario verificable de punta a
punta dentro de una capa.

### Una historia muy pequena

Se agrupa con una del mismo dueno y la misma capa. Si no hay ninguna, la tarea
sola es valida: una tarea de una linea con su comando sigue siendo una tarea.

### Dos historias que se tocan

Se revisa si comparten archivo. Si lo comparten, o se unen en una tarea o se
serializan explicitamente en el DAG. Lo que no se hace es dejar dos historias
en paralelo sobre el mismo archivo.

### Un criterio de aceptacion que no se puede automatizar

Se busca la forma mas cercana que si se pueda. Si no existe ninguna, el
criterio se mueve a "verificacion" y lo cubre una tarea de QA con evidencia
manual (captura, reporte). Nunca queda sin cubrir.

### La tarea requiere una decision que no esta tomada

No se asigna. Se devuelve al plan o al ADR. Una tarea que arranca suponiendo
una decision produce codigo que hay que tirar.

### El trabajo exploratorio

No es una tarea de implementacion: es una tarea de investigacion con su
criterio propio ("un reporte que compara las tres alternativas con criterio
X"). No se mezcla con la implementacion de la eleccion.

### Reasignacion a mitad de camino

La tarea cambia de dueno: se actualizan responsable, estado y el bloque de
notas de entrega. Se registra que paso, para que el siguiente agente sepa que
hereda un intento parcial.

---

## 6. Checklist de calidad del breakdown

- [ ] Cada tarea tiene un unico responsable del roster.
- [ ] Cada tarea toca una sola capa.
- [ ] Cada tarea tiene los seis campos de contexto completos.
- [ ] Cada criterio de aceptacion es un comando ejecutable.
- [ ] No hay ninguna tarea con tamano `grande`.
- [ ] Los tests van dentro de la tarea de la logica que cubren.
- [ ] El DAG no tiene ciclos.
- [ ] Las dependencias blandas estan en "Restricciones", no bloqueando.
- [ ] Todos los criterios de las historias estan cubiertos por alguna tarea.
- [ ] Ninguna tarea depende de algo posterior.
- [ ] Los IDs son correlativos y no se reutilizan.
- [ ] No hay nombres de personas: solo roles del roster.
