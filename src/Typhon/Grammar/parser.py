import ast
from pathlib import Path
import sys
import tokenize
import os
import io

from typing import (
    Literal,
    Union,
    Optional,
)

from ..Driver.debugging import is_debug_verbose

from .tokenizer_custom import TokenizerCustom, show_token
from .token_factory_custom import token_stream_factory
from ._typhon_parser import parse
from .typhon_ast_error import gather_errors


def parse_file(
    file_path: str,
    py_version: Optional[tuple[int, int]] = None,
    verbose: bool = False,
) -> ast.Module:
    """Parse a file."""
    with open(file_path) as f:
        if is_debug_verbose():
            show_token(Path(file_path).read_text())
        tok_stream = token_stream_factory(f.readline)
        tokenizer = TokenizerCustom(tok_stream, verbose=verbose, path=file_path)
        parsed = parse_tokenizer(
            tokenizer,
            py_version=py_version,
            verbose=verbose,
        )
        assert isinstance(parsed, ast.Module), f"Parsing failed: {parsed}"
        gather_errors(parsed)
        return parsed


def parse_tokenizer(
    tokenizer: TokenizerCustom,
    py_version: Optional[tuple[int, int]] = None,
    verbose: bool = False,
) -> ast.AST:
    """Parse using a tokenizer."""
    parsed = parse(
        filename="<tokenizer>",
        tokenizer=tokenizer,
        mode="file",
        py_version=py_version,
        verbose=verbose,
    )
    # Must be successful parse
    assert isinstance(parsed, ast.AST), f"Parsing failed: {parsed}"
    gather_errors(parsed)
    return parsed


def parse_string(
    source: str,
    mode: Union[Literal["eval"], Literal["exec"]] = "exec",
    py_version: Optional[tuple[int, int]] = None,
    verbose: bool = False,
) -> ast.AST | None:
    """Parse a string."""
    tok_stream = token_stream_factory(io.StringIO(source).readline)
    tokenizer = TokenizerCustom(tok_stream, verbose=verbose)
    parsed = parse(
        filename="<string>",
        tokenizer=tokenizer,
        mode=mode if mode == "eval" else "file",
        py_version=py_version,
        verbose=verbose,
    )
    if parsed:
        gather_errors(parsed)
    return parsed


def parse_expr(
    source: str,
    py_version: Optional[tuple[int, int]] = None,
    verbose: bool = False,
) -> ast.expr:
    """Parse an expression string and return expression node."""
    parsed = parse_string(
        source,
        mode="eval",
        py_version=py_version,
        verbose=verbose,
    )
    assert isinstance(parsed, ast.Expression), f"Expression parsing failed: {parsed}"
    return parsed.body


def parse_type(
    source: str,
    py_version: Optional[tuple[int, int]] = None,
    verbose: bool = False,
) -> ast.expr:
    """Parse a typing expression string and return expression node."""
    tok_stream = token_stream_factory(io.StringIO(source).readline)
    tokenizer = TokenizerCustom(tok_stream, verbose=verbose)
    parsed = parse(
        filename="<typing_expr>",
        tokenizer=tokenizer,
        mode="typing_expr",
        py_version=py_version,
        verbose=verbose,
    )
    assert isinstance(parsed, ast.Expression), f"Type parsing failed: {parsed}"
    gather_errors(parsed)
    return parsed.body
