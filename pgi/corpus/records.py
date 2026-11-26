"""The link board.

Every record carries a source. Experimental, definitional, and open-problem
records also carry the page or DOI used to write them. A record never emits
a value(...) atom. Measured and defined numbers stay anchors.

Coq is not cited here. Lean names elsewhere in the kernel were checked with
Lean 4.36.0. The Isabelle names for order sit in the math layer.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.corpus.formulas import FORMULAS, Formula
from pgi.corpus.measured import BOUNDS, QUANTITIES, Bound, Quantity

KINDS = frozenset(
    {
        "known_mistake",
        "obstruction",
        "experimental_bound",
        "definitional_anchor",
        "measured_anchor",
        "stored_formula",
        "open_problem",
        "effective_limit",
        "math_primitive",
    }
)

_URL_KINDS = frozenset(
    {
        "known_mistake",
        "obstruction",
        "experimental_bound",
        "definitional_anchor",
        "measured_anchor",
        "stored_formula",
        "open_problem",
        "effective_limit",
    }
)


@dataclass(frozen=True)
class Record:
    id: str
    kind: str
    standing: str
    title: str
    keys: tuple[str, ...]
    phrases: tuple[str, ...]
    statement: tuple[str, ...]
    source: str
    url: str
    forbids: tuple[str, ...]


RECORDS: tuple[Record, ...] = (
    Record(
        id="known.opera_timing",
        kind="known_mistake",
        standing="blocked",
        title="The 2011 OPERA timing anomaly is not a superluminal neutrino",
        keys=("opera", "superluminal"),
        phrases=("faster than light", "faster-than-light", "gran sasso"),
        statement=(
            "In September 2011 the OPERA collaboration reported that CNGS neutrinos arrived earlier than a light-speed flight from CERN to Gran Sasso.",
            "CERN's update of 8 June 2012 says Borexino, ICARUS, LVD, and OPERA all measured a neutrino time of flight consistent with the speed of light.",
            "That update attributes the original OPERA measurement to a faulty element of the experiment's fibre-optic timing system.",
            "The 23 February 2012 CERN note, quoted on the same page, had named two effects still to be tested with a pulsed beam: a GPS time-stamp oscillator, and the optical-fibre connector that brought the external GPS signal to the OPERA master clock.",
            "A flight faster than light is not admitted as a law from this episode.",
        ),
        source="CERN, OPERA experiment reports anomaly in flight time of neutrinos from CERN to Gran Sasso, 23 September 2011, with the updates of 23 February 2012 and 8 June 2012.",
        url="https://home.cern/opera-experiment-reports-anomaly-in-flight-time-of-neutrinos-from-cern-to-gran-sasso/",
        forbids=("law(neutrinos_exceed_c)",),
    ),
    Record(
        id="known.mechanical_ether_required",
        kind="known_mistake",
        standing="blocked",
        title="A mechanical ether is not required for light to propagate",
        keys=("michelson", "morley"),
        phrases=("luminiferous ether", "mechanical ether"),
        statement=(
            "Michelson and Morley, American Journal of Science 34 (1887) 333-345, reported no significant relative motion of the Earth and the luminiferous ether at the sensitivity of that interferometer.",
            "The null result does not by itself delete every ether theory. FitzGerald and Lorentz kept an ether by adding length contraction along the direction of motion.",
            "Michelson and Morley did not themselves abandon the ether because of the paper.",
            "What stays blocked is the claim that a mechanical ether is required. Einstein's 1905 special relativity does not use one.",
        ),
        source="A. A. Michelson and E. W. Morley, On the Relative Motion of the Earth and the Luminiferous Ether, American Journal of Science 34 (1887) 333-345. The nuance above is the account in APS News, November 2007.",
        url="https://www.aps.org/apsnews/2007/11/november-1887-michelson-uminiferous-ether",
        forbids=("law(mechanical_ether_required)",),
    ),
    Record(
        id="obstruction.perturbative_einstein",
        kind="obstruction",
        standing="blocked",
        title="Perturbative Einstein gravity diverges at two loops",
        keys=("goroff", "sagnotti"),
        phrases=("perturbative quantum gravity", "einstein-hilbert"),
        statement=(
            "Goroff and Sagnotti showed that the S-matrix of pure Einstein gravity diverges at two-loop order in four dimensions.",
            "The short report is Physics Letters B 160 (1985) 81-86. The detailed account is Nuclear Physics B 266 (1986) 709-736.",
            "This blocks treating the Einstein-Hilbert action, quantized perturbatively by itself, as an ultraviolet-complete source code.",
            "The calculation does not select a replacement theory.",
        ),
        source="M. H. Goroff and A. Sagnotti, Nuclear Physics B 266 (1986) 709-736, doi:10.1016/0550-3213(86)90193-8; Physics Letters B 160 (1985) 81-86, doi:10.1016/0370-2693(85)91470-4.",
        url="https://doi.org/10.1016/0550-3213(86)90193-8",
        forbids=("law(perturbative_einstein_hilbert_uv_complete)",),
    ),
    Record(
        id="bound.sk_proton",
        kind="experimental_bound",
        standing="bound",
        title="Super-Kamiokande bound on p to e+ pi0 and p to mu+ pi0",
        keys=("superkamiokande",),
        phrases=("proton decay", "su(5)", "su5", "georgi-glashow", "georgi glashow"),
        statement=(
            "Takenaka et al., Phys. Rev. D 102, 112011 (2020), arXiv:2010.16098, searched Super-Kamiokande from April 1996 to May 2018, an exposure of 450 kton-years.",
            "No candidates were found for p to e+ pi0. The partial-lifetime limit is tau/B(p to e+ pi0) greater than 2.4e34 years at 90% confidence.",
            "One candidate remains for p to mu+ pi0 in the conventional fiducial volume, consistent with the atmospheric-neutrino background. The limit is tau/B(p to mu+ pi0) greater than 1.6e34 years at 90% confidence.",
            "A model whose predicted partial lifetime for one of these modes sits below the matching limit is blocked.",
            "No grand-unified lifetime is stored in this record. The bound does not exclude every unified model.",
        ),
        source="A. Takenaka et al. (Super-Kamiokande), Phys. Rev. D 102, 112011 (2020), doi:10.1103/PhysRevD.102.112011, arXiv:2010.16098.",
        url="https://arxiv.org/abs/2010.16098",
        forbids=("law(proton_decay_detected)",),
    ),
    Record(
        id="anchor.c_si",
        kind="definitional_anchor",
        standing="anchor",
        title="The SI speed of light is fixed by the definition of the metre",
        keys=("bipm", "299792458"),
        phrases=("speed of light",),
        statement=(
            "The BIPM defines the metre by taking the fixed numerical value of the speed of light in vacuum c to be 299792458 when expressed in m/s, with the second defined by the caesium frequency.",
            "The page states the exact relation c = 299792458 m/s.",
            "This is a unit definition. It is an anchor. It is not a number derived by this system.",
        ),
        source="BIPM, SI base unit: metre. The 2019 statement of the SI keeps the exact value fixed in 1983.",
        url="https://www.bipm.org/en/si-base-units/metre",
        forbids=("derived(c_si)",),
    ),
    Record(
        id="open.cosmological_constant",
        kind="open_problem",
        standing="open",
        title="The cosmological-constant mismatch is open",
        keys=("weinberg",),
        phrases=("cosmological constant",),
        statement=(
            "Steven Weinberg, Reviews of Modern Physics 61, 1 (1989), is the standard named statement of the cosmological-constant problem.",
            "Vacuum-energy estimates depend on the cutoff. They do not match the observed cosmological constant.",
            "No ratio is stored. A figure such as ten to a large power has to arrive later as its own sourced estimate, with the cutoff named.",
            "The mismatch is open. It is not marked solved.",
        ),
        source="S. Weinberg, The cosmological constant problem, Rev. Mod. Phys. 61, 1 (1989), doi:10.1103/RevModPhys.61.1.",
        url="https://doi.org/10.1103/RevModPhys.61.1",
        forbids=("law(cosmological_constant_solved)",),
    ),
    Record(
        id="known.rayleigh_jeans",
        kind="known_mistake",
        standing="blocked",
        title="Classical equipartition does not give the blackbody spectrum",
        keys=("rayleigh", "jeans"),
        phrases=("ultraviolet catastrophe", "rayleigh-jeans", "rayleigh jeans"),
        statement=(
            "Lord Rayleigh, Philosophical Magazine series 5, volume 49 (1900), pages 539-540, discussed the spectrum of complete radiation from a black body.",
            "J. H. Jeans, Philosophical Magazine series 6, volume 10 (1905), pages 91-98, applied equipartition to a system of matter plus ether.",
            "Jeans, Proceedings of the Royal Society A, volume 76 (1905), pages 545-552, writes that the equipartition law sends the energy into waves of infinitesimal wavelength and cannot be the true law of the radiant energy found in nature.",
            "That divergence is the failure later called the ultraviolet catastrophe. Planck's quantum account is the one that stays finite.",
            "No spectral formula is stored here as a derived theorem.",
        ),
        source="Rayleigh, Phil. Mag. 49 (1900) 539-540, doi:10.1080/14786440009463878. Jeans, Phil. Mag. 10 (1905) 91-98, doi:10.1080/14786440509463348. Jeans, Proc. R. Soc. Lond. A 76 (1905) 545-552, doi:10.1098/rspa.1905.0060.",
        url="https://doi.org/10.1098/rspa.1905.0060",
        forbids=("law(classical_equipartition_blackbody)",),
    ),
    Record(
        id="primitive.integer_ring",
        kind="math_primitive",
        standing="primitive",
        title="The integer ring is a checked mathematical primitive",
        keys=(),
        phrases=("integer ring",),
        statement=(
            "Equality, congruence, and the integer ring laws in pgi/math are checked theorems.",
            "The Lean 4.36 names were checked on this machine. The matching Isabelle2025-2 HOL names were read from Groups.thy and Rings.thy.",
            "This primitive is arithmetic. It is not a physical law, and it does not fix a measured constant.",
        ),
        source="pgi/math, Lean 4.36.0, Isabelle2025-2 src/HOL/Groups.thy and Rings.thy.",
        url="",
        forbids=(),
    ),
    Record(
        id="primitive.rationals",
        kind="math_primitive",
        standing="primitive",
        title="The rationals are exact reduced fractions",
        keys=(),
        phrases=("rational number", "rationals"),
        statement=(
            "A rational is a reduced fraction with a positive denominator. The numerator carries the sign, and the absolute numerator is coprime to the denominator.",
            "Closed arithmetic uses addition, subtraction, multiplication, negation, and division, then reduces. Equality is cross multiplication. Comparison of positive-denominator fractions is the same cross multiplication.",
            "Division by zero stays open.",
            "This primitive is arithmetic. It is not a physical law, and it does not fix a measured constant.",
        ),
        source="pgi/math/rational.py, Lean 4.36.0 Rat.normalize, Isabelle2025-2 src/HOL/Rat.thy.",
        url="",
        forbids=("law(division_by_zero_is_zero)",),
    ),
    Record(
        id="primitive.continuum",
        kind="math_primitive",
        standing="primitive",
        title="The continuum is a Cauchy quotient of the rationals",
        keys=(),
        phrases=("constructed continuum", "cauchy sequence", "real number", "nested radical"),
        statement=(
            "A real is an equivalence class of Cauchy sequences of rationals, the construction in Isabelle Real.thy.",
            "Two sequences are the same real when both are Cauchy and their difference vanishes. A constant sequence is a rational.",
            "A positive rational has a bisection sequence whose square differs from the radicand by a vanishing sequence. Square factors move into the coefficient.",
            "A negative radicand stays open. Division by zero stays open. Nested radicals of one square-free integer are towers base^(odd/2^k), and sqrt(3 + 2*sqrt(2)) is 1 + sqrt(2) by real_sqrt_unique. sqrt(2 + sqrt(2)) is the positive nested radical sqrt(2 + sqrt(2)) by real_sqrt_unique, and its square is 2 + sqrt(2). sqrt(sqrt(2) + sqrt(3)) is 1/2 * sqrt(-2 + 2*sqrt(3)) + 1/2 * sqrt(2 + 2*sqrt(3)) by real_sqrt_unique, and its square is sqrt(2) + sqrt(3). A sum of two different square roots stays that sum. sqrt(sqrt(2) + sqrt(5)) is the positive nested radical sqrt(sqrt(2) + sqrt(5)) by real_sqrt_unique, and its square is sqrt(2) + sqrt(5). sqrt(sqrt(2 + sqrt(2))) is the positive nested radical sqrt(sqrt(2 + sqrt(2))) by real_sqrt_unique, and its square is sqrt(2 + sqrt(2)). sqrt(sqrt(sqrt(2) + sqrt(5))) is the positive nested radical sqrt(sqrt(sqrt(2) + sqrt(5))) by real_sqrt_unique, and its square is sqrt(sqrt(2) + sqrt(5)). Its inverse is 1/3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))). sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) is the positive nested radical sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) by real_sqrt_unique, and its square is sqrt(sqrt(sqrt(2) + sqrt(5))). Its inverse is 1/3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))). sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) is the positive nested radical sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) by real_sqrt_unique, and its square is sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))). Its inverse is 1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))). sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) is the positive nested radical sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) by real_sqrt_unique, and its square is sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))). Its inverse is 1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))))). sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) is the positive nested radical sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) by real_sqrt_unique, and its square is sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))). Its inverse is 1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))))). sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))) is that nested radical by real_sqrt_unique, and its square is sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))). Every further finite square root of this radical is the same rule, one square root deeper. Every further finite square root of one positive binomial nest is the same nested radical, one square root deeper. sqrt(sqrt(sqrt(2 + sqrt(2)))) is that nested radical by real_sqrt_unique, and its square is sqrt(sqrt(2 + sqrt(2))). The inverse of sqrt(sqrt(2) + sqrt(3)) is -1/2 * sqrt(-2 + 2 * sqrt(3)) + 1/2 * sqrt(2 + 2 * sqrt(3)). The inverse of sqrt(sqrt(sqrt(2 + sqrt(2)))) stays outside. A product of radicals at different levels is one integer to the power 1/2^k. sqrt(2)*sqrt(sqrt(3)) is sqrt(sqrt(12)). A radicand the kernel cannot see as nonnegative stays open. Division by another element of this span multiplies by the inverse, and that inverse times the divisor is 1. sqrt(sqrt(2))/sqrt(sqrt(3)) is 1/3 * sqrt(sqrt(54)). A divisor the kernel cannot see as nonzero stays open.",
            "The least-upper-bound statement in that file quantifies over an arbitrary set of reals. A finite enumeration carries that statement by its maximum. An arbitrary set is outside this construction.",
            "This primitive is arithmetic. It is not a physical law, and it does not fix a measured constant.",
        ),
        source="pgi/math/real.py, Isabelle2025-2 src/HOL/Real.thy.",
        url="",
        forbids=("law(sqrt_two_is_rational)",),
    ),
    Record(
        id="primitive.finite_set",
        kind="math_primitive",
        standing="primitive",
        title="A finite set is an enumeration of reals",
        keys=(),
        phrases=("finite set", "set enumeration"),
        statement=(
            "A finite set in this kernel is built from the empty set by inserting reals the kernel can already check.",
            "Membership, union, intersection, and equality compare those elements. The same elements in another order are the same set. A repeated element is one member.",
            "Isabelle complete_real says a nonempty set of reals that is bounded above has a least upper bound. For a finite enumeration the maximum member is that bound, by Max_in, Max_ge, and cSup_eq_maximum.",
            "The empty set is outside that statement. An arbitrary set stays outside this rule.",
            "This primitive is arithmetic. It is not a physical law, and it does not fix a measured constant.",
        ),
        source="pgi/math/set.py, Isabelle2025-2 src/HOL/Set.thy, Finite_Set.thy, Lattices_Big.thy, Conditionally_Complete_Lattices.thy, Real.thy.",
        url="",
        forbids=("law(empty_set_has_a_least_upper_bound)",),
    ),
    Record(
        id="primitive.quantifier",
        kind="math_primitive",
        standing="primitive",
        title="A quantifier ranges over a finite enumeration",
        keys=(),
        phrases=("quantifier", "bounded quantifier"),
        statement=(
            "A bounded quantifier in this kernel is Isabelle Ball or Bex over a finite enumeration of checked reals.",
            "The universal holds when the predicate holds at every member. The existential holds when a member is a witness. The empty universal holds. The empty existential fails.",
            "An unbounded quantifier stays open except where a uniform reason applies: a variable is related to itself, or a closed term is a witness of equality with itself.",
            "Isabelle complete_real says a nonempty set of reals that is bounded above has a least upper bound. For a finite enumeration this kernel exhibits the maximum and checks the bounded statements. The supremum of an atMost ray is its bound. The supremum of a lessThan ray is its bound, by the Archimedean bisection. The supremum of a two-sided interval is its upper bound.",
            "A finite check does not prove an unbounded quantifier. A comprehension is a separate primitive. An order ray is a separate primitive.",
            "This primitive is arithmetic. It is not a physical law, and it does not fix a measured constant.",
        ),
        source="pgi/math/quant.py, Isabelle2025-2 src/HOL/HOL.thy, Set.thy, Lattices_Big.thy, Real.thy.",
        url="",
        forbids=("law(finite_checks_prove_an_unbounded_quantifier)",),
    ),
    Record(
        id="primitive.comprehension",
        kind="math_primitive",
        standing="primitive",
        title="A comprehension separates a finite enumeration",
        keys=(),
        phrases=("set comprehension", "comprehension"),
        statement=(
            "A set comprehension in this kernel is Isabelle Collect.",
            "Separation keeps the members of a finite enumeration that satisfy <= or =. Collect_subset and finite_subset make that result a finite subset. The empty domain is empty, and that body is not evaluated.",
            "The equality shapes {x. x = a} and {x. a = x} are the singleton of a closed term, by singleton_conv and singleton_conv2.",
            "An unbounded predicate over the reals is not a finite enumeration. An order ray is the arbitrary-set primitive.",
            "This primitive is arithmetic. It is not a physical law, and it does not fix a measured constant.",
        ),
        source="pgi/math/collect.py, Isabelle2025-2 src/HOL/Set.thy and Finite_Set.thy.",
        url="",
        forbids=("law(every_real_predicate_is_a_finite_set)",),
    ),
    Record(
        id="primitive.arbitrary_set",
        kind="math_primitive",
        standing="primitive",
        title="An arbitrary set is an order ray, a two-sided interval, or the set of every real",
        keys=(),
        phrases=("arbitrary set", "order ray", "boolean connective"),
        statement=(
            "An arbitrary set in this kernel is an order ray, a two-sided interval, or the set of every real.",
            "{x. x <= a} is atMost a. {x. a <= x} is atLeast a. {x. x = x} and {x. x <= x} are UNIV.",
            "atMost_subset_iff and atLeast_subset_iff compare the bounds. infinite_Iic and infinite_Ici say a ray is not a finite enumeration.",
            "cSup_atMost says the supremum of an atMost ray is its bound. The Archimedean bisection constructs the supremum of a lessThan ray, and that supremum is the bound, which is not a member. A proper overlap of a lower ray and an upper ray is the two-sided interval, and its supremum is the upper bound.",
            "Collect_conj_eq makes a conjunction of two comparisons the intersection of those comprehensions. Collect_neg_eq and the complement lemmas send an order ray to the opposite ray. Collect_disj_eq unions two closed equalities.",
            "This primitive is arithmetic. It is not a physical law, and it does not fix a measured constant.",
        ),
        source="pgi/math/arbitrary.py, Isabelle2025-2 src/HOL/Set_Interval.thy, Conditionally_Complete_Lattices.thy, Set.thy, Orderings.thy, Rings.thy, Fields.thy, Finite_Set.thy, Archimedean_Field.thy, Real.thy.",
        url="",
        forbids=("law(an_order_ray_is_a_finite_enumeration)",),
    ),
)


def _quantity_statement(item: Quantity) -> tuple[str, ...]:
    unit = f" {item.unit}" if item.unit else ""
    lines = [f"{item.edition}: {item.name}, {item.symbol} = {item.value_text}{unit}."]
    if item.truncated:
        lines.append(
            "The value is exact. The source prints only its leading digits, so the exact value lies between the printed digits "
            "and one more unit in the last printed place. It is a definitional anchor. It is not a number derived by this system."
        )
    elif item.exact:
        lines.append("The value is exact. It is a definitional anchor. It is not a number derived by this system.")
    elif item.uncertainty_kind == "no uncertainty printed":
        lines.append("The source prints no uncertainty for this value, so none is stored.")
        lines.append("The value is a measured anchor. It is data, not a number derived by this system.")
    elif item.relative_uncertainty is not None:
        if item.uncertainty_kind == "relative standard uncertainty":
            lines.append(f"The source gives a relative standard uncertainty of {item.uncertainty_text}; it is stored as printed and not converted.")
        else:
            lines.append(f"The source gives a maximum relative uncertainty of about {item.uncertainty_text} ppm; it is stored as printed and not converted.")
        lines.append("The value is a measured anchor. It is data, not a number derived by this system.")
    elif item.systematic_text:
        lower = f" -{item.systematic_lower_text}" if item.systematic_lower_text else ""
        plus = "+" if item.systematic_lower_text else "+-"
        stat = f"+{item.uncertainty_text} -{item.lower_text}" if item.lower_text else item.uncertainty_text
        lines.append(
            f"The statistical uncertainty is {stat}{unit} and the systematic uncertainty is "
            f"{plus}{item.systematic_text}{lower}{unit}, printed separately by the source."
        )
        lines.append("The value is a measured anchor. It is data, not a number derived by this system.")
    elif item.lower_text:
        lines.append(
            f"The {item.uncertainty_kind} is +{item.uncertainty_text} -{item.lower_text}{unit}, as the source quotes it."
        )
        lines.append("The value is a measured anchor. It is data, not a number derived by this system.")
    else:
        lines.append(f"The {item.uncertainty_kind} is {item.uncertainty_text}{unit}, as the source quotes it.")
        lines.append("The value is a measured anchor. It is data, not a number derived by this system.")
    lines.extend(item.notes)
    lines.append(f"Retrieved {item.retrieved} from {item.retrieved_from}.")
    return tuple(lines)


def _quantity_record(item: Quantity) -> Record:
    unit = f" {item.unit}" if item.unit else ""
    return Record(
        id=item.id,
        kind="definitional_anchor" if item.exact else "measured_anchor",
        standing="anchor",
        title=f"{item.edition}: {item.name} {item.value_text}{unit}",
        keys=item.keys,
        phrases=item.phrases,
        statement=_quantity_statement(item),
        source=f"{item.source} Edition: {item.edition}.",
        url=item.url,
        forbids=((f"derived({item.id})",) if item.exact else ()) + item.forbids,
    )


def _bound_record(item: Bound) -> Record:
    unit = f" {item.unit}" if item.unit else ""
    return Record(
        id=item.id,
        kind="experimental_bound",
        standing="bound",
        title=f"{item.edition}: {item.lower_text} <= {item.symbol}" + (f" <= {item.upper_text}" if item.upper_text else ""),
        keys=item.keys,
        phrases=item.phrases,
        statement=(
            (f"{item.edition}: the {item.name}, {item.symbol}, lies between {item.lower_text} and {item.upper_text}{unit}."
             if item.upper_text else f"{item.edition}: the {item.name}, {item.symbol}, is at least {item.lower_text}{unit}."),
            *item.conditions,
            "A model that sits outside this interval under the same assumptions is blocked. No central value is stored.",
            f"Retrieved {item.retrieved} from {item.retrieved_from}.",
        ),
        source=f"{item.source} Edition: {item.edition}.",
        url=item.url,
        forbids=item.forbids,
    )


def _formula_record(item: Formula) -> Record:
    return Record(
        id=item.id,
        kind="stored_formula",
        standing=item.standing,
        title=f"{item.name} ({item.standing})",
        keys=item.keys,
        phrases=item.phrases,
        statement=(
            f"{item.edition}: {item.text}.",
            *(f"where {variable}" for variable in item.variables),
            *item.notes,
            f"Retrieved {item.retrieved} from {item.retrieved_from}.",
        ),
        source=f"{item.source} Edition: {item.edition}.",
        url=item.url,
        forbids=item.forbids,
    )


RECORDS = (
    RECORDS
    + tuple(_quantity_record(item) for item in QUANTITIES if item.record)
    + tuple(_bound_record(item) for item in BOUNDS)
    + tuple(_formula_record(item) for item in FORMULAS)
)


def audit_records(records: tuple[Record, ...] = RECORDS) -> None:
    seen: set[str] = set()
    for record in records:
        if not record.id or record.id in seen:
            raise ValueError(f"bad record id {record.id}")
        seen.add(record.id)
        if record.kind not in KINDS:
            raise ValueError(f"{record.id} has kind {record.kind}")
        if not record.standing or not record.title or not record.statement:
            raise ValueError(f"{record.id} is missing standing, title, or statement")
        if not record.source.strip():
            raise ValueError(f"{record.id} needs a source")
        if record.kind in _URL_KINDS and not record.url.startswith("https://"):
            raise ValueError(f"{record.id} needs an https source url")
        if record.kind == "math_primitive" and record.url and not record.url.startswith("https://"):
            raise ValueError(f"{record.id} has a bad url")
        blob = " ".join(record.statement).lower()
        if "value(" in blob:
            raise ValueError(f"{record.id} must not emit a value atom")
        for atom in record.forbids:
            if atom.startswith("value(") or not atom.endswith(")"):
                raise ValueError(f"{record.id} forbids {atom}")


audit_records()
