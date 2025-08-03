# Memo for implementation detail

## Token NEWLINE and NL

tokenize in Python distinguish `NEWLINE` and `NL` for newline character.
For those where paren level (the level of all `([{`) is NL. Others are `NEWLINE`.
`NL` is only recognized as separator and skipped by peek(and next) method in Tokenizer. So Parser does not see `NL` in parsing.
`NEWLINE` is recognized by Parser as important delimiter.

source is tokenize() in Lib/tokenize.py for 3.11, tok_get_normal_mode() in Parser/tokenize.c for 3.12 and later.
