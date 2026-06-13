from . import ast_nodes as A
from .environment import Environment
from .stdlib import UNDEFINED, is_truthy, to_number, to_string, strict_eq, loose_eq, make_console, wrap_array, make_math, JSDate, string_methods
from .errors import JSTypeError, JSRuntimeLimit

class ReturnSignal(Exception):
    def __init__(self, value): self.value = value

class BreakSignal(Exception): pass
class ContinueSignal(Exception): pass

class FunctionValue:
    def __init__(self, params, body, env, is_arrow=False):
        self.params = params
        self.body = body
        self.env = env
        self.is_arrow = is_arrow
    def call_scoped(self, intrp, args):
        local = Environment(self.env)
        # params (rest support)
        pi = 0; ai = 0
        while pi < len(self.params):
            p = self.params[pi]
            if p.is_rest:
                local.declare(p.id.name, args[ai:], constant=False)
                ai = len(args)
                pi += 1
                break
            else:
                val = args[ai] if ai < len(args) else UNDEFINED
                local.declare(p.id.name, val, constant=False)
                ai += 1; pi += 1
        # extra args ignored
        try:
            val = intrp.exec_block(self.body, local)
        except ReturnSignal as r:
            return r.value
        return UNDEFINED

def is_array(obj):
    return isinstance(obj, dict) and "_array" in obj and isinstance(obj["_array"], list)

class Interpreter:
    def __init__(self, step_limit=200000):
        self.global_env = Environment()
        self.captured = []
        # inject globals
        self.global_env.declare("console", {"log": make_console(self.captured)["log"]}, constant=True)
        self.global_env.declare("Math", make_math(), constant=True)
        self.global_env.declare("Date", JSDate, constant=True)
        self.global_env.declare("undefined", UNDEFINED, constant=True)
        self.steps = 0
        self.step_limit = step_limit

    def step(self, count=1):
        self.steps += count
        if self.steps > self.step_limit:
            raise JSRuntimeLimit("Execution step limit exceeded")

    def run(self, program: A.Program):
        self.steps = 0
        val = self.exec_program(program, self.global_env)
        return val

    def exec_program(self, prog, env):
        self.step()
        for stmt in prog.body:
            self.exec_stmt(stmt, env)

    def exec_block(self, block, env):
        self.step()
        for stmt in block.body:
            self.exec_stmt(stmt, env)

    def exec_stmt(self, node, env):
        self.step()
        if isinstance(node, A.BlockStatement):
            new_env = Environment(env)
            return self.exec_block(node, new_env)
        if isinstance(node, A.VariableDeclaration):
            for d in node.declarations:
                val = self.eval_expr(d.init, env) if d.init is not None else UNDEFINED
                env.declare(d.id.name, val, constant=(node.kind=="const"))
            return
        if isinstance(node, A.ExpressionStatement):
            self.eval_expr(node.expression, env); return
        if isinstance(node, A.IfStatement):
            if is_truthy(self.eval_expr(node.test, env)):
                return self.exec_stmt(node.consequent, env)
            elif node.alternate:
                return self.exec_stmt(node.alternate, env)
            return
        if isinstance(node, A.WhileStatement):
            while is_truthy(self.eval_expr(node.test, env)):
                try:
                    self.exec_stmt(node.body, env)
                except BreakSignal: break
                except ContinueSignal: continue
            return
        if isinstance(node, A.DoWhileStatement):
            while True:
                try:
                    self.exec_stmt(node.body, env)
                except BreakSignal: break
                except ContinueSignal: pass
                if not is_truthy(self.eval_expr(node.test, env)):
                    break
            return
        if isinstance(node, A.ForStatement):
            # For init may be decl or expr or None
            if node.init:
                if isinstance(node.init, A.VariableDeclaration):
                    self.exec_stmt(node.init, env)
                else:
                    self.eval_expr(node.init, env)
            while True:
                if node.test and not is_truthy(self.eval_expr(node.test, env)): break
                try:
                    self.exec_stmt(node.body, env)
                except BreakSignal: break
                except ContinueSignal: pass
                if node.update: self.eval_expr(node.update, env)
            return
        if isinstance(node, A.SwitchStatement):
            disc = self.eval_expr(node.discriminant, env)
            matched = False
            for case in node.cases:
                if case.test is None:
                    matched = matched or True
                else:
                    if strict_eq(self.eval_expr(case.test, env), disc) or self.eval_expr(case.test, env)==disc:
                        matched = True
                if matched:
                    for st in case.consequent:
                        try:
                            self.exec_stmt(st, env)
                        except BreakSignal:
                            matched = False
                            break
            return
        if isinstance(node, A.FunctionDeclaration):
            fn = FunctionValue(node.params, node.body, env, is_arrow=False)
            env.declare(node.id.name, fn, constant=True)
            return
        if isinstance(node, A.ReturnStatement):
            val = self.eval_expr(node.argument, env) if node.argument else UNDEFINED
            raise ReturnSignal(val)
        if isinstance(node, A.BreakStatement):
            raise BreakSignal()
        if isinstance(node, A.ContinueStatement):
            raise ContinueSignal()
        raise JSTypeError(f"Unknown statement: {type(node)}")

    def eval_expr(self, node, env):
        self.step()
        if node is None: return UNDEFINED
        if isinstance(node, A.Literal):
            return node.value
        if isinstance(node, A.Identifier):
            return env.get(node.name)
        
        if isinstance(node, A.UpdateExpression):
            if not isinstance(node.argument, A.Identifier):
                raise JSTypeError("Invalid update target")

            name = node.argument.name
            old = env.get(name)

            if node.operator == "++":
                new = to_number(old) + 1
            else:
                new = to_number(old) - 1

            env.set(name, new)

            return new if node.prefix else old
    

        if isinstance(node, A.AssignmentExpression):
            if node.left.__class__ is A.Identifier:
                name = node.left.name
                if node.operator == "=":
                    val = self.eval_expr(node.right, env)
                else:
                    cur = env.get(name)
                    rhs = self.eval_expr(node.right, env)
                    val = self.apply_assign_op(node.operator, cur, rhs)
                env.set(name, val); return val
            if isinstance(node.left, A.MemberExpression):
                obj, key = self.eval_member_lhs(node.left, env)
                if node.operator == "=":
                    val = self.eval_expr(node.right, env)
                else:
                    cur = obj[key] if key in obj else UNDEFINED
                    rhs = self.eval_expr(node.right, env)
                    val = self.apply_assign_op(node.operator, cur, rhs)
                obj[key] = val
                return val
            raise JSTypeError("Invalid left-hand side in assignment")
        if isinstance(node, A.BinaryExpression):
            l = self.eval_expr(node.left, env)
            r = self.eval_expr(node.right, env)
            op = node.operator
            if op == "+": 
                # string concat if any is string (JS-like)
                if isinstance(l, str) or isinstance(r, str):
                    return to_string(l) + to_string(r)
                return to_number(l) + to_number(r)
            if op == "-": return to_number(l) - to_number(r)
            if op == "*": return to_number(l) * to_number(r)
            if op == "**": return to_number(l) ** to_number(r)   
            if op == "/": return to_number(l) / to_number(r)
            if op == "%": return to_number(l) % to_number(r)
            if op == "===": return strict_eq(l, r)
            if op == "!==": return not strict_eq(l, r)
            if op == "==": return loose_eq(l, r)
            if op == "!=": return not loose_eq(l, r)
            if op == "<": return to_number(l) < to_number(r) if not (isinstance(l,str) or isinstance(r,str)) else to_string(l) < to_string(r)
            if op == ">": return to_number(l) > to_number(r) if not (isinstance(l,str) or isinstance(r,str)) else to_string(l) > to_string(r)
            if op == "<=": return to_number(l) <= to_number(r) if not (isinstance(l,str) or isinstance(r,str)) else to_string(l) <= to_string(r)
            if op == ">=": return to_number(l) >= to_number(r) if not (isinstance(l,str) or isinstance(r,str)) else to_string(l) >= to_string(r)
            if op in ("&&","||"):
                return self.logical(op, l, lambda: self.eval_expr(node.right, env))
            raise JSTypeError(f"Unsupported operator {op}")
        if isinstance(node, A.UnaryExpression):
            v = self.eval_expr(node.argument, env)
            if node.operator == "!": return not is_truthy(v)
            if node.operator == "+": return to_number(v)
            if node.operator == "-": return -to_number(v)
            if node.operator == "typeof":
                return self.typeof(v)
            raise JSTypeError(f"Unsupported unary {node.operator}")
        if isinstance(node, A.MemberExpression):
            obj = self.eval_expr(node.object, env)
            prop = self.eval_expr(node.property, env) if node.computed else node.property.name
            return self.get_prop(obj, prop)
        if isinstance(node, A.CallExpression):
            callee = self.eval_expr(node.callee, env)
            args = [self.eval_expr(a, env) for a in node.arguments]
            return self.call(callee, args)
        if isinstance(node, A.ObjectExpression):
            obj = {}
            for p in node.properties:
                if isinstance(p.value, A.SpreadElement):
                    spread_val = self.eval_expr(p.value.argument, env)
                    if isinstance(spread_val, dict):
                        obj.update(spread_val)
                    else:
                        raise JSTypeError("Spread expects object")
                else:
                    key = p.key.name if isinstance(p.key, A.Identifier) else p.key.value
                    val = self.eval_expr(p.value, env)
                    obj[key] = val
            return obj
        if isinstance(node, A.ArrayExpression):
            arr=[]
            for el in node.elements:
                if el is None:
                    arr.append(UNDEFINED)
                elif isinstance(el, A.SpreadElement):
                    v = self.eval_expr(el.argument, env)
                    if isinstance(v, list):
                        arr.extend(v)
                    elif is_array(v):
                        arr.extend(v["_array"])
                    else:
                        raise JSTypeError("Spread in array expects iterable")
                else:
                    arr.append(self.eval_expr(el, env))
            return arr
        if isinstance(node, A.FunctionExpression):
            return FunctionValue(node.params, node.body, env, is_arrow=node.is_arrow)
        raise JSTypeError(f"Unknown expression: {type(node)}")

    def logical(self, op, left_value, right_thunk):
        if op == "&&":
            return right_thunk() if is_truthy(left_value) else left_value
        if op == "||":
            return left_value if is_truthy(left_value) else right_thunk()
        return UNDEFINED

    def typeof(self, v):
        if v is UNDEFINED: return "undefined"
        if v is None: return "object"
        if isinstance(v, bool): return "boolean"
        if isinstance(v, (int,float)): return "number"
        if isinstance(v, str): return "string"
        if isinstance(v, FunctionValue): return "function"
        if is_array(v) or isinstance(v, list): return "object"
        if isinstance(v, dict): return "object"
        return "object"

    def apply_assign_op(self, op, cur, rhs):
        if op == "+=":
            if isinstance(cur, str) or isinstance(rhs, str):
                return to_string(cur) + to_string(rhs)
            return to_number(cur) + to_number(rhs)
        if op == "-=": return to_number(cur) - to_number(rhs)
        if op == "*=": return to_number(cur) * to_number(rhs)
        if op == "/=": return to_number(cur) / to_number(rhs)
        if op == "%=": return to_number(cur) % to_number(rhs)
        raise JSTypeError(f"Unsupported assignment operator {op}")

    def get_prop(self, obj, prop):
        # strings expose methods
        if isinstance(obj, str):
            m = string_methods(obj)
            if prop in m: return m[prop]
            if prop == "length": return len(obj)
            return UNDEFINED
        # arrays as Python list with methods via wrapper facade on demand
        if isinstance(obj, list):
            methods = wrap_array(obj)
            if prop == "length": return len(obj)
            if prop in methods: return methods[prop]
            # numeric index
            if isinstance(prop, int): 
                return obj[prop] if 0 <= prop < len(obj) else UNDEFINED
            # string index that is numeric
            if isinstance(prop, str) and prop.isdigit():
                idx = int(prop); return obj[idx] if 0 <= idx < len(obj) else UNDEFINED
            return UNDEFINED
        # our array facade
        if is_array(obj):
            if prop == "length": return len(obj["_array"])
            if prop in obj: return obj[prop]
            return UNDEFINED
        # function special props
        if isinstance(obj, FunctionValue):
            if prop == "length": return len([p for p in obj.params if not p.is_rest])
            return UNDEFINED
        # normal object
        if isinstance(obj, dict):
            return obj.get(prop, UNDEFINED)
        # class like Date
        return getattr(obj, prop, UNDEFINED)

    def eval_member_lhs(self, member: A.MemberExpression, env):
        obj = self.eval_expr(member.object, env)
        key = self.eval_expr(member.property, env) if member.computed else member.property.name
        if isinstance(obj, list):
            if isinstance(key, str) and key.isdigit(): key = int(key)
            if isinstance(key, int) and (key < 0 or key > len(obj)+100000):
                raise JSTypeError("Invalid array index")
            return obj, key
        if isinstance(obj, dict):
            return obj, key
        raise JSTypeError("Cannot set property on non-object")

    def call(self, callee, args):
        # Native: JSDate constructor
        if callee is JSDate:
            return JSDate(*args)
        # console.log
        if isinstance(callee, dict) and "log" in callee:
            return callee["log"](*args)
        if callable(callee) and not isinstance(callee, FunctionValue):
            return callee(*args)
        if isinstance(callee, FunctionValue):
            return callee.call_scoped(self, args)
        raise JSTypeError("Not a function")
