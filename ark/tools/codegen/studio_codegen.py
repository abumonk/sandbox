"""
studio_codegen.py — Code generation for Claude Code studio artifacts.

Generates from studio .ark specs:
  - agents/*.md       — Claude Code agent definition files (one per role)
  - commands/*.md     — Slash-command files (one per command)
  - hooks.json        — Settings fragment with all hook configurations
  - templates/*.md    — Template skeleton files (one per template)

Pipeline:  .ark → parse → ArkFile AST → studio_codegen → .md / .json
"""

import json
import os
from pathlib import Path
from typing import Optional, Union

# ---------------------------------------------------------------------------
# Tier helpers
# ---------------------------------------------------------------------------

TIER_MODEL = {
    1: "claude-opus-4-5",    # Director tier — highest capability
    2: "claude-opus-4-5",    # Lead tier    — also opus
    3: "claude-sonnet-4-5",  # Specialist tier — sonnet
}

TIER_LABEL = {
    1: "Director",
    2: "Lead",
    3: "Specialist",
}

TIER_DESCRIPTION = {
    1: "Strategic oversight and final decision authority",
    2: "Domain leadership and cross-team coordination",
    3: "Deep technical execution within a domain",
}

# String-form tier names (may be stored as strings when parsed from DSL idents)
TIER_NAME_TO_INT = {
    "director": 1, "Director": 1,
    "lead": 2, "Lead": 2,
    "specialist": 3, "Specialist": 3,
}


def _normalise_tier(tier) -> Optional[int]:
    """Normalise a tier value (int, str, dict or None) to an int or None."""
    if tier is None:
        return None
    if isinstance(tier, int):
        return tier
    if isinstance(tier, float):
        return int(tier)
    if isinstance(tier, str):
        return TIER_NAME_TO_INT.get(tier) or TIER_NAME_TO_INT.get(tier.capitalize())
    if isinstance(tier, dict):
        # Parser may store {"expr": "ident", "name": "Director"} or similar
        name = tier.get("name") or tier.get("value") or ""
        if isinstance(name, int):
            return name
        return TIER_NAME_TO_INT.get(name) or TIER_NAME_TO_INT.get(str(name).capitalize())
    return None


def _tier_model(tier) -> str:
    """Return the model string for a given tier level."""
    t = _normalise_tier(tier)
    if t is None:
        return "claude-sonnet-4-5"
    return TIER_MODEL.get(t, "claude-sonnet-4-5")


def _tier_label(tier) -> str:
    """Return the human-readable tier label."""
    t = _normalise_tier(tier)
    if t is None:
        return "Specialist"
    return TIER_LABEL.get(t, "Specialist")


def _tier_desc(tier) -> str:
    """Return the tier description string."""
    t = _normalise_tier(tier)
    if t is None:
        return TIER_DESCRIPTION[3]
    return TIER_DESCRIPTION.get(t, TIER_DESCRIPTION[3])


# ---------------------------------------------------------------------------
# gen_agent_md
# ---------------------------------------------------------------------------

def gen_agent_md(role) -> str:
    """
    Generate a Claude Code agent definition (.md file) from a parsed RoleDef.

    Produces YAML frontmatter followed by a structured markdown body.

    Args:
        role: A RoleDef dataclass instance from ark_parser.

    Returns:
        A string containing the complete .md file content.
    """
    name = role.name
    tier = role.tier
    description = role.description or f"Agent responsible for {name} duties."
    model = _tier_model(tier)
    tools_list = ", ".join(role.tools) if role.tools else ""
    tier_label = _tier_label(tier)
    tier_desc = _tier_desc(tier)

    responsibilities_block = "\n".join(
        f"- {r}" for r in role.responsibilities
    ) if role.responsibilities else "- (none specified)"

    skills_block = "\n".join(
        f"- {s}" for s in role.skills
    ) if role.skills else "- (none specified)"

    escalation = role.escalates_to if role.escalates_to else "None (Director)"

    lines = []

    # YAML frontmatter
    lines.append("---")
    lines.append(f"name: {name}")
    lines.append(f"description: {description}")
    lines.append(f"model: {model}")
    if tools_list:
        lines.append(f"tools: [{tools_list}]")
    else:
        lines.append("tools: []")
    lines.append("---")
    lines.append("")

    # Body
    tier_int = _normalise_tier(tier)
    lines.append(f"You are the {name} agent.")
    lines.append("")
    lines.append(f"## Tier")
    lines.append(f"{tier_label} (tier {tier_int}) — {tier_desc}" if tier_int is not None
                 else f"{tier_label} — {tier_desc}")
    lines.append("")
    lines.append("## Responsibilities")
    lines.append(responsibilities_block)
    lines.append("")
    lines.append("## Skills")
    lines.append(skills_block)
    lines.append("")
    lines.append("## Escalation")
    lines.append(f"Reports to: {escalation}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# gen_command_md
# ---------------------------------------------------------------------------

def gen_command_md(command) -> str:
    """
    Generate a slash-command file (.md) from a parsed CommandDef.

    Args:
        command: A CommandDef dataclass instance from ark_parser.

    Returns:
        A string containing the complete .md file content.
    """
    name = command.name
    phase = command.phase or "any"
    role = command.role or "any"
    prompt = command.prompt or "(no prompt defined)"
    output = command.output or "Default"

    lines = []
    lines.append(f"# /{name}")
    lines.append("")
    lines.append(f"Phase: {phase}")
    lines.append(f"Required Role: {role}")
    lines.append("")
    lines.append("## Prompt")
    lines.append(prompt)
    lines.append("")
    lines.append("## Output")
    lines.append(output)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# gen_hook_json
# ---------------------------------------------------------------------------

def gen_hook_json(hooks) -> str:
    """
    Generate a settings.json fragment dict for all hook configurations.

    Args:
        hooks: An iterable of HookDef dataclass instances from ark_parser.

    Returns:
        A JSON string (pretty-printed) representing the hooks settings fragment.
    """
    hooks_dict = {}
    for hook in hooks:
        entry = {}
        if hook.event is not None:
            entry["event"] = hook.event
        if hook.pattern is not None:
            entry["pattern"] = hook.pattern
        if hook.action is not None:
            entry["action"] = hook.action
        hooks_dict[hook.name] = entry

    result = {"hooks": hooks_dict}
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# gen_template_md
# ---------------------------------------------------------------------------

def gen_template_md(template) -> str:
    """
    Generate a template skeleton (.md) from a parsed TemplateDef.

    Each section in template.sections becomes a ## heading with a placeholder
    comment, making it clear to the author what must be filled in.

    Args:
        template: A TemplateDef dataclass instance from ark_parser.

    Returns:
        A string containing the complete template skeleton .md content.
    """
    name = template.name
    bound = template.bound_to

    lines = []
    lines.append(f"# {name}")
    lines.append("")
    if bound:
        lines.append(f"<!-- Template bound to: {bound} -->")
        lines.append("")

    if template.sections:
        for section in template.sections:
            lines.append(f"## {section}")
            lines.append("")
            lines.append("<!-- Required section — fill in content -->")
            lines.append("")
    else:
        lines.append("<!-- No sections defined for this template -->")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# gen_studio — main orchestrator
# ---------------------------------------------------------------------------

def gen_studio(ark_file, output_dir: Optional[Union[str, Path]] = None) -> dict:
    """
    Generate all studio artifacts from a parsed ArkFile.

    Produces:
      - agents/{role_name}.md   for each RoleDef
      - commands/{cmd_name}.md  for each CommandDef
      - hooks.json              collecting all HookDef items
      - templates/{tmpl_name}.md for each TemplateDef

    Args:
        ark_file: A parsed ArkFile instance with .items list and index dicts.
        output_dir: Optional path. If provided, files are written to disk.
                    If None, only the dict is returned.

    Returns:
        dict mapping relative filename (str) → file content (str).
    """
    try:
        from ark_parser import RoleDef, CommandDef, HookDef, TemplateDef
    except ImportError:
        from tools.parser.ark_parser import RoleDef, CommandDef, HookDef, TemplateDef

    artifacts = {}

    roles = []
    commands = []
    hooks = []
    templates = []

    for item in ark_file.items:
        if isinstance(item, RoleDef):
            roles.append(item)
        elif isinstance(item, CommandDef):
            commands.append(item)
        elif isinstance(item, HookDef):
            hooks.append(item)
        elif isinstance(item, TemplateDef):
            templates.append(item)

    # Also pull from index dicts (populated by _build_indices) in case
    # items list is incomplete or has already been de-duplicated.
    for name, role in getattr(ark_file, "roles", {}).items():
        if not any(r.name == name for r in roles):
            roles.append(role)

    for name, cmd in getattr(ark_file, "commands", {}).items():
        if not any(c.name == name for c in commands):
            commands.append(cmd)

    # Generate agent files
    for role in roles:
        filename = f"agents/{role.name}.md"
        artifacts[filename] = gen_agent_md(role)

    # Generate command files
    for command in commands:
        filename = f"commands/{command.name}.md"
        artifacts[filename] = gen_command_md(command)

    # Generate hooks.json (all hooks in one file)
    if hooks:
        artifacts["hooks.json"] = gen_hook_json(hooks)
    else:
        artifacts["hooks.json"] = gen_hook_json([])

    # Generate template files
    for template in templates:
        filename = f"templates/{template.name}.md"
        artifacts[filename] = gen_template_md(template)

    # Write to disk if output_dir is provided
    if output_dir is not None:
        out = Path(output_dir)
        for rel_path, content in artifacts.items():
            full_path = out / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")

    return artifacts


# ---------------------------------------------------------------------------
# Inline smoke-test
# ---------------------------------------------------------------------------

def _smoke_test():
    """Quick self-test using mock dataclass instances (no parser needed)."""
    from dataclasses import dataclass, field
    from typing import Optional

    @dataclass
    class MockRole:
        name: str = "Architect"
        tier: Optional[int] = 1
        description: Optional[str] = "Designs system blueprints."
        responsibilities: list = field(default_factory=lambda: [
            "Own the system architecture",
            "Review cross-island bridges",
        ])
        skills: list = field(default_factory=lambda: ["ark-dsl", "rust", "z3"])
        tools: list = field(default_factory=lambda: ["Read", "Bash", "Write"])
        escalates_to: Optional[str] = None

    @dataclass
    class MockCommand:
        name: str = "plan"
        phase: Optional[str] = "planning"
        role: Optional[str] = "Architect"
        prompt: Optional[str] = "Create a structured plan for the given feature."
        output: Optional[str] = "A markdown plan file at .agent/plans/{id}.md"

    @dataclass
    class MockHook:
        name: str = "on_save_ark"
        event: Optional[str] = "file_save"
        pattern: Optional[str] = "**/*.ark"
        action: Optional[str] = "python ark.py verify $file"

    @dataclass
    class MockTemplate:
        name: str = "FeaturePlan"
        sections: list = field(default_factory=lambda: ["Overview", "Design", "Tasks", "Risks"])
        bound_to: Optional[str] = "planning"

    role = MockRole()
    command = MockCommand()
    hook = MockHook()
    template = MockTemplate()

    agent_md = gen_agent_md(role)
    assert "---" in agent_md, "Missing YAML frontmatter"
    assert "name: Architect" in agent_md
    assert "model: claude-opus-4-5" in agent_md  # tier 1 → opus
    assert "You are the Architect agent." in agent_md
    assert "Director" in agent_md
    assert "Own the system architecture" in agent_md
    assert "Reports to: None (Director)" in agent_md
    print("gen_agent_md: PASS")

    cmd_md = gen_command_md(command)
    assert "# /plan" in cmd_md
    assert "Phase: planning" in cmd_md
    assert "Required Role: Architect" in cmd_md
    assert "## Prompt" in cmd_md
    assert "## Output" in cmd_md
    print("gen_command_md: PASS")

    hook_json_str = gen_hook_json([hook])
    hook_data = json.loads(hook_json_str)
    assert "hooks" in hook_data
    assert "on_save_ark" in hook_data["hooks"]
    assert hook_data["hooks"]["on_save_ark"]["event"] == "file_save"
    assert hook_data["hooks"]["on_save_ark"]["pattern"] == "**/*.ark"
    assert hook_data["hooks"]["on_save_ark"]["action"] == "python ark.py verify $file"
    print("gen_hook_json: PASS")

    tmpl_md = gen_template_md(template)
    assert "# FeaturePlan" in tmpl_md
    assert "## Overview" in tmpl_md
    assert "## Design" in tmpl_md
    assert "## Tasks" in tmpl_md
    assert "## Risks" in tmpl_md
    assert "Required section" in tmpl_md
    print("gen_template_md: PASS")

    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    _smoke_test()
