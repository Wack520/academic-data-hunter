from __future__ import annotations

import sys
from pathlib import Path

from scripts import check_dependency_sync, check_mcp_servers


def test_check_dependency_sync_main_pass(tmp_path: Path, monkeypatch) -> None:
    pyproject = tmp_path / "pyproject.toml"
    requirements = tmp_path / "requirements.txt"

    pyproject.write_text(
        """
[project]
name = "demo"
version = "0.0.1"
dependencies = [
  "requests>=2.32,<3.0",
  "pydantic>=2.8,<3.0",
]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    requirements.write_text(
        """
requests>=2.32,<3.0
pydantic>=2.8,<3.0  # inline comment
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_dependency_sync.py",
            "--pyproject",
            str(pyproject),
            "--requirements",
            str(requirements),
        ],
    )
    assert check_dependency_sync.main() == 0


def test_check_dependency_sync_main_fail(tmp_path: Path, monkeypatch) -> None:
    pyproject = tmp_path / "pyproject.toml"
    requirements = tmp_path / "requirements.txt"

    pyproject.write_text(
        """
[project]
name = "demo"
version = "0.0.1"
dependencies = [
  "requests>=2.32,<3.0",
  "pydantic>=2.8,<3.0",
]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    requirements.write_text("requests>=2.32,<3.0\n", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_dependency_sync.py",
            "--pyproject",
            str(pyproject),
            "--requirements",
            str(requirements),
        ],
    )
    assert check_dependency_sync.main() == 1


def test_default_codex_config_path_uses_env(monkeypatch) -> None:
    custom = Path("D:/custom/codex/config.toml")
    monkeypatch.setenv("CODEX_CONFIG", str(custom))
    assert check_mcp_servers.default_codex_config_path() == custom


def test_check_mcp_servers_main_missing_config_exits(monkeypatch, tmp_path: Path) -> None:
    missing = tmp_path / "not-found.toml"
    monkeypatch.setattr(check_mcp_servers, "configure_logging", lambda: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_mcp_servers.py", "--config", str(missing)],
    )
    try:
        check_mcp_servers.main()
    except SystemExit as exc:
        assert exc.code == 1
    else:  # pragma: no cover
        raise AssertionError("expected SystemExit(1)")


def test_check_mcp_servers_main_invalid_mcp_section_exits(monkeypatch, tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text('mcp_servers = "invalid"\n', encoding="utf-8")

    monkeypatch.setattr(check_mcp_servers, "configure_logging", lambda: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_mcp_servers.py", "--config", str(config)],
    )
    try:
        check_mcp_servers.main()
    except SystemExit as exc:
        assert exc.code == 1
    else:  # pragma: no cover
        raise AssertionError("expected SystemExit(1)")


def test_check_mcp_servers_main_runs_with_missing_and_found(monkeypatch, tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        """
[mcp_servers.tavily-proxy]
command = "npx"
args = ["-y", "dummy"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(check_mcp_servers, "configure_logging", lambda: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_mcp_servers.py", "--config", str(config), "--required", "tavily-proxy,exa-proxy"],
    )
    check_mcp_servers.main()


def test_check_mcp_servers_main_all_required_found(monkeypatch, tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        """
[mcp_servers.tavily-proxy]
command = "npx"
args = ["-y", "dummy"]

[mcp_servers.exa-proxy]
command = "npx"
args = ["-y", "dummy"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(check_mcp_servers, "configure_logging", lambda: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_mcp_servers.py", "--config", str(config), "--required", "tavily-proxy,exa-proxy"],
    )
    check_mcp_servers.main()
