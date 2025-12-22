from pathlib import Path
from ...src.Typhon.Driver.run import run_file, run_directory
from ...src.Typhon.Driver.translate import (
    translate_file,
    translate_and_run_type_check_file,
)
from ...src.Typhon.Driver.utils import prepare_default_output_file
from ...src.Typhon.Driver.debugging import debug_print, set_debug_mode
from .file_check_util import assert_file_stdout, assert_file_stderr
from ...src.Typhon.Grammar.syntax_errors import diag_errors


# Test to run .typh files in test/RunFileTest directory.
# This is test for translation and run_file functionality.
def test_typh_files():
    test_dir = Path(__file__).parent / "RunFileTest"
    for test in test_dir.glob("*.typh"):
        result = run_file(test, capture_output=True)
        debug_print(f"Test file: {test} result:\n{result}")
        assert result.returncode == 0
        assert_file_stdout(test, result.stdout)
        assert_file_stderr(test, result.stderr)


def test_typh_directory():
    set_debug_mode(True)
    test_dir = Path(__file__).parent / "RunDirTest" / "test_module"
    result = run_directory(test_dir, capture_output=True)
    debug_print(f"Test directory: {test_dir} result:\n{result}")
    assert_file_stdout(test_dir / "__main__.typh", result.stdout)
    assert_file_stderr(test_dir / "__main__.typh", result.stderr)


def test_typh_errors():
    test_dir = Path(__file__).parent / "RunTranslateErrorTest"
    for test in test_dir.glob("*.typh"):
        print(f"Running error test file: {test}")
        output_file = prepare_default_output_file(test)
        result = translate_file(test, output_file)
        assert result.syntax_error is not None
        stderr_output = diag_errors(
            result.syntax_error,
            source=test,
            source_code=test.read_text(encoding="utf-8"),
        )
        debug_print(f"Test file: {test} result:\n{result}")
        assert_file_stderr(test, stderr_output)
