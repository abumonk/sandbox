"""Shared helpers and path constants for ADV-010 telemetry tests.

Import this module from any test file to get:
  - REPO_ROOT: Path to the Sandbox root
  - TELEMETRY_DIR: Path to .agent/telemetry/
  - FIXTURES_DIR: Path to tests/fixtures/
  - load_event_fixture(name): parse fixtures/events/{name}.json -> dict
  - make_temp_metrics(tmpdir, rows, frontmatter): create metrics.md in tmpdir
  - make_temp_manifest(tmpdir, task_rows): create manifest.md with ## Evaluations
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — insert repo root so "from .agent.telemetry import ..." works.
# We cannot use dotted imports with a leading dot in the package name, so
# we use sys.path insertion and import by the package path alias.
# ---------------------------------------------------------------------------

# tests/ -> ADV-010/ -> adventures/ -> .agent/ -> Sandbox/
REPO_ROOT = Path(__file__).resolve().parents[4]

# Insert repo root so we can do:  import _agent_telemetry.schema  (see below)
# Actually we use a path-based importlib trick via sys.path.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TELEMETRY_DIR = REPO_ROOT / ".agent" / "telemetry"
FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Insert telemetry parent so `from telemetry import ...` works without the
# leading-dot problem.  The parent of telemetry is .agent/.
_AGENT_DIR = REPO_ROOT / ".agent"
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def load_event_fixture(name: str) -> dict:
    """Read and parse ``fixtures/events/{name}`` as JSON.

    ``name`` may include or omit the ``.json`` extension.
    """
    if not name.endswith(".json"):
        name = name + ".json"
    path = FIXTURES_DIR / "events" / name
    return json.loads(path.read_text(encoding="utf-8"))


def make_temp_metrics(
    tmpdir: Path,
    rows: list[str],
    *,
    adventure_id: str = "ADV-099",
    total_tokens_in: int = 0,
    total_tokens_out: int = 0,
    total_duration: int = 0,
    total_cost: float = 0.0,
    agent_runs: int = 0,
) -> Path:
    """Create a minimal ``metrics.md`` in *tmpdir* and return its path.

    Parameters
    ----------
    tmpdir:
        Temporary directory (``Path``).
    rows:
        List of pipe-table data row strings (no trailing newline needed).
    adventure_id, total_tokens_in, ...:
        Frontmatter field values.
    """
    from schema import ROW_HEADER, ROW_SEPARATOR  # type: ignore[import]

    fm = (
        f"---\n"
        f"adventure_id: {adventure_id}\n"
        f"total_tokens_in: {total_tokens_in}\n"
        f"total_tokens_out: {total_tokens_out}\n"
        f"total_duration: {total_duration}\n"
        f"total_cost: {total_cost:.4f}\n"
        f"agent_runs: {agent_runs}\n"
        f"---\n"
    )
    table = "\n## Agent Runs\n\n" + ROW_HEADER + "\n" + ROW_SEPARATOR + "\n"
    row_block = "".join(r + "\n" for r in rows)

    mp = tmpdir / "metrics.md"
    mp.write_text(fm + table + row_block, encoding="utf-8")
    return mp


def make_temp_manifest(
    tmpdir: Path,
    task_rows: list[dict],
    *,
    adventure_id: str = "ADV-099",
) -> Path:
    """Create a minimal ``manifest.md`` with ``## Evaluations`` table.

    Each dict in *task_rows* must have key ``task`` and may optionally have
    ``est_tokens`` (str, default ``"--"``).  Other actuals columns are set
    to ``---``.
    """
    header = (
        "| Task | Access Requirements | Skill Set | Est. Duration | Est. Tokens"
        " | Est. Cost | Actual Duration | Actual Tokens | Actual Cost | Variance |"
    )
    sep = (
        "|------|---------------------|-----------|---------------|-------------|"
        "-----------|-----------------|---------------|-------------|----------|"
    )
    data_lines = []
    for row in task_rows:
        task = row.get("task", "ADV099-T001")
        est_tokens = row.get("est_tokens", "--")
        data_lines.append(
            f"| {task} | Read, Write | coding | 20min | {est_tokens}"
            f" | --- | --- | --- | --- | --- |"
        )

    fm = (
        f"---\n"
        f"id: {adventure_id}\n"
        f"title: Test Fixture Adventure\n"
        f"state: completed\n"
        f"---\n"
    )
    body = "\n## Evaluations\n\n" + header + "\n" + sep + "\n"
    body += "\n".join(data_lines) + "\n"

    mp = tmpdir / "manifest.md"
    mp.write_text(fm + body, encoding="utf-8")
    return mp
