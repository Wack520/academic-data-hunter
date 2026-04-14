from __future__ import annotations

import json
import logging

from tools.logging_utils import JsonLogFormatter


def test_json_log_formatter_outputs_expected_fields() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.logger"
    assert payload["message"] == "hello world"
    assert "timestamp" in payload
