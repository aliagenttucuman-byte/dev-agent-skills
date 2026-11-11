# Review por tipo de cambio - errores tipicos

Detalle de que mirar en cada tipo de cambio, con el error que suele escaparse
y como se detecta.

---

## Deteccion del tipo de cambio

El tipo se deduce de los archivos tocados, no de lo que dice el titulo.

| Señal en el diff | Tipo |
|---|---|
| Archivos de migracion, `alembic/`, migraciones SQL | Base de datos |
| Archivos de workflow, `Dockerfile`, `terraform/`, `*.tf` | Infra / CI |
| Archivos de ruta de API, `routers/`, `controllers/`, `schemas/` | API / contrato |
| Archivos de componente, `*.tsx`, `*.jsx`, `*.vue` | UI |
| Archivos de dominio, `services/`, `domain/`, `use_cases/` | Logica de negocio |
| Archivos de test unico, sin cambio de produccion | Test |

Un cambio puede ser de varios tipos a la vez. Se revisa con todos los
checklists que apliquen.

---

## Logica de negocio

**El error que se escapa:** el caso en que el dato viene de un sistema
externo con formato distinto.

**Como se detecta:** buscar en el codigo los accesos a integraciones externas
y preguntarse que pasa si el campo viene null, viene como string numerico, o
viene con un timestamp sin zona.

**Revision clave:** no asumir que el dato externo cumple el contrato. El
contrato se cumple la primera vez y despues nadie lo verifica.

---

## API

**El error que se escapa:** cambiar un nombre de campo o un tipo y actualizar
solo un lado.

**Como se detecta:** buscar el nombre del campo en todo el repositorio (no
solo en el backend). Si aparece en el cliente, en los tests y en la
documentacion, hay que actualizar los tres.

**Segundo error que se escapa:** el endpoint que devuelve 200 con un cuerpo
vacio en vez de 404. El cliente no sabe si fallo o no hay datos.

---

## Base de datos

**El error que se escapa:** la migracion sin rollback.

**Como se detecta:** toda migracion debe tener su funcion de downgrade. Si no
la tiene, es bloqueante: sin rollback, un deploy fallido deja el schema en un
estado intermedio que nadie sabe revertir.

**Segundo error:** agregar columna `NOT NULL` sin default a una tabla con
datos. Falla en el deploy, en produccion, con datos reales.

**Tercero:** el indice que falta y se descubre en el primer endpoint lento.
Por eso el review de performance mira los indices de las columnas por las que
filtra la consulta nueva.

---

## Seguridad

**El error que se escapa:** la autorizacion que falta.

**Como se detecta:** por cada endpoint nuevo o modificado, verificar que hay
una verificacion de que el usuario puede acceder a ESE recurso. La
autenticacion no es autorizacion: que el usuario este autenticado no significa
que ese recurso sea suyo.

**Segundo error:** el error de aplicacion que devuelve el detalle interno.
Mensaje para el usuario: "no se pudo completar la operacion". Log para el
equipo: la excepcion completa con contexto.

---

## Performance

**El error que se escapa:** el N+1.

**Como se detecta:** un listado que, por cada fila, hace una consulta mas.
En el codigo se ve como un bucle con una llamada a la base de datos dentro.
Se detecta leyendo el log de queries, no el codigo.

**Segundo error:** la paginacion mal hecha. Si el codigo hace
`SELECT * FROM t` y despues corta la lista en memoria, el limite de pagina no
protege nada.

---

## Refactor

**El error que se escapa:** el cambio de comportamiento "de paso".

**Como se detecta:** comparar el diff con el criterio de aceptacion. Si el
refactor no deberia cambiar comportamiento y hay cambios en la logica, hay
dos opciones: separar el PR o justificar el cambio. Mezclados, el revisor
tiene que verificar dos cosas a la vez y no verifica ninguna.

**Segundo error:** tests modificados para que pasen. Un refactor que obliga a
cambiar los tests suele cambiar comportamiento, no solo estructura.

---

## UI

**El error que se escapa:** los estados que nunca se vieron.

**Como se detecta:** preguntarse que se ve sin datos, con datos, durante la
carga, y con error. Si el codigo solo tiene el caso "con datos", faltan tres.

**Segundo error:** el formulario que valida en el submit y no en el campo.
El usuario escribe todo, aprieta, y recien ahi se entera de que algo estaba
mal desde el principio.

---

## Infra / CI

**El error que se escapa:** los permisos excesivos.

**Como se detecta:** revisar que permisos pide el workflow. Si pide mas de lo
que la tarea necesita, es bloqueante: un pipeline con permisos de
administrador es un pipeline con acceso total a produccion si se compromete.

**Segundo error:** el recurso sin limite. Un job que se cuelga puede quedar
corriendo consumiendo presupuesto hasta que alguien lo note.

---

## Documentacion

**El error que se escapa:** el ejemplo que dejo de funcionar.

**Como se detecta:** ejecutar los ejemplos del README. Si son copiables,
deberian correr. Un ejemplo roto hace que el lector pierda confianza en todo
el documento.
