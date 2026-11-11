# CONSTITUCION - <NOMBRE_DEL_PROYECTO>

> Documento rector del proyecto. Se escribe antes del codigo y se modifica solo
> por amendment explicito. Si una propuesta lo contradice, la propuesta se
> rechaza.
>
> Version: 0.1.0 | Fecha: <AAAA-MM-DD> | Owner: <rol> | Revisa en: <AAAA-MM-DD>

---

## 1. Principios rectores

> Principios que endurecen ante conflicto entre requisitos. Cuando dos
> requisitos se contradicen, gana el que este mas arriba.

1. **Simplicidad operativa sobre sofisticacion.** Una solucion que el equipo
   puede operar a las 3 de la manana vale mas que la optima en el paper.
2. **Contrato antes que implementacion.** Nada se construye sin el contrato
   de API que lo define.
3. **Lo verificable gana.** Un estandar sin comando que lo compruebe no es un
   estandar.
4. **El dominio no se negocia.** Las reglas de negocio son invariantes, no
   sugerencias.

---

## 2. Stack permitido

| Capa | Permitido | Desviacion permitida |
|---|---|---|
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2 + Pydantic v2 | otro framework, con justificacion escrita y aprobacion del arquitecto |
| Frontend | React 18 + TypeScript 5 + Vite | otro stack, con justificacion escrita |
| Datos | PostgreSQL 16 + Alembic | otro motor solo si no se requieren transacciones ACID |
| Contenedores | Docker + Compose | orquestacion de plataforma con justificacion |
| CI | GitHub Actions | otro runner por restriccion de red del entorno |
| Lint y tipos | ruff + mypy | equivalente que corra en CI con el mismo criterio |
| Tests | pytest + Playwright | equivalente con cobertura e2e equivalente |
| Observabilidad | OpenTelemetry | equivalente con trazas y metricas exportadas |

**Regla:** toda libreria o servicio nuevo entra por solicitud explicita y
aprobacion del arquitecto. La tabla no es una lista de sugerencias.

---

## 3. Estandares de calidad

| Estandar | Umbral | Como se verifica | Donde corre |
|---|---|---|---|
| Tipos | `mypy --strict` sin errores | `mypy .` | CI |
| Formato y lint | sin hallazgos | `ruff check .` | CI |
| Tests de dominio | cobertura >= 70% | `pytest --cov` | CI |
| Conformidad de API | cero desviaciones | diff contra `specs/openapi.yaml` | CI |
| Migraciones | reversibles | `alembic downgrade -1` | CI |
| Latencia de lectura | p95 < <ms> | metricas | staging |
| Errores | formato unico con correlation id | test de contrato | CI |
| Accesibilidad | sin violaciones serias | axe en e2e | CI |

---

## 4. Reglas de negocio

```
REGLA: <afirmacion invariante en una linea>
TIPO: invariante | politica | convencion
PRUEBA: <test o verificacion concreta>
```

| # | Regla | Tipo | Prueba |
|---|---|---|---|
| R1 | <afirmacion> | invariante | <test> |
| R2 | <afirmacion> | invariante | <test> |

---

## 5. Restricciones

| Dimension | Limite | Comportamiento al alcanzar el limite | Quien decide |
|---|---|---|---|
| Presupuesto de infra | <moneda> por mes | alerta al 80%, se pausa el deploy al 100% | <rol> |
| Presupuesto de LLM | <cantidad> de tokens por mes | alerta al 80% | <rol> |
| Plazo | <fecha o ventana> | <que se sacrifica> | <rol> |
| Carga | <usuarios concurrentes> | <degradacion> | <rol> |
| Datos | <clasificacion>, retencion <periodo> | <que se borra> | <rol> |
| Compliance | <marco aplicable> | <control> | <rol> |
| Red | <permitido o no> | <que se bloquea> | <rol> |

---

## 6. Principios de UX

- **Claridad sobre ingenieria interna.** El texto de la interfaz describe lo que va
  a pasar, no como funciona por dentro.
- **Estados visibles.** Toda vista asincrona define los estados de carga, vacio
  y error.
- **Errores accionables.** Cada mensaje dice que paso y que puede hacer el
  usuario.
- **Teclado primero.** Toda accion principal se puede completar sin mouse.
- **Accesibilidad por defecto.** Contraste suficiente, foco visible, labels
  asociados.
- **Sin sorpresas.** Ninguna accion destructiva ocurre sin confirmacion.
- **Internacionalizacion lista.** Textos fuera del codigo desde el primer dia.

---

## 7. Prohibiciones

| Prohibicion | Motivo | Como se detecta |
|---|---|---|
| No loguear datos personales | exposicion de datos | regla de lint + revision |
| No llamar a servicios externos sin cache | costo no acotado | revision de dependencias |
| No persistir secretos en el repo | fuga de credenciales | scanner de secretos |
| No agregar dependencias sin version pineada | builds no reproducibles | lockfile obligatorio |
| No hacer migraciones destructivas sin rollback | perdida de datos | revision de PR |
| No desactivar gates de CI | erosion del proceso | proteccion de rama |

---

## 8. Proceso de cambio

1. Toda modificacion se propone como **amendment**: numero, fecha, seccion
   afectada, texto nuevo, motivo.
2. El owner de la constitucion aprueba o rechaza.
3. El cambio se aplica en el mismo commit que lo justifica.
4. Los commits de codigo que contradigan la constitucion vigente se rechazan.

| # | Amendment | Fecha | Seccion | Motivo | Estado |
|---|---|---|---|---|---|
| A1 | <cambio> | <AAAA-MM-DD> | <n> | <motivo> | aprobado / rechazado |

---

## Apendice: decisiones abiertas

| # | Decision pendiente | Responsable | Fecha limite | Impacto si no se decide |
|---|---|---|---|---|
| D1 | <decision> | <rol> | <AAAA-MM-DD> | <impacto> |
