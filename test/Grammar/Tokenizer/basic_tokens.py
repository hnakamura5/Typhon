from ..assertion_utils import show_token, assert_parse, TokenizerAsserter
from tokenize import NAME, OP, NEWLINE, ENDMARKER


# * (Bof)
# -* 2.0: NAME:'def'
# TokenInfo(type=1 (NAME), string='def', start=(2, 0), end=(2, 3), line='def func(x: int) -> None {\n')
# --* 2.4: NAME:'func'
# TokenInfo(type=1 (NAME), string='func', start=(2, 4), end=(2, 8), line='def func(x: int) -> None {\n')
# ---* 2.8: OP:'('
# TokenInfo(type=55 (OP), string='(', start=(2, 8), end=(2, 9), line='def func(x: int) -> None {\n')
# ----* 2.9: NAME:'x'
# TokenInfo(type=1 (NAME), string='x', start=(2, 9), end=(2, 10), line='def func(x: int) -> None {\n')
# -----* 2.10: OP:':'
# TokenInfo(type=55 (OP), string=':', start=(2, 10), end=(2, 11), line='def func(x: int) -> None {\n')
# ------* 2.12: NAME:'int'
# TokenInfo(type=1 (NAME), string='int', start=(2, 12), end=(2, 15), line='def func(x: int) -> None {\n')
# -------* 2.15: OP:')'
# TokenInfo(type=55 (OP), string=')', start=(2, 15), end=(2, 16), line='def func(x: int) -> None {\n')
# --------* 2.17: OP:'->'
# TokenInfo(type=55 (OP), string='->', start=(2, 17), end=(2, 19), line='def func(x: int) -> None {\n')
# ---------* 2.20: NAME:'None'
# TokenInfo(type=1 (NAME), string='None', start=(2, 20), end=(2, 24), line='def func(x: int) -> None {\n')
# ----------* 2.25: OP:'{'
# TokenInfo(type=55 (OP), string='{', start=(2, 25), end=(2, 26), line='def func(x: int) -> None {\n')
# -----------* 3.4: NAME:'let'
# TokenInfo(type=1 (NAME), string='let', start=(3, 4), end=(3, 7), line='    let y = x\n')
# ------------* 3.8: NAME:'y'
# TokenInfo(type=1 (NAME), string='y', start=(3, 8), end=(3, 9), line='    let y = x\n')
# -------------* 3.10: OP:'='
# TokenInfo(type=55 (OP), string='=', start=(3, 10), end=(3, 11), line='    let y = x\n')
# --------------* 3.12: NAME:'x'
# TokenInfo(type=1 (NAME), string='x', start=(3, 12), end=(3, 13), line='    let y = x\n')
# ---------------* 3.13: NEWLINE:'\n'
# TokenInfo(type=4 (NEWLINE), string='\n', start=(3, 13), end=(3, 14), line='    let y = x\n')
# ----------------* 4.4: NAME:'return'
# TokenInfo(type=1 (NAME), string='return', start=(4, 4), end=(4, 10), line='    return y\n')
# -----------------* 4.11: NAME:'y'
# TokenInfo(type=1 (NAME), string='y', start=(4, 11), end=(4, 12), line='    return y\n')
# ------------------* 5.0: OP:'}'
# TokenInfo(type=55 (OP), string='}', start=(5, 0), end=(5, 1), line='}\n')
# -------------------* 5.1: NEWLINE:'\n'
# TokenInfo(type=4 (NEWLINE), string='\n', start=(5, 1), end=(5, 2), line='}\n')
# --------------------* 6.0: ENDMARKER:''


code_multi_stmt = """
def func(x: int) -> None {
    let y = x
    return y
}
"""

result_multi_stmt = """
def func(x: int) -> None:
    y = x
    return y
"""


def test_code_multi_stmt_tokenized():
    show_token(code_multi_stmt)
    ta = TokenizerAsserter(code_multi_stmt)

    ta.next(NAME, "def")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(NAME, "x")
    ta.next(OP, ":")
    ta.next(NAME, "int")
    ta.next(OP, ")")
    ta.next(OP, "->")
    ta.next(NAME, "None")
    ta.next(OP, "{")
    ta.next(NAME, "let")
    ta.next(NAME, "y")
    ta.next(OP, "=")
    ta.next(NAME, "x")
    ta.next(NEWLINE, "\n")  # Here is a NEWLINE as a delimiter
    ta.next(NAME, "return")
    ta.next(NAME, "y")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")

    assert_parse(code_multi_stmt, result_multi_stmt)


code_comment = """
# This is a comment
def func() {
    pass  # Inline comment
}
"""
result_comment = """
def func():
    pass
"""


def test_code_comment_tokenized():
    show_token(code_comment)
    ta = TokenizerAsserter(code_comment)

    ta.next(NAME, "def")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(OP, ")")
    ta.next(OP, "{")
    ta.next(NAME, "pass")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")

    assert_parse(code_comment, result_comment)
