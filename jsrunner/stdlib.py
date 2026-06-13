import math, time, random
from datetime import datetime
from .errors import JSTypeError, JSRangeError

UNDEFINED = ("__undefined__",)

def to_number(v):
    if v is UNDEFINED: return float('nan')
    if v is None: return 0
    if v is True: return 1
    if v is False: return 0
    if isinstance(v, (int,float)): return v
    if isinstance(v, str):
        try:
            if v.strip()=="":
                return 0
            return float(v) if any(c in v for c in ".eE") else int(v)
        except:
            return float('nan')
    return float('nan')

def to_string(v):
    if v is UNDEFINED: return "undefined"
    if v is None: return "null"
    if v is True: return "true"
    if v is False: return "false"
    if isinstance(v, (int,float)):
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)
    if isinstance(v, list):
        return ",".join(to_string(x) for x in v)
    if isinstance(v, dict):
        return "[object Object]"
    return str(v)

def is_truthy(v):
    if v is UNDEFINED or v is None: return False
    if v is False: return False
    if v is True: return True
    if isinstance(v, (int,float)): return v != 0 and not (isinstance(v,float) and math.isnan(v))
    if isinstance(v, str): return len(v) > 0
    if isinstance(v, (list,dict)): return True
    return True

def strict_eq(a,b):
    # ===
    if a is UNDEFINED or b is UNDEFINED:
        return a is b
    if a is None or b is None:
        return a is b
    if type(a) != type(b): return False
    if isinstance(a, float) and math.isnan(a) and math.isnan(b):
        return False
    return a == b

def loose_eq(a,b):
    # ==
    # Handle null/undefined
    if (a is None and b is UNDEFINED) or (a is UNDEFINED and b is None): return True
    if a is None or a is UNDEFINED or b is None or b is UNDEFINED:
        return a is b
    # Number/String/Boolean coercion
    if isinstance(a, bool): a = 1 if a else 0
    if isinstance(b, bool): b = 1 if b else 0
    if isinstance(a, (int,float)) and isinstance(b, str): b = to_number(b)
    elif isinstance(a, str) and isinstance(b, (int,float)): a = to_number(a)
    return a == b

def make_console(captured):
    def log(*args):
        line = " ".join(to_string(a) for a in args)
        captured.append(line)
        print(line)
    return {"log": log}

def wrap_array(lst):
    # Provide methods similar to JS Array
    def check_index(i):
        if not isinstance(i, int): raise JSTypeError("Invalid array index")
        if i < 0 or i >= len(lst): return None
        return i

    def join(sep=","):
        return sep.join('' if v is None else to_string(v) for v in lst)

    def push(*items):
        for it in items: lst.append(it)
        return len(lst)

    def pop():
        if not lst: return UNDEFINED
        return lst.pop()

    def shift():
        if not lst: return UNDEFINED
        return lst.pop(0)

    def unshift(*items):
        for it in reversed(items):
            lst.insert(0, it)
        return len(lst)

    def slice_(start=0, end=None):
        n = len(lst)
        s = start if start is not None else 0
        if s < 0: s = max(n + s, 0)
        e = n if end is None else end
        if isinstance(e, int) and e < 0: e = max(n + e, 0)
        return lst[s:e]

    def splice(start, delete_count=None, *items):
        n = len(lst)
        s = start if start >=0 else max(n + start, 0)
        if delete_count is None:
            dc = n - s
        else:
            dc = max(0, min(delete_count, n - s))
        removed = []
        for _ in range(dc):
            removed.append(lst.pop(s))
        for idx, it in enumerate(items):
            lst.insert(s + idx, it)
        return removed

    def concat(*args):
        res = lst[:]
        for a in args:
            if isinstance(a, list):
                res.extend(a)
            else:
                res.append(a)
        return res

    def includes(x):
        return any(strict_eq(v, x) or v == x for v in lst)

    def indexOf(x):
        for i,v in enumerate(lst):
            if v == x: return i
        return -1

    def reverse():
        lst.reverse()
        return lst

    def sort(key=None):
        lst.sort(key=lambda v: to_string(v) if key is None else key(v))
        return lst

    def map_(fn):
        return [fn(v, i, lst) for i,v in enumerate(lst)]

    def filter_(fn):
        return [v for i,v in enumerate(lst) if is_truthy(fn(v,i,lst))]

    def reduce_(fn, initial=UNDEFINED):
        it = 0
        acc = None
        if initial is UNDEFINED:
            if not lst: raise JSRangeError("Reduce of empty array with no initial value")
            acc = lst[0]; it = 1
        else:
            acc = initial
        for i in range(it, len(lst)):
            acc = fn(acc, lst[i], i, lst)
        return acc

    def find(fn):
        for i,v in enumerate(lst):
            if is_truthy(fn(v,i,lst)): return v
        return UNDEFINED

    def some(fn):
        for i,v in enumerate(lst):
            if is_truthy(fn(v,i,lst)): return True
        return False

    def every(fn):
        for i,v in enumerate(lst):
            if not is_truthy(fn(v,i,lst)): return False
        return True

    return {
        "_array": lst,
        "join": join, "push": push, "pop": pop, "shift": shift, "unshift": unshift,
        "slice": slice_, "splice": splice, "concat": concat, "includes": includes, "indexOf": indexOf,
        "reverse": reverse, "sort": sort, "map": map_, "filter": filter_, "reduce": reduce_,
        "find": find, "some": some, "every": every
    }

def make_math():
    return {
        "PI": math.pi,
        "random": lambda: random.random(),
        "floor": lambda x: math.floor(x),
        "ceil": lambda x: math.ceil(x),
        "round": lambda x: round(x),
        "abs": lambda x: abs(x),
        "max": lambda *xs: max(xs),
        "min": lambda *xs: min(xs),
        "pow": lambda a,b: a**b,
        "sqrt": lambda x: math.sqrt(x)
    }

class JSDate:
    def __init__(self, *args):
        if not args:
            self.dt = datetime.fromtimestamp(time.time())
        else:
            # very simplified: Date(year, monthIndex, day, hours, minutes, seconds, ms)
            year = int(args[0])
            month = int(args[1]) if len(args)>1 else 0
            day = int(args[2]) if len(args)>2 else 1
            self.dt = datetime(year, month+1, day)
    def getFullYear(self): return self.dt.year
    def toString(self): return self.dt.isoformat(sep=" ")

def string_methods(s):
    return {
        "replace": lambda a,b: s.replace(a,b,1),
        "replaceAll": lambda a,b: s.replace(a,b),
        "substring": lambda a,b=None: s[a:b],
        "slice": lambda a,b=None: s[a:b],
        "split": lambda sep="": s.split(sep) if sep!="" else list(s),
        "trim": lambda : s.strip(),
        "toUpperCase": lambda : s.upper(),
        "toLowerCase": lambda : s.lower(),
        "includes": lambda sub: sub in s,
        "startsWith": lambda sub: s.startswith(sub),
        "endsWith": lambda sub: s.endswith(sub),
        "indexOf": lambda sub: s.find(sub)
    }
