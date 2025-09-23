from ..assertion_utils import assert_ast_equals, show_token, assert_transform_equals

type_arrow_annot_code = """
let x: (int) -> int;
"""
type_arrow_annot_result = """
x: __arrow_type
"""
type_arrow_annot_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_m0_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_0_a0: int, /) -> int:
        ...
x: _typh_ar_m0_0
"""


def test_type_arrow_annot():
    parsed = assert_ast_equals(type_arrow_annot_code, type_arrow_annot_result)
    assert_transform_equals(parsed, type_arrow_annot_transformed)


type_arrow_param_annot_code = """
let a: (x: int, y: str) -> int;
"""
type_arrow_param_annot_result = """
a: __arrow_type
"""
type_arrow_param_annot_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_m0_0(_typh_bi_Protocol):

    def __call__(self, x: int, y: str) -> int:
        ...
a: _typh_ar_m0_0
"""


def test_type_arrow_param_annot():
    parsed = assert_ast_equals(
        type_arrow_param_annot_code, type_arrow_param_annot_result
    )
    assert_transform_equals(parsed, type_arrow_param_annot_transformed)


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

class _typh_ar_f1_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_0_a0: int, /) -> int:
        ...

def h(x: int, f: _typh_ar_f1_0) -> int:
    return f(x)
"""


def test_type_arrow_def_param():
    parsed = assert_ast_equals(type_arrow_def_param_code, type_arrow_def_param_result)
    assert_transform_equals(parsed, type_arrow_def_param_transformed)


type_arrow_func_literal_code = """
let f: (x: int) -> int = (x:int) -> int => {
    return x + 1;
};
"""
type_arrow_func_literal_result = """
f: __arrow_type = __function_literal
"""
type_arrow_func_literal_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_m0_0(_typh_bi_Protocol):

    def __call__(self, x: int) -> int:
        ...

def _typh_fn_m0_0(x: int) -> int:
    return x + 1
f: _typh_ar_m0_0 = _typh_fn_m0_0
"""


def test_type_arrow_func_literal():
    parsed = assert_ast_equals(
        type_arrow_func_literal_code, type_arrow_func_literal_result
    )
    assert_transform_equals(parsed, type_arrow_func_literal_transformed)


type_arrow_star_etc_code = """
let f: (float, x: int, *args: str, **kwds: int) -> int;
"""
type_arrow_star_etc_result = """
f: __arrow_type
"""
type_arrow_star_etc_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_m0_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_0_a0: float, /, x: int, *args: str, **kwds: int) -> int:
        ...
f: _typh_ar_m0_0
"""


def test_type_arrow_star_etc():
    parsed = assert_ast_equals(type_arrow_star_etc_code, type_arrow_star_etc_result)
    assert_transform_equals(parsed, type_arrow_star_etc_transformed)
