"""
Screenshot manager for ARK visual tools.

Manages a catalog of screenshot entries with metadata, tagging, and persistence.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class ScreenshotEntry:
    """Represents a single screenshot in the catalog."""

    path: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = ""
    tags: list[str] = field(default_factory=list)
    description: str = ""
    width: Optional[int] = None
    height: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize entry to a plain dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScreenshotEntry":
        """Deserialize entry from a plain dict."""
        return cls(
            path=data.get("path", ""),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            source=data.get("source", ""),
            tags=data.get("tags", []),
            description=data.get("description", ""),
            width=data.get("width"),
            height=data.get("height"),
        )

    def _name(self) -> str:
        """Return a short name derived from the path (stem of the filename)."""
        return Path(self.path).stem if self.path else self.path


class ScreenshotCatalog:
    """Manages a collection of screenshot entries backed by a JSON file."""

    _CATALOG_VERSION = 1

    def __init__(self, catalog_path: Optional[Path] = None) -> None:
        self.catalog_path: Optional[Path] = (
            Path(catalog_path) if catalog_path is not None else None
        )
        # Internal store: name → ScreenshotEntry
        self._entries: dict[str, ScreenshotEntry] = {}

        if self.catalog_path is not None and self.catalog_path.exists():
            self.load()

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def register(self, entry: ScreenshotEntry) -> None:
        """Add or replace an entry in the catalog, keyed by the path stem."""
        name = Path(entry.path).stem if entry.path else entry.path
        self._entries[name] = entry

    def get(self, name: str) -> Optional[ScreenshotEntry]:
        """Return an entry by name (path stem) or None if not found."""
        # Try direct key first, then try matching by full path stem
        if name in self._entries:
            return self._entries[name]
        stem = Path(name).stem
        return self._entries.get(stem)

    def remove(self, name: str) -> bool:
        """Remove an entry by name. Returns True if it existed."""
        key = name if name in self._entries else Path(name).stem
        if key in self._entries:
            del self._entries[key]
            return True
        return False

    def list_screenshots(self, tags: Optional[list[str]] = None) -> list[ScreenshotEntry]:
        """
        Return all entries, optionally filtered so that each returned entry
        contains *all* of the requested tags.
        """
        entries = list(self._entries.values())
        if not tags:
            return entries
        tag_set = set(tags)
        return [e for e in entries if tag_set.issubset(set(e.tags))]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist the catalog to *catalog_path* as JSON."""
        if self.catalog_path is None:
            raise ValueError("catalog_path is not set — cannot save")
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": self._CATALOG_VERSION,
            "screenshots": {
                name: entry.to_dict() for name, entry in self._entries.items()
            },
        }
        self.catalog_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self) -> None:
        """Load (or re-load) the catalog from *catalog_path*."""
        if self.catalog_path is None:
            raise ValueError("catalog_path is not set — cannot load")
        if not self.catalog_path.exists():
            self._entries = {}
            return
        raw = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        screenshots = raw.get("screenshots", {})
        self._entries = {
            name: ScreenshotEntry.from_dict(data)
            for name, data in screenshots.items()
        }


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


def screenshot_from_spec(spec: dict[str, Any]) -> ScreenshotEntry:
    """
    Build a :class:`ScreenshotEntry` from a parsed AST node (spec dict).

    Expected keys (all optional except *path*):
    - ``path`` / ``name``  — file path or identifier
    - ``source``           — source description
    - ``tags``             — list of tag strings
    - ``description``      — human-readable description
    - ``width`` / ``height`` — pixel dimensions
    - ``timestamp``        — ISO-8601 string (defaults to *now*)
    """
    path = spec.get("path") or spec.get("name", "")
    timestamp = spec.get("timestamp", datetime.now(timezone.utc).isoformat())
    source = spec.get("source", "")
    tags: list[str] = list(spec.get("tags", []))
    description = spec.get("description", "")
    width = spec.get("width")
    height = spec.get("height")

    return ScreenshotEntry(
        path=path,
        timestamp=timestamp,
        source=source,
        tags=tags,
        description=description,
        width=width,
        height=height,
    )


# ---------------------------------------------------------------------------
# Module-level convenience wrappers (functional API matching the design)
# ---------------------------------------------------------------------------


def register_screenshot(screenshot_ast: dict[str, Any], catalog_path: Path) -> dict[str, Any]:
    """
    Register a screenshot AST node in the on-disk catalog.

    Returns a result dict: ``{"name": str, "path": str, "tags": list, "registered": bool}``.
    """
    catalog = ScreenshotCatalog(catalog_path)
    entry = screenshot_from_spec(screenshot_ast)
    catalog.register(entry)
    catalog.save()
    name = Path(entry.path).stem if entry.path else entry.path
    return {"name": name, "path": entry.path, "tags": entry.tags, "registered": True}


def load_catalog(catalog_path: Path) -> dict[str, Any]:
    """
    Load a catalog dict from *catalog_path*.

    Returns the raw ``{"version": ..., "screenshots": {...}}`` structure,
    or an empty catalog if the file does not exist.
    """
    path = Path(catalog_path)
    if not path.exists():
        return {"version": ScreenshotCatalog._CATALOG_VERSION, "screenshots": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_catalog(catalog: dict[str, Any], catalog_path: Path) -> None:
    """Write a raw catalog dict to disk."""
    path = Path(catalog_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


def list_screenshots(
    catalog: dict[str, Any], tags: Optional[list[str]] = None
) -> list[dict[str, Any]]:
    """
    Return screenshot dicts from a raw catalog, optionally filtered by tags.

    Each returned item is the raw dict stored under ``screenshots``.
    """
    screenshots: dict[str, Any] = catalog.get("screenshots", {})
    if not tags:
        return list(screenshots.values())
    tag_set = set(tags)
    return [s for s in screenshots.values() if tag_set.issubset(set(s.get("tags", [])))]


def get_screenshot(catalog: dict[str, Any], name: str) -> Optional[dict[str, Any]]:
    """Return a raw screenshot dict by name, or None."""
    screenshots: dict[str, Any] = catalog.get("screenshots", {})
    if name in screenshots:
        return screenshots[name]
    # Fall back to matching by path stem
    stem = Path(name).stem
    return screenshots.get(stem)


def generate_catalog_index(catalog: dict[str, Any], out_dir: Path) -> Path:
    """
    Generate a simple HTML index of the screenshot catalog.

    Returns the path to the created HTML file.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "screenshot_index.html"

    screenshots = catalog.get("screenshots", {})

    rows: list[str] = []
    for name, s in screenshots.items():
        tags_html = ", ".join(s.get("tags", []))
        path = s.get("path", "")
        desc = s.get("description", "")
        ts = s.get("timestamp", "")
        src = s.get("source", "")
        w = s.get("width", "")
        h = s.get("height", "")
        rows.append(
            f"<tr>"
            f"<td>{name}</td>"
            f"<td>{path}</td>"
            f"<td>{ts}</td>"
            f"<td>{src}</td>"
            f"<td>{tags_html}</td>"
            f"<td>{desc}</td>"
            f"<td>{w}</td>"
            f"<td>{h}</td>"
            f"</tr>"
        )

    rows_html = "\n".join(rows)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>Screenshot Catalog</title>
<style>
  body {{ font-family: sans-serif; padding: 1rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }}
  th {{ background: #f0f0f0; }}
</style>
</head>
<body>
<h1>Screenshot Catalog</h1>
<p>{len(screenshots)} screenshot(s)</p>
<table>
<thead>
<tr>
  <th>Name</th><th>Path</th><th>Timestamp</th><th>Source</th>
  <th>Tags</th><th>Description</th><th>Width</th><th>Height</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>
</body>
</html>
"""
    index_path.write_text(html, encoding="utf-8")
    return index_path
