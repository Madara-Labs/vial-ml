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

def target_func():
    print(os.environ)
    print(MAX_RETRIES)
    my_func()
"""


def test_extracts_used_imports():
    ctx = extract_context(SAMPLE, "target_func")
    assert "import os" in ctx
    assert "import json" not in ctx
    assert "from pathlib import Path" not in ctx


def test_extracts_used_global_assignments():
    ctx = extract_context(SAMPLE, "target_func")
    assert "MAX_RETRIES = 3" in ctx
    assert "DEFAULT_TIMEOUT = 30" not in ctx


def test_includes_called_function_stubs():
    ctx = extract_context(SAMPLE, "target_func")
    assert "def my_func():" in ctx
    assert "pass  # stub" in ctx


def test_empty_file_returns_empty_string():
    ctx = extract_context("", "target_func")
    assert ctx == ""
