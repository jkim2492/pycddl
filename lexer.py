import ply.lex as lex
from typing import Literal

# List of token names.
tokens = ["SYMBOL", "NUMBER", "BOOL", "DEFAULT", "RANGE", "ASSIGN", "COLON", "LPAREN", "RPAREN", "LBRACKET", "RBRACKET", "LBRACE", "RBRACE", "COMMA", "SEMICOLON", "STRING", "QUESTION", "STAR", "PLUS", "JOIN", "NEWLINE", "UNION"]

# Regular expression rules for simple tokens
t_ASSIGN = R"="
t_COLON = R":"
t_LPAREN = R"\("
t_RPAREN = R"\)"
t_LBRACKET = R"\["
t_RBRACKET = R"\]"
t_LBRACE = R"\{"
t_RBRACE = R"\}"
t_COMMA = R","
t_RANGE = R"\.\."
t_DEFAULT = R"\.default"
t_NEWLINE = R"\n"
t_SEMICOLON = R";"

# New tokens for ?, *, + before SYMBOL, and / for unions
t_QUESTION = R"\?"
t_STAR = R"\*"
t_PLUS = R"\+"
t_JOIN = R"/"
t_UNION = R"//"


# Regular expressions with actions
def t_NUMBER(t):
    R"\d+(\.\d+)?"
    if "." in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)
    return t


def t_BOOL(t):
    R"true|false|null|nil"
    if t.value == "true":
        t.value = True
    elif t.value == "false":
        t.value = False
    elif t.value in ["null", "nil"]:
        t.value = None
    return t


def t_STRING(t):
    R"\".*?\" "
    t.value = t.value[1:-1]
    t.value = Literal[t.value]
    return t


def t_SYMBOL(t):
    R"(?!true|false|null|nil)\b[A-Za-z]+(?:\.(?!default)\w*)?"
    if t.value in ["tstR", "text"]:
        t.value = str
    elif t.value in ["uint", "int", "js-int", "js-uint"]:
        t.value = int
    elif t.value == "float":
        t.value = float
    elif t.value == "dict":
        t.value = dict
    elif t.value == "bool":
        t.value = bool
    elif t.value in ["nil", "null"]:
        t.value = type(None)

    return t


# Ignored characters (spaces and tabs)
t_ignore = " \t\n"


# Error handling rule
def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()

# # Example usage
# data = 'myfield = "example" ;'
# lexer.input(data)
from preprocess import preprocess

if __name__ == "__main__":
    with open("examples.cddl") as rf:
        data = rf.read()
    data = preprocess(data)
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)
