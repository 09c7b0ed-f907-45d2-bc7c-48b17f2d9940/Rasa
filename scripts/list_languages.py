#!/usr/bin/env python3
"""
Lists all top-level language codes in src/locales/.
Prints a comma-separated list (e.g., da,en,el,es,cs).
"""

import os
from typing import Dict, List

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
    raw_regions: List[str] = [r for r in os.listdir(lang_path) if os.path.isdir(os.path.join(lang_path, r)) and not r.startswith(".")]
    if raw_regions:
        by_canon: Dict[str, str] = {}
        for r in raw_regions:
            is_script = len(r) == 4 and r[0].isupper() and r[1:].islower()
            if r.isdigit() or is_script:
                canon = r
            else:
                canon = r.upper()
            if canon in by_canon:
                if r == canon:
                    by_canon[canon] = r
            else:
                by_canon[canon] = r
        for region in sorted(by_canon.keys()):
            combinations.append(f"{lang}/{region}")
    else:
        combinations.append(lang)

print(",".join(combinations))
