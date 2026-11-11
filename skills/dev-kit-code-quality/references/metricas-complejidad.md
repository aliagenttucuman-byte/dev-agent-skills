# Metricas de complejidad y recetas de refactor

Guia de detalle para medir y bajar la complejidad del codigo. Complementa la
seccion "Metricas de complejidad" de `SKILL.md`.

---

## 1. Complejidad ciclomatica

### Que mide

El numero de caminos de ejecucion posibles de una funcion. Se calcula como
`1 + (cantidad de decisiones)`, donde cada `if`, `elif`, `for`, `while`, `case`,
`and`, `or` y comparacion booleana suma uno.

```python
def classify(order):          # base = 1
    if order.total > 100:    # +1  -> 2
        if order.priority:    # +1  -> 3
            return "high"     # camino 1
        return "normal"       # camino 2
    return "low"              # camino 3
```

Tres caminos: la funcion se prueba con tres casos minimos.

### Clases de radon

| Clase | Rango | Veredicto |
|---|---|---|
| A | 1 - 5 | trivial, no mirar |
| B | 6 - 10 | aceptable, es el techo |
| C | 11 - 20 | refactorizar |
| D | 21 - 30 | refactorizar ya |
| E | 31 - 40 | reescribir |
| F | 41+ | reescribir desde cero |

```bash
radon cc -s -n B src              # solo lo que supera el techo
radon cc -s -a src               # promedio por modulo
radon raw -s src                 # lineas, complejidad y volumen
```

### Clases de McCabe

| Valor | Interpretacion | Tests necesarios |
|---|---|---|
| 1 - 4 | simple | 1 caso base |
| 5 - 9 | baja | 1 caso base + camino alterno |
| 10 - 20 | media | 1 por rama |
| 21+ | alta | tabla de decisiones o refactor |

**Relacion con testing:** el numero minimo de casos de test de una funcion es su
complejidad ciclomatica. Una funcion de complejidad 15 necesita al menos 15
casos para cubrir todos los caminos. Esa es la justificacion tecnica del techo,
no la prefierncia estilistica.

---

## 2. Deep nesting

### Que mide

Cuantos niveles de indentacion se acumulan dentro de una funcion.

| Nivel | Lectura | Veredicto |
|---|---|---|
| 1 | caso normal | bien |
| 2 | una rama | bien |
| 3 | rama dentro de rama | aceptable con nombre |
| 4 | limite | extraer |
| 5+ | ilegible | obligatorio extraer |

### Como se mide sin herramienta

```bash
# Funciones con mas de 4 niveles de indentacion
grep -rnE "^(\t| {8,})" --include="*.py" src | awk -F: '{print $1}' | sort | uniq -c | sort -rn
```

En el caso de Python la convencion es de 4 espacios por nivel: 8 espacios de
indentacion profunda son 2 niveles, 16 espacios son 4 niveles.

### Por que el nesting es peor que la longitud

Una funcion de 80 lineas planas se lee de arriba abajo. Una funcion de 30 lineas
con 5 niveles de indentacion exige mantener en la cabeza el contexto de cada
nivel. El costo cognitivo escala con el nesting, no con la longitud.

---

## 3. Las otras cuatro metricas

### Longitud de funcion

| Metrica | Umbral | Motivo |
|---|---|---|
| Lineas por funcion | 50 | el diff legible cabe en una pantalla |
| Lineas logicas (sin comentarios ni vacias) | 30 | el codigo real que hay que entender |
| Statements por funcion | 15 | cada statement es una decision potencial |

```bash
radon raw -s src | head -20     # loc, lloc, statements por archivo
```

### Cantidad de argumentos

| Argumentos | Sintoma | Solucion |
|---|---|---|
| 0 - 3 | normal | nada |
| 4 - 5 | empieza a doler | agrupar en un objeto de dominio |
| 6+ | bandera roja | objeto de dominio o parametros keyword-only |

```python
# 6 argumentos: una posicion incorrecta rompe todo en silencio
def create_order(user_id, product_id, quantity, price, currency, discount, warehouse): ...

# Con un objeto de dominio: la posicion no importa
def create_order(order: OrderDraft) -> Order: ...
```

### Acoplamiento

| Metrica | Umbral | Como se mide |
|---|---|---|
| Imports por modulo | 15 | `ruff` reporta si se supera el limite con `TID` |
| Fan-out (modulos que dependen de este) | 20 | grafo de dependencias |
| Fan-in (modulos de los que depende) | ilimitado | un modulo util puede tener muchos fans |
| Ciclos de import | 0 | rompe el arranque |

Un modulo que importa 30 cosas no se puede testear aislado. Es una funcion con
30 dependencias, y probarla requiere probarlas todas.

### Duplicacion

| Bloque repetido | Veredicto |
|---|---|
| 2 lineas | aceptable |
| 3+ lineas | extraer a funcion |
| Bloque completo | extraer modulo |
| Copia con una diferencia minima | casi siempre es un bug esperando |

Copia con una diferencia minima: dos rutas de codigo casi identicas divergen
eventualmente, y el bug se reproduce en una sola de ellas.

---

## 4. Recetas de refactor, ordenadas por costo

De menor a mayor invasion. Siempre se empieza por la primera que resuelva.

### Receta 1 - Nombrar la condicion

```python
# Antes
if order.status == "pending" and order.total > 50 and not order.is_priority:
    discount = 0.1

# Despues
def qualifies_for_base_discount(order: Order) -> bool:
    return order.status == "pending" and order.total > 50 and not order.is_priority

if qualifies_for_base_discount(order):
    discount = 0.1
```

Costo: cero. Reduce la complejidad de la funcion que llama, y el nombre viaja
solo. **Es la primera opcion siempre que aplique.**

### Receta 2 - Early return

```python
# Antes: la condicion(valido) esta al final
def process(order):
    if order.is_valid():
        validate_schema(order)
        charge(order)
        notify(order)

# Despues: el caso raro sale primero
def process(order):
    if not order.is_valid():
        raise InvalidOrder(order.id)
    validate_schema(order)
    charge(order)
    notify(order)
```

Costo: bajo. Aplana la funcion y saca el `else` implicito.

### Receta 3 - Tabla de reglas

```python
# Antes: cadena de if
def fee_for(plan: str, seats: int) -> Decimal:
    if plan == "free":
        return Decimal("0")
    if plan == "basic":
        return Decimal("10")
    if plan == "pro":
        return Decimal("50") if seats <= 10 else Decimal("80")
    return Decimal("0")

# Despues: tabla
FEE_TABLE = {
    ("free", 0): Decimal("0"),
    ("basic", 0): Decimal("10"),
    ("pro", 10): Decimal("50"),
    ("pro", 99): Decimal("80"),
}

def fee_for(plan: str, seats: int) -> Decimal:
    limit = 10 if plan == "pro" else 0
    return FEE_TABLE.get((plan, limit), Decimal("0"))
```

Costo: medio. La tabla es testeable caso por caso, y agregar un plan no toca
la logica.

### Receta 4 - Partir la funcion

Cuando la funcion tiene dos responsabilidades con nombre propio. El umbral es
semantico, no de lineas: si las dos mitades se pueden nombrar con un verbo, se
parten.

```python
def handle_request(payload) -> Response:
    parsed = validate(payload)
    result = process(parsed)
    return render(result)
```

Costo: medio. Cuidado con la explosion de funciones de una linea: una funcion
que solo reenvia a otra no aporta.

### Receta 5 - Patron de diseno

Ultimo recurso. Solo cuando hay **variacion real** en el comportamiento (tres
implementaciones o mas), no cuando se sospecha que habra.

| Patron | Cuando |
|---|---|
| Strategy | Comportamiento intercambiable según un parametro |
| Policy | Regla de negocio que cambia por caso |
| State | Ciclo de vida con transiciones |
| Repository | Acceso a datos que se quiere aislar |
| Adapter | Integracion con un sistema con formato propio |

**Regla:** un patron con una sola implementacion es sobre-ingenieria. Se escribe
el ADR antes de aplicarlo (`dev-kit-documentation`).

---

## 5. Medicion del delta

La metrica que importa en un PR es el cambio, no el total.

```bash
# Complejidad solo de los archivos tocados en el PR
git diff --name-only origin/main...HEAD | grep '\.py$' | xargs radon cc -s -n B

# Comparacion antes/despues sobre el mismo archivo
git show origin/main:src/module.py > /tmp/antes.py
radon cc -s /tmp/antes.py
radon cc -s src/module.py
```

**Regla del PR:** la complejidad ciclomatica total del modulo no sube. Si una
funcion baja de 20 a 5 pero el modulo sube de 25 a 30, el PR no mejora nada:
movio la complejidad de lugar. Se acepta cuando el objetivo declarado es
justamente ese (por ejemplo, aislar una funcion para testearla).

---

## 6. Reporte de linea base

El repositorio guarda su estado de complejidad al inicio del trabajo con agentes,
para poder comparar:

```bash
radon cc -s -a src > complejidad-base.txt
radon raw -s src >> complejidad-base.txt
```

Ese archivo es la linea base. Los gates del pipeline comparan contra el, y el
diff se revisa en el PR como cualquier otro cambio.
