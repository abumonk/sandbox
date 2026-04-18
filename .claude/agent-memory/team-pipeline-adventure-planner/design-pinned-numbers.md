---
name: design-pinned-numbers
description: Avoid pinning exact integer counts in designs that depend on external-file contents without a runtime-recalc fallback
type: feedback
---

When writing design documents, do not assert exact integers ("coverage matrix row count must equal 278", "inventory must have exactly 218 rows") that are computed from external-file harvests unless you include an explicit runtime-recalc fallback instruction.

**Why**: In ADV-011 T009, the design pinned "278 source TCs" based on an a priori read of 9 manifests. The actual harvest yielded 272 (ADV-003's tests/test-strategy.md contributed 29 TCs, not 35). Without the design's explicit fallback clause, this would have triggered a rework cycle. The fallback clause ("STOP and log the discrepancy in § Open gaps") absorbed the drift cleanly.

**How to apply**: When a design mentions an exact integer from an external file, write it as `expected ~N (recount at implementation time and log variance)` rather than `must equal N`. Have unittests that guard the invariant re-count the file at test time rather than hard-coding the expected value. This preserves the integrity of the invariant without coupling the design to a potentially stale count.
