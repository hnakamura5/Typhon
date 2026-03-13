from ..assertion_utils import (
    assert_parse,
    assert_transform_ast,
    assert_typh_code_match_unparse,
)


comp_gen_code = """
var gen = (for (var i in range(100000000))
                for (var i in range(i)) if (i % 2 == 1)
                    yield i * i);
"""
comp_gen_result = """
gen = (i * i for i in range(100000000) for i in range(i) if i % 2 == 1)
"""
comp_gen_transformed = """
gen = ($i1 * $i1 for $i in range(100000000) for $i1 in range($i) if $i1 % 2 == 1)
"""


def test_comp_gen():
    parsed = assert_parse(comp_gen_code, comp_gen_result)
    assert_transform_ast(parsed, comp_gen_transformed)
    assert_typh_code_match_unparse(comp_gen_code)


comp_list_code = """
var odd_sq = [for (var i in range(10)) if (i % 2 == 1) yield i * i];
"""
comp_list_result = """
odd_sq = [i * i for i in range(10) if i % 2 == 1]
"""
comp_list_transformed = """
odd_sq = [$i * $i for $i in range(10) if $i % 2 == 1]
"""


def test_comp_list():
    parsed = assert_parse(comp_list_code, comp_list_result)
    assert_transform_ast(parsed, comp_list_transformed)
    assert_typh_code_match_unparse(comp_list_code)


comp_list_annotated_code = """
var odd_sq = [for (var i: int in range(10)) if (i % 2 == 1) yield i * i];
"""
comp_list_annotated_result = """
odd_sq = [i * i for i in range(10) if i % 2 == 1]
"""
comp_list_annotated_transformed = """
$i: int
odd_sq = [$i * $i for $i in range(10) if $i % 2 == 1]
"""


def test_comp_list_annotated():
    parsed = assert_parse(comp_list_annotated_code, comp_list_annotated_result)
    assert_transform_ast(parsed, comp_list_annotated_transformed)
    assert_typh_code_match_unparse(comp_list_annotated_code)


comp_set_code = """
var mul_odd = {
    for (var i in range(10)) if (i % 2 == 1)
            for (var j in range(10)) if (j % 2 == 1)
                yield i * j
};
"""
comp_set_result = """
mul_odd = {i * j for i in range(10) if i % 2 == 1 for j in range(10) if j % 2 == 1}
"""
comp_set_transformed = """
mul_odd = {$i * $j for $i in range(10) if $i % 2 == 1 for $j in range(10) if $j % 2 == 1}
"""


def test_comp_set():
    parsed = assert_parse(comp_set_code, comp_set_result)
    assert_transform_ast(parsed, comp_set_transformed)
    assert_typh_code_match_unparse(comp_set_code)


comp_set_annotated_code = """
var mul_odd = {
    for (var i: int in range(10)) if (i % 2 == 1)
            for (var j: int in range(10)) if (j % 2 == 1)
                yield i * j
};
"""
comp_set_annotated_result = """
mul_odd = {i * j for i in range(10) if i % 2 == 1 for j in range(10) if j % 2 == 1}
"""
comp_set_annotated_transformed = """
$i: int
$j: int
mul_odd = {$i * $j for $i in range(10) if $i % 2 == 1 for $j in range(10) if $j % 2 == 1}
"""


def test_comp_set_annotated():
    parsed = assert_parse(comp_set_annotated_code, comp_set_annotated_result)
    assert_transform_ast(parsed, comp_set_annotated_transformed)
    assert_typh_code_match_unparse(comp_set_annotated_code)


comp_dict_code = """
var square_dict = {
    for (var i in range(10)) if (i % 2 == 1)
        yield i: i * i
};
"""
comp_dict_result = """
square_dict = {i: i * i for i in range(10) if i % 2 == 1}
"""
comp_dict_transformed = """
square_dict = {$i: $i * $i for $i in range(10) if $i % 2 == 1}
"""


def test_comp_dict():
    parsed = assert_parse(comp_dict_code, comp_dict_result)
    assert_transform_ast(parsed, comp_dict_transformed)
    assert_typh_code_match_unparse(comp_dict_code)


comp_gen_noinline_code = """
def comp_gen_noinline() {
    var gen = (for (var i in range(100000000))
                    for (var i in range(i)) if (i % 2 == 1)
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

    def $anonymous1():
        for i in range(100000000):
            for $i1 in range(i):
                if $i1 % 2 == 1:

                    def $anonymous2(x: int):
                        return x * $i1
                    yield $anonymous2
    gen = $anonymous1()
    return gen
"""


def test_comp_gen_noinline():
    parsed = assert_parse(comp_gen_noinline_code, comp_gen_noinline_result)
    assert_transform_ast(parsed, comp_gen_noinline_transformed)
    assert_typh_code_match_unparse(comp_gen_noinline_code)


comp_list_noinline_code = """
def comp_list_noinline() {
    var odd_sq = [for (var i in range(10)) if (i % 2 == 1) yield (x: int) => x * i]
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

    def $anonymous1():
        for i in range(10):
            if i % 2 == 1:

                def $anonymous2(x: int):
                    return x * i
                yield $anonymous2
    odd_sq = [__listcomp_temp for __listcomp_temp in $anonymous1()]
    return odd_sq
"""


def test_comp_list_noinline():
    parsed = assert_parse(comp_list_noinline_code, comp_list_noinline_result)
    assert_transform_ast(parsed, comp_list_noinline_transformed)
    assert_typh_code_match_unparse(comp_list_noinline_code)


comp_dict_noinline_code = """
var square_dict = {
    for (var i in range(10)) if (i % 2 == 1)
        yield i: (x: int) => x * i
};
"""
comp_dict_noinline_result = """
square_dict = {__dictcomp_temp_key: __dictcomp_temp_val for __dictcomp_temp_key, __dictcomp_temp_val in __genexp_control}
"""
comp_dict_noinline_transformed = """
def $anonymous1():
    for i in range(10):
        if i % 2 == 1:

            def $anonymous2(x: int):
                return x * i
            yield (i, $anonymous2)
square_dict = {$key: $val for $key, $val in $anonymous1()}
"""


def test_comp_dict_noinline():
    parsed = assert_parse(comp_dict_noinline_code, comp_dict_noinline_result)
    assert_transform_ast(parsed, comp_dict_noinline_transformed)
    assert_typh_code_match_unparse(comp_dict_noinline_code)
