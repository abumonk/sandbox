---
name: Implementer log numeric claims must be machine-verified
description: When an implementer log asserts a specific row count / file length / element count, run the grep or len() that proves it rather than estimating from memory.
type: feedback
---

Rule: any numeric claim in the implementer's task log (row count, test count, line count, file size) must be produced by a shell or Python command executed in the same turn, and the command should be cited.

**Why:** ADV-010 T011's log stated `existing_rows.parse(ADV-008/metrics.md)` returns 35 rows; the real count was 21. The reviewer caught it, but only after reconciling four sources. A `grep -c '^| ' <file>` in the implementer's log would have prevented the failed review.

**How to apply:** Before writing "returns N rows" or "produces N files" in a task log, run the verifying command in the same turn and quote the output. If counts come from a Python REPL, paste the REPL line.
