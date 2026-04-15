## Summary

- What does this PR change?
- Why is this change needed?

## Scope

- [ ] docs / README
- [ ] scripts
- [ ] tools
- [ ] cases
- [ ] CI / repo config

## Verification

Please paste the commands you ran and the result summary.

```bash
python scripts/check_dependency_sync.py
python scripts/check_docs_command_paths.py
python -m ruff check .
python -m ruff format --check .
python -m mypy tools/ --ignore-missing-imports
python -m compileall -q scripts tools cases
python -m pytest -q
```

## Notes

- Any follow-up work?
- Any compatibility / migration concerns?
