import re


# Add a comma when a new line is used instead of comma
def fix_comma(text):
    lines = text.splitlines()
    if not (re.search(R"\{|\(|\[", lines[0]) and re.search(R"\}|\)|\]", lines[-1])):
        return text
    for i, line in enumerate(lines):
        if i in [0, len(lines) - 1] or re.search(R"\{|\(|\[|\}|\)|\]|\/", line):
            continue
        lines[i] = re.sub(R",$", "", line)
        lines[i] = re.sub(R"$", ",", lines[i])
    return "\n".join(lines)


# Replace type strings with more pythonic names
# Remove unsupported types and operations
def prune(text):
    text = re.sub(R"js-uint", R"int", text)
    text = re.sub(R"js-int", R"int", text)
    text = re.sub(R"float \.\w\w \d+\.\d+", R"float", text)
    text = re.sub(R"int \.\w\w \d+", R"int", text)
    text = re.sub(R"}\s*\.and\s*.*", R"}", text)
    text = re.sub(R"}\s*\.and\s*.*", R"}", text)
    return text


def preprocess(text, pattern=""):
    text = re.sub(R"\n;.*", R"", text)
    text = prune(text)
    # Remove comments
    text = re.sub(R"^#.*", R"", text)
    term_list = re.split(R"\n\n", text)
    new_list = []
    for term in term_list:
        try:
            term = fix_comma(term)
        except:
            pass
        term = re.sub(R"\s", "", term)
        term = term.strip()
        term = re.sub(R";$", "", term)
        term = re.sub(R"$", ";", term)
        key = term.split("=")[0].strip()

        if not re.search(pattern.lower(), key.lower()) and term:
            continue
        if R"{}" in term:
            continue

        new_list.append(term)
    new_text = "\n".join(new_list)
    new_text = new_text.replace(",,", ",")
    new_text = re.sub(R"\/+", "//", new_text)
    return new_text
