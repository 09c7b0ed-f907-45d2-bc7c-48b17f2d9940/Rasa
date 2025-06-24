from enum import Enum
from typing import Set, Type, TypeVar

T = TypeVar("T", bound="AliasEnum")


class AliasEnum(str, Enum):
    _value_: str
    _aliases: Set[str]

    @property
    def value(self) -> str:
        return self._value_

    @property
    def aliases(self) -> Set[str]:
        return self._aliases

    def __new__(cls, value: str, *aliases: str):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._aliases = set(alias.lower() for alias in aliases)
        return obj

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val = value.strip().lower()
            for member in cls:
                if val == member.value.lower() or val in member._aliases:
                    return member
        raise ValueError(f"Invalid value '{value}' for {cls.__name__}")

    @classmethod
    def from_value(cls: Type[T], value: str) -> T:
        return cls(value)

    @classmethod
    def describe_choices(cls) -> str:
        return "; ".join(f"{member.name} (aliases: {', '.join([member.value] + sorted(member._aliases))})" for member in cls)
