from __future__ import annotations

from pgi.model import Request, Rule, term_hit

TERMS = (
    "rain",
    "path",
    "ground",
    "slip",
    "risk",
    "freez",
    "cover",
    "dusk",
    "wet",
    "icy",
    "ice",
    "visibility",
    "loose",
)

EXCLUSIONS = (
    ("wet(ground)", "dry(ground)"),
    ("freezing", "above_freezing"),
    ("slippery(path)", "firm(path)"),
)

RULES = (
    Rule(
        id="causal.wet_from_rain",
        layer="domain",
        stage="ground",
        title="Rain wets open ground",
        produces="wet(ground)",
        requires=("rain",),
        absent=("covered(path)",),
    ),
    Rule(
        id="causal.dry_from_cover",
        layer="domain",
        stage="ground",
        title="Cover keeps the ground dry",
        produces="dry(ground)",
        requires=("covered(path)",),
    ),
    Rule(
        id="causal.icy",
        layer="domain",
        stage="ground",
        title="Wet ground freezes",
        produces="icy(ground)",
        requires=("wet(ground)", "freezing"),
    ),
    Rule(
        id="causal.slip_water",
        layer="domain",
        stage="path",
        title="Wet ground above freezing is slippery",
        produces="slippery(path)",
        requires=("wet(ground)", "above_freezing"),
        absent=("freezing",),
        variants=(
            "Water on a hard surface cuts friction. The foot fails at the surface film.",
            "A thin water film carries the step. The slip is on the surface, not in the soil.",
        ),
    ),
    Rule(
        id="causal.slip_ice",
        layer="domain",
        stage="path",
        title="Ice makes the path slippery",
        produces="slippery(path)",
        requires=("icy(ground)",),
        variants=(
            "Ice bonds poorly to a shoe. The path sheds traction along the frozen film.",
            "A frozen crust breaks the grip that dry ground would have held.",
        ),
    ),
    Rule(
        id="causal.visibility",
        layer="domain",
        stage="path",
        title="Dusk lowers visibility",
        produces="low_visibility",
        requires=("dusk",),
        variants=(
            "Dusk removes the contrast a walker uses to place the foot.",
            "Low light hides the edge of the path before the step lands.",
        ),
    ),
    Rule(
        id="causal.risk_traction",
        layer="domain",
        stage="answer",
        title="A slippery path is a traction risk",
        produces="risk(path)",
        requires=("slippery(path)",),
    ),
    Rule(
        id="causal.risk_sight",
        layer="domain",
        stage="answer",
        title="Low visibility is a sight risk",
        produces="risk(path)",
        requires=("low_visibility",),
    ),
    Rule(
        id="causal.settled_cover",
        layer="domain",
        stage="answer",
        title="Cover keeps the path from becoming a traction risk",
        produces="settled(no_traction_risk)",
        requires=("covered(path)", "dry(ground)"),
        absent=("slippery(path)",),
    ),
)


class CausalPack:
    name = "causal"

    def active(self, request: Request) -> bool:
        if request.domain == self.name:
            return True
        if request.domain not in (None, "auto"):
            return False
        haystack = " ".join((request.ask, *request.facts))
        return term_hit(haystack, TERMS)

    def exclusions(self) -> tuple[tuple[str, str], ...]:
        return EXCLUSIONS

    def rules(self, request: Request) -> tuple[Rule, ...]:
        return RULES
