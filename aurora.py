#      d888888
#     d88P aaa  888  888  888d88  .d88b.   888d88   8888b.
#    d88P  aaa  888  888  888P   d88^^88b  888P        88b
#   d88P   aaa  888  888  888    888  888  888    .d888888
#  d8888888888  Y88b 888  888    Y88..88P  888    888  888
# d88P     aaa    Y88888  888      Y88P    888     Y888888
# -- Copyright © 2023 Zandercraft. All rights reserved. --
"""
Purpose: Main implementation of Aurora
"""

# Imports
import string
from internal.term_utils import point_at

####################
# CONSTANTS
####################
DIGITS = "0123456789"
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS


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


class ExpectedCharErr(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'ExpectedCharacter', details)


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
            result = f'    File {pos.fn}, line {str(pos.ln + 1)}, in {context.display_name}\n' + result
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
TT_IDENTIFIER = "IDENTIFIER"
TT_KEYWORD = "KEYWORD"
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_POW = "POW"
TT_EQ = "EQ"
TT_EE = "EE"
TT_NE = "NE"
TT_LT = "LT"
TT_GT = "GT"
TT_LTE = "LTE"
TT_GTE = "GTE"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_COMMA = "COMMA"
TT_ARROW = "ARROW"
TT_EOF = "EOF"

KEYWORDS = [
    'set',
    'and',
    'or',
    'not',
    'if',
    'then',
    'eli',
    'else',
    'for',
    'to',
    'step',
    'while',
    'fun'
]


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end.copy()

    def matches(self, type_, value):
        return self.type == type_ and self.value == value

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
            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(self.make_dash_operators())
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == '^':
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == '!':
                token, error = self.make_not_equals()
                if error:
                    return [], error
                tokens.append(token)
            elif self.current_char == '=':
                tokens.append(self.make_equals())
                self.advance()
            elif self.current_char == '<':
                tokens.append(self.make_lt())
                self.advance()
            elif self.current_char == '>':
                tokens.append(self.make_gt())
                self.advance()
            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
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

    def make_dash_operators(self):
        token_type = TT_MINUS
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '>':
            self.advance()
            token_type = TT_ARROW

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_identifier(self):
        id_string = ''
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in (LETTERS_DIGITS + '_'):
            id_string += self.current_char
            self.advance()

        token_type = TT_KEYWORD if id_string in KEYWORDS else TT_IDENTIFIER
        return Token(token_type, id_string, pos_start, self.pos)

    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None

        self.advance()
        return None, ExpectedCharErr(pos_start, self.pos, "'=' after '!'")

    def make_equals(self):
        token_type = TT_EQ
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            token_type = TT_EE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_lt(self):
        token_type = TT_LT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            token_type = TT_LTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_gt(self):
        token_type = TT_GT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            token_type = TT_GTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)


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


class VarAccessNode:
    def __init__(self, var_name_token):
        self.var_name_token = var_name_token
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.var_name_token.pos_end


class VarAssignNode:
    def __init__(self, var_name_token, value_node):
        self.var_name_token = var_name_token
        self.value_node = value_node
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.var_name_token.pos_end


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


class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case
        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (self.else_case or self.cases[len(self.cases) - 1][0]).pos_end


class ForNode:
    def __init__(self, var_name_token, start_value_node, end_value_node, step_value_node, body_node):
        self.var_name_token = var_name_token
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node
        self.body_node = body_node
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.body_node.pos_end


class WhileNode:
    def __init__(self, condition_node, body_node):
        self.condition_node = condition_node
        self.body_node = body_node
        self.pos_start = condition_node.pos_start
        self.pos_end = body_node.pos_end


class FunDefNode:
    def __init__(self, var_name_token, arg_name_tokens, body_node):
        self.var_name_token = var_name_token
        self.arg_name_tokens = arg_name_tokens
        self.body_node = body_node
        if self.var_name_token:
            self.pos_start = self.var_name_token.pos_start
        elif len(self.arg_name_tokens) > 0:
            self.pos_start = self.arg_name_tokens[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start
        self.pos_end = self.body_node.pos_end


class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes
        self.pos_start = self.node_to_call.pos_start
        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end


####################
# PARSER RESULT
####################
class ParsedResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0

    def register_advancement(self):
        self.advance_count += 1

    def register(self, result):
        self.advance_count += result.advance_count
        if result.error:
            self.error = result.error
        return result.node

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.advance_count == 0:
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
                "Expected '+', '-', '*', '/', or '^'"
            ))
        return result

    def power(self):
        return self.binary_operation(self.call, (TT_POW,), self.factor)

    def call(self):
        result = ParsedResult()
        atom = result.register(self.atom())
        if result.error:
            return result

        if self.current_token.type == TT_LPAREN:
            result.register_advancement()
            self.advance()

            arg_nodes = []

            if self.current_token.type == TT_RPAREN:
                result.register_advancement()
                self.advance()
            else:
                arg_nodes.append(result.register(self.expr()))
                if result.error:
                    return result.failure(InvalidSyntaxErr(
                        self.current_token.pos_start,
                        self.current_token.pos_end,
                        "Expected ')', 'set', 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '(' or "
                        "'not'"
                    ))

                while self.current_token.type == TT_COMMA:
                    result.register_advancement()
                    self.advance()

                    arg_nodes.append(result.register(self.expr()))
                    if result.error:
                        return result

                if self.current_token.type != TT_RPAREN:
                    return result.failure(InvalidSyntaxErr(
                        self.current_token.pos_start,
                        self.current_token.pos_end,
                        "Expected ',' or')'"
                    ))

                result.register_advancement()
                self.advance()
            return result.success(CallNode(atom, arg_nodes))
        return result.success(atom)

    def atom(self):
        result = ParsedResult()
        token = self.current_token

        if token.type in (TT_INT, TT_FLOAT):
            result.register_advancement()
            self.advance()
            return result.success(NumberNode(token))
        elif token.type == TT_IDENTIFIER:
            result.register_advancement()
            self.advance()
            return result.success(VarAccessNode(token))
        elif token.type == TT_LPAREN:
            result.register_advancement()
            self.advance()
            expr = result.register(self.expr())
            if result.error:
                return result
            if self.current_token.type == TT_RPAREN:
                result.register_advancement()
                self.advance()
                return result.success(expr)
            else:
                return result.failure(InvalidSyntaxErr(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected ')'"
                ))
        elif token.matches(TT_KEYWORD, 'if'):
            if_expr = result.register(self.if_expr())
            if result.error:
                return result

            return result.success(if_expr)
        elif token.matches(TT_KEYWORD, 'for'):
            for_expr = result.register(self.for_expr())
            if result.error:
                return result

            return result.success(for_expr)
        elif token.matches(TT_KEYWORD, 'while'):
            while_expr = result.register(self.while_expr())
            if result.error:
                return result

            return result.success(while_expr)
        elif token.matches(TT_KEYWORD, 'fun'):
            fun_def = result.register(self.fun_def())
            if result.error:
                return result

            return result.success(fun_def)
        return result.failure(InvalidSyntaxErr(
            token.pos_start,
            token.pos_end,
            "Exprected int, float, identifier, '+', '-', '(', 'if', 'for', 'while', or 'fun'"
        ))

    def factor(self):
        result = ParsedResult()
        token = self.current_token

        if token.type in (TT_PLUS, TT_MINUS):
            result.register_advancement()
            self.advance()
            factor = result.register(self.factor())
            if result.error:
                return result
            return result.success(UnaryOperationNode(token, factor))

        return self.power()

    def term(self):
        return self.binary_operation(self.factor, (TT_MUL, TT_DIV, TT_POW))

    def ar_expr(self):
        return self.binary_operation(self.term, (TT_PLUS, TT_MINUS))

    def com_expr(self):
        result = ParsedResult()

        if self.current_token.matches(TT_KEYWORD, 'not'):
            operation = self.current_token
            result.register_advancement()
            self.advance()

            node = result.register(self.com_expr())
            if result.error:
                return result
            return result.success(UnaryOperationNode(operation, node))

        node = result.register(self.binary_operation(self.ar_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))
        if result.error:
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected int, float, identifier, '+', '-', '(', or 'not'"
            ))

        return result.success(node)

    def expr(self):
        result = ParsedResult()

        if self.current_token.matches(TT_KEYWORD, 'set'):
            result.register_advancement()
            self.advance()

            if self.current_token.type != TT_IDENTIFIER:
                return result.failure(InvalidSyntaxErr(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    "Expected identifier"
                ))

            var_name = self.current_token
            result.register_advancement()
            self.advance()

            if self.current_token.type != TT_EQ:
                return result.failure(InvalidSyntaxErr(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    "Expected '='"
                ))

            result.register_advancement()
            self.advance()
            expr = result.register(self.expr())
            if result.error:
                return result
            return result.success(VarAssignNode(var_name, expr))

        node = result.register(self.binary_operation(self.com_expr, ((TT_KEYWORD, "and"), (TT_KEYWORD, "or"))))
        if result.error:
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected 'set', int, float, identifier, '+', '-', '(', 'not', 'if', 'for', 'while', or 'fun'"
            ))
        return result.success(node)

    def if_expr(self):
        result = ParsedResult()
        cases = []
        else_case = None

        if not self.current_token.matches(TT_KEYWORD, 'if'):
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected 'if'"
            ))

        result.register_advancement()
        self.advance()

        condition = result.register(self.expr())
        if result.error:
            return result

        if not self.current_token.matches(TT_KEYWORD, 'then'):
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected 'then'"
            ))

        result.register_advancement()
        self.advance()

        expr = result.register(self.expr())
        if result.error:
            return result
        cases.append((condition, expr))

        while self.current_token.matches(TT_KEYWORD, 'eli'):
            result.register_advancement()
            self.advance()

            condition = result.register(self.expr())
            if result.error:
                return result

            if not self.current_token.matches(TT_KEYWORD, 'then'):
                return result.failure(InvalidSyntaxErr(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    "Expected 'then'"
                ))

            result.register_advancement()
            self.advance()

            expr = result.register(self.expr())
            if result.error:
                return result
            cases.append((condition, expr))

        if self.current_token.matches(TT_KEYWORD, 'else'):
            result.register_advancement()
            self.advance()

            else_case = result.register(self.expr())
            if result.error:
                return result
        return result.success(IfNode(cases, else_case))

    def for_expr(self):
        result = ParsedResult()

        if not self.current_token.matches(TT_KEYWORD, 'for'):
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected 'for'"
            ))

        result.register_advancement()
        self.advance()

        if self.current_token.type != TT_IDENTIFIER:
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected identifier"
            ))

        var_name = self.current_token
        result.register_advancement()
        self.advance()

        if self.current_token.type != TT_EQ:
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected '='"
            ))

        result.register_advancement()
        self.advance()

        start_value = result.register(self.expr())
        if result.error:
            return result

        if not self.current_token.matches(TT_KEYWORD, 'to'):
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected 'to'"
            ))

        result.register_advancement()
        self.advance()

        end_value = result.register(self.expr())
        if result.error:
            return result

        step_value = None
        if self.current_token.matches(TT_KEYWORD, 'step'):
            result.register_advancement()
            self.advance()

            step_value = result.register(self.expr())
            if result.error:
                return result

        if not self.current_token.matches(TT_KEYWORD, 'then'):
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected 'then'"
            ))

        result.register_advancement()
        self.advance()

        body = result.register(self.expr())
        if result.error:
            return result

        return result.success(ForNode(var_name, start_value, end_value, step_value, body))

    def while_expr(self):
        result = ParsedResult()

        if not self.current_token.matches(TT_KEYWORD, 'while'):
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected 'while'"
            ))

        result.register_advancement()
        self.advance()

        condition = result.register(self.expr())
        if result.error:
            return result

        if not self.current_token.matches(TT_KEYWORD, 'then'):
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected 'then'"
            ))

        result.register_advancement()
        self.advance()

        body = result.register(self.expr())
        if result.error:
            return result

        return result.success(WhileNode(condition, body))

    def fun_def(self):
        result = ParsedResult()

        if not self.current_token.matches(TT_KEYWORD, 'fun'):
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected 'fun'"
            ))

        result.register_advancement()
        self.advance()

        var_name_token = None
        if self.current_token.type == TT_IDENTIFIER:
            var_name_token = self.current_token
            result.register_advancement()
            self.advance()

            if self.current_token.type != TT_LPAREN:
                return result.failure(InvalidSyntaxErr(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    "Expected '('"
                ))
        else:
            if self.current_token.type != TT_LPAREN:
                return result.failure(InvalidSyntaxErr(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    "Expected identifier or '('"
                ))

        result.register_advancement()
        self.advance()

        arg_name_tokens = []

        if self.current_token.type == TT_IDENTIFIER:
            arg_name_tokens.append(self.current_token)
            result.register_advancement()
            self.advance()

            while self.current_token.type == TT_COMMA:
                result.register_advancement()
                self.advance()

                if self.current_token.type != TT_IDENTIFIER:
                    return result.failure(InvalidSyntaxErr(
                        self.current_token.pos_start,
                        self.current_token.pos_end,
                        "Expected identifier"
                    ))

                arg_name_tokens.append(self.current_token)
                result.register_advancement()
                self.advance()

            if self.current_token.type != TT_RPAREN:
                return result.failure(InvalidSyntaxErr(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    "Expected ')'"
                ))
        else:
            if self.current_token.type != TT_RPAREN:
                return result.failure(InvalidSyntaxErr(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    "Expected identifier or ')'"
                ))

        result.register_advancement()
        self.advance()

        if self.current_token.type != TT_ARROW:
            return result.failure(InvalidSyntaxErr(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected '->'"
            ))

        result.register_advancement()
        self.advance()

        node_to_return = result.register(self.expr())
        if result.error:
            return result

        return result.success(FunDefNode(
            var_name_token,
            arg_name_tokens,
            node_to_return
        ))

    def binary_operation(self, lfunc, operations, rfunc=None):
        if rfunc is None:
            rfunc = lfunc
        result = ParsedResult()
        left = result.register(lfunc())
        if result.error:
            return result

        while self.current_token.type in operations or \
                (self.current_token.type, self.current_token.value) in operations:
            operation = self.current_token
            result.register_advancement()
            self.advance()
            right = result.register(rfunc())
            if result.error:
                return result
            left = BinaryOperationNode(left, operation, right)

        return result.success(left)


####################
# VALUES
####################
class Type:
    def __init__(self):
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
        return None, self.illegal_operation(other)

    def subtracted_by(self, other):
        return None, self.illegal_operation(other)

    def multiplied_by(self, other):
        return None, self.illegal_operation(other)

    def divided_by(self, other):
        return None, self.illegal_operation(other)

    def power_of(self, other):
        return None, self.illegal_operation(other)

    def comp_eq(self, other):
        return None, self.illegal_operation(other)

    def comp_ne(self, other):
        return None, self.illegal_operation(other)

    def comp_lt(self, other):
        return None, self.illegal_operation(other)

    def comp_gt(self, other):
        return None, self.illegal_operation(other)

    def comp_lte(self, other):
        return None, self.illegal_operation(other)

    def comp_gte(self, other):
        return None, self.illegal_operation(other)

    def comp_and(self, other):
        return None, self.illegal_operation(other)

    def comp_or(self, other):
        return None, self.illegal_operation(other)

    def not_op(self):
        return None, self.illegal_operation()

    def is_true(self):
        return False

    def copy(self):
        raise Exception("No copy method defined")

    def illegal_operation(self, other=None):
        if not other:
            other = self
        return RuntimeErr(
            self.pos_start,
            other.pos_end,
            "Illegal operation",
            self.context
        )

    def __repr__(self):
        return f"<{self.__name__}>"


class Number(Type):
    def __init__(self, value):
        super().__init__()
        self.value = value

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
        else:
            return None, Type.illegal_operation(self, other)

    def subtracted_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

    def multiplied_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

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
        else:
            return None, Type.illegal_operation(self, other)

    def power_of(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

    def comp_eq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

    def comp_ne(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

    def comp_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

    def comp_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

    def comp_lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

    def comp_gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

    def comp_and(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

    def comp_or(self, other):
        if isinstance(other, Number):
            return Number(int(self.value or other.value)).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

    def not_op(self):
        return Number(1 if self.value == 0 else 0).set_context(self.context), None

    def is_true(self):
        return self.value not in (0, -1)

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return str(self.value)


class Function(Type):
    def __init__(self, name, body_node, arg_names):
        super().__init__()
        self.name = name or "<unnamed>"
        self.body_node = body_node
        self.arg_names = arg_names

    def execute(self, args):
        result = RuntimeResult()
        interpreter = Interpreter()
        fun_context = Context(self.name, self.context, self.pos_start)
        fun_context.symbol_table = SymbolTable(fun_context.parent.symbol_table)

        if len(args) > len(self.arg_names):
            return result.failure(RuntimeErr(
                self.pos_start,
                self.pos_end,
                f"Too many args ({len(args)}/{len(self.arg_names)}) passed into '{self.name}'",
                self.context
            ))
        elif len(args) < len(self.arg_names):
            return result.failure(RuntimeErr(
                self.pos_start,
                self.pos_end,
                f"Too few args ({len(args)}/{len(self.arg_names)} needed) passed into '{self.name}'",
                self.context
            ))

        for i in range(len(args)):
            arg_name = self.arg_names[i]
            arg_value = args[i]
            arg_value.set_context(fun_context)
            fun_context.symbol_table.set(arg_name, arg_value)

        value = result.register(interpreter.visit(self.body_node, fun_context))
        if result.error:
            return result

        return result.success(value)

    def copy(self):
        copy = Function(self.name, self.body_node, self.arg_names)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)

        return copy

    def __repr__(self):
        return f"<Function: '{self.name}'>"

####################
# CONTEXT
####################
class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


####################
# SYMBOL TABLE
####################
class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent  # Used in functions

    def get(self, name):
        value = self.symbols.get(name, None)

        if value is None and self.parent is not None:
            return self.parent.get(name)
        return value

    def set(self, name, value):
        self.symbols[name] = value

    def remove(self, name):
        del self.symbols[name]


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
        return RuntimeResult().success(
            Number(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end))

    def visit_VarAccessNode(self, node, context):
        result = RuntimeResult()
        var_name = node.var_name_token.value
        value = context.symbol_table.get(var_name)

        if not value:
            return result.failure(RuntimeErr(
                node.pos_start,
                node.pos_end,
                f"'{var_name}' is not defined",
                context
            ))

        value = value.copy().set_pos(node.pos_start, node.pos_end)
        return result.success(value)

    def visit_VarAssignNode(self, node, context):
        result = RuntimeResult()
        var_name = node.var_name_token.value
        value = result.register(self.visit(node.value_node, context))
        if result.error:
            return result

        context.symbol_table.set(var_name, value)
        return result.success(value)

    def visit_BinaryOperationNode(self, node, context):
        result = error = None
        rt_result = RuntimeResult()
        left = rt_result.register(self.visit(node.left_node, context))
        if rt_result.error:
            return rt_result
        right = rt_result.register(self.visit(node.right_node, context))
        if rt_result.error:
            return rt_result

        if node.operation.type == TT_PLUS:
            result, error = left.added_to(right)
        elif node.operation.type == TT_MINUS:
            result, error = left.subtracted_by(right)
        elif node.operation.type == TT_MUL:
            result, error = left.multiplied_by(right)
        elif node.operation.type == TT_DIV:
            result, error = left.divided_by(right)
        elif node.operation.type == TT_POW:
            result, error = left.power_of(right)
        elif node.operation.type == TT_EE:
            result, error = left.comp_eq(right)
        elif node.operation.type == TT_NE:
            result, error = left.comp_ne(right)
        elif node.operation.type == TT_LT:
            result, error = left.comp_lt(right)
        elif node.operation.type == TT_GT:
            result, error = left.comp_gt(right)
        elif node.operation.type == TT_LTE:
            result, error = left.comp_lte(right)
        elif node.operation.type == TT_GTE:
            result, error = left.comp_gte(right)
        elif node.operation.matches(TT_KEYWORD, 'and'):
            result, error = left.comp_and(right)
        elif node.operation.matches(TT_KEYWORD, 'or'):
            result, error = left.comp_or(right)

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
        elif node.operation.matches(TT_KEYWORD, 'not'):
            number, error = number.not_op()

        if error:
            return result.failure(error)
        return result.success(number.set_pos(node.pos_start, node.pos_end))

    def visit_IfNode(self, node: IfNode, context):
        result = RuntimeResult()

        for condition, expr, in node.cases:
            condition_value = result.register(self.visit(condition, context))
            if result.error:
                return result

            if condition_value.is_true():
                expr_value = result.register(self.visit(expr, context))
                if result.error:
                    return result

                return result.success(expr_value)

        if node.else_case:
            else_value = result.register(self.visit(node.else_case, context))
            if result.error:
                return result

            return result.success(else_value)

        return result.success(None)

    def visit_ForNode(self, node: ForNode, context: Context):
        result = RuntimeResult()

        start_value = result.register(self.visit(node.start_value_node, context))
        if result.error:
            return result

        end_value = result.register(self.visit(node.end_value_node, context))
        if result.error:
            return result

        step_value = Number(1)
        if node.step_value_node:
            step_value = result.register(self.visit(node.step_value_node, context))
            if result.error:
                return result

        i = start_value.value

        if step_value.value >= 0:
            condition = lambda: i < end_value.value
        else:
            condition = lambda: i > end_value.value

        while condition():
            context.symbol_table.set(node.var_name_token.value, Number(i))
            i += step_value.value

            result.register(self.visit(node.body_node, context))
            if result.error:
                return result

        return result.success(None)

    def visit_WhileNode(self, node: WhileNode, context: Context):
        result = RuntimeResult()

        while True:
            condition = result.register(self.visit(node.condition_node, context))
            if result.error:
                return result

            if not condition.is_true():
                break

            result.register(self.visit(node.body_node, context))
            if result.error:
                return result

        return result.success(None)

    def visit_FunDefNode(self, node: FunDefNode, context: Context):
        result = RuntimeResult()

        fun_name = node.var_name_token.value if node.var_name_token else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_tokens]
        fun_value = Function(fun_name, body_node, arg_names).set_context(context).set_pos(node.pos_start, node.pos_end)

        if node.var_name_token:
            context.symbol_table.set(fun_name, fun_value)

        return result.success(fun_value)

    def visit_CallNode(self, node: CallNode, context: Context):
        result = RuntimeResult()
        args = []

        value_to_call = result.register(self.visit(node.node_to_call, context))
        if result.error:
            return result

        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(result.register(self.visit(arg_node, context)))
            if result.error:
                return result

        return_value = result.register(value_to_call.execute(args))
        if result.error:
            return result

        return result.success(return_value)




####################
# RUNNER
####################
global_symbol_table = SymbolTable()
global_symbol_table.set("null", Number(-1))
global_symbol_table.set("true", Number(1))
global_symbol_table.set("false", Number(0))


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
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error
