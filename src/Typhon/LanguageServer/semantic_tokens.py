import attrs
import enum
import operator
import ast
from functools import reduce
from lsprotocol import types

from ..Grammar.typhon_ast import is_internal_name
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


def encode_semantic_tokens(
    tokens: list[SemanticToken],
) -> types.SemanticTokens:
    encoded_tokens: list[list[int]] = []
    prev_line = 0
    prev_start_col = 0
    for token in tokens:
        delta_line = token.line - prev_line
        if delta_line == 0:
            delta_offset = token.start_col - prev_start_col
        else:
            delta_offset = token.start_col
            prev_start_col = 0
        encoded_tokens.append(
            [
                delta_line,
                delta_offset,
                token.length,
                TOKEN_TYPES_MAP.get(token.tok_type, 0),
                reduce(operator.or_, token.tok_modifiers, 0),
            ]
        )
        prev_line = token.line
        prev_start_col = token.start_col
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
        i += 5
        line += delta_line
        if delta_line == 0:
            offset = offset + delta_offset
        else:
            offset = delta_offset
        debug_file_write_verbose(
            lambda: (
                f"Decoding semantic token: delta_line={delta_line}, delta_offset={delta_offset}, length={length}, tok_type_index={tok_type_index}, tok_modifiers_bitmask={tok_modifiers_bitmask}, line={line}, offset={offset}"
            )
        )
        tok_type = client_legend.get(tok_type_index, TOKEN_TYPES[tok_type_index])
        tok_modifiers: list[TokenModifier] = []
        for mod in TokenModifier:
            if tok_modifiers_bitmask & mod:
                tok_modifiers.append(mod)
        decoded_tokens.append(
            SemanticToken(
                line=line,
                offset=delta_offset,
                length=length,
                start_col=offset,
                end_col=offset + length,
                text="",  # Text is not needed for mapping
                tok_type=tok_type,
                tok_modifiers=tok_modifiers,
            )
        )
        debug_file_write_verbose(
            lambda: f"  Decoded Semantic Token: {decoded_tokens[-1]}"
        )
    return decoded_tokens


def map_semantic_tokens(
    tokens: types.SemanticTokens,
    mapping: MatchBasedSourceMap,
    client_legend: dict[int, str],
) -> types.SemanticTokens:
    # First decode the tokens into SemanticTokens
    decoded_tokens = decode_semantic_tokens(tokens, client_legend)
    debug_file_write_verbose(lambda: f"Decoded tokens for mapping: {decoded_tokens}")
    # Map each token position
    mapped_tokens: list[SemanticToken] = []
    for token in decoded_tokens:
        token_range = Range(
            start=Pos(line=token.line, column=token.start_col),
            end=Pos(line=token.line, column=token.end_col),
        )
        # For debugging to see text.
        token.text = Range.of_string(token_range, mapping.unparsed_code)
        debug_file_write_verbose(
            lambda: f"Mapping token from decoded: {token} at range: {token_range}"
        )
        if mapped_node := mapping.unparsed_range_to_origin_node(
            token_range,
            ast.Name,
            lambda n: isinstance(n, ast.Name) and not is_internal_name(n),
        ):
            if isinstance(mapped_node, ast.Name):
                if mapped_range := Range.from_ast_node(mapped_node):
                    line = mapped_range.start.line
                    debug_file_write_verbose(
                        lambda: (
                            f"Mapping token to node with range OK: {token}\n --> {ast.dump(mapped_node)} [{mapped_node.__dict__}](internal={is_internal_name(mapped_node)})@{mapped_range}"
                        )
                    )
                    debug_file_write_verbose(
                        lambda: (
                            f"  line: {line}, start_col: {mapped_range.start.column}, end_col: {mapped_range.end.column}"
                        )
                    )
                    if mapped_range.is_empty():
                        debug_file_write_verbose(
                            lambda: (
                                f"  Skipping token mapping for empty range: {token} mapped to {ast.dump(mapped_node)} at {mapped_range}"
                            )
                        )
                        continue
                    mapped_tokens.append(
                        SemanticToken(
                            line=line,
                            offset=-1,
                            length=mapped_range.end.column - mapped_range.start.column,
                            start_col=mapped_range.start.column,
                            end_col=mapped_range.end.column,
                            text=Range.of_string(mapped_range, mapping.source_code),
                            tok_type=token.tok_type,  # TODO: map this
                            tok_modifiers=token.tok_modifiers,
                        )
                    )
                    continue
    sorted_tokens = list(sorted(mapped_tokens, key=lambda t: (t.line, t.start_col)))
    # Calculate offsets
    prev_line = 0
    prev_end_col = 0
    for token in sorted_tokens:
        if token.line == prev_line:
            token.offset = token.start_col - prev_end_col
        else:
            token.offset = token.start_col
            prev_line = token.line
        prev_end_col = token.end_col
    debug_file_write_verbose(
        lambda: f"Mapped semantic tokens(before encode): {sorted_tokens}"
    )
    return encode_semantic_tokens(sorted_tokens)


# Mainly for testing
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


# Mainly for testing
def semantic_token_capabilities() -> types.ClientCapabilities:
    return types.ClientCapabilities(
        text_document=types.TextDocumentClientCapabilities(
            semantic_tokens=types.SemanticTokensClientCapabilities(
                requests=types.ClientSemanticTokensRequestOptions(
                    range=True,
                    # full=True,
                    full=types.ClientSemanticTokensRequestFullDelta(delta=True),
                ),
                token_types=TOKEN_TYPES,
                token_modifiers=[
                    m.name if m.name != "async_" else "async"
                    for m in TokenModifier
                    if m.name is not None
                ],
                formats=(types.TokenFormat.Relative,),
                dynamic_registration=True,
                overlapping_token_support=False,
                multiline_token_support=False,
                server_cancel_support=True,
                augments_syntax_tokens=True,
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
