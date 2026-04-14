# Visual Search — Design

## Overview
Create `tools/visual/search.py` that provides semantic search over visual artifacts using text-based keyword and tag matching (v1). Processes `visual_search` items from the AST and queries the screenshot catalog.

## Target Files
- `ark/tools/visual/search.py` — Visual search module

## Approach

### Search Strategy (v1)
For v1, implement keyword + tag matching against the screenshot catalog. Semantic embedding-based search is deferred to v2.

### Functions
```python
def execute_search(search_ast: dict, catalog: dict) -> list:
    """Execute a visual_search query against the catalog.
    
    Returns:
        List of SearchResult dicts sorted by relevance score.
    """

def keyword_search(query: str, catalog: dict) -> list:
    """Search by keyword matching in descriptions and source fields."""

def tag_search(tags: list, catalog: dict) -> list:
    """Filter catalog entries by tag intersection."""

def combined_search(query: str, tags: list, catalog: dict) -> list:
    """Combined keyword + tag search with weighted scoring."""

def score_result(entry: dict, query: str, tags: list) -> float:
    """Score a catalog entry against the query. Higher = more relevant."""
```

### Scoring
- Keyword match in name: weight 3.0
- Keyword match in description: weight 2.0
- Keyword match in source: weight 1.0
- Tag intersection: weight 2.0 per matching tag
- Results capped at `max_results` from the search query

### Design Decisions
- v1 uses simple text matching (no ML dependencies)
- SearchMode.semantic returns empty results with a "not implemented" warning
- Combined mode multiplies keyword and tag scores
- Results returned as list of dicts matching SearchResult schema

## Dependencies
- design-screenshot-manager (catalog to search against)

## Target Conditions
- TC-020: Keyword search returns correct matches from catalog
- TC-021: Tag search filters correctly by tag intersection
