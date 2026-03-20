from ..assertion_utils import (
    assert_parse,
    show_token,
    assert_token,
    assert_transform,
    assert_parse_error_recovery,
    Range,
    Pos,
    with_parser_verbose,
)

import_code = """
import module
"""
import_result = """
import module
"""


def test_stmt_import():
    assert_parse(import_code, import_result)


import_as_code = """
import module as m
"""
import_as_result = """
import module as m
"""


def test_stmt_import_as():
    assert_parse(import_as_code, import_as_result)


import_multi_code = """
import a as b, c.d as e
"""
import_multi_result = """
import a as b, c.d as e
"""


def test_stmt_import_multi():
    assert_parse(import_multi_code, import_multi_result)


from_import_code = """
from os import path
"""
from_import_result = """
from os import path
"""


def test_stmt_from_import():
    assert_parse(from_import_code, from_import_result)


from_import_relative_code = """
from . import core
"""
from_import_relative_result = """
from . import core
"""


def test_stmt_from_import_relative():
    assert_parse(from_import_relative_code, from_import_relative_result)


from_import_relative_code_ellipsis = """
from ... import core
"""
from_import_relative_result_ellipsis = """
from ... import core
"""


def test_stmt_from_import_relative_ellipsis():
    assert_parse(
        from_import_relative_code_ellipsis, from_import_relative_result_ellipsis
    )


import_dot_missing_name_code = """
import a.
"""
import_dot_missing_name_recover = """
import a
"""


def test_stmt_import_dot_missing_name():
    assert_parse_error_recovery(
        import_dot_missing_name_code,
        import_dot_missing_name_recover,
        [
            ("expected name after '.'", Range(Pos(1, 7), Pos(1, 10))),
        ],
    )


import_alias_missing_name_code = """
import a as
"""
import_alias_missing_name_recover = """
import a
"""


def test_stmt_import_alias_missing_name():
    assert_parse_error_recovery(
        import_alias_missing_name_code,
        import_alias_missing_name_recover,
        [
            ("expected name after 'as'", Range(Pos(1, 9), Pos(1, 11))),
        ],
    )


from_import_dot_missing_name_code = """
from a. import b
"""
from_import_dot_missing_name_recover = """
from a import b
"""


def test_stmt_from_import_dot_missing_name():
    assert_parse_error_recovery(
        from_import_dot_missing_name_code,
        from_import_dot_missing_name_recover,
        [
            ("expected name after '.'", Range(Pos(1, 5), Pos(1, 8))),
        ],
    )


from_import_alias_missing_name_code = """
from a import b as
"""
from_import_alias_missing_name_recover = """
from a import b
"""


def test_stmt_from_import_alias_missing_name():
    assert_parse_error_recovery(
        from_import_alias_missing_name_code,
        from_import_alias_missing_name_recover,
        [
            ("expected name after 'as'", Range(Pos(1, 16), Pos(1, 18))),
        ],
    )
