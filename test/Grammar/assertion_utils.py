import ast
from ...src.Grammar.parser import parse_string
from ...src.Transform.transform import transform
import tokenize
from typing import Type, Union


def assert_token(token: tokenize.TokenInfo, type_: int, string: str):
    assert token.type == type_, f"Expected {type_}, got {token.type}"
    assert token.string == string, f"Expected '{string}', got '{token.string}'"


def assert_ast_equals(typhon_code: str, python_code: str) -> ast.Module:
    parsed = parse_string(typhon_code, mode="exec", verbose=True)
    assert isinstance(parsed, ast.Module)
    assert ast.unparse(parsed) == python_code.strip()
    return parsed


def assert_transform_equals(typhon_ast: ast.Module, python_code: str):
    assert isinstance(typhon_ast, ast.Module)
    transform(typhon_ast)
    assert ast.unparse(typhon_ast) == python_code.strip()


def assert_ast_error(typhon_code: str, error_message: str = ""):
    # TODO: Support error type
    try:
        parse_string(typhon_code, mode="exec", verbose=True)
        assert False, f"Expected error: {error_message}"
    except Exception:
        pass


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
