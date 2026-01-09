from typing import Dict, Protocol


class NamedAction(Protocol):
    def name(self) -> str: ...


_REGISTRY: Dict[str, NamedAction] = {}


def register(action: NamedAction) -> None:
    _REGISTRY[action.name()] = action


def get(action_name: str) -> NamedAction:
    return _REGISTRY[action_name]
