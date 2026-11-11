---
name: dev-kit-frontend-stack
description: "Convenciones del frontend en React con TypeScript y Vite. Arbol de componentes, estrategia de estado, data fetching, formularios, estilos, accesibilidad, performance y code splitting. CARGAR cuando hay que crear o revisar una interfaz, definir la jerarquia de componentes o decidir donde vive cada estado."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [frontend, react, typescript, vite, accesibilidad]
    category: software-development
    related_skills: [dev-kit-backend-stack, dev-kit-code-quality, dev-kit-testing, dev-kit-review]
---

# Dev Kit - Stack Frontend

> **Trigger:** "crear una interfaz", "arbol de componentes", "donde guardo este
> estado", "la pantalla va lenta", "code splitting", "accesibilidad de la
> pantalla". Cargar esta skill ANTES de escribir el primer componente.

## Que es esto

El contrato de como se construye el frontend. El default es React 18 con
TypeScript estricto y Vite como bundler. Cuatro decisiones lo sostienen:

1. **El componente no decide, muestra.** La logica de negocio vive en el
   servidor o en una capa de hooks; el componente traduce estado a vista.
2. **El estado tiene una sola fuente de verdad.** Un dato del servidor no se
   copia a `useState`.
3. **La accesibilidad no es un extra.** Semantica nativa, foco visible y
   teclado funcionando son parte del criterio de aceptacion.
4. **El bundle se divide por ruta.** Quien no entra a una pantalla no descarga
   el codigo de esa pantalla.

## Las tres capas de la interfaz

| Capa | Carpeta | Responsabilidad | Puede importar de |
|---|---|---|---|
| Pagina | `app/routes/` | Ruta, layout, carga inicial, error de ruta | features, components, hooks |
| Feature | `features/` | Todo lo de un dominio: estado, hooks, subcomponentes | components, lib |
| Componente | `components/` | Presentacion reusable, sin logica de negocio | ui, lib |

La regla de dependencia apunta hacia adentro: `routes -> features -> components`.
Un componente presentacional nunca importa una feature. El arbol completo esta en
`templates/component-tree.md`.

## Workflow

| Paso | Que hace | Artefacto | Gate |
|---|---|---|---|
| 1. Ubicar | Decide en que capa vive la funcionalidad | carpeta asignada | La capa no depende hacia afuera |
| 2. Modelar | Define tipos y forma del dato | tipo de dominio | Sin `any` implicito |
| 3. Estados | Clasifica cada dato: servidor, URL, cliente o formulario | tabla de estados | Cada dato tiene una sola fuente |
| 4. Construir | Escribe el componente y sus hooks | componente | Sin fetch dentro del render |
| 5. Verificar | Corre lint, tipos, tests y accesibilidad | reporte | Los cuatro verdes |

### Paso 1 - Decidir la capa antes de escribir

| Si la funcionalidad es... | Va en |
|---|---|
| Una ruta con su layout y su carga inicial | `app/routes/` |
| Todo lo que pertenece a un dominio de negocio | `features/<dominio>/` |
| Un control presentacional que se usa en varias features | `components/` |
| Un primitivo visual sin logica (boton, input, dialogo) | `components/ui/` |
| Logica transversal (formateo de fechas, cliente HTTP) | `lib/` |

**Regla:** si un componente importa de dos features distintas, no es un
componente: es un arbol de componentes mal partido.

### Paso 2 - Tipos antes que JSX

El tipo se define en el borde y se propaga. Los tipos de dominio no viven en el
archivo del componente.

```ts
// features/orders/types.ts
export interface Order {
  readonly id: string
  readonly customerId: string
  readonly status: "pending" | "confirmed" | "shipped" | "cancelled"
  readonly total: number
  readonly createdAt: string
}

// features/orders/useOrders.ts: la clave incluye todos los filtros
export function useOrders(filters: OrderFilters) {
  return useQuery({
    queryKey: ["orders", filters],
    queryFn: () => ordersApi.list(filters),
    staleTime: 30_000,
  });
}
```

| Regla | Motivo |
|---|---|
| `strict: true` y `noUncheckedIndexedAccess: true` | El compilador encuentra el acceso invalido |
| Tipos de dominio en `types.ts`, no en el `.tsx` | Se reutilizan y se testean sueltos |
| `readonly` en los tipos de respuesta | Nadie muta datos que son de otro |
| Estados como union de strings, no numeros magicos | El estado de la API es un string |
| Sin `any` | `unknown` obliga a estrechar antes de usar |

### Paso 3 - Clasificar el estado: la parte que mas falla

Cinco tipos de estado, cinco lugares. La pregunta de decision es una sola:
**¿de donde viene el dato?**

| Tipo de estado | Ejemplos | Donde vive | Como se accede |
|---|---|---|---|
| **Server state** | pedidos, perfil, permisos | cache del servidor | `useQuery` / `useMutation` |
| **URL state** | tab activa, pagina, filtro, orden | la URL | `useSearchParams` |
| **Form state** | valores del formulario, errores por campo | libreria de formularios | `useForm` |
| **Client state** | modal abierto, panel expandido | `useState` local | props hacia abajo |
| **Global UI state** | tema, idioma, densidad | contexto | `useContext` |

Las cuatro reglas que resuelven el 90% de los problemas:

1. **Si el estado puede ir en la URL, va en la URL.** El boton de atras, el
   enlace compartible y el refresh dejan de ser casos especiales.
2. **Si el dato viene del servidor, no se copia a `useState`.** Copiar rompe la
   invalidacion: la pantalla muestra un valor viejo y nadie sabe por que.
3. **Si solo lo usa un subarbol, vive en el subarbol.** El contexto global se
   paga en cada render de la app.
4. **Si se puede derivar, se deriva.** `const total = items.reduce(...)` en
   render es mas barato y mas correcto que un estado sincronizado a mano.

```tsx
// Bien: el filtro vive en la URL, el servidor es la fuente
export function OrdersRoute() {
  const [params, setParams] = useSearchParams();
  const status = params.get("status") as Order["status"] | null;
  const { data, isPending, isError } = useOrders({ status: status ?? undefined });

  if (isPending) return <OrdersSkeleton />;
  if (isError) return <ErrorState onRetry={...} />;
  if (data.length === 0) return <EmptyState />;
  return <OrdersTable orders={data} onFilterChange={...} />;
}
```

**Mal:** el mismo dato guardado en la URL, en un contexto y en un `useState`.
Tres fuentes de verdad, tres valores distintos, un bug garantizado.

### Paso 4 - Data fetching: cuatro estados, no dos

Una pantalla tiene cuatro estados, no dos. Los tres ultimos se olvidan y
producen la experiencia que el equipo llama "la app se rompe".

| Estado | Condicion | Que se muestra |
|---|---|---|
| Carga | `isPending` | esqueleto con la forma del contenido |
| Error | `isError` | mensaje accionable y boton de reintento |
| Vacio | `data.length === 0` | explicacion y accion primaria |
| Exito | con datos | el contenido |

| Regla | Motivo |
|---|---|
| El fetch no vive en `useEffect` | Es la fuente clasica de dependencia mal declarada y peticiones duplicadas |
| Un hook por recurso | La clave de cache, la invalidacion y el retry quedan en un lugar |
| La clave incluye todos los filtros | Si no, dos consultas distintas comparten cache |
| Invalidar por clave, no recargar todo | Un `invalidateQueries` global tumba la performance |
| El error del servidor se distingue del error de red | Uno se reintenta solo, el otro necesita intervencion |

El cliente HTTP con errores tipados, los reintentos y los casos de cache estan
en `references/estado-y-fetching.md`.

### Paso 5 - Formularios

| Decision | Criterio |
|---|---|
| Controlado vs no controlado | No controlado por defecto; controlado solo si hay validacion en vivo o dependencia entre campos |
| Validacion | Un unico schema que genera los tipos; el mismo schema corre en cliente y en servidor |
| Errores del servidor | Se mapean al campo correspondiente, no a un banner generico |

```tsx
const orderSchema = z.object({
  customerId: z.string().min(1, "El cliente es obligatorio"),
  quantity: z.coerce.number().int().min(1, "La cantidad es al menos 1"),
});

type OrderFormValues = z.infer<typeof orderSchema>;

export function OrderForm({ onSubmit }: { onSubmit: (v: OrderFormValues) => void }) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm<OrderFormValues>({ resolver: zodResolver(orderSchema) });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <label htmlFor="customerId">Cliente</label>
      <input id="customerId" {...register("customerId")} aria-invalid={!!errors.customerId} />
      {errors.customerId && <span role="alert">{errors.customerId.message}</span>}
      <button type="submit" disabled={isSubmitting}>Crear pedido</button>
    </form>
  );
}
```

| Regla | Motivo |
|---|---|
| El schema genera los tipos | No puede haber deriva entre lo que se valida y lo que se tipa |
| `noValidate` con validacion propia | El navegador no mensajes en otro idioma ni con otro formato |
| Cada error cerca de su campo, con `role="alert"` | El lector de pantalla lo anuncia |
| El formulario no muta el servidor directamente | La mutacion vive en el hook, con su invalidacion |

### Paso 6 - Estilos

Un solo sistema, tres piezas: **tokens** (variables), **base** (reset y
tipografia), **componentes** (modulos por pieza).

```css
/* styles/tokens.css */
:root {
  --color-surface: #ffffff;
  --color-text: #16181d;
  --color-brand: #2f5bea;
  --space-2: 0.5rem;
  --space-4: 1rem;
  --radius-md: 6px;
}
```

| Regla | Motivo |
|---|---|
| Los valores de diseno son tokens, no literales | Un cambio de marca no es un buscar y reemplazar en 80 archivos |
| CSS Modules por componente | El nombre de clase no colisiona entre pantallas |
| Sin `!important` | Con cascada por especificidad se resuelve |
| Sin selectores globales profundos | `div.app > ul > li` se rompe con el primer wrapper |
| Orden fijo: reset, tokens, base, componentes | La especificidad deja de ser un misterio |
| Los componentes de UI no know de la feature | Se pueden extraer a un paquete y reusar |

### Paso 7 - Accesibilidad

El criterio de aceptacion de una pantalla incluye que se pueda usar con teclado
y que un lector de pantalla entienda la estructura. No es un extra del final.

| Regla | Como se verifica |
|---|---|
| HTML semantico antes que `div` con handlers | `<button>`, `<a>`, `<label>`, `<table>` |
| Todo control interactivo es alcanzable con `Tab` | Recorrido de teclado sin trampa |
| Foco visible, nunca `outline: none` sin reemplazo | `:focus-visible` con contraste suficiente |
| Cada input tiene su `label` con `htmlFor` | Automatizable con un test |
| Contraste minimo 4.5:1 en texto | Herramienta de contraste sobre los tokens |
| Cambios dinamicos anunciados | `role="status"` o `aria-live="polite"` |
| `aria-label` solo si no hay texto visible | Un boton con icono necesita nombre accesible |
| Modales con foco atrapado y `Escape` | Se cierra y devuelve el foco al disparador |

```bash
# Chequeo automatico de accesibilidad en el build
npx playwright test tests/a11y --reporter=list
```

El detalle por categoria, con los casos que se escapan al test automatico, esta
en `references/accesibilidad.md`.

### Paso 8 - Performance y code splitting

Se optimiza lo que se midio. La regla de oro: **primero medir, luego
optimizar**.

| Sintoma | Causa probable | Que hacer |
|---|---|---|
| Bundle inicial grande | Todo entra en el chunk principal | Dividir por ruta |
| Re-render innecesario | Estado alto mal ubicado | Mover el estado hacia abajo |
| Lista larga que se traba | Todo el DOM montado | Virtualizar la lista |
| Imagen que empuja el layout | Sin dimensiones fijas | `width`, `height`, `loading="lazy"` |
| Transicion que se siente pesada | Trabajo en el hilo principal | `useMemo` en el calculo caro |

**Code splitting por ruta**, que es el 80% del caso:

```tsx
// app/routes/router.tsx
const OrdersPage = lazy(() => import("@features/orders/OrdersPage"));
const ReportsPage = lazy(() => import("@features/reports/ReportsPage"));

export function AppRoutes() {
  return (
    <Suspense fallback={<RouteSkeleton />}>
      <Routes>
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/reports" element={<ReportsPage />} />
      </Routes>
    </Suspense>
  );
}
```

| Regla | Motivo |
|---|---|
| `lazy` en rutas, no en cada componente | El chunk por componente chico no compensa |
| Un `Suspense` con esqueleto con forma real | Un spinner en pantalla vacia se siente lento |
| `manualChunks` para el vendor | El vendor cambia menos: se cachea entre despliegues |
| Los assets llevan hash en el nombre | El cache se invalida solo cuando cambia el contenido |
| `memo` solo con perfilado que lo justifique | Es memoizacion cara y a veces mas lenta que el render |
| Virtualizar listas de mas de 200 filas | El DOM tiene un limite practico |

Las metricas que se vigilan (LCP, INP, CLS), la configuracion de build y como se
miden estan en `references/performance.md`.

### Paso 9 - Convenciones de nombres

| Tipo | Convencion | Ejemplo |
|---|---|---|
| Componente | `PascalCase.tsx` | `OrdersTable.tsx` |
| Hook | `useXxx.ts` | `useOrders.ts` |
| Tipo | `Xxx.types.ts` | `order.types.ts` |
| Utilidad | `camelCase.ts` | `formatCurrency.ts` |
| Test | `Xxx.test.tsx` | `OrdersTable.test.tsx` |
| Constante | `SCREAMING_SNAKE_CASE` | `MAX_PAGE_SIZE` |
| Booleano | prefijo `is`, `has`, `can` | `isLoading`, `hasPending` |

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| `useEffect` con `fetch` dentro | Dependencias mal declaradas, peticiones duplicadas, estado desincronizado | Hook de query por recurso |
| Copiar la respuesta del servidor a `useState` | La cache y el estado divergen y la invalidacion no llega | Dejar el server state en su cache |
| El mismo estado en la URL y en un contexto | Dos fuentes de verdad para el mismo dato | Elegir una: URL para lo compartible |
| Un componente con mas de 300 lineas | Mezcla datos, estado y vista | Partir por responsabilidad |
| Un provider global con todo el estado | Cada cambio re-renderiza la app entera | Contexto para lo global minimo |
| Props drilling de mas de tres niveles | Cada refactor toca la cadena entera | Composicion o contexto acotado |
| `any` para callar al compilador | El error aparece en runtime | `unknown` y estrechamiento |
| Formulario sin schema | Cliente y servidor validan distinto | Schema unico compartido |
| Deshabilitar el submit sin explicar el error | El usuario no sabe que falta | Mostrar el error en el campo |
| `outline: none` sin estilo de foco | El teclado pierde la posicion | `:focus-visible` con contraste |
| `div` con `onClick` | No es alcanzable con teclado ni anunciable | `button` y `a` nativos |
| `!important` para resolver cascada | La especificidad se vuelve imposible de rastrear | Tokens y orden de hojas |
| `useMemo` en todo | La memoizacion tiene costo propio | Solo con medicion que lo justifique |
| Colores y espaciados literales por todo el codigo | El cambio de marca es un refactor masivo | Tokens CSS |
| `console.log` en el codigo de produccion | Fuga de datos y ruido en el navegador | Logger con niveles controlados |

## Referencias

### Skills relacionadas

| Skill | Que aporta |
|---|---|
| `dev-kit-backend-stack` | De donde viene el contrato que consume el frontend |
| `dev-kit-code-quality` | Lint, tipos y gates que esta skill asume |
| `dev-kit-testing` | Estrategia de pruebas de componentes y flujos |
| `dev-kit-review` | Checklist de revision de cambios de interfaz |

### Archivos de esta skill

| Archivo | Contenido |
|---|---|
| `templates/component-tree.md` | Arbol de proyecto y reglas de extraccion |
| `references/estado-y-fetching.md` | Estado, cache e invalidacion |
| `references/accesibilidad.md` | Checklist de accesibilidad por categoria |
| `references/performance.md` | Metricas y tecnicas de optimizacion |
