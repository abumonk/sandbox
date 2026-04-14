"""
ARK DSL Parser
Парсит .ark файлы → AST (Python dict) → JSON
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from lark import Lark, Transformer, v_args, Token, Tree
from lark.exceptions import (
    UnexpectedInput,
    UnexpectedToken,
    UnexpectedCharacters,
    UnexpectedEOF,
)


# ============================================================
# PARSE ERROR REPORTING
# ============================================================

class ArkParseError(Exception):
    """User-facing parse error with source position and snippet."""

    def __init__(self, message: str, file_path: Optional[str], line: int,
                 column: int, snippet: str, caret: str,
                 expected: Optional[list] = None):
        super().__init__(message)
        self.message = message
        self.file_path = file_path
        self.line = line
        self.column = column
        self.snippet = snippet  # pre-formatted multi-line context block
        self.caret = caret      # caret line (e.g. "    ^^^^^ expected ...")
        self.expected = expected or []

    def format_report(self) -> str:
        path = self.file_path if self.file_path else "<string>"
        out = [f"error: {self.message}",
               f"  --> {path}:{self.line}:{self.column}",
               "      |"]
        # The snippet builder returns context lines WITH the caret line
        # already interleaved after the offending line, so we just append
        # the whole block.  If for any reason there is no snippet, fall
        # back to a stand-alone caret so the report always contains '^'.
        if self.snippet:
            out.append(self.snippet.rstrip("\n"))
            if self.caret and self.caret not in self.snippet:
                out.append(self.caret.rstrip("\n"))
        else:
            out.append(self.caret.rstrip("\n") if self.caret else "      ^")
        return "\n".join(out)


def _build_snippet(source: str, line: int, column: int,
                   expected: Optional[list] = None,
                   bad_token: Optional[str] = None) -> tuple:
    """Return (snippet_block, caret_line) for the given error position."""
    src_lines = source.split("\n")
    if not src_lines:
        return ("", "")
    # 1-based line → 0-based index, clamp.
    idx = max(0, min(len(src_lines) - 1, line - 1))
    start = max(0, idx - 2)
    end = min(len(src_lines), idx + 2)
    width = len(str(end))
    out = []
    caret_line = ""
    for i in range(start, end):
        ln = i + 1
        prefix = f"{ln:>{width}} | "
        out.append(prefix + src_lines[i])
        if i == idx:
            # caret under the offending column (1-based)
            col = max(1, column)
            span = max(1, len(bad_token) if bad_token else 1)
            pad = " " * (len(prefix) + col - 1)
            hint = ""
            if expected:
                shown = " | ".join(sorted(str(e) for e in expected)[:6])
                more = "" if len(expected) <= 6 else f" | ... (+{len(expected)-6})"
                hint = f" expected {shown}{more}"
            caret_line = pad + ("^" * span) + hint
            out.append(caret_line)
    # `out` contains source context with the caret line interleaved
    # directly after the offending line.  We return the whole block as
    # `snippet`, and also return the bare caret line separately so
    # callers (and tests) can introspect it.
    return ("\n".join(out), caret_line)


def _lark_to_ark_error(exc: UnexpectedInput, source: str,
                       file_path: Optional[str]) -> ArkParseError:
    """Convert a Lark UnexpectedInput exception → ArkParseError."""
    line = getattr(exc, "line", 1) or 1
    column = getattr(exc, "column", 1) or 1
    expected = None
    bad_token = None
    if isinstance(exc, UnexpectedToken):
        tok = getattr(exc, "token", None)
        bad_token = str(tok) if tok is not None else None
        message = f"unexpected token {bad_token!r}" if bad_token else "unexpected token"
        exp = getattr(exc, "expected", None) or getattr(exc, "accepts", None)
        if exp:
            expected = list(exp)
    elif isinstance(exc, UnexpectedCharacters):
        ch = source[exc.pos_in_stream] if getattr(exc, "pos_in_stream", None) is not None and exc.pos_in_stream < len(source) else ""
        bad_token = ch
        message = f"unexpected character {ch!r}" if ch else "unexpected character"
        exp = getattr(exc, "allowed", None)
        if exp:
            expected = list(exp)
    elif isinstance(exc, UnexpectedEOF):
        message = "unexpected end of file (did you forget a closing '}'?)"
        exp = getattr(exc, "expected", None)
        if exp:
            expected = list(exp)
        # Point at the last line.
        src_lines = source.split("\n")
        if src_lines:
            line = len(src_lines)
            column = max(1, len(src_lines[-1]) + 1)
    else:
        message = str(exc).splitlines()[0] if str(exc) else "parse error"

    snippet, caret = _build_snippet(source, line, column, expected, bad_token)
    return ArkParseError(
        message=message,
        file_path=file_path,
        line=line,
        column=column,
        snippet=snippet,
        caret=caret,
        expected=expected,
    )

# ============================================================
# AST DATACLASSES
# ============================================================

@dataclass
class TypedField:
    name: str
    type: dict

@dataclass
class MetaPair:
    key: str
    value: dict

@dataclass
class InPort:
    kind: str = "in_port"
    fields: list = field(default_factory=list)

@dataclass
class OutPort:
    kind: str = "out_port"
    meta: list = field(default_factory=list)
    fields: list = field(default_factory=list)

@dataclass
class ProcessRule:
    kind: str = "process"
    meta: list = field(default_factory=list)
    pre: list = field(default_factory=list)
    post: list = field(default_factory=list)
    body: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class DataField:
    kind: str = "data"
    name: str = ""
    type: dict = field(default_factory=dict)
    constraint: Optional[dict] = None
    default: Optional[dict] = None

@dataclass
class EntityDef:
    kind: str = ""  # "abstraction" or "class"
    name: str = ""
    inherits: list = field(default_factory=list)
    data_fields: list = field(default_factory=list)
    in_ports: list = field(default_factory=list)
    out_ports: list = field(default_factory=list)
    processes: list = field(default_factory=list)
    invariants: list = field(default_factory=list)
    temporals: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class InstanceDef:
    kind: str = "instance"
    name: str = ""
    class_name: str = ""
    assignments: list = field(default_factory=list)

@dataclass
class IslandDef:
    kind: str = "island"
    name: str = ""
    strategy: Optional[str] = None
    memory: list = field(default_factory=list)
    contains: list = field(default_factory=list)
    in_ports: list = field(default_factory=list)
    out_ports: list = field(default_factory=list)
    processes: list = field(default_factory=list)
    classes: list = field(default_factory=list)
    data_fields: list = field(default_factory=list)
    invariants: list = field(default_factory=list)
    temporals: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class BridgeDef:
    kind: str = "bridge"
    name: str = ""
    from_port: str = ""
    to_port: str = ""
    contract: Optional[dict] = None

@dataclass
class RegistryDef:
    kind: str = "registry"
    name: str = ""
    entries: list = field(default_factory=list)

@dataclass
class VerifyDef:
    kind: str = "verify"
    target: str = ""
    checks: list = field(default_factory=list)

@dataclass
class PrimitiveDef:
    kind: str = "primitive"
    name: str = ""
    description: Optional[str] = None

@dataclass
class StructDef:
    kind: str = "struct"
    name: str = ""
    fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class EnumDef:
    kind: str = "enum"
    name: str = ""
    variants: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class ExpressionDef:
    kind: str = "expression"
    name: str = ""
    inputs: list = field(default_factory=list)    # List of typed_field dicts
    output: dict = field(default_factory=dict)     # type_expr dict
    chain: dict = field(default_factory=dict)      # expr dict (pipe or single atom)
    description: Optional[str] = None

@dataclass
class PredicateDef:
    kind: str = "predicate"
    name: str = ""
    inputs: list = field(default_factory=list)    # List of typed_field dicts
    check: dict = field(default_factory=dict)      # expr dict (must type-check to Bool)
    description: Optional[str] = None

@dataclass
class RoleDef:
    kind: str = "role"
    name: str = ""
    inherits: list = field(default_factory=list)
    tier: Optional[int] = None
    responsibilities: list = field(default_factory=list)
    escalates_to: Optional[str] = None
    skills: list = field(default_factory=list)
    tools: list = field(default_factory=list)
    data_fields: list = field(default_factory=list)
    in_ports: list = field(default_factory=list)
    out_ports: list = field(default_factory=list)
    processes: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class TierGroup:
    level: int = 0
    members: list = field(default_factory=list)

@dataclass
class StudioDef:
    kind: str = "studio"
    name: str = ""
    tiers: list = field(default_factory=list)      # list of TierGroup
    contains: list = field(default_factory=list)
    data_fields: list = field(default_factory=list)
    invariants: list = field(default_factory=list)
    processes: list = field(default_factory=list)
    bridges: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class CommandDef:
    kind: str = "command"
    name: str = ""
    phase: Optional[str] = None
    prompt: Optional[str] = None
    role: Optional[str] = None
    output: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class HookDef:
    kind: str = "hook"
    name: str = ""
    event: Optional[str] = None
    pattern: Optional[str] = None
    action: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class RuleDef:
    kind: str = "rule"
    name: str = ""
    path: Optional[str] = None
    constraint: Optional[str] = None
    severity: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class TemplateDef:
    kind: str = "template"
    name: str = ""
    sections: list = field(default_factory=list)
    bound_to: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

# ============================================================
# EVOLUTION SYSTEM DATACLASSES
# ============================================================

@dataclass
class EvolutionTargetDef:
    kind: str = "evolution_target"
    name: str = ""
    tier: Optional[str] = None
    file_ref: Optional[str] = None
    constraints: list = field(default_factory=list)  # list of dicts from constraints_block
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class EvalDatasetDef:
    kind: str = "eval_dataset"
    name: str = ""
    source: Optional[str] = None
    splits: dict = field(default_factory=dict)        # {split_name: ratio}
    scoring_rubric: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class FitnessFunctionDef:
    kind: str = "fitness_function"
    name: str = ""
    dimensions: list = field(default_factory=list)    # list of dicts {name, weight, metric}
    aggregation: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class OptimizerDef:
    kind: str = "optimizer"
    name: str = ""
    engine: Optional[str] = None
    iterations: Optional[int] = None
    population_size: Optional[int] = None
    mutation_strategy: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class BenchmarkGateDef:
    kind: str = "benchmark_gate"
    name: str = ""
    benchmark: Optional[str] = None
    tolerance: Optional[float] = None
    pass_criteria: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class EvolutionRunDef:
    kind: str = "evolution_run"
    name: str = ""
    target_ref: Optional[str] = None
    optimizer_ref: Optional[str] = None
    dataset_ref: Optional[str] = None
    gate_ref: Optional[str] = None
    status: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class EvolutionConstraintDef:
    kind: str = "evolution_constraint"
    name: str = ""
    type: Optional[str] = None
    threshold: Optional[dict] = None   # expr dict from threshold_stmt
    enforcement: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

# ============================================================
# AGENT SYSTEM DATACLASSES
# ============================================================

@dataclass
class AgentDef:
    kind: str = "agent"
    name: str = ""
    persona: Optional[str] = None
    model_ref: Optional[str] = None
    capabilities: list = field(default_factory=list)
    learning_ref: Optional[str] = None
    backends: list = field(default_factory=list)
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class PlatformDef:
    kind: str = "platform"
    name: str = ""
    type: Optional[str] = None
    auth: Optional[str] = None
    format: Optional[str] = None
    endpoint: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class GatewayDef:
    kind: str = "gateway"
    name: str = ""
    agent_ref: Optional[str] = None
    platforms: list = field(default_factory=list)
    routes: list = field(default_factory=list)   # list of dicts {from, to}
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class ExecutionBackendDef:
    kind: str = "execution_backend"
    name: str = ""
    backend_type: Optional[str] = None
    connection: Optional[str] = None
    limits: dict = field(default_factory=dict)
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class AgentSkillDef:
    kind: str = "skill"
    name: str = ""
    trigger: Optional[str] = None
    steps: list = field(default_factory=list)
    status: Optional[str] = None
    improvement_history: list = field(default_factory=list)
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class LearningConfigDef:
    kind: str = "learning_config"
    name: str = ""
    mode: Optional[str] = None
    skill_gen: Optional[dict] = None
    memory_persist: Optional[dict] = None
    session_search: Optional[dict] = None
    self_improve: Optional[dict] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class CronTaskDef:
    kind: str = "cron_task"
    name: str = ""
    schedule: Optional[str] = None
    agent_ref: Optional[str] = None
    platform_delivery: Optional[str] = None
    action: Optional[str] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class ModelConfigDef:
    kind: str = "model_config"
    name: str = ""
    provider: Optional[str] = None
    model_id: Optional[str] = None
    fallback: Optional[str] = None
    params: dict = field(default_factory=dict)
    cost_limit: Optional[dict] = None
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None


# ============================================================
# VISUAL COMMUNICATION LAYER DATACLASSES
# ============================================================

@dataclass
class DiagramDef:
    kind: str = "diagram"
    name: str = ""
    diagram_type: Optional[str] = None
    source: Optional[str] = None
    render_config: Optional[str] = None
    description: Optional[str] = None
    data_fields: list = field(default_factory=list)

@dataclass
class PreviewDef:
    kind: str = "preview"
    name: str = ""
    source: Optional[str] = None
    viewport: Optional[str] = None
    mode: Optional[str] = None
    render_config: Optional[str] = None
    description: Optional[str] = None
    data_fields: list = field(default_factory=list)

@dataclass
class AnnotationDef:
    kind: str = "annotation"
    name: str = ""
    target: Optional[str] = None
    elements: list = field(default_factory=list)
    description: Optional[str] = None
    data_fields: list = field(default_factory=list)

@dataclass
class VisualReviewDef:
    kind: str = "visual_review"
    name: str = ""
    target: Optional[str] = None
    render_config: Optional[str] = None
    feedback_mode: Optional[str] = None
    description: Optional[str] = None
    data_fields: list = field(default_factory=list)

@dataclass
class ScreenshotDef:
    kind: str = "screenshot"
    name: str = ""
    path: Optional[str] = None
    source: Optional[str] = None
    tags: list = field(default_factory=list)
    description: Optional[str] = None
    data_fields: list = field(default_factory=list)

@dataclass
class VisualSearchDef:
    kind: str = "visual_search"
    name: str = ""
    search_mode: Optional[str] = None
    query: Optional[str] = None
    tags: list = field(default_factory=list)
    max_results: Optional[int] = None
    description: Optional[str] = None
    data_fields: list = field(default_factory=list)

@dataclass
class RenderConfigDef:
    kind: str = "render_config"
    name: str = ""
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    theme: Optional[str] = None
    scale: Optional[float] = None
    description: Optional[str] = None
    data_fields: list = field(default_factory=list)


@dataclass
class PipeStage:
    name: str = ""          # kebab-case allowed, e.g. "text-to-lower"
    args: list = field(default_factory=list)  # extra args beyond piped value

@dataclass
class ArkFile:
    imports: list = field(default_factory=list)
    items: list = field(default_factory=list)
    # --- Indices built by _build_indices() after parsing/import resolution ---
    # Top-level classes only (not island-nested).
    classes: dict = field(default_factory=dict)         # name -> EntityDef
    # Instances grouped by their declared class_name. Includes orphans
    # (instances whose class_name isn't declared) — caller can detect this
    # by checking `class_name not in ark_file.classes`.
    instances: dict = field(default_factory=dict)       # class_name -> [InstanceDef]
    # Per-island nested classes: island_name -> {class_name -> EntityDef}.
    # Separate map so top-level and island-scoped names can't collide.
    island_classes: dict = field(default_factory=dict)
    # Expression and predicate indices: name -> index into items list.
    expression_index: dict = field(default_factory=dict)  # name -> int index
    predicate_index: dict = field(default_factory=dict)   # name -> int index
    # Studio hierarchy indices: name -> definition dataclass.
    roles: dict = field(default_factory=dict)             # name -> RoleDef
    studios: dict = field(default_factory=dict)           # name -> StudioDef
    commands: dict = field(default_factory=dict)          # name -> CommandDef
    # Evolution system indices: name -> definition dataclass.
    evolution_targets: dict = field(default_factory=dict)   # name -> EvolutionTargetDef
    eval_datasets: dict = field(default_factory=dict)       # name -> EvalDatasetDef
    fitness_functions: dict = field(default_factory=dict)   # name -> FitnessFunctionDef
    optimizers: dict = field(default_factory=dict)          # name -> OptimizerDef
    benchmark_gates: dict = field(default_factory=dict)     # name -> BenchmarkGateDef
    evolution_runs: dict = field(default_factory=dict)      # name -> EvolutionRunDef
    evolution_constraints: dict = field(default_factory=dict)  # name -> EvolutionConstraintDef
    # Agent system indices: name -> definition dataclass.
    agents: dict = field(default_factory=dict)               # name -> AgentDef
    platforms: dict = field(default_factory=dict)            # name -> PlatformDef
    gateways: dict = field(default_factory=dict)             # name -> GatewayDef
    execution_backends: dict = field(default_factory=dict)   # name -> ExecutionBackendDef
    agent_skills: dict = field(default_factory=dict)         # name -> AgentSkillDef
    learning_configs: dict = field(default_factory=dict)     # name -> LearningConfigDef
    cron_tasks: dict = field(default_factory=dict)           # name -> CronTaskDef
    model_configs: dict = field(default_factory=dict)        # name -> ModelConfigDef
    # Visual communication layer indices: name -> definition dataclass.
    diagrams: dict = field(default_factory=dict)             # name -> DiagramDef
    previews: dict = field(default_factory=dict)             # name -> PreviewDef
    annotations: dict = field(default_factory=dict)          # name -> AnnotationDef
    visual_reviews: dict = field(default_factory=dict)       # name -> VisualReviewDef
    screenshots: dict = field(default_factory=dict)          # name -> ScreenshotDef
    visual_searches: dict = field(default_factory=dict)      # name -> VisualSearchDef
    render_configs: dict = field(default_factory=dict)       # name -> RenderConfigDef

    def instances_of(self, class_name: str) -> list:
        """Return the list of instances declared for `class_name`, or []."""
        return self.instances.get(class_name, [])


# ============================================================
# LARK TRANSFORMER → AST
# ============================================================

class ArkTransformer(Transformer):
    """Converts Lark parse tree → ARK AST dataclasses"""

    # --- Primitives ---

    def IDENT(self, token):
        return str(token)

    def NUMBER(self, token):
        s = str(token)
        return float(s) if '.' in s else int(s)

    def STRING(self, items):
        # STRING matches: "content" → we get the inner content
        return str(items)

    # --- Expressions ---

    def ident_expr(self, items):
        return {"expr": "ident", "name": items[0]}

    def data_ref_expr(self, items):
        # `$data IDENT` is an explicit marker that this identifier refers
        # to a $data field of the enclosing entity. Semantically equivalent
        # to a bare IDENT — so we lower it to the same ident-expr shape.
        return {"expr": "ident", "name": str(items[0])}

    def number_expr(self, items):
        return {"expr": "number", "value": items[0]}

    def string_expr(self, items):
        return {"expr": "string", "value": items[0]}

    def true_expr(self, _):
        return {"expr": "bool", "value": True}

    def false_expr(self, _):
        return {"expr": "bool", "value": False}

    def path_expr(self, items):
        return items[0]  # dotted_path already handled

    def paren_expr(self, items):
        return items[0]

    def array_expr(self, items):
        return {"expr": "array", "elements": items[0] if items else []}

    @staticmethod
    def _fold_fixed_op(items, op):
        """Left-fold for operators that don't carry an op token (or/and)."""
        result = items[0]
        for rhs in items[1:]:
            result = {"expr": "binop", "op": op, "left": result, "right": rhs}
        return result

    @staticmethod
    def _fold_token_op(items):
        """Left-fold for (operand OP operand OP operand ...) flat lists."""
        result = items[0]
        i = 1
        while i + 1 < len(items):
            op = str(items[i])
            rhs = items[i + 1]
            result = {"expr": "binop", "op": op, "left": result, "right": rhs}
            i += 2
        return result

    def or_expr(self, items):
        if len(items) == 1:
            return items[0]
        return self._fold_fixed_op(items, "or")

    def and_expr(self, items):
        if len(items) == 1:
            return items[0]
        return self._fold_fixed_op(items, "and")

    def cmp_expr(self, items):
        if len(items) == 1:
            return items[0]
        return self._fold_token_op(items)

    def add_expr(self, items):
        if len(items) == 1:
            return items[0]
        return self._fold_token_op(items)

    def mul_expr(self, items):
        if len(items) == 1:
            return items[0]
        return self._fold_token_op(items)

    def temporal_expr(self, items):
        return {"expr": "temporal", "op": str(items[0]), "operand": items[1]}

    def not_expr(self, items):
        return {"expr": "unary", "op": "not", "operand": items[0]}

    def fn_call(self, items):
        name = items[0]
        args = items[1] if len(items) > 1 else []
        if isinstance(name, dict) and name.get("expr") == "path":
            name_str = ".".join(name["parts"])
        else:
            name_str = str(name)
        return {"expr": "call", "name": name_str, "args": args}

    def for_all_expr(self, items):
        ty = items[0]
        var = items[1]
        rest = items[2:]
        cond = None
        body = rest[-1] if rest else None
        if len(rest) > 1:
            cond = rest[0]
        return {"expr": "for_all", "type": ty, "var": var, "condition": cond, "body": body}

    # --- Pipe expressions ---

    def pipe_expr(self, items):
        if len(items) == 1:
            return items[0]  # no pipe, pass through
        head = items[0]
        stages = [{"name": s.name, "args": s.args} for s in items[1:]]
        return {"expr": "pipe", "head": head, "stages": stages}

    def pipe_stage(self, items):
        name = items[0]  # string from pipe_fn_ident
        args = items[1] if len(items) > 1 else []
        return PipeStage(name=name, args=args)

    def pipe_fn_ident(self, items):
        return "-".join(str(i) for i in items)

    # --- Param refs ---

    def var_ref(self, items):
        return {"expr": "param_ref", "ref_kind": "var", "name": str(items[0])}

    def prop_ref(self, items):
        parts = [str(i) for i in items]
        return {"expr": "param_ref", "ref_kind": "prop", "parts": parts}

    def idx_ref(self, items):
        return {"expr": "param_ref", "ref_kind": "idx", "name": str(items[0]), "index": items[1]}

    def nested_ref(self, items):
        return {"expr": "param_ref", "ref_kind": "nested", "inner": items[0]}

    # --- Paths ---

    def dotted_path(self, items):
        return {"expr": "path", "parts": [str(i) for i in items]}

    def dotted_path_or_ident(self, items):
        parts = [str(i) for i in items]
        if len(parts) == 1:
            return {"expr": "ident", "name": parts[0]}
        return {"expr": "path", "parts": parts}

    # --- Types ---

    def named_type(self, items):
        return {"type": "named", "name": items[0]}

    def generic_type(self, items):
        return {"type": "generic", "name": items[0], "param": items[1]}

    def array_type(self, items):
        ty = items[0]
        size = items[1] if len(items) > 1 else None
        return {"type": "array", "element": ty, "size": size}

    def type_expr(self, items):
        return items[0]

    # --- Constraints ---

    def range_constraint(self, items):
        return {"constraint": "range", "min": items[0], "max": items[1]}

    def enum_constraint(self, items):
        return {"constraint": "enum", "values": items[0]}

    def constraint(self, items):
        return items[0]

    def default_value(self, items):
        return items[0]

    # --- Meta ---

    def meta_pair(self, items):
        return {"key": items[0], "value": items[1]}

    def meta_pair_list(self, items):
        return list(items)

    def meta_brackets(self, items):
        return items[0] if items else []

    # --- Fields & Lists ---

    def typed_field(self, items):
        return {"name": items[0], "type": items[1]}

    def typed_field_list(self, items):
        return list(items)

    def ident_list(self, items):
        return [str(i) for i in items]

    def expr_list(self, items):
        return list(items)

    # --- Four Primitives ---

    def in_port(self, items):
        fields = items[0] if items else []
        return InPort(fields=fields)

    def empty_meta(self, items):
        return items[0] if items else []

    def out_port(self, items):
        meta = []
        fields = []
        for item in items:
            if isinstance(item, list) and item and isinstance(item[0], dict) and "key" in item[0]:
                meta = item
            elif isinstance(item, list):
                fields = item
        return OutPort(meta=meta, fields=fields)

    def process_rule(self, items):
        meta = []
        rule = ProcessRule()
        for item in items:
            if isinstance(item, list) and item and isinstance(item[0], dict) and "key" in item[0]:
                meta = item
            elif isinstance(item, ProcessRule):
                rule = item
                break
        rule.meta = meta
        return rule

    def process_stmt(self, items):
        # Unwrap the single child (pre_stmt, post_stmt, assignment, for_all_stmt,
        # condition_stmt, description_stmt, or bare expr).
        return items[0]

    def process_body(self, items):
        rule = ProcessRule()
        for item in items:
            if isinstance(item, dict):
                s = item.get("_stmt")
                if s == "pre":
                    rule.pre.append(item["expr"])
                elif s == "post":
                    rule.post.append(item["expr"])
                elif s == "description":
                    rule.description = item["value"]
                else:
                    # assignment, for_all, condition, or bare expression
                    rule.body.append(item)
        return rule

    def pre_stmt(self, items):
        return {"_stmt": "pre", "expr": items[0]}

    def post_stmt(self, items):
        return {"_stmt": "post", "expr": items[0]}

    def requires_stmt(self, items):
        # `requires:` is a semantic alias for `pre:` — both are preconditions.
        return {"_stmt": "pre", "expr": items[0]}

    def data_field(self, items):
        name = items[0]
        ty = items[1]
        constraint = None
        default = None
        for item in items[2:]:
            if isinstance(item, dict) and "constraint" in item:
                constraint = item
            else:
                default = item
        return DataField(name=name, type=ty, constraint=constraint, default=default)

    # --- Statements ---

    def strategy_stmt(self, items):
        return {"_stmt": "strategy", "value": items[0]}

    def memory_stmt(self, items):
        return {"_stmt": "memory", "entries": list(items)}

    def memory_entry(self, items):
        return {"name": items[0], "args": list(items[1:])}

    def contains_stmt(self, items):
        return {"_stmt": "contains", "value": items[0]}

    def description_stmt(self, items):
        return {"_stmt": "description", "value": items[0]}

    def invariant_stmt(self, items):
        return {"_stmt": "invariant", "expr": items[0]}

    def temporal_stmt(self, items):
        return {"_stmt": "temporal", "expr": items[0]}

    def assignment(self, items):
        return {"_stmt": "assignment", "target": items[0], "value": items[1]}

    def for_all_stmt(self, items):
        return {"_stmt": "for_all", "type": items[0], "var": items[1],
                "condition": items[2] if len(items) > 3 else None,
                "body": items[-1]}

    def condition_stmt(self, items):
        return {"_stmt": "condition", "expr": items[0], "body": items[1]}

    # --- Entity definitions ---

    def _collect_entity_members(self, items):
        """Common collector for entity body members"""
        result = {
            "data_fields": [], "in_ports": [], "out_ports": [],
            "processes": [], "invariants": [], "temporals": [],
            "description": None, "classes": [],
        }
        for item in items:
            if isinstance(item, InPort):
                result["in_ports"].append(item)
            elif isinstance(item, OutPort):
                result["out_ports"].append(item)
            elif isinstance(item, ProcessRule):
                result["processes"].append(item)
            elif isinstance(item, DataField):
                result["data_fields"].append(item)
            elif isinstance(item, EntityDef):
                result["classes"].append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "invariant":
                    result["invariants"].append(item["expr"])
                elif s == "temporal":
                    result["temporals"].append(item["expr"])
                elif s == "description":
                    result["description"] = item["value"]
        return result

    def entity_body(self, items):
        return items

    def entity_member(self, items):
        return items[0]

    def abstraction_def(self, items):
        name = items[0]
        inherits = []
        members = []
        for item in items[1:]:
            if isinstance(item, list) and item and isinstance(item[0], str):
                inherits = item
            elif isinstance(item, list):
                members = item
        m = self._collect_entity_members(members)
        m.pop("classes", None)
        return EntityDef(kind="abstraction", name=name, inherits=inherits, **m)

    def class_def(self, items):
        name = items[0]
        inherits = []
        members = []
        for item in items[1:]:
            if isinstance(item, list) and item and isinstance(item[0], str):
                inherits = item
            elif isinstance(item, list):
                members = item
        m = self._collect_entity_members(members)
        m.pop("classes", None)
        return EntityDef(kind="class", name=name, inherits=inherits, **m)

    def instance_def(self, items):
        name = items[0]
        class_name = items[1]
        assignments = []
        for item in items[2:]:
            if isinstance(item, dict) and item.get("_stmt") == "assignment":
                assignments.append({"target": item["target"], "value": item["value"]})
        return InstanceDef(name=name, class_name=class_name, assignments=assignments)

    def inherits(self, items):
        return items[0]

    # --- Island ---

    def island_def(self, items):
        name = items[0]
        members = items[1] if len(items) > 1 else []
        island = IslandDef(name=name)
        m = self._collect_entity_members(members)
        island.in_ports = m["in_ports"]
        island.out_ports = m["out_ports"]
        island.processes = m["processes"]
        island.data_fields = m["data_fields"]
        island.classes = m["classes"]
        island.invariants = m["invariants"]
        island.temporals = m["temporals"]
        island.description = m["description"]
        for item in members:
            if isinstance(item, dict):
                s = item.get("_stmt")
                if s == "strategy":
                    island.strategy = item["value"]
                elif s == "contains":
                    island.contains = item["value"]
                elif s == "memory":
                    island.memory = item["entries"]
        return island

    def island_body(self, items):
        return items

    def island_member(self, items):
        return items[0]

    # --- Bridge ---

    def bridge_def(self, items):
        name = items[0]
        bridge = BridgeDef(name=name)
        # items[1] is a list produced by bridge_body; flatten it.
        body = items[1] if len(items) > 1 else []
        for item in body:
            if isinstance(item, dict):
                s = item.get("_stmt")
                if s == "from":
                    bridge.from_port = item["value"]
                elif s == "to":
                    bridge.to_port = item["value"]
                elif s == "contract":
                    bridge.contract = item
        return bridge

    def bridge_body(self, items):
        return list(items)

    def from_stmt(self, items):
        path = items[0]
        if isinstance(path, dict) and path.get("expr") == "path":
            return {"_stmt": "from", "value": ".".join(path["parts"])}
        return {"_stmt": "from", "value": str(path)}

    def to_stmt(self, items):
        path = items[0]
        if isinstance(path, dict) and path.get("expr") == "path":
            return {"_stmt": "to", "value": ".".join(path["parts"])}
        return {"_stmt": "to", "value": str(path)}

    def contract_block(self, items):
        inv = []
        temp = []
        for item in items:
            if isinstance(item, dict):
                if item.get("_stmt") == "invariant":
                    inv.append(item["expr"])
                elif item.get("_stmt") == "temporal":
                    temp.append(item["expr"])
        return {"_stmt": "contract", "invariants": inv, "temporals": temp}

    def contract_member(self, items):
        return items[0]

    # --- Registry ---

    def registry_def(self, items):
        name = items[0]
        entries = [i for i in items[1:] if isinstance(i, dict)]
        return RegistryDef(name=name, entries=entries)

    def register_stmt(self, items):
        name = items[0]
        meta = items[1] if len(items) > 1 else []
        return {"name": name, "meta": meta}

    # --- Verify ---

    def verify_def(self, items):
        target = items[0]
        checks = [i for i in items[1:] if isinstance(i, dict)]
        return VerifyDef(target=target, checks=checks)

    def check_stmt(self, items):
        return {"name": items[0], "expr": items[1]}

    # --- Stdlib type declarations ---

    def primitive_def(self, items):
        return PrimitiveDef(name=str(items[0]))

    def struct_field(self, items):
        return {"name": str(items[0]), "type": items[1]}

    def struct_field_list(self, items):
        return list(items)

    def struct_def(self, items):
        name = str(items[0])
        fields_list = []
        for item in items[1:]:
            if isinstance(item, list):
                fields_list = item
                break
        return StructDef(name=name, fields=fields_list)

    def enum_param_typed(self, items):
        return {"name": str(items[0]), "type": items[1]}

    def enum_param_bare(self, items):
        return {"name": str(items[0]), "type": None}

    def enum_variant_params(self, items):
        return list(items)

    def enum_variant(self, items):
        name = str(items[0])
        params = items[1] if len(items) > 1 else []
        return {"name": name, "params": params}

    def enum_variant_list(self, items):
        return list(items)

    def enum_def(self, items):
        name = str(items[0])
        variants = []
        for item in items[1:]:
            if isinstance(item, list):
                variants = item
                break
        return EnumDef(name=name, variants=variants)

    def map_type(self, items):
        return {"type": "map", "key": items[0], "value": items[1]}

    def inline_enum_type(self, items):
        return {"type": "inline_enum", "values": items[0]}

    # --- Expression / Predicate definitions ---

    def def_ident(self, items):
        """Kebab-case name rule: IDENT ('-' IDENT)* → joined string."""
        return "-".join(str(i) for i in items)

    def expression_body(self, items):
        # items: [typed_field_list, type_expr, chain_expr]
        return {"inputs": items[0], "output": items[1], "chain": items[2]}

    def expression_def(self, items):
        name = str(items[0])
        body = items[1]
        return ExpressionDef(
            name=name,
            inputs=body["inputs"],
            output=body["output"],
            chain=body["chain"],
        )

    def predicate_body(self, items):
        # items: [typed_field_list, check_expr]
        return {"inputs": items[0], "check": items[1]}

    def predicate_def(self, items):
        name = str(items[0])
        body = items[1]
        return PredicateDef(
            name=name,
            inputs=body["inputs"],
            check=body["check"],
        )

    # --- Studio hierarchy ---

    def role_body(self, items):
        return list(items)

    def role_member(self, items):
        return items[0]

    def tier_stmt(self, items):
        return {"_stmt": "tier", "value": items[0]}

    def responsibility_stmt(self, items):
        return {"_stmt": "responsibility", "value": items[0]}

    def escalates_to_stmt(self, items):
        return {"_stmt": "escalates_to", "value": str(items[0])}

    def skills_stmt(self, items):
        return {"_stmt": "skills", "value": items[0]}

    def tools_stmt(self, items):
        return {"_stmt": "tools", "value": items[0]}

    def role_def(self, items):
        name = items[0]
        inherits = []
        members = []
        for item in items[1:]:
            if isinstance(item, list) and item and isinstance(item[0], str):
                inherits = item
            elif isinstance(item, list):
                members = item
        role = RoleDef(name=name, inherits=inherits)
        for item in members:
            if isinstance(item, InPort):
                role.in_ports.append(item)
            elif isinstance(item, OutPort):
                role.out_ports.append(item)
            elif isinstance(item, ProcessRule):
                role.processes.append(item)
            elif isinstance(item, DataField):
                role.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "tier":
                    val = item["value"]
                    # tier value may be a number or ident_expr
                    if isinstance(val, (int, float)):
                        role.tier = int(val)
                    elif isinstance(val, dict) and val.get("expr") == "ident":
                        role.tier = val["name"]
                    else:
                        role.tier = val
                elif s == "responsibility":
                    role.responsibilities.append(item["value"])
                elif s == "escalates_to":
                    role.escalates_to = item["value"]
                elif s == "skills":
                    role.skills = item["value"]
                elif s == "tools":
                    role.tools = item["value"]
                elif s == "description":
                    role.description = item["value"]
        return role

    def studio_body(self, items):
        return list(items)

    def studio_member(self, items):
        return items[0]

    def tier_group(self, items):
        level_val = items[0]
        members = items[1] if len(items) > 1 else []
        if isinstance(level_val, (int, float)):
            level = int(level_val)
        elif isinstance(level_val, dict) and level_val.get("expr") == "number":
            level = int(level_val["value"])
        elif isinstance(level_val, dict) and level_val.get("expr") == "ident":
            level = level_val["name"]
        else:
            level = level_val
        return TierGroup(level=level, members=members)

    def studio_def(self, items):
        name = items[0]
        members = items[1] if len(items) > 1 else []
        studio = StudioDef(name=name)
        for item in members:
            if isinstance(item, TierGroup):
                studio.tiers.append(item)
            elif isinstance(item, ProcessRule):
                studio.processes.append(item)
            elif isinstance(item, DataField):
                studio.data_fields.append(item)
            elif isinstance(item, BridgeDef):
                studio.bridges.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "contains":
                    studio.contains = item["value"]
                elif s == "invariant":
                    studio.invariants.append(item["expr"])
                elif s == "description":
                    studio.description = item["value"]
        return studio

    def command_body(self, items):
        return list(items)

    def command_member(self, items):
        return items[0]

    def phase_stmt(self, items):
        return {"_stmt": "phase", "value": str(items[0])}

    def prompt_stmt(self, items):
        return {"_stmt": "prompt", "value": items[0]}

    def role_ref_stmt(self, items):
        return {"_stmt": "role_ref", "value": str(items[0])}

    def output_stmt(self, items):
        return {"_stmt": "output", "value": str(items[0])}

    def command_def(self, items):
        name = items[0]
        members = items[1] if len(items) > 1 else []
        cmd = CommandDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                cmd.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "phase":
                    cmd.phase = item["value"]
                elif s == "prompt":
                    cmd.prompt = item["value"]
                elif s == "role_ref":
                    cmd.role = item["value"]
                elif s == "output":
                    cmd.output = item["value"]
                elif s == "description":
                    cmd.description = item["value"]
        return cmd

    def hook_body(self, items):
        return list(items)

    def hook_member(self, items):
        return items[0]

    def event_stmt(self, items):
        return {"_stmt": "event", "value": str(items[0])}

    def pattern_stmt(self, items):
        return {"_stmt": "pattern", "value": items[0]}

    def action_stmt(self, items):
        return {"_stmt": "action", "value": items[0]}

    def hook_def(self, items):
        name = items[0]
        members = items[1] if len(items) > 1 else []
        hook = HookDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                hook.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "event":
                    hook.event = item["value"]
                elif s == "pattern":
                    hook.pattern = item["value"]
                elif s == "action":
                    hook.action = item["value"]
                elif s == "description":
                    hook.description = item["value"]
        return hook

    def rule_body(self, items):
        return list(items)

    def rule_member(self, items):
        return items[0]

    def path_stmt(self, items):
        return {"_stmt": "path", "value": items[0]}

    def constraint_stmt_rule(self, items):
        return {"_stmt": "constraint_rule", "value": items[0]}

    def severity_stmt(self, items):
        return {"_stmt": "severity", "value": str(items[0])}

    def rule_def(self, items):
        name = items[0]
        members = items[1] if len(items) > 1 else []
        rule = RuleDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                rule.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "path":
                    rule.path = item["value"]
                elif s == "constraint_rule":
                    rule.constraint = item["value"]
                elif s == "severity":
                    rule.severity = item["value"]
                elif s == "description":
                    rule.description = item["value"]
        return rule

    def template_body(self, items):
        return list(items)

    def template_member(self, items):
        return items[0]

    def sections_stmt(self, items):
        return {"_stmt": "sections", "value": items[0]}

    def bound_to_stmt(self, items):
        return {"_stmt": "bound_to", "value": str(items[0])}

    def string_list(self, items):
        return list(items)

    def template_def(self, items):
        name = items[0]
        members = items[1] if len(items) > 1 else []
        tmpl = TemplateDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                tmpl.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "sections":
                    tmpl.sections = item["value"]
                elif s == "bound_to":
                    tmpl.bound_to = item["value"]
                elif s == "description":
                    tmpl.description = item["value"]
        return tmpl

    # --- Evolution system ---

    # Shared helper statements used across evolution grammar rules
    # NOTE: tier_stmt is already defined above for role_def and is reused here.

    def file_ref_stmt(self, items):
        return {"_stmt": "file_ref", "value": items[0]}

    def source_stmt(self, items):
        return {"_stmt": "source", "value": items[0]}

    def split_entry(self, items):
        return (str(items[0]), items[1])

    def split_stmt(self, items):
        # items is a flat list of (name, value) tuples
        splits = {}
        for entry in items:
            if isinstance(entry, tuple):
                splits[entry[0]] = entry[1]
        return {"_stmt": "split", "value": splits}

    def scoring_rubric_stmt(self, items):
        return {"_stmt": "scoring_rubric", "value": items[0]}

    def aggregation_stmt(self, items):
        return {"_stmt": "aggregation", "value": str(items[0])}

    def weight_stmt(self, items):
        return {"_stmt": "weight", "value": items[0]}

    def metric_stmt(self, items):
        return {"_stmt": "metric", "value": items[0]}

    def dimension_body(self, items):
        return list(items)

    def dimension_body_empty(self, items):
        return list(items)

    def dimension_member(self, items):
        return items[0]

    def dimension_stmt(self, items):
        dim_name = str(items[0])
        members = items[1] if len(items) > 1 else []
        dim = {"name": dim_name, "weight": None, "metric": None}
        for item in members:
            if isinstance(item, dict):
                s = item.get("_stmt")
                if s == "weight":
                    dim["weight"] = item["value"]
                elif s == "metric":
                    dim["metric"] = item["value"]
        return {"_stmt": "dimension", "value": dim}

    def engine_stmt(self, items):
        return {"_stmt": "engine", "value": str(items[0])}

    def iterations_stmt(self, items):
        return {"_stmt": "iterations", "value": items[0]}

    def population_stmt(self, items):
        return {"_stmt": "population_size", "value": items[0]}

    def mutation_stmt(self, items):
        return {"_stmt": "mutation_strategy", "value": str(items[0])}

    def benchmark_stmt(self, items):
        return {"_stmt": "benchmark", "value": items[0]}

    def tolerance_stmt(self, items):
        return {"_stmt": "tolerance", "value": items[0]}

    def pass_criteria_stmt(self, items):
        return {"_stmt": "pass_criteria", "value": items[0]}

    def target_ref_stmt(self, items):
        return {"_stmt": "target_ref", "value": str(items[0])}

    def optimizer_ref_stmt(self, items):
        return {"_stmt": "optimizer_ref", "value": str(items[0])}

    def dataset_ref_stmt(self, items):
        return {"_stmt": "dataset_ref", "value": str(items[0])}

    def gate_ref_stmt(self, items):
        return {"_stmt": "gate_ref", "value": str(items[0])}

    def status_stmt(self, items):
        return {"_stmt": "status", "value": str(items[0])}

    def type_stmt(self, items):
        return {"_stmt": "type", "value": str(items[0])}

    def threshold_stmt(self, items):
        return {"_stmt": "threshold", "value": items[0]}

    def enforcement_stmt(self, items):
        return {"_stmt": "enforcement", "value": str(items[0])}

    def name_stmt(self, items):
        return {"_stmt": "name", "value": items[0]}

    def constraint_item_member(self, items):
        return items[0]

    def constraint_item(self, items):
        """Collect inline constraint members into a dict."""
        c = {"name": None, "type": None, "threshold": None, "enforcement": None}
        for item in items:
            if isinstance(item, dict):
                s = item.get("_stmt")
                if s == "name":
                    c["name"] = item["value"]
                elif s == "type":
                    c["type"] = item["value"]
                elif s == "threshold":
                    c["threshold"] = item["value"]
                elif s == "enforcement":
                    c["enforcement"] = item["value"]
        return c

    def constraints_block(self, items):
        return {"_stmt": "constraints_block", "value": list(items)}

    # evolution_target_def

    def evolution_target_body(self, items):
        return list(items)

    def evolution_target_member(self, items):
        return items[0]

    def evolution_target_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        et = EvolutionTargetDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                et.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "tier":
                    val = item["value"]
                    if isinstance(val, (int, float)):
                        et.tier = str(int(val))
                    elif isinstance(val, dict) and val.get("expr") == "ident":
                        et.tier = val["name"]
                    else:
                        et.tier = str(val)
                elif s == "file_ref":
                    et.file_ref = item["value"]
                elif s == "constraints_block":
                    et.constraints = item["value"]
                elif s == "description":
                    et.description = item["value"]
        return et

    # eval_dataset_def

    def eval_dataset_body(self, items):
        return list(items)

    def eval_dataset_member(self, items):
        return items[0]

    def eval_dataset_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        ed = EvalDatasetDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                ed.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "source":
                    ed.source = item["value"]
                elif s == "split":
                    ed.splits = item["value"]
                elif s == "scoring_rubric":
                    ed.scoring_rubric = item["value"]
                elif s == "description":
                    ed.description = item["value"]
        return ed

    # fitness_function_def

    def fitness_function_body(self, items):
        return list(items)

    def fitness_function_member(self, items):
        return items[0]

    def fitness_function_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        ff = FitnessFunctionDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                ff.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "dimension":
                    ff.dimensions.append(item["value"])
                elif s == "aggregation":
                    ff.aggregation = item["value"]
                elif s == "description":
                    ff.description = item["value"]
        return ff

    # optimizer_def

    def optimizer_body(self, items):
        return list(items)

    def optimizer_member(self, items):
        return items[0]

    def optimizer_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        opt = OptimizerDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                opt.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "engine":
                    opt.engine = item["value"]
                elif s == "iterations":
                    val = item["value"]
                    opt.iterations = int(val) if isinstance(val, (int, float)) else val
                elif s == "population_size":
                    val = item["value"]
                    opt.population_size = int(val) if isinstance(val, (int, float)) else val
                elif s == "mutation_strategy":
                    opt.mutation_strategy = item["value"]
                elif s == "description":
                    opt.description = item["value"]
        return opt

    # benchmark_gate_def

    def benchmark_gate_body(self, items):
        return list(items)

    def benchmark_gate_member(self, items):
        return items[0]

    def benchmark_gate_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        bg = BenchmarkGateDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                bg.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "benchmark":
                    bg.benchmark = item["value"]
                elif s == "tolerance":
                    val = item["value"]
                    bg.tolerance = float(val) if isinstance(val, (int, float)) else val
                elif s == "pass_criteria":
                    bg.pass_criteria = item["value"]
                elif s == "description":
                    bg.description = item["value"]
        return bg

    # evolution_run_def

    def evolution_run_body(self, items):
        return list(items)

    def evolution_run_member(self, items):
        return items[0]

    def evolution_run_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        er = EvolutionRunDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                er.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "target_ref":
                    er.target_ref = item["value"]
                elif s == "optimizer_ref":
                    er.optimizer_ref = item["value"]
                elif s == "dataset_ref":
                    er.dataset_ref = item["value"]
                elif s == "gate_ref":
                    er.gate_ref = item["value"]
                elif s == "status":
                    er.status = item["value"]
                elif s == "description":
                    er.description = item["value"]
        return er

    # constraint_def (reusable named constraint — EvolutionConstraintDef)

    def constraint_def_body(self, items):
        return list(items)

    def constraint_def_member(self, items):
        return items[0]

    def constraint_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        cd = EvolutionConstraintDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                cd.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "type":
                    cd.type = item["value"]
                elif s == "threshold":
                    cd.threshold = item["value"]
                elif s == "enforcement":
                    cd.enforcement = item["value"]
                elif s == "description":
                    cd.description = item["value"]
        return cd

    # --- Agent system ---

    # agent_def
    def agent_body(self, items):
        return list(items)

    def agent_member(self, items):
        return items[0]

    def persona_stmt(self, items):
        return {"_stmt": "persona", "value": items[0]}

    def model_ref_stmt(self, items):
        return {"_stmt": "model_ref", "value": str(items[0])}

    def capabilities_stmt(self, items):
        return {"_stmt": "capabilities", "value": items[0]}

    def learning_ref_stmt(self, items):
        return {"_stmt": "learning_ref", "value": str(items[0])}

    def backends_stmt(self, items):
        return {"_stmt": "backends", "value": items[0]}

    def agent_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        ag = AgentDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                ag.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "persona":
                    ag.persona = item["value"]
                elif s == "model_ref":
                    ag.model_ref = item["value"]
                elif s == "capabilities":
                    ag.capabilities = item["value"]
                elif s == "learning_ref":
                    ag.learning_ref = item["value"]
                elif s == "backends":
                    ag.backends = item["value"]
                elif s == "description":
                    ag.description = item["value"]
        return ag

    # platform_def
    def platform_body(self, items):
        return list(items)

    def platform_member(self, items):
        return items[0]

    def auth_stmt(self, items):
        return {"_stmt": "auth", "value": items[0]}

    def format_stmt(self, items):
        return {"_stmt": "format", "value": str(items[0])}

    def endpoint_stmt(self, items):
        return {"_stmt": "endpoint", "value": items[0]}

    def platform_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        pl = PlatformDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                pl.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "type":
                    pl.type = item["value"]
                elif s == "auth":
                    pl.auth = item["value"]
                elif s == "format":
                    pl.format = item["value"]
                elif s == "endpoint":
                    pl.endpoint = item["value"]
                elif s == "description":
                    pl.description = item["value"]
        return pl

    # gateway_def
    def gateway_body(self, items):
        return list(items)

    def gateway_member(self, items):
        return items[0]

    def agent_ref_stmt(self, items):
        return {"_stmt": "agent_ref", "value": str(items[0])}

    def platforms_stmt(self, items):
        return {"_stmt": "platforms", "value": items[0]}

    def route_entry(self, items):
        return {"from": str(items[0]), "to": str(items[1])}

    def routes_stmt(self, items):
        return {"_stmt": "routes", "value": list(items)}

    def gateway_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        gw = GatewayDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                gw.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "agent_ref":
                    gw.agent_ref = item["value"]
                elif s == "platforms":
                    gw.platforms = item["value"]
                elif s == "routes":
                    gw.routes = item["value"]
                elif s == "description":
                    gw.description = item["value"]
        return gw

    # execution_backend_def
    def exec_backend_body(self, items):
        return list(items)

    def exec_backend_member(self, items):
        return items[0]

    def backend_type_stmt(self, items):
        return {"_stmt": "backend_type", "value": str(items[0])}

    def connection_stmt(self, items):
        return {"_stmt": "connection", "value": items[0]}

    def limit_entry(self, items):
        return (str(items[0]), items[1])

    def limits_stmt(self, items):
        limits = {}
        for entry in items:
            if isinstance(entry, tuple):
                limits[entry[0]] = entry[1]
        return {"_stmt": "limits", "value": limits}

    def execution_backend_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        eb = ExecutionBackendDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                eb.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "backend_type":
                    eb.backend_type = item["value"]
                elif s == "connection":
                    eb.connection = item["value"]
                elif s == "limits":
                    eb.limits = item["value"]
                elif s == "description":
                    eb.description = item["value"]
        return eb

    # skill_def
    def skill_body(self, items):
        return list(items)

    def skill_member(self, items):
        return items[0]

    def trigger_stmt(self, items):
        return {"_stmt": "trigger", "value": items[0]}

    def steps_stmt(self, items):
        return {"_stmt": "steps", "value": items[0]}

    def improvement_stmt(self, items):
        pairs = items[0] if items else []
        return {"_stmt": "improvement", "value": pairs}

    def skill_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        sk = AgentSkillDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                sk.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "trigger":
                    sk.trigger = item["value"]
                elif s == "steps":
                    sk.steps = item["value"]
                elif s == "status":
                    sk.status = item["value"]
                elif s == "improvement":
                    sk.improvement_history = item["value"]
                elif s == "description":
                    sk.description = item["value"]
        return sk

    # learning_config_def
    def learning_body(self, items):
        return list(items)

    def learning_member(self, items):
        return items[0]

    def mode_stmt(self, items):
        return {"_stmt": "mode", "value": str(items[0])}

    def skill_gen_stmt(self, items):
        return {"_stmt": "skill_gen", "value": items[0]}

    def memory_persist_stmt(self, items):
        return {"_stmt": "memory_persist", "value": items[0]}

    def session_search_stmt(self, items):
        return {"_stmt": "session_search", "value": items[0]}

    def self_improve_stmt(self, items):
        return {"_stmt": "self_improve", "value": items[0]}

    def learning_config_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        lc = LearningConfigDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                lc.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "mode":
                    lc.mode = item["value"]
                elif s == "skill_gen":
                    lc.skill_gen = item["value"]
                elif s == "memory_persist":
                    lc.memory_persist = item["value"]
                elif s == "session_search":
                    lc.session_search = item["value"]
                elif s == "self_improve":
                    lc.self_improve = item["value"]
                elif s == "description":
                    lc.description = item["value"]
        return lc

    # cron_task_def
    def cron_body(self, items):
        return list(items)

    def cron_member(self, items):
        return items[0]

    def schedule_stmt(self, items):
        return {"_stmt": "schedule", "value": items[0]}

    def platform_delivery_stmt(self, items):
        return {"_stmt": "platform_delivery", "value": str(items[0])}

    def cron_task_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        ct = CronTaskDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                ct.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "schedule":
                    ct.schedule = item["value"]
                elif s == "agent_ref":
                    ct.agent_ref = item["value"]
                elif s == "platform_delivery":
                    ct.platform_delivery = item["value"]
                elif s == "action":
                    ct.action = item["value"]
                elif s == "description":
                    ct.description = item["value"]
        return ct

    # model_config_def
    def model_config_body(self, items):
        return list(items)

    def model_config_member(self, items):
        return items[0]

    def provider_stmt(self, items):
        return {"_stmt": "provider", "value": str(items[0])}

    def model_id_stmt(self, items):
        return {"_stmt": "model_id", "value": items[0]}

    def fallback_stmt(self, items):
        return {"_stmt": "fallback", "value": str(items[0])}

    def params_stmt(self, items):
        pairs = items[0] if items else []
        params = {}
        if isinstance(pairs, list):
            for p in pairs:
                if isinstance(p, dict) and "key" in p:
                    params[p["key"]] = p["value"]
        return {"_stmt": "params", "value": params}

    def cost_limit_stmt(self, items):
        return {"_stmt": "cost_limit", "value": items[0]}

    def model_config_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        mc = ModelConfigDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                mc.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "provider":
                    mc.provider = item["value"]
                elif s == "model_id":
                    mc.model_id = item["value"]
                elif s == "fallback":
                    mc.fallback = item["value"]
                elif s == "params":
                    mc.params = item["value"]
                elif s == "cost_limit":
                    mc.cost_limit = item["value"]
                elif s == "description":
                    mc.description = item["value"]
        return mc

    # --- Visual communication layer ---

    # diagram_def
    def diagram_body(self, items):
        return list(items)

    def diagram_member(self, items):
        return items[0]

    def diagram_type_stmt(self, items):
        return {"_stmt": "diagram_type", "value": str(items[0])}

    def render_config_stmt(self, items):
        return {"_stmt": "render_config_ref", "value": str(items[0])}

    def diagram_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        d = DiagramDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                d.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "diagram_type":
                    d.diagram_type = item["value"]
                elif s == "source":
                    d.source = item["value"]
                elif s == "render_config_ref":
                    d.render_config = item["value"]
                elif s == "description":
                    d.description = item["value"]
        return d

    # preview_def
    def preview_body(self, items):
        return list(items)

    def preview_member(self, items):
        return items[0]

    def viewport_stmt(self, items):
        return {"_stmt": "viewport", "value": str(items[0])}

    def preview_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        p = PreviewDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                p.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "source":
                    p.source = item["value"]
                elif s == "viewport":
                    p.viewport = item["value"]
                elif s == "mode":
                    p.mode = item["value"]
                elif s == "render_config_ref":
                    p.render_config = item["value"]
                elif s == "description":
                    p.description = item["value"]
        return p

    # annotation_def
    def annotation_body(self, items):
        return list(items)

    def annotation_member(self, items):
        return items[0]

    def element_stmt(self, items):
        name = str(items[0])
        meta = items[1] if len(items) > 1 else []
        return {"_stmt": "element", "name": name, "meta": meta}

    def annotation_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        a = AnnotationDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                a.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "target_ref":
                    a.target = item["value"]
                elif s == "element":
                    a.elements.append({"name": item["name"], "meta": item["meta"]})
                elif s == "description":
                    a.description = item["value"]
        return a

    # visual_review_def
    def visual_review_body(self, items):
        return list(items)

    def visual_review_member(self, items):
        return items[0]

    def feedback_mode_stmt(self, items):
        return {"_stmt": "feedback_mode", "value": str(items[0])}

    def visual_review_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        vr = VisualReviewDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                vr.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "target_ref":
                    vr.target = item["value"]
                elif s == "render_config_ref":
                    vr.render_config = item["value"]
                elif s == "feedback_mode":
                    vr.feedback_mode = item["value"]
                elif s == "description":
                    vr.description = item["value"]
        return vr

    # screenshot_def
    def screenshot_body(self, items):
        return list(items)

    def screenshot_member(self, items):
        return items[0]

    def tags_stmt(self, items):
        return {"_stmt": "tags", "value": items[0] if items else []}

    def screenshot_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        sc = ScreenshotDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                sc.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "path":
                    sc.path = item["value"]
                elif s == "source":
                    sc.source = item["value"]
                elif s == "tags":
                    sc.tags = item["value"]
                elif s == "description":
                    sc.description = item["value"]
        return sc

    # visual_search_def
    def visual_search_body(self, items):
        return list(items)

    def visual_search_member(self, items):
        return items[0]

    def search_mode_stmt(self, items):
        return {"_stmt": "search_mode", "value": str(items[0])}

    def query_stmt(self, items):
        return {"_stmt": "query", "value": items[0]}

    def max_results_stmt(self, items):
        return {"_stmt": "max_results", "value": items[0]}

    def visual_search_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        vs = VisualSearchDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                vs.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "search_mode":
                    vs.search_mode = item["value"]
                elif s == "query":
                    vs.query = item["value"]
                elif s == "tags":
                    vs.tags = item["value"]
                elif s == "max_results":
                    val = item["value"]
                    vs.max_results = int(val) if isinstance(val, (int, float)) else val
                elif s == "description":
                    vs.description = item["value"]
        return vs

    # render_config_def
    def render_config_body(self, items):
        return list(items)

    def render_config_member(self, items):
        return items[0]

    def width_stmt(self, items):
        return {"_stmt": "width", "value": items[0]}

    def height_stmt(self, items):
        return {"_stmt": "height", "value": items[0]}

    def theme_stmt(self, items):
        return {"_stmt": "theme", "value": items[0]}

    def scale_stmt(self, items):
        return {"_stmt": "scale", "value": items[0]}

    def render_config_def(self, items):
        name = str(items[0])
        members = items[1] if len(items) > 1 else []
        rc = RenderConfigDef(name=name)
        for item in members:
            if isinstance(item, DataField):
                rc.data_fields.append(item)
            elif isinstance(item, dict):
                s = item.get("_stmt")
                if s == "format":
                    rc.format = item["value"]
                elif s == "width":
                    val = item["value"]
                    rc.width = int(val) if isinstance(val, (int, float)) else val
                elif s == "height":
                    val = item["value"]
                    rc.height = int(val) if isinstance(val, (int, float)) else val
                elif s == "theme":
                    rc.theme = item["value"]
                elif s == "scale":
                    val = item["value"]
                    rc.scale = float(val) if isinstance(val, (int, float)) else val
                elif s == "description":
                    rc.description = item["value"]
        return rc

    # --- Import ---

    def item(self, items):
        return items[0]

    def import_stmt(self, items):
        path = items[0]
        if isinstance(path, dict) and path.get("expr") == "path":
            return path["parts"]
        return [str(path)]

    # --- Top level ---

    def start(self, items):
        imports = []
        ark_items = []
        for item in items:
            if isinstance(item, list) and item and isinstance(item[0], str):
                imports.append(item)
            elif isinstance(item, (EntityDef, InstanceDef, IslandDef,
                                   BridgeDef, RegistryDef, VerifyDef,
                                   PrimitiveDef, StructDef, EnumDef,
                                   ExpressionDef, PredicateDef,
                                   RoleDef, StudioDef, CommandDef,
                                   HookDef, RuleDef, TemplateDef,
                                   EvolutionTargetDef, EvalDatasetDef,
                                   FitnessFunctionDef, OptimizerDef,
                                   BenchmarkGateDef, EvolutionRunDef,
                                   EvolutionConstraintDef,
                                   AgentDef, PlatformDef, GatewayDef,
                                   ExecutionBackendDef, AgentSkillDef,
                                   LearningConfigDef, CronTaskDef,
                                   ModelConfigDef,
                                   DiagramDef, PreviewDef, AnnotationDef,
                                   VisualReviewDef, ScreenshotDef,
                                   VisualSearchDef, RenderConfigDef)):
                ark_items.append(item)
        return ArkFile(imports=imports, items=ark_items)


# ============================================================
# PARSER API
# ============================================================

_GRAMMAR_PATH = Path(__file__).parent / "ark_grammar.lark"

# ARK project root (parent of tools/) — used by import resolver.
_ARK_ROOT = Path(__file__).resolve().parent.parent.parent

def get_parser() -> Lark:
    """Create or return cached Lark parser"""
    grammar_text = _GRAMMAR_PATH.read_text(encoding="utf-8")
    return Lark(grammar_text, parser="earley", propagate_positions=True)

def _parse_no_resolve(source: str, file_path: Optional[str] = None) -> ArkFile:
    """Parse source text into ArkFile AST without resolving imports.

    Raises ArkParseError (never a raw Lark exception) on syntax errors.
    """
    parser = get_parser()
    try:
        tree = parser.parse(source)
    except UnexpectedInput as exc:
        raise _lark_to_ark_error(exc, source, file_path) from None
    transformer = ArkTransformer()
    return transformer.transform(tree)

def _resolve_import_path(parts, base_dir: Path) -> Optional[Path]:
    """Resolve import dotted-path parts to an absolute .ark file path.

    Import like `stdlib.types` maps to `<ark_root>/dsl/stdlib/types.ark`.
    Returns None if no candidate file exists on disk.
    """
    if not parts:
        return None
    # Primary convention: dsl/<p0>/<p1>/.../<pN>.ark under the ARK project root.
    candidates = [
        _ARK_ROOT / "dsl" / Path(*parts[:-1]) / f"{parts[-1]}.ark",
        base_dir / Path(*parts[:-1]) / f"{parts[-1]}.ark",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand.resolve()
    return None

def import_resolve(ark_file: ArkFile, file_path: Optional[Path],
                   visited: Optional[set] = None) -> ArkFile:
    """Recursively load imported .ark files and merge their items.

    For each import in `ark_file.imports`, resolve it to a file under
    `<ark_root>/dsl/...`, parse it, recurse, and PREPEND its items to the
    current file's items list (stdlib items appear first).

    - `file_path`: absolute path of the file that produced `ark_file`, used
      as a secondary base for resolution and for circular-import tracking.
    - `visited`: set of absolute import paths already loaded in this chain;
      prevents circular / duplicate re-parsing.
    - Missing files emit a stderr warning but do not crash.
    - Import files that fail to parse emit a stderr warning and are skipped.
    """
    if visited is None:
        visited = set()
    if file_path is not None:
        try:
            visited.add(Path(file_path).resolve())
        except OSError:
            pass

    base_dir = Path(file_path).resolve().parent if file_path else _ARK_ROOT

    prepended: list = []
    for imp in ark_file.imports:
        parts = list(imp) if isinstance(imp, (list, tuple)) else [str(imp)]
        resolved = _resolve_import_path(parts, base_dir)
        if resolved is None:
            print(f"[ark_parser] warning: import '{'.'.join(parts)}' "
                  f"could not be resolved (looked under {_ARK_ROOT / 'dsl'})",
                  file=sys.stderr)
            continue
        if resolved in visited:
            continue
        visited.add(resolved)
        try:
            sub_source = resolved.read_text(encoding="utf-8")
            sub_ast = _parse_no_resolve(sub_source, file_path=str(resolved))
        except ArkParseError:
            # Re-raise with the imported file's path already set by
            # _parse_no_resolve — caller will see a clean report.
            raise
        except Exception as e:
            print(f"[ark_parser] warning: failed to parse import "
                  f"'{'.'.join(parts)}' at {resolved}: {e}", file=sys.stderr)
            continue
        sub_ast = import_resolve(sub_ast, resolved, visited)
        prepended.extend(sub_ast.items)

    if prepended:
        ark_file.items = prepended + list(ark_file.items)
    return ark_file

def _build_indices(ark_file: ArkFile) -> ArkFile:
    """Populate ArkFile.classes / instances / island_classes from items.

    Pure-additive: `items` is left untouched. Duplicate class names shadow
    (last-wins) with an insertion-order-preserving dict, matching how the
    rest of the codebase resolves names. Orphan instances (class_name not
    declared) still land in `instances` — consumers can detect them by
    checking `class_name not in ark_file.classes`.
    """
    classes: dict = {}
    instances: dict = {}
    island_classes: dict = {}
    expression_index: dict = {}
    predicate_index: dict = {}
    for idx, item in enumerate(ark_file.items):
        if isinstance(item, EntityDef) and item.kind == "class":
            classes[item.name] = item
        elif isinstance(item, InstanceDef):
            instances.setdefault(item.class_name, []).append(item)
        elif isinstance(item, IslandDef):
            nested: dict = {}
            for nested_item in getattr(item, "classes", []) or []:
                if isinstance(nested_item, EntityDef) and nested_item.kind == "class":
                    nested[nested_item.name] = nested_item
            if nested:
                island_classes[item.name] = nested
        elif isinstance(item, ExpressionDef):
            expression_index[item.name] = idx
        elif isinstance(item, PredicateDef):
            predicate_index[item.name] = idx
    ark_file.classes = classes
    ark_file.instances = instances
    ark_file.island_classes = island_classes
    ark_file.expression_index = expression_index
    ark_file.predicate_index = predicate_index
    roles: dict = {}
    studios: dict = {}
    commands: dict = {}
    for item in ark_file.items:
        if isinstance(item, RoleDef):
            roles[item.name] = item
        elif isinstance(item, StudioDef):
            studios[item.name] = item
        elif isinstance(item, CommandDef):
            commands[item.name] = item
    ark_file.roles = roles
    ark_file.studios = studios
    ark_file.commands = commands
    evolution_targets: dict = {}
    eval_datasets: dict = {}
    fitness_functions: dict = {}
    optimizers: dict = {}
    benchmark_gates: dict = {}
    evolution_runs: dict = {}
    evolution_constraints: dict = {}
    for item in ark_file.items:
        if isinstance(item, EvolutionTargetDef):
            evolution_targets[item.name] = item
        elif isinstance(item, EvalDatasetDef):
            eval_datasets[item.name] = item
        elif isinstance(item, FitnessFunctionDef):
            fitness_functions[item.name] = item
        elif isinstance(item, OptimizerDef):
            optimizers[item.name] = item
        elif isinstance(item, BenchmarkGateDef):
            benchmark_gates[item.name] = item
        elif isinstance(item, EvolutionRunDef):
            evolution_runs[item.name] = item
        elif isinstance(item, EvolutionConstraintDef):
            evolution_constraints[item.name] = item
    ark_file.evolution_targets = evolution_targets
    ark_file.eval_datasets = eval_datasets
    ark_file.fitness_functions = fitness_functions
    ark_file.optimizers = optimizers
    ark_file.benchmark_gates = benchmark_gates
    ark_file.evolution_runs = evolution_runs
    ark_file.evolution_constraints = evolution_constraints
    agents: dict = {}
    platforms: dict = {}
    gateways: dict = {}
    execution_backends: dict = {}
    agent_skills: dict = {}
    learning_configs: dict = {}
    cron_tasks: dict = {}
    model_configs: dict = {}
    for item in ark_file.items:
        if isinstance(item, AgentDef):
            agents[item.name] = item
        elif isinstance(item, PlatformDef):
            platforms[item.name] = item
        elif isinstance(item, GatewayDef):
            gateways[item.name] = item
        elif isinstance(item, ExecutionBackendDef):
            execution_backends[item.name] = item
        elif isinstance(item, AgentSkillDef):
            agent_skills[item.name] = item
        elif isinstance(item, LearningConfigDef):
            learning_configs[item.name] = item
        elif isinstance(item, CronTaskDef):
            cron_tasks[item.name] = item
        elif isinstance(item, ModelConfigDef):
            model_configs[item.name] = item
    ark_file.agents = agents
    ark_file.platforms = platforms
    ark_file.gateways = gateways
    ark_file.execution_backends = execution_backends
    ark_file.agent_skills = agent_skills
    ark_file.learning_configs = learning_configs
    ark_file.cron_tasks = cron_tasks
    ark_file.model_configs = model_configs
    diagrams: dict = {}
    previews: dict = {}
    annotations: dict = {}
    visual_reviews: dict = {}
    screenshots: dict = {}
    visual_searches: dict = {}
    render_configs: dict = {}
    for item in ark_file.items:
        if isinstance(item, DiagramDef):
            diagrams[item.name] = item
        elif isinstance(item, PreviewDef):
            previews[item.name] = item
        elif isinstance(item, AnnotationDef):
            annotations[item.name] = item
        elif isinstance(item, VisualReviewDef):
            visual_reviews[item.name] = item
        elif isinstance(item, ScreenshotDef):
            screenshots[item.name] = item
        elif isinstance(item, VisualSearchDef):
            visual_searches[item.name] = item
        elif isinstance(item, RenderConfigDef):
            render_configs[item.name] = item
    ark_file.diagrams = diagrams
    ark_file.previews = previews
    ark_file.annotations = annotations
    ark_file.visual_reviews = visual_reviews
    ark_file.screenshots = screenshots
    ark_file.visual_searches = visual_searches
    ark_file.render_configs = render_configs
    return ark_file


def parse(source: str, file_path=None) -> ArkFile:
    """Parse .ark source → ArkFile AST.

    If `file_path` is provided, import statements like `import stdlib.types`
    are resolved relative to the ARK project root and their items merged in.
    Without a file_path, import resolution is skipped (a debug note is
    written to stderr if any imports were declared).
    """
    ark_file = _parse_no_resolve(source, file_path=str(file_path) if file_path else None)
    if file_path is None:
        if ark_file.imports:
            print("[ark_parser] debug: parse() called without file_path; "
                  "skipping import resolution", file=sys.stderr)
        return _build_indices(ark_file)
    return _build_indices(import_resolve(ark_file, Path(file_path)))

def to_json(ark_file: ArkFile) -> str:
    """Serialize ArkFile → JSON"""
    def convert(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        return obj
    return json.dumps(convert(ark_file), indent=2, ensure_ascii=False)


# ============================================================
# CLI
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python ark_parser.py <file.ark> [--json] [--tree]")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    source = filepath.read_text(encoding="utf-8")

    if "--tree" in sys.argv:
        # Raw parse tree (for debugging grammar)
        parser = get_parser()
        tree = parser.parse(source)
        print(tree.pretty())
    else:
        # Full AST → JSON
        ark_file = parse(source, file_path=filepath)
        print(to_json(ark_file))

if __name__ == "__main__":
    main()
