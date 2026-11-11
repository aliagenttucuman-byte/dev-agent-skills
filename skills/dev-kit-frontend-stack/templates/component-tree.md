# Estructura de componentes

> Referencia de `dev-kit-frontend-stack`. Como se organiza una aplicacion React
> para que crecerla no se vuelva un problema.

## El principio

> **Un componente por responsabilidad, y la responsabilidad se puede nombrar en
> una frase.**

Si no podes decir que hace un componente en una frase, todavia tiene dos
responsabilidades.

## Arbol

```
<App>
├── <AppShell>                     layout, navegacion, tema
│   ├── <Sidebar>                  navegacion principal
│   ├── <TopBar>
│   │   ├── <UserMenu>
│   │   └── <GlobalSearch>
│   └── <main>
│       └── <Outlet>               contenido de la ruta
├── <Routes>
│   ├── <DashboardPage>            pagina
│   │   ├── <MetricCard>           componente
│   │   ├── <MetricGrid>           componente
│   │   └── <RecentActivity>       componente
│   │       ├── <ActivityList>
│   │       └── <EmptyState>       componente
│   └── <SettingsPage>             pagina
│       └── <SettingsForm>         componente
└── <Providers>                    contexto, tema, cliente de datos
```

## Las tres capas

| Capa | Que es | Donde vive | Quien lo usa |
|---|---|---|---|
| **Pagina** | Un destino de la aplicacion. Compone, no implementa | `pages/` | El router |
| **Componente** | Una pieza de UI reutilizable, con estado local opcional | `components/` | Paginas y otros componentes |
| **Servicio / hook** | El acceso a datos y la logica reutilizable | `hooks/`, `services/` | Componentes |

**Regla:** la logica de negocio no vive en un componente. Si un componente
hace fetch, transformaciones y render, esta haciendo tres cosas.

## Donde va cada cosa

```
src/
├── app/                 enrutado, providers, layout raiz
├── pages/               una carpeta por pagina
│   └── Dashboard/
│       ├── DashboardPage.tsx
│       ├── components/   componentes propios de esta pagina
│       └── hooks/        hooks propios de esta pagina
├── components/          componentes compartidos
│   ├── ui/              primitivos (Button, Input, Modal)
│   └── shared/          compuestos de dominio (MetricCard, DataTable)
├── hooks/               hooks reutilizables
├── services/            llamadas a la API
├── lib/                 utilidades sin estado
├── types/               tipos compartidos
├── styles/              tokens, temas, estilos globales
└── assets/
```

**Regla de colocation:** lo que solo usa una pagina vive con la pagina. Lo
que usa mas de una pagina sube a `components/` o `hooks/`. Un componente en
`components/` que usa un solo consumidor es una dependencia de mas.

## Un componente bien hecho

```tsx
type MetricCardProps = {
  label: string;
  value: string;
  delta?: { value: number; direction: "up" | "down" };
  onSelect?: () => void;
};

export function MetricCard({ label, value, delta, onSelect }: MetricCardProps) {
  return (
    <button className="metric-card" onClick={onSelect} disabled={!onSelect}>
      <span className="metric-card__label">{label}</span>
      <span className="metric-card__value">{value}</span>
      {delta && (
        <span className={`metric-card__delta metric-card__delta--${delta.direction}`}>
          {delta.direction === "up" ? "+" : ""}{delta.value}%
        </span>
      )}
    </button>
  );
}
```

Cumple:
- **Una responsabilidad:** mostrar una metrica.
- **Tipado completo:** props y retorno.
- **Sin logica de negocio:** no sabe de donde viene el valor.
- **Sin fetching:** no pide datos.
- **Un elemento semantico:** el `button` con `disabled` cuando no es accionable.

## Nombres

| Tipo | Convencion | Ejemplo |
|---|---|---|
| Componente | PascalCase, sustantivo | `MetricCard` |
| Hook | `useXxx` | `useMetrics` |
| Handler | `handleXxx` | `handleSelect` |
| Booleano | `is/has/can` + sustantivo | `isLoading`, `hasError` |
| Evento | `onXxx` | `onSelect` |
| Servicio | verbo + sustantivo | `fetchMetrics` |
| Tipo | sustantivo + `Props` / `State` / `Response` | `MetricCardProps` |

## Cuando extraer un componente

Extrae cuando se cumple **cualquiera** de estas:

- [ ] Se repite en mas de un lugar
- [ ] El bloque tiene mas de ~40 lineas
- [ ] El bloque tiene su propia logica (estado o calculo)
- [ ] El nombre del bloque es mas claro que el codigo que contiene
- [ ] Necesitas testearlo por separado

**No extraigas** cuando:
- Solo lo usas una vez y no tiene logica propia
- Lo extraido necesita 5 props para funcionar (probablemente estas
  partiendo un componente que debia partirse en dos)
- El nombre del nuevo componente es "Container" o "Wrapper" sin mas

## Anti-patrones

| Anti-patron | Consecuencia |
|---|---|
| Un componente de 500 lineas | Nadie lo mantiene |
| Fetch dentro del componente | La logica se duplica en cada pantalla |
| Props drilling de 6 niveles | El estado deberia estar en un contexto |
| Booleanos como props (`isX isY isZ`) | Explosion combinatoria de variantes |
| `useEffect` para transformar datos | Se puede derivar en el render |
| Componente que hace fetch y render | Dos responsabilidades, dos razones para cambiar |
| Estilos inline hardcodeados | Se pierde el sistema de diseno |

## Referencias

- `dev-kit-frontend-stack/references/estado-y-fetching.md` - donde vive el estado
- `dev-kit-frontend-stack/references/accesibilidad.md` - checklist accesible
- `dev-kit-frontend-stack/references/performance.md` - optimizaciones que importan
