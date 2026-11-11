# Estrategia por nivel de test

> Referencia de `dev-kit-testing`. Como se decide que nivel cubre cada riesgo y
> como se escala la suite sin que se vuelva lenta.

---

## 1. El criterio de decision

Un solo criterio decide el nivel: **como se manifiesta el fallo si la regla se
rompe**.

| Manifestacion del fallo | Nivel | Ejemplo |
|---|---|---|
| El resultado de una operacion pura cambia | unitario | el descuento mal calculado |
| El dato no llega al destino o llega mal | integracion | la orden no se persiste |
| El usuario no puede completar un flujo | e2e | el checkout no cierra |
| Otro sistema recibe un dato con otra forma | contract | el consumidor espera un campo que ya no existe |

**Regla:** un test de nivel superior que verifica lo mismo que uno inferior es
redundante. La piramide no es un adorno: cada nivel verifica algo que el de
abajo no puede ver.

---

## 2. Reparto objetivo y por que

| Nivel | Reparto objetivo | Costo | Cuando sube demasiado |
|---|---|---|---|
| Unitario | ~70% | milisegundos | logica extraida de la infraestructura: buena noticia |
| Integracion | ~20% | segundos | el modelo de dominio esta atado al ORM: mala noticia |
| E2E | ~10% | minutos | los flujos criticos se multiplicaron: revisar alcance |
| Contract | transversal | segundos | se versionaron contratos incompatibles |

**Como leer un reparto raro:**

- **Unitarios en 5%, integracion en 90%:** casi todo el codigo depende del
  framework. La accion no es testear mas: es extraer la logica de negocio a
  funciones puras y testearlas ahi.
- **E2E en 40%:** la suite tarda horas y el equipo deja de correrla. Bajar el
  E2E a los caminos criticos y mover el resto a integracion.
- **Cero unitarios, mucho E2E:** el equipo no confia en los tests rapidos. Es
  un problema de arnes, no de estrategia.

---

## 3. Que entra en cada nivel

### Unitario

- Funciones puras: calculos, validaciones, reglas de estado.
- Maquinas de estado y transiciones validas.
- Formateo y transformacion de datos.
- Casos borde de cada regla: vacio, uno, maximo, maximo mas uno, duplicado.

**No entra:** nada que toque red, disco, reloj real ni base de datos.

### Integracion

- El endpoint completo contra la base real de tests.
- El ORM con sus queries reales (detecta el N+1 y el mapeo roto).
- La migracion hacia adelante y hacia atras.
- El consumidor de un mensaje contra el productor real o contra su contrato.
- La autorizacion: el endpoint rechaza lo que debe rechazar.

**No entra:** el flujo completo de varios servicios con sus multiples
dependencias (eso es E2E).

### E2E

- El camino feliz completo de un rol (comprar, publicar, permisos).
- Los caminos que cruzan mas de un servicio.
- Un smoke por release: el recorrido minimo que demuestra que el sistema vivo.

**No entra:** cada combinacion de reglas. Se prueba en integracion.

### Contract

- Que el consumidor acepta la forma que el productor publica.
- Que un cambio incompatible del productor es detectado antes del despliegue.

---

## 4. Escalar la suite

### El presupuesto de tiempo

| Momento | Suite | Presupuesto | Que corre |
|---|---|---|---|
| Antes de cada push | unitaria | < 60 s | `pytest tests/unit -q` |
| Antes de cada PR | unitaria + integracion | < 5 min | `pytest -q` |
| Merge a main | completa | < 15 min | `pytest -q --cov` |
| Release | E2E smoke | < 15 min | `playwright test --project=smoke` |

**Regla:** si la suite del push supera el presupuesto, el problema es la suite,
no el presupuesto. Se mide con `pytest --durations=10` y se ataca el test mas
lento.

### Tres salidas, en este orden

1. **Alejar el I/O.** Un test de integracion que espera por red se reemplaza por
   un fake. Ojo: si el I/O **es** lo que se prueba, no se puede alejar.
2. **Marcar el test lento.** Para el suite largo, un marcador de slowest:

   ```bash
   pytest -m "not slow"        # push
   pytest -m "slow"            # pipeline completo
   ```

3. **Partir la suite.** Se separa en shards que corren en paralelo en CI:

   ```bash
   pytest -n auto              # con pytest-xdist, requiere plafond de recursos
   ```

### Lo que nunca se hace

- No se aumenta el presupuesto de tiempo porque la suite crecio.
- No se baja el timeout global para que el pipeline "pase": eso convierte tests
  lentos en tests falsos, que es peor que no tenerlos.
- No se desactiva un test flaky en el pipeline: se arregla o se borra con
  justificacion escrita.

---

## 5. Cobertura util: el criterio de piso

La cobertura se mide como **piso**, no como objetivo:

| Concepto | Definicion | Uso |
|---|---|---|
| Linea base | porcentaje minimo de cobertura del modulo | se compara con el PR |
| Delta | diferencia contra la linea base | si baja, el PR no pasa |
| Cobertura de rama | caminhos condicionales cubiertos | apunta a reglas, no a lineas |
| Mutacion sobreviviente | cambios que los tests no detectan | la verdad sobre la calidad |

**El error clasico:** subir cobertura ejecutando codigo. Un test que llama una
funcion y no afirma nada sube el numero y no sube la proteccion. Por eso el
gate de higiene (tests sin asercion, `sleep`, dependencia de orden) es tan
importante como el de cobertura.

**Regla operativa:** un PR puede bajar la cobertura de lineas si agrega tests
que no dependen de ella (por ejemplo, un test de contrato contra un mock) y lo
justifica en el plan. Lo que no se permite es bajar la cobertura sin analisis.

---

## 6. Tests de contrato en detalle

El contrato es la forma del dato en la frontera. Hay dos lados y dos tests.

| Lado | Test | Falla cuando |
|---|---|---|
| Productor | el esquema publicado se cumple | el productor cambia el contrato y no lo actualiza |
| Consumidor | el minimo que el consumidor necesita esta presente | el productor elimina o renombra un campo |

```python
# Test del consumidor: define el minimo que necesita, no el maximo del productor
def test_orders_contract_provides_required_fields(orders_client):
    payload = orders_client.get("/orders/1")

    assert set(payload) >= {"id", "status", "total", "created_at"}
    assert isinstance(payload["total"], int)
```

**Por que "minimo" y no "exacto":** si el consumidor exige el conjunto exacto
de campos, cada campo nuevo del productor rompe al consumidor sin necesidad. El
minimo protege lo que el consumidor usa; lo demas se acepta.

**Versionado:** un cambio incompatible (se elimina un campo, se cambia un tipo)
es una version nueva del contrato. El productor publica la version nueva, el
consumidor migra, y el despliegue del productor se bloquea hasta que todos los
consumidores esten en la version nueva.

---

## 7. Anti-patrones de estrategia

| Anti-patron | Sintoma | Correccion |
|---|---|---|
| Piramide invertida | mas E2E que unitarios | extraer logica pura |
| Suite como red de seguridad | todo el equipo depende del E2E para confiar | recuperar el unitario |
| Test que reimplementa el codigo | el test calcula lo mismo que la funcion | assert contra un valor fijo |
| Fixture que sabe demasiado | el test falla si algo no relacionado cambio | aislar el fixture |
| Suite lenta sin medicion | nadie sabe que test la traba | `pytest --durations=10` |
| Cobertura como objetivo | tests sin assert para subir el numero | piso + higiene |
| Un test, muchos asserts | al fallar no se sabe que se rompio | un comportamiento por test |
