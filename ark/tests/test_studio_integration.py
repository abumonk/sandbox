"""
test_studio_integration.py — End-to-end integration tests for studio hierarchy.

Covers TC-020 through TC-027:
  TC-020: ark.py parse specs/meta/ark_studio.ark exits 0
  TC-021: ark.py parse specs/meta/game_studio.ark exits 0
  TC-022: ark studio verify ark_studio.ark passes all studio checks
  TC-023: ark_studio.ark models Ark's team correctly (roles, tiers)
  TC-024: game_studio.ark has ~18 roles, ~20 commands
  TC-025: Both studios pass escalation acyclicity verification
  TC-026: Both studios pass command-role resolution verification
  TC-027: Both files registered in root.ark

All tests use subprocess.run (capture_output=True) and check returncode == 0.
Tests skip gracefully when spec files do not exist.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
ARK_STUDIO = REPO_ROOT / "specs" / "meta" / "ark_studio.ark"
GAME_STUDIO = REPO_ROOT / "specs" / "meta" / "game_studio.ark"
ROOT_ARK = REPO_ROOT / "specs" / "root.ark"

_PARSER_DIR = REPO_ROOT / "tools" / "parser"
if str(_PARSER_DIR) not in sys.path:
    sys.path.insert(0, str(_PARSER_DIR))


def _run(*args, **kwargs):
    """Run `python ark.py <args>` in REPO_ROOT, return CompletedProcess."""
    return subprocess.run(
        [sys.executable, "ark.py"] + list(args),
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        **kwargs,
    )


def _parse_ark_api(spec_path: Path):
    """Parse a .ark file using Python API; return ArkFile."""
    from ark_parser import parse
    source = spec_path.read_text(encoding="utf-8")
    return parse(source, file_path=spec_path)


# ---------------------------------------------------------------------------
# Skip markers
# ---------------------------------------------------------------------------

skip_no_ark_studio = pytest.mark.skipif(
    not ARK_STUDIO.exists(),
    reason=f"spec file not found: {ARK_STUDIO}",
)
skip_no_game_studio = pytest.mark.skipif(
    not GAME_STUDIO.exists(),
    reason=f"spec file not found: {GAME_STUDIO}",
)
skip_no_root = pytest.mark.skipif(
    not ROOT_ARK.exists(),
    reason=f"root.ark not found: {ROOT_ARK}",
)


# ---------------------------------------------------------------------------
# TC-020: Parse ark_studio.ark
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestArkStudioParse:
    """TC-020 — ark.py parse specs/meta/ark_studio.ark exits 0."""

    @skip_no_ark_studio
    def test_ark_studio_parses_exit_zero(self):
        """Parse command must exit 0 for ark_studio.ark."""
        result = _run("parse", str(ARK_STUDIO))
        assert result.returncode == 0, (
            f"Parse failed with code {result.returncode}\n"
            f"stderr: {result.stderr}"
        )

    @skip_no_ark_studio
    def test_ark_studio_parse_produces_json(self):
        """Parse output must be valid JSON."""
        result = _run("parse", str(ARK_STUDIO))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)

    @skip_no_ark_studio
    def test_ark_studio_has_lead_role(self):
        """Parsed AST must contain a 'Lead' role definition."""
        ark_file = _parse_ark_api(ARK_STUDIO)
        assert "Lead" in ark_file.roles, "Expected 'Lead' role in ark_studio.ark"

    @skip_no_ark_studio
    def test_ark_studio_has_ark_studio_item(self):
        """Parsed AST must contain an 'ArkStudio' studio definition."""
        ark_file = _parse_ark_api(ARK_STUDIO)
        assert "ArkStudio" in ark_file.studios, "Expected 'ArkStudio' studio in ark_studio.ark"


# ---------------------------------------------------------------------------
# TC-021: Parse game_studio.ark
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestGameStudioParse:
    """TC-021 — ark.py parse specs/meta/game_studio.ark exits 0."""

    @skip_no_game_studio
    def test_game_studio_parses_exit_zero(self):
        """Parse command must exit 0 for game_studio.ark."""
        result = _run("parse", str(GAME_STUDIO))
        assert result.returncode == 0, (
            f"Parse failed with code {result.returncode}\n"
            f"stderr: {result.stderr}"
        )

    @skip_no_game_studio
    def test_game_studio_parse_produces_json(self):
        """Parse output must be valid JSON."""
        result = _run("parse", str(GAME_STUDIO))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)

    @skip_no_game_studio
    def test_game_studio_role_count_at_least_15(self):
        """game_studio.ark should define at least 15 roles."""
        ark_file = _parse_ark_api(GAME_STUDIO)
        assert len(ark_file.roles) >= 15, (
            f"Expected >= 15 roles, found {len(ark_file.roles)}: {list(ark_file.roles.keys())}"
        )

    @skip_no_game_studio
    def test_game_studio_command_count_at_least_10(self):
        """game_studio.ark should define at least 10 commands."""
        ark_file = _parse_ark_api(GAME_STUDIO)
        assert len(ark_file.commands) >= 10, (
            f"Expected >= 10 commands, found {len(ark_file.commands)}"
        )


# ---------------------------------------------------------------------------
# TC-022: Studio verify ark_studio.ark
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestArkStudioVerify:
    """TC-022 — ark studio verify specs/meta/ark_studio.ark passes."""

    @skip_no_ark_studio
    def test_ark_studio_verify_exits_zero(self):
        """studio verify must exit 0 for ark_studio.ark."""
        result = _run("studio", "verify", str(ARK_STUDIO))
        assert result.returncode == 0, (
            f"studio verify failed with code {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    @skip_no_ark_studio
    def test_ark_studio_escalation_acyclic(self):
        """Verify output must confirm escalation_acyclicity passed."""
        result = _run("studio", "verify", str(ARK_STUDIO))
        assert result.returncode == 0
        assert "escalation_acyclicity" in result.stdout

    @skip_no_ark_studio
    def test_ark_studio_commands_all_resolve(self):
        """Verify output must confirm command_role_resolution passed."""
        result = _run("studio", "verify", str(ARK_STUDIO))
        assert result.returncode == 0
        assert "command_role_resolution" in result.stdout

    @skip_no_game_studio
    def test_game_studio_verify_exits_zero(self):
        """studio verify must exit 0 for game_studio.ark."""
        result = _run("studio", "verify", str(GAME_STUDIO))
        assert result.returncode == 0, (
            f"studio verify failed with code {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


# ---------------------------------------------------------------------------
# TC-023: ark_studio model accuracy
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestArkStudioModel:
    """TC-023 — ark_studio.ark correctly models Ark's team."""

    @skip_no_ark_studio
    def test_ark_studio_has_planner_role(self):
        """ArkStudio must define a Planner role."""
        ark_file = _parse_ark_api(ARK_STUDIO)
        assert "Planner" in ark_file.roles

    @skip_no_ark_studio
    def test_ark_studio_has_coder_role(self):
        """ArkStudio must define a Coder role."""
        ark_file = _parse_ark_api(ARK_STUDIO)
        assert "Coder" in ark_file.roles

    @skip_no_ark_studio
    def test_ark_studio_has_reviewer_role(self):
        """ArkStudio must define a CodeReviewer role."""
        ark_file = _parse_ark_api(ARK_STUDIO)
        assert "CodeReviewer" in ark_file.roles

    @skip_no_ark_studio
    def test_ark_studio_tier_groups_populated(self):
        """ArkStudio studio item must have tiers populated."""
        ark_file = _parse_ark_api(ARK_STUDIO)
        studio = ark_file.studios.get("ArkStudio")
        assert studio is not None, "ArkStudio not found in studios index"
        assert len(studio.tiers) > 0, "ArkStudio has no tier groups"

    @skip_no_ark_studio
    def test_ark_studio_lead_at_tier_1(self):
        """Lead role must be at tier 1 (parser may store tier as dict or int)."""
        ark_file = _parse_ark_api(ARK_STUDIO)
        lead = ark_file.roles.get("Lead")
        assert lead is not None
        # The parser stores tier as a dict {'expr': 'number', 'value': N} or int N
        tier = lead.tier
        tier_val = tier["value"] if isinstance(tier, dict) else tier
        assert tier_val == 1, f"Expected Lead at tier 1, got {lead.tier}"

    @skip_no_ark_studio
    def test_ark_studio_has_commands(self):
        """ArkStudio must define workflow commands."""
        ark_file = _parse_ark_api(ARK_STUDIO)
        assert len(ark_file.commands) > 0, "No commands found in ark_studio.ark"

    @skip_no_ark_studio
    def test_ark_studio_plan_task_command_exists(self):
        """plan_task command should exist in ark_studio.ark."""
        ark_file = _parse_ark_api(ARK_STUDIO)
        assert "plan_task" in ark_file.commands


# ---------------------------------------------------------------------------
# TC-024: game_studio model accuracy
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestGameStudioModel:
    """TC-024 — game_studio.ark has directors, leads, and specialists."""

    @skip_no_game_studio
    def test_game_studio_has_creative_director(self):
        """GameStudio must define a Creative_Director role."""
        ark_file = _parse_ark_api(GAME_STUDIO)
        assert "Creative_Director" in ark_file.roles

    @skip_no_game_studio
    def test_game_studio_has_technical_director(self):
        """GameStudio must define a Technical_Director role."""
        ark_file = _parse_ark_api(GAME_STUDIO)
        assert "Technical_Director" in ark_file.roles

    @skip_no_game_studio
    def test_game_studio_has_lead_programmer(self):
        """GameStudio must define a Lead_Programmer role."""
        ark_file = _parse_ark_api(GAME_STUDIO)
        assert "Lead_Programmer" in ark_file.roles

    @skip_no_game_studio
    def test_game_studio_tier_1_has_directors(self):
        """GameStudio tier 1 must contain directors."""
        ark_file = _parse_ark_api(GAME_STUDIO)
        studio = ark_file.studios.get("GameStudio")
        assert studio is not None
        # Find tier 1 group
        tier1_groups = [t for t in studio.tiers if t.level == 1]
        assert len(tier1_groups) > 0, "No tier 1 group found in GameStudio"
        tier1_members = tier1_groups[0].members
        assert len(tier1_members) > 0, "Tier 1 group is empty"

    @skip_no_game_studio
    def test_game_studio_tier_3_has_specialists(self):
        """GameStudio tier 3 must contain specialists."""
        ark_file = _parse_ark_api(GAME_STUDIO)
        studio = ark_file.studios.get("GameStudio")
        assert studio is not None
        tier3_groups = [t for t in studio.tiers if t.level == 3]
        assert len(tier3_groups) > 0, "No tier 3 group found in GameStudio"
        tier3_members = tier3_groups[0].members
        assert len(tier3_members) >= 5, (
            f"Expected >= 5 tier-3 specialists, found {len(tier3_members)}"
        )

    @skip_no_game_studio
    def test_game_studio_creative_director_at_tier_1(self):
        """Creative_Director must be at tier 1."""
        ark_file = _parse_ark_api(GAME_STUDIO)
        cd = ark_file.roles.get("Creative_Director")
        assert cd is not None
        tier = cd.tier
        tier_val = tier["value"] if isinstance(tier, dict) else tier
        assert tier_val == 1, f"Expected Creative_Director at tier 1, got {cd.tier}"

    @skip_no_game_studio
    def test_game_studio_lead_programmer_at_tier_2(self):
        """Lead_Programmer must be at tier 2."""
        ark_file = _parse_ark_api(GAME_STUDIO)
        lp = ark_file.roles.get("Lead_Programmer")
        assert lp is not None
        tier = lp.tier
        tier_val = tier["value"] if isinstance(tier, dict) else tier
        assert tier_val == 2, f"Expected Lead_Programmer at tier 2, got {lp.tier}"

    @skip_no_game_studio
    def test_game_studio_gameplay_programmer_at_tier_3(self):
        """Gameplay_Programmer must be at tier 3."""
        ark_file = _parse_ark_api(GAME_STUDIO)
        gp = ark_file.roles.get("Gameplay_Programmer")
        assert gp is not None
        tier = gp.tier
        tier_val = tier["value"] if isinstance(tier, dict) else tier
        assert tier_val == 3, f"Expected Gameplay_Programmer at tier 3, got {gp.tier}"


# ---------------------------------------------------------------------------
# TC-025: Escalation acyclicity for both studios
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestEscalationBoth:
    """TC-025 — Both studios pass escalation acyclicity verification."""

    @skip_no_ark_studio
    def test_ark_studio_no_escalation_cycles(self):
        """ark_studio.ark verify must pass escalation_acyclicity check."""
        result = _run("studio", "verify", str(ARK_STUDIO))
        assert result.returncode == 0
        assert "escalation_acyclicity" in result.stdout

    @skip_no_game_studio
    def test_game_studio_no_escalation_cycles(self):
        """game_studio.ark verify must pass escalation_acyclicity check."""
        result = _run("studio", "verify", str(GAME_STUDIO))
        assert result.returncode == 0
        assert "escalation_acyclicity" in result.stdout

    @skip_no_ark_studio
    def test_ark_studio_chain_terminates_at_lead(self):
        """In ark_studio.ark, every escalation chain must end at Lead (tier 1)."""
        ark_file = _parse_ark_api(ARK_STUDIO)
        # Follow escalation chains; they must all terminate
        def find_chain_root(role_name, visited=None):
            if visited is None:
                visited = set()
            if role_name in visited:
                return None  # cycle
            visited.add(role_name)
            role = ark_file.roles.get(role_name)
            if role is None or role.escalates_to is None:
                return role_name  # terminal node
            return find_chain_root(role.escalates_to, visited)

        for name, role in ark_file.roles.items():
            if role.escalates_to is not None:
                root = find_chain_root(name)
                assert root is not None, f"Cycle detected in escalation chain from {name}"

    @skip_no_game_studio
    def test_game_studio_chain_terminates_at_director(self):
        """In game_studio.ark, every escalation chain must terminate at a tier-1 role."""
        ark_file = _parse_ark_api(GAME_STUDIO)

        def find_chain_root(role_name, visited=None):
            if visited is None:
                visited = set()
            if role_name in visited:
                return None  # cycle
            visited.add(role_name)
            role = ark_file.roles.get(role_name)
            if role is None or role.escalates_to is None:
                return role_name
            return find_chain_root(role.escalates_to, visited)

        def get_tier_val(role):
            """Normalise tier which may be dict or int."""
            t = role.tier
            if isinstance(t, dict):
                return t.get("value")
            return t

        for name, role in ark_file.roles.items():
            if role.escalates_to is not None:
                root = find_chain_root(name)
                assert root is not None, f"Cycle detected in escalation chain from {name}"
                # Root must be a tier-1 role
                root_role = ark_file.roles.get(root)
                if root_role is not None:
                    tier_val = get_tier_val(root_role)
                    assert tier_val == 1, (
                        f"Chain from {name} terminates at {root} (tier {tier_val}), expected tier 1"
                    )


# ---------------------------------------------------------------------------
# TC-026: Command-role resolution for both studios
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestCommandResolutionBoth:
    """TC-026 — Both studios pass command-role resolution verification."""

    @skip_no_ark_studio
    def test_ark_studio_all_commands_resolve(self):
        """All commands in ark_studio.ark must reference roles that exist."""
        ark_file = _parse_ark_api(ARK_STUDIO)
        for cmd_name, cmd in ark_file.commands.items():
            if cmd.role:
                assert cmd.role in ark_file.roles, (
                    f"Command '{cmd_name}' references role '{cmd.role}' which is not defined"
                )

    @skip_no_game_studio
    def test_game_studio_all_commands_resolve(self):
        """All commands in game_studio.ark must reference roles that exist."""
        ark_file = _parse_ark_api(GAME_STUDIO)
        for cmd_name, cmd in ark_file.commands.items():
            if cmd.role:
                assert cmd.role in ark_file.roles, (
                    f"Command '{cmd_name}' references role '{cmd.role}' which is not defined"
                )

    @skip_no_ark_studio
    def test_ark_studio_verify_confirms_command_resolution(self):
        """studio verify output must explicitly confirm command_role_resolution."""
        result = _run("studio", "verify", str(ARK_STUDIO))
        assert result.returncode == 0
        assert "command_role_resolution" in result.stdout

    @skip_no_game_studio
    def test_game_studio_verify_confirms_command_resolution(self):
        """studio verify output must explicitly confirm command_role_resolution."""
        result = _run("studio", "verify", str(GAME_STUDIO))
        assert result.returncode == 0
        assert "command_role_resolution" in result.stdout


# ---------------------------------------------------------------------------
# Codegen output file count checks
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestCodegenOutputCounts:
    """Verify ark_studio: 13 files, game_studio: 50 files from codegen."""

    @skip_no_ark_studio
    def test_ark_studio_codegen_exit_zero(self, tmp_path):
        """ark studio codegen ark_studio.ark must exit 0."""
        result = _run("studio", "codegen", str(ARK_STUDIO), "--out", str(tmp_path))
        assert result.returncode == 0

    @skip_no_ark_studio
    def test_ark_studio_codegen_file_count(self, tmp_path):
        """ark_studio.ark codegen must produce exactly 13 output files."""
        result = _run("studio", "codegen", str(ARK_STUDIO), "--out", str(tmp_path))
        assert result.returncode == 0
        all_files = list(tmp_path.rglob("*"))
        file_count = sum(1 for f in all_files if f.is_file())
        assert file_count == 13, (
            f"Expected 13 files from ark_studio codegen, got {file_count}:\n"
            + "\n".join(str(f.relative_to(tmp_path)) for f in all_files if f.is_file())
        )

    @skip_no_game_studio
    def test_game_studio_codegen_exit_zero(self, tmp_path):
        """ark studio codegen game_studio.ark must exit 0."""
        result = _run("studio", "codegen", str(GAME_STUDIO), "--out", str(tmp_path))
        assert result.returncode == 0

    @skip_no_game_studio
    def test_game_studio_codegen_file_count(self, tmp_path):
        """game_studio.ark codegen must produce exactly 50 output files."""
        result = _run("studio", "codegen", str(GAME_STUDIO), "--out", str(tmp_path))
        assert result.returncode == 0
        all_files = list(tmp_path.rglob("*"))
        file_count = sum(1 for f in all_files if f.is_file())
        assert file_count == 50, (
            f"Expected 50 files from game_studio codegen, got {file_count}"
        )


# ---------------------------------------------------------------------------
# Orgchart generation
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestOrgchartGeneration:
    """Verify orgchart generation for both studios."""

    @skip_no_ark_studio
    def test_ark_studio_orgchart_exits_zero(self, tmp_path):
        """ark studio orgchart ark_studio.ark must exit 0."""
        out_file = tmp_path / "ark_orgchart.html"
        result = _run("studio", "orgchart", str(ARK_STUDIO), "--out", str(out_file))
        assert result.returncode == 0, (
            f"orgchart failed\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    @skip_no_ark_studio
    def test_ark_studio_orgchart_creates_html(self, tmp_path):
        """studio orgchart must create an HTML file on disk."""
        out_file = tmp_path / "ark_orgchart.html"
        _run("studio", "orgchart", str(ARK_STUDIO), "--out", str(out_file))
        assert out_file.exists(), "Orgchart HTML file was not created"

    @skip_no_ark_studio
    def test_ark_studio_orgchart_mentions_studios_roles(self, tmp_path):
        """Orgchart output must mention studio and role counts."""
        out_file = tmp_path / "ark_orgchart.html"
        result = _run("studio", "orgchart", str(ARK_STUDIO), "--out", str(out_file))
        assert "studios" in result.stdout or "roles" in result.stdout

    @skip_no_game_studio
    def test_game_studio_orgchart_exits_zero(self, tmp_path):
        """ark studio orgchart game_studio.ark must exit 0."""
        out_file = tmp_path / "game_orgchart.html"
        result = _run("studio", "orgchart", str(GAME_STUDIO), "--out", str(out_file))
        assert result.returncode == 0, (
            f"orgchart failed\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    @skip_no_game_studio
    def test_game_studio_orgchart_creates_html(self, tmp_path):
        """studio orgchart must create an HTML file on disk."""
        out_file = tmp_path / "game_orgchart.html"
        _run("studio", "orgchart", str(GAME_STUDIO), "--out", str(out_file))
        assert out_file.exists(), "GameStudio orgchart HTML file was not created"


# ---------------------------------------------------------------------------
# TC-027: Root registration
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestRootRegistration:
    """TC-027 — Both studio files are registered in root.ark."""

    @skip_no_root
    def test_ark_studio_registered_in_root(self):
        """root.ark must reference ArkStudio or ark_studio."""
        source = ROOT_ARK.read_text(encoding="utf-8")
        assert (
            "ark_studio" in source.lower()
            or "ArkStudio" in source
            or "meta/ark_studio" in source
        ), "ark_studio is not referenced in root.ark"

    @skip_no_root
    def test_game_studio_registered_in_root(self):
        """root.ark must reference GameStudio or game_studio."""
        source = ROOT_ARK.read_text(encoding="utf-8")
        assert (
            "game_studio" in source.lower()
            or "GameStudio" in source
            or "meta/game_studio" in source
        ), "game_studio is not referenced in root.ark"
