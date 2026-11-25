from __future__ import annotations

from pgi.model import Clash, Support


def contradicts(left: str, right: str, pairs: frozenset[frozenset[str]]) -> bool:
    if left == right:
        return False
    if left.startswith("value(") and right.startswith("value("):
        return True
    return frozenset((left, right)) in pairs


def settle(
    held: set[str],
    supports: list[Support],
    givens: set[str],
    pairs: frozenset[frozenset[str]],
) -> tuple[tuple[Support, ...], tuple[Support, ...], tuple[Clash, ...], tuple[str, ...]]:
    """Drop contradictory atoms and every claim that rests only on them.

    Saturation is allowed to derive both sides. The settle then retracts the
    clash and its dependents, so rule order cannot pick a winner.
    """
    atoms = set(held)
    contested: set[str] = set()
    clashes: set[Clash] = set()
    ordered_atoms = sorted(atoms)
    for index, left in enumerate(ordered_atoms):
        for right in ordered_atoms[index + 1 :]:
            if contradicts(left, right, pairs):
                contested.add(left)
                contested.add(right)
                pair = tuple(sorted((left, right)))
                clashes.add(Clash(pair[0], pair[1]))

    derived = {support.atom for support in supports}
    changed = True
    while changed:
        changed = False
        for atom in sorted(derived):
            if atom in contested or atom in givens:
                continue
            mine = [support for support in supports if support.atom == atom]
            if mine and all(_tainted(support, contested) for support in mine):
                contested.add(atom)
                changed = True

    public = tuple(support for support in supports if not _tainted(support, contested))
    dropped = tuple(support for support in supports if _tainted(support, contested))
    retracted = tuple(sorted(contested))
    return public, dropped, tuple(sorted(clashes, key=lambda item: (item.left, item.right))), retracted


def _tainted(support: Support, contested: set[str]) -> bool:
    if support.atom in contested:
        return True
    return any(item in contested for item in support.because)
