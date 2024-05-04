import ast
import operator
import math


def safe_eval(expr):
    allowed_operators = {
        ast.Add: operator.add,  # Addition
        ast.Sub: operator.sub,  # Subtraction
        ast.Mult: operator.mul,  # Multiplication
        ast.Div: operator.truediv,  # True division
        ast.Pow: operator.pow,  # Power operator
        ast.USub: operator.neg,  # Unary minus
    }

    # Use lower case for all function and constant names
    allowed_functions = {
        'sin': math.sin,  # Trigonometric functions
        'cos': math.cos,  # Trigonometric functions
        'tan': math.tan,  # Trigonometric functions
        'log': math.log,  # Natural logarithm
        'log10': math.log10,  # Base 10 logarithm
        'sqrt': math.sqrt,  # Square root
        'exp': math.exp,  # Exponential function
        'pi': math.pi,  # Math constant pi
        'e': math.e,  # Math constant e
    }

    def eval_(node):
        if isinstance(node, ast.Expression):
            return eval_(node.body)
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.UnaryOp):
            return allowed_operators[type(node.op)](eval_(node.operand))
        elif isinstance(node, ast.BinOp):
            return allowed_operators[type(node.op)](eval_(node.left), eval_(node.right))
        elif isinstance(node, ast.Name):
            # Normalize the name to lower case before checking
            normalized_name = node.id.lower()
            if normalized_name in allowed_functions:
                return allowed_functions[normalized_name]
        elif isinstance(node, ast.Call):
            # Normalize function name to lower case before checking
            normalized_func_name = node.func.id.lower()
            if normalized_func_name in allowed_functions:
                arguments = [eval_(arg) for arg in node.args]
                return allowed_functions[normalized_func_name](*arguments)
        raise TypeError(f"Unsupported type or operation: {type(node)}")

    tree = ast.parse(expr, mode='eval')
    return eval_(tree.body)


# Examples
# Sin(PI/2) + COS(0) = 2.0
# 2 * (3 + 4) = 14
# LOG10(100) = 2.0
# SQRT(16) = 4.0
# EXP(1) = 2.718281828459045
# E = 2.718281828459045
# PI = 3.141592653589793
# 2 * PI = 6.283185307179586
# -2 * PI = -6.283185307179586
# -SIN(PI) = 0.0
# TAN(PI/4) = 0.9999999999999999

