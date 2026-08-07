# pyright: reportMissingTypeStubs=false, reportMissingModuleSource=false
"""Shared helpers for reading SSOT YAML files (src/shared/SSOT/*.yml).

Used by both ssot_canonicalizer.py (post-extraction value canonicalization,
locale-agnostic) and layered_importer.py (pre-train NLU lookup/synonym
generation, locale-aware) so there is exactly one place that understands the
SSOT YAML shape.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, cast

import yaml  # type: ignore[import-untyped]  # pyright: ignore[reportMissingModuleSource, reportMissingTypeStubs]


def load_ssot_items(path: Path) -> List[Dict[str, Any]]:
    """Load an SSOT YAML file's list of {canonical, synonyms, ...} entries."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        raw_list = cast(List[Any], raw)
        return [cast(Dict[str, Any], item) for item in raw_list if isinstance(item, dict)]
    if isinstance(raw, dict):
        return [cast(Dict[str, Any], raw)]
    return []


def as_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        value_list = cast(List[Any], value)
        return [str(v) for v in value_list if v is not None]
    return [str(value)]


def all_synonyms(item: Dict[str, Any]) -> List[str]:
    """Flatten every locale's synonyms together (locale-agnostic canonicalization)."""
    synonyms = item.get("synonyms")
    out: List[str] = []
    if isinstance(synonyms, dict):
        synonyms_dict = cast(Dict[Any, Any], synonyms)
        for localized in synonyms_dict.values():
            out.extend(as_str_list(localized))
    return out


def locale_synonyms(item: Dict[str, Any], locale: str) -> List[str]:
    """Return the synonym list for one locale, falling back to `en` if that
    locale has no entry (e.g. a canonical added before a translation pass)."""
    synonyms = item.get("synonyms")
    if not isinstance(synonyms, dict):
        return []
    synonyms_dict = cast(Dict[str, Any], synonyms)
    names = as_str_list(synonyms_dict.get(locale))
    if not names and locale != "en":
        names = as_str_list(synonyms_dict.get("en"))
    return names
