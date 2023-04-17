#      d888888
#     d88P aaa  888  888  888d88  .d88b.   888d88   8888b.
#    d88P  aaa  888  888  888P   d88^^88b  888P        88b
#   d88P   aaa  888  888  888    888  888  888    .d888888
#  d8888888888  Y88b 888  888    Y88..88P  888    888  888
# d88P     aaa    Y88888  888      Y88P    888     Y888888
# -- Copyright © 2023 Zandercraft. All rights reserved. --
"""
Purpose: Contains all the valid types in the language.
"""

# Imports
from exceptions import core as exceptions
# from aurora import RuntimeResult, Interpreter, Context, SymbolTable
import aurora


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
        return exceptions.RuntimeErr(
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
                return None, exceptions.RuntimeErr(
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


class String(Type):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

    def multiplied_by(self, other):
        if isinstance(other, Number):
            return String(self.value * other.value).set_context(self.context), None
        else:
            return None, Type.illegal_operation(self, other)

    def is_true(self):
        return len(self.value) > 0

    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return f'"{self.value}"'


class Function(Type):
    def __init__(self, name, body_node, arg_names):
        super().__init__()
        self.name = name or "<unnamed>"
        self.body_node = body_node
        self.arg_names = arg_names

    def execute(self, args):
        result = aurora.RuntimeResult()
        interpreter = aurora.Interpreter()
        fun_context = aurora.Context(self.name, self.context, self.pos_start)
        fun_context.symbol_table = aurora.SymbolTable(fun_context.parent.symbol_table)

        if len(args) > len(self.arg_names):
            return result.failure(exceptions.RuntimeErr(
                self.pos_start,
                self.pos_end,
                f"Too many args ({len(args)}/{len(self.arg_names)}) passed into '{self.name}'",
                self.context
            ))
        elif len(args) < len(self.arg_names):
            return result.failure(exceptions.RuntimeErr(
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
