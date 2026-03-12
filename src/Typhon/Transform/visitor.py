from typing import TypeGuard, override, Callable, cast, Any
from contextlib import contextmanager
import ast
from ..Grammar.typhon_ast import (
    PossibleAnnotatedNode,
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
    name_gen: UniqueNameGenerator
    parent_python_scopes: list[PythonScope]

    def __init__(self, module: ast.Module):
        self.name_gen = UniqueNameGenerator(module)
        self.parent_python_scopes = []

    def enter_scope(self, node: PythonScope):
        self.name_gen.enter_scope(node)
        self.parent_python_scopes.append(node)

    def exit_scope(self, node: PythonScope):
        self.name_gen.exit_scope(node)
        self.parent_python_scopes.pop()

    def is_python_scope(self, node: ast.AST) -> TypeGuard[PythonScope]:
        return isinstance(node, PythonScope)

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

    def new_func_literal_name(self, origin_node: ast.AST) -> str:
        return self.name_gen.new_name_anonymous(
            NameKind.FUNCTION_LITERAL,
            anchored_node=origin_node,
        )

    def new_control_comprehension_name(self, origin_node: ast.AST) -> str:
        return self.name_gen.new_name_anonymous(
            NameKind.CONTROL_COMPREHENSION,
            anchored_node=origin_node,
        )

    def new_anonymous_arg_name(self, origin_node: ast.AST, pos: int) -> str:
        return self.name_gen.new_name_anonymous(
            NameKind.ARGUMENT,
            anchored_node=origin_node,
            pretty_name=f"<arg {pos}>",
        )

    def new_variable_rename_name(self, original_name: str, anchor_node: ast.AST) -> str:
        return self.name_gen.new_name_decl(
            NameKind.VARIABLE,
            anchored_node=anchor_node,
            original_name=original_name,
        )

    def new_temp_variable_name(
        self,
        origin_node: ast.AST,
    ) -> str:
        return self.name_gen.new_name_decl(
            NameKind.VARIABLE,
            anchored_node=origin_node,
        )

    def new_const_rename_name(self, original_name: str, anchor_node: ast.AST) -> str:
        return self.name_gen.new_name_decl(
            NameKind.CONST,
            anchored_node=anchor_node,
            original_name=original_name,
        )

    def new_arrow_type_name(self, original_name: str, anchor_node: ast.AST) -> str:
        return self.name_gen.new_name_anonymous(
            NameKind.ARROW_TYPE,
            anchored_node=anchor_node,
            pretty_name=original_name,
        )

    def new_arg_name(self, original_name: str, anchor_node: ast.AST) -> str:
        return self.name_gen.new_name_decl(
            NameKind.ARGUMENT,
            anchored_node=anchor_node,
            original_name=original_name,
        )

    def new_typevar_name(self, original_name: str, anchor_node: ast.AST) -> str:
        return self.name_gen.new_name_decl(
            NameKind.TYPEVAR,
            anchored_node=anchor_node,
            original_name=original_name,
        )

    def new_class_name(self, original_name: str, anchor_node: ast.AST) -> str:
        return self.name_gen.new_name_decl(
            NameKind.CLASS,
            anchored_node=anchor_node,
            original_name=original_name,
        )


class _ParentStmtExprMixin:
    parent_stmts: list[ast.stmt]
    parent_exprs: list[ast.expr]

    def __init__(self):
        self.parent_stmts = []
        self.parent_exprs = []

    def get_parent_stmt(self) -> ast.stmt:
        if self.parent_stmts:
            return self.parent_stmts[-1]
        raise RuntimeError(
            "get_parent_stmt should only be called when there is a parent statement."
        )

    @contextmanager
    def _visit_stmt_expr(self, node: ast.AST):
        if isinstance(node, ast.stmt):
            self.parent_stmts.append(node)
            yield
            self.parent_stmts.pop()
        elif isinstance(node, ast.expr):
            self.parent_exprs.append(node)
            yield
            self.parent_exprs.pop()
        else:
            yield


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
        if isinstance(node, PossibleAnnotatedNode):
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

    def _generic_visit(
        self,
        node: ast.AST,
        visitor: ast.NodeVisitor | ast.NodeTransformer,
        otherwise: Callable[[ast.AST], Any],
    ) -> ast.AST:
        if isinstance(node, ast.Name):
            if is_function_literal(node):
                return self._visit_FunctionLiteral(node, visitor, False)
            elif is_function_type(node):
                return self._visit_FunctionType(node, visitor, False)
            elif is_control_comprehension(node):
                return self._visit_ControlComprehension(node, visitor, False)
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

    def run(self, module: ast.Module):
        self.visit(module)

    @override
    def visit(self, node: ast.AST):
        return self._visit(node, self, super().visit)

    @override
    def generic_visit(self, node: ast.AST):
        # visit() calls _visit() but generic_visit() does not. So we need to dispatch here too.
        return _TyphonExtendedNodeTransformerMixin._generic_visit(
            self, node, self, super().generic_visit
        )


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
        if self.is_python_scope(node):
            self.enter_scope(node)
            result = self._visit(node, self, super().visit)
            self.exit_scope(node)
            return result
        else:
            return self._visit(node, self, super().visit)

    @override
    def generic_visit(self, node: ast.AST):
        return _TyphonExtendedNodeTransformerMixin._generic_visit(
            self, node, self, super().generic_visit
        )


class TyphonParentASTVisitor(
    ast.NodeVisitor,
    _ScopeManagerMixin,
    _TyphonExtendedNodeTransformerMixin,
    _ParentStmtExprMixin,
    _ErrorHandlingMixin,
):
    def __init__(self, module: ast.Module):
        ast.NodeVisitor.__init__(self)
        _ScopeManagerMixin.__init__(self, module)
        _TyphonExtendedNodeTransformerMixin.__init__(self)
        _ErrorHandlingMixin.__init__(self, module)
        _ParentStmtExprMixin.__init__(self)
        self.module = module

    def run(self):
        self.visit(self.module)

    def visit_PossiblyAnnotatedNode(self, node: ast.AST):
        self._visit_Possibly_Annotated_Node(node, self, False)

    @override
    def visit(self, node: ast.AST):
        with self._visit_stmt_expr(node):
            if self.is_python_scope(node):
                self.enter_scope(node)
                result = self._visit(node, self, super().visit)
                self.exit_scope(node)
                return result
            else:
                return self._visit(node, self, super().visit)

    @override
    def generic_visit(self, node: ast.AST):
        return _TyphonExtendedNodeTransformerMixin._generic_visit(
            self, node, self, super().generic_visit
        )


class TyphonASTRawTransformer(
    ast.NodeTransformer,
    _TyphonExtendedNodeTransformerMixin,
):
    def __init__(self, module: ast.Module):
        ast.NodeTransformer.__init__(self)
        _TyphonExtendedNodeTransformerMixin.__init__(self)
        self.module = module

    def run(self):
        return self.visit(self.module)

    def visit_PossiblyAnnotatedNode(self, node: ast.AST):
        self._visit_Possibly_Annotated_Node(node, self, False)

    @override
    def visit(self, node: ast.AST):
        return self._visit(node, self, super().visit)

    @override
    def generic_visit(self, node: ast.AST) -> ast.AST:
        # visit() calls _visit() but generic_visit() does not. So we need to dispatch here too.
        return _TyphonExtendedNodeTransformerMixin._generic_visit(
            self, node, self, super().generic_visit
        )


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
    def visit(self, node: ast.AST):
        if self.is_python_scope(node):
            self.enter_scope(node)
            result = self._visit(node, self, super().visit)
            self.exit_scope(node)
            return result
        else:
            return self._visit(node, self, super().visit)

    @override
    def generic_visit(self, node: ast.AST) -> ast.AST:
        return _TyphonExtendedNodeTransformerMixin._generic_visit(
            self, node, self, super().generic_visit
        )
