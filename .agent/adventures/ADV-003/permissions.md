---
adventure_id: ADV-003
status: pending_approval
created: 2026-04-13T20:00:00Z
approved: null
passes_completed: 4
validation_gaps: 0
---

# Permission Requests — ADV-003: Claude-Code-Game-Studios-style Studio Hierarchy in Ark DSL

## Summary
38 permissions across 14 tasks, 3 agents (planner, coder, code-reviewer). All 4 analysis passes complete. 0 validation gaps.

## Requests

### Shell Access
| # | Agent | Stage | Command | Reason | Tasks |
|---|-------|-------|---------|--------|-------|
| 1 | coder | implementing | `python ark.py parse <file>` | Validate .ark file parsing after grammar/parser changes | T002,T003,T005,T011,T012,T013 |
| 2 | coder | implementing | `python ark.py verify <file>` | Run Z3 verification on studio specs | T006,T007,T011,T012,T013 |
| 3 | coder | implementing | `python ark.py codegen <file> --target studio --out <dir>` | Generate studio artifacts | T008,T009,T013 |
| 4 | coder | implementing | `python ark.py graph <file>` | Generate org-chart visualization | T010,T013 |
| 5 | coder | implementing | `python ark.py pipeline <file> --target studio` | Run full pipeline end-to-end | T009,T013 |
| 6 | coder | implementing | `pytest tests/test_studio_*.py` | Run studio test suite | T014 |
| 7 | coder | implementing | `pytest tests/` | Run full test suite for regression | T003,T005,T014 |
| 8 | code-reviewer | reviewing | `python ark.py parse <file>` | Verify parsing works in review | all |
| 9 | code-reviewer | reviewing | `python ark.py verify <file>` | Verify Z3 checks in review | T006,T007,T011,T012 |
| 10 | code-reviewer | reviewing | `pytest tests/` | Run tests during review | all |

### File Access
| # | Agent | Stage | Scope | Mode | Reason | Tasks |
|---|-------|-------|-------|------|--------|-------|
| 1 | planner | planning | `R:/Sandbox/.agent/adventures/ADV-003/**` | read/write | Read designs, write test strategy | T001 |
| 2 | coder | implementing | `R:/Sandbox/ark/dsl/stdlib/studio.ark` | write | Create stdlib types | T002 |
| 3 | coder | implementing | `R:/Sandbox/ark/tools/parser/ark_grammar.lark` | read/write | Extend Lark grammar | T003 |
| 4 | coder | implementing | `R:/Sandbox/ark/dsl/grammar/ark.pest` | read/write | Extend pest grammar | T004 |
| 5 | coder | implementing | `R:/Sandbox/ark/tools/parser/ark_parser.py` | read/write | Add dataclasses and transformer | T005 |
| 6 | coder | implementing | `R:/Sandbox/ark/tools/verify/studio_verify.py` | write | Create studio verifier | T006,T007 |
| 7 | coder | implementing | `R:/Sandbox/ark/tools/verify/ark_verify.py` | read/write | Integrate studio verify | T006,T007 |
| 8 | coder | implementing | `R:/Sandbox/ark/tools/codegen/studio_codegen.py` | write | Create studio codegen | T008 |
| 9 | coder | implementing | `R:/Sandbox/ark/tools/codegen/ark_codegen.py` | read/write | Integrate studio target | T009 |
| 10 | coder | implementing | `R:/Sandbox/ark/ark.py` | read/write | Add studio CLI target | T009 |
| 11 | coder | implementing | `R:/Sandbox/ark/tools/visualizer/ark_visualizer.py` | read/write | Add org-chart rendering | T010 |
| 12 | coder | implementing | `R:/Sandbox/ark/specs/meta/ark_studio.ark` | write | Author Ark team studio | T011 |
| 13 | coder | implementing | `R:/Sandbox/ark/specs/meta/game_studio.ark` | write | Author game studio exemplar | T012 |
| 14 | coder | implementing | `R:/Sandbox/ark/specs/root.ark` | read/write | Register studio specs | T011,T012 |
| 15 | coder | implementing | `R:/Sandbox/ark/tests/test_studio_*.py` | write | Create test files | T014 |
| 16 | coder | implementing | `R:/Sandbox/ark/dsl/stdlib/*.ark` | read | Read existing stdlib for reference | T002 |
| 17 | coder | implementing | `R:/Sandbox/ark/specs/**/*.ark` | read | Read existing specs for reference | T011,T012,T013 |
| 18 | code-reviewer | reviewing | `R:/Sandbox/ark/**` | read | Read all project files for review | all |

### MCP Tools
| # | Agent | Stage | Tool | Reason | Tasks |
|---|-------|-------|------|--------|-------|
| 1 | planner | planning | Read | Read codebase for test strategy design | T001 |
| 2 | planner | planning | Glob | Find files for test strategy | T001 |
| 3 | planner | planning | Grep | Search codebase for patterns | T001 |
| 4 | planner | planning | Write | Write test strategy document | T001 |

### External Access
| # | Agent | Stage | Type | Target | Reason | Tasks |
|---|-------|-------|------|--------|--------|-------|
| (none required) | | | | | | |

## Validation Matrix

| Task | Agent | Stage | Read | Write | Shell | MCP | External | Verified |
|------|-------|-------|------|-------|-------|-----|----------|----------|
| T001 | planner | planning | yes | yes | no | yes | no | yes |
| T002 | coder | implementing | yes | yes | yes | no | no | yes |
| T003 | coder | implementing | yes | yes | yes | no | no | yes |
| T004 | coder | implementing | yes | yes | no | no | no | yes |
| T005 | coder | implementing | yes | yes | yes | no | no | yes |
| T006 | coder | implementing | yes | yes | yes | no | no | yes |
| T007 | coder | implementing | yes | yes | yes | no | no | yes |
| T008 | coder | implementing | yes | yes | yes | no | no | yes |
| T009 | coder | implementing | yes | yes | yes | no | no | yes |
| T010 | coder | implementing | yes | yes | yes | no | no | yes |
| T011 | coder | implementing | yes | yes | yes | no | no | yes |
| T012 | coder | implementing | yes | yes | yes | no | no | yes |
| T013 | coder | implementing | yes | yes | yes | no | no | yes |
| T014 | coder | implementing | yes | yes | yes | no | no | yes |

## Historical Notes
No prior studio-related adventures. ADV-001 (Expressif) and ADV-002 (CodeGraph) followed similar patterns: grammar -> parser -> stdlib -> verify -> codegen -> specs -> tests. Permission patterns from those adventures are replicated here.

## Approval
- [ ] Approved by user
- [ ] Approved with modifications: {notes}
- [ ] Denied: {reason}
