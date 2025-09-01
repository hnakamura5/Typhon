from typing import override, Callable
from contextlib import contextmanager
import ast
from ..Grammar.typhon_ast import (
    is_function_literal,
    is_function_type,
    get_function_literal_def,
    set_function_literal_def,
    FunctionLiteral,
    FunctionType,
    fieldsOfFunctionType,
)
from .name_generator import UniqueNameGenerator, PythonScope


class _ScopeManagerMixin:
    parent_classes: list[ast.ClassDef]
    parent_functions: list[ast.FunctionDef | ast.AsyncFunctionDef]
    parent_stmts: list[ast.stmt]
    parent_exprs: list[ast.expr]
    name_gen: UniqueNameGenerator
    parent_python_scopes: list[PythonScope]

    def __init__(self):
        super().__init__()
        self.parent_stmts = []
        self.parent_exprs = []
        self.parent_classes = []
        self.parent_functions = []
        self.name_gen = UniqueNameGenerator()
        self.parent_python_scopes = []

    @contextmanager
    def _parent_class(self, node: ast.AST):
        if isinstance(node, ast.ClassDef):
            class_def = node
            self.parent_classes.append(class_def)
            yield
            self.parent_classes.pop()
        else:
            yield

    @contextmanager
    def _parent_stmt(self, node: ast.AST):
        if isinstance(node, ast.stmt):
            self.parent_stmts.append(node)
            yield
            self.parent_stmts.pop()
        else:
            yield

    @contextmanager
    def _parent_expr(self, node: ast.AST):
        if isinstance(node, ast.expr):
            self.parent_exprs.append(node)
            yield
            self.parent_exprs.pop()
        else:
            yield

    @contextmanager
    def _parent_function(self, node: ast.AST):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_def = node
            self.parent_functions.append(func_def)
            yield
            self.parent_functions.pop()
        else:
            yield

    @contextmanager
    def _name_scope(self, node: ast.AST):
        if isinstance(node, PythonScope):
            self.name_gen.enter_scope(node)
            yield
            self.name_gen.exit_scope(node)
        else:
            yield

    @contextmanager
    def _parent_python_scope(self, node: ast.AST):
        if isinstance(node, PythonScope):
            self.parent_python_scopes.append(node)
            yield
            self.parent_python_scopes.pop()
        else:
            yield

    @contextmanager
    def _visit_scope(self, node: ast.AST):
        with self._parent_stmt(node):
            with self._parent_class(node):
                with self._parent_expr(node):
                    with self._parent_function(node):
                        with self._name_scope(node):
                            with self._parent_python_scope(node):
                                yield

    def new_func_literal_name(self) -> str:
        return self.name_gen.new_func_literal_name()

    def new_variable_rename_name(self, original_name: str) -> str:
        return self.name_gen.new_variable_rename_name(original_name)

    def new_const_rename_name(self, original_name: str) -> str:
        return self.name_gen.new_const_rename_name(original_name)

    def new_arrow_type_name(self) -> str:
        return self.name_gen.new_arrow_type_name()


def flat_map[T](f: Callable[[T], T | list[T] | None], v: list[T]) -> list[T]:
    result: list[T] = []
    for item in v:
        new_item = f(item)
        if new_item is None:
            continue
        if isinstance(new_item, list):
            result.extend(new_item)
        else:
            result.append(new_item)
    return result


class _TyphonExtendedNodeTransformerMixin:
    def _visit_FunctionLiteral(
        self,
        node: FunctionLiteral,
        visitor: ast.NodeVisitor | ast.NodeTransformer,
        transform: bool,
    ):
        new_def = visitor.visit(get_function_literal_def(node))
        if transform and isinstance(new_def, ast.FunctionDef):
            set_function_literal_def(node, new_def)
        return node

    def _visit_FunctionType(
        self,
        node: FunctionType,
        visitor: ast.NodeVisitor | ast.NodeTransformer,
        transform: bool,
    ):
        for field in fieldsOfFunctionType:
            value = getattr(node, field, None)
            if value is None:
                continue
            if isinstance(value, list):
                new_value = flat_map(visitor.visit, value)
                if transform:
                    setattr(node, field, new_value)
            else:
                new_value = visitor.visit(value)
                if transform:
                    if new_value is None:
                        delattr(node, field)
                    else:
                        setattr(node, field, new_value)
        return node

    def _visit(
        self,
        node: ast.AST,
        visitor: ast.NodeVisitor | ast.NodeTransformer,
        otherwise: Callable[[ast.AST], ast.AST | list[ast.AST] | None],
    ):
        if isinstance(node, ast.Name):
            if is_function_literal(node):
                visit = getattr(visitor, "visit_FunctionLiteral", visitor.generic_visit)
                return visit(node)
            elif is_function_type(node):
                visit = getattr(visitor, "visit_FunctionType", visitor.generic_visit)
                return visit(node)
        return otherwise(node)


class TyphonASTVisitor(
    ast.NodeVisitor, _ScopeManagerMixin, _TyphonExtendedNodeTransformerMixin
):
    @override
    def visit(self, node: ast.AST):
        with self._visit_scope(node):
            return self._visit(node, self, super().visit)

    @override
    def generic_visit(self, node: ast.AST):
        if isinstance(node, ast.Name):
            if is_function_literal(node):
                return self._visit_FunctionLiteral(node, self, False)
            elif is_function_type(node):
                return self._visit_FunctionType(node, self, False)
        return super().generic_visit(node)


class TyphonASTTransformer(
    ast.NodeTransformer, _ScopeManagerMixin, _TyphonExtendedNodeTransformerMixin
):
    @override
    def visit(self, node: ast.AST) -> ast.AST | list[ast.AST] | None:
        with self._visit_scope(node):
            return self._visit(node, self, super().visit)

    @override
    def generic_visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Name):
            if is_function_literal(node):
                return self._visit_FunctionLiteral(node, self, True)
            elif is_function_type(node):
                return self._visit_FunctionType(node, self, True)
        return super().generic_visit(node)
