# Skill and Learning System — Design

## Overview
Implement `tools/agent/skill_manager.py` and `tools/agent/learning.py` — the procedural knowledge system. Skills are triggered by patterns, execute steps, and improve over time. The learning system generates skills from execution traces, scores them, and persists knowledge.

## Target Files
- `ark/tools/agent/skill_manager.py` — Skill CRUD, trigger matching, improvement loop
- `ark/tools/agent/learning.py` — Session memory, skill generation, self-improvement scoring

## Approach

### Skill Manager

```python
@dataclass
class Skill:
    name: str
    trigger: SkillTrigger
    steps: list[str]
    status: str           # Draft, Active, Improving, Deprecated
    improvement_history: list[dict]
    version: int
    score: float          # 0.0 - 1.0 quality score

class SkillManager:
    def __init__(self, skills: list[Skill]):
        self._skills = {s.name: s for s in skills}
    
    def match_trigger(self, context: str) -> list[Skill]:
        """Find skills whose trigger matches the context, ordered by priority."""
        ...
    
    def execute_skill(self, skill: Skill, context: dict) -> dict:
        """Execute skill steps in sequence, return results."""
        ...
    
    def add_skill(self, skill: Skill):
        """Register a new skill."""
        ...
    
    def improve_skill(self, name: str, feedback: dict) -> Skill:
        """Record improvement, bump version, update score."""
        ...
    
    def deprecate_skill(self, name: str):
        """Mark skill as deprecated."""
        ...
```

### Trigger Matching
- Regex-based pattern matching on context strings
- Priority ordering: higher priority triggers match first
- Ambiguity detection: warn if two skills match with equal priority

### Learning System

```python
@dataclass
class SessionEntry:
    timestamp: float
    context: str
    action: str
    result: str
    score: float

class LearningEngine:
    def __init__(self, mode: str, config: dict):
        self.mode = mode  # Passive, Active, Autonomous
        self._sessions: list[SessionEntry] = []
        self._skill_manager: SkillManager = None
    
    def record_session(self, entry: SessionEntry):
        """Persist session entry for learning."""
        ...
    
    def search_sessions(self, query: str, limit: int = 10) -> list[SessionEntry]:
        """Search past sessions for contextual understanding."""
        ...
    
    def generate_skill_from_trace(self, trace: list[SessionEntry]) -> Skill:
        """Analyze execution trace, extract procedural knowledge as skill."""
        ...
    
    def score_skill(self, skill: Skill, test_cases: list[dict]) -> float:
        """Score skill quality against test cases."""
        ...
    
    def self_improve_loop(self, skill: Skill) -> Skill:
        """Run one improvement iteration on a skill."""
        ...
```

### Persistence
- Skills stored as JSON files in a configurable directory
- Session entries stored as JSONL (one entry per line)
- Improvement history embedded in skill JSON

### Integration with Specs
```python
def skill_from_spec(skill_def: dict) -> Skill:
    """Build Skill from parsed skill_def."""

def learning_from_spec(learning_def: dict, skill_mgr: SkillManager) -> LearningEngine:
    """Build LearningEngine from parsed learning_config_def."""
```

### Design Decisions
- Trigger matching uses regex for flexibility, priority for disambiguation
- Skill generation from traces is a heuristic: extract repeated action sequences
- Self-improvement is iterative: each loop bumps version, may improve or deprecate
- v1 learning is file-based (no database dependency)
- LearningMode controls automation level: Passive only records, Active generates, Autonomous improves

## Dependencies
- design-dsl-surface (skill_def, learning_config_def must be parseable)
- design-stdlib-agent-schema (SkillStatus, LearningMode, SkillTrigger)

## Target Conditions
- TC-014: SkillManager matches triggers correctly with priority ordering
- TC-015: SkillManager CRUD operations (add, improve, deprecate) work correctly
- TC-016: LearningEngine records sessions and searches by query
- TC-017: LearningEngine generates a skill from an execution trace
