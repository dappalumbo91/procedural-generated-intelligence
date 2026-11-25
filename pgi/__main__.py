from __future__ import annotations

import argparse
from pathlib import Path

from pgi.engine import unfold
from pgi.journal import append_journal
from pgi.model import Request
from pgi.scenes import demo_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m pgi",
        description="Unfold a procedural answer from rules, a seed, and constraints.",
    )
    parser.add_argument("ask", nargs="?", help="question or expression to unfold")
    parser.add_argument("--fact", action="append", default=[], help="anchor fact; repeatable")
    parser.add_argument("--lod", type=int, default=1, help="0 outline, 1 claims, 2 claims plus detail")
    parser.add_argument("--seed", type=int, default=None, help="explicit seed; omit to derive one")
    parser.add_argument("--domain", default=None, help="force a domain pack, such as causal")
    parser.add_argument("--zoom", action="append", default=[], help="rule_id=lod, repeatable")
    parser.add_argument("--demo", action="store_true", help="print the baked scenes")
    parser.add_argument("--journal", default=None, help="append a JSON line for this unfold")
    args = parser.parse_args(argv)

    if args.demo:
        print(demo_text())
        return 0
    if not args.ask:
        parser.print_help()
        return 2

    session = unfold(
        Request(
            ask=args.ask,
            facts=tuple(args.fact),
            domain=args.domain,
            lod=args.lod,
            seed=args.seed,
        )
    )
    print(session.text(lod=args.lod, zoom=_zoom(args.zoom)))
    if args.journal:
        append_journal(Path(args.journal), session)
    return 0


def _zoom(items: list[str]) -> dict[str, int]:
    zoom: dict[str, int] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"zoom must look like rule_id=2, got {item}")
        rule_id, _, raw = item.partition("=")
        zoom[rule_id] = int(raw)
    return zoom


if __name__ == "__main__":
    raise SystemExit(main())
