---
name: dev-kit-react-testing
description: "Testing profesional de aplicaciones React: Vitest para unidades y hooks, React Testing Library para componentes con criterio de queries por rol, MSW para mockear red a nivel de API, Playwright para end-to-end, cobertura de interacciones reales, cobertura de componentes y los limites de cada nivel. CARGAR cuando hay que escribir tests de una interfaz, decidir que mockear, configurar Vitest o Testing Library, montar un componente o escribir un flujo end-to-end."
version: 1.0.0
author: Dev Agent Kit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [react, testing, vitest, testing-library, msw, playwright]
    category: software-development
    related_skills: [dev-kit-frontend-stack, dev-kit-testing, dev-kit-code-quality, dev-kit-ci-cd]
---

# Dev Kit - React Testing

> **Trigger:** "testear un componente React", "configurar Vitest", "React
> Testing Library", "mockear la API", "Playwright", "que tests escribo", "mi test
> falla por estado". Cargar esta skill ANTES de escribir el primer test de UI.

## Que es esto

El contrato de como se prueba una interfaz React. No es un catalogo de
librerias: es la decision de **que se testea en cada nivel** y **que se mockea
en cada nivel**.

La premisa: **un test que imita la implementacion es un test que se rompe
cuando refactorizas y no encuentra bugs.** La jerarquia de mocks va de menos a
mas, y cada nivel usa el mas bajo posible.

| Nivel | Que se prueba | Que se mockea | Herramienta |
|---|---|---|---|
| Unidad | Una funcion pura | Nada | Vitest |
| Hook | Logica de un hook | Red (con MSW) | Vitest + RTL |
| Componente | Interaccion del usuario | Red (con MSW) | RTL |
| Integracion | Varias piezas juntas | Red (con MSW) | RTL |
| E2E | Flujo real en navegador | Nada | Playwright |

**La regla que resume todo:** en los tests de React no se mockea lo que se
puede.renderizar de verdad.

## Los cinco tests que hay que evitar

1. **Testear el estado interno.** `expect(wrapper.state().isOpen).toBe(true)`.
   No le importa al usuario. El usuario ve un dialogo abierto o no.
2. **Snapshots de componentes completos.** Un snapshot grande cambia con
   cualquier cambio de markup y nadie lo lee. Los snapshots solo valen para
   datos serializados.
3. **Mockear la libreria bajo prueba.** Mockear `useState` es no testear nada.
4. **Consultar por clase CSS o por implementacion.** `container.querySelector`.
   Cambia con el refactor y no describe la intencion.
5. **Probar los detalles de MUI, de React o del router.** Se testea lo que la
   aplicacion controla, no lo que controla la libreria.

## Workflow

| Paso | Que hace | Artefacto | Gate |
|---|---|---|---|
| 1. Clasificar | Decidir el nivel de cada caso | matriz caso-nivel | Ningun caso en el nivel equivocado |
| 2. Configurar | Vitest, RTL, MSW, Playwright | config + scripts | Todos los comandos en el package.json |
| 3. Queries | Escribir por rol, no por selector | queries semanticas | Cero `querySelector` |
| 4. Mockear red | MSW a nivel de API | handlers | Sin fetch mockeado a mano |
| 5. Escribir | Usuario primero, asserts despues | test | El test falla si el usuario no puede hacer la accion |
| 6. E2E | Los flujos que cruzan el navegador | specs | Pocos y estables |
| 7. Cobertura | Medir sobre los flujos | reporte | Umbral por capa |

### Paso 1 - Clasificar el caso antes de escribirlo

| El caso verifica... | Nivel | Ubicacion |
|---|---|---|
| Una funcion pura (formato, calculo, validacion) | Unidad | `src/**/*.test.ts` |
| Un hook con logica (useFetch, useCarrito) | Hook | `src/**/*.test.tsx` |
| Que un boton dispara la accion | Componente | `src/**/*.test.tsx` |
| Que un formulario envia los datos correctos | Componente | `src/**/*.test.tsx` |
| Varias vistas coordinadas | Integracion | `src/**/*.test.tsx` |
| El flujo completo desde login hasta resultado | E2E | `e2e/**/*.spec.ts` |

**Regla:** si el caso se puede escribir sin renderizar, es unidad. No lo
subas de nivel "porque es UI". Un test de unidad corre en milisegundos.

### Paso 2 - Configuracion

**Vitest** para unidades y componentes:

```ts
// vite.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      thresholds: {
        statements: 80,
        branches: 75,
        functions: 80,
        lines: 80,
      },
      exclude: ["**/*.test.*", "**/test/**", "**/*.stories.*", "e2e/**"],
    },
  },
});
```

```ts
// src/test/setup.ts
import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

**Por que `onUnhandledRequest: "error"`:** si el test hace una peticion que no
esta mockeada, falla en vez de devolver 404 silencioso. Sin esto, un endpoint
renombrado sigue "funcionando" porque el test nunca lee la respuesta.

**Scripts** en `package.json`:

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:e2e": "playwright test",
    "test:all": "npm run test && npm run test:e2e"
  }
}
```

**Playwright** para E2E:

```ts
// playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "html",
  use: {
    baseURL: "http://localhost:4173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm run build && npm run preview",
    url: "http://localhost:4173",
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
```

**Reglas:**

- `forbidOnly: true` en CI: un `test.only` commiteado no debe hacer pasar el
  pipeline saltando el resto.
- `trace: "on-first-retry"` guarda la traza solo cuando hay reintento. En el
  primer fallo, el screenshot basta.
- Solo Chromium por defecto. Agregar navegadores es lento; se agrega uno
  cuando hay un bug especifico de Safari o Firefox.
- `webServer` levanta la app: el E2E no depende de que alguien la haya
  levantado a mano.

### Paso 3 - Queries por rol, no por selector

React Testing Library no tiene `getByTestId` como API principal. Se consulta
como lo haria un usuario: por rol y por nombre accesible.

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { BotonPagar } from "./BotonPagar";

test("el boton de pago deshabilita mientras se procesa", async () => {
  const usuario = userEvent.setup();
  render(<BotonPagar total={100} alPagar={vi.fn()} />);

  const boton = screen.getByRole("button", { name: /pagar/i });
  expect(boton).toBeEnabled();

  await usuario.click(boton);
  expect(boton).toBeDisabled();
});
```

**La tabla de queries, en orden de preferencia:**

| Quiero... | Query |
|---|---|
| Un boton | `getByRole("button", { name: /.../ })` |
| Un campo de texto | `getByRole("textbox", { name: /.../ })` |
| Un enlace | `getByRole("link", { name: /.../ })` |
| Un encabezado | `getByRole("heading", { name: /.../ })` |
| Una tabla | `getByRole("table")` |
| Un dialogo | `getByRole("dialog")` |
| Una alerta | `getByRole("alert")` |
| Texto exacto | `getByText("Total a pagar")` |

**Reglas:**

- `getBy*` cuando el elemento **debe** existir. Si no existe, el test falla con
  un mensaje util.
- `queryBy*` cuando el elemento **no debe** existir. `queryBy` devuelve `null`
  en vez de lanzar.
- `findBy*` cuando hay que esperar (elemento asincrono). Devuelve una promesa.
- `getAllBy*` cuando hay varios.
- El nombre accesible es el contrato visible. Si hay que agregar
  `aria-label`, eso es una mejora de accesibilidad, no un parche para el test.
- Nunca `container.querySelector`. Nunca `getByTestId` salvo para un valor
  que no es visible y no tiene rol (un input hidden).

### Paso 4 - Mockear la red con MSW, no con fetch

El error clasico: mockear `global.fetch` con un `vi.fn()` y devolver un objeto
inventado. Eso testea el mock, no la aplicacion.

```ts
// src/test/server.ts
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";

export const server = setupServer(
  http.get("/api/pedidos/:id", ({ params }) => {
    if (params.id === "inexistente") {
      return HttpResponse.json({ error: "no encontrado" }, { status: 404 });
    }
    return HttpResponse.json({ id: params.id, total: 100, estado: "pagado" });
  }),
);
```

```tsx
import { http, HttpResponse } from "msw";
import { server } from "../test/server";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DetallePedido } from "./DetallePedido";

test("muestra el error cuando el pedido no existe", async () => {
  const usuario = userEvent.setup();
  render(<DetallePedido id="inexistente" />);

  expect(await screen.findByRole("alert")).toHaveTextContent(/no encontrado/i);
});

test("reintenta cuando la red falla", async () => {
  const usuario = userEvent.setup();
  server.use(
    http.get("/api/pedidos/:id", () => HttpResponse.error()),
  );

  render(<DetallePedido id="123" />);

  await usuario.click(await screen.findByRole("button", { name: /reintentar/i }));
  expect(await screen.findByRole("alert")).toBeInTheDocument();
});
```

**Reglas:**

- El handler por defecto representa el caso de exito. Los casos de error se
  sobreescriben con `server.use()` solo en el test que los necesita.
- `server.resetHandlers()` en `afterEach` es lo que hace que el override no
  contamine el siguiente test.
- MSW intercepta en el nivel de red: el codigo de la aplicacion no cambia.
- Un test con MSW verifica el codigo de parsing de la respuesta, que es parte
  de la aplicacion y por lo tanto debe probarse.
- `server.use()` con un handler de error de red simula el caso "la API no
  respondio", que es distinto de "la API respondio 500".

### Paso 5 - Escribir el test como el usuario

```tsx
test("el usuario completa el checkout y ve la confirmacion", async () => {
  const usuario = userEvent.setup();
  const alConfirmar = vi.fn();

  render(<Checkout alConfirmar={alConfirmar} />);

  await usuario.type(screen.getByRole("textbox", { name: /correo/i }), "a@b.com");
  await usuario.click(screen.getByRole("radio", { name: /tarjeta/i }));
  await usuario.type(screen.getByRole("textbox", { name: /numero/i }), "4111111111111111");

  const boton = screen.getByRole("button", { name: /confirmar/i });
  expect(boton).toBeEnabled();

  await usuario.click(boton);

  expect(await screen.findByRole("heading", { name: /gracias/i })).toBeInTheDocument();
  expect(alConfirmar).toHaveBeenCalledWith(
    expect.objectContaining({ correo: "a@b.com" }),
  );
});
```

**Reglas:**

- `userEvent.setup()` en cada test. Sin `setup()`, los eventos se encolan y el
  test pasa por el motivo equivocado.
- `userEvent` es async: `await usuario.click(...)`. Olvidar el `await` es la
  causa numero uno de tests flaky.
- El test no depende del orden de los clicks ni del texto literal de los
  mensajes: usa regex para lo variable.
- Un test verifica **un** comportamiento. Si hace tres asserts de tres
  componentes distintos, son tres tests.
- El nombre del test describe el comportamiento, no el mecanismo:
  `"deshabilita el boton mientras se procesa el pago"`, no `"testPaymentButton"`.

### Paso 6 - E2E: pocos y estables

```ts
// e2e/checkout.spec.ts
import { expect, test } from "@playwright/test";

test("compra completa desde el carrito", async ({ page }) => {
  await page.goto("/productos/1");
  await page.getByRole("button", { name: /agregar al carrito/i }).click();

  await page.getByRole("link", { name: /carrito/i }).click();
  await expect(page.getByRole("heading", { name: /carrito/i })).toBeVisible();

  await page.getByRole("button", { name: /finalizar/i }).click();
  await page.getByRole("textbox", { name: /correo/i }).fill("a@b.com");
  await page.getByRole("button", { name: /pagar/i }).click();

  await expect(page.getByRole("heading", { name: /gracias/i })).toBeVisible();
});
```

**Reglas:**

- E2E es para los flujos que cruzan el navegador: navegacion, redirecciones,
  formularios largos, pago. Nada mas.
- Se usa el mismo vocabulario de queries que en RTL. Un unico lenguaje de
  busqueda para las dos capas.
- Cada E2E es independiente: crea sus propios datos. No depende del orden de
  ejecucion ni de otro test.
- `data-testid` se permite en E2E cuando el elemento no tiene un rol fiable,
  pero se documenta el por que. En componentes de UI, se prefiere el rol.
- Nada de esperas fijas (`waitForTimeout`). Se espera por condicion:
  `await expect(locator).toBeVisible()`.
- La cantidad de E2E es un presupuesto: mas de 20 E2E hace el pipeline lento es un
  problema de arquitectura, no de testing.

### Paso 7 - Cobertura util

La cobertura se mide por capa, con umbrales distintos:

| Capa | Umbral | Razon |
|---|---|---|
| Funciones puras y hooks | 90% | Son logica pura, se prueba todo |
| Componentes | 70-80% | Mucho es markup |
| E2E | No se mide | El SUT es la aplicacion completa |

**Reglas:**

- La cobertura no es el objetivo. Es el detector de codigo muerto.
- Un uncovered branch que es logica de negocio es un bug pendiente.
- El umbral esta en la config y falla el build. No es un numero que se mira
  una vez.
- Los archivos de test, stories y utilidades quedan excluidos del calculo.

## Anti-patrones

| Anti-patron | Por que falla | Que hacer |
|---|---|---|
| `getByTestId` en todo | No describe la intencion, no valida accesibilidad | Queries por rol |
| `container.querySelector` | Acoplado al markup | `getByRole` |
| Testear estado interno | No le importa al usuario | Verificar lo visible |
| Snapshot de componente completo | Cambia siempre, nadie lo lee | Snapshot solo de datos |
| Mockear `useState` o `useRouter` | No se prueba nada real | MSW + router de test |
| `vi.mock` de la libreria entera | El test verifica el mock | Probar la app real |
| Sin `userEvent.setup()` | Eventos encolados, test pasa por el motivo equivocado | `setup()` en cada test |
| Olvidar `await` en el click | Test flaky | `await usuario.click()` |
| `server.use()` sin `resetHandlers` | El error se filtra al siguiente test | `resetHandlers` en `afterEach` |
| Mockear `fetch` a mano | Se testea el mock, no la app | MSW |
| `waitForTimeout(1000)` | Espera fija, CI lento y flaky | Esperar por condicion |
| E2E para todo | Pipeline lento e inestable | E2E solo para flujos |
| Un test con tres asserts de tres sitios | Cuando falla, no se sabe cual | Un comportamiento por test |
| Nombres de test mecanicos | No documentan nada | Describir el comportamiento |
| Snapshot sin revisar | El snapshot nuevo se aprueba sin leer | Revisar el diff del snapshot |

## Referencias

### Skills relacionadas

- `dev-kit-frontend-stack` - arquitectura del frontend, estado y data fetching.
- `dev-kit-testing` - estrategia de tests transversal, piramide y fixtures.
- `dev-kit-code-quality` - lint, tipos y gates de calidad del frontend.
- `dev-kit-ci-cd` - pipeline donde corren los tests.

### Archivos de esta skill

- `references/vitest-setup.md` - configuracion completa de Vitest, RTL y MSW.
- `references/playwright-e2e.md` - E2E, datos de prueba y debugging de flakes.
- `references/queries-y-roles.md` - tabla completa de queries y como elegir la correcta.
