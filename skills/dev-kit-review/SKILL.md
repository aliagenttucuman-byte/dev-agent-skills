---
name: dev-kit-review
description: "Code review con checklist por tipo de cambio, severidad explicita y formato de comentario. CARGAR al revisar un pull request, antes de merge, o cuando hay que decidir si algo esta listo para publicar."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [review, code-quality, pull-request, merge]
    category: software-development
    related_skills: [dev-kit-code-quality, dev-kit-testing, dev-kit-security, dev-kit-sdd-workflow]
---

# Dev Kit - Code Review

> **Trigger:** "revisar esto", "esta listo para merge", "dame feedback del PR",
> "que le falta a este cambio". Cargar cuando hay un cambio propuesto y hay que
> decidir si pasa.

## Que es esto

Un proceso de revision que produce un resultado accionable: o el cambio pasa,
o tiene bloqueantes concretos con como resolverlos.

No es buscarle el pelo al gato. Una review que no encuentra nada en un cambio
grande es una review que no se leyo.

## La regla que gobierna todo

> **Una review sin severidad es una opinion. Una review sin criterio de
> aceptacion es una discusion.**

Cada comentario dice: que esta mal, por que importa, y que hacer.

## Severidad

| Severidad | Que significa | Bloquea merge |
|---|---|---|
| **Bloqueante** | El cambio no cumple un criterio de aceptacion, rompe algo existente, o tiene un riesgo de seguridad o datos | Si |
| **Importante** | Funciona pero de forma fragil, inmantenible o con performance que va a doler | No, pero se deja comentario explicito |
| **Sugerencia** | Hay una forma mejor, no un error | No |

**Regla:** no inflar la severidad. Si todo es bloqueante, la review pierde
autoridad y el equipo deja de leerla. Si todo es sugerencia, la review no
cumple su funcion.

## Que revisar segun el tipo de cambio

No se revisa todo igual. Un cambio de documentacion no necesita la misma
atenion que uno de migracion de base de datos.

| Tipo de cambio | Revisar ademas | Que se suele escapar |
|---|---|---|
| **Logica de negocio** | Criterios de aceptacion cubiertos por tests | La logica de un caso borde que el spec no menciona |
| **API / contrato** | Compatibilidad hacia atras, codigos de error, paginacion | Romper un campo que alguien mas consume |
| **Base de datos / migracion** | Lock, tiempo de bloqueo, rollback, indices | La migracion sin rollback, o el lock en tabla grande |
| **Seguridad** | Validacion de input, autorizacion, secretos | Autorizacion que falta en un endpoint nuevo |
| **Infra / CI** | Secretos, permisos, costo de recursos | Un secreto en el YAML del pipeline |
| **Performance** | Consulta a base de datos, indices, cache | El N+1 en una lista paginada |
| **Refactor** | Comportamiento identico, tests siguen verdes | El refactor que cambia un comportamiento "de paso" |
| **UI** | Accesibilidad, estados vacios y de error | El estado de carga que nunca se vio porque hay datos de prueba |
| **Documentacion** | Que el doc coincide con el codigo | El ejemplo del README que ya no funciona |

## Checklist general

### Correctitud
- [ ] La logica hace lo que dice el criterio de aceptacion
- [ ] Los casos borde estan manejados (vacio, null, maximo, concurrencia)
- [ ] Los errores se propagan con contexto, no se silencian
- [ ] No hay supresiones de tipo sin justificacion

### Tests
- [ ] Cada criterio de aceptacion del cambio tiene cobertura
- [ ] Los tests fallan si el codigo se rompe (verificar que no son triviales)
- [ ] No hay tests deshabilitados con `skip` sin motivo
- [ ] Los tests no dependen del orden de ejecucion

### Diseño
- [ ] El cambio esta en el lugar correcto del codigo
- [ ] No se duplica logica que ya existe
- [ ] Los nombres dicen lo que el codigo hace
- [ ] Las funciones publicas estan tipadas

### Seguridad
- [ ] Ningun secreto en el codigo ni en la configuracion
- [ ] Los inputs externos se validan
- [ ] La autorizacion aplica a todos los endpoints tocados
- [ ] No se loguean datos sensibles

### Operacion
- [ ] Los logs tienen contexto suficiente para diagnosticar
- [ ] Los errores nuevos tienen un mensaje accionable
- [ ] La observabilidad cubre el camino nuevo si aplica

### Alcance
- [ ] El cambio no hace mas de lo que dice el ticket
- [ ] No hay cambios de formato mezclados con cambios de logica
- [ ] No hay archivos generados que no deberian versionarse

## Formato del comentario

```markdown
**[Bloqueante] El timeout no aplica al endpoint de exportacion**

El timeout configurado es de 30s, pero el export genera un archivo que puede
tardar varios minutos. Con el timeout actual el cliente recibe un 504 y el
proceso sigue corriendo en el servidor.

Impacto: en datos de volumen alto, el export falla de forma consistente.

Sugerencia: separar el timeout de la request del timeout del job, o mover el
export a un proceso asincrono con polling de estado.

Ref: `handlers/export.py:142`
```

**Partes obligatorias:**
1. Severidad (marcada).
2. Que esta mal (con referencia al archivo y linea).
3. Por que importa (el impacto concreto).
4. Que hacer (una via de resolucion, no cinco).

**Lo que no es un buen comentario:**
- "esto no me gusta"
- "refactorizar esto"
- "usar el helper de X" sin decir por que importa
- Errores de ortografia o formato (van como sugerencia o comentario
  separado, nunca mezclados con el contenido)

## Que bloquea merge y que no

| Bloquea | No bloquea |
|---|---|
| Criterio de aceptacion sin cubrir | Sugerencia de estilo |
| Error de logica | Nombres de variables preferences |
| Vulnerabilidad de seguridad | Refactor opcional |
| Migracion sin rollback | Mejora de performance marginal |
| Test deshabilitado | Comentario de documentacion |
| Secret en el codigo | Reordenamiento de imports |
| Contrato de API incompatible | |

## Tiempo maximo de respuesta

| Tipo de cambio | Primer turnaround | Recordatorio si no hay respuesta |
|---|---|---|
| Fix pequeno | 4 horas habiles | 24 horas |
| Feature / refactor | 1 dia habil | 2 dias |
| Cambio de infra o migracion | 2 dias habiles | 3 dias |

**Regla:** si la review no se puede hacer en el tiempo previsto, se dice
explicitamente y se propone un revisor alternativo. El silencio bloquea el
equipo tanto como una review mala.

## Anti-patrones

| Anti-patron | Por que falla |
|---|---|
| Aprobar sin leer | Aprobar sin leer es dejar el costo para despues |
| Revision cosmetica | Detalle de formato tapa un problema de fondo |
| Inflar severidad | Si todo es bloqueante, nadie lo distingue |
| Pedir un refactor completo en un PR de 5 lineas | El cambio chico se diluye y se pierde |
| Sin criterio de aceptacion a la vista | No se puede determinar si el cambio cumple |
| Dejar el PR sin revisar | El costo del silencio es del equipo, no del autor |
| Comentar en la linea equivocada | El comentario se pierde en el scroll |

## Referencias

- `templates/review-checklist.md` - checklist imprimible por tipo de cambio
- `references/por-tipo-de-cambio.md` - que mirar en cada tipo de cambio, con el error tipico
