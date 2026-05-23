import pytest
from pathlib import Path
from vial.extractor import find_target, ExtractionResult

SAMPLE = """\
import os

MAX_RETRIES = 3

def simple_func():
    return 42

async def async_func(x: int) -> int:
    return x * 2

class MyClass:
    def __init__(self):
        self.value = 0

    def method(self):
        return self.value
"""


def test_finds_simple_function():
    result = find_target(SAMPLE, "simple_func")
    assert result.target_name == "simple_func"
    assert "def simple_func" in result.code
    assert "return 42" in result.code


def test_finds_async_function():
    result = find_target(SAMPLE, "async_func")
    assert "async def async_func" in result.code
    assert "return x * 2" in result.code


def test_finds_class_with_methods():
    result = find_target(SAMPLE, "MyClass")
    assert "class MyClass" in result.code
    assert "def __init__" in result.code
    assert "def method" in result.code


def test_raises_on_missing_target():
    with pytest.raises(ValueError, match="not found"):
        find_target(SAMPLE, "nonexistent_function")


def test_result_has_correct_line_bounds():
    result = find_target(SAMPLE, "simple_func")
    # start_line is 0-indexed
    assert result.start_line >= 0
    assert result.end_line > result.start_line


def test_result_code_matches_source_lines():
    lines = SAMPLE.splitlines()
    result = find_target(SAMPLE, "simple_func")
    expected = "\n".join(lines[result.start_line : result.end_line])
    assert result.code == expected
