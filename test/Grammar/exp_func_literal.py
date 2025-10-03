from ..assertion_utils import assert_ast_equals, show_token, assert_transform_equals

func_literal_exp_code = """
let f = (x) => x + 1;
"""
func_literal_exp_result = """
f = __function_literal
"""
func_literal_exp_transformed = """
def _typh_fn_m0_0(x):
    return x + 1
f = _typh_fn_m0_0
"""


def test_exp_func_literal_exp():
    parsed = assert_ast_equals(func_literal_exp_code, func_literal_exp_result)
    assert_transform_equals(parsed, func_literal_exp_transformed)


func_literal_exp_typed_code = """
let f = (x: int) -> int => x + 1;
"""
func_literal_exp_typed_result = """
f = __function_literal
"""
func_literal_exp_typed_transformed = """
def _typh_fn_m0_0(x: int) -> int:
    return x + 1
f = _typh_fn_m0_0
"""


def test_exp_func_literal_exp_typed():
    parsed = assert_ast_equals(
        func_literal_exp_typed_code, func_literal_exp_typed_result
    )
    assert_transform_equals(parsed, func_literal_exp_typed_transformed)


func_literal_block_code = """
(x) => {
    return x + 1;
};
"""
func_literal_block_result = """
__function_literal
"""
func_literal_block_transformed = """
def _typh_fn_m0_0(x):
    return x + 1
_typh_fn_m0_0
"""


def test_exp_func_literal_block_():
    parsed = assert_ast_equals(func_literal_block_code, func_literal_block_result)
    assert_transform_equals(parsed, func_literal_block_transformed)


func_literal_block_typed_code = """
let f = (x: int) -> int => {
    return x + 1;
};
"""
func_literal_block_typed_result = """
f = __function_literal
"""
func_literal_block_typed_transformed = """
def _typh_fn_m0_0(x: int) -> int:
    return x + 1
f = _typh_fn_m0_0
"""


def test_exp_func_literal_block_typed():
    parsed = assert_ast_equals(
        func_literal_block_typed_code, func_literal_block_typed_result
    )
    assert_transform_equals(parsed, func_literal_block_typed_transformed)


func_literal_nested_code = """
def test_exp_func_literal_nested() {
    let f = (x: int) -> (int) -> int => {
        if (x > 0) {
            return (x: int) -> int => {
                return x + 1;
            };
        } else {
            return (x: int) -> int => {
                return x - 1;
            };
        }
    };
    let g = (x: int) -> int => {
        return x * 2;
    };
}
"""
func_literal_nested_result = """
def test_exp_func_literal_nested():
    f = __function_literal
    g = __function_literal
"""
func_literal_nested_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_f2_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f2_0_a0: int, /) -> int:
        ...

def test_exp_func_literal_nested():

    def _typh_fn_f1_0(x: int) -> _typh_ar_f2_0:
        if x > 0:

            def _typh_fn_f2_0(x: int) -> int:
                return x + 1
            return _typh_fn_f2_0
        else:

            def _typh_fn_f2_1(x: int) -> int:
                return x - 1
            return _typh_fn_f2_1
    f = _typh_fn_f1_0

    def _typh_fn_f1_1(x: int) -> int:
        return x * 2
    g = _typh_fn_f1_1
"""


def test_exp_func_literal_nested():
    parsed = assert_ast_equals(func_literal_nested_code, func_literal_nested_result)
    assert_transform_equals(parsed, func_literal_nested_transformed)


placeholder_func_literal_code = """
def apply_func(f: (int, int) -> int, x: int) -> ((int) -> int) {
    return f(x, ...)
}
"""
placeholder_func_literal_result = """
def apply_func(f: __arrow_type, x: int) -> __arrow_type:
    return f(x, ...)
"""
placeholder_func_literal_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_f1_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_0_a0: int, _typh_ar_f1_0_a1: int, /) -> int:
        ...

class _typh_ar_f1_1(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_1_a0: int, /) -> int:
        ...

def apply_func(f: _typh_ar_f1_0, x: int) -> _typh_ar_f1_1:

    def _typh_fn_f1_1(_typh_ag_f1_0_1):
        return f(x, _typh_ag_f1_0_1)
    return _typh_fn_f1_1
"""


def test_exp_placeholder_func_literal():
    parsed = assert_ast_equals(
        placeholder_func_literal_code, placeholder_func_literal_result
    )
    assert_transform_equals(parsed, placeholder_func_literal_transformed)


placeholder_func_literal_code = """
def apply_func(f: (int, int, int, kw:int) -> int, x: int) -> ((int, int, int) -> int) {
    return f(..., x, ..., kw=...)
}
"""
placeholder_func_literal_result = """
def apply_func(f: __arrow_type, x: int) -> __arrow_type:
    return f(..., x, ..., kw=...)
"""
placeholder_func_literal_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_f1_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_0_a0: int, _typh_ar_f1_0_a1: int, _typh_ar_f1_0_a2: int, /, kw: int) -> int:
        ...

class _typh_ar_f1_1(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_1_a0: int, _typh_ar_f1_1_a1: int, _typh_ar_f1_1_a2: int, /) -> int:
        ...

def apply_func(f: _typh_ar_f1_0, x: int) -> _typh_ar_f1_1:

    def _typh_fn_f1_3(_typh_ag_f1_0_0, _typh_ag_f1_1_2, _typh_ag_f1_2_kw):
        return f(_typh_ag_f1_0_0, x, _typh_ag_f1_1_2, kw=_typh_ag_f1_2_kw)
    return _typh_fn_f1_3
"""


def test_exp_placeholder_func_literal_kw():
    parsed = assert_ast_equals(
        placeholder_func_literal_code, placeholder_func_literal_result
    )
    assert_transform_equals(parsed, placeholder_func_literal_transformed)
