import ast
import pytest
from pathlib import Path
from vial.merger import validate_syntax, strip_header, splice_back

HEADER_DELIMITER = "#" + "=" * 40 + " END OF CONTEXT " + "=" * 40

ORIGINAL = """\
import os

MAX_RETRIES = 3

def helper():
    return 1

def process_payment(amount: float) -> dict:
    return {"amount": amount, "status": "pending"}

def another():
    return 2
"""


def test_validate_syntax_accepts_valid_code():
    ok, msg = validate_syntax("def foo():\n    return 1\n")
    assert ok is True
    assert msg == ""


def test_validate_syntax_rejects_invalid_code():
    ok, msg = validate_syntax("def foo(\n    return 1\n")
    assert ok is False
    assert "SyntaxError" in msg


def test_strip_header_removes_header_block():
    content = f"# context\n# import os\n{HEADER_DELIMITER}\ndef foo():\n    return 1\n"
    code = strip_header(content, HEADER_DELIMITER)
    assert "# context" not in code
    assert "def foo" in code


def test_strip_header_passthrough_when_no_delimiter():
    content = "def foo():\n    return 1\n"
    code = strip_header(content, HEADER_DELIMITER)
    assert "def foo" in code


def test_splice_back_replaces_target_lines(tmp_path):
    original_file = tmp_path / "original.py"
    original_file.write_text(ORIGINAL)

    modified_func = "def process_payment(amount: float) -> dict:\n    if amount <= 0:\n        raise ValueError('negative')\n    return {'amount': amount, 'status': 'ok'}"

    # process_payment starts at line index 7 (0-indexed), ends at index 9
    result = splice_back(
        source_filepath=original_file,
        modified_code=modified_func,
        start_line=7,
        end_line=9,
    )
    assert result.exists()
    content = result.read_text()
    assert "raise ValueError" in content
    assert "def helper" in content
    assert "def another" in content


def test_splice_back_reindents_with_indent(tmp_path):
    original = "class Foo:\n    def bar(self):\n        return 1\n"
    original_file = tmp_path / "original.py"
    original_file.write_text(original)

    # agent edits dedented code; splice_back must re-indent it
    modified = "def bar(self):\n    return 99"
    splice_back(
        source_filepath=original_file,
        modified_code=modified,
        start_line=1,
        end_line=3,
        indent="    ",
    )
    content = original_file.read_text()
    assert "    def bar(self):" in content
    assert "        return 99" in content


def test_splice_back_preserves_surrounding_code(tmp_path):
    original_file = tmp_path / "original.py"
    original_file.write_text(ORIGINAL)

    modified_func = "def process_payment(amount: float) -> dict:\n    return {'amount': amount * 2, 'status': 'ok'}"

    splice_back(
        source_filepath=original_file,
        modified_code=modified_func,
        start_line=7,
        end_line=9,
    )
    content = original_file.read_text()
    assert "import os" in content
    assert "MAX_RETRIES = 3" in content
    assert "def helper" in content
    assert "def another" in content
