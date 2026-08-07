"""Pure, rasa-independent helper for detecting which locale a deployed Rasa
model/container was actually built to serve.

Reads LAYERS -- the same env var the production Dockerfile already bakes in
as a persistent runtime ENV (ARG LAYERS -> ENV LAYERS, populated per-locale
by docker-build.yml's build matrix) -- rather than guessing or defaulting to
a fixed language. Local dev's docker-compose command exports the same var
for parity, so this works identically in both.
"""
from __future__ import annotations

import os
from typing import List, Optional


def detect_locale_overlay_domain(layers_env_value: Optional[str] = None) -> List[str]:
    """Parse LAYERS (space-separated build layer paths, e.g.
    "src/core src/locales/en/US") to find the most specific locale-overlay
    domain path for this deployment. Returns [] (base-only, no overlay) if
    LAYERS isn't set or contains no locale-specific layer -- never guesses
    a default language."""
    raw = layers_env_value if layers_env_value is not None else os.environ.get("LAYERS", "")
    raw = raw.strip()
    if not raw:
        return []

    locale_paths = [p for p in raw.split() if p.startswith("src/locales/")]
    if not locale_paths:
        return []

    # Prefer the most specific path present, e.g. src/locales/en/US over
    # src/locales/en if both happen to be listed.
    most_specific = max(locale_paths, key=lambda p: p.count("/"))
    return [f"{most_specific}/domain"]
