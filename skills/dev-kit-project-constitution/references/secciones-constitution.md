# Guia de escritura de la CONSTITUTION.md

Detalle seccion por seccion: que preguntar, como redactar y que errores
producen documentos que despues no se pueden aplicar.

---

## 1. Principios rectores

**Que responder:** ante dos requisitos contradictorios, cual gana.

**Numero recomendado:** 3 a 5. Mas de 5 no se recuerdan, y un principio que no
se recuerda no gobierna.

**Forma de cada principio:**

```
<Verbo en imperativo> <prioridad> sobre <la otra cosa>.
```

Ejemplos de forma utilizable:

- "Contrato antes que implementacion: nada se construye sin el contrato de API."
- "Simplicidad operativa sobre sofisticacion: la solucion debe poder operarse
  sin el equipo autor."

**Error tipico:** escribir valores ("quality is our priority"). Los valores no
resuelven conflictos porque no dicen que hacer cuando chocan.

**Prueba de que un principio funciona:** poner dos requisitos reales del
proyecto que se contradigan y ver si el principio indica cual gana. Si no,
el principio es decorativo.

---

## 2. Stack permitido

**Que preguntar:** que corre hoy, que se puede instalar sin aprobacion, que
libreria nueva requiere acuerdo.

**Formato de fila:**

| Capa | Permitido | Desviacion permitida |
|---|---|---|
| <capa> | <stack por defecto> | <condicion que habilita otra opcion> |

**Reglas:**

1. Una fila por capa. Lo que no esta, no esta permitido.
2. La desviacion se expresa como **condicion**, no como libertad.
3. Las librerias de terceros que el equipo ya usa se declaran aca con su
   proposito. El agente no debe inventar dependencias nuevas por su cuenta.
4. Los servicios externos (correo, almacenamiento, pasarelas, modelos de
   lenguaje) van en su propia fila con su condicion de uso, porque tienen
   costo variable.

**El patron de la fila de servicio externo:**

| Servicio | Proveedor | Cuando se usa | Condicion de corte |
|---|---|---|---|
| <servicio> | <nube/proveedor> | <caso de uso> | "no se usa si <X>" |

La columna "condicion de corte" es la que evita el gasto silencioso: sin ella,
un agente puede elegir el servicio mas caro sin que nadie lo note.

**Error tipico:** dejar la tabla como "stack del kit" sin condiciones. Es
delegar la decision al primer PR, que es exactamente lo que se queria evitar.

---

## 3. Estandares de calidad

**Que preguntar:** que comandos corre el equipo hoy, que umbrales se van a
medir de verdad, que se exige antes de mergear.

**Regla de oro:** cada estandar tiene **un comando o un artefacto** que lo
prueba. La tabla tiene tres columnas obligatorias: umbral, verificacion,
donde corre.

**Escala sugerida de umbrales** (ajustar al proyecto, no copiar):

| Tipo | Valor por defecto | Cuando se relaja |
|---|---|---|
| Tipos | `mypy --strict` | nunca sin justificacion escrita |
| Cobertura de dominio | 70% | 60% si hay integracion legacy sin tests |
| Latencia p95 | 400 ms lectura | 800 ms si hay dependencia externa lenta |
| Complejidad por funcion | 10 | 15 en orquestadores declarados |
| Tamaño de PR | 400 lineas | 800 con justificacion |

**Regla de relajacion:** un umbral se relaja **declarando el nuevo valor y el
motivo**, nunca omitiendo la fila. Si la fila desaparece, el estandar se
confunde con "no aplica" y nadie lo revisa.

**Error tipico:** escribir "codigo limpio y testeado". No es medible, no se
verifica, y no puede ser un gate.

---

## 4. Reglas de negocio

**Que preguntar:** que afirmaciones del dominio son siempre ciertas, cuales
dependen del momento del negocio, cuales son convenciones del equipo.

**Distincion util:**

| Tipo | Que es | Caduca | Prueba tipica |
|---|---|---|---|
| invariante | siempre verdad | nunca | test unitario de dominio |
| politica | verdad hoy, puede cambiar | cuando el negocio cambia | test parametrizado por fecha |
| convencion | como hacemos las cosas | nunca | lint / convencion de codigo |

**Formato por regla:**

```
REGLA: <afirmacion en presente, una linea>
TIPO: invariante | politica | convencion
PRUEBA: <test o verificacion concreta>
```

**Diseno de la afirmacion:** debe ser **negable**, es decir, poder escribir un
test que falle. "Los totales se calculan con aritmetica decimal" es negable
(un test con 0.1 + 0.2 falla). "Los totales deben ser correctos" no lo es.

**Diseno de la prueba:** debe existir un artefacto, no una intencion. "test de
dominio" no es una prueba; `test_calculo_total_con_redondeo` si.

**Errores tipicos:**

- Regla que describe la implementacion ("el total se guarda en la columna
  `amount_cents`"). Eso es diseno, no regla de negocio, y bloquea refactors.
- Regla sin prueba: se vuelve preferencia y el gate no puede aplicarla.
- Regla duplicada en dos secciones: se contradicen en el futuro y nadie sabe
  cual manda.

---

## 5. Restricciones

**Que preguntar:** cuanto se puede gastar, cuando hay que entregar, cuantos
usuarios, que datos se tocan, que auditorias hacen falta, si hay salida a
internet.

**Formato de fila:**

| Dimension | Limite | Comportamiento al alcanzar el limite | Quien decide |
|---|---|---|---|

**Por que la columna "comportamiento al alcanzar el limite" es obligatoria:**

un tope sin consecuencia es una sugerencia. El comportamiento tipico tiene
tres escalones:

1. **80%**: alerta al responsable.
2. **100%**: el sistema deja de crecer (feature flag apagada, job pausado).
3. **Excepcion**: solo con aprobacion del rol que decide.

**Restricciones tipicas y su unidad obligatoria:**

| Dimension | Unidad | Nota |
|---|---|---|
| Infra cloud | moneda por mes | separar compute, storage y red |
| LLM | tokens por mes | separar entrada y salida si difieren |
| Suscripciones | moneda por mes por herramienta | listar las que ya se pagan |
| Equipo | horas o dias por rol | ver `dev-kit-cost-estimation` |
| Plazo | fecha | naming "primera entrega" |
| Carga | usuarios concurrentes o requests por minuto | definir si pico o promedio |
| Almacenamiento | GB o TB | incluir crecimiento estimado |
| Datos | retencion en dias | por clase de dato |

**Error tipico:** mezclar restricciones de negocio con restricciones tecnicas
en la misma fila. "El sistema debe ser seguro y no pasar de 400 USD" mezcla dos
cosas con unidades distintas y ninguna se puede verificar.

---

## 6. Principios de UX

**Que preguntar:** quien es el usuario, en que contexto usa la herramienta,
cual es la accion principal, que pasa con los datos que ingresa.

**Lista minima de principios (adaptar, no copiar a ciegas):**

| Principio | Significado Practico |
|---|---|
| Accion principal evidente | en pantalla nueva se ve que hacer |
| Estados completos | carga, vacio, error, exito en toda vista asincrona |
| Errores accionables | que paso + que hacer + a donde ir |
| Teclado primero | toda accion principal sin mouse |
| Accesibilidad | contraste, foco visible, labels, roles |
| Sin sorpresas | nada destructivo sin confirmacion |
| Internacionalizable | textos fuera del codigo desde el dia uno |
| Consistencia | el mismo concepto se nombra igual en toda la app |

**Como se escribe:** cada principio con **una consecuencia observable**. "La app
debe ser simple" no dice nada; "en la vista principal hay una sola accion
primaria y no mas de tres secundarias" si.

**Error tipico:** dejar los principios de UX como adjetivos de marketing
("amigable", "moderno"). No son verificables y el agente los interpretara
como quiera.

---

## 7. Prohibiciones

**Que preguntar:** que mistakes ya se cometieron en proyectos anteriores, que
tiene prohibido el compliance, que no se quiere ni discutir.

**Estructura obligatoria de cada fila:**

| Prohibicion | Motivo | Como se detecta |
|---|---|---|

**El motivo importa tanto como la regla.** Sin motivo, el siguiente que llega
no sabe si la prohibicion sigue vigente y la relaja.

**El modo de deteccion define si la prohibicion es real:**

| Modo | Ejemplo | Fortaleza |
|---|---|---|
| Automatizada | scanner de secretos, regla de lint, lockfile en CI | alta |
| Revisión | checklist de review, revision de PR | media |
| Declarada | "no lo hacemos", sin verificacion | nula |

Preferencia: **toda prohibicion con consecuencia fuerte (seguridad, datos,
costo) debe tener deteccion automatizada.**

**Prohibiciones tipicas que conviene listar explicitamente:**

- No loguear datos personales ni sensibles.
- No persistir secretos en el repo ni en la imagen.
- No llamar a servicios de pago o de envio sin aprobacion.
- No agregar dependencias sin version pineada.
- No hacer migraciones destructivas sin plan de rollback.
- No desactivar ni saltear gates de CI.
- No modificar contratos de API sin versionado.
- No hacer push directo a la rama principal.
- No desplegar a produccion sin pasar por el pipeline.

**Error tipico:** una tabla de prohibiciones de 40 filas. Nadie la aplica. Diez
prohibiciones con deteccion automatizada valen mas que cuarenta con texto.

---

## 8. Proceso de cambio

**Que preguntar:** quien puede cambiar la constitucion, como se registra el
cambio, que pasa con el codigo que ya la contradice.

**Reglas minimas:**

1. Un **owner** unico de la constitucion (rol, no persona).
2. Todo cambio es un **amendment numerado** con motivo.
3. El cambio y su codigo consecuencia van en el mismo commit o PR.
4. El codigo existente que contradiga la constitucion se corrige en el mismo
   ciclo; si no se puede, es un debt registrado con fecha.
5. Revision periodica con fecha maxima (por ejemplo cada 4 semanas o al
   cambiar el stack).

**Tabla de amendments:**

| # | Amendment | Fecha | Seccion | Motivo | Estado |
|---|---|---|---|---|---|

---

## Apendice: decisiones abiertas

Las decisiones que no se pudieron cerrar no se esconden: se listan con
**responsable, fecha limite e impacto**. Una decision abierta sin responsable
es una decision que nadie va a tomar.

| # | Decision pendiente | Responsable | Fecha limite | Impacto si no se decide |
|---|---|---|---|---|

---

## Checklist de revision de la constitution

Antes de dar por cerrada la fase 1, verificar:

- [ ] Las 8 secciones estan presentes y en orden.
- [ ] El stack esta cerrado por capa, con condicion de desviacion.
- [ ] Los servicios con costo variable tienen fila propia y condicion de corte.
- [ ] Cada estandar de calidad tiene comando o artefacto que lo verifica.
- [ ] Cada regla de negocio tiene tipo y prueba.
- [ ] Cada restriccion tiene unidad, comportamiento al limite y quien decide.
- [ ] Cada principio de UX tiene una consecuencia observable.
- [ ] Cada prohibicion tiene motivo y modo de deteccion.
- [ ] Hay owner y fecha de revision.
- [ ] Las decisiones abiertas tienen responsable y fecha.
- [ ] Ningun `PENDIENTE` sin dueno.
