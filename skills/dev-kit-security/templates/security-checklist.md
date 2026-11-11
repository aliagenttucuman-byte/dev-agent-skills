# Checklist de seguridad pre-deploy

> Referencia de `dev-kit-security`. Para revisar antes de exponer un servicio.
> Cada item se marca con como se verifica, no solo con un casillero.

## Secretos

- [ ] No hay secretos en el codigo (`grep` del repo por nombres comunes de claves)
- [ ] No hay secretos en el historial de git (revisar los commits iniciales)
- [ ] No hay secretos en la imagen de Docker (revisar las capas)
- [ ] `.env` esta en `.gitignore`
- [ ] `.env.example` esta versionado y no tiene valores reales
- [ ] Las variables obligatorias fallan al arrancar si faltan
- [ ] El gestor de secretos esta configurado para el ambiente destino
- [ ] Existe procedimiento de rotacion documentado

**Comando de verificacion:** buscar en el repo y en la imagen los prefijos de
los proveedores de credenciales mas usados.

## Autenticacion

- [ ] Las contrasenas se hashean con argon2 o bcrypt
- [ ] Hay salt unico por usuario
- [ ] El segundo factor esta habilitado para operaciones sensibles
- [ ] Los tokens de sesion van en cookie HttpOnly + Secure + SameSite
- [ ] El token de acceso expira en menos de una hora
- [ ] El refresh token rota en cada uso
- [ ] Los JWT validan firma, `exp`, `aud` e `iss`
- [ ] El algoritmo del JWT es fijo (no se negocia en el header)
- [ ] El payload del JWT no tiene datos personales

## Autorizacion

- [ ] Cada endpoint verifica que el recurso pertenece al usuario
- [ ] Los recursos ajenos devuelven 404, no 403
- [ ] Los endpoints administrativos tienen control de acceso
- [ ] El chequeo de permisos es un punto unico, no condiciones repetidas
- [ ] Hay un test que verifica que un usuario no accede a datos de otro

**Verificacion:** el test de aislamiento multi-cliente es el que mas importa.
Debe estar en la pipeline, no solo en QA.

## Validacion de input

- [ ] Los endpoints validan el cuerpo con un schema
- [ ] Las consultas a base de datos son parametrizadas
- [ ] Los comandos del sistema no usan `shell=True` con interpolacion
- [ ] Los paths se resuelven y se validan contra el directorio permitido
- [ ] La salida de HTML se escapa
- [ ] Las paginaciones tienen limite maximo
- [ ] Los campos de archivo tienen limite de tamano y de tipo

## Red

- [ ] CORS usa una lista explicita de origenes
- [ ] No hay `allow_origins=["*"]` con `allow_credentials=True`
- [ ] Hay CSP sin `unsafe-inline` en scripts
- [ ] Esta `X-Content-Type-Options: nosniff`
- [ ] Esta `X-Frame-Options` o `frame-ancestors` en la CSP
- [ ] HSTS esta activo en produccion
- [ ] El TLS esta configurado con cifrados aceptables

## Rate limiting y DoS

- [ ] El login tiene rate limit por usuario y por IP
- [ ] Los endpoints caros (LLM, exportaciones) tienen limite
- [ ] El limite responde 429 con `Retry-After`
- [ ] Hay limite de tamano de body
- [ ] Hay timeout en las llamadas a dependencias externas

## Datos

- [ ] Los datos sensibles no van a los logs (filtro verificado)
- [ ] Los datos personales no se exponen en las respuestas de error
- [ ] La base de datos no es accesible desde internet
- [ ] El backup esta cifrado
- [ ] Los datos en los ambientes de prueba estan anonimizados

## Dependencias

- [ ] `pip audit` / `npm audit` pasa sin vulnerabilidades altas
- [ ] Las dependencias nuevas fueron revisadas antes de agregarse
- [ ] Hay actualizaciones automaticas configuradas
- [ ] Las acciones de CI estan fijadas a versiones

## Verificacion final

- [ ] Se ejecuto un escaneo de dependencias
- [ ] Se ejecuto un escaneo de secretos sobre el repo y la imagen
- [ ] Los tests de seguridad corrieron en la pipeline
- [ ] Un tester que intento romper el endpoint mas expuesto lo logro

**Regla:** el ultimo item no es opcional. Es el que encuentra lo que la
checklist no anticipo.

## Resultado

Fecha: ______
Responsable: ______
Entorno: [dev / staging / produccion]
Resultado: [aprobado / rechazado]
Observaciones: ______
