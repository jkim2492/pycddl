import ply.yacc as yacc
from lexer import tokens
from ply.lex import LexToken
from typing import Union, Optional, List, get_args, get_origin
from preprocess import preprocess
from pprint import pprint
import re
from typing import Literal


def get_token(something, i):
    x = something.slice[i]
    if isinstance(x, LexToken):
        return x.type
    return str(x)


def is_optional(value):
    return get_origin(value) is Union and type(None) in get_args(value)


def is_union(value):
    return get_origin(value) is Union


def is_literal_union(t) -> bool:
    if get_origin(t) is Union:
        return all(get_origin(arg) is Literal for arg in get_args(t))
    return False


def is_builtin(s):
    if s == "type":
        return True
    return False


def repre(value, module=None):
    if isinstance(value, (str, int, float)):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return f"[{', '.join([repre(x,module) for x in value])}]"
    if isinstance(value, CddlType):
        if module and module == value.module:
            return value.name
        return value.fname
    if value.__module__ == "builtins":
        return value.__name__
    if get_args(value) and not is_optional(value) and not is_literal_union(value):
        origin = get_origin(value).__name__
        args = list(get_args(value))
        return f"typing.{origin}{repre(args,module)}"
    if is_optional(value):
        union_args = [x for x in value.__args__ if x != type(None)]
        return f"typing.Optional{repre(union_args,module)}"
    if is_literal_union(value):
        args = list(get_args(value))
        args = [get_args(v)[0] for v in args]
        return f"typing.Literal{repr(args)}"
    return repr(value)


# If params is a singleton with a CddlType as its only entry, remove the surrounding array
def flatten_params(params):
    if not isinstance(params, list):
        return params
    if len(params) == 1 and not isinstance(params[0], CddlPair):
        return params[0]
    return params


def typify(s):
    if isinstance(s, str):
        return CddlType(s, (object,), {})
    return s


def untypify(s):
    if type(s).__module__ == "builtins":
        return s
    args = get_args(s)
    if len(args) != 1:
        raise "ERROR"
    return args[0]


class CddlType(type):
    def __init__(self, name, *_):
        self.fname = name
        self.module = self.fname.split(".")[0]
        self.name = self.fname.split(".")[-1]
        self.__qualname__ = self.name

    def __repr__(self):
        return repre(self)


class CddlKey(str):
    def __init__(self, fname, default=None):
        self.fname = fname
        self.module = self.fname.split(".")[0]
        self.name = self.fname.split(".")[-1]
        self.default = default


class CddlPair(dict):
    def __init__(self, *args, **kwargs):
        super(CddlPair, self).__init__(*args, **kwargs)
        self.key = list(self.keys())[0]
        self.value = self[self.key]

    def __setitem__(self, key, value):
        super(CddlPair, self).__setitem__(key, value)

    def __getitem__(self, key):
        return super(CddlPair, self).__getitem__(key)

    @property
    def is_optional(self):
        return is_optional(self.value)

    @property
    def defaultstr(self):
        if self.key.default:
            return f" = {repr(self.key.default)}"
        if self.is_optional:
            return " = None"
        if get_origin(self.value) == Literal and len(get_args(self.value)) == 1:
            return f" = {repr(get_args(self.value)[0])}"
        return ""

    def code(self, module=None):
        if is_builtin(self.key):
            key = f"_{self.key}"
        else:
            key = self.key
        ret = f"{key}: {repre(self.value,module)}{self.defaultstr}"
        return ret


# params can either be CddlType or CddlPair
class CddlEntry:
    def __init__(self, fname, params):
        self.fname = fname
        self.module = self.fname.split(".")[0]
        self.name = self.fname.split(".")[-1]

        self.params = flatten_params(params)


def p_cddl(p):
    """cddl : assignment_list"""
    p[0] = p[1]


def p_assignment_list(p):
    """assignment_list : assignment_list assignment
    | assignment"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]


def p_assignment(p):
    """assignment : SYMBOL ASSIGN value SEMICOLON"""
    p[0] = CddlEntry(p[1], p[3])


def p_group(p):
    """group : LPAREN value RPAREN"""
    p[0] = p[2]


def p_entry(p):
    """entry : LBRACE params RBRACE
    | LPAREN params RPAREN"""
    if len(p) == 4:
        p[0] = p[2]


def p_key(p):
    """key : SYMBOL"""
    p[0] = CddlKey(p[1])


def p_value(p):
    """value : type
    | entry"""
    p[0] = p[1]


def p_value_optional(p):
    """value_optional : QUESTION value"""
    p[0] = Optional[p[2]]


def p_value_default(p):
    """value_default : type DEFAULT type_literal"""
    x = untypify(p[3])
    p[0] = (p[1], x)


def p_type(p):
    """type : type_union
    | type_array
    | type_range
    | type_literal
    | group
    | SYMBOL
    """
    p[0] = typify(p[1])


def p_type_union(p):
    """type_union : type_union UNION type
    | type_union UNION
    | type
    """
    if len(p) == 4:
        p[0] = Union[p[1], p[3]]
    else:
        p[0] = p[1]


def p_type_array(p):
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


def p_type_range(p):
    """type_range : NUMBER RANGE NUMBER"""
    p[0] = type(p[1])


def p_type_literal(p):
    """type_literal : NUMBER
    | STRING
    | BOOL
    """
    if p[1] is not None:
        p[0] = Literal[p[1]]
    else:
        p[0] = p[1]


def p_params(p):
    """params : params sep param
    | params sep
    | param"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif len(p) == 3:
        p[0] = p[1]
    elif str(p.slice[1]) == "param":
        p[0] = [p[1]]


def p_param(p):
    """param : key COLON value
    |  key COLON value_default
    |  QUESTION key COLON value
    |  QUESTION key COLON value_default
    | value
    | value_optional
    """
    if get_token(p, 1) == "QUESTION":
        if get_token(p, -1) == "value_default":
            p[2].default = p[4][1]
            p[0] = CddlPair({p[2]: Optional[p[4][0]]})
        else:
            p[0] = CddlPair({p[2]: Optional[p[4]]})
    elif get_token(p, 1) == "key":
        if get_token(p, -1) == "value_default":
            p[1].default = p[3][1]
            p[0] = CddlPair({p[1]: p[3][0]})
        else:
            p[0] = CddlPair({p[1]: p[3]})
    else:
        p[0] = p[1]


def p_sep(p):
    """sep : COMMA"""
    p[0] = p[1]


# Error rule for syntax errors
def p_error(p):
    global parser
    if not p:
        print("Syntax error at EOF")
        return
    if p and p.type == "JOIN":
        print(f"Syntax error: unexpected 'JOIN'. Replacing with 'UNION'.")
        p.type = "UNION"
        p.value = "//"
        parser.errok()
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

        parser.errok()
        return None
    pos = p.lexpos

    start = max(0, pos - 20)
    end = min(len(p.lexer.lexdata), pos + 20)

    # Extract the substring around the error token
    error_context = p.lexer.lexdata[start:end]

    # Indicate the error token within the context
    print(f"Syntax error at token {p}")
    print(f"Context: {error_context}")


parser = yacc.yacc()


def parse(data, pattern=""):
    data = preprocess(data, pattern)
    return parser.parse(data)
