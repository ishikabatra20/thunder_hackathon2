class JSError(Exception):
    pass

class JSReferenceError(JSError):
    pass

class JSSyntaxError(JSError):
    pass

class JSTypeError(JSError):
    pass

class JSRangeError(JSError):
    pass

class JSRuntimeLimit(JSError):
    pass
