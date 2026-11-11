# Playwright E2E

End-to-end es un presupuesto, no una estrategia. Cada E2E cuesta minutos de
pipeline y es la capa mas fragile. Se usa solo para lo que cruza el navegador.

---

## Que merece un E2E

| Si cruza... | E2E |
|---|---|
| Navegacion y rutas | Si |
| Formulario largo con validacion | Si |
| Integracion con un tercero real | Si |
| Flujo de pago o suscripcion | Si |
| Un solo componente | No, RTL |
| Logica de negocio | No, test de unidad |
| Un endpoint | No, test de integracion |

**Regla de presupuesto:** si el E2E falla, el equipo tiene que ir a mirar el
navegador. Eso cuesta 10 minutos. Con 30 E2E, el pipeline es un problema.

---

## playwright.config.ts

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  reporter: process.env.CI
    ? [["github"], ["html", { open: "never" }]]
    : [["list"]],
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:4173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 10_000,
  },
  webServer: {
    command: "npm run build && npm run preview -- --port 4173",
    url: "http://localhost:4173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
```

**Claves:**

- `actionTimeout: 10_000`: una accion que no responde en 10s es un error, no
  un cuelgue silencioso.
- `expect.timeout: 5_000`: la espera por condicion.
- `retries: 2` solo en CI. Localmente, un retry esconde un bug.
- `forbidOnly: true` en CI: un `test.only` commiteado no debe hacer pasar el
  pipeline saltando el resto.

---

## Estructura de una spec

```ts
// e2e/checkout.spec.ts
import { expect, test } from "@playwright/test";

test.describe("checkout", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/productos/1");
  });

  test("agrega al carrito y muestra el total", async ({ page }) => {
    await page.getByRole("button", { name: /agregar al carrito/i }).click();

    await expect(page.getByRole("status")).toHaveText(/1 producto/i);
    await expect(page.getByTestId("total-carrito")).toHaveText("$1.00");
  });

  test("impide checkout con carrito vacio", async ({ page }) => {
    await page.goto("/carrito");
    await expect(page.getByRole("button", { name: /finalizar/i })).toBeDisabled();
  });
});
```

---

## Datos de prueba

Cada E2E crea sus propios datos. Un E2E que depende de datos de otro test
es flaky por construccion.

```ts
// e2e/fixtures/usuario.ts
import { test as base, expect } from "@playwright/test";

export const test = base.extend({
  usuarioRegistrado: async ({ page }, use) => {
    const sufijo = Date.now();
    await page.goto("/registro");
    await page.getByRole("textbox", { name: /correo/i }).fill(`u${sufijo}@test.com`);
    await page.getByRole("textbox", { name: /contrasena/i }).fill("Clave123!");
    await page.getByRole("button", { name: /crear cuenta/i }).click();
    await expect(page.getByRole("heading", { name: /bienvenido/i })).toBeVisible();
    await use();
  },
});

export { expect };
```

**Reglas:**

- El sufijo unico (`Date.now()`, `crypto.randomUUID()`) evita colisiones entre
  workers paralelos.
- Los datos se crean via la API cuando se puede: es mas rapido y mas
  confiable que la UI.
- Los datos de prueba se identifican con un prefijo (por ejemplo `e2e-`) para
  poder limpiarlos.

---

## Crear datos por API desde el test

```ts
import { test as base } from "@playwright/test";

export const test = base.extend({
  pedido: async ({ request }, use) => {
    const respuesta = await request.post("/api/pedidos", {
      data: { total: 100, productos: ["1"] },
    });
    const pedido = await respuesta.json();
    await use(pedido);
  },
});
```

El `request` fixture de Playwright no pasa por el navegador: es mas rapido y
no depende de la UI.

---

## Debugging de flakes

```bash
# Ver el trace de una prueba fallida
npx playwright show-trace test-results/test-name/trace.zip

# Re-run solo el que fallo, con el UI de Playwright
npx playwright test --last-failed --debug

# headed: ver el navegador
npx playwright test --headed

# mas lento, paso a paso
npx playwright test --debug

# repetir 10 veces para detectar intermitencia
npx playwright test --repeat-each=10
```

**Causas de flake, en orden de frecuencia:**

1. **Espera fija.** `await page.waitForTimeout(1000)`. Se reemplaza por
   `await expect(locator).toBeVisible()`.
2. **Datos compartidos.** Dos tests usan el mismo usuario. Se resuelve con
   sufijo unico.
3. **Animaciones.** El elemento esta presente pero no clickeable. Se espera
   `toBeEnabled()` o se desactiva la animacion en el entorno de test.
4. **Carreras de red.** El test clickea antes de que el boton se habilite.
   Se espera la condicion.
5. **Orden de ejecucion.** Un test depende de otro. Se rompe la dependencia.

```ts
// MAL
await page.waitForTimeout(2000);
await page.getByRole("button", { name: /pagar/i }).click();

// BIEN
await expect(page.getByRole("button", { name: /pagar/i })).toBeEnabled();
await page.getByRole("button", { name: /pagar/i }).click();
```

---

## Onboarding de selectores

Un E2E nuevo no debe romper los E2E viejos. Los selectores se exposure en un
unico lugar:

```ts
// e2e/selectors.ts
export const selectors = {
  botonPagar: "button[data-testid='pagar']",
  totalCarrito: "[data-testid='total-carrito']",
};
```

Los `data-testid` se permiten en E2E. En los componentes de UI se prefiere el
rol, pero un `data-testid` estable para un elemento sin rol confiable es una
decision valida si se documenta.

---

## Integracion con CI

```yaml
- name: install browsers
  run: npx playwright install --with-deps chromium

- name: run e2e
  run: npx playwright test
  env:
    BASE_URL: http://localhost:4173

- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-report
    path: |
      playwright-report/
      test-results/
```

El artefacto se sube **solo si falla**: el reporte es grande y no se necesita
cuando todo pasa.

---

## Checklist de E2E

- [ ] Cada spec es independiente del orden
- [ ] Los datos son unicos por test
- [ ] Cero esperas fijas
- [ ] Las esperas son por condicion, no por tiempo
- [ ] El `webServer` levanta la app solo
- [ ] El trace se activa en reintento
- [ ] El reporte se sube como artefacto en fallo
- [ ] El numero de E2E esta por debajo del presupuesto acordado
