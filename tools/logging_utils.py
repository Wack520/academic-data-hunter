from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from tools.config import LOG_FORMAT, LOG_JSON, LOG_LEVEL


class JsonLogFormatter(logging.Formatter):
    """Minimal JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str | int | None = None, *, json_logs: bool | None = None) -> None:
    """Configure root logging once per entrypoint.

    - Default level/format comes from tools.config.
    - Set ADH_LOG_JSON=1 for JSON logs.
    """
    resolved_level: int
    if isinstance(level, int):
        resolved_level = level
    else:
        level_name = (level or LOG_LEVEL).upper()
        resolved_level = getattr(logging, level_name, logging.INFO)

    use_json = LOG_JSON if json_logs is None else json_logs
    if use_json:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonLogFormatter())
        logging.basicConfig(level=resolved_level, handlers=[handler], force=True)
        return

    logging.basicConfig(level=resolved_level, format=LOG_FORMAT, force=True)
