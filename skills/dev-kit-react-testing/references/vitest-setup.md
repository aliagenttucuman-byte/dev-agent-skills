# Configuracion de Vitest, Testing Library y MSW

Configuracion completa de referencia. Ajustar al proyecto, pero no cambiar la
estructura: cada pieza resuelve un problema concreto.

---

## Dependencias

```bash
npm install -D vitest @vitest/coverage-v8 jsdom \
  @testing-library/react @testing-library/jest-dom @testing-library/user-event \
  msw @playwright/test
```

| Paquete | Para que |
|---|---|
| `vitest` | Runner, compatible con Vite, sin configuracion extra |
| `@vitest/coverage-v8` | Cobertura usando el motor de V8, sin instrumentar |
| `jsdom` | Entorno DOM para los tests de componente |
| `@testing-library/react` | Render y queries |
| `@testing-library/jest-dom` | Matchers de DOM (`toBeInTheDocument`) |
| `@testing-library/user-event` | Interacciones reales de usuario |
| `msw` | Intercepta red a nivel de API |
| `@playwright/test` | E2E en navegador real |

**Alternativa a jsdom:** `happy-dom` es mas rapido en algunos benchmarks. El
default es `jsdom` por mayor compatibilidad.

---

## vite.config.ts

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    restoreMocks: true,
    clearMocks: true,
    unstubEnvs: true,
    unstubGlobals: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      reportsDirectory: "./coverage",
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "**/*.test.{ts,tsx}",
        "**/*.spec.{ts,tsx}",
        "**/test/**",
        "**/*.stories.tsx",
        "**/*.config.{ts,tsx}",
        "src/main.tsx",
      ],
      thresholds: {
        statements: 80,
        branches: 75,
        functions: 80,
        lines: 80,
      },
    },
  },
});
```

**Claves:**

- `restoreMocks: true` restaura los spies entre tests: sin esto, un
  `vi.spyOn` de un test anterior sigue activo en el siguiente.
- `clearMocks: true` limpia las llamadas registradas.
- `unstubEnvs` y `unstubGlobals` revierten `vi.stubEnv` y `vi.stubGlobal`.
- `include` en coverage: sin esto, se miden los archivos de test.

---

## src/test/setup.ts

```ts
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";

import { server } from "./server";

beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});
```

`cleanup` desmonta los componentes renderizados. Con `globals: true` y
`environment: "jsdom"`, Vitest no lo hace automaticamente en todas las
versiones: hacerlo explicito evita fugas entre tests.

---

## src/test/server.ts

```ts
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";

export const server = setupServer(
  http.get("/api/sesion", () => HttpResponse.json({ usuario: null })),

  http.get("/api/pedidos", () =>
    HttpResponse.json([
      { id: "1", total: 100, estado: "pagado" },
      { id: "2", total: 250, estado: "pendiente" },
    ]),
  ),

  http.get("/api/pedidos/:id", ({ params }) => {
    const id = String(params.id);
    return HttpResponse.json({ id, total: 100, estado: "pagado" });
  }),

  http.post("/api/pedidos", async ({ request }) => {
    const cuerpo = (await request.json()) as { total: number };
    return HttpResponse.json(
      { id: "nuevo", total: cuerpo.total, estado: "pendiente" },
      { status: 201 },
    );
  }),
);
```

**El handler por defecto es el caso de exito.** Los errores se agregan en el
test especifico con `server.use()`.

---

## src/test/factories.ts

```ts
import type { Pedido } from "@/types/pedido";

export function crearPedido(overrides: Partial<Pedido> = {}): Pedido {
  return {
    id: "1",
    total: 100,
    estado: "pagado",
    ...overrides,
  };
}
```

Los factories evitan que cada test escriba el objeto completo y que un campo
nuevo rompa 40 tests.

---

## Hooks de test reutilizables

```ts
// src/test/hooks.ts
import { renderHook, waitFor } from "@testing-library/react";
import type { RenderHookOptions, RenderHookResult } from "@testing-library/react";

export function renderHookConResultado<TProps, TResult>(
  callback: (props: TProps) => TResult,
  options?: RenderHookOptions<TProps>,
): RenderHookResult<TResult, TProps> {
  return renderHook(callback, {
    ...options,
    wrapper: ({ children }) => <>{children}</>,
  });
}

export { waitFor };
```

---

## Mockear el router

```tsx
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

export function renderConRouter(
  ui: React.ReactElement,
  { ruta = "/" }: { ruta?: string } = {},
) {
  return render(<MemoryRouter initialEntries={[ruta]}>{ui}</MemoryRouter>);
}
```

El router de test es un `MemoryRouter` con `initialEntries`. Nunca se mockea
`useNavigate` con un `vi.fn()`: se pierde la verificacion de que el enlace
lleva a la ruta correcta.

---

## Mockear el tiempo

```ts
import { vi } from "vitest";

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

test("muestra el spinner mientras carga", async () => {
  render(<DetallePedido id="1" />);
  expect(screen.getByRole("status")).toBeInTheDocument();
  await vi.advanceTimersByTimeAsync(1000);
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
});
```

`advanceTimersByTimeAsync` es la version que deja correr las promesas pendientes.
`advanceTimersByTime` no las ejecuta y el test falla.

---

## Script de test

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest run --coverage",
    "test:e2e": "playwright test",
    "test:all": "npm run test && npm run test:e2e"
  }
}
```

---

## Errores frecuentes

| Error | Causa | Correccion |
|---|---|---|
| `ReferenceError: expect is not defined` | Sin `globals: true` o sin el import | Activar `globals` o importar de `vitest` |
| `Cannot use import statement outside a module` | Falta el plugin de React | Agregar `plugins: [react()]` |
| `document is not defined` | Entorno equivocado | `environment: "jsdom"` |
| `getByRole` no encuentra el elemento | Rol o nombre incorrecto | Imprimir el arbol con `screen.debug()` |
| "Found multiple elements" | Query no es unica | Usar `getAllBy*` o acotar el ambito |
| Test flaky por estado compartido | Mock no restaurado | `restoreMocks: true` |
| "Network request was not made" | `onUnhandledRequest: "error"` | Agregar el handler faltante |
| `act(...)` warning | Actualizacion de estado fuera de act | Envolver en `await usuario.click()` |
| `waitFor` expira | Elemento nunca aparece | Revisar la query y la condicion |
| Snapshot obsoleto en CI | Snapshot no versionado | Versionar los snapshots o evitarlos |
