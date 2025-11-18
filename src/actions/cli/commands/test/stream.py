from __future__ import annotations

import time
from typing import Any, Dict, List

from rasa_sdk.events import EventType  # type: ignore

from .. import command


@command("test_stream")
def test_stream(dispatcher: Any, tracker: Any, domain: Any, args: List[str], opts: Dict[str, Any]) -> List[EventType]:
    """
    Emit multiple messages sequentially to simulate streaming behavior.

    Usage from CLI router (metadata.cli_command_text):
      /cli test_stream               # default count=5, delay=1.0s
      /cli test_stream count=3       # 3 messages
      /cli test_stream delay=0.5     # 0.5s between messages
      /cli test_stream count=3 delay=0.2
    """
    try:
        count = int(opts.get("count", 5))
    except Exception:
        count = 5
    try:
        delay = float(opts.get("delay", 1.0))
    except Exception:
        delay = 1.0

    # Clamp to reasonable bounds to avoid excessive blocking
    count = max(1, min(count, 50))
    delay = max(0.0, min(delay, 5.0))

    for i in range(count, 0, -1):
        dispatcher.utter_message(text=f"Countdown: {i}")
        # Note: Rasa REST channel will buffer these and return them together at the end of the action.
        # Channels supporting streaming might deliver incrementally.
        time.sleep(delay)

    dispatcher.utter_message(text="Done.")
    return []
