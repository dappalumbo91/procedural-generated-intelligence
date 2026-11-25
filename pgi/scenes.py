from __future__ import annotations

from pgi.engine import unfold
from pgi.model import Request


def warm_rain(seed: int | None = 1, lod: int = 1) -> Request:
    return Request(
        ask="why is the path risky?",
        facts=("rain", "above_freezing"),
        lod=lod,
        seed=seed,
    )


def covered_rain(seed: int | None = 1, lod: int = 1) -> Request:
    return Request(
        ask="why is the path risky?",
        facts=("rain", "covered path"),
        lod=lod,
        seed=seed,
    )


def ice_and_dusk(seed: int | None = 1, lod: int = 1) -> Request:
    return Request(
        ask="why is the path risky?",
        facts=("rain", "freezing", "dusk"),
        lod=lod,
        seed=seed,
    )


def contested_ground(seed: int | None = 1, lod: int = 1) -> Request:
    return Request(
        ask="why is the path risky?",
        facts=("wet ground", "dry ground", "above freezing"),
        lod=lod,
        seed=seed,
    )


def seventeen(lod: int = 1, seed: int | None = 1) -> Request:
    return Request(ask="what is 17 plus 13?", lod=lod, seed=seed)


def wrong_sum(seed: int | None = 1) -> Request:
    return Request(ask="what is 17 plus 13?", facts=("value(31)",), lod=2, seed=seed)


def demo_text() -> str:
    blocks = [
        "=== warm rain, outline ===",
        unfold(warm_rain(lod=0)).text(lod=0),
        "",
        "=== warm rain, zoomed ===",
        unfold(warm_rain(lod=2)).text(lod=2),
        "",
        "=== covered rain ===",
        unfold(covered_rain()).text(lod=1),
        "",
        "=== ice and dusk, seed 0 ===",
        unfold(ice_and_dusk(seed=0)).text(lod=1),
        "",
        "=== ice and dusk, seed 1 ===",
        unfold(ice_and_dusk(seed=1)).text(lod=1),
        "",
        "=== contested wet and dry ===",
        unfold(contested_ground()).text(lod=1),
        "",
        "=== 17 + 13, outline ===",
        unfold(seventeen(lod=0)).text(lod=0),
        "",
        "=== 17 + 13, places ===",
        unfold(seventeen(lod=2)).text(lod=2),
        "",
        "=== asserted value(31) ===",
        unfold(wrong_sum()).text(lod=1),
        "",
        "=== precedence ===",
        unfold(Request(ask="what is 2 + 3 * 4", seed=1)).text(lod=1),
        "",
        "=== sourced lengths ===",
        unfold(
            Request(
                ask="what is length * width",
                facts=("length=4@meter stick", "width=3@meter stick"),
                seed=1,
            )
        ).text(lod=2),
        "",
        "=== integer order ===",
        unfold(Request(ask="prove 2 <= 5", seed=1)).text(lod=2),
        "",
        "=== compound order ===",
        unfold(Request(ask="prove 1 + 1 <= 3", seed=1)).text(lod=2),
        "",
        "=== rational sum ===",
        unfold(Request(ask="what is 1/2 + 1/3", lod=2, seed=1)).text(lod=2),
        "",
        "=== square root ===",
        unfold(Request(ask="what is sqrt(2)", lod=2, seed=1)).text(lod=2),
        "",
        "=== finite set ===",
        unfold(Request(ask="what is sup {1, sqrt(2)}", lod=2, seed=1)).text(lod=2),
        "",
        "=== quantifier ===",
        unfold(Request(ask="prove complete {1, sqrt(2)}", lod=2, seed=1)).text(lod=2),
        "",
        "=== comprehension ===",
        unfold(Request(ask="what is {x in {1, 2, 3}. x <= 2}", lod=2, seed=1)).text(lod=2),
        "",
        "=== arbitrary set ===",
        unfold(Request(ask="what is {x. x <= 2}", lod=2, seed=1)).text(lod=2),
        "",
        "=== least upper bound ===",
        unfold(Request(ask="what is sup {x. x <= 2}", lod=2, seed=1)).text(lod=2),
        "",
        "=== archimedean bisection ===",
        unfold(Request(ask="what is sup {x. x < 2}", lod=2, seed=1)).text(lod=2),
        "",
        "=== two-sided interval ===",
        unfold(Request(ask="what is sup ({x. 1 <= x} inter {x. x <= 3})", lod=2, seed=1)).text(lod=2),
        "",
        "=== boolean connective ===",
        unfold(Request(ask="what is sup {x. 1 <= x and x <= 3}", lod=2, seed=1)).text(lod=2),
        "",
        "=== nested radical ===",
        unfold(Request(ask="what is sqrt(sqrt(2))", lod=2, seed=1)).text(lod=2),
        "",
        "=== division ===",
        unfold(Request(ask="what is sqrt(2) / sqrt(3)", lod=2, seed=1)).text(lod=2),
        "",
        "=== product of radicals ===",
        unfold(Request(ask="what is sqrt(2) * sqrt(sqrt(3))", lod=2, seed=1)).text(lod=2),
        "",
        "=== binomial nest ===",
        unfold(Request(ask="what is sqrt(2 + sqrt(2))", lod=2, seed=1)).text(lod=2),
        "",
        "=== two square roots ===",
        unfold(Request(ask="what is sqrt(sqrt(2) + sqrt(3))", lod=2, seed=1)).text(lod=2),
        "",
        "=== two square roots, non-square gap ===",
        unfold(Request(ask="what is sqrt(sqrt(2) + sqrt(5))", lod=2, seed=1)).text(lod=2),
        "",
        "=== square root of a nested binomial ===",
        unfold(Request(ask="what is sqrt(sqrt(2 + sqrt(2)))", lod=2, seed=1)).text(lod=2),
        "",
        "=== square root of a pair radical ===",
        unfold(Request(ask="what is sqrt(sqrt(sqrt(2) + sqrt(5)))", lod=2, seed=1)).text(lod=2),
        "",
        "=== square root of a high ===",
        unfold(Request(ask="what is sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))", lod=2, seed=1)).text(lod=2),
        "",
        "=== square root of a peak ===",
        unfold(Request(ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))", lod=2, seed=1)).text(lod=2),
        "",
        "=== square root of a crest ===",
        unfold(Request(ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))", lod=2, seed=1)).text(lod=2),
        "",
        "=== square root of a summit ===",
        unfold(Request(ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))", lod=2, seed=1)).text(lod=2),
        "",
        "=== further square roots ===",
        unfold(Request(ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))", lod=2, seed=1)).text(lod=2),
        "",
        "=== square root of the nested binomial ===",
        unfold(Request(ask="what is sqrt(sqrt(sqrt(2 + sqrt(2))))", lod=2, seed=1)).text(lod=2),
        "",
        "=== inverse of the denested sum ===",
        unfold(Request(ask="what is 1 / sqrt(sqrt(2) + sqrt(3))", lod=2, seed=1)).text(lod=2),
        "",
        "=== inverse of a further nested binomial ===",
        unfold(Request(ask="what is 1 / sqrt(sqrt(sqrt(2 + sqrt(2))))", lod=2, seed=1)).text(lod=2),
        "",
        "=== square root of one plus sqrt(2) plus sqrt(5) ===",
        unfold(Request(ask="what is sqrt(1 + sqrt(2) + sqrt(5))", lod=2, seed=1)).text(lod=2),
        "",
        "=== opera timing is linked, not settled ===",
        unfold(Request(ask="what happened with the opera neutrinos", seed=1)).text(lod=1),
    ]
    return "\n".join(blocks)
