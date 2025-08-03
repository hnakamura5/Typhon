import ast
from ...src.Grammar.parser import parse_string


code = """
def func() {
    return;
}
"""
# code = """
# def func():
#     return

# """

result = """
def func():
    return

"""


def show_token(source: str):
    import tokenize
    import io
    from pegen.tokenizer import Tokenizer

    tok_stream = tokenize.generate_tokens(io.StringIO(source).readline)
    tokenizer = Tokenizer(tok_stream, verbose=True)
    print("Tokens:")
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        print(tok)
    print("Tokens in pegen:")
    tok = tokenizer.getnext()
    while tok.type != tokenize.ENDMARKER:
        print(tok)
        tok = tokenizer.getnext()


def test_stmt_def():
    show_token(code)
    parsed = parse_string(code, mode="exec", verbose=True)
    assert isinstance(parsed, ast.Module)
    assert ast.unparse(parsed) == result.strip()
