# AGENTS

## Purpose
This file defines the shared, tool-agnostic rules for automated coding agents in this repository.

## Repository Rules
1. Keep changes minimal and focused on the requested task.
2. Do not refactor unrelated files.
3. Do not manually edit generated parser output:
   - `src/Typhon/Grammar/_typhon_parser.py`
   - Regenerate it through the build script instead.
4. Prefer project scripts for routine operations (build, test, run, upload).
5. Run quality checks when relevant to the change:
   - formatting (`uv run -m ruff format`)
   - type checking (`basedpyright`) (Type error still exists, but try to minimize new ones)
   - tests (`uv run -m script.test.all`)
6. Never run release/upload operations unless the user explicitly asks.

## Language and Comment Policy
- All newly added comments must be written in English.
- All newly added documentation text must be written in English.
- If you modify existing comments, keep them in English.
- Keep comments concise and avoid long prose.
- Write sentence-style comments only for truly complex parts.

## Safety
- Avoid destructive file operations unless explicitly requested.
- For high-impact actions (publishing, deleting artifacts, changing packaging metadata), ask for confirmation first.

## Project description

This project is an implementation of programming language Typhon.
The core features:
- Translated to Python and has seamless interoperability with it.
- Typescript like brace scoping with optional semicolons
- Builtin static type checking with basedpyright
- Static lexical scoping

## Project Structure

- All packages are managed by `uv`.
- Source code is under `src/`.
- Tests are under `test/`.
- Scripts are under `script/`.
- Documentation is under `doc/`.
- Generated parser output is under `src/Typhon/Grammar/_typhon_parser.py` (do not edit manually).

