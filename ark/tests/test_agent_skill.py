"""Tests for tools/agent/skill_manager.py and tools/agent/learning.py.

Covers TC-014 through TC-018.
"""

import sys
import pathlib
import tempfile
import importlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_AGENT_DIR = REPO_ROOT / "tools" / "agent"

# Insert agent dir into path so the package is on sys.path
if str(_AGENT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR.parent))
# Also add the agent dir itself for direct imports
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

# Import via the agent package to resolve relative imports
from agent.skill_manager import Skill, SkillTrigger, SkillManager, skill_from_spec  # noqa: E402
from agent.learning import SessionEntry, LearningEngine, learning_from_spec  # noqa: E402


# ---------------------------------------------------------------------------
# Skill / SkillTrigger basics
# ---------------------------------------------------------------------------

def test_skill_trigger_compiled_is_pattern():
    """SkillTrigger.compiled() returns a compiled regex pattern."""
    import re
    trigger = SkillTrigger(pattern=r"search|find", priority=5)
    pat = trigger.compiled()
    assert hasattr(pat, "search")
    assert pat.search("please search this")


def test_skill_trigger_property():
    """Skill.trigger property builds a SkillTrigger from stored fields."""
    skill = Skill(name="s", trigger_pattern=r"\btest\b", trigger_priority=2, steps=[])
    t = skill.trigger
    assert isinstance(t, SkillTrigger)
    assert t.pattern == r"\btest\b"
    assert t.priority == 2


def test_skill_to_dict_roundtrip():
    """Skill.to_dict() / Skill.from_dict() round-trip preserves all fields."""
    original = Skill(
        name="my_skill",
        trigger_pattern="search",
        trigger_priority=3,
        steps=["step1", "step2"],
        status="active",
        description="A test skill",
    )
    d = original.to_dict()
    restored = Skill.from_dict(d)
    assert restored.name == original.name
    assert restored.trigger_pattern == original.trigger_pattern
    assert restored.steps == original.steps
    assert restored.description == original.description


# ---------------------------------------------------------------------------
# SkillManager CRUD
# ---------------------------------------------------------------------------

def _make_manager():
    skills = [
        Skill(name="search", trigger_pattern="search|find", trigger_priority=5, steps=["do search"]),
        Skill(name="greet", trigger_pattern="hello|hi", trigger_priority=1, steps=["say hello"]),
        Skill(name="draft_skill", trigger_pattern="draft", trigger_priority=0,
              steps=["draft step"], status="draft"),
    ]
    return SkillManager(skills=skills)


def test_skill_manager_add_and_get():
    """SkillManager.add_skill() and get_skill() work correctly."""
    mgr = SkillManager()
    skill = Skill(name="new_skill", trigger_pattern="test", trigger_priority=1, steps=[])
    mgr.add_skill(skill)
    retrieved = mgr.get_skill("new_skill")
    assert retrieved is skill


def test_skill_manager_get_missing_raises():
    """SkillManager.get_skill() raises KeyError for missing skill."""
    mgr = SkillManager()
    try:
        mgr.get_skill("nonexistent")
        assert False, "Expected KeyError"
    except KeyError:
        pass


def test_skill_manager_update_skill():
    """SkillManager.update_skill() modifies a field on an existing skill."""
    mgr = _make_manager()
    mgr.update_skill("search", status="deprecated")
    assert mgr.get_skill("search").status == "deprecated"


def test_skill_manager_remove_skill():
    """SkillManager.remove_skill() removes skill from registry."""
    mgr = _make_manager()
    mgr.remove_skill("greet")
    skills = mgr.list_skills()
    assert all(s.name != "greet" for s in skills)


def test_skill_manager_list_all():
    """SkillManager.list_skills() returns all skills."""
    mgr = _make_manager()
    skills = mgr.list_skills()
    assert len(skills) == 3


def test_skill_manager_list_by_status():
    """SkillManager.list_skills(status=...) filters by status."""
    mgr = _make_manager()
    active = mgr.list_skills(status="active")
    assert all(s.status == "active" for s in active)
    draft = mgr.list_skills(status="draft")
    assert all(s.status == "draft" for s in draft)


# ---------------------------------------------------------------------------
# Trigger matching
# ---------------------------------------------------------------------------

def test_match_trigger_returns_active_only():
    """match_trigger() only returns active skills."""
    mgr = _make_manager()
    matches = mgr.match_trigger("draft something")
    names = [s.name for s, _ in matches]
    assert "draft_skill" not in names


def test_match_trigger_priority_sort():
    """match_trigger() returns matches sorted by trigger_priority descending."""
    mgr = _make_manager()
    matches = mgr.match_trigger("search hi hello find")
    priorities = [s.trigger_priority for s, _ in matches]
    assert priorities == sorted(priorities, reverse=True)


def test_match_trigger_no_match():
    """match_trigger() returns empty list when no pattern matches."""
    mgr = _make_manager()
    matches = mgr.match_trigger("unrelated content xyz")
    assert matches == []


def test_match_trigger_case_insensitive():
    """match_trigger() is case-insensitive."""
    mgr = _make_manager()
    matches = mgr.match_trigger("SEARCH something")
    names = [s.name for s, _ in matches]
    assert "search" in names


# ---------------------------------------------------------------------------
# Skill execution
# ---------------------------------------------------------------------------

def test_execute_skill_formats_steps():
    """SkillManager.execute_skill() returns formatted step plan."""
    mgr = _make_manager()
    skill = mgr.get_skill("search")
    result = mgr.execute_skill(skill, context={"sender": "alice", "content": "search foo"})
    assert "Executing skill: search" in result
    assert "1." in result


# ---------------------------------------------------------------------------
# Improvement tracking
# ---------------------------------------------------------------------------

def test_improve_skill_records_entry():
    """SkillManager.improve_skill() appends an improvement entry."""
    mgr = _make_manager()
    updated = mgr.improve_skill("search", old_score=0.5, new_score=0.8, summary="better")
    assert len(updated.improvement_history) == 1
    entry = updated.improvement_history[0]
    assert entry["old_score"] == 0.5
    assert entry["new_score"] == 0.8
    assert "delta" in entry


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_skill_manager_save_and_load(tmp_path):
    """SkillManager can save to JSON and load it back."""
    persist = str(tmp_path / "skills.json")
    mgr = SkillManager(persist_path=persist)
    skill = Skill(name="saved", trigger_pattern="test", trigger_priority=1, steps=["go"])
    mgr.add_skill(skill)
    mgr.save()

    mgr2 = SkillManager(persist_path=persist)
    mgr2.load()
    assert "saved" in [s.name for s in mgr2.list_skills()]


# ---------------------------------------------------------------------------
# skill_from_spec factory
# ---------------------------------------------------------------------------

def test_skill_from_spec_dict_trigger():
    """skill_from_spec() handles dict trigger."""
    spec = {
        "name": "my_skill",
        "trigger": {"pattern": "test", "priority": 2},
        "steps": ["do something"],
        "status": "active",
    }
    skill = skill_from_spec(spec)
    assert skill.name == "my_skill"
    assert skill.trigger_pattern == "test"
    assert skill.trigger_priority == 2


def test_skill_from_spec_string_trigger():
    """skill_from_spec() handles plain string trigger."""
    spec = {
        "name": "str_skill",
        "trigger": "find|search",
        "steps": ["search step"],
    }
    skill = skill_from_spec(spec)
    assert skill.trigger_pattern == "find|search"


# ---------------------------------------------------------------------------
# LearningEngine
# ---------------------------------------------------------------------------

def _make_entry(session_id, outcome="success", messages=None):
    return SessionEntry(
        session_id=session_id,
        timestamp="2024-01-01T00:00:00Z",
        messages=messages or [{"role": "user", "content": "hello world"}],
        outcome=outcome,
    )


def test_record_session_adds_entry():
    """LearningEngine.record_session() appends to internal list."""
    engine = LearningEngine(mode="passive")
    entry = _make_entry("s1")
    engine.record_session(entry)
    assert len(engine._sessions) == 1


def test_search_sessions_finds_matching():
    """LearningEngine.search_sessions() returns sessions matching query."""
    engine = LearningEngine()
    engine.record_session(_make_entry("s1", messages=[{"role": "user", "content": "ark parser test"}]))
    engine.record_session(_make_entry("s2", messages=[{"role": "user", "content": "something else"}]))
    results = engine.search_sessions("ark")
    assert len(results) == 1
    assert results[0].session_id == "s1"


def test_search_sessions_empty_on_no_match():
    """LearningEngine.search_sessions() returns empty list when no match."""
    engine = LearningEngine()
    engine.record_session(_make_entry("s1", messages=[{"role": "user", "content": "hello"}]))
    results = engine.search_sessions("xxxxxxxx")
    assert results == []


def test_search_sessions_limit():
    """LearningEngine.search_sessions() respects the limit parameter."""
    engine = LearningEngine()
    for i in range(10):
        engine.record_session(_make_entry(f"s{i}", messages=[{"content": "test query"}]))
    results = engine.search_sessions("test", limit=3)
    assert len(results) <= 3


def test_generate_skill_from_trace():
    """LearningEngine.generate_skill_from_trace() returns a draft Skill."""
    engine = LearningEngine()
    sessions = [
        _make_entry("s1", messages=[{"content": "search the internet for python"}, {"content": "search the internet for python"}]),
        _make_entry("s2", messages=[{"content": "search the internet for python"}, {"content": "search the internet for python"}]),
    ]
    skill = engine.generate_skill_from_trace(sessions, "generated_skill")
    assert skill.name == "generated_skill"
    assert skill.status == "draft"
    assert isinstance(skill.trigger_pattern, str)
    assert isinstance(skill.steps, list)


def test_score_skill_all_success():
    """LearningEngine.score_skill() returns 1.0 when all matching sessions succeed."""
    engine = LearningEngine()
    sessions = [
        _make_entry("s1", outcome="success", messages=[{"content": "search foo"}]),
        _make_entry("s2", outcome="success", messages=[{"content": "search bar"}]),
    ]
    skill = Skill(name="s", trigger_pattern="search", trigger_priority=1, steps=[])
    score = engine.score_skill(skill, sessions)
    assert score == 1.0


def test_score_skill_no_sessions():
    """LearningEngine.score_skill() returns 0.0 for empty sessions list."""
    engine = LearningEngine()
    skill = Skill(name="s", trigger_pattern="search", trigger_priority=1, steps=[])
    score = engine.score_skill(skill, [])
    assert score == 0.0


def test_self_improve_loop_flags_underperformer():
    """LearningEngine.self_improve_loop() flags skills scoring below 0.5."""
    engine = LearningEngine()
    # Sessions that do NOT match the skill trigger
    sessions = [
        _make_entry("s1", outcome="failure", messages=[{"content": "unrelated topic"}]),
    ]
    mgr = SkillManager()
    skill = Skill(name="low_skill", trigger_pattern="search", trigger_priority=1, steps=["do"])
    mgr.add_skill(skill)
    suggestions = engine.self_improve_loop(mgr, sessions=sessions)
    assert len(suggestions) >= 1
    assert any(s["skill_name"] == "low_skill" for s in suggestions)


def test_learning_engine_save_and_load(tmp_path):
    """LearningEngine persists sessions to JSONL and loads them back."""
    persist = str(tmp_path / "sessions.jsonl")
    engine = LearningEngine(persist_path=persist)
    engine.record_session(_make_entry("persisted"))
    engine.save()

    engine2 = LearningEngine(persist_path=persist)
    engine2.load()
    assert len(engine2._sessions) == 1
    assert engine2._sessions[0].session_id == "persisted"


def test_learning_from_spec_factory():
    """learning_from_spec() builds a LearningEngine from spec dict."""
    spec = {"mode": "active"}
    engine = learning_from_spec(spec)
    assert isinstance(engine, LearningEngine)
    assert engine.mode == "active"
