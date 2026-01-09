"""Legacy polling module for long actions.

The original implementation used Rasa reminders and a polling action to
retrieve progress updates from long-running tasks. The current design has
been simplified to either:

- run long tasks synchronously like normal actions, or
- run them asynchronously and notify an external callback URL.

This module is kept as an empty shell to avoid import errors from older
configuration, but it no longer defines any Rasa actions.
"""

__all__: list[str] = []
