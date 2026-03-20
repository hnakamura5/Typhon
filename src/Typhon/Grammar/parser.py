import ast
import importlib
import sys
import io
from pathlib import Path

from typing import Literal, Union, Optional

from Typhon.Grammar.typhon_ast import (
    is_reparse_target_token_size,
    set_is_reparse_target,
)


from ..Driver.debugging import is_debug_verbose

from .tokenizer_custom import TokenizerCustom, show_token
from .token_factory_custom import token_stream_factory
from .typhon_ast_error import gather_errors

# We need to patch to the pegen parser to optimize memorization functions.
import pegen.parser as pegen_parser
from . import parser_patch


# Monkey patching mechanism.
def _load_typhon_parser_module():
    # import or reload the generated parser module
    module_name = f"{__package__}._typhon_parser"
    if module_name in sys.modules:
        return importlib.reload(sys.modules[module_name])
    return importlib.import_module("._typhon_parser", package=__package__)


def _install_parser_patch():
    pegen_parser.memoize = parser_patch.memoize
    pegen_parser.memoize_left_rec = parser_patch.memoize_left_rec
    parser_patch.redecorate_pegen_parser_base_methods()
    return _load_typhon_parser_module()


# Semantically equal to,
# from . import _typhon_parser as _TYPHON_PARSER_MODULE
_TYPHON_PARSER_MODULE = _install_parser_patch()


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
            file_path=file_path,
            py_version=py_version,
            verbose=verbose,
        )
        if not isinstance(parsed, ast.Module):
            raise SyntaxError(f"Parsing failed: {parsed}")
        assert isinstance(parsed, ast.Module), f"Parsing failed: {parsed}"
        gather_errors(parsed)
        return parsed


def parse_tokenizer(
    tokenizer: TokenizerCustom,
    file_path: str | None = None,
    py_version: Optional[tuple[int, int]] = None,
    verbose: bool = False,
) -> ast.AST:
    """Parse using a tokenizer."""
    parsed = _TYPHON_PARSER_MODULE.parse(
        filename=file_path or "<tokenizer>",
        tokenizer=tokenizer,
        mode="file",
        py_version=py_version,
        verbose=verbose,
    )
    # Must be successful parse
    assert isinstance(parsed, ast.AST), f"Parsing failed: {parsed}"
    gather_errors(parsed)
    set_is_reparse_target(
        parsed, is_reparse_target_token_size(len(tokenizer.read_all_tokens()))
    )
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
    parsed = _TYPHON_PARSER_MODULE.parse(
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
    parsed = _TYPHON_PARSER_MODULE.parse(
        filename="<typing_expr>",
        tokenizer=tokenizer,
        mode="typing_expr",
        py_version=py_version,
        verbose=verbose,
    )
    assert isinstance(parsed, ast.Expression), f"Type parsing failed: {parsed}"
    gather_errors(parsed)
    return parsed.body
