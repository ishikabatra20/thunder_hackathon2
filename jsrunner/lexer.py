import re
from .tokens import Token
from .errors import JSSyntaxError

KEYWORDS = {
    "let","const","var","if","else","while","do","for","of","in","switch","case","default",
    "break","continue","function","return","true","false","null","undefined","new",
    "this","typeof","instanceof","void","delete","try","catch","finally","throw","class",
    "super","yield","await"
}

TOKEN_SPEC = [
    ("WHITESPACE", r"[ \t]+"),
    ("COMMENT", r"//[^\n]*"),
    ("MCOMMENT", r"/\*[\s\S]*?\*/"),
    ("NUMBER", r"(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?"),
    ("STRING", r"'(?:\\.|[^'])*'|\"(?:\\.|[^\"])*\""),
    ("TEMPLATE_START", r"`"),
    ("ELLIPSIS", r"\.\.\."),
    ("OP", r"\*\*|===|!==|==|!=|<=|>=|\+\+|--|=>|\|\||&&|<<|>>|>>>|\+=|-=|\*=|/=|%=|\+|-|\*|/|%|<|>|=|!|\?|:|~|\^|&|\|"),
    ("PUNC", r"[{}\[\]().,;]"),
    ("IDENT", r"[A-Za-z_$][A-Za-z0-9_$]*"),
    ("NEWLINE", r"\n"),
]

MASTER = re.compile("|".join(f"(?P<{name}>{regex})" for name, regex in TOKEN_SPEC))

ESCAPE_MAP = {
    "n":"\n","r":"\r","t":"\t","b":"\b","f":"\f","v":"\v","0":"\0","\\":"\\","'":"'",
    '"':'"','`':'`'
}

def unescape_string(s):
    if s[0] == s[-1] and s[0] in ("'", '"'):
        body = s[1:-1]
        def repl(m):
            ch = m.group(1)
            return ESCAPE_MAP.get(ch, ch)
        return re.sub(r"\\(.)", repl, body)
    return s

def lex(src):
    tokens = []
    line = 1
    col = 1
    i = 0
    n = len(src)
    in_template = False
    template_buf = ""

    while i < n:
        m = MASTER.match(src, i)
        if not m:
            raise JSSyntaxError(f"Unexpected character {src[i]!r} at {line}:{col}")
        kind = m.lastgroup
        text = m.group(kind)
        start = i
        i = m.end()

        if kind in ("WHITESPACE","COMMENT","MCOMMENT"):
            col += len(text)
            continue
        if kind == "NEWLINE":
            line += 1
            col = 1
            continue

        if kind == "STRING":
            val = unescape_string(text)
            tokens.append(Token("STRING", val, line, col))
        elif kind == "NUMBER":
            tokens.append(Token("NUMBER", text, line, col))
        elif kind == "IDENT":
            ttype = "KEYWORD" if text in KEYWORDS else "IDENT"
            tokens.append(Token(ttype, text, line, col))
        elif kind == "PUNC":
            tokens.append(Token(text, text, line, col))
        elif kind == "OP":
            tokens.append(Token(text, text, line, col))
        elif kind == "ELLIPSIS":
            tokens.append(Token("ELLIPSIS", text, line, col))
        elif kind == "TEMPLATE_START":
            # Minimal template literal (no ${} interpolation in this version)
            # Consume until next `
            end = src.find("`", i)
            if end == -1:
                raise JSSyntaxError(f"Unterminated template literal at {line}:{col}")
            body = src[i:end]
            i = end + 1
            tokens.append(Token("STRING", body, line, col))
        else:
            tokens.append(Token(kind, text, line, col))

        col += (i - start)
    tokens.append(Token("EOF","",line,col))
    return tokens
