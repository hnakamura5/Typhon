import ast
from pathlib import Path
from .typhon_ast import PosAttributes
from typing import Unpack
from ..Driver.diagnostic import diag_error_file_position, positioned_source_code
from ..SourceMap.datatype import Range


class ScopeError(Exception):
    def __init__(self, message: str, **pos: Unpack[PosAttributes]):
        self.message = message
        self.pos = PosAttributes(**pos)
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} at {self.pos}"


def raise_scope_error(
    message: str,
    **pos: Unpack[PosAttributes],
):
    raise ScopeError(message, **pos)


class ForbiddenStatementError(Exception):
    def __init__(self, message: str, **pos: Unpack[PosAttributes]):
        self.message = message
        self.pos = PosAttributes(**pos)
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} at {self.pos}"


def raise_forbidden_statement_error(
    message: str,
    **pos: Unpack[PosAttributes],
):
    raise ForbiddenStatementError(message, **pos)


class TypeAnnotationError(Exception):
    def __init__(self, message: str, **pos: Unpack[PosAttributes]):
        self.message = message
        self.pos = PosAttributes(**pos)
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} at {self.pos}"


def raise_type_annotation_error(
    message: str,
    **pos: Unpack[PosAttributes],
):
    raise TypeAnnotationError(message, **pos)


def diag_syntax_error(
    syntax_error: SyntaxError,
    source: Path,
    source_code: str,
) -> str:
    result = diag_error_file_position(
        error_type="syntax error",
        file_path=source.as_posix(),
        position=Range.from_syntax_error(syntax_error),
        rule=None,
        source_lines=source_code.splitlines(),
        message=syntax_error.msg,
    )
    result += "\n"
    result += positioned_source_code(
        source_lines=source_code.splitlines(),
        range_in_source=Range.from_syntax_error(syntax_error),
    )
    return result
