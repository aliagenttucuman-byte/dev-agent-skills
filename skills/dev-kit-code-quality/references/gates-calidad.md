# Gates de calidad: implementacion, excepciones y linea base

Detalle operativo de los gates G1 a G8 definidos en `SKILL.md`. Esta referencia
responde: como se implementa cada gate, como se escala una excepcion y como se
mantiene la linea base de cobertura.

---

## 1. Anatomia de un gate

Todo gate tiene tres partes. Si le falta una, no es un gate.

| Parte | Pregunta que responde | Donde vive |
|---|---|---|
| Medida | Que se evalua | Definicion del gate |
| Comando | Como se evalua | Configuracion de la herramienta |
| Umbral | Cuando pasa | Configuracion de la herramienta |

Ejemplo completo:

```yaml
# Gate G5 - tests
measure: "suite de tests completa"
command: "pytest -q --cov=src --cov-report=xml"
threshold: "0 fallos y cobertura >= linea base"
fails: "el pipeline se detiene antes de la etapa de build"
```

Un gate sin umbral se reporta pero no bloquea. Un gate sin comando no se puede
reproducir. Un gate sin "fails" es decorativo.

---

## 2. G1 - Formato

```bash
ruff format --check .
```

- **Donde corre:** pre-commit (commit) y CI (pipeline completo).
- **Excepcion valida:** codigo generado automaticamente. Se anade a
  `extend-exclude` en la config de ruff con un comentario que diga quien lo
  genera.
- **Excepcion invalida:** "este archivo es viejo". Los archivos viejos se
  formatean en un commit aparte, sin cambios funcionales.

```bash
# Commit de normalizacion, sin cambios de logica
ruff format . && git diff --stat
```

---

## 3. G2 - Lint

```bash
ruff check .
```

- **Fallo por regla:** se informa por familia (no por archivo). Un equipo que ve
  "12 errores de `ANN`" sabe que hacer; un equipo que ve 200 archivos con errores
  no sabe por donde empezar.
- **Excepcion:** `# noqa: RULE` con comentario. Formato obligatorio:

```python
# El cliente de pagos exige SHA-1 por contrato de la pasarela: no negociable.
digest = hashlib.sha1(payload).hexdigest()  # noqa: S324
```

- **Regla de escala:** una regla que falla mas de 20 veces se "
  grandfathered" durante una semana: se desactiva a nivel de repo con un `# TODO`
  y una fecha de reversion, no se arregla de a una.

---

## 4. G3 - Tipos

```bash
mypy src        # con strict = True
npx tsc --noEmit
```

- **Regla:** los errores de tipos no se silencian con `Any` en cascada.
- **Excepcion temporal:** `# type: ignore[error-code]` con ticket de seguimiento en
  el comentario. El `warn_unused_ignores = True` en mypy obliga a que el ignore
  se elimine cuando el error desaparece.
- **Frontera legitima:** `Any` solo donde entra codigo sin tipar (JSON crudo,
  respuesta de un tercero). En ese punto se convierte a tipo del dominio
  inmediatamente, con un validador.

```python
def parse_raw(payload: dict[str, Any]) -> Order:
    """Convierte la respuesta cruda del proveedor al modelo del dominio."""
    return Order.model_validate(payload)  # la validacion ocurre aca
```

---

## 5. G4 - Complejidad

```bash
radon cc -s -n B src     # falla si hay clase B o peor
complexipy --max-complexity 10 src
```

- **Alcance:** solo codigo nuevo y modificado. El codigo existente se mide y se
  registra como linea base, no se bloquea.
- **Excepcion:** una funcion con complejidad alta que sea casi lineal (muchos
  `if` de validacion sin ramificacion) se acepta con un comentario que lo diga.
- **Como se mide el delta:** el pipeline compara la complejidad del diff, no la
  del repo completo.

```bash
git diff --name-only origin/main...HEAD | grep '\.py$' | xargs radon cc -s -n B
```

---

## 6. G5 - Tests

```bash
pytest -q
```

- **Sin `skip` sin justificacion.** Un `pytest.mark.skip` con un comentario del
  porque y un issue de seguimiento. Un skip sin fecha es un test muerto.
- **Sin `xfail` sin condiciones.** Un `xfail` que se cumple en silencio es peor
  que un test roto: hides el defecto.
- **Orden de los markers:** `unit`, `integration`, `e2e`, `slow`. El pipeline
  corre primero `unit` (rapido, feedback inmediato) y despues el resto.

```bash
pytest -q -m unit              # solo unitarios
pytest -q -m "not e2e"         # todo menos end-to-end
pytest -q -m e2e               # solo end-to-end
```

---

## 7. G6 - Secretos

```bash
gitleaks detect --no-git --redact
```

- Corre en pre-commit y en CI.
- `--redact` es obligatorio: la salida del scanner no debe contener el secreto
  en claro.
- Si hay una filtracion real: **rotar el secreto primero**, despues limpiar el
  historial. Limpiar sin rotar deja vivo el secreto.

---

## 8. G7 - Cobertura

```bash
pytest --cov=src --cov-report=xml --cov-report=term-missing
```

**La cobertura es un piso, no una meta.** Un 95% de cobertura puede ocultar una
base de codigo sin un solo test de los caminos de error.

### Como se mantiene la linea base

1. El pipeline publica el numero de cobertura del PR.
2. Si el numero baja por debajo de la linea base, el gate falla.
3. La linea base sube manualmente cuando el PR **agrega** tests bien hechos.

```bash
# Reporte con el detalle de lo que falta cubrir
pytest --cov=src --cov-report=term-missing | grep -E "^src/.*[0-9]+%"
```

### Que medir

| Si | No |
|---|---|
| Ramas de error y casos borde | Funciones `getter` triviales |
| Reglas de negocio | Imports y `__init__` |
| Validaciones de entrada | Codigo de terceros que no controlamos |
| Integraciones criticas | Clases de datos sin comportamiento |

---

## 9. G8 - Build

```bash
python -m build        # o el comando de build del frontend
```

- El artefacto tiene que generarse de forma reproducible: mismo commit, mismo
  hash de artefacto.
- El pipeline nunca despliega un artefacto que no se construyo en ese pipeline.

---

## 10. Escalamiento de excepciones

Una excepcion de gate es un artefacto, no un comentario de chat.

```yaml
# exceptions/gates.yaml
- gate: G4-complejidad
  scope: "src/payments/legacy_router.py"
  reason: "Refund logic: 14 branches, each with a dedicated test"
  owner: "equipo de pagos"
  expires: "2026-12-31"
  reviewed_by: "lider tecnico"
```

Reglas:

- Toda excepcion tiene **dueño** (un rol, no una persona), **motivo**, **fecha de
  vencimiento** y **fecha de revision**.
- Sin vencimiento, no es excepcion: es deuda sin control. El pipeline la
  rechaza.
- Al vencer, el gate vuelve a fallar. La renovacion es un acto explicito.

---

## 11. Como se reportan los gates

Un tablero con una fila por gate:

| Gate | Estado | Bloquea | Ultimo fallo | Excepciones |
|---|---|---|---|---|
| G1 Formato | verde | commit | ninguno | 0 |
| G2 Lint | verde | commit | 3 dias atras | 1 |
| G3 Tipos | verde | pipeline | ninguno | 0 |
| G4 Complejidad | amarillo | pipeline | 1 semana atras | 2 |
| G5 Tests | verde | pipeline | ninguno | 0 |
| G6 Secretos | verde | pipeline | ninguno | 0 |
| G7 Cobertura | amarillo | pipeline | 2 semanas atras | 0 |
| G8 Build | verde | pipeline | ninguno | 0 |

**Verde** = pasa. **Amarillo** = pasa con excepcion vigente. **Rojo** = falla y
bloquea. Un gate que nunca falla es un gate que nadie mira.
