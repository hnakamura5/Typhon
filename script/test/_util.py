def except_debug_options(args: list[str]) -> list[str]:
    return [arg for arg in args if not arg.startswith("--debug-verbose")]


# Note "--debug" options is used by pytest itself. We cannot use here.
def get_debug_options(args: list[str]) -> list[str]:
    return [arg for arg in args if arg.startswith("--debug-verbose")]


def except_test_options(args: list[str]) -> list[str]:
    return except_debug_options(args)
