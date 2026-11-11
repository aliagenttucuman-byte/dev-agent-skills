# Estado y fetching en el frontend

> Referencia de `dev-kit-frontend-stack`. Donde vive cada tipo de estado y como
> se traen los datos.

## La pregunta que decide todo

> **¿Este estado se puede derivar de otro estado?**

Si la respuesta es si, no es estado: es un calculo. Ejemplos tipicos:

| Se suele guardar | Mejor derivar |
|---|---|
| `filteredItems` a partir de `items` y `filter` | Filtrar en el render o con `useMemo` |
| `isLoading` a partir de `data === undefined` | Dejar que la libreria lo Exponga |
| `isModalOpen` a partir de la ruta | Usar el router |
| `total` a partir de `items` | `items.length` |

**Regla:** el estado duplicado es un bug esperando. Dos fuentes de verdad para
el mismo dato siempre se desincronizan.

## Los cuatro tipos de estado

| Tipo | Donde vive | Ejemplo |
|---|---|---|
| **Servidor** | La cache de la libreria de datos | Lista de usuarios, metricas |
| **URL** | Los parametros de la ruta | Filtros, paginacion, tab activa |
| **Cliente global** | Un contexto | Usuario logueado, tema, preferencias |
| **Cliente local** | `useState` del componente | Input abierto, valor del campo |

### Estado de servidor

Va en la cache de la libreria de fetching, no en `useState`.

```tsx
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ["metrics", period],
  queryFn: () => fetchMetrics(period),
});
```

**Por que:** la cache resuelve el re-fetch, el deduplicado, la invalidacion
invalidation, el garbage collection y el refetch en foco. Si guardas el
resultado en `useState`, escribis de nuevo todo eso a mano, peor.

**Regla:** los datos que vienen del servidor NUNCA se copian a `useState`.
Si necesitas transformarlos, deriva en el render.

### Estado de URL

Todo lo que el usuario podria querer compartir por link va en la URL.

```tsx
const [searchParams, setSearchParams] = useSearchParams();
const page = Number(searchParams.get("page") ?? 1);
const status = searchParams.get("status") ?? "all";
```

**Por que:** la URL es el estado compartible. Con filtros en la URL, recargar
no pierde nada, "copiar link" funciona, y el boton atras funciona.

**Candidatos a URL:** filtros, paginacion, orden, tab activa, rango de fechas,
vista (tabla/cards), query de busqueda.

**No va en la URL:** estado efimero (un menu abierto), datos del usuario,
preferencias de la app.

### Estado global

Solo lo que de verdad es global y lo comparte mas de una rama de la app.

```tsx
const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const value = useMemo(() => ({ user, setUser }), [user]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
```

**Test de necesidad:** antes de crear un contexto, responde: ¿dos ramas
distintas de la app necesitan esto? Si la respuesta es no, es `useState` local
o props.

**Anti-patron:** el "context store" que guarda todo. Cuando un contexto tiene
50 campos y lo consume toda la app, cualquier cambio re-renderiza todo.

## Fetching

### Donde va la llamada

En la capa de servicio, no en el componente.

```tsx
// services/metrics.ts
export async function fetchMetrics(period: string): Promise<Metric[]> {
  const res = await fetch(`/api/metrics?period=${period}`);
  if (!res.ok) throw new Error(`Error ${res.status} al obtener metricas`);
  return res.json();
}
```

**Por que:** el componente no sabe la URL ni el formato. Se puede cambiar el
endpoint sin tocar la UI, y se puede testear el servicio sin montar nada.

### Los cuatro estados

Una pantalla de datos tiene siempre cuatro estados. Si solo implementaste el
"con datos", te faltan tres:

```tsx
if (isLoading) return <Skeleton />;
if (error) return <ErrorState error={error} onRetry={refetch} />;
if (!data?.length) return <EmptyState action={<Button>Crear</Button>} />;
return <List items={data} />;
```

| Estado | Que muestra | Regla |
|---|---|---|
| Cargando | Esqueleto de la forma real, no un spinner central | El esqueleto tiene la forma del contenido, para que no salte el layout |
| Error | Que fallo y como reintentar | El mensaje dice que hacer |
| Vacio | Que no hay datos y como crear el primero | El vacio es una accion, no un sorry |
| Con datos | El contenido | - |

**El error sin accion es un bug de UX.** "Algo salio mal" no le dice nada al
usuario. "No pudimos cargar las metricas. Reintentar" si.

### Mutaciones

```tsx
const mutation = useMutation({
  mutationFn: (payload: CreateUser) => createUser(payload),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["users"] });
    closeModal();
  },
});
```

**Regla:** despues de una mutacion, invalidar las queries afectadas. Si no,
la UI muestra datos viejos y el usuario piensa que el guardado fallo.

**Regla:** el error de una mutacion se muestra junto a la accion que la
disparo, no como un toast que desaparece.

### Invalidacion

| Operacion | Invalidar |
|---|---|
| Crear | La lista y el detalle |
| Actualizar | El detalle y la lista (si cambia lo que se ve en la lista) |
| Borrar | La lista |
| Accion masiva | Todas las queries afectadas, con `refetchType: "inactive"` |

**Evitar:** invalidar todo con `invalidateQueries()` sin filtro. Dispara
refetches que nadie pidio.

## El patron de `useEffect`

`useEffect` es para sincronizar con el exterior: timers, suscripciones,
eventos del navegador, focus, scroll.

```tsx
// Bien: sincronizacion con el exterior
useEffect(() => {
  const id = setInterval(refresh, 30_000);
  return () => clearInterval(id);
}, [refresh]);

// Mal: transformacion de datos que podria ser un calculo
useEffect(() => {
  setTotal(items.filter(i => i.active).length);
}, [items]);
```

**Test:** si el `useEffect` podria ser un `useMemo`, es un `useMemo`.
Si podria ser un calculo en el render, es un calculo en el render.

**El anti-patron clasico:** el doble `useEffect` que causa el "doble fetch":

```tsx
// MAL: fetch en un efecto que depende de un estado que otro efecto setea
useEffect(() => { setUserId(1); }, []);
useEffect(() => { fetchUser(userId); }, [userId]);

// BIEN: derivar, no sincronizar
const userId = 1;
useEffect(() => { fetchUser(userId); }, [userId]);
```

## Formularios

| Parte | Regla |
|---|---|
| Estado del campo | El componente, con un unico valor por campo |
| Validacion | En el blur y en el submit, no en cada tecla |
| Error | Junto al campo, con `aria-describedby` |
| Envio | Boton deshabilitado mientras corre, con estado de "enviando" |
| Error de envio | Se muestra y el formulario conserva lo escrito |

**Regla:** nunca se pierde lo que el usuario escribio por un error de red.

## Anti-patrones

| Anti-patron | Consecuencia |
|---|---|
| Copiar datos del servidor a `useState` | Datos viejos, doble fuente de verdad |
| `useEffect` para derivar | Un render de atraso, bugs de sincronizacion |
| Filtros fuera de la URL | El link no reproduce la vista |
| Contexto con todo el estado | Re-render global, debug imposible |
| Fetch en el componente | URL y formato regados por la UI |
| Sin estado de error | Pantalla en blanco |
| Sin estado vacio | Pantalla vacia sin salida |
| Invalidar todo en cada mutacion | Rafaga de requests innecesarios |

## Referencias

- `dev-kit-frontend-stack/templates/component-tree.md` - donde vive cada pieza
- `dev-kit-frontend-stack/references/accesibilidad.md` - checklist accesible
- `dev-kit-frontend-stack/references/performance.md` - que optimizar y que no
