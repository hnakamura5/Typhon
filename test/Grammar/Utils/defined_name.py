import ast
from Typhon.Grammar.typhon_ast import get_defined_name, get_pos_attributes
from Typhon.SourceMap.defined_name_retrieve import defined_name_retrieve

decorator_func_code = """
from decorators import decorator, another_decorator

@decorator('arg1', 'arg2')
@another_decorator
def f(x: int) -> int:
    return x + 1
"""


def test_decorator_func_code():
    parsed = ast.parse(decorator_func_code)
    defined_name_retrieve(parsed, decorator_func_code)
    ast_func = parsed.body[1]  # FunctionDef node
    assert isinstance(ast_func, ast.FunctionDef)
    name_node = get_defined_name(ast_func)
    assert name_node is not None
    print(
        f"Defined name node: {ast.dump(name_node)} at {get_pos_attributes(name_node)}"
    )
    assert name_node.lineno == 6
    assert name_node.col_offset == 4
    assert name_node.end_lineno == 6
    assert name_node.end_col_offset == 5
    assert name_node.id == "f"


decorator_class_code = """
from decorators import class_decorator

@class_decorator
class MyClass:
    def method(self) -> None:
        pass
"""


def test_decorator_class_code():
    parsed = ast.parse(decorator_class_code)
    defined_name_retrieve(parsed, decorator_class_code)
    ast_class = parsed.body[1]  # ClassDef node
    assert isinstance(ast_class, ast.ClassDef)
    name_node = get_defined_name(ast_class)
    assert name_node is not None
    print(
        f"Defined name node: {ast.dump(name_node)} at {get_pos_attributes(name_node)}"
    )
    assert name_node.lineno == 5
    assert name_node.col_offset == 6
    assert name_node.end_lineno == 5
    assert name_node.end_col_offset == 13
    assert name_node.id == "MyClass"


import_code = """
import module.submodule
def func():
    pass
"""


def test_import_code():
    parsed = ast.parse(import_code)
    defined_name_retrieve(parsed, import_code)
    ast_import = parsed.body[0]  # Import node
    assert isinstance(ast_import, ast.Import)
    alias_node = ast_import.names[0]
    name_node = get_defined_name(alias_node)
    assert name_node is not None
    print(
        f"Defined name node: {ast.dump(name_node)} at {get_pos_attributes(name_node)}"
    )
    assert name_node.lineno == 2
    assert name_node.col_offset == 14
    assert name_node.end_lineno == 2
    assert name_node.end_col_offset == 23
    assert name_node.id == "submodule"


import_from_code = """
from pathlib import Path as P, PurePath
"""


def test_import_from_code():
    parsed = ast.parse(import_from_code)
    defined_name_retrieve(parsed, import_from_code)
    ast_import_from = parsed.body[0]  # ImportFrom node
    assert isinstance(ast_import_from, ast.ImportFrom)
    alias_node_as = ast_import_from.names[0]
    name_node_as = get_defined_name(alias_node_as)
    assert name_node_as is not None
    print(
        f"Defined name node (asname): {ast.dump(name_node_as)} at {get_pos_attributes(name_node_as)}"
    )
    assert name_node_as.lineno == 2
    assert name_node_as.col_offset == 28
    assert name_node_as.end_lineno == 2
    assert name_node_as.end_col_offset == 29
    assert name_node_as.id == "P"

    alias_node_no_as = ast_import_from.names[1]
    name_node_no_as = get_defined_name(alias_node_no_as)
    assert name_node_no_as is not None
    print(
        f"Defined name node (no asname): {ast.dump(name_node_no_as)} at {get_pos_attributes(name_node_no_as)}"
    )
    assert name_node_no_as.lineno == 2
    assert name_node_no_as.col_offset == 31
    assert name_node_no_as.end_lineno == 2
    assert name_node_no_as.end_col_offset == 39
    assert name_node_no_as.id == "PurePath"
