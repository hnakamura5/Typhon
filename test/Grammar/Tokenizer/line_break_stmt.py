from ..assertion_utils import show_token, assert_ast_equals, TokenizerAsserter
from tokenize import NAME, OP, NEWLINE, ENDMARKER, NUMBER

code_class_line_brk = """
class
MyClass[
T
](
Base[
T
]
)
{

    def
    method(
    self,
    x: int
    )
    ->
    int
    {
        let
        y
        =

        x
        +
        1

        return y

    }

}
"""
result_class_line_brk = """
class MyClass[T](Base[T]):

    def method(self, x: int) -> int:
        y = x + 1
        return y
"""


def test_class_line_brk():
    show_token(code_class_line_brk)
    ta = TokenizerAsserter(code_class_line_brk)
    ta.next(NAME, "class")
    ta.next(NAME, "MyClass")
    ta.next(OP, "[")
    ta.next(NAME, "T")
    ta.next(OP, "]")
    ta.next(OP, "(")
    ta.next(NAME, "Base")
    ta.next(OP, "[")
    ta.next(NAME, "T")
    ta.next(OP, "]")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n")  # This is ignored NEWLINE after ')' of class def
    ta.next(OP, "{")
    ta.next(NAME, "def")
    ta.next(NAME, "method")
    ta.next(OP, "(")
    ta.next(NAME, "self")
    ta.next(OP, ",")
    ta.next(NAME, "x")
    ta.next(OP, ":")
    ta.next(NAME, "int")
    ta.next(OP, ")")
    ta.next(OP, "->")
    ta.next(NAME, "int")
    ta.next(NEWLINE, "\n")  # This is ignored NEWLINE in function_def
    ta.next(OP, "{")
    ta.next(NAME, "let")
    ta.next(NAME, "y")
    ta.next(OP, "=")
    ta.next(NAME, "x")
    ta.next(OP, "+")
    ta.next(NUMBER, "1")
    ta.next(NEWLINE, "\n")  # NEWLINE as a delimiter
    ta.next(NAME, "return")
    ta.next(NAME, "y")
    ta.next(OP, "}")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")

    assert_ast_equals(code_class_line_brk, result_class_line_brk)


code_stmt_line_brk = """
def
func(
x: int,
y: int
)
->
int
{
    if
      (
    True
    )
    {
    let
    z
    =
    x

    +
    y
    if
    (
    z
    >
    10
    # This is a comment
    )
    {
        return z
    }
    let
      w = z
      + 1 # This still in last line
    @decolator
    def
    g() {
    return w
    }
    return
    g(

    )
    # Error, dead code after return
    }


}
"""


result_stmt_line_brk = """
def func(x: int, y: int) -> int:
    if True:
        z = x + y
        if z > 10:
            return z
        w = z + 1

        @decolator
        def g():
            return w
        return
        g()
"""


def test_stmt_line_brk():
    show_token(code_stmt_line_brk)
    ta = TokenizerAsserter(code_stmt_line_brk)
    ta.next(NAME, "def")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(NAME, "x")
    ta.next(OP, ":")
    ta.next(NAME, "int")
    ta.next(OP, ",")
    ta.next(NAME, "y")
    ta.next(OP, ":")
    ta.next(NAME, "int")
    ta.next(OP, ")")
    ta.next(OP, "->")
    ta.next(NAME, "int")
    ta.next(NEWLINE, "\n")  # This is ignored NEWLINE in function_def
    ta.next(OP, "{")
    ta.next(NAME, "if")
    ta.next(OP, "(")
    ta.next(NAME, "True")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n")  # This is ignored NEWLINE in if_stmt
    ta.next(OP, "{")
    ta.next(NAME, "let")
    ta.next(NAME, "z")
    ta.next(OP, "=")
    ta.next(NAME, "x")
    ta.next(OP, "+")
    ta.next(NAME, "y")
    ta.next(NEWLINE, "\n")  # NEWLINE as a delimiter
    ta.next(NAME, "if")
    ta.next(OP, "(")
    ta.next(NAME, "z")
    ta.next(OP, ">")
    ta.next(NUMBER, "10")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n")  # This is ignored NEWLINE in if_stmt
    ta.next(OP, "{")
    ta.next(NAME, "return")
    ta.next(NAME, "z")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")  # NEWLINE as a delimiter
    ta.next(NAME, "let")
    ta.next(NAME, "w")
    ta.next(OP, "=")
    ta.next(NAME, "z")
    ta.next(OP, "+")  # Still in last line
    ta.next(NUMBER, "1")
    ta.next(NEWLINE, "\n")  # NEWLINE as a delimiter
    ta.next(OP, "@")
    ta.next(NAME, "decolator")
    ta.next(NEWLINE, "\n")  # NEWLINE for decorator
    ta.next(NAME, "def")
    ta.next(NAME, "g")
    ta.next(OP, "(")
    ta.next(OP, ")")
    ta.next(OP, "{")
    ta.next(NAME, "return")
    ta.next(NAME, "w")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")  # NEWLINE as a delimiter
    ta.next(NAME, "return")
    ta.next(NEWLINE, "\n")  # Here is a NEWLINE as a delimiter. After return
    ta.next(NAME, "g")  # Dead code after return
    ta.next(OP, "(")
    ta.next(OP, ")")
    ta.next(OP, "}")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")  # This is ignored NEWLINE in function
    ta.next(ENDMARKER, "")
    assert_ast_equals(code_stmt_line_brk, result_stmt_line_brk)
