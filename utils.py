import re
from typing import Literal, Union, get_args, get_origin

from ply.lex import LexToken

SNAKE = True


def get_token(p, i):
    x = p.slice[i]
    if isinstance(x, LexToken):
        return x.type
    return str(x)


def to_snake(camel_case: str) -> str:
    snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", camel_case)
    return snake_case.lower()


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
        origin = origin[0].upper() + origin[1:]
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
    if s == "text":
        s = "str"
    if s in __builtins__:
        return __builtins__.get(s)
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
    def __init__(self, fname, *_):
        if "." in fname:
            self.fname = fname
            self.module = self.fname.split(".")[0]
            self.name = self.fname.split(".")[-1]
        else:
            self.fname = fname
            self.name = fname
            self.module = None
        if SNAKE and self.module:
            self.module = to_snake(self.module)
            self.fname = f"{self.module}.{self.name}"
        self.__qualname__ = self.name

    def __repr__(self):
        return repre(self)


class CddlKey(str):
    def __init__(self, name, default=None):
        name = str(name)
        if "." in name:
            self.fname = name
            self.module = self.fname.split(".")[0]
            self.name = self.fname.split(".")[-1]
        else:
            self.fname = name
            self.name = name
            self.module = None
        if SNAKE and self.module:
            self.module = to_snake(self.module)
            self.fname = f"{self.module}.{self.name}"
        self.default = default


class CddlPair(dict):
    # You can override the constructor (__init__) to add custom behavior
    def __init__(self, *args, **kwargs):
        # Call the parent dict constructor
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
            key = f"{self.key}_"
        else:
            key = self.key
        ret = f"{key}: {repre(self.value,module)}{self.defaultstr}"
        return ret


# params can either be CddlType or CddlPair
class CddlEntry:
    def __init__(self, name, params):
        if "." in name:
            self.fname = name
            self.module = self.fname.split(".")[0]
            self.name = self.fname.split(".")[-1]
        else:
            self.fname = name
            self.name = name
            self.module = None
        if SNAKE and self.module:
            self.module = to_snake(self.module)
            self.fname = f"{self.module}.{self.name}"

        self.params = flatten_params(params)

    def __str__(self):
        paramstr = "\n".join([str(param) for param in self.params])
        return f"""{self.fname} = {{
            {paramstr}          
        }}"""

    def __repr__(self):
        if isinstance(self.params, list):
            paramstr = "\n".join([str(param) for param in self.params])
        else:
            paramstr = str(self.params)
        return f"""{self.fname} = {{
        {paramstr}          
        }}
"""
