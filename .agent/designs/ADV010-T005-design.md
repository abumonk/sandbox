# Schema + Validator Module - Design

## Approach

Implement `.agent/telemetry/schema.py` as a single stdlib-only Python module containing two frozen dataclasses (`SubagentEvent`, `MetricsRow`), a strict event validator, a row builder with SHA-1 Run ID derivation, and round-trippable pipe-table serialization/parsing. Reuse the exception hierarchy from `errors.py` (created by T004).

## Target Files
- `.agent/telemetry/schema.py` - New file; all dataclasses, validators, row builder, serializer, and parser

## Implementation Steps

### 1. Imports and constants

- Import `dataclasses`, `hashlib`, `re`, `typing.Optional`.
- Import `CaptureError`, `PayloadError`, `SchemaError` from `.errors`.
- Import `cost_for`, `normalize_model`, `known_models` from `.cost_model`.
- Define `VALID_EVENT_TYPES = {"SubagentStop", "PostToolUse"}`.
- Define `VALID_RESULTS = {"complete", "ready", "done", "passed", "failed", "error"}`.
- Define `VALID_CONFIDENCE = {"high", "medium", "low", "estimated"}`.
- Define regex patterns: `RE_ADVENTURE_ID = re.compile(r"^ADV-\d{3}$")`, `RE_TASK_ID = re.compile(r"^ADV\d{3}-T\d{3}$")`, `RE_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")`.
- Define `ROW_COLUMNS` as an ordered tuple of 12 column names matching `row_schema.md`.
- Define `ROW_HEADER` and `ROW_SEPARATOR` strings derived from `ROW_COLUMNS`.

### 2. SubagentEvent dataclass

```python
@dataclass(frozen=True)
class SubagentEvent:
    event_type: str
    timestamp: str
    adventure_id: str
    agent: str
    task: Optional[str]
    model: str
    tokens_in: int
    tokens_out: int
    duration_ms: int
    turns: int
    result: str
    session_id: Optional[str] = None
```

### 3. MetricsRow dataclass

```python
@dataclass(frozen=True)
class MetricsRow:
    run_id: str          # 12 hex chars
    timestamp: str
    agent: str
    task: str            # task ID or literal "-"
    model: str
    tokens_in: int
    tokens_out: int
    duration_s: int      # rounded from ms
    turns: int
    cost_usd: float      # 4dp
    result: str
    confidence: str      # "high" for hook-written rows
```

### 4. validate_event(payload: dict) -> SubagentEvent

Strict validator covering exactly 10 rejection cases (raising `PayloadError` for each):

1. Missing `event_type` field
2. Missing `timestamp` field (or invalid format)
3. Missing `adventure_id` field (or fails `^ADV-\d{3}$`)
4. Missing `agent` field
5. Missing `model` field (or not in `known_models()`)
6. `tokens_in` missing or not a non-negative int
7. `tokens_out` missing or not a non-negative int
8. `duration_ms` missing or not a positive int (> 0)
9. `turns` missing or not a non-negative int
10. `task` present but does not match `^ADV\d{3}-T\d{3}$`

Additional checks (not counted among the 10, but enforced):
- `result` must be in `VALID_RESULTS`; `event_type` must be in `VALID_EVENT_TYPES`.

Implementation pattern:
```python
def validate_event(payload: dict) -> SubagentEvent:
    # Check each required field, raising PayloadError with a specific message
    # Normalize model via cost_model.normalize_model() before storing
    # Construct and return frozen SubagentEvent
```

### 5. build_row(event: SubagentEvent, cost: float) -> MetricsRow

- Compute `run_id`: `hashlib.sha1(f"{event.adventure_id}|{event.agent}|{event.task or '-'}|{event.model}|{event.timestamp}|{event.session_id or ''}".encode()).hexdigest()[:12]`.
- Compute `duration_s`: `max(1, round(event.duration_ms / 1000))` -- minimum 1 so sub-second runs never show 0.
- Format `cost` to 4 decimal places.
- Set `confidence = "high"` (hook-written rows).
- Set `task = event.task or "-"`.
- Return `MetricsRow(...)`.

Note: The caller passes `cost` from `cost_model.cost_for(event.model, event.tokens_in, event.tokens_out)`. This keeps `schema.py` decoupled from cost computation (the cost model import is only needed for validation of the model name in `validate_event`).

### 6. serialize(row: MetricsRow) -> str

- Format the row as a pipe-separated line: `| {run_id} | {timestamp} | ... |`.
- `cost_usd` formatted as `f"{row.cost_usd:.4f}"`.
- All other fields use their natural `str()` representation.
- Returns the line without a trailing newline.

### 7. parse_row(line: str) -> MetricsRow

- Split `line` on `|`, strip each cell.
- Expect exactly 12 data cells (ignoring empty leading/trailing from split).
- Coerce types: `tokens_in`, `tokens_out`, `duration_s`, `turns` to `int`; `cost_usd` to `float`.
- Raise `SchemaError` if column count wrong or type coercion fails.
- Return `MetricsRow(...)`.

### 8. Round-trip guarantee

`serialize(row)` then `parse_row(line)` must produce a `MetricsRow` where all numeric fields are identical to the original. This is ensured by:
- Integer fields serialized without padding or formatting.
- `cost_usd` serialized to exactly 4 decimal places and parsed back via `float()`.
- The acceptance criterion checks byte-equivalence on numeric columns specifically (not string representation equivalence of the full line, which would be trivially true).

## Testing Strategy

Target conditions covered: TC-CC-1 (partial), TC-S-3.

Tests will live in `.agent/adventures/ADV-010/tests/test_schema.py` (created by a later test task):

- **TC-CC-1 (10 invalid payload cases)**: Parameterize with fixtures for each of the 10 rejection cases listed above. Each must raise `PayloadError` with a specific, distinguishable message.
- **TC-S-3 (row type coercion)**: Parse a serialized row and verify all numeric columns return their original int/float values.
- **Round-trip**: Build a row from a known event, serialize it, parse it back, assert numeric field equality.
- **Run ID determinism**: Two calls to `build_row` with the same event must produce the same `run_id`.
- **Sub-second duration clamping**: `duration_ms=500` produces `duration_s=1`, not 0.

## Risks

- **Coupling with cost_model**: `validate_event` calls `known_models()` to check the model field. If T004 is not complete or `errors.py` is missing, `schema.py` will fail to import. The `depends_on: [ADV010-T004]` constraint mitigates this.
- **Float precision on cost**: Using Python `float` with 4dp formatting is safe for the expected cost range (< $100). No Decimal needed.
- **Pipe character in field values**: Agent names and task IDs never contain `|`, so no escaping is needed. If a future field could contain `|`, the parser would need updating.
