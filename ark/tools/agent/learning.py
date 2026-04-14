"""
learning.py — Session memory, skill generation, and self-improvement scoring.

Provides:
  - SessionEntry dataclass
  - LearningEngine class
  - learning_from_spec() factory
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

from skill_manager import Skill, SkillManager


# ---------------------------------------------------------------------------
# SessionEntry
# ---------------------------------------------------------------------------


@dataclass
class SessionEntry:
    """One recorded interaction session."""

    session_id: str
    timestamp: str
    messages: list[dict] = field(default_factory=list)
    skills_used: list[str] = field(default_factory=list)
    outcome: str = "success"   # "success" | "failure" | "partial"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "SessionEntry":
        return SessionEntry(
            session_id=d["session_id"],
            timestamp=d["timestamp"],
            messages=d.get("messages", []),
            skills_used=d.get("skills_used", []),
            outcome=d.get("outcome", "success"),
            metadata=d.get("metadata", {}),
        )

    # ------------------------------------------------------------------
    # Text helpers for search
    # ------------------------------------------------------------------

    def _text_blob(self) -> str:
        """Concatenate all searchable text in the session into one string."""
        parts: list[str] = [self.outcome]
        for msg in self.messages:
            if isinstance(msg, dict):
                parts.extend(str(v) for v in msg.values())
            else:
                parts.append(str(msg))
        return " ".join(parts).lower()


# ---------------------------------------------------------------------------
# LearningEngine
# ---------------------------------------------------------------------------


class LearningEngine:
    """Records sessions, searches past interactions, and generates skills.

    Modes
    -----
    passive    — only records sessions (no auto-generation)
    active     — records and generates skills on demand
    autonomous — records, generates, and self-improves automatically
    """

    def __init__(
        self,
        persist_path: Optional[str] = None,
        mode: str = "passive",
    ) -> None:
        self.mode: str = mode
        self._sessions: list[SessionEntry] = []
        self.persist_path: Optional[Path] = (
            Path(persist_path) if persist_path else None
        )

    # ------------------------------------------------------------------
    # Session recording
    # ------------------------------------------------------------------

    def record_session(self, entry: SessionEntry) -> None:
        """Append *entry* to the in-memory list and the JSONL file (if configured)."""
        self._sessions.append(entry)
        if self.persist_path is not None:
            self._append_jsonl(entry)

    def _append_jsonl(self, entry: SessionEntry) -> None:
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        with self.persist_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_sessions(
        self,
        query: str,
        limit: int = 10,
    ) -> list[SessionEntry]:
        """Keyword search over session messages and outcome.

        Returns up to *limit* entries sorted by relevance (count of
        *query* occurrences across all text fields, descending).
        Comparisons are case-insensitive.
        """
        query_lower = query.lower()
        scored: list[tuple[int, SessionEntry]] = []

        for entry in self._sessions:
            blob = entry._text_blob()
            count = blob.count(query_lower)
            if count > 0:
                scored.append((count, entry))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

    # ------------------------------------------------------------------
    # Skill generation from trace
    # ------------------------------------------------------------------

    def generate_skill_from_trace(
        self,
        sessions: list[SessionEntry],
        skill_name: str,
    ) -> Skill:
        """Analyse *sessions* and build a Skill from frequent action patterns.

        Algorithm
        ---------
        1. Collect every message ``content`` string from all sessions.
        2. Tokenise each message into words and count word frequencies.
        3. Pick the top N words as the trigger pattern.
        4. Extract repeated full-message strings as skill steps.
        5. Return a Skill (status="draft") with those steps.
        """
        all_message_texts: list[str] = []
        step_counter: Counter[str] = Counter()

        for session in sessions:
            for msg in session.messages:
                text: str = ""
                if isinstance(msg, dict):
                    text = str(msg.get("content", "") or msg.get("text", "") or "")
                else:
                    text = str(msg)
                if text:
                    all_message_texts.append(text)
                    step_counter[text.strip()] += 1

        # Steps = messages that appear more than once, sorted by frequency desc.
        repeated: list[str] = [
            text for text, count in step_counter.most_common()
            if count > 1
        ]

        # If nothing repeats, fall back to all unique messages (first session).
        if not repeated and sessions:
            first = sessions[0]
            for msg in first.messages:
                if isinstance(msg, dict):
                    t = str(msg.get("content", "") or msg.get("text", "") or "")
                else:
                    t = str(msg)
                if t.strip():
                    repeated.append(t.strip())

        # Build trigger pattern from the most common words across all messages.
        word_counter: Counter[str] = Counter()
        for text in all_message_texts:
            for word in re.findall(r"\w+", text.lower()):
                word_counter[word] += 1

        top_words = [w for w, _ in word_counter.most_common(5) if len(w) > 3]
        if top_words:
            trigger_pattern = "|".join(re.escape(w) for w in top_words[:3])
        else:
            trigger_pattern = ".*"

        return Skill(
            name=skill_name,
            trigger_pattern=trigger_pattern,
            trigger_priority=0,
            steps=repeated or ["(no steps extracted)"],
            status="draft",
            improvement_history=[],
            description=(
                f"Auto-generated from {len(sessions)} session(s). "
                f"Trigger words: {top_words[:3]}"
            ),
        )

    # ------------------------------------------------------------------
    # Skill scoring
    # ------------------------------------------------------------------

    def score_skill(
        self,
        skill: Skill,
        sessions: list[SessionEntry],
    ) -> float:
        """Score how well *skill* matches session outcomes.

        Score = fraction of sessions where:
          - the skill trigger pattern matches at least one message, AND
          - the session outcome is "success".

        Returns a float in [0.0, 1.0].  Returns 0.0 if *sessions* is empty.
        """
        if not sessions:
            return 0.0

        try:
            pattern = re.compile(skill.trigger_pattern, re.IGNORECASE)
        except re.error:
            return 0.0

        hits = 0
        for session in sessions:
            blob = session._text_blob()
            if pattern.search(blob) and session.outcome == "success":
                hits += 1

        return round(hits / len(sessions), 6)

    # ------------------------------------------------------------------
    # Self-improvement loop
    # ------------------------------------------------------------------

    def self_improve_loop(
        self,
        skill_manager: SkillManager,
        sessions: Optional[list[SessionEntry]] = None,
    ) -> list[dict]:
        """Score all active skills; flag underperformers for improvement.

        For each active skill:
          - Score it against *sessions* (or self._sessions if not provided).
          - If score < 0.5, mark it for improvement and record a suggestion.

        Returns a list of suggestion dicts with keys:
          skill_name, score, suggestion.
        """
        working_sessions = sessions if sessions is not None else self._sessions
        suggestions: list[dict] = []

        for skill in skill_manager.list_skills(status="active"):
            score = self.score_skill(skill, working_sessions)
            if score < 0.5:
                suggestion: dict[str, Any] = {
                    "skill_name": skill.name,
                    "score": score,
                    "suggestion": (
                        f"Skill '{skill.name}' scored {score:.2f} — below 0.5 threshold. "
                        "Consider revising trigger pattern or steps."
                    ),
                }
                suggestions.append(suggestion)

                # Record improvement event in the skill itself.
                skill_manager.improve_skill(
                    name=skill.name,
                    old_score=score,
                    new_score=score,  # Not yet changed — flagged only.
                    summary=suggestion["suggestion"],
                )

        return suggestions

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Write all in-memory sessions to the JSONL file at *persist_path*.

        Overwrites any existing file.  Raises RuntimeError if persist_path
        is not configured.
        """
        if self.persist_path is None:
            raise RuntimeError("persist_path is not configured")
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        with self.persist_path.open("w", encoding="utf-8") as fh:
            for entry in self._sessions:
                fh.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def load(self) -> None:
        """Load sessions from the JSONL file at *persist_path*.

        Clears the current in-memory list and replaces it with the loaded
        data.  Raises RuntimeError if persist_path is not configured.
        """
        if self.persist_path is None:
            raise RuntimeError("persist_path is not configured")
        if not self.persist_path.exists():
            return  # Nothing to load yet.
        self._sessions = []
        with self.persist_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    self._sessions.append(SessionEntry.from_dict(json.loads(line)))


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def learning_from_spec(spec: dict) -> LearningEngine:
    """Build a LearningEngine from a parsed spec dict.

    Expected spec keys:
      persist_path  — path to the JSONL file (optional)
      mode          — "passive" | "active" | "autonomous" (default: "passive")
    """
    persist_path: Optional[str] = spec.get("persist_path", None)
    mode: str = spec.get("mode", "passive")
    return LearningEngine(persist_path=persist_path, mode=mode)
