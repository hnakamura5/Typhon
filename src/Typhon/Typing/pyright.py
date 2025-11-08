import sys
from pathlib import Path
import subprocess
from ..Driver.debugging import debug_print
from typing import Literal
import json

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


def run_pyright(py_file_or_dir: Path, level: TypeCheckLevel = "translate") -> bool:
    output = subprocess.run(
        [sys.executable, "-m", "basedpyright", str(py_file_or_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # TODO: Currently printing directly. Take json and convert lines to Typhon source locations.
    decoded = output.stdout.decode()
    result_line = decoded.strip().split("\n")[-1]
    print(f"Pyright result: {result_line}")
    if len(output.stderr) > 0:
        print(decoded, file=sys.stderr)
        return False
    if (
        not result_line.startswith("0 errors, 0 warnings, 0 notes")
        or len(output.stderr) > 0
    ):
        print(decoded, file=sys.stderr)
    num_errors = result_line.split(" errors,")[0]
    return num_errors == "0"
