from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from .._util import get_project_root


def _pick_wheel_file(dist_dir: Path) -> Path:
    wheel_files = sorted(
        dist_dir.glob("*.whl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    assert wheel_files, (
        f"No wheel files were found in {dist_dir}. Run `uv build` first."
    )
    return wheel_files[0]


def assert_create_venv(test_dir: Path, test_venv_dir: Path) -> Path:
    create_venv_command = ["uv", "venv", str(test_venv_dir)]
    create_venv_result = subprocess.run(
        create_venv_command,
        cwd=str(test_dir),
        capture_output=True,
        text=True,
    )
    assert create_venv_result.returncode == 0, (
        "Failed to create virtual environment.\n"
        f"stdout:\n{create_venv_result.stdout}\n"
        f"stderr:\n{create_venv_result.stderr}"
    )
    venv_python = test_venv_dir / "bin" / "python"
    venv_python_exe = test_venv_dir / "Scripts" / "python.exe"
    assert venv_python.exists() or venv_python_exe.exists(), (
        f"Python executable was not found in {test_venv_dir}"
    )
    return venv_python if venv_python.exists() else venv_python_exe


def assert_install_wheel(test_dir: Path, venv_python: Path, wheel_file: Path) -> None:
    install_command = [
        "uv",
        "pip",
        "install",
        "--python",
        str(venv_python),
        str(wheel_file),
    ]
    install_result = subprocess.run(
        install_command,
        cwd=str(test_dir),
        capture_output=True,
        text=True,
    )
    assert install_result.returncode == 0, (
        "Failed to install wheel file.\n"
        f"stdout:\n{install_result.stdout}\n"
        f"stderr:\n{install_result.stderr}"
    )


def assert_smoke_import(test_dir: Path, venv_python: Path) -> None:
    smoke_script = test_dir / "smoke_test.py"
    smoke_script.write_text(
        "import Typhon\n"
        "print('Typhon import path:', Typhon.__file__)\n"
        "print('Typhon wheel smoke test: OK')\n",
        encoding="utf-8",
    )
    smoke_command = [str(venv_python), str(smoke_script)]
    smoke_result = subprocess.run(
        smoke_command,
        cwd=str(test_dir),
        capture_output=True,
        text=True,
    )
    assert smoke_result.returncode == 0, (
        "Failed to run smoke test script.\n"
        f"stdout:\n{smoke_result.stdout}\n"
        f"stderr:\n{smoke_result.stderr}"
    )


def assert_binary_help(test_dir: Path, test_venv_dir: Path) -> None:
    typhon_command = test_venv_dir / "bin" / "typhon"
    typhon_exe_command = test_venv_dir / "Scripts" / "typhon.exe"
    has_typhon = typhon_command.exists()
    has_typhon_exe = typhon_exe_command.exists()
    assert has_typhon or has_typhon_exe, (
        "Install test failed: expected entrypoint at "
        f"{typhon_command} or {typhon_exe_command}"
    )
    if has_typhon:
        help_command = [str(typhon_command), "--help"]
    else:
        help_command = [str(typhon_exe_command), "--help"]

    help_result = subprocess.run(
        help_command,
        cwd=str(test_dir),
        capture_output=True,
        text=True,
    )
    assert help_result.returncode == 0, (
        "Failed to run typhon --help.\n"
        f"stdout:\n{help_result.stdout}\n"
        f"stderr:\n{help_result.stderr}"
    )


def run_install_test() -> int:
    project_root = Path(get_project_root())
    test_dir = (
        project_root
        / "test"
        / "Install"
        / "wheels"
        / f"wheel-{date.today().strftime('%Y%m%d')}"
    )
    test_venv_dir = test_dir / ".venv"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)
    python_version_file = project_root / ".python-version"
    if python_version_file.exists():
        shutil.copy2(python_version_file, test_dir / ".python-version")
    try:
        wheel_file = _pick_wheel_file(project_root / "dist")
        print(f"Install wheel file for testing: {wheel_file}")

        venv_python = assert_create_venv(test_dir, test_venv_dir)
        assert_install_wheel(test_dir, venv_python, wheel_file)
        assert_smoke_import(test_dir, venv_python)
        assert_binary_help(test_dir, test_venv_dir)

        print(f"Wheel install test passed: {wheel_file.name}")
        return 0
    except Exception as error:  # noqa: BLE001
        print(f"Wheel install test failed: {error}")
        return 1
    finally:
        if test_venv_dir.exists():
            subprocess.run(
                ["uv", "venv", "--clear", str(test_venv_dir)],
                cwd=str(test_dir),
                capture_output=True,
                text=True,
            )
        if test_dir.exists():
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(run_install_test())
