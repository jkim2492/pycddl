from typing import List, Literal, Optional, Union

import ply.yacc as yacc

from lexer import CDDL_TOKENS, CddlLexer
from preprocess import preprocess
from utils import *


class CddlParser:
    def __init__(self):
        self.lexer = CddlLexer().lexer
        self.parser = yacc.yacc(module=self, debug=False, write_tables=False)

    tokens = CDDL_TOKENS

    def p_cddl(self, p):
        """cddl : assignment_list"""
        p[0] = p[1]

    def p_assignment_list(self, p):
        """assignment_list : assignment_list assignment
        | assignment"""
        if len(p) == 3:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[1]]

    def p_assignment(self, p):
        """assignment : SYMBOL ASSIGN value SEMICOLON"""
        p[0] = CddlEntry(p[1], p[3])

    def p_group(self, p):
        """group : LPAREN value RPAREN"""
        p[0] = p[2]

    def p_entry(self, p):
        """entry : LBRACE params RBRACE
        | LPAREN params RPAREN"""
        if len(p) == 4:
            p[0] = p[2]

    def p_value(self, p):
        """value : type
        | entry"""
        p[0] = p[1]

    def p_value_optional(self, p):
        """value_optional : QUESTION value"""
        p[0] = Optional[p[2]]

    def p_value_default(self, p):
        """value_default : type DEFAULT type_literal"""
        x = untypify(p[3])
        p[0] = (p[1], x)

    def p_type(self, p):
        """type : type_union
        | type_array
        | type_range
        | type_literal
        | group
        | SYMBOL
        """
        p[0] = typify(p[1])

    def p_type_union(self, p):
        """type_union : type_union UNION type
        | type_union UNION
        | type
        """
        if len(p) == 4:
            p[0] = Union[p[1], p[3]]
        else:
            p[0] = p[1]

    def p_type_array(self, p):
        """type_array : LBRACKET STAR type RBRACKET
        | LBRACKET PLUS type RBRACKET
        | LBRACKET type RBRACKET
        """
        if p[2] == "*":
            p[0] = Optional[List[p[3]]]
        elif get_token(p, 3) == "type":
            p[0] = List[p[3]]
        else:
            p[0] = List[p[2]]

    def p_type_range(self, p):
        """type_range : NUMBER RANGE NUMBER"""
        p[0] = type(p[1])

    def p_type_literal(self, p):
        """type_literal : NUMBER
        | STRING
        | BOOL
        """
        if p[1] is not None:
            p[0] = Literal[p[1]]
        else:
            p[0] = p[1]

    def p_params(self, p):
        """params : params sep param
        | params sep
        | param"""
        if len(p) == 4:
            p[0] = p[1] + [p[3]]
        elif len(p) == 3:
            p[0] = p[1]
        elif get_token(p, 1) == "param":
            p[0] = [p[1]]

    def p_param(self, p):
        """param : SYMBOL COLON value
        |  SYMBOL COLON value_default
        |  QUESTION SYMBOL COLON value
        |  QUESTION SYMBOL COLON value_default
        | value
        | value_optional
        """
        if get_token(p, 1) == "QUESTION":
            p[2] = CddlKey(p[2])
            if get_token(p, -1) == "value_default":
                p[2].default = p[4][1]
                p[0] = CddlPair({p[2]: Optional[p[4][0]]})
            else:
                p[0] = CddlPair({p[2]: Optional[p[4]]})
        elif get_token(p, 1) == "SYMBOL":
            p[1] = CddlKey(p[1])
            if get_token(p, -1) == "value_default":
                p[1].default = p[3][1]
                p[0] = CddlPair({p[1]: p[3][0]})
            else:
                p[0] = CddlPair({p[1]: p[3]})
        else:
            p[0] = p[1]

    def p_sep(self, p):
        """sep : COMMA"""
        p[0] = p[1]

    # Error rule for syntax errors
    def p_error(self, p):
        global parser
        if not p:
            print("Syntax error at EOF")
            return
        if p and p.type == "JOIN":
            print(f"Syntax error: unexpected 'JOIN'. Replacing with 'UNION'.")
            p.type = "UNION"
            p.value = "//"
            parser.errok()  # Clear the error state
            return p

        if p.type == "LPAREN":
            print(f"Syntax error: unmatched '('. Searching for ')'.")
            paren_depth = 1
            while True:
                tok = parser.token()  # Get the next token
                if not tok:
                    print("Error: No matching ')' found. Discarding.")
                    break
                if tok.type == "LPAREN":
                    paren_depth += 1  # Nested parenthesis
                elif tok.type == "RPAREN":
                    paren_depth -= 1
                    if paren_depth == 0:
                        print("Found matching ')'. Discarding parentheses and restarting.")
                        break

            parser.errok()  # Clear the error state
            return None  # Restart parsing
        pos = p.lexpos

        # Extract 10 characters before and after the error token
        start = max(0, pos - 20)
        end = min(len(p.lexer.lexdata), pos + 20)

        # Extract the substring around the error token
        error_context = p.lexer.lexdata[start:end]

        # Indicate the error token within the context
        print(f"Syntax error at token {p}")
        print(f"Context: {error_context}")

    def parse(self, data):
        return self.parser.parse(data)


def parse(data, pattern=""):
    parser = CddlParser()
    data = preprocess(data, pattern)
    return parser.parse(data)
