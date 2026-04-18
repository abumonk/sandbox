"""adventure_pipeline.tools — IR extractor for live adventure directories.

Re-exports the public API from ir.py for programmatic use:
  extract_ir(adv_id_or_path, adventures_root=None) -> AdventurePipelineIR
  to_json(ir) -> str
  AdventurePipelineIR + record dataclasses (Task, Document, TargetCondition,
  Permission, Decision, Agent, Role)
"""

from .ir import (  # noqa: F401
    AdventurePipelineIR,
    Task,
    Document,
    TargetCondition,
    Permission,
    Decision,
    Agent,
    Role,
    extract_ir,
    to_json,
)
