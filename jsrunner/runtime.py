from .lexer import lex
from .parser import Parser
from .interpreter import Interpreter

def run_js(source: str, step_limit=200000):
    tokens = lex(source)
    #print(tokens)
    parser = Parser(tokens)
    ast = parser.parse()
    intrp = Interpreter(step_limit=step_limit)
    intrp.run(ast)
    # stdout already printed via console.log; but return captured lines for tests
    return intrp

