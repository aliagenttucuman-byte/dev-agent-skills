# Checklist de implementacion

> Fase 8 del flujo SDD. Todos los items deben estar en verde antes de
> escribir la primera linea de codigo. Un item sin verificar es un item sin
> verificar.

## Artefactos

- [ ] `CONSTITUTION.md` existe y no tiene secciones pendientes
- [ ] `specs/openapi.yaml` valida sin errores
- [ ] `specs/user-stories.md` tiene todas las historias con criterios
- [ ] `specs/data-model.md` cubre las entidades del spec
- [ ] Seccion de clarificaciones completa, sin preguntas abiertas
- [ ] `PLAN.md` existe y mapea todas las historias
- [ ] `ESTIMACION.md` existe con los 3 escenarios y la decision registrada
- [ ] `REPORT-GAPS.md` no tiene gaps bloqueantes
- [ ] `TASKS.md` tiene tareas con responsable, dependencias y criterio
- [ ] `CHECKLIST.md` (este archivo) completo

## Coherencia

- [ ] Cada historia del spec tiene al menos una tarea que la implementa
- [ ] Cada endpoint del OpenAPI esta mapeado a una tarea
- [ ] Cada componente del plan tiene origen justificado (no hay over-engineering)
- [ ] El modelo de datos soporta todas las entidades del spec
- [ ] La estimacion cubre todas las tareas

## Contrato

- [ ] Los contratos de API estan cerrados (permite paralelismo backend/frontend)
- [ ] Los codigos de error estan definidos en el contrato
- [ ] Los datos vacios y los limites estan especificados

## Entorno

- [ ] El entorno de desarrollo levanta desde cero
- [ ] El smoke test del proyecto pasa
- [ ] Los comandos de install, build, test y lint estan documentados
- [ ] Las variables de entorno estan declaradas con ejemplo (`.env.example`)

## Calidad

- [ ] Linter configurado y pasa
- [ ] Formateador configurado
- [ ] Chequeo de tipos configurado y pasa
- [ ] Cobertura minima definida en la configuracion
- [ ] Hooks de pre-commit activos

## Seguridad

- [ ] Los secretos estan fuera del repositorio (`.env` ignorado, `.env.example` versionado)
- [ ] `.gitignore` cubre lo sensible
- [ ] La autenticacion y la autorizacion estan definidas donde aplican
- [ ] Los inputs externos se validan

## Verificacion

- [ ] Cada criterio de aceptacion tiene un test o una verificacion asignada
- [ ] Los tests criticos (paths de error) estan cubiertos
- [ ] Hay un test de humo que levanta el proyecto

## Criterios de detencion

Detener la implementacion y volver a la fase indicada si:

- [ ] Aparece un requisito que el spec no cubre -> volver a la fase 2
- [ ] El plan no sirve para la historia -> volver a la fase 4
- [ ] El costo real excede la estimacion -> volver a la fase 5
- [ ] El contrato de API resulta insuficiente -> volver a la fase 4

---

**Resultado:** todos los items en verde. Si alguno no, se vuelve a la fase que
corresponde. No se empieza a implementar con items abiertos.

Fecha: ______
Responsable: ______
