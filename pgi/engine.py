from __future__ import annotations

from pathlib import Path

from pgi.constraints import settle
from pgi.model import (
    ANSWER_STAGES,
    STAGE_ORDER,
    Pack,
    Request,
    Rule,
    Session,
    Support,
    normalize_request,
)
from pgi.packs.base import BasePack
from pgi.packs.causal import CausalPack
from pgi.packs.link import LinkPack
from pgi.seed import derive_seed, variant_index
from pgi.store import load_store
from pgi.version import RULE_VERSION

DEFAULT_PACKS = (BasePack(), CausalPack(), LinkPack())


def unfold(
    request: Request,
    *,
    packs: tuple[Pack, ...] | None = None,
    extra_rules: tuple[Rule, ...] = (),
    extra_pairs: tuple[tuple[str, str], ...] = (),
    store_path: Path | None = None,
    rule_version: str = RULE_VERSION,
    use_store: bool = True,
) -> Session:
    normalized = normalize_request(request)
    chosen = DEFAULT_PACKS if packs is None else packs
    rules: list[Rule] = []
    pairs: set[frozenset[str]] = set()
    for pack in chosen:
        if pack.active(normalized):
            rules.extend(pack.rules(normalized))
            for left, right in pack.exclusions():
                pairs.add(frozenset((left, right)))
    if use_store:
        rules.extend(load_store(store_path))
    rules.extend(extra_rules)
    for left, right in extra_pairs:
        pairs.add(frozenset((left, right)))
    _reject_duplicate_ids(rules)

    seed = normalized.seed
    if seed is None:
        seed = derive_seed(rule_version, normalized.ask, normalized.facts, normalized.domain)

    held = set(normalized.facts)
    supports: list[Support] = []
    fired: set[str] = set()
    ordered = tuple(sorted(rules, key=lambda rule: rule.id))
    capped = False
    for _ in range(len(ordered) + 1):
        snapshot = set(held)
        ready = [rule for rule in ordered if rule.id not in fired and rule.ready(snapshot)]
        if not ready:
            break
        for rule in ready:
            fired.add(rule.id)
            held.add(rule.produces)
            supports.append(_support(rule, seed))
    else:
        capped = True

    public, dropped, clashes, retracted = settle(held, supports, set(normalized.facts), frozenset(pairs))
    claims = _canonical(public)
    dropped_claims = _canonical(dropped)
    gaps = _gaps(claims, clashes, capped)
    return Session(
        rule_version=rule_version,
        seed=seed,
        request=normalized,
        claims=claims,
        dropped=dropped_claims,
        clashes=clashes,
        retracted=retracted,
        open_gaps=gaps,
        capped=capped,
    )


def _support(rule: Rule, seed: int) -> Support:
    if rule.variants:
        index = variant_index(seed, rule.id, len(rule.variants))
        lines = (rule.variants[index],)
    else:
        lines = rule.detail_lines
    return Support(
        rule_id=rule.id,
        layer=rule.layer,
        stage=rule.stage,
        title=rule.title,
        atom=rule.produces,
        because=rule.requires,
        detail_lines=lines,
    )


def _canonical(supports: tuple[Support, ...] | list[Support]) -> tuple[Support, ...]:
    return tuple(
        sorted(
            supports,
            key=lambda support: (STAGE_ORDER.index(support.stage), support.rule_id, support.atom),
        )
    )


def _gaps(claims: tuple[Support, ...], clashes: tuple[object, ...], capped: bool) -> tuple[str, ...]:
    gaps: list[str] = []
    if capped:
        gaps.append("Rule saturation stopped at the step cap.")
    answered = any(claim.stage in ANSWER_STAGES for claim in claims)
    linked = any(claim.stage == "link" for claim in claims)
    if not answered and clashes:
        gaps.append("Contested claims blocked a settled answer.")
    elif not answered and linked:
        gaps.append("Linked records are on the board. None of them is a settled answer.")
    elif not answered:
        gaps.append("No answer rule fired from the given facts.")
    return tuple(gaps)


def _reject_duplicate_ids(rules: list[Rule]) -> None:
    seen: set[str] = set()
    for rule in rules:
        if rule.id in seen:
            raise ValueError(f"duplicate rule id {rule.id}")
        seen.add(rule.id)
