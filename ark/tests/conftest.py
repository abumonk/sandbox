"""Pytest configuration for ARK parser tests.

Injects `tools/parser` into sys.path (mirroring the trick in `ark.py`) and
exposes a `parse_src` fixture that parses a source string and returns the
JSON-deserialized AST dict, so tests can assert against plain dicts
instead of dataclasses.
"""

import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: marks tests as end-to-end integration tests (may require real spec files)",
    )

import json
import sys
from pathlib import Path

import pytest

_ARK_ROOT = Path(__file__).resolve().parent.parent
_PARSER_DIR = _ARK_ROOT / "tools" / "parser"
_VERIFY_DIR = _ARK_ROOT / "tools" / "verify"
_DIFF_DIR = _ARK_ROOT / "tools" / "diff"
_WATCH_DIR = _ARK_ROOT / "tools" / "watch"
_DISPATCH_DIR = _ARK_ROOT / "tools" / "dispatch"
for _dir in (_PARSER_DIR, _VERIFY_DIR, _DIFF_DIR, _WATCH_DIR, _DISPATCH_DIR):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

from ark_parser import parse as _ark_parse  # noqa: E402
from ark_parser import to_json as _ark_to_json  # noqa: E402


def _parse_src(source: str) -> dict:
    """Parse ARK source text → AST dict (via JSON round-trip)."""
    ark_file = _ark_parse(source)
    return json.loads(_ark_to_json(ark_file))


def _parse_file(path) -> dict:
    """Parse an .ark file on disk → AST dict (imports resolved)."""
    p = Path(path)
    source = p.read_text(encoding="utf-8")
    ark_file = _ark_parse(source, file_path=p)
    return json.loads(_ark_to_json(ark_file))


@pytest.fixture(scope="session")
def ark_root() -> Path:
    return _ARK_ROOT


@pytest.fixture
def parse_src():
    """Return a callable: (source: str) -> AST dict."""
    return _parse_src


@pytest.fixture
def parse_file():
    """Return a callable: (path) -> AST dict."""
    return _parse_file
