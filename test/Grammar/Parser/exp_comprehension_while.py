from ..assertion_utils import (
    assert_parse,
    assert_transform_ast,
    assert_typh_code_match_unparse,
)


code_while_comp = """
var inf = (while (True) yield 1);
"""
result_while_comp = """
inf = __while_comp
"""
transformed_while_comp = """
def $anonymous1():
    while True:
        yield 1
inf = $anonymous1()
"""


def test_while_comp():
    parsed = assert_parse(code_while_comp, result_while_comp)
    assert_transform_ast(parsed, transformed_while_comp)
    assert_typh_code_match_unparse(code_while_comp)


code_while_let_comp = """
var parsed = (with (let f = open("file.txt"))
                (while (let [x, y] = f.readline().split())
                    yield (x, y)))
"""
result_while_let_comp = """
parsed = __with_control
"""
transformed_while_let_comp = """
from typing import Final as _typh_bi_Final

def $anonymous1():
    with open('file.txt') as f:
        f: _typh_bi_Final

        def $anonymous2():
            $anonymous3 = True
            while $anonymous3:
                $anonymous3 = False
                match f.readline().split():
                    case [x, y]:
                        x: _typh_bi_Final
                        y: _typh_bi_Final
                        yield (x, y)
                        $anonymous3 = True
                    case _:
                        pass
        return $anonymous2()
parsed = $anonymous1()
"""


def test_while_let_comp():
    parsed = assert_parse(code_while_let_comp, result_while_let_comp)
    assert_transform_ast(parsed, transformed_while_let_comp)
    assert_typh_code_match_unparse(code_while_let_comp)
