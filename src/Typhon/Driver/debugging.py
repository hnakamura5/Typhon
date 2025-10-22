from .utils import copy_type

_debug = False
_debug_verbose = False


def set_debug_mode(debug: bool):
    global _debug
    _debug = debug


def set_debug_verbose(verbose: bool):
    global _debug_verbose
    _debug_verbose = verbose
    if verbose:
        set_debug_mode(True)


def is_debug_mode() -> bool:
    return _debug


def is_debug_verbose() -> bool:
    return _debug_verbose


@copy_type(print)
def debug_print(*arg, **kwargs) -> None:
    if _debug:
        print(*arg, **kwargs)


@copy_type(print)
def debug_verbose_print(*arg, **kwargs) -> None:
    if _debug_verbose:
        print(*arg, **kwargs)
