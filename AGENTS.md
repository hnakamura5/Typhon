# AGENTS

## Purpose

This file defines the shared, tool-agnostic rules for automated coding agents in this repository.

## Repository Rules

### General

- Keep changes minimal and focused on the requested task.
- Do not refactor unrelated files.
- Keep documentation updates in sync with code changes.
- For large feature work, create a brief implementation overview, get review, then implement.
- When changing existing tests, summarize planned test changes and reasons, then get review before applying.

### Testing

- Run quality checks when relevant:
  - formatting: `uv run -m ruff format`
  - type checking: `basedpyright` (existing type errors may exist; avoid adding new ones)
  - tests (default): `uv run -m script.test.all`
- `script.test.all` supports `--parallel` and `--debug-verbose` (combinable).
- Before reporting task completion, always run `uv run -m script.test.all --parallel` as the final test gate.
- For command recipes and examples, use `SKILLS.md` as the operational reference.

### Script and Build

- Prefer project scripts for routine operations (build, test, run, upload).
- Standardize script execution with `uv run -m ...`.
- Do not manually edit generated parser output `src/Typhon/Grammar/_typhon_parser.py`; regenerate via build scripts.

### Naming and Utility Placement

- Consider reusable utility API design when introducing utility logic.
- Extract common utilities selectively (typically when used in 2+ places or clearly expected to be reused soon).
- Internal helper naming:
  - module: `_utils.py`
  - package: `_utils/`
- Cross-directory shared/public utility API: `src/Typhon/Utils/<domain>.py`.
- Do not introduce new internal `utils.py` or `utils/` names.
- If private `_utils` APIs need cross-directory imports under `src/`, promote them to `src/Typhon/Utils/` and update call sites.
- Tests under `test/` may import private `_utils` APIs for white-box testing.

### Coding Conventions

- During refactoring, do not keep compatibility layers unless explicitly requested; update affected imports in the same task.
- For type annotations, prefer `typing` imports over `collections.abc`.
- For generics, prefer Python generic syntax (e.g., `class Box[T]: ...`, `def f[T](x: T) -> T: ...`) over introducing `TypeVar` unless explicitly required.

## Language and Comment Policy

- All newly added comments must be written in English.
- All newly added documentation text must be written in English.
- If you modify existing comments, keep them in English.
- Keep comments concise and avoid long prose.
- Write sentence-style comments only for truly complex parts.
- In documentation, prefer concise key points and practical examples over long explanations or decorative writing.

## Safety

- Avoid destructive file operations unless explicitly requested.
- For high-impact actions (publishing, deleting artifacts, changing packaging metadata), ask for confirmation first.
- Never run release/upload operations.

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
- For `src/` package responsibilities and data flow, see `doc/reference/architecture.md`.
- Generated parser output is under `src/Typhon/Grammar/_typhon_parser.py` (do not edit manually).
