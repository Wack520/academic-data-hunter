from __future__ import annotations

from scripts.summarize_workspace_changes import build_report, parse_status_porcelain


def test_parse_status_porcelain_parses_common_rows() -> None:
    rows = parse_status_porcelain(
        "\n".join(
            [
                " M README.md",
                "A  scripts/new_file.py",
                " D tools/old.py",
                "?? tmp/untracked.txt",
            ]
        )
    )
    assert len(rows) == 4
    assert rows[0].kind == "modified"
    assert rows[1].kind == "added"
    assert rows[2].kind == "deleted"
    assert rows[3].kind == "untracked"


def test_parse_status_porcelain_strips_wrapping_quotes() -> None:
    rows = parse_status_porcelain(' M "cases/case01-nev-carbon/data/中文.md"\n')
    assert rows[0].path == "cases/case01-nev-carbon/data/中文.md"


def test_build_report_contains_summary_tables() -> None:
    rows = parse_status_porcelain(" M README.md\n?? tests/new_test.py\n")
    report = build_report(rows)
    assert "Total changed paths" in report
    assert "| Top-level | Count | Breakdown |" in report
    assert "Suggested review batches" in report
