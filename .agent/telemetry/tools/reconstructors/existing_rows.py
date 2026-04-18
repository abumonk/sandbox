"""Parse existing ``metrics.md`` pipe-tables into :class:`Candidate` objects.

Usage::

    from pathlib import Path
    from telemetry.tools.reconstructors.existing_rows import parse

    candidates = parse(Path(".agent/adventures/ADV-008/metrics.md"))

Each data row in the ``## Agent Runs`` table yields one ``Candidate`` with
``confidence="medium"`` and ``source="existing"``.  Tilde-prefixed numeric
fields (e.g. ``~18000``) have the ``~`` stripped; duration strings such as
``4min``, ``95s``, or ``16min`` are converted to integer seconds.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from . import Candidate

# Regex to extract individual duration components: e.g. "4min", "95s",
# "2min 30s".  We sum all matches.
_RE_DURATION = re.compile(r"(\d+)\s*min|(\d+)\s*s")


def _parse_duration(raw: str) -> int:
    """Convert a duration string to integer seconds.

    Handles formats:
    - ``NNmin``    e.g. "16min"   -> 960
    - ``NNs``      e.g. "95s"     -> 95
    - ``NNmin NNs`` e.g. "2min 30s" -> 150

    Returns 0 for unrecognised formats.
    """
    total = 0
    for m in _RE_DURATION.finditer(raw):
        if m.group(1):          # minutes group
            total += int(m.group(1)) * 60
        elif m.group(2):        # seconds group
            total += int(m.group(2))
    return total


def _strip_tilde(value: str) -> str:
    """Remove a leading ``~`` from *value* if present."""
    return value.lstrip("~")


def parse(metrics_path: Path) -> List[Candidate]:
    """Parse *metrics_path* and return one ``Candidate`` per data row.

    Parameters
    ----------
    metrics_path:
        Path to a ``metrics.md`` file containing an ``## Agent Runs``
        pipe-table section.

    Returns
    -------
    list[Candidate]
        Empty list if the file does not exist, has no ``## Agent Runs``
        section, or contains no data rows.
    """
    if not metrics_path.exists():
        return []

    text = metrics_path.read_text(encoding="utf-8")

    # Locate the ## Agent Runs section.
    section_match = re.search(r"^##\s+Agent Runs\b", text, re.MULTILINE)
    if not section_match:
        return []

    # Work only with lines after the section header.
    section_text = text[section_match.end():]

    candidates: List[Candidate] = []
    header_found = False
    separator_found = False
    column_indices: dict[str, int] = {}

    for raw_line in section_text.splitlines():
        line = raw_line.strip()

        if not line.startswith("|"):
            # Stop at the next section header or blank-after-table.
            if line.startswith("#"):
                break
            continue

        # Split the pipe-delimited row into cells.
        parts = line.split("|")
        # Leading and trailing "|" produce empty strings; strip them.
        cells = [p.strip() for p in parts[1:-1]]

        if not header_found:
            # First pipe row is the header.
            header_found = True
            column_indices = {name.lower(): i for i, name in enumerate(cells)}
            continue

        if not separator_found:
            # Second pipe row is the separator (``|---|---|...``).
            separator_found = True
            continue

        # Data row.
        if not cells:
            continue

        # Helper to get a cell by (case-insensitive) column name, falling
        # back to positional index if the header mapping is unavailable.
        def _cell(name: str, fallback_idx: int) -> str:
            idx = column_indices.get(name.lower(), fallback_idx)
            return cells[idx] if idx < len(cells) else ""

        agent = _cell("agent", 0)
        task = _cell("task", 1) or "-"
        model = _cell("model", 2) or "unknown"

        tokens_in_raw = _strip_tilde(_cell("tokens in", 3))
        tokens_out_raw = _strip_tilde(_cell("tokens out", 4))
        duration_raw = _strip_tilde(_cell("duration", 5))
        turns_raw = _strip_tilde(_cell("turns", 6))
        result = _cell("result", 7) or "unknown"

        # Coerce numeric fields; default to 0 on failure.
        try:
            tokens_in = int(tokens_in_raw)
        except (ValueError, TypeError):
            tokens_in = 0

        try:
            tokens_out = int(tokens_out_raw)
        except (ValueError, TypeError):
            tokens_out = 0

        duration_s = _parse_duration(duration_raw)

        try:
            turns = int(turns_raw)
        except (ValueError, TypeError):
            turns = 0

        candidates.append(
            Candidate(
                run_id="",
                timestamp="",
                agent=agent,
                task=task,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                duration_s=duration_s,
                turns=turns,
                cost=0.0,
                result=result,
                confidence="medium",
                source="existing",
            )
        )

    return candidates
