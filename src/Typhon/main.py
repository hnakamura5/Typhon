import sys
from .Grammar.parser import parse_file
import ast


def input_check():
    if len(sys.argv) < 2:
        print("Usage: python main.py <input_file>")
        sys.exit(1)


def main():
    input_file = sys.argv[1]
    parsed = parse_file(input_file)
    print(f"Parsed file: {input_file}")
    print(ast.unparse(parsed))
    # ast.dump(parsed, indent=4)
    return 0


if __name__ == "__main__":
    input_check()
    result = main()
    sys.exit(result)
