import attrs
import enum
import operator
import ast
from functools import reduce
from tokenize import (
    OP,
    NAME,
    STRING,
    COMMENT,
    NUMBER,
    FSTRING_START,
    FSTRING_MIDDLE,
    FSTRING_END,
)
from ..Grammar.tokenizer_custom import TokenInfo
from ..Driver.debugging import debug_file_write_verbose
from lsprotocol import types
from pygls.workspace import TextDocument


# https://code.visualstudio.com/api/language-extensions/semantic-highlight-guide
TokenTypes = [
    "namespace",  # For identifiers that declare or reference a namespace, module, or package.
    "class",  # For identifiers that declare or reference a class type.
    "enum",  # For identifiers that declare or reference an enumeration type.
    "interface",  # For identifiers that declare or reference an interface type.
    "struct",  # For identifiers that declare or reference a struct type.
    "typeParameter",  # For identifiers that declare or reference a type parameter.
    "type",  # For identifiers that declare or reference a type that is not covered above.
    "parameter",  # For identifiers that declare or reference a function or method parameters.
    "variable",  # For identifiers that declare or reference a local or global variable.
    "property",  # For identifiers that declare or reference a member property, member field, or member variable.
    "enumMember",  # For identifiers that declare or reference an enumeration property, constant, or member.
    "decorator",  # For identifiers that declare or reference decorators and annotations.
    "event",  # For identifiers that declare an event property.
    "function",  # For identifiers that declare a function.
    "method",  # For identifiers that declare a member function or method.
    "macro",  # For identifiers that declare a macro.
    "label",  # For identifiers that declare a label.
    "comment",  # For tokens that represent a comment.
    "string",  # For tokens that represent a string literal.
    "keyword",  # For tokens that represent a language keyword.
    "number",  # For tokens that represent a number literal.
    "regexp",  # For tokens that represent a regular expression literal.
    "operator",  # For tokens that represent an operator.
]
TokenTypesMap = {t: i for i, t in enumerate(TokenTypes)}


# TODO: Temporal implementation
def token_to_type(tok: TokenInfo) -> str:
    if tok.string in (
        "def",
        "class",
        "let",
        "var",
        "import",
        "from",
        "as",
        "if",
        "else",
        "elif",
        "while",
        "for",
        "try",
        "except",
        "finally",
        "with",
        "match",
        "case",
        "return",
        "raise",
        "yield",
        "break",
        "continue",
        "async",
        "static",
        "in",
        "is",
        "not",
    ):
        return "keyword"
    elif tok.type == NAME:
        return "variable"
    elif tok.type == OP:
        return "operator"
    elif tok.type == STRING:
        return "string"
    elif tok.type == COMMENT:
        return "comment"
    elif tok.type == NUMBER:
        return "number"
    elif tok.type in (FSTRING_START, FSTRING_MIDDLE, FSTRING_END):
        return "string"
    else:
        return "operator"


class TokenModifier(enum.IntFlag):
    declaration = enum.auto()  # For declarations of symbols.
    definition = (
        enum.auto()
    )  # For definitions of symbols, for example, in header files.
    readonly = enum.auto()  # For readonly variables and member fields (constants).
    static = enum.auto()  # For class members (static members).
    deprecated = enum.auto()  # For symbols that should no longer be used.
    abstract = enum.auto()  # For types and member functions that are abstract.
    async_ = enum.auto()  # For functions that are marked async.
    modification = (
        enum.auto()
    )  # For variable references where the variable is assigned to.
    documentation = enum.auto()  # For occurrences of symbols in documentation.
    defaultLibrary = enum.auto()  # For symbols that are part of the standard library.


def semantic_legend() -> types.SemanticTokensLegend:
    return types.SemanticTokensLegend(
        token_types=TokenTypes,
        token_modifiers=[
            m.name if m.name != "async_" else "async"
            for m in TokenModifier
            if m.name is not None
        ],
    )


@attrs.define
class SemanticToken:
    line: int
    offset: int  # Column offset from the previous token
    text: str
    tok_type: str = ""
    tok_modifiers: list[TokenModifier] = attrs.field(factory=list[TokenModifier])


def semantic_token_to_encoded(token: SemanticToken) -> list[int]:
    return [
        token.line,
        token.offset,
        len(token.text),
        TokenTypesMap.get(token.tok_type, 0),
        reduce(operator.or_, token.tok_modifiers, 0),
    ]


def ast_tokens_to_semantic_tokens(
    node: ast.AST | None, tokens: list[TokenInfo], doc: TextDocument
) -> tuple[list[SemanticToken], list[int]]:
    # TODO temporal implementation. Consider nothing.
    semantic_tokens: list[SemanticToken] = []
    prev_line = 0
    prev_end_offset = 0
    for tok in tokens:
        # Offset encoding
        line = tok.start[0] - 1 - prev_line
        offset = tok.start[1]
        if line == 0:
            offset -= prev_end_offset
        debug_file_write_verbose(
            f"Semantic token encode Token: {tok}, Line: {line}, Offset: {offset} prev_line: {prev_line}, prev_end_offset: {prev_end_offset}"
        )
        prev_line = tok.end[0] - 1
        prev_end_offset = tok.start[1]
        semantic_tokens.append(
            SemanticToken(
                line=line, offset=offset, text=tok.string, tok_type=token_to_type(tok)
            )
        )
        debug_file_write_verbose(
            f"  Added Semantic Token: {semantic_tokens[-1]}, {semantic_token_to_encoded(semantic_tokens[-1])}"
        )
    encoded_tokens = [semantic_token_to_encoded(t) for t in semantic_tokens]
    return semantic_tokens, [i for token in encoded_tokens for i in token]
