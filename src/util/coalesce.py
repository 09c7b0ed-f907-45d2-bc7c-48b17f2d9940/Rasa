from typing import Optional, TypeVar, overload

T = TypeVar("T")


@overload
def coalesce(value: Optional[T]) -> Optional[T]: ...
@overload
def coalesce(value: Optional[T], default: T) -> T: ...


def coalesce(value: Optional[T], default: Optional[T] = None):
    return value if value is not None else default
