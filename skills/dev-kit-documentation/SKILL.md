---
name: dev-kit-documentation
description: "README efectivo, ADRs con ciclo de vida, documentacion viva generada por scripts, changelog y upkeep de la documentacion. CARGAR cuando hay que escribir o actualizar la documentacion de un proyecto, registrar una decision de arquitectura o decidir que se documenta y que no."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [documentation, readme, adr, changelog, api-docs]
    category: software-development
    related_skills: [dev-kit-spec-authoring, dev-kit-task-breakdown, dev-kit-project-bootstrap, dev-kit-ci-cd]
---

# Dev Kit - Documentacion

> **Trigger:** "documentar el proyecto", "escribir el README", "registrar esta
> decision", "la documentacion esta desactualizada", "que hay que documentar".
> Cargar esta skill ANTES de escribir documentacion a mano.

## Que es esto

El procedimiento para producir documentacion que **se mantiene sola**: cada
documento tiene un autor claro, una fuente de verdad y una regla de upkeep.

No es escribir prosa. Es decidir que sobrevive cuando el proyecto cambie.

La regla que lo gobierna:

> **Documento que no se regenera, se pudre. Documento que no tiene dueno, se
> contradice.** Lo que no se puede regenerar con un comando tiene que tener un
> dueno humano y una fecha de revision.

## Los cuatro tipos de documento

| Documento | Que es | Fuente de verdad | Se regenera | Dueno |
|---|---|---|---|---|
| **README** | como arrancar, usar y desplegar | el codigo y los comandos | parcialmente | redactor de documentacion |
| **ADR** | una decision de arquitectura y su porque | el archivo ADR | no | arquitecto |
| **Viva** | referencia de API, cobertura, diagramas | el codigo | si, con scripts | generacion automatica |
| **Changelog** | que cambio en cada version | los commits con etiqueta | si, con scripts | devops |

**Regla:** el README, el ADR y el changelog se escriben a mano. Todo lo demas se
genera. Un documento generado que se edita a mano vuelve a mentir en la
siguiente regeneracion.

## 1. El README efectivo

Un README es el manual de operacion de quien llega sin contexto. Se lee en
tres minutos y responde cuatro preguntas.

| Pregunta | Seccion | Si falta |
|---|---|---|
| Que es esto y para que sirve | Proposito | nadie sabe si le sirve |
| Como lo arranco | Instalacion | el primer comando falla y se va |
| Como lo uso | Uso rapido | no hay ejemplo ejecutable |
| Como lo pruebo y lo despliego | Comandos y despliegue | nadie puede verificar nada |

### Secciones minimas

| # | Seccion | Contenido | Error tipico |
|---|---|---|---|
| 1 | Proposito | una frase con el problema que resuelve | historia del proyecto en vez de su proposito |
| 2 | Estado | en que fase esta y que falta | presentarlo como terminado |
| 3 | Requisitos | versiones minimas de runtime y herramientas | "instala Python" |
| 4 | Instalacion | comandos copy-pasteables, en orden | pasos que asumen un entorno |
| 5 | Uso rapido | el ejemplo mas pequeno que produce un resultado | comandos sin resultado visible |
| 6 | Configuracion | tabla de variables, con default y obligatorio | secretos escritos en el ejemplo |
| 7 | Comandos | tabla de test, lint, tipos, build, migrate | comandos sin saber que verifican |
| 8 | Estructura | arbol breve con el rol de cada carpeta | arbol completo de 40 lineas |
| 9 | API | enlace al doc generado, no una copia | contrato copiado a mano |
| 10 | Despliegue | como se publica y como se revierte | solo el camino feliz |
| 11 | Tests | como se corren y donde estan | nada o "usa pytest" |
| 12 | Licencia | tipo de licencia | ausente |

### Reglas de redaccion

| Regla | Motivo |
|---|---|
| Todo comando es copy-pasteable y corre desde la raiz | un comando con ruta rara no se copia |
| Todo ejemplo tiene resultado visible | sin salida, el lector no sabe si funciono |
| Todo secret aparece como variable, nunca como valor | el README se versiona y se difunde |
| Los enlaces internos usan rutas relativas | funcionan en el repo y en el visor |
| El arbol muestra 2 niveles, no 4 | el detalle se descubre con `ls` |

## 2. ADRs: cuando se escribe uno

Un ADR (Architecture Decision Record) registra **una decision con alternativas
razonables y consecuencias**. No es un acta de reunion ni un tutorial.

### Cuando SI escribir un ADR

| Situacion | Por que es una decision |
|---|---|
| Se elige una libreria o un framework | hay alternativas y cambiar despues es caro |
| Se elige un modelo de datos o esquema | define la forma de la informacion |
| Se define un contrato de API publico | otras capas dependeran de esa forma |
| Se elige un patron arquitectonico | estructura todo lo que viene despues |
| Se descarta una alternativa que se replanteara | el porque es lo que se pierde |
| Se cambia una decision previa | el registro historico es el valor |
| Se elige modelo de despliegue o infraestructura | define costo y operacion |
| Se decide que NO se va a hacer algo | la decision negativa tambien se toma |

### Cuando NO escribir un ADR

| Situacion | Donde va en su lugar |
|---|---|
| El nombre de una funcion o clase | el codigo y su docstring |
| Un detalle de implementacion reversible | el commit |
| Un bugfix | el changelog |
| El detalle de una funcion publica | el docstring o el doc generado |
| Una preferencia de estilo | la guia de estilo del linter |
| Una regla ya escrita en la constitucion | la constitucion |

**Regla de tamano:** un ADR cabe en una pagina. Si pasa de dos, se mezclaron dos
decisiones: se separan.

### Ciclo de vida

```
PROPUESTO  ->  ACEPTADO  ->  (SUPERADO POR ADR-XXXX)
                    |
                    +----->  RECHAZADO
```

| Estado | Significado | Se edita el cuerpo |
|---|---|---|
| Propuesto | esta en discusion, no aplica | si |
| Aceptado | es la decision vigente | no: se corrige con un ADR nuevo |
| Rechazado | se considero y no se adopto | no |
| Superado por | otra decision la reemplaza | no |

**Regla:** un ADR aceptado **no se reescribe**. Se marca como superado y se
escribe el nuevo. Si se edita el cuerpo, se pierde el criterio que sirvio para
decidir, que es justo el motivo del ADR.

Plantilla: `templates/adr.md`. Criterios detallados: `references/adr-criterios.md`.

### Ubicacion e indice

| Regla | Valor |
|---|---|
| Ubicacion | `docs/adr/` |
| Nombre | `NNNN-titulo-en-kebab-case.md` |
| Numeracion | correlativa, sin reutilizar numeros |
| Indice | `docs/adr/README.md` con estado y titulo de cada ADR |

```markdown
| # | Titulo | Estado | Fecha |
|---|---|---|---|
| 0001 | Arquitectura por capas | Aceptado | 2026-01-15 |
| 0002 | Migraciones con Alembic | Aceptado | 2026-02-03 |
| 0003 | Versionado de la API por path | Rechazado | 2026-02-20 |
```

## 3. Documentacion viva

La documentacion viva se genera desde el codigo con un comando. Si el comando
no existe, se desactualiza en semanas.

| Documento | Se genera con | Gate |
|---|---|---|
| Referencia de la API | introspeccion del servidor al arrancar | el JSON generado se versiona y se compara en CI |
| Esquema de la base de datos | migracion aplicada mas introspeccion | la migracion coincide con el modelo |
| Diagramas de arquitectura | analisis estatico de imports | el diagrama regenerado no tiene diferencias sin commitear |
| Metricas de cobertura | `pytest --cov` | umbral minimo definido |
| Tabla de variables de entorno | el modulo de configuracion | toda variable del `.env.example` esta usada |

### Regla del artefacto generado

1. El generador es un **script versionado**, no un comando manual.
2. El comando esta en el README, con la salida exacta.
3. El resultado se versiona (para diffear) o se ignora por completo. Nunca a medias.
4. El CI regenera y falla si hay diferencias sin commitear.

```bash
make docs && git diff --exit-code docs/ || {
  echo "documentacion generada desactualizada: corra 'make docs' y commitee"; exit 1; }
```

**Regla:** si el documento generado esta desactualizado, el fallo lo tiene el
documento, no la persona que commitea. Por eso lo detecta el CI y no la
revision a ojo.

## 4. Changelog

El changelog responde: que cambio, desde cuando, y como migrar.

```markdown
# Changelog

Formato basado en Keep a Changelog. Versionado semantico.

## [No publicado]

## [1.2.0] - 2026-03-10

### Agregado
- Endpoint de exportacion de pedidos en formato CSV.

### Cambiado
- El parametro `estado` de listar pedidos acepta multiples valores.

### Eliminado
- El endpoint v1 de clientes. Migrar a `/api/v2/clientes`.

### Corregido
- El total de un pedido con descuento ya no se redondea al alza.
```

| Regla | Motivo |
|---|---|
| Se escribe desde los commits con etiqueta, no a mano | la version manual se desincroniza |
| Una version por release, con su fecha | es un registro historico |
| Secciones Agregado / Cambiado / Eliminado / Corregido / Seguridad | el lector busca por tipo de impacto |
| Se anota el impacto de la migracion | el lector necesita saber si le rompe algo |
| `No publicado` acumula lo pendiente | el proximo release arranca de ahi |
| Los cambios de seguridad se marcan explicitamente | el lector decide si actualiza ya |

El generador mapea los prefijos `feat:`, `fix:` y `BREAKING CHANGE:` a las
secciones. El mapeo esta documentado en el script para que el equipo sepa que
escribir.

## 5. Documentacion de la API

| Nivel | Que es | Como se mantiene |
|---|---|---|
| **Referencia** | todos los endpoints, parametros, respuestas, errores | generado por introspeccion del framework |
| **Guia** | los flujos principales con request y response | escrita a mano, un ejemplo minimo por flujo |
| **Contrato** | el esquema formal que ambos lados firman | el archivo OpenAPI, versionado, revisado |

- La referencia **nunca** se edita a mano: se regenera.
- La guia usa el mismo ejemplo que el test de integracion, para que no diverjan.
- El contrato se versiona; un cambio incompatible es un cambio mayor y necesita
  su nota de migracion en el changelog.
- Todo endpoint que devuelve error documenta el codigo, el cuerpo de la
  respuesta y cuando ocurre.

## 6. Reglas de upkeep

Cada documento tiene un dueno y una cadencia. Sin eso, la documentacion
envejece por omision.

| Documento | Dueno | Cadencia | Se actualiza cuando |
|---|---|---|---|
| README | redactor de documentacion | por release | cambia un comando, una variable o el flujo de uso |
| ADR | arquitecto | por decision | se toma, se revisa o se supera una decision |
| Referencia de API | generacion automatica | por commit | cambia el contrato |
| Guia de la API | backend senior | por trimestre | cambia un flujo principal |
| Changelog | devops | por release | se corta una version |
| Runbook | devops | por trimestre | cambia el procedimiento de operacion |
| Guia de contribucion | redactor de documentacion | por trimestre | cambia el flujo de trabajo |

### El runbook

Un runbook responde "que hago cuando esto se rompe". Para cada alerta
importante: sintoma (como se detecta), diagnostico (comandos para confirmar la
causa), mitigacion (accion inmediata para restaurar el servicio), causa raiz
(por que paso, cuando se corrige) y escalamiento (a quien y en que momento).

**Regla:** un runbook sin comandos verificables es un texto. Con comandos, es una
operacion.

## 7. Cuando NO escribir documentacion

| Situacion | Que hacer en su lugar |
|---|---|
| El codigo es autoexplicativo y sin comportamiento sorprendente | un buen nombre y un test |
| Es una decision reversible en menos de un dia | un commit con buen mensaje |
| El dato ya existe generado en otro lado | un enlace |
| Es informacion de una sola persona, de una sola vez | un mensaje, no un archivo |
| Es del dominio del cliente y no del software | el backlog del cliente |
| El codigo va a cambiar la semana que viene | esperar a que se estabilice |

### La prueba de las dos preguntas

1. **¿Alguien va a leer esto buscando algo concreto?** Si no, es un archivo.
2. **¿Que pasa si este documento no existe?** Si la respuesta es "nada", no hace
   falta. Si es "nadie puede arrancar el proyecto", hace falta.

**Regla de obsolescencia:** un documento que se puede generar con un comando
**se genera**. La unica excepcion es la narrativa del porque: esa no se puede
generar y por eso vive en un ADR.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| README como folleto de la empresa | nadie lo lee para arrancar el proyecto | responder las cuatro preguntas |
| Documentar el codigo linea por linea | duplica lo que el codigo ya dice | documentar el porque y el contrato |
| Editar a mano un documento generado | la siguiente regeneracion pisa el cambio | generar con comando y versionar el script |
| ADR que reescribe la historia | se pierde el criterio que sirvio para decidir | marcar el anterior como superado |
| ADR de cosas triviales | el directorio de ADRs se llena de ruido | ADR solo con alternativas reales |
| Changelog escrito a mano | se desincroniza de los commits | generarlo desde las etiquetas |
| Documentacion sin dueno | nadie se hace cargo de actualizarla | dueno y cadencia por documento |
| Un documento por cada duda | proliferacion sin indice | un solo lugar, con indice |
| Guardar decisiones en el chat | se pierden, no se buscan | ADR o seccion del plan |
| Enlace a un documento que no existe | el peor tipo de doc: promete y no cumple | crear el archivo o quitar el enlace |
| Documentar el futuro | el alcance cambia y el documento miente | el backlog guarda el futuro |
| Sin comando de verificacion | el documento envejece sin avisar | gate en CI que regenere y compare |

## Referencias

### Skills relacionadas

- `dev-kit-spec-authoring` - define el contrato OpenAPI que se documenta.
- `dev-kit-task-breakdown` - genera el entregable que hay que documentar.
- `dev-kit-project-bootstrap` - genera el proyecto base con su README inicial.
- `dev-kit-ci-cd` - donde vive el gate que regenera y compara la documentacion.

### Archivos de esta skill

| Archivo | Contenido |
|---|---|
| `templates/readme.md` | esqueleto de README con las doce secciones minimas |
| `templates/adr.md` | formato de ADR con ciclo de vida y alternativas |
| `references/adr-criterios.md` | criterios de redaccion, ciclo de vida y casos borde |