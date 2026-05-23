import json
import pytest
from pathlib import Path
from vial.workspace import Workspace


def test_workspace_creates_directory(tmp_path):
    ws = Workspace(tmp_path / ".vial")
    assert ws.dir.exists()


def test_save_and_load_metadata(tmp_path):
    ws = Workspace(tmp_path / ".vial")
    meta = {
        "source_filepath": "/some/file.py",
        "target_name": "my_func",
        "start_line": 10,
        "end_line": 20,
        "isolated_filepath": str(ws.dir / "my_func_isolated.py"),
    }
    ws.save_metadata(meta)
    loaded = ws.load_metadata()
    assert loaded == meta


def test_load_metadata_raises_when_missing(tmp_path):
    ws = Workspace(tmp_path / ".vial")
    with pytest.raises(FileNotFoundError):
        ws.load_metadata()


def test_isolated_path(tmp_path):
    ws = Workspace(tmp_path / ".vial")
    p = ws.isolated_path("calculate_taxes")
    assert p.name == "calculate_taxes_isolated.py"
    assert p.parent == ws.dir


def test_cleanup_removes_files(tmp_path):
    ws = Workspace(tmp_path / ".vial")
    isolated = ws.isolated_path("foo")
    isolated.write_text("def foo(): pass")
    ws.save_metadata({"source_filepath": "x", "target_name": "foo",
                       "start_line": 0, "end_line": 1,
                       "isolated_filepath": str(isolated)})
    ws.cleanup()
    assert not isolated.exists()
    assert not ws.metadata_path.exists()
