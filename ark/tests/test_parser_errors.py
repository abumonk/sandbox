"""Tests for ArkParseError and graceful parser error reporting."""

import sys
from pathlib import Path

import pytest

# Same sys.path trick as conftest.py, in case this test is run solo.
_ARK_ROOT = Path(__file__).resolve().parent.parent
_PARSER_DIR = _ARK_ROOT / "tools" / "parser"
if str(_PARSER_DIR) not in sys.path:
    sys.path.insert(0, str(_PARSER_DIR))

from ark_parser import parse, ArkParseError  # noqa: E402


def test_parse_error_has_position():
    """A deliberately broken source should raise ArkParseError with
    a non-zero line/column and a non-empty snippet."""
    src = "class Vehicle { $data xyz abc }"
    with pytest.raises(ArkParseError) as excinfo:
        parse(src)
    err = excinfo.value
    assert err.line >= 1
    assert err.column >= 1
    assert err.snippet, "snippet should be non-empty"
    # The report should be renderable end-to-end.
    report = err.format_report()
    assert "error:" in report


def test_parse_error_format_report_has_caret():
    """An ArkParseError.format_report() must contain '^' and file path."""
    err = ArkParseError(
        message="unexpected token 'foo'",
        file_path="specs/fake.ark",
        line=2,
        column=5,
        snippet="1 | class X {\n2 |     $data foo bar\n3 | }",
        caret="      ^^^^^ expected ':'",
        expected=[":"],
    )
    report = err.format_report()
    assert "^" in report
    assert "specs/fake.ark" in report
    assert "unexpected token 'foo'" in report


def test_parse_error_unexpected_eof():
    """An unterminated class body should raise an ArkParseError whose
    message mentions EOF or a closing brace."""
    src = "class Vehicle {"
    with pytest.raises(ArkParseError) as excinfo:
        parse(src)
    err = excinfo.value
    lowered = err.message.lower()
    assert ("eof" in lowered) or ("end of" in lowered) or ("}" in err.message) \
        or ("}" in err.format_report())
