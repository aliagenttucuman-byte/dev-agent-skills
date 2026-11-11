# Dev Agent Skills

**Biblioteca de skills genéricas para equipos de agentes de IA que desarrollan software.**

Cada skill es una unidad de conocimiento procedural: un trigger claro, un
workflow con pasos verificables, artefactos que produce, gates que no se pueden
saltar, y anti-patrones con su por que.

Este repo **no contiene datos de cliente**. Es conocimiento destilado, escrito
para ser instalado y usado por cualquiera. La genericidad no es una promesa
editorial: la verifica un scanner (`dev-agent-kit/scripts/scan_clean.py`) que
falla el build si aparece un nombre de cliente, una persona o una ruta de una
maquina concreta.

---

## Instalacion

```bash
git clone https://github.com/aliagenttucuman-byte/dev-agent-skills.git
bash ../dev-agent-kit/scripts/install.sh --target ~/.hermes/skills --profile standard
```

Perfiles: `minimal` (metodologia, 8 skills) · `standard` (metodologia + agentes
+ ingenieria, 21) · `full` (todo, 24).

---

## Como esta organizada

```
dev-agent-skills/
├── skills/                     # la biblioteca
│   └── dev-kit-<area>-<tema>/
│       ├── SKILL.md            # trigger, workflow, gates, anti-patrones
│       ├── references/         # detalle largo y casos
│       ├── templates/          # artefactos copiables
│       └── scripts/            # verificadores ejecutables
├── spec/                       # la spec de ESTE producto (dogfooding)
│   ├── CONSTITUTION.md         # principios no negociables
│   ├── product-spec.md         # que es, para quien, que entrega
│   └── skill-contract.md       # el contrato que debe cumplir una skill
├── docs/                       # catalogo, guia de autoria, changelog
└── README.md
```

Areas: `methodology` (SDD) · `agents` (roster, routing, orquestacion) ·
`engineering` (calidad, stacks, datos, seguridad, CI/CD, observabilidad,
documentacion, testing, review) · `vertical` (RAG, browser, documentos).

---

## La metodologia que codifica

```
CONSTITUCION -> SPEC -> CLARIFICAR -> PLAN -> ESTIMAR -> ANALIZAR
   -> TAREAS -> CHECKLIST -> IMPLEMENTAR
```

Cada fase produce un artefacto escrito y tiene un gate. Un agente no avanza de
fase sin evidencia. Es el flujo de `dev-kit-sdd-workflow`.

---

## Contrato de una skill

Una skill entra a este repo si cumple las 5 condiciones de
`spec/skill-contract.md`:

1. Trigger explicito en la primera linea (cuando cargarla).
2. Workflow con pasos verificables y artefacto por paso.
3. Gates explícitos (que bloquea el avance y como se verifica).
4. Anti-patrones con la razon del fallo.
5. Cero datos de cliente: ni personas, ni marcas, ni rutas concretas.

La quinta se verifica automaticamente. Las otras cuatro las revisa un humano.

---

## Dogfooding

Este repo se construye con su propia metodologia: la spec de este producto esta
en `spec/`, escrita en el formato que las skills de este repo enseñan. Si una
skill nueva contradice la spec, se actualiza la spec.

---

## Licencia

MIT.
