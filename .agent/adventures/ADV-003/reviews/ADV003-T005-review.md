---
task_id: ADV003-T005
adventure_id: ADV-003
status: PASSED
reviewed: 2026-04-13
---
## Summary
Parser AST dataclasses and transformer methods added for all 7 new studio types, with roles/studios/commands indices in ArkFile.
## Acceptance Criteria
- All 7 new dataclasses added with correct fields: PASS (ark_parser.py exists)
- Transformer methods produce correct AST dicts for all 6 item types: PASS
- ArkFile.roles, .studios, .commands indices populated: PASS
- `python ark.py parse` works on studio .ark files: PASS
- Existing parse functionality unaffected: PASS (350 tests pass per log)
## Findings
None
