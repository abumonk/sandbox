"""
test_studio_codegen.py — Tests for studio_codegen.py

Covers TC-015 through TC-019:
  TC-015: Agent .md files generated correctly from role items
  TC-016: Command .md files generated correctly from command items
  TC-017: Hook settings.json fragment generated correctly
  TC-018: Template skeleton files generated correctly
  TC-019: --target studio CLI flag works end-to-end
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
_CODEGEN_DIR = REPO_ROOT / "tools" / "codegen"
_PARSER_DIR = REPO_ROOT / "tools" / "parser"

if str(_CODEGEN_DIR) not in sys.path:
    sys.path.insert(0, str(_CODEGEN_DIR))
if str(_PARSER_DIR) not in sys.path:
    sys.path.insert(0, str(_PARSER_DIR))

from studio_codegen import gen_agent_md, gen_command_md, gen_hook_json, gen_template_md, gen_studio


# ---------------------------------------------------------------------------
# Mock dataclasses (matching parser output structure)
# ---------------------------------------------------------------------------

@dataclass
class MockRole:
    kind: str = "role"
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
    inherits: list = field(default_factory=list)
    data_fields: list = field(default_factory=list)
    in_ports: list = field(default_factory=list)
    out_ports: list = field(default_factory=list)
    processes: list = field(default_factory=list)


@dataclass
class MockCommand:
    kind: str = "command"
    name: str = "plan"
    phase: Optional[str] = "planning"
    role: Optional[str] = "Architect"
    prompt: Optional[str] = "Create a structured plan for the given feature."
    output: Optional[str] = "A markdown plan file at .agent/plans/{id}.md"
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class MockHook:
    kind: str = "hook"
    name: str = "on_save_ark"
    event: Optional[str] = "file_save"
    pattern: Optional[str] = "**/*.ark"
    action: Optional[str] = "python ark.py verify $file"
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class MockTemplate:
    kind: str = "template"
    name: str = "FeaturePlan"
    sections: list = field(default_factory=lambda: ["Overview", "Design", "Tasks", "Risks"])
    bound_to: Optional[str] = "planning"
    data_fields: list = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class MockArkFile:
    imports: list = field(default_factory=list)
    items: list = field(default_factory=list)
    classes: dict = field(default_factory=dict)
    instances: dict = field(default_factory=dict)
    island_classes: dict = field(default_factory=dict)
    expression_index: dict = field(default_factory=dict)
    predicate_index: dict = field(default_factory=dict)
    roles: dict = field(default_factory=dict)
    studios: dict = field(default_factory=dict)
    commands: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# TC-015: gen_agent_md
# ---------------------------------------------------------------------------

class TestAgentMd:
    """TC-015 — Agent .md files generated correctly from role items."""

    def setup_method(self):
        self.role = MockRole()
        self.md = gen_agent_md(self.role)

    def test_agent_md_has_frontmatter(self):
        """Output must contain YAML frontmatter delimiters."""
        assert "---" in self.md

    def test_agent_md_name_field(self):
        """name field in frontmatter must match role name."""
        assert "name: Architect" in self.md

    def test_agent_md_description_field(self):
        """description field must appear in frontmatter."""
        assert "description: Designs system blueprints." in self.md

    def test_agent_md_model_derived_from_tier(self):
        """Model must be derived from the role tier."""
        # tier 1 (Director) → claude-opus-4-5
        assert "model: claude-opus-4-5" in self.md

    def test_agent_md_tools_list(self):
        """Tools must appear in frontmatter."""
        assert "tools:" in self.md
        # All tools must be present
        for tool in ["Read", "Bash", "Write"]:
            assert tool in self.md

    def test_agent_md_has_responsibilities_section(self):
        """## Responsibilities section must be present with role data."""
        assert "## Responsibilities" in self.md
        assert "Own the system architecture" in self.md
        assert "Review cross-island bridges" in self.md

    def test_agent_md_has_escalation_section(self):
        """## Escalation section must be present."""
        assert "## Escalation" in self.md
        assert "Reports to:" in self.md

    def test_director_gets_opus_model(self):
        """Tier 1 role must use claude-opus-4-5."""
        role = MockRole(tier=1)
        md = gen_agent_md(role)
        assert "model: claude-opus-4-5" in md

    def test_specialist_gets_sonnet_model(self):
        """Tier 3 role must use claude-sonnet-4-5."""
        role = MockRole(name="Coder", tier=3, escalates_to="Lead")
        md = gen_agent_md(role)
        assert "model: claude-sonnet-4-5" in md

    def test_agent_md_no_escalation_for_director(self):
        """Director with no escalates_to should show 'None (Director)'."""
        role = MockRole(tier=1, escalates_to=None)
        md = gen_agent_md(role)
        assert "None (Director)" in md

    def test_agent_md_escalation_shows_target(self):
        """Role with escalates_to should show target name in escalation."""
        role = MockRole(name="Specialist", tier=3, escalates_to="Lead")
        md = gen_agent_md(role)
        assert "Reports to: Lead" in md

    def test_agent_md_tier_label_director(self):
        """Tier 1 should appear with 'Director' label."""
        role = MockRole(tier=1)
        md = gen_agent_md(role)
        assert "Director" in md

    def test_agent_md_tier_label_specialist(self):
        """Tier 3 should appear with 'Specialist' label."""
        role = MockRole(name="Coder", tier=3)
        md = gen_agent_md(role)
        assert "Specialist" in md

    def test_agent_md_skills_block(self):
        """Skills must appear in the output."""
        assert "ark-dsl" in self.md
        assert "rust" in self.md

    def test_agent_md_tier_2_gets_opus(self):
        """Tier 2 (Lead) must also use claude-opus-4-5."""
        role = MockRole(name="Lead", tier=2)
        md = gen_agent_md(role)
        assert "model: claude-opus-4-5" in md

    def test_agent_md_empty_tools(self):
        """Role with no tools should output empty tools list."""
        role = MockRole(tools=[])
        md = gen_agent_md(role)
        assert "tools: []" in md

    def test_agent_md_string_tier_director(self):
        """Tier passed as string 'Director' should map to opus model."""
        role = MockRole(tier="Director")
        md = gen_agent_md(role)
        assert "model: claude-opus-4-5" in md

    def test_agent_md_string_tier_specialist(self):
        """Tier passed as string 'Specialist' should map to sonnet model."""
        role = MockRole(name="Coder", tier="Specialist")
        md = gen_agent_md(role)
        assert "model: claude-sonnet-4-5" in md


# ---------------------------------------------------------------------------
# TC-016: gen_command_md
# ---------------------------------------------------------------------------

class TestCommandMd:
    """TC-016 — Command .md files generated correctly."""

    def setup_method(self):
        self.cmd = MockCommand()
        self.md = gen_command_md(self.cmd)

    def test_command_md_has_title(self):
        """Output must start with a # heading containing the command name."""
        assert "# /plan" in self.md

    def test_command_md_phase_present(self):
        """Phase field must appear in the output."""
        assert "Phase: planning" in self.md

    def test_command_md_role_present(self):
        """Required Role field must appear."""
        assert "Required Role: Architect" in self.md

    def test_command_md_prompt_body(self):
        """Prompt content must appear under ## Prompt."""
        assert "## Prompt" in self.md
        assert "Create a structured plan for the given feature." in self.md

    def test_command_md_output_section(self):
        """## Output section must be present."""
        assert "## Output" in self.md
        assert "A markdown plan file" in self.md

    def test_command_md_defaults_for_none(self):
        """None fields should produce sensible defaults."""
        cmd = MockCommand(phase=None, role=None, prompt=None, output=None)
        md = gen_command_md(cmd)
        assert "Phase: any" in md
        assert "Required Role: any" in md


# ---------------------------------------------------------------------------
# TC-017: gen_hook_json
# ---------------------------------------------------------------------------

class TestHookJson:
    """TC-017 — Hook settings.json fragment generated correctly."""

    def setup_method(self):
        self.hook = MockHook()
        self.json_str = gen_hook_json([self.hook])
        self.data = json.loads(self.json_str)

    def test_hook_json_has_hooks_key(self):
        """Output must be a dict with top-level 'hooks' key."""
        assert "hooks" in self.data

    def test_hook_json_entry_has_event(self):
        """Hook entry must include the event field."""
        assert self.data["hooks"]["on_save_ark"]["event"] == "file_save"

    def test_hook_json_entry_has_pattern(self):
        """Hook entry must include the pattern field."""
        assert self.data["hooks"]["on_save_ark"]["pattern"] == "**/*.ark"

    def test_hook_json_entry_has_action(self):
        """Hook entry must include the action field."""
        assert self.data["hooks"]["on_save_ark"]["action"] == "python ark.py verify $file"

    def test_multiple_hooks_all_present(self):
        """All hooks passed to gen_hook_json must appear in output."""
        hook2 = MockHook(name="on_test_run", event="test_start",
                         pattern="tests/**/*.py", action="run_tests")
        result = json.loads(gen_hook_json([self.hook, hook2]))
        assert "on_save_ark" in result["hooks"]
        assert "on_test_run" in result["hooks"]

    def test_hook_json_is_valid_json(self):
        """gen_hook_json output must be parseable JSON."""
        parsed = json.loads(self.json_str)
        assert isinstance(parsed, dict)

    def test_hook_json_empty_hooks(self):
        """Empty hook list should yield {'hooks': {}}."""
        result = json.loads(gen_hook_json([]))
        assert result == {"hooks": {}}

    def test_hook_json_none_fields_omitted(self):
        """None event/pattern/action fields should not appear in output."""
        hook = MockHook(name="bare", event=None, pattern=None, action=None)
        result = json.loads(gen_hook_json([hook]))
        entry = result["hooks"]["bare"]
        assert "event" not in entry
        assert "pattern" not in entry
        assert "action" not in entry


# ---------------------------------------------------------------------------
# TC-018: gen_template_md
# ---------------------------------------------------------------------------

class TestTemplateMd:
    """TC-018 — Template skeleton files generated correctly."""

    def setup_method(self):
        self.tmpl = MockTemplate()
        self.md = gen_template_md(self.tmpl)

    def test_template_md_has_title(self):
        """Output must have a # title with the template name."""
        assert "# FeaturePlan" in self.md

    def test_template_md_has_required_sections(self):
        """All sections must appear as ## headings."""
        for section in ["Overview", "Design", "Tasks", "Risks"]:
            assert f"## {section}" in self.md

    def test_template_md_section_placeholder_present(self):
        """Each section must have a placeholder comment."""
        assert "Required section" in self.md
        assert "fill in content" in self.md

    def test_template_md_bound_to_comment(self):
        """bound_to must appear as an HTML comment."""
        assert "Template bound to: planning" in self.md

    def test_template_md_no_bound_to(self):
        """Template without bound_to should not include bound_to comment."""
        tmpl = MockTemplate(bound_to=None)
        md = gen_template_md(tmpl)
        assert "Template bound to:" not in md

    def test_template_md_no_sections(self):
        """Template with empty sections should show no-sections comment."""
        tmpl = MockTemplate(sections=[])
        md = gen_template_md(tmpl)
        assert "No sections defined" in md

    def test_template_md_multiple_sections(self):
        """Every section name must become a ## heading."""
        tmpl = MockTemplate(sections=["Alpha", "Beta", "Gamma"])
        md = gen_template_md(tmpl)
        assert "## Alpha" in md
        assert "## Beta" in md
        assert "## Gamma" in md


# ---------------------------------------------------------------------------
# TC-019: gen_studio (orchestrator + CLI)
# ---------------------------------------------------------------------------

class TestGenStudio:
    """TC-019 — gen_studio generates all artifact types from an ArkFile."""

    def _make_ark_file(self):
        from ark_parser import RoleDef, CommandDef, HookDef, TemplateDef
        role = RoleDef(name="Architect", tier=1,
                       description="System architect",
                       responsibilities=["Design systems"],
                       skills=["rust"],
                       tools=["Read", "Write"])
        cmd = CommandDef(name="plan_arch", phase="planning",
                         role="Architect",
                         prompt="Design the architecture",
                         output="arch_doc")
        hook = HookDef(name="on_verify", event="pre_commit",
                       pattern="specs/**/*.ark",
                       action="python ark.py verify $FILE")
        tmpl = TemplateDef(name="ArchPlan",
                           sections=["Overview", "Components"],
                           bound_to="Architect")
        ark_file = MockArkFile(items=[role, cmd, hook, tmpl])
        return ark_file

    def test_cli_studio_target_exits_zero(self, tmp_path):
        """ark studio codegen on a valid .ark file should exit with code 0."""
        result = subprocess.run(
            [sys.executable, "ark.py", "studio", "codegen",
             "specs/meta/ark_studio.ark", "--out", str(tmp_path)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Expected exit 0, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_cli_generates_agent_files(self, tmp_path):
        """studio codegen must create agents/ directory with .md files."""
        subprocess.run(
            [sys.executable, "ark.py", "studio", "codegen",
             "specs/meta/ark_studio.ark", "--out", str(tmp_path)],
            cwd=str(REPO_ROOT), capture_output=True,
        )
        agents_dir = tmp_path / "agents"
        assert agents_dir.exists(), "agents/ directory not created"
        md_files = list(agents_dir.glob("*.md"))
        assert len(md_files) > 0, "No agent .md files generated"

    def test_cli_generates_command_files(self, tmp_path):
        """studio codegen must create commands/ directory with .md files."""
        subprocess.run(
            [sys.executable, "ark.py", "studio", "codegen",
             "specs/meta/ark_studio.ark", "--out", str(tmp_path)],
            cwd=str(REPO_ROOT), capture_output=True,
        )
        cmds_dir = tmp_path / "commands"
        assert cmds_dir.exists(), "commands/ directory not created"
        md_files = list(cmds_dir.glob("*.md"))
        assert len(md_files) > 0, "No command .md files generated"

    def test_cli_generates_hook_json(self, tmp_path):
        """studio codegen must create hooks.json."""
        subprocess.run(
            [sys.executable, "ark.py", "studio", "codegen",
             "specs/meta/ark_studio.ark", "--out", str(tmp_path)],
            cwd=str(REPO_ROOT), capture_output=True,
        )
        hooks_file = tmp_path / "hooks.json"
        assert hooks_file.exists(), "hooks.json not created"
        data = json.loads(hooks_file.read_text())
        assert "hooks" in data

    def test_cli_output_dir_created(self, tmp_path):
        """Output directory (and subdirs) must be created by codegen."""
        out_dir = tmp_path / "codegen_output"
        subprocess.run(
            [sys.executable, "ark.py", "studio", "codegen",
             "specs/meta/ark_studio.ark", "--out", str(out_dir)],
            cwd=str(REPO_ROOT), capture_output=True,
        )
        assert out_dir.exists(), "Output directory was not created"

    def test_gen_studio_returns_artifacts_dict(self):
        """gen_studio must return a dict mapping filename -> content."""
        ark_file = self._make_ark_file()
        result = gen_studio(ark_file)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_gen_studio_produces_agent_files(self):
        """gen_studio must produce agents/*.md keys."""
        ark_file = self._make_ark_file()
        result = gen_studio(ark_file)
        agent_keys = [k for k in result if k.startswith("agents/")]
        assert len(agent_keys) > 0

    def test_gen_studio_produces_command_files(self):
        """gen_studio must produce commands/*.md keys."""
        ark_file = self._make_ark_file()
        result = gen_studio(ark_file)
        cmd_keys = [k for k in result if k.startswith("commands/")]
        assert len(cmd_keys) > 0

    def test_gen_studio_produces_hooks_json(self):
        """gen_studio must include hooks.json in results."""
        ark_file = self._make_ark_file()
        result = gen_studio(ark_file)
        assert "hooks.json" in result
        data = json.loads(result["hooks.json"])
        assert "hooks" in data

    def test_gen_studio_produces_template_files(self):
        """gen_studio must produce templates/*.md keys."""
        ark_file = self._make_ark_file()
        result = gen_studio(ark_file)
        tmpl_keys = [k for k in result if k.startswith("templates/")]
        assert len(tmpl_keys) > 0

    def test_gen_studio_writes_files_to_disk(self, tmp_path):
        """gen_studio with output_dir must write files to disk."""
        ark_file = self._make_ark_file()
        gen_studio(ark_file, output_dir=tmp_path)
        agents_dir = tmp_path / "agents"
        assert agents_dir.exists()
        assert (tmp_path / "hooks.json").exists()
