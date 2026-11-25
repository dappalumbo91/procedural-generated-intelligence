from __future__ import annotations

from pgi.math.numerals import add_lines, sub_lines
from pgi.math.prove import rules_from_ask
from pgi.model import Request, Rule

__all__ = ["BasePack", "add_lines", "sub_lines"]


class BasePack:
    """Integer kernel. Every numeric claim is a checked theorem."""

    name = "base"

    def active(self, request: Request) -> bool:
        return True

    def exclusions(self) -> tuple[tuple[str, str], ...]:
        return ()

    def rules(self, request: Request) -> tuple[Rule, ...]:
        return rules_from_ask(request.ask, request.facts)
