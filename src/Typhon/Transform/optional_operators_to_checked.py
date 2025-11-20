import ast
from typing import cast, Callable
from contextlib import contextmanager
from ..Grammar.typhon_ast import (
    PosAttributes,
    get_empty_pos_attributes,
    get_pos_attributes,
    is_force_unwrap,
    is_coalescing,
    is_optional,
    is_optional_pipe,
    clear_is_optional,
)

from .visitor import TyphonASTTransformer
from .name_generator import get_unwrap_name, get_unwrap_error_name

# TODO: Raise what exception?
_unwrap_func_code = f"""
def {get_unwrap_name()}[T](value: T | None) -> T:
    if value is None:
        raise {get_unwrap_error_name()}("Unwrapped None")
    return value
"""
_unwrap_ast = ast.parse(_unwrap_func_code)


def _insert_unwrap_function(mod: ast.Module):
    first_non_import_index = 0
    for i, stmt in enumerate(mod.body):
        if not isinstance(stmt, (ast.Import, ast.ImportFrom)):
            first_non_import_index = i
            break
    unwrap_func = _unwrap_ast.body[0]
    mod.body.insert(first_non_import_index, unwrap_func)


class _OptionalToCheckTransformer(TyphonASTTransformer):
    unwrap_inserted: bool = False

    def _optional_check_if_exp(
        self,
        maybe_none_val: ast.expr,
        then_val: Callable[[str], ast.expr],
        orelse_val: ast.expr,
        pos: PosAttributes,
    ) -> ast.IfExp:
        tmp_name = self.new_temp_variable_name()
        return ast.IfExp(
            # (_tmp := a) is not None
            test=ast.Compare(
                # (_tmp := a)
                left=ast.NamedExpr(
                    target=ast.Name(id=tmp_name, ctx=ast.Store()),
                    value=maybe_none_val,
                    **pos,
                ),
                ops=[ast.IsNot()],
                comparators=[ast.Constant(value=None, **pos)],
                **pos,
            ),
            body=then_val(tmp_name),
            orelse=orelse_val,
            **pos,
        )

    def _visit_unwrap(self, node: ast.Tuple):
        pos = get_pos_attributes(node)
        if len(node.elts) != 1:
            return self._raise_type_annotation_error_default(
                self.generic_visit(node),
                "Postfix `?` type annotation must have exactly one element type.",
                pos,
            )
        elt = node.elts[0]
        assert isinstance(elt, ast.expr), (
            f"Unexpected element in OptionalQuestion: {ast.dump(elt)}"
        )
        self.unwrap_inserted = True
        result = ast.Call(
            func=ast.Name(id=get_unwrap_name(), ctx=ast.Load()),
            args=[elt],
            keywords=[],
            **get_empty_pos_attributes(),
        )
        return self.generic_visit(result)

    def _visit_coalescing(self, node: ast.Tuple):
        pos = get_pos_attributes(node)
        if len(node.elts) != 2:
            return self._raise_type_annotation_error_default(
                self.generic_visit(node),
                "Postfix `??` type annotation must have exactly two element types.",
                pos,
            )
        left = node.elts[0]
        right = node.elts[1]
        # Transform a ?? b to (_tmp if (_tmp := a) is not None else b)
        result = self._optional_check_if_exp(
            left,
            (lambda tmp_name: ast.Name(id=tmp_name, ctx=ast.Load())),
            right,
            pos,
        )
        return self.generic_visit(result)

    # Visit unwrap and coalescing.
    def visit_Tuple(self, node: ast.Tuple):
        if is_force_unwrap(node):
            return self._visit_unwrap(node)
        elif is_coalescing(node):
            return self._visit_coalescing(node)
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Transform optional call f?(...) to
        # _tmp(...) if (_tmp := f) is not None else None
        # Transform optional pipe x ?|> f to
        # f(_tmp) if (_tmp := x) is not None else None
        if not is_optional(node) and not is_optional_pipe(node):
            return self.generic_visit(node)
        pos = get_pos_attributes(node)
        if is_optional(node):
            result = self._optional_check_if_exp(
                node.func,
                lambda tmp_name: ast.Call(
                    func=ast.Name(id=tmp_name, ctx=ast.Load()),
                    args=node.args,
                    keywords=node.keywords,
                    **pos,
                ),
                ast.Constant(value=None, **pos),
                pos,
            )
        else:  # is_optional_pipe
            if len(node.args) != 1:
                return self._raise_type_annotation_error_default(
                    self.generic_visit(node),
                    "Postfix `?|>` operator must have exactly one argument.",
                    pos,
                )
            arg = node.args[0]
            result = self._optional_check_if_exp(
                arg,
                lambda tmp_name: ast.Call(
                    func=node.func,
                    args=[ast.Name(id=tmp_name, ctx=ast.Load())],
                    keywords=[],
                    **pos,
                ),
                ast.Constant(value=None, **pos),
                pos,
            )
        return self.generic_visit(result)

    def visit_Subscript(self, node: ast.Subscript):
        # Transform optional subscript a?[...] to
        # _tmp[...] if (_tmp := a) is not None else None
        if not is_optional(node):
            return self.generic_visit(node)
        pos = get_pos_attributes(node)
        result = self._optional_check_if_exp(
            node.value,
            lambda tmp_name: ast.Subscript(
                value=ast.Name(id=tmp_name, ctx=ast.Load()),
                slice=node.slice,
                ctx=node.ctx,
                **pos,
            ),
            ast.Constant(value=None, **pos),
            pos,
        )
        return self.generic_visit(result)

    def visit_Attribute(self, node: ast.Attribute):
        # Transform optional attribute access a?.attr to
        # _tmp.attr if (_tmp := a) is not None else None
        if not is_optional(node):
            return self.generic_visit(node)
        pos = get_pos_attributes(node)
        result = self._optional_check_if_exp(
            node.value,
            lambda tmp_name: ast.Attribute(
                value=ast.Name(id=tmp_name, ctx=ast.Load()),
                attr=node.attr,
                ctx=node.ctx,
                **pos,
            ),
            ast.Constant(value=None, **pos),
            pos,
        )
        return self.generic_visit(result)


def optional_to_checked(mod: ast.Module) -> None:
    transformer = _OptionalToCheckTransformer(mod)
    transformer.run()
    if transformer.unwrap_inserted:
        _insert_unwrap_function(mod)
