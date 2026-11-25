from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.collect import CollectCongTheorem, CollectMemberTheorem, CollectSubsetTheorem
from pgi.math.kernel import KernelError
from pgi.math.rational import Ratio
from pgi.math.real import RealForm, real_of_rat
from pgi.math.set import SetTheorem, set_empty, set_insert
from pgi.math.syntax import IntLit, Var, parse_term
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


def _atoms(session, prefix: str) -> tuple[str, ...]:
    return tuple(claim.atom for claim in session.claims if claim.atom.startswith(prefix))


class ComprehensionTests(unittest.TestCase):
    def test_separation_filters_a_finite_enumeration(self) -> None:
        kept = run(Request(ask="what is {x in {1, 2, 3}. x <= 2}", seed=1))
        self.assertEqual(kept.claims[0].atom, "set({1, 2})")
        self.assertIn("Collect", kept.text(lod=2))
        self.assertIn("Collect_subset", kept.text(lod=2))
        self.assertIn("finite_subset", kept.text(lod=2))
        self.assertNotIn("set({1, 2})", kept.text(lod=0))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in kept.claims))
        self.assertEqual(kept.open_gaps, ())

        named = run(Request(ask="what is {x in {1, 2, 3}. x = 2}", seed=1))
        self.assertEqual(named.claims[0].atom, "set({2})")
        self.assertIn("mem_Collect_eq", named.text(lod=2))
        self.assertEqual(named.open_gaps, ())

        none = run(Request(ask="what is {x in {1, 2}. x <= 0}", seed=1))
        self.assertEqual(none.claims[0].atom, "set({})")
        self.assertEqual(none.claims[0].rule_id, "math.set.empty")
        self.assertIn("No member satisfies the predicate.", none.text(lod=2))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in none.claims))
        self.assertEqual(none.open_gaps, ())

        equal = run(Request(ask="prove {x in {1, 2, 3}. x <= 2} = {1, 2}", seed=1))
        self.assertEqual(equal.claims[0].atom, "identity({x in {1, 2, 3}. x <= 2} = {1, 2})")
        self.assertIn("set_eqI", equal.text(lod=2))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in equal.claims))
        self.assertEqual(equal.open_gaps, ())

        inside = run(Request(ask="prove 1 in {x in {1, 2, 3}. x <= 2}", seed=1))
        self.assertEqual(inside.claims[0].atom, "member(1,{x in {1, 2, 3}. x <= 2})")
        self.assertIn("member(1,{x in {1, 2, 3}. x <= 2}) holds", inside.text(lod=1))
        self.assertEqual(inside.open_gaps, ())

        covered = run(Request(ask="prove {x in {1, 2, 3}. x <= 2} subset {1, 2, 3}", seed=1))
        self.assertEqual(covered.claims[0].atom, "subset({x in {1, 2, 3}. x <= 2},{1, 2, 3})")
        self.assertEqual(covered.open_gaps, ())

        nested = run(Request(ask="what is {x in {y in {1, 2, 3}. y <= 2}. x = 1}", seed=1))
        self.assertEqual(nested.claims[0].atom, "set({1})")
        self.assertEqual(nested.open_gaps, ())

    def test_empty_domain_does_not_evaluate_the_body(self) -> None:
        vacuous = run(Request(ask="what is {x in {}. x / 0 <= 1}", seed=1))
        self.assertEqual(vacuous.claims[0].atom, "set({})")
        self.assertIn("The body is not evaluated.", vacuous.text(lod=2))
        self.assertNotIn("division by zero", vacuous.text(lod=2))
        self.assertEqual(vacuous.open_gaps, ())

        operand = run(Request(ask="what is {x in {1, 2}. x <= {1}}", seed=1))
        self.assertIn("a set does not enter this comprehension", operand.text(lod=1))
        self.assertEqual(_atoms(operand, "set("), ())

        zero = run(Request(ask="what is {x in {1 / 0}. x <= 1}", seed=1))
        self.assertIn("division by zero", zero.text(lod=1))
        self.assertEqual(_atoms(zero, "set("), ())

        negative = run(Request(ask="what is {x in {sqrt(-2)}. x <= 1}", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertEqual(_atoms(negative, "set("), ())

        nested = run(Request(ask="what is {x in {1}. sqrt(sqrt(2)) <= x}", seed=1))
        self.assertEqual(nested.claims[0].atom, "set({})")
        self.assertEqual(nested.open_gaps, ())

    def test_singleton_equality_is_the_element(self) -> None:
        number = run(Request(ask="what is {x. x = 2}", seed=1))
        self.assertEqual(number.claims[0].atom, "set({2})")
        self.assertIn("singleton_conv", number.text(lod=2))
        self.assertFalse(any(claim.atom.startswith(("value(", "cauchy(")) for claim in number.claims))
        self.assertEqual(number.open_gaps, ())

        radical = run(Request(ask="what is {x. sqrt(2) = x}", seed=1))
        self.assertEqual(radical.claims[0].atom, "set({sqrt(2)})")
        self.assertIn("singleton_conv2", radical.text(lod=2))
        self.assertFalse(any(claim.atom.startswith(("value(", "cauchy(")) for claim in radical.claims))
        self.assertEqual(radical.open_gaps, ())

        summed = run(Request(ask="what is {x. x = 1 + 1}", seed=1))
        self.assertEqual(summed.claims[0].atom, "set({2})")
        self.assertIn("{x. x = 1 + 1}", summed.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in summed.claims))
        self.assertEqual(summed.open_gaps, ())

        zero = run(Request(ask="what is {x. x = 1 / 0}", seed=1))
        self.assertIn("division by zero", zero.text(lod=1))
        self.assertEqual(_atoms(zero, "set("), ())

        negative = run(Request(ask="what is {x. x = sqrt(-2)}", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertEqual(_atoms(negative, "set("), ())

    def test_unbounded_predicates_stay_open(self) -> None:
        compound = run(Request(ask="what is {x. x <= x + 1}", seed=1))
        self.assertEqual(compound.claims[0].atom, "univ")
        self.assertEqual(compound.open_gaps, ())

        quadratic = run(Request(ask="what is {x. x * x <= 2}", seed=1))
        self.assertEqual(quadratic.claims[0].atom, "atLeastAtMost(-sqrt(2), sqrt(2))")
        self.assertEqual(quadratic.open_gaps, ())

        cubic = run(Request(ask="what is {x. x * x * x <= 2}", seed=1))
        self.assertEqual(cubic.claims[0].atom, "atMost(root(x^3 - 2, 1))")
        self.assertEqual(cubic.open_gaps, ())

        broken = run(Request(ask="what is {x. x / 0 <= 1}", seed=1))
        self.assertIn("this comprehension is not a finite enumeration", broken.text(lod=1))
        self.assertNotIn("division by zero", broken.text(lod=1))
        self.assertEqual(_atoms(broken, "atMost("), ())

        below = run(Request(ask="prove 1 in {x. x <= 5}", seed=1))
        self.assertEqual(below.claims[0].atom, "member(1,{x. x <= 5})")
        self.assertIn("CollectI", below.text(lod=2))
        self.assertEqual(below.open_gaps, ())

        above = run(Request(ask="prove 9 in {x. x <= 5}", seed=1))
        self.assertEqual(above.claims[0].atom, "not_member(9,{x. x <= 5})")
        self.assertIn("CollectD", above.text(lod=2))
        self.assertEqual(above.open_gaps, ())

        contained = run(Request(ask="prove {1} subset {x. x <= 5}", seed=1))
        self.assertEqual(contained.claims[0].atom, "subset({1},{x. x <= 5})")
        self.assertEqual(contained.open_gaps, ())

        spilled = run(Request(ask="prove {1, 9} subset {x. x <= 5}", seed=1))
        self.assertEqual(spilled.claims[0].atom, "not_subset({1, 9},{x. x <= 5})")
        self.assertIn("9", spilled.text(lod=2))
        self.assertEqual(spilled.open_gaps, ())

        vacuous = run(Request(ask="prove {} subset {x. x / 0 <= 1}", seed=1))
        self.assertEqual(vacuous.claims[0].atom, "subset({},{x. x / 0 <= 1})")
        self.assertIn("empty_subsetI", vacuous.text(lod=2))
        self.assertNotIn("division by zero", vacuous.text(lod=2))
        self.assertEqual(vacuous.open_gaps, ())

        backward = run(Request(ask="prove {x. x <= 5} subset {1}", seed=1))
        self.assertEqual(backward.claims[0].atom, "not_subset({x. x <= 5},{1})")
        self.assertIn("0", backward.text(lod=2))
        self.assertEqual(backward.open_gaps, ())

        same = run(Request(ask="prove {x. x <= 1 + 1} = {x. x <= 2}", seed=1))
        self.assertEqual(same.claims[0].atom, "identity({x. x <= 1 + 1} = {x. x <= 2})")
        self.assertIn("Collect_cong", same.text(lod=2))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in same.claims))
        self.assertEqual(same.open_gaps, ())

        renamed = run(Request(ask="prove {x. x <= sqrt(4)} = {y. y <= 2}", seed=1))
        self.assertEqual(renamed.claims[0].atom, "identity({x. x <= sqrt(4)} = {y. y <= 2})")
        self.assertEqual(renamed.open_gaps, ())

        different = run(Request(ask="prove {x. x <= 1} = {x. x <= 2}", seed=1))
        self.assertIn("is not a theorem", different.text(lod=1))
        self.assertIn("2", different.text(lod=1))
        self.assertEqual(_atoms(different, "identity("), ())

        witness = run(Request(ask="prove {1, 9} = {x. x <= 2}", seed=1))
        self.assertIn("is not a theorem", witness.text(lod=1))
        self.assertIn("9", witness.text(lod=1))
        self.assertEqual(_atoms(witness, "identity("), ())

        matched = run(Request(ask="prove {1, 2} = {x. x <= 2}", seed=1))
        self.assertIn("outside the finite enumeration", matched.text(lod=1))
        self.assertEqual(_atoms(matched, "identity("), ())

        quantified = run(Request(ask="prove all x in {y. y <= 5}. x <= 5", seed=1))
        self.assertEqual(quantified.claims[0].atom, "all(x in {y. y <= 5}, x <= 5)")
        self.assertEqual(quantified.open_gaps, ())

    def test_sup_complete_and_quantifier_use_the_separation(self) -> None:
        radical = run(Request(ask="what is sup {x in {1, sqrt(2), 3}. x <= 2}", seed=1))
        self.assertEqual(radical.claims[0].atom, "cauchy(sqrt(2))")
        self.assertFalse(any(claim.atom.startswith("value(") for claim in radical.claims))
        self.assertEqual(radical.open_gaps, ())

        integer = run(Request(ask="what is sup {x in {1, 2, 3}. x <= 2}", seed=1))
        self.assertEqual(integer.claims[0].atom, "value(2)")
        self.assertEqual(integer.open_gaps, ())

        bound = run(Request(ask="prove complete {x in {1, sqrt(2)}. x <= 2}", seed=1))
        self.assertEqual(bound.claims[0].atom, "complete({1, sqrt(2)})")
        self.assertFalse(any(claim.atom.startswith("value(") for claim in bound.claims))
        self.assertEqual(bound.open_gaps, ())

        trimmed = run(Request(ask="prove complete {x in {1, sqrt(2), 4}. x <= 2}", seed=1))
        self.assertEqual(trimmed.claims[0].atom, "complete({1, sqrt(2)})")
        self.assertFalse(any(claim.atom.startswith("value(") for claim in trimmed.claims))
        self.assertEqual(trimmed.open_gaps, ())

        universal = run(Request(ask="prove all x in {y in {1, 2, 3}. y <= 2}. x <= 2", seed=1))
        self.assertEqual(universal.claims[0].atom, "all(x in {1, 2}, x <= 2)")
        self.assertEqual(universal.open_gaps, ())

    def test_anchors_shadow_the_binder_and_clashes_retract(self) -> None:
        measured = run(
            Request(
                ask="what is {x in {length, 1}. x <= 4}",
                facts=("length=4@meter stick",),
                seed=1,
            )
        )
        self.assertEqual(measured.claims[0].atom, "set({1, 4})")
        self.assertIn("meter stick", measured.text(lod=2))
        self.assertEqual(measured.open_gaps, ())

        member = run(
            Request(
                ask="prove 4 in {x. x <= length}",
                facts=("length=5@meter stick",),
                seed=1,
            )
        )
        self.assertEqual(member.claims[0].atom, "member(4,{x. x <= length})")
        self.assertIn("meter stick", member.text(lod=2))
        self.assertEqual(member.open_gaps, ())

        shadowed = run(
            Request(
                ask="prove 1 in {x in {1, 2}. x <= 3}",
                facts=("x=9@stick",),
                seed=1,
            )
        )
        self.assertEqual(shadowed.claims[0].atom, "member(1,{x in {1, 2}. x <= 3})")
        self.assertNotIn("source stick", " ".join(shadowed.claims[0].detail_lines))
        self.assertNotIn("9", shadowed.claims[0].atom)
        self.assertEqual(shadowed.open_gaps, ())

        clash = run(
            Request(
                ask="what is {x in {length, 1}. x <= 4}",
                facts=("length=4@left stick", "length=5@right stick"),
                seed=1,
            )
        )
        self.assertIn("value(4)", clash.retracted)
        self.assertIn("value(5)", clash.retracted)
        self.assertEqual(_atoms(clash, "set("), ())
        self.assertIn("Contested claims blocked a settled answer.", clash.open_gaps)

        free = run(Request(ask="what is {x in {1}. y <= 1}", seed=1))
        self.assertIn("a free variable stays open", free.text(lod=1))
        self.assertEqual(_atoms(free, "set("), ())

        outside = run(Request(ask="prove y in {x. x <= 1}", seed=1))
        self.assertIn("a free variable stays open", outside.text(lod=1))
        self.assertEqual(_atoms(outside, "member("), ())

        inside = run(Request(ask="prove 1 in {x. y <= x}", seed=1))
        self.assertIn("a free variable stays open", inside.text(lod=1))
        self.assertEqual(_atoms(inside, "member("), ())

    def test_open_comparison_does_not_emit_a_partial_subset(self) -> None:
        import pgi.math.quant as quant

        original = quant.compare_reals

        def _open(left, right):
            if left == right:
                return "eq"
            return "open"

        quant.compare_reals = _open
        try:
            session = run(Request(ask="what is {x in {1, 2}. x <= 2}", seed=1))
        finally:
            quant.compare_reals = original
        self.assertIn("this comprehension is not settled", session.text(lod=1))
        self.assertEqual(_atoms(session, "set("), ())

    def test_forged_comprehensions_are_rejected(self) -> None:
        one = real_of_rat(Ratio(1, 1))
        two = real_of_rat(Ratio(2, 1))
        domain = set_insert(set_insert(set_empty(), one), two)
        both = SetTheorem(
            domain.members,
            "Set.collect",
            (domain,),
            None,
            None,
            (),
            binder="x",
            relation="le",
            left=Var("x"),
            right=IntLit(2),
        )
        self.assertEqual(both.members, domain.members)
        only = SetTheorem(
            (one.form,),
            "Set.collect",
            (domain,),
            None,
            None,
            (),
            binder="x",
            relation="le",
            left=Var("x"),
            right=IntLit(1),
        )
        self.assertEqual(only.members, (one.form,))
        empty = SetTheorem(
            (),
            "Set.collect",
            (domain,),
            None,
            None,
            (),
            binder="x",
            relation="le",
            left=Var("x"),
            right=IntLit(0),
        )
        self.assertEqual(empty.members, ())
        with self.assertRaises(KernelError):
            SetTheorem(
                domain.members,
                "Set.collect",
                (domain,),
                None,
                None,
                (),
                binder="x",
                relation="le",
                left=Var("x"),
                right=IntLit(1),
            )
        with self.assertRaises(KernelError):
            SetTheorem(
                (RealForm(Ratio(2, 4), ()),),
                "Set.singleton",
                (),
                real_of_rat(Ratio(1, 2)),
                None,
                (),
                binder="x",
                relation="eq",
                left=Var("x"),
                right=IntLit(1),
            )
        with self.assertRaises(KernelError):
            SetTheorem(
                (two.form,),
                "Set.singleton",
                (),
                two,
                None,
                (),
                binder="x",
                relation="eq",
                left=Var("x"),
                right=IntLit(1),
            )
        held = SetTheorem(
            (two.form,),
            "Set.singleton",
            (),
            two,
            None,
            (),
            binder="x",
            relation="eq",
            left=Var("x"),
            right=IntLit(2),
        )
        self.assertEqual(held.members, (two.form,))
        with self.assertRaises(KernelError):
            CollectMemberTheorem(real_of_rat(Ratio(9, 1)).form, "x", "le", Var("x"), IntLit(5), "Collect.member")
        with self.assertRaises(KernelError):
            CollectMemberTheorem(RealForm(Ratio(2, 4), ()), "x", "le", Var("x"), IntLit(1), "Collect.member")
        with self.assertRaises(KernelError):
            CollectSubsetTheorem(domain.members, "x", "le", Var("x"), IntLit(0), None, "Collect.subset")
        with self.assertRaises(KernelError):
            CollectCongTheorem("x", "le", Var("x"), IntLit(1), "x", "le", Var("x"), IntLit(2), "Collect.cong")

    def test_older_paths_stay_on_their_rules(self) -> None:
        enumerated = run(Request(ask="what is {1, 2}", seed=1))
        self.assertEqual(enumerated.claims[0].atom, "set({1, 2})")
        self.assertNotIn("Collect", enumerated.text(lod=2))

        root = run(Request(ask="what is sqrt(2)", seed=1))
        self.assertEqual(root.claims[0].atom, "cauchy(sqrt(2))")
        self.assertNotIn("Collect", root.text(lod=2))

        member = run(Request(ask="prove 2 in {1, 2}", seed=1))
        self.assertEqual(member.claims[0].atom, "member(2,{1, 2})")

        bare = run(Request(ask="what is {1}", seed=1))
        self.assertEqual(bare.claims[0].atom, "set({1})")
        self.assertNotIn("record(", bare.text(lod=1))

        free = run(Request(ask="what is {x}", seed=1))
        self.assertEqual(free.claims, ())
        self.assertIn("No answer rule fired from the given facts.", free.open_gaps)

        universal = run(Request(ask="prove all x in {1, 2}. x <= 2", seed=1))
        self.assertEqual(universal.claims[0].atom, "all(x in {1, 2}, x <= 2)")

        self.assertIsNone(parse_term("1.2"))
        self.assertIsNone(parse_term("{1 in 2}"))
        dotted = run(Request(ask="what is 1.2", seed=1))
        self.assertEqual(dotted.claims, ())
        self.assertIn("No answer rule fired from the given facts.", dotted.open_gaps)
