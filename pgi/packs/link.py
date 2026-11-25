"""Link sourced records into the board.

A hit unfolds the record. It does not settle an answer and it does not emit
a value. Re-asserting a forbidden atom contests that atom against the record.
"""

from __future__ import annotations

from pgi.corpus.records import RECORDS, Record
from pgi.model import Request, Rule, tokens


class LinkPack:
    name = "link"

    def active(self, request: Request) -> bool:
        if request.domain == self.name:
            return True
        if request.domain not in (None, "auto"):
            return False
        return bool(_matching(request))

    def exclusions(self) -> tuple[tuple[str, str], ...]:
        pairs: list[tuple[str, str]] = []
        for record in RECORDS:
            for atom in record.forbids:
                pairs.append((atom, f"blocked({record.id})"))
        return tuple(pairs)

    def rules(self, request: Request) -> tuple[Rule, ...]:
        found = _matching(request)
        rules: list[Rule] = []
        held = set(request.facts)
        for record in found:
            rules.append(_record_rule(record))
            for atom in record.forbids:
                if atom not in held:
                    continue
                rules.append(
                    Rule(
                        id=f"link.block.{record.id}.{atom}",
                        layer="corpus",
                        stage="link",
                        title=f"{atom} is blocked by {record.id}",
                        produces=f"blocked({record.id})",
                        requires=(atom,),
                        detail_lines=(f"{atom} contradicts the standing of {record.id}.",),
                    )
                )
        return tuple(rules)


def _matching(request: Request) -> tuple[Record, ...]:
    haystack = " ".join((request.ask, *request.facts))
    found = tokens(haystack)
    chosen: list[Record] = []
    for record in RECORDS:
        if any(key in found for key in record.keys):
            chosen.append(record)
            continue
        if any(phrase in haystack for phrase in record.phrases):
            chosen.append(record)
    return tuple(chosen)


def _record_rule(record: Record) -> Rule:
    return Rule(
        id=f"link.{record.id}",
        layer="corpus",
        stage="link",
        title=record.title,
        produces=f"record({record.id})",
        detail_lines=(*record.statement, f"source {record.source}", f"url {record.url}" if record.url else "url none", f"standing {record.standing}"),
    )
