import sys
import subprocess


def build_grammar():
    output = subprocess.run(
        [
            sys.executable,
            "-m",
            "pegen",
            "src/Typhon/Grammar/typhon.gram",
            "-o",
            "src/Typhon/Grammar/parser.py",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if output.returncode != 0:
        print("Error building grammar:", output.stderr.decode())
        sys.exit(output.returncode)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "src/Typhon/Grammar/parser.py",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def type_check(source_file: str) -> bool:
    output = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyright",
            source_file,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if output.returncode != 0:
        print("Type check failed:", output.stderr.decode())
        return False
    print("Type check passed.", output.stdout.decode())
    return True


if __name__ == "__main__":
    build_grammar()
