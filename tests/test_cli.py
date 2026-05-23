import pytest
from pathlib import Path
from typer.testing import CliRunner
from vial.cli import app

runner = CliRunner()

SAMPLE = """\
import os

def greet(name: str) -> str:
    return f"Hello, {name}"

def farewell(name: str) -> str:
    return f"Goodbye, {name}"
"""


@pytest.fixture
def source_file(tmp_path):
    f = tmp_path / "greetings.py"
    f.write_text(SAMPLE)
    return f


def test_extract_command_creates_isolated_file(source_file, tmp_path):
    result = runner.invoke(
        app,
        ["extract", str(source_file), "greet", "--workspace", str(tmp_path / ".vial")],
    )
    assert result.exit_code == 0
    assert "Isolated" in result.output
    isolated = tmp_path / ".vial" / "greet_isolated.py"
    assert isolated.exists()


def test_extract_command_shows_isolated_path(source_file, tmp_path):
    result = runner.invoke(
        app,
        ["extract", str(source_file), "greet", "--workspace", str(tmp_path / ".vial")],
    )
    assert "greet_isolated.py" in result.output


def test_extract_nonexistent_target_exits_nonzero(source_file, tmp_path):
    result = runner.invoke(
        app,
        ["extract", str(source_file), "no_such_func", "--workspace", str(tmp_path / ".vial")],
    )
    assert result.exit_code != 0


def test_merge_command_splices_back(source_file, tmp_path):
    ws = tmp_path / ".vial"
    runner.invoke(app, ["extract", str(source_file), "greet", "--workspace", str(ws)])
    isolated = ws / "greet_isolated.py"
    content = isolated.read_text()
    isolated.write_text(content.replace('return f"Hello, {name}"', 'return f"Hi, {name}!"'))
    result = runner.invoke(app, ["merge", "--workspace", str(ws)])
    assert result.exit_code == 0
    assert "greet" in result.output
    assert 'Hi, {name}' in source_file.read_text()


def test_merge_without_prior_extract_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["merge", "--workspace", str(tmp_path / ".vial")])
    assert result.exit_code != 0
