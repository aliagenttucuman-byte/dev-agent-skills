# <Nombre del proyecto>

> Esqueleto de README. Copiar, completar los corchetes y borrar lo que no
> aplique. Las doce secciones son el minimo: si una no aplica, se deja una linea
> que diga por que no aplica.

## Proposito

<Una frase: que problema resuelve este proyecto y para quien.>

## Estado

| Campo | Valor |
|---|---|
| Fase actual | <alpha / beta / produccion> |
| Version | <semver> |
| Que falta | <lo que todavia no esta, en una linea> |

## Requisitos

| Herramienta | Version minima | Para que |
|---|---|---|
| Python | <3.12> | backend |
| Node | <20> | frontend |
| Docker | <24> | entorno local |

## Instalacion

```bash
# 1. clonar el repositorio
git clone <url del repositorio>
cd <nombre del proyecto>

# 2. copiar la configuracion de ejemplo
cp .env.example .env

# 3. instalar dependencias
make install

# 4. levantar el entorno
make up
```

Salida esperada:

```
<salida real del comando, para que el lector sepa que funciono>
```

## Uso rapido

```bash
<el ejemplo mas pequeno que produce un resultado observable>
```

Resultado:

```
<salida real>
```

## Configuracion

| Variable | Default | Obligatoria | Para que |
|---|---|---|---|
| `<NOMBRE>` | `<valor>` | si / no | <que configura> |

Los valores sensibles van en el entorno, nunca en el repositorio.

## Comandos

| Comando | Que hace | Cuando se usa |
|---|---|---|
| `make install` | instala dependencias | una vez, al arrancar |
| `make test` | corre la suite de pruebas | antes de commitear |
| `make lint` | verifica estilo y formato | antes de commitear |
| `make typecheck` | verifica tipos estaticos | antes de commitear |
| `make migrate` | aplica las migraciones | al cambiar el esquema |
| `make up` / `make down` | levanta o baja el entorno | en desarrollo |
| `make smoke` | verifica que el proyecto arranca | en CI |

## Estructura

```
<nombre-del-proyecto>/
├── <carpeta>/    # <que vive ahi, una linea>
├── <carpeta>/    # <que vive ahi, una linea>
└── <archivo>     # <que hace>
```

## API

La referencia de la API se genera desde el codigo:

```bash
make docs
```

- Referencia interactiva: <enlace o ruta local>
- Esquema versionado: `docs/openapi.json`

Los ejemplos de esta seccion se generan desde los tests de integracion: si un
ejemplo falla, el test falla.

## Despliegue

| Paso | Comando o accion | Resultado esperado |
|---|---|---|
| 1 | <build de la imagen> | <imagen construida> |
| 2 | <publicacion> | <version publicada> |
| 3 | <verificacion> | <health check en verde> |

Revertir: <como se vuelve a la version anterior, con el comando>.

## Tests

```bash
make test              # suite completa
make test-unit         # solo unitarios, rapido
make test-integration  # requiere base de datos
```

Cobertura minima: <umbral>%. El gate vive en CI.

## Licencia

<Tipo de licencia>. Ver <ruta del archivo de licencia>.
