# Performance y bundle

Como medir el bundle y decidir que se divide.

---

## Primero medir

Sin medicion, cualquier discusion sobre performance es opinion.

```bash
# Analisis del build
npm run build

# Ver el detalle de los chunks
npx vite-bundle-visualizer
```

El reporte tipico dice:

```
dist/assets/index-abc123.js       187 kB
dist/assets/checkout-def456.js     42 kB
dist/assets/vendor-ghi789.js      312 kB
dist/assets/chart-jkl012.js       95 kB   <- se carga aunque no se use
```

---

## Los cuatro vectores de peso

| Vector | Ejemplo | Como se mide |
|---|---|---|
| Bundle inicial | Todo lo que se descarga antes de interactuar | Peso del chunk de entrada |
| Dependencias pesadas | Un editor, un mapa, un grafico | Lista de dependencias |
| Re-renders | Contexto que cambia de valor | React DevTools Profiler |
| Requests | Waterfalls de fetching | Waterfall del Network panel |

El mas comun en React moderno no es el bundle: es el **waterfall de red**. Un
componente pide datos, cuando llegan pide otros. Cada salto es un round trip.

---

## Waterfalls: el problema dominante

```tsx
// MAL: tres round trips en serie
function PaginaPedido({ id }: { id: string }) {
  const { data: pedido } = useQuery({ queryKey: ["pedido", id], queryFn: () => obtenerPedido(id) });
  const { data: cliente } = useQuery({ queryKey: ["cliente", pedido?.clienteId], queryFn: ..., enabled: !!pedido?.clienteId });
  const { data: envios } = useQuery({ queryKey: ["envios", id], queryFn: ..., enabled: !!pedido });
  // ...
}
```

Cada query espera al anterior. Tres round trips en serie.

**Correccion 1: traer lo necesario en una respuesta.**

La API devuelve el pedido con su cliente y envios incluidos. Un round trip.

**Correccion 2: queries en paralelo cuando son independientes.**

```tsx
// BIEN: el cliente no depende del pedido si se conoce el id
const { data: cliente } = useQuery({
  queryKey: ["cliente", clienteId],
  queryFn: () => obtenerCliente(clienteId),
});
```

**Correccion 3: prefetch de la siguiente navegacion.**

```tsx
function BotonVerPedido({ id }: { id: string }) {
  const cache = useQueryClient();

  function alMouseEnter() {
    // Precarga la ruta siguiente mientras el usuario Todavia no clickea.
    void cache.prefetchQuery({ queryKey: ["pedido", id], queryFn: () => obtenerPedido(id) });
  }

  return (
    <Link to={`/pedidos/${id}`} onMouseEnter={alMouseEnter}>
      Ver pedido
    </Link>
  );
}
```

---

## Code splitting por ruta

```tsx
import { lazy, Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";

const CatalogoPage = lazy(() => import("@/features/catalogo/routes"));
const CheckoutPage = lazy(() => import("@/features/checkout/routes"));
const AdminPage = lazy(() => import("@/features/admin/routes"));

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <CatalogoPage /> },
      {
        path: "checkout",
        element: (
          <Suspense fallback={<Cargando />}>
            <CheckoutPage />
          </Suspense>
        ),
      },
      {
        path: "admin",
        element: (
          <Suspense fallback={<Cargando />}>
            <AdminPage />
          </Suspense>
        ),
      },
    ],
  },
]);
```

**El layout (`AppShell`) no es lazy.** Se descarga siempre: es el armazon de la
app y lazyarlo agrega un salto visible en cada navegacion.

**Fallback real.** Un spinner es un fallback pobre. Un esqueleto que imite la
forma del contenido reduce el salto perceptual:

```tsx
function EsqueletoTabla() {
  return (
    <div aria-busy="true" aria-label="Cargando">
      {Array.from({ length: 5 }).map((_, indice) => (
        <div key={indice} className="fila-esqueleto" />
      ))}
    </div>
  );
}
```

---

## Dependencias pesadas: carga bajo demanda

```tsx
const Editor = lazy(() => import("@/features/editor/Editor"));

function CampoDescripcion() {
  return (
    <Suspense fallback={<AreaTextoSimple />}>
      <Editor valor={descripcion} onChange={setDescripcion} />
    </Suspense>
  );
}
```

**Regla:** un componente pesado se carga cuando el usuario llega a la zona que
lo necesita, no al cargar la app.

**Alternativa sin React.lazy:** import dinamico con estado.

```tsx
const [Modulo, setModulo] = useState<React.ComponentType | null>(null);

useEffect(() => {
  void import("./ModuloPesado").then((m) => setModulo(() => m.default));
}, []);
```

---

## Presupuesto de bundle

```ts
// vite.config.ts
export default defineConfig({
  build: {
    chunkSizeWarningLimit: 300,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            if (id.includes("react")) return "vendor-react";
            if (id.includes("@tanstack")) return "vendor-data";
            return "vendor";
          }
        },
      },
    },
  },
});
```

**El presupuesto se verifica en CI, no en el build local:**

```yaml
- name: bundle budget
  run: |
    npx vite-bundle-visualizer --json > stats.json
    node scripts/check-budget.mjs stats.json
```

```js
// scripts/check-budget.mjs
import { readFile } from "node:fs/promises";

const LIMITE_INICIAL_KB = 250;

const stats = JSON.parse(await readFile("stats.json", "utf8"));
const inicial = stats.find((c) => c.name === "index" || c.entryName === "index");

if (!inicial) {
  console.error("No se encontro el chunk inicial");
  process.exit(1);
}

const peso = inicial.size / 1024;
console.log(`Chunk inicial: ${peso.toFixed(1)} kB`);

if (peso > LIMITE_INICIAL_KB) {
  console.error(`Presupuesto excedido: ${peso.toFixed(1)} kB > ${LIMITE_INICIAL_KB} kB`);
  process.exit(1);
}
```

Sin este paso, el presupuesto es una intencion que se pierde en el primer
`npm install` de una dependencia grande.

---

## Re-renders: causas y soluciones

| Causa | Sintoma | Correccion |
|---|---|---|
| Contexto con valor nuevo | Todo re-renderiza | `useMemo` en el value, dividir contextos |
| Props nuevas cada render | Hijos re-renderizan | `useCallback`, `memo` |
| Lista sin `key` estable | Todo se re-renderiza | `key={id}` |
| Estado en el padre | Todos los hijos re-renderizan | Subir el estado al hijo |
| Funcion recreada en prop | Hijos re-renderizan | `useCallback` |
| `useEffect` sin dependencias | Loop de renders | Dependencias correctas |

**Antes de optimizar, medir.** React DevTools Profiler muestra que componente
re-renderiza y por que. Optimizar sin medir es adivinar.

**`memo` tiene costo.** Compara props shallow y agrega una comparacion en
cada render. Solo vale cuando el componente es caro o el padre re-renderiza
muy seguido.

```tsx
// Solo tiene sentido si el render es costoso
const FilaProducto = memo(function FilaProducto({ producto }: Props) {
  return <tr>{/* render caro */}</tr>;
});
```

**`useMemo` y `useCallback` tambien tienen costo.** No envolver todo:
primero medir, y memoizar lo que se demostro caro.

---

## Metricas que se siguen

| Metrica | Objetivo tipico | Como se mide |
|---|---|---|
| Chunk inicial | < 250 kB gzipped | Analisis de bundle en CI |
| LCP | < 2.5 s | Lighthouse CI |
| CLS | < 0.1 | Lighthouse CI |
| INP | < 200 ms | Lighthouse CI / RUM |
| Requests en cascada | 0 avoidable | Waterfall del Network |
| Re-renders por interaccion | Estable | React DevTools Profiler |

```yaml
- name: lighthouse
  run: |
    npx @lhci/cli autorun \
      --collect.url=http://localhost:4173 \
      --assert.assertions.largestContentfulPaint=2500 \
      --assert.assertions.cumulativeLayoutShift=0.1
```

---

## Checklist de performance

- [ ] El bundle inicial esta medido y bajo presupuesto
- [ ] El presupuesto se verifica en CI
- [ ] Las rutas pesadas son lazy
- [ ] Las dependencias pesadas se cargan bajo demanda
- [ ] No hay waterfalls de fetching evitables
- [ ] Las listas tienen `key` estable
- [ ] Los contextos tienen `value` memoizado
- [ ] `memo` y `useMemo` se usan con medicion, no por defecto
- [ ] Las metricas de Web Vitals se miden en CI
