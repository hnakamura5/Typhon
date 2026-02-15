from pathlib import Path
import pytest

from Typhon.Driver.debugging import debug_print
from Typhon.Driver.translate import translate_file
from Typhon.Utils.path import prepare_default_output_file
from Typhon.Grammar.syntax_errors import diag_errors

from .file_check_util import assert_file_stderr


SYNTAX_ERROR_TESTS = sorted((Path(__file__).parent / "SyntaxErrorTest").glob("*.typh"))


@pytest.mark.parametrize("test_file", SYNTAX_ERROR_TESTS, ids=lambda p: p.name)
def test_typh_syntax_errors(test_file: Path):
    print(f"Running error test file: {test_file}")
    output_file = prepare_default_output_file(test_file)
    result = translate_file(test_file, output_file)
    assert result.syntax_error is not None
    stderr_output = diag_errors(
        result.syntax_error,
        source=test_file,
        source_code=test_file.read_text(encoding="utf-8"),
    )
    debug_print(f"Test file: {test_file} result:\n{result}")
    assert_file_stderr(test_file, stderr_output)
