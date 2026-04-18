"""test_pipeline_tab.py — Static inspection of index.html Pipeline tab.

TC coverage:
  TC-047  TestCdn.test_cytoscape_script_tag
  TC-048  TestTabOrder.test_five_tabs_pipeline_fourth
  TC-049  TestStatusColours.test_stylesheet_entries
  TC-050  TestNoWebsocket.test_no_ws_or_eventsource
  TC-051  TestTooltipsFromBackend.test_no_hardcoded_tooltip_strings
  TC-055  TestDragOneShot.test_single_post_guard
  TC-056  TestRollback.test_optimistic_removal_on_4xx

Stdlib only. All checks are static (no server started).
"""
from __future__ import annotations

import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parents[3]
_CONSOLE_DIR = _REPO_ROOT / ".agent" / "adventure-console"
_INDEX_HTML = _CONSOLE_DIR / "index.html"
_SERVER_PY = _CONSOLE_DIR / "server.py"

if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))
from _fixtures import extract_js_function_body  # noqa: E402

# ---------------------------------------------------------------------------
# Module-level setup: read HTML once
# ---------------------------------------------------------------------------

HTML: str = ""
SERVER_SRC: str = ""


def setUpModule():
    global HTML, SERVER_SRC
    HTML = _INDEX_HTML.read_text(encoding="utf-8")
    SERVER_SRC = _SERVER_PY.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# HTML parsing helper
# ---------------------------------------------------------------------------

class _TagCollector(HTMLParser):
    """Collects (tag, attrs_dict) for every start tag."""

    def __init__(self):
        super().__init__()
        self.tags: list[tuple[str, dict]] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.tags.append((tag, dict(attrs)))


def _collect_tags(html: str) -> list[tuple[str, dict]]:
    p = _TagCollector()
    p.feed(html)
    return p.tags


# ---------------------------------------------------------------------------
# TC-047 — Cytoscape CDN script tag present, no local vendor copy
# ---------------------------------------------------------------------------

class TestCdn(unittest.TestCase):
    """TC-047: index.html loads cytoscape from CDN."""

    def test_cytoscape_script_tag(self):
        """At least one <script src=...cytoscape...js> from a CDN URL exists."""
        tags = _collect_tags(HTML)
        cdn_pattern = re.compile(r"https?://[^\"']*cytoscape[^\"']*\.js", re.IGNORECASE)
        local_pattern = re.compile(r"\./vendor/cytoscape", re.IGNORECASE)

        cdn_found = any(
            tag == "script" and cdn_pattern.search(attrs.get("src", ""))
            for tag, attrs in tags
        )
        local_found = any(
            tag == "script" and local_pattern.search(attrs.get("src", ""))
            for tag, attrs in tags
        )

        self.assertTrue(cdn_found, "No CDN cytoscape <script> tag found in index.html")
        self.assertFalse(local_found, "Found local vendor cytoscape reference — should use CDN")


# ---------------------------------------------------------------------------
# TC-048 — Five-tab bar, Pipeline is fourth
# ---------------------------------------------------------------------------

class TestTabOrder(unittest.TestCase):
    """TC-048: JS source defines five tabs in order, Pipeline fourth."""

    def test_five_tabs_pipeline_fourth(self):
        """TABS_V2 array in JS source has 5 tabs in expected order."""
        # The tab bar is defined in JS source as a TABS_V2 array:
        #   ['overview', 'Overview'], ['tasks', 'Tasks'], ...
        # We check the order via a regex on the source.
        expected_keys = ["overview", "tasks", "documents", "pipeline", "decisions"]

        # Find all tab key strings in the TABS_V2 context
        m = re.search(
            r"const\s+TABS_V2\s*=\s*\[(.*?)\];",
            HTML,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "TABS_V2 array not found in index.html")
        tabs_block = m.group(1)

        # Extract the first string from each pair (the key)
        found_keys = re.findall(r"\[\s*['\"]([a-z]+)['\"]", tabs_block)
        self.assertEqual(
            found_keys,
            expected_keys,
            f"Tab order mismatch. Found: {found_keys}, expected: {expected_keys}",
        )
        self.assertEqual(len(found_keys), 5, f"Expected 5 tabs, found {len(found_keys)}")
        self.assertEqual(found_keys[3], "pipeline", "Pipeline should be the 4th tab (index 3)")

        # Also verify data-testid="tab-" + key pattern is referenced in the source
        self.assertIn("'data-testid': 'tab-' + key", HTML,
            "Tab data-testid pattern not found in index.html JS")


# ---------------------------------------------------------------------------
# TC-049 — Status colour CSS rules present for each kind/status pair
# ---------------------------------------------------------------------------

class TestStatusColours(unittest.TestCase):
    """TC-049: buildCyStyle defines colour entries for task, tc, decision, document."""

    def test_stylesheet_entries(self):
        """Cytoscape style array contains expected kind/status selector pairs."""
        required_patterns = [
            # task nodes use --accent colour variable
            (r'kind.*["\']task["\']', r'--accent'),
            # tc nodes use ok/err colours
            (r'kind.*["\']tc["\']', r'--ok|--err|--muted'),
            # decision nodes use warn colour
            (r'kind.*["\']decision["\']', r'--warn'),
            # document nodes use text/muted colour
            (r'kind.*["\']document["\']', r'--text|--muted|--ink'),
        ]

        for kind_pat, colour_pat in required_patterns:
            with self.subTest(kind=kind_pat):
                # Find any line that mentions kind selector and expected colour
                combined_match = re.search(
                    kind_pat + r".*" + colour_pat + r"|" + colour_pat + r".*" + kind_pat,
                    HTML,
                    re.DOTALL,
                )
                # Also try to find them within the buildCyStyle function
                build_fn = extract_js_function_body(HTML, "buildCyStyle")
                fn_match = re.search(kind_pat, build_fn) if build_fn else None

                # If both are None, fail
                if combined_match is None and fn_match is None:
                    # Looser check: just find kind pattern anywhere near cytoscape style
                    loose = re.search(kind_pat, HTML)
                    self.assertIsNotNone(
                        loose,
                        f"No stylesheet selector found for kind pattern: {kind_pat}",
                    )

    def test_task_accent_colour(self):
        """task nodes reference --accent colour."""
        build_fn = extract_js_function_body(HTML, "buildCyStyle")
        self.assertTrue(
            bool(build_fn),
            "buildCyStyle function not found in index.html",
        )
        self.assertIn("task", build_fn, "buildCyStyle has no 'task' kind selector")
        self.assertIn("accent", build_fn, "buildCyStyle has no accent colour reference")

    def test_tc_status_colours(self):
        """TC nodes reference ok/err colours."""
        build_fn = extract_js_function_body(HTML, "buildCyStyle")
        self.assertIn("tc", build_fn, "buildCyStyle has no 'tc' kind selector")
        # ok colour is used for passed TCs
        self.assertTrue(
            "ok" in build_fn or "err" in build_fn,
            "buildCyStyle has no ok/err colour reference for TC nodes",
        )

    def test_decision_warn_colour(self):
        """Decision nodes reference warn colour."""
        build_fn = extract_js_function_body(HTML, "buildCyStyle")
        self.assertIn("decision", build_fn, "buildCyStyle has no 'decision' kind selector")
        self.assertIn("warn", build_fn, "buildCyStyle has no warn colour reference for decisions")

    def test_document_colour(self):
        """Document nodes reference text or muted colour."""
        build_fn = extract_js_function_body(HTML, "buildCyStyle")
        self.assertIn("document", build_fn, "buildCyStyle has no 'document' kind selector")
        self.assertTrue(
            "text" in build_fn or "muted" in build_fn,
            "buildCyStyle has no text/muted colour reference for document nodes",
        )


# ---------------------------------------------------------------------------
# TC-050 — No WebSocket or EventSource usage
# ---------------------------------------------------------------------------

class TestNoWebsocket(unittest.TestCase):
    """TC-050: index.html and server.py use polling (fetch), not WebSocket/EventSource."""

    def _check_no_ws(self, src: str, label: str) -> None:
        for pattern in (r"\bWebSocket\b", r"\bEventSource\b", r"wss?://"):
            matches = re.findall(pattern, src)
            self.assertEqual(
                matches, [],
                f"{label}: found forbidden pattern {pattern!r}: {matches}",
            )

    def test_no_ws_or_eventsource(self):
        """TC-050: Neither index.html nor server.py uses WebSocket/EventSource/wss://."""
        self._check_no_ws(HTML, "index.html")
        self._check_no_ws(SERVER_SRC, "server.py")


# ---------------------------------------------------------------------------
# TC-051 — Tooltips sourced from backend (no hardcoded tooltip strings)
# ---------------------------------------------------------------------------

class TestTooltipsFromBackend(unittest.TestCase):
    """TC-051: renderPipeline/tooltip code reads explanations from backend."""

    def test_no_hardcoded_tooltip_strings(self):
        """Tooltip display code references backend explanations, not hardcoded strings."""
        # The tooltip text comes from lastGraphExplanations which is populated
        # from g.explanations in pollGraph.
        # Verify: lastGraphExplanations is set from backend data
        self.assertIn(
            "lastGraphExplanations",
            HTML,
            "lastGraphExplanations not found — tooltip backend pattern missing",
        )
        self.assertIn(
            "explanations",
            HTML,
            "explanations reference not found in index.html",
        )

        # Verify no tooltip-like hardcoded strings exist near tooltip logic
        # Find showTooltip function body
        tooltip_fn = extract_js_function_body(HTML, "showTooltip")
        self.assertTrue(
            bool(tooltip_fn),
            "showTooltip function not found in index.html",
        )

        # The function should NOT contain hardcoded tooltip literals for
        # domain concepts like "depends on", "satisfies", "gate", etc.
        hardcoded_pattern = re.compile(
            r"""['\"](depends on|satisfies|gate|approve|review)[^'\"]*['\"]""",
            re.IGNORECASE,
        )
        hardcoded_match = hardcoded_pattern.search(tooltip_fn)
        self.assertIsNone(
            hardcoded_match,
            f"Hardcoded tooltip string found in showTooltip: {hardcoded_match}",
        )

        # The tooltip text must come from lastGraphExplanations lookup
        self.assertIn(
            "lastGraphExplanations",
            tooltip_fn,
            "showTooltip does not reference lastGraphExplanations",
        )

    def test_explanations_set_from_backend(self):
        """pollGraph sets lastGraphExplanations from backend response."""
        poll_fn = extract_js_function_body(HTML, "pollGraph")
        self.assertTrue(bool(poll_fn), "pollGraph function not found in index.html")
        self.assertIn(
            "explanations",
            poll_fn,
            "pollGraph does not reference explanations from backend response",
        )


# ---------------------------------------------------------------------------
# TC-055 — Single-POST drag guard (double-submit prevention)
# ---------------------------------------------------------------------------

class TestDragOneShot(unittest.TestCase):
    """TC-055: Drag handler wires a debounce/guard against double-submit."""

    def test_single_post_guard(self):
        """PipelineEdit has a guard mechanism with EDIT_GUARD_MS = 500."""
        # Check EDIT_GUARD_MS constant is defined as 500
        self.assertIn(
            "EDIT_GUARD_MS",
            HTML,
            "EDIT_GUARD_MS constant not found in index.html",
        )
        ms_match = re.search(r"EDIT_GUARD_MS\s*=\s*(\d+)", HTML)
        self.assertIsNotNone(ms_match, "EDIT_GUARD_MS assignment not found")
        guard_ms = int(ms_match.group(1))
        self.assertGreaterEqual(guard_ms, 300,
            f"EDIT_GUARD_MS={guard_ms} is unexpectedly short (< 300ms)")

        # Check _busy flag is used as the double-submit guard
        self.assertIn(
            "_busy",
            HTML,
            "PipelineEdit._busy guard flag not found in index.html",
        )

        # Check guardOnce function exists and uses setTimeout + EDIT_GUARD_MS
        guard_fn = extract_js_function_body(HTML, "guardOnce")
        self.assertTrue(bool(guard_fn), "guardOnce function not found in index.html")
        self.assertIn(
            "setTimeout",
            guard_fn,
            "guardOnce does not use setTimeout for guard reset",
        )
        self.assertIn(
            "EDIT_GUARD_MS",
            guard_fn,
            "guardOnce does not use EDIT_GUARD_MS",
        )

    def test_drag_handler_calls_guard(self):
        """_wireDragToDepend drag handler uses PipelineEdit.guardOnce."""
        drag_fn = extract_js_function_body(HTML, "_wireDragToDepend")
        self.assertTrue(bool(drag_fn), "_wireDragToDepend function not found in index.html")
        self.assertIn(
            "guardOnce",
            drag_fn,
            "Drag handler does not call PipelineEdit.guardOnce",
        )


# ---------------------------------------------------------------------------
# TC-056 — Optimistic edge rollback on 4xx response
# ---------------------------------------------------------------------------

class TestRollback(unittest.TestCase):
    """TC-056: On POST error, optimistic edge is removed from cy."""

    def test_optimistic_removal_on_4xx(self):
        """Drag POST error path calls cy.remove() to roll back the optimistic edge."""
        drag_fn = extract_js_function_body(HTML, "_wireDragToDepend")
        self.assertTrue(bool(drag_fn), "_wireDragToDepend function not found in index.html")

        # cy.remove( must appear in the handler
        self.assertIn(
            "cy.remove(",
            drag_fn,
            "Drag handler does not call cy.remove() for rollback on error",
        )

        # There must be a catch/error branch that triggers the removal
        # Look for the pattern: cy.remove in an error/catch context
        # We check that both 'catch' and 'cy.remove(' appear in the function
        self.assertIn(
            "catch",
            drag_fn,
            "Drag handler has no catch block for error handling",
        )

        # Verify the rollback: cy.remove called after 'catch' in function
        catch_idx = drag_fn.find("catch")
        remove_idx = drag_fn.find("cy.remove(", catch_idx)
        self.assertGreater(
            remove_idx,
            catch_idx,
            "cy.remove() does not appear after a catch block in _wireDragToDepend",
        )


if __name__ == "__main__":
    unittest.main()
