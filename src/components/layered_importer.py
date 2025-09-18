from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, cast

import yaml
from rasa.shared.core.domain import Domain  # type: ignore
from rasa.shared.core.training_data.structures import StoryGraph  # type: ignore
from rasa.shared.importers.importer import TrainingDataImporter  # type: ignore
from rasa.shared.nlu.training_data import loading as nlu_loading  # type: ignore
from rasa.shared.nlu.training_data.training_data import TrainingData  # type: ignore

ADD = "add"
REPLACE = "replace"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OverlayImporter")


def _iter_yaml_files(path: Path) -> List[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() in {".yml", ".yaml"} else []
    if path.is_dir():
        return [p for p in path.rglob("*") if p.suffix.lower() in {".yml", ".yaml"}]
    return []


def _load_yaml_docs(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    files: List[Path] = []
    for p in paths:
        if p.exists():
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(_iter_yaml_files(p))
    for fpath in files:
        with fpath.open("r", encoding="utf-8") as f:
            doc_any = yaml.safe_load(f)
            if isinstance(doc_any, dict):
                docs.append(cast(Dict[str, Any], doc_any))
    return docs


def _has_yaml_under(path: Path) -> bool:
    if path.is_file():
        return path.suffix.lower() in {".yml", ".yaml"}
    if path.is_dir():
        for p in path.rglob("*"):
            if p.suffix.lower() in {".yml", ".yaml"}:
                return True
    return False


def _parse_key(key: str, inherited_op: str) -> Tuple[str, str]:
    if key.endswith(".add"):
        return key[:-4], ADD
    if key.endswith(".replace"):
        return key[:-8], REPLACE
    return key, inherited_op


def _normalize_ops(node: Any, inherited: str = REPLACE) -> Tuple[Any, str]:
    if isinstance(node, dict):
        clean: Dict[str, Any] = {}
        dict_node = cast(Dict[str, Any], node)
        for k, v in dict_node.items():
            base_k, child_op = _parse_key(k, inherited)
            sub_clean, _ = _normalize_ops(v, child_op)
            clean[base_k] = sub_clean
        return clean, inherited
    if isinstance(node, list):
        list_node = cast(List[Any], node)
        return [_normalize_ops(i, inherited)[0] for i in list_node], inherited
    return node, inherited


def _list_unique_extend(base: List[Any], extra: List[Any]) -> List[Any]:
    seen: Set[str] = set()
    out: List[Any] = []
    for x in base + extra:
        key = yaml.dump(x, sort_keys=True)
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out


def _deep_add(base: Any, overlay: Any) -> Any:
    if isinstance(base, dict) and isinstance(overlay, dict):
        base_dict = cast(Dict[str, Any], base)
        overlay_dict = cast(Dict[str, Any], overlay)
        out: Dict[str, Any] = dict(base_dict)
        for k, v in overlay_dict.items():
            if k in out:
                out[k] = _deep_add(out[k], v)
            else:
                out[k] = v
        return out
    if isinstance(base, list) and isinstance(overlay, list):
        return _list_unique_extend(cast(List[Any], base), cast(List[Any], overlay))
    return overlay


def _apply_overlay_strict_dict(base: Optional[Dict[str, Any]], overlay: Dict[str, Any], op: str, section_name: str = "") -> Dict[str, Any]:
    if base is None:
        base = {}
    if op == REPLACE:
        missing = [k for k in overlay.keys() if k not in base]
        if missing:
            sec = f" in '{section_name}'" if section_name else ""
            raise ValueError(f"Overlay attempted to replace non-existent keys{sec}: {missing}")
        merged = dict(base)
        merged.update(overlay)
        return merged
    return _deep_add(base, overlay)


DOMAIN_LIST_KEYS = {"intents", "entities", "actions", "e2e_actions"}


def _merge_domain_docs(base_docs: List[Dict[str, Any]], overlay_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    base: Dict[str, Any] = {}
    for d in base_docs:
        clean, _ = _normalize_ops(d, REPLACE)
        base = _deep_add(base, clean)

    for d in overlay_docs:
        # Normalize to strip markers, but capture per-section ops
        clean_top: Dict[str, Any] = {}
        section_ops: Dict[str, str] = {}
        for raw_key, value in d.items():
            key, sec_op = _parse_key(raw_key, REPLACE)
            section_ops[key] = sec_op
            clean_top[key] = _normalize_ops(value, sec_op)[0]

        # Dict-like sections
        for section in ("responses", "slots", "forms", "session_config"):
            if section in clean_top:
                base_section = base.get(section, {})
                op = section_ops.get(section, REPLACE)
                base[section] = _apply_overlay_strict_dict(base_section, clean_top[section], op, section)

        # List-like sections
        for section in DOMAIN_LIST_KEYS:
            if section in clean_top:
                op = section_ops.get(section, REPLACE)
                if section not in base:
                    if op == REPLACE:
                        raise ValueError(f"Overlay attempted to replace non-existent domain section '{section}'")
                    base[section] = []
                if op == REPLACE:
                    base[section] = clean_top[section]
                else:
                    base[section] = _list_unique_extend(base.get(section, []), clean_top[section])

        # Any other keys -> deep add
        for k, v in clean_top.items():
            if k in {"responses", "slots", "forms", "session_config"} | DOMAIN_LIST_KEYS:
                continue
            base[k] = _deep_add(base.get(k), v)

    return base


def _split_intent_op(item: Dict[str, Any], inherited: str = REPLACE) -> Tuple[Dict[str, Any], str, Optional[str]]:
    intent_key = next((k for k in item.keys() if k.startswith("intent")), None)
    if not intent_key:
        return item, inherited, None
    _, op = _parse_key(intent_key, inherited)
    new_item = dict(item)
    new_item["intent"] = new_item.pop(intent_key)
    return new_item, op, None


def _merge_nlu_docs(base_docs: List[Dict[str, Any]], overlay_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_intent: Dict[str, List[Dict[str, Any]]] = {}
    version = "3.1"

    def _feed(doc: Dict[str, Any]):
        nonlocal version
        if "version" in doc:
            version = doc["version"]
        for it in cast(List[Any], doc.get("nlu") or []):
            if isinstance(it, dict):
                item = cast(Dict[str, Any], it)
                if "intent" in item:
                    by_intent.setdefault(cast(str, item["intent"]), []).append(item)

    for d in base_docs:
        clean, _ = _normalize_ops(d, REPLACE)
        _feed(clean)

    for d in overlay_docs:
        clean, parent_op = _normalize_ops(d, REPLACE)
        for raw in cast(List[Any], clean.get("nlu") or []):
            item_raw = cast(Dict[str, Any], raw)
            item, item_op, name_from_marker = _split_intent_op(item_raw, inherited=parent_op)
            intent = cast(Optional[str], name_from_marker or item.get("intent"))
            if not intent:
                continue
            if item_op == REPLACE:
                if intent not in by_intent:
                    raise ValueError(f"Overlay attempted to replace unknown intent '{intent}'")
                by_intent[intent] = [item]
            else:
                by_intent.setdefault(intent, []).append(item)

    merged_items: List[Dict[str, Any]] = []
    for items in by_intent.values():
        merged_items.extend(items)
    return {"version": version, "nlu": merged_items}


def _derive_nlu_paths(domain_paths: List[Path]) -> List[Path]:
    n_paths: List[Path] = []
    for d in domain_paths:
        root = d.parent
        for rel in (Path("data") / "nlu", Path("nlu")):
            cand = root / rel
            if cand.exists():
                n_paths.append(cand)
    return n_paths


def _parse_comma_paths(value: Optional[str]) -> List[Path]:
    if not value:
        return []
    out: List[Path] = []
    for s in [s.strip() for s in value.split(",") if s.strip()]:
        p = Path(s)
        if p.exists():
            out.append(p)
    return out


def _uniq_paths(paths: List[Path]) -> List[Path]:
    seen: Set[str] = set()
    out: List[Path] = []
    for x in paths:
        sx = str(x)
        if sx not in seen:
            seen.add(sx)
            out.append(x)
    return out


def _to_existing_strs(paths: List[Path]) -> List[str]:
    out: List[str] = []
    for p in paths:
        if p.exists():
            if p.is_dir():
                out.append(str(p))
            elif p.is_file() and p.suffix.lower() in {".yml", ".yaml"}:
                out.append(str(p))
    return out


class OverlayImporter(TrainingDataImporter):
    def __init__(self, *args: Any, base_domain: Optional[List[str]] = None, overlay_domain: Optional[List[str]] = None, **kwargs: Any):
        cfg: Dict[str, Any] = {}
        if args and isinstance(args[0], dict):
            cfg.update(cast(Dict[str, Any], args[0]))
        cfg.update(kwargs)

        base_domain = base_domain if base_domain is not None else cfg.get("base_domain")
        overlay_domain = overlay_domain if overlay_domain is not None else cfg.get("overlay_domain")

        self._base_domain_paths = [Path(p) for p in (base_domain or [])]
        self._overlay_domain_paths = [Path(p) for p in (overlay_domain or [])]
        logger.info(f"Base domain files: {[str(p) for p in self._base_domain_paths]}")
        logger.info(f"Overlay domain files: {[str(p) for p in self._overlay_domain_paths]}")

        # Allow env to override base/overlay domains dynamically
        env_base_domain = os.environ.get("OVERLAY_BASE_DOMAIN", "").strip()
        if env_base_domain:
            override_paths = _parse_comma_paths(env_base_domain)
            if override_paths:
                self._base_domain_paths = override_paths

        # Allow env to override overlay domains dynamically for CI/builds
        env_overlay_domain = os.environ.get("OVERLAY_DOMAIN", "").strip()
        if env_overlay_domain:
            override_paths = _parse_comma_paths(env_overlay_domain)
            if override_paths:
                self._overlay_domain_paths = override_paths

        self._base_nlu_paths: List[Path] = _derive_nlu_paths(self._base_domain_paths)
        self._overlay_nlu_paths: List[Path] = _derive_nlu_paths(self._overlay_domain_paths)

        raw_overlay_nlu: Any = cfg.get("overlay_nlu")
        env_overlay_nlu: List[str] = []
        if isinstance(raw_overlay_nlu, str):
            env_overlay_nlu = [p.strip() for p in raw_overlay_nlu.split(",") if p.strip()]
        elif isinstance(raw_overlay_nlu, list):
            for p in cast(List[Any], raw_overlay_nlu):
                s = str(p).strip()
                if s:
                    env_overlay_nlu.append(s)
        for p in env_overlay_nlu:
            pp = Path(p)
            if pp.exists():
                self._overlay_nlu_paths.append(pp)

        env_str = os.environ.get("OVERLAY_NLU", "").strip()
        if env_str:
            for pp in _parse_comma_paths(env_str):
                self._overlay_nlu_paths.append(pp)

        self._base_nlu_paths = _uniq_paths(self._base_nlu_paths)
        self._overlay_nlu_paths = _uniq_paths(self._overlay_nlu_paths)
        if self._base_nlu_paths:
            logger.info(f"Base NLU paths: {[str(p) for p in self._base_nlu_paths]}")
        if self._overlay_nlu_paths:
            logger.info(f"Overlay NLU paths: {[str(p) for p in self._overlay_nlu_paths]}")

    def get_domain(self) -> Domain:
        base_docs: List[Dict[str, Any]] = []
        for p in self._base_domain_paths:
            if not _has_yaml_under(p):
                logger.info(f"Skipping base domain path with no YAML: {p}")
                continue
            logger.info(f"Loading base domain: {p}")
            base_docs.append(Domain.load(str(p)).as_dict())
        overlay_docs: List[Dict[str, Any]] = []
        for p in self._overlay_domain_paths:
            if not _has_yaml_under(p):
                logger.info(f"Skipping overlay domain path with no YAML: {p}")
                continue
            logger.info(f"Loading overlay domain: {p}")
            overlay_docs.append(Domain.load(str(p)).as_dict())
        logger.info("Merging domains...")
        merged = _merge_domain_docs(base_docs, overlay_docs)
        logger.info(f"Merged domain keys: {list(merged.keys())}")
        for ov_doc in overlay_docs:
            for k in ov_doc.keys():
                if k in merged:
                    logger.info(f"Overlay key '{k}' present in merged domain.")

        dump_target = os.environ.get("OVERLAY_DUMP_DOMAIN", "").strip()
        if dump_target:
            try:
                if dump_target.lower() in {"1", "true", "yes", "stdout"}:
                    yaml.safe_dump(merged, sys.stdout, sort_keys=False, allow_unicode=True)
                else:
                    out_path = Path(dump_target)
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    with out_path.open("w", encoding="utf-8") as f:
                        yaml.safe_dump(merged, f, sort_keys=False, allow_unicode=True)
                    logger.info(f"Dumped merged domain to {out_path}")
            except Exception as e:
                logger.warning(f"Failed to dump merged domain: {e}")
        return Domain.from_dict(merged)  # type: ignore[arg-type]

    def get_nlu_data(self, language: Optional[str] = None) -> TrainingData:
        base_paths = _to_existing_strs(self._base_nlu_paths)
        overlay_paths = _to_existing_strs(self._overlay_nlu_paths)

        if not base_paths and not overlay_paths:
            with tempfile.TemporaryDirectory(prefix="v2_empty_nlu_") as td:
                tmp = Path(td) / "empty_nlu.yml"
                with tmp.open("w", encoding="utf-8") as f:
                    yaml.safe_dump({"version": "3.1", "nlu": []}, f, sort_keys=False, allow_unicode=True)
                return nlu_loading.load_data(str(tmp))

        logger.info(f"Merging NLU from base={base_paths} overlays={overlay_paths}")
        base_docs = _load_yaml_docs([Path(p) for p in base_paths])
        overlay_docs = _load_yaml_docs([Path(p) for p in overlay_paths])
        merged: Dict[str, Any] = _merge_nlu_docs(base_docs, overlay_docs)
        merged_nlu_list = cast(List[Dict[str, Any]], merged.get("nlu", []))
        intents = [str(it.get("intent")) for it in merged_nlu_list if it.get("intent")]
        logger.info(f"Merged NLU intents: {sorted(set(intents))}")

        dump_target = os.environ.get("OVERLAY_DUMP_NLU", "").strip()
        with tempfile.TemporaryDirectory(prefix="v2_merged_nlu_") as td:
            tmp = Path(td) / "merged_nlu.yml"
            with tmp.open("w", encoding="utf-8") as f:
                yaml.safe_dump(merged, f, sort_keys=False, allow_unicode=True)

            if dump_target:
                try:
                    if dump_target.lower() in {"1", "true", "yes", "stdout"}:
                        yaml.safe_dump(merged, sys.stdout, sort_keys=False, allow_unicode=True)
                    else:
                        out_path = Path(dump_target)
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        with out_path.open("w", encoding="utf-8") as outf:
                            yaml.safe_dump(merged, outf, sort_keys=False, allow_unicode=True)
                        logger.info(f"Dumped merged NLU to {out_path}")
                except Exception as e:
                    logger.warning(f"Failed to dump merged NLU: {e}")

            return nlu_loading.load_data(str(tmp))

    def get_stories(self, exclusion_percentage: Optional[int] = None) -> StoryGraph:
        return StoryGraph([])

    def get_config(self) -> Dict[str, Any]:
        return {}

    def get_config_file_for_auto_config(self) -> Optional[str]:
        return None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m src.components.layered_importer <base_domain_path> <overlay_domain_path>")
        sys.exit(1)
    importer = OverlayImporter(base_domain=[sys.argv[1]], overlay_domain=[sys.argv[2]])
    merged_domain = importer.get_domain()
    yaml.safe_dump(merged_domain.as_dict(), sys.stdout, sort_keys=False, allow_unicode=True)
