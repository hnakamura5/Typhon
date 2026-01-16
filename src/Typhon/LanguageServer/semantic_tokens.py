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
from lsprotocol import types
from pygls.workspace import TextDocument
from ..Grammar.tokenizer_custom import TokenInfo
from ..Driver.debugging import debug_file_write_verbose
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ..SourceMap.datatype import Range, Pos

# https://code.visualstudio.com/api/language-extensions/semantic-highlight-guide
TOKEN_TYPES = [
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
    # Extensions beyond the standard LSP semantic token types:
    "selfParameter",  # For the 'self' or equivalent parameter in methods. Pyright specific.
    "clsParameter",  # For the 'cls' or equivalent parameter in class methods. Pyright specific.
]
TOKEN_TYPES_MAP = {t: i for i, t in enumerate(TOKEN_TYPES)}


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


TokenModifierMap: dict[str, TokenModifier] = {
    (e.name if e.name != "async_" else "async") or "": e for e in TokenModifier
}


def semantic_legend() -> types.SemanticTokensLegend:
    return types.SemanticTokensLegend(
        token_types=TOKEN_TYPES,
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
    length: int  # Length is derived from text
    start_col: int
    end_col: int
    text: str
    tok_type: str = ""
    tok_modifiers: list[TokenModifier] = attrs.field(factory=list[TokenModifier])


def semantic_token_to_encoded(token: SemanticToken) -> list[int]:
    return [
        token.line,
        token.offset,
        token.length,
        TOKEN_TYPES_MAP.get(token.tok_type, 0),
        reduce(operator.or_, token.tok_modifiers, 0),
    ]


def encode_semantic_tokens(
    tokens: list[SemanticToken],
) -> types.SemanticTokens:
    encoded_tokens = [semantic_token_to_encoded(t) for t in tokens]
    return types.SemanticTokens(data=[i for token in encoded_tokens for i in token])


def decode_semantic_tokens(
    tokens: types.SemanticTokens, client_legend: dict[int, str]
) -> list[SemanticToken]:
    decoded_tokens: list[SemanticToken] = []
    i = 0
    line = 0
    offset = 0
    while i < len(tokens.data):
        delta_line = tokens.data[i]
        delta_offset = tokens.data[i + 1]
        length = tokens.data[i + 2]
        tok_type_index = tokens.data[i + 3]
        tok_modifiers_bitmask = tokens.data[i + 4]
        line += delta_line
        if delta_line == 0:
            offset += delta_offset
        else:
            offset = delta_offset
        tok_type = client_legend.get(tok_type_index, TOKEN_TYPES[tok_type_index])
        tok_modifiers: list[TokenModifier] = []
        for mod in TokenModifier:
            if tok_modifiers_bitmask & mod:
                tok_modifiers.append(mod)
        decoded_tokens.append(
            SemanticToken(
                line=line,
                offset=offset,
                length=length,
                start_col=offset,
                end_col=offset + length,
                text="",  # Text is not needed for mapping
                tok_type=tok_type,
                tok_modifiers=tok_modifiers,
            )
        )
        i += 5
    return decoded_tokens


def map_semantic_tokens(
    tokens: types.SemanticTokens,
    mapping: MatchBasedSourceMap,
    client_legend: dict[int, str],
) -> types.SemanticTokens:
    # First decode the tokens into SemanticTokens
    decoded_tokens = decode_semantic_tokens(tokens, client_legend)
    # Map each token position
    mapped_tokens: list[SemanticToken] = []
    current_line = 0
    current_offset = 0
    for token in decoded_tokens:
        if token.line == current_line:
            current_offset += token.offset
        else:
            current_line = token.line
            current_offset = 0
        token_range = Range(
            start=Pos(line=current_line, column=current_offset),
            end=Pos(line=current_line, column=current_offset + token.length),
        )
        mapped_range = mapping.unparsed_range_to_origin(token_range)
        if mapped_range is not None:
            line = mapped_range.start.line
            if mapped_tokens and line == mapped_tokens[-1].line:
                # Calculate offset from the previous token in the same line.
                offset = mapped_range.start.column - mapped_tokens[-1].end_col
            else:
                # First token overall, or first token on this line.
                offset = mapped_range.start.column
            mapped_tokens.append(
                SemanticToken(
                    line=line,
                    offset=offset,
                    length=token.length,
                    start_col=mapped_range.start.column,
                    end_col=mapped_range.end.column,
                    text=token.text,
                    tok_type=token.tok_type,
                    tok_modifiers=token.tok_modifiers,
                )
            )
        else:
            debug_file_write_verbose(f"Mapping failed for token: {token}")
    return encode_semantic_tokens(mapped_tokens)


def get_semantic_token_text(token: SemanticToken, lines: list[str]) -> str:
    """Retrieve the text of a semantic token from the document."""
    if token.line < 0 or token.line >= len(lines):
        return ""
    line_text = lines[token.line]
    if token.start_col < 0 or token.end_col > len(line_text):
        return ""
    return line_text[token.start_col : token.end_col]


def semantic_legends_of_initialized_response(
    legend: types.SemanticTokensLegend,
) -> dict[int, str]:
    return {i: tok_type for i, tok_type in enumerate(legend.token_types)}


# Fallback case that semantic tokens are not provided by the language server.
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


# Fallback implementation that makes semantic tokens from tokens only.
def ast_tokens_to_semantic_tokens(
    node: ast.AST | None, tokens: list[TokenInfo], doc: TextDocument
) -> tuple[list[SemanticToken], list[int]]:
    semantic_tokens: list[SemanticToken] = []
    prev_line = 0
    prev_end_offset = 0
    for tok in tokens:
        # Offset encoding
        line = tok.start[0] - 1 - prev_line
        offset = tok.start[1]
        if line == 0:
            offset -= prev_end_offset  # Offset is from previous token in the same line
        debug_file_write_verbose(
            f"Semantic token encode Token: {tok}, Line: {line}, Offset: {offset} prev_line: {prev_line}, prev_end_offset: {prev_end_offset}"
        )
        prev_line = tok.end[0] - 1
        prev_end_offset = tok.start[1]
        semantic_tokens.append(
            SemanticToken(
                line=line,
                offset=offset,
                start_col=tok.start[1],
                end_col=tok.end[1],
                length=len(tok.string),
                text=tok.string,
                tok_type=token_to_type(tok),
            )
        )
        debug_file_write_verbose(
            f"  Added Semantic Token: {semantic_tokens[-1]}, {semantic_token_to_encoded(semantic_tokens[-1])}"
        )
    encoded_tokens = [semantic_token_to_encoded(t) for t in semantic_tokens]
    return semantic_tokens, [i for token in encoded_tokens for i in token]


# Mainly for testing
def semantic_token_capabilities() -> types.ClientCapabilities:
    return types.ClientCapabilities(
        text_document=types.TextDocumentClientCapabilities(
            semantic_tokens=types.SemanticTokensClientCapabilities(
                requests=types.ClientSemanticTokensRequestOptions(
                    range=True,
                    full=True,
                ),
                token_types=TOKEN_TYPES,
                token_modifiers=[
                    m.name if m.name != "async_" else "async"
                    for m in TokenModifier
                    if m.name is not None
                ],
                formats=[types.TokenFormat.Relative],
                dynamic_registration=True,
            )
        )
    )


# Pyrefly server currently not seems to return semantic token legend in capabilities.
# We use here a fixed legend from the source code of Pyrefly.

# pyrefly/lib/state/semantic_tokens.rs
#
# impl SemanticTokensLegends {
#     pub fn lsp_semantic_token_legends() -> SemanticTokensLegend {
#         SemanticTokensLegend {
#             token_types: vec![
#                 SemanticTokenType::NAMESPACE,
#                 SemanticTokenType::TYPE,
#                 SemanticTokenType::CLASS,
#                 SemanticTokenType::ENUM,
#                 SemanticTokenType::INTERFACE,
#                 SemanticTokenType::STRUCT,
#                 SemanticTokenType::TYPE_PARAMETER,
#                 SemanticTokenType::PARAMETER,
#                 SemanticTokenType::VARIABLE,
#                 SemanticTokenType::PROPERTY,
#                 SemanticTokenType::ENUM_MEMBER,
#                 SemanticTokenType::EVENT,
#                 SemanticTokenType::FUNCTION,
#                 SemanticTokenType::METHOD,
#                 SemanticTokenType::MACRO,
#                 SemanticTokenType::KEYWORD,
#                 SemanticTokenType::MODIFIER,
#                 SemanticTokenType::COMMENT,
#                 SemanticTokenType::STRING,
#                 SemanticTokenType::NUMBER,
#                 SemanticTokenType::REGEXP,
#                 SemanticTokenType::OPERATOR,
#                 SemanticTokenType::DECORATOR,
#             ],
#             token_modifiers: vec![
#                 SemanticTokenModifier::DECLARATION,
#                 SemanticTokenModifier::DEFINITION,
#                 SemanticTokenModifier::READONLY,
#                 SemanticTokenModifier::STATIC,
#                 SemanticTokenModifier::DEPRECATED,
#                 SemanticTokenModifier::ABSTRACT,
#                 SemanticTokenModifier::ASYNC,
#                 SemanticTokenModifier::MODIFICATION,
#                 SemanticTokenModifier::DOCUMENTATION,
#                 SemanticTokenModifier::DEFAULT_LIBRARY,
#             ],
#         }

PYREFLY_TOKEN_TYPES: list[str] = [
    "namespace",
    "type",
    "class",
    "enum",
    "interface",
    "struct",
    "typeParameter",
    "parameter",
    "variable",
    "property",
    "enumMember",
    "event",
    "function",
    "method",
    "macro",
    "keyword",
    "modifier",
    "comment",
    "string",
    "number",
    "regexp",
    "operator",
    "decorator",
]
PYREFLY_TOKEN_TYPES_MAP: dict[str, int] = {
    t: i for i, t in enumerate(PYREFLY_TOKEN_TYPES)
}


def pyrefly_semantic_legend() -> types.SemanticTokensLegend:
    return types.SemanticTokensLegend(
        token_types=PYREFLY_TOKEN_TYPES,
        token_modifiers=[
            m.name if m.name != "async_" else "async"
            for m in TokenModifier
            if m.name is not None
        ],
    )
