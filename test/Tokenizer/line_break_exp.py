from ..assertion_utils import show_token, assert_ast_equals, TokenizerAsserter
from tokenize import NAME, OP, NEWLINE, ENDMARKER, NUMBER

code_comp_exp_line_brk = """
let sq =
  [
  for (let
  i in
    range(
  10
  )
  )
    if (
    i
      %
      2 ==
      0)
      yield i
      *
      i
      ]
let sq_2 = sq
"""
result_comp_exp_line_brk = """
sq = [i * i for i in range(10) if i % 2 == 0]
sq_2 = sq
"""


def test_comp_exp_line_brk():
    show_token(code_comp_exp_line_brk)
    ta = TokenizerAsserter(code_comp_exp_line_brk)
    ta.next(NAME, "let")
    ta.next(NAME, "sq")
    ta.next(OP, "=")
    ta.next(OP, "[")
    ta.next(NAME, "for")
    ta.next(OP, "(")
    ta.next(NAME, "let")
    ta.next(NAME, "i")
    ta.next(NAME, "in")
    ta.next(NAME, "range")
    ta.next(OP, "(")
    ta.next(NUMBER, "10")
    ta.next(OP, ")")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n")  # Ignored NEWLINE after ')' of for
    ta.next(NAME, "if")
    ta.next(OP, "(")
    ta.next(NAME, "i")
    ta.next(OP, "%")
    ta.next(NUMBER, "2")
    ta.next(OP, "==")
    ta.next(NUMBER, "0")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n")  # Ignored NEWLINE after ')' of if
    ta.next(NAME, "yield")
    ta.next(NAME, "i")
    ta.next(OP, "*")
    ta.next(NAME, "i")
    ta.next(OP, "]")
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "let")
    ta.next(NAME, "sq_2")
    ta.next(OP, "=")
    ta.next(NAME, "sq")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")

    assert_ast_equals(code_comp_exp_line_brk, result_comp_exp_line_brk)


code_comp_dict_line_brk = """
let sq = {
    for (
    let
      i
        in
    range(10)
    )
      if (
      i % 2 ==
        1
      )
        yield i:
          i * i
}
"""

result_comp_dict_line_brk = """
sq = {i: i * i for i in range(10) if i % 2 == 1}
"""


def test_comp_dict_line_brk():
    show_token(code_comp_dict_line_brk)
    ta = TokenizerAsserter(code_comp_dict_line_brk)
    ta.next(NAME, "let")
    ta.next(NAME, "sq")
    ta.next(OP, "=")
    ta.next(OP, "{")
    ta.next(NAME, "for")
    ta.next(OP, "(")
    ta.next(NAME, "let")
    ta.next(NAME, "i")
    ta.next(NAME, "in")
    ta.next(NAME, "range")
    ta.next(OP, "(")
    ta.next(NUMBER, "10")
    ta.next(OP, ")")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n")  # Ignored NEWLINE after ')' of for
    ta.next(NAME, "if")
    ta.next(OP, "(")
    ta.next(NAME, "i")
    ta.next(OP, "%")
    ta.next(NUMBER, "2")
    ta.next(OP, "==")
    ta.next(NUMBER, "1")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n")  # Ignored NEWLINE after ')' of if
    ta.next(NAME, "yield")
    ta.next(NAME, "i")
    ta.next(OP, ":")
    ta.next(NAME, "i")
    ta.next(OP, "*")
    ta.next(NAME, "i")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")

    assert_ast_equals(code_comp_dict_line_brk, result_comp_dict_line_brk)
