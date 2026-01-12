from typing import Any, Callable, Dict, Optional, cast


class LongActionContext:
    def __init__(self, sender_id: str, tracker_snapshot: Dict[str, Any], dispatcher: Optional[Any] = None):
        self.sender_id = sender_id
        self.tracker_snapshot = tracker_snapshot
        self.dispatcher = dispatcher
        # Optional progress callback used in callback mode to stream
        # individual messages back to the frontend as they are emitted.
        self._progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None

    @property
    def text(self) -> str:
        latest_any = self.tracker_snapshot.get("latest_message")
        if isinstance(latest_any, dict):
            latest = cast(Dict[str, Any], latest_any)
            text_val = latest.get("text")
            if isinstance(text_val, str):
                return text_val
        return ""

    @property
    def metadata(self) -> Dict[str, Any]:
        latest_any = self.tracker_snapshot.get("latest_message")
        if isinstance(latest_any, dict):
            latest = cast(Dict[str, Any], latest_any)
            meta_val = latest.get("metadata")
            if isinstance(meta_val, dict):
                return cast(Dict[str, Any], meta_val)
        return {}

    @property
    def slots(self) -> Dict[str, Any]:
        """Return the tracked slots snapshot for this long action."""
        slots_any = self.tracker_snapshot.get("slots")
        if isinstance(slots_any, dict):
            return cast(Dict[str, Any], slots_any)
        return {}

    def say(self, **kwargs: Any) -> None:
        """
        - ctx.say(text="hi")  normal message
        - ctx.say(json_message={...}) / ctx.say(image="...")  normal message
        - ctx.say(progress="...")  special progress event (frontend decides how to render/replace)
        """
        if self.dispatcher is not None:
            # Synchronous mode: send directly via dispatcher.
            self.dispatcher.utter_message(**kwargs)
            return

        # Callback mode: normalise dispatcher-style kwargs into the same
        # shape Rasa's REST channel produces, i.e. content lives under
        # "custom".
        message: Dict[str, Any] = dict(kwargs)

        # Progress helper: ctx.say(progress="...") becomes
        # {"custom": {"progress": "..."}} when there is no explicit
        # custom/json_message override.
        if "progress" in message and "custom" not in message and "json_message" not in message:
            progress_val = message.pop("progress")
            message = {"custom": {"progress": progress_val}}

        # json_message helper: ctx.say(json_message={...}) should mirror
        # dispatcher.utter_message(json_message=...) which surfaces the
        # payload under "custom" in REST responses.
        if "json_message" in message and "custom" not in message:
            custom_val = message.pop("json_message")
            message = {"custom": custom_val}

        # If a progress callback is configured, invoke it so the message is
        # streamed immediately to the frontend.
        if self._progress_callback is not None:
            try:
                self._progress_callback(message)
            except Exception:
                # Swallow exceptions here so a failing callback endpoint
                # doesn't break the long-running job logic.
                pass

    def attach_progress_callback(self, cb: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback to be invoked on every ctx.say() in callback mode."""
        self._progress_callback = cb

    def done(self) -> None:
        if self.dispatcher is not None:
            # Nothing to clean up in synchronous mode.
            return
