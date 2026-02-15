from typing import Callable, cast


def shorthand[T](
    normal_name: str,
    normal: T | None,
    shorthand_name: str,
    shorthand: T | None,
    default: T | None = None,
) -> T:
    if normal is not None and shorthand is not None:
        raise ValueError(
            f"Cannot provide both {normal_name} and {shorthand_name}(shorthand) arguments."
        )
    if normal is None:
        if shorthand is None:
            if default is None:
                raise ValueError(
                    f"At least one of {normal_name} or {shorthand_name}(shorthand) must be provided."
                )
            return default
        return shorthand
    return normal


def copy_type[**P, T](
    _: Callable[P, T],
) -> Callable[[Callable[..., T]], Callable[P, T]]:
    def decorator(f: Callable[..., T]) -> Callable[P, T]:
        return cast(Callable[P, T], f)

    return decorator
