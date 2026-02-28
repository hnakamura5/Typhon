import pytest
from Typhon.Driver.debugging import (
    set_debug_mode,
    set_debug_verbose,
)
from .Grammar.assertion_utils import set_parser_verbose


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add pytest command options."""
    # --debug is already used by pytest itself.
    parser.addoption(
        "--debug-verbose",
        action="store_true",
        default=False,
        help="Enable verbose debug mode for test runners and test code.",
    )
    parser.addoption(
        "--debug-parser",
        action="store_true",
        default=False,
        help="Enable debug mode for the parser.",
    )


@pytest.fixture(scope="session", autouse=True)
def debug_mode(request: pytest.FixtureRequest):
    """Fixture to set debug mode based on command line options."""
    if request.config.getoption("--debug-verbose"):
        set_debug_verbose(True)
    elif request.config.getoption("--debug-parser"):
        set_parser_verbose(True)
