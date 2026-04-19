import logging

from fastmcp import FastMCP

logger = logging.getLogger(__name__)
mcp = FastMCP("Math Server", instructions="A math utility server.")


def _add(a: float, b: float) -> float:
    """Add two numbers."""
    logger.debug("Adding %s and %s", a, b)
    return a + b


def _subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


def _multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def _divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b


def _power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    return base**exponent


def _sqrt(a: float) -> float:
    """Calculate the square root of a number."""
    if a < 0:
        raise ValueError("Cannot take square root of a negative number.")
    return a**0.5


def _modulo(a: float, b: float) -> float:
    """Calculate a mod b."""
    if b == 0:
        raise ValueError("Cannot modulo by zero.")
    return a % b


def _factorial(n: int) -> int:
    """Calculate the factorial of a non-negative integer."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


# MCP tools
mcp.tool()(_add)
mcp.tool()(_subtract)
mcp.tool()(_multiply)
mcp.tool()(_divide)
mcp.tool()(_power)
mcp.tool()(_sqrt)
mcp.tool()(_modulo)
mcp.tool()(_factorial)

math_tools = [_add, _subtract, _multiply, _divide, _power, _sqrt, _modulo, _factorial]
