#!/usr/bin/env python3
"""
Lists all top-level language codes in src/locales/.
Prints a comma-separated list (e.g., da,en,el,es,cs).
"""

import os
from typing import List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
locales_dir = os.path.join(SCRIPT_DIR, "..", "src", "locales")
locales_dir = os.path.abspath(locales_dir)
if not os.path.isdir(locales_dir):
    print("No locales directory found.")
    exit(1)

combinations: List[str] = []
for lang in sorted(os.listdir(locales_dir)):
    lang_path = os.path.join(locales_dir, lang)
    if not os.path.isdir(lang_path) or lang.startswith("."):
        continue
    regions: List[str] = [r for r in os.listdir(lang_path) if os.path.isdir(os.path.join(lang_path, r)) and not r.startswith(".")]
    if regions:
        for region in sorted(regions):
            combinations.append(f"{lang}/{region}")
    else:
        combinations.append(lang)

print(",".join(combinations))
