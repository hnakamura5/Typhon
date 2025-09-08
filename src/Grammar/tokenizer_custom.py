from typing import Callable, Iterator, Unpack, TypedDict
from tokenize import TokenInfo, generate_tokens, OP
import tokenize
from dataclasses import dataclass


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
