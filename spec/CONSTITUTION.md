# CONSTITUTION - Dev Agent Kit

> Principios no negociables del producto. Una skill o un script que los
> contradiga no entra al repo, o entra accompanied de una amendment explicita.

## 1. Principio rector

> **Ejecutado no es entregado. Entregado no es verificado.**

Cada fase del flujo produce un artefacto. El avance se justifica con el
artefacto, no con la sensacion de avance.

## 2. Genericidad absoluta

**Regla:** ninguna skill contiene nombres de personas, marcas, corporaciones,
clientes, repos privados, IDs de proyectos ni rutas de maquinas concretas.

**Verificacion:** `scan_clean.py` corre en CI y falla el build. Las reglas
publicas viven en un solo archivo (`scripts/forbidden_terms.py`) para que sean
auditable y extensible.

**Sobre la denylist:** el repo publico NO puede contener la lista de terminos
prohibidos: seria tan sensible como los terminos que prohibe. Por eso:

- El repo publica **reglas estructurales** que detectan la clase de
  contaminacion sin nombrar a nadie (rutas de maquina, dominios de cliente).
- Los terminos concretos viven en una **denylist privada** en
  `~/.config/dev-agent-kit/denylist.local.json`, que no se versiona nunca.
- Cuando el scanner detecta uno, lo reporta por **hash**, no por nombre: el log
  de CI es publico. Con `--private-labels` se ve el nombre real, para uso
  local.

La consecuencia practica: el repo se puede publicar y auditar sin filtrar
nada, y la deteccion sigue siendo completa.

**Por que:** el valor del kit es el conocimiento destilado. Un dato de cliente
en una skill no agrega valor: agrega riesgo de fuga y vuelve el kit
imposible de vender.

## 3. Conocimiento, no codigo de aplicacion

**Regla:** el kit entrega skills, templates y verificadores. No entrega
aplicaciones que haya que mantener.

**Excepcion:** un script ejecutable es aceptable cuando su unica funcion es
*verificar* (scanner, auditor, validador de contrato). Un script que
implementa logica de negocio no.

## 4. Roles genericos, siempre

**Regla:** cuando el kit habla de quien hace una tarea, usa el rol
(`arquitecto`, `backend senior`, `qa`, `devops`, `orquestador`). Nunca un
nombre propio.

**Por que:** un cliente puede mapear los roles a su propia estructura. Un
nombre propio rompe ese mapeo y filtra identidad.

## 5. Stack por defecto, no stack impuesto

**Regla:** el kit declara un stack por defecto (Python/FastAPI + React/
TypeScript + PostgreSQL + Docker) y documenta como desviarse de el.

**Por que:** la opinion del equipo es un default razonable, no una dogma. Un
kit que exige un stack no se puede aplicar a una base de codigo existente.

## 6. Cada skill es autocontenida

**Regla:** una skill se entiende y se aplica leyendo solo esa skill. Si
depende de otra para funcionar, lo declara en `related_skills` y explica en
una linea que aporta.

**Por que:** el loader carga una skill a la vez. Una skill que exige leer
otras tres para empezar no se usa.

## 7. Los gates son gates

**Regla:** un gate que se puede saltar no es un gate. Cada skill define su
gate en terminos verificables, con el comando o el artefacto que lo prueba.

**Por que:** un gate decorativo genera la sensacion de rigor sin el rigor. Es
peor que no tener gate.

## 8. Idioma

**Regla:** espanol tecnico. Los nombres de herramientas, comandos, flags,
clases y funciones van en su forma original en ingles.

**Por que:** el equipo es hispanohablante y el codigo ya es inglés. Traducir la
prosa es lo que hace el kit usable.

## 9. Versionado semantico por skill

**Regla:** `version` en el frontmatter. Minor cuando se agrega contenido, major
cuando cambia un contrato de uso. Un cambio de workflow es major.

## 10. Una skill, un tema

**Regla:** si una skill tiene tres trigger classes distintos, son tres skills.

**Por que:** el matching por trigger se rompe cuando una skill cubre todo. La
precision del routing depende de que cada skill responda a una pregunta.

---

## Stack por defecto

| Capa | Default | Desviacion documentada en |
|---|---|---|
| Backend | Python 3.12 + FastAPI + SQLAlchemy + Pydantic | `dev-kit-backend-stack` |
| Frontend | React 18 + TypeScript + Vite | `dev-kit-frontend-stack` |
| Datos | PostgreSQL 16 + Alembic | `dev-kit-database` |
| Contenedores | Docker + Compose | `dev-kit-ci-cd` |
| CI | GitHub Actions | `dev-kit-ci-cd` |
| Lint / types | ruff + mypy + pyright | `dev-kit-code-quality` |
| Tests | pytest + Playwright | `dev-kit-testing` |
| Orquestacion | runtime de agentes con skills | `dev-kit-orchestrator` |

---

## Lo que este producto NO es

- No es un framework cerrado con licencia proprietary.
- No es un gestor de proyectos.
- No es un servicio de IA.
- No requiere una plataforma especifica: funciona sobre cualquier runtime que
  lea el formato de skill.

---

## Amendments

Toda excepcion a estos principios se registra aca con: fecha, principio
afectado, razon, y alcance. Sin amendment, no hay excepcion.
