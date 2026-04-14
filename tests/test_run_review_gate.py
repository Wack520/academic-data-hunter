from __future__ import annotations

from pathlib import Path

from scripts.run_review_gate import CheckResult, build_markdown, run_check, trim_block


def test_trim_block_truncates_long_text() -> None:
    long_text = "a" * 5000
    trimmed = trim_block(long_text, limit=100)
    assert len(trimmed) <= 100
    assert "[truncated]" in trimmed


def test_build_markdown_includes_status_table() -> None:
    results = [
        CheckResult(
            name="dummy",
            command=["python", "--version"],
            returncode=0,
            duration_sec=0.123,
            stdout="ok",
            stderr="",
        )
    ]
    md = build_markdown(results, generated_at="2026-03-31T00:00:00+00:00", python_exe="python")
    assert "| dummy | ✅ |" in md
    assert "Overall: PASS" in md


def test_run_check_executes_subprocess(tmp_path: Path) -> None:
    script = tmp_path / "hello.py"
    script.write_text("print('hello')\n", encoding="utf-8")
    result = run_check("hello", ["python", str(script)], cwd=tmp_path)
    assert result.ok is True
    assert result.returncode == 0
    assert "hello" in result.stdout
