"""Logging estructurado en JSON con correlation id y redaccion de sensibles.

Implementacion de referencia para `dev-kit-observability`.

Uso basico:
    from app.core.logger import get_logger, configure_logging

    configure_logging("INFO")
    log = get_logger(__name__)
    log.info("order_created", order_id=order.id, total=order.total)

Uso con correlation id (por peticion):
    from app.core.logger import correlation_scope

    with correlation_scope() as cid:
        log.info("request_started")

El correlation id se toma del header entrante si existe, o se genera.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Iterator

# --------------------------------------------------------------------- contexto

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

# Campos que nunca deben aparecer en un log.
SENSITIVE_FIELDS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "access_key",
        "authorization",
        "auth",
        "cookie",
        "session",
        "ssn",
        "credit_card",
        "card_number",
        "cvv",
        "private_key",
        "refresh_token",
        "client_secret",
    }
)

REDACTED = "<redacted>"

# Atributos internos del LogRecord que no son campos del usuario.
_RESERVED = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


def get_correlation_id() -> str | None:
    """Devuelve el correlation id del contexto actual."""
    return _correlation_id.get()


def set_correlation_id(value: str) -> None:
    """Fija el correlation id en el contexto actual."""
    _correlation_id.set(value)


@contextmanager
def correlation_scope(value: str | None = None) -> Iterator[str]:
    """Abre un scope con correlation id.

    Si no se pasa valor, se genera uno. Al salir, se restaura el anterior.
    """
    cid = value or uuid.uuid4().hex[:12]
    token = _correlation_id.set(cid)
    try:
        yield cid
    finally:
        _correlation_id.reset(token)


def redact(value: Any) -> Any:
    """Reemplaza valores sensibles por un marcador."""
    if isinstance(value, dict):
        return {
            key: (REDACTED if str(key).lower() in SENSITIVE_FIELDS else redact(val))
            for key, val in value.items()
        }
    if isinstance(value, (list, tuple)):
        return type(value)(redact(item) for item in value)
    return value


# ------------------------------------------------------------------- formatters


class JsonFormatter(logging.Formatter):
    """Serializa cada registro como una linea JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        cid = get_correlation_id()
        if cid:
            payload["correlation_id"] = cid

        for key, value in record.__dict__.items():
            if key in _RESERVED:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(redact(payload), default=str, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Formato legible para desarrollo."""

    def format(self, record: logging.LogRecord) -> str:
        cid = get_correlation_id()
        prefix = f"[{cid}] " if cid else ""
        base = f"{prefix}{record.levelname:<7} {record.name}: {record.getMessage()}"
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _RESERVED and not key.startswith("_")
        }
        if extras:
            base += " " + " ".join(f"{k}={v}" for k, v in sorted(extras.items()))
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


# ------------------------------------------------------------------ configuracion


def configure_logging(level: str = "INFO", json_output: bool | None = None) -> None:
    """Configura el logging root.

    Args:
        level: nivel minimo a registrar.
        json_output: True fuerza JSON, False fuerza texto, None decide por entorno.
    """
    if json_output is None:
        import os

        json_output = os.environ.get("LOG_FORMAT", "json").lower() == "json"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if json_output else ConsoleFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Las librerias de terceros son ruidosas: bajan a WARNING.
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger con soporte de campos extra.

    Uso:
        log = get_logger(__name__)
        log.info("order_created", order_id=1)
    """
    logger = logging.getLogger(name)

    # Evita duplicar el handler si se llama varias veces.
    if not logger.handlers and not logger.propagate:
        logger.addHandler(logging.NullHandler())

    return logger


class StructuredLogger:
    """Wrapper que fuerza el formato `message, **fields`."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def _log(self, level: int, event: str, exc_info: bool = False, **fields: Any) -> None:
        self._logger.log(level, event, exc_info=exc_info, extra=fields)

    def debug(self, event: str, **fields: Any) -> None:
        self._log(logging.DEBUG, event, **fields)

    def info(self, event: str, **fields: Any) -> None:
        self._log(logging.INFO, event, **fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._log(logging.WARNING, event, **fields)

    def error(self, event: str, exc_info: bool = True, **fields: Any) -> None:
        self._log(logging.ERROR, event, exc_info=exc_info, **fields)

    def critical(self, event: str, exc_info: bool = True, **fields: Any) -> None:
        self._log(logging.CRITICAL, event, exc_info=exc_info, **fields)


def structured(name: str) -> StructuredLogger:
    """Devuelve un logger que acepta campos extra."""
    return StructuredLogger(get_logger(name))
