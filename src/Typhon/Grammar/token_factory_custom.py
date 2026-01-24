import sys
import token
from typing import Callable, Iterator, Literal
from tokenize import TokenInfo, generate_tokens
import tokenize
import re
from dataclasses import dataclass
from ..Driver.debugging import debug_print, debug_verbose_print
from enum import Enum, auto


def generate_tokens_ignore_error(readline: Callable[[], str]) -> Iterator[TokenInfo]:
    # yield from _generate_tokens_parso(readline)
    try:
        for tok in generate_tokens(readline):
            yield tok
    except tokenize.TokenError as e:
        # Ignore the error on EOF in multiline.
        message: str
        lineno: int
        offset: int
        message, (lineno, offset) = e.args
        pos = (lineno, offset)
        print(f"Tokenization error ignored at {pos}: {e}")
        yield TokenInfo(token.ENDMARKER, "", pos, pos, "")


def _regularize_token_type(token_type: int) -> int:
    """Convert token type to a regularized form for Typhon.

    NL -> NEWLINE
    """
    if token_type == tokenize.NL:
        return tokenize.NEWLINE
    return token_type


@dataclass
class _BlockComment:
    start_line: int
    start_col: int
    end_line: int
    end_col: int
    comment: str
    lines: str

    def __hash__(self) -> int:
        return hash(
            (
                self.start_line,
                self.start_col,
            )
        )


class _StrKind(Enum):
    SINGLE_QUOTE = auto()
    DOUBLE_QUOTE = auto()
    SINGLE_QUOTE_DOCSTRING = auto()
    DOUBLE_QUOTE_DOCSTRING = auto()
    FSTRING_START = auto()


@dataclass
class _StrPrefix:
    is_raw: bool
    is_fstring: bool


@dataclass
class _Str:
    prefix: _StrPrefix
    kind: _StrKind

    def is_raw(self) -> bool:
        return self.prefix.is_raw

    def is_fstring(self) -> bool:
        return self.prefix.is_fstring


# Line parser that handles block comments and strings.
# This is ONLY for implementing block comments that can span multiple lines.
class _LineParser:
    def __init__(self, readline: Callable[[], str]) -> None:
        self.readline = readline
        self.line = ""
        self.result_line = ""
        self.line_num = 0
        self._column = 0
        # Is inside string. Note this is false in f-string expression parts unless not in the string in the expression.
        self.in_string = False
        self.in_comment = False

        # For f-string interpolation handling.
        self.interpolation_stack: list[Literal["{"]] = []
        # String context stack for nested strings (only in f-string expressions).
        self.str_context: list[_Str] = []
        # To count the brackets in f-string interpolation.
        self.bracket_stack_in_interpolation: list[str] = []
        self.block_comment_begin_stack: list[_BlockComment] = []
        self.outermost_block_comments: list[_BlockComment] = []
        self.line_head_spaces: list[str] = []

    def _next_char(self) -> str | None:
        if self._column >= len(self.line):
            return None
        ch = self.line[self._column]
        self._column += 1
        return ch

    # Current column of character taken last time.
    def _get_char_column(self) -> int:
        return self._column - 1

    def _peek_char(self, offset: int = 0) -> str | None:
        if self._column + offset >= len(self.line):
            return None
        return self.line[self._column + offset]

    def _passed(self) -> str:
        return self.line[: self._column]

    def _pop_index(self, bracket: str) -> int | None:
        for idx in range(len(self.bracket_stack_in_interpolation) - 1, -1, -1):
            if self.bracket_stack_in_interpolation[idx] == bracket:
                return idx
        return None

    def _commit(self, ch: str | None) -> None:
        if ch is not None:
            if self.block_comment_begin_stack:
                # Inside block comment, do not commit to result line
                self.block_comment_begin_stack[0].comment += ch
            else:
                # Normal code
                self.result_line += ch

    def _handle_bracket(self, ch: str) -> None:
        if self.interpolation_stack:
            if ch == "{":
                self.bracket_stack_in_interpolation.append("{")
            elif ch == "[":
                self.bracket_stack_in_interpolation.append("[")
            elif ch == "(":
                self.bracket_stack_in_interpolation.append("(")
            # Unclosed brackets to be ignored.
            elif ch == "}":
                if (pop_idx := self._pop_index("{")) is not None:
                    self.bracket_stack_in_interpolation = (
                        self.bracket_stack_in_interpolation[:pop_idx]
                    )
                    if not self.bracket_stack_in_interpolation:
                        # All brackets closed, end of interpolation
                        self.interpolation_stack.pop()
                        self.in_string = True
            elif ch == "]":
                if (pop_idx := self._pop_index("[")) is not None:
                    self.bracket_stack_in_interpolation = (
                        self.bracket_stack_in_interpolation[:pop_idx]
                    )
            elif ch == ")":
                if (pop_idx := self._pop_index("(")) is not None:
                    self.bracket_stack_in_interpolation = (
                        self.bracket_stack_in_interpolation[:pop_idx]
                    )
        elif self.str_context and self.str_context[-1].is_fstring() and ch == "{":
            # Start of f-string interpolation
            debug_verbose_print(
                f"Starting f-string interpolation at column={self._get_char_column()}"
            )
            self.interpolation_stack.append("{")
            self.bracket_stack_in_interpolation.append("{")
            self.in_string = False

    def _get_str_prefix(self) -> _StrPrefix:
        is_raw = False
        is_fstring = False
        for back_ch in reversed(self._passed()[:-1]):
            if back_ch in {"r", "R"}:
                is_raw = True
            elif back_ch in {"f", "F", "t", "T"}:
                is_fstring = True
            elif back_ch in {"b", "B"}:
                continue
            else:
                break
        debug_verbose_print(
            f"Determined string prefix {list(reversed(self._passed()[:-1]))[0:2]} is_raw={is_raw} is_fstring={is_fstring} at column={self._get_char_column()}"
        )
        return _StrPrefix(is_raw=is_raw, is_fstring=is_fstring)

    def _handle_string_delim(self, ch: str) -> None:
        if self.in_string:
            # Possible string end
            assert self.str_context, "String context stack should not be empty"
            prefix = self.str_context[-1].prefix
            kind = self.str_context[-1].kind
            debug_verbose_print(
                f"Handling string may end delim: {ch!r} kind={kind} prefix={prefix} column={self._get_char_column()}"
            )
            if kind == _StrKind.SINGLE_QUOTE and ch == "'":
                self.str_context.pop()
                self.in_string = False
                return
            elif kind == _StrKind.DOUBLE_QUOTE and ch == '"':
                self.str_context.pop()
                self.in_string = False
                return
            elif kind == _StrKind.SINGLE_QUOTE_DOCSTRING and ch == "'":
                next_ch = self._peek_char()
                third_ch = self._peek_char(1)
                if next_ch == "'" and third_ch == "'":
                    self._commit(self._next_char())  # consume
                    self._commit(self._next_char())  # consume
                    self.str_context.pop()
                    self.in_string = False
                    return
            elif kind == _StrKind.DOUBLE_QUOTE_DOCSTRING and ch == '"':
                next_ch = self._peek_char()
                third_ch = self._peek_char(1)
                if next_ch == '"' and third_ch == '"':
                    self._commit(self._next_char())  # consume
                    self._commit(self._next_char())  # consume
                    self.str_context.pop()
                    self.in_string = False
                    return
        else:
            # String start
            prefix = self._get_str_prefix()
            next_ch = self._peek_char()
            debug_verbose_print(
                f"Handling string start delim: {ch!r} next_ch={next_ch!r} prefix={prefix} passed={self._passed()} column={self._get_char_column()}"
            )
            self.in_string = True
            if next_ch == ch:
                # Maybe triple quote
                third_ch = self._peek_char(1)
                if third_ch == ch:
                    self._commit(self._next_char())  # consume
                    self._commit(self._next_char())  # consume
                    # Docstring
                    if ch == "'":
                        self.str_context.append(
                            _Str(prefix, _StrKind.SINGLE_QUOTE_DOCSTRING)
                        )
                    else:
                        self.str_context.append(
                            _Str(prefix, _StrKind.DOUBLE_QUOTE_DOCSTRING)
                        )
                    return
            if ch == "'":
                self.str_context.append(_Str(prefix, _StrKind.SINGLE_QUOTE))
            else:
                self.str_context.append(_Str(prefix, _StrKind.DOUBLE_QUOTE))
            return

    def _handle_comment(self) -> None:
        first_sharp_column = self._get_char_column()
        debug_verbose_print(
            f"Handling comment at line {self.line_num} col {first_sharp_column} in line: {self.line!r}"
        )
        # Block comment begin in front
        while self._peek_char() == "#":
            self._next_char()
        if self._peek_char() == "(":
            # Block comment begin
            # Consume the '('
            self._next_char()
            # All # and (
            comment_starter = self.line[
                first_sharp_column : self._get_char_column() + 1
            ]
            debug_verbose_print(
                f"Block comment begin detected at col {first_sharp_column} in line comment_starter={comment_starter}: {self.line!r}"
            )
            self.block_comment_begin_stack.append(
                _BlockComment(
                    start_line=self.line_num,
                    start_col=first_sharp_column,
                    end_line=0,
                    end_col=0,
                    comment="",
                    lines=self.line,
                )
            )
            # Accumulate the begin part to the outermost block comment
            self.block_comment_begin_stack[0].comment += comment_starter
        elif not self.block_comment_begin_stack:
            # Normal comment line, skip to end
            self.result_line += self.line[first_sharp_column:]
            self._column = len(self.line)
        else:
            # Inside block comment, just commit the '#'
            self.block_comment_begin_stack[0].comment += self.line[
                first_sharp_column : self._get_char_column()
            ]

    def _handle_block_comment_end(self) -> None:
        if self.block_comment_begin_stack:
            while self._peek_char() == "#":
                self._commit(self._next_char())
            debug_verbose_print(
                f"Block comment end detected at col {self._column} in line: {self.line!r} "
            )
            if len(self.block_comment_begin_stack) == 1:
                block_comment = self.block_comment_begin_stack[-1]
                block_comment.end_line = self.line_num
                block_comment.end_col = self._column  # after the last '#'
                self.outermost_block_comments.append(block_comment)
                self.in_comment = False
                debug_verbose_print(
                    f"block comment from line {block_comment.start_line} col {block_comment.start_col} "
                    f"to line {block_comment.end_line} col {block_comment.end_col}"
                )
                self.result_line += " "  # Replace block comment with space
            # Pop the block comment begin
            self.block_comment_begin_stack.pop()

    def _cut_line_head_spaces(
        self, line: str, line_head_in_string_or_comment: bool
    ) -> str:
        if not line_head_in_string_or_comment:
            match = re.match(r"[ \t]*", line)
            if match:
                self.line_head_spaces.append(match.group(0))
                return line[match.end() :]
        self.line_head_spaces.append("")
        return line

    def _next_line(self) -> None:
        self.line = self.readline()
        self._column = 0
        self.line_num += 1

    # Parse the line and return true start/end of block comment.
    # block comment begin/end is ignored in string/docstring.
    # They are valid in f-string expressions.
    def parse_next_line(self) -> str:
        self._next_line()
        ch = ""
        line_head_in_string_or_comment = self.in_string or self.in_comment
        while True:
            ch = self._next_char()
            if ch is None:
                # End of line. Continue if block comment continues.
                if self.block_comment_begin_stack:
                    self._next_line()
                    continue
                # True end of line
                break
            if self.block_comment_begin_stack:
                # Inside block comment
                if ch == "#":
                    self._handle_comment()
                if ch == ")" and self._peek_char() == "#":
                    self._commit(ch)
                    self._handle_block_comment_end()
                else:
                    self._commit(ch)
            elif self.in_string:  # Inside string
                self._commit(ch)
                if ch in {"'", '"'}:
                    self._handle_string_delim(ch)
                elif ch == "\\" and not self.str_context[-1].is_raw():
                    self._commit(self._next_char())  # consume escape character
                elif (
                    ch == "{" and self.str_context and self.str_context[-1].is_fstring()
                ):
                    # Possible interpolation start
                    self._handle_bracket(ch)
            else:  # Normal code
                if ch == "#":
                    self._handle_comment()
                else:
                    self._commit(ch)
                    if ch in {"'", '"'}:
                        self._handle_string_delim(ch)
                    elif ch in {"{", "}", "(", ")", "[", "]"}:
                        self._handle_bracket(ch)
        result = self._cut_line_head_spaces(
            self.result_line, line_head_in_string_or_comment
        )
        self.result_line = ""
        debug_verbose_print(f"Parsed line {self.line_num} result: {result!r}")
        return result


def _generate_and_postprocess_tokens(
    readline: Callable[[], str],  # After block comment is processed.
    unconsumed_block_comment: list[_BlockComment],
    head_space_lines: list[str],
) -> Iterator[TokenInfo]:
    """Generate tokens from readline, handling head space and  block comments."""
    line_offset_already_consumed = 0
    block_comment_already_output: set[_BlockComment] = set()
    # Adjust token positions from generated tokens, and mix in block comment tokens.
    for tok in generate_tokens_ignore_error(readline):
        debug_verbose_print(
            f"Generated token: {tok.string!r} type={tok.type} start={tok.start} end={tok.end}"
        )
        # Retrieve the line head spaces for this line.
        start = (
            tok.start[0],
            tok.start[1] + len(head_space_lines[tok.start[0] - 1]),
        )
        end = (
            tok.end[0],
            tok.end[1] + len(head_space_lines[tok.end[0] - 1]),
        )
        # Gather unconsumed block comments before this token.
        tok_start_line, tok_start_col = start
        while (
            unconsumed_block_comment
            and (block_comment := unconsumed_block_comment[0])
            and (
                block_comment.end_line < tok_start_line
                or (
                    block_comment.end_line == tok_start_line
                    and block_comment.end_col <= tok_start_col
                )
            )
        ):
            debug_verbose_print(
                f"pop block comment token: {block_comment.comment!r} start=({block_comment.start_line}, {block_comment.start_col}) end=({block_comment.end_line}, {block_comment.end_col})"
            )
            # Pop away comments that will never affect to remaining tokens.
            # Remove already passed block comments.
            line_offset_already_consumed += (
                block_comment.end_line - block_comment.start_line
            )
            unconsumed_block_comment.pop(0)
        # Adjust the token position if there are block comments before this token.
        adjusted_start_line, adjusted_start_col = start
        adjusted_end_line, adjusted_end_col = end
        adjusted_start_line += line_offset_already_consumed
        adjusted_end_line += line_offset_already_consumed
        for block_comment in unconsumed_block_comment:
            if (block_comment.start_line, block_comment.start_col) >= (
                adjusted_start_line,
                adjusted_start_col,
            ):
                break
            # This block comment is before the token, yield here first.
            if block_comment not in block_comment_already_output:
                block_comment_already_output.add(block_comment)
                debug_verbose_print(
                    f"Yielding block comment at start=({block_comment.start_line}, {block_comment.start_col}) "
                    f"end=({block_comment.end_line}, {block_comment.end_col})"
                )
                yield TokenInfo(
                    type=tokenize.COMMENT,
                    string=block_comment.comment,
                    start=(block_comment.start_line, block_comment.start_col),
                    end=(block_comment.end_line, block_comment.end_col),
                    line=block_comment.lines,
                )
            # The length of the last line of block comment.
            block_comment_last_line_len = (
                block_comment.end_col - block_comment.start_col
                if block_comment.end_line == block_comment.start_line
                else block_comment.end_col
            )
            # Adjust start position
            debug_verbose_print(
                f"Adjusting token start {tok.string!r} adjusted_start: {(adjusted_start_line, adjusted_start_col)} adjusted_end:{(adjusted_end_col, adjusted_end_col)} block_comment.start_col: {block_comment.start_col} block_comment.end_col:{block_comment.end_col} block_comment_last_line_len: {block_comment_last_line_len}  block_comment.start_line: {block_comment.start_line} block_comment.end_line: {block_comment.end_line}"
            )
            # Line start adjustment: shift down by number of lines in block comment.
            adjusted_start_line = adjusted_start_line + (
                block_comment.end_line - block_comment.start_line
            )
            # Column start adjustment:
            adjusted_start_col = (
                # If last of the comment is on the same line, add the length of block comment end part.
                (
                    adjusted_start_col
                    - block_comment.start_col
                    + block_comment.end_col
                    - 1  # Account for space
                )
                if adjusted_start_line == block_comment.end_line
                # If on different lines, the start of the token itself is.
                else adjusted_start_col
            )
            # Adjust end position
            # Line end adjustment: same as start
            adjusted_end_line = adjusted_end_line + (
                block_comment.end_line - block_comment.start_line
            )
            # Column end adjustment:
            adjusted_end_col = (
                # If last of the comment is on the same line, add the length of block comment end part.
                (
                    adjusted_end_col
                    - block_comment.start_col
                    + block_comment.end_col
                    - 1  # Account for space
                )
                if adjusted_end_line == block_comment.end_line
                # If on different lines, the start of the token itself is.
                else adjusted_end_col
            )
            debug_verbose_print(
                f"Block Comment Adjusting token {tok.string!r} to start=({adjusted_start_line}, {adjusted_start_col}) "
                f"end=({adjusted_end_line}, {adjusted_end_col}) due to block comment"
            )
        debug_verbose_print(
            f"Yielding token {tok.string!r} at adjusted start=({adjusted_start_line}, {adjusted_start_col}) "
            f"end=({adjusted_end_line}, {adjusted_end_col})"
        )
        yield TokenInfo(
            type=_regularize_token_type(tok.type),
            string=tok.string,
            start=(adjusted_start_line, adjusted_start_col),
            end=(adjusted_end_line, adjusted_end_col),
            line=tok.line,
        )
    for block_comment in unconsumed_block_comment:
        # Yield remaining unconsumed block comments at the end.
        if block_comment not in block_comment_already_output:
            debug_verbose_print(
                f"Yielding remaining block comment at end: start=({block_comment.start_line}, {block_comment.start_col}) "
                f"end=({block_comment.end_line}, {block_comment.end_col})"
            )
            yield TokenInfo(
                type=tokenize.COMMENT,
                string=block_comment.comment,
                start=(block_comment.start_line, block_comment.start_col),
                end=(block_comment.end_line, block_comment.end_col),
                line=block_comment.lines,
            )


def token_stream_factory(readline: Callable[[], str]) -> Iterator[TokenInfo]:
    line_parser = _LineParser(readline)

    yield from _generate_and_postprocess_tokens(
        line_parser.parse_next_line,
        line_parser.outermost_block_comments,
        line_parser.line_head_spaces,
    )
