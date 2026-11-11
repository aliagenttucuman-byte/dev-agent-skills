# Plan de test

> Artefacto obligatorio en todo PR que cambia comportamiento observable.
> Referencia de `dev-kit-testing`. Completar, no dejar en blanco.
> Cada linea del plan debe poder convertirse en un test con nombre y assert.

---

## Identificacion

- **PR / ticket:**
- **Modulo o servicio afectado:**
- **Regla de negocio que cambia:**
- **Nivel de riesgo:** bajo / medio / alto / critico

---

## 1. Reglas afectadas y criterio de aceptacion

Una fila por regla. La columna "criterio de aceptacion" es la que se convierte
en el assert del test.

| # | Regla de negocio | Como falla si se rompe | Criterio de aceptacion | Nivel |
|---|---|---|---|---|
| 1 | | | | unitario / integracion / e2e / contract |
| 2 | | | | |
| 3 | | | | |

**Regla:** si una fila no tiene criterio de aceptacion, no hay test que
escribir. Si una regla no se lista, queda fuera del alcance del PR y eso debe
ser explicito.

---

## 2. Casos borde yPaths de error

| # | Caso (borde o error) | Entrada | Resultado esperado | Nivel |
|---|---|---|---|---|
| 1 | vacio / null | | | |
| 2 | limite (max, min, exacto) | | | |
| 3 | duplicado | | | |
| 4 | formato invalido | | | |
| 5 | dependencia caida | | | |
| 6 | concurrencia / reentrada | | | |

---

## 3. Fixtures y datos de test

- **Fixtures nuevas o modificadas:**
- **Factories usadas:**
- **Datos sensibles usados:** (deben ser sinteticos, nunca reales)

```text
fixture: <nombre> -> <que provee> -> <scope: function | module | session>
factory: <nombre> -> <que construye> -> <defaults validos>
```

---

## 4. Doubles de prueba

| Doble | Tipo (stub/fake/mock/spy) | Que frontera reemplaza | Por que no se testea real |
|---|---|---|---|
| | | | |

**Regla:** ningun doble reemplaza logica propia. Si el doble reemplaza algo que
se quiere verificar, el test no verifica nada.

---

## 5. Plan por nivel

### 5.1 Unitarios

| Test (nombre completo) | Regla que cubre | Asercion principal |
|---|---|---|
| `test_` | | |

### 5.2 Integracion

| Test (nombre completo) | Componente / contrato que verifica | Datos de base |
|---|---|---|
| `test_` | | |

### 5.3 E2E

| Test (nombre completo) | Flujo de usuario | Precondicion |
|---|---|---|
| `test_` | | |

### 5.4 Contrato (si aplica)

- **Productor:** <servicio> publica <schema>
- **Consumidor:** <servicio> acepta <campos minimos>
- **Version del contrato:** <version>
- **Compatibilidad:** compatible / rompe y exige version nueva

---

## 6. Cobertura

- **Linea base antes del PR:** <numero>%
- **Linea base despues del PR:** <numero>%
- **Delta:** <+/- numero> puntos
- **Si el delta baja:** ADR que lo justifica (id): <ADR>

---

## 7. No se testea (y por que)

| Elemento | Por que no lleva test |
|---|---|
| | |

Esta seccion es obligatoria y no puede estar vacia. Es la que evita que el
proximo PR agregue tests por inercia sobre codigo que no lo necesita.

---

## 8. Ejecucion

```bash
# suite rapida (obligatoria antes de push)
pytest tests/unit -q

# suite completa (obligatoria antes de merge)
pytest -q

# cobertura
pytest --cov=src --cov-report=term-missing --cov-fail-under=<LINEA_BASE>

# e2e (si el PR toca camino critico)
playwright test --project=smoke
```

- **Resultado local:** verde / rojo
- **Tests nuevos:** <numero>
- **Tests modificados:** <numero>
- **Tests eliminados:** <numero> (motivo: <motivo>)

---

## 9. Checkpoint

- [ ] Cada regla afectada tiene un test con nombre y criterio de aceptacion
- [ ] Los casos borde criticos estan cubiertos
- [ ] Ningun doble reemplaza logica propia
- [ ] No se mockea el tiempo con `sleep`
- [ ] Los tests no dependen del orden de ejecucion
- [ ] La cobertura no baja respecto de la linea base
- [ ] La seccion "No se testea" esta completa
- [ ] El plan refleja el diff real, no la intencion

**Gate:** el PR no se mergea sin este plan completo y con tests verdes.
