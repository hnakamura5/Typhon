from .utils import copy_type

_debug = False
_debug_verbose = False
_debug_first_error = False


def set_debug_mode(debug: bool):
    global _debug
    _debug = debug


def set_debug_verbose(verbose: bool):
    global _debug_verbose
    _debug_verbose = verbose
    if verbose:
        set_debug_mode(True)


def set_debug_first_error(first_error: bool):
    global _debug_first_error
    _debug_first_error = first_error


def is_debug_mode() -> bool:
    return _debug


def is_debug_verbose() -> bool:
    return _debug_verbose


# Whether to stop transformation at the first error encountered.
def is_debug_first_error() -> bool:
    return _debug_first_error


@copy_type(print)
def debug_print(*arg, **kwargs) -> None:
    if _debug:
        print(*arg, **kwargs)


@copy_type(print)
def debug_verbose_print(*arg, **kwargs) -> None:
    if _debug_verbose:
        print(*arg, **kwargs)
