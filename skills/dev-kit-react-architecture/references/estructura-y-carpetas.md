# Estructura de carpetas y reglas de dependencia

Arbol de referencia con las reglas de dependencia entre capas.

---

## El grafo de dependencias

```
   main.tsx
      |
      v
    app/  (composicion: rutas, providers, layout)
      |
      v
 features/<dominio>/  (logica de negocio)
      |
      v
  shared/  (utilidades, UI base, hooks transversales)
      |
      v
   core/   (config, cliente HTTP, tipos base)
```

**Regla de dependencia:** las flechas apuntan hacia abajo, nunca hacia arriba
ni en zigzag.

| Imports | Permitido | Prohibido |
|---|---|---|
| `app` -> `features` | Si | |
| `features` -> `shared` | Si | |
| `features` -> `features` | Solo via `index.ts` | Directo a un archivo interno |
| `shared` -> `features` | | Si |
| `shared` -> `shared` | Si, con criterio | |
| `core` -> cualquier capa | | Si |

---

## Estructura completa de un feature

```
features/checkout/
├── index.ts                 # Superficie publica. Lo unico que se importa de afuera.
│
├── routes.tsx               # Componentes de ruta. Punto de entrada del feature.
│
├── components/              # Componentes propios del feature
│   ├── CheckoutForm.tsx
│   ├── CartSummary.tsx
│   └── CouponInput.tsx
│
├── hooks/                   # Hooks propios del feature
│   ├── useCart.ts
│   ├── useCoupon.ts
│   └── useCheckout.ts
│
├── api/                     # Acceso a la API de este feature
│   ├── checkoutApi.ts
│   └── queries.ts
│
├── schemas.ts               # Tipos, validacion y transformadores
│
├── constants.ts             # Constantes del feature
│
└── __tests__/               # Tests del feature
    ├── CheckoutForm.test.tsx
    └── useCart.test.ts
```

**Reglas:**

- `index.ts` exporta solo lo que otro modulo necesita. Si exporta todo, deja
  de ser una frontera.
- Los tests van en `__tests__/` del feature, no en un `tests/` global. El test
  viaja con el codigo que prueba.
- `api/` no se importa desde `components/` directamente si hay un hook que lo
  envuelve. El componente llama al hook, el hook llama a la API.
- `schemas.ts` define los tipos. Ningun `any` cruza el limite del feature.

---

## `shared/` en detalle

```
shared/
├── ui/                      # Componentes de presentacion, sin logica
│   ├── Button.tsx
│   ├── Dialog.tsx
│   ├── Table.tsx
│   └── index.ts
│
├── hooks/                   # Hooks transversales
│   ├── useDebounce.ts
│   ├── useMediaQuery.ts
│   └── useIntersection.ts
│
├── lib/                     # Utilidades puras
│   ├── format.ts
│   ├── money.ts
│   └── validation.ts
│
├── types/                   # Tipos base
│   ├── api.ts
│   └── result.ts
│
└── test/                    # Utilidades de testing compartidas
    ├── factories.ts
    └── renderWithRouter.tsx
```

**El criterio para decidir si algo va a `shared/`:**

1. Lo usan **dos o mas** features. Si lo usa uno, queda en el feature.
2. No tiene logica de negocio especifica. Un componente que conoce el
   concepto de "pedido" no va a `shared/`.
3. Es estable: no cambia por cada feature nueva.

**El test del criterio:** si mover el archivo a `shared/` obliga a importarlo
en 5 features, es compartido de verdad. Si obliga a tocar 5 features con
imports nuevos y logica condicional, no lo es.

---

## `app/` en detalle

```
app/
├── router.tsx               # Definicion de rutas
├── providers.tsx            # Providers globales en orden
├── queryClient.ts           # Configuracion de React Query
│
├── layout/
│   ├── AppShell.tsx         # Layout principal: header, nav, outlet
│   ├── MainLayout.tsx
│   └── ErrorBoundary.tsx
│
└── pages/                   # Paginas que no pertenecen a ningun feature
    ├── NotFound.tsx
    └── Unauthorized.tsx
```

**El orden de los providers importa:**

```tsx
// app/providers.tsx
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider } from "@/shared/ui/ThemeProvider";

import { queryClient } from "./queryClient";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>{children}</BrowserRouter>
      </QueryClientProvider>
    </ThemeClientProvider>
  );
}
```

El provider mas externo es el mas estable. Si el router esta dentro del
query client, los hooks de query funcionan dentro de las rutas. Al reves, las
rutas que necesitan datos fallan.

**Regla:** `app/` no importa nada de `features/` salvo desde `router.tsx`. Si
un layout necesita un dato de un feature, ese dato se pasa por props o por un
hook compartido, no por import directo.

---

## `core/` en detalle

```
core/
├── config.ts                # Configuracion leida del entorno
├── http/
│   ├── client.ts            # Cliente HTTP con interceptores
│   ├── errors.ts            # Errores de API tipados
│   └── types.ts
├── logger.ts
├── analytics.ts             # Tracking, si aplica
└── env.ts                   # Lectura y validacion de variables de entorno
```

`core/` es el unico lugar que sabe de variables de entorno:

```ts
// core/env.ts
const esquema = z.object({
  VITE_API_URL: z.string().url(),
  VITE_SENTRY_DSN: z.string().optional(),
});

export const env = esquema.parse(import.meta.env);
```

El parseo falla en el arranque si falta una variable. Es preferible a que
falle en produccion a las 3 de la manana.

---

## Import aliases

```json
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@app/*": ["./src/app/*"],
      "@features/*": ["./src/features/*"],
      "@shared/*": ["./src/shared/*"],
      "@core/*": ["./src/core/*"]
    }
  }
}
```

```ts
// vite.config.ts
resolve: {
  alias: {
    "@": path.resolve(__dirname, "./src"),
    "@app": path.resolve(__dirname, "./src/app"),
    "@features": path.resolve(__dirname, "./src/features"),
    "@shared": path.resolve(__dirname, "./src/shared"),
    "@core": path.resolve(__dirname, "./src/core"),
  },
},
```

Los aliases revelan la arquitectura en cada import. Un import de `@core/*`
dentro de `@shared/*` es visible en el diff y viola la regla.

**La regla del import de una sola direccion se puede verificar automaticamente:**

```ts
// scripts/check-boundaries.ts
import { glob } from "fast-glob";

const REGLAS: Array<[RegExp, RegExp[]]> = [
  [/^@shared\//, [/^@features\//]],
  [/^@core\//, [/^@features\//, /^@shared\//]],
  [/^@app\//, [/^@features\//]],
];

const violaciones = [];
for (const archivo of await glob("src/**/*.{ts,tsx}")) {
  const contenido = await readFile(archivo, "utf8");
  const imports = contenido.match(/from "([^"]+)"/g) ?? [];

  for (const [patron, prohibidos] of REGLAS) {
    if (!patron.test(archivo)) continue;
    for (const prohibido of prohibidos) {
      if (imports.some((i) => i.includes(prohibido.source))) {
        violaciones.push({ archivo, violacion: prohibido.source });
      }
    }
  }
}
```

Este script es un verificador, no logica de aplicacion: entra al kit bajo la
regla 3 de la constitucion.

---

## Checklist de estructura

- [ ] `app/` no tiene logica de negocio
- [ ] `shared/` no importa de `features/`
- [ ] Los features se importan entre si solo via `index.ts`
- [ ] Cada feature tiene `index.ts` con su superficie publica
- [ ] `core/` es el unico que lee variables de entorno
- [ ] Los tests viven junto al codigo que prueban
- [ ] Los aliases de import reflejan la arquitectura
- [ ] Las fronteras se verifican en CI, no a ojo
