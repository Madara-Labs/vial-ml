"""
Benchmark: measures token efficiency of Vial isolation vs. full-file exposure.

No API calls required. Uses character count as a proxy for token count
(1 token ≈ 4 chars for English/code text).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vial import Vial

FIXTURE = Path(__file__).parent / "fixtures" / "large_module.py"
WORKSPACE = Path(__file__).parent / ".benchmark_workspace"
TARGETS = ["compute_hash", "read_config", "write_config", "ConnectionPool", "ConfigManager", "EventBus"]


def char_to_tokens(chars: int) -> float:
    return chars / 4.0


def run():
    full_source = FIXTURE.read_text()
    full_chars = len(full_source)
    full_tokens = char_to_tokens(full_chars)

    print(f"\n{'='*60}")
    print(f"Benchmark: {FIXTURE.name}  ({len(full_source.splitlines())} lines)")
    print(f"{'='*60}")
    print(f"{'Target':<20} {'Isolated chars':>15} {'Isolated tokens':>16} {'Savings':>10}")
    print(f"{'-'*60}")

    for target in TARGETS:
        v = Vial(workspace_dir=WORKSPACE / target)
        isolated_path = v.extract(FIXTURE, target)
        isolated_content = Path(isolated_path).read_text()
        iso_chars = len(isolated_content)
        iso_tokens = char_to_tokens(iso_chars)
        savings_pct = (1 - iso_tokens / full_tokens) * 100
        print(f"{target:<20} {iso_chars:>15,} {iso_tokens:>16.0f} {savings_pct:>9.1f}%")
        # cleanup so the fixture file is not modified
        v.workspace.cleanup()

    print(f"{'-'*60}")
    print(f"{'Full file':<20} {full_chars:>15,} {full_tokens:>16.0f} {'baseline':>10}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()
