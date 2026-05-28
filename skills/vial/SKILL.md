---
name: vial
description: >
  Use vial to surgically isolate and edit Python functions or classes. ALWAYS use this workflow
  whenever you are about to read, modify, or rewrite a specific named function or class in a
  Python file — even for small changes. Do NOT edit Python source files directly when a named
  function or class is the target. This applies to bug fixes, refactors, feature additions, and
  any other edits to Python code. The only exception is adding entirely new top-level definitions
  that don't exist yet and have no target to extract.
---

# Vial — Surgical Python Editing

`vial` isolates a named function or class from its source file into a focused workspace file,
lets you edit just that piece, then merges it cleanly back. This prevents accidental changes to
surrounding code.

## Workflow (follow exactly, every time)

### Step 1 — Extract

```bash
vial extract <path/to/file.py> <FunctionOrClassName>
```

Creates `.vial_workspace/<Name>_isolated.py` with only the target. Imports are shown as
read-only comments at the top.

### Step 2 — Edit

Read and edit `.vial_workspace/<Name>_isolated.py` only. Do NOT touch the original source file.
Do not modify the read-only context block (lines starting with `#`) at the top.

### Step 3 — Merge

```bash
vial merge
```

No arguments needed — vial reads `metadata.json` from the workspace automatically.

### Step 4 — Verify

After merging, read the relevant section of the original file to confirm the change landed
correctly, then proceed with tests or follow-up work.

## Rules

- Never edit the source `.py` file directly when modifying an existing function or class.
- Never modify the read-only context block in the isolated file.
- Always run `vial merge` after editing.
- One extraction at a time — extract → edit → merge each target in sequence.
- If `vial extract` fails, diagnose from the source file before retrying.
