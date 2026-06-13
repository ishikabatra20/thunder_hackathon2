from dataclasses import dataclass
from typing import List, Optional, Any



@dataclass
class Node: pass
#ad
@dataclass
class UpdateExpression(Node):
    operator: str
    argument: Node
    prefix: bool

@dataclass
class Program(Node):
    body: List[Node]

@dataclass
class BlockStatement(Node):
    body: List[Node]

@dataclass
class VariableDeclaration(Node):
    kind: str  # 'let' or 'const'
    declarations: List["VariableDeclarator"]

@dataclass
class VariableDeclarator(Node):
    id: "Identifier"
    init: Optional[Node]

@dataclass
class Identifier(Node):
    name: str

@dataclass
class Literal(Node):
    value: Any  # number, string, boolean, None (null), 'undefined' sentinel

@dataclass
class ExpressionStatement(Node):
    expression: Node

@dataclass
class BinaryExpression(Node):
    operator: str
    left: Node
    right: Node

@dataclass
class UnaryExpression(Node):
    operator: str
    argument: Node
    prefix: bool = True

@dataclass
class AssignmentExpression(Node):
    operator: str
    left: Node
    right: Node

@dataclass
class MemberExpression(Node):
    object: Node
    property: Node
    computed: bool  # obj[prop] vs obj.prop

@dataclass
class CallExpression(Node):
    callee: Node
    arguments: List[Node]

@dataclass
class IfStatement(Node):
    test: Node
    consequent: Node
    alternate: Optional[Node]

@dataclass
class WhileStatement(Node):
    test: Node
    body: Node

@dataclass
class DoWhileStatement(Node):
    body: Node
    test: Node

@dataclass
class ForStatement(Node):
    init: Optional[Node]
    test: Optional[Node]
    update: Optional[Node]
    body: Node

@dataclass
class SwitchCase(Node):
    test: Optional[Node]
    consequent: List[Node]

@dataclass
class SwitchStatement(Node):
    discriminant: Node
    cases: List[SwitchCase]

@dataclass
class FunctionDeclaration(Node):
    id: Identifier
    params: List["Param"]
    body: BlockStatement
    is_arrow: bool = False

@dataclass
class FunctionExpression(Node):
    id: Optional[Identifier]
    params: List["Param"]
    body: BlockStatement
    is_arrow: bool = False

@dataclass
class ReturnStatement(Node):
    argument: Optional[Node]

@dataclass
class BreakStatement(Node): pass

@dataclass
class ContinueStatement(Node): pass

@dataclass
class ObjectProperty(Node):
    key: Node  # Identifier or Literal
    value: Node

@dataclass
class ObjectExpression(Node):
    properties: List[ObjectProperty]

@dataclass
class ArrayExpression(Node):
    elements: List[Node]  # supports None holes and SpreadElement

@dataclass
class Param(Node):
    id: Identifier
    is_rest: bool = False

@dataclass
class SpreadElement(Node):
    argument: Node
