"""
skill_manager.py — Skill CRUD, trigger matching, and improvement tracking.

Provides:
  - Skill dataclass
  - SkillTrigger dataclass
  - SkillManager class
  - skill_from_spec() factory
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


@dataclass
class SkillTrigger:
    """Regex pattern and dispatch priority for a skill."""
    pattern: str
    priority: int = 0

    def compiled(self) -> re.Pattern:
        return re.compile(self.pattern, re.IGNORECASE)


@dataclass
class Skill:
    """A single reusable procedural unit triggered by a pattern."""
    name: str
    trigger_pattern: str
    trigger_priority: int
    steps: list[str]
    status: str = "active"           # active | deprecated | draft | archived
    improvement_history: list[dict] = field(default_factory=list)
    description: str = ""

    # Convenience accessor – build a SkillTrigger from the stored fields.
    @property
    def trigger(self) -> SkillTrigger:
        return SkillTrigger(pattern=self.trigger_pattern, priority=self.trigger_priority)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Skill":
        return Skill(
            name=d["name"],
            trigger_pattern=d["trigger_pattern"],
            trigger_priority=d.get("trigger_priority", 0),
            steps=d.get("steps", []),
            status=d.get("status", "active"),
            improvement_history=d.get("improvement_history", []),
            description=d.get("description", ""),
        )


class SkillManager:
    """Manages the skill registry: CRUD, trigger matching, persistence."""

    def __init__(
        self,
        skills: Optional[list[Skill]] = None,
        persist_path: Optional[str] = None,
    ):
        self._skills: dict[str, Skill] = {}
        if skills:
            for skill in skills:
                self._skills[skill.name] = skill
        self.persist_path: Optional[Path] = (
            Path(persist_path) if persist_path else None
        )

    # ------------------------------------------------------------------
    # Trigger matching
    # ------------------------------------------------------------------

    def match_trigger(self, input_text: str) -> list[tuple[Skill, re.Match]]:
        """Return (skill, match) tuples for all active skills whose trigger
        pattern matches *input_text*, sorted by priority descending."""
        results: list[tuple[Skill, re.Match]] = []
        for skill in self._skills.values():
            if skill.status != "active":
                continue
            try:
                m = re.search(skill.trigger_pattern, input_text, re.IGNORECASE)
                if m:
                    results.append((skill, m))
            except re.error:
                # Silently skip malformed patterns.
                pass
        results.sort(key=lambda pair: pair[0].trigger_priority, reverse=True)
        return results

    # ------------------------------------------------------------------
    # Skill execution (simplified)
    # ------------------------------------------------------------------

    def execute_skill(self, skill: Skill, context: dict) -> str:
        """Execute a skill by formatting its steps into a structured string.

        In this simplified implementation the 'execution' is a formatted
        plan that a caller or AI layer can act on.  Each step is numbered.
        The *context* dict values are available for {key} substitution.
        """
        lines = [f"Executing skill: {skill.name}"]
        for i, step in enumerate(skill.steps, start=1):
            try:
                formatted = step.format(**context)
            except KeyError:
                formatted = step
            lines.append(f"  {i}. {formatted}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_skill(self, skill: Skill) -> None:
        """Add (or replace) a skill in the registry."""
        self._skills[skill.name] = skill

    def update_skill(self, name: str, **kwargs: Any) -> Skill:
        """Update arbitrary fields on an existing skill.

        Raises KeyError if the skill does not exist.
        """
        skill = self.get_skill(name)
        for key, value in kwargs.items():
            if not hasattr(skill, key):
                raise AttributeError(f"Skill has no attribute '{key}'")
            setattr(skill, key, value)
        return skill

    def remove_skill(self, name: str) -> None:
        """Remove a skill by name.  Silent if not found."""
        self._skills.pop(name, None)

    def get_skill(self, name: str) -> Skill:
        """Retrieve a skill by name.  Raises KeyError if absent."""
        if name not in self._skills:
            raise KeyError(f"Skill '{name}' not found")
        return self._skills[name]

    def list_skills(self, status: Optional[str] = None) -> list[Skill]:
        """Return all skills, optionally filtered by status."""
        skills = list(self._skills.values())
        if status is not None:
            skills = [s for s in skills if s.status == status]
        return skills

    # ------------------------------------------------------------------
    # Improvement tracking
    # ------------------------------------------------------------------

    def improve_skill(
        self,
        name: str,
        old_score: float,
        new_score: float,
        summary: str,
    ) -> Skill:
        """Record an improvement event in the skill's history.

        Appends a dict with old_score, new_score, summary, and delta.
        Returns the updated Skill.
        """
        skill = self.get_skill(name)
        entry = {
            "old_score": old_score,
            "new_score": new_score,
            "delta": round(new_score - old_score, 6),
            "summary": summary,
        }
        skill.improvement_history.append(entry)
        return skill

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist all skills to the JSON file at *persist_path*.

        Raises RuntimeError if persist_path is not set.
        """
        if self.persist_path is None:
            raise RuntimeError("persist_path is not configured")
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        data = {name: skill.to_dict() for name, skill in self._skills.items()}
        with self.persist_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)

    def load(self) -> None:
        """Load skills from the JSON file at *persist_path*.

        Clears the current registry and replaces it with the loaded data.
        Raises RuntimeError if persist_path is not set.
        """
        if self.persist_path is None:
            raise RuntimeError("persist_path is not configured")
        if not self.persist_path.exists():
            return  # Nothing to load yet; this is not an error.
        with self.persist_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        self._skills = {name: Skill.from_dict(d) for name, d in data.items()}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def skill_from_spec(spec: dict) -> Skill:
    """Build a Skill from a parsed AST spec dict (e.g. from ark_parser).

    Expected spec keys (loosely matched):
      name          — skill identifier (required)
      trigger       — dict with 'pattern' and optional 'priority'
                      OR a plain string pattern
      steps         — list of step strings
      status        — one of active/deprecated/draft/archived (default: active)
      description   — human-readable description (optional)
      improvement_history — list of history dicts (optional)
    """
    name: str = spec.get("name", "unnamed_skill")

    # Resolve trigger — may be a dict or a plain string.
    raw_trigger = spec.get("trigger", {})
    if isinstance(raw_trigger, dict):
        trigger_pattern: str = raw_trigger.get("pattern", ".*")
        trigger_priority: int = int(raw_trigger.get("priority", 0))
    elif isinstance(raw_trigger, str):
        trigger_pattern = raw_trigger
        trigger_priority = int(spec.get("trigger_priority", 0))
    else:
        trigger_pattern = ".*"
        trigger_priority = 0

    # Fall back to top-level keys for flat spec layouts.
    if "trigger_pattern" in spec and not raw_trigger:
        trigger_pattern = spec["trigger_pattern"]
    if "trigger_priority" in spec and not isinstance(raw_trigger, dict):
        trigger_priority = int(spec["trigger_priority"])

    steps: list[str] = spec.get("steps", [])
    if isinstance(steps, str):
        steps = [steps]

    status: str = spec.get("status", "active")
    description: str = spec.get("description", "")
    improvement_history: list[dict] = spec.get("improvement_history", [])

    return Skill(
        name=name,
        trigger_pattern=trigger_pattern,
        trigger_priority=trigger_priority,
        steps=steps,
        status=status,
        improvement_history=improvement_history,
        description=description,
    )
