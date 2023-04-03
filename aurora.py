"""
     d888888
    d88P aaa  888  888  888d88  .d88b.   888d88   8888b.
   d88P  aaa  888  888  888P   d88^^88b  888P        88b
  d88P   aaa  888  888  888    888  888  888    .d888888
 d8888888888  Y88b 888  888    Y88..88P  888    888  888
d88P     aaa    Y88888  888      Y88P    888     Y888888
-- Copyright © 2023 Zandercraft. All rights reserved. --

Purpose: Main implementation of Aurora
"""

# Imports
from internal.term_utils import point_at

####################
# CONSTANTS
####################
DIGITS = "0123456789"


####################
# ERRORS
####################
class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f'{self.error_name}: {self.details}\n'
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        result += f'\n{point_at(self.pos_start.ftxt, self.pos_start, self.pos_end)}'
        return result


class IllegalCharErr(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'IllegalCharacter', details)


class InvalidSyntaxErr(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'InvalidSyntax', details)


class RuntimeErr(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, 'RuntimeErr', details)
        self.context = context

    def as_string(self):
        result = self.generate_traceback()
        result += f'{self.error_name}: {self.details}\n'
        result += f'\n{point_at(self.pos_start.ftxt, self.pos_start, self.pos_end)}'
        return result

    def generate_traceback(self):
        result = ''
        pos = self.pos_start
        context = self.context

        while context:
            result = f'    File {pos.fn} line {str(pos.ln + 1)}, in {context.display_name}\n' + result
            pos = context.parent_entry_pos
            context = context.parent

        return f"Traceback (most recent call last):\n" \
               f"{result}"


####################
# POSITION
####################
class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)


####################
# TOKENS
####################
# Token types
TT_INT = "INT"
TT_FLOAT = "FLOAT"
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_EOF = "EOF"


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end

    def __repr__(self):
        """
        Will return "type:value" if a value exists. Otherwise, just "type".
        """
        return f"<{self.type}:{self.value}>" if self.value else f"<{self.type}>"


####################
# LEXER
####################
class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char is not None:
            if self.current_char in ' \t':
                # Ignore spaces and tabs
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharErr(pos_start, self.pos, "'" + char + "'")

        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    def make_number(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in (DIGITS + '.'):
            if self.current_char == '.':
                if dot_count == 1:
                    break  # Break if multiple dots.
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)


####################
# NODES
####################
class NumberNode:
    def __init__(self, token):
        self.token = token
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end

    def __repr__(self):
        return f"{self.token}"


class BinaryOperationNode:
    def __init__(self, left_node, operation, right_node):
        self.left_node = left_node
        self.operation = operation
        self.right_node = right_node
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f"({self.left_node}, {self.operation}, {self.right_node})"


class UnaryOperationNode:
    def __init__(self, operation, node):
        self.operation = operation
        self.node = node
        self.pos_start = self.operation.pos_start
        self.pos_end = self.node.pos_end

    def __repr__(self):
        return f'({self.operation}, {self.node})'


####################
# PARSER RESULT
####################
class ParsedResult:
    def __init__(self):
        self.error = None
        self.node = None

    def register(self, result):
        if isinstance(result, ParsedResult):
            if result.error:
                self.error = result.error
            return result.node
        return result

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        self.error = error
        return self


####################
# RUNTIME RESULT
####################
class RuntimeResult:
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, result):
        if result.error:
            self.error = result.error
        return result.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self


####################
# PARSER
####################
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_idx = -1
        self.current_token = None
        self.advance()

    def advance(self):
        self.token_idx += 1
        if self.token_idx < len(self.tokens):
            self.current_token = self.tokens[self.token_idx]
        return self.current_token

    def parse(self):
        result = self.expr()
        if not result.error and self.current_token.type != TT_EOF:
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected '+', '-', '*', or '/'"
            ))
        return result

    def factor(self):
        result = ParsedResult()
        token = self.current_token

        if token.type in (TT_PLUS, TT_MINUS):
            result.register(self.advance())
            factor = result.register(self.factor())
            if result.error:
                return result
            return result.success(UnaryOperationNode(token, factor))
        elif token.type in (TT_INT, TT_FLOAT):
            result.register(self.advance())
            return result.success(NumberNode(token))
        elif token.type == TT_LPAREN:
            result.register(self.advance())
            expr = result.register(self.expr())
            if result.error:
                return result
            if self.current_token.type == TT_RPAREN:
                result.register(self.advance())
                return result.success(expr)
            else:
                return result.failure(InvalidSyntaxErr(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected ')'"
                ))

        return result.failure(InvalidSyntaxErr(token.pos_start, token.pos_end, "Expected int or float"))

    def term(self):
        return self.binary_operation(self.factor, (TT_MUL, TT_DIV))

    def expr(self):
        return self.binary_operation(self.term, (TT_PLUS, TT_MINUS))

    def binary_operation(self, func, operations):
        result = ParsedResult()
        left = result.register(func())
        if result.error:
            return result

        while self.current_token.type in operations:
            operation = self.current_token
            result.register(self.advance())
            right = result.register(func())
            if result.error:
                return result
            left = BinaryOperationNode(left, operation, right)

        return result.success(left)


####################
# VALUES
####################
class Number:
    def __init__(self, value):
        self.value = value
        self.pos_start = None
        self.pos_end = None
        self.context = None

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def added_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None

    def subtracted_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None

    def multiplied_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None

    def divided_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RuntimeErr(
                    other.pos_start,
                    other.pos_end,
                    "Division by zero",
                    self.context
                )
            return Number(self.value / other.value).set_context(self.context), None

    def __repr__(self):
        return str(self.value)


####################
# CONTEXT
####################
class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos


####################
# INTERPRETER
####################
class Interpreter:
    def visit(self, node, context):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f"No visit_{type(node).__name__} method defined")

    def visit_NumberNode(self, node, context):
        return RuntimeResult().success(Number(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end))

    def visit_BinaryOperationNode(self, node, context):
        rt_result = RuntimeResult()
        left = rt_result.register(self.visit(node.left_node, context))
        if rt_result.error:
            return rt_result
        right = rt_result.register(self.visit(node.right_node, context))
        if rt_result.error:
            return rt_result

        if node.operation.type == TT_PLUS:
            result, error = left.added_to(right)
        if node.operation.type == TT_MINUS:
            result, error = left.subtracted_by(right)
        if node.operation.type == TT_MUL:
            result, error = left.multiplied_by(right)
        if node.operation.type == TT_DIV:
            result, error = left.divided_by(right)

        if error:
            return rt_result.failure(error)
        return rt_result.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOperationNode(self, node: UnaryOperationNode, context):
        result = RuntimeResult()
        number = result.register(self.visit(node.node, context))
        if result.error:
            return result

        if node.operation.type == TT_MINUS:
            number, error = number.multiplied_by(Number(-1))

        if error:
            return result.failure(error)
        return number.set_pos(node.pos_start, node.pos_end)


####################
# RUNNER
####################
def evaluate(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error

    if error:
        return None, error

    # Generate the abstract syntax tree
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error:
        return None, ast.error

    # Run the program
    interpreter = Interpreter()
    context = Context("<program>")
    result = interpreter.visit(ast.node, context)

    return result.value, result.error
