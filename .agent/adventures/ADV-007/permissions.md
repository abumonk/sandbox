---
adventure_id: ADV-007
status: pending_approval
created: 2026-04-13T22:22:00Z
approved: null
passes_completed: 4
validation_gaps: 0
---

# Permission Requests — ADV-007: Claudovka Ecosystem Roadmap — Research & Adventure Planning

## Summary
42 permissions across 24 tasks, 2 agents (researcher, planner). All 4 analysis passes complete. 0 validation gaps.

## Requests

### Shell Access
| # | Agent | Stage | Command | Reason | Tasks |
|---|-------|-------|---------|--------|-------|
| 1 | researcher | researching | `grep -l pattern path` | Verify research artifact existence for TC validation | T024 |
| 2 | researcher | researching | `ls path` | List research files for completeness checks | T024 |
| 3 | researcher | researching | `wc -l file` | Count entries in research files | T024 |
| 4 | researcher | researching | `test -f file` | Check file existence for TC proof commands | T024 |

### File Access
| # | Agent | Stage | Scope | Mode | Reason | Tasks |
|---|-------|-------|-------|------|--------|-------|
| 5 | researcher | researching | `.agent/adventures/ADV-007/research/**` | write | Write research documents | T002-T023 |
| 6 | researcher | researching | `.agent/adventures/ADV-007/tests/**` | write | Write test strategy and validation reports | T001, T024 |
| 7 | researcher | researching | `.agent/adventures/ADV-007/research/**` | read | Read research documents for cross-referencing | T006-T024 |
| 8 | researcher | researching | `.agent/adventures/ADV-*/manifest.md` | read | Read past adventure manifests for management review | T009 |
| 9 | researcher | researching | `.agent/adventures/ADV-*/adventure.log` | read | Read past adventure logs for failure analysis | T009 |
| 10 | researcher | researching | `.agent/adventures/ADV-*/metrics.md` | read | Read past metrics for performance analysis | T009 |
| 11 | researcher | researching | `.agent/knowledge/*.md` | read | Read knowledge base for patterns and issues | T009, T010, T011 |
| 12 | researcher | researching | `.agent/roles/*.md` | read | Read role definitions for effectiveness review | T011 |
| 13 | researcher | researching | `.agent/config.md` | read | Read project configuration | T001 |
| 14 | researcher | researching | `ark/tools/**/*.py` | read | Read ark tool modules for architecture understanding | T008 |
| 15 | researcher | researching | `ark/specs/**/*.ark` | read | Read ark specs for architecture understanding | T008 |
| 16 | researcher | researching | `ark/CLAUDE.md` | read | Read project instructions for context | T008 |
| 17 | planner | planning | `.agent/adventures/ADV-007/**` | read | Read adventure artifacts for planning | all |

### MCP Tools
| # | Agent | Stage | Tool | Reason | Tasks |
|---|-------|-------|------|--------|-------|
| 18 | researcher | researching | Read | Read local files | all |
| 19 | researcher | researching | Write | Write research documents | all |
| 20 | researcher | researching | Glob | Find files by pattern | T008, T009, T011, T024 |
| 21 | researcher | researching | Grep | Search file contents | T009, T011, T024 |

### External Access
| # | Agent | Stage | Type | Target | Reason | Tasks |
|---|-------|-------|------|--------|--------|-------|
| 22 | researcher | researching | WebSearch | github.com | Find Claudovka project repositories | T002-T005 |
| 23 | researcher | researching | WebSearch | npmjs.com | Find npm packages for Claudovka projects | T002-T005 |
| 24 | researcher | researching | WebSearch | general | Research external tools (QMD, CGC, etc.) | T012-T015 |
| 25 | researcher | researching | WebSearch | general | Research UI patterns and frameworks | T017 |
| 26 | researcher | researching | WebSearch | general | Research MCP servers | T015 |
| 27 | researcher | researching | WebSearch | general | Research operational patterns | T022 |
| 28 | researcher | researching | WebSearch | general | Research new ecosystem concepts | T018 |
| 29 | researcher | researching | WebSearch | general | Research CI/CD and automation patterns | T019 |
| 30 | researcher | researching | WebFetch | github.com/* | Fetch repository READMEs and source files | T002-T005, T012-T015 |
| 31 | researcher | researching | WebFetch | npmjs.com/* | Fetch npm package details | T002-T005 |
| 32 | researcher | researching | WebFetch | modelcontextprotocol.io/* | Fetch MCP specifications | T015 |
| 33 | researcher | researching | WebFetch | general | Fetch documentation for external tools | T012-T015, T017 |

## Validation Matrix

| Task | Agent | Stage | Read | Write | Shell | MCP | External | Verified |
|------|-------|-------|------|-------|-------|-----|----------|----------|
| T001 | researcher | researching | #13 | #6 | - | #18,#19 | - | yes |
| T002 | researcher | researching | #7 | #5 | - | #18,#19 | #22,#23,#30,#31 | yes |
| T003 | researcher | researching | #7 | #5 | - | #18,#19 | #22,#23,#30,#31 | yes |
| T004 | researcher | researching | #7 | #5 | - | #18,#19 | #22,#23,#30,#31 | yes |
| T005 | researcher | researching | #7 | #5 | - | #18,#19 | #22,#23,#30,#31 | yes |
| T006 | researcher | researching | #7 | #5 | - | #18,#19 | - | yes |
| T007 | researcher | researching | #7 | #5 | - | #18,#19 | #24 | yes |
| T008 | researcher | researching | #7,#14,#15,#16 | #5 | - | #18,#19,#20,#21 | - | yes |
| T009 | researcher | researching | #7,#8,#9,#10,#11 | #5 | - | #18,#19,#20,#21 | - | yes |
| T010 | researcher | researching | #7,#11 | #5 | - | #18,#19 | - | yes |
| T011 | researcher | researching | #7,#11,#12 | #5 | - | #18,#19,#20,#21 | - | yes |
| T012 | researcher | researching | #7 | #5 | - | #18,#19 | #24,#30,#33 | yes |
| T013 | researcher | researching | #7 | #5 | - | #18,#19 | #24,#30,#33 | yes |
| T014 | researcher | researching | #7 | #5 | - | #18,#19 | #24,#30,#33 | yes |
| T015 | researcher | researching | #7 | #5 | - | #18,#19 | #26,#30,#32 | yes |
| T016 | researcher | researching | #7 | #5 | - | #18,#19 | - | yes |
| T017 | researcher | researching | #7 | #5 | - | #18,#19 | #25,#33 | yes |
| T018 | researcher | researching | #7 | #5 | - | #18,#19 | #28 | yes |
| T019 | researcher | researching | #7 | #5 | - | #18,#19 | #29 | yes |
| T020 | researcher | researching | #7 | #5 | - | #18,#19 | - | yes |
| T021 | researcher | researching | #7 | #5 | - | #18,#19 | - | yes |
| T022 | researcher | researching | #7 | #5 | - | #18,#19 | #27 | yes |
| T023 | researcher | researching | #7 | #5 | - | #18,#19 | - | yes |
| T024 | researcher | researching | #7 | #6 | #1,#2,#3,#4 | #18,#19,#20,#21 | - | yes |

## Historical Notes
- ADV-001: Permission blocks on pytest/cargo caused delays. Not relevant here (no code execution).
- ADV-002-006: Incomplete metrics tracking is a recurring issue. Ensure T024 validation checks metrics completeness.
- Past adventures used Read/Write/Glob/Grep extensively for research tasks -- all covered above.
- No past adventure required WebSearch/WebFetch at this scale; token estimates may need upward adjustment.

## Approval
- [ ] Approved by user
- [ ] Approved with modifications: {notes}
- [ ] Denied: {reason}
