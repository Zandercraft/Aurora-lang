"""
     d888888
    d88P aaa  888  888  888d88  .d88b.   888d88   8888b.
   d88P  aaa  888  888  888P   d88^^88b  888P        88b
  d88P   aaa  888  888  888    888  888  888    .d888888
 d8888888888  Y88b 888  888    Y88..88P  888    888  888
d88P     aaa    Y88888  888      Y88P    888     Y888888
-- Copyright © 2023 Zandercraft. All rights reserved. --

Purpose: Command-line interface for the aurora language.
"""

# Imports
import aurora
from internal.term_utils import AURORA_TEXT, AURORA_BANNER, WELCOME


def interactive_shell():
    """
    An interactive shell implementation.
    Allows for command-like execution of Aurora code.
    """
    # Print the banner and welcome message
    print(AURORA_BANNER)
    print(WELCOME)

    # Start the programming loop.
    try:
        while (u := input(f"{AURORA_TEXT}> ")) != "exit":
            result, error = aurora.evaluate('<stdin>', u)

            if error:
                print(error.as_string())
            elif result:
                print(result)
    except KeyboardInterrupt:
        # Handle keyboard interrupts and gracefully shut down.
        print("^C")  # bump exit message onto newline.

    print(f"Thanks for using {AURORA_TEXT}! See you soon!")


if __name__ == '__main__':
    interactive_shell()
