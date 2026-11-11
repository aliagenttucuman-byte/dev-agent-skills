# Estado de servidor, URL y cliente

Como separar los tres tipos de estado sin duplicarlos ni desincronizarlos.

---

## Las tres fuentes, una sola verdad

El error clasico de una app React con estado duplicado: el filtro esta en la
URL, en un store local y en el estado del componente. Las tres se desincronizan
y nadie sabe cual manda.

La regla: **cada dato tiene exactamente una fuente de verdad.**

| Dato | Fuente | Se lee con | Se escribe con |
|---|---|---|---|
| Producto en pantalla | Cache de fetching | `useQuery` | Invalidacion |
| Filtro activo | URL | `useSearchParams` | `setSearchParams` |
| Panel abierto | Estado local | `useState` | `setState` |
| Usuario logueado | Store global | `useUser()` | `login()` / `logout()` |

Si un dato aparece en dos filas de esta tabla, hay un problema.

---

## Estado de servidor: React Query

```ts
// shared/api/queries.ts
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

interface Pedido {
  id: string;
  total: number;
  estado: "pendiente" | "pagado";
}

export function usePedido(id: string) {
  return useQuery({
    queryKey: ["pedido", id],
    queryFn: async ({ signal }) => {
      const respuesta = await fetch(`/api/pedidos/${id}`, { signal });
      if (!respuesta.ok) {
        throw new Error(`no se pudo cargar el pedido ${id}`);
      }
      return (await respuesta.json()) as Pedido;
    },
    staleTime: 30_000,
  });
}

export function useConfirmarPedido() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const respuesta = await fetch(`/api/pedidos/${id}/confirmar`, {
        method: "POST",
      });
      if (!respuesta.ok) throw new Error("no se pudo confirmar");
      return respuesta.json();
    },
    onSuccess: (_datos, id) => {
      // Invalidacion: la cache se marca como obsoleta y se vuelve a pedir.
      cache.invalidateQueries({ queryKey: ["pedido", id] });
      cache.invalidateQueries({ queryKey: ["pedidos"] });
    },
  });
}
```

**Reglas:**

- El `queryKey` es la identidad del dato. Es un array: `["pedido", id]`, no
  un string concatenado. La estructura permite invalidacion por prefijo.
- `queryFn` recibe `signal`: React Query cancela la peticion si el componente
  se desmonta o la query se invalida. Sin `signal`, la peticion sigue viva.
- `staleTime` define cuando los datos se consideran viejos. Sin esto, cada
  montaje de componente dispara una peticion.
- Las mutaciones invalidan la cache. **No se actualiza la cache a mano** salvo
  que se conozca exactamente la forma de la respuesta del servidor.
- Los errores de `useQuery` no se tragan: se renderizan con un mensaje.

### Invalidacion vs actualizacion manual

```ts
// BIEN: invalidar, el servidor es la verdad
cache.invalidateQueries({ queryKey: ["pedido", id] });

// BIEN: actualizacion optimista, con rollback
cache.setQueryData(["pedido", id], (viejo) => ({ ...viejo, estado: "pagado" }));

// MAL: mutar el array de la cache a mano
cache.getQueryData(["pedidos"]).push(nuevoPedido);   // no dispara re-render
```

La actualizacion optimista vale cuando el resultado es casi seguro y el
feedback debe ser inmediato. Siempre con rollback:

```ts
useMutation({
  mutationFn: renombrarPedido,
  onMutate: async (variables) => {
    await cache.cancelQueries({ queryKey: ["pedido", variables.id] });
    const previo = cache.getQueryData(["pedido", variables.id]);
    cache.setQueryData(["pedido", variables.id], (viejo) => ({
      ...viejo,
      nombre: variables.nombre,
    }));
    return { previo };
  },
  onError: (_error, variables, contexto) => {
    // Rollback: se restaura el estado previo.
    cache.setQueryData(["pedido", variables.id], contexto.previo);
  },
});
```

---

## Estado de URL

```tsx
import { useSearchParams } from "react-router-dom";

const ORDENES_POR_DEFECTO = ["fecha", "total"] as const;

function useOrdenamiento() {
  const [params, setParams] = useSearchParams();

  const orden = (params.get("orden") ?? ORDENES_POR_DEFECTO[0]) as
    | (typeof ORDENES_POR_DEFECTO)[number]
    | "asc"
    | "desc";

  function cambiarOrden(nuevo: string) {
    const nuevos = new URLSearchParams(params);
    nuevos.set("orden", nuevo);
    setParams(nuevos, { replace: true });   // replace evita historial infinito
  }

  return { orden, cambiarOrden };
}
```

**Que va en la URL:**

| Dato | Por que |
|---|---|
| Filtros y busqueda | El usuario puede compartir el link |
| Paginacion | El refresh no pierde la pagina |
| Tab o vista activa | El back del navegador funciona |
| Orden de columnas | Es parte de la vista |
| Vista de lista o grilla | Preferencia de visualizacion |

**Que NO va en la URL:**

- Estado efimero (un tooltip abierto).
- Datos que el usuario no comparte ni recuerda (el texto de un campo sin
  submit).
- Objetos completos: la URL lleva identificadores, no payloads.

**Reglas:**

- `setParams` con `replace: true` para cambios que no merecen entrada en el
  historial (ordenar, cambiar de tab).
- Sin `replace` para navegacion con sentido (ir a la pagina 2).
- La URL se parsea con defaults: un parametro ausente o invalido usa el
  default, no rompe.

```tsx
const pagina = Math.max(1, Number(params.get("pagina") ?? "1"));
```

---

## Estado local: `useState` y `useReducer`

```tsx
const [estado, setEstado] = useState<"idle" | "loading" | "error">("idle");
```

**Cuando `useReducer`:**

- La transicion depende del estado anterior de forma no trivial.
- Hay tres o mas estados relacionados.
- El estado se actualiza desde varios lugares.

```tsx
type Estado =
  | { fase: "inactivo" }
  | { fase: "cargando" }
  | { fase: "listo"; datos: Pedido[] }
  | { fase: "error"; mensaje: string };

type Accion =
  | { tipo: "cargar" }
  | { tipo: "exito"; datos: Pedido[] }
  | { tipo: "fallo"; mensaje: string };

function reducer(estado: Estado, accion: Accion): Estado {
  switch (accion.tipo) {
    case "cargar":
      return { fase: "cargando" };
    case "exito":
      return { fase: "listo", datos: accion.datos };
    case "fallo":
      return { fase: "error", mensaje: accion.mensaje };
  }
}
```

**La regla del `useState` con objeto:** no se muta. Se reemplaza.

```tsx
// MAL: mutacion que no dispara re-render
setFormulario({ ...formulario, nombre: "x" });   // ok si no hay dependencia
formulario.nombre = "x";                          // MAL: no re-renderiza

// BIEN: reemplazo
setFormulario((previo) => ({ ...previo, nombre: "x" }));
```

Cuando el estado depende del anterior, se usa la forma funcional. Es la unica
segura con actualizaciones asincronas.

---

## Estado global: contexto con disciplina

```tsx
// shared/state/SesionContext.tsx
interface Sesion {
  usuario: Usuario | null;
  cargando: boolean;
}

interface ValorContexto extends Sesion {
  iniciarSesion: (usuario: Usuario) => void;
  cerrarSesion: () => void;
}

const Contexto = createContext<ValorContexto | null>(null);

export function ProveedorSesion({ children }: { children: React.ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);

  // useEffect de carga inicial: es una excepcion justificada.
  // El resto del estado de servidor va en React Query.
  useEffect(() => {
    let vigente = true;
    obtenerSesion()
      .then((datos) => {
        if (vigente) setUsuario(datos.usuario);
      })
      .finally(() => {
        if (vigente) setCargando(false);
      });
    return () => {
      vigente = false;   // evita setState tras desmontar
    };
  }, []);

  const valor = useMemo(
    () => ({ usuario, cargando, iniciarSesion: setUsuario, cerrarSesion: () => setUsuario(null) }),
    [usuario, cargando],
  );

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}
```

**Reglas de contexto:**

- Un contexto por dominio, no un contexto global gigante. `SesionContext` y
  `TemaContext` separados: un cambio de tema no debe re-renderizar todo.
- El `value` va en `useMemo`. Sin eso, cada render crea un objeto nuevo y
  todos los consumidores re-renderizan.
- `createContext(null)` y un hook que lance si no hay provider: el error
  aparece claro en vez de `undefined is not an object`.
- El estado de servidor **no** va en contexto. Va en React Query, que ya
  resuelve cache, revalidacion y deduplicacion.

```tsx
export function useSesion(): ValorContexto {
  const valor = useContext(Contexto);
  if (valor === null) {
    throw new Error("useSesion debe usarse dentro de ProveedorSesion");
  }
  return valor;
}
```

---

## Server State vs Client State: tabla de decision

| Pregunta | Si | No |
|---|---|---|
| Viene de una API? | Estado de servidor | |
| Se puede re-fetchear? | Estado de servidor | |
| Cambia con cada tecla? | Estado local | |
| Se comparte entre rutas? | Store global | |
| El usuario lo puede compartir por link? | URL | |
| Sobrevive al refresh? | URL o servidor | Estado local |

---

## Anti-patrones de estado

| Anti-patron | Consecuencia |
|---|---|
| Mismo dato en URL y en store | Se desincronizan al navegar |
| `useEffect` con fetch manual | Sin cache, con race condition |
| Contexto unico con todo | Re-render en cascada |
| `value` sin `useMemo` | Re-render de todo el arbol |
| Cache actualizada a mano sin invalidar | Datos viejos |
| Mutacion de `useState` | No re-renderiza |
| `useState` con objeto y logica complexa | Bugs sutiles |
| Reset de formulario con `key` innecesario | Se pierde el foco |
| Guardar todo en localStorage | Estado obsoleto sin invalidacion |
