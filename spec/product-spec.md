# Product Spec - Dev Agent Kit

> Que es este producto, para quien es, que entrega y como crece.
> Especificado con la propia metodologia que el kit teach (dogfooding).

## 1. Resumen ejecutivo

**Dev Agent Kit** es un producto que se instala en la maquina de un cliente y
le entrega a su equipo de agentes de IA el conocimiento procedural que hace que
trabajen como un equipo senior: una metodologia de desarrollo con gates, un
roster de agentes con limites de responsabilidad, y estandares de ingenieria
verificables.

**El problema que resuelve:** un equipo que usa agentes sin metodologia produce
mucho codigo que no se puede mantener. Un equipo con metodologia y gates
produce software que se sostiene. El kit es la metodologia, codificada.

**La tesis:** el valor esta en el conocimiento destilado, no en el codigo. Por
eso el kit es skills (portables, versionables, auditables) y no una plataforma
plataforma (lock-in, mantenimiento, imposible de escalar).

## 2. Para quien es

| Perfil | Que necesita | Que gana |
|---|---|---|
| Equipe de desarrollo que incorpora agentes | Un proceso que no dependa de que alguien se acuerde | Codigo mantenible, gates que no se saltan |
| Consultor /(provider) que entrega IA aplicada | Un activo reutilizable entre clientes | No reconstruir el conocimiento en cada proyecto |
| Lider tecnico que evalua IA | Criterio objetivo, no demo | Saber si la IA entrega o solo genera volumen |

**No es para:** quien busca un producto cerrado sin instalar nada, ni quien
quiere un generador de codigo autoconfigurable.

## 3. Que entrega

### 3.1 Dos repos

| Repo | Contenido | Rol |
|---|---|---|
| `dev-agent-skills` | La biblioteca de skills + la spec del producto | El activo vendible |
| `dev-agent-kit` | Instalador, scanner de genericidad, smoke test, manifest | El harness que hace verificable la promesa |

La separacion no es estetica: las skills son lo que el cliente lee y lo que
cambia seguido. El harness es lo que el cliente ejecuta una vez.

### 3.2 Una skill

Una unidad de conocimiento procedural con:
- trigger explicito (cuando cargarla)
- workflow con pasos y artefacto por paso
- gates verificables
- anti-patrones con razon
- cero datos de cliente

### 3.3 Perfiles de instalacion

`minimal` (8) · `standard` (21) · `full` (24). Un perfil es un conjunto de
skills. El cliente elige el alcance; el harness instala solo eso.

## 4. El loop de aprendizaje (core del producto)

Esta es la parte que convierte el kit de un catalogo en un producto vivo.

```
PROYECTO                 el cliente usa el kit en un proyecto real
   |
   v
HUELLA                  que skills se cargaron, que gates fallaron,
   |                    que patrones se encontraron, que falto
   v
DESTILACION             un proceso convierte la huella en candidatos
   |                    (skill nueva | patch a skill | entrada al backlog)
   v
PROMOCION               el candidato se valida (scanner + revision) y
   |                    se promotes a skill en dev-agent-skills
   v
KIT MAS FUERTE           la proxima instalacion arranca con mas cobertura
   |
   +------> vuelve al proyecto (feedback loop)
```

### 4.1 Que es una huella

La huella se captura durante el trabajo, no despues. Cuatro fuentes:

| Fuente | Que captura |
|---|---|
| Skills cargadas | Que habilidades se invocaron y cuantas veces |
| Gates fallidos | Donde se traba el proceso: el gap mas valioso del kit |
| Decisiones tomadas | Que se decidio y por que: el criterio que se perdio |
| Desviaciones | Donde el kit no se ajusto a la realidad: el error del kit |

La cuarta es la mas importante y la mas incomoda: un kit que nunca se corrige
es un kit que no se uso.

### 4.2 Las tres salidas de la destilacion

Una huella produce exactamente una de tres cosas:

1. **Skill nueva** — el patron es reusable y no tiene hogar.
2. **Patch a skill existente** — el patron contradice o amplia una skill.
3. **Entrada al backlog** — el patron es util pero todavia no es generalizable.

Y una cuarta que NO es una salida valida:

4. **Descartar** — la huella es especifica del cliente y no se puede destilar.
   Se registra el descarte (con su motivo) y no su contenido.

**Regla:** una huella que no se puede destilar NO se archiva con su contenido.
Se archiva el aprendizaje ("aca hay que preguntar el alcance") sin el dato.
Esto es lo que mantiene la genericidad garantizada, no solo verificada.

### 4.3 Donde vive el backlog

`dev-agent-skills/knowledge/registry.yaml` — el registro vivo:

- que skills existen y su estado (activa, candidata, deprecada)
- que ideas esperan destilacion y de donde vinieron
- que gaps se detectaron y si ya se cubrieron
- la fecha de la ultima revision

Es un archivo de texto, versionado, revisable. No una base de datos: tiene que
poder leerlo un humano en un `cat`.

### 4.4 El ciclo de una idea

```
idea (backlog)
  -> candidata: hay patron suficiente para escribirla?
  -> borrador: skill escrita + scanner limpio + revision
  -> activa: instalada y usada en al menos un proyecto real
  -> consolidada: usada en 2+ proyectos, entra al perfil standard
```

Una skill no entra al perfil `standard` hasta que se uso en dos proyectos
distintos. Ese es el filtro de calidad: una skill que solo funciono en un
contexto es una skill de ese contexto.

## 5. Criterios de exito del producto

| Criterio | Como se mide |
|---|---|
| Genericidad | `scan_clean.py --strict` en CI: 0 hallazgos |
| Instalabilidad | `smoke_test.sh` verde en una maquina vacia |
| Carga | toda skill del kit carga y su `name` coincide con su directorio |
| Cobertura | cada proyecto real deja al menos una huella destilada |
| Consolidacion | las skills del perfil `standard` se usaron en 2+ proyectos |

## 6. Fuera de alcance (v1)

- Editor grafico o dashboard.
- Marketplace de skills de terceros.
- Ejecucion autonoma de tareas (el kit no implementa: orquesta y verifica).
- Multi-tenancy del propio kit (un cliente, una instalacion).
- Soporte para runtimes que no lean el formato de skill.

## 7. Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| La genericidad erosiona con el uso | Se filtran datos de cliente | Scanner en CI + la regla de "descartar con motivo" |
| El kit crece sin filtro | 200 skills y nadie sabe cual usar | Perfiles + registro con estado + consolidacion a 2+ proyectos |
| Una skill contradice a otra | El agente elige mal | Revisar `related_skills` + gate de coherencia en el registro |
| El producto se usa pero no se realimenta | Se estanca en la v1 | La huella se captura durante el trabajo, no despues |
| Se confunde con un framework | Expectativas incorrectas | La spec dice explicitamente que no es plataforma |

## 8. Preguntas abiertas

- El perfil `standard` incluye las verticales (`rag`, `browser`) o quedan en
  `full` para el cliente que ya tiene esas capacidades.
- El registro (`knowledge/registry.yaml`) se mantiene a mano o un script
  propone los cambios desde las huellas.
- Si el kit se ofrece con instalacion hecha por el proveedor o self-serve.
