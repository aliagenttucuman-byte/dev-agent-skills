#!/usr/bin/env python3
"""route.py - routing declarativo de un objetivo a un agente.

Dado un objetivo en lenguaje natural, decide que agente lo resuelve, con
nivel de confianza, razones y fallback.

Uso:
    python3 route.py "agregar endpoint POST /orders con validacion"
    python3 route.py --file objetivos.txt
    python3 route.py --compact "revisar el modelo de datos"
    python3 route.py --taxonomy mi-taxonomia.json "mi objetivo"
    python3 route.py --min-confidence 0.5 "mi objetivo"

Solo stdlib. La taxonomia por defecto esta en TAXONOMY; se puede reemplazar
con un JSON externo usando --taxonomy.

Formato del JSON de taxonomia:
    {
      "BACKEND": {
        "agent": "backend",
        "keywords": ["api", "endpoint", ...],
        "synonyms": {"post": ["endpoint", "ruta"]}
      }
    }

Exit codes: 0 = ruta resuelta, 2 = error de uso, 3 = confianza baja.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ------------------------------------------------------------------ taxonomia

TAXONOMY: dict[str, dict] = {
    "SPEC": {
        "agent": "spec",
        "keywords": [
            "spec", "especificacion", "historia de usuario", "user story",
            "criterio de aceptacion", "criterios de aceptacion", "contrato",
            "openapi", "prd", "requerimiento", "requerimientos", "backlog",
            "alcance", "epica", "epicas", "caso de uso", "documento de requisitos",
        ],
        "synonyms": {
            "hu": ["historia de usuario", "user story"],
            "ca": ["criterio de aceptacion"],
            "api contract": ["contrato de api"],
        },
    },
    "BACKEND": {
        "agent": "backend",
        "keywords": [
            "api", "endpoint", "servicio", "python", "fastapi", "sqlalchemy",
            "modelo", "orm", "migracion", "job", "tarea asincrona", "webhook",
            "backend", "logica de negocio", "use case", "cola", "worker",
            "procesamiento", "validacion", "serializador", "schema",
        ],
        "synonyms": {
            "ruta": ["endpoint"],
            "controlador": ["endpoint"],
            "crud": ["api"],
            "async": ["tarea asincrona"],
        },
    },
    "FRONTEND": {
        "agent": "frontend",
        "keywords": [
            "componente", "ui", "interfaz", "react", "typescript", "vite",
            "hook", "store", "estado", "formulario", "css", "tailwind",
            "paginacion", "frontend", "pantalla", "render", "props", "layout",
            "accesibilidad", "responsive", "modal", "tabla",
        ],
        "synonyms": {
            "vista": ["pantalla", "componente"],
            "hook": ["estado"],
            "estilos": ["css"],
        },
    },
    "BROWSER": {
        "agent": "browser",
        "keywords": [
            "scraping", "scraper", "playwright", "selenium", "formulario web",
            "automatizacion web", "click", "captura de pantalla", "navegacion",
            "navegador", "browser", "headless", "crawl", "spider",
        ],
        "synonyms": {
            "web scraping": ["scraping"],
            "screenshots": ["captura de pantalla"],
        },
    },
    "INFRA": {
        "agent": "infra",
        "keywords": [
            "docker", "despliegue", "deploy", "kubernetes", "terraform",
            "pipeline", "ci", "cd", "infraestructura", "servidor", "dominio",
            "ssl", "tls", "certificado", "contenedor", "compose", "cloud",
            "nube", "servicio", "monitoreo", "proxy", "reverse proxy",
        ],
        "synonyms": {
            "deployment": ["despliegue"],
            "hosting": ["servidor"],
            "k8s": ["kubernetes"],
        },
    },
    "RAG_AI": {
        "agent": "rag",
        "keywords": [
            "rag", "embedding", "embeddings", "vector", "vectorial",
            "busqueda semantica", "chunk", "chunking", "retrieval",
            "vectorstore", "base de conocimiento", "indexacion", "llm",
            "prompt", "agente", "reindex",
        ],
        "synonyms": {
            "base vectorial": ["vectorstore"],
            "semantic search": ["busqueda semantica"],
            "rag pipeline": ["rag"],
        },
    },
    "QA": {
        "agent": "qa",
        "keywords": [
            "test", "tests", "prueba", "pruebas", "caso de prueba", "cobertura",
            "regresion", "e2e", "verificacion", "calidad", "bug", "qa",
            "assertion", "fixture", "mock", "playwright test", "smoke test",
        ],
        "synonyms": {
            "testing": ["test"],
            "unit tests": ["test"],
            "integracion": ["test"],
        },
    },
    "DOCS": {
        "agent": "docs",
        "keywords": [
            "readme", "documentacion", "adr", "changelog", "guia", "manual",
            "api docs", "docstring", "comentarios", "wiki", "kb", "knowledge base",
            "documentar", "docs",
        ],
        "synonyms": {
            "readme": ["documentacion"],
            "adr": ["decision record"],
        },
    },
    "VISION": {
        "agent": "vision",
        "keywords": [
            "imagen", "imagenes", "foto", "fotos", "video", "ocr", "deteccion",
            "objetos", "vision", "reconocimiento", "pixel", "camara", "captura",
            "segmentacion", "clase",
        ],
        "synonyms": {
            "fotos": ["imagenes"],
            "computer vision": ["vision"],
        },
    },
    "AUDIO": {
        "agent": "audio",
        "keywords": [
            "audio", "voz", "transcripcion", "whisper", "tts", "sonido",
            "podcast", "microfono", "musica", "locucion",
        ],
        "synonyms": {
            "speech to text": ["transcripcion"],
            "text to speech": ["tts"],
        },
    },
    "EXTERNAL": {
        "agent": "external",
        "keywords": [
            "api externa", "integracion", "webhooks", "proveedor", "moneda",
            "cotizacion", "email", "correo", "tercero", "servicio externo",
            "market data", "mercado",
        ],
        "synonyms": {
            "3rd party": ["proveedor", "servicio externo"],
            "mercado": ["market data"],
        },
    },
    "SECURITY": {
        "agent": "security",
        "keywords": [
            "seguridad", "vulnerabilidad", "autenticacion", "autorizacion",
            "permisos", "roles", "amenaza", "auditoria de codigo", "secretos",
            "secret", "token", "jwt", "sesion", "owasp", "cve", "xss",
            "sql injection", "sanitizar",
        ],
        "synonyms": {
            "auth": ["autenticacion", "autorizacion"],
            "vulnerabilidades": ["vulnerabilidad"],
        },
    },
}

# Pesos
EXACT_WEIGHT = 1.0
SYNONYM_WEIGHT = 0.8
TITLE_MULTIPLIER = 2.0

LOW_CONFIDENCE = 0.3
MEDIUM_CONFIDENCE = 0.6


# ------------------------------------------------------------------ scoring


def normalize(text: str) -> str:
    """Normaliza para comparar: minusculas, sin acentos, espacios colapsados."""
    import unicodedata

    text = text.lower().strip()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", text)


def _matches(text: str, keyword: str) -> bool:
    """True si el texto contiene el keyword.

    Los keywords de una sola palabra exigen limites de palabra: sin eso,
    'ci' matchea 'validacion' y 'api' matchea 'rapido'. Los keywords de
    varias palabras se buscan como frase, porque ahi el limite no aporta.
    """
    if " " in keyword:
        return keyword in text
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def score_category(goal: str, title: str, spec: dict) -> tuple[float, list[str]]:
    """Devuelve (score, razones) para una categoria."""
    score = 0.0
    reasons: list[str] = []

    for keyword in spec.get("keywords", []):
        kw = normalize(keyword)
        if not kw:
            continue
        if _matches(goal, kw):
            points = EXACT_WEIGHT
            if _matches(title, kw):
                points *= TITLE_MULTIPLIER
            score += points
            reasons.append(f"match exacto: '{keyword}' (+{points:.1f})")

    for synonym, originals in spec.get("synonyms", {}).items():
        syn = normalize(synonym)
        if syn and _matches(goal, syn):
            points = SYNONYM_WEIGHT
            score += points
            reasons.append(f"match de sinonimo: '{synonym}' (+{points:.1f})")

    return score, reasons


def route(goal: str, taxonomy: dict, title: str = "") -> dict:
    """Rutea un objetivo a un agente."""
    norm_goal = normalize(goal)
    norm_title = normalize(title)

    scored = []
    for category, spec in taxonomy.items():
        score, reasons = score_category(norm_goal, norm_title, spec)
        if score > 0:
            scored.append({
                "category": category,
                "agent": spec.get("agent", category.lower()),
                "score": round(score, 3),
                "reasons": reasons,
            })

    scored.sort(key=lambda item: item["score"], reverse=True)

    if not scored:
        return {
            "goal": goal,
            "category": None,
            "agent": "spec",
            "confidence": 0.0,
            "reasons": ["ninguna categoria coincidio"],
            "alternatives": [],
            "fallback": "revisar el objetivo antes de asignar",
            "needs_clarification": True,
        }

    best = scored[0]
    second_score = scored[1]["score"] if len(scored) > 1 else 0.0
    margin = best["score"] - second_score
    confidence = round(margin / best["score"], 3) if best["score"] else 0.0

    alternatives = [
        {
            "category": item["category"],
            "agent": item["agent"],
            "confidence": round(
                (item["score"] - (second_score if item is not scored[0] else 0.0)) / item["score"], 3
            ) if item["score"] else 0.0,
            "reasons": item["reasons"],
        }
        for item in scored[1:3]
    ]

    needs_clarification = confidence < LOW_CONFIDENCE
    fallback = None
    if confidence < LOW_CONFIDENCE:
        fallback = (
            f"confianza baja ({confidence}): pedir clarificacion antes de asignar. "
            f"Candidatas: {', '.join(item['category'] for item in scored[:3])}"
        )
    elif confidence < MEDIUM_CONFIDENCE:
        fallback = f"asignacion con confianza media ({confidence}): conviene confirmar el alcance"

    return {
        "goal": goal,
        "category": best["category"],
        "agent": best["agent"],
        "confidence": confidence,
        "reasons": best["reasons"],
        "alternatives": alternatives,
        "fallback": fallback,
        "needs_clarification": needs_clarification,
    }


# ---------------------------------------------------------------------- cli


def main() -> int:
    ap = argparse.ArgumentParser(description="Rutea un objetivo a un agente.")
    ap.add_argument("goal", nargs="?", help="El objetivo a enrutar")
    ap.add_argument("--file", help="Archivo con un objetivo por linea")
    ap.add_argument("--title", default="", help="Titulo de la tarea (pondera x2)")
    ap.add_argument("--taxonomy", help="JSON con una taxonomia alternativa")
    ap.add_argument("--compact", action="store_true", help="Salida de una linea")
    ap.add_argument("--min-confidence", type=float, default=0.0)
    args = ap.parse_args()

    taxonomy = TAXONOMY
    if args.taxonomy:
        path = Path(args.taxonomy)
        if not path.is_file():
            print(f"No existe el archivo de taxonomia: {path}", file=sys.stderr)
            return 2
        taxonomy = json.loads(path.read_text(encoding="utf-8"))

    goals: list[str] = []
    if args.goal:
        goals.append(args.goal)
    if args.file:
        path = Path(args.file)
        if not path.is_file():
            print(f"No existe el archivo: {path}", file=sys.stderr)
            return 2
        goals.extend(
            line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
        )

    if not goals:
        ap.error("se requiere un objetivo o --file")

    results = [route(g, taxonomy, args.title) for g in goals]

    if args.compact:
        for r in results:
            flag = "?" if r["needs_clarification"] else " "
            print(f"{flag} {r['agent']:<10} conf={r['confidence']:<5} {r['goal'][:60]}")
    elif len(results) == 1:
        print(json.dumps(results[0], indent=2, ensure_ascii=False))
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))

    min_conf = min(r["confidence"] for r in results)
    if min_conf < args.min_confidence:
        return 3
    if any(r["needs_clarification"] for r in results):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
