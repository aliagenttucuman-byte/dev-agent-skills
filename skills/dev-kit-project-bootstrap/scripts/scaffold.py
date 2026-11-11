#!/usr/bin/env python3
"""scaffold.py - genera la estructura base de un proyecto nuevo.

Genera un esqueleto de proyecto con backend, frontend, Docker y CI.
Solo stdlib: se ejecuta con cualquier Python 3.9+ sin instalar nada.

Uso:
    python3 scripts/scaffold.py --name mi-proyecto --out .
    python3 scripts/scaffold.py --name mi-proyecto --out ./proyectos --stack python-only
    python3 scripts/scaffold.py --name mi-proyecto --out . --dry-run

Opciones:
    --name       Nombre del proyecto (kebab-case). Requerido.
    --out        Directorio destino. Por defecto el actual.
    --stack      python-only | full (default: full)
    --dry-run    Muestra que se crearia sin escribir nada.
    --force      Sobrescribe archivos existentes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# ------------------------------------------------------------------ templates

PYPROJECT = """[project]
name = "{name}"
version = "0.1.0"
description = "{name}"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.9",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "psycopg[binary]>=3.2",
    "pydantic-settings>=2.5",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
    "ruff>=0.6",
    "mypy>=1.11",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]
"""

RUFF_CONFIG = """[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "C4", "SIM", "ANN", "S", "RUF"]
ignore = ["ANN401"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "ANN"]

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"
"""

MYPY_CONFIG = """[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_configs = true
disallow_untyped_defs = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
"""

MAIN_PY = '''"""Punto de entrada de la API."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    return app


app = create_app()
'''

CONFIG_PY = '''"""Configuracion por entorno."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "API"
    environment: str = "development"
    debug: bool = False

    database_url: str = "postgresql+psycopg://app:app@localhost:5432/app"
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
'''

LOGGING_PY = '''"""Logging estructurado en JSON."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "asctime", "message", "taskName",
}


class JsonFormatter(logging.Formatter):
    """Serializa el registro como una linea JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
'''

ROUTERS_INIT = '''"""Punto de entrada de los routers de la API."""

from fastapi import APIRouter

api_router = APIRouter()
'''

HEALTH_PY = '''"""Health check del servicio."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
'''

PYTEST_INIT = ""

CONFTEST_PY = '''"""Fixtures compartidas."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
'''

TEST_EXAMPLE = '''"""Ejemplo de test de endpoint."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
'''

DOCKERFILE = """FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[dev]"

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

DOCKER_COMPOSE = r"""services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      ENVIRONMENT: development
    volumes:
      - ./app:/app/app
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  pgdata:
"""

ENV_EXAMPLE = """ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/app
"""

GITIGNORE = """__pycache__/
*.py[cod]
.venv/
venv/
.env
.env.local
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
dist/
build/
node_modules/
.DS_Store
"""

CI_YML = r"""name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Instalar dependencias
        run: pip install ".[dev]"

      - name: Lint
        run: ruff check .

      - name: Formato
        run: ruff format --check .

      - name: Tipos
        run: mypy app

      - name: Tests
        run: pytest -q --cov=app --cov-report=term-missing

  build:
    needs: quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build de la imagen
        run: docker build -t ${{ github.repository }}:${{ github.sha }} .
"""

PACKAGE_JSON = """{
  "name": "__PROJECT_NAME__",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint .",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.5",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "eslint": "^9.10.0",
    "typescript": "^5.6.2",
    "vite": "^5.4.8",
    "vitest": "^2.1.1"
  }
}
"""

TSCONFIG = """{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "skipLibCheck": true,
    "isolatedModules": true,
    "noEmit": true
  },
  "include": ["src"]
}
"""

VITE_CONFIG = """import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
"""

INDEX_HTML = """<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""

MAIN_TSX = """import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";

const container = document.getElementById("root");
if (!container) {
  throw new Error("No se encontro el elemento #root");
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>
);
"""

APP_TSX = """export function App() {
  return (
    <main>
      <h1>{title}</h1>
    </main>
  );
}

const title = "{name}";
"""

GITLAB_CI = r"""stages:
  - quality
  - build

quality:
  stage: quality
  image: python:3.11
  script:
    - pip install ".[dev]"
    - ruff check .
    - ruff format --check .
    - mypy app
    - pytest -q

build:
  stage: build
  script:
    - docker build -t $CI_PROJECT_NAME:$CI_COMMIT_SHA .
  only:
    - main
"""

# ------------------------------------------------------------------ generador


def build_tree(name: str, stack: str) -> dict[str, str]:
    """Devuelve el mapa ruta -> contenido a crear."""
    tree: dict[str, str] = {}

    # Raiz
    tree[".gitignore"] = GITIGNORE
    tree["README.md"] = (
        f"# {name}\n\n\n## Requisitos\n\n"
        "- Python 3.11+\n- Node 20+\n- Docker (opcional)\n\n"
        "## Puesta en marcha\n\n```bash\n"
        "cp .env.example .env\n"
        "pip install -e \".[dev]\"\n"
        "uvicorn app.main:app --reload\n```\n\n"
        "## Comandos\n\n"
        "| Comando | Que hace |\n|---|---|\n"
        "| `ruff check .` | Lint |\n"
        "| `ruff format .` | Formato |\n"
        "| `mypy app` | Chequeo de tipos |\n"
        "| `pytest` | Tests |\n"
    )

    # Backend
    tree["pyproject.toml"] = PYPROJECT.format(name=name)
    tree["ruff.toml"] = RUFF_CONFIG
    tree["mypy.ini"] = MYPY_CONFIG
    tree["app/__init__.py"] = ""
    tree["app/main.py"] = MAIN_PY
    tree["app/core/__init__.py"] = ""
    tree["app/core/config.py"] = CONFIG_PY
    tree["app/core/logging.py"] = LOGGING_PY
    tree["app/api/__init__.py"] = ""
    tree["app/api/router.py"] = ROUTERS_INIT
    tree["app/api/v1/__init__.py"] = ""
    tree["app/api/v1/health.py"] = HEALTH_PY
    tree["app/domain/__init__.py"] = ""
    tree["app/infrastructure/__init__.py"] = ""
    tree["tests/__init__.py"] = PYTEST_INIT
    tree["tests/conftest.py"] = CONFTEST_PY
    tree["tests/test_health.py"] = TEST_EXAMPLE
    tree[".env.example"] = ENV_EXAMPLE
    tree["Dockerfile"] = DOCKERFILE
    tree["docker-compose.yml"] = DOCKER_COMPOSE
    tree[".github/workflows/ci.yml"] = CI_YML

    if stack == "full":
        tree["frontend/package.json"] = PACKAGE_JSON.replace("__PROJECT_NAME__", name)
        tree["frontend/tsconfig.json"] = TSCONFIG
        tree["frontend/vite.config.ts"] = VITE_CONFIG
        tree["frontend/index.html"] = INDEX_HTML.replace("__PROJECT_NAME__", name)
        tree["frontend/src/main.tsx"] = MAIN_TSX
        tree["frontend/src/App.tsx"] = APP_TSX.replace("__PROJECT_NAME__", name)
        tree["frontend/.gitignore"] = "node_modules/\ndist/\n"

    return tree


def main() -> int:
    ap = argparse.ArgumentParser(description="Genera el scaffold de un proyecto nuevo.")
    ap.add_argument("--name", required=True, help="Nombre del proyecto en kebab-case")
    ap.add_argument("--out", default=".", help="Directorio destino")
    ap.add_argument("--stack", default="full", choices=["full", "python-only"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    out_root = Path(args.out).expanduser().resolve()
    project_root = out_root / args.name
    tree = build_tree(args.name, args.stack)

    created: list[str] = []
    skipped: list[str] = []

    for rel, content in tree.items():
        dest = project_root / rel
        if dest.exists() and not args.force:
            skipped.append(rel)
            continue
        if args.dry_run:
            created.append(rel)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        created.append(rel)

    if args.dry_run:
        print(f"[dry-run] {len(created)} archivos a crear en {project_root}")
        for rel in created:
            print(f"  + {rel}")
        return 0

    print(f"Proyecto generado en {project_root}")
    print(f"  archivos creados: {len(created)}")
    if skipped:
        print(f"  omitidos (ya existian): {len(skipped)}")
        for rel in skipped:
            print(f"    = {rel}")

    print("\nSiguientes pasos:")
    print(f"  cd {args.name}")
    print("  cp .env.example .env")
    print('  pip install -e ".[dev]"')
    print("  uvicorn app.main:app --reload")
    if args.stack == "full":
        print("  cd frontend && npm install && npm run dev")
    print("\nVerificar con: ruff check . && mypy app && pytest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
