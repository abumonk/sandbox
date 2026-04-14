---
name: Metrics enforcement
description: Implementers must append metrics row to metrics.md before marking task complete
type: feedback
---

Append a metrics row to the adventure's metrics.md before marking any task as complete. This has been a recurring gap across ADV-002 and ADV-006 (7/17 and 7/19 tasks missing respectively). The adventure reviewer cannot produce accurate cost analysis without complete metrics data.

**Why:** Incomplete metrics make cost estimation and process analysis unreliable. The adventure reviewer flags this every time.
**How to apply:** Before writing "complete:" to the adventure log, append your metrics row: `| implementer | {task-id} | {model} | {tokens_in} | {tokens_out} | {duration} | {turns} | {result} |`
