from typing import Callable, Iterator, Unpack, TypedDict
from tokenize import TokenInfo, generate_tokens, OP, NAME
import tokenize
import token
from dataclasses import dataclass
from pegen.tokenizer import Tokenizer as PegenTokenizer
from typing import override
from .line_break import line_breakable_after, line_breakable_before


# Combine sequencial 2 tokens (optionally without space between) into 1
@dataclass
class _CombineInfo:
    first: tuple[int, str]  # type and string
    second: tuple[int, str]
    result_type: int
    # Whether is limited in the case no space are between tokens.
    only_without_space: bool


# Combine list
_combine_seq2_tokens: list[_CombineInfo] = [
    _CombineInfo((OP, "="), (OP, ">"), OP, True),
    _CombineInfo((OP, "&"), (OP, "&"), OP, True),
    _CombineInfo((OP, "|"), (OP, "|"), OP, True),
]
_combine_seq2_map: dict[tuple[int, str], list[_CombineInfo]] = {}
for info in _combine_seq2_tokens:
    _combine_seq2_map.setdefault(info.first, []).append(info)


def _is_token_combine_first(tok: TokenInfo) -> bool:
    return _combine_seq2_map.get((tok.type, tok.string)) is not None


def _try_combine_token(prev: TokenInfo, tok: TokenInfo) -> TokenInfo | None:
    infos = _combine_seq2_map.get((prev.type, prev.string))
    if infos is None:
        return None
    for info in infos:
        if (
            tok.type == info.second[0]
            and tok.string == info.second[1]
            and (not info.only_without_space or prev.end == tok.start)
        ):
            # Combine into one token
            return TokenInfo(
                info.result_type,
                prev.string + tok.string,
                prev.start,
                tok.end,
                prev.line,
            )
    return None


def token_stream_factory(readline: Callable[[], str]) -> Iterator[TokenInfo]:
    prev: TokenInfo | None = None
    for tok in generate_tokens(readline):
        if prev is not None:
            result = _try_combine_token(prev, tok)
            if result is not None:
                prev = None
                yield result
                continue
            else:
                result = prev
                prev = None
                yield result
                # Fall through. No continue
        if _is_token_combine_first(tok):
            prev = tok
            continue
        yield tok
    if prev:
        yield prev
    return


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
            # Normal token
            self._tokens.append(tok)
            if not self._path and tok.start[0] not in self._lines:
                self._lines[tok.start[0]] = tok.line
        return self._tokens[self._index]
