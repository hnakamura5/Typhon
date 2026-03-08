from Typhon.Typing.result_diagnostic import Diagnostic


from pathlib import Path
import sys
import ast
from dataclasses import dataclass
from typing import Any, cast
from ..Grammar.parser import parse_file
from ..Grammar.demangle import demangle_text
from ..Grammar.syntax_errors import (
    diag_errors,
    get_syntax_error_in_module,
    syntax_error_message,
    TyphonTransformSyntaxError,
    TyphonSyntaxErrorList,
)
from ..Grammar.unparse_custom import unparse_custom
from ..Utils.path import (
    TYPHON_EXT,
    default_output_dir,
    canonicalize_path,
    mkdir_and_setup_init_py,
)
from ._utils import (
    shorthand,
    copy_type,
)
from ..Transform.transform import transform
from .debugging import debug_print, is_debug_verbose
from ..Driver.type_check import run_type_check, TypeCheckResult
from ..SourceMap import SourceMap
from ..SourceMap.datatype import Range
from ..SourceMap.ast_match_based_map import map_from_translated_ast
from ..Typing.result_diagnostic import Diagnostic, Severity


@dataclass
class TranslateResult:
    source_path_canonical: str
    output_path_canonical: str
    source_map: SourceMap | None
    module: ast.Module | None
    syntax_error: (
        SyntaxError | TyphonTransformSyntaxError | TyphonSyntaxErrorList | None
    )
    translated_code: str | None


def _syntax_errors_to_diagnostics(
    source_path: str,
    source_code: str,
    module: ast.Module | None,
    syntax_error: SyntaxError
    | TyphonTransformSyntaxError
    | TyphonSyntaxErrorList
    | None,
) -> list[Diagnostic]:
    if syntax_error is None:
        return []
    errors = (
        syntax_error.errors
        if isinstance(syntax_error, TyphonSyntaxErrorList)
        else [syntax_error]
    )
    return [
        Diagnostic(
            file_path=source_path,
            severity=Severity.ERROR,
            message=demangle_text(syntax_error_message(error), module),
            pos=Range.from_syntax_error(error),
            rule="",
            source_lines=source_code.splitlines(),
        )
        for error in errors
    ]


def _demangle_type_check_result(
    type_check_result: TypeCheckResult,
    translate_results: list[TranslateResult],
    source_maps: dict[str, SourceMap | None],
) -> TypeCheckResult:
    output_module_map = {
        result.output_path_canonical: result.module
        for result in translate_results
        if result.module is not None
    }
    debug_print(
        lambda: (
            f"Output module map for demangling type check diagnostics: {[d.file_path for d in type_check_result.diagnostics]}"
        )
    )
    diagnostics: list[Diagnostic] = [
        diag.demangle(
            module=output_module_map.get(canonicalize_path(Path(diag.file_path))),
            source_map=source_maps.get(canonicalize_path(Path(diag.file_path))),
        )
        for diag in type_check_result.diagnostics
    ]
    return TypeCheckResult(
        returncode=type_check_result.returncode,
        stderr=type_check_result.stderr,
        files_analyzed=type_check_result.files_analyzed,
        num_errors=type_check_result.num_errors,
        num_warnings=type_check_result.num_warnings,
        num_info=type_check_result.num_info,
        time_in_sec=type_check_result.time_in_sec,
        diagnostics=diagnostics,
    )


def _merge_translate_result_errors(
    type_check_result: TypeCheckResult,
    translate_results: list[TranslateResult],
    source_maps: dict[str, SourceMap | None],
) -> TypeCheckResult:
    type_check_result = _demangle_type_check_result(
        type_check_result, translate_results, source_maps
    )
    syntax_diagnostics = [
        diagnostic
        for result in translate_results
        for diagnostic in _syntax_errors_to_diagnostics(
            result.source_path_canonical,
            Path(result.source_path_canonical).read_text(encoding="utf-8"),
            result.module,
            result.syntax_error,
        )
    ]
    if not syntax_diagnostics:
        return type_check_result
    diagnostics = sorted(
        [*syntax_diagnostics, *type_check_result.diagnostics],
        key=lambda diagnostic: (
            diagnostic.file_path,
            diagnostic.pos.start.line,
            diagnostic.pos.start.column,
            diagnostic.pos.end.line,
            diagnostic.pos.end.column,
        ),
    )
    return TypeCheckResult(
        returncode=1,
        stderr=type_check_result.stderr,
        files_analyzed=type_check_result.files_analyzed,
        num_errors=type_check_result.num_errors + len(syntax_diagnostics),
        num_warnings=type_check_result.num_warnings,
        num_info=type_check_result.num_info,
        time_in_sec=type_check_result.time_in_sec,
        diagnostics=diagnostics,
    )


def _print_type_check_result(
    type_check_result: TypeCheckResult,
    source_maps: dict[str, SourceMap | None],
) -> None:
    output_message = type_check_result.make_output_message(
        source_maps=source_maps,
    )
    if not output_message:
        return
    print(
        output_message,
        file=sys.stderr if not type_check_result.is_successful() else sys.stdout,
    )


def _type_check_failed_empty_result() -> TypeCheckResult:
    return TypeCheckResult(
        returncode=1,
        stderr="",
        files_analyzed=0,
        num_errors=0,
        num_warnings=0,
        num_info=0,
        time_in_sec=0.0,
        diagnostics=[],
    )


def _diag_errors_demangled(
    syntax_error: SyntaxError | TyphonTransformSyntaxError | TyphonSyntaxErrorList,
    source: Path,
    source_code: str,
    module: ast.Module | None,
) -> str:
    return demangle_text(
        diag_errors(
            syntax_error,
            source=source,
            source_code=source_code,
        ),
        module,
    )


def translate_file(
    source: Path,
    output: Path,
    *,
    recover: bool = True,
) -> TranslateResult:
    debug_print(lambda: f"Translating source: {source} to output_dir: {output}")
    ast_tree: ast.Module | None = None
    syntax_error: (
        SyntaxError | TyphonTransformSyntaxError | TyphonSyntaxErrorList | None
    ) = None
    try:
        ast_tree = parse_file(source.as_posix(), verbose=is_debug_verbose())
        transform(
            ast_tree,
            ignore_error=recover,
        )
        if recover:
            syntax_errors = get_syntax_error_in_module(ast_tree)
            if syntax_errors:
                syntax_error = TyphonSyntaxErrorList(syntax_errors)
    except (SyntaxError, TyphonTransformSyntaxError, TyphonSyntaxErrorList) as error:
        error_message = (
            "\n".join(syntax_error_message(e) for e in error.errors)
            if isinstance(error, TyphonSyntaxErrorList)
            else syntax_error_message(error)
        )
        debug_print(lambda: f"Error parsing file {source}: {error_message}")
        return TranslateResult(
            source_path_canonical=canonicalize_path(source),
            output_path_canonical=canonicalize_path(output),
            source_map=None,
            module=ast_tree,
            syntax_error=error,
            translated_code=None,
        )
    translated_code = unparse_custom(ast_tree)
    source_code = source.read_text(encoding="utf-8")
    mapping = map_from_translated_ast(
        ast_tree,
        ast.parse(translated_code),
        source_code,
        source.as_posix(),
        translated_code,
    )
    output.write_text(translated_code)
    return TranslateResult(
        source_path_canonical=canonicalize_path(source),
        output_path_canonical=canonicalize_path(output),
        source_map=cast(SourceMap | None, mapping),
        module=ast_tree,
        syntax_error=syntax_error,
        translated_code=translated_code,
    )


def translate_and_run_type_check_file(
    source: Path,
    output: Path,
    *,
    recover: bool = True,
) -> TypeCheckResult:
    translate_result = translate_file(
        source,
        output,
        recover=recover,
    )
    if translate_result.syntax_error is not None:
        syntax_message = _diag_errors_demangled(
            translate_result.syntax_error,
            source=source,
            source_code=source.read_text(encoding="utf-8"),
            module=translate_result.module,
        )
        if not recover:
            print(syntax_message, file=sys.stderr)
            raise RuntimeError("Syntax error during translation.")
        if translate_result.translated_code is None:
            result = _merge_translate_result_errors(
                _type_check_failed_empty_result(),
                [translate_result],
                {translate_result.output_path_canonical: translate_result.source_map},
            )
            _print_type_check_result(result, source_maps={})
            return result
    type_check_result = run_type_check(output)
    type_check_result = _merge_translate_result_errors(
        type_check_result,
        [translate_result],
        {translate_result.output_path_canonical: translate_result.source_map},
    )
    _print_type_check_result(
        type_check_result,
        source_maps={
            translate_result.output_path_canonical: translate_result.source_map
        },
    )
    return type_check_result


# Always translate as a module.
# __init__.py is always created in the output directory.
def translate_directory(
    source_dir: Path,
    module_output_dir: Path,
    *,
    recover: bool = True,
) -> dict[Path, TranslateResult]:
    result: dict[Path, TranslateResult] = {}
    debug_print(
        lambda: (
            f"Translating source directory: {source_dir} to module output_dir: {module_output_dir}"
        )
    )
    module_output_dir.mkdir(parents=True, exist_ok=True)
    for source in source_dir.glob(f"*{TYPHON_EXT}"):
        output_path = module_output_dir / (source.stem + ".py")
        file_result = translate_file(
            source,
            output_path,
            recover=recover,
        )
        result[source] = file_result
    mkdir_and_setup_init_py(module_output_dir)
    for subdir in source_dir.iterdir():
        if subdir.is_dir():
            sub_output_dir = module_output_dir / subdir.name
            sub_output_dir.mkdir(exist_ok=True)
            subdir_result = translate_directory(
                subdir,
                sub_output_dir,
                recover=recover,
            )
            result.update(subdir_result)
    return result


def translate_and_run_type_check_directory(
    source_dir: Path,
    module_output_dir: Path,
    *,
    recover: bool = True,
) -> TypeCheckResult:
    translate_results = translate_directory(
        source_dir,
        module_output_dir,
        recover=recover,
    )
    source_maps = {
        t.output_path_canonical: t.source_map
        for t in translate_results.values()
        if t.translated_code is not None
    }
    if not recover:
        exists_syntax_error = False
        for t in translate_results.values():
            if t.syntax_error is not None:
                exists_syntax_error = True
                print(
                    _diag_errors_demangled(
                        t.syntax_error,
                        source=Path(t.source_path_canonical),
                        source_code=Path(t.source_path_canonical).read_text(
                            encoding="utf-8"
                        ),
                        module=t.module,
                    ),
                    file=sys.stderr,
                )
        if exists_syntax_error:
            raise RuntimeError("Syntax errors during translation.")
    elif any(
        t.syntax_error is not None and t.translated_code is None
        for t in translate_results.values()
    ):
        result = _merge_translate_result_errors(
            _type_check_failed_empty_result(),
            list(translate_results.values()),
            source_maps,
        )
        _print_type_check_result(result, source_maps=source_maps)
        return result

    type_check_result = run_type_check(module_output_dir, run_mode=True)

    type_check_result = _merge_translate_result_errors(
        type_check_result,
        list(translate_results.values()),
        source_maps,
    )
    _print_type_check_result(type_check_result, source_maps=source_maps)
    return type_check_result


def translate(
    source: str,
    *,
    output_dir: str | None = None,
    _o: str | None = None,  # Shorthand for output_dir
    recover: bool = True,
):
    """
    Translates the given source code from Typhon language to Python code.

    Single file to single file, or directory to module directory translation is supported.
    In directory, all '.typh' files are translated to '.py' files.

    Usage:
        source: The Typhon source code or directory to be translated.
        --output_dir [str]: The directory where the translated Python code will be saved. The default is .typhon directory in the source's parent directory of source.
        -o [str]: Shorthand for output_dir.
        --recover: Continue to type checking when parsing recovered enough to produce an AST.
    """
    source_path = Path(source)
    output_dir = shorthand(
        "--output_dir", output_dir, "-o", _o, default_output_dir(source).as_posix()
    )
    output_dir_path = Path(output_dir)
    debug_print(
        lambda: (
            f"Translating source: {source} to output_dir: {output_dir_path.as_posix()}"
        )
    )
    output_dir_path.mkdir(parents=True, exist_ok=True)
    if source_path.is_file():
        output_file = output_dir_path / (source_path.stem + ".py")
        result = translate_and_run_type_check_file(
            source_path,
            output_file,
            recover=recover,
        )
    elif source_path.is_dir():
        result = translate_and_run_type_check_directory(
            source_path,
            output_dir_path / source_path.name,
            recover=recover,
        )
    else:
        raise FileNotFoundError(f"Source path '{source}' does not exist.")
    if not result.is_successful():
        raise RuntimeError("Type checking failed.")


@copy_type(translate)
def tr(*args: Any, **kwargs: Any):
    """Shorthand for translate"""
    return translate(*args, **kwargs)
