from pathlib import Path
import sys
import ast
from dataclasses import dataclass
from ..Grammar.parser import parse_file
from ..Grammar.syntax_errors import (
    diag_errors,
    TyphonSyntaxError,
    TyphonSyntaxErrorList,
)
from .utils import (
    shorthand,
    TYPHON_EXT,
    copy_type,
    default_output_dir,
    canonicalize_path,
)
from ..Transform.transform import transform
from .debugging import is_debug_mode, debug_print, is_debug_verbose
from ..Driver.type_check import run_type_check, TypeCheckResult
from ..SourceMap import SourceMap
from ..SourceMap.ast_match_based_map import map_from_transformed_ast


@dataclass
class TranslateResult:
    source_path_canonical: str
    output_path_canonical: str
    source_map: SourceMap | None
    syntax_error: SyntaxError | TyphonSyntaxError | TyphonSyntaxErrorList | None


def translate_file(source: Path, output: Path) -> TranslateResult:
    debug_print(f"Translating source: {source} to output_dir: {output}")
    try:
        ast_tree = parse_file(source.as_posix(), verbose=is_debug_verbose())
        transform(ast_tree)
    except (SyntaxError, TyphonSyntaxError, TyphonSyntaxErrorList) as e:
        debug_print(f"Error parsing file {source}: {e}")
        return TranslateResult(
            source_path_canonical=canonicalize_path(source),
            output_path_canonical=canonicalize_path(output),
            source_map=None,
            syntax_error=e,
        )
    translated_code = ast.unparse(ast_tree)
    source_code = source.read_text(encoding="utf-8")
    mapping = map_from_transformed_ast(
        ast_tree, ast.parse(translated_code), source_code, source.as_posix()
    )
    output.write_text(translated_code)
    return TranslateResult(
        source_path_canonical=canonicalize_path(source),
        output_path_canonical=canonicalize_path(output),
        source_map=mapping,
        syntax_error=None,
    )


def translate_and_run_type_check_file(source: Path, output: Path) -> TypeCheckResult:
    translate_result = translate_file(source, output)
    if translate_result.syntax_error is not None:
        print(
            diag_errors(
                translate_result.syntax_error,
                source=source,
                source_code=source.read_text(encoding="utf-8"),
            ),
            file=sys.stderr,
        )
        raise RuntimeError("Syntax error during translation.")
    type_check_result = run_type_check(output)
    print(
        type_check_result.make_output_message(
            source_maps={
                translate_result.output_path_canonical: translate_result.source_map
            }
        ),
        file=sys.stderr if not type_check_result.is_successful() else sys.stdout,
    )
    return type_check_result


# Always translate as a module.
# __init__.py is always created in the output directory.
def translate_directory(
    source_dir: Path, module_output_dir: Path
) -> dict[Path, TranslateResult]:
    result: dict[Path, TranslateResult] = {}
    debug_print(
        f"Translating source directory: {source_dir} to module output_dir: {module_output_dir}"
    )
    module_output_dir.mkdir(parents=True, exist_ok=True)
    for source in source_dir.glob(f"*{TYPHON_EXT}"):
        output_path = module_output_dir / (source.stem + ".py")
        file_result = translate_file(source, output_path)
        result[source] = file_result
    if not (module_output_dir / "__init__.py").exists():
        (module_output_dir / "__init__.py").write_text(
            "# Init file for Typhon module\n", "utf-8"
        )
    for subdir in source_dir.iterdir():
        if subdir.is_dir():
            sub_output_dir = module_output_dir / subdir.name
            sub_output_dir.mkdir(exist_ok=True)
            subdir_result = translate_directory(subdir, sub_output_dir)
            result.update(subdir_result)
    return result


def translate_and_run_type_check_directory(
    source_dir: Path, module_output_dir: Path
) -> TypeCheckResult:
    translate_result = translate_directory(source_dir, module_output_dir)
    exists_syntax_error = False
    for t in translate_result.values():
        if t.syntax_error is not None:
            exists_syntax_error = True
            print(
                diag_errors(
                    t.syntax_error,
                    source=Path(t.source_path_canonical),
                    source_code=Path(t.source_path_canonical).read_text(
                        encoding="utf-8"
                    ),
                ),
                file=sys.stderr,
            )
    if exists_syntax_error:
        raise RuntimeError("Syntax errors during translation.")
    type_check_result = run_type_check(module_output_dir, run_mode=True)
    print(
        type_check_result.make_output_message(
            source_maps={
                t.output_path_canonical: t.source_map
                for _, t in translate_result.items()
            }
        ),
        file=sys.stderr if not type_check_result.is_successful() else sys.stdout,
    )
    return type_check_result


def translate(
    source: str,
    *,
    output_dir: str | None = None,
    _o: str | None = None,  # Shorthand for output_dir
):
    """
    Translates the given source code from Typhon language to Python code.

    Single file to single file, or directory to module directory translation is supported.
    In directory, all '.typh' files are translated to '.py' files.

    Usage:
        source: The Typhon source code or directory to be translated.
        --output_dir [str]: The directory where the translated Python code will be saved. The default is .typhon directory in the source's parent directory of source.
        -o [str]: Shorthand for output_dir.
    """
    source_path = Path(source)
    output_dir = shorthand(
        "--output_dir", output_dir, "-o", _o, default_output_dir(source).as_posix()
    )
    output_dir_path = Path(output_dir)
    debug_print(
        f"Translating source: {source} to output_dir: {output_dir_path.as_posix()}"
    )
    output_dir_path.mkdir(parents=True, exist_ok=True)
    if source_path.is_file():
        output_file = output_dir_path / (source_path.stem + ".py")
        result = translate_and_run_type_check_file(source_path, output_file)
    elif source_path.is_dir():
        result = translate_and_run_type_check_directory(
            source_path, output_dir_path / source_path.name
        )
    else:
        raise FileNotFoundError(f"Source path '{source}' does not exist.")
    if not result.is_successful():
        raise RuntimeError("Type checking failed.")


@copy_type(translate)
def tr(*args, **kwargs):
    """Shorthand for translate"""
    return translate(*args, **kwargs)
