#      d888888
#     d88P aaa  888  888  888d88  .d88b.   888d88   8888b.
#    d88P  aaa  888  888  888P   d88^^88b  888P        88b
#   d88P   aaa  888  888  888    888  888  888    .d888888
#  d8888888888  Y88b 888  888    Y88..88P  888    888  888
# d88P     aaa    Y88888  888      Y88P    888     Y888888
# -- Copyright © 2023 Zandercraft. All rights reserved. --
"""
Purpose: Core Exception Set
"""

# Imports
from internal.term_utils import point_at


class Error:
    """
    Base class for Aurora exception types.
    """
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
    """
    Illegal Character Error
    - Thrown when a character is detected that is not valid in a particular situation.
    """
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'IllegalCharacter', details)


class ExpectedCharErr(Error):
    """
    Expected Character Error
    - Thrown when a character is missing that is required in a particular situation.
    """
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'ExpectedCharacter', details)


class InvalidSyntaxErr(Error):
    """
    Invalid Syntax Error
    - Thrown when invalid keywords or symbols are used or when they are misused.
    """
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'InvalidSyntax', details)


class RuntimeErr(Error):
    """
    Runtime Error
    - Thrown during the evaluation of an expression when something goes wrong.
    Example: dividing by zero (valid syntax, but invalid operation)
    """
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
