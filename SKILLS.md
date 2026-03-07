# SKILLS

## Purpose

This file defines the minimum operational playbook for agents in this repository.

## Operational Playbook

Use this file for command-level workflows. Policy rules remain authoritative in `AGENTS.md`.

### Core Commands

#### Run Typhon

- Command: `uv run -m script.run`
- Use when running the language entry flow.

#### Build / Setup

- Command: `uv run -m script.build`
- Use to regenerate grammar and prepare packaging/build artifacts.

### Quality and Tests

- Formatting: `uv run -m ruff format`
- Type checking: `basedpyright`

#### Run Tests

- Full suite commands:
  - `uv run -m script.test.all`
  - `uv run -m script.test.all --parallel`
  - `uv run -m script.test.all --debug-verbose`
  - `uv run -m script.test.all --parallel --debug-verbose`
- Targeted suite commands:
  - Command: `uv run -m script.test.lsp <test_name>`
  - Command: `uv run -m script.test.grammar <test_name>`
  - Command: `uv run -m script.test.execute <test_name>`
  - Command: `uv run -m script.test.files <test_files...>`
  - Use for specific test categories. `<test_name>` is optional, to specify relative test path from:
  - `test/Grammar` for grammar tests.
  - `test/LanguageServer` for LSP tests.
  - `test/Execute` for execution tests (`script.test.execute`).
- Common test options:
  - `--parallel`: parallel run with xdist.
  - `--debug-verbose`: verbose debug logging for test code and runners.
  - Options can be combined.
- Policy note: final gate requirements are defined in `AGENTS.md`.

### Performance

#### Run Benchmark

- Command: `uv run -m script.benchmark.parse_large_file`
- Use to benchmark parse/transform/unparse (and optional source-map build) with an auto-generated large Typhon file.

#### Run Profiling

- Command: `uv run -m script.benchmark.profile_parse`
- Use to collect profiling data for parse processing.

### Release

#### Upload Package (Forbidden)

- Command: `uv run -m script.upload`
- Do not run by default. Run only when the user explicitly requests publishing.

## Execution Notes

- Use `uv run -m ...` as the default execution style for project scripts.
- Prefer script modules over ad-hoc shell commands.
- Keep command usage predictable and reproducible.
- Keep comments and explanatory notes in English.
