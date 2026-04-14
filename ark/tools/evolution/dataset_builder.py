"""Dataset builder for evaluation framework.

Generates evaluation datasets from various sources:
- Synthetic generation from file content (template-based, no LLM)
- Golden set loading from hand-curated JSONL files
- Split assignment with deterministic shuffling
"""
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_dataset(eval_dataset_spec: dict, seed: int = 42) -> list[dict]:
    """Main entry point — build a dataset from an eval_dataset spec.

    The spec dict should contain:
        source      : str — "synthetic" | "golden"
        path        : str — file path for synthetic source or JSONL path for golden
        num_cases   : int — number of synthetic cases (ignored for golden)
        splits      : dict — {"train": 0.7, "val": 0.15, "test": 0.15}

    Returns a flat list of case dicts, each containing a "split" key.
    """
    source = eval_dataset_spec.get("source", "synthetic")
    splits = eval_dataset_spec.get("splits", {"train": 0.7, "val": 0.15, "test": 0.15})

    if source == "synthetic":
        path = eval_dataset_spec.get("path", "")
        num_cases = int(eval_dataset_spec.get("num_cases", 10))
        try:
            file_content = Path(path).read_text(encoding="utf-8") if path else ""
        except (OSError, FileNotFoundError):
            file_content = ""
        cases = generate_synthetic(file_content, num_cases=num_cases, seed=seed)
    elif source == "golden":
        path = eval_dataset_spec.get("path", "")
        cases = load_golden(path)
    else:
        raise ValueError(f"Unknown dataset source: {source!r}. Expected 'synthetic' or 'golden'.")

    split_map = assign_splits(cases, splits, seed=seed)

    # Flatten back to a single list, annotating each case with its split
    result: list[dict] = []
    for split_name, split_cases in split_map.items():
        for case in split_cases:
            annotated = dict(case)
            annotated["split"] = split_name
            result.append(annotated)

    return result


def generate_synthetic(file_content: str, num_cases: int = 10, seed: int = 42) -> list[dict]:
    """Create template test cases by extracting sections/paragraphs from content.

    Generation is fully deterministic: case IDs and content are derived from
    the content hash and case index so the same inputs always produce the same
    output regardless of environment.

    Each returned dict contains:
        id              : str  — stable identifier for this case
        input           : str  — a prompt/question derived from the content
        expected_output : str  — expected answer / behaviour (template placeholder)
        context         : str  — excerpt of the source material used
        source          : str  — "synthetic"
    """
    segments = _extract_segments(file_content)
    content_hash = hashlib.sha256(file_content.encode("utf-8")).hexdigest()[:8]

    rng = random.Random(seed)

    cases: list[dict] = []
    for i in range(num_cases):
        # Pick a segment deterministically
        if segments:
            segment = segments[i % len(segments)]
        else:
            segment = f"(no content — case {i})"

        # Build a stable case ID from content hash + index
        case_id = f"syn-{content_hash}-{i:04d}"

        # Generate a simple input prompt from the segment
        first_sentence = _first_sentence(segment)
        input_text = f"Given the following context, describe what it represents:\n\n{first_sentence}"

        # The expected_output is a template: fill-in-the-blank style
        expected_output = f"[EXPECTED: describe '{_short_label(segment, rng)}' in 1-2 sentences]"

        cases.append({
            "id": case_id,
            "input": input_text,
            "expected_output": expected_output,
            "context": segment,
            "source": "synthetic",
        })

    return cases


def load_golden(jsonl_path: str) -> list[dict]:
    """Read a JSONL file and return a list of case dicts.

    Each line must be a valid JSON object. Lines that are blank or start with
    '#' are skipped.  Raises ValueError if a line cannot be parsed as JSON.
    """
    path = Path(jsonl_path)
    cases: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {lineno} of {jsonl_path!r}: {exc}"
                ) from exc
            if not isinstance(obj, dict):
                raise ValueError(
                    f"Expected JSON object on line {lineno} of {jsonl_path!r}, got {type(obj).__name__}"
                )
            cases.append(obj)
    return cases


def assign_splits(
    cases: list[dict],
    splits_dict: dict[str, float],
    seed: int = 42,
) -> dict[str, list[dict]]:
    """Distribute cases into train/val/test (or custom) splits.

    Args:
        cases:       List of case dicts to distribute.
        splits_dict: Mapping from split name to fraction, e.g.
                     {"train": 0.7, "val": 0.15, "test": 0.15}.
                     Fractions must sum to approximately 1.0.
        seed:        Random seed for deterministic shuffling.

    Returns:
        Dict mapping each split name to its list of cases.

    Raises:
        ValueError: If split ratios do not sum to ~1.0 or are negative.
    """
    if not splits_dict:
        raise ValueError("splits_dict must not be empty")

    total_ratio = sum(splits_dict.values())
    if abs(total_ratio - 1.0) > 1e-6:
        raise ValueError(
            f"Split ratios must sum to 1.0, got {total_ratio} "
            f"(splits: {splits_dict})"
        )
    for name, ratio in splits_dict.items():
        if ratio < 0:
            raise ValueError(f"Split ratio for {name!r} must be non-negative, got {ratio}")

    # Deterministic shuffle
    shuffled = list(cases)
    random.Random(seed).shuffle(shuffled)

    n = len(shuffled)
    result: dict[str, list[dict]] = {}
    start = 0

    split_names = list(splits_dict.keys())
    for idx, name in enumerate(split_names):
        if idx == len(split_names) - 1:
            # Last bucket gets any rounding remainder
            end = n
        else:
            end = start + round(splits_dict[name] * n)
        result[name] = shuffled[start:end]
        start = end

    return result


def save_jsonl(cases: list[dict], output_path: str) -> None:
    """Write a list of dicts to a JSONL file (one JSON object per line).

    The file is created (or overwritten) at *output_path*.  Parent directories
    are created automatically.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for case in cases:
            fh.write(json.dumps(case, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_segments(content: str) -> list[str]:
    """Extract meaningful text segments from *content*.

    Strategy (in priority order):
    1. Markdown headings (## / ###) — treat each section as a segment.
    2. Non-empty paragraphs (blank-line separated).
    3. Individual non-empty lines.
    """
    if not content.strip():
        return []

    # Try markdown sections
    sections = re.split(r"(?m)^#{1,6}\s+", content)
    sections = [s.strip() for s in sections if s.strip()]
    if len(sections) > 1:
        return sections

    # Try paragraphs
    paragraphs = re.split(r"\n\s*\n", content)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    if len(paragraphs) > 1:
        return paragraphs

    # Fall back to individual lines
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    return lines if lines else [content.strip()]


def _first_sentence(text: str) -> str:
    """Return the first sentence (or first 200 chars) of *text*."""
    text = text.strip()
    match = re.search(r"[.!?]", text)
    if match and match.start() > 0:
        return text[: match.start() + 1].strip()
    return text[:200].strip()


def _short_label(text: str, rng: random.Random) -> str:
    """Derive a short label from *text* (first few words, stripped of markup)."""
    clean = re.sub(r"[#`*_\[\]()]", "", text).strip()
    words = clean.split()
    # Take first 4–6 words for variety
    n = rng.randint(4, min(6, max(4, len(words))))
    return " ".join(words[:n]) if words else "content"
