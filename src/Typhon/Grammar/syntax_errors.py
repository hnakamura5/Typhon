import ast
from pathlib import Path
from tokenize import TokenInfo
from .typhon_ast import PosAttributes
from typing import Unpack, Callable
from ..Driver.diagnostic import diag_error_file_position, positioned_source_code
from ..SourceMap.datatype import Range
from ..Driver.debugging import debug_print, is_debug_first_error

_SYNTAX_ERROR_IN_MODULE = "_typh_syntax_error_in_module"


# Error recovery skips unrecognized tokens
class SkipTokensError(SyntaxError):
    tokens: list[TokenInfo]


class ExpectedTokenError(SyntaxError):
    expected: str


class TyphonTransformSyntaxError(SyntaxError):
    message: str
    pos: PosAttributes

    def __init__(self, message: str, **pos: Unpack[PosAttributes]):
        self.message = message
        self.pos = PosAttributes(**pos)
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} at {self.pos}"


def set_syntax_error(node: ast.AST, error_details: list[SyntaxError]):
    setattr(node, _SYNTAX_ERROR_IN_MODULE, error_details)


def add_syntax_error_in_module(module: ast.Module, error_detail: SyntaxError):
    if not hasattr(module, _SYNTAX_ERROR_IN_MODULE):
        setattr(module, _SYNTAX_ERROR_IN_MODULE, [])
    error_list = getattr(module, _SYNTAX_ERROR_IN_MODULE)
    error_list.append(error_detail)


def get_syntax_error_in_module(module: ast.Module) -> list[SyntaxError] | None:
    return getattr(module, _SYNTAX_ERROR_IN_MODULE, None)


def has_syntax_error_in_module(module: ast.Module) -> bool:
    return hasattr(module, _SYNTAX_ERROR_IN_MODULE)


def clear_syntax_error_in_module(module: ast.Module) -> None:
    if hasattr(module, _SYNTAX_ERROR_IN_MODULE):
        delattr(module, _SYNTAX_ERROR_IN_MODULE)


class TyphonSyntaxErrorList(Exception):
    errors: list[SyntaxError]

    def __init__(self, errors: list[SyntaxError]):
        self.errors = errors
        super().__init__(self.errors)

    def __str__(self):
        return "\n".join(str(error) for error in self.errors)


def raise_from_module_syntax_errors(module: ast.Module):
    errors = get_syntax_error_in_module(module)
    if errors is not None and len(errors) > 0:
        raise TyphonSyntaxErrorList(errors)


def handle_syntax_error(
    module: ast.Module, syntax_error: TyphonTransformSyntaxError
) -> None:
    if is_debug_first_error():
        debug_print(f"Raising syntax error: {syntax_error}")
        raise syntax_error
    # Otherwise, record the syntax error in the module
    add_syntax_error_in_module(module, syntax_error)


def try_handle_syntax_error_or[T](
    orelse: T, module: ast.Module, maybe_syntax_error: Callable[[], T]
) -> T:
    try:
        return maybe_syntax_error()
    except TyphonTransformSyntaxError as syntax_error:
        handle_syntax_error(module, syntax_error)
    return orelse


class ScopeError(TyphonTransformSyntaxError):
    pass


def raise_scope_error(
    message: str,
    **pos: Unpack[PosAttributes],
):
    raise ScopeError(message, **pos)


class ForbiddenStatementError(TyphonTransformSyntaxError):
    pass


def raise_forbidden_statement_error(
    message: str,
    **pos: Unpack[PosAttributes],
):
    raise ForbiddenStatementError(message, **pos)


class TypeAnnotationError(TyphonTransformSyntaxError):
    pass


def raise_type_annotation_error(
    message: str,
    **pos: Unpack[PosAttributes],
):
    raise TypeAnnotationError(message, **pos)


class LetMissingElseError(TyphonTransformSyntaxError):
    pass


def raise_let_missing_else_error(
    message: str,
    **pos: Unpack[PosAttributes],
):
    raise LetMissingElseError(message, **pos)


def _get_range_of_error(
    syntax_error: SyntaxError | TyphonTransformSyntaxError,
) -> Range:
    if isinstance(syntax_error, TyphonTransformSyntaxError):
        return Range.from_pos_attr_may_not_end(syntax_error.pos)
    else:
        return Range.from_syntax_error(syntax_error)


def _get_message_of_error(
    syntax_error: SyntaxError | TyphonTransformSyntaxError,
) -> str:
    if isinstance(syntax_error, TyphonTransformSyntaxError):
        return syntax_error.message
    else:
        return syntax_error.msg


def raise_must_have_resolved(msg: str):
    if is_debug_first_error():
        debug_print("Raising error: AST must have been resolved at this point")
        raise NotImplementedError(msg)


def diag_error(
    syntax_error: SyntaxError | TyphonTransformSyntaxError,
    source: Path,
    source_code: str,
) -> str:
    result = diag_error_file_position(
        error_type="syntax error",
        file_path=source.as_posix(),
        position=_get_range_of_error(syntax_error),
        rule=None,
        source_lines=source_code.splitlines(),
        message=_get_message_of_error(syntax_error),
    )
    result += "\n"
    result += positioned_source_code(
        source_lines=source_code.splitlines(),
        range_in_source=_get_range_of_error(syntax_error),
    )
    return result


def diag_errors(
    syntax_error: SyntaxError | TyphonTransformSyntaxError | TyphonSyntaxErrorList,
    source: Path,
    source_code: str,
) -> str:
    if isinstance(syntax_error, TyphonSyntaxErrorList):
        return "\n".join(
            diag_error(error, source, source_code) for error in syntax_error.errors
        )
    else:
        return diag_error(syntax_error, source, source_code)
