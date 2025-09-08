import ast
from ..src.Grammar.parser import parse_string
from ..src.Transform.transform import transform
import tokenize
from typing import Type, Union

PARSER_VERBOSE = True


def assert_token(token: tokenize.TokenInfo, type_: int, string: str):
    assert token.type == type_, f"Expected {type_}, got {token.type}"
    assert token.string == string, f"Expected '{string}', got '{token.string}'"


def assert_ast_equals(typhon_code: str, python_code: str) -> ast.Module:
    parsed = parse_string(typhon_code, mode="exec", verbose=PARSER_VERBOSE)
    assert isinstance(parsed, ast.Module)
    print(ast.unparse(parsed))
    assert ast.unparse(parsed) == python_code.strip()
    return parsed


def assert_transform_equals(typhon_ast: ast.Module, python_code: str):
    assert isinstance(typhon_ast, ast.Module)
    transform(typhon_ast)
    print(f"Transform result:\n{ast.unparse(typhon_ast)}")
    assert ast.unparse(typhon_ast) == python_code.strip()


def assert_ast_transform(typhon_code: str, python_code: str):
    parsed = parse_string(typhon_code, mode="exec")
    assert isinstance(parsed, ast.Module)
    transform(parsed)
    print(f"Transform result:\n{ast.unparse(parsed)}")
    assert ast.unparse(parsed) == python_code.strip()
    return parsed


def _assert_exception(e: Exception, exception: type, error_message: str):
    assert isinstance(e, exception)
    if error_message:
        assert error_message in str(e), (
            f"Expected error message: '{error_message}', got: '{str(e)}'"
        )


def assert_ast_error(
    typhon_code: str, exception: type = Exception, error_message: str = ""
):
    try:
        parse_string(typhon_code, mode="exec", verbose=PARSER_VERBOSE)
        assert False, "Expected exception but none was raised"
    except Exception as e:
        _assert_exception(e, exception, error_message)


def assert_transform_error(
    typhon_ast: str, exception: type = Exception, error_message: str = ""
):
    parsed = parse_string(typhon_ast, mode="exec")
    assert isinstance(parsed, ast.Module)
    try:
        transform(parsed)
        assert False, "Expected exception but none was raised"
    except Exception as e:
        _assert_exception(e, exception, error_message)


def assert_ast_type[T](node: ast.AST, t: Type[T]) -> T:
    assert isinstance(node, t), f"Expected {t}, got {type(node)}"
    return node


def show_token(source: str):
    import io
    from pegen.tokenizer import Tokenizer

    tok_stream = tokenize.generate_tokens(io.StringIO(source).readline)
    tokenizer = Tokenizer(tok_stream, verbose=True)
    print("Tokens:")
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        print(tok)
    print("Tokens in pegen:")
    tok = tokenizer.getnext()
    while tok.type != tokenize.ENDMARKER:
        print(tok)
        tok = tokenizer.getnext()
