# SKILLS

## Purpose

This file defines the minimum operational playbook for agents in this repository.

## Script Operations (Minimum)

Use these script entry points as the default workflow.

### Run Typhon

- Command: `uv run -m script.run`
- Use when running the language entry flow.

### Build / Setup

- Command: `uv run -m script.build`
- Use to regenerate grammar and prepare packaging/build artifacts.

### Run Tests

- Command: `uv run -m script.test.all`
- Use for the repository test execution flow.
- Command: `uv run -m script.test.lsp <test_name>`
- Command: `uv run -m script.test.grammar <test_name>`
- Command: `uv run -m script.test.run`
- Use for specific test categories. `<test_name>` is optional, to specify relative test path from
  - `test/Grammar` for grammar tests.
  - `test/LanguageServer` for LSP tests.
  - `test/Execute` for execution tests (`script.test.run`).

### Upload Package (Forbidden)

- Command: `uv run -m script.upload`
- Do not run by default. Run only when the user explicitly requests publishing.

## Execution Notes

- Use `uv run -m ...` as the default execution style for project scripts.
- Prefer script modules over ad-hoc shell commands.
- Keep command usage predictable and reproducible.
- Keep comments and explanatory notes in English.
