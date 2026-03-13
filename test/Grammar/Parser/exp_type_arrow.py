from Typhon.Driver.debugging import set_debug_verbose
from ..assertion_utils import (
    assert_parse,
    show_token,
    assert_transform_ast,
    assert_typh_code_match_unparse,
)

type_arrow_annot_code = """
var x: (int) -> int;
"""
type_arrow_annot_result = """
x: __arrow_type
"""
type_arrow_annot_transformed = """
from typing import Protocol as _typh_bi_Protocol

class $func_type1(_typh_bi_Protocol):

    def __call__(self, $a0: int, /) -> int:
        ...
x: $func_type1
"""


def test_type_arrow_annot():
    parsed = assert_parse(type_arrow_annot_code, type_arrow_annot_result)
    assert_transform_ast(parsed, type_arrow_annot_transformed)
    assert_typh_code_match_unparse(type_arrow_annot_code)


type_arrow_param_annot_code = """
var a: (x: int, y: str) -> int;
"""
type_arrow_param_annot_result = """
a: __arrow_type
"""
type_arrow_param_annot_transformed = """
from typing import Protocol as _typh_bi_Protocol

class $func_type1(_typh_bi_Protocol):

    def __call__(self, x: int, y: str) -> int:
        ...
a: $func_type1
"""


def test_type_arrow_param_annot():
    parsed = assert_parse(type_arrow_param_annot_code, type_arrow_param_annot_result)
    assert_transform_ast(parsed, type_arrow_param_annot_transformed)
    assert_typh_code_match_unparse(type_arrow_param_annot_code)


type_arrow_def_param_code = """
def h(x: int, f: (int) -> int) -> int {
    return f(x);
}
"""
type_arrow_def_param_result = """
def h(x: int, f: __arrow_type) -> int:
    return f(x)
"""
type_arrow_def_param_transformed = """
from typing import Protocol as _typh_bi_Protocol

class $func_type2(_typh_bi_Protocol):

    def __call__(self, $a1: int, /) -> int:
        ...

def h(x: int, f: $func_type2) -> int:
    return f(x)
"""


def test_type_arrow_def_param():
    parsed = assert_parse(type_arrow_def_param_code, type_arrow_def_param_result)
    assert_transform_ast(parsed, type_arrow_def_param_transformed)


type_arrow_func_literal_code = """
var f: (x: int) -> int = (x:int) -> int => {
    return x + 1;
};
"""
type_arrow_func_literal_result = """
f: __arrow_type = __function_literal
"""
type_arrow_func_literal_transformed = """
from typing import Protocol as _typh_bi_Protocol

class $func_type3(_typh_bi_Protocol):

    def __call__(self, x: int) -> int:
        ...

def $anonymous1(x: int) -> int:
    return x + 1
f: $func_type3 = $anonymous1
"""


def test_type_arrow_func_literal():
    parsed = assert_parse(type_arrow_func_literal_code, type_arrow_func_literal_result)
    assert_transform_ast(parsed, type_arrow_func_literal_transformed)
    assert_typh_code_match_unparse(type_arrow_func_literal_code)


type_arrow_star_etc_code = """
var f: (float, x: int, *args: str, **kwds: int) -> int;
"""
type_arrow_star_etc_result = """
f: __arrow_type
"""
type_arrow_star_etc_transformed = """
from typing import Protocol as _typh_bi_Protocol

class $func_type1(_typh_bi_Protocol):

    def __call__(self, $a0: float, /, x: int, *args: str, **kwds: int) -> int:
        ...
f: $func_type1
"""


def test_type_arrow_star_etc():
    parsed = assert_parse(type_arrow_star_etc_code, type_arrow_star_etc_result)
    assert_transform_ast(parsed, type_arrow_star_etc_transformed)
    assert_typh_code_match_unparse(type_arrow_star_etc_code)


type_arrow_single_no_paren_code = """
var f: int -> int;
"""
type_arrow_single_no_paren_result = """
f: __arrow_type
"""
type_arrow_single_no_paren_transformed = """
from typing import Protocol as _typh_bi_Protocol

class $func_type1(_typh_bi_Protocol):

    def __call__(self, $a0: int, /) -> int:
        ...
f: $func_type1
"""


def test_type_arrow_single_no_paren():
    parsed = assert_parse(
        type_arrow_single_no_paren_code, type_arrow_single_no_paren_result
    )
    assert_transform_ast(parsed, type_arrow_single_no_paren_transformed)
    assert_typh_code_match_unparse(type_arrow_single_no_paren_code)


type_arrow_in_subscript_code = """
var x: list[int -> str];
"""
type_arrow_in_subscript_result = """
x: list[__arrow_type]
"""
type_arrow_in_subscript_transformed = """
from typing import Protocol as _typh_bi_Protocol

class $func_type1(_typh_bi_Protocol):

    def __call__(self, $a0: int, /) -> str:
        ...
x: list[$func_type1]
"""


def test_type_arrow_in_subscript():
    parsed = assert_parse(type_arrow_in_subscript_code, type_arrow_in_subscript_result)
    assert_transform_ast(parsed, type_arrow_in_subscript_transformed)
    assert_typh_code_match_unparse(type_arrow_in_subscript_code)


type_arrow_to_subscript_code = """
var x: list[int -> list[str -> float]];
"""
type_arrow_to_subscript_result = """
x: list[__arrow_type]
"""
type_arrow_to_subscript_transformed = """
from typing import Protocol as _typh_bi_Protocol

class $func_type1(_typh_bi_Protocol):

    def __call__(self, $a0: int, /) -> list[$func_type4]:
        ...

class $func_type4(_typh_bi_Protocol):

    def __call__(self, $a2: str, /) -> float:
        ...
x: list[$func_type1]
"""


def test_type_arrow_to_subscript():
    parsed = assert_parse(type_arrow_to_subscript_code, type_arrow_in_subscript_result)
    assert_transform_ast(parsed, type_arrow_to_subscript_transformed)
    assert_typh_code_match_unparse(type_arrow_to_subscript_code)


type_arrow_single_no_paren_chain_code = """
var f: int? -> [int] -> list[str -> float] -> (int -> int) -> (int, float) -> int?;
"""
type_arrow_single_no_paren_chain_result = """
f: __arrow_type
"""
type_arrow_single_no_paren_chain_transformed = """
from typing import Protocol as _typh_bi_Protocol

class $func_type1(_typh_bi_Protocol):

    def __call__(self, $a0_1: int | None, /) -> $func_type4:
        ...

class $func_type4(_typh_bi_Protocol):

    def __call__(self, $a0_2: list[int], /) -> $func_type5:
        ...

class $func_type5(_typh_bi_Protocol):

    def __call__(self, $a0_3: list[$func_type6], /) -> $func_type7:
        ...

class $func_type6(_typh_bi_Protocol):

    def __call__(self, $a0_4: str, /) -> float:
        ...

class $func_type7(_typh_bi_Protocol):

    def __call__(self, $a0_5: $func_type8, /) -> $func_type9:
        ...

class $func_type8(_typh_bi_Protocol):

    def __call__(self, $a0_6: int, /) -> int:
        ...

class $func_type9(_typh_bi_Protocol):

    def __call__(self, $a0_7: int, $a0_8: float, /) -> int | None:
        ...
f: $func_type1
"""


def test_type_arrow_single_no_paren_chain():
    parsed = assert_parse(
        type_arrow_single_no_paren_chain_code, type_arrow_single_no_paren_chain_result
    )
    assert_transform_ast(parsed, type_arrow_single_no_paren_chain_transformed)
    assert_typh_code_match_unparse(type_arrow_single_no_paren_chain_code)
