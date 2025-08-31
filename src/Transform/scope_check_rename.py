import ast
import builtins
from contextlib import contextmanager
from dataclasses import dataclass

from ..Grammar.typhon_ast import (
    is_let,
    is_decl_assign,
    PosAttributes,
    get_pos_attributes,
    get_empty_pos_attributes,
)
from ..Grammar.syntax_errors import raise_scope_error
from .visitor import TyphonASTVisitor


@dataclass
class SymbolDeclaration:
    name: str
    is_mutable: bool
    renamed_to: str | None = None


@dataclass
class DeclarationContext:
    node: ast.AST
    is_mutable: bool


class SymbolScopeVisitor(TyphonASTVisitor):
    scopes: list[dict[str, SymbolDeclaration]]
    symbols: dict[str, list[SymbolDeclaration]]  # Synchronized with scopes stack
    declaration_context: DeclarationContext | None
    non_declaration_assign_context: bool

    def __init__(self):
        super().__init__()
        self.scopes = [{}]  # Stack of scopes
        self.symbols = {}
        self.visiting_left_hand_side = False
        self.declaration_context = None
        self.non_declaration_assign_context = False
        self.parent_python_scopes = []
        for sym in dir(builtins):
            self.add_symbol_declaration(
                sym,
                is_mutable=False,
                pos=get_empty_pos_attributes(),
            )  # Make builtins immutable

    def _enter_scope(self):
        self.scopes.append({})

    def _exit_scope(self):
        for var in self.scopes[-1].values():
            self.symbols[var.name].pop()
        self.scopes.pop()

    def current_scope(self):
        return self.scopes[-1]

    @contextmanager
    def scope(self):
        self._enter_scope()
        try:
            yield
        finally:
            self._exit_scope()

    @contextmanager
    def declaration(self, node: ast.AST, is_mutable: bool):
        assert self.declaration_context is None, "Left hand side in left hand side?"
        self.declaration_context = DeclarationContext(node=node, is_mutable=is_mutable)
        yield
        self.declaration_context = None

    @contextmanager
    def non_declaration_assign(self):
        assert not self.non_declaration_assign_context, "Nested non-declaration assign?"
        self.non_declaration_assign_context = True
        yield
        self.non_declaration_assign_context = False

    def get_symbol(self, name: str) -> SymbolDeclaration | None:
        decs = self.symbols.get(name, [])
        return decs[-1] if decs else None

    def is_shadowed(self, name: str) -> bool:
        return len(self.symbols.get(name, [])) > 1

    def add_symbol_declaration(
        self, name: str, is_mutable: bool, pos: PosAttributes
    ) -> SymbolDeclaration:
        if name in self.current_scope():
            # Already declared in this scope.
            # TODO: Appropriate error handling (SyntaxError?)
            self.duplicate_declaration(ast.Name(id=name, ctx=ast.Store(), **pos))
        dec = SymbolDeclaration(name, is_mutable)
        self.current_scope()[name] = dec
        self.symbols.setdefault(name, []).append(dec)
        return dec

    def reference_undeclared(self, name: ast.Name) -> ast.Name:
        # TODO: Raise error or keep for TDZ handling
        raise_scope_error(
            f"Symbol '{name.id}' is referenced before declaration.",
            **get_pos_attributes(name),
        )
        return name

    def assign_to_immutable(self, name: ast.Name) -> ast.Name:
        raise_scope_error(
            f"Cannot assign to immutable variable '{name.id}'.",
            **get_pos_attributes(name),
        )
        return name

    def duplicate_declaration(self, name: ast.Name) -> ast.Name:
        raise_scope_error(
            f"Symbol '{name.id}' is already declared in this scope.",
            **get_pos_attributes(name),
        )
        return name

    def visit_declaration(self, node: ast.AST, is_mutable: bool):
        with self.declaration(node, is_mutable=is_mutable):
            self.visit(node)
        return node

    def visit_list_scoped[T: ast.AST](self, nodes: list[T]):
        with self.scope():
            for node in nodes:
                self.visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.add_symbol_declaration(
                alias.name, is_mutable=False, pos=get_pos_attributes(alias)
            )
        self.generic_visit(node)
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name == "*":  # TODO Make this syntax error?
                raise NotImplementedError("from module import * is not supported")
            self.add_symbol_declaration(
                alias.asname or alias.name,
                is_mutable=False,
                pos=get_pos_attributes(alias),
            )
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        pos = get_pos_attributes(node)
        self.add_symbol_declaration(node.name, is_mutable=False, pos=pos)
        with self.scope():
            self.add_symbol_declaration("self", is_mutable=False, pos=pos)
            self.add_symbol_declaration("super", is_mutable=False, pos=pos)
            self.add_symbol_declaration(node.name, is_mutable=False, pos=pos)
            for tp in node.type_params or []:
                if isinstance(tp, (ast.TypeVar, ast.TypeVarTuple, ast.ParamSpec)):
                    self.add_symbol_declaration(tp.name, is_mutable=False, pos=pos)
            self.generic_visit(node)
        return node

    def visit_FunctionDef_AsyncFunctionDef(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ):
        self.add_symbol_declaration(
            node.name, is_mutable=False, pos=get_pos_attributes(node)
        )
        with self.scope():  # Type parameters scope
            for tp in node.type_params or []:
                if isinstance(tp, (ast.TypeVar, ast.TypeVarTuple, ast.ParamSpec)):
                    self.add_symbol_declaration(
                        tp.name, is_mutable=False, pos=get_pos_attributes(tp)
                    )
            with self.scope():  # Function arguments scope
                for arg in node.args.args + node.args.posonlyargs:
                    self.add_symbol_declaration(
                        arg.arg, is_mutable=False, pos=get_pos_attributes(arg)
                    )
                if node.args.vararg:
                    self.add_symbol_declaration(
                        node.args.vararg.arg,
                        is_mutable=False,
                        pos=get_pos_attributes(node.args.vararg),
                    )
                for arg in node.args.kwonlyargs:
                    self.add_symbol_declaration(
                        arg.arg, is_mutable=False, pos=get_pos_attributes(arg)
                    )
                if node.args.kwarg:
                    self.add_symbol_declaration(
                        node.args.kwarg.arg,
                        is_mutable=False,
                        pos=get_pos_attributes(node.args.kwarg),
                    )
                with self.scope():  # Function body scope
                    self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        return self.visit_FunctionDef_AsyncFunctionDef(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        return self.visit_FunctionDef_AsyncFunctionDef(node)

    def visit_If(self, node: ast.If):
        # TODO: Handle "if let" syntax for optional unwrapping
        self.visit(node.test)
        self.visit_list_scoped(node.body)
        self.visit_list_scoped(node.orelse)
        return node

    def visit_For_AsyncFor(self, node: ast.For | ast.AsyncFor):
        self.visit(node.iter)
        with self.scope():  # for initializer scope
            # Assuming target is a simple variable name for now
            self.visit_declaration(node.target, is_mutable=is_let(node))
            self.visit_list_scoped(node.body)
            self.visit_list_scoped(node.orelse)
        return node

    def visit_For(self, node: ast.For):
        return self.visit_For_AsyncFor(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        return self.visit_For_AsyncFor(node)

    def visit_While(self, node: ast.While):
        # TODO: Handle "while let" syntax for optional unwrapping
        self.visit(node.test)
        self.visit_list_scoped(node.body)
        self.visit_list_scoped(node.orelse)
        return node

    def visit_With_AsyncWith(self, node: ast.With | ast.AsyncWith):
        with self.scope():  # with contexts scope
            for item in node.items:
                self.visit(item.context_expr)
                if item.optional_vars:
                    self.visit_declaration(item.optional_vars, is_mutable=is_let(item))
            self.visit_list_scoped(node.body)
        return node

    def visit_With(self, node: ast.With):
        return self.visit_With_AsyncWith(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        return self.visit_With_AsyncWith(node)

    def visit_Try(self, node: ast.Try):
        self.visit_list_scoped(node.body)
        self.visit_list_scoped(node.handlers)
        self.visit_list_scoped(node.orelse)
        self.visit_list_scoped(node.finalbody)
        return node

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type:
            self.visit(node.type)
        with self.scope():  # except handler scope
            if node.name:
                name = ast.Name(
                    id=node.name, ctx=ast.Store(), **get_pos_attributes(node)
                )
                self.visit_declaration(
                    name,
                    is_mutable=False,
                )
                node.name = name.id
            self.visit_list_scoped(node.body)
        return node

    def visit_Match(self, node: ast.Match):
        self.visit(node.subject)
        self.visit_list_scoped(node.cases)
        return node

    # Match patterns. Basis of declarative patterns are MatchAs, MatchStar.
    # Other patterns are composed of these.
    # Declarations in patterns are immutable.
    def visit_match_case(self, node: ast.match_case):
        with self.scope():
            self.visit(node.pattern)
            if node.guard:
                self.visit(node.guard)
            self.visit_list_scoped(node.body)

    def visit_MatchAs(self, node: ast.MatchAs):
        if node.pattern:
            self.visit(node.pattern)
        if node.name:
            name = ast.Name(id=node.name, ctx=ast.Store(), **get_pos_attributes(node))
            self.visit_declaration(
                name,
                is_mutable=False,
            )
            node.name = name.id
        return node

    def visit_MatchStar(self, node: ast.MatchStar):
        if node.name:
            name = ast.Name(id=node.name, ctx=ast.Store(), **get_pos_attributes(node))
            self.visit_declaration(
                name,
                is_mutable=False,
            )
            node.name = name.id
        return node

    # Assignments
    def visit_Assign(self, node: ast.Assign):
        self.visit(node.value)
        if is_decl_assign(node):
            for target in node.targets:
                self.visit_declaration(target, is_mutable=is_let(node))
        else:  # LHS of non-declaration assignment is just reference
            with self.non_declaration_assign():
                for target in node.targets:
                    self.visit(target)
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if node.value:
            self.visit(node.value)
        if node.annotation:
            self.visit(node.annotation)
        if node.target:
            if is_decl_assign(node):
                self.visit_declaration(node.target, is_mutable=is_let(node))
            else:  # LHS of non-declaration assignment is just reference
                with self.non_declaration_assign():
                    self.visit(node.target)
        return node

    def visit_AugAssign(self, node: ast.AugAssign):
        self.visit(node.value)
        # LHS of non-declaration assignment is just reference
        with self.non_declaration_assign():
            self.visit(node.target)
        return node

    def visit_NamedExpr(self, node: ast.NamedExpr):
        self.visit(node.value)
        with self.non_declaration_assign():
            self.visit(node.target)
        return node

    def visit_Name(self, node: ast.Name):
        # TODO: Insert global/nonlocal handling automatically
        # TODO: TDZ handling for Top-level code
        if self.declaration_context:
            # Left-hand side of an declaration assignment
            if self.current_scope().get(node.id):
                return self.duplicate_declaration(node)
            sym = self.add_symbol_declaration(
                node.id,
                is_mutable=self.declaration_context.is_mutable,
                pos=get_pos_attributes(node),
            )
            if self.is_shadowed(node.id):
                new_name = self.new_variable_rename_name(node.id)
                sym.renamed_to = new_name
                node.id = new_name
                print(f"Renamed variable '{sym.name}' to '{new_name}'")
        else:
            # Reference to the symbol
            sym = self.get_symbol(node.id)
            if sym is None:
                return self.reference_undeclared(node)
            if not sym.is_mutable and self.non_declaration_assign_context:
                return self.assign_to_immutable(node)
            # Rename variable if necessary
            if sym and sym.renamed_to:
                node.id = sym.renamed_to
                print(f"Renamed variable '{sym.name}' to '{sym.renamed_to}'")
        return node


def scope_check_rename(node: ast.Module):
    visitor = SymbolScopeVisitor()
    visitor.visit(node)
