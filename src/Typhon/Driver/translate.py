from pathlib import Path
import ast
from ..Grammar.parser import parse_file
from .utils import shorthand, TYPHON_EXT, copy_type, default_output_dir
from ..Transform.transform import transform
from .debugging import is_debug_mode, debug_print, is_debug_verbose


def _translate_file(source: Path, output: Path):
    debug_print(f"Translating source: {source} to output_dir: {output}")
    ast_tree = parse_file(source.as_posix(), verbose=is_debug_verbose())
    transform(ast_tree)
    translated_code = ast.unparse(ast_tree)
    output.write_text(translated_code)


# Always translate as a module.
# __init__.py is always created in the output directory.
def translate_directory(source_dir: Path, module_output_dir: Path):
    debug_print(
        f"Translating source directory: {source_dir} to module output_dir: {module_output_dir}"
    )
    module_output_dir.mkdir(parents=True, exist_ok=True)
    for source in source_dir.glob(f"*{TYPHON_EXT}"):
        output_path = module_output_dir / (source.stem + ".py")
        _translate_file(source, output_path)
    if not (module_output_dir / "__init__.py").exists():
        (module_output_dir / "__init__.py").write_text(
            "# Init file for Typhon module\n", "utf-8"
        )
    for subdir in source_dir.iterdir():
        if subdir.is_dir():
            sub_output_dir = module_output_dir / subdir.name
            sub_output_dir.mkdir(exist_ok=True)
            translate_directory(subdir, sub_output_dir)


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
        _translate_file(source_path, output_file)
    elif source_path.is_dir():
        translate_directory(source_path, output_dir_path / source_path.name)
    else:
        raise FileNotFoundError(f"Source path '{source}' does not exist.")


@copy_type(translate)
def tr(*args, **kwargs):
    """Shorthand for translate"""
    return translate(*args, **kwargs)
