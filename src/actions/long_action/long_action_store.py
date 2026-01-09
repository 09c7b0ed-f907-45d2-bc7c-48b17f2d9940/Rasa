from typing import Any, Dict

_state: Dict[str, Dict[str, Any]] = {}


def start(sender_id: str, action_name: str) -> None:
    _state[sender_id] = {
        "action": action_name,
        "seq": 0,
        "events": [],  # List[Tuple[int, Dict[str, Any]]]
        "last": 0,
        "done": False,
    }


def emit(sender_id: str, event: Dict[str, Any]) -> None:
    s = _state[sender_id]
    s["seq"] += 1
    s["events"].append((s["seq"], event))


def read_events(sender_id: str):
    s = _state[sender_id]
    new = [(seq, ev) for (seq, ev) in s["events"] if seq > s["last"]]
    if new:
        s["last"] = new[-1][0]
    return new


def done(sender_id: str) -> None:
    _state[sender_id]["done"] = True


def is_done(sender_id: str) -> bool:
    return _state.get(sender_id, {}).get("done", True)


def action_name(sender_id: str) -> str:
    return _state[sender_id]["action"]


def exists(sender_id: str) -> bool:
    return sender_id in _state


def clear(sender_id: str) -> None:
    _state.pop(sender_id, None)
