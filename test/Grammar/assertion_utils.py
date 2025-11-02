import ast
import tokenize
from typing import Type, Union
import io
from ...src.Typhon.Grammar.parser import parse_string
from ...src.Typhon.Transform.transform import transform
from ...src.Typhon.Grammar.tokenizer_custom import TokenizerCustom
from ...src.Typhon.Grammar.token_factory_custom import token_stream_factory

PARSER_VERBOSE = False


def assert_token(
    token: tokenize.TokenInfo,
    type_: int,
    string: str,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
):
    assert token.type == type_, f"Expected {type_}, got {token.type}"
    assert token.string == string, f"Expected '{string}', got '{token.string}'"
    if start is not None:
        assert token.start == start, f"Expected start {start}, got {token.start}"
    if end is not None:
        assert token.end == end, f"Expected end {end}, got {token.end}"


class TokenizerAsserter:
    def __init__(self, code: str):
        tok_stream = token_stream_factory(io.StringIO(code).readline)
        self.tokenizer = TokenizerCustom(tok_stream, verbose=True)

    def next(
        self,
        type_: int,
        string: str,
        start: tuple[int, int] | None = None,
        end: tuple[int, int] | None = None,
    ):
        token = self.tokenizer.getnext()
        assert_token(token, type_, string, start, end)


class RawTokenStreamAsserter:
    def __init__(self, code: str):
        self.tokens = token_stream_factory(io.StringIO(code).readline)

    def next(
        self,
        type_: int,
        string: str,
        start: tuple[int, int] | None = None,
        end: tuple[int, int] | None = None,
    ):
        token = next(self.tokens)
        assert_token(token, type_, string, start, end)


def assert_ast_equals(typhon_code: str, python_code: str) -> ast.Module:
    show_token(typhon_code)
    parsed = parse_string(typhon_code, mode="exec", verbose=PARSER_VERBOSE)
    assert isinstance(parsed, ast.Module)
    print(ast.dump(parsed))
    print(ast.unparse(parsed))
    assert ast.unparse(parsed) == python_code.strip()
    return parsed


def assert_transform_equals(typhon_ast: ast.Module, python_code: str):
    assert isinstance(typhon_ast, ast.Module)
    transform(typhon_ast)
    print(f"Transform result:\n{ast.unparse(typhon_ast)}")
    assert ast.unparse(typhon_ast) == python_code.strip()


def assert_ast_transform(typhon_code: str, python_code: str):
    parsed = parse_string(typhon_code, mode="exec", verbose=PARSER_VERBOSE)
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
    print("Tokens of Raw tokenizer:")
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        print(f"    {tok}")
    print("Tokens of Token Factory:")
    tok_stream = token_stream_factory(io.StringIO(source).readline)
    for tok in tok_stream:
        print(f"    {tok}")
    print("Tokens of Custom tokenizer:")
    tok_stream = tokenize.generate_tokens(io.StringIO(source).readline)
    tokenizer = TokenizerCustom(tok_stream, verbose=True)
    tok = tokenizer.getnext()
    while tok.type != tokenize.ENDMARKER:
        print(f"    {tok}")
        tok = tokenizer.getnext()
