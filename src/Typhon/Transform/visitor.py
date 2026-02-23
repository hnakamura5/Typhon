from typing import override, Callable, cast
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
    is_control_comprehension,
    get_control_comprehension_def,
    set_control_comprehension_def,
    get_type_annotation,
    set_type_annotation,
    PosAttributes,
)
from .name_generator import UniqueNameGenerator, PythonScope, NameKind
from ..Grammar.syntax_errors import (
    raise_type_annotation_error,
    try_handle_syntax_error_or,
)


class _ScopeManagerMixin:
    parent_classes: list[ast.ClassDef]
    parent_functions: list[ast.FunctionDef | ast.AsyncFunctionDef]
    parent_stmts: list[ast.stmt]
    parent_exprs: list[ast.expr]
    name_gen: UniqueNameGenerator
    parent_python_scopes: list[PythonScope]

    def __init__(self, module: ast.Module):
        self.parent_stmts = []
        self.parent_exprs = []
        self.parent_classes = []
        self.parent_functions = []
        self.name_gen = UniqueNameGenerator(module)
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

    def get_parent_function(self) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        if self.parent_functions:
            return self.parent_functions[-1]
        return None

    def get_parent_python_scope(self, ignore_top: bool = False) -> PythonScope:
        if not self.parent_python_scopes:
            # TODO: proper error handling
            raise RuntimeError("No Module scope found.")
        if ignore_top:
            if len(self.parent_python_scopes) == 1:
                raise RuntimeError("No parent scope found (at top level).")
            return self.parent_python_scopes[-2]
        return self.parent_python_scopes[-1]

    def now_is_top_level(self, ignore_current: bool = False) -> bool:
        if ignore_current:
            return len(self.parent_python_scopes) == 2
        return len(self.parent_python_scopes) == 1

    def new_func_literal_name(self) -> str:
        return self.name_gen.new_name(NameKind.FUNCTION_LITERAL)

    def new_control_comprehension_name(self) -> str:
        return self.name_gen.new_name(NameKind.CONTROL_COMPREHENSION)

    def new_variable_rename_name(self, original_name: str) -> str:
        return self.name_gen.new_name(NameKind.VARIABLE, original_name)

    def new_temp_variable_name(self) -> str:
        return self.name_gen.new_name(NameKind.VARIABLE, "")

    def new_const_rename_name(self, original_name: str) -> str:
        return self.name_gen.new_name(NameKind.CONST, original_name)

    def new_arrow_type_name(self, original_name: str = "") -> str:
        return self.name_gen.new_name(NameKind.ARROW_TYPE, original_name)

    def new_name(self, kind: NameKind, original_name: str = "") -> str:
        return self.name_gen.new_name(kind, original_name)

    def new_arg_name(self, original_name: str) -> str:
        return self.name_gen.new_name(NameKind.ARGUMENT, original_name)

    def new_typevar_name(self, original_name: str) -> str:
        return self.name_gen.new_name(NameKind.TYPEVAR, original_name)

    def new_class_name(self, original_name: str) -> str:
        return self.name_gen.new_name(NameKind.CLASS, original_name)


def flat_map[T](f: Callable[[T], T | list[T] | None], v: list[T]) -> list[T]:
    result: list[T] = []
    for item in v:
        new_item: T | list[T] | None = f(item)
        if new_item is None:
            continue
        if isinstance(new_item, list):
            result.extend(cast(list[T], new_item))
        else:
            result.append(new_item)
    return result


def flat_append(result: list[ast.AST], item: ast.AST | list[ast.AST] | None) -> None:
    if item is None:
        return
    if isinstance(item, list):
        result.extend(item)
    else:
        result.append(item)


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

    def _visit_ControlComprehension(
        self,
        node: ast.Name,
        visitor: ast.NodeVisitor | ast.NodeTransformer,
        transform: bool,
    ):
        func_def = get_control_comprehension_def(node)
        if func_def is not None:
            new_def = visitor.visit(func_def)
            if transform and isinstance(new_def, ast.FunctionDef):
                set_control_comprehension_def(node, new_def)
        return node

    def _visit_Possibly_Annotated_Node(
        self,
        node: ast.AST,
        visitor: ast.NodeVisitor | ast.NodeTransformer,
        transform: bool,
    ):
        type_annotation = get_type_annotation(node)
        if type_annotation is not None:
            new_annotation = visitor.visit(type_annotation)
            if transform:
                set_type_annotation(node, new_annotation)
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
            elif is_control_comprehension(node):
                visit = getattr(
                    visitor, "visit_ControlComprehension", visitor.generic_visit
                )
                return visit(node)
        return otherwise(node)


class _ErrorHandlingMixin:
    module: ast.Module

    def __init__(self, module: ast.Module):
        self.module = module

    def _raise_type_annotation_error_default[T](
        self, orelse: T, message: str, pos: PosAttributes
    ) -> T:
        return try_handle_syntax_error_or(
            orelse,
            self.module,
            lambda: raise_type_annotation_error(message, **pos),
        )


class TyphonASTRawVisitor(
    ast.NodeVisitor,
    _TyphonExtendedNodeTransformerMixin,
):
    def visit_PossiblyAnnotatedNode(self, node: ast.AST):
        self._visit_Possibly_Annotated_Node(node, self, False)

    @override
    def visit(self, node: ast.AST):
        return self._visit(node, self, super().visit)

    @override
    def generic_visit(self, node: ast.AST):
        # visit() calls _visit() but generic_visit() does not. So we need to dispatch here too.
        if isinstance(node, ast.Name):
            if is_function_literal(node):
                return self._visit_FunctionLiteral(node, self, False)
            elif is_function_type(node):
                return self._visit_FunctionType(node, self, False)
            elif is_control_comprehension(node):
                return self._visit_ControlComprehension(node, self, False)
        self.visit_PossiblyAnnotatedNode(node)
        return super().generic_visit(node)


class TyphonASTVisitor(
    ast.NodeVisitor,
    _ScopeManagerMixin,
    _TyphonExtendedNodeTransformerMixin,
    _ErrorHandlingMixin,
):
    def __init__(self, module: ast.Module):
        ast.NodeVisitor.__init__(self)
        _ScopeManagerMixin.__init__(self, module)
        _TyphonExtendedNodeTransformerMixin.__init__(self)
        _ErrorHandlingMixin.__init__(self, module)
        self.module = module

    def run(self):
        self.visit(self.module)

    def visit_PossiblyAnnotatedNode(self, node: ast.AST):
        self._visit_Possibly_Annotated_Node(node, self, False)

    @override
    def visit(self, node: ast.AST):
        with self._visit_scope(node):
            return self._visit(node, self, super().visit)

    @override
    def generic_visit(self, node: ast.AST):
        # visit() calls _visit() but generic_visit() does not. So we need to dispatch here too.
        if isinstance(node, ast.Name):
            if is_function_literal(node):
                return self._visit_FunctionLiteral(node, self, False)
            elif is_function_type(node):
                return self._visit_FunctionType(node, self, False)
            elif is_control_comprehension(node):
                return self._visit_ControlComprehension(node, self, False)
        self.visit_PossiblyAnnotatedNode(node)
        return super().generic_visit(node)


class TyphonASTTransformer(
    ast.NodeTransformer,
    _ScopeManagerMixin,
    _TyphonExtendedNodeTransformerMixin,
    _ErrorHandlingMixin,
):
    def __init__(self, module: ast.Module):
        ast.NodeTransformer.__init__(self)
        _ScopeManagerMixin.__init__(self, module)
        _TyphonExtendedNodeTransformerMixin.__init__(self)
        _ErrorHandlingMixin.__init__(self, module)
        self.module = module

    def run(self):
        return self.visit(self.module)

    def visit_PossiblyAnnotatedNode(self, node: ast.AST):
        self._visit_Possibly_Annotated_Node(node, self, True)

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
            elif is_control_comprehension(node):
                return self._visit_ControlComprehension(node, self, True)
        self.visit_PossiblyAnnotatedNode(node)
        return super().generic_visit(node)
