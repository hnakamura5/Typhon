def is_test_option(arg: str) -> bool:
    return arg.startswith("--debug-") or arg == "--parallel"


def map_test_option(arg: str) -> list[str]:
    if arg == "--parallel":
        return ["-n", "auto"]
    return [arg]


def except_test_options(args: list[str]) -> list[str]:
    return [arg for arg in args if not is_test_option(arg)]


# Note "--debug" options is used by pytest itself. We cannot use here.
def get_test_options(args: list[str]) -> list[str]:
    return [
        option for arg in args if is_test_option(arg) for option in map_test_option(arg)
    ]
