import ast
from token import ENDMARKER, NEWLINE
from tokenize import COMMENT, TokenInfo

from Typhon.Driver.debugging import debug_verbose_print
from Typhon.Format.attach_comments import attach_comments
from Typhon.Format.doc_render import render_doc_to_string
from Typhon.Format.print_to_doc import print_to_doc
from Typhon.Grammar.parser import parse_string
from Typhon.Grammar.tokenizer_custom import source_to_tokens
from Typhon.SourceMap.source_ast_cache import SourceAstCache


def _parse_module(source: str) -> ast.Module:
    parsed = parse_string(source, mode="exec")
    assert isinstance(parsed, ast.Module)
    return parsed


def _render_source(source: str) -> str:
    module = _parse_module(source)
    attach_comments(module, SourceAstCache(module, source, "<test>"))
    doc = print_to_doc(module)
    debug_verbose_print(lambda: f"Printed doc for source:\n{source}\n\nis:\n{doc}\n")
    return render_doc_to_string(doc)


def _mess_up_source(source: str) -> str:
    # Between some keywords, space cannot be replaced with newline.
    elts = source.split()
    result: list[str] = []
    for i, elt in enumerate(elts):
        next_elt = elts[i + 1] if i + 1 < len(elts) else ""
        if elt in ["return", "yield", "raise", "as", "from", "type"] or next_elt in {
            "import",
            "from",
        }:
            result.append(elt + "  ")
        else:
            result.append(elt + " \n  ")
    return "".join(result)


def _insert_messing_comments(origin_tokens: list[TokenInfo]) -> str:
    # Inserts block comments to every space, line comments to every newline.
    result: list[str] = []
    block_comment_id = 0
    line_comment_id = 0

    def next_block_comment() -> str:
        nonlocal block_comment_id
        comment = f" #(b_{block_comment_id})# "
        block_comment_id += 1
        return comment

    def next_line_comment() -> str:
        nonlocal line_comment_id
        comment = f" #l_{line_comment_id}"
        line_comment_id += 1
        return comment

    for tok in origin_tokens:
        if tok.type == NEWLINE:
            result.append(f"{next_line_comment()}\n")
        elif tok.type == ENDMARKER:
            result.append(tok.string)
        else:
            result.append(next_block_comment())
            result.append(tok.string)
            result.append(next_block_comment())

    return "".join(result)


def assert_comment_format_round_trip(source: str) -> None:
    raw_tokens = source_to_tokens(source)
    source_with_comments = _insert_messing_comments(raw_tokens)
    # Check the formatting results to same token stream.
    origin_tokens = source_to_tokens(source_with_comments)
    formatted = _render_source(source_with_comments)
    formatted_tokens = source_to_tokens(formatted)
    # The allowed difference is only added trailing comma.
    f_cursor = 0
    for o_cursor in range(len(origin_tokens)):
        formatted_tok = formatted_tokens[f_cursor]
        origin_tok = origin_tokens[o_cursor]
        if (
            origin_tok.type == formatted_tok.type
            and origin_tok.string == formatted_tok.string
        ):
            f_cursor += 1
            continue  # OK
        # source_to_tokens still keeps ignored newline. Skip it.
        if origin_tok.type == NEWLINE:
            continue
        if formatted_tok.type == NEWLINE:
            f_cursor += 1
        # Allow trailing comma added by formatter.
        if formatted_tok.string == ",":
            # Check if it's trailing comma by looking at the previous non-comment token.
            debug_verbose_print(
                lambda: f"Found comma {formatted_tok.string} at {f_cursor}"
            )
            next_formatted_tok = None
            for f_next_cursor in range(f_cursor + 1, len(formatted_tokens)):
                next_formatted_tok = formatted_tokens[f_next_cursor]
                if next_formatted_tok.type == COMMENT:
                    continue
                break
            debug_verbose_print(
                lambda: (
                    f"Next non-comment token after comma is {next_formatted_tok} at {f_next_cursor}"
                )
            )
            if next_formatted_tok and next_formatted_tok.string in [
                ")",
                "]",
                "}",
            ]:
                f_cursor += 1  # Skip this is trailing comma
        # Now check again.
        formatted_tok = formatted_tokens[f_cursor]
        if (
            origin_tok.type == formatted_tok.type
            and origin_tok.string == formatted_tok.string
        ):
            f_cursor += 1
            continue  # OK
        assert False, (
            f"Token mismatch expected {origin_tok} at index {f_cursor}, got: {formatted_tok}.\nOriginal source with comments:\n{source_with_comments}\n\nFormatted source:\n{formatted}\n\noriginal tokens:\n{origin_tokens}\n\nFormatted tokens:\n{formatted_tokens}"
        )


def assert_render_pipeline(source: str, expected: str) -> None:
    result = _render_source(source)
    assert result == expected.strip(), f"Expected:\n{expected}\n\nGot:\n{result}"
    round_tripped = _render_source(result)
    assert round_tripped.strip() == expected.strip(), (
        f"Round trip failed. Expected:\n{expected}\n\nGot:\n{round_tripped}"
    )
    messed_up = _mess_up_source(source)
    result_from_messed_up = _render_source(messed_up)
    assert result_from_messed_up.strip() == expected.strip(), (
        f"Formatter did not normalize messed up source. Expected:\n{expected}\n\nGot:\n{result_from_messed_up}\n\nOriginal source:\n{source}\n\nOriginal messed up source:\n{messed_up}"
    )
    assert_comment_format_round_trip(source)  # TODO: Not OK yet


def assert_render_pipeline_comment_sensitive(source: str, expected: str) -> None:
    result = _render_source(source)
    assert result == expected.strip(), f"Expected:\n{expected}\n\nGot:\n{result}"
    round_tripped = _render_source(result)
    assert round_tripped.strip() == expected.strip(), (
        f"Round trip failed. Expected:\n{expected}\n\nGot:\n{round_tripped}"
    )
