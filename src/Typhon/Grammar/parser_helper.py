# Based on https://github.com/we-like-parsers/pegen/blob/main/data/python.gram
# Extracted Python code part from grammar file.

import ast
import sys
import tokenize

import enum
from typing import (
    Any,
    Callable,
    Iterator,
    List,
    Literal,
    Sequence,
    Unpack,
    Tuple,
    TypeVar,
    Union,
    Optional,
    Protocol,
    cast,
    Type,
)

from pegen.tokenizer import Tokenizer
from pegen.parser import P, memoize, memoize_left_rec, logger, Parser as PegenParser
from ..Driver.debugging import is_debug_first_error
from .typhon_ast import (
    set_anonymous_name_id,
    PosAttributes,
    get_pos_attributes,
    get_anonymous_base_name,
)
from .syntax_errors import SkipTokensError, ExpectedTokenError

EXPR_NAME_MAPPING: dict[type, str] = {
    ast.Attribute: "attribute",
    ast.Subscript: "subscript",
    ast.Starred: "starred",
    ast.Name: "name",
    ast.List: "list",
    ast.Tuple: "tuple",
    ast.Lambda: "lambda",
    ast.Call: "function call",
    ast.BoolOp: "expression",
    ast.BinOp: "expression",
    ast.UnaryOp: "expression",
    ast.GeneratorExp: "generator expression",
    ast.Yield: "yield expression",
    ast.YieldFrom: "yield expression",
    ast.Await: "await expression",
    ast.ListComp: "list comprehension",
    ast.SetComp: "set comprehension",
    ast.DictComp: "dict comprehension",
    ast.Dict: "dict literal",
    ast.Set: "set display",
    ast.JoinedStr: "f-string expression",
    ast.FormattedValue: "f-string expression",
    ast.Compare: "comparison",
    ast.IfExp: "conditional expression",
    ast.NamedExpr: "named expression",
}


# Singleton ast nodes, created once for efficiency
Load = ast.Load()
Store = ast.Store()
Del = ast.Del()

Node = TypeVar("Node")
FC = TypeVar("FC", ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


class Target(enum.Enum):
    FOR_TARGETS = enum.auto()
    STAR_TARGETS = enum.auto()
    DEL_TARGETS = enum.auto()


# ast.AST with position info
class PositionedNode(Protocol):
    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int


class Parser(PegenParser):
    #: Name of the source file, used in error reports
    filename: str
    _anonymous_id = 0

    def __init__(
        self,
        tokenizer: Tokenizer,
        *,
        verbose: bool = False,
        filename: str = "<unknown>",
        py_version: tuple[int, int] | None = None,
    ) -> None:
        super().__init__(tokenizer, verbose=verbose)
        self.filename = filename
        self.py_version = (
            min(py_version, sys.version_info) if py_version else sys.version_info
        )
        # Note "invalid_*" rules returns None. Cannot use for error recovery.
        self.call_invalid_rules = True

    def parse(self, rule: str, call_invalid_rules: bool = True) -> Optional[ast.AST]:
        old = self.call_invalid_rules
        self.call_invalid_rules = call_invalid_rules
        res = getattr(self, rule)()

        if res is None:
            # Grab the last token that was parsed in the first run to avoid
            # polluting a generic error reports with progress made by invalid rules.
            last_token = self._tokenizer.diagnose()

            if not call_invalid_rules:
                self.call_invalid_rules = True

                # Reset the parser cache to be able to restart parsing from the
                # beginning.
                self._reset(0)  # type: ignore
                self._cache.clear()

                res = getattr(self, rule)()

            self.raise_raw_syntax_error(
                "invalid syntax", last_token.start, last_token.end
            )

        return res

    def check_version(
        self, min_version: Tuple[int, ...], error_msg: str, node: Node
    ) -> Node:
        """Check that the python version is high enough for a rule to apply."""
        if self.py_version >= min_version:
            return node
        else:
            raise SyntaxError(
                f"{error_msg} is only supported in Python {min_version} and above."
            )

    def make_anonymous_name(
        self, ctx: ast.expr_context, **kwargs: Unpack[PosAttributes]
    ) -> tuple[ast.Name, int]:
        anon_id = self._anonymous_id
        self._anonymous_id += 1
        name = ast.Name(f"{get_anonymous_base_name()}_{anon_id}", ctx, **kwargs)
        set_anonymous_name_id(name, anon_id)
        return name, anon_id

    def raise_indentation_error(self, msg: str) -> None:
        """Raise an indentation error."""
        last_token = self._tokenizer.diagnose()
        args = (
            self.filename,
            last_token.start[0],
            last_token.start[1] + 1,
            last_token.line,
        )
        if sys.version_info >= (3, 10):
            args += (last_token.end[0], last_token.end[1] + 1)
        raise IndentationError(msg, args)

    def get_expr_name(self, node: ast.expr) -> str:
        """Get a descriptive name for an expression."""
        # See https://github.com/python/cpython/blob/master/Parser/pegen.c#L161
        assert node is not None
        node_t = type(node)
        if isinstance(node, ast.Constant):
            v = node.value
            if v is Ellipsis:
                return "ellipsis"
            elif v is None:
                return str(v)
            # Avoid treating 1 as True through == comparison
            elif v is True:
                return str(v)
            elif v is False:
                return str(v)
            else:
                return "literal"

        try:
            return EXPR_NAME_MAPPING[node_t]
        except KeyError:
            raise ValueError(
                f"unexpected expression in assignment {type(node).__name__} "
                f"(line {node.lineno})."
            )

    def get_invalid_target(
        self, target: Target, node: Optional[ast.AST]
    ) -> Optional[ast.AST]:
        """Get the meaningful invalid target for different assignment type."""
        if node is None:
            return None

        # We only need to visit List and Tuple nodes recursively as those
        # are the only ones that can contain valid names in targets when
        # they are parsed as expressions. Any other kind of expression
        # that is a container (like Sets or Dicts) is directly invalid and
        # we do not need to visit it recursively.
        if isinstance(node, (ast.List, ast.Tuple)):
            for e in node.elts:
                if (inv := self.get_invalid_target(target, e)) is not None:
                    return inv
        elif isinstance(node, ast.Starred):
            if target is Target.DEL_TARGETS:
                return node
            return self.get_invalid_target(target, node.value)
        elif isinstance(node, ast.Compare):
            # This is needed, because the `a in b` in `for a in b` gets parsed
            # as a comparison, and so we need to search the left side of the comparison
            # for invalid targets.
            if target is Target.FOR_TARGETS:
                if isinstance(node.ops[0], ast.In):
                    return self.get_invalid_target(target, node.left)
                return None

            return node
        elif isinstance(node, (ast.Name, ast.Subscript, ast.Attribute)):
            return None
        else:
            return node

    def set_expr_context(
        self,
        node: ast.Starred
        | ast.List
        | ast.Tuple
        | ast.Subscript
        | ast.Attribute
        | ast.Name,
        context: ast.expr_context,
    ) -> ast.expr:
        """Set the context (Load, Store, Del) of an ast node."""
        node.ctx = context
        return node

    def ensure_real(self, number: tokenize.TokenInfo) -> float:
        value = ast.literal_eval(number.string)
        if type(value) is complex:
            self.raise_syntax_error_known_location(
                "real number required in complex literal", number
            )
        return value

    def ensure_imaginary(self, number: tokenize.TokenInfo) -> complex:
        value = ast.literal_eval(number.string)
        if type(value) is not complex:
            self.raise_syntax_error_known_location(
                "imaginary number required in complex literal", number
            )
        return value

    def check_fstring_conversion(
        self, mark: tokenize.TokenInfo, name: tokenize.TokenInfo
    ) -> tokenize.TokenInfo:
        if mark.end != name.start:
            self.raise_syntax_error_known_range(
                "f-string: conversion type must come right after the exclamanation mark",
                mark,
                name,
            )

        s = name.string
        if len(s) > 1 or s not in ("s", "r", "a"):
            self.raise_syntax_error_known_location(
                f"f-string: invalid conversion character '{s}': expected 's', 'r', or 'a'",
                name,
            )
        return name

    def _concat_strings_in_constant(
        self, parts: list[tokenize.TokenInfo]
    ) -> ast.Constant:
        s = ast.literal_eval(parts[0].string)
        for ss in parts[1:]:
            s += ast.literal_eval(ss.string)
        args = dict(
            value=s,
            lineno=parts[0].start[0],
            col_offset=parts[0].start[1],
            end_lineno=parts[-1].end[0],
            end_col_offset=parts[0].end[1],
        )
        if parts[0].string.startswith("u"):
            args["kind"] = "u"
        return ast.Constant(**args)

    def concatenate_strings(self, parts: list[tokenize.TokenInfo]):
        """Concatenate multiple tokens and ast.JoinedStr"""
        # Get proper start and stop
        start = end = None
        if isinstance(parts[0], ast.JoinedStr):
            start = parts[0].lineno, parts[0].col_offset
        if isinstance(parts[-1], ast.JoinedStr):
            end = parts[-1].end_lineno, parts[-1].end_col_offset

        # Combine the different parts
        seen_joined = False
        values: list[ast.expr] = []
        ss: list[tokenize.TokenInfo] = []
        for p in parts:
            if isinstance(p, ast.JoinedStr):
                seen_joined = True
                if ss:
                    values.append(self._concat_strings_in_constant(ss))
                    ss.clear()
                values.extend(p.values)
            else:
                ss.append(p)

        if ss:
            values.append(self._concat_strings_in_constant(ss))

        consolidated: list[ast.expr] = []
        for p in values:
            if (
                consolidated
                and isinstance(consolidated[-1], ast.Constant)
                and isinstance(p, ast.Constant)
            ):
                consolidated[-1].value += p.value  # type: ignore[misc]
                consolidated[-1].end_lineno = p.end_lineno
                consolidated[-1].end_col_offset = p.end_col_offset
            else:
                consolidated.append(p)

        if not seen_joined and len(values) == 1 and isinstance(values[0], ast.Constant):
            return values[0]
        else:
            return ast.JoinedStr(
                values=consolidated,
                lineno=start[0] if start else values[0].lineno,
                col_offset=start[1] if start else values[0].col_offset,
                end_lineno=end[0] if end else values[-1].end_lineno,
                end_col_offset=end[1] if end else values[-1].end_col_offset,
            )

    def extract_import_level(self, tokens: List[tokenize.TokenInfo]) -> int:
        """Extract the relative import level from the tokens preceding the module name.

        '.' count for one and '...' for 3.

        """
        level = 0
        for t in tokens:
            if t.string == ".":
                level += 1
            else:
                level += 3
        return level

    def set_decorators(self, target: FC, decorators: list[ast.expr]) -> FC:
        """Set the decorators on a function or class definition."""
        target.decorator_list = decorators
        return target

    def get_comparison_ops(
        self, pairs: list[tuple[ast.cmpop, ast.expr]]
    ) -> list[ast.cmpop]:
        return [op for op, _ in pairs]

    def get_comparators(
        self, pairs: list[tuple[ast.cmpop, ast.expr]]
    ) -> list[ast.expr]:
        return [comp for _, comp in pairs]

    def set_arg_type_comment(self, arg: ast.arg, type_comment: str | None) -> ast.arg:
        if type_comment or sys.version_info < (3, 9):
            arg.type_comment = type_comment
        return arg

    def build_syntax_error[T: SyntaxError](
        self,
        message: str,
        start: Tuple[int, int],
        end: Tuple[int, int],
        error_type: Type[T] = SyntaxError,
    ) -> T:
        # End is used only to get the proper text
        line = "\\n".join(self._tokenizer.get_lines(list(range(start[0], end[0] + 1))))

        # tokenize.py index column offset from 0 while Cpython index column
        # offset at 1 when reporting SyntaxError, so we need to increment
        # the column offset when reporting the error.
        # But in Typhon, first we take all the ranges as 0-based.
        args = (self.filename, start[0], start[1], line)
        if sys.version_info >= (3, 10):
            args += (end[0], end[1])

        result = error_type(message, args)
        if is_debug_first_error():
            raise result
        return result

    def build_expected_error(
        self, message: str, start: Tuple[int, int], end: Tuple[int, int]
    ) -> SyntaxError:
        error = self.build_syntax_error(
            f"expected {message}", start, end, ExpectedTokenError
        )
        error.expected = message
        return error

    def build_skip_tokens_error(
        self,
        tokens: list[tokenize.TokenInfo],
        start: Tuple[int, int],
        end: Tuple[int, int],
    ) -> SyntaxError:
        error = self.build_syntax_error(
            "skipped unknown tokens", start, end, SkipTokensError
        )
        error.tokens = tokens
        return error

    def raise_raw_syntax_error(
        self, message: str, start: Tuple[int, int], end: Tuple[int, int]
    ) -> SyntaxError:
        return self.build_syntax_error(message, start, end)

    def expect_forced(self, res: Any, expectation: str) -> Optional[tokenize.TokenInfo]:
        if res is None:
            last_token = self._tokenizer.diagnose()
            end = last_token.start
            if sys.version_info >= (3, 12) or (
                sys.version_info >= (3, 11) and last_token.type != 4
            ):  # i.e. not a \n
                end = last_token.end
            self.raise_raw_syntax_error(
                f"expected {expectation}", last_token.start, end
            )
        return res

    def raise_syntax_error(self, message: str) -> SyntaxError:
        """Raise a syntax error."""
        tok = self._tokenizer.diagnose()
        return self.build_syntax_error(
            message,
            tok.start,
            tok.end if sys.version_info >= (3, 12) or tok.type != 4 else tok.start,
        )

    def raise_syntax_error_known_location(
        self, message: str, node: PositionedNode | tokenize.TokenInfo
    ) -> SyntaxError:
        """Raise a syntax error that occured at a given AST node."""
        if isinstance(node, tokenize.TokenInfo):
            start = node.start
            end = node.end
        else:
            start = node.lineno, node.col_offset
            end = node.end_lineno, node.end_col_offset

        return self.build_syntax_error(message, start, end)

    def raise_syntax_error_known_range(
        self,
        message: str,
        start_node: Union[PositionedNode, tokenize.TokenInfo],
        end_node: Union[PositionedNode, tokenize.TokenInfo],
    ) -> SyntaxError:
        if isinstance(start_node, tokenize.TokenInfo):
            start = start_node.start
        else:
            start = start_node.lineno, start_node.col_offset

        if isinstance(end_node, tokenize.TokenInfo):
            end = end_node.end
        else:
            end = end_node.end_lineno, end_node.end_col_offset

        return self.build_syntax_error(message, start, end)

    def raise_syntax_error_starting_from(
        self, message: str, start_node: Union[PositionedNode, tokenize.TokenInfo]
    ) -> SyntaxError:
        if isinstance(start_node, tokenize.TokenInfo):
            start = start_node.start
        else:
            start = start_node.lineno, start_node.col_offset

        last_token = self._tokenizer.diagnose()

        return self.build_syntax_error(message, start, last_token.start)

    def raise_syntax_error_invalid_target(
        self, target: Target, node: Optional[ast.AST]
    ) -> None:
        invalid_target = self.get_invalid_target(target, node)

        if invalid_target is None:
            return None

        if target in (Target.STAR_TARGETS, Target.FOR_TARGETS):
            msg = (
                f"cannot assign to {self.get_expr_name(cast(ast.expr, invalid_target))}"
            )
        else:
            msg = f"cannot delete {self.get_expr_name(cast(ast.expr, invalid_target))}"

        self.raise_syntax_error_known_location(
            msg, cast(PositionedNode, invalid_target)
        )

    def raise_syntax_error_on_next_token(self, message: str) -> SyntaxError:
        next_token = self._tokenizer.peek()
        return self.build_syntax_error(message, next_token.start, next_token.end)
