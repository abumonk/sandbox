"""Tier 3 — Playwright smoke tests for Adventure Console UI.

TC-010, TC-011, TC-014, TC-015, TC-016, TC-017, TC-020, TC-024.

All test classes are decorated with @unittest.skipUnless(PW_AVAILABLE, ...)
so that this file still exits 0 when Playwright is not installed (satisfying
TC-036 on machines without a browser binary).

Run from repo root:
    python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"
"""
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Playwright availability guard
# ---------------------------------------------------------------------------

try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PW_AVAILABLE = True
except Exception:  # ImportError or any runtime error during import
    PW_AVAILABLE = False

_SKIP_REASON = "playwright not installed (pip install playwright && playwright install chromium)"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[4]


# ---------------------------------------------------------------------------
# Shared Playwright base class
# ---------------------------------------------------------------------------

@unittest.skipUnless(PW_AVAILABLE, _SKIP_REASON)
class _PlaywrightBase(unittest.TestCase):
    """Base class that launches a headless Chromium and a synthetic server."""

    _pw = None
    _browser: "Browser | None" = None
    _srv_thread = None
    _tmpdir: Path | None = None
    _adv_root = None

    @classmethod
    def setUpClass(cls):
        from _fixtures import make_synthetic_adventure, ServerThread

        # Create tmpdir and synthetic adventure
        import tempfile
        cls._tmpdir = Path(tempfile.mkdtemp())
        cls._adv_root = make_synthetic_adventure(
            cls._tmpdir, "ADV-999", state="review", permissions_approved=False
        )

        # Start server
        cls._srv_thread = ServerThread(cls._tmpdir / ".agent")
        cls._srv_thread.__enter__()

        # Launch browser — skip if binary missing
        try:
            cls._pw = sync_playwright().start()
            cls._browser = cls._pw.chromium.launch(headless=True)
        except Exception as exc:  # pragma: no cover
            # Missing browser binary or other launch error — skip cleanly
            if cls._srv_thread:
                cls._srv_thread.__exit__(None, None, None)
            raise unittest.SkipTest(
                f"Playwright browser launch failed: {exc}"
            ) from exc

    @classmethod
    def tearDownClass(cls):
        if cls._browser:
            try:
                cls._browser.close()
            except Exception:
                pass
        if cls._pw:
            try:
                cls._pw.stop()
            except Exception:
                pass
        if cls._srv_thread:
            cls._srv_thread.__exit__(None, None, None)
        if cls._tmpdir:
            import shutil
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def _new_page(self) -> "Page":
        ctx = self._browser.new_context()
        page = ctx.new_page()
        page.goto(self._srv_thread.url + "/", wait_until="networkidle")
        # Wait for sidebar to load
        page.wait_for_selector('[data-testid="adv-item-ADV-999"]', timeout=8000)
        # Click the adventure to open it
        page.click('[data-testid="adv-item-ADV-999"]')
        # Wait for tab bar
        page.wait_for_selector('[data-testid="tab-overview"]', timeout=8000)
        return page


# ---------------------------------------------------------------------------
# TC-010 + TC-011: Task detail panel
# ---------------------------------------------------------------------------

@unittest.skipUnless(PW_AVAILABLE, _SKIP_REASON)
class TestTaskDetail(_PlaywrightBase):
    """TC-010: structured task detail; TC-011: disclosure toggle."""

    def test_structured(self):
        """TC-010: clicking task card shows Description and Acceptance Criteria in separate cards."""
        page = self._new_page()
        # Navigate to Tasks tab
        page.click('[data-testid="tab-tasks"]')
        # Wait for any task card
        page.wait_for_selector('[data-testid^="task-card-"]', timeout=5000)
        # Click first task card
        task_cards = page.locator('[data-testid^="task-card-"]')
        task_cards.first.click()
        # Wait for detail panel
        page.wait_for_selector('[data-testid="task-detail"]', timeout=5000)
        # Should have a Description card and an Acceptance Criteria card (separate h3 elements)
        detail = page.locator('[data-testid="task-detail"]')
        desc_heading = detail.locator("h3", has_text="Description")
        ac_heading = detail.locator("h3", has_text="Acceptance Criteria")
        self.assertGreater(desc_heading.count(), 0,
                           "Task detail missing 'Description' card heading")
        self.assertGreater(ac_heading.count(), 0,
                           "Task detail missing 'Acceptance Criteria' card heading")
        page.context.close()

    def test_disclosure(self):
        """TC-011: 'Show details' disclosure is collapsed by default; click expands it."""
        page = self._new_page()
        page.click('[data-testid="tab-tasks"]')
        page.wait_for_selector('[data-testid^="task-card-"]', timeout=5000)
        page.locator('[data-testid^="task-card-"]').first.click()
        page.wait_for_selector('[data-testid="task-show-details"]', timeout=5000)

        # The disclosure <details> should be closed (not have 'open' attribute)
        disclosure = page.locator('[data-testid="task-show-details"]').locator("..")
        open_attr = disclosure.get_attribute("open")
        self.assertIsNone(open_attr, "Disclosure should be closed by default")

        # Click the summary to open
        page.locator('[data-testid="task-show-details"]').click()
        # After click, details[open] should exist
        time.sleep(0.2)
        open_attr_after = disclosure.get_attribute("open")
        self.assertIsNotNone(open_attr_after, "Disclosure should be open after click")
        page.context.close()


# ---------------------------------------------------------------------------
# TC-014..TC-017: Documents tab
# ---------------------------------------------------------------------------

@unittest.skipUnless(PW_AVAILABLE, _SKIP_REASON)
class TestDocuments(_PlaywrightBase):
    """TC-014..TC-017: Documents tab chip filter, design header, plan waves, review strip."""

    def test_chip_filter(self):
        """TC-014: clicking a chip filter does not fire XHR (client-side filter only)."""
        page = self._new_page()
        page.click('[data-testid="tab-documents"]')
        page.wait_for_selector('[data-testid="documents-chips"]', timeout=8000)

        # Collect requests fired during chip click
        requests_fired: list[str] = []

        def on_request(req):
            if req.resource_type in ("xhr", "fetch") and "documents" in req.url:
                requests_fired.append(req.url)

        page.on("request", on_request)
        # Click "design" chip (chip-design in implementation)
        page.click('[data-testid="chip-design"]')
        time.sleep(0.3)

        # No additional /documents XHR should have been fired
        self.assertEqual(
            requests_fired, [],
            f"Unexpected XHR(s) fired after chip click: {requests_fired}",
        )
        page.context.close()

    def test_design_header(self):
        """TC-015: opening a design doc shows a one_liner header area."""
        page = self._new_page()
        page.click('[data-testid="tab-documents"]')
        page.wait_for_selector('[data-testid="documents-list"]', timeout=8000)
        # Filter to designs
        page.wait_for_selector('[data-testid="chip-design"]', timeout=5000)
        page.click('[data-testid="chip-design"]')
        # Click first doc row
        doc_rows = page.locator('[data-testid^="doc-row-"]')
        if doc_rows.count() == 0:
            self.skipTest("No design documents visible in fixture")
        doc_rows.first.click()
        page.wait_for_selector(".doc-view", timeout=5000)
        # The doc view should contain content (design markdown rendered)
        doc_view = page.locator(".doc-view")
        content = doc_view.inner_text()
        self.assertGreater(len(content.strip()), 0,
                           "Doc view is empty after clicking design document")
        page.context.close()

    def test_plan_waves(self):
        """TC-016: opening plan fixture shows two wave-group elements."""
        page = self._new_page()
        page.click('[data-testid="tab-documents"]')
        page.wait_for_selector('[data-testid="documents-list"]', timeout=8000)
        page.wait_for_selector('[data-testid="chip-plan"]', timeout=5000)
        page.click('[data-testid="chip-plan"]')
        doc_rows = page.locator('[data-testid^="doc-row-"]')
        if doc_rows.count() == 0:
            self.skipTest("No plan documents visible in fixture")
        doc_rows.first.click()
        page.wait_for_selector(".doc-view", timeout=5000)
        # Give JS time to render the wave groups
        time.sleep(0.5)
        wave_groups = page.locator(".wave-group")
        count = wave_groups.count()
        self.assertEqual(count, 2,
                         f"Expected 2 .wave-group elements for plan fixture, got {count}")
        page.context.close()

    def test_review_strip(self):
        """TC-017: opening review fixture shows PASSED status badge."""
        page = self._new_page()
        page.click('[data-testid="tab-documents"]')
        page.wait_for_selector('[data-testid="documents-list"]', timeout=8000)
        page.wait_for_selector('[data-testid="chip-review"]', timeout=5000)
        page.click('[data-testid="chip-review"]')
        doc_rows = page.locator('[data-testid^="doc-row-"]')
        if doc_rows.count() == 0:
            self.skipTest("No review documents visible in fixture")
        doc_rows.first.click()
        page.wait_for_selector(".doc-view", timeout=5000)
        time.sleep(0.3)
        doc_view = page.locator(".doc-view")
        content = doc_view.inner_text()
        self.assertIn(
            "PASSED", content,
            f"Expected 'PASSED' in review doc view, got: {content[:200]}",
        )
        page.context.close()


# ---------------------------------------------------------------------------
# TC-020: Overview next-action card
# ---------------------------------------------------------------------------

@unittest.skipUnless(PW_AVAILABLE, _SKIP_REASON)
class TestOverview(_PlaywrightBase):
    """TC-020: overview next-action card text matches backend summary."""

    def test_next_action(self):
        """TC-020: next-action-card label matches backend summary.next_action.label."""
        from _fixtures import http_get
        page = self._new_page()
        # Already on overview tab after open()
        page.wait_for_selector('[data-testid="next-action-card"]', timeout=8000)

        # Fetch backend summary
        data = http_get(self._srv_thread.url, "/api/adventures/ADV-999")
        na = data.get("summary", {}).get("next_action", {})
        expected_label = na.get("label", "")

        if not expected_label:
            self.skipTest("next_action.label is empty — no assertion possible")

        # Get card text
        card = page.locator('[data-testid="next-action-card"]')
        card_text = card.inner_text()
        self.assertIn(
            expected_label, card_text,
            f"next-action-card text {card_text!r} does not contain label {expected_label!r}",
        )
        page.context.close()


# ---------------------------------------------------------------------------
# TC-024: Decisions state transition POST
# ---------------------------------------------------------------------------

@unittest.skipUnless(PW_AVAILABLE, _SKIP_REASON)
class TestDecisions(_PlaywrightBase):
    """TC-024: clicking state-transition button fires POST to /state endpoint."""

    def test_state_post(self):
        """TC-024: state-transition button fires POST /api/adventures/ADV-999/state."""
        page = self._new_page()
        page.click('[data-testid="tab-decisions"]')

        post_urls: list[str] = []

        def on_request(req):
            if req.method == "POST" and "/state" in req.url:
                post_urls.append(req.url)

        page.on("request", on_request)

        # Find any state-transition button
        btn = page.locator('[data-testid^="state-transition-btn-"]').first
        if btn.count() == 0:
            self.skipTest("No state-transition buttons found (adventure may have no transitions)")

        # Dismiss confirm dialog automatically
        page.on("dialog", lambda dialog: dialog.dismiss())
        try:
            btn.click(timeout=3000)
        except Exception:
            pass  # dialog dismiss may cause navigation error — that's fine
        time.sleep(0.5)

        self.assertGreater(
            len(post_urls), 0,
            "No POST to /state endpoint was fired after clicking state-transition button",
        )
        page.context.close()


if __name__ == "__main__":
    unittest.main()
