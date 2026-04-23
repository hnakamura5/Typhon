import ast

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


def assert_render_pipeline_comment_sensitive(source: str, expected: str) -> None:
    result = _render_source(source)
    assert result == expected.strip(), f"Expected:\n{expected}\n\nGot:\n{result}"
    round_tripped = _render_source(result)
    assert round_tripped.strip() == expected.strip(), (
        f"Round trip failed. Expected:\n{expected}\n\nGot:\n{round_tripped}"
    )
