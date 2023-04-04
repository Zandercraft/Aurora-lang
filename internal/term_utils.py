#      d888888
#     d88P aaa  888  888  888d88  .d88b.   888d88   8888b.
#    d88P  aaa  888  888  888P   d88^^88b  888P        88b
#   d88P   aaa  888  888  888    888  888  888    .d888888
#  d8888888888  Y88b 888  888    Y88..88P  888    888  888
# d88P     aaa    Y88888  888      Y88P    888     Y888888
# -- Copyright © 2023 Zandercraft. All rights reserved. --
"""
Purpose: Contains utility functions to enhance terminal functionality.
NOTE: Meant to be used internally in Aurora. It is not meant for external use.
"""

# Imports
import enum


class Colour(enum.Enum):
    """
    ANSII colour code representations.
    (Use in the colour() function)
    """
    RED = 91
    GREEN = 92
    YELLOW = 93
    LIGHT_PURPLE = 94
    PURPLE = 95
    CYAN = 96


def colour(text: str, variant: Colour):
    """
    Sets the colour of the given text. (To be used in print() calls)
    :param text: text to set the colour of.
    :param variant: the colour to set the text to.
    :return: coloured text (when printed).
    """
    return f"\033[{variant.value}m{text}\033[00m"


color = colour  # Alias (for the United States)


def point_at(text, pos_start, pos_end):
    """
    CREDIT: CodePulse
    :param text: the text in which to point
    :param pos_start: starting position in text to point at
    :param pos_end: ending position in text to point at
    :return: Pointed text
    """
    result = ''

    # Calculate indices
    idx_start = max(text.rfind('\n', 0, pos_start.idx), 0)
    idx_end = text.find('\n', idx_start + 1)
    if idx_end < 0: idx_end = len(text)

    # Generate each line
    line_count = pos_end.ln - pos_start.ln + 1
    for i in range(line_count):
        # Calculate line columns
        line = text[idx_start:idx_end]
        col_start = pos_start.col if i == 0 else 0
        col_end = pos_end.col if i == line_count - 1 else len(line) - 1

        # Append to result
        result += line + '\n'
        result += ' ' * col_start + '^' * (col_end - col_start)

        # Re-calculate indices
        idx_start = idx_end
        idx_end = text.find('\n', idx_start + 1)
        if idx_end < 0: idx_end = len(text)

    return result.replace('\t', '')


# --- Constants ---
AURORA_TEXT = f"{colour('A', Colour.CYAN)}" \
              f"{colour('u', Colour.LIGHT_PURPLE)}" \
              f"{colour('r', Colour.GREEN)}" \
              f"{colour('o', Colour.PURPLE)}" \
              f"{colour('r', Colour.LIGHT_PURPLE)}" \
              f"{colour('a', Colour.CYAN)}"

COPYRIGHT_NOTICE = "-- Copyright © 2023 Zandercraft. All rights reserved. --"

WELCOME = f"Welcome to the {AURORA_TEXT} CLI interpreter! To exit type 'exit'"

AURORA_BANNER = f'     {colour("d888888", Colour.CYAN)}\n' \
                f'    {colour("d88P aaa", Colour.CYAN)}  {colour("888  888", Colour.LIGHT_PURPLE)}  {colour("888d88", Colour.GREEN)}  {colour(".d88b.", Colour.PURPLE)}   {colour("888d88", Colour.LIGHT_PURPLE)}   {colour("8888b.", Colour.CYAN)}\n' \
                f'   {colour("d88P  aaa", Colour.CYAN)}  {colour("888  888", Colour.LIGHT_PURPLE)}  {colour("888P", Colour.GREEN)}   {colour("d88^^88b", Colour.PURPLE)}  {colour("888P", Colour.LIGHT_PURPLE)}        {colour("88b", Colour.CYAN)}\n' \
                f'  {colour("d88P   aaa", Colour.CYAN)}  {colour("888  888", Colour.LIGHT_PURPLE)}  {colour("888", Colour.GREEN)}    {colour("888  888", Colour.PURPLE)}  {colour("888", Colour.LIGHT_PURPLE)}    {colour(".d888888", Colour.CYAN)}\n' \
                f' {colour("d8888888888", Colour.CYAN)}  {colour("Y88b 888", Colour.LIGHT_PURPLE)}  {colour("888", Colour.GREEN)}    {colour("Y88..88P", Colour.PURPLE)}  {colour("888", Colour.LIGHT_PURPLE)}    {colour("888  888", Colour.CYAN)}\n' \
                f'{colour("d88P     aaa", Colour.CYAN)}  {colour("  Y88888", Colour.LIGHT_PURPLE)}  {colour("888", Colour.GREEN)}      {colour("Y88P", Colour.PURPLE)}    {colour("888", Colour.LIGHT_PURPLE)}     {colour("Y888888", Colour.CYAN)}\n' \
                f'{COPYRIGHT_NOTICE}'
