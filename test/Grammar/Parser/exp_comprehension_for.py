from ..assertion_utils import (
    assert_ast_equals,
    assert_transform_equals,
    assert_typh_code_match_unparse,
)


comp_gen_code = """
let gen = (for (let i in range(100000000))
                for (let i in range(i)) if (i % 2 == 1)
                    yield i * i);
"""
comp_gen_result = """
gen = (i * i for i in range(100000000) for i in range(i) if i % 2 == 1)
"""
comp_gen_transformed = """
gen = (_typh_cn_m0_1_i * _typh_cn_m0_1_i for _typh_cn_m0_0_i in range(100000000) for _typh_cn_m0_1_i in range(_typh_cn_m0_0_i) if _typh_cn_m0_1_i % 2 == 1)
"""


def test_comp_gen():
    parsed = assert_ast_equals(comp_gen_code, comp_gen_result)
    assert_transform_equals(parsed, comp_gen_transformed)
    assert_typh_code_match_unparse(comp_gen_code)


comp_list_code = """
let odd_sq = [for (let i in range(10)) if (i % 2 == 1) yield i * i];
"""
comp_list_result = """
odd_sq = [i * i for i in range(10) if i % 2 == 1]
"""
comp_list_transformed = """
odd_sq = [_typh_cn_m0_0_i * _typh_cn_m0_0_i for _typh_cn_m0_0_i in range(10) if _typh_cn_m0_0_i % 2 == 1]
"""


def test_comp_list():
    parsed = assert_ast_equals(comp_list_code, comp_list_result)
    assert_transform_equals(parsed, comp_list_transformed)
    assert_typh_code_match_unparse(comp_list_code)


comp_list_annotated_code = """
let odd_sq = [for (let i: int in range(10)) if (i % 2 == 1) yield i * i];
"""
comp_list_annotated_result = """
odd_sq = [i * i for i in range(10) if i % 2 == 1]
"""
comp_list_annotated_transformed = """
_typh_cn_m0_0_i: int
odd_sq = [_typh_cn_m0_0_i * _typh_cn_m0_0_i for _typh_cn_m0_0_i in range(10) if _typh_cn_m0_0_i % 2 == 1]
"""


def test_comp_list_annotated():
    parsed = assert_ast_equals(comp_list_annotated_code, comp_list_annotated_result)
    assert_transform_equals(parsed, comp_list_annotated_transformed)
    assert_typh_code_match_unparse(comp_list_annotated_code)


comp_set_code = """
let mul_odd = {
    for (let i in range(10)) if (i % 2 == 1)
            for (let j in range(10)) if (j % 2 == 1)
                yield i * j
};
"""
comp_set_result = """
mul_odd = {i * j for i in range(10) if i % 2 == 1 for j in range(10) if j % 2 == 1}
"""
comp_set_transformed = """
mul_odd = {_typh_cn_m0_0_i * _typh_cn_m0_1_j for _typh_cn_m0_0_i in range(10) if _typh_cn_m0_0_i % 2 == 1 for _typh_cn_m0_1_j in range(10) if _typh_cn_m0_1_j % 2 == 1}
"""


def test_comp_set():
    parsed = assert_ast_equals(comp_set_code, comp_set_result)
    assert_transform_equals(parsed, comp_set_transformed)
    assert_typh_code_match_unparse(comp_set_code)


comp_set_annotated_code = """
let mul_odd = {
    for (let i: int in range(10)) if (i % 2 == 1)
            for (let j: int in range(10)) if (j % 2 == 1)
                yield i * j
};
"""
comp_set_annotated_result = """
mul_odd = {i * j for i in range(10) if i % 2 == 1 for j in range(10) if j % 2 == 1}
"""
comp_set_annotated_transformed = """
_typh_cn_m0_0_i: int
_typh_cn_m0_1_j: int
mul_odd = {_typh_cn_m0_0_i * _typh_cn_m0_1_j for _typh_cn_m0_0_i in range(10) if _typh_cn_m0_0_i % 2 == 1 for _typh_cn_m0_1_j in range(10) if _typh_cn_m0_1_j % 2 == 1}
"""


def test_comp_set_annotated():
    parsed = assert_ast_equals(comp_set_annotated_code, comp_set_annotated_result)
    assert_transform_equals(parsed, comp_set_annotated_transformed)
    assert_typh_code_match_unparse(comp_set_annotated_code)


comp_dict_code = """
let square_dict = {
    for (let i in range(10)) if (i % 2 == 1)
        yield i: i * i
};
"""
comp_dict_result = """
square_dict = {i: i * i for i in range(10) if i % 2 == 1}
"""
comp_dict_transformed = """
square_dict = {_typh_cn_m0_0_i: _typh_cn_m0_0_i * _typh_cn_m0_0_i for _typh_cn_m0_0_i in range(10) if _typh_cn_m0_0_i % 2 == 1}
"""


def test_comp_dict():
    parsed = assert_ast_equals(comp_dict_code, comp_dict_result)
    assert_transform_equals(parsed, comp_dict_transformed)
    assert_typh_code_match_unparse(comp_dict_code)


comp_gen_noinline_code = """
def comp_gen_noinline() {
    let gen = (for (let i in range(100000000))
                    for (let i in range(i)) if (i % 2 == 1)
                        yield (x: int) => x * i)
    return gen
}
"""
comp_gen_noinline_result = """
def comp_gen_noinline():
    gen = __genexp_control
    return gen
"""
comp_gen_noinline_transformed = """
def comp_gen_noinline():

    def _typh_cc_f1_0():
        for i in range(100000000):
            for _typh_cn_f2_1_i in range(i):
                if _typh_cn_f2_1_i % 2 == 1:

                    def _typh_fn_f2_0(x: int):
                        return x * _typh_cn_f2_1_i
                    yield _typh_fn_f2_0
    gen = _typh_cc_f1_0()
    return gen
"""


def test_comp_gen_noinline():
    parsed = assert_ast_equals(comp_gen_noinline_code, comp_gen_noinline_result)
    assert_transform_equals(parsed, comp_gen_noinline_transformed)
    assert_typh_code_match_unparse(comp_gen_noinline_code)


comp_list_noinline_code = """
def comp_list_noinline() {
    let odd_sq = [for (let i in range(10)) if (i % 2 == 1) yield (x: int) => x * i]
    return odd_sq
}
"""
comp_list_noinline_result = """
def comp_list_noinline():
    odd_sq = [__listcomp_temp for __listcomp_temp in __genexp_control]
    return odd_sq
"""
comp_list_noinline_transformed = """
def comp_list_noinline():

    def _typh_cc_f1_0():
        for i in range(10):
            if i % 2 == 1:

                def _typh_fn_f2_0(x: int):
                    return x * i
                yield _typh_fn_f2_0
    odd_sq = [__listcomp_temp for __listcomp_temp in _typh_cc_f1_0()]
    return odd_sq
"""


def test_comp_list_noinline():
    parsed = assert_ast_equals(comp_list_noinline_code, comp_list_noinline_result)
    assert_transform_equals(parsed, comp_list_noinline_transformed)
    assert_typh_code_match_unparse(comp_list_noinline_code)


comp_dict_noinline_code = """
let square_dict = {
    for (let i in range(10)) if (i % 2 == 1)
        yield i: (x: int) => x * i
};
"""
comp_dict_noinline_result = """
square_dict = {__dictcomp_temp_key: __dictcomp_temp_val for __dictcomp_temp_key, __dictcomp_temp_val in __genexp_control}
"""
comp_dict_noinline_transformed = """
def _typh_cc_m0_0():
    for i in range(10):
        if i % 2 == 1:

            def _typh_fn_f1_0(x: int):
                return x * i
            yield (i, _typh_fn_f1_0)
square_dict = {_typh_cn_m0_1___dictcomp_temp_key: _typh_cn_m0_2___dictcomp_temp_val for _typh_cn_m0_1___dictcomp_temp_key, _typh_cn_m0_2___dictcomp_temp_val in _typh_cc_m0_0()}
"""


def test_comp_dict_noinline():
    parsed = assert_ast_equals(comp_dict_noinline_code, comp_dict_noinline_result)
    assert_transform_equals(parsed, comp_dict_noinline_transformed)
    assert_typh_code_match_unparse(comp_dict_noinline_code)
