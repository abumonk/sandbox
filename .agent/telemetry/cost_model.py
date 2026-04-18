"""Cost model for the agent pipeline telemetry subsystem.

Public API
----------
load_rates(config_path=None) -> dict[str, float]
    Read token-cost-per-1k rates from `.agent/config.md` (memoised).

normalize_model(model_id: str) -> str
    Map a full model ID (e.g. ``claude-opus-4-6``) to its canonical
    short name (``opus``, ``sonnet``, or ``haiku``).

known_models() -> frozenset[str]
    Return the union of canonical rate keys and their common aliases.

cost_for(model, tokens_in, tokens_out, rates=None) -> float
    Compute USD cost rounded to 4 decimal places.
    Raises ``UnknownModelError`` for unrecognised model IDs.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from .errors import CostModelError, UnknownModelError

# ---------------------------------------------------------------------------
# Internal: hand-rolled YAML-subset frontmatter parser (~40 LOC)
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config.md"


def _coerce(value: str):
    """Coerce a scalar YAML value string to int, float, or str."""
    stripped = value.strip()
    if (stripped.startswith('"') and stripped.endswith('"')) or (
        stripped.startswith("'") and stripped.endswith("'")
    ):
        return stripped[1:-1]
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        pass
    return stripped


def _parse_frontmatter(text: str) -> dict:
    """Parse YAML-subset frontmatter delimited by ``---`` lines.

    Supports nested mappings via 2-space indentation.
    Raises ``CostModelError`` on structural errors.
    """
    lines = text.splitlines()

    # Find the opening delimiter
    start = None
    for i, line in enumerate(lines):
        if line.rstrip() == "---":
            start = i
            break
    if start is None:
        raise CostModelError("config.md: missing opening '---' frontmatter delimiter")

    # Collect lines until the closing delimiter
    fm_lines: list[tuple[int, str]] = []  # (original_lineno, content)
    end = None
    for i in range(start + 1, len(lines)):
        if lines[i].rstrip() == "---":
            end = i
            break
        fm_lines.append((i + 1, lines[i]))  # 1-based line numbers for errors

    if end is None:
        raise CostModelError("config.md: missing closing '---' frontmatter delimiter")

    # Parse key: value pairs with indent-based nesting
    root: dict = {}
    # Stack entries: (indent_level, dict_ref)
    stack: list[tuple[int, dict]] = [(-1, root)]

    for lineno, raw in fm_lines:
        if not raw.strip() or raw.strip().startswith("#"):
            continue  # skip blank lines and comments

        # Measure indentation (must be multiples of 2 spaces)
        stripped_left = raw.lstrip(" ")
        indent = len(raw) - len(stripped_left)
        if indent % 2 != 0:
            raise CostModelError(
                f"config.md line {lineno}: indentation {indent} is not a "
                "multiple of 2 spaces"
            )

        if ":" not in stripped_left:
            # Not a key-value line (e.g. list items with '-'); skip gracefully
            continue

        colon_pos = stripped_left.index(":")
        key = stripped_left[:colon_pos].strip()
        value_raw = stripped_left[colon_pos + 1:].strip()

        # Pop stack until we find the parent at indent - 2
        parent_indent = indent - 2
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()

        # The current parent dict
        _, parent_dict = stack[-1]

        if value_raw == "" or value_raw.startswith("#"):
            # This key introduces a nested mapping; create child dict
            child: dict = {}
            parent_dict[key] = child
            stack.append((indent, child))
        else:
            parent_dict[key] = _coerce(value_raw)

    return root


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def load_rates(config_path: str | None = None) -> dict[str, float]:
    """Return ``{model_name: cost_per_1k_tokens}`` from ``config.md``.

    The result is memoised for the lifetime of the process.

    Parameters
    ----------
    config_path:
        Absolute path to a ``config.md`` file.  Defaults to the standard
        ``.agent/config.md`` relative to this package.

    Raises
    ------
    CostModelError
        If the config file is missing, malformed, or lacks the
        ``adventure.token_cost_per_1k`` block.
    """
    path = Path(config_path) if config_path else _DEFAULT_CONFIG
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise CostModelError(f"config.md not found at {path}")

    fm = _parse_frontmatter(text)

    try:
        rates = fm["adventure"]["token_cost_per_1k"]
    except (KeyError, TypeError):
        raise CostModelError(
            "config.md missing adventure.token_cost_per_1k"
        )

    if not isinstance(rates, dict) or not rates:
        raise CostModelError("token_cost_per_1k must be a non-empty mapping")

    return {k: float(v) for k, v in rates.items()}


def normalize_model(model_id: str) -> str:
    """Map a model ID string to its canonical short name.

    Recognised patterns (case-sensitive):

    - ``opus``, ``claude-opus``, ``claude-opus-*``, ``opus-*``  → ``"opus"``
    - Same for ``sonnet`` and ``haiku``
    - Anything else is returned unchanged.

    Parameters
    ----------
    model_id:
        A raw model identifier such as ``"claude-opus-4-6"``.

    Returns
    -------
    str
        The canonical short name, or *model_id* if unrecognised.
    """
    for canon in ("opus", "sonnet", "haiku"):
        if model_id == canon:
            return canon
        if re.match(rf"^(claude-)?{canon}(-.*)?$", model_id):
            return canon
    return model_id


def known_models() -> frozenset[str]:
    """Return a frozen set of all recognised model identifiers.

    Includes canonical short names from the config plus their common
    ``claude-{name}`` and ``claude-{name}-4-6`` aliases.
    """
    base = set(load_rates().keys())
    return frozenset(
        base
        | {f"claude-{m}" for m in base}
        | {f"claude-{m}-4-6" for m in base}
    )


def cost_for(
    model: str,
    tokens_in: int,
    tokens_out: int,
    rates: dict[str, float] | None = None,
) -> float:
    """Compute the USD cost for a model invocation.

    Formula: ``(tokens_in + tokens_out) / 1000 * rate_per_1k``,
    rounded to 4 decimal places.

    Parameters
    ----------
    model:
        Model identifier (canonical or full, e.g. ``"claude-opus-4-6"``).
    tokens_in:
        Number of input (prompt) tokens consumed.
    tokens_out:
        Number of output (completion) tokens generated.
    rates:
        Optional override rate table.  Defaults to ``load_rates()``.

    Returns
    -------
    float
        Rounded USD cost.

    Raises
    ------
    UnknownModelError
        If *model* (after normalisation) is not in the rate table.
    """
    if rates is None:
        rates = load_rates()
    key = normalize_model(model)
    if key not in rates:
        raise UnknownModelError(
            f"Unknown model: {model!r} (normalized: {key!r}). "
            f"Known: {sorted(rates)}"
        )
    total_tokens = tokens_in + tokens_out
    cost = total_tokens / 1000.0 * rates[key]
    return round(cost, 4)
