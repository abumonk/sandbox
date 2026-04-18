# Design — Cost Model

## Overview

A single-source-of-truth pure function that maps `(model,
tokens_in, tokens_out)` to a USD cost. Lives in
`.agent/telemetry/cost_model.py`. Reads rates from
`.agent/config.md` frontmatter so the rates file does not fork.

## Target files

- `.agent/telemetry/cost_model.py` — the module (new).
- `.agent/config.md` — read-only source of rates (no changes
  authored by this adventure; relies on existing L17-L20).

## Rate lookup

```python
def load_rates(config_path: Path) -> Dict[str, float]:
    """Parse YAML frontmatter of .agent/config.md and return
    adventure.token_cost_per_1k as {model: usd_per_1k}."""
```

Stdlib constraint: Python stdlib has no YAML parser. The config file
uses a trivial YAML subset (flat mapping with one nested mapping
`adventure.token_cost_per_1k`). We parse with a hand-rolled reader:

1. Read lines between the first and second `---` line.
2. Track indentation depth (2-space).
3. Recognise `key: scalar` and `key:` (opening a nested block).
4. Coerce scalars: int, float, quoted string, bare string.

Total implementation: ~40 LOC in `cost_model.py`. Tested in
`tests/test_cost_model.py` with fixtures covering:

- Standard `.agent/config.md` frontmatter (happy path).
- Missing `token_cost_per_1k` block → `CostModelError`.
- Missing frontmatter entirely → `CostModelError`.
- Malformed indentation → `CostModelError` with line number.

If in future the config grows beyond our parser's subset, we replace
the reader — the function signature stays.

## Cost function

```python
def cost_for(model: str, tokens_in: int, tokens_out: int,
             rates: Dict[str, float] | None = None) -> float:
    """Return USD cost to 4dp. Raises UnknownModelError if model
    is not in rates. Never returns 0.0 for a non-zero-token run
    unless the rate itself is 0.0."""
```

Rules:

- `rates` defaults to `load_rates()` (memoised).
- `model` is normalized first via `normalize_model(model)`:
  - `claude-opus-4-6` / `claude-opus-*` / `opus-*` → `opus`.
  - `claude-sonnet-*` / `sonnet-*` → `sonnet`.
  - `claude-haiku-*` / `haiku-*` → `haiku`.
  - Anything else → passed through unchanged (lets future models be
    added to the config without code changes).
- Cost formula (flat per-token — no input/output split in current
  config, preserving compatibility):

  ```
  cost = (tokens_in + tokens_out) / 1000.0 * rates[model_key]
  ```

- Returned as `round(cost, 4)`.

### Known-models

```python
def known_models() -> FrozenSet[str]:
    """Union of rate keys and their common aliases."""
    base = set(load_rates().keys())
    return frozenset(base | {f"claude-{m}-4-6" for m in base}
                          | {f"claude-{m}-*" for m in base})
```

Used by `schema.validate_event` so a payload with an unrecognised
model fails *validation*, not cost.

## Future-proofing

If Anthropic publishes differentiated input/output rates (which they
typically do for Opus/Sonnet), we extend the config to:

```yaml
token_cost_per_1k:
  opus: { in: 0.015, out: 0.075 }
  sonnet: { in: 0.003, out: 0.015 }
```

and `cost_for` grows a branch. The test suite must add a mixed-rate
fixture when that happens. ADV-010 ships with the flat-rate config as
it exists today, but structures the parser so the upgrade is
additive.

## Target Conditions

- TC-CM-1: `cost_for("opus", 85000, 28000)` equals the hand-computed
  value from the rates table to 4dp — single fixture asserting the
  formula.
- TC-CM-2: `cost_for("unknown-model-xyz", 1, 1)` raises
  `UnknownModelError`, NOT returns 0.0.
- TC-CM-3: `normalize_model` correctly maps every alias in a
  table-driven test (≥ 6 cases).
- TC-CM-4: `load_rates` returns `{"opus": 0.015, "sonnet": 0.003,
  "haiku": 0.001}` from the current `.agent/config.md`.

## Dependencies

None. This is a pure module.
