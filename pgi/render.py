from __future__ import annotations

from pgi.model import STAGE_ORDER, Session, Support
from pgi.seed import order_key

_STAGE_LINE = {
    "quantity": "A quantity is fixed by the operation",
    "ground": "Ground condition follows from the weather and the cover",
    "path": "Path condition follows from the ground",
    "answer": "The answer follows from the supported conditions",
    "check": "A proposed claim was checked and did not settle",
    "link": "A sourced record is on the board. A link is not a settled answer",
}


def render(session: Session, lod: int, zoom: dict[str, int]) -> str:
    lines = [
        f"PGI {session.rule_version}",
        f"seed {session.seed}",
        f"lod {lod}",
        f"ask {session.request.ask}",
        "",
    ]
    if session.request.facts:
        lines.append("Anchors")
        for fact in session.request.facts:
            mark = " contested" if fact in session.retracted else ""
            lines.append(f"- {fact}{mark}")
        lines.append("")
    lines.append("Outline")
    if lod <= 0:
        lines.extend(_stage_outline(session))
    else:
        shown = _ordered(session, session.seed)
        if not shown:
            lines.append("- none")
        for index, support in enumerate(shown, start=1):
            lines.extend(_claim_block(support, index, _line_lod(support, lod, zoom)))
    if session.dropped:
        lines.append("")
        lines.append("Retracted")
        for support in session.dropped:
            lines.append(f"- [{support.rule_id}] {support.title}")
    lines.append("")
    lines.append("Clashes")
    if session.clashes:
        for clash in session.clashes:
            lines.append(f"- {clash.left} contradicts {clash.right}")
        if session.retracted:
            lines.append(f"  retracted: {', '.join(session.retracted)}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("Open")
    if session.open_gaps:
        for gap in session.open_gaps:
            lines.append(f"- {gap}")
    else:
        lines.append("- none")
    return "\n".join(lines)


def _stage_outline(session: Session) -> list[str]:
    present = {claim.stage for claim in session.claims}
    lines = []
    number = 1
    for stage in STAGE_ORDER:
        if stage not in present:
            continue
        lines.append(f"{number}. {_STAGE_LINE[stage]}")
        number += 1
    if not lines:
        lines.append("- none")
    return lines


def _ordered(session: Session, seed: int) -> tuple[Support, ...]:
    return tuple(
        sorted(
            session.claims,
            key=lambda support: (
                STAGE_ORDER.index(support.stage),
                order_key(seed, support.rule_id),
                support.rule_id,
            ),
        )
    )


def _line_lod(support: Support, lod: int, zoom: dict[str, int]) -> int:
    raised = lod
    if support.rule_id in zoom:
        raised = max(raised, zoom[support.rule_id])
    if support.atom in zoom:
        raised = max(raised, zoom[support.atom])
    return raised


def _claim_block(support: Support, index: int, lod: int) -> list[str]:
    lines = [f"{index}. [{support.rule_id}] {support.title}"]
    if support.because:
        lines.append(f"   {support.atom} because {', '.join(support.because)}")
    elif support.atom.startswith("value("):
        lines.append(f"   {support.atom} is the exact result")
    elif support.atom.startswith("ratio("):
        lines.append(f"   {support.atom} is the exact rational")
    elif support.atom.startswith("cauchy("):
        lines.append(f"   {support.atom} is the constructed real")
    elif support.atom.startswith("matrix("):
        lines.append(f"   {support.atom} is the exact rational matrix")
    elif support.atom.startswith("charpoly("):
        lines.append(f"   {support.atom} is the characteristic polynomial")
    elif support.atom.startswith("poly("):
        lines.append(f"   {support.atom} is the exact polynomial")
    elif support.atom.startswith("rat("):
        lines.append(f"   {support.atom} is the exact rational function")
    elif support.atom.startswith("identity(") and " = " not in support.atom:
        lines.append(f"   {support.atom} is the identity map on these coordinates")
    elif support.atom.startswith("map("):
        lines.append(f"   {support.atom} is the exact rational map")
    elif support.atom.startswith("jac("):
        lines.append(f"   {support.atom} is the exact Jacobian")
    elif support.atom == "eigenvalues()":
        lines.append("   eigenvalues() is the empty set of real eigenvalues")
    elif support.atom.startswith("eigenvalues("):
        lines.append(f"   {support.atom} are the real eigenvalues")
    elif support.atom.startswith("set("):
        lines.append(f"   {support.atom} is the finite set")
    elif " union " in support.atom:
        lines.append(f"   {support.atom} is the union of these admitted intervals")
    elif support.atom.startswith("atMost("):
        lines.append(f"   {support.atom} is the set of reals at most this bound")
    elif support.atom.startswith("atLeast("):
        lines.append(f"   {support.atom} is the set of reals at least this bound")
    elif support.atom.startswith("lessThan("):
        lines.append(f"   {support.atom} is the set of reals strictly below this bound")
    elif support.atom.startswith("greaterThan("):
        lines.append(f"   {support.atom} is the set of reals strictly above this bound")
    elif support.atom.startswith("atLeastAtMost("):
        lines.append(f"   {support.atom} is the closed interval from the lower bound through the upper bound")
    elif support.atom.startswith("greaterThanAtMost("):
        lines.append(f"   {support.atom} is the interval strictly above the lower bound through the upper bound")
    elif support.atom.startswith("atLeastLessThan("):
        lines.append(f"   {support.atom} is the interval from the lower bound strictly below the upper bound")
    elif support.atom.startswith("greaterThanLessThan("):
        lines.append(f"   {support.atom} is the open interval strictly between these bounds")
    elif support.atom == "univ":
        lines.append("   univ is the set of every real")
    elif support.atom.startswith("complete(lessThan("):
        lines.append(f"   {support.atom} is the least upper bound of this open ray")
    elif support.atom.startswith("complete(atMost("):
        lines.append(f"   {support.atom} is the least upper bound of this order ray")
    elif support.atom.startswith(("complete(atLeastAtMost(", "complete(greaterThanAtMost(", "complete(atLeastLessThan(", "complete(greaterThanLessThan(")):
        lines.append(f"   {support.atom} is the least upper bound of this interval")
    elif support.atom.startswith("complete("):
        lines.append(f"   {support.atom} is the least upper bound of this finite set")
    elif support.atom.startswith(("member(", "not_member(", "subset(", "not_subset(", "all(", "not_all(", "ex(", "not_ex(")):
        lines.append(f"   {support.atom} holds")
    else:
        lines.append(f"   {support.atom}")
    if lod >= 2:
        for detail in support.detail_lines:
            lines.append(f"   {detail}")
    return lines
