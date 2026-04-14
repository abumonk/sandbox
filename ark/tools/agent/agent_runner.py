"""
agent_runner.py — Orchestrator for agent lifecycle: init, listen, process, learn, persist.

Wires together gateway, backends, skills, learning, and scheduler into a coherent
agent runtime.  AgentRunner is the single entry point; all subsystems are injected.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from gateway import Gateway, Message, gateway_from_spec
from backend import ExecutionBackend, backend_from_spec
from skill_manager import Skill, SkillManager, skill_from_spec
from learning import LearningEngine, SessionEntry, learning_from_spec
from scheduler import Scheduler, scheduler_from_spec


# ---------------------------------------------------------------------------
# AgentConfig
# ---------------------------------------------------------------------------

@dataclass
class AgentConfig:
    """Static configuration for an agent."""
    name: str
    persona: str
    model_config: dict
    capabilities: list[str]
    learning_mode: str  # "passive" | "active" | "proactive"


# ---------------------------------------------------------------------------
# AgentRunner
# ---------------------------------------------------------------------------

class AgentRunner:
    """
    Top-level agent runtime.

    Responsibilities:
    - Initialise all subsystems and load persisted state.
    - Process incoming messages: skill-first, model-fallback.
    - Run periodic scheduler ticks.
    - Persist state on demand or at shutdown.
    """

    def __init__(
        self,
        config: AgentConfig,
        gateway: Gateway,
        backend: ExecutionBackend,
        skill_manager: SkillManager,
        learning: LearningEngine,
        scheduler: Scheduler,
    ) -> None:
        self.config = config
        self.gateway = gateway
        self.backend = backend
        self.skills = skill_manager
        self.learning = learning
        self.scheduler = scheduler
        self._running: bool = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def init(self) -> None:
        """Initialize all subsystems and load persisted state from skills/learning."""
        # Load persisted skills (silently skip if persist_path not configured)
        try:
            self.skills.load()
        except RuntimeError:
            pass

        # Load persisted learning sessions (silently skip if persist_path not set)
        try:
            self.learning.load()
        except RuntimeError:
            pass

        self._running = True

    def persist(self) -> None:
        """Save all state: skills and learning sessions."""
        try:
            self.skills.save()
        except RuntimeError:
            pass

        try:
            self.learning.save()
        except RuntimeError:
            pass

    def shutdown(self) -> None:
        """Graceful shutdown: persist state and stop the run loop."""
        self.persist()
        self._running = False

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    def process_message(self, message: Message) -> Message:
        """
        Core processing loop.

        1. Check skill triggers via self.skills.match_trigger(message.content).
        2. If a skill matched, execute its steps via the backend and build response.
        3. If no skill matched, build a model prompt and return a placeholder response.
        4. Record the session for learning.
        5. If learning_mode is "active" or "proactive", attempt skill generation from
           recent sessions.
        """
        skill_used: Optional[str] = None
        response_content: str

        # 1 & 2 — skill-first path
        matches = self.skills.match_trigger(message.content)
        if matches:
            best_skill, _match = matches[0]
            skill_used = best_skill.name
            context = {
                "sender": message.sender,
                "content": message.content,
                "platform": message.platform,
            }
            # Build the skill execution plan and optionally run it on the backend
            execution_plan = self.skills.execute_skill(best_skill, context)
            # Run the plan as a command on the backend (best-effort)
            try:
                result = self.backend.execute(execution_plan, timeout=30)
                if result.exit_code == 0 and result.stdout.strip():
                    response_content = result.stdout.strip()
                else:
                    response_content = execution_plan
            except Exception:
                response_content = execution_plan
        else:
            # 3 — model fallback
            prompt = self._build_model_prompt(message)
            response_content = f"[model response for: {prompt}]"

        # 4 — record session for learning
        session_entry = SessionEntry(
            session_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            messages=[
                {"role": "user", "content": message.content},
                {"role": "agent", "content": response_content},
            ],
            skills_used=[skill_used] if skill_used else [],
            outcome="success",
            metadata={"platform": message.platform, "sender": message.sender},
        )
        self.learning.record_session(session_entry)

        # 5 — attempt skill generation in active/proactive modes
        if self.config.learning_mode in ("active", "proactive"):
            self._attempt_skill_generation()

        # Build and return the response Message
        response = Message(
            id=str(uuid.uuid4()),
            platform=message.platform,
            sender=self.config.name,
            content=response_content,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"in_reply_to": message.id},
        )
        return response

    def _build_model_prompt(self, message: Message) -> str:
        """Construct the prompt string to pass to a language model."""
        lines = [
            f"Agent: {self.config.name}",
            f"Persona: {self.config.persona}",
            f"Message from {message.sender}: {message.content}",
        ]
        return "\n".join(lines)

    def _attempt_skill_generation(self) -> None:
        """Try to generate a new skill from recent learning sessions.

        Generates a draft skill if there are at least 2 recorded sessions.
        The draft is added to the skill registry with status="draft".
        """
        recent = self.learning._sessions[-10:] if self.learning._sessions else []
        if len(recent) < 2:
            return
        candidate_name = f"auto_skill_{len(self.skills.list_skills())}"
        try:
            new_skill = self.learning.generate_skill_from_trace(recent, candidate_name)
            self.skills.add_skill(new_skill)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Scheduler tick
    # ------------------------------------------------------------------

    def tick(self, now: float) -> None:
        """
        Periodic tick.

        Converts the POSIX timestamp *now* to a datetime and delegates to
        self.scheduler.tick().  Also runs maintenance (best-effort persist).
        """
        dt = datetime.utcfromtimestamp(now)
        self.scheduler.tick(dt)
        # Maintenance: persist state periodically
        self.persist()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_agent_runtime(agent_def: dict, specs: dict) -> AgentRunner:
    """
    Build a complete AgentRunner from a parsed agent_def and related specs.

    Parameters
    ----------
    agent_def : dict
        The parsed agent definition block.  Expected keys (all optional):
          name            — agent name
          persona         — agent persona string
          model           — key into specs["model_configs"] (or inline dict)
          learning        — key into specs["learning_configs"] (or inline dict)
          backends        — list of backend_type keys or inline backend spec dicts
          capabilities    — list of capability strings
          learning_mode   — "passive" | "active" | "proactive"

    specs : dict
        A registry of pre-parsed spec dicts keyed by category.  Expected keys:
          "model_configs"    — dict mapping name -> model_config dict
          "learning_configs" — dict mapping name -> learning spec dict
          "backend_defs"     — dict mapping name -> backend spec dict
          "gateway_specs"    — dict mapping agent_name -> gateway spec dict
          "skill_defs"       — list of skill spec dicts
          "cron_tasks"       — list of cron task spec dicts (filtered to this agent)

    Returns
    -------
    AgentRunner
        Fully wired agent runtime, ready to call .init() on.
    """
    agent_name: str = agent_def.get("name", "agent")

    # -- Model config -------------------------------------------------------
    model_ref = agent_def.get("model", {})
    if isinstance(model_ref, str):
        model_config = specs.get("model_configs", {}).get(model_ref, {})
    else:
        model_config = model_ref or {}

    # -- Learning config / mode ---------------------------------------------
    learning_ref = agent_def.get("learning", {})
    if isinstance(learning_ref, str):
        learning_spec = specs.get("learning_configs", {}).get(learning_ref, {})
    else:
        learning_spec = learning_ref or {}

    learning_mode: str = agent_def.get(
        "learning_mode",
        learning_spec.get("mode", "passive"),
    )
    # Ensure the spec carries the resolved mode
    learning_spec = dict(learning_spec)
    learning_spec.setdefault("mode", learning_mode)

    learning_engine = learning_from_spec(learning_spec)

    # -- Execution backend --------------------------------------------------
    backend_refs = agent_def.get("backends", [])
    backend_spec: dict = {}
    if backend_refs:
        first_ref = backend_refs[0]
        if isinstance(first_ref, str):
            backend_spec = specs.get("backend_defs", {}).get(first_ref, {"backend_type": "Local"})
        elif isinstance(first_ref, dict):
            backend_spec = first_ref
    if not backend_spec:
        backend_spec = {"backend_type": "Local"}
    backend = backend_from_spec(backend_spec)

    # -- Gateway ------------------------------------------------------------
    gateway_spec = specs.get("gateway_specs", {}).get(agent_name, {"name": agent_name, "routes": []})
    gateway = gateway_from_spec(gateway_spec)

    # -- Skills -------------------------------------------------------------
    raw_skill_defs = specs.get("skill_defs", [])
    skills: list[Skill] = []
    for sdef in raw_skill_defs:
        if isinstance(sdef, dict):
            # Filter to skills that belong to this agent (if agent_ref present)
            if "agent_ref" in sdef and sdef["agent_ref"] != agent_name:
                continue
            skills.append(skill_from_spec(sdef))
    skill_manager = SkillManager(skills=skills)

    # -- Scheduler ----------------------------------------------------------
    raw_cron_tasks = specs.get("cron_tasks", [])
    # Filter to tasks referencing this agent
    agent_cron_tasks = [
        t for t in raw_cron_tasks
        if isinstance(t, dict) and t.get("agent_ref", agent_name) == agent_name
    ]
    scheduler = scheduler_from_spec(agent_cron_tasks)

    # -- AgentConfig --------------------------------------------------------
    capabilities: list[str] = agent_def.get("capabilities", [])
    persona: str = agent_def.get("persona", "")

    config = AgentConfig(
        name=agent_name,
        persona=persona,
        model_config=model_config,
        capabilities=capabilities,
        learning_mode=learning_mode,
    )

    return AgentRunner(
        config=config,
        gateway=gateway,
        backend=backend,
        skill_manager=skill_manager,
        learning=learning_engine,
        scheduler=scheduler,
    )
