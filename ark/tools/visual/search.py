"""
Visual search module for ARK visual tools.

Provides keyword-based and tag-based search over screenshot catalog entries.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class SearchResult:
    """A single search result from the visual catalog."""

    path: str
    score: float  # 0.0 – 1.0, higher is more relevant
    tags: list[str] = field(default_factory=list)
    description: str = ""
    matched_terms: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _entry_text_fields(entry: dict[str, Any]) -> dict[str, str]:
    """Return a dict of searchable text fields from a catalog entry dict."""
    return {
        "description": str(entry.get("description", "") or ""),
        "tags": " ".join(entry.get("tags", []) or []),
        "source": str(entry.get("source", "") or ""),
        "path": str(entry.get("path", "") or ""),
    }


def _count_keyword_occurrences(text: str, keyword: str) -> int:
    """Count case-insensitive occurrences of *keyword* in *text*."""
    if not text or not keyword:
        return 0
    return text.lower().count(keyword.lower())


# ---------------------------------------------------------------------------
# Public search functions
# ---------------------------------------------------------------------------


def keyword_search(
    catalog_entries: list[dict[str, Any]],
    query: str,
    max_results: int = 10,
) -> list[SearchResult]:
    """Search catalog entries by keyword matching.

    Matches *query* terms (whitespace-separated) case-insensitively against
    each entry's description, tags, source, and path fields.

    Score = number_of_matched_keyword_occurrences / total_terms in query.

    Returns a list of :class:`SearchResult` sorted by score descending,
    capped at *max_results*.
    """
    if not query or not query.strip():
        return []

    terms = query.strip().split()
    total_terms = len(terms)

    results: list[SearchResult] = []

    for entry in catalog_entries:
        fields = _entry_text_fields(entry)
        combined_text = " ".join(fields.values())

        matched: list[str] = []
        hit_count = 0
        for term in terms:
            count = _count_keyword_occurrences(combined_text, term)
            if count > 0:
                matched.append(term)
                hit_count += count

        if matched:
            score = min(1.0, len(matched) / total_terms)
            results.append(
                SearchResult(
                    path=entry.get("path", ""),
                    score=score,
                    tags=list(entry.get("tags", []) or []),
                    description=entry.get("description", ""),
                    matched_terms=matched,
                )
            )

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:max_results]


def tag_search(
    catalog_entries: list[dict[str, Any]],
    tags: list[str],
    max_results: int = 10,
) -> list[SearchResult]:
    """Search catalog entries by tag intersection.

    An entry must contain **all** requested *tags* to be included.

    Score = len(matching_tags) / len(requested_tags).  Because the entry must
    have ALL requested tags, score is always 1.0 for matched entries.

    Returns a list of :class:`SearchResult` sorted by score descending,
    capped at *max_results*.
    """
    if not tags:
        return []

    requested = [t.lower() for t in tags]
    total_requested = len(requested)

    results: list[SearchResult] = []

    for entry in catalog_entries:
        entry_tags_lower = [t.lower() for t in (entry.get("tags", []) or [])]
        matching = [t for t in requested if t in entry_tags_lower]

        if len(matching) == total_requested:
            score = len(matching) / total_requested
            results.append(
                SearchResult(
                    path=entry.get("path", ""),
                    score=score,
                    tags=list(entry.get("tags", []) or []),
                    description=entry.get("description", ""),
                    matched_terms=matching,
                )
            )

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:max_results]


def combined_search(
    catalog_entries: list[dict[str, Any]],
    query: Optional[str] = None,
    tags: Optional[list[str]] = None,
    max_results: int = 10,
) -> list[SearchResult]:
    """Combined keyword and tag search with weighted scoring.

    - Both *query* and *tags* provided: score = 0.6 * keyword_score + 0.4 * tag_score
      (only entries that match at least one keyword **and** all tags are included)
    - Only *query*: pure keyword search
    - Only *tags*: pure tag search
    - Neither: returns an empty list

    Returns results sorted by score descending, capped at *max_results*.
    """
    has_query = bool(query and query.strip())
    has_tags = bool(tags)

    if not has_query and not has_tags:
        return []

    if has_query and not has_tags:
        return keyword_search(catalog_entries, query, max_results=max_results)  # type: ignore[arg-type]

    if has_tags and not has_query:
        return tag_search(catalog_entries, tags, max_results=max_results)  # type: ignore[arg-type]

    # Both — combine scores
    kw_results = keyword_search(catalog_entries, query, max_results=len(catalog_entries))  # type: ignore[arg-type]
    tag_results = tag_search(catalog_entries, tags, max_results=len(catalog_entries))  # type: ignore[arg-type]

    kw_by_path = {r.path: r for r in kw_results}
    tag_by_path = {r.path: r for r in tag_results}

    # Intersection: entry must appear in both result sets
    common_paths = set(kw_by_path.keys()) & set(tag_by_path.keys())

    combined: list[SearchResult] = []
    for path in common_paths:
        kw_r = kw_by_path[path]
        tag_r = tag_by_path[path]
        combined_score = 0.6 * kw_r.score + 0.4 * tag_r.score
        # Merge matched_terms from both searches
        all_matched = list(dict.fromkeys(kw_r.matched_terms + tag_r.matched_terms))
        combined.append(
            SearchResult(
                path=path,
                score=round(combined_score, 6),
                tags=kw_r.tags,
                description=kw_r.description,
                matched_terms=all_matched,
            )
        )

    combined.sort(key=lambda r: r.score, reverse=True)
    return combined[:max_results]


def search_from_spec(
    search_ast: dict[str, Any],
    catalog: dict[str, Any],
) -> list[SearchResult]:
    """Factory that reads search parameters from a parsed AST node and dispatches.

    Reads the following keys from *search_ast*:
    - ``search_mode`` / ``mode`` — ``"keyword"``, ``"tag"``, ``"semantic"`` (default: ``"keyword"``)
    - ``query``                   — query string for keyword/combined search
    - ``tags`` / ``filters``      — list of tags for tag/combined search
    - ``max_results``             — cap on returned results (default: 10)

    *catalog* should be a raw catalog dict as returned by
    :func:`~tools.visual.screenshot_manager.load_catalog`:
    ``{"version": ..., "screenshots": {"name": {...}, ...}}``.

    For ``search_mode = "semantic"``, an empty list is returned and a warning is
    emitted (semantic search is not implemented in v1).
    """
    mode: str = (
        search_ast.get("search_mode") or search_ast.get("mode") or "keyword"
    ).lower()
    query: Optional[str] = search_ast.get("query") or None
    tags: Optional[list[str]] = search_ast.get("tags") or search_ast.get("filters") or None
    max_results: int = int(search_ast.get("max_results", 10) or 10)

    # Flatten catalog dict → list of entry dicts
    screenshots: dict[str, Any] = catalog.get("screenshots", {})
    entries: list[dict[str, Any]] = list(screenshots.values())

    if mode == "semantic":
        warnings.warn(
            "SearchMode.semantic is not implemented in v1 — returning empty results.",
            stacklevel=2,
        )
        return []

    if mode == "tag":
        return tag_search(entries, tags or [], max_results=max_results)

    if mode == "keyword":
        return keyword_search(entries, query or "", max_results=max_results)

    # mode == "combined" or anything else → combined
    return combined_search(entries, query=query, tags=tags, max_results=max_results)


# ---------------------------------------------------------------------------
# Class-based façade (matches test strategy: VisualSearch.search(...))
# ---------------------------------------------------------------------------


class VisualSearch:
    """Thin façade over the functional search API.

    Provides ``VisualSearch.search(query, mode, tags, catalog, max_results)``
    which is the interface expected by ``test_visual_renderer.py``.
    """

    @staticmethod
    def search(
        query: Optional[str] = None,
        mode: str = "keyword",
        tags: Optional[list[str]] = None,
        catalog: Optional[dict[str, Any]] = None,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Execute a search against *catalog*.

        Args:
            query:       Keyword query string.
            mode:        One of ``"keyword"``, ``"tag"``, ``"semantic"``, ``"combined"``.
            tags:        List of tags (used when mode is ``"tag"`` or ``"combined"``).
            catalog:     Raw catalog dict (``{"screenshots": {...}}``).
            max_results: Maximum number of results to return.

        Returns:
            List of :class:`SearchResult` sorted by score descending.
        """
        if catalog is None:
            catalog = {"screenshots": {}}

        ast: dict[str, Any] = {
            "search_mode": mode,
            "query": query,
            "tags": tags,
            "max_results": max_results,
        }
        return search_from_spec(ast, catalog)
