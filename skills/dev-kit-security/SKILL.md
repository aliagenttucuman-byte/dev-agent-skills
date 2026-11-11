---
name: dev-kit-security
description: "Baseline de seguridad para aplicaciones y agentes: gestion de secretos, autenticacion y autorizacion, validacion de input, CORS, rate limiting y checklist de pre-deploy. CARGAR antes de exponer un servicio, al agregar un endpoint nuevo o cuando se revisa la postura de seguridad de un proyecto."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, secrets, auth, validation, owasp, checklist]
    category: software-development
    related_skills: [dev-kit-backend-stack, dev-kit-database, dev-kit-ci-cd, dev-kit-review]
---

# Dev Kit - Security

> **Trigger:** "exponer la API", "agregar un endpoint", "guardar una clave",
> "revisar seguridad", "checklist antes de salir a produccion". Cargar antes
> de que el servicio quede accesible, no despues de un incidente.

## Que es esto

El minimo de seguridad que tiene que tener cualquier servicio, y el criterio
para decidir cuando algo alcanza ese minimo.

## La regla que gobierna todo

> **La seguridad no es una etapa. Es una propiedad de cada linea que se
> escribe.**

Un checklist que se corre al final encuentra lo que se busco. Un criterio que
se aplica al escribir evita el problema.

## El modelo de amenaza minimo

Antes de aplicar controles, responder tres preguntas:

| Pregunta | Ejemplo |
|---|---|
| Que datos protegemos? | Datos personales, credenciales, datos financieros |
| Quien puede tocarlos? | Usuarios autenticados, administradores, anonimos |
| Como falla si se filtran? | Legal, reputacional, operativo |

**Regla:** sin este modelo, los controles se eligen por moda y se ajustan al
proyecto equivocado.

## Secretos

### La regla

> **Un secreto en el repositorio es un secreto filtrado, sin importar que el
> repo sea privado.**

Un repositorio privado con 10 personas tiene 10 personas con acceso, mas los
sistemas de CI, mas los backups, mas las copias que hizo cada uno. Rotar un
secreto filtrado es barato; recorrer los logs, los forks y las copias para
encontrar donde mas esta, no.

### Como se maneja

| Que | Donde | Como |
|---|---|---|
| Claves de API de terceros | Gestor de secretos o variable de entorno | Inyectada en runtime |
| Credenciales de base de datos | Gestor de secretos | Variable de entorno con URL completa |
| Tokens de firma | Gestor de secretos | Rotacion periodica |
| Claves privadas | Archivo con permisos restrictivos | Montado en runtime, nunca en la imagen |

**Regla:** ninguna clave en el codigo, ni en el historial de git, ni en la
imagen de Docker, ni en los logs.

### En el repositorio

```gitignore
.env
.env.*
!.env.example
*.pem
*.key
secrets/
```

```bash
# .env.example versionado: el contrato sin los valores
DATABASE_URL=postgresql+psycopg://user:password@host:5432/db
API_KEY=your-key-here
```

**Regla:** `.env.example` con el nombre de cada variable y un valor de ejemplo
que obviously no funciona. Es documentación ejecutable.

### En el codigo

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    api_key: str
```

**Regla:** las variables de entorno obligatorias (sin default) fallan al
arrancar si no estan definidas. Es preferible que el servicio no levante a
que levante sin credenciales.

### Rotacion

**Regla:** todo secreto tiene procedimiento de rotacion documentado y probado.
El dia que hay que rotar es el peor dia para descubrir que no se sabe como.

**Regla:** la rotacion es compatible con las dos versiones durante el
transicion (la clave vieja y la nueva funcionan a la vez). Sin eso, la
rotacion es una caida.

### Cuando un secreto se filtra

1. Rotar **primero**. No investigar primero: la clave esta filtrada.
2. Revisar los logs de acceso en busca de uso inexplicable.
3. Revisar el historial de git: el secreto puede seguir ahi.
4. Notificar a los afectados si hubo acceso.

**Regla:** la Investigacion va despues de la rotacion, nunca antes.

## Autenticacion

### Los tres factores

| Factor | Que es | Como se verifica |
|---|---|---|
| **Que se** | Un secreto que el usuario conoce | Contrasena, PIN |
| **Que tiene** | Un dispositivo | Token TOTP, llave de seguridad |
| **Que es** | Una biometria | Huella, reconocimiento facial |

**Regla:** el segundo factor en el login. Es la medida con mejor relacion
costo/beneficio de toda la seguridad de usuario.

### Contrasenas

- [ ] Se guardan con un algoritmo de derivacion lento (argon2, bcrypt, scrypt), nunca con hash simple
- [ ] Con una salt unica por usuario
- [ ] Con parametros de costo que suban con el hardware
- [ ] Con un limite de intentos y un bloqueo temporal
- [ ] Nunca se reenvian ni se registran

```python
# argon2 con parametros por defecto revisados
password_hash = argon2.PasswordHasher().hash(password)

def verify(password_hash: str, password: str) -> bool:
    try:
        argon2.PasswordHasher().verify(password_hash, password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False
```

**Regla:** el hash no se verifica comparando strings: se usa la funcion de
verificacion, que maneja el caso de que el usuario no exista sin filtrar
tiempos.

### Tokens

| Tipo | Uso | Caracteristicas |
|---|---|---|
| **Sesion** | Navegador | Almacenado en cookie `HttpOnly`, `Secure`, `SameSite` |
| **Acceso** | API | Corto-lived, con refresh |
| **Refresh** | Renovar acceso | Almacenado de forma segura, rotativo |

**Regla:** el token de sesion va en cookie `HttpOnly` + `Secure` + `SameSite=Lax`.
Un token en `localStorage` es accesible desde cualquier XSS.

**Regla:** el token de acceso es corto (15-60 minutos). El refresh es largo y
rotativo: cada uso genera uno nuevo, y el anterior deja de servir.

### JWT

| Regla | Por que |
|---|---|
| Validar la firma | Un JWT sin verificar es contenido del cliente |
| Validar `exp` | Un token sin expiracion es una credencial permanente |
| Validar `aud` (audiencia) | Un token emitido para otra API no sirve aca |
| Validar `iss` (emisor) | Idem |
| Usar un algoritmo fijo (HS256 o RS256) | El algoritmo "none" o el cambio en el header es un ataque clasico |
| No meter datos sensibles | El payload se decodifica sin secreto |

**Regla:** el payload de un JWT es legible por cualquiera. Solo van IDs,
roles y expiracion. Nunca datos personales.

## Autorizacion

### La diferencia que se confunde

| | Autenticacion | Autorizacion |
|---|---|---|
| Pregunta | Quien sos? | Que podes hacer? |
| Falla | 401 Unauthorized | 403 Forbidden |

**Regla:** un endpoint sin autorizacion devuelve 401 si no hay credenciales,
403 si las hay pero no alcanzan. Confundirlos esconde el bug.

### El error mas caro

> **Autenticado no significa autorizado.**

Un usuario autenticado que pide un recurso que no es suyo es el error de
seguridad mas comun y mas grave. Es el que produce las fugas de datos
multi-cliente.

### Modelo por recurso (la forma que escala)

```python
@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> Order:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="orden no encontrada")
    if order.user_id != user.id:
        # 404 y no 403: no revelamos que el recurso existe.
        raise HTTPException(status_code=404, detail="orden no encontrada")
    return order
```

**Regla:** la autorizacion se verifica contra el recurso, no contra el
endpoint. Que el endpoint tenga un control de acceso no alcanza: hay que
comprobar que **este** recurso pertenece a **este** usuario.

**Regla:** devolver 404 en vez de 403 cuando el recurso existe pero es de
otro. Un 403 confirma que el recurso existe, lo cual es informacion.

### Roles vs permisos

| Modelo | Cuando | Complejidad |
|---|---|---|
| Roles fijos | El equipo es pequeno y estable | Baja |
| Permisos granulares | Hay varios tipos de usuario con permisos distintos | Media |
| ABAC (atributos) | Las reglas dependen del recurso y del contexto | Alta |

**Regla:** empezar con roles. Migrar a permisos cuando los roles se queden
chicos, no antes.

**Regla:** el chequeo de permisos es un punto unico del codigo, no una
condicion repetida en cada endpoint. Un helper `require_permission("orders:write")`
que se aplica como dependencia.

## Validacion de input

### Las tres validaciones

| Capa | Que valida | Como |
|---|---|---|
| **Sintactica** | El formato | Tipos, regex, rango |
| **Semantica** | El significado | Reglas de negocio, existencia, permisos |
| **De contexto** | El encuadre | Rate limit, CSRF, idempotencia |

**Regla:** la validacion de sintaxis se hace en el borde (el schema de
pydantic). La semantica, en la capa de dominio. Nunca todo en el controlador.

### Inyeccion

| Tipo | Defensa |
|---|---|
| SQL | Consultas parametrizadas. Nunca concatenar strings |
| Comandos del sistema | `subprocess` con lista de argumentos, sin `shell=True` |
| Paths | Resolver y verificar que esta dentro del directorio permitido |
| HTML | Escapar al renderizar |
| LDAP / NoSQL | Consultas parametrizadas |

**Regla:** el punto de inyeccion mas comun no es la base de datos: es el shell.
Nunca construir un comando con f-strings.

```python
# MAL
subprocess.run(f"tar -xf {user_path}", shell=True)

# BIEN
subprocess.run(["tar", "-xf", resolved_path], check=True)
```

**Regla:** la validacion de paths tiene que resolver los simbolos antes de
comparar. `/app/data/../../etc/passwd` no empieza con `/app/data`.

### CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],   # lista explicita
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

**Regla:** nunca `allow_origins=["*"]` junto con `allow_credentials=True`. La
especificacion lo prohibe y el navegador lo rechaza, pero un proxy mal
configurado puede dejarlo pasar.

**Regla:** la lista de origenes viene de configuracion, no hardcodeada.

## Rate limiting

| Endpoint | Limite tipico | Por que |
|---|---|---|
| Login | 5 por minuto por IP + por usuario | Fuerza bruta |
| Envio de codigo | 3 por minuto por usuario | Abuso de SMS |
| API general | 100 por minuto por usuario | Consumo abusivo |
| Endpoint caro (LLM) | Segun el presupuesto | Costo |

**Regla:** el limite se aplica **por identidad**, no solo por IP. Las IPs se
comparten (corporaciones, NAT, proxies). Un limite solo por IP castiga a los
usuarios legitimos detrás de un proxy corporativo.

**Regla:** el limite de login se cuenta por usuario Y por IP, y el mas
estricto gana.

**Regla:** el rate limit responde 429 con un header `Retry-After`.

## Headers de seguridad

```python
MIDDLEWARE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Permissions-Policy": "geolocation=(), microphone=()",
}
```

**Regla:** la CSP se define con `default-src 'self'` y se abre lo
necesario. Una CSP con `unsafe-inline` en scripts no protege de XSS.

**Regla:** HSTS solo si el servicio es exclusivamente HTTPS. En un ambiente de
desarrollo con HTTP rompe el flujo.

## Checklist de pre-deploy

- [ ] No hay secretos en el codigo, ni en el historial, ni en la imagen
- [ ] `.env` esta ignorado y `.env.example` versionado
- [ ] Las variables obligatorias fallan al arrancar si faltan
- [ ] Las contrasenas se hashean con algoritmo lento y salt unico
- [ ] El segundo factor esta habilitado
- [ ] Los tokens de sesion van en cookie HttpOnly + Secure + SameSite
- [ ] Los tokens tienen expiracion, y los refresh rotan
- [ ] Cada endpoint verifica que el recurso pertenece al usuario
- [ ] Los 403 se diferencian de los 404 en recursos ajenos
- [ ] Las consultas a base de datos son parametrizadas
- [ ] Los comandos del sistema no usan `shell=True` con interpolacion
- [ ] Los paths se validan contra el directorio permitido
- [ ] La CSP esta definida sin `unsafe-inline`
- [ ] CORS usa lista explicita de origenes
- [ ] Hay rate limit en login y en los endpoints caros
- [ ] Los logs no contienen datos sensibles (verificado con un filtro)
- [ ] Las dependencias pasan la auditoria
- [ ] Los errores no exponen detalle interno al cliente

## Anti-patrones

| Anti-patron | Consecuencia |
|---|---|
| Secreto en el codigo | Filtracion |
| `.env` versionado | Filtracion |
| `allow_origins=["*"]` con credenciales | Fuga entre origenes |
| Sin rate limit en login | Fuerza bruta |
| Solo autenticacion, sin autorizacion por recurso | Fuga de datos multi-cliente |
| 403 donde va 404 | Se revela la existencia del recurso |
| SQL con strings concatenados | Inyeccion |
| `shell=True` con f-string | Inyeccion de comandos |
| Sin CSP | XSS sin barrera |
| Secretos en los logs | Filtracion por logs |
| JWT sin validar `exp` ni `aud` | Token reutilizable |
| Dependencias sin auditar | Vulnerabilidades conocidas |
| CSP con `unsafe-inline` | XSS pasa igual |
| Comparacion de contrasenas con `==` | Vulnerable a timing |
| Rate limit solo por IP | Usuarios legitimos bloqueados |

## Referencias

- `templates/security-checklist.md` - checklist imprimible de pre-deploy
- `dev-kit-backend-stack` - donde se implementan los controles
- `dev-kit-database` - aislamiento multi-tenant (una forma de autorizacion)
- `dev-kit-ci-cd` - auditoria de dependencias y busqueda de secretos
