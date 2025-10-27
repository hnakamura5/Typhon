from typing import Callable, Iterator
from tokenize import TokenInfo, generate_tokens
import tokenize
import re
from dataclasses import dataclass
from ..Driver.debugging import debug_print, debug_verbose_print


def regularize_token_type(token_type: int) -> int:
    """Convert token type to a regularized form for Typhon.

    NL -> NEWLINE
    """
    if token_type == tokenize.NL:
        return tokenize.NEWLINE
    return token_type


@dataclass
class BlockComment:
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


_BLOCK_COMMENT_BEGIN_IN_FRONT = re.compile(r"^#+\(.*")
_BLOCK_COMMENT_BEGIN_OR_END_RE = re.compile(r"(?P<begin>#+\()|(?P<end>\)#+)")


def token_stream_factory(readline: Callable[[], str]) -> Iterator[TokenInfo]:
    line_num: int = 0
    block_comment_begin_stack: list[BlockComment] = []
    unconsumed_block_comment: list[BlockComment] = []
    block_comment_already_output: set[BlockComment] = set()

    def readline_wrapper() -> str:
        nonlocal line_num, block_comment_begin_stack, unconsumed_block_comment
        line_num += 1
        line: str | None = readline()
        if line.startswith("#") and not _BLOCK_COMMENT_BEGIN_IN_FRONT.match(line):
            return line  # Normal comment line
        result = ""
        line_last_took = 0
        while line:
            begin_ends = _BLOCK_COMMENT_BEGIN_OR_END_RE.finditer(line)
            for match in begin_ends:
                if block_comment_begin_stack:
                    # Accumulate comment content to outermost block comment
                    debug_verbose_print(
                        f"Adding block comment mid part : {line[line_last_took : match.start()]!r}"
                    )
                    block_comment_begin_stack[0].comment += line[
                        line_last_took : match.start()
                    ]
                    line_last_took = match.start()
                else:
                    result += line[line_last_took : match.start()]
                if match.group("begin"):
                    debug_print(
                        f"Block comment begins at line {line_num} col {match.start()}:{match.end()} stack={len(block_comment_begin_stack)}"
                    )
                    # Stack the begin to distinguish the corresponding end.
                    block_comment_begin_stack.append(
                        BlockComment(
                            start_line=line_num,
                            start_col=match.start(),
                            end_line=0,
                            end_col=0,
                            comment="",
                            lines=line,
                        )
                    )
                    # Add comment delimiting part to outermost.
                    debug_verbose_print(
                        f"Adding block comment begin part : {line[match.start() : match.end()]!r}"
                    )
                    block_comment_begin_stack[0].comment += line[
                        match.start() : match.end()
                    ]
                    line_last_took = match.end()
                elif match.group("end") and block_comment_begin_stack:
                    debug_verbose_print(
                        f"Block comment ends at line {line_num} col {match.start()}:{match.end()} stack={len(block_comment_begin_stack)} comment={block_comment_begin_stack[0].comment!r}"
                    )
                    if len(block_comment_begin_stack) == 1:
                        # Outermost block comment ends here.
                        block_comment = block_comment_begin_stack[-1]
                        block_comment.end_line = line_num
                        block_comment.end_col = match.end()
                        unconsumed_block_comment.append(block_comment)
                        result += " "  # Replace block comment with space
                    # Add comment delimiting part to outermost.
                    debug_verbose_print(
                        f"Adding block comment end part : {line[line_last_took : match.end()]!r}"
                    )
                    block_comment_begin_stack[0].comment += line[
                        line_last_took : match.end()
                    ]
                    line_last_took = match.end()
                    block_comment_begin_stack.pop()
            if block_comment_begin_stack:
                # Still inside block comment, continue to next line.
                block_comment_begin_stack[0].comment += line[line_last_took:]
                debug_verbose_print(
                    f"Adding remaining line to block comment: {line[line_last_took:]!r}"
                )
                line = readline()
                if line:
                    block_comment_begin_stack[0].lines += "\n" + line
                line_num += 1
                line_last_took = 0
            else:
                result += line[line_last_took:]
                break
        return result

    line_offset_already_consumed = 0
    # Adjust token positions from generated tokens, and mix in block comment tokens.
    for tok in generate_tokens(readline_wrapper):
        debug_verbose_print(
            f"Generated token: {tok.string!r} type={tok.type} start={tok.start} end={tok.end}"
        )
        tok_start_line, tok_start_col = tok.start
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
        adjusted_start_line, adjusted_start_col = tok.start
        adjusted_end_line, adjusted_end_col = tok.end
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
                debug_print(
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
            type=regularize_token_type(tok.type),
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
