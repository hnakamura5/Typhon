from .assertion_utils import assert_ast_equals, show_token, assert_token

code_def = """
def func() {
    return;
}
"""
result_def = """
def func():
    return
"""


def test_stmt_def():
    assert_ast_equals(code_def, result_def)


code_def_typed = """
def func(x: int) -> None {
    return None;
}
"""
result_def_typed = """
def func(x: int) -> None:
    return None

"""
# code_typed
# -* 2.0: NAME:'def'
# TokenInfo(type=1 (NAME), string='def', start=(2, 0), end=(2, 3), line='def func(x: int) -> None {\n')
# --* 2.4: NAME:'func'
# TokenInfo(type=1 (NAME), string='func', start=(2, 4), end=(2, 8), line='def func(x: int) -> None {\n')
# ---* 2.8: OP:'('
# TokenInfo(type=54 (OP), string='(', start=(2, 8), end=(2, 9), line='def func(x: int) -> None {\n')
# ----* 2.9: NAME:'x'
# TokenInfo(type=1 (NAME), string='x', start=(2, 9), end=(2, 10), line='def func(x: int) -> None {\n')
# -----* 2.10: OP:':'
# TokenInfo(type=54 (OP), string=':', start=(2, 10), end=(2, 11), line='def func(x: int) -> None {\n')
# ------* 2.12: NAME:'int'
# TokenInfo(type=1 (NAME), string='int', start=(2, 12), end=(2, 15), line='def func(x: int) -> None {\n')
# -------* 2.15: OP:')'
# TokenInfo(type=54 (OP), string=')', start=(2, 15), end=(2, 16), line='def func(x: int) -> None {\n')
# --------* 2.17: OP:'->'
# TokenInfo(type=54 (OP), string='->', start=(2, 17), end=(2, 19), line='def func(x: int) -> None {\n')
# ---------* 2.20: NAME:'None'
# TokenInfo(type=1 (NAME), string='None', start=(2, 20), end=(2, 24), line='def func(x: int) -> None {\n')
# ----------* 2.25: OP:'{'
# TokenInfo(type=54 (OP), string='{', start=(2, 25), end=(2, 26), line='def func(x: int) -> None {\n')
# -----------* 3.4: NAME:'return'
# TokenInfo(type=1 (NAME), string='return', start=(3, 4), end=(3, 10), line='    return None;\n')
# ------------* 3.11: NAME:'None'
# TokenInfo(type=1 (NAME), string='None', start=(3, 11), end=(3, 15), line='    return None;\n')
# -------------* 3.15: OP:';'
# TokenInfo(type=54 (OP), string=';', start=(3, 15), end=(3, 16), line='    return None;\n')
# --------------* 4.0: OP:'}'
# TokenInfo(type=54 (OP), string='}', start=(4, 0), end=(4, 1), line='}\n')
# ---------------* 4.1: NEWLINE:'\n'
# TokenInfo(type=4 (NEWLINE), string='\n', start=(4, 1), end=(4, 2), line='}\n')
# ----------------* 5.0: ENDMARKER:''


def test_stmt_def_token_typed():
    import tokenize
    import io
    from pegen.tokenizer import Tokenizer

    tok_stream = tokenize.generate_tokens(io.StringIO(code_def_typed).readline)
    tokenizer = Tokenizer(tok_stream, verbose=True)

    show_token(code_def_typed)

    def assert_next_token(type_, string):
        token = tokenizer.getnext()
        assert_token(token, type_, string)

    assert_next_token(tokenize.NAME, "def")
    assert_next_token(tokenize.NAME, "func")
    assert_next_token(tokenize.OP, "(")
    assert_next_token(tokenize.NAME, "x")
    assert_next_token(tokenize.OP, ":")
    assert_next_token(tokenize.NAME, "int")
    assert_next_token(tokenize.OP, ")")
    assert_next_token(tokenize.OP, "->")
    assert_next_token(tokenize.NAME, "None")
    assert_next_token(tokenize.OP, "{")
    assert_next_token(tokenize.NAME, "return")
    assert_next_token(tokenize.NAME, "None")
    assert_next_token(tokenize.OP, ";")
    # Note NL does not appear here.
    assert_next_token(tokenize.OP, "}")
    assert_next_token(tokenize.NEWLINE, "\n")
    assert_next_token(tokenize.ENDMARKER, "")


def test_stmt_def_typed():
    assert_ast_equals(code_def_typed, result_def_typed)


code_def_async_typed = """
async def func(x: int) -> None {
    return None;
}
"""
result_def_async_typed = """
async def func(x: int) -> None:
    return None

"""


def test_stmt_def_async_typed():
    assert_ast_equals(code_def_async_typed, result_def_async_typed)
