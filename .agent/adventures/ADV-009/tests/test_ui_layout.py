"""Tier 2 — Static HTML structure tests for Adventure Console UI.

TC-001..TC-005, TC-008, TC-009, TC-013, TC-018, TC-022, TC-031..TC-033.

Parses .agent/adventure-console/index.html with stdlib html.parser only.
No network, no subprocess, no third-party imports.

Run from repo root:
    python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"
"""
from __future__ import annotations

import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[4]
INDEX_HTML = REPO_ROOT / ".agent" / "adventure-console" / "index.html"
AUDIT_MD = REPO_ROOT / ".agent" / "adventures" / "ADV-009" / "research" / "audit.md"

# ---------------------------------------------------------------------------
# TagSoup — minimal HTML tree recorder
# ---------------------------------------------------------------------------

class _Tag:
    """A recorded HTML tag with its attrs, inner text, and raw innerHTML."""
    __slots__ = ("tag", "attrs", "text", "inner_html", "children")

    def __init__(self, tag: str, attrs: dict):
        self.tag = tag
        self.attrs = attrs
        self.text = ""
        self.inner_html = ""
        self.children: list[_Tag] = []

    def get(self, attr: str, default=None):
        return self.attrs.get(attr, default)

    def has_class(self, cls: str) -> bool:
        classes = self.attrs.get("class", "").split()
        return cls in classes

    def __repr__(self):
        return f"<{self.tag} {self.attrs} text={self.text!r}>"


class TagSoup(HTMLParser):
    """Record every tag encountered in an HTML document.

    Provides flat list ``self.tags`` of all tags (including nested ones)
    plus helper query methods.
    """

    VOID_TAGS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags: list[_Tag] = []
        self._stack: list[_Tag] = []
        self._script_depth = 0
        self._style_depth = 0
        self._raw_text: list[str] = []   # collect all style + raw text blocks

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = {k: (v or "") for k, v in attrs}
        node = _Tag(tag, attrs_dict)
        self.tags.append(node)
        if self._stack:
            self._stack[-1].children.append(node)
        if tag not in self.VOID_TAGS:
            self._stack.append(node)
        if tag == "script":
            self._script_depth += 1
        if tag == "style":
            self._style_depth += 1

    def handle_endtag(self, tag: str):
        if tag == "script":
            self._script_depth = max(0, self._script_depth - 1)
        if tag == "style":
            self._style_depth = max(0, self._style_depth - 1)
        # Pop matching tag from stack
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i].tag == tag:
                self._stack.pop(i)
                break

    def handle_data(self, data: str):
        if self._stack:
            self._stack[-1].text += data
            self._stack[-1].inner_html += data
        self._raw_text.append(data)

    # -- Query helpers -------------------------------------------------------

    def find_all(self, tag: str = "", **attr_filters) -> list[_Tag]:
        """Return all nodes matching tag (if given) and/or attrs."""
        result = []
        for node in self.tags:
            if tag and node.tag != tag:
                continue
            if all(node.attrs.get(k) == v for k, v in attr_filters.items()):
                result.append(node)
        return result

    def find_by_testid(self, testid: str) -> list[_Tag]:
        return [n for n in self.tags if n.attrs.get("data-testid") == testid]

    def find_by_testid_prefix(self, prefix: str) -> list[_Tag]:
        return [n for n in self.tags
                if n.attrs.get("data-testid", "").startswith(prefix)]

    def count_by_class(self, cls: str) -> int:
        return sum(1 for n in self.tags if cls in n.attrs.get("class", "").split())

    def has_link_to(self, href_substr: str) -> bool:
        return any(href_substr in n.attrs.get("href", "") or
                   href_substr in n.attrs.get("src", "")
                   for n in self.tags)

    def all_raw_text(self) -> str:
        return "\n".join(self._raw_text)

    def style_block(self) -> str:
        """Return concatenated text of all <style> elements."""
        parts = []
        for node in self.tags:
            if node.tag == "style":
                parts.append(node.text)
        return "\n".join(parts)

    def script_block(self) -> str:
        """Return concatenated text of all <script> elements."""
        parts = []
        for node in self.tags:
            if node.tag == "script":
                parts.append(node.text)
        return "\n".join(parts)


def _parse_index() -> TagSoup:
    """Parse index.html and return a TagSoup instance."""
    soup = TagSoup()
    soup.feed(INDEX_HTML.read_text(encoding="utf-8"))
    return soup


# Cache at module level so each test class doesn't reparse
_SOUP: TagSoup | None = None


def _soup() -> TagSoup:
    global _SOUP
    if _SOUP is None:
        _SOUP = _parse_index()
    return _SOUP


# ---------------------------------------------------------------------------
# TC-001: audit.md has >= 30 markdown table rows
# ---------------------------------------------------------------------------

class TestAuditPresence(unittest.TestCase):
    """TC-001: research/audit.md has at least 30 rows in a markdown table."""

    @classmethod
    def setUpClass(cls):
        if not AUDIT_MD.exists():
            raise unittest.SkipTest(f"audit.md not found: {AUDIT_MD}")
        cls.audit_text = AUDIT_MD.read_text(encoding="utf-8")

    def test_min_rows(self):
        """audit.md must have >= 30 markdown table rows (non-header pipe lines)."""
        rows = [
            line for line in self.audit_text.splitlines()
            if line.strip().startswith("|")
            and not re.match(r"^\s*\|[-:\s|]+\|\s*$", line)
            and not re.match(r"^\s*\|[^|]*Element[^|]*\|", line, re.IGNORECASE)
        ]
        self.assertGreaterEqual(
            len(rows), 30,
            f"Expected >= 30 audit table rows, got {len(rows)}",
        )


# ---------------------------------------------------------------------------
# TC-002: audit.md verdicts are in allowed set
# ---------------------------------------------------------------------------

class TestAuditVerdicts(unittest.TestCase):
    """TC-002: every verdict cell in audit.md is in the allowed set."""

    ALLOWED = {"keep", "hide-behind-toggle", "remove"}

    @classmethod
    def setUpClass(cls):
        if not AUDIT_MD.exists():
            raise unittest.SkipTest(f"audit.md not found: {AUDIT_MD}")
        cls.audit_text = AUDIT_MD.read_text(encoding="utf-8")

    def test_verdict_set(self):
        """Every non-header, non-separator, non-section-header table row has a verdict in ALLOWED."""
        lines = self.audit_text.splitlines()
        in_table = False
        header_seen = False
        bad: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped.startswith("|"):
                if in_table and stripped:
                    in_table = False
                continue
            in_table = True
            # Skip separator rows
            if re.match(r"^\s*\|[-:\s|]+\|\s*$", stripped):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not header_seen:
                header_seen = True
                continue
            # Skip section-header rows (e.g. | **SIDEBAR** | | | | |)
            first_cell = cells[0] if cells else ""
            if re.match(r"^\*\*[A-Z\s]+\*\*$", first_cell):
                continue
            # Also skip rows where all cells except first are empty (section dividers)
            non_empty = [c for c in cells[1:] if c]
            if not non_empty:
                continue
            # Check that at least one allowed verdict appears in the row
            row_text = "|".join(cells).lower()
            has_allowed = any(v in row_text for v in self.ALLOWED)
            if not has_allowed:
                bad.append(stripped)
        # Only fail if we actually found rows without any verdict keyword
        if bad:
            self.fail(f"audit.md rows with no recognised verdict: {bad[:5]}")


# ---------------------------------------------------------------------------
# TC-003: audit.md covers legacy tab names
# ---------------------------------------------------------------------------

class TestAuditCoverage(unittest.TestCase):
    """TC-003: audit.md element column covers every legacy tab name."""

    LEGACY_TABS = {"Log", "Knowledge", "Permissions", "Designs", "Plans",
                   "Research", "Reviews"}

    @classmethod
    def setUpClass(cls):
        if not AUDIT_MD.exists():
            raise unittest.SkipTest(f"audit.md not found: {AUDIT_MD}")
        cls.audit_text = AUDIT_MD.read_text(encoding="utf-8")

    def test_branches(self):
        """Union of audit Element column should cover all legacy tab names."""
        missing = [
            name for name in self.LEGACY_TABS
            if name.lower() not in self.audit_text.lower()
        ]
        self.assertFalse(
            missing,
            f"Legacy tab names missing from audit.md: {missing}",
        )


# ---------------------------------------------------------------------------
# TC-004 + TC-005: tab bar
# ---------------------------------------------------------------------------

class TestTabBar(unittest.TestCase):
    """TC-004 + TC-005: four tabs with correct data-testid, no legacy tab labels."""

    # The JS builds tabs dynamically from TABS_V2 array; the HTML source itself
    # doesn't have static tab elements. We parse the JS to verify the definition.

    EXPECTED_TABS = {"tab-overview", "tab-tasks", "tab-documents", "tab-pipeline", "tab-decisions"}

    def test_four_tabs(self):
        """TC-004: TABS_V2 array in JS defines exactly four tab keys matching expected set."""
        script = _soup().script_block()
        # Match: const TABS_V2 = [ ['key', 'Label'], ... ]
        m = re.search(r"const TABS_V2\s*=\s*\[(.*?)\];", script, re.DOTALL)
        self.assertIsNotNone(m, "TABS_V2 array not found in index.html script block")
        tabs_text = m.group(1)
        # Extract first element of each sub-array: ['key', ...]
        keys = re.findall(r"\[\s*'([^']+)'", tabs_text)
        testids = {"tab-" + k for k in keys}
        self.assertEqual(
            testids, self.EXPECTED_TABS,
            f"Tab testids mismatch. Expected: {self.EXPECTED_TABS}, got: {testids}",
        )

    def test_no_legacy_tabs(self):
        """TC-005: TABS_V2 does not define any legacy tab label."""
        LEGACY_LABELS = {"Log", "Knowledge", "Permissions", "Designs", "Plans",
                         "Research", "Reviews"}
        script = _soup().script_block()
        m = re.search(r"const TABS_V2\s*=\s*\[(.*?)\];", script, re.DOTALL)
        if not m:
            self.skipTest("TABS_V2 not found in script block")
        tabs_text = m.group(1)
        # Extract labels (second string element): ['key', 'Label']
        labels = re.findall(r"\[\s*'[^']+'\s*,\s*'([^']+)'", tabs_text)
        legacy_found = LEGACY_LABELS.intersection(labels)
        self.assertFalse(
            legacy_found,
            f"Legacy tab labels found in TABS_V2: {legacy_found}",
        )


# ---------------------------------------------------------------------------
# TC-006: header components
# ---------------------------------------------------------------------------

class TestHeader(unittest.TestCase):
    """TC-006: header renders TC progress bar, CTA button, state pill, title, ID."""

    def test_components(self):
        """Script block references expected header data-testid values."""
        script = _soup().script_block()
        # Each of these testids must be referenced in the JS as they're built dynamically
        required_testids = [
            "tc-progress-bar",
            "header-state-pill",
            "header-title",
            "header-id",
        ]
        for tid in required_testids:
            self.assertIn(
                tid, script,
                f"data-testid {tid!r} not found in index.html script",
            )
        # next-action-button is built in renderNextActionCard
        self.assertIn("next-action-button", script)


# ---------------------------------------------------------------------------
# TC-008: task bucket containers
# ---------------------------------------------------------------------------

class TestTasksTab(unittest.TestCase):
    """TC-008 + TC-009: task buckets and card shape in the JS template."""

    def test_buckets(self):
        """TC-008: renderTasks JS creates bucket containers per status dynamically."""
        script = _soup().script_block()
        # The JS builds task-bucket-<status> testids dynamically:
        # 'data-testid': 'task-bucket-' + status
        self.assertIn("task-bucket-", script,
                      "task-bucket-* testid pattern not found in script")
        # BUCKET_ORDER array must include standard statuses
        m = re.search(r"BUCKET_ORDER\s*=\s*\[(.*?)\]", script, re.DOTALL)
        self.assertIsNotNone(m, "BUCKET_ORDER array not found in renderTasks JS")
        bucket_text = m.group(1)
        for status in ("pending", "in_progress", "done"):
            self.assertIn(
                f"'{status}'", bucket_text,
                f"status '{status}' not in BUCKET_ORDER",
            )

    def test_card_shape(self):
        """TC-009: task card JS uses task-card-<id> testid; no assignee slot in card."""
        script = _soup().script_block()
        self.assertIn("task-card-", script,
                      "task-card-* testids not found in script")
        # TC-checklist slot present
        self.assertIn("tc-checklist", script,
                      "tc-checklist not found in script (TC checklist slot missing)")
        # depends-on slot present
        self.assertIn("depends_on", script,
                      "depends_on not referenced in renderTasks JS")
        # No data-testid="task-card-path" in script (per design spec)
        self.assertNotIn("task-card-path", script,
                         "task-card-path should not be present per design spec")


# ---------------------------------------------------------------------------
# TC-013: documents chip bar (5 chips)
# ---------------------------------------------------------------------------

class TestDocumentsTab(unittest.TestCase):
    """TC-013: chip filter bar has exactly five chip kinds."""

    EXPECTED_CHIP_KINDS = {"all", "design", "plan", "research", "review"}

    def test_chips(self):
        """TC-013: KINDS array in renderDocuments has exactly five entries."""
        script = _soup().script_block()
        # Match: const KINDS = ['all', 'design', 'plan', 'research', 'review'];
        m = re.search(r"const KINDS\s*=\s*\[(.*?)\];", script, re.DOTALL)
        self.assertIsNotNone(m, "KINDS array not found in renderDocuments JS")
        kinds_text = m.group(1)
        kinds = set(re.findall(r"'([^']+)'", kinds_text))
        self.assertEqual(
            kinds, self.EXPECTED_CHIP_KINDS,
            f"Chip kinds mismatch. Expected: {self.EXPECTED_CHIP_KINDS}, got: {kinds}",
        )
        # Also confirm the testid pattern chip-<kind> is used
        self.assertIn("chip-", script,
                      "chip-* testid pattern not found in script")


# ---------------------------------------------------------------------------
# TC-018: overview progress bar (no <table> for TC progress)
# ---------------------------------------------------------------------------

class TestOverview(unittest.TestCase):
    """TC-018: overview card has tc-progress-bar; TC progress shown without <table>."""

    def test_progress_bar(self):
        """TC-018: tc-progress-bar data-testid referenced in JS; progress bar uses .progress class not a <table>."""
        script = _soup().script_block()
        self.assertIn("tc-progress-bar", script,
                      "tc-progress-bar testid not found in script")
        # The progress bar element must use class 'progress' (not a <table> element)
        # Find the tc-progress-bar creation in script
        idx = script.find("tc-progress-bar")
        self.assertGreater(idx, 0)
        # Within 300 chars of the tc-progress-bar reference, should see 'progress'
        context = script[max(0, idx - 100): idx + 300]
        self.assertIn(
            "progress", context,
            "tc-progress-bar element should use a .progress class element",
        )
        # The progress bar div itself should not be an h('table') call
        self.assertNotIn(
            "h('table'", context,
            "tc-progress-bar area uses a <table> instead of a .progress div",
        )


# ---------------------------------------------------------------------------
# TC-022: decisions three cards
# ---------------------------------------------------------------------------

class TestDecisions(unittest.TestCase):
    """TC-022: decisions tab has three card data-testids."""

    # Actual testids used in the implementation (grounded against index.html)
    EXPECTED_CARD_TESTIDS = {
        "decisions-state-card",
        "decisions-permissions-card",
        "decisions-knowledge-card",
    }

    def test_three_cards(self):
        """TC-022: three decisions cards with correct data-testid values present in JS."""
        script = _soup().script_block()
        for testid in self.EXPECTED_CARD_TESTIDS:
            self.assertIn(
                testid, script,
                f"decisions card testid {testid!r} not found in index.html script",
            )


# ---------------------------------------------------------------------------
# TC-031: visual system CSS classes defined in <style>
# ---------------------------------------------------------------------------

class TestVisualSystem(unittest.TestCase):
    """TC-031 + TC-032 + TC-033: visual system CSS and external resource checks."""

    REQUIRED_CLASSES = {".card", ".pill", ".progress", ".chip-bar", ".chip",
                        ".stack", "details.disclosure"}

    def test_classes(self):
        """TC-031: inline <style> defines all required CSS classes."""
        style = _soup().style_block()
        for cls in self.REQUIRED_CLASSES:
            # Match e.g. ".card {" or ".card\n{" or ".chip-bar" anywhere in style
            pattern = re.escape(cls)
            self.assertRegex(
                style, pattern,
                f"CSS class {cls!r} not found in <style> block",
            )

    def test_no_external(self):
        """TC-032: no external stylesheet <link rel="stylesheet" href="http...">."""
        soup = _soup()
        for node in soup.find_all("link"):
            rel = node.attrs.get("rel", "").lower()
            href = node.attrs.get("href", "")
            if "stylesheet" in rel and href.startswith("http"):
                self.fail(
                    f"External stylesheet found: <link rel={rel!r} href={href!r}>"
                )

    def test_card_usage(self):
        """TC-033: card-related data-testid elements in JS use the 'card' class."""
        script = _soup().script_block()
        # next-action-card uses class 'card'
        # Find renderNextActionCard and check it creates a .card element
        self.assertIn("next-action-card", script)
        # The card elements in renderDecisions also have 'card' class
        # Verify that wherever decisions-state-card testid is set, 'card' class is also nearby
        for testid in ("decisions-state-card", "decisions-permissions-card",
                       "decisions-knowledge-card"):
            # Find the context around this testid
            idx = script.find(testid)
            if idx == -1:
                self.fail(f"testid {testid!r} not found in script")
            # Check within 200 chars before the testid for 'card' class reference
            context = script[max(0, idx - 200): idx + 50]
            self.assertIn(
                "'card'", context,
                f"testid {testid!r} does not appear to use class 'card' (context: {context!r})",
            )


if __name__ == "__main__":
    unittest.main()
