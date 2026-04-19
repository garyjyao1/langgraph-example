import ast
import logging
import operator

logger = logging.getLogger(__name__)

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval(node.operand))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def calculate_math_expression(expression: str) -> str:
    """Evaluates an arithmetic expression and returns the result.
    Supports +, -, *, /, //, %, ** and parentheses. Example: '2 + 2', '(3 * 4) / 2'."""
    logger.info("Evaluating math expression: %s", expression)
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval(tree)
        return str(result)
    except Exception as e:
        return f"Invalid expression '{expression}': {e}"
