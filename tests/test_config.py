from __future__ import annotations

import importlib

from tools import config as config_module


def test_env_bool_cases(monkeypatch) -> None:
    monkeypatch.delenv("ADH_TEST_BOOL", raising=False)
    assert config_module._env_bool("ADH_TEST_BOOL", default=True) is True
    assert config_module._env_bool("ADH_TEST_BOOL", default=False) is False

    monkeypatch.setenv("ADH_TEST_BOOL", " yes ")
    assert config_module._env_bool("ADH_TEST_BOOL", default=False) is True

    monkeypatch.setenv("ADH_TEST_BOOL", "0")
    assert config_module._env_bool("ADH_TEST_BOOL", default=True) is False


def test_env_int_cases(monkeypatch) -> None:
    monkeypatch.delenv("ADH_TEST_INT", raising=False)
    assert config_module._env_int("ADH_TEST_INT", 10) == 10

    monkeypatch.setenv("ADH_TEST_INT", "abc")
    assert config_module._env_int("ADH_TEST_INT", 10) == 10

    monkeypatch.setenv("ADH_TEST_INT", "5")
    assert config_module._env_int("ADH_TEST_INT", 10, min_value=6) == 10
    assert config_module._env_int("ADH_TEST_INT", 10, max_value=4) == 10
    assert config_module._env_int("ADH_TEST_INT", 10, min_value=1, max_value=20) == 5


def test_env_float_cases(monkeypatch) -> None:
    monkeypatch.delenv("ADH_TEST_FLOAT", raising=False)
    assert config_module._env_float("ADH_TEST_FLOAT", 1.5) == 1.5

    monkeypatch.setenv("ADH_TEST_FLOAT", "abc")
    assert config_module._env_float("ADH_TEST_FLOAT", 1.5) == 1.5

    monkeypatch.setenv("ADH_TEST_FLOAT", "0.25")
    assert config_module._env_float("ADH_TEST_FLOAT", 1.5, min_value=0.3) == 1.5
    assert config_module._env_float("ADH_TEST_FLOAT", 1.5, max_value=0.2) == 1.5
    assert config_module._env_float("ADH_TEST_FLOAT", 1.5, min_value=0.0, max_value=1.0) == 0.25


def test_reload_constants_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("ADH_LOG_JSON", "1")
    monkeypatch.setenv("ADH_FETCH_RETRIES", "7")
    monkeypatch.setenv("ADH_FETCH_TIMEOUT_SEC", "25")
    monkeypatch.setenv("ADH_FETCH_RETRY_SLEEP_SEC", "0.7")
    monkeypatch.setenv("ADH_FETCH_SSL_VERIFY", "0")
    monkeypatch.setenv("ADH_AGENT_HUB_PORT", "9900")
    monkeypatch.setenv("ADH_AGENT_HUB_MAX_BODY_BYTES", "2048")
    monkeypatch.setenv("ADH_AGENT_HUB_SCRIPT_TIMEOUT_SEC", "123")

    reloaded = importlib.reload(config_module)
    assert reloaded.LOG_JSON is True
    assert reloaded.FETCH_DEFAULT_RETRIES == 7
    assert reloaded.FETCH_DEFAULT_TIMEOUT_SEC == 25
    assert abs(reloaded.FETCH_RETRY_SLEEP_SEC - 0.7) < 1e-9
    assert reloaded.FETCH_SSL_VERIFY is False
    assert reloaded.AGENT_HUB_DEFAULT_PORT == 9900
    assert reloaded.AGENT_HUB_MAX_REQUEST_BODY_BYTES == 2048
    assert reloaded.AGENT_HUB_SCRIPT_TIMEOUT_SEC == 123

    monkeypatch.setenv("ADH_AGENT_HUB_PORT", "99999")  # out of max range
    monkeypatch.setenv("ADH_AGENT_HUB_MAX_BODY_BYTES", "1000")  # below min
    monkeypatch.setenv("ADH_AGENT_HUB_SCRIPT_TIMEOUT_SEC", "0")  # below min
    reloaded_again = importlib.reload(config_module)
    assert reloaded_again.AGENT_HUB_DEFAULT_PORT == 8787
    assert reloaded_again.AGENT_HUB_MAX_REQUEST_BODY_BYTES == 1_048_576
    assert reloaded_again.AGENT_HUB_SCRIPT_TIMEOUT_SEC == 600
