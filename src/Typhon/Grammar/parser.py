import ast
import sys
import tokenize
import os
import io

from typing import (
    Literal,
    Union,
    Optional,
)

from .tokenizer_custom import TokenizerCustom
from .token_factory_custom import token_stream_factory
from ._typhon_parser import parse


def parse_file(
    file_path: str,
    py_version: Optional[tuple[int, int]] = None,
    verbose: bool = False,
) -> ast.Module:
    """Parse a file."""
    with open(file_path) as f:
        tok_stream = token_stream_factory(f.readline)
        tokenizer = TokenizerCustom(tok_stream, verbose=verbose, path=file_path)
        parsed = parse_tokenizer(
            tokenizer,
            py_version=py_version,
            verbose=verbose,
        )
        assert isinstance(parsed, ast.Module), f"Parsing failed: {parsed}"
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
    return parse(
        filename="<string>",
        tokenizer=tokenizer,
        mode=mode if mode == "eval" else "file",
        py_version=py_version,
        verbose=verbose,
    )
