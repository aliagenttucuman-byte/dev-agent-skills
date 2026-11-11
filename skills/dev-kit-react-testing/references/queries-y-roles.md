# Queries y roles

Tabla completa de queries de Testing Library y como elegir la correcta.

---

## Las cuatro familias

| Familia | Cuando | Comportamiento si no encuentra |
|---|---|---|
| `getBy*` | El elemento **debe** existir | Lanza error |
| `queryBy*` | El elemento **no debe** existir | Devuelve `null` |
| `findBy*` | El elemento **aparecera** (async) | Devuelve promesa, espera |
| `getAllBy*` | Hay **varios** | Devuelve array, falla si hay 0 |

La combinacion incorrecta es `queryBy` esperando que exista: devuelve `null` y
el assert falla con un mensaje confuso. `queryBy` es para afirmar **ausencia**.

```tsx
// MAL: queryBy para algo que debe existir
expect(queryByRole("alert")).toBeInTheDocument();  // siempre falla

// BIEN
expect(screen.getByRole("alert")).toBeInTheDocument();

// BIEN: para afirmar que no esta
expect(screen.queryByRole("alert")).not.toBeInTheDocument();
```

---

## Tabla de queries por rol

| Elemento | Rol | Query tipica |
|---|---|---|
| Boton | `button` | `getByRole("button", { name: /guardar/i })` |
| Enlace | `link` | `getByRole("link", { name: /inicio/i })` |
| Campo de texto | `textbox` | `getByRole("textbox", { name: /correo/i })` |
| Checkbox | `checkbox` | `getByRole("checkbox", { name: /acepto/i })` |
| Radio | `radio` | `getByRole("radio", { name: /tarjeta/i })` |
| Select | `combobox` | `getByRole("combobox", { name: /pais/i })` |
| Menu desplegable | `combobox` o `button` | Segun la implementacion |
| Dialogo | `dialog` | `getByRole("dialog")` |
| Panel expandible | `region` | `getByRole("region", { name: /filtros/i })` |
| Tabla | `table` | `getByRole("table")` |
| Fila | `row` | `getByRole("row", { name: /pedido 1/i })` |
| Celda | `cell` | `getByRole("cell", { name: /100/i })` |
| Columna | `columnheader` | `getByRole("columnheader", { name: /total/i })` |
| Encabezado de pagina | `heading` | `getByRole("heading", { name: /pedidos/i })` |
| Formulario | `form` | `getByRole("form")` |
| Lista | `list` | `getByRole("list")` |
| Item de lista | `listitem` | `getByRole("listitem")` |
| Alerta | `alert` | `getByRole("alert")` |
| Mensaje de estado | `status` | `getByRole("status")` |
| Barra de progreso | `progressbar` | `getByRole("progressbar")` |
| Spinner | `status` | `getByRole("status")` |
| Image | `img` | `getByRole("img", { name: /logo/i })` |

**Todos los roles validos estan en la especificacion ARIA.** La lista completa
es la referencia para elegir: si el elemento no tiene rol, es porque la
accesibilidad tiene un problema, y ese es el hallazgo real.

---

## Nombre accesible: la conexion con la etiqueta

El `{ name: /.../ }` busca por el nombre accesible, que se calcula asi:

1. `aria-label`
2. `aria-labelledby` (el texto del elemento referenciado)
3. El contenido de texto del elemento
4. `title`
5. El `<label>` asociado, si es un control de formulario
6. `alt` de una imagen dentro
7. `placeholder` (ultimo recurso, con advertencia de accesibilidad)

```tsx
// El texto visible es el nombre accesible
<button>Guardar cambios</button>
screen.getByRole("button", { name: /guardar cambios/i });

// Un input con label
<label htmlFor="correo">Correo electronico</label>
<input id="correo" type="email" />
screen.getByRole("textbox", { name: /correo electronico/i });
```

**El nombre accesible se matchea con regex** cuando es texto variable:

```tsx
screen.getByRole("button", { name: /eliminar/i })        // matchea "Eliminar pedido 42"
screen.getByRole("heading", { name: /^pedidos$/i })      // exacto, ignorando mayusculas
```

---

## Cuando no hay rol: `data-testid`

Elementos sin rol semantico natural:

- Un `div` que envuelve un valor de un grafico.
- Un canvas.
- Un input `type="hidden"`.

```tsx
// Aceptable, con justificacion documentada
const grafico = screen.getByTestId("grafico-ventas");
```

**Regla:** `data-testid` es la excepcion. Si la mayoria de los queries del
proyecto son `getByTestId`, el problema no es el test: es que la interfaz no
tiene roles correctos. Arreglar la interfaz mejora accesibilidad y testeo a
la vez.

---

## Alcance: within

Cuando hay varios elementos con el mismo rol, se acota el ambito:

```tsx
import { within } from "@testing-library/react";

const tabla = screen.getByRole("table");
const filas = within(tabla).getAllByRole("row");
expect(filas).toHaveLength(4);

const celdaTotal = within(filas[1]).getByRole("cell", { name: /100/i });
```

Tambien se acota por seccion:

```tsx
const dialogo = screen.getByRole("dialog");
await user.click(within(dialogo).getByRole("button", { name: /confirmar/i }));
```

---

## Debugging: ver el arbol

```tsx
screen.debug();                       // imprime el arbol completo
screen.debug(screen.getByRole("table"));
```

Alternativa cuando `debug()` no alcanza:

```tsx
import { prettyDOM } from "@testing-library/dom";

console.log(prettyDOM(document.body));
```

Para encontrar un elemento por texto en el arbol:

```tsx
screen.getByText(/total a pagar/i);
```

Si hay varios, el error del `getBy` lista todos los que encontro. Ese listado
es la guia para elegir la query correcta.

---

## Errores frecuentes y su causa

| Error | Causa tipica | Correccion |
|---|---|---|
| `Unable to find an accessible element` | Rol o nombre incorrecto | `screen.debug()` y corregir |
| `Found multiple elements` | Query no unica | `getAllBy*` o `within` |
| `Found a label with the text of: X` | Label sin `htmlFor` | Asociar `htmlFor` e `id` |
| Elemento no encontrado por texto | Texto partido en varios nodos | Usar un contenedor con `textContent` |
| `getByRole` no encuentra el boton | Boton deshabilitado todavia | Esperar con `findBy` |
| No encuentra el input | Falta `<label>` | Agregar label o `aria-label` |
| Funciona en local, falla en CI | Estado compartido entre tests | `restoreMocks`, `cleanup` |
