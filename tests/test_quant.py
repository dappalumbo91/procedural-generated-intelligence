from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.kernel import KernelError
from pgi.math.quant import CompleteTheorem, Pred, QuantTheorem
from pgi.math.rational import Ratio
from pgi.math.real import RealForm, real_of_rat
from pgi.math.syntax import IntLit, Var
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


def _quantifier_atoms(session) -> tuple[str, ...]:
    prefixes = ("all(", "not_all(", "ex(", "not_ex(", "complete(")
    return tuple(claim.atom for claim in session.claims if claim.atom.startswith(prefixes))


class QuantifierTests(unittest.TestCase):
    def test_bounded_all_and_ex(self) -> None:
        holds = run(Request(ask="prove all x in {1, 2}. x <= 2", seed=1))
        self.assertEqual(holds.claims[0].atom, "all(x in {1, 2}, x <= 2)")
        self.assertEqual(holds.claims[0].rule_id, "math.ball")
        self.assertIn("all(x in {1, 2}, x <= 2) holds", holds.text(lod=1))
        self.assertIn("ballI", holds.text(lod=2))
        self.assertNotIn("all(x in {1, 2}, x <= 2)", holds.text(lod=0))
        self.assertEqual(holds.open_gaps, ())

        reflexive = run(Request(ask="prove all x in {1, 2}. x <= x", seed=1))
        self.assertEqual(reflexive.claims[0].atom, "all(x in {1, 2}, x <= x)")
        self.assertEqual(reflexive.open_gaps, ())

        fails = run(Request(ask="prove all x in {1, 2, 3}. x <= 1", seed=1))
        self.assertEqual(fails.claims[0].atom, "not_all(x in {1, 2, 3}, x <= 1)")
        self.assertEqual(fails.claims[0].rule_id, "math.not_ball")
        self.assertIn("The counterexample is 2.", fails.text(lod=2))
        self.assertIn("ball_simps", fails.text(lod=2))
        self.assertIn("not_all(x in {1, 2, 3}, x <= 1) holds", fails.text(lod=1))
        self.assertEqual(fails.open_gaps, ())

        witness = run(Request(ask="prove ex x in {1, 3, 2}. x = 2", seed=1))
        self.assertEqual(witness.claims[0].atom, "ex(x in {1, 2, 3}, x = 2)")
        self.assertEqual(witness.claims[0].rule_id, "math.bex")
        self.assertIn("The witness is 2.", witness.text(lod=2))
        self.assertIn("bexI", witness.text(lod=2))
        self.assertEqual(witness.open_gaps, ())

        same = run(Request(ask="prove ex x in {sqrt(8)}. x = 2 * sqrt(2)", seed=1))
        self.assertEqual(same.claims[0].atom, "ex(x in {2 * sqrt(2)}, x = 2 * sqrt(2))")
        self.assertEqual(same.open_gaps, ())

        missing = run(Request(ask="prove ex x in {1, 2}. x = 4", seed=1))
        self.assertEqual(missing.claims[0].atom, "not_ex(x in {1, 2}, x = 4)")
        self.assertEqual(missing.claims[0].rule_id, "math.not_bex")
        self.assertIn("bex_simps", missing.text(lod=2))
        self.assertEqual(missing.open_gaps, ())

    def test_empty_bounds_are_vacuous(self) -> None:
        universal = run(Request(ask="prove all x in {}. x / 0 <= 1", seed=1))
        self.assertEqual(universal.claims[0].atom, "all(x in {}, x / 0 <= 1)")
        self.assertIn("ball_empty", universal.text(lod=2))
        self.assertIn("The body is not evaluated.", universal.text(lod=2))
        self.assertNotIn("division by zero", universal.text(lod=2))
        self.assertEqual(universal.open_gaps, ())

        existential = run(Request(ask="prove ex x in {}. x / 0 <= 1", seed=1))
        self.assertEqual(existential.claims[0].atom, "not_ex(x in {}, x / 0 <= 1)")
        self.assertIn("bex_empty", existential.text(lod=2))
        self.assertIn("The body is not evaluated.", existential.text(lod=2))
        self.assertNotIn("division by zero", existential.text(lod=2))
        self.assertEqual(existential.open_gaps, ())

    def test_finite_completeness_uses_the_maximum(self) -> None:
        bound = run(Request(ask="prove complete {1, sqrt(2)}", seed=1))
        self.assertEqual(bound.claims[0].atom, "complete({1, sqrt(2)})")
        self.assertEqual(bound.claims[0].rule_id, "math.complete")
        self.assertIn("sqrt(2) is the least upper bound of {1, sqrt(2)}", bound.text(lod=1))
        self.assertIn("complete({1, sqrt(2)}) is the least upper bound of this finite set", bound.text(lod=1))
        detail = bound.text(lod=2)
        self.assertIn("complete_real", detail)
        self.assertIn("ballI", detail)
        self.assertIn("bspec", detail)
        self.assertIn("Max_le_iff", detail)
        self.assertIn("Max_in", detail)
        self.assertIn("cSup_eq_maximum", detail)
        self.assertIn("cSup_eq_Max", detail)
        self.assertIn("The witness is the class sqrt(2).", detail)
        self.assertIn("arbitrary set", detail)
        self.assertNotIn("complete({1, sqrt(2)})", bound.text(lod=0))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in bound.claims))
        self.assertEqual(bound.open_gaps, ())

        ordered = run(Request(ask="prove complete {sqrt(2), 1}", seed=1))
        self.assertEqual(ordered.claims[0].atom, "complete({1, sqrt(2)})")

        numbers = run(Request(ask="prove complete {2, 1}", seed=1))
        self.assertEqual(numbers.claims[0].atom, "complete({1, 2})")
        self.assertIn("The witness is 2.", numbers.text(lod=2))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in numbers.claims))

        single = run(Request(ask="prove complete {sqrt(2)}", seed=1))
        self.assertEqual(single.claims[0].atom, "complete({sqrt(2)})")
        self.assertIn("cSup_singleton", single.text(lod=2))

        union = run(Request(ask="prove complete {1} union {2}", seed=1))
        self.assertEqual(union.claims[0].atom, "complete({1, 2})")

        empty = run(Request(ask="prove complete {}", seed=1))
        self.assertIn("complete_real assumes a member. The empty set has none", empty.text(lod=1))
        self.assertEqual(_quantifier_atoms(empty), ())
        self.assertTrue(empty.open_gaps)

    def test_leastness_follows_membership(self) -> None:
        holds = run(Request(ask="prove all z. (all x in {1, 2}. x <= z) --> 2 <= z", seed=1))
        self.assertEqual(holds.claims[0].atom, "all(z, (all x in {1, 2}, x <= z) --> 2 <= z)")
        detail = holds.text(lod=2)
        self.assertIn("impI", detail)
        self.assertIn("allI", detail)
        self.assertIn("bspec", detail)
        self.assertFalse(any(claim.atom.startswith("value(") for claim in holds.claims))
        self.assertEqual(holds.open_gaps, ())

        refuted = run(Request(ask="prove all z. (all x in {1, 2}. x <= z) --> 3 <= z", seed=1))
        self.assertEqual(refuted.claims[0].atom, "not_all(z, (all x in {1, 2}, x <= z) --> 3 <= z)")
        self.assertIn("Isabelle spec", refuted.text(lod=2))
        self.assertIn("The witness is 2.", refuted.text(lod=2))
        self.assertEqual(refuted.open_gaps, ())

        below = run(Request(ask="prove all z. (all x in {1, 2}. x <= z) --> 0 <= z", seed=1))
        self.assertIn("this leastness statement stays open", below.text(lod=1))
        self.assertEqual(_quantifier_atoms(below), ())
        self.assertTrue(below.open_gaps)

        vacant = run(Request(ask="prove all z. (all x in {}. x <= z) --> 0 <= z", seed=1))
        self.assertIn("vacuous", vacant.text(lod=1))
        self.assertEqual(_quantifier_atoms(vacant), ())
        self.assertTrue(vacant.open_gaps)

    def test_unbounded_quantifiers_stay_open_without_a_uniform_reason(self) -> None:
        reflexive = run(Request(ask="prove all x. x <= x", seed=1))
        self.assertEqual(reflexive.claims[0].atom, "all(x, x <= x)")
        self.assertIn("allI", reflexive.text(lod=2))
        self.assertIn("refl", reflexive.text(lod=2))
        self.assertEqual(reflexive.open_gaps, ())

        same = run(Request(ask="prove all x. x = x", seed=1))
        self.assertEqual(same.claims[0].atom, "all(x, x = x)")
        self.assertEqual(same.open_gaps, ())

        exists = run(Request(ask="prove ex x. x = x", seed=1))
        self.assertEqual(exists.claims[0].atom, "ex(x, x = x)")
        self.assertIn("exI", exists.text(lod=2))
        self.assertIn("The witness is 0.", exists.text(lod=2))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in exists.claims))
        self.assertEqual(exists.open_gaps, ())

        order = run(Request(ask="prove ex x. x <= x", seed=1))
        self.assertEqual(order.claims[0].atom, "ex(x, x <= x)")
        self.assertEqual(order.open_gaps, ())

        named = run(Request(ask="prove ex x. x = 1 + 1", seed=1))
        self.assertEqual(named.claims[0].atom, "ex(x, x = 1 + 1)")
        self.assertIn("The witness is 2.", named.text(lod=2))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in named.claims))

        radical = run(Request(ask="prove ex x. sqrt(2) = x", seed=1))
        self.assertEqual(radical.claims[0].atom, "ex(x, sqrt(2) = x)")
        self.assertIn("The witness is sqrt(2).", radical.text(lod=2))
        self.assertFalse(any(claim.atom.startswith(("value(", "cauchy(")) for claim in radical.claims))

        capped = run(Request(ask="prove all x. x <= 1", seed=1))
        self.assertIn("this unbounded quantifier is not settled", capped.text(lod=1))
        self.assertEqual(_quantifier_atoms(capped), ())
        self.assertTrue(capped.open_gaps)

        searched = run(Request(ask="prove ex x. x <= 5", seed=1))
        self.assertIn("this unbounded quantifier is not settled", searched.text(lod=1))
        self.assertEqual(_quantifier_atoms(searched), ())
        self.assertTrue(searched.open_gaps)

    def test_free_variables_sets_and_open_expressions_stay_notes(self) -> None:
        free = run(Request(ask="prove all x in {1}. y <= x", seed=1))
        self.assertIn("free variable", free.text(lod=1))
        self.assertEqual(_quantifier_atoms(free), ())

        operand = run(Request(ask="prove all x in {1}. x <= {2}", seed=1))
        self.assertIn("a set does not enter this quantifier", operand.text(lod=1))
        self.assertEqual(_quantifier_atoms(operand), ())

        zero = run(Request(ask="prove all x in {1 / 0}. x <= 1", seed=1))
        self.assertIn("division by zero", zero.text(lod=1))
        self.assertEqual(_quantifier_atoms(zero), ())

        negative = run(Request(ask="prove all x in {sqrt(-2)}. x <= 1", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertEqual(_quantifier_atoms(negative), ())

        nested = run(Request(ask="prove all x in {1}. sqrt(sqrt(2)) <= x", seed=1))
        self.assertEqual(nested.claims[0].atom, "not_all(x in {1}, sqrt(sqrt(2)) <= x)")
        self.assertIn("The counterexample is 1.", nested.text(lod=2))
        self.assertEqual(nested.open_gaps, ())

        gap = run(Request(ask="what is all x in {1}. x <= 1", seed=1))
        self.assertEqual(gap.claims, ())
        self.assertIn("No answer rule fired from the given facts.", gap.open_gaps)

    def test_anchors_shadow_the_binder_and_clashes_retract(self) -> None:
        measured = run(
            Request(
                ask="prove all x in {length}. x <= 4",
                facts=("length=4@meter stick",),
                seed=1,
            )
        )
        self.assertEqual(measured.claims[0].atom, "all(x in {4}, x <= 4)")
        self.assertIn("meter stick", measured.text(lod=2))
        self.assertEqual(measured.open_gaps, ())

        shadowed = run(
            Request(
                ask="prove all x in {1, 2}. x <= 3",
                facts=("x=9@stick",),
                seed=1,
            )
        )
        self.assertEqual(shadowed.claims[0].atom, "all(x in {1, 2}, x <= 3)")
        self.assertNotIn("source stick", " ".join(shadowed.claims[0].detail_lines))
        self.assertNotIn("9", shadowed.claims[0].atom)
        self.assertEqual(shadowed.open_gaps, ())

        clash = run(
            Request(
                ask="prove all x in {length}. x <= 4",
                facts=("length=4@left stick", "length=5@right stick"),
                seed=1,
            )
        )
        self.assertIn("value(4)", clash.retracted)
        self.assertIn("value(5)", clash.retracted)
        self.assertNotIn("all(", clash.text(lod=2))
        self.assertIn("Contested claims blocked a settled answer.", clash.open_gaps)

    def test_older_paths_stay_on_their_rules(self) -> None:
        root = run(Request(ask="what is sqrt(2)", seed=1))
        self.assertEqual(root.claims[0].atom, "cauchy(sqrt(2))")
        self.assertNotIn("ballI", root.text(lod=2))

        order = run(Request(ask="prove 2 <= 5", seed=1))
        self.assertEqual(order.claims[0].atom, "le(2,5)")
        self.assertNotIn("Ball", order.text(lod=2))

        member = run(Request(ask="prove 2 in {1, 2}", seed=1))
        self.assertEqual(member.claims[0].atom, "member(2,{1, 2})")

        enumerated = run(Request(ask="what is {1}", seed=1))
        self.assertEqual(enumerated.claims[0].atom, "set({1})")
        self.assertNotIn("record(", enumerated.text(lod=1))

    def test_forged_quantifiers_are_rejected(self) -> None:
        one = real_of_rat(Ratio(1, 1)).form
        two = real_of_rat(Ratio(2, 1)).form
        bad = RealForm(Ratio(2, 4), ())
        below = Pred("le", Var("x"), IntLit(0))
        above = Pred("le", Var("x"), IntLit(2))
        self.assertRaises(
            KernelError,
            lambda: QuantTheorem("bounded", "all", True, "x", (one,), below, None, None, "Ball.holds"),
        )
        QuantTheorem("bounded", "all", True, "x", (one, two), above, None, None, "Ball.holds")
        self.assertRaises(
            KernelError,
            lambda: QuantTheorem("bounded", "all", False, "x", (one, two), above, one, None, "Ball.fails"),
        )
        self.assertRaises(
            KernelError,
            lambda: CompleteTheorem((one, two), one, "Ball.complete"),
        )
        CompleteTheorem((one, two), two, "Ball.complete")
        self.assertRaises(KernelError, lambda: CompleteTheorem((bad,), bad, "Ball.complete"))
        self.assertRaises(
            KernelError,
            lambda: QuantTheorem("least", "all", True, "z", (one, two), None, None, bad, "Ball.least"),
        )
        QuantTheorem("least", "all", True, "z", (one, two), None, None, two, "Ball.least")
