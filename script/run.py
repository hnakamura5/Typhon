import subprocess
import sys
import pathlib
import os

PROJECT_ROOT = str(pathlib.Path(__file__).resolve().parent.parent)


def invoke_main():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "src.Typhon",
        ]
        + sys.argv[1:],
        env={"PYTHONPATH": PROJECT_ROOT, **dict(os.environ)},
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    invoke_main()
