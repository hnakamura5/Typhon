# uv run -m script.test.all *> .\private\test.log
# at project root

from ..build import setup
from .grammar import run_all_tests as run_grammar_tests
from .execute import run_all_tests as run_execute_tests
from .lsp import run_all_tests as run_lsp_tests


def test_all():
    setup()
    exit(run_grammar_tests() + run_execute_tests() + run_lsp_tests())


if __name__ == "__main__":
    test_all()
