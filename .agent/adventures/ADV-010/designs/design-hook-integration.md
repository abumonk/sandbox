# Design — Hook Integration

## Overview

Wires Claude Code's `SubagentStop` and `PostToolUse` events to the
Python capture writer. The hook is declarative; its job is solely to
hand the event payload to `python .agent/telemetry/capture.py`.

## Target files

- `.claude/settings.local.json` — add a `hooks` key. Merge with the
  existing `permissions.allow` list; do not clobber 128 existing
  entries.
- `.agent/telemetry/capture.py` — existing stub from
  `design-capture-contract.md`. This design specifies what the hook
  delivers to it.

## Why `.claude/settings.local.json` and not `~/.claude/settings.json`

- The project already has `.claude/settings.local.json` in-repo
  (checked earlier). It is the authoritative project-local settings
  file.
- Hooks defined here travel with the repo → reviewers / other
  checkouts get identical capture behaviour. A user-global config
  does not reproduce across machines.
- `.claude/settings.local.json` is gitignored by convention in some
  projects; verify it is tracked in this one before shipping (Wave
  B acceptance check).

## Hook payload

Claude Code's hook runtime invokes a command with the event
serialised to **stdin** as JSON. The shape (per the Claude Code
hooks specification, confirmed by live inspection of a reference
hook in another project) includes at minimum:

```json
{
  "event": "SubagentStop",
  "timestamp": "2026-04-15T01:23:45Z",
  "session_id": "...",
  "cwd": "/r/Sandbox",
  "agent": "adventure-planner",
  "task_id": "ADV010-T003",
  "model": "claude-opus-4-6",
  "usage": {"input_tokens": 48000, "output_tokens": 14000},
  "duration_ms": 720000,
  "turns": 12,
  "result": "complete"
}
```

Field names that differ from our internal `SubagentEvent`
dataclass are aliased inside `capture.py::normalize_payload()`:

| Wire field         | Internal field      | Notes                        |
|--------------------|---------------------|------------------------------|
| `event`            | `event_type`        | direct                       |
| `task_id`          | `task`              | may be absent                |
| `usage.input_tokens` | `tokens_in`       | unwrap nested                |
| `usage.output_tokens`| `tokens_out`      | unwrap nested                |
| `cwd`              | (drives adventure_id) | cwd path → last `ADV-NNN`  |

`adventure_id` resolution order (first hit wins):

1. `payload["adventure_id"]` if present.
2. `payload["task_id"]`'s `ADV\d{3}` prefix.
3. An env var `ADVENTURE_ID` if set by the parent pipeline.
4. Parse `cwd` for `.agent/adventures/ADV-NNN/` path segment.
5. Fail — write error log, exit 0.

## Merged settings block

Adding to the existing `.claude/settings.local.json`:

```json
{
  "permissions": { "allow": [ /* ...unchanged 128 entries... */ ] },
  "hooks": {
    "SubagentStop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python .agent/telemetry/capture.py",
            "timeout_ms": 5000
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python .agent/telemetry/capture.py --event PostToolUse",
            "timeout_ms": 5000
          }
        ]
      }
    ]
  }
}
```

The `--event` flag lets `capture.py` distinguish the two triggers
for the idempotency check in `design-capture-contract.md`.

`timeout_ms: 5000` bounds the hook execution; capture must complete
within 5s or fail-closed (and the failure goes to the error log,
not the pipeline).

## Ordering contract

The hook `timeout_ms` forces capture.py to be fast. Budget:

- stdin read + JSON parse: < 5 ms.
- validate + normalize: < 5 ms.
- cost_model lookup (memoised): < 1 ms.
- metrics.md row append (open + write + close): < 20 ms on NTFS.
- aggregator frontmatter recompute: < 50 ms (file size < 50 KB).
- task_actuals manifest update (conditional): < 50 ms.

Total budget: < 200 ms on typical hardware. 5s timeout is 25× that.

## Failure posture

`capture.py` exits 0 on *any* internal error. The hook thus never
fails into the agent's view. Errors are recorded in
`.agent/telemetry/capture-errors.log`.

## Target Conditions

- TC-HI-1: `.claude/settings.local.json` contains both `SubagentStop`
  and `PostToolUse` hook entries pointing at `capture.py`.
- TC-HI-2: The existing `permissions.allow` list is preserved
  byte-for-byte (no collateral damage).
- TC-HI-3: A synthetic event delivered to `capture.py` via stdin
  produces a row in the correct `metrics.md` — end-to-end harness
  using subprocess, not a mock.
- TC-HI-4: A malformed JSON payload on stdin does not raise into the
  caller (exit 0) and leaves an entry in `capture-errors.log`.

## Dependencies

- `design-capture-contract.md` — defines what `capture.py` does
  after receiving a payload.
- `design-error-isolation.md` — defines the exit-0-on-failure rule.
