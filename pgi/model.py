from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

STAGE_ORDER = ("quantity", "ground", "path", "answer", "check", "link")
ANSWER_STAGES = frozenset({"quantity", "answer"})

_TOKEN = re.compile(r"[a-z0-9_]+")
_SPACE = re.compile(r"\s+")

_FACT_ALIASES = {
    "above freezing": "above_freezing",
    "below freezing": "freezing",
    "freezing": "freezing",
    "covered": "covered(path)",
    "covered path": "covered(path)",
    "wet": "wet(ground)",
    "wet ground": "wet(ground)",
    "dry": "dry(ground)",
    "dry ground": "dry(ground)",
    "dusk": "dusk",
    "rain": "rain",
    "loose": "loose(ground)",
    "loose ground": "loose(ground)",
    "loose gravel": "loose(ground)",
}


class Pack(Protocol):
    name: str

    def active(self, request: Request) -> bool: ...

    def rules(self, request: Request) -> tuple[Rule, ...]: ...

    def exclusions(self) -> tuple[tuple[str, str], ...]: ...


@dataclass(frozen=True)
class Request:
    ask: str
    facts: tuple[str, ...] = ()
    domain: str | None = None
    lod: int = 1
    seed: int | None = None


@dataclass(frozen=True)
class Rule:
    id: str
    layer: str
    stage: str
    title: str
    produces: str
    requires: tuple[str, ...] = ()
    absent: tuple[str, ...] = ()
    variants: tuple[str, ...] = ()
    detail_lines: tuple[str, ...] = ()

    def ready(self, held: set[str]) -> bool:
        if any(item not in held for item in self.requires):
            return False
        if any(item in held for item in self.absent):
            return False
        return True


@dataclass(frozen=True)
class Support:
    rule_id: str
    layer: str
    stage: str
    title: str
    atom: str
    because: tuple[str, ...]
    detail_lines: tuple[str, ...] = ()


@dataclass(frozen=True)
class Clash:
    left: str
    right: str


@dataclass(frozen=True)
class Session:
    rule_version: str
    seed: int
    request: Request
    claims: tuple[Support, ...]
    dropped: tuple[Support, ...]
    clashes: tuple[Clash, ...]
    retracted: tuple[str, ...]
    open_gaps: tuple[str, ...]
    capped: bool = False

    def text(self, lod: int | None = None, zoom: dict[str, int] | None = None) -> str:
        from pgi.render import render

        shown = self.request.lod if lod is None else lod
        return render(self, shown, zoom or {})

    def as_dict(self) -> dict[str, object]:
        return {
            "ask": self.request.ask,
            "claims": [
                {
                    "atom": claim.atom,
                    "because": list(claim.because),
                    "detail": list(claim.detail_lines),
                    "rule": claim.rule_id,
                    "stage": claim.stage,
                }
                for claim in self.claims
            ],
            "clashes": [{"left": clash.left, "right": clash.right} for clash in self.clashes],
            "domain": self.request.domain,
            "facts": list(self.request.facts),
            "lod": self.request.lod,
            "open_gaps": list(self.open_gaps),
            "retracted": list(self.retracted),
            "rule_version": self.rule_version,
            "seed": self.seed,
        }


def normalize_ask(ask: str) -> str:
    text = _SPACE.sub(" ", ask.strip())
    if text.endswith(("?", "!", ".")):
        text = text[:-1].strip()
    return text.lower()


def normalize_fact(fact: str) -> str:
    text = _SPACE.sub(" ", fact.strip())
    lowered = text.lower()
    if lowered.startswith("value(") and lowered.endswith(")"):
        inner = lowered[len("value(") : -1].replace(" ", "")
        return f"value({inner})"
    return _FACT_ALIASES.get(lowered, lowered)


def normalize_facts(facts: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for fact in facts:
        item = normalize_fact(fact)
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return tuple(sorted(ordered))


def normalize_request(request: Request) -> Request:
    domain = request.domain.strip().lower() if request.domain else None
    if domain == "":
        domain = None
    return Request(
        ask=normalize_ask(request.ask),
        facts=normalize_facts(request.facts),
        domain=domain,
        lod=request.lod,
        seed=request.seed,
    )


def tokens(text: str) -> set[str]:
    found: set[str] = set()
    for token in _TOKEN.findall(text.lower()):
        found.add(token)
        found.update(piece for piece in token.split("_") if piece)
    return found


def term_hit(text: str, terms: tuple[str, ...]) -> bool:
    found = tokens(text)
    for term in terms:
        for token in found:
            if token == term or (len(term) >= 4 and token.startswith(term)):
                return True
    return False
