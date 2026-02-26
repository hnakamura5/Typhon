import sys
from pathlib import Path
import subprocess
from ..Driver.debugging import debug_print
from typing import Literal, cast, Any
import json
from .result_diagnostic import Severity, Diagnostic, TypeCheckResult
from ..SourceMap.datatype import Range, Pos

# https://docs.basedpyright.com/dev/configuration/config-files/
type TypeCheckLevel = Literal[
    "off",
    "basic",
    "strict",
    "all",
    "translate",  # Default for Typhon translation
    "script",  # Default for Typhon scripts
]
translate_config = {
    "typeCheckingMode": "strict",
    "reportUnusedExpression": "warning",
    "reportUnusedClass": "warning",
    "reportUnusedImport": "warning",
    "reportUnusedFunction": "warning",
    "reportUnusedVariable": "warning",
    "reportUnusedCallResult": "warning",
    "reportUnnecessaryIsInstance": "warning",
    "reportUnnecessaryCast": "warning",
    # "reportUnnecessaryComparison": "warning", # To check type of patterns
    "reportUnnecessaryContains": "warning",
    "reportDeprecated": "warning",
}
script_config = {
    "typeCheckingMode": "strict",
    "reportUnusedExpression": "none",
    "reportUnusedClass": "none",
    "reportUnusedImport": "none",
    "reportUnusedFunction": "none",
    "reportUnusedVariable": "none",
    "reportUnusedCallResult": "none",
    "reportUnnecessaryIsInstance": "none",
    "reportUnnecessaryCast": "none",
    # "reportUnnecessaryComparison": "none",  # To check type of patterns
    "reportUnnecessaryContains": "none",
    "reportDeprecated": "none",
}

ignore_errors_by_message = {
    # for (let i in ...)
    'A "Final" variable cannot be assigned within a loop',
}


def write_pyright_config(
    output_dir: Path, level: TypeCheckLevel = "translate", overwrite: bool = False
) -> str:
    config = {
        "include": ["**/*.py"],
        "exclude": ["**/__pycache__"],
        "typeCheckingMode": "off",
    }
    if level == "translate":
        config.update(translate_config)
    elif level == "script":
        config.update(script_config)
    elif level == "basic":
        config["typeCheckingMode"] = "basic"
    elif level == "strict":
        config["typeCheckingMode"] = "strict"
    elif level == "all":
        config["typeCheckingMode"] = "all"
    else:
        raise ValueError(f"Unknown type check level: {level}")
    config_path = output_dir / "pyrightconfig.json"
    if not overwrite and config_path.exists():
        debug_print(
            f"Config file already exists at {config_path}. Use overwrite=True to replace."
        )
        return str(config_path)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
    debug_print(f"Generated pyright config at {config_path}")
    return str(config_path)


def _try_read_attr[T](d: Any, attr: str, default: T) -> T:
    result = d.get(attr, default)
    return cast(T, result)


def _parse_pos_range(pos: Any) -> Range:
    start = _try_read_attr(pos, "start", {})
    end = _try_read_attr(pos, "end", {})
    return Range(
        start=Pos(line=start.get("line", 0), column=start.get("character", 0)),
        end=Pos(line=end.get("line", 0), column=end.get("character", 0)),
    )


def _parse_diagnostic(diag: Any) -> Diagnostic:
    return Diagnostic(
        file_path=_try_read_attr(diag, "file", ""),
        severity=Severity[_try_read_attr(diag, "severity", "INFO").upper()],
        message=_try_read_attr(diag, "message", ""),
        pos=_parse_pos_range(diag["range"]),
        rule=_try_read_attr(diag, "rule", ""),
    )


def parse_json_output(output: str, returncode: int, stderr: str) -> TypeCheckResult:
    data = json.loads(output)
    diagnostics = [
        _parse_diagnostic(diag) for diag in data.get("generalDiagnostics", [])
    ]
    summary = _try_read_attr(data, "summary", {})
    return TypeCheckResult(
        returncode=returncode,
        stderr=stderr,
        files_analyzed=_try_read_attr(summary, "filesAnalyzed", 0),
        num_errors=_try_read_attr(summary, "errorCount", 0),
        num_warnings=_try_read_attr(summary, "warningCount", 0),
        num_info=_try_read_attr(summary, "informationCount", 0),
        time_in_sec=_try_read_attr(summary, "timeInSec", 0.0),
        diagnostics=diagnostics,
    )


def filter_ignore_message(message: str) -> bool:
    return message in ignore_errors_by_message


def filter_ignore_position(pos: Range) -> bool:
    # Ignore diagnostics at position (0, 0).
    return pos == Range(
        start=Pos(line=0, column=0),
        end=Pos(line=0, column=0),
    )


def _filter_ignore_diagnostics(
    result: TypeCheckResult,
) -> TypeCheckResult:
    filtered_diagnostics: list[Diagnostic] = []
    num_error = 0
    num_warning = 0
    num_info = 0
    for diag in result.diagnostics:
        if filter_ignore_message(diag.message):
            debug_print(f"Ignoring diagnostic by message: {diag}")
            continue
        if filter_ignore_position(diag.pos) and diag.severity != Severity.ERROR:
            debug_print(f"Ignoring diagnostic by position: {diag}")
            continue
        filtered_diagnostics.append(diag)
        if diag.severity == Severity.ERROR:
            num_error += 1
        elif diag.severity == Severity.WARNING:
            num_warning += 1
        elif diag.severity == Severity.INFO:
            num_info += 1
    returncode = result.returncode
    if returncode == 1 and num_error == 0:
        returncode = 0
    return TypeCheckResult(
        returncode=returncode,
        stderr=result.stderr,
        files_analyzed=result.files_analyzed,
        num_errors=num_error,
        num_warnings=num_warning,
        num_info=num_info,
        time_in_sec=result.time_in_sec,
        diagnostics=filtered_diagnostics,
    )


def run_pyright(
    py_file_or_dir: Path, level: TypeCheckLevel = "translate"
) -> TypeCheckResult:
    output = subprocess.run(
        [
            sys.executable,
            "-m",
            "basedpyright",
            str(py_file_or_dir),
            "--outputjson",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )
    result = parse_json_output(
        output.stdout.decode(), output.returncode, output.stderr.decode()
    )
    return _filter_ignore_diagnostics(result)
