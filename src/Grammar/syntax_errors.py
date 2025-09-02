import ast
from .typhon_ast import PosAttributes
from typing import Unpack


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
