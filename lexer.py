from typing import Literal

import ply.lex as lex

CDDL_TOKENS = [
    # Data types
    "NUMBER",
    "BOOL",
    "STRING",
    "SYMBOL",
    "RANGE",
    # Logical operators
    "ASSIGN",
    "COLON",
    "UNION",
    "JOIN",
    # Modifiers
    "STAR",
    "PLUS",
    "QUESTION",
    # Delimiters
    "LPAREN",
    "RPAREN",
    "LBRACKET",
    "RBRACKET",
    "LBRACE",
    "RBRACE",
    "COMMA",
    "SEMICOLON",
    # Miscellaneous
    "NEWLINE",  # Unused for now
    "DEFAULT",
]


class CddlLexer:
    def __init__(self):
        self.lexer = lex.lex(module=self)

    tokens = CDDL_TOKENS

    t_RANGE = R"\.\."
    t_ASSIGN = R"="
    t_COLON = R":"
    t_UNION = R"//"
    t_JOIN = R"/"
    t_STAR = R"\*"
    t_PLUS = R"\+"
    t_QUESTION = R"\?"
    t_LPAREN = R"\("
    t_RPAREN = R"\)"
    t_LBRACKET = R"\["
    t_RBRACKET = R"\]"
    t_LBRACE = R"\{"
    t_RBRACE = R"\}"
    t_COMMA = R","
    t_SEMICOLON = R";"
    t_NEWLINE = R"\n"
    t_DEFAULT = R"\.default"

    # Ignored characters (spaces and tabs)
    t_ignore = " \t\n"

    def t_NUMBER(self, t):
        R"\d+(\.\d+)?"
        if "." in t.value:
            t.value = float(t.value)
        else:
            t.value = int(t.value)
        return t

    def t_BOOL(self, t):
        R"true|false|null|nil"
        if t.value == "true":
            t.value = True
        elif t.value == "false":
            t.value = False
        elif t.value in ["null", "nil"]:
            t.value = None
        return t

    def t_STRING(self, t):
        R"\".*?\" "
        t.value = t.value[1:-1]
        t.value = Literal[t.value]
        return t

    def t_SYMBOL(self, t):
        R"(?!true|false|null|nil)\b[A-Za-z]+(?:\.(?!default)\w*)?"
        return t

    # Error handling rule
    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}'")
        t.lexer.skip(1)