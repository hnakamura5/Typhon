import ast
from Typhon.Transform._utils.jump_away import is_body_jump_away
from ..assertion_utils import get_code_source_ast, assert_ast_type
from typing import Any


def assert_body_jump_away(body: list[ast.stmt], jump_away: bool):
    assert is_body_jump_away(body) == jump_away


def assert_func_body_jump_away(func: Any, jump_away: bool):
    func_def = get_code_source_ast(func)
    assert_body_jump_away(func_def.body, jump_away)


def test_simple_return():
    def simple_return() -> int:
        return 42

    assert_func_body_jump_away(simple_return, True)


def test_simple_raise():
    def simple_raise() -> int:
        raise ValueError("Error")

    assert_func_body_jump_away(simple_raise, True)


def test_if_return():
    def if_return(x: int) -> int:
        if x > 0:
            return x
        else:
            return -x

    assert_func_body_jump_away(if_return, True)


def test_if_nested_return():
    def if_nested_return(x: int) -> int:
        if x > 0:
            if x < 10:
                return x
            else:
                return 10
        else:
            return -x

    assert_func_body_jump_away(if_nested_return, True)


def test_if_return_partial():
    def if_return_partial(x: int) -> int | None:
        if x > 0:
            return x

    assert_func_body_jump_away(if_return_partial, False)


def test_if_else_no_return():
    def if_else_no_return(x: int) -> int | None:
        if x > 0:
            return x
        else:
            print("No return here")

    assert_func_body_jump_away(if_else_no_return, False)


def test_if_no_return():
    def if_no_return(x: int) -> int | None:
        if x > 0:
            print("No return in else")
        else:
            return -x

    assert_func_body_jump_away(if_no_return, False)


def test_for():
    def for_loop(x: int) -> int:
        for i in range(x):
            return i
        return -1

    assert_func_body_jump_away(for_loop, True)


def test_for_not():
    def for_loop_not(x: int) -> int | None:
        for i in range(x):
            return None

    assert_func_body_jump_away(for_loop_not, False)


def test_for_break():
    def for_loop_break(x: int) -> int | None:
        for i in range(x):
            if i == 5:
                break
            return i

    assert_func_body_jump_away(for_loop_break, False)


def test_for_continue():
    def for_loop_continue(x: int) -> int | None:
        for i in range(x):
            if i == 5:
                continue
            else:
                return i

    assert_func_body_jump_away(for_loop_continue, False)


def test_for_else():
    def for_loop_else(x: int) -> int | None:
        for i in range(x):
            print(i)
        else:
            return -1

    assert_func_body_jump_away(for_loop_else, True)


def test_while():
    def while_loop(x: int) -> int:
        while x > 0:
            return x
        return 0

    assert_func_body_jump_away(while_loop, True)


def test_while_not():
    def while_loop_not(x: int) -> int | None:
        while x > 0:
            return None

    assert_func_body_jump_away(while_loop_not, False)


def test_while_break():
    def while_loop_break(x: int) -> int | None:
        while x > 0:
            if x == 5:
                break
            return x

    assert_func_body_jump_away(while_loop_break, False)


def test_while_continue():
    def while_loop_continue(x: int) -> int | None:
        while x > 0:
            if x == 5:
                continue
            else:
                return x

    assert_func_body_jump_away(while_loop_continue, False)


def test_while_else():
    def while_loop_else(x: int) -> int | None:
        while x > 0:
            x -= 1
        else:
            return 0

    assert_func_body_jump_away(while_loop_else, True)


def test_try_finally():
    def try_finally(x: int) -> int:
        try:
            return x
        finally:
            print("Finally block")

    assert_func_body_jump_away(try_finally, True)


def test_try_except():
    def try_except(x: int) -> int | None:
        try:
            return x
        except ValueError:
            return None
        except Exception:
            return -1

    assert_func_body_jump_away(try_except, True)


def test_try_no_return():
    def try_no_return(x: int) -> int | None:
        try:
            return x
        except ValueError:
            print("No return here")

    assert_func_body_jump_away(try_no_return, False)


def test_try_except_no_return():
    def try_except_no_return(x: int) -> int | None:
        try:
            return x
        except ValueError:
            print("No return here")

    assert_func_body_jump_away(try_except_no_return, False)


def test_with():
    def with_stmt(x: int) -> int:
        with open("file.txt", "r") as f:
            return x

    assert_func_body_jump_away(with_stmt, True)


def test_with_no_return():
    def with_stmt_no_return(x: int) -> int | None:
        with open("file.txt", "r") as f:
            print(x)

    assert_func_body_jump_away(with_stmt_no_return, False)


def test_match():
    def match_stmt(x: int) -> int:
        match x:
            case 1:
                return 1
            case 2:
                return 2
            case _:
                return -1

    assert_func_body_jump_away(match_stmt, True)


def test_match_no_return():
    def match_stmt_no_return(x: int) -> int | None:
        match x:
            case 1:
                return 1
            case 2:
                print("No return here")
            case _:
                return -1

    assert_func_body_jump_away(match_stmt_no_return, False)


def test_match_partial_return():
    def match_stmt_partial_return(x: int) -> int | None:
        match x:
            case 1:
                return 1
            case 2:
                return 2

    assert_func_body_jump_away(match_stmt_partial_return, False)


def test_match_irrefutable():
    def match_stmt_irrefutable(x: int) -> int:
        match x:
            case _:
                match x + 1:
                    case y:
                        match y - 1:
                            case _ as z:
                                return z

    assert_func_body_jump_away(match_stmt_irrefutable, True)


def test_match_guard_no_return():
    def match_stmt_guard_no_return(x: int) -> int | None:
        match x:
            case y if y > 0:
                return y

    assert_func_body_jump_away(match_stmt_guard_no_return, False)


def test_complex():
    def sequence_stmt(x: int) -> int:
        if x > 0:
            for i in range(x):
                match i:
                    case 0:
                        return 0
                    case _:
                        pass
            else:
                if x % 2 == 0:
                    return -1
                else:
                    raise ValueError("Error")
        else:
            while x < 0:
                return -x
            try:
                return x
            except ValueError:
                return -1
            finally:
                print("Done")

    assert_func_body_jump_away(sequence_stmt, True)


def test_break_outside_loop():
    def break_outside_loop(x: int) -> int | None:
        while x > 0:
            if x == 5:  # Extract only this if contains break
                print("Breaking")
                break

    assert_func_body_jump_away(break_outside_loop, False)
    func = get_code_source_ast(break_outside_loop)
    while_stmt = assert_ast_type(func.body[0], ast.While)
    if_stmt = assert_ast_type(while_stmt.body[0], ast.If)
    assert_body_jump_away(if_stmt.body, True)
