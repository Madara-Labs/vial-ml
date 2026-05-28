# Vial

Surgical code isolation for AI agents.

Vial extracts a single function or class from a large Python file into a clean, focused workspace file so an agent only sees — and edits — exactly what it needs to.

## Install

```bash
pip install vial-ml
# or with uv:
uv add vial-ml
```

## CLI

```bash
# Isolate a function
vial extract billing.py process_payment

# Agent edits .vial_workspace/process_payment_isolated.py ...

# Stitch it back (validates syntax first)
vial merge
```

## Python API

```python
from vial import Vial

v = Vial()
isolated_path = v.extract("billing.py", "process_payment")
# agent edits isolated_path ...
v.merge()
```

## Token efficiency

Vial reduces the context an agent sees to only what matters. On a representative 175-line module:

```
Target            Isolated tokens    Full-file tokens    Savings
----------------------------------------------------------------
compute_hash               ~139              ~1,172        88%  ████████████████████████████░░░
read_config                ~148              ~1,172        87%  ███████████████████████████░░░░
write_config               ~156              ~1,172        87%  ███████████████████████████░░░░
ConnectionPool             ~297              ~1,172        75%  ███████████████████████░░░░░░░░
ConfigManager              ~290              ~1,172        75%  ███████████████████████░░░░░░░░
EventBus                   ~337              ~1,172        71%  ██████████████████████░░░░░░░░░
```

Token estimate: 1 token ≈ 4 characters (standard approximation for code).

### Run it yourself

```bash
git clone https://github.com/Madara-Labs/vial-ml
cd vial-ml
uv run python benchmarks/run_benchmark.py
```

No API key needed — the benchmark uses only local file analysis.

## Why

When an agent reads a 2,000-line file to fix a 20-line function it wastes tokens, risks editing the wrong code, and produces complex diffs that frequently fail. Vial reduces the context to only what matters, cutting token usage by 71–88% on typical files.

## How it works

1. **Extract** — AST-based line-bound finder locates the exact start/end of the target. A protected context header (imports + module-level globals, commented out) is prepended so the agent has the context it needs without being able to accidentally modify it.
2. **Edit** — The agent modifies only the isolated file.
3. **Merge** — Vial validates the modified code's syntax, then splices it back into the original file at the exact line range. Surrounding code is never touched.

All session state lives in a `metadata.json` file inside the workspace directory.

## Dependencies

| Package | Purpose |
|---|---|
| [`typer`](https://github.com/fastapi/typer) | CLI interface |

The standard library covers everything else: `ast` for parsing, `pathlib` for file I/O, `json` for workspace state.
