"""_errors.py — Shared exception type for integration adapters."""


class AdapterError(Exception):
    """Raised when an integration adapter cannot produce a valid result.

    Common causes:
    - Ark subcommand not present or returned non-zero exit code.
    - Ark output shape changed in an incompatible way.
    - JSON parse failure on Ark's stdout.

    If the output shape changed, the message will contain a hint:
      "see research/ark-as-host-feasibility.md"
    """
