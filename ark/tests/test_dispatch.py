"""Tests for ark_dispatch — ready Task → Subagent routing.

Covers the MVP: collect tasks and subagents from a parsed spec, filter
to the ready set, sort by priority, and resolve each task's declared
agent name to a concrete Subagent class.
"""

from ark_dispatch import (
    collect_tasks,
    collect_subagents,
    find_ready,
    assign_subagent,
    build_plan,
    render,
)


# Reused across tests — a tiny bespoke backlog (not the real one, so
# failures point here, not at regressions in specs/meta/backlog.ark).
_SPEC = """
abstraction Subagent {
  $data name:     String
  $data role:     String = "executor"
  $data capacity: Int [0..10] = 1
}

class CodeAgent : Subagent {
  $data name:     String = "general-purpose"
  $data role:     String = "executor"
  $data capacity: Int [0..10] = 4
}

class PlanAgent : Subagent {
  $data name:     String = "Plan"
  $data role:     String = "architect"
  $data capacity: Int [0..10] = 2
}

abstraction Task {
  $data id:       String
  $data title:    String
  $data priority: Int [1..5] = 3
  $data status:   String = "todo"
  $data phase:    String = "backlog"
  $data agent:    String = "general-purpose"
}

class DoneTask : Task {
  $data id:       String = "t-done"
  $data title:    String = "Already finished"
  $data priority: Int [1..5] = 1
  $data status:   String = "done"
  $data phase:    String = "codegen"
  $data agent:    String = "general-purpose"
}

class LowPriTask : Task {
  $data id:       String = "t-low"
  $data title:    String = "Lower priority work"
  $data priority: Int [1..5] = 3
  $data status:   String = "todo"
  $data phase:    String = "runtime"
  $data agent:    String = "general-purpose"
}

class HighPriTask : Task {
  $data id:       String = "t-high"
  $data title:    String = "Urgent"
  $data priority: Int [1..5] = 1
  $data status:   String = "todo"
  $data phase:    String = "parser"
  $data agent:    String = "Plan"
}

class OrphanAgentTask : Task {
  $data id:       String = "t-orphan"
  $data title:    String = "No matching subagent"
  $data priority: Int [1..5] = 2
  $data status:   String = "todo"
  $data phase:    String = "tools"
  $data agent:    String = "Ghostbusters"
}
"""


def test_collect_tasks_finds_all_task_subclasses(parse_src):
    ast = parse_src(_SPEC)
    tasks = collect_tasks(ast)
    class_names = {t["class_name"] for t in tasks}
    assert class_names == {"DoneTask", "LowPriTask", "HighPriTask", "OrphanAgentTask"}
    # String defaults must be unquoted.
    high = next(t for t in tasks if t["class_name"] == "HighPriTask")
    assert high["id"] == "t-high"
    assert high["title"] == "Urgent"
    assert high["priority"] == 1
    assert high["agent"] == "Plan"


def test_collect_subagents_finds_all_subagent_subclasses(parse_src):
    ast = parse_src(_SPEC)
    agents = collect_subagents(ast)
    assert {a["class_name"] for a in agents} == {"CodeAgent", "PlanAgent"}
    code = next(a for a in agents if a["class_name"] == "CodeAgent")
    assert code["name"] == "general-purpose"
    assert code["role"] == "executor"
    assert code["capacity"] == 4


def test_find_ready_filters_done_and_sorts_by_priority(parse_src):
    ast = parse_src(_SPEC)
    ready = find_ready(collect_tasks(ast))
    # DoneTask is excluded; remaining sorted by priority asc.
    assert [t["class_name"] for t in ready] == [
        "HighPriTask",        # priority 1
        "OrphanAgentTask",    # priority 2
        "LowPriTask",         # priority 3
    ]


def test_assign_subagent_matches_by_name_then_role(parse_src):
    ast = parse_src(_SPEC)
    tasks = collect_tasks(ast)
    agents = collect_subagents(ast)
    high = next(t for t in tasks if t["class_name"] == "HighPriTask")
    low = next(t for t in tasks if t["class_name"] == "LowPriTask")
    orphan = next(t for t in tasks if t["class_name"] == "OrphanAgentTask")

    # HighPri wants "Plan" → matches PlanAgent.name
    sa_high = assign_subagent(high, agents)
    assert sa_high is not None and sa_high["class_name"] == "PlanAgent"

    # LowPri wants "general-purpose" → matches CodeAgent.name
    sa_low = assign_subagent(low, agents)
    assert sa_low is not None and sa_low["class_name"] == "CodeAgent"

    # Orphan wants "Ghostbusters" — no match by name OR role → None
    assert assign_subagent(orphan, agents) is None


def test_build_plan_and_render_show_resolved_and_unresolved(parse_src):
    ast = parse_src(_SPEC)
    plan = build_plan(ast)
    assert plan["total_tasks"] == 4
    assert plan["ready_count"] == 3
    assert plan["subagents_known"] == 2
    # First dispatch entry must be the highest-priority ready task.
    assert plan["dispatch"][0]["task"]["class_name"] == "HighPriTask"
    assert plan["dispatch"][0]["resolved"] is True
    # The orphan entry is present but unresolved.
    orphan_entry = next(
        e for e in plan["dispatch"]
        if e["task"]["class_name"] == "OrphanAgentTask"
    )
    assert orphan_entry["resolved"] is False

    text = render(plan)
    assert "HighPriTask" in text
    assert "Plan" in text                  # resolved name
    assert "unresolved" in text            # orphan callout
    assert "Ghostbusters" in text
