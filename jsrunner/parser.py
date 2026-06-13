from typing import List, Optional
from .tokens import Token
from .errors import JSSyntaxError
from . import ast_nodes as A

# Pratt parser with precedence table
PRECEDENCE = {
    "||": 1, "&&": 2, "|":3, "^":4, "&":5,
    "==":6,"!=":6,"===":6,"!==":6,
    "<":7,"<=":7,">":7,">=":7,
    "<<":8,">>":8,">>>":8,
    "+":9,"-":9,
    "*":10,"/":10,"%":10,
    "**": 11
}

ASSIGN_OPS = {"=","+=","-=","*=","/=","%="}

class Parser:
    def __init__(self, tokens: List[Token]):
        self.toks = tokens
        self.i = 0

    def peek(self): return self.toks[self.i]
    def next(self): 
        t = self.toks[self.i]
        self.i += 1
        return t
    def match(self, *types):
        if self.peek().type in types or self.peek().value in types:
            return self.next()
        return None
    def expect(self, typ, msg=None):
        t = self.peek()
        if not (t.type == typ or t.value == typ):
            raise JSSyntaxError(msg or f"Expected {typ} at {t.line}:{t.col}, got {t.type}({t.value})")
        return self.next()

    def parse(self):
        body = []
        while self.peek().type != "EOF":
            body.append(self.parse_statement())
        return A.Program(body)

    def parse_statement(self):
        t = self.peek()
        if t.type == "KEYWORD":
            if t.value in ("let","const","var"):
                return self.parse_var_decl()
            if t.value == "if":
                return self.parse_if()
            if t.value == "while":
                return self.parse_while()
            if t.value == "do":
                return self.parse_dowhile()
            if t.value == "for":
                return self.parse_for()
            if t.value == "function":
                return self.parse_function_decl()
            if t.value == "return":
                return self.parse_return()
            if t.value == "break":
                self.next(); self.match(";")
                return A.BreakStatement()
            if t.value == "continue":
                self.next(); self.match(";")
                return A.ContinueStatement()
            if t.value == "switch":
                return self.parse_switch()
        if t.value == "{":
            return self.parse_block()
        # default: expression statement
        expr = self.parse_expression()
        self.match(";")
        return A.ExpressionStatement(expr)

    def parse_block(self):
        self.expect("{")
        body = []
        while self.peek().value != "}":
            body.append(self.parse_statement())
        self.expect("}")
        return A.BlockStatement(body)

    def parse_var_decl(self):
        kind_tok = self.next()  # let/const/var (var treated as let)
        kind = "let" if kind_tok.value in ("let","var") else "const"
        decls = []
        while True:
            ident = self.expect("IDENT","Identifier expected")
            init = None
            if self.match("="):
                init = self.parse_expression()
            decls.append(A.VariableDeclarator(A.Identifier(ident.value), init))
            if not self.match(","):
                break
        self.match(";")
        return A.VariableDeclaration(kind, decls)

    def parse_if(self):
        self.expect("KEYWORD")  # if
        self.expect("(")
        test = self.parse_expression()
        self.expect(")")
        cons = self.parse_statement()
        alt = None
        if self.peek().type == "KEYWORD" and self.peek().value == "else":
            self.next()
            alt = self.parse_statement()
        return A.IfStatement(test, cons, alt)

    def parse_while(self):
        self.expect("KEYWORD")  # while
        self.expect("(")
        test = self.parse_expression()
        self.expect(")")
        body = self.parse_statement()
        return A.WhileStatement(test, body)

    def parse_dowhile(self):
        self.expect("KEYWORD")  # do
        body = self.parse_statement()
        self.expect("KEYWORD")  # while
        self.expect("(")
        test = self.parse_expression()
        self.expect(")")
        self.match(";")
        return A.DoWhileStatement(body, test)

    def parse_for(self):
        self.expect("KEYWORD")  # for
        self.expect("(")
        init = None
        if self.peek().value != ";":
            if self.peek().type=="KEYWORD" and self.peek().value in ("let","const","var"):
                init = self.parse_var_decl()
            else:
                init = self.parse_expression()
                self.match(";")
        else:
            self.expect(";")
        test = None
        if self.peek().value != ";":
            test = self.parse_expression()
        self.expect(";")
        update = None
        if self.peek().value != ")":
            update = self.parse_expression()
        self.expect(")")
        body = self.parse_statement()
        return A.ForStatement(init, test, update, body)

    def parse_switch(self):
        self.expect("KEYWORD")  # switch
        self.expect("(")
        disc = self.parse_expression()
        self.expect(")")
        self.expect("{")
        cases = []
        while self.peek().value != "}":
            if self.peek().type=="KEYWORD" and self.peek().value=="case":
                self.next()
                test = self.parse_expression()
                self.expect(":")
                cons=[]
                while self.peek().value not in ("case","default","}"):
                    cons.append(self.parse_statement())
                cases.append(A.SwitchCase(test, cons))
            elif self.peek().type=="KEYWORD" and self.peek().value=="default":
                self.next(); self.expect(":")
                cons=[]
                while self.peek().value not in ("case","default","}"):
                    cons.append(self.parse_statement())
                cases.append(A.SwitchCase(None, cons))
            else:
                raise JSSyntaxError("Expected case/default")
        self.expect("}")
        return A.SwitchStatement(disc, cases)

    def parse_function_decl(self):
        self.expect("KEYWORD")  # function
        ident = self.expect("IDENT","Function name expected")
        params = self.parse_params()
        body = self.parse_block()
        return A.FunctionDeclaration(A.Identifier(ident.value), params, body, is_arrow=False)

    def parse_params(self):
        self.expect("(")
        params=[]
        if self.peek().value != ")":
            while True:
                is_rest = False
                if self.match("ELLIPSIS"):
                    is_rest = True
                ident = self.expect("IDENT","Parameter name expected")
                params.append(A.Param(A.Identifier(ident.value), is_rest=is_rest))
                if not self.match(","):
                    break
        self.expect(")")
        return params

    def parse_expression(self):
        return self.parse_assignment()

    def parse_assignment(self):
        left = self.parse_binary(1)
        if self.peek().value in ASSIGN_OPS:
            op = self.next().value
            right = self.parse_assignment()
            return A.AssignmentExpression(op, left, right)
        return left

    def parse_binary(self, prec_min):
        left = self.parse_unary()
        while True:
            op = self.peek().value
            if op not in PRECEDENCE: break
            prec = PRECEDENCE[op]
            if prec < prec_min: break
            self.next()
            right = self.parse_binary(prec + 1)
            left = A.BinaryExpression(op, left, right)
        return left

    def parse_unary(self):
        t = self.peek().value
        if t in ("+","-","!","typeof","++","--"):
            op = self.next().value
            arg = self.parse_unary()
            return A.UnaryExpression(op, arg, True)
        return self.parse_postfix()
    
    

    def parse_postfix(self):
        expr = self.parse_primary()
        while True:
            if self.peek().value in ("++", "--"):
                op = self.next().value
                expr = A.UpdateExpression(op, expr, False)
                continue
            if self.match("("):
                args=[]
               
                if self.peek().value != ")":
                    while True:
                        args.append(self.parse_expression())
                        if not self.match(","): break
                self.expect(")")
                expr = A.CallExpression(expr, args)
                continue
            if self.match("."):
                prop = self.expect("IDENT","Property name expected")
                expr = A.MemberExpression(expr, A.Identifier(prop.value), False)
                continue
            if self.match("["):
                prop = self.parse_expression()
                self.expect("]")
                expr = A.MemberExpression(expr, prop, True)
                continue
            break
        return expr

    def parse_primary(self):
        t = self.peek()
        if t.value == "(":
            self.next()
            expr = self.parse_expression()
            self.expect(")")
            return expr
        if t.type == "NUMBER":
            self.next()
            return A.Literal(float(t.value) if any(c in t.value for c in ".eE") else int(t.value))
        if t.type == "STRING":
            self.next()
            return A.Literal(t.value)
        if t.type == "KEYWORD":
            if t.value == "true":
                self.next(); return A.Literal(True)
            if t.value == "false":
                self.next(); return A.Literal(False)
            if t.value == "null":
                self.next(); return A.Literal(None)
            if t.value == "undefined":
                self.next(); return A.Literal(("__undefined__",))
            if t.value == "function":
                self.next()
                fid = None
                if self.peek().type=="IDENT":
                    fid = A.Identifier(self.next().value)
                params = self.parse_params()
                body = self.parse_block()
                return A.FunctionExpression(fid, params, body, is_arrow=False)
        if t.type == "IDENT":
            # arrow function or identifier
            # Lookahead for arrow: IDENT | (params) =>
            if self._is_arrow_start():
                return self.parse_arrow_function()
            name = self.next().value
            return A.Identifier(name)
        if t.value == "{":
            return self.parse_object_literal()
        if t.value == "[":
            return self.parse_array_literal()
        raise JSSyntaxError(f"Unexpected token {t.type}({t.value}) at {t.line}:{t.col}")

    def _is_arrow_start(self):
        # IDENT => or ( ... ) =>
        j = self.i
        t = self.toks
        if t[j].type=="IDENT":
            j += 1
            return t[j].value == "=>"
        if t[j].value == "(":
            depth = 1
            j += 1
            while depth and j < len(t):
                if t[j].value == "(": depth += 1
                elif t[j].value == ")": depth -= 1
                j += 1
            if j < len(t) and t[j].value == "=>":
                return True
        return False

    def parse_arrow_function(self):
        # params
        params=[]
        if self.peek().type=="IDENT":
            ident = self.next().value
            params=[A.Param(A.Identifier(ident))]
            self.expect("=>")
        else:
            self.expect("(")
            if self.peek().value != ")":
                while True:
                    is_rest = False
                    if self.match("ELLIPSIS"): is_rest = True
                    ident = self.expect("IDENT","Parameter name expected").value
                    params.append(A.Param(A.Identifier(ident), is_rest))
                    if not self.match(","): break
            self.expect(")")
            self.expect("=>")
        # body: expression or block
        if self.peek().value == "{":
            body = self.parse_block()
        else:
            expr = self.parse_expression()
            body = A.BlockStatement([A.ReturnStatement(expr)])
        return A.FunctionExpression(None, params, body, is_arrow=True)

    def parse_object_literal(self):
        self.expect("{")
        props=[]
        if self.peek().value != "}":
            while True:
                if self.match("ELLIPSIS"):
                    # Spread in objects not implemented in this version
                    key = A.Identifier("__spread__")
                    val = self.parse_expression()
                    props.append(A.ObjectProperty(key, A.SpreadElement(val)))
                else:
                    if self.peek().type == "IDENT":
                        keytoken = self.next()
                        key = A.Identifier(keytoken.value)
                    elif self.peek().type in ("STRING","NUMBER"):
                        lit = self.next()
                        key = A.Literal(lit.value if lit.type=="STRING" else lit.value)
                    else:
                        raise JSSyntaxError("Invalid object key")
                    if self.match(":"):
                        val = self.parse_expression()
                    else:
                        # shorthand
                        val = A.Identifier(key.name) if isinstance(key, A.Identifier) else A.Literal(key.value)
                    props.append(A.ObjectProperty(key, val))
                if not self.match(","): break
        self.expect("}")
        return A.ObjectExpression(props)
    
    def parse_return(self):
        self.expect("KEYWORD")  # return

        if self.peek().value == ";":
            self.next()
            return A.ReturnStatement(None)

        if self.peek().value == "}":
            return A.ReturnStatement(None)

        expr = self.parse_expression()
        self.match(";")

        return A.ReturnStatement(expr)

    def parse_array_literal(self):
        self.expect("[")
        elems=[]
        if self.peek().value != "]":
            while True:
                if self.match("ELLIPSIS"):
                    arg = self.parse_expression()
                    elems.append(A.SpreadElement(arg))
                elif self.peek().value == ",":
                    self.next()
                    elems.append(None)
                else:
                    elems.append(self.parse_expression())
                if not self.match(","): break
        self.expect("]")
        return A.ArrayExpression(elems)
