import pytest
from pathlib import Path
from vial import Vial

SAMPLE_SOURCE = """\
import os

class PaymentProcessor:
    def __init__(self, key: str):
        self.key = key
        
    def charge(self, amount: float) -> dict:
        print("Charging", amount)
        return {"amount": amount, "status": "ok"}
        
    def refund(self, amount: float) -> dict:
        return {"amount": amount, "status": "refunded"}
        
    def _helper(self):
        pass
"""

@pytest.fixture
def source_file(tmp_path):
    f = tmp_path / "billing.py"
    f.write_text(SAMPLE_SOURCE)
    return f

@pytest.fixture
def vial(tmp_path):
    return Vial(workspace_dir=tmp_path / ".vial")

def test_extract_class_shape(vial, source_file):
    isolated = vial.extract(source_file, "PaymentProcessor", methods=["charge"])
    content = Path(isolated).read_text()
    
    # Check that charge is fully extracted
    assert 'print("Charging", amount)' in content
    
    # Check that refund and __init__ are stubbed
    assert 'return {"amount": amount, "status": "refunded"}' not in content
    assert 'self.key = key' not in content
    assert 'pass  # stub' in content
    
    # Check that the class header is present
    assert 'class PaymentProcessor:' in content

def test_merge_class_shape_modifies_target_method(vial, source_file):
    isolated = vial.extract(source_file, "PaymentProcessor", methods=["charge"])
    isolated_path = Path(isolated)
    
    # Modify the charge method
    content = isolated_path.read_text()
    new_content = content.replace('status": "ok"', 'status": "success"')
    isolated_path.write_text(new_content)
    
    vial.merge()
    
    final_source = source_file.read_text()
    assert 'status": "success"' in final_source
    # Ensure other methods are untouched
    assert 'return {"amount": amount, "status": "refunded"}' in final_source

def test_merge_class_shape_ignores_stub_modifications(vial, source_file):
    isolated = vial.extract(source_file, "PaymentProcessor", methods=["charge"])
    isolated_path = Path(isolated)
    
    # Maliciously modify a stub (e.g. refund) in the isolated file
    content = isolated_path.read_text()
    new_content = content.replace('pass  # stub', 'print("malicious")')
    isolated_path.write_text(new_content)
    
    vial.merge()
    
    final_source = source_file.read_text()
    # The malicious print should NOT be in the merged file
    assert 'print("malicious")' not in final_source
    # The original refund implementation should still be there
    assert 'return {"amount": amount, "status": "refunded"}' in final_source

def test_merge_class_shape_adds_new_methods(vial, source_file):
    isolated = vial.extract(source_file, "PaymentProcessor", methods=["charge"])
    isolated_path = Path(isolated)
    
    # Add a completely new method
    content = isolated_path.read_text()
    new_method = "\n    def new_method(self):\n        return True\n"
    new_content = content + new_method
    isolated_path.write_text(new_content)
    
    vial.merge()
    
    final_source = source_file.read_text()
    assert 'def new_method(self):' in final_source
    assert 'return True' in final_source
    # Should still have the old methods
    assert 'return {"amount": amount, "status": "refunded"}' in final_source
