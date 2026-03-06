# pyright: reportPrivateUsage=false
# Patch to pegen.parser to replace memoize, memoize_left_rec decorators implementation because of performance issues.

from typing import Any, cast, Callable, Optional
from pegen.parser import T, P, F
import pegen.parser as pegen_parser


# TODO: Monkey patching for memo of parser to optimize
def memoize(method: F) -> F:
    """Memoize a symbol method."""
    method_name = method.__name__

    def memoize_wrapper(self: Any, *args: object) -> Any:
        mark = self._mark()
        key = mark, method_name, args
        # Fast path: cache hit, and not verbose.
        key_in_cache = key in self._cache
        if key_in_cache and not self._verbose:
            tree, endmark = self._cache[key]
            self._reset(endmark)
            return tree
        # Slow path: no cache hit, or verbose.
        verbose = self._verbose
        argsr = ""
        fill = ""
        if verbose:  # Optimized
            argsr = ",".join(repr(arg) for arg in args)
            fill = "  " * self._level
        if not key_in_cache:
            if verbose:
                print(
                    f"{fill}{method_name}({argsr}) ... (looking at {self.showpeek()})"
                )
            self._level += 1
            tree = method(self, *args)
            self._level -= 1
            if verbose:
                print(f"{fill}... {method_name}({argsr}) -> {tree!s:.200}")
            endmark = self._mark()
            self._cache[key] = tree, endmark
        else:
            tree, endmark = self._cache[key]
            if verbose:
                print(f"{fill}{method_name}({argsr}) -> {tree!s:.200}")
            self._reset(endmark)
        return tree

    memoize_wrapper.__wrapped__ = method  # type: ignore
    return cast(F, memoize_wrapper)


def memoize_left_rec(method: Callable[[P], Optional[T]]) -> Callable[[P], Optional[T]]:
    """Memoize a left-recursive symbol method."""
    method_name = method.__name__

    def memoize_left_rec_wrapper(self: Any) -> Optional[T]:
        mark = self._mark()
        key = mark, method_name, ()
        # Fast path: cache hit, and not verbose.
        key_in_cache = key in self._cache
        if key_in_cache and not self._verbose:
            tree, endmark = self._cache[key]
            self._reset(endmark)
            return tree
        # Slow path: no cache hit, or verbose.
        verbose = self._verbose
        fill = ""
        if verbose:
            fill = "  " * self._level
        if not key_in_cache:
            if verbose:
                print(f"{fill}{method_name} ... (looking at {self.showpeek()})")
            self._level += 1

            # For left-recursive rules we manipulate the cache and
            # loop until the rule shows no progress, then pick the
            # previous result.  For an explanation why this works, see
            # https://github.com/PhilippeSigaud/Pegged/wiki/Left-Recursion
            # (But we use the memoization cache instead of a static
            # variable; perhaps this is similar to a paper by Warth et al.
            # (http://web.cs.ucla.edu/~todd/research/pub.php?id=pepm08).

            # Prime the cache with a failure.
            self._cache[key] = None, mark
            lastresult, lastmark = None, mark
            depth = 0
            if verbose:
                print(f"{fill}Recursive {method_name} at {mark} depth {depth}")

            while True:
                self._reset(mark)
                self.in_recursive_rule += 1
                try:
                    result = method(self)
                finally:
                    self.in_recursive_rule -= 1
                endmark = self._mark()
                depth += 1
                if verbose:
                    print(
                        f"{fill}Recursive {method_name} at {mark} depth {depth}: {result!s:.200} to {endmark}"
                    )
                if not result:
                    if verbose:
                        print(f"{fill}Fail with {lastresult!s:.200} to {lastmark}")
                    break
                if endmark <= lastmark:
                    if verbose:
                        print(f"{fill}Bailing with {lastresult!s:.200} to {lastmark}")
                    break
                self._cache[key] = lastresult, lastmark = result, endmark

            self._reset(lastmark)
            tree = lastresult

            self._level -= 1
            if verbose:
                print(f"{fill}{method_name}() -> {tree!s:.200} [cached]")
            if tree:
                endmark = self._mark()
            else:
                endmark = mark
                self._reset(endmark)
            self._cache[key] = tree, endmark
        else:
            tree, endmark = self._cache[key]
            if verbose:
                print(f"{fill}{method_name}() -> {tree!s:.200} [fresh]")
            if tree:
                self._reset(endmark)
        return tree

    memoize_left_rec_wrapper.__wrapped__ = method  # type: ignore
    return memoize_left_rec_wrapper


# Re decorate the base methods of pegen.parser.Parser with our memoization decorators.
def redecorate_pegen_parser_base_methods() -> None:
    parser_cls = pegen_parser.Parser
    for name, attr in list(parser_cls.__dict__.items()):
        if name == "start" or not callable(attr):
            continue
        wrapped = getattr(attr, "__wrapped__", None)
        if wrapped is None:
            continue
        if getattr(attr, "__typhon_patched__", False):
            continue
        patched = pegen_parser.memoize(wrapped)
        setattr(patched, "__typhon_patched__", True)
        setattr(parser_cls, name, patched)
