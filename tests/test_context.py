import ast
import pytest
from vial.context import extract_context

SAMPLE = """\
import os
import json
from pathlib import Path

MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

def my_func():
    pass

class MyClass:
    pass
"""


def test_extracts_imports():
    ctx = extract_context(SAMPLE)
    assert "import os" in ctx
    assert "import json" in ctx
    assert "from pathlib import Path" in ctx


def test_extracts_global_assignments():
    ctx = extract_context(SAMPLE)
    assert "MAX_RETRIES = 3" in ctx
    assert "DEFAULT_TIMEOUT = 30" in ctx


def test_does_not_include_function_defs():
    ctx = extract_context(SAMPLE)
    assert "def my_func" not in ctx


def test_does_not_include_class_defs():
    ctx = extract_context(SAMPLE)
    assert "class MyClass" not in ctx


def test_empty_file_returns_empty_string():
    ctx = extract_context("")
    assert ctx == ""
