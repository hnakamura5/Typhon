from typing import NamedTuple
from tokenize import TokenInfo, OP, NAME
import tokenize
import token
import io
from pegen.tokenizer import Tokenizer as PegenTokenizer
from typing import override
from .line_break import line_breakable_after, line_breakable_before
from .typhon_ast import get_postfix_operator_temp_name
from ..Driver.debugging import debug_verbose_print
from .token_factory_custom import token_stream_factory, generate_tokens_ignore_error


# Combine sequencial 2 tokens (optionally without space between) into 1
class _CombineInfo(NamedTuple):
    first: tuple[int, str]  # type and string
    second: tuple[int, str]
    result_type: int
    # Whether is limited in the case no space are between tokens.
    only_without_space: bool


class _CombineTriInfo(NamedTuple):
    first: tuple[int, str]
    second: tuple[int, str]
    third: tuple[int, str]
    result_type: int
    only_without_space: bool


# Short alias
_C2 = _CombineInfo
_C3 = _CombineTriInfo


# Combine list
_combine_seq2_tokens: list[_CombineInfo] = [
    _C2((OP, "="), (OP, ">"), OP, True),
    _C2((OP, "&"), (OP, "&"), OP, True),
    _C2((OP, "|"), (OP, "|"), OP, True),
    _C2((OP, "|"), (OP, ">"), OP, True),
    # Optional operators.
    _C2((OP, "?"), (OP, "."), OP, True),
    _C2((OP, "?"), (OP, "?"), OP, True),
    _C2((OP, "?"), (OP, "("), OP, True),
    _C2((OP, "?"), (OP, "["), OP, True),
    # Record literal bracket.
    _C2((OP, "{"), (OP, "|"), OP, True),
    _C2((OP, "|"), (OP, "}"), OP, True),
]
_combine_seq3_tokens: list[_CombineTriInfo] = [
    _C3((OP, "?"), (OP, "|"), (OP, ">"), OP, True),
]
_combine_seq2_map: dict[tuple[int, str], list[_CombineInfo]] = {}
for info in _combine_seq2_tokens:
    _combine_seq2_map.setdefault(info.first, []).append(info)
_combine_seq3_map: dict[
    tuple[int, str], dict[tuple[int, str], list[_CombineTriInfo]]
] = {}
for info in _combine_seq3_tokens:
    _combine_seq3_map.setdefault(info.first, {}).setdefault(info.second, []).append(
        info
    )


def _is_unified(prev: TokenInfo, tok: TokenInfo) -> bool:
    return prev.end == tok.start and prev.line == tok.line


def _try_get_combine_info(prev: TokenInfo, tok: TokenInfo) -> _CombineInfo | None:
    infos = _combine_seq2_map.get((prev.type, prev.string))
    if infos is None:
        return None
    for info in infos:
        if (
            tok.type == info.second[0]
            and tok.string == info.second[1]
            and (not info.only_without_space or _is_unified(prev, tok))
        ):
            return info
    return None


def _try_combine_token(prev: TokenInfo, tok: TokenInfo) -> TokenInfo | None:
    info = _try_get_combine_info(prev, tok)
    if info is None:
        return None
    # Combine into one token
    return TokenInfo(
        info.result_type,
        prev.string + tok.string,
        prev.start,
        tok.end,
        prev.line,
    )


def _try_get_tri_combine_info(
    first: TokenInfo, second: TokenInfo, third: TokenInfo
) -> _CombineTriInfo | None:
    second_map = _combine_seq3_map.get((first.type, first.string))
    if second_map is None:
        return None
    infos = second_map.get((second.type, second.string))
    if infos is None:
        return None
    for info in infos:
        if (
            third.type == info.third[0]
            and third.string == info.third[1]
            and (
                not info.only_without_space
                or (_is_unified(first, second) and _is_unified(second, third))
            )
        ):
            return info
    return None


def _try_combine_tri_token(
    first: TokenInfo, second: TokenInfo, third: TokenInfo
) -> TokenInfo | None:
    info = _try_get_tri_combine_info(first, second, third)
    if info is None:
        return None
    # Combine into one token
    return TokenInfo(
        info.result_type,
        first.string + second.string + third.string,
        first.start,
        third.end,
        first.line,
    )


def is_newline(tok: TokenInfo) -> bool:
    return tok.type in (token.NEWLINE, token.NL)


def is_newline_to_skip(
    prev_tok: TokenInfo, tok: TokenInfo, next_tok: TokenInfo
) -> bool:
    if not is_newline(tok):
        return False
    if is_newline(prev_tok):
        # Skip continuous NEWLINE or NL
        return True
    if line_breakable_after(prev_tok):
        return True
    if line_breakable_before(next_tok):
        return True
    return False


def is_comment(tok: TokenInfo) -> bool:
    return tok.type == tokenize.COMMENT or tok.type == tokenize.TYPE_COMMENT


def is_indent_dedent(tok: TokenInfo) -> bool:
    return tok.type in (tokenize.INDENT, tokenize.DEDENT)


def is_possible_postfix_operator(tok: TokenInfo) -> bool:
    return tok.type == OP and tok.string in ("!", "?")


# Custom Tokenizer to override peek() not to skip always continuous NEWLINE and NL tokens.
class TokenizerCustom(PegenTokenizer):
    _forward_next: list[TokenInfo]  # Next token to be processed in peek()
    _all_tokens: list[TokenInfo]  # All tokens including comments
    _end_tok: TokenInfo | None  # Whether reached the end of token stream

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._all_tokens = []
        self._forward_next = []
        self._end_tok = None

    def _is_token_to_skip(self, tok: TokenInfo) -> bool:
        return (
            is_comment(tok)
            or is_indent_dedent(tok)
            or (tok.type == token.ERRORTOKEN and tok.string.isspace())
        )

    def _exact_next(self) -> TokenInfo:
        if self._end_tok is not None:  # Repeat end token if already reached the end
            return self._end_tok
        while True:
            tok = next(self._tokengen)
            if self._is_token_to_skip(tok):
                self._all_tokens.append(tok)
                continue
            if tok.type == token.ENDMARKER:
                self._end_tok = tok
                return tok
            return tok

    def _next(self) -> TokenInfo:
        if self._forward_next:
            return self._forward_next.pop(0)
        else:
            return self._exact_next()

    def _add_forward_next(self, tok: TokenInfo) -> None:
        self._forward_next.append(tok)

    def _peek_forward(self, num: int) -> TokenInfo:
        while len(self._forward_next) < num:
            next_tok = self._exact_next()
            self._add_forward_next(next_tok)
        return self._forward_next[num - 1]

    def _commit_token(self, tok: TokenInfo) -> None:
        self._tokens.append(tok)
        self._all_tokens.append(tok)
        if not self._path and tok.start[0] not in self._lines:
            self._lines[tok.start[0]] = tok.line

    def _peek_on_newline(self, tok: TokenInfo) -> list[TokenInfo]:
        if not self._tokens:
            # No previous token. Just skip.
            return []
        # Forward the next token to check if the current newline.
        next_tok = self._next()
        while is_newline(next_tok):
            next_tok = self._next()  # consume
        combined = self._peek_try_combine(next_tok)
        if combined is not None:
            next_tok = combined
        if is_newline_to_skip(self._tokens[-1], tok, next_tok):
            return [next_tok]  # Skip this newline
        return [
            TokenInfo(  # Canonicalize to NEWLINE
                tokenize.NEWLINE,
                "\n",
                tok.start,
                tok.end,
                tok.line,
            ),
            next_tok,
        ]

    def _peek_try_combine(self, tok: TokenInfo) -> TokenInfo | None:
        second = self._peek_forward(1)
        third = self._peek_forward(2)
        combined3 = _try_combine_tri_token(tok, second, third)
        if combined3 is not None:
            self._next()  # consume second token
            self._next()  # consume third token
            return combined3
        combined2 = _try_combine_token(tok, second)
        if combined2 is not None:
            # This will be combined to next token.
            self._next()  # consume second token
            return combined2
        return None

    def _postfix_operator_next_guard(self, tok: TokenInfo) -> bool:
        if tok.string == "!":
            second = self._peek_forward(1)
            if second.type == NAME and _is_unified(tok, second):
                # This is conversion inside f-string
                return False
        return True

    @override
    def peek(self) -> tokenize.TokenInfo:
        """Return the next token *without* updating the index."""
        while self._index >= len(self._tokens):
            tok = self._next()
            # Newline handling: skip continuous NEWLINE or NL tokens.
            if is_newline(tok):
                result = self._peek_on_newline(tok)
                if result:
                    for r in result:
                        self._commit_token(r)
                continue
            # Try to Combine tokens. Prioritize combine rather than postfix operator.
            combined = self._peek_try_combine(tok)
            if combined is not None:
                self._commit_token(combined)
                continue
            if (
                is_possible_postfix_operator(tok)
                and self._postfix_operator_next_guard(tok)
                and self._tokens
                and _is_unified(self._tokens[-1], tok)
            ):
                # This is postfix operator.
                self._commit_token(
                    TokenInfo(  # Replace to a special token
                        tokenize.NAME,
                        get_postfix_operator_temp_name(tok.string),
                        tok.start,
                        tok.end,
                        tok.line,
                    )
                )
                continue
            self._commit_token(tok)
        return self._tokens[self._index]

    def read_all_tokens(self) -> list[TokenInfo]:
        """Return all tokens including comments."""
        # Force to consume all tokens
        debug_verbose_print("Reading all tokens for tokenizer.")
        while tok := self.getnext():
            debug_verbose_print(f"  Token: {tok}")
            if tok.type == token.ENDMARKER:
                break
        debug_verbose_print("Finished reading all tokens.")
        self.reset(0)
        return sorted(self._all_tokens, key=lambda t: t.start)


def tokenizer_for_file(file_path: str) -> TokenizerCustom:
    """Tokenize the specified file."""
    with open(file_path) as f:
        tok_stream = token_stream_factory(f.readline)
        tokenizer = TokenizerCustom(tok_stream, path=file_path)
    return tokenizer


def tokenizer_for_string(source: str) -> TokenizerCustom:
    """Tokenize the specified string."""
    tok_stream = token_stream_factory(io.StringIO(source).readline)
    tokenizer = TokenizerCustom(tok_stream)
    return tokenizer


def show_token(
    source: str, show_typhon_token: bool = True, show_python_token: bool = True
):
    if show_python_token:
        print("Tokens of Python tokenizer:")
        for tok in generate_tokens_ignore_error(io.StringIO(source).readline):
            print(f"    {tok}")
    if show_typhon_token:
        print("Tokens of Typhon Token Factory:")
        tok_stream = token_stream_factory(io.StringIO(source).readline)
        for tok in tok_stream:
            print(f"    {tok}")
    print("Tokens of Typhon Custom tokenizer:")
    tok_stream = token_stream_factory(io.StringIO(source).readline)
    tokenizer = TokenizerCustom(tok_stream, verbose=True)
    tokens = tokenizer.read_all_tokens()
    for tok in tokens:
        print(f"    {tok}")
