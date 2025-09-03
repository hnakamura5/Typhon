from ..assertion_utils import assert_ast_transform, assert_transform_error
from ...src.Grammar.syntax_errors import ScopeError

# Symbol in block must not exported to outer scope through top-level.
block_module_rename_code = """
def f(x) {
    print(x);
}
if (True) {
    let x = 10;
    def g() {
        f(x);
    }
    g();
}
let y = 20;
"""
block_module_rename_result = """
def f(x):
    print(x)
if True:
    _typh_cn_m0_0_x = 10

    def _typh_df_f2_0_g():
        f(_typh_cn_m0_0_x)
    _typh_df_f2_0_g()
y = 20
"""


def test_block_module_rename():
    assert_ast_transform(block_module_rename_code, block_module_rename_result)


block_module_import_code = """
import math as mt;
print(mt.pi);
if (True) {
    import math;
    print(math.pi);
}
if (True) {
    from math import pi;
    print(pi);
}
if (False) {
    import contextlib as mt;
    print(mt.pi);
}
if (False) {
    import mt;
    print(mt.pi);
}

"""
block_module_import_result = """
import math as mt
print(mt.pi)
if True:
    import math as _typh_im_m0_0_math
    print(_typh_im_m0_0_math.pi)
if True:
    from math import pi as _typh_im_m0_1_pi
    print(_typh_im_m0_1_pi)
if False:
    import contextlib as _typh_im_m0_2_mt
    print(_typh_im_m0_2_mt.pi)
if False:
    import mt as _typh_im_m0_3_mt
    print(_typh_im_m0_3_mt.pi)
"""


def test_block_module_import():
    assert_ast_transform(block_module_import_code, block_module_import_result)
