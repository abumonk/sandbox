# Hook Registration in settings.local.json - Design

## Approach

Add a `hooks` top-level key to `.claude/settings.local.json` containing
`SubagentStop` and `PostToolUse` hook arrays, exactly as specified in
`design-hook-integration.md`. The existing `permissions.allow` list
(124 entries, lines 3-126) must remain byte-for-byte identical.

The implementer writes a small one-shot Python merger script that:
1. Reads the current JSON.
2. Asserts `"hooks"` key is absent (guard against double-apply).
3. Injects the hooks block.
4. Writes the result with identical formatting (2-space indent, no trailing comma).
5. Diffs the `permissions.allow` array before/after to prove no clobber.

The merger script is a local tool, not shipped code.

## Target Files

- `.claude/settings.local.json` - Add `hooks` key with `SubagentStop` and `PostToolUse` arrays. No other changes.

## Implementation Steps

1. **Read current file** - Load `.claude/settings.local.json` via `json.load()`. Snapshot `permissions.allow` for later comparison.

2. **Create merger script** (e.g., `.agent/adventures/ADV-010/tools/merge_hooks.py`):
   ```python
   import json, sys, copy

   with open('.claude/settings.local.json', 'r') as f:
       original_text = f.read()
       
   data = json.loads(original_text)
   original_allow = copy.deepcopy(data["permissions"]["allow"])
   
   assert "hooks" not in data, "hooks key already exists"
   
   data["hooks"] = {
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
   
   assert data["permissions"]["allow"] == original_allow, "allow list was modified"
   
   with open('.claude/settings.local.json', 'w', newline='\n') as f:
       json.dump(data, f, indent=2)
       f.write('\n')
   ```

3. **Alternative: Use Edit tool directly** - Since the JSON structure is simple (one top-level object ending with `}`), the implementer can also use the Edit tool to insert the `hooks` block before the final closing brace. This avoids a script entirely. The edit would replace the final:
   ```
     }
   }
   ```
   with:
   ```
     },
     "hooks": {
       "SubagentStop": [ ... ],
       "PostToolUse": [ ... ]
     }
   }
   ```
   The Edit tool approach is preferred for its simplicity, provided the implementer reads the file first and identifies the exact closing pattern.

4. **Verify with jq assertions** (from acceptance criteria):
   - `jq '.hooks.SubagentStop | length' .claude/settings.local.json` returns `1`
   - `jq '.hooks.PostToolUse[0].matcher' .claude/settings.local.json` returns `"Task"`
   - `jq '.permissions.allow | length' .claude/settings.local.json` returns `124` (unchanged)
   - `jq '.hooks.SubagentStop[0].hooks[0].command' .claude/settings.local.json` contains `capture.py`
   - `jq '.hooks.PostToolUse[0].hooks[0].command' .claude/settings.local.json` contains `capture.py`

5. **Byte-diff verification on permissions.allow**:
   - Extract `.permissions.allow` before and after with `jq` and `diff`.
   - `jq '.permissions.allow' .claude/settings.local.json > /tmp/allow_after.json`
   - Compare against a pre-edit snapshot to confirm zero diff.

## Hook Block Specification (from design-hook-integration.md)

| Hook Event     | Matcher | Command                                              | Timeout |
|----------------|---------|------------------------------------------------------|---------|
| SubagentStop   | `*`     | `python .agent/telemetry/capture.py`                 | 5000ms  |
| PostToolUse    | `Task`  | `python .agent/telemetry/capture.py --event PostToolUse` | 5000ms  |

## Testing Strategy

- **AC-1**: `jq '.hooks.SubagentStop | length'` returns >= 1
- **AC-2**: `jq '.hooks.PostToolUse[0].matcher'` returns `"Task"`
- **AC-3**: Byte diff on `.permissions.allow` is empty (extract before/after, diff)
- **AC-4**: Both hook commands contain `python .agent/telemetry/capture.py`

All verification uses `jq` and `diff` -- no custom test code needed.

## Risks

- **JSON formatting drift**: `json.dump` with `indent=2` may reformat the
  existing file slightly (e.g., trailing newline, string escaping of
  backslashes in the allow list). The Edit tool approach avoids this
  entirely by only touching the insertion point. Recommend Edit tool.
- **Backslash escaping**: Many `permissions.allow` entries contain
  escaped parentheses `\\(` etc. A round-trip through `json.dump` will
  preserve these correctly since they are valid JSON string escapes,
  but visual diff should be checked.
- **Idempotency**: The merger script guards against double-apply with
  the `assert "hooks" not in data` check. If using Edit tool, the
  implementer should grep for `"hooks"` first.
