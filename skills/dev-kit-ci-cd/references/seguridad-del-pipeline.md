# Seguridad del pipeline

Referencia de `dev-kit-ci-cd`. Permisos, secretos y superficie de ataque de la
pipeline.

---

## La regla

> **La pipeline corre codigo de terceros en cada commit. Es el punto mas
> expuesto de todo el sistema.**

Un `pip install` ejecuta un `setup.py` arbitrario. Un action de GitHub es
codigo remoto que se ejecuta con los permisos del job. Tratar la pipeline
como si fuera confiable es el error mas caro.

---

## Permisos

### El default es readonly

```yaml
permissions:
  contents: read
```

A nivel de workflow. Cada job pide mas solo si lo necesita:

```yaml
jobs:
  build:
    permissions:
      contents: read
      packages: write    # solo este job publica la imagen
```

**Regla:** el permiso minimo por job, no por workflow. Un job de tests no
tiene por que poder publicar imagenes.

**Regla:** nunca `permissions: write-all`. Con `write-all`, un action
comprometido puede publicar releases, modificar el repo y todo lo demas.

### Nunca dar permisos a codigo no confiable

```yaml
# MAL: un PR de un fork recibe write sobre el repo
pull_request_target:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - run: npm install && npm test   # ejecuta codigo del PR con write
```

**Regla:** `pull_request_target` NO se usa para correr codigo del PR. Un fork
puede enviar un PR y ejecutar cualquier cosa con los secretos del repo.

**Patron correcto:** en un PR de fork, usar `pull_request` (sin secretos) o
no correr nada que dependa del codigo del PR.

---

## Secretos

### De donde vienen

| Fuente | Uso | Nivel de exposicion |
|---|---|---|
| Secretos del repositorio | Tokens de despliegue | Alto: cualquier job lo puede leer |
| Secretos del ambiente | Credenciales de produccion | Medio: solo jobs con ese ambiente |
| OIDC | Credenciales temporales por identidad | Bajo: expiran solas |
| Variables del repositorio | Configuracion no sensible | Bajo: son publicas |

**Regla:** un secreto que puede vivir en un ambiente, vive en el ambiente.
Los secretos del ambiente se restringen a los jobs que declaran
`environment:`.

**Regla:** preferir OIDC (identidad federada) sobre tokens de larga duracion.
Un token temporal que expira en una hora es infinitamente mejor que uno que
expira en un ano.

### Reglas de uso

- [ ] Ningun secreto se imprime en los logs (`set -x` desactivado en pasos con secretos)
- [ ] Ningun secreto se pasa por `env` a un paso que corre codigo de terceros sin necesidad
- [ ] Ningun secreto se escribe en un archivo que se versiona
- [ ] Los secretos rotan, y la rotacion esta documentada
- [ ] `dependabot` esta activo para las actualizaciones de acciones

```yaml
# MAL: el error de un comando puede imprimir el token
- name: Deploy
  run: curl -H "Authorization: $TOKEN" https://api.example.com
  # si falla, el token puede quedar en el log

# BIEN: mascarar en el paso
- name: Deploy
  env:
    TOKEN: ${{ secrets.DEPLOY_TOKEN }}
  run: |
    set +x
    curl -H "Authorization: $TOKEN" https://api.example.com
```

---

## Actions de terceros

### Fijar la version

```yaml
# MAL: usa la ultima version, que puede cambiar en cualquier momento
- uses: actions/checkout@v4

# BIEN: fijado a un commit
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
```

**Regla:** para acciones de terceros en una pipeline critica, fijar el SHA.
Una etiqueta `v4` se puede mover.

**Regla:** para acciones oficiales de GitHub, la etiqueta mayor es aceptable si
`dependabot` esta configurado para actualizarlas.

### Revisar antes de agregar

Antes de agregar una action, preguntar:
1. Quien la mantiene?
2. Que permisos necesita?
3. Que hace con los secretos que recibe?
4. Cuantos usos tiene en otros repos?

**Regla:** una action que hace lo mismo que cinco lineas de shell no se
agrega. El costo de supply chain es permanente.

---

## El contenedor de los jobs

```yaml
jobs:
  quality:
    runs-on: ubuntu-latest
    container:
      image: python:3.11-slim
    options: >-
      --security-opt no-new-privileges:true
      --cap-drop ALL
```

**Regla:** `no-new-privileges` y `cap-drop ALL` en los contenedores que
ejecutan codigo no confiable.

---

## Superficie de ataque del repositorio

| Vector | Mitigacion |
|---|---|
| Action de terceros comprometida | Fijar el SHA, revisar antes de agregar |
| Dependencia con codigo malicioso en el build | Auditoria de dependencias, revision de los paquetes nuevos |
| PR de un fork con permisos | No usar `pull_request_target` para ejecutar codigo |
| Secretos expuestos en los logs | Revisar el historial de los logs, rotar |
| Action de unmantenedor que abandona el repo | `dependabot` actualiza las versiones |
| Script de post-checkout con el repo clonado | Revisar `.git/hooks`, que no se versiona pero se puede inyectar |

---

## Checklist de la pipeline

- [ ] `permissions` en el workflow, minimo, no `write-all`
- [ ] Permisos especificos por job
- [ ] Ningun `pull_request_target` que ejecute codigo del PR
- [ ] Secretos del ambiente para lo que toca produccion
- [ ] Secretos fuera de los logs
- [ ] `set +x` en los pasos que usan secretos
- [ ] Acciones fijadas a SHA (las de terceros)
- [ ] `dependabot` activo
- [ ] Auditoria de dependencias en el pipeline
- [ ] Busqueda de secretos (gitleaks) en el pipeline
- [ ] Contenedores con `no-new-privileges`
- [ ] `concurrency` definido para cancelar runs redundantes
- [ ] `timeout-minutes` en todos los jobs

## Referencias

- `dev-kit-ci-cd/templates/github-actions-ci.yml` - pipeline de calidad
- `dev-kit-ci-cd/templates/github-actions-deploy.yml` - pipeline de deploy
- `dev-kit-ci-cd/references/promocion-y-rollback.md` - promocion y rollback
