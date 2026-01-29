import ast
from ..Grammar.typhon_ast import (
    set_defined_name,
    get_pos_attributes,
    set_import_from_names,
)


# Assume the base source code is in canonical form by ast.unparse
class _DefinedNameRetriever(ast.NodeVisitor):
    def __init__(self, unparsed_source_code: str):
        self.unparsed_source_code = unparsed_source_code

    def _visit_defines(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
        column_offset: int,
    ):
        pos = get_pos_attributes(node)
        start_line = pos["lineno"]  # decorator is not included in the original position
        start_col = pos["col_offset"] + column_offset
        print(
            f"Retrieving defined name for node: {ast.dump(node)} at line {start_line}, col {start_col}"
        )
        name = ast.Name(
            id=node.name,
            ctx=ast.Store(),
            lineno=start_line,
            col_offset=start_col,
            end_lineno=start_line,
            end_col_offset=start_col + len(node.name),
        )
        set_defined_name(node, name)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_defines(node, len("def "))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_defines(node, len("async def "))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self._visit_defines(node, len("class "))
        self.generic_visit(node)

    def visit_alias(self, node: ast.alias):
        pos = get_pos_attributes(node)
        start_line = pos["lineno"]
        start_col = pos["col_offset"]
        if node.asname:
            if pos["end_col_offset"]:
                start_col = pos["end_col_offset"] - len(node.asname)
            else:
                # Fallback: search 'as' in the source code line
                # TODO: Is this truly necessary? and reliable?
                line_start = self.unparsed_source_code.splitlines()[start_line - 1]
                as_index = line_start.find(" as ", start_col)
                if as_index != -1:
                    start_col = as_index + len(" as ")
            name = ast.Name(
                id=node.asname,
                ctx=ast.Store(),
                lineno=start_line,
                col_offset=start_col,
                end_lineno=start_line,
                end_col_offset=start_col + len(node.asname),
            )
            set_defined_name(node, name)
        else:
            # No asname. Stem of imported name is the defined name.
            after_last_dot_index = node.name.rfind(".") + 1
            start_col += after_last_dot_index
            defined_name = node.name[after_last_dot_index:]
            name = ast.Name(
                id=defined_name,
                ctx=ast.Store(),
                lineno=start_line,
                col_offset=start_col,
                end_lineno=start_line,
                end_col_offset=start_col + len(defined_name),
            )
            set_defined_name(node, name)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            self.visit(alias)
        column = node.col_offset + len("from ") + node.level * len(".")
        module_names: list[ast.Name] = []
        for mod in node.module.split(".") if node.module else []:
            if mod:
                name = ast.Name(
                    id=mod,
                    lineno=node.lineno,
                    col_offset=column,
                    end_lineno=node.lineno,
                    end_col_offset=column + len(mod),
                    ctx=ast.Load(),
                )
                module_names.append(name)
            column += len(mod) + len(".")
        set_import_from_names(node, module_names)


def defined_name_retrieve(node: ast.AST, unparsed_source_code: str) -> None:
    visitor = _DefinedNameRetriever(unparsed_source_code)
    visitor.visit(node)
