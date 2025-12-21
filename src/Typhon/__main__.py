import sys
import fire
from .Driver.translate import translate, tr
from .Driver.debugging import (
    set_debug_mode,
    set_debug_verbose,
    set_debug_first_error,
    set_debug_log_file,
)
from .Driver.run import run
from .Driver.type_check import type_check
from .Driver.language_server import language_server


def _setup_debug_mode():
    if "--debug" in sys.argv:
        set_debug_mode(True)
        sys.argv.remove("--debug")
    if "--debug-verbose" in sys.argv:
        set_debug_mode(True)
        set_debug_verbose(True)
        sys.argv.remove("--debug-verbose")
    if "--debug-first-error" in sys.argv:
        set_debug_mode(True)
        set_debug_first_error(True)
        sys.argv.remove("--debug-first-error")
    if "--debug-log-file" in sys.argv:
        index = sys.argv.index("--debug-log-file")
        if index + 1 < len(sys.argv):
            log_file = sys.argv[index + 1]
            set_debug_log_file(log_file)
            sys.argv.pop(index)  # Remove --debug-log-file
            sys.argv.pop(index)  # Remove log file path


def main():
    try:
        _setup_debug_mode()
        fire.Fire(
            {
                "translate": translate,
                "tr": tr,
                "run": run,
                "type_check": type_check,
                "lsp": language_server,
            },
            name="typhon",
        )
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
