from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.axioms import AXIOMS, LOGIC
from pgi.math.kernel import KernelError, Theorem, anchor, apply_axiom, refl
from pgi.math.octave_check import octave_cli, octave_integers
from pgi.math.rational import Ratio, RatTheorem, rat_normalize
from pgi.math.syntax import App, Eq, IntLit, Var, parse_term
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class MathKernelTests(unittest.TestCase):
    def test_catalog_names_and_each_axiom_checks(self) -> None:
        seen = set()
        for axiom in AXIOMS:
            self.assertTrue(axiom.lean)
            self.assertTrue(axiom.isabelle)
            self.assertTrue(axiom.coq)
            self.assertNotIn(axiom.rule, seen)
            seen.add(axiom.rule)
            sample = _sample(axiom.rule)
            theorem = apply_axiom(axiom, sample)
            self.assertIsNotNone(theorem)
            self.assertEqual(theorem.rule, axiom.rule)
        logic_rules = {row[0] for row in LOGIC}
        self.assertEqual(logic_rules, {"Eq.refl", "Eq.symm", "Eq.trans", "congr"})

    def test_forged_steps_are_rejected(self) -> None:
        with self.assertRaises(KernelError):
            Theorem(Eq(IntLit(1), IntLit(2)), "Eq.refl")
        forged = Eq(App("add", (IntLit(1), IntLit(1))), IntLit(3))
        with self.assertRaises(KernelError):
            Theorem(forged, "Int.add")
        with self.assertRaises(KernelError):
            anchor("length", 4, "  ")

    def test_refl_and_false_equality(self) -> None:
        term = parse_term("1 + 1")
        self.assertIsNotNone(term)
        proven = refl(term)
        self.assertEqual(proven.rule, "Eq.refl")
        refused = run(Request(ask="prove 1 + 1 = 3", seed=1))
        self.assertNotIn("value(3)", [claim.atom for claim in refused.claims])
        self.assertIn("is not a theorem", refused.text(lod=1))
        self.assertTrue(refused.open_gaps)
        accepted = run(Request(ask="prove 1 + 1 = 2", seed=1))
        self.assertEqual(accepted.claims[0].atom, "value(2)")

    def test_precedence_and_exact_division(self) -> None:
        self.assertEqual(run(Request(ask="what is 2 + 3 * 4", seed=1)).claims[0].atom, "value(14)")
        self.assertEqual(run(Request(ask="what is (2 + 3) * 4", seed=1)).claims[0].atom, "value(20)")
        self.assertEqual(run(Request(ask="what is 8 / 2", seed=1)).claims[0].atom, "value(4)")
        self.assertEqual(run(Request(ask="what is 8 / 2 * 2", seed=1)).claims[0].atom, "value(8)")
        uneven = run(Request(ask="what is 8 / 3", seed=1))
        self.assertEqual(uneven.claims[0].atom, "ratio(8,3)")
        self.assertIn("ratio(8,3) is the exact rational", uneven.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in uneven.claims))
        zero = run(Request(ask="what is 8 / 0", seed=1))
        self.assertIn("division by zero", zero.text(lod=1))
        self.assertFalse(any(claim.atom.startswith(("value(", "ratio(")) for claim in zero.claims))

    def test_words_and_negatives_still_reduce(self) -> None:
        session = run(Request(ask="what is 17 plus 13?", seed=1))
        self.assertEqual(session.claims[0].atom, "value(30)")
        negative = run(Request(ask="what is -5 plus 3?", seed=1))
        self.assertEqual(negative.claims[0].atom, "value(-2)")

    def test_ring_identities(self) -> None:
        zero = run(Request(ask="simplify x + 0", seed=1))
        self.assertIn("Int.add_zero", zero.text(lod=2))
        self.assertIn("x + 0 = x", zero.text(lod=1))
        comm = run(Request(ask="prove x + y = y + x", seed=1))
        self.assertIn("Int.add_comm", comm.text(lod=2))
        flipped = run(Request(ask="prove x + (y + z) = (x + y) + z", seed=1))
        self.assertIn("Eq.symm", flipped.text(lod=2))
        self.assertIn("Int.add_assoc", flipped.text(lod=2))
        cancelled = run(Request(ask="what is (x - x) + 1", seed=1))
        self.assertEqual(cancelled.claims[0].atom, "value(1)")
        self.assertIn("Int.sub_eq_add_neg", cancelled.text(lod=2))
        self.assertIn("Int.add_right_neg", cancelled.text(lod=2))

    def test_observables_are_sourced_anchors(self) -> None:
        missing = run(Request(ask="what is length + 1", facts=("length=4",), seed=1))
        self.assertFalse(any(claim.atom.startswith("value(") for claim in missing.claims))
        measured = run(
            Request(ask="what is length * width", facts=("length=4@meter stick", "width=3@meter stick"), seed=1)
        )
        self.assertEqual(measured.claims[0].atom, "value(12)")
        detail = measured.text(lod=2)
        self.assertIn("observable.anchor", detail)
        self.assertIn("meter stick", detail)
        clash = run(
            Request(
                ask="what is length + 0",
                facts=("length=4@first tape", "length=5@second tape"),
                seed=1,
            )
        )
        self.assertEqual(clash.claims, ())
        self.assertIn("value(4)", clash.retracted)
        self.assertIn("value(5)", clash.retracted)
        self.assertIn("Contested claims blocked a settled answer.", clash.open_gaps)

    def test_octave_agrees_on_exact_integers(self) -> None:
        if octave_cli() is None:
            self.skipTest("Octave was not found")
        expressions = ["17+13", "(2+3)*4", "2+3*4", "-5+3", "15-7", "999+1", "8/2", "(17+13)+1"]
        expected = []
        for expression in expressions:
            session = run(Request(ask=expression, seed=1))
            atom = session.claims[0].atom
            self.assertTrue(atom.startswith("value("))
            expected.append(int(atom[len("value(") : -1]))
        self.assertEqual(octave_integers(expressions), expected)


class RationalTests(unittest.TestCase):
    def test_closed_arithmetic_reduces(self) -> None:
        cases = {
            "what is 8 / 6": "ratio(4,3)",
            "what is 2 / 4": "ratio(1,2)",
            "what is 1/2 + 1/3": "ratio(5,6)",
            "what is 1/2 * 2/3": "ratio(1,3)",
            "what is 1/2 - 1/3": "ratio(1,6)",
            "what is -1 / 2": "ratio(-1,2)",
            "what is 8 / -3": "ratio(-8,3)",
        }
        for ask, atom in cases.items():
            session = run(Request(ask=ask, seed=1))
            self.assertEqual(session.claims[0].atom, atom, ask)
            self.assertEqual(session.open_gaps, (), ask)
            self.assertIn("is the exact rational", session.text(lod=1))
            self.assertNotIn("value(", session.text(lod=1))
        reduced = run(Request(ask="what is 8 / 6", seed=1))
        self.assertIn("8/6 = 4/3", reduced.text(lod=2))
        self.assertIn("Lean Rat.div", reduced.text(lod=2))
        added = run(Request(ask="what is 1/2 + 1/3", seed=1))
        self.assertIn("Isabelle add_rat", added.text(lod=2))
        outline = run(Request(ask="what is 8 / 3", seed=1)).text(lod=0)
        self.assertNotIn("ratio(8,3)", outline)

    def test_denominator_one_is_an_integer(self) -> None:
        whole = run(Request(ask="what is (8 / 6) * 3", seed=1))
        self.assertEqual(whole.claims[0].atom, "value(4)")
        self.assertIn("The denominator is 1, so the exact integer is 4.", whole.text(lod=2))
        quotient = run(Request(ask="what is (1 / 2) / (1 / 4)", seed=1))
        self.assertEqual(quotient.claims[0].atom, "value(2)")
        cancelled = run(Request(ask="what is -1 / 2 + 1 / 2", seed=1))
        self.assertEqual(cancelled.claims[0].atom, "value(0)")
        zero = run(Request(ask="what is 0 / 5", seed=1))
        self.assertEqual(zero.claims[0].atom, "value(0)")
        self.assertIn("Int.ediv", zero.text(lod=2))

    def test_division_by_zero_stays_open(self) -> None:
        nested = run(Request(ask="what is (8 / 3) / 0", seed=1))
        self.assertIn("division by zero", nested.text(lod=1))
        self.assertFalse(any(claim.atom.startswith(("value(", "ratio(")) for claim in nested.claims))
        self.assertTrue(nested.open_gaps)

    def test_equality_and_order(self) -> None:
        same = run(Request(ask="prove 2 / 4 = 1 / 2", seed=1))
        self.assertEqual(same.claims[0].atom, "identity(2 / 4 = 1 / 2)")
        self.assertIn("eq_rat", same.text(lod=2))
        self.assertEqual(same.open_gaps, ())
        different = run(Request(ask="prove 1 / 2 = 1 / 3", seed=1))
        self.assertIn("is not a theorem", different.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("identity(") for claim in different.claims))
        held = run(Request(ask="prove 1 / 3 <= 1 / 2", seed=1))
        self.assertEqual(held.claims[0].atom, "le(1 / 3,1 / 2)")
        self.assertIn("le_rat", held.text(lod=2))
        self.assertEqual(held.open_gaps, ())
        refused = run(Request(ask="prove 1 / 2 <= 1 / 3", seed=1))
        self.assertEqual(refused.claims[0].atom, "not_le(1 / 2,1 / 3)")
        self.assertIn("Int.not_le", refused.text(lod=2))
        exact = run(Request(ask="prove 8 / 2 <= 5", seed=1))
        self.assertEqual(exact.claims[0].atom, "le(8 / 2,5)")
        self.assertIn("Int.ediv", exact.text(lod=2))
        self.assertNotIn("le_rat", exact.text(lod=2))
        reflected = run(Request(ask="prove x <= x", seed=1))
        self.assertEqual(reflected.claims[0].atom, "le(x,x)")
        self.assertIn("Int.le_refl", reflected.text(lod=2))
        field = run(Request(ask="prove x / x = 1", seed=1))
        self.assertEqual(field.claims[0].atom, "identity(x / x = 1)")
        self.assertEqual(field.open_gaps, ())

    def test_sourced_anchor_and_a_clash(self) -> None:
        measured = run(Request(ask="what is length / 3", facts=("length=4@meter stick",), seed=1))
        self.assertEqual(measured.claims[0].atom, "ratio(4,3)")
        self.assertIn("meter stick", measured.text(lod=2))
        self.assertEqual(measured.open_gaps, ())
        clash = run(
            Request(
                ask="what is length / 3",
                facts=("length=4@first tape", "length=5@second tape"),
                seed=1,
            )
        )
        self.assertEqual(clash.claims, ())
        self.assertIn("value(4)", clash.retracted)
        self.assertIn("value(5)", clash.retracted)
        self.assertNotIn("ratio(", clash.text(lod=1))

    def test_forged_ratio_is_rejected(self) -> None:
        with self.assertRaises(KernelError):
            RatTheorem(Ratio(2, 4), "Rat.normalize", raw=(2, 4))
        with self.assertRaises(KernelError):
            RatTheorem(Ratio(1, 2), "Rat.normalize", raw=(1, 3))
        with self.assertRaises(KernelError):
            RatTheorem(Ratio(0, 1), "Rat.normalize", raw=(1, 0))
        left = rat_normalize(1, 2)
        right = rat_normalize(1, 3)
        with self.assertRaises(KernelError):
            RatTheorem(Ratio(5, 6), "Rat.add", (left, right), (1, 6))
        shown = rat_normalize(8, 6)
        self.assertEqual((shown.value.num, shown.value.den), (4, 3))
        self.assertEqual(rat_normalize(-8, 6).value, Ratio(-4, 3))


def _sample(rule: str):
    x = Var("x")
    y = Var("y")
    z = Var("z")
    samples = {
        "Int.add_comm": App("add", (x, y)),
        "Int.add_assoc": App("add", (App("add", (x, y)), z)),
        "Int.add_zero": App("add", (x, IntLit(0))),
        "Int.zero_add": App("add", (IntLit(0), x)),
        "Int.add_right_neg": App("add", (x, App("neg", (x,)))),
        "Int.add_left_neg": App("add", (App("neg", (x,)), x)),
        "Int.neg_neg": App("neg", (App("neg", (x,)),)),
        "Int.sub_eq_add_neg": App("sub", (x, y)),
        "Int.mul_comm": App("mul", (x, y)),
        "Int.mul_assoc": App("mul", (App("mul", (x, y)), z)),
        "Int.mul_one": App("mul", (x, IntLit(1))),
        "Int.one_mul": App("mul", (IntLit(1), x)),
        "Int.mul_zero": App("mul", (x, IntLit(0))),
        "Int.zero_mul": App("mul", (IntLit(0), x)),
        "Int.mul_add": App("mul", (x, App("add", (y, z)))),
        "Int.add_mul": App("mul", (App("add", (x, y)), z)),
    }
    return samples[rule]


if __name__ == "__main__":
    unittest.main()
