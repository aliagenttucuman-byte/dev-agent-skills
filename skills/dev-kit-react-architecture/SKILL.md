---
name: dev-kit-react-architecture
description: "Arquitectura de aplicaciones React a escala: organizacion por features, composicion sobre configuracion, estado de servidor contra estado de cliente, Server Components frente a SPA, routing y code splitting, gestion de errores y de carga, y reglas para decidir donde vive cada pieza. CARGAR cuando hay que estructurar una aplicacion React, decidir donde vive un estado, elegir entre Server Components y client components, dividir el bundle o definir la estructura de carpetas."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [react, arquitectura, feature-based, estado, routing, code-splitting, error-boundary]
    category: software-development
    related_skills: [dev-kit-frontend-stack, dev-kit-react-testing, dev-kit-backend-stack, dev-kit-code-quality]
---

# Dev Kit - React Architecture

> **Trigger:** "estructurar una app React", "donde va este estado", "Server
> Components o SPA", "dividir el bundle", "organizar las carpetas", "state
> management", "error boundary", "code splitting". Cargar esta skill ANTES de
> crear la estructura de carpetas de una aplicacion.

## Que es esto

El contrato de como se organiza una aplicacion React para que crezca sin
convertirse en un nido de acoplamiento. No es un curso de React: es el
conjunto de decisiones que se toman una vez al inicio y que determinan cuan
facil va a ser cambiar el codigo despues.

Las tres preguntas que esta skill responde:

1. **Donde vive cada pieza de codigo?** (organizacion)
2. **Donde vive cada pieza de estado?** (separacion de estados)
3. **Que corre en el servidor y que corre en el navegador?** (boundary)

## Las tres decisiones fundacionales

1. **Se organiza por feature, no por tipo.** `features/checkout/` con sus
   componentes, hooks y tests juntos, no `components/`, `hooks/`, `utils/`
   apaisados donde hay que recorrer 40 carpetas para cambiar un flujo.
2. **El estado de servidor no es estado de cliente.** La respuesta de una API
   no vive en un store: vive en la cache de fetching y se invalida.
3. **La composicion gana a la configuracion.** Un componente con 15 props
   configurables es un componente que hay que entender entero para usar.

## Organizacion por feature

```
src/
├── app/                     # Composicion de la app: rutas, providers, layout
│   ├── router.tsx
│   ├── providers.tsx
│   └── layout/
│       ├── AppShell.tsx
│       └── AppShell.test.tsx
│
├── features/                # Dominios de negocio. Cada uno autocontenido
│   ├── checkout/
│   │   ├── components/      # Solo de este feature
│   │   ├── hooks/
│   │   ├── api/             # Llamadas a la API de este feature
│   │   ├── schemas.ts       # Tipos y validacion
│   │   ├── routes.tsx       # Rutas de este feature
│   │   └── index.ts         # Superficie publica del feature
│   └── catalogo/
│
├── shared/                  # Codigo compartido entre features
│   ├── ui/                  # Componentes de presentacion sin logica de negocio
│   ├── lib/                 # Utilidades puras
│   ├── hooks/               # Hooks transversales
│   └── types/
│
└── main.tsx                 # Punto de entrada. Minimo posible.
```

**Las tres reglas de esta estructura:**

1. **`shared/` no conoce `features/`.** La dependencia va en una sola
   direccion: las features importan de `shared`, nunca al reves. Si
   `shared/ui/Button.tsx` importa de `features/checkout`, el Button ya no es
   compartido: es un componente de checkout con otro nombre.
2. **`features/` no se importan entre si directamente.** Si `catalogo` necesita
   algo de `checkout`, ese algo va a `shared/` o se expone por el `index.ts` del
   feature. La importacion cruzada entre features es la que crea el acoplamiento
   imposible de deshacer.
3. **`app/` no tiene logica de negocio.** Solo composicion: rutas, providers,
   layout. Si hay un `if` de negocio en `app/`, ese `if` pertenece a un
   feature.

**El `index.ts` de un feature es su superficie publica:**

```ts
// features/checkout/index.ts
export { CheckoutPage } from "./routes";
export { useCart } from "./hooks/useCart";
export type { CartItem } from "./schemas";
```

Quien importa de otro feature importa de aca, no de un archivo interno. Eso
permite mover archivos internos sin romper 40 imports.

## Separacion del estado

Hay cuatro tipos de estado, y cada uno tiene un lugar distinto:

| Tipo | Ejemplo | Donde vive | Como se comparte |
|---|---|---|---|
| Estado de servidor | Lista de productos | Cache de fetching | React Query / SWR |
| Estado de URL | Filtro activo, tab, paginacion | La URL | `useSearchParams` |
| Estado de cliente | Panel abierto, hovered | Local del componente | `useState` |
| Estado global | Usuario autenticado, tema, preferencias | Contexto | Context + store |

**El orden de decision, de mas local a mas global:**

1. **Puede vivir en la URL?** Si el usuario puede compartir el link o
   recargar y espera el mismo resultado, va en la URL. Filtros, paginacion,
   tab, vista.
2. **Es de servidor?** Si viene de una API y se puede re-fetchear, va en la
   cache de fetching. No en un `useState` con un `useEffect` que hace el
   fetch.
3. **Lo usa un solo componente?** `useState` local.
4. **Lo usan dos componentes hermanos?** Subir al padre comun.
5. **Lo usa toda la app?** Contexto. Y si es mucho, un store.

**El anti-patron mas caro:**

```tsx
// MAL: estado de servidor en estado local
function ListaProductos() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    fetch("/api/productos")
      .then((r) => r.json())
      .then(setProductos)
      .finally(() => setCargando(false));
  }, []);

  // No hay cache, no hay revalidacion, no hay deduplicacion,
  // hay race condition si el componente se monta dos veces.
}
```

Con React Query:

```tsx
// BIEN: estado de servidor con cache, revalidacion y deduplicacion
import { useQuery } from "@tanstack/react-query";

function ListaProductos() {
  const { data, isPending, error } = useQuery({
    queryKey: ["productos"],
    queryFn: async ({ signal }) => {
      const respuesta = await fetch("/api/productos", { signal });
      if (!respuesta.ok) throw new Error("no se pudo cargar");
      return respuesta.json() as Promise<Producto[]>;
    },
  });

  if (isPending) return <Spinner />;
  if (error) return <MensajeError error={error} />;
  return <Tabla productos={data} />;
}
```

**El estado de URL, que es el mas subestimado:**

```tsx
import { useSearchParams } from "react-router-dom";

function FiltrosCatalogo() {
  const [params, setParams] = useSearchParams();
  const categoria = params.get("categoria") ?? "todos";

  function cambiarCategoria(nueva: string) {
    const nuevos = new URLSearchParams(params);
    nuevos.set("categoria", nueva);
    setParams(nuevos);
  }

  // La URL ahora es compartible y sobrevive al refresh.
}
```

## Composicion sobre configuracion

```tsx
// MAL: un componente con 15 props, 8 de los cuales son de layout
function Panel({
  titulo,
  subtitulo,
  icono,
  color,
  tamano,
  conBorde,
  conSombra,
  padding,
  alineado,
  children,
  ...resto
}: PanelProps) {
  // 30 lineas de ternarios para decidir clases
}
```

```tsx
// BIEN: componentes compuestos donde cada pieza decide lo suyo
function Panel({ children }: { children: React.ReactNode }) {
  return <section className="panel">{children}</section>;
}

function Panel.Header({ children }: { children: React.ReactNode }) {
  return <header className="panel-header">{children}</header>;
}

function Panel.Title({ children }: { children: React.ReactNode }) {
  return <h2 className="panel-title">{children}</h2>;
}

function Panel.Body({ children }: { children: React.ReactNode }) {
  return <div className="panel-body">{children}</div>;
}

// Uso
<Panel>
  <Panel.Header>
    <Panel.Title>Pedidos del dia</Panel.Title>
  </Panel.Header>
  <Panel.Body>
    <TablaPedidos />
  </Panel.Body>
</Panel>
```

**Regla:** los componentes de `shared/ui` reciben `className` para permitir
extender, pero no reciben props de comportamiento. Un componente de UI no
llama a la API ni lee del store.

## Server Components frente a SPA

Dos modelos distintos, con criterios claros:

| Criterio | Server Components (RSC) | SPA client-side |
|---|---|---|
| Envoltura | Next.js App Router | Vite + React Router |
| Donde corre el JS | Servidor por defecto | Cliente |
| Secretos del servidor | Si, nunca llegan al bundle | No aplica |
| Interactividad | Componentes `"use client"` | Todo en el cliente |
| Bundle inicial | Chico | Incluye todo lo importado |
| SEO | Renderizado en servidor | Requiere SSR extra |
| Datos | Fetch en el servidor, sin waterfall | Fetch en el cliente |

**La decision:**

| El proyecto tiene... | Modelo |
|---|---|
| Contenido SEO-critical, panel con sesion, marketing + app | RSC |
| App interna, panel, backoffice, dashboard | SPA |
| Embeds, widgets, micro-frontends | SPA |
| Sitios publicos de contenido | RSC o generador estatico |

**La regla del boundary:** un componente con `"use client"` se convierte en un
boundary. Todo lo que importa pasa al bundle del cliente. Cuantos menos
boundaries, mejor.

```tsx
// Server Component: solo en el server, los secretos no salen
// features/checkout/routes.tsx
export default async function CheckoutPage() {
  const sesion = await obtenerSesion();       // usa cookies del servidor
  const total = await calcularTotal(sesion);   // logica de negocio en servidor

  return (
    <CheckoutForm total={total}>
      <BotonPagar />                            {/* client component */}
    </CheckoutForm>
  );
}
```

```tsx
// Client Component: interactividad
"use client";

export function BotonPagar() {
  const [estado, setEstado] = useState<"idle" | "procesando">("idle");

  async function pagar() {
    setEstado("procesando");
    await iniciarPago();
    setEstado("idle");
  }

  return (
    <button onClick={pagar} disabled={estado === "procesando"}>
      {estado === "procesando" ? "Procesando..." : "Pagar"}
    </button>
  );
}
```

**En SPA, el equivalente de "estado de servidor" es la cache de fetching**, y
el equivalente de "Server Component" es "no renderizar ese componente en el
cliente hasta que haya datos".

## Routing y code splitting

```tsx
// app/router.tsx
import { lazy, Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";

const CheckoutPage = lazy(() => import("@/features/checkout/routes"));

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <CatalogoPage /> },
      {
        path: "checkout",
        element: (
          <Suspense fallback={<PantallaCarga />}>
            <CheckoutPage />
          </Suspense>
        ),
      },
    ],
  },
]);
```

**Reglas de code splitting:**

- El split es **por ruta**, no por componente suelto. Un componente lazy
  dentro de una ruta que ya se cargo no aporta: el bundle de la ruta se
  descarga entero.
- `React.lazy` + `Suspense` con un fallback real.
- Las rutas que se necesitan en el primer render **no** se hacen lazy: el
  layout y la ruta inicial se descargan siempre.
- Los modulos pesados (un editor, un mapa, un grafico) se cargan bajo demanda
  con `import()` dinamico en el punto de uso:

```tsx
const Mapa = lazy(() => import("./MapaPesado"));

function TarjetaUbicacion() {
  return (
    <Suspense fallback={<MapaPlaceholder />}>
      <Mapa />
    </Suspense>
  );
}
```

**El presupuesto de bundle se mide, no se estima:**

```ts
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
    chunkSizeWarningLimit: 300,
  },
});
```

Se verifica el resultado con un analisis de bundle en CI. Un presupuesto sin
medir es una intencion.

## Manejo de errores y de carga

Tres estados, siempre los tres:

```tsx
import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback: ReactNode;
}

interface State {
  tieneError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { tieneError: false };

  static getDerivedStateFromError(): State {
    return { tieneError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    logger.error("error en el arbol de componentes", { error, info });
  }

  render(): ReactNode {
    if (this.state.tieneError) return this.props.fallback;
    return this.props.children;
  }
}
```

**Reglas:**

- El `ErrorBoundary` va en el **layout**, no en cada pantalla. Un error en una
  pantalla no debe tumbar la app entera.
- El fallback es un mensaje accionable, no "algo salio mal".
- `componentDidCatch` loguea con contexto. Sin log, el error se pierde.
- Los errores de fetching se manejan en la capa de datos (por ejemplo con
  `errorElement` del router o el `onError` de React Query), no con try/catch
  en cada componente.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| Carpetas por tipo (`components/`, `hooks/`) | Hay que recorrer 40 carpetas | Organizar por feature |
| `shared/` importando de `features/` | Dependencia circular | La flecha va en una sola direccion |
| `features/` importando de `features/` | Acoplamiento imposible de deshacer | Superficie publica en `index.ts` |
| `useEffect` para fetch a mano | Sin cache, con race condition | React Query / SWR |
| Estado de filtro en `useState` | Se pierde al recargar | En la URL |
| Componente con 15 props de config | Nadie lo entiende | Composicion |
| `useContext` para todo | Re-render en cascada | Contexto dividido por dominio |
| Lazy por componente suelto | No reduce el bundle de la ruta | Lazy por ruta |
| `ErrorBoundary` en cada pantalla | Codigo repetido | En el layout |
| `key={index}` en listas | Estado mal asociado al item | `key` con id estable |
| Estado duplicado entre URL y store | Se desincronizan | Una sola fuente |
| `any` en props de componentes | Los errores aparecen en runtime | `unknown` + validacion |
| Feature nueva que importa de otra feature | Acoplamiento | Superficie publica o `shared/` |
| Logica de negocio en `app/` | `app/` no escala | Logica en el feature |

## Referencias

### Skills relacionadas

- `dev-kit-frontend-stack` - convenciones de componentes, estado y estilos.
- `dev-kit-react-testing` - como testear cada capa de esta arquitectura.
- `dev-kit-backend-stack` - contrato de la API que consume el frontend.
- `dev-kit-code-quality` - tipos, lint y gates del frontend.

### Archivos de esta skill

- `references/estructura-y-carpetas.md` - arbol completo con reglas de dependencia.
- `references/estado-y-servidor.md` - estado de servidor, URL y cliente en detalle.
- `references/performance-y-bundle.md` - code splitting, budgets y metricas.
