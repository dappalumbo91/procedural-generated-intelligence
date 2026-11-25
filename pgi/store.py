from __future__ import annotations

import json
from pathlib import Path

from pgi.model import Rule

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STORE = ROOT / "rules" / "local.json"

_REQUIRED = ("id", "title", "produces")


def load_store(path: Path | None = None) -> tuple[Rule, ...]:
    store = DEFAULT_STORE if path is None else path
    if not store.exists():
        return ()
    payload = json.loads(store.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{store} must be a list of rules")
    rules: list[Rule] = []
    for index, item in enumerate(payload):
        rules.append(_rule_from_json(index, item, store))
    return tuple(rules)


def _rule_from_json(index: int, item: object, store: Path) -> Rule:
    if not isinstance(item, dict):
        raise ValueError(f"{store} rule {index} must be an object")
    missing = [key for key in _REQUIRED if not item.get(key)]
    if missing:
        raise ValueError(f"{store} rule {index} is missing {', '.join(missing)}")
    stage = str(item.get("stage", "path"))
    if stage not in {"quantity", "ground", "path", "answer"}:
        raise ValueError(f"{store} rule {item['id']} has an unknown stage {stage}")
    return Rule(
        id=str(item["id"]),
        layer=str(item.get("layer", "domain")),
        stage=stage,
        title=str(item["title"]),
        produces=str(item["produces"]),
        requires=_strings(item.get("requires", ())),
        absent=_strings(item.get("absent", ())),
        variants=_strings(item.get("variants", ())),
        detail_lines=_strings(item.get("detail_lines", ())),
    )


def _strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("rule fields requires, absent, variants, and detail_lines must be lists")
    return tuple(str(item) for item in value)
