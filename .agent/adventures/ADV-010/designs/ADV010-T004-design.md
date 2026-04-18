# Cost Model Module — Design

## Approach

Implement three new files under `.agent/telemetry/`: a shared error
hierarchy (`errors.py`), the cost model itself (`cost_model.py`), and
a package init (`__init__.py`). The cost model reads rates from
`.agent/config.md` YAML frontmatter using a hand-rolled stdlib-only
parser (~40 LOC), normalises model ID strings to canonical short
names, and computes flat-rate USD costs. All functions are pure;
`load_rates` is memoised via `functools.lru_cache`.

## Target Files

- `.agent/telemetry/__init__.py` — Package init. Empty or minimal
  (re-exports if desired). Makes `telemetry` importable as a package.
- `.agent/telemetry/errors.py` — Exception hierarchy shared across
  T004-T007. Classes: `CaptureError` (base), `PayloadError`,
  `SchemaError`, `CostModelError`, `UnknownModelError` (subclass of
  `CostModelError`), `WriteError`, `AggregationError`,
  `TaskActualsError`. All inherit from `Exception` via `CaptureError`.
- `.agent/telemetry/cost_model.py` — Four public functions:
  `load_rates`, `normalize_model`, `known_models`, `cost_for`.

## Implementation Steps

### Step 1 — `.agent/telemetry/__init__.py`

Create an empty `__init__.py` (or with a single docstring) to
establish the package.

### Step 2 — `.agent/telemetry/errors.py`

Define the full exception hierarchy from `design-error-isolation.md`:

```python
class CaptureError(Exception):
    """Base for all telemetry capture failures."""

class PayloadError(CaptureError): ...
class SchemaError(CaptureError): ...
class CostModelError(CaptureError): ...
class UnknownModelError(CostModelError): ...
class WriteError(CaptureError): ...
class AggregationError(CaptureError): ...
class TaskActualsError(CaptureError): ...
```

Each class gets a one-line docstring. No external imports.

### Step 3 — `.agent/telemetry/cost_model.py` — frontmatter parser

Implement `_parse_frontmatter(text: str) -> dict`:

1. Split on lines. Find the first line that is exactly `---`.
2. Collect lines until the next `---` line.
3. For each line, detect indentation depth (count of leading spaces,
   2-space increments).
4. Parse `key: value` pairs. Track a stack of nested mapping keys.
5. Coerce scalar values: `int` (try first), `float`, quoted string
   (strip quotes), bare string.
6. Return a nested dict.

Error handling: raise `CostModelError` with line number on malformed
indentation or missing frontmatter delimiters.

### Step 4 — `load_rates(config_path=None)`

```python
from functools import lru_cache
from pathlib import Path

_DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config.md"

@lru_cache(maxsize=1)
def load_rates(config_path: str | None = None) -> dict[str, float]:
    path = Path(config_path) if config_path else _DEFAULT_CONFIG
    text = path.read_text(encoding="utf-8")
    fm = _parse_frontmatter(text)
    try:
        rates = fm["adventure"]["token_cost_per_1k"]
    except (KeyError, TypeError):
        raise CostModelError(
            "config.md missing adventure.token_cost_per_1k")
    if not isinstance(rates, dict) or not rates:
        raise CostModelError("token_cost_per_1k must be a non-empty mapping")
    return {k: float(v) for k, v in rates.items()}
```

Note: `lru_cache` requires hashable args. Since `config_path` defaults
to `None` (hashable) or is a string (hashable), this works. The cache
means the file is read at most once per process invocation — acceptable
for a subprocess hook that runs once and exits.

### Step 5 — `normalize_model(model_id: str) -> str`

```python
import re

def normalize_model(model_id: str) -> str:
    for canon in ("opus", "sonnet", "haiku"):
        if model_id == canon:
            return canon
        if re.match(rf"^(claude-)?{canon}(-.*)?$", model_id):
            return canon
    return model_id  # pass-through for future unknown models
```

Matching rules (from design doc):
- `claude-opus-4-6`, `claude-opus-*`, `opus-*`, `opus` → `"opus"`
- Same pattern for `sonnet` and `haiku`
- Anything else → returned unchanged (allows config-driven extension)

### Step 6 — `known_models() -> frozenset[str]`

```python
def known_models() -> frozenset[str]:
    base = set(load_rates().keys())
    return frozenset(
        base
        | {f"claude-{m}-4-6" for m in base}
        | {f"claude-{m}" for m in base}
    )
```

Returns the union of rate keys and their common aliases so that
`schema.validate_event` can reject unknown models at validation time
rather than at cost-computation time.

### Step 7 — `cost_for(model, tokens_in, tokens_out, rates=None)`

```python
def cost_for(model: str, tokens_in: int, tokens_out: int,
             rates: dict[str, float] | None = None) -> float:
    if rates is None:
        rates = load_rates()
    key = normalize_model(model)
    if key not in rates:
        raise UnknownModelError(
            f"Unknown model: {model!r} (normalized: {key!r}). "
            f"Known: {sorted(rates)}")
    total_tokens = tokens_in + tokens_out
    cost = total_tokens / 1000.0 * rates[key]
    return round(cost, 4)
```

Formula: `(tokens_in + tokens_out) / 1000 * rate_per_1k`, rounded to
4 decimal places.

Verification: `cost_for("opus", 85000, 28000)` → `(85000+28000)/1000
* 0.015` = `113 * 0.015` = `1.695` — matches TC-CM-1.

## Testing Strategy

Tests live in `.agent/adventures/ADV-010/tests/test_cost_model.py`
(created in a later test task, but acceptance criteria are verified via
the following assertions):

1. **TC-CM-4**: `load_rates()` returns `{"opus": 0.015, "sonnet":
   0.003, "haiku": 0.001}` from the real `.agent/config.md`.
2. **TC-CM-1**: `cost_for("opus", 85000, 28000)` returns `1.695`.
3. **TC-CM-2**: `cost_for("unknown-model-xyz", 1, 1)` raises
   `UnknownModelError`.
4. **TC-CM-3**: Table-driven `normalize_model` test with >= 6 cases:
   - `"opus"` → `"opus"`
   - `"claude-opus-4-6"` → `"opus"`
   - `"sonnet"` → `"sonnet"`
   - `"claude-sonnet-4"` → `"sonnet"`
   - `"haiku"` → `"haiku"`
   - `"claude-haiku-3-5"` → `"haiku"`
   - `"gpt-4o"` → `"gpt-4o"` (pass-through)

Additional parser edge-case tests:
- Missing frontmatter delimiters → `CostModelError`.
- Missing `token_cost_per_1k` block → `CostModelError`.
- Malformed indentation → `CostModelError` with line info.

## Risks

1. **Fragile YAML parser**: The hand-rolled parser handles only the
   subset used by `.agent/config.md` today. If config grows to use
   YAML features like anchors, flow mappings, or multi-line strings,
   the parser will need extension. Mitigated by: (a) the function
   signature is stable — only the body changes; (b) config is under
   our control.
2. **`lru_cache` and config hot-reload**: If config changes mid-process
   the cached rates are stale. Not a concern for capture hooks (each
   invocation is a fresh subprocess), but would matter if the module
   were imported into a long-lived process. Mitigated by accepting the
   subprocess-per-event model.
3. **Windows path handling**: `Path(__file__).resolve().parents[1]`
   must correctly traverse from `.agent/telemetry/cost_model.py` up to
   `.agent/`. This works on Windows with `pathlib`. No risk.
