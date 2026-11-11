# Promocion entre ambientes y rollback

Referencia de `dev-kit-ci-cd`. Como pasa un cambio de dev a produccion, y como
se vuelve atras.

---

## La cadena de promocion

```
PR  ->  CI (calidad + seguridad + build)  ->  staging  ->  produccion
         ^                                      |             |
         |                                      v             v
      rollback <--------------------------  rollback <---  rollback
```

**Regla:** el mismo artefacto que se probó en staging es el que se despliega
en produccion. Si se reconstruye, se esta probando otra cosa.

Por eso el CI construye la imagen una vez, la guarda como artefacto, y el
deploy la promote. No se vuelve a construir.

---

## Los ambientes

| Ambiente | Proposito | Quien lo ve | Datos |
|---|---|---|---|
| **dev** | Desarrollo local y Pull Requests | El equipo | Sinteticos o anonimizados |
| **staging** | Verificacion pre-produccion | El equipo y quien valida | Copia anonimizada de produccion |
| **produccion** | Usuarios reales | Los usuarios | Reales |

**Regla:** staging tiene datos con la misma forma y volumen aproximado que
produccion, pero nunca los reales sin anonimizar. La diferencia de volumen es
lo que hace que staging no detecte el problema de performance.

**Regla:** las migraciones se aplican primero en staging, con el volumen
realista. Si una migracion bloquea 5 minutos, en staging con 10 veces menos
datos bloquea 30 segundos y el problema no aparece.

---

## Del PR a produccion

### 1. Pull Request

Los gates del PR:
- [ ] CI en verde (lint, tipos, tests, build, seguridad)
- [ ] Al menos una revision que no bloquee
- [ ] Los criterios de aceptacion de la historia tienen cobertura
- [ ] La migracion tiene su reversa (si toca el schema)

### 2. Merge a main

El merge dispara el CI completo. El CI construye la imagen y la publica
como artefacto.

**Regla:** el pipeline es codigo y se revisa como codigo. Un cambio en el
pipeline que hace que los tests dejen de correr es un cambio que rompe la
garantia de todo lo que vino antes.

### 3. Despliegue a staging

El deploy corre automaticamente cuando CI termina en verde.

Se verifica:
- [ ] El servicio levanta
- [ ] `/health` responde
- [ ] Los logs no muestran errores
- [ ] Un smoke test del camino critico pasa
- [ ] Las metricas basicas se ven nomales

**Regla:** el deploy a staging falla si el smoke test falla. Un staging roto
no es un staging "casi roto": es peor que no desplegar, porque da una falsa
sensacion de que el pipeline funciona.

### 4. Verificacion en staging

Verificacion manual o automatizada del comportamiento, con el alcance que se
definio en el ticket. **Regla:** el criterio de verificacion se escribe antes
del deploy, no despues. Despues, uno verifica lo que le sale bien.

### 5. Despliegue a produccion

- Manual, con aprobacion, o automatico si el cambio es de bajo riesgo.
- **Regla:** los cambios de migracion de datos se despliegan en dos pasos:
  primero el codigo compatible con ambos schemas, despues la migracion.

### 6. Verificacion post-deploy

- [ ] El health check responde
- [ ] La tasa de error no subio
- [ ] La latencia p95 no subio
- [ ] Los logs no muestran excepciones nuevas
- [ ] El camino critico funciona (verificacion real, no solo el health check)

---

## Rollback

### Cuando hacer rollback

| Situacion | Accion |
|---|---|
| El servicio no levanta | Rollback inmediato |
| Tasa de error > umbral | Rollback inmediato |
| Latencia p95 > umbral | Rollback inmediato |
| Funcionalidad rota no critica | Rollback si el fix no esta en minutos |
| Funcionalidad rota critica | Rollback inmediato |
| El problema no se conoce | Rollback primero, debug despues |

**Regla:** el rollback es la accion por defecto ante la duda. Debuggear en
produccion con usuarios Inside While usa el tiempo de ellos.

### Como se hace

**Regla:** el rollback despliega el artefacto anterior, no recompila. Es la
unica forma de que sea rapido y confiable.

```bash
# El deploy mantiene el historial de imagenes por ambiente
deploy --env production --tag "<tag anterior>" --wait
```

**Regla:** el rollback esta automatizado en el pipeline, disparado
automaticamente cuando falla la verificacion post-deploy. Un rollback que hay
que hacer a mano con prisa es un rollback que no se hace.

### Rollback de migraciones

Un rollback de codigo no siempre alcanza: si la migracion cambio el schema de
forma incompatible, el codigo viejo tampoco funciona.

**Regla:** toda migracion tiene su reversa, y el rollback de codigo incluye
la reversa de la migracion. Por eso las migraciones Expandir y migrar son el
patron: el codigo viejo funciona con los dos schemas.

### La ventana de rollback

**Regla:** el rollback automatico esta disponible durante los primeros 30
minutos del deploy. Despues, se requiere una decision explicita.

---

## Lo que no se hace

| Anti-patron | Consecuencia |
|---|---|
| Reconstruir la imagen para produccion | Se despliega algo distinto de lo que se probo |
| Hotfix en produccion sin pasar por el pipeline | El fix no existe en el historial |
| Migrar y desplegar en el mismo paso | Sin ventana de rollback |
| Rollback con debug en paralelo | El debug consume recursos del servicio degradado |
| Deploy sin verificacion post | El problema se descubre por el usuario |
| Ambientes con datos de formas distintas | El bug solo aparece en produccion |

## Referencias

- `dev-kit-ci-cd/templates/github-actions-ci.yml` - pipeline de calidad
- `dev-kit-ci-cd/templates/github-actions-deploy.yml` - pipeline de deploy
- `dev-kit-ci-cd/references/seguridad-del-pipeline.md` - permisos y secretos
