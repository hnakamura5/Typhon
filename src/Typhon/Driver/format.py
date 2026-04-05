from pathlib import Path
import sys

from ..Format.doc_render import render_doc_to_string
from ..Format.print_to_doc import print_to_doc
from ..Grammar.parser import parse_file
from ..Grammar.syntax_errors import (
    TyphonSyntaxErrorList,
    diag_errors,
    get_syntax_error_in_module,
)
from ..Utils.path import TYPHON_EXT
from ._utils import shorthand
from .debugging import is_debug_verbose


def _syntax_error_message(
    source: Path, syntax_errors: list[SyntaxError], *, compact: bool
) -> str:
    if len(syntax_errors) == 0:
        return ""
    if compact:
        return f"Syntax errors found in '{source.as_posix()}'."
    return diag_errors(
        TyphonSyntaxErrorList(syntax_errors),
        source=source,
        source_code=source.read_text(encoding="utf-8"),
    )


def _format_file_or_error(source: Path) -> tuple[str | None, list[SyntaxError]]:
    parsed = parse_file(source.as_posix(), verbose=is_debug_verbose())
    syntax_errors = get_syntax_error_in_module(parsed) or []
    if len(syntax_errors) > 0:
        return None, syntax_errors
    return render_doc_to_string(print_to_doc(parsed)), []


def format_file(source: Path) -> str | None:
    formatted, _ = _format_file_or_error(source)
    return formatted


def format_directory(
    source_dir: Path,
) -> dict[Path, tuple[str | None, list[SyntaxError]]]:
    return {
        source: _format_file_or_error(source)
        for source in sorted(
            source_dir.rglob(f"*{TYPHON_EXT}"), key=lambda p: p.as_posix()
        )
    }


def format(
    source: str,
    *,
    inplace: bool | None = None,
    _i: bool | None = None,  # Shorthand for inplace
) -> None:
    """
    Formats Typhon source code.

    Usage:
        source: The Typhon source file or directory to format.
        --inplace [bool]: Overwrite files with the formatted result.
        -i [bool]: Shorthand for inplace.
    """
    source_path = Path(source)
    inplace = shorthand("--inplace", inplace, "-i", _i, False)

    if source_path.is_file():
        if source_path.suffix != TYPHON_EXT:
            raise ValueError(f"Source file must have '{TYPHON_EXT}' extension.")

        formatted, syntax_errors = _format_file_or_error(source_path)
        if formatted is None:
            print(
                _syntax_error_message(source_path, syntax_errors, compact=inplace),
                file=sys.stderr,
            )
            raise RuntimeError("Formatting failed due to syntax errors.")
        if inplace:
            source_path.write_text(formatted, encoding="utf-8")
        else:
            print(formatted)
        return

    if source_path.is_dir():
        formatted_by_file = format_directory(source_path)
        has_syntax_error = False

        for path, (formatted, syntax_errors) in formatted_by_file.items():
            if formatted is None:
                has_syntax_error = True
                print(
                    _syntax_error_message(path, syntax_errors, compact=inplace),
                    file=sys.stderr,
                )

        if inplace:
            # Overwrite the file. Not print to stdout.
            for path, (formatted, _) in formatted_by_file.items():
                if formatted is None:
                    continue
                path.write_text(formatted, encoding="utf-8")
            if has_syntax_error:
                raise RuntimeError("Formatting failed due to syntax errors.")
            return

        formatted_outputs = [
            formatted
            for formatted, _ in formatted_by_file.values()
            if formatted is not None
        ]
        for i, formatted in enumerate(formatted_outputs):
            if i > 0:
                print()
            print(formatted)
        if has_syntax_error:
            raise RuntimeError("Formatting failed due to syntax errors.")
        return

    raise FileNotFoundError(f"Source path '{source}' does not exist.")
