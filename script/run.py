import script.build as build
import subprocess
import sys


def invoke_main():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "src.main",
        ]
        + sys.argv[1:],
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py <input_file>")
        sys.exit(1)
    build.build_grammar()
    if not build.type_check(sys.argv[1]):
        print("Type checking failed. Exiting.")
        sys.exit(1)
    invoke_main()
