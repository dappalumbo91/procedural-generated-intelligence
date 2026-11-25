from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.kernel import KernelError, NotExact
from pgi.math.rational import Ratio
from pgi.math.real import RealForm, real_of_rat
from pgi.math.set import EqTheorem, MemberTheorem, SetTheorem, SupTheorem, set_empty, set_insert, set_sup
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


def _settled_atoms(session) -> tuple[str, ...]:
    return tuple(claim.atom for claim in session.claims if claim.atom.startswith(("value(", "ratio(", "cauchy(", "set(")))


class FiniteSetTests(unittest.TestCase):
    def test_enumeration_membership_and_equality(self) -> None:
        empty = run(Request(ask="what is {}", seed=1))
        self.assertEqual(empty.claims[0].atom, "set({})")
        self.assertIn("set({}) is the finite set", empty.text(lod=1))
        self.assertIn("empty_iff", empty.text(lod=2))
        self.assertIn("finite.emptyI", empty.text(lod=2))
        self.assertNotIn("set({})", empty.text(lod=0))
        self.assertEqual(empty.open_gaps, ())

        numbers = run(Request(ask="what is {2, 2, 1}", seed=1))
        self.assertEqual(numbers.claims[0].atom, "set({1, 2})")
        self.assertIn("insert_absorb", numbers.text(lod=2))
        self.assertEqual(numbers.open_gaps, ())

        fractions = run(Request(ask="what is {1/2, 1/3}", seed=1))
        self.assertEqual(fractions.claims[0].atom, "set({1/3, 1/2})")

        same = run(Request(ask="what is {sqrt(8), 2 * sqrt(2)}", seed=1))
        self.assertEqual(same.claims[0].atom, "set({2 * sqrt(2)})")

        inside = run(Request(ask="prove 2 in {1, 2}", seed=1))
        self.assertEqual(inside.claims[0].atom, "member(2,{1, 2})")
        self.assertIn("member(2,{1, 2}) holds", inside.text(lod=1))
        self.assertIn("insert_iff", inside.text(lod=2))
        self.assertEqual(inside.open_gaps, ())

        outside = run(Request(ask="prove 3 in {1, 2}", seed=1))
        self.assertEqual(outside.claims[0].atom, "not_member(3,{1, 2})")
        self.assertIn("not_member(3,{1, 2}) holds", outside.text(lod=1))

        radical = run(Request(ask="prove sqrt(8) in {2 * sqrt(2)}", seed=1))
        self.assertEqual(radical.claims[0].atom, "member(sqrt(8),{2 * sqrt(2)})")
        self.assertIn("singleton_iff", radical.text(lod=2))

        equal = run(Request(ask="prove {1, 2} = {2, 1, 1}", seed=1))
        self.assertEqual(equal.claims[0].atom, "identity({1, 2} = {2, 1, 1})")
        self.assertIn("set_eqI", equal.text(lod=2))
        self.assertEqual(equal.open_gaps, ())
        self.assertFalse(any(claim.atom.startswith("value(") for claim in equal.claims))

        unequal = run(Request(ask="prove {1} = {2}", seed=1))
        self.assertIn("is not a theorem", unequal.text(lod=1))
        self.assertIn("outside the right set", unequal.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("identity(") for claim in unequal.claims))
        self.assertTrue(unequal.open_gaps)

    def test_union_intersection_and_subset(self) -> None:
        union = run(Request(ask="what is {1, 2} union {2, 3}", seed=1))
        self.assertEqual(union.claims[0].atom, "set({1, 2, 3})")
        self.assertIn("Un_iff", union.text(lod=2))
        self.assertIn("finite_Un", union.text(lod=2))
        self.assertEqual(union.open_gaps, ())

        chained = run(Request(ask="what is {1} union {2} union {3}", seed=1))
        self.assertEqual(chained.claims[0].atom, "set({1, 2, 3})")

        shared = run(Request(ask="what is {1, 2} inter {2, 3}", seed=1))
        self.assertEqual(shared.claims[0].atom, "set({2})")
        self.assertIn("Int_iff", shared.text(lod=2))

        with_empty = run(Request(ask="what is {} union {1}", seed=1))
        self.assertEqual(with_empty.claims[0].atom, "set({1})")

        contained = run(Request(ask="prove {1} subset {1, 2}", seed=1))
        self.assertEqual(contained.claims[0].atom, "subset({1},{1, 2})")
        self.assertIn("subset_eq", contained.text(lod=2))
        self.assertEqual(contained.open_gaps, ())

        empty_side = run(Request(ask="prove {} subset {1}", seed=1))
        self.assertEqual(empty_side.claims[0].atom, "subset({},{1})")
        self.assertIn("empty_subsetI", empty_side.text(lod=2))

        spilled = run(Request(ask="prove {1, 3} subset {1, 2}", seed=1))
        self.assertEqual(spilled.claims[0].atom, "not_subset({1, 3},{1, 2})")
        self.assertIn("not_subset({1, 3},{1, 2}) holds", spilled.text(lod=1))

    def test_least_upper_bound_is_the_maximum(self) -> None:
        bound = run(Request(ask="what is sup {1, 2, sqrt(2)}", seed=1))
        self.assertEqual(bound.claims[0].atom, "value(2)")
        detail = bound.text(lod=2)
        self.assertIn("complete_real", detail)
        self.assertIn("cSup_eq_maximum", detail)
        self.assertIn("cSup_eq_Max", detail)
        self.assertIn("Max_in", detail)
        self.assertIn("Max_ge", detail)
        self.assertIn("bdd_aboveI", detail)
        self.assertIn("arbitrary set", detail)
        self.assertEqual(bound.open_gaps, ())

        radical = run(Request(ask="what is sup {1, sqrt(2)}", seed=1))
        self.assertEqual(radical.claims[0].atom, "cauchy(sqrt(2))")
        self.assertIn("cauchy(sqrt(2)) is the constructed real", radical.text(lod=1))
        self.assertNotIn("cauchy(sqrt(2))", radical.text(lod=0))

        larger = run(Request(ask="what is sup {sqrt(2), sqrt(8)}", seed=1))
        self.assertEqual(larger.claims[0].atom, "cauchy(2 * sqrt(2))")

        half = run(Request(ask="what is sup {1/3, 1/2}", seed=1))
        self.assertEqual(half.claims[0].atom, "ratio(1,2)")
        self.assertIn("is the exact rational", half.text(lod=1))

        single = run(Request(ask="what is sup {sqrt(2)}", seed=1))
        self.assertEqual(single.claims[0].atom, "cauchy(sqrt(2))")
        self.assertIn("cSup_singleton", single.text(lod=2))

        proved = run(Request(ask="prove sup {1, sqrt(2)} = sqrt(2)", seed=1))
        self.assertEqual(proved.claims[0].atom, "identity(sup {1, sqrt(2)} = sqrt(2))")
        self.assertIn("cSup_eq_maximum", proved.text(lod=2))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in proved.claims))
        self.assertEqual(proved.open_gaps, ())

        missed = run(Request(ask="prove sup {1, 2} = 3", seed=1))
        self.assertIn("is not a theorem", missed.text(lod=1))
        self.assertFalse(any(claim.atom.startswith(("identity(", "value(")) for claim in missed.claims))

    def test_open_sets_stay_open(self) -> None:
        empty = run(Request(ask="what is sup {}", seed=1))
        self.assertIn("complete_real assumes a member", empty.text(lod=1))
        self.assertEqual(_settled_atoms(empty), ())
        self.assertTrue(empty.open_gaps)

        negative = run(Request(ask="what is {sqrt(-2)}", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertEqual(_settled_atoms(negative), ())

        nested = run(Request(ask="what is {sqrt(sqrt(2))}", seed=1))
        self.assertEqual(nested.claims[0].atom, "set({sqrt(sqrt(2))})")
        self.assertEqual(nested.open_gaps, ())

        zero = run(Request(ask="what is {1 / 0}", seed=1))
        self.assertIn("division by zero", zero.text(lod=1))
        self.assertEqual(_settled_atoms(zero), ())

        added = run(Request(ask="what is 1 + {2}", seed=1))
        self.assertIn("a set does not enter this operation", added.text(lod=1))
        self.assertEqual(_settled_atoms(added), ())

        free = run(Request(ask="what is {x}", seed=1))
        self.assertEqual(free.claims, ())
        self.assertIn("No answer rule fired from the given facts.", free.open_gaps)

        order = run(Request(ask="prove {1} <= {2}", seed=1))
        self.assertIn("is not a theorem", order.text(lod=1))
        self.assertEqual(_settled_atoms(order), ())

        mixed = run(Request(ask="prove {1} = 1", seed=1))
        self.assertIn("different objects", mixed.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("identity(") for claim in mixed.claims))

    def test_anchors_enter_and_clashes_retract(self) -> None:
        measured = run(Request(ask="what is {length, 1}", facts=("length=4@meter stick",), seed=1))
        self.assertEqual(measured.claims[0].atom, "set({1, 4})")
        self.assertIn("meter stick", measured.text(lod=2))
        self.assertEqual(measured.open_gaps, ())

        bound = run(Request(ask="what is sup {length}", facts=("length=4@meter stick",), seed=1))
        self.assertEqual(bound.claims[0].atom, "value(4)")
        self.assertIn("meter stick", bound.text(lod=2))
        self.assertIn("cSup_singleton", bound.text(lod=2))

        member = run(Request(ask="prove length in {4, 9}", facts=("length=4@meter stick",), seed=1))
        self.assertEqual(member.claims[0].atom, "member(length,{4, 9})")
        self.assertIn("meter stick", member.text(lod=2))

        clash = run(
            Request(
                ask="what is {length}",
                facts=("length=4@left stick", "length=5@right stick"),
                seed=1,
            )
        )
        self.assertIn("value(4)", clash.retracted)
        self.assertIn("value(5)", clash.retracted)
        self.assertNotIn("set(", clash.text(lod=2))
        self.assertIn("Contested claims blocked a settled answer.", clash.open_gaps)

    def test_older_paths_stay_on_their_rules(self) -> None:
        root = run(Request(ask="what is sqrt(2)", seed=1))
        self.assertEqual(root.claims[0].atom, "cauchy(sqrt(2))")
        self.assertNotIn("complete_real", root.text(lod=2))

        ratio = run(Request(ask="what is 8 / 3", seed=1))
        self.assertEqual(ratio.claims[0].atom, "ratio(8,3)")

        quotient = run(Request(ask="what is 8 / 2", seed=1))
        self.assertEqual(quotient.claims[0].atom, "value(4)")
        self.assertIn("Int.ediv", quotient.text(lod=2))

        order = run(Request(ask="prove 2 <= 5", seed=1))
        self.assertEqual(order.claims[0].atom, "le(2,5)")
        self.assertNotIn("cSup", order.text(lod=2))

        rational_order = run(Request(ask="prove 1 / 2 <= 1 / 3", seed=1))
        self.assertEqual(rational_order.claims[0].atom, "not_le(1 / 2,1 / 3)")

        plain = run(Request(ask="what is {1}", seed=1))
        self.assertNotIn("record(", plain.text(lod=2))

    def test_forgery_is_rejected(self) -> None:
        one = real_of_rat(Ratio(1, 1))
        two = real_of_rat(Ratio(2, 1))
        base = set_insert(set_insert(set_empty(), one), two)
        proved = set_sup(base)
        self.assertEqual(proved.form, two.form)
        with self.assertRaises(KernelError):
            SupTheorem(one.form, base.members, base, "Set.sup")
        with self.assertRaises(KernelError):
            SetTheorem((), "Set.insert")
        with self.assertRaises(KernelError):
            MemberTheorem(two.form, base.members, "Set.not_member")
        with self.assertRaises(KernelError):
            EqTheorem(base.members, (one.form,), "Set.eq")
        with self.assertRaises(KernelError):
            MemberTheorem(RealForm(Ratio(2, 4), ()), (RealForm(Ratio(2, 4), ()),), "Set.member")
        with self.assertRaises(NotExact):
            set_sup(set_empty())
