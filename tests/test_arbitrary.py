from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.arbitrary import (
    BisectTheorem,
    ConnectiveTheorem,
    IntervalSupTheorem,
    IntervalTheorem,
    RayEqTheorem,
    RayMeetTheorem,
    RayQuantTheorem,
    RaySubsetTheorem,
    RaySupTheorem,
    RayTheorem,
)
from pgi.math.collect import CollectForm
from pgi.math.kernel import KernelError
from pgi.math.quant import Pred
from pgi.math.rational import Ratio
from pgi.math.real import RealForm, real_of_rat
from pgi.math.syntax import App, IntLit, Var
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


def _atoms(session, prefix: str) -> tuple[str, ...]:
    return tuple(claim.atom for claim in session.claims if claim.atom.startswith(prefix))


class ArbitrarySetTests(unittest.TestCase):
    def test_rays_and_the_universe_are_sets(self) -> None:
        down = run(Request(ask="what is {x. x <= 2}", seed=1))
        self.assertEqual(down.claims[0].atom, "atMost(2)")
        self.assertIn("atMost(2) is the set of reals at most this bound", down.text(lod=1))
        self.assertIn("atMost_def", down.text(lod=2))
        self.assertIn("infinite_Iic", down.text(lod=2))
        self.assertNotIn("atMost(2)", down.text(lod=0))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in down.claims))
        self.assertFalse(any(claim.atom.startswith("set(") for claim in down.claims))
        self.assertEqual(down.open_gaps, ())

        reduced = run(Request(ask="what is {x. x <= sqrt(4)}", seed=1))
        self.assertEqual(reduced.claims[0].atom, "atMost(2)")
        self.assertIn("{x. x <= sqrt(4)}", reduced.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in reduced.claims))
        self.assertEqual(reduced.open_gaps, ())

        root = run(Request(ask="what is {x. sqrt(2) <= x}", seed=1))
        self.assertEqual(root.claims[0].atom, "atLeast(sqrt(2))")
        self.assertIn("atLeast_def", root.text(lod=2))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in root.claims))
        self.assertEqual(root.open_gaps, ())

        same = run(Request(ask="what is {x. x = x}", seed=1))
        self.assertEqual(same.claims[0].atom, "univ")
        self.assertIn("univ is the set of every real", same.text(lod=1))
        self.assertIn("UNIV_def", same.text(lod=2))
        self.assertEqual(same.open_gaps, ())

        order = run(Request(ask="what is {x. x <= x}", seed=1))
        self.assertEqual(order.claims[0].atom, "univ")
        self.assertEqual(_atoms(order, "set("), ())
        self.assertEqual(order.open_gaps, ())

        divided = run(Request(ask="what is {x. x <= 1 / 0}", seed=1))
        self.assertIn("division by zero", divided.text(lod=1))
        self.assertEqual(_atoms(divided, "atMost("), ())

        nested = run(Request(ask="what is {x. x <= sqrt(sqrt(2))}", seed=1))
        self.assertEqual(nested.claims[0].atom, "atMost(sqrt(sqrt(2)))")
        self.assertEqual(nested.open_gaps, ())
        bound = run(Request(ask="what is sup {x. x <= sqrt(sqrt(2))}", seed=1))
        self.assertEqual(bound.claims[0].atom, "cauchy(sqrt(sqrt(2)))")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        self.assertEqual(bound.open_gaps, ())

    def test_inclusion_follows_the_bounds(self) -> None:
        held = run(Request(ask="prove {x. x <= 1} subset {x. x <= 2}", seed=1))
        self.assertEqual(held.claims[0].atom, "subset({x. x <= 1},{x. x <= 2})")
        self.assertIn("atMost_subset_iff", held.text(lod=2))
        self.assertEqual(held.open_gaps, ())

        wider = run(Request(ask="prove {x. 2 <= x} subset {x. 0 <= x}", seed=1))
        self.assertEqual(wider.claims[0].atom, "subset({x. 2 <= x},{x. 0 <= x})")
        self.assertIn("atLeast_subset_iff", wider.text(lod=2))
        self.assertEqual(wider.open_gaps, ())

        refused = run(Request(ask="prove {x. x <= 3} subset {x. x <= 2}", seed=1))
        self.assertEqual(refused.claims[0].atom, "not_subset({x. x <= 3},{x. x <= 2})")
        self.assertIn("3", refused.text(lod=2))
        self.assertEqual(refused.open_gaps, ())

        crossed = run(Request(ask="prove {x. 0 <= x} subset {x. x <= 2}", seed=1))
        self.assertEqual(crossed.claims[0].atom, "not_subset({x. 0 <= x},{x. x <= 2})")
        self.assertIn("not_Ici_le_Iic", crossed.text(lod=2))
        self.assertEqual(crossed.open_gaps, ())

        carrier = run(Request(ask="prove {x. x <= 5} subset {x. x = x}", seed=1))
        self.assertEqual(carrier.claims[0].atom, "subset({x. x <= 5},{x. x = x})")
        self.assertIn("subset_UNIV", carrier.text(lod=2))
        self.assertEqual(carrier.open_gaps, ())

        spilled = run(Request(ask="prove {x. x = x} subset {x. x <= 5}", seed=1))
        self.assertEqual(spilled.claims[0].atom, "not_subset({x. x = x},{x. x <= 5})")
        self.assertIn("not_UNIV_le_Iic", spilled.text(lod=2))
        self.assertEqual(spilled.open_gaps, ())

    def test_equality_uses_a_witness(self) -> None:
        same = run(Request(ask="prove {x. x = x} = {y. y <= y}", seed=1))
        self.assertEqual(same.claims[0].atom, "identity({x. x = x} = {y. y <= y})")
        self.assertIn("UNIV_def", same.text(lod=2))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in same.claims))
        self.assertEqual(same.open_gaps, ())

        apart = run(Request(ask="prove {x. x <= 2} = {x. 2 <= x}", seed=1))
        self.assertIn("is not a theorem", apart.text(lod=1))
        self.assertEqual(_atoms(apart, "identity("), ())

        finite = run(Request(ask="prove {} = {x. x <= 2}", seed=1))
        self.assertIn("outside the finite enumeration", finite.text(lod=1))
        self.assertNotIn("division by zero", finite.text(lod=1))
        self.assertEqual(_atoms(finite, "identity("), ())

    def test_quantifiers_use_the_bound(self) -> None:
        held = run(Request(ask="prove all x in {y. y <= 5}. x <= 6", seed=1))
        self.assertEqual(held.claims[0].atom, "all(x in {y. y <= 5}, x <= 6)")
        self.assertIn("atMost_iff", held.text(lod=2))
        self.assertEqual(held.open_gaps, ())

        failed = run(Request(ask="prove all x in {y. y <= 5}. x <= 4", seed=1))
        self.assertEqual(failed.claims[0].atom, "not_all(x in {y. y <= 5}, x <= 4)")
        self.assertIn("5", failed.text(lod=2))
        self.assertEqual(failed.open_gaps, ())

        witness = run(Request(ask="prove ex x in {y. y <= 5}. x = 1", seed=1))
        self.assertEqual(witness.claims[0].atom, "ex(x in {y. y <= 5}, x = 1)")
        self.assertIn("The witness is 1.", witness.text(lod=2))
        self.assertEqual(witness.open_gaps, ())

        missing = run(Request(ask="prove ex x in {y. y <= 5}. x = 9", seed=1))
        self.assertEqual(missing.claims[0].atom, "not_ex(x in {y. y <= 5}, x = 9)")
        self.assertEqual(missing.open_gaps, ())

        universe = run(Request(ask="prove all x in {y. y = y}. x = x", seed=1))
        self.assertEqual(universe.claims[0].atom, "all(x in {y. y = y}, x = x)")
        self.assertIn("ball_UNIV", universe.text(lod=2))
        self.assertEqual(universe.open_gaps, ())

        above = run(Request(ask="prove all x in {y. y = y}. x <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_all(x in {y. y = y}, x <= 1)")
        self.assertIn("2", above.text(lod=2))
        self.assertEqual(above.open_gaps, ())

    def test_intersection_of_rays(self) -> None:
        smaller = run(Request(ask="what is {x. x <= 1} inter {x. x <= 2}", seed=1))
        self.assertEqual(smaller.claims[0].atom, "atMost(1)")
        self.assertIn("Int_atMost", smaller.text(lod=2))
        self.assertEqual(_atoms(smaller, "set("), ())
        self.assertEqual(smaller.open_gaps, ())

        point = run(Request(ask="what is {x. x <= 2} inter {x. 2 <= x}", seed=1))
        self.assertEqual(point.claims[0].atom, "set({2})")
        self.assertIn("atMost_Int_atLeast", point.text(lod=2))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in point.claims))
        self.assertEqual(point.open_gaps, ())

        empty = run(Request(ask="what is {x. 3 <= x} inter {x. x <= 1}", seed=1))
        self.assertEqual(empty.claims[0].atom, "set({})")
        self.assertIn("atLeastatMost_empty_iff", empty.text(lod=2))
        self.assertEqual(empty.open_gaps, ())

        interval = run(Request(ask="what is {x. 1 <= x} inter {x. x <= 3}", seed=1))
        self.assertEqual(interval.claims[0].atom, "atLeastAtMost(1, 3)")
        self.assertIn("atLeastAtMost(1, 3) is the closed interval from the lower bound through the upper bound", interval.text(lod=1))
        self.assertIn("atLeastAtMost_def", interval.text(lod=2))
        self.assertEqual(_atoms(interval, "set("), ())
        self.assertEqual(_atoms(interval, "atMost("), ())
        self.assertEqual(_atoms(interval, "atLeast("), ())
        self.assertEqual(interval.open_gaps, ())

        filtered = run(Request(ask="what is {1, 2, 3} inter {x. x <= 2}", seed=1))
        self.assertEqual(filtered.claims[0].atom, "set({1, 2})")
        self.assertIn("Int_iff", filtered.text(lod=2))
        self.assertEqual(filtered.open_gaps, ())

        absorbed = run(Request(ask="what is {x. x = x} inter {x. x <= 2}", seed=1))
        self.assertEqual(absorbed.claims[0].atom, "atMost(2)")
        self.assertIn("Int_UNIV_left", absorbed.text(lod=2))
        self.assertEqual(absorbed.open_gaps, ())

    def test_the_bound_is_the_least_upper_bound(self) -> None:
        supremum = run(Request(ask="what is sup {x. x <= 5}", seed=1))
        self.assertEqual(supremum.claims[0].atom, "value(5)")
        self.assertIn("cSup_atMost", supremum.text(lod=2))
        self.assertIn("bdd_above_Iic", supremum.text(lod=2))
        self.assertIn("The Archimedean bisection in the proof of complete_real stays outside this rule.", supremum.text(lod=2))
        self.assertNotIn("value(5)", supremum.text(lod=0))
        self.assertEqual(_atoms(supremum, "atMost("), ())
        self.assertNotIn("Max_in", supremum.text(lod=2))
        self.assertNotIn("cSup_eq_Max", supremum.text(lod=2))
        self.assertEqual(supremum.open_gaps, ())

        reduced = run(Request(ask="what is sup {x. x <= sqrt(4)}", seed=1))
        self.assertEqual(reduced.claims[0].atom, "value(2)")
        self.assertIn("{x. x <= sqrt(4)}", reduced.text(lod=1))
        self.assertEqual(reduced.open_gaps, ())

        root = run(Request(ask="what is sup {x. x <= sqrt(2)}", seed=1))
        self.assertEqual(root.claims[0].atom, "cauchy(sqrt(2))")
        self.assertEqual(_atoms(root, "value("), ())
        self.assertEqual(root.open_gaps, ())

        complete = run(Request(ask="prove complete {x. x <= 5}", seed=1))
        self.assertEqual(complete.claims[0].atom, "complete(atMost(5))")
        self.assertIn("complete(atMost(5)) is the least upper bound of this order ray", complete.text(lod=1))
        self.assertIn("atMost_iff", complete.text(lod=2))
        self.assertNotIn("complete(atMost(5))", complete.text(lod=0))
        self.assertEqual(_atoms(complete, "value("), ())
        self.assertNotIn("Max_in", complete.text(lod=2))
        self.assertEqual(complete.open_gaps, ())

        agreed = run(Request(ask="prove sup {x. x <= 5} = 5", seed=1))
        self.assertEqual(agreed.claims[0].atom, "identity(sup {x. x <= 5} = 5)")
        self.assertIn("cSup_atMost", agreed.text(lod=2))
        self.assertEqual(agreed.open_gaps, ())

        missed = run(Request(ask="prove sup {x. x <= 5} = 4", seed=1))
        self.assertIn("is not a theorem", missed.text(lod=1))
        self.assertEqual(_atoms(missed, "identity("), ())

        upward = run(Request(ask="what is sup {x. 0 <= x}", seed=1))
        self.assertIn("this set is not bounded above", upward.text(lod=1))
        self.assertIn("less_add_one", upward.text(lod=1))
        self.assertEqual(_atoms(upward, "value("), ())
        self.assertEqual(_atoms(upward, "complete("), ())

        carrier = run(Request(ask="prove complete {x. x = x}", seed=1))
        self.assertIn("this set is not bounded above", carrier.text(lod=1))
        self.assertIn("UNIV_I", carrier.text(lod=1))
        self.assertEqual(_atoms(carrier, "complete("), ())

        interval = run(Request(ask="what is sup ({x. 1 <= x} inter {x. x <= 3})", seed=1))
        self.assertEqual(interval.claims[0].atom, "value(3)")
        self.assertIn("cSup_atLeastAtMost", interval.text(lod=2))
        self.assertIn("cSup_eq_maximum", interval.text(lod=2))
        self.assertIn("The upper bound is a member of this interval.", interval.text(lod=2))
        self.assertIn("The Archimedean bisection in the proof of complete_real stays outside this rule.", interval.text(lod=2))
        self.assertNotIn("of_int_floor_le", interval.text(lod=2))
        self.assertNotIn("cSup_lessThan", interval.text(lod=2))
        self.assertEqual(interval.open_gaps, ())

        met = run(Request(ask="what is sup ({x. x <= 1} inter {x. x <= 2})", seed=1))
        self.assertEqual(met.claims[0].atom, "value(1)")
        self.assertIn("Int_atMost", met.text(lod=2))
        self.assertIn("cSup_atMost", met.text(lod=2))
        self.assertEqual(met.open_gaps, ())

        compound = run(Request(ask="what is sup {x. x <= x + 1}", seed=1))
        self.assertIn("this set is not bounded above", compound.text(lod=1))
        self.assertIn("UNIV_I", compound.text(lod=1))
        self.assertEqual(_atoms(compound, "value("), ())

    def test_the_bisection_builds_the_least_upper_bound(self) -> None:
        supremum = run(Request(ask="what is sup {x. x < 5}", seed=1))
        self.assertEqual(supremum.claims[0].atom, "value(5)")
        self.assertIn("cSup_lessThan", supremum.text(lod=2))
        self.assertIn("of_int_floor_le", supremum.text(lod=2))
        self.assertIn("le_of_int_ceiling", supremum.text(lod=2))
        self.assertIn("reals_Archimedean2", supremum.text(lod=2))
        self.assertIn("bdd_above_Iio", supremum.text(lod=2))
        self.assertIn("less_irrefl", supremum.text(lod=2))
        self.assertNotIn("value(5)", supremum.text(lod=0))
        self.assertNotIn("cSup_atMost", supremum.text(lod=2))
        self.assertNotIn("Max_in", supremum.text(lod=2))
        self.assertNotIn("cSup_eq_Max", supremum.text(lod=2))
        self.assertEqual(supremum.open_gaps, ())

        reduced = run(Request(ask="what is sup {x. x < sqrt(4)}", seed=1))
        self.assertEqual(reduced.claims[0].atom, "value(2)")
        self.assertIn("{x. x < sqrt(4)}", reduced.text(lod=1))
        self.assertEqual(reduced.open_gaps, ())

        root = run(Request(ask="what is sup {x. x < sqrt(2)}", seed=1))
        self.assertEqual(root.claims[0].atom, "cauchy(sqrt(2))")
        self.assertIn("reals_Archimedean2", root.text(lod=2))
        self.assertEqual(_atoms(root, "value("), ())
        self.assertEqual(root.open_gaps, ())

        negative = run(Request(ask="what is sup {x. x < -3}", seed=1))
        self.assertEqual(negative.claims[0].atom, "value(-3)")
        self.assertEqual(negative.open_gaps, ())

        named = run(Request(ask="what is {x. x < 5}", seed=1))
        self.assertEqual(named.claims[0].atom, "lessThan(5)")
        self.assertIn("lessThan(5) is the set of reals strictly below this bound", named.text(lod=1))
        self.assertIn("lessThan_def", named.text(lod=2))
        self.assertIn("infinite_Iio", named.text(lod=2))
        self.assertNotIn("stays outside this rule", named.text(lod=2))
        self.assertEqual(named.open_gaps, ())

        complete = run(Request(ask="prove complete {x. x < 5}", seed=1))
        self.assertEqual(complete.claims[0].atom, "complete(lessThan(5))")
        self.assertIn("complete(lessThan(5)) is the least upper bound of this open ray", complete.text(lod=1))
        self.assertIn("eq_Real", complete.text(lod=2))
        self.assertNotIn("complete(lessThan(5))", complete.text(lod=0))
        self.assertEqual(_atoms(complete, "value("), ())
        self.assertEqual(complete.open_gaps, ())

        agreed = run(Request(ask="prove sup {x. x < 5} = 5", seed=1))
        self.assertEqual(agreed.claims[0].atom, "identity(sup {x. x < 5} = 5)")
        self.assertIn("cSup_lessThan", agreed.text(lod=2))
        self.assertEqual(agreed.open_gaps, ())

        missed = run(Request(ask="prove sup {x. x < 5} = 4", seed=1))
        self.assertIn("is not a theorem", missed.text(lod=1))
        self.assertEqual(_atoms(missed, "identity("), ())

        upward = run(Request(ask="what is sup {x. 0 < x}", seed=1))
        self.assertIn("this set is not bounded above", upward.text(lod=1))
        self.assertIn("greaterThan_iff", upward.text(lod=1))
        self.assertEqual(_atoms(upward, "value("), ())
        self.assertEqual(_atoms(upward, "complete("), ())

        empty = run(Request(ask="what is {x. x < x}", seed=1))
        self.assertIn("less_irrefl", empty.text(lod=1))
        self.assertEqual(_atoms(empty, "lessThan("), ())
        self.assertEqual(_atoms(empty, "value("), ())

        strict = run(Request(ask="what is {x in {1, 2, 3}. x < 2}", seed=1))
        self.assertIn("a strict comparison on a finite enumeration stays outside this rule", strict.text(lod=1))
        self.assertEqual(_atoms(strict, "set("), ())

        met = run(Request(ask="what is sup ({x. x < 1} inter {x. x < 2})", seed=1))
        self.assertEqual(met.claims[0].atom, "value(1)")
        self.assertIn("lessThan_iff", met.text(lod=2))
        self.assertIn("cSup_lessThan", met.text(lod=2))
        self.assertEqual(met.open_gaps, ())

        covered = run(Request(ask="prove {x. x < 1} subset {x. x < 2}", seed=1))
        self.assertEqual(covered.claims[0].atom, "subset({x. x < 1},{x. x < 2})")
        self.assertIn("lessThan_subset_iff", covered.text(lod=2))
        self.assertEqual(covered.open_gaps, ())

        vacant = run(Request(ask="what is {x. x < 1} inter {x. 2 <= x}", seed=1))
        self.assertEqual(vacant.claims[0].atom, "set({})")
        self.assertEqual(vacant.open_gaps, ())

        interval = run(Request(ask="what is {x. 1 <= x} inter {x. x < 3}", seed=1))
        self.assertEqual(interval.claims[0].atom, "atLeastLessThan(1, 3)")
        self.assertIn("atLeastLessThan_def", interval.text(lod=2))
        self.assertNotIn("stays outside this rule", interval.text(lod=2))
        self.assertEqual(_atoms(interval, "value("), ())
        self.assertEqual(_atoms(interval, "lessThan("), ())
        self.assertEqual(interval.open_gaps, ())

        filtered = run(Request(ask="what is {1, 2, 3} inter {x. x < 2}", seed=1))
        self.assertEqual(filtered.claims[0].atom, "set({1})")
        self.assertEqual(filtered.open_gaps, ())

        witness = run(Request(ask="prove ex x in {y. y < 5}. x <= x", seed=1))
        self.assertIn("The witness is 4.", witness.text(lod=2))
        self.assertIn("lessThan_iff", witness.text(lod=2))
        self.assertNotIn("The witness is 5.", witness.text(lod=2))
        self.assertEqual(witness.open_gaps, ())

        compound = run(Request(ask="what is sup {x. x < x + 1}", seed=1))
        self.assertIn("this set is not bounded above", compound.text(lod=1))
        self.assertIn("UNIV_I", compound.text(lod=1))
        self.assertEqual(_atoms(compound, "value("), ())

        measured = run(
            Request(
                ask="what is sup {x. x < length}",
                facts=("length=4@meter stick",),
                seed=1,
            )
        )
        self.assertEqual(measured.claims[0].atom, "value(4)")
        self.assertIn("{x. x < length}", measured.text(lod=1))
        self.assertIn("meter stick", measured.text(lod=2))
        self.assertEqual(measured.open_gaps, ())

    def test_anchors_shadows_and_clashes(self) -> None:
        measured = run(
            Request(
                ask="what is {x. x <= length}",
                facts=("length=4@meter stick",),
                seed=1,
            )
        )
        self.assertEqual(measured.claims[0].atom, "atMost(4)")
        self.assertIn("meter stick", measured.text(lod=2))
        self.assertIn("{x. x <= length}", measured.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in measured.claims))
        self.assertEqual(measured.open_gaps, ())

        covered = run(
            Request(
                ask="prove {x. x <= length} subset {x. x <= 5}",
                facts=("length=4@meter stick",),
                seed=1,
            )
        )
        self.assertEqual(covered.claims[0].atom, "subset({x. x <= length},{x. x <= 5})")
        self.assertIn("meter stick", covered.text(lod=2))
        self.assertEqual(covered.open_gaps, ())

        shadowed = run(
            Request(
                ask="what is {x. x <= 3}",
                facts=("x=9@stick",),
                seed=1,
            )
        )
        self.assertEqual(shadowed.claims[0].atom, "atMost(3)")
        self.assertNotIn("source stick", " ".join(shadowed.claims[0].detail_lines))
        self.assertNotIn("9", shadowed.claims[0].atom)
        self.assertEqual(shadowed.open_gaps, ())

        clash = run(
            Request(
                ask="what is {x. x <= length}",
                facts=("length=4@left stick", "length=5@right stick"),
                seed=1,
            )
        )
        self.assertIn("value(4)", clash.retracted)
        self.assertIn("value(5)", clash.retracted)
        self.assertEqual(_atoms(clash, "atMost("), ())
        self.assertIn("Contested claims blocked a settled answer.", clash.open_gaps)

    def test_open_bounds_stay_open(self) -> None:
        import pgi.math.arbitrary as arbitrary

        original = arbitrary.compare_reals

        def _open(left, right):
            if left == right:
                return "eq"
            return "open"

        arbitrary.compare_reals = _open
        try:
            session = run(Request(ask="prove {x. x <= 1} subset {x. x <= 2}", seed=1))
            settled = run(Request(ask="what is sup {x. x <= 2}", seed=1))
            upward = run(Request(ask="what is sup {x. 0 <= x}", seed=1))
            opened = run(Request(ask="what is sup {x. x < 2}", seed=1))
            between = run(Request(ask="what is sup ({x. 1 <= x} inter {x. x <= 3})", seed=1))
        finally:
            arbitrary.compare_reals = original
        self.assertIn("this set is not settled", session.text(lod=1))
        self.assertEqual(_atoms(session, "subset("), ())
        self.assertEqual(_atoms(session, "not_subset("), ())
        self.assertEqual(settled.claims[0].atom, "value(2)")
        self.assertIn("this set is not settled", upward.text(lod=1))
        self.assertNotIn("not bounded above", upward.text(lod=1))
        self.assertEqual(_atoms(upward, "value("), ())
        self.assertIn("this set is not settled", opened.text(lod=1))
        self.assertNotIn("not bounded above", opened.text(lod=1))
        self.assertEqual(_atoms(opened, "value("), ())
        self.assertIn("this set is not settled", between.text(lod=1))
        self.assertEqual(_atoms(between, "value("), ())
        self.assertEqual(_atoms(between, "atLeastAtMost("), ())

    def test_forged_rays_are_rejected(self) -> None:
        two = real_of_rat(Ratio(2, 1)).form
        one = real_of_rat(Ratio(1, 1)).form
        three = real_of_rat(Ratio(3, 1)).form
        down = CollectForm("x", "le", Var("x"), IntLit(2))
        RayTheorem("atMost", two, down, "Set.atMost")
        with self.assertRaises(KernelError):
            RayTheorem("atMost", one, down, "Set.atMost")
        with self.assertRaises(KernelError):
            RayTheorem("atMost", RealForm(Ratio(2, 4), ()), down, "Set.atMost")
        with self.assertRaises(KernelError):
            RayTheorem("atLeast", two, down, "Set.atLeast")
        reflexive = CollectForm("x", "eq", Var("x"), Var("x"))
        RayTheorem("univ", None, reflexive, "Set.univ")
        with self.assertRaises(KernelError):
            RayTheorem("univ", two, reflexive, "Set.univ")
        with self.assertRaises(KernelError):
            RaySubsetTheorem("atMost", two, "atMost", one, None, True, None, "Ray.subset")
        with self.assertRaises(KernelError):
            RayEqTheorem("atMost", one, "atMost", two, "Ray.eq")
        with self.assertRaises(KernelError):
            RayQuantTheorem("all", True, "x", "atMost", one, Pred("le", Var("x"), IntLit(0)), None, "Ball.ray")
        with self.assertRaises(KernelError):
            RayMeetTheorem("atMost", two, (), "atMost", one, (), "atMost", two, (), "Set.meet_atMost")
        RaySupTheorem(two, down, "Ray.sup")
        with self.assertRaises(KernelError):
            RaySupTheorem(one, down, "Ray.sup")
        with self.assertRaises(KernelError):
            RaySupTheorem(RealForm(Ratio(2, 4), ()), down, "Ray.sup")
        opened = CollectForm("x", "lt", Var("x"), IntLit(5))
        five = real_of_rat(Ratio(5, 1)).form
        BisectTheorem(five, opened, "Ray.bisect")
        with self.assertRaises(KernelError):
            BisectTheorem(two, opened, "Ray.bisect")
        with self.assertRaises(KernelError):
            BisectTheorem(RealForm(Ratio(5, 1), ((Ratio(1, 1), 2),)), opened, "Ray.bisect")
        with self.assertRaises(KernelError):
            RaySupTheorem(five, opened, "Ray.sup")
        with self.assertRaises(KernelError):
            BisectTheorem(five, down, "Ray.bisect")
        IntervalSupTheorem(three, "atLeastAtMost", one, three, "Interval.sup")
        IntervalSupTheorem(three, "atLeastLessThan", one, three, "Interval.bisect")
        IntervalTheorem("greaterThanLessThan", one, three, "Set.greaterThanLessThan")
        with self.assertRaises(KernelError):
            IntervalSupTheorem(one, "atLeastAtMost", one, three, "Interval.sup")
        with self.assertRaises(KernelError):
            IntervalSupTheorem(one, "atLeastAtMost", three, one, "Interval.sup")
        with self.assertRaises(KernelError):
            IntervalSupTheorem(three, "atMost", one, three, "Interval.sup")
        with self.assertRaises(KernelError):
            IntervalSupTheorem(three, "atLeastAtMost", one, three, "Interval.bisect")
        with self.assertRaises(KernelError):
            IntervalSupTheorem(three, "atLeastLessThan", one, three, "Interval.sup")
        with self.assertRaises(KernelError):
            IntervalSupTheorem(RealForm(Ratio(6, 2), ()), "atLeastAtMost", one, RealForm(Ratio(6, 2), ()), "Interval.sup")
        with self.assertRaises(KernelError):
            IntervalTheorem("atLeastAtMost", three, three, "Set.atLeastAtMost")

    def test_the_two_sided_interval(self) -> None:
        swapped = run(Request(ask="what is {x. x <= 3} inter {x. 1 <= x}", seed=1))
        self.assertEqual(swapped.claims[0].atom, "atLeastAtMost(1, 3)")
        self.assertEqual(swapped.open_gaps, ())

        half = run(Request(ask="what is {x. 1 < x} inter {x. x <= 4}", seed=1))
        self.assertEqual(half.claims[0].atom, "greaterThanAtMost(1, 4)")
        self.assertIn("greaterThanAtMost(1, 4) is the interval strictly above the lower bound through the upper bound", half.text(lod=1))
        self.assertIn("greaterThanAtMost_iff", half.text(lod=2))
        self.assertEqual(half.open_gaps, ())

        half_sup = run(Request(ask="what is sup ({x. 1 < x} inter {x. x <= 4})", seed=1))
        self.assertEqual(half_sup.claims[0].atom, "value(4)")
        self.assertIn("cSup_greaterThanAtMost", half_sup.text(lod=2))
        self.assertIn("bdd_above_Ioc", half_sup.text(lod=2))
        self.assertIn("The upper bound is a member of this interval.", half_sup.text(lod=2))
        self.assertIn("The Archimedean bisection in the proof of complete_real stays outside this rule.", half_sup.text(lod=2))
        self.assertNotIn("of_int_floor_le", half_sup.text(lod=2))
        self.assertEqual(half_sup.open_gaps, ())

        opened = run(Request(ask="what is sup ({x. 1 <= x} inter {x. x < 3})", seed=1))
        self.assertEqual(opened.claims[0].atom, "value(3)")
        self.assertIn("cSup_atLeastLessThan", opened.text(lod=2))
        self.assertIn("cSup_eq_non_empty", opened.text(lod=2))
        self.assertIn("bdd_above_Ico", opened.text(lod=2))
        self.assertIn("of_int_floor_le", opened.text(lod=2))
        self.assertIn("le_of_int_ceiling", opened.text(lod=2))
        self.assertIn("reals_Archimedean2", opened.text(lod=2))
        self.assertIn("less_irrefl", opened.text(lod=2))
        self.assertIn("the upper bound is not a member of this interval", opened.text(lod=2))
        self.assertNotIn("stays outside this rule", opened.text(lod=2))
        self.assertNotIn("cSup_eq_maximum", opened.text(lod=2))
        self.assertNotIn("cSup_lessThan", opened.text(lod=2))
        self.assertNotIn("Max_in", opened.text(lod=2))
        self.assertNotIn("value(3)", opened.text(lod=0))
        self.assertEqual(opened.open_gaps, ())

        both = run(Request(ask="what is sup ({x. 1 < x} inter {x. x < 4})", seed=1))
        self.assertEqual(both.claims[0].atom, "value(4)")
        self.assertIn("cSup_greaterThanLessThan", both.text(lod=2))
        self.assertIn("bdd_above_Ioo", both.text(lod=2))
        self.assertIn("the upper bound is not a member of this interval", both.text(lod=2))
        self.assertNotIn("stays outside this rule", both.text(lod=2))
        self.assertEqual(both.open_gaps, ())

        named = run(Request(ask="what is {x. 1 < x} inter {x. x < 4}", seed=1))
        self.assertEqual(named.claims[0].atom, "greaterThanLessThan(1, 4)")
        self.assertIn("greaterThanLessThan(1, 4) is the open interval strictly between these bounds", named.text(lod=1))
        self.assertEqual(named.open_gaps, ())

        complete = run(Request(ask="prove complete ({x. 1 <= x} inter {x. x <= 3})", seed=1))
        self.assertEqual(complete.claims[0].atom, "complete(atLeastAtMost(1, 3))")
        self.assertIn("complete(atLeastAtMost(1, 3)) is the least upper bound of this interval", complete.text(lod=1))
        self.assertNotIn("complete(atLeastAtMost(1, 3))", complete.text(lod=0))
        self.assertEqual(_atoms(complete, "value("), ())
        self.assertEqual(complete.open_gaps, ())

        open_complete = run(Request(ask="prove complete ({x. 1 <= x} inter {x. x < 3})", seed=1))
        self.assertEqual(open_complete.claims[0].atom, "complete(atLeastLessThan(1, 3))")
        self.assertIn("complete(atLeastLessThan(1, 3)) is the least upper bound of this interval", open_complete.text(lod=1))
        self.assertIn("cSup_atLeastLessThan", open_complete.text(lod=2))
        self.assertEqual(open_complete.open_gaps, ())

        agreed = run(Request(ask="prove sup ({x. 1 <= x} inter {x. x <= 3}) = 3", seed=1))
        self.assertEqual(agreed.claims[0].atom, "identity(sup ({x. 1 <= x} inter {x. x <= 3}) = 3)")
        self.assertIn("cSup_atLeastAtMost", agreed.text(lod=2))
        self.assertEqual(agreed.open_gaps, ())

        missed = run(Request(ask="prove sup ({x. 1 <= x} inter {x. x <= 3}) = 2", seed=1))
        self.assertIn("is not a theorem", missed.text(lod=1))
        self.assertEqual(_atoms(missed, "identity("), ())

        root = run(Request(ask="what is sup ({x. 0 <= x} inter {x. x <= sqrt(4)})", seed=1))
        self.assertEqual(root.claims[0].atom, "value(2)")
        self.assertIn("sqrt(4)", root.text(lod=1))
        self.assertIn("cSup_atLeastAtMost", root.text(lod=2))
        self.assertNotIn("of_int_floor_le", root.text(lod=2))
        self.assertEqual(root.open_gaps, ())

        irrational = run(Request(ask="what is sup ({x. 0 <= x} inter {x. x < sqrt(2)})", seed=1))
        self.assertEqual(irrational.claims[0].atom, "cauchy(sqrt(2))")
        self.assertIn("cSup_atLeastLessThan", irrational.text(lod=2))
        self.assertIn("reals_Archimedean2", irrational.text(lod=2))
        self.assertEqual(_atoms(irrational, "value("), ())
        self.assertEqual(irrational.open_gaps, ())

        negative = run(Request(ask="what is sup ({x. -5 <= x} inter {x. x <= -3})", seed=1))
        self.assertEqual(negative.claims[0].atom, "value(-3)")
        self.assertNotIn("of_int_floor_le", negative.text(lod=2))
        self.assertEqual(negative.open_gaps, ())

        below = run(Request(ask="what is sup ({x. -4 <= x} inter {x. x < -1})", seed=1))
        self.assertEqual(below.claims[0].atom, "value(-1)")
        self.assertIn("cSup_atLeastLessThan", below.text(lod=2))
        self.assertEqual(below.open_gaps, ())

        same = run(Request(ask="what is {x. 2 <= x} inter {x. x < 2}", seed=1))
        self.assertEqual(same.claims[0].atom, "set({})")
        self.assertEqual(same.open_gaps, ())

        touch = run(Request(ask="what is {x. 2 < x} inter {x. x <= 2}", seed=1))
        self.assertEqual(touch.claims[0].atom, "set({})")
        self.assertEqual(touch.open_gaps, ())

        vacant = run(Request(ask="what is sup ({x. 3 <= x} inter {x. x <= 1})", seed=1))
        self.assertIn("complete_real assumes a member. The empty set has none", vacant.text(lod=1))
        self.assertEqual(_atoms(vacant, "value("), ())

        measured = run(
            Request(
                ask="what is sup ({x. 0 <= x} inter {x. x <= length})",
                facts=("length=4@meter stick",),
                seed=1,
            )
        )
        self.assertEqual(measured.claims[0].atom, "value(4)")
        self.assertIn("length", measured.text(lod=1))
        self.assertIn("meter stick", measured.text(lod=2))
        self.assertEqual(measured.open_gaps, ())

    def test_boolean_connectives(self) -> None:
        closed = run(Request(ask="what is {x. 1 <= x and x <= 3}", seed=1))
        self.assertEqual(closed.claims[0].atom, "atLeastAtMost(1, 3)")
        self.assertIn("Collect_conj_eq", closed.text(lod=2))
        self.assertNotIn("Collect_conj_eq2", closed.text(lod=2))
        self.assertIn("atLeastAtMost_def", closed.text(lod=2))
        self.assertIn(
            "atLeastAtMost(1, 3) is the closed interval from the lower bound through the upper bound",
            closed.text(lod=1),
        )
        self.assertEqual(closed.open_gaps, ())

        swapped = run(Request(ask="what is {x. x <= 3 and 1 <= x}", seed=1))
        self.assertEqual(swapped.claims[0].atom, "atLeastAtMost(1, 3)")
        self.assertEqual(swapped.open_gaps, ())

        grouped = run(Request(ask="what is {x. (1 <= x) and (x <= 3)}", seed=1))
        self.assertEqual(grouped.claims[0].atom, "atLeastAtMost(1, 3)")
        self.assertEqual(grouped.open_gaps, ())

        opened = run(Request(ask="what is {x. 1 <= x and x < 3}", seed=1))
        self.assertEqual(opened.claims[0].atom, "atLeastLessThan(1, 3)")
        self.assertIn("Collect_conj_eq", opened.text(lod=2))
        self.assertEqual(opened.open_gaps, ())

        both = run(Request(ask="what is {x. 1 < x and x < 4}", seed=1))
        self.assertEqual(both.claims[0].atom, "greaterThanLessThan(1, 4)")
        self.assertEqual(both.open_gaps, ())

        point = run(Request(ask="what is {x. x <= 2 and 2 <= x}", seed=1))
        self.assertEqual(point.claims[0].atom, "set({2})")
        self.assertIn("atMost_Int_atLeast", point.text(lod=2))
        self.assertEqual(point.open_gaps, ())

        vacant = run(Request(ask="what is {x. 3 <= x and x <= 1}", seed=1))
        self.assertEqual(vacant.claims[0].atom, "set({})")
        self.assertIn("atLeastatMost_empty_iff", vacant.text(lod=2))
        self.assertEqual(vacant.open_gaps, ())

        touch = run(Request(ask="what is {x. 2 <= x and x < 2}", seed=1))
        self.assertEqual(touch.claims[0].atom, "set({})")
        self.assertEqual(touch.open_gaps, ())

        closed_sup = run(Request(ask="what is sup {x. 1 <= x and x <= 3}", seed=1))
        self.assertEqual(closed_sup.claims[0].atom, "value(3)")
        self.assertIn("Collect_conj_eq", closed_sup.text(lod=2))
        self.assertIn("cSup_atLeastAtMost", closed_sup.text(lod=2))
        self.assertIn(
            "The Archimedean bisection in the proof of complete_real stays outside this rule.",
            closed_sup.text(lod=2),
        )
        self.assertEqual(closed_sup.open_gaps, ())

        open_sup = run(Request(ask="what is sup {x. 1 <= x and x < 3}", seed=1))
        self.assertEqual(open_sup.claims[0].atom, "value(3)")
        self.assertIn("Collect_conj_eq", open_sup.text(lod=2))
        self.assertIn("cSup_atLeastLessThan", open_sup.text(lod=2))
        self.assertIn("reals_Archimedean2", open_sup.text(lod=2))
        self.assertIn("less_irrefl", open_sup.text(lod=2))
        self.assertNotIn("stays outside this rule", open_sup.text(lod=2))
        self.assertEqual(open_sup.open_gaps, ())

        complete = run(Request(ask="prove complete {x. 1 <= x and x <= 3}", seed=1))
        self.assertEqual(complete.claims[0].atom, "complete(atLeastAtMost(1, 3))")
        self.assertEqual(complete.open_gaps, ())

        agreed = run(Request(ask="prove sup {x. 1 <= x and x <= 3} = 3", seed=1))
        self.assertEqual(agreed.claims[0].atom, "identity(sup {x. 1 <= x and x <= 3} = 3)")
        self.assertEqual(agreed.open_gaps, ())

        root = run(Request(ask="what is {x. 0 <= x and x <= sqrt(4)}", seed=1))
        self.assertEqual(root.claims[0].atom, "atLeastAtMost(0, 2)")
        self.assertEqual(root.open_gaps, ())

        negative = run(Request(ask="what is {x. -5 <= x and x <= -3}", seed=1))
        self.assertEqual(negative.claims[0].atom, "atLeastAtMost(-5, -3)")
        self.assertEqual(negative.open_gaps, ())

        measured = run(
            Request(
                ask="what is {x. 0 <= x and x <= length}",
                facts=("length=4@meter stick",),
                seed=1,
            )
        )
        self.assertEqual(measured.claims[0].atom, "atLeastAtMost(0, 4)")
        self.assertIn("length", measured.text(lod=1))
        self.assertIn("meter stick", measured.text(lod=2))
        self.assertEqual(measured.open_gaps, ())

        separated = run(Request(ask="what is {x in {1, 2, 3, 4}. 1 <= x and x <= 3}", seed=1))
        self.assertEqual(separated.claims[0].atom, "set({1, 2, 3})")
        self.assertIn("Collect_conj_eq2", separated.text(lod=2))
        self.assertEqual(separated.open_gaps, ())

        strict = run(Request(ask="what is {x in {1, 2}. x < 2 and x = 1}", seed=1))
        self.assertIn("a strict comparison on a finite enumeration stays outside this rule", strict.text(lod=1))
        self.assertEqual(_atoms(strict, "set("), ())

        either = run(Request(ask="what is {x. x = 1 or x = 2}", seed=1))
        self.assertEqual(either.claims[0].atom, "set({1, 2})")
        self.assertIn("Collect_disj_eq", either.text(lod=2))
        self.assertIn("Un_iff", either.text(lod=2))
        self.assertIn("singleton_conv", either.text(lod=2))
        self.assertEqual(either.open_gaps, ())

        collapsed = run(Request(ask="what is {x. x = sqrt(4) or x = 2}", seed=1))
        self.assertEqual(collapsed.claims[0].atom, "set({2})")
        self.assertEqual(collapsed.open_gaps, ())

        witnessed = run(Request(ask="prove 1 in {x. x = 1 or x = 2}", seed=1))
        self.assertEqual(witnessed.claims[0].atom, "member(1,{x. x = 1 or x = 2})")
        self.assertEqual(witnessed.open_gaps, ())

        missed = run(Request(ask="prove 4 in {x. x = 1 or x = 2}", seed=1))
        self.assertEqual(missed.claims[0].atom, "not_member(4,{x. x = 1 or x = 2})")
        self.assertEqual(missed.open_gaps, ())

        topped = run(Request(ask="what is sup {x. x = 1 or x = 2}", seed=1))
        self.assertEqual(topped.claims[0].atom, "value(2)")
        self.assertIn("Collect_disj_eq", topped.text(lod=2))
        self.assertEqual(topped.open_gaps, ())

        above = run(Request(ask="what is {x. not x <= 5}", seed=1))
        self.assertEqual(above.claims[0].atom, "greaterThan(5)")
        self.assertIn("Collect_neg_eq", above.text(lod=2))
        self.assertIn("Compl_atMost", above.text(lod=2))
        self.assertEqual(above.open_gaps, ())

        below = run(Request(ask="what is {x. not 5 <= x}", seed=1))
        self.assertEqual(below.claims[0].atom, "lessThan(5)")
        self.assertIn("Compl_atLeast", below.text(lod=2))
        self.assertEqual(below.open_gaps, ())

        from_open = run(Request(ask="what is {x. not x < 5}", seed=1))
        self.assertEqual(from_open.claims[0].atom, "atLeast(5)")
        self.assertIn("Compl_lessThan", from_open.text(lod=2))
        self.assertEqual(from_open.open_gaps, ())

        from_up = run(Request(ask="what is {x. not 5 < x}", seed=1))
        self.assertEqual(from_up.claims[0].atom, "atMost(5)")
        self.assertIn("Compl_greaterThan", from_up.text(lod=2))
        self.assertEqual(from_up.open_gaps, ())

        none = run(Request(ask="what is {x. not x = x}", seed=1))
        self.assertEqual(none.claims[0].atom, "set({})")
        self.assertIn("Compl_UNIV_eq", none.text(lod=2))
        self.assertEqual(none.open_gaps, ())

        none_le = run(Request(ask="what is {x. not x <= x}", seed=1))
        self.assertEqual(none_le.claims[0].atom, "set({})")
        self.assertEqual(none_le.open_gaps, ())

        rooted = run(Request(ask="what is {x. not x <= sqrt(4)}", seed=1))
        self.assertEqual(rooted.claims[0].atom, "greaterThan(2)")
        self.assertEqual(rooted.open_gaps, ())

        negated_sup = run(Request(ask="what is sup {x. not 5 < x}", seed=1))
        self.assertEqual(negated_sup.claims[0].atom, "value(5)")
        self.assertIn("Compl_greaterThan", negated_sup.text(lod=2))
        self.assertIn("cSup_atMost", negated_sup.text(lod=2))
        self.assertIn(
            "The Archimedean bisection in the proof of complete_real stays outside this rule.",
            negated_sup.text(lod=2),
        )
        self.assertEqual(negated_sup.open_gaps, ())

        parenthesized = run(Request(ask="what is {x. (1 + 1) <= x}", seed=1))
        self.assertEqual(parenthesized.claims[0].atom, "atLeast(2)")
        self.assertNotIn("Collect_neg_eq", parenthesized.text(lod=2))
        self.assertEqual(parenthesized.open_gaps, ())

        plain = run(Request(ask="what is {x. x <= 2}", seed=1))
        self.assertEqual(plain.claims[0].atom, "atMost(2)")
        self.assertNotIn("Collect_conj_eq", plain.text(lod=2))
        self.assertNotIn("Collect_neg_eq", plain.text(lod=2))

        rays = run(Request(ask="what is {x. x <= 1 or 3 <= x}", seed=1))
        self.assertEqual(rays.claims[0].atom, "atMost(1) union atLeast(3)")
        self.assertIn("Un_iff", rays.text(lod=2))
        self.assertEqual(rays.open_gaps, ())

        complement = run(Request(ask="what is {x. not x = 2}", seed=1))
        self.assertEqual(complement.claims[0].atom, "lessThan(2) union greaterThan(2)")
        self.assertIn("linorder_neq_iff", complement.text(lod=2))
        self.assertEqual(complement.open_gaps, ())

        nested = run(Request(ask="what is {x. 1 <= x and x <= 3 and x <= 4}", seed=1))
        self.assertEqual(nested.claims[0].atom, "atLeastAtMost(1, 3)")
        self.assertIn("Collect_conj_eq", nested.text(lod=2))
        self.assertEqual(nested.open_gaps, ())

        tightened = run(Request(ask="what is {x. 1 <= x and x <= 3 and x <= 2}", seed=1))
        self.assertEqual(tightened.claims[0].atom, "atLeastAtMost(1, 2)")
        self.assertEqual(tightened.open_gaps, ())

        vacant_and = run(Request(ask="what is {x. 1 <= x and x <= 3 and 4 <= x}", seed=1))
        self.assertEqual(vacant_and.claims[0].atom, "set({})")
        self.assertEqual(vacant_and.open_gaps, ())

        doubled = run(Request(ask="what is {x. not not x <= 2}", seed=1))
        self.assertEqual(doubled.claims[0].atom, "atMost(2)")
        self.assertIn("Collect_neg_eq", doubled.text(lod=2))
        self.assertIn("double_compl", doubled.text(lod=2))
        self.assertEqual(doubled.open_gaps, ())

        tripled = run(Request(ask="what is {x. not not not x <= 2}", seed=1))
        self.assertEqual(tripled.claims[0].atom, "greaterThan(2)")
        self.assertEqual(tripled.open_gaps, ())

        implied = run(Request(ask="what is {x. x <= 1 implies x <= 3}", seed=1))
        self.assertEqual(implied.claims[0].atom, "univ")
        self.assertIn("imp_conv_disj", implied.text(lod=2))
        self.assertEqual(implied.open_gaps, ())

        implied_gap = run(Request(ask="what is {x. x <= 1 implies x <= 0}", seed=1))
        self.assertEqual(implied_gap.claims[0].atom, "atMost(0) union greaterThan(1)")
        self.assertIn("imp_conv_disj", implied_gap.text(lod=2))
        self.assertEqual(implied_gap.open_gaps, ())

        covered = run(Request(ask="what is {x. x <= 1 or x <= 3}", seed=1))
        self.assertEqual(covered.claims[0].atom, "atMost(3)")
        self.assertIn("Collect_disj_eq", covered.text(lod=2))
        self.assertEqual(covered.open_gaps, ())

        whole = run(Request(ask="what is {x. x <= 3 or 1 <= x}", seed=1))
        self.assertEqual(whole.claims[0].atom, "univ")
        self.assertEqual(whole.open_gaps, ())

        joined = run(Request(ask="what is {x. x <= 3} union {x. x <= 1}", seed=1))
        self.assertEqual(joined.claims[0].atom, "atMost(3)")
        self.assertEqual(joined.open_gaps, ())

        trimmed = run(Request(ask="what is ({x. 1 <= x} inter {x. x <= 3}) inter {x. x <= 2}", seed=1))
        self.assertEqual(trimmed.claims[0].atom, "atLeastAtMost(1, 2)")
        self.assertEqual(trimmed.open_gaps, ())

        arithmetic = run(Request(ask="what is 1 and 2", seed=1))
        self.assertIn("No answer rule fired from the given facts.", arithmetic.open_gaps)
        self.assertEqual(_atoms(arithmetic, "value("), ())

        one = real_of_rat(Ratio(1, 1)).form
        two = real_of_rat(Ratio(2, 1)).form
        three = real_of_rat(Ratio(3, 1)).form
        predicate = App(
            "and",
            (
                App("le", (IntLit(1), Var("x"))),
                App("le", (Var("x"), IntLit(3))),
            ),
        )
        domain = App("type", ())
        ConnectiveTheorem("x", domain, predicate, "Collect.conj", "atLeastAtMost", one, (three,), ())
        with self.assertRaises(KernelError):
            ConnectiveTheorem("x", domain, predicate, "Collect.conj", "atLeastAtMost", one, (two,), ())
        with self.assertRaises(KernelError):
            ConnectiveTheorem("x", domain, predicate, "Collect.disj", "atLeastAtMost", one, (three,), ())

    def test_gapped_unions_and_finite_complements(self) -> None:
        rays = run(Request(ask="what is {x. x <= 1 or 3 <= x}", seed=1))
        self.assertEqual(rays.claims[0].atom, "atMost(1) union atLeast(3)")
        self.assertEqual(rays.open_gaps, ())

        joined = run(Request(ask="what is {x. x <= 3} union {x. 5 <= x}", seed=1))
        self.assertEqual(joined.claims[0].atom, "atMost(3) union atLeast(5)")
        self.assertEqual(joined.open_gaps, ())

        absorbed = run(Request(ask="what is {x. x <= 1 or 3 <= x or 10 <= x}", seed=1))
        self.assertEqual(absorbed.claims[0].atom, "atMost(1) union atLeast(3)")
        self.assertEqual(absorbed.open_gaps, ())

        punctured = run(Request(ask="what is {x. not x = 2}", seed=1))
        self.assertEqual(punctured.claims[0].atom, "lessThan(2) union greaterThan(2)")
        self.assertIn("linorder_neq_iff", punctured.text(lod=2))
        self.assertEqual(punctured.open_gaps, ())

        two = run(Request(ask="what is {x. not (x = 1 or x = 2)}", seed=1))
        self.assertEqual(two.claims[0].atom, "lessThan(1) union greaterThanLessThan(1, 2) union greaterThan(2)")
        self.assertEqual(two.open_gaps, ())

        outside = run(Request(ask="what is {x. not (1 <= x and x <= 3)}", seed=1))
        self.assertEqual(outside.claims[0].atom, "lessThan(1) union greaterThan(3)")
        self.assertEqual(outside.open_gaps, ())

        mixed = run(Request(ask="what is {x. x <= 1 or x = 3}", seed=1))
        self.assertEqual(mixed.claims[0].atom, "atMost(1) union set({3})")
        self.assertEqual(mixed.open_gaps, ())

        met = run(Request(ask="what is {x. x <= 1 or 3 <= x} inter {x. x <= 4}", seed=1))
        self.assertEqual(met.claims[0].atom, "atMost(1) union atLeastAtMost(3, 4)")
        self.assertEqual(met.open_gaps, ())

        bounded = run(Request(ask="what is sup {x. x <= 1 or (2 <= x and x <= 3)}", seed=1))
        self.assertEqual(bounded.claims[0].atom, "value(3)")
        self.assertIn("Un_iff", bounded.text(lod=2))
        self.assertEqual(bounded.open_gaps, ())

        upward = run(Request(ask="what is sup {x. x <= 1 or 3 <= x}", seed=1))
        self.assertIn("this set is not bounded above", upward.text(lod=1))
        self.assertEqual(_atoms(upward, "value("), ())

        inside = run(Request(ask="prove 0 in {x. x <= 1 or 3 <= x}", seed=1))
        self.assertEqual(inside.claims[0].atom, "member(0,{x. x <= 1 or 3 <= x})")
        self.assertEqual(inside.open_gaps, ())

        gap = run(Request(ask="prove 2 in {x. x <= 1 or 3 <= x}", seed=1))
        self.assertEqual(gap.claims[0].atom, "not_member(2,{x. x <= 1 or 3 <= x})")
        self.assertEqual(gap.open_gaps, ())

        missed = run(Request(ask="prove 2 in {x. not x = 2}", seed=1))
        self.assertEqual(missed.claims[0].atom, "not_member(2,{x. not x = 2})")
        self.assertEqual(missed.open_gaps, ())

        quadratic = run(Request(ask="what is {x. x * x <= 2}", seed=1))
        self.assertEqual(quadratic.claims[0].atom, "atLeastAtMost(-sqrt(2), sqrt(2))")
        self.assertEqual(quadratic.open_gaps, ())

    def test_affine_comparisons_reduce_to_rays(self) -> None:

        always = run(Request(ask="what is {x. x <= x + 1}", seed=1))
        self.assertEqual(always.claims[0].atom, "univ")
        self.assertIn("add_le_cancel", always.text(lod=2))
        self.assertEqual(always.open_gaps, ())

        empty = run(Request(ask="what is {x. x + 1 <= x}", seed=1))
        self.assertEqual(empty.claims[0].atom, "set({})")
        self.assertEqual(empty.open_gaps, ())

        cancelled = run(Request(ask="what is {x. 2 * x <= x + 1}", seed=1))
        self.assertEqual(cancelled.claims[0].atom, "atMost(1)")
        self.assertIn("mult_le_cancel_left", cancelled.text(lod=2))
        self.assertEqual(cancelled.open_gaps, ())

        flipped = run(Request(ask="what is {x. 0 <= -x}", seed=1))
        self.assertEqual(flipped.claims[0].atom, "atMost(0)")
        self.assertEqual(flipped.open_gaps, ())

        point = run(Request(ask="what is {x. 2 * x = x + 1}", seed=1))
        self.assertEqual(point.claims[0].atom, "set({1})")
        self.assertEqual(point.open_gaps, ())

        bound = run(Request(ask="what is sup {x. 2 * x <= x + 1}", seed=1))
        self.assertEqual(bound.claims[0].atom, "value(1)")
        self.assertEqual(bound.open_gaps, ())

        witnessed = run(Request(ask="prove 0 in {x. x <= x + 1}", seed=1))
        self.assertEqual(witnessed.claims[0].atom, "member(0,{x. x <= x + 1})")
        self.assertEqual(witnessed.open_gaps, ())

        quadratic = run(Request(ask="what is {x. x * x <= 2}", seed=1))
        self.assertEqual(quadratic.claims[0].atom, "atLeastAtMost(-sqrt(2), sqrt(2))")
        self.assertEqual(quadratic.open_gaps, ())
        self.assertEqual(_atoms(quadratic, "atMost("), ())

    def test_quadratic_sign_charts(self) -> None:
        closed = run(Request(ask="what is {x. x * x <= 2}", seed=1))
        self.assertEqual(closed.claims[0].atom, "atLeastAtMost(-sqrt(2), sqrt(2))")
        self.assertIn("Sturm", closed.text(lod=2))
        self.assertIn("admitted radical", closed.text(lod=2))
        self.assertEqual(closed.open_gaps, ())

        opened = run(Request(ask="what is {x. x * x < 2}", seed=1))
        self.assertEqual(opened.claims[0].atom, "greaterThanLessThan(-sqrt(2), sqrt(2))")
        self.assertEqual(opened.open_gaps, ())

        outside = run(Request(ask="what is {x. 2 <= x * x}", seed=1))
        self.assertEqual(outside.claims[0].atom, "atMost(-sqrt(2)) union atLeast(sqrt(2))")
        self.assertEqual(outside.open_gaps, ())

        roots = run(Request(ask="what is {x. x * x = 2}", seed=1))
        self.assertEqual(roots.claims[0].atom, "set({-sqrt(2), sqrt(2)})")
        self.assertEqual(roots.open_gaps, ())

        factored = run(Request(ask="what is {x. (x - 1) * (x - 3) <= 0}", seed=1))
        self.assertEqual(factored.claims[0].atom, "atLeastAtMost(1, 3)")
        self.assertEqual(factored.open_gaps, ())

        vacant = run(Request(ask="what is {x. x * x + 1 <= 0}", seed=1))
        self.assertEqual(vacant.claims[0].atom, "set({})")
        self.assertEqual(vacant.open_gaps, ())

        bound = run(Request(ask="what is sup {x. x * x <= 2}", seed=1))
        self.assertEqual(bound.claims[0].atom, "cauchy(sqrt(2))")
        self.assertEqual(bound.open_gaps, ())

        inside = run(Request(ask="prove 0 in {x. x * x <= 2}", seed=1))
        self.assertEqual(inside.claims[0].atom, "member(0,{x. x * x <= 2})")
        self.assertEqual(inside.open_gaps, ())

        missed = run(Request(ask="prove 2 in {x. x * x <= 2}", seed=1))
        self.assertEqual(missed.claims[0].atom, "not_member(2,{x. x * x <= 2})")
        self.assertEqual(missed.open_gaps, ())

        cubic = run(Request(ask="what is {x. x * x * x <= 2}", seed=1))
        self.assertEqual(cubic.claims[0].atom, "atMost(root(x^3 - 2, 1))")
        self.assertEqual(cubic.open_gaps, ())

    def test_polynomial_sign_charts(self) -> None:
        cubic = run(Request(ask="what is {x. x * x * x <= 2}", seed=1))
        self.assertEqual(cubic.claims[0].atom, "atMost(root(x^3 - 2, 1))")
        self.assertIn("Sturm", cubic.text(lod=2))
        self.assertEqual(cubic.open_gaps, ())

        opened = run(Request(ask="what is {x. x * x * x < 2}", seed=1))
        self.assertEqual(opened.claims[0].atom, "lessThan(root(x^3 - 2, 1))")
        self.assertEqual(opened.open_gaps, ())

        above = run(Request(ask="what is {x. x * x * x >= 2}", seed=1))
        self.assertEqual(above.claims[0].atom, "atLeast(root(x^3 - 2, 1))")
        self.assertEqual(above.open_gaps, ())

        roots = run(Request(ask="what is {x. x * x * x = 2}", seed=1))
        self.assertEqual(roots.claims[0].atom, "set({root(x^3 - 2, 1)})")
        self.assertEqual(roots.open_gaps, ())

        bound = run(Request(ask="what is sup {x. x * x * x <= 2}", seed=1))
        self.assertEqual(bound.claims[0].atom, "cauchy(root(x^3 - 2, 1))")
        self.assertEqual(bound.open_gaps, ())

        inside = run(Request(ask="prove 1 in {x. x * x * x <= 2}", seed=1))
        self.assertEqual(inside.claims[0].atom, "member(1,{x. x * x * x <= 2})")
        self.assertEqual(inside.open_gaps, ())

        missed = run(Request(ask="prove 2 in {x. x * x * x <= 2}", seed=1))
        self.assertEqual(missed.claims[0].atom, "not_member(2,{x. x * x * x <= 2})")
        self.assertEqual(missed.open_gaps, ())

        factored = run(Request(ask="what is {x. (x * x * x) - x <= 0}", seed=1))
        self.assertEqual(factored.claims[0].atom, "atMost(-1) union atLeastAtMost(0, 1)")
        self.assertEqual(factored.open_gaps, ())

        nested = run(Request(ask="what is {x. x * x * x * x <= 2}", seed=1))
        self.assertEqual(nested.claims[0].atom, "atLeastAtMost(-sqrt(sqrt(2)), sqrt(sqrt(2)))")
        self.assertEqual(nested.open_gaps, ())

        mixed = run(Request(ask="what is {x. (x * x - 2) * (x - 3) <= 0}", seed=1))
        self.assertEqual(mixed.claims[0].atom, "atMost(-sqrt(2)) union atLeastAtMost(sqrt(2), 3)")
        self.assertEqual(mixed.open_gaps, ())

        vacant = run(Request(ask="what is {x. x * x * x * x + 1 <= 0}", seed=1))
        self.assertEqual(vacant.claims[0].atom, "set({})")
        self.assertEqual(vacant.open_gaps, ())

        irreducible = run(Request(ask="what is {x. x * x * x + x + 1 = 0}", seed=1))
        self.assertEqual(irreducible.claims[0].atom, "set({root(x^3 + x + 1, 1)})")
        self.assertEqual(irreducible.open_gaps, ())

        unformable = run(Request(ask="what is {x. x * x <= sqrt(sqrt(2)) + sqrt(sqrt(3))}", seed=1))
        self.assertIn("this comprehension is not a finite enumeration", unformable.text(lod=1))
        self.assertTrue(unformable.open_gaps)

    def test_ge_and_gt_rewrite_to_le_and_lt(self) -> None:

        from pgi.math.syntax import GE_IFF, GT_IFF, parse_term, pretty, rewrite_ge_gt

        parsed = parse_term("{x. x >= 2}")
        self.assertIsNotNone(parsed)
        self.assertEqual(pretty(parsed), "{x. x >= 2}")
        rewritten, lines = rewrite_ge_gt(parsed)
        self.assertEqual(pretty(rewritten), "{x. 2 <= x}")
        self.assertIn(GE_IFF, lines)

        parsed_gt = parse_term("{x. x > 2}")
        rewritten_gt, gt_lines = rewrite_ge_gt(parsed_gt)
        self.assertEqual(pretty(rewritten_gt), "{x. 2 < x}")
        self.assertIn(GT_IFF, gt_lines)

        closed = run(Request(ask="what is {x. x >= 2}", seed=1))
        self.assertEqual(closed.claims[0].atom, "atLeast(2)")
        self.assertIn("ge_iff_le", closed.text(lod=2))
        self.assertEqual(closed.open_gaps, ())

        opened = run(Request(ask="what is {x. x > 2}", seed=1))
        self.assertEqual(opened.claims[0].atom, "greaterThan(2)")
        self.assertIn("gt_iff_lt", opened.text(lod=2))
        self.assertEqual(opened.open_gaps, ())

        down = run(Request(ask="what is {x. 2 >= x}", seed=1))
        self.assertEqual(down.claims[0].atom, "atMost(2)")
        self.assertEqual(down.open_gaps, ())

        outside = run(Request(ask="what is {x. x * x >= 2}", seed=1))
        self.assertEqual(outside.claims[0].atom, "atMost(-sqrt(2)) union atLeast(sqrt(2))")
        self.assertIn("ge_iff_le", outside.text(lod=2))
        self.assertEqual(outside.open_gaps, ())

        strict = run(Request(ask="what is {x. x * x > 2}", seed=1))
        self.assertEqual(strict.claims[0].atom, "lessThan(-sqrt(2)) union greaterThan(sqrt(2))")
        self.assertEqual(strict.open_gaps, ())

        filtered = run(Request(ask="what is {x in {1, 2, 3}. x >= 2}", seed=1))
        self.assertEqual(filtered.claims[0].atom, "set({2, 3})")
        self.assertEqual(filtered.open_gaps, ())

        complemented = run(Request(ask="what is {x. not x >= 2}", seed=1))
        self.assertEqual(complemented.claims[0].atom, "lessThan(2)")
        self.assertEqual(complemented.open_gaps, ())

        compared = run(Request(ask="prove 5 >= 2", seed=1))
        self.assertEqual(compared.claims[0].atom, "le(2,5)")
        self.assertIn("ge_iff_le", compared.text(lod=2))
        self.assertEqual(compared.open_gaps, ())

        refused = run(Request(ask="prove 2 >= 5", seed=1))
        self.assertEqual(refused.claims[0].atom, "not_le(5,2)")
        self.assertIn("ge_iff_le", refused.text(lod=2))
        self.assertEqual(refused.open_gaps, ())

    def test_older_paths_stay_on_their_rules(self) -> None:



        enumerated = run(Request(ask="what is {1, 2}", seed=1))
        self.assertEqual(enumerated.claims[0].atom, "set({1, 2})")
        self.assertNotIn("atMost", enumerated.text(lod=2))
        self.assertNotIn("UNIV", enumerated.text(lod=2))

        root = run(Request(ask="what is sqrt(2)", seed=1))
        self.assertEqual(root.claims[0].atom, "cauchy(sqrt(2))")
        self.assertNotIn("atMost", root.text(lod=2))

        member = run(Request(ask="prove 2 in {1, 2}", seed=1))
        self.assertEqual(member.claims[0].atom, "member(2,{1, 2})")

        universal = run(Request(ask="prove all x in {1, 2}. x <= 2", seed=1))
        self.assertEqual(universal.claims[0].atom, "all(x in {1, 2}, x <= 2)")
