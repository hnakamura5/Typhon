import sys
import fire
from .Driver.translate import translate, tr
from .Driver.debugging import set_debug_mode
from .Driver.run import run
from .Driver.type_check import type_check


def _setup_debug_mode():
    if "--debug" in sys.argv:
        set_debug_mode(True)
        sys.argv.remove("--debug")
    if "--debug-verbose" in sys.argv:
        set_debug_mode(True)
        sys.argv.remove("--debug-verbose")


def main():
    try:
        _setup_debug_mode()
        fire.Fire(
            {
                "translate": translate,
                "tr": tr,
                "run": run,
                "type_check": type_check,
            },
            name="typhon",
        )
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
