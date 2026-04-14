"""Entry point for `python -m shape_grammar.tools.verify`."""

import sys
from . import _cli_main

sys.exit(_cli_main(sys.argv))
