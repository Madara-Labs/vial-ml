import pytest
from pathlib import Path
from vial import Vial

SAMPLE_SOURCE = """\
import os
import json

MAX_RETRIES = 3

def helper():
    return 1

def process_payment(amount: float) -> dict:
    return {"amount": amount, "status": "pending"}

class PaymentProcessor:
    def __init__(self, key: str):
        self.key = key

    def charge(self, amount: float) -> dict:
        return process_payment(amount)
"""


@pytest.fixture
def source_file(tmp_path):
    f = tmp_path / "billing.py"
    f.write_text(SAMPLE_SOURCE)
    return f


@pytest.fixture
def vial(tmp_path, source_file):
    return Vial(workspace_dir=tmp_path / ".vial")


def test_extract_creates_isolated_file(vial, source_file):
    isolated = vial.extract(source_file, "process_payment")
    assert Path(isolated).exists()
    content = Path(isolated).read_text()
    assert "def process_payment" in content


def test_extract_includes_context_header(vial, source_file):
    isolated = vial.extract(source_file, "process_payment")
    content = Path(isolated).read_text()
    assert "import os" in content
    assert "import json" in content
    assert "MAX_RETRIES = 3" in content


def test_extract_header_is_commented_out(vial, source_file):
    isolated = vial.extract(source_file, "process_payment")
    lines = Path(isolated).read_text().splitlines()
    header_lines = [l for l in lines if l.startswith("# ") and "import" in l]
    assert len(header_lines) > 0


def test_merge_splices_changes_back(vial, source_file):
    vial.extract(source_file, "process_payment")
    isolated_path = vial.workspace.isolated_path("process_payment")
    # Simulate agent rewriting the isolated file
    isolated_path.write_text(
        Path(isolated_path).read_text().replace(
            'return {"amount": amount, "status": "pending"}',
            'if amount <= 0:\n        raise ValueError("negative")\n    return {"amount": amount, "status": "ok"}',
        )
    )
    vial.merge()
    final = source_file.read_text()
    assert 'raise ValueError("negative")' in final
    assert "def helper" in final


def test_merge_raises_on_invalid_syntax(vial, source_file):
    vial.extract(source_file, "process_payment")
    isolated_path = vial.workspace.isolated_path("process_payment")
    # Write invalid Python into the isolated file (below the delimiter)
    content = Path(isolated_path).read_text()
    delimiter = "#" + "=" * 40 + " END OF CONTEXT " + "=" * 40
    if delimiter in content:
        header, _ = content.split(delimiter, 1)
        Path(isolated_path).write_text(header + delimiter + "\ndef broken(\n    return 1\n")
    else:
        Path(isolated_path).write_text("def broken(\n    return 1\n")
    with pytest.raises(ValueError, match="invalid Python"):
        vial.merge()


def test_merge_cleans_up_workspace(vial, source_file):
    vial.extract(source_file, "process_payment")
    isolated_path = vial.workspace.isolated_path("process_payment")
    vial.merge()
    assert not isolated_path.exists()
    assert not vial.workspace.metadata_path.exists()


def test_extract_method_is_dedented(vial, source_file):
    isolated = vial.extract(source_file, "charge")
    content = Path(isolated).read_text()
    # The isolated code must be valid standalone Python
    import ast
    code_only = content.split("#" + "=" * 40 + " END OF CONTEXT " + "=" * 40)[-1].strip()
    ast.parse(code_only)  # raises if indented
    assert "def charge" in code_only
    assert not any(line.startswith("    def") for line in code_only.splitlines()[:1])


def test_merge_method_splices_back_correctly(vial, source_file):
    vial.extract(source_file, "charge")
    isolated_path = vial.workspace.isolated_path("charge")
    content = Path(isolated_path).read_text()
    Path(isolated_path).write_text(
        content.replace(
            "return process_payment(amount)",
            "return process_payment(amount * 2)",
        )
    )
    vial.merge()
    final = source_file.read_text()
    assert "return process_payment(amount * 2)" in final
    assert "class PaymentProcessor" in final
    assert "def __init__" in final


def test_extract_class(vial, source_file):
    isolated = vial.extract(source_file, "PaymentProcessor")
    content = Path(isolated).read_text()
    assert "class PaymentProcessor" in content
    assert "def charge" in content
