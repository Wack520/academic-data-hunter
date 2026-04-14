from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.check_docs_command_paths import _extract_python_script_refs, check_docs_command_paths


def test_extract_python_script_refs_filters_module_mode() -> None:
    text = """
python scripts/run_round.py --data a.csv
python -m pytest -q
py tools/qc_checker.py data.csv
"""
    refs = _extract_python_script_refs(text)
    assert refs == [(2, "scripts/run_round.py"), (4, "tools/qc_checker.py")]


def test_check_docs_command_paths_supports_repo_and_doc_relative(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts"
    docs_dir = tmp_path / "docs"
    scripts_dir.mkdir()
    docs_dir.mkdir()
    (scripts_dir / "ok.py").write_text("print('ok')\n", encoding="utf-8")

    (tmp_path / "README.md").write_text(
        "```bash\npython scripts/ok.py\n```\n",
        encoding="utf-8",
    )
    (docs_dir / "guide.md").write_text(
        "```bash\npython ../scripts/ok.py\n```\n",
        encoding="utf-8",
    )

    issues = check_docs_command_paths(tmp_path, ["README.md", "docs"])
    assert issues == []


def test_check_docs_command_paths_ignores_placeholders_and_reports_missing(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text(
        """
python tools/<your_api_script>.py --indicator x
python $SCRIPT_DIR/bootstrap.py
python scripts/not_exists.py --foo bar
python -m ruff check .
""",
        encoding="utf-8",
    )

    issues = check_docs_command_paths(tmp_path, ["docs"])
    assert len(issues) == 1
    issue = issues[0]
    assert issue.markdown_file == (docs_dir / "guide.md").resolve()
    assert issue.script_ref == "scripts/not_exists.py"


def test_check_docs_command_paths_does_not_ignore_scan_root_under_tmp_named_ancestor(tmp_path: Path) -> None:
    root = tmp_path / "tmp" / "project"
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / "guide.md").write_text("python scripts/not_exists.py --foo bar\n", encoding="utf-8")

    issues = check_docs_command_paths(root, ["docs"])
    assert len(issues) == 1
    assert issues[0].script_ref == "scripts/not_exists.py"


def test_check_docs_command_paths_cli_bootstraps_without_site_packages() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-S", "scripts/check_docs_command_paths.py", "--paths", "README.md"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
