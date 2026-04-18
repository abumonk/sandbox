"""Validates TC-004 and cross-file completeness.

TC-004 (poc): every bucket value in concept-mapping.md is one of
  {descriptor, builder, controller, out-of-scope}.
Cross-file: every concept named in concept-inventory.md appears at least
  once in concept-mapping.md (no dropped concepts during classification).
"""

import pathlib
import re
import unittest

INVENTORY = pathlib.Path(
    ".agent/adventures/ADV-011/research/concept-inventory.md"
)
MAPPING = pathlib.Path(
    ".agent/adventures/ADV-011/research/concept-mapping.md"
)

ALLOWED_BUCKETS = {"descriptor", "builder", "controller", "out-of-scope"}


def _table_rows(text):
    """Yield cell-list for each pipe-table data row (skips header + ---)."""
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s-]+\|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].lower() in {"concept", "tc"}:
            continue  # header row
        yield cells


class TestMappingCompleteness(unittest.TestCase):
    def setUp(self):
        for f in (INVENTORY, MAPPING):
            self.assertTrue(
                f.exists(),
                f"Missing {f} — upstream task must produce it first.",
            )
        self.inventory_text = INVENTORY.read_text(encoding="utf-8")
        self.mapping_text = MAPPING.read_text(encoding="utf-8")

    def test_buckets_allowlist(self):
        """TC-004: every mapping row's bucket column is in the allowlist."""
        # Bucket column index must match schemas/entities.md#ConceptMappingRow.
        # Expected columns: concept | bucket | source_adventure | rationale
        bucket_idx = 2
        for cells in _table_rows(self.mapping_text):
            if len(cells) <= bucket_idx:
                continue
            bucket = cells[bucket_idx].lower()
            self.assertIn(
                bucket,
                ALLOWED_BUCKETS,
                f"Row has invalid bucket '{bucket}': {cells}",
            )

    def test_every_inventory_concept_is_mapped(self):
        """Cross-file: no concept from inventory is silently dropped."""
        inv_concepts = set()
        for cells in _table_rows(self.inventory_text):
            if cells:
                inv_concepts.add(cells[0].lower())
        missing = [
            c for c in inv_concepts if c and c.lower() not in self.mapping_text.lower()
        ]
        self.assertEqual(
            missing,
            [],
            f"Concepts in inventory missing from mapping: {missing[:5]} ...",
        )


if __name__ == "__main__":
    unittest.main()
