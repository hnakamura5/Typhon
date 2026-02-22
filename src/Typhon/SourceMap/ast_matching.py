from dataclasses import dataclass
import ast
from contextlib import contextmanager
from typing import Any, cast
from ..Driver.debugging import debug_verbose_print
from ..Grammar.typhon_ast import (
    DefinesName,
    get_defined_name,
    get_import_from_names,
    get_return_type_annotation_anchor,
)


# Match the AST node to right module recursively
class MatchingVisitor(ast.NodeVisitor):
    def __init__(
        self,
        right: ast.AST,
        left_to_right: dict[ast.AST, ast.AST],
        right_to_left: dict[ast.AST, ast.AST],
    ):
        self.left_to_right = left_to_right
        self.right_to_left = right_to_left
        self.right = right

    @contextmanager
    def _with_right(self, right: ast.AST):
        old_right = self.right
        self.right = right
        yield
        self.right = old_right

    def _commit(self, left: ast.AST, right: ast.AST):
        debug_verbose_print(f"Matched: {ast.dump(left)}  <->  {ast.dump(right)}")
        self.left_to_right[left] = right
        self.right_to_left[right] = left

    def _visit_list(self, lefts: list[Any], rights: list[Any]):
        if len(lefts) != len(rights):
            # TODO: Error rescue: List length mismatch
            raise ValueError(f"List length mismatch: {len(lefts)} vs {len(rights)}")
        for left, right in zip(lefts, rights):
            if not isinstance(left, ast.AST) or not isinstance(right, ast.AST):
                if left != right:
                    # TODO: Error rescue: List value mismatch
                    raise ValueError(f"List value mismatch: {left} vs {right}")
                continue
            with self._with_right(right):
                self.visit(left)

    def visit(self, node: ast.AST):
        right = self.right
        if type(node) is not type(right):
            # TODO: Error rescue: Type mismatch
            raise ValueError(f"Type mismatch: {ast.dump(node)} vs {ast.dump(right)}")
        # Commit the match
        self._commit(node, right)
        # Check defined name
        if isinstance(node, DefinesName):
            left_name = get_defined_name(node)
            right_name = get_defined_name(cast(DefinesName, right))
            if left_name is not None and right_name is not None:
                with self._with_right(right_name):
                    self.visit(left_name)
            # Allow defined name not matching
        # Check import from module names
        if isinstance(node, ast.ImportFrom):
            modules = get_import_from_names(node)
            right_modules = get_import_from_names(cast(ast.ImportFrom, right))
            if modules and right_modules:
                self._visit_list(modules, right_modules)
        # Check return type annotation anchor
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            left_anchor = get_return_type_annotation_anchor(node)
            right_anchor = get_return_type_annotation_anchor(
                cast(ast.FunctionDef | ast.AsyncFunctionDef, right)
            )
            if left_anchor is not None and right_anchor is not None:
                with self._with_right(right_anchor):
                    self.visit(left_anchor)
            # Allow return type annotation anchor not matching
        # Recursively visit fields
        for field, value in ast.iter_fields(node):
            right_value = getattr(right, field, None)
            if isinstance(value, list):
                if isinstance(right_value, list):
                    self._visit_list(
                        cast(list[Any], value), cast(list[Any], right_value)
                    )
                else:
                    # TODO: Error rescue: List length mismatch
                    raise ValueError(
                        f"List mismatch in field {field}: {ast.dump(node)} vs {ast.dump(right)}"
                    )
            elif isinstance(value, ast.AST):
                with self._with_right(cast(ast.AST, right_value)):
                    self.visit(value)
            else:
                if value != right_value:
                    # TODO: Error rescue: Value mismatch
                    raise ValueError(
                        f"Value mismatch in field {field}: {value} vs {right_value}"
                    )


@dataclass
class MatchResult:
    left_to_right: dict[ast.AST, ast.AST]
    right_to_left: dict[ast.AST, ast.AST]


def match_ast[T: ast.AST](left: T, right: T) -> MatchResult | None:
    left_to_right: dict[ast.AST, ast.AST] = {}
    right_to_left: dict[ast.AST, ast.AST] = {}
    visitor = MatchingVisitor(right, left_to_right, right_to_left)
    visitor.visit(left)
    return MatchResult(left_to_right, right_to_left)
