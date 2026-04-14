"""Review Loop Orchestrator — coordinates visual review cycles via file-based JSON.

Implements a human-in-the-loop review mechanism:
  render artifact → create manifest → wait for feedback → parse result

Pipeline:  target_ast → render_fn → rendered_path
           → create_review_manifest() → {review_id}_manifest.json
           → wait_for_feedback() → parse_feedback() → result dict
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Union


# ============================================================
# ENUMS
# ============================================================

class FeedbackStatus(str, Enum):
    """Valid status values for a review feedback response."""
    PENDING           = "pending"
    APPROVED          = "approved"
    REJECTED          = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    ANNOTATED         = "annotated"


class TargetType(str, Enum):
    """Type of visual artifact under review."""
    DIAGRAM    = "diagram"
    PREVIEW    = "preview"
    SCREENSHOT = "screenshot"


# ============================================================
# DATACLASS
# ============================================================

@dataclass
class ReviewManifest:
    """Metadata for a single visual review cycle.

    Attributes:
        review_id:     UUID string uniquely identifying this review.
        target_name:   Name of the artifact being reviewed.
        target_type:   One of "diagram", "preview", or "screenshot".
        rendered_path: Absolute path to the rendered artifact file.
        feedback_path: Expected path where the human will write feedback JSON.
        status:        Current lifecycle status (default "pending").
        created_at:    ISO-8601 UTC timestamp when the manifest was created.
    """
    review_id:     str
    target_name:   str
    target_type:   str
    rendered_path: str
    feedback_path: str
    status:        str = "pending"
    created_at:    str = field(default_factory=lambda: _utcnow_iso())


# ============================================================
# FEEDBACK TEMPLATE
# ============================================================

FEEDBACK_TEMPLATE: dict = {
    "status":          FeedbackStatus.PENDING.value,
    "comments":        "",
    "annotations":     [],
    "change_requests": [],
}


# ============================================================
# PUBLIC API
# ============================================================

def create_review_manifest(
    target_ast: Union[dict, object],
    rendered_path: Union[str, Path],
    out_dir: Union[str, Path],
) -> dict:
    """Create a review manifest JSON file describing an artifact awaiting review.

    Args:
        target_ast:    Parsed target item from AST (dict or dataclass).
                       Expected keys/attrs: ``name``, ``type`` or ``target_type``.
        rendered_path: Path to the already-rendered artifact.
        out_dir:       Directory where the manifest file will be written.

    Returns:
        The manifest as a plain dict.  The file is written to
        ``out_dir/{review_id}_manifest.json``.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Extract fields from target_ast ---
    name        = _get(target_ast, "name") or "artifact"
    target_type = (
        _get(target_ast, "target_type")
        or _get(target_ast, "type")
        or TargetType.DIAGRAM.value
    )

    review_id     = str(uuid.uuid4())
    feedback_path = str(out_dir / f"{review_id}_feedback.json")

    manifest = ReviewManifest(
        review_id=review_id,
        target_name=name,
        target_type=str(target_type),
        rendered_path=str(Path(rendered_path).resolve()),
        feedback_path=feedback_path,
    )

    manifest_dict = _manifest_to_dict(manifest)

    manifest_path = out_dir / f"{review_id}_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest_dict, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return manifest_dict


def wait_for_feedback(
    manifest_path: Union[str, Path],
    timeout: Optional[float] = None,
) -> Optional[dict]:
    """Poll for a feedback file referenced in the manifest.

    Args:
        manifest_path: Path to the manifest JSON file produced by
                       :func:`create_review_manifest`.
        timeout:       Maximum seconds to wait.  ``None`` means check once
                       and return immediately (non-blocking).

    Returns:
        Parsed feedback dict if the feedback file exists and is valid JSON,
        or ``None`` if no feedback was found within the timeout window.
    """
    manifest_path = Path(manifest_path)

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    feedback_path = Path(manifest_data["feedback_path"])

    if timeout is None:
        # Single non-blocking check
        if feedback_path.exists():
            return _read_json(feedback_path)
        return None

    # Polling loop
    poll_interval = 1.0  # seconds
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if feedback_path.exists():
            return _read_json(feedback_path)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(poll_interval, remaining))

    return None


def parse_feedback(feedback_json: Union[str, dict, Path]) -> dict:
    """Parse and normalise a feedback payload.

    Accepts:
    - A dict (already parsed JSON)
    - A JSON string
    - A Path pointing to a JSON file

    Args:
        feedback_json: Feedback data in one of the accepted forms.

    Returns:
        Normalised dict with keys:
            ``status``          (str, validated FeedbackStatus value),
            ``comments``        (str),
            ``annotations``     (list),
            ``change_requests`` (list).

    Raises:
        ValueError: If ``status`` is not a recognised :class:`FeedbackStatus`.
    """
    if isinstance(feedback_json, Path):
        raw = json.loads(feedback_json.read_text(encoding="utf-8"))
    elif isinstance(feedback_json, str):
        raw = json.loads(feedback_json)
    else:
        raw = feedback_json

    status_raw = raw.get("status", FeedbackStatus.PENDING.value)

    # Validate against FeedbackStatus enum
    valid_values = {s.value for s in FeedbackStatus}
    if status_raw not in valid_values:
        raise ValueError(
            f"Unknown feedback status '{status_raw}'. "
            f"Expected one of: {sorted(valid_values)}"
        )

    return {
        "status":          status_raw,
        "comments":        raw.get("comments", ""),
        "annotations":     list(raw.get("annotations", [])),
        "change_requests": list(raw.get("change_requests", [])),
    }


def run_review(
    target_ast: Union[dict, object],
    render_fn: Callable[[Union[dict, object], Path], Union[str, Path]],
    out_dir: Union[str, Path],
) -> dict:
    """Orchestrate a full visual review cycle.

    Steps:
    1. Render the target artifact via ``render_fn``.
    2. Create a review manifest in ``out_dir``.
    3. Check once (non-blocking) for an existing feedback file.
    4. Return the result dict.

    Args:
        target_ast: Parsed visual target item from the ARK AST.
        render_fn:  Callable ``(target_ast, out_dir) -> rendered_path``.
                    Must return the path to the rendered artifact.
        out_dir:    Directory for all review files (manifest + feedback).

    Returns:
        {
            "review_id":     str — UUID of this review cycle,
            "manifest_path": Path — path to the written manifest JSON,
            "status":        str — current review status,
            "feedback":      dict | None — parsed feedback or None,
        }
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Render
    rendered_path = render_fn(target_ast, out_dir)

    # Step 2: Create manifest
    manifest = create_review_manifest(target_ast, rendered_path, out_dir)
    review_id     = manifest["review_id"]
    manifest_path = out_dir / f"{review_id}_manifest.json"

    # Step 3: Non-blocking feedback check
    feedback = wait_for_feedback(manifest_path, timeout=None)

    parsed_feedback: Optional[dict] = None
    if feedback is not None:
        try:
            parsed_feedback = parse_feedback(feedback)
        except (ValueError, json.JSONDecodeError):
            parsed_feedback = None

    status = parsed_feedback["status"] if parsed_feedback else FeedbackStatus.PENDING.value

    return {
        "review_id":     review_id,
        "manifest_path": manifest_path,
        "status":        status,
        "feedback":      parsed_feedback,
    }


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _get(obj: object, key: str, default=None):
    """Retrieve a field from either a dict or a dataclass/object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _manifest_to_dict(m: ReviewManifest) -> dict:
    """Serialise a ReviewManifest dataclass to a plain dict."""
    return {
        "review_id":     m.review_id,
        "target_name":   m.target_name,
        "target_type":   m.target_type,
        "rendered_path": m.rendered_path,
        "feedback_path": m.feedback_path,
        "status":        m.status,
        "created_at":    m.created_at,
    }


def _read_json(path: Path) -> Optional[dict]:
    """Read and parse a JSON file, returning None on error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _utcnow_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
