from pathlib import Path


# extract the result written in docstring """result ... """
def extract_results(source_code: Path) -> str:
    result = ""
    with source_code.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    in_result_block = False

    for line in lines:
        if line.strip().startswith('"""result'):
            in_result_block = True
            continue
        elif line.strip().startswith('"""') and in_result_block:
            in_result_block = False
            continue
        if in_result_block:
            result += line + "\n"
    return result.strip()


def assert_file_output(source_code: Path, stdout: str):
    expected_output = extract_results(source_code)
    assert stdout.strip() == expected_output.strip(), (
        f"Output does not match expected result in {source_code.name}.\n"
        f"Expected:\n{expected_output}\n\nGot:\n{stdout}"
    )
