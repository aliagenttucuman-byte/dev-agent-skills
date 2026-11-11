# Performance en el frontend

> Referencia de `dev-kit-frontend-stack`. Que optimizar de verdad y que es
>micro-optimizacion que no vale el costo.

## La pregunta primero

> **Que accion del usuario se siente lenta?**

La performance se mide contra la accion, no contra un score. Un bundle de
400 KB con un tiempo de carga de 800 ms en 4G es aceptable. Un bundle de
120 KB con una tabla que tarda 4 segundos en filtrar es un problema.

Optimizar sin saber que esta lento es escribir codigo mas complejo a ciegas.

## Lo que casi siempre importa

En orden de impacto real para la mayoria de las aplicaciones:

### 1. La consulta a la base de datos (es un problema de backend)

La razon mas comun de "el frontend va lento" es que el endpoint trae 50.000
filas y el navegador las procesa. El fix es paginar en el servidor.

**Como se detecta:** mirar el log de queries del backend durante la accion
lenta. Si hay una consulta que trae mas de lo que se muestra, el problema no
es el frontend.

### 2. Renderizados costosos

Un componente que renderiza 2.000 elementos sin virtualizacion.

```tsx
// Con virtualizacion: solo se renderizan las filas visibles
const virtualizer = useVirtualizer({
  count: rows.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 40,
  overscan: 5,
});
```

**Regla:** virtualizar por encima de ~200 filas visibles. Debajo, la
complejidad no se justifica.

### 3. Recalculos en cada render

```tsx
// MAL: se recalcula en cada render
const filtered = rows.filter(r => r.status === status);
const total = filtered.reduce((acc, r) => acc + r.amount, 0);

// BIEN: se recalcula solo si cambian las dependencias
const filtered = useMemo(
  () => rows.filter(r => r.status === status),
  [rows, status]
);
const total = useMemo(
  () => filtered.reduce((acc, r) => acc + r.amount, 0),
  [filtered]
);
```

**Regla:** `useMemo` tiene costo. Usarlo para un calculo trivial es ruido.
Vale la pena cuando el calculo es O(n) con n grande, o cuando el resultado es
una dependencia de otro `useMemo` o `useEffect`.

### 4. Cargar solo lo necesario (code splitting)

```tsx
const SettingsPage = lazy(() => import("./pages/Settings/SettingsPage"));
```

**Regla:** partir por ruta. Todo lo que no esta en la ruta inicial se carga
despues. Es la optimizacion con mejor relacion esfuerzo/beneficio.

**Que no partir:** componentes pequenos y usados en todas partes. El costo de
la request extra supera el ahorro.

### 5. Imagenes

```tsx
<img src={url} width={320} height={180} loading="lazy" alt="..." />
```

- `width` y `height` evitan el salto de layout (CLS).
- `loading="lazy"` en imagenes fuera del viewport inicial.
- Servir formatos modernos (WebP, AVIF).
- No cargar imagenes por debajo del pliegue a resolucion completa.

### 6. Estilos

Las sombras y los filtros grandes (`blur`, `backdrop-filter`) son caros de
pintar, especialmente en listas largas.

```css
/* En listas largas, evitar backdrop-filter por elemento */
.card { background: var(--surface); }  /* en vez de backdrop-filter */
```

## Lo que casi nunca importa

| Optimizacion | Realidad |
|---|---|
| `React.memo` en todo | Encarece el codigo y evita pocas re-renderizaciones |
| Aplanar el estado en muchos `useState` | Un solo objeto es mas simple |
| Virtualizar una lista de 20 elementos | El costo supera el beneficio |
| Optimizar el bundle sin medir | El problema real suele estar en otro lado |
| `useCallback` en todas las funciones | Solo importa si es dependencia de un `useMemo`/`useEffect` |

**Regla general:** primero medir con el profiler, después optimizar. El
profiler de React muestra que componente re-renderiza y por que.

## Medicion

### Metricas que importan

| Metrica | Objetivo tipico | Se mide con |
|---|---|---|
| Largest Contentful Paint | < 2.5s | PerformanceObserver |
| Interaction to Next Paint | < 200ms | PerformanceObserver |
| Cumulative Layout Shift | < 0.1 | PerformanceObserver |
| Time to Interactive | Depende del caso | Lighthouse |

### Midiendo el render

```tsx
const profilerRef = useRef<Profiler>(null);

<Profiler
  ref={profilerRef}
  id="Table"
  onRender={(id, phase, actualDuration) => {
    // registrar si actualDuration supera el umbral
  }}
>
  <DataTable rows={rows} />
</Profiler>
```

**Regla:** medir el componente que el usuario dice que va lento. No el arbol
entero.

## Budget

Definir el presupuesto en el pipeline, no en la cabeza:

```yaml
# presupuesto de performance que falla el build
budgets:
  javascript: 250kb
  initialRoute: 180kb
  largestContentfulPaint: 2500ms
```

**Por que:** un presupuesto que no falla el build es una intencion. Uno que
falla, es un limite.

## Anti-patrones

| Anti-patron | Consecuencia |
|---|---|
| Traer todo y paginar en el cliente | El server se traba igual, el payload es enorme |
| `useMemo` en todo | Codigo ruidoso, sin beneficio |
| `React.memo` por defecto | Encarece el codigo |
| Code splitting de componentes triviales | Requests extra que no compensan |
| Virtualizar listas chicas | Complejidad sin beneficio |
| Optimizar sin medir | Se optimiza lo que no molesta |
| Sin `width`/`height` en imagenes | Salto de layout |
| Sin `loading="lazy"` | Se cargan imagenes fuera de pantalla |
| Bundle sin presupuesto | Crece sin limite hasta que alguien se queja |

## Referencias

- `dev-kit-frontend-stack/templates/component-tree.md` - donde vive cada pieza
- `dev-kit-frontend-stack/references/estado-y-fetching.md` - estados y fetching
- `dev-kit-frontend-stack/references/accesibilidad.md` - checklist accesible
