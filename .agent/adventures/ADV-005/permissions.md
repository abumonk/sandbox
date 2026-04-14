---
adventure_id: ADV-005
status: pending_approval
created: 2026-04-13T18:06:00Z
approved: null
passes_completed: 4
validation_gaps: 0
---

# Permission Requests — ADV-005: Hermes-style Autonomous Agent System in Ark DSL

## Summary
52 permissions across 21 tasks, 3 agents (planner, coder, code-reviewer). All 4 analysis passes complete. 0 validation gaps.

## Requests

### Shell Access
| # | Agent | Stage | Command | Reason | Tasks |
|---|-------|-------|---------|--------|-------|
| 1 | coder | implementing | `python ark.py parse <file>` | Validate .ark file parsing after grammar/parser changes | T002,T003,T005,T017,T018,T019 |
| 2 | coder | implementing | `python ark.py verify <file>` | Run Z3 verification on agent specs | T012,T013,T017,T018 |
| 3 | coder | implementing | `python ark.py agent codegen <file> [--out <dir>]` | Generate agent artifacts | T014,T015,T017 |
| 4 | coder | implementing | `python ark.py agent verify <file>` | Run agent-specific verification | T012,T013,T015,T017,T018 |
| 5 | coder | implementing | `python ark.py graph <file>` | Generate agent architecture visualization | T016 |
| 6 | coder | implementing | `python ark.py pipeline <file>` | Run full pipeline end-to-end | T020 |
| 7 | coder | implementing | `pytest tests/test_agent_*.py` | Run agent test suite | T021 |
| 8 | coder | implementing | `pytest tests/` | Run full test suite for regression | T003,T005,T020,T021 |
| 9 | code-reviewer | reviewing | `python ark.py parse <file>` | Verify parsing works in review | all |
| 10 | code-reviewer | reviewing | `python ark.py verify <file>` | Verify Z3 checks in review | T012,T013,T017,T018 |
| 11 | code-reviewer | reviewing | `python ark.py agent verify <file>` | Verify agent checks in review | T012,T013,T017,T018 |
| 12 | code-reviewer | reviewing | `python ark.py agent codegen <file>` | Verify codegen output in review | T014,T017 |
| 13 | code-reviewer | reviewing | `pytest tests/` | Run tests during review | all |

### File Access
| # | Agent | Stage | Scope | Mode | Reason | Tasks |
|---|-------|-------|-------|------|--------|-------|
| 1 | planner | planning | `R:/Sandbox/.agent/adventures/ADV-005/**` | read/write | Read designs, write test strategy | T001 |
| 2 | coder | implementing | `R:/Sandbox/ark/dsl/stdlib/agent.ark` | write | Create agent stdlib types | T002 |
| 3 | coder | implementing | `R:/Sandbox/ark/dsl/stdlib/*.ark` | read | Read existing stdlib for reference | T002 |
| 4 | coder | implementing | `R:/Sandbox/ark/tools/parser/ark_grammar.lark` | read/write | Extend Lark grammar | T003 |
| 5 | coder | implementing | `R:/Sandbox/ark/dsl/grammar/ark.pest` | read/write | Extend pest grammar | T004 |
| 6 | coder | implementing | `R:/Sandbox/ark/tools/parser/ark_parser.py` | read/write | Add dataclasses and transformer | T005 |
| 7 | coder | implementing | `R:/Sandbox/ark/tools/agent/__init__.py` | write | Create agent package | T006 |
| 8 | coder | implementing | `R:/Sandbox/ark/tools/agent/gateway.py` | write | Create gateway module | T006 |
| 9 | coder | implementing | `R:/Sandbox/ark/tools/agent/backend.py` | write | Create backend module | T007 |
| 10 | coder | implementing | `R:/Sandbox/ark/tools/agent/skill_manager.py` | write | Create skill manager | T008 |
| 11 | coder | implementing | `R:/Sandbox/ark/tools/agent/learning.py` | write | Create learning engine | T009 |
| 12 | coder | implementing | `R:/Sandbox/ark/tools/agent/scheduler.py` | write | Create scheduler | T010 |
| 13 | coder | implementing | `R:/Sandbox/ark/tools/agent/agent_runner.py` | write | Create agent runner | T011 |
| 14 | coder | implementing | `R:/Sandbox/ark/tools/verify/agent_verify.py` | write | Create agent verifier | T012 |
| 15 | coder | implementing | `R:/Sandbox/ark/tools/verify/ark_verify.py` | read/write | Integrate agent verify | T013 |
| 16 | coder | implementing | `R:/Sandbox/ark/tools/codegen/agent_codegen.py` | write | Create agent codegen | T014 |
| 17 | coder | implementing | `R:/Sandbox/ark/ark.py` | read/write | Add agent CLI subcommands | T015 |
| 18 | coder | implementing | `R:/Sandbox/ark/tools/visualizer/ark_visualizer.py` | read/write | Add agent visualization | T016 |
| 19 | coder | implementing | `R:/Sandbox/ark/specs/infra/agent_system.ark` | write | Author exemplar agent spec | T017 |
| 20 | coder | implementing | `R:/Sandbox/ark/specs/meta/ark_agent.ark` | write | Author reflexive agent spec | T018 |
| 21 | coder | implementing | `R:/Sandbox/ark/specs/root.ark` | read/write | Register agent specs | T019 |
| 22 | coder | implementing | `R:/Sandbox/ark/specs/**/*.ark` | read | Read existing specs for reference | T017,T018,T019,T020 |
| 23 | coder | implementing | `R:/Sandbox/ark/tests/test_agent_*.py` | write | Create test files | T021 |
| 24 | coder | implementing | `R:/Sandbox/ark/tests/conftest.py` | read/write | Update conftest for agent paths | T013 |
| 25 | code-reviewer | reviewing | `R:/Sandbox/ark/**` | read | Read all project files for review | all |

### MCP Tools
| # | Agent | Stage | Tool | Reason | Tasks |
|---|-------|-------|------|--------|-------|
| 1 | planner | planning | Read | Read codebase for test strategy design | T001 |
| 2 | planner | planning | Glob | Find files for test strategy | T001 |
| 3 | planner | planning | Grep | Search codebase for patterns | T001 |
| 4 | planner | planning | Write | Write test strategy document | T001 |
| 5 | coder | implementing | Read | Read source files | all |
| 6 | coder | implementing | Write | Create new files | T002,T006-T014,T017,T018,T021 |
| 7 | coder | implementing | Edit | Modify existing files | T003-T005,T013,T015-T016,T019 |
| 8 | coder | implementing | Glob | Find files by pattern | all |
| 9 | coder | implementing | Grep | Search for patterns in code | all |
| 10 | code-reviewer | reviewing | Read | Read files for review | all |
| 11 | code-reviewer | reviewing | Glob | Find files for review | all |
| 12 | code-reviewer | reviewing | Grep | Search patterns for review | all |

### External Access
| # | Agent | Stage | Type | Target | Reason | Tasks |
|---|-------|-------|------|--------|--------|-------|
| 1 | coder | implementing | WebFetch | https://github.com/NousResearch/hermes-agent | Reference Hermes Agent patterns for skill format | T008,T014 |

## Validation Matrix

| Task | Agent | Stage | Read | Write | Shell | MCP | External | Verified |
|------|-------|-------|------|-------|-------|-----|----------|----------|
| T001 | planner | planning | yes | yes | no | yes | no | yes |
| T002 | coder | implementing | yes | yes | yes | yes | no | yes |
| T003 | coder | implementing | yes | yes | yes | yes | no | yes |
| T004 | coder | implementing | yes | yes | no | yes | no | yes |
| T005 | coder | implementing | yes | yes | yes | yes | no | yes |
| T006 | coder | implementing | yes | yes | no | yes | no | yes |
| T007 | coder | implementing | yes | yes | no | yes | no | yes |
| T008 | coder | implementing | yes | yes | no | yes | yes | yes |
| T009 | coder | implementing | yes | yes | no | yes | no | yes |
| T010 | coder | implementing | yes | yes | no | yes | no | yes |
| T011 | coder | implementing | yes | yes | no | yes | no | yes |
| T012 | coder | implementing | yes | yes | yes | yes | no | yes |
| T013 | coder | implementing | yes | yes | yes | yes | no | yes |
| T014 | coder | implementing | yes | yes | no | yes | yes | yes |
| T015 | coder | implementing | yes | yes | yes | yes | no | yes |
| T016 | coder | implementing | yes | yes | yes | yes | no | yes |
| T017 | coder | implementing | yes | yes | yes | yes | no | yes |
| T018 | coder | implementing | yes | yes | yes | yes | no | yes |
| T019 | coder | implementing | yes | yes | yes | yes | no | yes |
| T020 | coder | implementing | yes | no | yes | yes | no | yes |
| T021 | coder | implementing | yes | yes | yes | yes | no | yes |

## Historical Notes
- ADV-003 had 38 permissions across 14 tasks, 3 agents. Pattern followed here.
- ADV-001 experienced Bash permission blocks on pytest/cargo validation (issues.md). All test commands explicitly listed above.
- ADV-003 used separate domain modules (studio_verify.py, studio_codegen.py). Same pattern used here (agent_verify.py, agent_codegen.py).
- ADV-002 metrics tracking was incomplete. T021 explicitly includes test execution verification.

## Approval
- [ ] Approved by user
- [ ] Approved with modifications: {notes}
- [ ] Denied: {reason}
