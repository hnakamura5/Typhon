from pathlib import Path
import pytest

from Typhon.Driver.debugging import debug_print
from Typhon.Driver.translate import translate_file
from Typhon.Driver.type_check import run_type_check
from Typhon.Utils.path import prepare_default_output_file
from Typhon.Grammar.syntax_errors import diag_errors


TYPE_ERROR_TESTS = sorted((Path(__file__).parent / "TypeErrorTest").glob("*.typh"))


@pytest.mark.parametrize("test_file", TYPE_ERROR_TESTS, ids=lambda p: p.name)
def test_typh_type_errors(test_file: Path):
    print(f"Running type error test file: {test_file}")
    output_file = prepare_default_output_file(test_file)
    translate_result = translate_file(test_file, output_file)
    if translate_result.syntax_error is not None:
        stderr_output = diag_errors(
            translate_result.syntax_error,
            source=test_file,
            source_code=test_file.read_text(encoding="utf-8"),
        )
        assert stderr_output
        return

    type_check_result = run_type_check(output_file)
    debug_print(f"Type check result for {test_file}: {type_check_result.summary()}")
    assert not type_check_result.is_successful()
    assert type_check_result.num_errors > 0
