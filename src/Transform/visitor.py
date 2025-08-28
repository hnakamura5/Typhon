from typing import Any, Union, override
import ast
from ..Grammar.typhon_ast import (
    is_function_literal,
    is_function_type,
    get_function_literal_def,
    FunctionLiteral,
    FunctionType,
    get_args_of_function_type,
    get_star_arg_of_function_type,
    get_star_kwds_of_function_type,
)
from .name_generator import UniqueNameGenerator


class TyphonASTVisitor(ast.NodeTransformer):
    parent_classes: list[ast.ClassDef]
    parent_functions: list[ast.FunctionDef | ast.AsyncFunctionDef]
    parent_stmts: list[ast.stmt]
    parent_exprs: list[ast.expr]
    name_gen: UniqueNameGenerator

    def __init__(self):
        super().__init__()
        self.parent_stmts = []
        self.parent_exprs = []
        self.parent_classes = []
        self.parent_functions = []
        self.name_gen = UniqueNameGenerator()

    @override
    def visit(self, node: ast.AST) -> ast.AST | list[ast.AST] | None:
        if isinstance(node, ast.stmt):
            self.parent_stmts.append(node)
            is_class = isinstance(node, ast.ClassDef)
            is_function = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            if is_class:
                self.parent_classes.append(node)
            elif is_function:
                self.parent_functions.append(node)
            result = super().visit(node)
            if is_class:
                self.parent_classes.pop()
            elif is_function:
                self.parent_functions.pop()
            self.parent_stmts.pop()
            return result
        elif isinstance(node, ast.expr):
            self.parent_exprs.append(node)
            if isinstance(node, ast.Name):
                if is_function_literal(node):
                    result = self.visit_FunctionLiteral(node)
                elif is_function_type(node):
                    result = self.visit_FunctionType(node)
                else:
                    result = super().visit(node)
            else:
                result = super().visit(node)
            self.parent_exprs.pop()
            return result
        else:
            return super().visit(node)

    def visit_FunctionLiteral(self, node: FunctionLiteral):
        self.visit(get_function_literal_def(node))
        self.generic_visit(node)
        return node

    def visit_FunctionType(self, node: FunctionType):
        self.generic_visit(node)
        for arg in get_args_of_function_type(node):
            self.visit(arg)
        star_arg = get_star_arg_of_function_type(node)
        if star_arg:
            self.visit(star_arg)
        star_kwds = get_star_kwds_of_function_type(node)
        if star_kwds:
            self.visit(star_kwds)
        return node

    def visit_Module(self, node: ast.Module) -> Any:
        self.name_gen.enter_scope(node)
        result = self.generic_visit(node)
        self.name_gen.exit_scope(node)
        return result

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        self.name_gen.enter_scope(node)
        result = self.generic_visit(node)
        self.name_gen.exit_scope(node)
        return result

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.name_gen.enter_scope(node)
        result = self.generic_visit(node)
        self.name_gen.exit_scope(node)
        return result

    def new_func_literal_name(self) -> str:
        return self.name_gen.new_func_literal_name()

    def new_variable_rename_name(self, original_name: str) -> str:
        return self.name_gen.new_variable_rename_name(original_name)

    def new_const_rename_name(self, original_name: str) -> str:
        return self.name_gen.new_const_rename_name(original_name)

    def new_arrow_type_name(self) -> str:
        return self.name_gen.new_arrow_type_name()
