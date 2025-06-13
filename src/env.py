import os

from dotenv import load_dotenv

_loaded = False


def require_all_env(*keys: str, force: bool = False) -> tuple[str, ...]:
    global _loaded
    if not _loaded or force:
        load_dotenv(override=force)
        _loaded = True

    values: list[str] = []
    missing: list[str] = []

    for key in keys:
        val = os.getenv(key)
        if val is None:
            missing.append(key)
        else:
            values.append(val)

    if missing:
        raise OSError(f"Missing required environment variable(s): {', '.join(missing)}")
    else:
        return tuple(v for v in values)


def require_any_env(*keys: str, force: bool = False) -> tuple[str, ...]:
    """
    Require at least one of the given environment variables to be present.
    Returns a tuple of all present values (in order of keys).
    Raises OSError if none are present.
    """
    global _loaded
    if not _loaded or force:
        load_dotenv(override=force)
        _loaded = True

    values: list[str] = []
    for key in keys:
        val = os.getenv(key)
        if val is not None:
            values.append(val)

    if not values:
        raise OSError(f"At least one of the required environment variables must be set: {', '.join(keys)}")
    return tuple(values)
