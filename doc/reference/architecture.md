# Architecture Overview

This document provides a concise map of the `src/` layout.

## Top-Level under `src/`

- `Typhon/`: main implementation package.

## `Typhon/` Package Map

- `__main__.py`: CLI entry point (`typhon`).
- `Driver/`: command orchestration for run/translate/type-check/language-server flows.
- `Grammar/`: tokenizer/parser/AST definitions and grammar artifacts. Important files are:
  - `typhon.gram`: grammar definition for parser generation.
  - `typhon_ast.py`: AST node definitions. Extends Python `ast` objects using ad hoc `getattr`/`setattr`.
- `Transform/`: AST rewrite pipeline (desugaring, safety checks, normalization).
- `Typing/`: type-check backends and result diagnostics (`pyright`/`pyrefly`). The main type checker is `basedpyright` (called `pyright`).
- `SourceMap/`: source-to-source mapping between Typhon code and generated Python code, for diagnostics, error reporting, and language server features.
- `LanguageServer/`: LSP server integration, diagnostics, semantic tokens, and checker clients.

## Data Flow (High Level)

1. Parse Typhon source in `Grammar/`.
2. Apply language transforms in `Transform/`.
3. Build mappings in `SourceMap/` as needed.
4. Run type diagnostics through `Typing/`.
5. Execute command workflows via `Driver/` or serve editor features via `LanguageServer/`.

## Notes

- Do not manually edit `Grammar/_typhon_parser.py`; regenerate it via the build script. It is generated from `Grammar/typhon.gram` by command `uv run -m script.build`.
- Keep this document brief and update it when package responsibilities change.
