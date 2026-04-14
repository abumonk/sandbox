---
adventure_id: ADV-004
status: pending_approval
created: 2026-04-13T13:00:00Z
approved: null
passes_completed: 4
validation_gaps: 0
---

# Permission Requests — ADV-004: Hermes-style Agent Self-Evolution System in Ark DSL

## Summary
52 permissions across 19 tasks, 3 agents (planner, coder, code-reviewer). All 4 analysis passes complete. 0 validation gaps.

## Requests

### Shell Access
| # | Agent | Stage | Command | Reason | Tasks |
|---|-------|-------|---------|--------|-------|
| 1 | coder | implementing | `python ark.py parse <file>` | Validate .ark file parsing after grammar/parser changes | T002,T003,T005,T015,T016,T017 |
| 2 | coder | implementing | `python ark.py verify <file>` | Run Z3 verification on evolution specs | T013,T015,T016,T017 |
| 3 | coder | implementing | `python ark.py codegen <file> --target evolution --out <dir>` | Generate evolution artifacts | T012,T018 |
| 4 | coder | implementing | `python ark.py graph <file>` | Generate visualization with evolution items | T014,T018 |
| 5 | coder | implementing | `python ark.py evolution run <file>` | Execute evolution run via CLI | T011 |
| 6 | coder | implementing | `python ark.py evolution status <file>` | Show evolution run status | T011 |
| 7 | coder | implementing | `pytest tests/test_evolution_*.py` | Run evolution test suite | T019 |
| 8 | coder | implementing | `pytest tests/` | Run full test suite for regression | T003,T005,T019 |
| 9 | coder | implementing | `pytest tests/test_evolution_*.py -v` | Verbose test output for debugging | T019 |
| 10 | code-reviewer | reviewing | `python ark.py parse <file>` | Verify parsing works in review | all |
| 11 | code-reviewer | reviewing | `python ark.py verify <file>` | Verify Z3 checks in review | T013,T015,T016 |
| 12 | code-reviewer | reviewing | `pytest tests/` | Run tests during review | all |
| 13 | code-reviewer | reviewing | `pytest tests/test_evolution_*.py` | Run evolution-specific tests in review | all |

### File Access
| # | Agent | Stage | Scope | Mode | Reason | Tasks |
|---|-------|-------|-------|------|--------|-------|
| 1 | planner | planning | `R:/Sandbox/.agent/adventures/ADV-004/**` | read/write | Read designs, write test strategy | T001 |
| 2 | coder | implementing | `R:/Sandbox/ark/dsl/stdlib/evolution.ark` | write | Create stdlib evolution types | T002 |
| 3 | coder | implementing | `R:/Sandbox/ark/tools/parser/ark_grammar.lark` | read/write | Extend Lark grammar | T003 |
| 4 | coder | implementing | `R:/Sandbox/ark/dsl/grammar/ark.pest` | read/write | Extend pest grammar | T004 |
| 5 | coder | implementing | `R:/Sandbox/ark/tools/parser/ark_parser.py` | read/write | Add dataclasses and transformer | T005 |
| 6 | coder | implementing | `R:/Sandbox/ark/tools/evolution/__init__.py` | write | Create evolution package | T006 |
| 7 | coder | implementing | `R:/Sandbox/ark/tools/evolution/dataset_builder.py` | write | Create dataset builder | T006 |
| 8 | coder | implementing | `R:/Sandbox/ark/tools/evolution/fitness.py` | write | Create fitness scorer | T007 |
| 9 | coder | implementing | `R:/Sandbox/ark/tools/evolution/optimizer.py` | write | Create optimizer engine | T008 |
| 10 | coder | implementing | `R:/Sandbox/ark/tools/evolution/constraint_checker.py` | write | Create constraint checker | T009 |
| 11 | coder | implementing | `R:/Sandbox/ark/tools/evolution/evolution_runner.py` | write | Create evolution runner | T010 |
| 12 | coder | implementing | `R:/Sandbox/ark/ark.py` | read/write | Add evolution CLI commands | T011 |
| 13 | coder | implementing | `R:/Sandbox/ark/tools/codegen/evolution_codegen.py` | write | Create evolution codegen | T012 |
| 14 | coder | implementing | `R:/Sandbox/ark/tools/codegen/ark_codegen.py` | read/write | Integrate evolution target | T012 |
| 15 | coder | implementing | `R:/Sandbox/ark/tools/verify/evolution_verify.py` | write | Create evolution verifier | T013 |
| 16 | coder | implementing | `R:/Sandbox/ark/tools/verify/ark_verify.py` | read/write | Integrate evolution verify | T013 |
| 17 | coder | implementing | `R:/Sandbox/ark/tools/visualizer/ark_visualizer.py` | read/write | Extend visualizer | T014 |
| 18 | coder | implementing | `R:/Sandbox/ark/specs/meta/evolution_skills.ark` | write | Create skill evolution spec | T015 |
| 19 | coder | implementing | `R:/Sandbox/ark/specs/meta/evolution_roles.ark` | write | Create role evolution spec | T016 |
| 20 | coder | implementing | `R:/Sandbox/ark/specs/root.ark` | read/write | Register evolution specs | T017 |
| 21 | coder | implementing | `R:/Sandbox/ark/tests/test_evolution_*.py` | write | Create 8 test files | T019 |
| 22 | coder | implementing | `R:/Sandbox/ark/dsl/stdlib/*.ark` | read | Read existing stdlib for reference | T002 |
| 23 | coder | implementing | `R:/Sandbox/ark/specs/**/*.ark` | read | Read existing specs for reference | T015,T016,T017 |
| 24 | coder | implementing | `R:/Sandbox/ark/tools/codegen/studio_codegen.py` | read | Reference pattern for codegen | T012 |
| 25 | coder | implementing | `R:/Sandbox/ark/tools/verify/studio_verify.py` | read | Reference pattern for verify | T013 |
| 26 | coder | implementing | `R:/Sandbox/ark/tools/evolution/*.py` | read | Read own modules for integration | T010,T011 |
| 27 | code-reviewer | reviewing | `R:/Sandbox/ark/**` | read | Read all project files for review | all |

### MCP Tools
| # | Agent | Stage | Tool | Reason | Tasks |
|---|-------|-------|------|--------|-------|
| 1 | planner | planning | Read | Read codebase for test strategy design | T001 |
| 2 | planner | planning | Glob | Find files for test strategy | T001 |
| 3 | planner | planning | Grep | Search codebase for patterns | T001 |
| 4 | planner | planning | Write | Write test strategy document | T001 |
| 5 | coder | implementing | Read | Read source files | all |
| 6 | coder | implementing | Write | Create new files | T002,T004,T006-T016,T019 |
| 7 | coder | implementing | Edit | Modify existing files | T003,T005,T011,T012,T013,T014,T017 |
| 8 | coder | implementing | Glob | Find files | all |
| 9 | coder | implementing | Grep | Search patterns | all |
| 10 | code-reviewer | reviewing | Read | Read files for review | all |
| 11 | code-reviewer | reviewing | Glob | Find files for review | all |
| 12 | code-reviewer | reviewing | Grep | Search for patterns in review | all |

### External Access
| # | Agent | Stage | Type | Target | Reason | Tasks |
|---|-------|-------|------|--------|--------|-------|
| (none required) | | | | | | |

## Validation Matrix

| Task | Agent | Stage | Read | Write | Shell | MCP | External | Verified |
|------|-------|-------|------|-------|-------|-----|----------|----------|
| T001 | planner | planning | yes | yes | no | yes | no | yes |
| T002 | coder | implementing | yes | yes | yes | yes | no | yes |
| T003 | coder | implementing | yes | yes | yes | yes | no | yes |
| T004 | coder | implementing | yes | yes | no | yes | no | yes |
| T005 | coder | implementing | yes | yes | yes | yes | no | yes |
| T006 | coder | implementing | yes | yes | yes | yes | no | yes |
| T007 | coder | implementing | yes | yes | yes | yes | no | yes |
| T008 | coder | implementing | yes | yes | yes | yes | no | yes |
| T009 | coder | implementing | yes | yes | yes | yes | no | yes |
| T010 | coder | implementing | yes | yes | yes | yes | no | yes |
| T011 | coder | implementing | yes | yes | yes | yes | no | yes |
| T012 | coder | implementing | yes | yes | yes | yes | no | yes |
| T013 | coder | implementing | yes | yes | yes | yes | no | yes |
| T014 | coder | implementing | yes | yes | yes | yes | no | yes |
| T015 | coder | implementing | yes | yes | yes | yes | no | yes |
| T016 | coder | implementing | yes | yes | yes | yes | no | yes |
| T017 | coder | implementing | yes | yes | yes | yes | no | yes |
| T018 | coder | implementing | yes | no | yes | yes | no | yes |
| T019 | coder | implementing | yes | yes | yes | yes | no | yes |

## Historical Notes
- ADV-003 (studio hierarchy) used the same pattern: grammar + parser + stdlib + verify + codegen + visualizer + reflexive specs + tests. 38 permissions were sufficient. ADV-004 follows the same structure with 52 permissions (more tools/evolution/ files).
- ADV-001/002 showed Bash permission blocks for pytest/cargo. All shell commands are pre-approved in this plan.
- ADV-002 had incomplete metrics tracking. This plan includes explicit metrics tracking in T019.

## Approval
- [ ] Approved by user
- [ ] Approved with modifications: {notes}
- [ ] Denied: {reason}
