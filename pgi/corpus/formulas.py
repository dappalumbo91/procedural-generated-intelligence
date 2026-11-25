"""Stored formulas.

A stored formula is a sourced expression, copied in the notation of its
source. It is not a theorem of this kernel and it is not derived here. A
formula that failed against observation keeps that standing, with the regime
where it failed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from pgi.corpus.measured import RETRIEVED

STANDINGS = frozenset({"stored", "failed"})


@dataclass(frozen=True)
class Formula:
    id: str
    name: str
    text: str
    variables: tuple[str, ...]
    standing: str
    source: str
    edition: str
    url: str
    retrieved_from: str
    retrieved: str
    keys: tuple[str, ...]
    phrases: tuple[str, ...]
    notes: tuple[str, ...]
    forbids: tuple[str, ...]


PLANCK_1901_SOURCE = (
    "M. Planck, Ueber das Gesetz der Energieverteilung im Normalspectrum, Annalen der Physik 309 (3), 553-563 (1901), "
    "doi:10.1002/andp.19013090310. Equation (8) and equation (12) are on page 560 and page 561."
)
PLANCK_1901_EDITION = "Annalen der Physik, 4. Folge, Band 4 (1901)"
_PLANCK_VARIABLES = (
    "u: spatial energy density of the radiation per unit frequency interval (Planck's fraktur u)",
    "nu: frequency",
    "theta: absolute temperature (Planck's vartheta)",
    "h, k: the universal constants Planck introduces in this paper",
    "c: speed of propagation",
)

FORMULAS: tuple[Formula, ...] = (
    Formula(
        id="formula.planck_spectrum",
        name="Planck's energy distribution law for black-body radiation",
        text="u = (8 pi h nu^3 / c^3) * 1 / (exp(h nu / (k theta)) - 1)",
        variables=_PLANCK_VARIABLES,
        standing="stored",
        source=PLANCK_1901_SOURCE,
        edition=PLANCK_1901_EDITION,
        url="https://doi.org/10.1002/andp.19013090310",
        retrieved_from="https://de.wikisource.org/wiki/Seite:Gesetz_der_Energieverteilung_im_Normalspectrum.pdf/9",
        retrieved=RETRIEVED,
        keys=("blackbody",),
        phrases=("planck's law", "planck law", "planck spectrum", "black-body spectrum", "blackbody spectrum", "black body spectrum"),
        notes=(
            "This is Planck's equation (12), in his notation. It follows in the paper from the resonator energy U = h nu / (exp(h nu / (k theta)) - 1), equation (11), and u = 8 pi nu^2 U / c^3, equation (8).",
            "The formula is stored. It is not derived by this system, and the kernel does not hold the analysis needed to derive it.",
            "The page was read from the proofread Wikisource transcription of the journal pages, because the Wiley page is behind a login.",
        ),
        forbids=("derived(planck_spectrum)",),
    ),
    Formula(
        id="formula.rayleigh_jeans",
        name="Rayleigh-Jeans law: classical equipartition in Planck's relation (8)",
        text="u = 8 pi nu^2 k theta / c^3",
        variables=_PLANCK_VARIABLES,
        standing="failed",
        source=PLANCK_1901_SOURCE
        + " The equipartition failure is recorded on known.rayleigh_jeans: Rayleigh, Phil. Mag. 49 (1900) 539-540; Jeans, Phil. Mag. 10 (1905) 91-98; Jeans, Proc. R. Soc. Lond. A 76 (1905) 545-552.",
        edition=PLANCK_1901_EDITION,
        url="https://doi.org/10.1002/andp.19013090310",
        retrieved_from="https://de.wikisource.org/wiki/Seite:Gesetz_der_Energieverteilung_im_Normalspectrum.pdf/8",
        retrieved=RETRIEVED,
        keys=("rayleigh", "jeans"),
        phrases=("rayleigh-jeans law", "rayleigh jeans law", "ultraviolet catastrophe"),
        notes=(
            "The expression is Planck's equation (8), u = 8 pi nu^2 U / c^3, with the classical equipartition energy U = k theta for each resonator.",
            "Rayleigh's and Jeans' own pages were not reachable without a login, so their notation is not copied here.",
            "Standing: failed at high frequency. The energy density it assigns grows as nu^2 without bound, so the energy summed over all frequencies diverges. That is the failure later called the ultraviolet catastrophe.",
            "A failed formula stays failed. It is not promoted to a law in any regime by this record.",
        ),
        forbids=("law(rayleigh_jeans_at_high_frequency)",),
    ),
)


def formula(id: str) -> Formula:
    for item in FORMULAS:
        if item.id == id:
            return item
    raise KeyError(id)


def planck_u(nu: float, theta: float, h: Fraction, k: Fraction, c: Fraction) -> float:
    """Evaluate the stored text of formula.planck_spectrum."""
    x = float(h) * nu / (float(k) * theta)
    return 8 * math.pi * float(h) * nu**3 / float(c) ** 3 / math.expm1(x)


def rayleigh_jeans_u(nu: float, theta: float, k: Fraction, c: Fraction) -> float:
    """Evaluate the stored text of formula.rayleigh_jeans."""
    return 8 * math.pi * nu**2 * float(k) * theta / float(c) ** 3


def audit_formulas(items: tuple[Formula, ...] = FORMULAS) -> None:
    seen: set[str] = set()
    for item in items:
        if not item.id or item.id in seen:
            raise ValueError(f"bad formula id {item.id}")
        seen.add(item.id)
        if item.standing not in STANDINGS:
            raise ValueError(f"{item.id} has standing {item.standing}")
        if not item.source.strip() or not item.edition.strip() or not item.text.strip():
            raise ValueError(f"{item.id} needs a source, an edition, and its text")
        if not item.url.startswith("https://") or not item.retrieved_from.startswith("https://"):
            raise ValueError(f"{item.id} needs https urls")
        if item.standing == "failed" and not any(atom.startswith("law(") for atom in item.forbids):
            raise ValueError(f"{item.id} is failed and must block its law")


audit_formulas()
