# Supuestos de costo por categoria

Guias de estimacion para cada tipo de costo, con los supuestos que hay que
declarar explicitamente para que el numero sea defendible.

---

## Equipo de desarrollo

**Supuestos que hay que declarar:**
- Utilizacion efectiva (no todo el tiempo del mes es facturable).
- Cantidad de personas por rol durante todo el periodo.
- Pisos de calendario: el proyecto no puede durar menos que X meses con Y
  personas, aunque el trabajo real ocupe menos.
- Si el desarrollo se cobra mensual o por hito.

**Error tipico:** sumar meses de trabajo sin aplicar utilizacion. El resultado
es un numero que no se puede defender en una reunion.

**Como se corrige:** aplicar el mismo factor de utilizacion a todos los
escenarios y mostrarlo explicitamente en la tabla del equipo.

---

## Infraestructura cloud

**Supuestos que hay que declarar:**
- Ambiente de desarrollo vs produccion: se cobran por separado.
- Crecimiento esperado: el costo no es lineal si hay almacenamiento acumulativo
  (logs, backups, artefactos, datos historicos).
- Cuando se dispara el escalon: el costo real de un servidor cambia por saltos,
  no de forma continua.

**Error tipico:** estimar el mes 1 y Extrapolar linealmente. A los 6 meses el
error es de un factor.

**Como se corrige:** tres escenarios con volumetricos distintos, y un escenario
adicional de "crecimiento realista" que es el recommended.

---

## Consumo de LLM

**Supuestos que hay que declarar:**
- Tokens por request (entrada + salida).
- Requests por mes, y de donde sale ese numero.
- Cache hit rate, si hay caching.
- Modelo por tipo de uso: no es lo mismo un modelo caro para razonamiento que
  uno barato para clasificar.

**Error tipico:** forgetting los tokens de entrada. Si el contexto del prompt
es grande y se reenvia en cada request, la entrada domina el costo.

**Como se corrige:** calcular el costo por request con entrada y salida por
separado, y multiplicar por el volumen mensual declarado.

**Medicion:** el costo real se conoce recien despues del primer mes de uso.
La estimacion es un techo de referencia; el seguimiento mensual es el dato
real.

---

## Suscripciones y licencias

**Supuestos que hay que declarar:**
- Cantidad de licencias y quienes las necesitan (por rol, no por persona).
- Herramientas que se pueden compartir.

**Error tipico:** multiplicar licencias por el equipo completo cuando solo un
rol las necesita.

---

## Costos de una sola vez

**Supuestos que hay que declarar:**
- Licencias de desarrollo, hardware, credenciales de un solo uso.
- Si el proyecto los asume o el cliente.

---

## Sensibilidad

Antes de presentar un numero, responder tres preguntas:

1. **Que variable lo mueve mas?** Si es una sola, medir esa primero.
2. **Que pasa si se duplica el volumen?** El proyecto sigue siendo rentable?
3. **Que pasa si se alarga un mes?** El margen lo aguanta?

Si alguna respuesta es incómoda, el numero necesita un escenario mas o una
decision de alcance.
