from ....src.Typhon.Typing.pyright import parse_json_output

code_with_error = """
{
  "version": "1.32.1",
  "time": "1000000000000",
  "generalDiagnostics": [
    {
      "file": ".\\\\Typhon\\\\test\\\\execute\\\\RunFileTest\\\\.typhon\\\\comprehension.py",
      "severity": "error",
      "message": "Type \\"Generator[int, Any, None]\\" is not assignable to declared type \\"tuple[int, str]\\"\\\\n\\\\xa0\\\\xa0\\"Generator[int, Any, None]\\" is not assignable to \\"tuple[int, str]\\"",
      "range": {
        "start": { "line": 17, "character": 24 },
        "end": { "line": 17, "character": 39 }
      },
      "rule": "reportAssignmentType"
    },
    {
      "file": ".\\\\Typhon\\\\test\\\\execute\\\\RunFileTest\\\\.typhon\\\\comprehension.py",
      "severity": "error",
      "message": "Type \\"int | str\\" is not assignable to declared type \\"str\\"\\\\n\\\\xa0\\\\xa0Type \\"int | str\\" is not assignable to type \\"str\\"\\\\n\\\\xa0\\\\xa0\\\\xa0\\\\xa0\\"int\\" is not assignable to \\"str\\"",
      "range": {
        "start": { "line": 19, "character": 4 },
        "end": { "line": 19, "character": 19 }
      },
      "rule": "reportAssignmentType"
    }
  ],
  "summary": {
    "filesAnalyzed": 1,
    "errorCount": 2,
    "warningCount": 0,
    "informationCount": 0,
    "timeInSec": 0.277
  }
}
"""


def test_parse_pyright_json_with_error():
    result = parse_json_output(code_with_error, returncode=0, stderr="")
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.files_analyzed == 1
    assert result.num_errors == 2
    assert result.num_warnings == 0
    assert result.num_info == 0
    assert len(result.diagnostics) == 2
    diag1 = result.diagnostics[0]
    assert diag1.file_path.endswith("comprehension.py")
    assert diag1.severity.name == "ERROR"
    assert "Generator[int, Any, None]" in diag1.message
    assert "tuple[int, str]" in diag1.message
    assert diag1.pos["lineno"] == 17
    assert diag1.pos["col_offset"] == 24
    assert diag1.pos["end_lineno"] == 17
    assert diag1.pos["end_col_offset"] == 39
    assert diag1.rule == "reportAssignmentType"
    diag2 = result.diagnostics[1]
    assert diag2.file_path.endswith("comprehension.py")
    assert diag2.severity.name == "ERROR"
    assert "int | str" in diag2.message
    assert "str" in diag2.message
    assert diag2.pos["lineno"] == 19
    assert diag2.pos["col_offset"] == 4
    assert diag2.pos["end_lineno"] == 19
    assert diag2.pos["end_col_offset"] == 19
    assert diag2.rule == "reportAssignmentType"


code_no_error = """
{
    "version": "1.32.1",
    "time": "1000000000000",
    "generalDiagnostics": [],
    "summary": {
        "filesAnalyzed": 4,
        "errorCount": 0,
        "warningCount": 0,
        "informationCount": 0,
        "timeInSec": 0.188
    }
}
"""


def test_parse_pyright_json_no_error():
    result = parse_json_output(code_no_error, returncode=0, stderr="")
    assert result.files_analyzed == 4
    assert result.num_errors == 0
    assert result.num_warnings == 0
    assert result.num_info == 0
    assert len(result.diagnostics) == 0
