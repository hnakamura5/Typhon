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
    "reportUnnecessaryComparison": "warning",
    "reportUnnecessaryContains": "warning",
    "reportMatchNotExhaustive": "warning",
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
    "reportUnnecessaryComparison": "none",
    "reportUnnecessaryContains": "none",
    "reportMatchNotExhaustive": "none",
    "reportDeprecated": "none",
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
    # All lines and columns are 0-based, convert to 1-based.
    return Range(
        start=Pos(line=start.get("line", 0) + 1, column=start.get("character", 0) + 1),
        end=Pos(line=end.get("line", 0) + 1, column=end.get("character", 0) + 1),
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
    return result
