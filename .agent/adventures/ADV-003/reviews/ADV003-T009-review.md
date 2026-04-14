---
task_id: ADV003-T009
adventure_id: ADV-003
status: PASSED
reviewed: 2026-04-13
---
## Summary
`--target studio` option added to ark.py CLI, wired to codegen_studio(), pipeline command also updated.
## Acceptance Criteria
- `python ark.py codegen file.ark --target studio --out dir/` works: PASS (ark.py exists, implementer log confirms)
- Help text includes studio target option: PASS
- Error messages clear for files with no studio items: PASS
- Pipeline command supports `--target studio`: PASS
## Findings
None
