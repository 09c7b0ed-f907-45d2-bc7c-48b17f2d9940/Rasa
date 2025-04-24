import os

from dotenv import load_dotenv

_loaded = False


def require_env(*keys: str) -> tuple[str, ...]:
    global _loaded
    if not _loaded:
        load_dotenv()
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
