from dataclasses import dataclass
from .errors import JSReferenceError, JSTypeError

@dataclass
class Binding:
    value: object
    constant: bool

class Environment:
    def __init__(self, outer=None):
        self.outer = outer
        self.bindings = {}

    def declare(self, name, value, constant=False):
        if name in self.bindings:
            raise JSTypeError(f"Identifier '{name}' has already been declared")
        self.bindings[name] = Binding(value, constant)

    def set(self, name, value):
        if name in self.bindings:
            b = self.bindings[name]
            if b.constant:
                raise JSTypeError(f"Assignment to constant variable '{name}'")
            b.value = value
            return
        if self.outer:
            self.outer.set(name, value)
            return
        raise JSReferenceError(f"{name} is not defined")

    def get(self, name):
        if name in self.bindings:
            return self.bindings[name].value
        if self.outer:
            return self.outer.get(name)
        raise JSReferenceError(f"{name} is not defined")
