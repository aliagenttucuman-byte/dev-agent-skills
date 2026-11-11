# Handoff - <agente origen> -> <agente destino>

> Paquete de traspaso. Si el receptor necesita preguntar algo para empezar,
> falta contexto: completar antes de asignar.

## Identificacion

| Campo | Valor |
|---|---|
| Tarea | <id de tarea> |
| Agente origen | <rol> |
| Agente destino | <rol> |
| Capa | producto / contrato / diseno / implementacion / datos / verificacion / operacion |
| Fecha | - |

## Objetivo

Una frase: que queda distinto al terminar.

```
<Que se obtiene al terminar que no existia antes>
```

## Contexto

Donde encaja el trabajo, que modulos toca, que reglas del proyecto aplica.

```
<Contexto minimo suficiente para trabajar sin preguntar>
```

## Artefactos previos

| Artefacto | Version | Ubicacion | Que aporta |
|---|---|---|---|
| <contrato / plan / especificacion> | - | `<ruta relativa>` | <que define> |

## Criterio de aceptacion

Comandos verificables. Un criterio sin comando no es criterio.

| # | Criterio | Comando que lo prueba | Estado |
|---|---|---|---|
| 1 | <criterio observable> | `<comando>` | pendiente |
| 2 | <criterio observable> | `<comando>` | pendiente |

## Fuera de alcance

Lo que este agente NO debe tocar:

- <lista>

## Estado de partida

| Campo | Valor |
|---|---|
| Intentos previos | 0 |
| Errores ya vistos | - |
| Ultimo artefacto bueno | - |
| Bloqueos | - |

## Notas de entrega

<Contexto no obvio que el receptor no puede deducir del codigo. Omitir si no hay.>

---

## Confirmacion de recepcion (opcional)

- [ ] El receptor confirma que puede arrancar sin preguntas
- [ ] El receptor confirma que entendio el criterio de aceptacion
- [ ] Ante cualquier duda, se devuelve al origen en vez de suponer
