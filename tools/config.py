from __future__ import annotations

import os


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int, *, min_value: int | None = None, max_value: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if min_value is not None and value < min_value:
        return default
    if max_value is not None and value > max_value:
        return default
    return value


def _env_float(name: str, default: float, *, min_value: float | None = None, max_value: float | None = None) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if min_value is not None and value < min_value:
        return default
    if max_value is not None and value > max_value:
        return default
    return value


LOG_FORMAT = os.getenv("ADH_LOG_FORMAT", "%(asctime)s [%(levelname)s] %(message)s")
LOG_LEVEL = os.getenv("ADH_LOG_LEVEL", "INFO")
LOG_JSON = _env_bool("ADH_LOG_JSON", False)

FETCH_USER_AGENT = os.getenv(
    "ADH_FETCH_USER_AGENT",
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
)
FETCH_CACHE_MAX_SIZE = _env_int("ADH_FETCH_CACHE_MAX_SIZE", 512, min_value=1)
FETCH_DEFAULT_RETRIES = _env_int("ADH_FETCH_RETRIES", 2, min_value=0)
FETCH_DEFAULT_TIMEOUT_SEC = _env_int("ADH_FETCH_TIMEOUT_SEC", 18, min_value=1)
FETCH_RETRY_SLEEP_SEC = _env_float("ADH_FETCH_RETRY_SLEEP_SEC", 0.4, min_value=0.0)
FETCH_SSL_VERIFY = _env_bool("ADH_FETCH_SSL_VERIFY", True)

AGENT_HUB_DEFAULT_HOST = os.getenv("ADH_AGENT_HUB_HOST", "127.0.0.1")
AGENT_HUB_DEFAULT_PORT = _env_int("ADH_AGENT_HUB_PORT", 8787, min_value=1, max_value=65535)
AGENT_HUB_MAX_REQUEST_BODY_BYTES = _env_int("ADH_AGENT_HUB_MAX_BODY_BYTES", 1_048_576, min_value=1_024)
AGENT_HUB_SCRIPT_TIMEOUT_SEC = _env_int("ADH_AGENT_HUB_SCRIPT_TIMEOUT_SEC", 600, min_value=1)
