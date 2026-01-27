from ..assertion_utils import (
    assert_parse,
)


match_call_code = """
import re
re.match(pattern="abc", string="abcdef")
"""
match_call_result = """
import re
re.match(pattern='abc', string='abcdef')
"""


def test_match_call():
    assert_parse(match_call_code, match_call_result)


case_call_code = """
def case(x: int) -> bool {
    return x == 1
}
result = case(5)
"""

case_call_result = """
def case(x: int) -> bool:
    return x == 1
result = case(5)
"""


def test_case_call():
    assert_parse(case_call_code, case_call_result)
