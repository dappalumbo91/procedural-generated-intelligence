from __future__ import annotations

import unittest

from pgi.corpus.records import RECORDS, audit_records
from pgi.engine import unfold
from pgi.math.kernel import KernelError
from pgi.math.order import add_le_add_left, le_antisymm, le_refl, le_trans, numeral_le, numeral_not_le, show
from pgi.math.syntax import IntLit, Var
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class OrderTests(unittest.TestCase):
    def test_numerals_and_reflexivity(self) -> None:
        held = run(Request(ask="prove 2 <= 5", seed=1))
        self.assertEqual(held.claims[0].atom, "le(2,5)")
        self.assertEqual(held.open_gaps, ())
        self.assertIn("numeral_le: 2 <= 5", held.text(lod=2))
        self.assertNotIn("value(", held.text(lod=2))

        refused = run(Request(ask="prove 5 <= 2", seed=1))
        self.assertEqual(refused.claims[0].atom, "not_le(5,2)")
        self.assertIn("Int.not_le", refused.text(lod=2))
        self.assertEqual(refused.open_gaps, ())

        reflected = run(Request(ask="prove x <= x", seed=1))
        self.assertEqual(reflected.claims[0].atom, "le(x,x)")
        self.assertIn("Int.le_refl", reflected.text(lod=2))

        free = run(Request(ask="prove x <= y", seed=1))
        self.assertIn("is not a theorem", free.text(lod=1))
        self.assertNotIn("le(x,y)", [claim.atom for claim in free.claims])

        compound = run(Request(ask="prove 1 + 1 <= 3", seed=1))
        self.assertIn("1 + 1 <= 3", compound.text(lod=1))
        self.assertIn("Int.add: 1 + 1 = 2", compound.text(lod=2))
        self.assertIn("numeral_le: 2 <= 3", compound.text(lod=2))
        self.assertEqual(compound.open_gaps, ())
        rejected = run(Request(ask="prove 3 <= 1 + 1", seed=1))
        self.assertIn("Int.not_le", rejected.text(lod=2))
        self.assertEqual(rejected.open_gaps, ())
        cancelled = run(Request(ask="prove (x - x) + 1 <= 1", seed=1))
        self.assertIn("Int.add_right_neg", cancelled.text(lod=2))
        self.assertEqual(cancelled.open_gaps, ())
        shifted = run(Request(ask="prove x + 0 <= 0 + x", seed=1))
        self.assertIn("Int.add_zero", shifted.text(lod=2))
        self.assertIn("Int.zero_add", shifted.text(lod=2))
        self.assertEqual(shifted.open_gaps, ())
        anchored = run(Request(ask="prove length <= 5", facts=("length=4@meter stick",), seed=1))
        self.assertIn("observable.anchor", anchored.text(lod=2))
        self.assertIn("length <= 5", anchored.text(lod=1))
        self.assertEqual(anchored.open_gaps, ())
        uneven = run(Request(ask="prove 8 / 3 <= 4", seed=1))
        self.assertEqual(uneven.claims[0].atom, "le(8 / 3,4)")
        self.assertIn("le_rat", uneven.text(lod=2))
        self.assertNotIn("not an exact integer", uneven.text(lod=2))
        self.assertEqual(uneven.open_gaps, ())

    def test_forged_comparisons_and_the_algebra(self) -> None:
        with self.assertRaises(KernelError):
            numeral_le(5, 2)
        with self.assertRaises(KernelError):
            numeral_not_le(2, 5)
        chained = le_trans(numeral_le(1, 2), numeral_le(2, 4))
        self.assertEqual(show(chained.formula), "1 <= 4")
        with self.assertRaises(KernelError):
            le_trans(numeral_le(1, 2), numeral_le(3, 4))
        shifted = add_le_add_left(numeral_le(1, 2), IntLit(10))
        self.assertEqual(show(shifted.formula), "10 + 1 <= 10 + 2")
        same = le_antisymm(le_refl(Var("x")), le_refl(Var("x")))
        self.assertEqual(show(same.formula), "x = x")
        self.assertEqual(same.rule, "Int.le_antisymm")


class LinkBoardTests(unittest.TestCase):
    def test_records_are_sourced_and_do_not_carry_values(self) -> None:
        audit_records()
        ids = [record.id for record in RECORDS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("known.opera_timing", ids)
        self.assertIn("anchor.c_si", ids)
        for record in RECORDS:
            self.assertNotIn("value(", " ".join(record.statement))

    def test_opera_is_linked_and_a_reasserted_law_is_contested(self) -> None:
        session = run(Request(ask="what happened with the opera neutrinos", seed=1))
        self.assertIn("record(known.opera_timing)", [claim.atom for claim in session.claims])
        self.assertIn("Linked records are on the board. None of them is a settled answer.", session.open_gaps)
        detail = session.text(lod=2)
        self.assertIn("https://home.cern/opera-experiment-reports-anomaly", detail)
        self.assertIn("fibre-optic timing system", detail)
        self.assertNotIn("value(", detail)

        contested = run(
            Request(
                ask="what happened with the opera neutrinos",
                facts=("law(neutrinos_exceed_c)",),
                seed=1,
            )
        )
        self.assertIn("blocked(known.opera_timing) contradicts law(neutrinos_exceed_c)", contested.text(lod=1))
        self.assertIn("record(known.opera_timing)", [claim.atom for claim in contested.claims])
        self.assertIn("Contested claims blocked a settled answer.", contested.open_gaps)
        self.assertIn("law(neutrinos_exceed_c)", contested.retracted)

    def test_speed_of_light_stays_a_definition(self) -> None:
        session = run(Request(ask="what is the speed of light", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(anchor.c_si)", text)
        self.assertIn("299792458", text)
        self.assertNotIn("value(299792458)", text)
        self.assertIn("Linked records are on the board", " ".join(session.open_gaps))
        contested = run(Request(ask="what is the speed of light", facts=("derived(c_si)",), seed=1))
        self.assertIn("derived(c_si)", contested.retracted)

    def test_proton_bound_does_not_invent_a_lifetime(self) -> None:
        session = run(Request(ask="what is the proton decay bound", seed=1))
        text = session.text(lod=2)
        self.assertIn("2.4e34", text)
        self.assertIn("does not exclude every unified model", text)
        self.assertNotIn("value(", text)

    def test_rayleigh_jeans_is_a_blocked_classical_law(self) -> None:
        session = run(Request(ask="what is the ultraviolet catastrophe", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(known.rayleigh_jeans)", text)
        self.assertIn("10.1098/rspa.1905.0060", text)
        self.assertIn("infinitesimal wavelength", text)
        self.assertIn("No spectral formula is stored", text)
        self.assertNotIn("value(", text)
        contested = run(
            Request(
                ask="what is the ultraviolet catastrophe",
                facts=("law(classical_equipartition_blackbody)",),
                seed=1,
            )
        )
        self.assertIn("law(classical_equipartition_blackbody)", contested.retracted)

    def test_rationals_are_linked_and_division_by_zero_stays_blocked(self) -> None:
        session = run(Request(ask="what is a rational number", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(primitive.rationals)", text)
        self.assertIn("Division by zero stays open.", text)
        self.assertNotIn("value(", text)
        self.assertIn("Linked records are on the board", " ".join(session.open_gaps))
        contested = run(
            Request(
                ask="what is a rational number",
                facts=("law(division_by_zero_is_zero)",),
                seed=1,
            )
        )
        self.assertIn(
            "blocked(primitive.rationals) contradicts law(division_by_zero_is_zero)",
            contested.text(lod=1),
        )
        self.assertIn("law(division_by_zero_is_zero)", contested.retracted)
        self.assertIn("record(primitive.rationals)", [claim.atom for claim in contested.claims])

    def test_continuum_is_linked_and_a_rational_square_root_is_blocked(self) -> None:
        session = run(Request(ask="what is a real number", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(primitive.continuum)", text)
        self.assertIn("Cauchy sequences of rationals", text)
        self.assertNotIn("value(", text)
        self.assertIn("Linked records are on the board", " ".join(session.open_gaps))
        contested = run(
            Request(
                ask="what is a real number",
                facts=("law(sqrt_two_is_rational)",),
                seed=1,
            )
        )
        self.assertIn(
            "blocked(primitive.continuum) contradicts law(sqrt_two_is_rational)",
            contested.text(lod=1),
        )
        self.assertIn("law(sqrt_two_is_rational)", contested.retracted)
        self.assertIn("record(primitive.continuum)", [claim.atom for claim in contested.claims])

    def test_finite_set_is_linked_and_an_empty_supremum_is_blocked(self) -> None:
        session = run(Request(ask="what is a finite set", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(primitive.finite_set)", text)
        self.assertIn("maximum member is that bound", text)
        self.assertNotIn("value(", text)
        self.assertIn("Linked records are on the board", " ".join(session.open_gaps))
        contested = run(
            Request(
                ask="what is a finite set",
                facts=("law(empty_set_has_a_least_upper_bound)",),
                seed=1,
            )
        )
        self.assertIn(
            "blocked(primitive.finite_set) contradicts law(empty_set_has_a_least_upper_bound)",
            contested.text(lod=1),
        )
        self.assertIn("law(empty_set_has_a_least_upper_bound)", contested.retracted)
        self.assertIn("record(primitive.finite_set)", [claim.atom for claim in contested.claims])

    def test_quantifier_is_linked_and_a_finite_check_is_blocked(self) -> None:
        session = run(Request(ask="what is a quantifier", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(primitive.quantifier)", text)
        self.assertIn("exhibits the maximum", text)
        self.assertNotIn("value(", text)
        self.assertIn("Linked records are on the board", " ".join(session.open_gaps))
        contested = run(
            Request(
                ask="what is a quantifier",
                facts=("law(finite_checks_prove_an_unbounded_quantifier)",),
                seed=1,
            )
        )
        self.assertIn(
            "blocked(primitive.quantifier) contradicts law(finite_checks_prove_an_unbounded_quantifier)",
            contested.text(lod=1),
        )
        self.assertIn("law(finite_checks_prove_an_unbounded_quantifier)", contested.retracted)
        self.assertIn("record(primitive.quantifier)", [claim.atom for claim in contested.claims])

    def test_comprehension_is_linked_and_an_unbounded_predicate_is_blocked(self) -> None:
        session = run(Request(ask="what is a comprehension", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(primitive.comprehension)", text)
        self.assertIn("singleton_conv", text)
        self.assertNotIn("value(", text)
        self.assertIn("Linked records are on the board", " ".join(session.open_gaps))
        contested = run(
            Request(
                ask="what is a set comprehension",
                facts=("law(every_real_predicate_is_a_finite_set)",),
                seed=1,
            )
        )
        self.assertIn(
            "blocked(primitive.comprehension) contradicts law(every_real_predicate_is_a_finite_set)",
            contested.text(lod=1),
        )
        self.assertIn("law(every_real_predicate_is_a_finite_set)", contested.retracted)
        self.assertIn("record(primitive.comprehension)", [claim.atom for claim in contested.claims])

    def test_arbitrary_set_is_linked_and_a_finite_ray_is_blocked(self) -> None:
        session = run(Request(ask="what is an arbitrary set", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(primitive.arbitrary_set)", text)
        self.assertIn("atMost", text)
        self.assertNotIn("value(", text)
        self.assertNotIn("record(primitive.finite_set)", text)
        self.assertNotIn("record(primitive.continuum)", text)
        self.assertNotIn("record(primitive.comprehension)", text)
        self.assertIn("Linked records are on the board", " ".join(session.open_gaps))
        contested = run(
            Request(
                ask="what is an order ray",
                facts=("law(an_order_ray_is_a_finite_enumeration)",),
                seed=1,
            )
        )
        self.assertIn(
            "blocked(primitive.arbitrary_set) contradicts law(an_order_ray_is_a_finite_enumeration)",
            contested.text(lod=1),
        )
        self.assertIn("law(an_order_ray_is_a_finite_enumeration)", contested.retracted)
        self.assertIn("record(primitive.arbitrary_set)", [claim.atom for claim in contested.claims])
        finite = run(Request(ask="what is a finite set", seed=1))
        self.assertIn("record(primitive.finite_set)", finite.text(lod=2))
        self.assertNotIn("record(primitive.arbitrary_set)", finite.text(lod=2))

    def test_unrelated_asks_stay_on_their_own_packs(self) -> None:
        story = run(Request(ask="tell me a story about a dragon", seed=1))
        self.assertIn("No answer rule fired from the given facts.", story.open_gaps)
        self.assertEqual(story.claims, ())
        causal = run(Request(ask="why is the path risky?", facts=("rain", "above_freezing"), seed=1))
        self.assertNotIn("record(", causal.text(lod=1))
        arithmetic = run(
            Request(ask="what happened with the opera neutrinos", domain="arithmetic", seed=1)
        )
        self.assertNotIn("record(", arithmetic.text(lod=1))
        self.assertIn("No answer rule fired from the given facts.", arithmetic.open_gaps)
