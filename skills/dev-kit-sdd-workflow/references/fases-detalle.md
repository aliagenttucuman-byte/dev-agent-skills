# Fases del flujo SDD en detalle

Referencia extendida de `dev-kit-sdd-workflow`. Cada fase: entrada, trabajo, salida, gate.

---

## Fase 1 - Constitucion

**Entrada:** la idea del proyecto, en una frase o un parrafo.

**Trabajo:** definir el marco. Que stack esta permitido, que calidad se espera,
que reglas de negocio son inviolables, que restricciones pesan (presupuesto,
plazo, compliance), que principios de UX rigen.

**Salida:** `CONSTITUTION.md`.

**Gate:** el archivo existe y cada seccion tiene al menos una decision
escrita (no un placeholder). Sin gate, la constitucion es decorativa.

**Lo que define una buena constitucion:**
- El stack por defecto y como desviarse de el.
- Los umbrales de calidad verificables (cobertura minima, complejidad maxima,
  tipos obligatorios).
- Las reglas de negocio que ningun agente puede romper.
- Las restricciones con su origen (por que ese presupuesto, por que ese plazo).
- Lo que esta prohibido explicitamente.

---

## Fase 2 - Especificar

**Entrada:** `CONSTITUTION.md` + el problema a resolver.

**Trabajo:** escribir el contrato. Que expone el sistema, que entradas tiene,
que errores maneja, que criterios de aceptacion tiene cada historia.

**Salida:** `specs/openapi.yaml`, `specs/user-stories.md`, `specs/data-model.md`.

**Gate:** el OpenAPI valida. Cada historia tiene criterios de aceptacion
verificables. No hay endpoint sin historia que lo justifique.

**Error tipico:** especificar la solucion (tabla, endpoint) en vez del problema.
La spec dice que se necesita el dato, no que la tabla se llama `X`.

---

## Fase 3 - Clarificar

**Entrada:** el spec escrito.

**Trabajo:** buscar la ambiguedad. Permisos, datos vacios, limites de paginacion,
errores parciales, concurrencia, que pasa si una dependencia externa cae.

**Salida:** seccion `## Clarificaciones` agregada al spec, con la pregunta y la
respuesta, y quien decidio.

**Gate:** cada ambiguedad listada tiene respuesta o una decision de "se asume X
porque Y".

**Por que existe:** una ambiguedad sin resolver se convierte en una decision
tomada por el que escribe el codigo, en silencio, tres dias despues.

---

## Fase 4 - Planear

**Entrada:** spec + clarificaciones.

**Trabajo:** decidir como. Componentes, dependencias y versiones, orden de
implementacion, modelo de datos, estrategia de testing, riesgos y mitigaciones.

**Salida:** `PLAN.md`.

**Gate:** los contratos de API estan cerrados. A partir de aqui, backend y
frontend pueden trabajar en paralelo.

**Error tipico:** el plan describe el codigo a escribir en vez de los
componentes a construir. Si un lector tiene que imaginar un archivo, al plan
le falta una decision.

---

## Fase 5 - Estimar

**Entrada:** `PLAN.md`.

**Trabajo:** poner numeros. Costo de infra, de tokens, de suscripciones, de
equipo, por escenario.

**Salida:** `ESTIMACION.md`.

**Gate:** hay tres escenarios (conservador, base, optimista) y una decision
recomendada. La decision economica la toma el cliente, no el agente.

---

## Fase 6 - Analizar

**Entrada:** spec + plan + estimacion.

**Trabajo:** verificar coherencia en las tres direcciones.

- Plan que no cubre historias -> gap.
- Plan que agrega cosas no pedidas -> over-engineering.
- Historias sin endpoint -> gap.
- Entidades sin soporte en el modelo de datos -> gap.
- Tareas del plan sin estimar -> gap.

**Salida:** `REPORT-GAPS.md` con severidad.

**Gate:** cero gaps bloqueantes. Con gaps no bloqueantes se avanza documentando
el riesgo aceptado.

---

## Fase 7 - Tareas

**Entrada:** `PLAN.md` validado.

**Trabajo:** convertir en tareas asignables. Una tarea = un agente = un output
verificable, con contexto explicito.

**Salida:** `TASKS.md`.

**Gate:** cada tarea tiene responsable, criterio de aceptacion, dependencias y
contexto suficiente para ejecutarla sin preguntar.

---

## Fase 8 - Checklist

**Entrada:** todos los artefactos anteriores.

**Trabajo:** verificar que todo esta listo. El checklist es la ultima linea de
defensa antes de que un agente escriba codigo.

**Salida:** `CHECKLIST.md` con todos los items en verde.

**Gate:** ningun item sin verificar. Un item sin check es un item sin verificar.

---

## Fase 9 - Implementar

**Entrada:** todo verde.

**Trabajo:** ejecutar contra los contratos.

**Regla:** si aparece un gap de diseno, se vuelve a la fase 4. No se improvisa
en codigo. El costo de volver es menor que el costo de construir sobre una
base equivocada.

**Salida:** codigo + tests + evidencia de que los criterios se cumplen.

**Gate:** cada criterio de aceptacion de cada historia tiene un test o una
verificacion que lo cubre.
