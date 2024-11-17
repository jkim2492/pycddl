"""
Adjust the input file to handle some edge cases.
Ideally, the edge cases should be handled in lexer/parser, but it is easier to handle them here for now
"""

import re

UNSUPPORTED_PATTERNS = [
    "=>",
]
BRACES = R"\{|\(|\[|\}|\)|\]"


# Add a comma when a new line is used instead of comma
def fix_comma(text):
    if not re.search(BRACES, text):
        return text
    lines = text.splitlines()
    for i, line in enumerate(lines):
        line = line.strip()
        if re.search(Rf"{BRACES}|\/", line):
            continue
        if not line:
            continue
        lines[i] = re.sub(R",*$", ",", line, count=1)
    return "\n".join(lines)


def split_entry(entry):
    match = re.match(
        R"^\s*([\w.-]+)\s*=\s*(.+?)\s*$",  # Match key and value
        entry.strip(),
        flags=re.DOTALL,  # Handle multiline values
    )
    if match:
        key, value = match.groups()
        return key, value
    return None


# Replace type strings with more standard names
# Remove some "." modifiers
def prune(text):
    text = re.sub(R"js-uint", R"int", text)
    text = re.sub(R"js-int", R"int", text)
    text = re.sub(R"uint", R"int", text)
    text = re.sub(R"tstr", R"text", text)
    # Remove ".ge" and ".le"
    text = re.sub(R"float \.\w\w \d+\.\d+", R"float", text)
    text = re.sub(R"int \.\w\w \d+", R"int", text)
    # Remove ".and"
    text = re.sub(R"}\s*\.and\s*.*", R"}", text)
    return text


def remove_comments(text):
    return re.sub(R"^;.+\n", R"", text, flags=re.MULTILINE)


def remove_spaces(text):
    return re.sub(R"\s", "", text)


def ensure_semicolon(text):
    return re.sub(R";*$", ";", text, count=1)


def is_unsupported(value):
    for pattern in UNSUPPORTED_PATTERNS:
        if re.search(pattern, value):
            return True
    return False


def is_empty(value):
    return re.search(R"{(,|\s)*};?", value, re.DOTALL)


def remove_unsupported_param(text):
    for term in UNSUPPORTED_TERMS:
        text = re.sub(Rf"/*{term}\s*,?", "", text)
    return text


UNSUPPORTED_TERMS = []


def preprocess(text, pattern=""):
    text = remove_comments(text)
    text = prune(text)
    entry_list = re.split(R"\n\n", text)

    new_list = []
    for entry in entry_list:
        if not entry:
            continue
        key, value = split_entry(entry)

        if is_unsupported(value):
            UNSUPPORTED_TERMS.append(key)
            continue

        value = remove_unsupported_param(value)

        if is_empty(value):
            UNSUPPORTED_TERMS.append(key)
            continue

        try:
            value = fix_comma(value)
        except:
            pass

        value = remove_spaces(value)
        value = ensure_semicolon(value)

        if not re.search(pattern.lower(), key.lower()) and entry:
            continue

        entry = f"{key}={value}"
        new_list.append(entry)

    new_text = "\n".join(new_list)
    new_text = re.sub(R"\/+", "//", new_text)
    return new_text
