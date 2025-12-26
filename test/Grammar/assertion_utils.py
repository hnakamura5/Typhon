import ast
import tokenize
from typing import Type, Union, Any
import io
from ...src.Typhon.Grammar.typhon_ast import get_pos_attributes_if_exists
from ...src.Typhon.Grammar.parser import parse_string
from ...src.Typhon.Transform.transform import transform
from ...src.Typhon.Grammar.tokenizer_custom import TokenizerCustom
from ...src.Typhon.Grammar.token_factory_custom import token_stream_factory
from ...src.Typhon.Grammar.unparse_custom import unparse_custom
from ...src.Typhon.SourceMap.ast_matching import match_ast, MatchResult
from ...src.Typhon.SourceMap.ast_match_based_map import MatchBasedSourceMap
from ...src.Typhon.SourceMap.defined_name_retrieve import defined_name_retrieve
from ...src.Typhon.SourceMap.datatype import Range
from ...src.Typhon.Driver.debugging import set_debug_first_error, is_debug_first_error
from ...src.Typhon.Grammar.syntax_errors import TyphonSyntaxErrorList
import inspect
from contextlib import contextmanager

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


class AllTokenAsserter:
    def __init__(self, code: str):
        tok_stream = token_stream_factory(io.StringIO(code).readline)
        self.tokenizer = TokenizerCustom(tok_stream, verbose=True)
        self.tokens = self.tokenizer.read_all_tokens()
        self.index = 0
        print(f"All tokens: {self.tokens}")

    def next(
        self,
        type_: int,
        string: str,
        start: tuple[int, int] | None = None,
        end: tuple[int, int] | None = None,
    ):
        assert self.index < len(self.tokens), "No more tokens"
        token = self.tokens[self.index]
        self.index += 1
        assert_token(token, type_, string, start, end)

    def assert_length(self, length: int):
        assert len(self.tokens) == length, (
            f"Expected {length} tokens, got {len(self.tokens)}"
        )


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


def assert_ast_equals(
    typhon_code: str,
    python_code: str,
    show_typhon_token: bool = True,
    show_python_token: bool = True,
) -> ast.Module:
    show_token(typhon_code, show_typhon_token, show_python_token)
    parsed = parse_string(typhon_code, mode="exec", verbose=PARSER_VERBOSE)
    assert isinstance(parsed, ast.Module)
    print(ast.dump(parsed))
    print(unparse_custom(parsed))
    assert unparse_custom(parsed).strip() == python_code.strip()
    return parsed


def assert_transform_equals(typhon_ast: ast.Module, python_code: str):
    assert isinstance(typhon_ast, ast.Module)
    transform(typhon_ast)
    print(f"Typhon AST:\n\n{unparse_custom(typhon_ast)}")
    print(f"\nTransform result:\n\n{unparse_custom(typhon_ast)}")
    assert unparse_custom(typhon_ast).strip() == python_code.strip()


def assert_ast_transform(typhon_code: str, python_code: str):
    parsed = parse_string(typhon_code, mode="exec", verbose=PARSER_VERBOSE)
    assert isinstance(parsed, ast.Module)
    transform(parsed)
    print(f"Typhon code:\n{typhon_code}")
    print(f"Transform result:\n\n{unparse_custom(parsed)}")
    print(f"\nExpected Python code:\n\n{python_code.strip()}")
    assert unparse_custom(parsed).strip() == python_code.strip()
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


@contextmanager
def first_error_test():
    previous_setting = is_debug_first_error()
    set_debug_first_error(True)
    yield
    set_debug_first_error(previous_setting)


def assert_transform_first_error(
    typhon_ast: str, exception: type = Exception, error_message: str = ""
):
    parsed = parse_string(typhon_ast, mode="exec")
    assert isinstance(parsed, ast.Module)
    with first_error_test():
        try:
            transform(parsed)
            assert False, "Expected exception but none was raised"
        except Exception as e:
            _assert_exception(e, exception, error_message)


def assert_transform_errors(typhon_ast: str, exceptions: list[type]):
    parsed = parse_string(typhon_ast, mode="exec")
    assert isinstance(parsed, ast.Module)
    try:
        transform(parsed)
        assert False, "Expected exception but none was raised"
    except TyphonSyntaxErrorList as e:
        assert len(e.errors) == len(exceptions), (
            f"Expected {len(exceptions)} errors, got {len(e.errors)}"
        )
        for error, expected_exception in zip(e.errors, exceptions):
            assert isinstance(error, expected_exception), (
                f"Expected exception {expected_exception}, got {type(error)}"
            )


def assert_ast_type[T](node: ast.AST, t: Type[T]) -> T:
    assert isinstance(node, t), f"Expected {t}, got {type(node)}"
    return node


def assert_ast_match_unparse_code(code: Any):
    code_ast = get_code_source_ast(code)
    code_unparsed_ast = ast.parse(unparse_custom(code_ast)).body[0]
    result = match_ast(code_ast, code_unparsed_ast)
    assert result is not None
    return result


def assert_ast_match_unparse_success(node: ast.AST) -> tuple[MatchResult, str]:
    unparse = unparse_custom(node)
    unparsed_ast = ast.parse(unparse)
    defined_name_retrieve(unparsed_ast, unparse)
    print(
        f"Unparsed code:\n{unparse}\nunparsed lines:{unparse.splitlines()}\nunparsed AST:{ast.dump(unparsed_ast)}"
    )
    result = match_ast(node, unparsed_ast)
    assert result is not None
    return result, unparse


def assert_typh_code_match_unparse(code: str) -> tuple[MatchResult, str]:
    parsed = parse_string(code)
    assert parsed
    assert isinstance(parsed, ast.Module)
    transform(parsed)
    return assert_ast_match_unparse_success(parsed)


def assert_node_range(node: ast.AST, expected_range: Range | None):
    attr = get_pos_attributes_if_exists(node)
    if attr is None or expected_range is None:
        assert attr == expected_range, f"Expected range {expected_range}, got {attr}"
    if attr is not None:
        node_range = Range.from_pos_attr_may_not_end(attr)
        assert node_range == expected_range, (
            f"Expected range {expected_range}, got {node_range}"
        )


def assert_source_map_ident(code: Any):
    code_ast = get_code_source_ast(code)
    mapping = match_ast(code_ast, code_ast)
    assert mapping is not None
    source_map = MatchBasedSourceMap(
        mapping.left_to_right,
        mapping.right_to_left,
        unparse_custom(code_ast),
        "<string>",
    )
    for left_node, right_node in mapping.left_to_right.items():
        print(f"Asserting node range for {ast.dump(left_node)}")
        print(f"    mapped to {ast.dump(right_node)}")
        assert_node_range(
            right_node, source_map.origin_node_to_unparsed_range(left_node)
        )


class SourceMapAsserter:
    def __init__(self, typhon_code: str):
        mapping, unparsed_code = assert_typh_code_match_unparse(typhon_code)
        self.source_map = MatchBasedSourceMap(
            mapping.left_to_right,
            mapping.right_to_left,
            typhon_code,
            "<string>",
        )
        self.origin_code = typhon_code
        self.unparsed_code = unparsed_code

    def assert_range(self, origin_range: Range, unparsed_range: Range):
        mapped_range = self.source_map.unparsed_range_to_origin(unparsed_range)
        assert mapped_range == origin_range, (
            f"Expected mapped range {origin_range}, got {mapped_range}"
        )

    def assert_range_text(
        self,
        origin_range: Range,
        origin_text: str,
        unparsed_range: Range,
        unparsed_text: str,
    ):
        mapped_range = self.source_map.unparsed_range_to_origin(unparsed_range)
        print(
            f"Unparsed interval tree: {self.source_map.unparsed_interval_tree.interval_tree}"
        )
        assert mapped_range is not None, "Mapped range is None"
        print(
            f"Mapped range: origin: {origin_range} origin_text get:'{origin_range.of_string(self.origin_code)}' origin_lines:{self.origin_code.splitlines()} unparsed: {mapped_range} unparsed_text get:'{mapped_range.of_string(self.unparsed_code)}' unparsed_lines:{self.unparsed_code.splitlines()}"
        )
        assert mapped_range == origin_range, (
            f"Expected mapped range {origin_range}, got {mapped_range}"
        )
        mapped_text = mapped_range.of_string(self.origin_code)
        assert mapped_text == origin_text, (
            f"Expected mapped text '{origin_text}', got '{mapped_text}'"
        )
        unparsed_mapped_text = unparsed_range.of_string(self.unparsed_code)
        assert unparsed_mapped_text == unparsed_text, (
            f"Expected unparsed text '{unparsed_text}', got '{unparsed_mapped_text}'"
        )


def show_token(
    source: str, show_typhon_token: bool = True, show_python_token: bool = True
):
    if show_python_token:
        print("Tokens of Python tokenizer:")
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            print(f"    {tok}")
    if show_typhon_token:
        print("Tokens of Typhon Token Factory:")
        tok_stream = token_stream_factory(io.StringIO(source).readline)
        for tok in tok_stream:
            print(f"    {tok}")
    print("Tokens of Typhon Custom tokenizer:")
    tok_stream = token_stream_factory(io.StringIO(source).readline)
    tokenizer = TokenizerCustom(tok_stream, verbose=True)
    tok = tokenizer.getnext()
    while tok.type != tokenize.ENDMARKER:
        print(f"    {tok}")
        tok = tokenizer.getnext()


def get_code_source_ast(code: Any) -> ast.AST:
    # Workaround to remove indent from inspect.getsource, because it cannot handle
    # nested functions properly.
    def _remove_indent(source: str) -> str:
        lines = source.splitlines()
        if not lines:
            return source
        first_line = lines[0]
        indent = len(first_line) - len(first_line.lstrip())
        trimmed_lines = [
            line[indent:] if len(line) >= indent else line for line in lines
        ]
        return "\n".join(trimmed_lines)

    source = _remove_indent(inspect.getsource(code))
    code_def = ast.parse(source).body[0]
    return code_def
