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

## How this compares to standard approaches

Every AI coding tool has to solve the same problem: the model needs to see relevant code without consuming the entire codebase. Here's how common approaches compare to Vial.

### Claude Code / Gemini CLI — shell-tool exploration

Terminal-native agents hand the model shell tools (`grep`, `find`, `cat`) and let it explore the repo the way a new hire would — searching for keywords, opening files one at a time. For a question like "what calls `process_payment`?", an agent might open 10–25 files and burn tens of thousands of tokens before writing a single line. The model sees everything it found, not just what it needs.

Independent measurements on real codebases put Claude Code's grep-only mode at **108,000–117,000 tokens** for a single targeted task ([source](https://dev.to/marjoballabani/your-ai-agent-wastes-87-of-its-tokens-just-finding-code-i-fixed-that-4d5p)). Those measurements were on larger codebases than Vial's benchmark fixture — direct comparison isn't apples-to-apples — but the dynamic is the same: the agent reads far more than it needs.

### GitHub Copilot — cursor-proximity windowing

Copilot focuses context on the area around the cursor and recently open files. This is fast and works well for completions, but the agent has no understanding of where a function starts and ends — it sends a fixed character window, which may include half a function above and half a function below the target. Inline completions use an 8–16k token local window; agent mode uses the full model context ([source](https://tokenlimits.app/blog/copilot-context-window-limit)).

### Cursor — RAG + embeddings

Cursor indexes the codebase and retrieves semantically relevant chunks via embeddings. Better than raw grep, but retrieval returns *chunks* (fixed line ranges), not *semantic units* (full function/class boundaries). A retrieved chunk can cut off mid-function, leaving the agent with incomplete context ([source](https://www.nxcode.io/resources/news/cursor-vs-claude-code-vs-github-copilot-2026-ultimate-comparison)).

### Aider — whole-file map

Aider builds a repo-map summarising every file's symbols and sends relevant whole files to the model. More precise than grep, but the unit of context is still the whole file. A 500-line file gets sent even if only a 20-line function needs changing. With structural retrieval Aider uses 8,500–13,000 tokens per task — better than grep-mode agents, but still file-scoped ([source](https://dev.to/marjoballabani/your-ai-agent-wastes-87-of-its-tokens-just-finding-code-i-fixed-that-4d5p)).

### Vial — AST-bounded isolation

Vial uses Python's AST to find the exact start and end line of the target, so the isolated file always contains exactly one complete, syntactically valid function or class — nothing more. Surrounding code is never included, never at risk of accidental modification, and never charged as tokens.

```
Approach          Context unit       Risk of side-effects    Token cost
──────────────────────────────────────────────────────────────────────
grep / cat        Whole file         High                    High
Cursor RAG        Fixed-line chunk   Medium (cut-off risk)   Medium
Aider map         Whole file         Medium                  Medium-High
Vial              Single AST node    None                    Low (71–88% less)
```

The tradeoff: Vial works at the function/class level. It is not a replacement for tools that handle cross-file refactors or project-wide search — it is the right tool once you know *what* to edit.

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
