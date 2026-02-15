# Architecture Overview

This document summarizes the `src/` layout.

## Top-Level under `src/`

- `Typhon/`: Main implementation package.

## `Typhon/` Package Map

- `__main__.py`: CLI entry point (`typhon`).
- `Driver/`: Command orchestration for run/translate/type-check/language-server flows.
- `Grammar/`: Tokenizer/parser/AST definitions and grammar artifacts. Important files include:
  - `typhon.gram`: grammar definition for parser generation.
  - `typhon_ast.py`: AST node definitions. Extends Python `ast` objects using dynamic attributes.
- `Transform/`: AST rewrite pipeline (desugaring, safety checks, normalization).
- `Typing/`: Type-check backends and diagnostics (`basedpyright`/`pyrefly`).
- `SourceMap/`: Source mapping between Typhon and generated Python for diagnostics and editor features.
- `LanguageServer/`: LSP integration, diagnostics, semantic tokens, and checker clients.
- `Utils/`: Cross-directory shared public utility APIs (for example, path-related helpers).

## Data Flow (High Level)

1. Parse Typhon source in `Grammar/`.
2. Apply language transforms in `Transform/`.
3. Build mappings in `SourceMap/` as needed.
4. Run type diagnostics through `Typing/`.
5. Execute command workflows via `Driver/` or serve editor features via `LanguageServer/`.

## Notes

- Do not manually edit `Grammar/_typhon_parser.py`; regenerate it via the build script. It is generated from `Grammar/typhon.gram` by command `uv run -m script.build`.
- Keep this document brief and update it when package responsibilities change.
