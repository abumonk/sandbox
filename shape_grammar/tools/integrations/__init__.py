"""shape_grammar.tools.integrations — Adapters that wrap Ark CLI tools.

Each adapter shells out to the corresponding ``ark`` CLI subcommand and
augments the result with shape-grammar-specific semantics (semantic labels,
rule-tree edges, terminal counts).

Adapter subcommand availability (probed 2026-04-14):
  - ``ark graph``  → available (visualizer_adapter uses this)
  - ``ark impact`` → available (impact_adapter uses this)
  - ``ark diff``   → available (diff_adapter uses this)

All three subcommands exist in the current Ark CLI. If a future Ark version
removes or renames them, the adapter raises ``AdapterError`` with a hint to
``research/ark-as-host-feasibility.md``.
"""

from shape_grammar.tools.integrations._errors import AdapterError
from shape_grammar.tools.integrations.visualizer_adapter import visualize
from shape_grammar.tools.integrations.impact_adapter import impact
from shape_grammar.tools.integrations.diff_adapter import diff

__all__ = ["AdapterError", "visualize", "impact", "diff"]
