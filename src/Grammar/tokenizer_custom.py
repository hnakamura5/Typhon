from typing import Callable, Iterator, Unpack, TypedDict, NamedTuple
from tokenize import TokenInfo, generate_tokens, OP, NAME
import tokenize
import token
from dataclasses import dataclass
from pegen.tokenizer import Tokenizer as PegenTokenizer
from typing import override
from .line_break import line_breakable_after, line_breakable_before
from .typhon_ast import get_postfix_operator_temp_name


# Combine sequencial 2 tokens (optionally without space between) into 1
class _CombineInfo(NamedTuple):
    first: tuple[int, str]  # type and string
    second: tuple[int, str]
    result_type: int
    # Whether is limited in the case no space are between tokens.
    only_without_space: bool


# Short alias
_C = _CombineInfo


# Combine list
_combine_seq2_tokens: list[_CombineInfo] = [
    _C((OP, "="), (OP, ">"), OP, True),
    _C((OP, "&"), (OP, "&"), OP, True),
    _C((OP, "|"), (OP, "|"), OP, True),
    # Optional operators.
    _C((OP, "?"), (OP, "."), OP, True),
    _C((OP, "?"), (OP, "?"), OP, True),
    _C((OP, "?"), (OP, "("), OP, True),
    _C((OP, "?"), (OP, "["), OP, True),
]
_combine_seq2_map: dict[tuple[int, str], list[_CombineInfo]] = {}
for info in _combine_seq2_tokens:
    _combine_seq2_map.setdefault(info.first, []).append(info)


def _is_token_possibly_combined_to_next(tok: TokenInfo) -> bool:
    return _combine_seq2_map.get((tok.type, tok.string)) is not None


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


def token_stream_factory(readline: Callable[[], str]) -> Iterator[TokenInfo]:
    yield from generate_tokens(readline)


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
class Tokenizer(PegenTokenizer):
    _forward_next: TokenInfo | None  # Next token to be processed in peek()
    _all_tokens: list[TokenInfo]  # All tokens including comments

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._all_tokens = []
        self._forward_next = None

    def skip_newlines(self):
        while self._index < len(self._tokens) and is_newline(self._tokens[self._index]):
            self._index += 1

    def _next(self) -> TokenInfo:
        if self._forward_next is not None:
            tok = self._forward_next
            self._forward_next = None
        else:
            while True:
                tok = next(self._tokengen)
                self._all_tokens.append(tok)
                if is_comment(tok):
                    continue
                if is_indent_dedent(tok):
                    continue
                if tok.type == token.ERRORTOKEN and tok.string.isspace():
                    continue
                break
        return tok

    @override
    def peek(self) -> tokenize.TokenInfo:
        """Return the next token *without* updating the index."""
        while self._index == len(self._tokens):
            tok = self._next()
            # Newline handling: skip continuous NEWLINE or NL tokens.
            if is_newline(tok):
                if not self._tokens:
                    # No previous token. Just skip.
                    continue
                # Forward the next token to check if the current newline.
                next_tok = self._next()
                while is_newline(next_tok):
                    next_tok = self._next()
                self._forward_next = next_tok
                if is_newline_to_skip(self._tokens[-1], tok, self._forward_next):
                    continue
                tok = TokenInfo(  # Canonicalize to NEWLINE
                    tokenize.NEWLINE,
                    "\n",
                    tok.start,
                    tok.end,
                    tok.line,
                )
            elif is_possible_postfix_operator(tok) and self._tokens:
                # Connected postfix `!` and `?` as special tokens.
                self._forward_next = next(self._tokengen)  # get exactly next token
                combined = _try_combine_token(tok, self._forward_next)
                if combined is not None:
                    # This will be combined to next token.
                    tok = combined
                    self._forward_next = None
                elif _is_unified(self._tokens[-1], tok):
                    # This is postfix operator without space.
                    tok = TokenInfo(  # Replace to a special token
                        tokenize.NAME,
                        get_postfix_operator_temp_name(tok.string),
                        tok.start,
                        tok.end,
                        tok.line,
                    )
            elif _is_token_possibly_combined_to_next(tok):
                # Combined tokens
                self._forward_next = next(self._tokengen)  # get exactly next token
                combined = _try_combine_token(tok, self._forward_next)
                if combined is not None:
                    tok = combined
                    self._forward_next = None
            # Normal token
            self._tokens.append(tok)
            if not self._path and tok.start[0] not in self._lines:
                self._lines[tok.start[0]] = tok.line
        return self._tokens[self._index]
