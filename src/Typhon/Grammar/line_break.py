from tokenize import TokenInfo, generate_tokens, OP, NAME


def is_operator_line_breakable_after(tok: TokenInfo) -> bool:
    # Exceptional symbols that are NOT operator.
    if tok.string in (
        "?"  # Single `?` is optional type annotation, not operator.
        "..."  # Ellipsis is not operator. Just a singleton symbol.
    ):
        return False

    return (
        tok.type == OP
        and (
            tok.string.endswith(
                (
                    "+",
                    "-",
                    "*",
                    "/",
                    "%",
                    ">",
                    "<",
                    "&",
                    "|",
                    "?",
                    ":",
                    "=",
                    ",",
                    ".",
                    "@",
                    "^",
                    "~",
                    "!",
                    ";",  # Also breakable here. Even if itself is a delimiter.
                )
            )
        )
        or (tok.type == NAME and tok.string in ("await", "in", "is"))
    )


def is_bracket_line_breakable_after(tok: TokenInfo) -> bool:
    return tok.type == OP and tok.string in ("(", "[", "{")


def is_stmt_keyword_line_breakable_after(tok: TokenInfo) -> bool:
    # Except for return/break like ones (`return`, `raise`, `yield`, `break`, `continue`).
    return tok.type == NAME and tok.string in (
        "import",
        "from",
        "as",
        "class",
        "def",
        "let",
        "var",
        "if",
        "elif",
        "else",
        "while",
        "for",
        "try",
        "except",
        "finally",
        "with",
        "match",
        "case",
        # modifiers
        "async",
        "static",
    )


def line_breakable_after(tok: TokenInfo) -> bool:
    return (
        is_operator_line_breakable_after(tok)
        or is_bracket_line_breakable_after(tok)
        or is_stmt_keyword_line_breakable_after(tok)
    )


def is_operator_line_breakable_before(tok: TokenInfo) -> bool:
    return is_operator_line_breakable_after(tok) and tok.string not in ("@", "await")


def is_bracket_line_breakable_before(tok: TokenInfo) -> bool:
    return tok.type == OP and tok.string in (")", "]", "}")


def is_stmt_keyword_line_breakable_before(tok: TokenInfo) -> bool:
    return tok.type == NAME and tok.string in (
        "elif",
        "else",
        "except",
        "finally",
        "case",
    )


def line_breakable_before(tok: TokenInfo) -> bool:
    return (
        is_operator_line_breakable_before(tok)
        or is_bracket_line_breakable_before(tok)
        or is_stmt_keyword_line_breakable_before(tok)
    )
