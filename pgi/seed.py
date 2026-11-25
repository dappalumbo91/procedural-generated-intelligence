from __future__ import annotations

import hashlib


def derive_seed(rule_version: str, ask: str, facts: tuple[str, ...], domain: str | None) -> int:
    body = "\n".join(
        (
            rule_version,
            ask,
            "\n".join(facts),
            domain or "",
        )
    )
    digest = hashlib.sha256(body.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def variant_index(seed: int, rule_id: str, count: int) -> int:
    if count <= 1:
        return 0
    digest = hashlib.sha256(f"{seed}:variant:{rule_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % count


def order_key(seed: int, rule_id: str) -> bytes:
    return hashlib.sha256(f"{seed}:order:{rule_id}".encode("utf-8")).digest()
