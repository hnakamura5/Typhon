# uv run -m script.grammar_test  *> .\private\test.log
# at project root

from .build import build_grammar, install_editable_package
from .grammar_test import run_all_tests as run_grammar_tests
from .run_test import run_all_tests as run_run_tests
from .lsp_test import run_all_tests as run_lsp_tests

if __name__ == "__main__":
    build_grammar()
    install_editable_package()
    exit(run_grammar_tests() + run_run_tests() + run_lsp_tests())
