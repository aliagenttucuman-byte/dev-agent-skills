# Accesibilidad en el frontend

> Referencia de `dev-kit-frontend-stack`. Lo minimo que tiene que cumplir una
> interfaz para ser usable por todos.

## El criterio

> **Un control que no se puede usar con el teclado no existe para una parte de
> tus usuarios. Un texto que no se puede leer no existe para otra.**

La accesibilidad no es un extra: es parte de la definicion de "terminado".

## Checklist por componente

### Botones y enlaces

- [ ] Un boton hace una accion, un enlace navega
- [ ] El elemento es `<button>` o `<a>`, no un `<div>` con `onClick`
- [ ] El texto del boton dice que hace ("Guardar cambios", no "Aceptar")
- [ ] El icono solo tiene texto alternativo si no hay texto visible
- [ ] El foco se ve (`:focus-visible` con contraste suficiente)
- [ ] El orden de tabulacion sigue el orden visual

```tsx
// MAL: no es un boton, no es accesible con teclado
<div onClick={submit}>Enviar</div>

// BIEN
<button type="submit" onClick={submit}>Enviar</button>
```

### Formularios

- [ ] Cada campo tiene un `<label>` asociado (no solo un placeholder)
- [ ] Los errores se anuncian y se asocian al campo con `aria-describedby`
- [ ] Los errores tienen texto, no solo color
- [ ] El foco va al primer campo con error despues de un submit fallido
- [ ] Los campos requeridos se marcan de forma accesible (`aria-required`)
- [ ] El grupo de radios y checkboxes tiene `fieldset` y `legend`

```tsx
<label htmlFor="email">Email</label>
<input
  id="email"
  type="email"
  aria-required="true"
  aria-invalid={!!error}
  aria-describedby={error ? "email-error" : undefined}
/>
{error && <p id="email-error" role="alert">{error}</p>}
```

**El placeholder no es un label:** desaparece cuando el usuario escribe, no es
accesible con lectores de pantalla de forma fiable, y es invisible en muchos
navegadores cuando el campo tiene valor.

### Contenido dinamico

- [ ] Los cambios de estado se anuncian (`role="status"` o `role="alert"`)
- [ ] Un modal atrapa el foco y lo devuelve al cerrarse
- [ ] Un spinner de carga tiene texto para lectores de pantalla
- [ ] Las notificaciones de error se anuncian

```tsx
<div role="status" aria-live="polite">
  {isSaving ? "Guardando..." : null}
</div>
```

### Tablas y datos

- [ ] La tabla tiene `<th>` con `scope`
- [ ] Las celdas de datos tienen `<td>`
- [ ] La tabla tiene `<caption>` o un titulo asociado
- [ ] Los datos no dependen solo del color para diferenciarse

### Imagenes y contenido no textual

- [ ] Las imagenes informativas tienen `alt` con descripcion
- [ ] Las imagenes decorativas tienen `alt=""`
- [ ] Los graficos tienen una descripcion textual o una tabla equivalente
- [ ] Los iconos con accion tienen nombre accesible

### Estructura y navegacion

- [ ] Hay un solo `<h1>` por pagina
- [ ] Los headings no se saltan niveles
- [ ] Las regiones de la pagina tienen landmarks (`header`, `nav`, `main`, `footer`)
- [ ] El `main` existe y es unico

### Movimiento

- [ ] Las animaciones se pueden desactivar con `prefers-reduced-motion`
- [ ] Nada parpadea mas de 3 veces por segundo
- [ ] El contenido que se mueve no es unico portador de informacion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Contraste

| Texto | Minimo |
|---|---|
| Normal | 4.5:1 |
| Grande (18pt+ o 14pt bold) | 3:1 |
| Elementos de interfaz y bordes de foco | 3:1 |

**El color no es el unico portador de significado.** Un campo invalido con
borde rojo y sin texto de error no es accesible: quien no distingue el rojo no
sabe que esta mal.

## Foco

```css
:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}
```

**Regla:** nunca `outline: none` sin reemplazo. Quitar el foco sin poner otro
deja al usuario de teclado sin saber donde esta.

**Regla:** el modal devuelve el foco al elemento que lo abrio. Si no, el
usuario vuelve al principio de la pagina.

## Verificacion

### Manual

1. Recorrer toda la pagina solo con `Tab` y `Shift+Tab`.
2. Operar todos los controles con `Enter` y `Space`.
3. Verificar que el foco siempre se ve.
4. Desactivar CSS y verificar que la pagina sigue siendo usable.

### Automatizada

Integrar un chequeo de accesibilidad en el pipeline:

```bash
# Con un linter de accesibilidad sobre los archivos de componentes
npx eslint --ext .tsx,.jsx src/
```

**Regla:** el chequeo automatico es un piso, no una garantia. Detecta el 30% de
los problemas. El resto se descubre recorriendo la pagina con el teclado.

## Anti-patrones

| Anti-patron | Consecuencia |
|---|---|
| `<div>` con `onClick` | No operable con teclado |
| Placeholder como label | El campo no tiene nombre accesible |
| `outline: none` sin reemplazo | El usuario de teclado se pierde |
| Error solo en rojo | Se pierde el 8% de los usuarios con daltonismo |
| Modal sin trampa de foco | El foco se va al fondo |
| Spinner sin texto | Silencio para lectores de pantalla |
| Animacion sin alternativa | Puede provocar nauseas |
| Tablas sin `scope` | Lectores de pantalla pierden la relacion |
| Contenido que solo se explica con color | Informacion perdida |

## Referencias

- `dev-kit-frontend-stack/templates/component-tree.md` - donde vive cada pieza
- `dev-kit-frontend-stack/references/estado-y-fetching.md` - estados de fetching
- `dev-kit-frontend-stack/references/performance.md` - que optimizar y que no
