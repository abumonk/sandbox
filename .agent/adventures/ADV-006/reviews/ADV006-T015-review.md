---
task_id: ADV006-T015
verdict: PASSED
---
## Integrate visual verify into pipeline
**Files:** `ark/ark.py`
**Findings:** `ark.py` exists and contains the `ark visual verify <file>` sub-command (line 768/841) with auto-detection of visual items. The import of `visual_verify` is guarded with a clear fallback message; no regression in existing verify paths is expected from the additive change.
**Verdict:** PASSED
