from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.kernel import KernelError
from pgi.math.rational import Ratio
from pgi.math.real import (
    RealForm,
    RealTheorem,
    _canonical,
    eval_real,
    real_div,
    real_mul,
    real_of_rat,
    real_sqrt,
    show_form,
)
from pgi.math.syntax import parse_term
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class ContinuumTests(unittest.TestCase):
    def test_perfect_squares_are_rational_constants(self) -> None:
        four = run(Request(ask="what is sqrt(4)", seed=1))
        self.assertEqual(four.claims[0].atom, "value(2)")
        self.assertIn("cauchy_const", four.text(lod=2))
        self.assertEqual(four.open_gaps, ())
        zero = run(Request(ask="what is sqrt(0)", seed=1))
        self.assertEqual(zero.claims[0].atom, "value(0)")
        fraction = run(Request(ask="what is sqrt(4/9)", seed=1))
        self.assertEqual(fraction.claims[0].atom, "ratio(2,3)")
        self.assertIn("is the exact rational", fraction.text(lod=1))
        reduced = run(Request(ask="what is sqrt(8/18)", seed=1))
        self.assertEqual(reduced.claims[0].atom, "ratio(2,3)")
        nested = run(Request(ask="what is sqrt(sqrt(4))", seed=1))
        self.assertEqual(nested.claims[0].atom, "cauchy(sqrt(2))")
        summed = run(Request(ask="what is sqrt(4) + sqrt(9)", seed=1))
        self.assertEqual(summed.claims[0].atom, "value(5)")

    def test_square_roots_are_cauchy_classes(self) -> None:
        root = run(Request(ask="what is sqrt(2)", seed=1))
        self.assertEqual(root.claims[0].atom, "cauchy(sqrt(2))")
        self.assertIn("cauchy(sqrt(2)) is the constructed real", root.text(lod=1))
        detail = root.text(lod=2)
        self.assertIn("vanishing sequence", detail)
        self.assertIn("1/16", detail)
        self.assertNotIn("value(", detail)
        self.assertEqual(root.open_gaps, ())
        outline = root.text(lod=0)
        self.assertNotIn("cauchy(sqrt(2))", outline)
        extracted = run(Request(ask="what is sqrt(8)", seed=1))
        self.assertEqual(extracted.claims[0].atom, "cauchy(2 * sqrt(2))")
        self.assertIn("Square factors", extracted.text(lod=2))
        eighteen = run(Request(ask="what is sqrt(18)", seed=1))
        self.assertEqual(eighteen.claims[0].atom, "cauchy(3 * sqrt(2))")
        third = run(Request(ask="what is sqrt(2/3)", seed=1))
        self.assertEqual(third.claims[0].atom, "cauchy(1/3 * sqrt(6))")
        doubled = run(Request(ask="what is sqrt(2) + sqrt(2)", seed=1))
        self.assertEqual(doubled.claims[0].atom, "cauchy(2 * sqrt(2))")
        combined = run(Request(ask="what is 2 * sqrt(2) + 3 * sqrt(2)", seed=1))
        self.assertEqual(combined.claims[0].atom, "cauchy(5 * sqrt(2))")
        negative = run(Request(ask="what is -sqrt(2)", seed=1))
        self.assertEqual(negative.claims[0].atom, "cauchy(-sqrt(2))")

    def test_products_and_rational_division(self) -> None:
        square = run(Request(ask="what is sqrt(2) * sqrt(2)", seed=1))
        self.assertEqual(square.claims[0].atom, "value(2)")
        self.assertIn("vanishing sequence", square.text(lod=2))
        mixed = run(Request(ask="what is sqrt(8) * sqrt(2)", seed=1))
        self.assertEqual(mixed.claims[0].atom, "value(4)")
        half = run(Request(ask="what is sqrt(2) / 2", seed=1))
        self.assertEqual(half.claims[0].atom, "cauchy(1/2 * sqrt(2))")
        same = run(Request(ask="what is sqrt(2) / sqrt(2)", seed=1))
        self.assertEqual(same.claims[0].atom, "value(1)")
        other = run(Request(ask="what is sqrt(2) / sqrt(3)", seed=1))
        self.assertEqual(other.claims[0].atom, "cauchy(1/3 * sqrt(6))")
        self.assertIn("inverse_unique", other.text(lod=2))
        self.assertIn("divide_real_def", other.text(lod=2))
        self.assertEqual(other.open_gaps, ())

    def test_division_by_zero_and_negative_radicands_stay_open(self) -> None:
        zero = run(Request(ask="what is sqrt(2) / 0", seed=1))
        self.assertIn("division by zero", zero.text(lod=1))
        self.assertFalse(any(claim.atom.startswith(("value(", "ratio(", "cauchy(")) for claim in zero.claims))
        self.assertTrue(zero.open_gaps)
        negative = run(Request(ask="what is sqrt(-2)", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in negative.claims))

    def test_equality_and_order(self) -> None:
        held = run(Request(ask="prove sqrt(2) * sqrt(2) = 2", seed=1))
        self.assertEqual(held.claims[0].atom, "identity(sqrt(2) * sqrt(2) = 2)")
        self.assertIn("eq_Real", held.text(lod=2))
        self.assertEqual(held.open_gaps, ())
        extracted = run(Request(ask="prove sqrt(8) = 2 * sqrt(2)", seed=1))
        self.assertEqual(extracted.claims[0].atom, "identity(sqrt(8) = 2 * sqrt(2))")
        self.assertEqual(extracted.open_gaps, ())
        summed = run(Request(ask="prove sqrt(2) + sqrt(8) = 3 * sqrt(2)", seed=1))
        self.assertEqual(summed.claims[0].atom, "identity(sqrt(2) + sqrt(8) = 3 * sqrt(2))")
        refused = run(Request(ask="prove sqrt(2) = 3 / 2", seed=1))
        self.assertIn("is not a theorem", refused.text(lod=1))
        self.assertIn("strictly", refused.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("identity(") for claim in refused.claims))
        below = run(Request(ask="prove sqrt(2) <= 3 / 2", seed=1))
        self.assertEqual(below.claims[0].atom, "le(sqrt(2),3 / 2)")
        self.assertIn("positive(y - x)", below.text(lod=2))
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask="prove sqrt(2) <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_le(sqrt(2),1)")
        self.assertEqual(above.open_gaps, ())
        pair = run(Request(ask="prove sqrt(2) <= sqrt(3)", seed=1))
        self.assertEqual(pair.claims[0].atom, "le(sqrt(2),sqrt(3))")
        flipped = run(Request(ask="prove sqrt(3) <= sqrt(2)", seed=1))
        self.assertEqual(flipped.claims[0].atom, "not_le(sqrt(3),sqrt(2))")
        same = run(Request(ask="prove sqrt(2) <= sqrt(2)", seed=1))
        self.assertEqual(same.claims[0].atom, "le(sqrt(2),sqrt(2))")
        self.assertIn("realrel_refl", same.text(lod=2))
        signed = run(Request(ask="prove -sqrt(2) <= 0", seed=1))
        self.assertEqual(signed.claims[0].atom, "le((-sqrt(2)),0)")
        reflected = run(Request(ask="prove 0 <= -sqrt(2)", seed=1))
        self.assertEqual(reflected.claims[0].atom, "not_le(0,(-sqrt(2)))")
        scale = run(Request(ask="prove 2 * sqrt(2) <= 3", seed=1))
        self.assertEqual(scale.claims[0].atom, "le(2 * sqrt(2),3)")
        self.assertEqual(scale.open_gaps, ())
        integer = run(Request(ask="prove sqrt(4) <= 9", seed=1))
        self.assertEqual(integer.claims[0].atom, "le(sqrt(4),9)")
        self.assertEqual(integer.open_gaps, ())

    def test_nested_radicals_are_towers(self) -> None:
        fourth = run(Request(ask="what is sqrt(sqrt(2))", seed=1))
        self.assertEqual(fourth.claims[0].atom, "cauchy(sqrt(sqrt(2)))")
        detail = fourth.text(lod=2)
        self.assertIn("real_sqrt_unique", detail)
        self.assertIn("real_sqrt_pow2", detail)
        self.assertIn("real_le_lsqrt", detail)
        self.assertIn("eq_Real", detail)
        self.assertIn("1/16", detail)
        self.assertEqual(fourth.open_gaps, ())
        square = run(Request(ask="what is sqrt(sqrt(2)) * sqrt(sqrt(2))", seed=1))
        self.assertEqual(square.claims[0].atom, "cauchy(sqrt(2))")
        self.assertEqual(square.open_gaps, ())
        eighth = run(Request(ask="what is sqrt(sqrt(sqrt(2)))", seed=1))
        self.assertEqual(eighth.claims[0].atom, "cauchy(sqrt(sqrt(sqrt(2))))")
        self.assertEqual(eighth.open_gaps, ())
        scaled = run(Request(ask="what is sqrt(4 * sqrt(2))", seed=1))
        self.assertEqual(scaled.claims[0].atom, "cauchy(2 * sqrt(sqrt(2)))")
        self.assertEqual(scaled.open_gaps, ())
        same = run(Request(ask="what is sqrt(2) * sqrt(sqrt(2))", seed=1))
        self.assertEqual(same.claims[0].atom, "cauchy(sqrt(sqrt(8)))")
        self.assertEqual(same.open_gaps, ())
        denested = run(Request(ask="what is sqrt(3 + 2 * sqrt(2))", seed=1))
        self.assertEqual(denested.claims[0].atom, "cauchy(1 + sqrt(2))")
        self.assertIn("real_sqrt_unique", denested.text(lod=2))
        self.assertEqual(denested.open_gaps, ())
        other = run(Request(ask="what is sqrt(4 + 2 * sqrt(3))", seed=1))
        self.assertEqual(other.claims[0].atom, "cauchy(1 + sqrt(3))")
        self.assertEqual(other.open_gaps, ())
        below = run(Request(ask="prove sqrt(sqrt(2)) <= 2", seed=1))
        self.assertEqual(below.claims[0].atom, "le(sqrt(sqrt(2)),2)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask="prove sqrt(sqrt(2)) <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_le(sqrt(sqrt(2)),1)")
        self.assertEqual(above.open_gaps, ())
        identity = run(Request(ask="prove sqrt(sqrt(2)) * sqrt(sqrt(2)) = sqrt(2)", seed=1))
        self.assertEqual(identity.claims[0].atom, "identity(sqrt(sqrt(2)) * sqrt(sqrt(2)) = sqrt(2))")
        self.assertEqual(identity.open_gaps, ())
        paired = run(Request(ask="what is sqrt(sqrt(2)) * sqrt(sqrt(3))", seed=1))
        self.assertEqual(paired.claims[0].atom, "cauchy(sqrt(sqrt(6)))")
        split = run(Request(ask="what is sqrt(2) * sqrt(sqrt(3))", seed=1))
        self.assertEqual(split.claims[0].atom, "cauchy(sqrt(sqrt(12)))")
        self.assertEqual(split.open_gaps, ())

    def test_division_by_a_different_irrational(self) -> None:
        quotient = run(Request(ask="what is sqrt(2) / sqrt(3)", seed=1))
        self.assertEqual(quotient.claims[0].atom, "cauchy(1/3 * sqrt(6))")
        self.assertIn("real_div_sqrt", quotient.text(lod=2))
        self.assertIn("inverse (0::real) = 0", quotient.text(lod=2))
        self.assertEqual(quotient.open_gaps, ())
        identity = run(Request(ask="prove sqrt(2) / sqrt(3) = sqrt(6) / 3", seed=1))
        self.assertEqual(identity.claims[0].atom, "identity(sqrt(2) / sqrt(3) = sqrt(6) / 3)")
        self.assertEqual(identity.open_gaps, ())
        reduced = run(Request(ask="what is sqrt(8) / sqrt(2)", seed=1))
        self.assertEqual(reduced.claims[0].atom, "value(2)")
        self.assertEqual(reduced.open_gaps, ())
        fourth = run(Request(ask="what is sqrt(2) / sqrt(sqrt(2))", seed=1))
        self.assertEqual(fourth.claims[0].atom, "cauchy(sqrt(sqrt(2)))")
        self.assertEqual(fourth.open_gaps, ())
        nested = run(Request(ask="what is sqrt(sqrt(8)) / sqrt(sqrt(2))", seed=1))
        self.assertEqual(nested.claims[0].atom, "cauchy(sqrt(2))")
        self.assertEqual(nested.open_gaps, ())
        binomial = run(Request(ask="what is 1 / (1 + sqrt(2))", seed=1))
        self.assertEqual(binomial.claims[0].atom, "cauchy(-1 + sqrt(2))")
        self.assertEqual(binomial.open_gaps, ())
        conjugate = run(Request(ask="prove 1 / (1 + sqrt(2)) = -1 + sqrt(2)", seed=1))
        self.assertEqual(conjugate.claims[0].atom, "identity(1 / (1 + sqrt(2)) = -1 + sqrt(2))")
        self.assertEqual(conjugate.open_gaps, ())
        pair = run(Request(ask="what is 1 / (sqrt(2) + sqrt(3))", seed=1))
        self.assertEqual(pair.claims[0].atom, "cauchy(-sqrt(2) + sqrt(3))")
        self.assertEqual(pair.open_gaps, ())
        triple = run(Request(ask="what is 1 / (1 + sqrt(2) + sqrt(3))", seed=1))
        self.assertEqual(triple.claims[0].atom, "cauchy(1/2 + 1/4 * sqrt(2) - 1/4 * sqrt(6))")
        self.assertEqual(triple.open_gaps, ())
        tower = run(Request(ask="what is 1 / (1 + sqrt(sqrt(2)))", seed=1))
        self.assertEqual(
            tower.claims[0].atom,
            "cauchy(-1 - sqrt(2) + sqrt(sqrt(2)) + sqrt(sqrt(8)))",
        )
        self.assertEqual(tower.open_gaps, ())
        pure = run(Request(ask="what is 2 / sqrt(2)", seed=1))
        self.assertEqual(pure.claims[0].atom, "cauchy(sqrt(2))")
        self.assertIn("real_div_sqrt", pure.text(lod=2))
        negative = run(Request(ask="what is sqrt(2) / -sqrt(3)", seed=1))
        self.assertEqual(negative.claims[0].atom, "cauchy(-1/3 * sqrt(6))")
        cancelled = run(Request(ask="what is sqrt(2) / (sqrt(2) - sqrt(2))", seed=1))
        self.assertIn("division by zero", cancelled.text(lod=1))
        self.assertFalse(any(claim.atom.startswith(("value(", "ratio(", "cauchy(")) for claim in cancelled.claims))
        members = run(Request(ask="what is {sqrt(2) / sqrt(3)}", seed=1))
        self.assertEqual(members.claims[0].atom, "set({1/3 * sqrt(6)})")
        ray = run(Request(ask="what is {x. x <= sqrt(2) / sqrt(3)}", seed=1))
        self.assertEqual(ray.claims[0].atom, "atMost(1/3 * sqrt(6))")
        bound = run(Request(ask="what is sup {x. x <= sqrt(2) / sqrt(3)}", seed=1))
        self.assertEqual(bound.claims[0].atom, "cauchy(1/3 * sqrt(6))")
        self.assertIn("cSup_atMost", bound.text(lod=2))

    def test_products_of_radicals_at_different_levels(self) -> None:
        product = run(Request(ask="what is sqrt(2) * sqrt(sqrt(3))", seed=1))
        self.assertEqual(product.claims[0].atom, "cauchy(sqrt(sqrt(12)))")
        detail = product.text(lod=2)
        self.assertIn("real_root_mult", detail)
        self.assertIn("real_root_power", detail)
        self.assertIn("real_root_mult_exp", detail)
        self.assertEqual(product.open_gaps, ())
        identity = run(Request(ask="prove sqrt(2) * sqrt(sqrt(3)) = sqrt(sqrt(12))", seed=1))
        self.assertEqual(identity.claims[0].atom, "identity(sqrt(2) * sqrt(sqrt(3)) = sqrt(sqrt(12)))")
        self.assertEqual(identity.open_gaps, ())
        quotient = run(Request(ask="what is sqrt(sqrt(2)) / sqrt(sqrt(3))", seed=1))
        self.assertEqual(quotient.claims[0].atom, "cauchy(1/3 * sqrt(sqrt(54)))")
        self.assertIn("inverse_unique", quotient.text(lod=2))
        self.assertIn("real_root_mult", quotient.text(lod=2))
        self.assertEqual(quotient.open_gaps, ())
        reduced = run(Request(ask="prove sqrt(sqrt(2)) / sqrt(sqrt(3)) = sqrt(sqrt(54)) / 3", seed=1))
        self.assertEqual(
            reduced.claims[0].atom,
            "identity(sqrt(sqrt(2)) / sqrt(sqrt(3)) = sqrt(sqrt(54)) / 3)",
        )
        self.assertEqual(reduced.open_gaps, ())
        squared = run(Request(ask="what is sqrt(sqrt(12)) * sqrt(sqrt(12))", seed=1))
        self.assertEqual(squared.claims[0].atom, "cauchy(2 * sqrt(3))")
        self.assertEqual(squared.open_gaps, ())
        cancelled = run(Request(ask="what is sqrt(sqrt(12)) * sqrt(sqrt(108))", seed=1))
        self.assertEqual(cancelled.claims[0].atom, "value(6)")
        self.assertEqual(cancelled.open_gaps, ())
        nested = run(Request(ask="what is sqrt(3 * sqrt(2))", seed=1))
        self.assertEqual(nested.claims[0].atom, "cauchy(sqrt(sqrt(18)))")
        self.assertIn("real_root_mult_exp", nested.text(lod=2))
        self.assertEqual(nested.open_gaps, ())
        same = run(Request(ask="what is sqrt(sqrt(18))", seed=1))
        self.assertEqual(same.claims[0].atom, "cauchy(sqrt(sqrt(18)))")
        folded = run(Request(ask="what is sqrt(2) * sqrt(sqrt(3)) * sqrt(sqrt(12))", seed=1))
        self.assertEqual(folded.claims[0].atom, "cauchy(2 * sqrt(3))")
        below = run(Request(ask="prove sqrt(sqrt(12)) <= 2", seed=1))
        self.assertEqual(below.claims[0].atom, "le(sqrt(sqrt(12)),2)")
        above = run(Request(ask="prove sqrt(sqrt(12)) <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_le(sqrt(sqrt(12)),1)")
        members = run(Request(ask="what is {sqrt(2) * sqrt(sqrt(3))}", seed=1))
        self.assertEqual(members.claims[0].atom, "set({sqrt(sqrt(12))})")
        ray = run(Request(ask="what is {x. x <= sqrt(2) * sqrt(sqrt(3))}", seed=1))
        self.assertEqual(ray.claims[0].atom, "atMost(sqrt(sqrt(12)))")
        bound = run(Request(ask="what is sup {x. x <= sqrt(2) * sqrt(sqrt(3))}", seed=1))
        self.assertEqual(bound.claims[0].atom, "cauchy(sqrt(sqrt(12)))")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        mixed = run(Request(ask="what is 1 / (sqrt(sqrt(2)) + sqrt(sqrt(3)))", seed=1))
        self.assertEqual(
            mixed.claims[0].atom,
            "cauchy(-sqrt(sqrt(8)) + sqrt(sqrt(27)) + sqrt(sqrt(12)) - sqrt(sqrt(18)))",
        )
        self.assertEqual(mixed.open_gaps, ())
        mixed_back = run(
            Request(
                ask="prove (sqrt(sqrt(2)) + sqrt(sqrt(3))) * (1 / (sqrt(sqrt(2)) + sqrt(sqrt(3)))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            mixed_back.claims[0].atom,
            "identity((sqrt(sqrt(2)) + sqrt(sqrt(3))) * (1 / (sqrt(sqrt(2)) + sqrt(sqrt(3)))) = 1)",
        )
        self.assertEqual(mixed_back.open_gaps, ())
        packed = run(Request(ask="what is 1 / (1 + sqrt(sqrt(12)))", seed=1))
        self.assertEqual(
            packed.claims[0].atom,
            "cauchy(-1/11 - 2/11 * sqrt(3) + 1/11 * sqrt(sqrt(12)) + 2/11 * sqrt(sqrt(108)))",
        )
        self.assertEqual(packed.open_gaps, ())
        packed_back = run(
            Request(
                ask="prove (1 + sqrt(sqrt(12))) * (1 / (1 + sqrt(sqrt(12)))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            packed_back.claims[0].atom,
            "identity((1 + sqrt(sqrt(12))) * (1 / (1 + sqrt(sqrt(12)))) = 1)",
        )
        self.assertEqual(packed_back.open_gaps, ())

    def test_denesting_sqrt_of_two_plus_sqrt_of_two(self) -> None:
        nested = run(Request(ask="what is sqrt(2 + sqrt(2))", seed=1))
        self.assertEqual(nested.claims[0].atom, "cauchy(sqrt(2 + sqrt(2)))")
        detail = nested.text(lod=2)
        self.assertIn("real_sqrt_unique", detail)
        self.assertIn("real_sqrt_pow2", detail)
        self.assertIn("real_sqrt_ge_zero", detail)
        self.assertIn("real_le_lsqrt", detail)
        self.assertIn("eq_Real", detail)
        self.assertEqual(nested.open_gaps, ())
        square = run(Request(ask="prove sqrt(2 + sqrt(2)) * sqrt(2 + sqrt(2)) = 2 + sqrt(2)", seed=1))
        self.assertEqual(
            square.claims[0].atom,
            "identity(sqrt(2 + sqrt(2)) * sqrt(2 + sqrt(2)) = 2 + sqrt(2))",
        )
        self.assertEqual(square.open_gaps, ())
        sibling = run(Request(ask="what is sqrt(2 - sqrt(2))", seed=1))
        self.assertEqual(sibling.claims[0].atom, "cauchy(sqrt(2 - sqrt(2)))")
        self.assertEqual(sibling.open_gaps, ())
        sibling_square = run(
            Request(ask="prove sqrt(2 - sqrt(2)) * sqrt(2 - sqrt(2)) = 2 - sqrt(2)", seed=1)
        )
        self.assertEqual(
            sibling_square.claims[0].atom,
            "identity(sqrt(2 - sqrt(2)) * sqrt(2 - sqrt(2)) = 2 - sqrt(2))",
        )
        self.assertEqual(sibling_square.open_gaps, ())
        product = run(Request(ask="what is sqrt(2 + sqrt(2)) * sqrt(2 - sqrt(2))", seed=1))
        self.assertEqual(product.claims[0].atom, "cauchy(sqrt(2))")
        self.assertEqual(product.open_gaps, ())
        scaled = run(Request(ask="what is sqrt(3) * sqrt(2 + sqrt(2))", seed=1))
        self.assertEqual(scaled.claims[0].atom, "cauchy(sqrt(6 + 3 * sqrt(2)))")
        self.assertEqual(scaled.open_gaps, ())
        partner = run(Request(ask="prove sqrt(2) * sqrt(2 + sqrt(2)) = sqrt(4 + 2 * sqrt(2))", seed=1))
        self.assertEqual(
            partner.claims[0].atom,
            "identity(sqrt(2) * sqrt(2 + sqrt(2)) = sqrt(4 + 2 * sqrt(2)))",
        )
        self.assertEqual(partner.open_gaps, ())
        inverse = run(Request(ask="what is 1 / sqrt(2 + sqrt(2))", seed=1))
        self.assertEqual(
            inverse.claims[0].atom,
            "cauchy(sqrt(2 + sqrt(2)) - 1/2 * sqrt(4 + 2 * sqrt(2)))",
        )
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(
            Request(ask="prove sqrt(2 + sqrt(2)) * (1 / sqrt(2 + sqrt(2))) = 1", seed=1)
        )
        self.assertEqual(
            back.claims[0].atom,
            "identity(sqrt(2 + sqrt(2)) * (1 / sqrt(2 + sqrt(2))) = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        shifted = run(Request(ask="what is 1 / (1 + sqrt(2 + sqrt(2)))", seed=1))
        self.assertEqual(
            shifted.claims[0].atom,
            "cauchy(1 - sqrt(2) - sqrt(2 + sqrt(2)) + sqrt(4 + 2 * sqrt(2)))",
        )
        self.assertEqual(shifted.open_gaps, ())
        shifted_back = run(
            Request(
                ask="prove (1 + sqrt(2 + sqrt(2))) * (1 / (1 + sqrt(2 + sqrt(2)))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            shifted_back.claims[0].atom,
            "identity((1 + sqrt(2 + sqrt(2))) * (1 / (1 + sqrt(2 + sqrt(2)))) = 1)",
        )
        self.assertEqual(shifted_back.open_gaps, ())
        below = run(Request(ask="prove sqrt(2 + sqrt(2)) <= 2", seed=1))
        self.assertEqual(below.claims[0].atom, "le(sqrt(2 + sqrt(2)),2)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask="prove sqrt(2 + sqrt(2)) <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_le(sqrt(2 + sqrt(2)),1)")
        self.assertEqual(above.open_gaps, ())
        members = run(Request(ask="what is {sqrt(2 + sqrt(2))}", seed=1))
        self.assertEqual(members.claims[0].atom, "set({sqrt(2 + sqrt(2))})")
        bound = run(Request(ask="what is sup {x. x <= sqrt(2 + sqrt(2))}", seed=1))
        self.assertEqual(bound.claims[0].atom, "cauchy(sqrt(2 + sqrt(2)))")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        classical = run(Request(ask="what is sqrt(2 + sqrt(3))", seed=1))
        self.assertEqual(classical.claims[0].atom, "cauchy(1/2 * sqrt(2) + 1/2 * sqrt(6))")
        self.assertEqual(classical.open_gaps, ())
        other = run(Request(ask="what is sqrt(3 + sqrt(2))", seed=1))
        self.assertEqual(other.claims[0].atom, "cauchy(sqrt(3 + sqrt(2)))")
        self.assertEqual(other.open_gaps, ())

    def test_denesting_sqrt_of_sqrt_two_plus_sqrt_three(self) -> None:
        nested = run(Request(ask="what is sqrt(sqrt(2) + sqrt(3))", seed=1))
        shown = "1/2 * sqrt(-2 + 2 * sqrt(3)) + 1/2 * sqrt(2 + 2 * sqrt(3))"
        self.assertEqual(nested.claims[0].atom, f"cauchy({shown})")
        detail = nested.text(lod=2)
        self.assertIn("real_sqrt_unique", detail)
        self.assertIn("real_sqrt_pow2", detail)
        self.assertIn("real_sqrt_ge_zero", detail)
        self.assertIn("real_le_lsqrt", detail)
        self.assertIn("eq_Real", detail)
        self.assertEqual(nested.open_gaps, ())
        square = run(
            Request(
                ask="prove sqrt(sqrt(2) + sqrt(3)) * sqrt(sqrt(2) + sqrt(3)) = sqrt(2) + sqrt(3)",
                seed=1,
            )
        )
        self.assertEqual(
            square.claims[0].atom,
            "identity(sqrt(sqrt(2) + sqrt(3)) * sqrt(sqrt(2) + sqrt(3)) = sqrt(2) + sqrt(3))",
        )
        self.assertEqual(square.open_gaps, ())
        sibling = run(Request(ask="what is sqrt(sqrt(3) - sqrt(2))", seed=1))
        self.assertEqual(
            sibling.claims[0].atom,
            "cauchy(-1/2 * sqrt(-2 + 2 * sqrt(3)) + 1/2 * sqrt(2 + 2 * sqrt(3)))",
        )
        self.assertEqual(sibling.open_gaps, ())
        sibling_square = run(
            Request(
                ask="prove sqrt(sqrt(3) - sqrt(2)) * sqrt(sqrt(3) - sqrt(2)) = sqrt(3) - sqrt(2)",
                seed=1,
            )
        )
        self.assertEqual(
            sibling_square.claims[0].atom,
            "identity(sqrt(sqrt(3) - sqrt(2)) * sqrt(sqrt(3) - sqrt(2)) = sqrt(3) - sqrt(2))",
        )
        self.assertEqual(sibling_square.open_gaps, ())
        product = run(
            Request(ask="what is sqrt(sqrt(3) - sqrt(2)) * sqrt(sqrt(2) + sqrt(3))", seed=1)
        )
        self.assertEqual(product.claims[0].atom, "value(1)")
        self.assertEqual(product.open_gaps, ())
        scaled = run(Request(ask="what is sqrt(2 * sqrt(3) + 2 * sqrt(2))", seed=1))
        self.assertEqual(scaled.claims[0].atom, "cauchy(sqrt(-1 + sqrt(3)) + sqrt(1 + sqrt(3)))")
        self.assertEqual(scaled.open_gaps, ())
        other = run(Request(ask="what is sqrt(sqrt(6) + sqrt(2))", seed=1))
        self.assertEqual(
            other.claims[0].atom,
            "cauchy(1/2 * sqrt(-4 + 2 * sqrt(6)) + 1/2 * sqrt(4 + 2 * sqrt(6)))",
        )
        self.assertEqual(other.open_gaps, ())
        below = run(Request(ask="prove sqrt(sqrt(2) + sqrt(3)) <= 2", seed=1))
        self.assertEqual(below.claims[0].atom, "le(sqrt(sqrt(2) + sqrt(3)),2)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask="prove sqrt(sqrt(2) + sqrt(3)) <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_le(sqrt(sqrt(2) + sqrt(3)),1)")
        self.assertEqual(above.open_gaps, ())
        members = run(Request(ask="what is {sqrt(sqrt(2) + sqrt(3))}", seed=1))
        self.assertEqual(members.claims[0].atom, f"set({{{shown}}})")
        bound = run(Request(ask="what is sup {x. x <= sqrt(sqrt(2) + sqrt(3))}", seed=1))
        self.assertEqual(bound.claims[0].atom, f"cauchy({shown})")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        self.assertEqual(bound.open_gaps, ())
        three = run(Request(ask="what is sqrt(1 + sqrt(2) + sqrt(3))", seed=1))
        self.assertEqual(three.claims[0].atom, "cauchy(sqrt(1 + sqrt(2) + sqrt(3)))")
        self.assertEqual(three.open_gaps, ())
        inverse = run(Request(ask="what is 1 / sqrt(sqrt(2) + sqrt(3))", seed=1))
        self.assertEqual(
            inverse.claims[0].atom,
            "cauchy(-1/2 * sqrt(-2 + 2 * sqrt(3)) + 1/2 * sqrt(2 + 2 * sqrt(3)))",
        )
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        inverse_back = run(
            Request(
                ask="prove (1 / sqrt(sqrt(2) + sqrt(3))) * sqrt(sqrt(2) + sqrt(3)) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            inverse_back.claims[0].atom,
            "identity(1 / sqrt(sqrt(2) + sqrt(3)) * sqrt(sqrt(2) + sqrt(3)) = 1)",
        )
        self.assertEqual(inverse_back.open_gaps, ())
        negative = run(Request(ask="what is sqrt(sqrt(2) - sqrt(3))", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in negative.claims))

    def test_denesting_sqrt_of_sqrt_two_plus_sqrt_five(self) -> None:
        nested = run(Request(ask="what is sqrt(sqrt(2) + sqrt(5))", seed=1))
        shown = "sqrt(sqrt(2) + sqrt(5))"
        self.assertEqual(nested.claims[0].atom, f"cauchy({shown})")
        detail = nested.text(lod=2)
        self.assertIn("real_sqrt_unique", detail)
        self.assertIn("real_sqrt_pow2", detail)
        self.assertIn("real_sqrt_ge_zero", detail)
        self.assertIn("real_le_lsqrt", detail)
        self.assertIn("eq_Real", detail)
        self.assertEqual(nested.open_gaps, ())
        square = run(
            Request(
                ask="prove sqrt(sqrt(2) + sqrt(5)) * sqrt(sqrt(2) + sqrt(5)) = sqrt(2) + sqrt(5)",
                seed=1,
            )
        )
        self.assertEqual(
            square.claims[0].atom,
            "identity(sqrt(sqrt(2) + sqrt(5)) * sqrt(sqrt(2) + sqrt(5)) = sqrt(2) + sqrt(5))",
        )
        self.assertEqual(square.open_gaps, ())
        sibling = run(Request(ask="what is sqrt(sqrt(5) - sqrt(2))", seed=1))
        self.assertEqual(sibling.claims[0].atom, "cauchy(sqrt(-sqrt(2) + sqrt(5)))")
        self.assertEqual(sibling.open_gaps, ())
        sibling_square = run(
            Request(
                ask="what is sqrt(sqrt(5) - sqrt(2)) * sqrt(sqrt(5) - sqrt(2))",
                seed=1,
            )
        )
        self.assertEqual(sibling_square.claims[0].atom, "cauchy(-sqrt(2) + sqrt(5))")
        self.assertEqual(sibling_square.open_gaps, ())
        product = run(
            Request(ask="what is sqrt(sqrt(5) - sqrt(2)) * sqrt(sqrt(2) + sqrt(5))", seed=1)
        )
        self.assertEqual(product.claims[0].atom, "cauchy(sqrt(3))")
        self.assertEqual(product.open_gaps, ())
        inverse = run(Request(ask="what is 1 / sqrt(sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(
            inverse.claims[0].atom,
            "cauchy(1/3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))",
        )
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(
            Request(
                ask="prove sqrt(sqrt(2) + sqrt(5)) * (1 / sqrt(sqrt(2) + sqrt(5))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            back.claims[0].atom,
            "identity(sqrt(sqrt(2) + sqrt(5)) * (1 / sqrt(sqrt(2) + sqrt(5))) = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        scaled = run(Request(ask="what is sqrt(4 * sqrt(2) + 4 * sqrt(5))", seed=1))
        self.assertEqual(scaled.claims[0].atom, "cauchy(2 * sqrt(sqrt(2) + sqrt(5)))")
        self.assertEqual(scaled.open_gaps, ())
        absorbed = run(Request(ask="what is sqrt(2) * sqrt(sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(absorbed.claims[0].atom, "cauchy(sqrt(2 * sqrt(2) + 2 * sqrt(5)))")
        direct = run(Request(ask="what is sqrt(2 * sqrt(2) + 2 * sqrt(5))", seed=1))
        self.assertEqual(direct.claims[0].atom, absorbed.claims[0].atom)
        reduced = run(Request(ask="what is sqrt(sqrt(8) + sqrt(5))", seed=1))
        self.assertEqual(reduced.claims[0].atom, "cauchy(sqrt(2 * sqrt(2) + sqrt(5)))")
        self.assertEqual(reduced.open_gaps, ())
        below = run(Request(ask="prove sqrt(sqrt(2) + sqrt(5)) <= 2", seed=1))
        self.assertEqual(below.claims[0].atom, "le(sqrt(sqrt(2) + sqrt(5)),2)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask="prove sqrt(sqrt(2) + sqrt(5)) <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_le(sqrt(sqrt(2) + sqrt(5)),1)")
        self.assertEqual(above.open_gaps, ())
        members = run(Request(ask="what is {sqrt(sqrt(2) + sqrt(5))}", seed=1))
        self.assertEqual(members.claims[0].atom, f"set({{{shown}}})")
        bound = run(Request(ask="what is sup {x. x <= sqrt(sqrt(2) + sqrt(5))}", seed=1))
        self.assertEqual(bound.claims[0].atom, f"cauchy({shown})")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        self.assertEqual(bound.open_gaps, ())
        negative = run(Request(ask="what is sqrt(sqrt(2) - sqrt(5))", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in negative.claims))
        five = run(Request(ask="what is sqrt(1 + sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(five.claims[0].atom, "cauchy(sqrt(1 + sqrt(2) + sqrt(5)))")
        self.assertEqual(five.open_gaps, ())
        mixed = run(Request(ask="what is sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(mixed.claims[0].atom, "cauchy(sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)))")
        self.assertEqual(mixed.open_gaps, ())
        quotient = run(Request(ask="what is 1 / (sqrt(sqrt(2) + sqrt(5)) + sqrt(2))", seed=1))
        self.assertIn("this quotient stays outside", quotient.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in quotient.claims))

    def test_denesting_sqrt_of_nested_binomial(self) -> None:
        nested = run(Request(ask="what is sqrt(sqrt(2 + sqrt(2)))", seed=1))
        shown = "sqrt(sqrt(2 + sqrt(2)))"
        self.assertEqual(nested.claims[0].atom, f"cauchy({shown})")
        detail = nested.text(lod=2)
        self.assertIn("real_sqrt_unique", detail)
        self.assertIn("real_sqrt_pow2", detail)
        self.assertIn("real_sqrt_ge_zero", detail)
        self.assertIn("real_le_lsqrt", detail)
        self.assertIn("eq_Real", detail)
        self.assertEqual(nested.open_gaps, ())
        square = run(
            Request(
                ask="prove sqrt(sqrt(2 + sqrt(2))) * sqrt(sqrt(2 + sqrt(2))) = sqrt(2 + sqrt(2))",
                seed=1,
            )
        )
        self.assertEqual(
            square.claims[0].atom,
            "identity(sqrt(sqrt(2 + sqrt(2))) * sqrt(sqrt(2 + sqrt(2))) = sqrt(2 + sqrt(2)))",
        )
        self.assertEqual(square.open_gaps, ())
        sibling = run(Request(ask="what is sqrt(sqrt(2 - sqrt(2)))", seed=1))
        self.assertEqual(sibling.claims[0].atom, "cauchy(sqrt(sqrt(2 - sqrt(2))))")
        self.assertEqual(sibling.open_gaps, ())
        product = run(
            Request(
                ask="what is sqrt(sqrt(2 + sqrt(2))) * sqrt(sqrt(2 - sqrt(2)))",
                seed=1,
            )
        )
        self.assertEqual(product.claims[0].atom, "cauchy(sqrt(sqrt(2)))")
        self.assertEqual(product.open_gaps, ())
        scaled = run(Request(ask="what is sqrt(4 * sqrt(2 + sqrt(2)))", seed=1))
        self.assertEqual(scaled.claims[0].atom, "cauchy(2 * sqrt(sqrt(2 + sqrt(2))))")
        self.assertEqual(scaled.open_gaps, ())
        absorbed = run(Request(ask="what is sqrt(2) * sqrt(sqrt(2 + sqrt(2)))", seed=1))
        self.assertEqual(absorbed.claims[0].atom, "cauchy(sqrt(2 * sqrt(2 + sqrt(2))))")
        direct = run(Request(ask="what is sqrt(2 * sqrt(2 + sqrt(2)))", seed=1))
        self.assertEqual(direct.claims[0].atom, absorbed.claims[0].atom)
        inverse = run(Request(ask="what is 1 / sqrt(sqrt(2 + sqrt(2)))", seed=1))
        self.assertEqual(
            inverse.claims[0].atom,
            "cauchy(sqrt(sqrt(20 + 14 * sqrt(2))) - 1/2 * sqrt(2 * sqrt(20 + 14 * sqrt(2))))",
        )
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(
            Request(
                ask="prove sqrt(sqrt(2 + sqrt(2))) * (1 / sqrt(sqrt(2 + sqrt(2)))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            back.claims[0].atom,
            "identity(sqrt(sqrt(2 + sqrt(2))) * (1 / sqrt(sqrt(2 + sqrt(2)))) = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        other = run(Request(ask="what is sqrt(sqrt(3 + sqrt(2)))", seed=1))
        self.assertEqual(other.claims[0].atom, "cauchy(sqrt(sqrt(3 + sqrt(2))))")
        self.assertEqual(other.open_gaps, ())
        added = run(Request(ask="what is 1 + sqrt(sqrt(2 + sqrt(2)))", seed=1))
        self.assertEqual(added.claims[0].atom, "cauchy(1 + sqrt(sqrt(2 + sqrt(2))))")
        self.assertEqual(added.open_gaps, ())
        below = run(Request(ask="prove sqrt(sqrt(2 + sqrt(2))) <= 2", seed=1))
        self.assertEqual(below.claims[0].atom, "le(sqrt(sqrt(2 + sqrt(2))),2)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask="prove sqrt(sqrt(2 + sqrt(2))) <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_le(sqrt(sqrt(2 + sqrt(2))),1)")
        self.assertEqual(above.open_gaps, ())
        members = run(Request(ask="what is {sqrt(sqrt(2 + sqrt(2)))}", seed=1))
        self.assertEqual(members.claims[0].atom, f"set({{{shown}}})")
        bound = run(Request(ask="what is sup {x. x <= sqrt(sqrt(2 + sqrt(2)))}", seed=1))
        self.assertEqual(bound.claims[0].atom, f"cauchy({shown})")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        self.assertEqual(bound.open_gaps, ())
        negative = run(Request(ask="what is sqrt(-sqrt(2 + sqrt(2)))", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in negative.claims))
        again = run(Request(ask="what is sqrt(sqrt(sqrt(2 + sqrt(2))))", seed=1))
        self.assertEqual(again.claims[0].atom, "cauchy(sqrt(sqrt(sqrt(2 + sqrt(2)))))")
        self.assertIn("real_sqrt_unique", again.text(lod=2))
        self.assertEqual(again.open_gaps, ())
        again_square = run(
            Request(
                ask="prove sqrt(sqrt(sqrt(2 + sqrt(2)))) * sqrt(sqrt(sqrt(2 + sqrt(2)))) = sqrt(sqrt(2 + sqrt(2)))",
                seed=1,
            )
        )
        self.assertEqual(
            again_square.claims[0].atom,
            "identity(sqrt(sqrt(sqrt(2 + sqrt(2)))) * sqrt(sqrt(sqrt(2 + sqrt(2)))) = sqrt(sqrt(2 + sqrt(2))))",
        )
        self.assertEqual(again_square.open_gaps, ())
        mixed_shown = (
            "1 - sqrt(2) + sqrt(2 + sqrt(2)) - sqrt(4 + 2 * sqrt(2))"
            " - sqrt(sqrt(2 + sqrt(2))) + sqrt(2 * sqrt(2 + sqrt(2)))"
            " - sqrt(sqrt(20 + 14 * sqrt(2))) + sqrt(2 * sqrt(20 + 14 * sqrt(2)))"
        )
        mixed = run(Request(ask="what is 1 / (1 + sqrt(sqrt(2 + sqrt(2))))", seed=1))
        self.assertEqual(mixed.claims[0].atom, f"cauchy({mixed_shown})")
        self.assertIn("inverse_unique", mixed.text(lod=2))
        self.assertEqual(mixed.open_gaps, ())
        mixed_back = run(
            Request(
                ask="prove (1 / (1 + sqrt(sqrt(2 + sqrt(2))))) * (1 + sqrt(sqrt(2 + sqrt(2)))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            mixed_back.claims[0].atom,
            "identity(1 / (1 + sqrt(sqrt(2 + sqrt(2)))) * (1 + sqrt(sqrt(2 + sqrt(2)))) = 1)",
        )
        self.assertEqual(mixed_back.open_gaps, ())

    def test_denesting_sqrt_of_pair_radical(self) -> None:
        nested = run(Request(ask="what is sqrt(sqrt(sqrt(2) + sqrt(5)))", seed=1))
        shown = "sqrt(sqrt(sqrt(2) + sqrt(5)))"
        self.assertEqual(nested.claims[0].atom, f"cauchy({shown})")
        detail = nested.text(lod=2)
        self.assertIn("real_sqrt_unique", detail)
        self.assertIn("real_sqrt_pow2", detail)
        self.assertIn("real_sqrt_ge_zero", detail)
        self.assertIn("real_le_lsqrt", detail)
        self.assertIn("eq_Real", detail)
        self.assertEqual(nested.open_gaps, ())
        square = run(
            Request(
                ask="prove sqrt(sqrt(sqrt(2) + sqrt(5))) * sqrt(sqrt(sqrt(2) + sqrt(5))) = sqrt(sqrt(2) + sqrt(5))",
                seed=1,
            )
        )
        self.assertEqual(
            square.claims[0].atom,
            "identity(sqrt(sqrt(sqrt(2) + sqrt(5))) * sqrt(sqrt(sqrt(2) + sqrt(5))) = sqrt(sqrt(2) + sqrt(5)))",
        )
        self.assertEqual(square.open_gaps, ())
        sibling = run(Request(ask="what is sqrt(sqrt(sqrt(5) - sqrt(2)))", seed=1))
        self.assertEqual(sibling.claims[0].atom, "cauchy(sqrt(sqrt(-sqrt(2) + sqrt(5))))")
        self.assertEqual(sibling.open_gaps, ())
        product = run(
            Request(
                ask="what is sqrt(sqrt(sqrt(2) + sqrt(5))) * sqrt(sqrt(sqrt(5) - sqrt(2)))",
                seed=1,
            )
        )
        self.assertEqual(product.claims[0].atom, "cauchy(sqrt(sqrt(3)))")
        self.assertEqual(product.open_gaps, ())
        scaled = run(Request(ask="what is sqrt(4 * sqrt(sqrt(2) + sqrt(5)))", seed=1))
        self.assertEqual(scaled.claims[0].atom, "cauchy(2 * sqrt(sqrt(sqrt(2) + sqrt(5))))")
        self.assertEqual(scaled.open_gaps, ())
        absorbed = run(Request(ask="what is sqrt(2) * sqrt(sqrt(sqrt(2) + sqrt(5)))", seed=1))
        self.assertEqual(absorbed.claims[0].atom, "cauchy(sqrt(2 * sqrt(sqrt(2) + sqrt(5))))")
        direct = run(Request(ask="what is sqrt(2 * sqrt(sqrt(2) + sqrt(5)))", seed=1))
        self.assertEqual(direct.claims[0].atom, absorbed.claims[0].atom)
        inverse = run(Request(ask="what is 1 / sqrt(sqrt(sqrt(2) + sqrt(5)))", seed=1))
        self.assertEqual(
            inverse.claims[0].atom,
            "cauchy(1/3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))",
        )
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(
            Request(
                ask="prove sqrt(sqrt(sqrt(2) + sqrt(5))) * (1 / sqrt(sqrt(sqrt(2) + sqrt(5)))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            back.claims[0].atom,
            "identity(sqrt(sqrt(sqrt(2) + sqrt(5))) * (1 / sqrt(sqrt(sqrt(2) + sqrt(5)))) = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        added = run(Request(ask="what is 1 + sqrt(sqrt(sqrt(2) + sqrt(5)))", seed=1))
        self.assertEqual(added.claims[0].atom, "cauchy(1 + sqrt(sqrt(sqrt(2) + sqrt(5))))")
        self.assertEqual(added.open_gaps, ())
        below = run(Request(ask="prove sqrt(sqrt(sqrt(2) + sqrt(5))) <= 2", seed=1))
        self.assertEqual(below.claims[0].atom, "le(sqrt(sqrt(sqrt(2) + sqrt(5))),2)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask="prove sqrt(sqrt(sqrt(2) + sqrt(5))) <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_le(sqrt(sqrt(sqrt(2) + sqrt(5))),1)")
        self.assertEqual(above.open_gaps, ())
        members = run(Request(ask="what is {sqrt(sqrt(sqrt(2) + sqrt(5)))}", seed=1))
        self.assertEqual(members.claims[0].atom, f"set({{{shown}}})")
        bound = run(Request(ask="what is sup {x. x <= sqrt(sqrt(sqrt(2) + sqrt(5)))}", seed=1))
        self.assertEqual(bound.claims[0].atom, f"cauchy({shown})")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        self.assertEqual(bound.open_gaps, ())
        negative = run(Request(ask="what is sqrt(-sqrt(sqrt(2) + sqrt(5)))", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in negative.claims))
        quotient_shown = (
            "3/2 - sqrt(2) + 1/2 * sqrt(5) - 1/2 * sqrt(10)"
            " + 3/2 * sqrt(sqrt(2) + sqrt(5)) - sqrt(2 * sqrt(2) + 2 * sqrt(5))"
            " + 1/2 * sqrt(5 * sqrt(2) + 5 * sqrt(5)) - 1/2 * sqrt(10 * sqrt(2) + 10 * sqrt(5))"
            " - 3/2 * sqrt(sqrt(sqrt(2) + sqrt(5))) + sqrt(2 * sqrt(sqrt(2) + sqrt(5)))"
            " - 1/2 * sqrt(5 * sqrt(sqrt(2) + sqrt(5))) + 1/2 * sqrt(10 * sqrt(sqrt(2) + sqrt(5)))"
            " - 3/2 * sqrt(sqrt(17 * sqrt(2) + 11 * sqrt(5))) + sqrt(2 * sqrt(17 * sqrt(2) + 11 * sqrt(5)))"
            " - 1/2 * sqrt(5 * sqrt(17 * sqrt(2) + 11 * sqrt(5))) + 1/2 * sqrt(10 * sqrt(17 * sqrt(2) + 11 * sqrt(5)))"
        )
        quotient = run(Request(ask="what is 1 / (1 + sqrt(sqrt(sqrt(2) + sqrt(5))))", seed=1))
        self.assertEqual(quotient.claims[0].atom, f"cauchy({quotient_shown})")
        self.assertIn("inverse_unique", quotient.text(lod=2))
        self.assertEqual(quotient.open_gaps, ())
        quotient_back = run(
            Request(
                ask="prove (1 / (1 + sqrt(sqrt(sqrt(2) + sqrt(5))))) * (1 + sqrt(sqrt(sqrt(2) + sqrt(5)))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            quotient_back.claims[0].atom,
            "identity(1 / (1 + sqrt(sqrt(sqrt(2) + sqrt(5)))) * (1 + sqrt(sqrt(sqrt(2) + sqrt(5)))) = 1)",
        )
        self.assertEqual(quotient_back.open_gaps, ())
        five = run(Request(ask="what is sqrt(1 + sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(five.claims[0].atom, "cauchy(sqrt(1 + sqrt(2) + sqrt(5)))")
        self.assertEqual(five.open_gaps, ())
        nest_pair = run(Request(ask="what is sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(nest_pair.claims[0].atom, "cauchy(sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)))")
        self.assertEqual(nest_pair.open_gaps, ())

    def test_denesting_sqrt_of_high(self) -> None:
        nested = run(Request(ask="what is sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))", seed=1))
        shown = "sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))"
        self.assertEqual(nested.claims[0].atom, f"cauchy({shown})")
        detail = nested.text(lod=2)
        self.assertIn("real_sqrt_unique", detail)
        self.assertIn("real_sqrt_pow2", detail)
        self.assertIn("real_sqrt_ge_zero", detail)
        self.assertIn("real_le_lsqrt", detail)
        self.assertIn("eq_Real", detail)
        self.assertNotIn("real_sqrt_le_iff", detail)
        self.assertNotIn("real_sqrt_minus", detail)
        self.assertEqual(nested.open_gaps, ())
        square = run(
            Request(
                ask="prove sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) * sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) = sqrt(sqrt(sqrt(2) + sqrt(5)))",
                seed=1,
            )
        )
        self.assertEqual(
            square.claims[0].atom,
            "identity(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) * sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) = sqrt(sqrt(sqrt(2) + sqrt(5))))",
        )
        self.assertEqual(square.open_gaps, ())
        sibling = run(Request(ask="what is sqrt(sqrt(sqrt(sqrt(5) - sqrt(2))))", seed=1))
        self.assertEqual(sibling.claims[0].atom, "cauchy(sqrt(sqrt(sqrt(-sqrt(2) + sqrt(5)))))")
        self.assertEqual(sibling.open_gaps, ())
        product = run(
            Request(
                ask="what is sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) * sqrt(sqrt(sqrt(sqrt(5) - sqrt(2))))",
                seed=1,
            )
        )
        self.assertEqual(product.claims[0].atom, "cauchy(sqrt(sqrt(sqrt(3))))")
        self.assertEqual(product.open_gaps, ())
        scaled = run(Request(ask="what is sqrt(4 * sqrt(sqrt(sqrt(2) + sqrt(5))))", seed=1))
        self.assertEqual(scaled.claims[0].atom, "cauchy(2 * sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))")
        self.assertEqual(scaled.open_gaps, ())
        absorbed = run(Request(ask="what is sqrt(2) * sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))", seed=1))
        self.assertEqual(absorbed.claims[0].atom, "cauchy(sqrt(2 * sqrt(sqrt(sqrt(2) + sqrt(5)))))")
        direct = run(Request(ask="what is sqrt(2 * sqrt(sqrt(sqrt(2) + sqrt(5))))", seed=1))
        self.assertEqual(direct.claims[0].atom, absorbed.claims[0].atom)
        inverse = run(Request(ask="what is 1 / sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))", seed=1))
        self.assertEqual(
            inverse.claims[0].atom,
            "cauchy(1/3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))))",
        )
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(
            Request(
                ask="prove sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) * (1 / sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            back.claims[0].atom,
            "identity(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) * (1 / sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        added = run(Request(ask="what is 1 + sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))", seed=1))
        self.assertEqual(added.claims[0].atom, "cauchy(1 + sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))")
        self.assertEqual(added.open_gaps, ())
        below = run(Request(ask="prove sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) <= 2", seed=1))
        self.assertEqual(below.claims[0].atom, "le(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))),2)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask="prove sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_le(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))),1)")
        self.assertEqual(above.open_gaps, ())
        members = run(Request(ask="what is {sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))}", seed=1))
        self.assertEqual(members.claims[0].atom, f"set({{{shown}}})")
        bound = run(Request(ask="what is sup {x. x <= sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))}", seed=1))
        self.assertEqual(bound.claims[0].atom, f"cauchy({shown})")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        self.assertEqual(bound.open_gaps, ())
        negative = run(Request(ask="what is sqrt(-sqrt(sqrt(sqrt(2) + sqrt(5))))", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in negative.claims))
        quotient = run(Request(ask="what is 1 / (1 + sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))", seed=1))
        self.assertIn("this quotient stays outside", quotient.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in quotient.claims))
        five = run(Request(ask="what is sqrt(1 + sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(five.claims[0].atom, "cauchy(sqrt(1 + sqrt(2) + sqrt(5)))")
        self.assertEqual(five.open_gaps, ())
        nest_pair = run(Request(ask="what is sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(nest_pair.claims[0].atom, "cauchy(sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)))")
        self.assertEqual(nest_pair.open_gaps, ())

    def test_denesting_sqrt_of_peak(self) -> None:
        nested = run(Request(ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))", seed=1))
        shown = "sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))"
        self.assertEqual(nested.claims[0].atom, f"cauchy({shown})")
        detail = nested.text(lod=2)
        self.assertIn("real_sqrt_unique", detail)
        self.assertIn("real_sqrt_pow2", detail)
        self.assertIn("real_sqrt_ge_zero", detail)
        self.assertIn("real_le_lsqrt", detail)
        self.assertIn("eq_Real", detail)
        self.assertNotIn("real_sqrt_le_iff", detail)
        self.assertNotIn("real_sqrt_minus", detail)
        self.assertEqual(nested.open_gaps, ())
        square = run(
            Request(
                ask="prove sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) * sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) = sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))",
                seed=1,
            )
        )
        self.assertEqual(
            square.claims[0].atom,
            "identity(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) * sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) = sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))",
        )
        self.assertEqual(square.open_gaps, ())
        sibling = run(Request(ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(5) - sqrt(2)))))", seed=1))
        self.assertEqual(sibling.claims[0].atom, "cauchy(sqrt(sqrt(sqrt(sqrt(-sqrt(2) + sqrt(5))))))")
        self.assertEqual(sibling.open_gaps, ())
        product = run(
            Request(
                ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) * sqrt(sqrt(sqrt(sqrt(sqrt(5) - sqrt(2)))))",
                seed=1,
            )
        )
        self.assertEqual(product.claims[0].atom, "cauchy(sqrt(sqrt(sqrt(sqrt(3)))))")
        self.assertEqual(product.open_gaps, ())
        scaled = run(Request(ask="what is sqrt(4 * sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))", seed=1))
        self.assertEqual(scaled.claims[0].atom, "cauchy(2 * sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))")
        self.assertEqual(scaled.open_gaps, ())
        absorbed = run(Request(ask="what is sqrt(2) * sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))", seed=1))
        self.assertEqual(absorbed.claims[0].atom, "cauchy(sqrt(2 * sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))")
        direct = run(Request(ask="what is sqrt(2 * sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))", seed=1))
        self.assertEqual(direct.claims[0].atom, absorbed.claims[0].atom)
        inverse = run(Request(ask="what is 1 / sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))", seed=1))
        self.assertEqual(
            inverse.claims[0].atom,
            "cauchy(1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))))",
        )
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(
            Request(
                ask="prove sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) * (1 / sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            back.claims[0].atom,
            "identity(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) * (1 / sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        added = run(Request(ask="what is 1 + sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))", seed=1))
        self.assertEqual(added.claims[0].atom, "cauchy(1 + sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))")
        self.assertEqual(added.open_gaps, ())
        below = run(Request(ask="prove sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) <= 2", seed=1))
        self.assertEqual(below.claims[0].atom, "le(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))),2)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask="prove sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_le(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))),1)")
        self.assertEqual(above.open_gaps, ())
        members = run(Request(ask="what is {sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))}", seed=1))
        self.assertEqual(members.claims[0].atom, f"set({{{shown}}})")
        bound = run(Request(ask="what is sup {x. x <= sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))}", seed=1))
        self.assertEqual(bound.claims[0].atom, f"cauchy({shown})")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        self.assertEqual(bound.open_gaps, ())
        negative = run(Request(ask="what is sqrt(-sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in negative.claims))
        quotient = run(Request(ask="what is 1 / (1 + sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))", seed=1))
        self.assertIn("this quotient stays outside", quotient.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in quotient.claims))
        five = run(Request(ask="what is sqrt(1 + sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(five.claims[0].atom, "cauchy(sqrt(1 + sqrt(2) + sqrt(5)))")
        self.assertEqual(five.open_gaps, ())
        nest_pair = run(Request(ask="what is sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(nest_pair.claims[0].atom, "cauchy(sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)))")
        self.assertEqual(nest_pair.open_gaps, ())


    def test_denesting_sqrt_of_crest(self) -> None:
        nested = run(Request(ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))", seed=1))
        shown = "sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))"
        self.assertEqual(nested.claims[0].atom, f"cauchy({shown})")
        detail = nested.text(lod=2)
        self.assertIn("real_sqrt_unique", detail)
        self.assertIn("real_sqrt_pow2", detail)
        self.assertIn("real_sqrt_ge_zero", detail)
        self.assertIn("real_le_lsqrt", detail)
        self.assertIn("eq_Real", detail)
        self.assertNotIn("real_sqrt_le_iff", detail)
        self.assertNotIn("real_sqrt_minus", detail)
        self.assertEqual(nested.open_gaps, ())
        built = eval_real(parse_term("sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))"))
        self.assertEqual(built.form.summits, ((Ratio(1, 1), 1, 1, 1, 1, 1, 2, 1, 5),))
        self.assertEqual(built.form.crests, ())
        self.assertEqual(real_sqrt(eval_real(parse_term("sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))"))).form, built.form)
        square = run(
            Request(
                ask="prove sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) = sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))",
                seed=1,
            )
        )
        self.assertEqual(
            square.claims[0].atom,
            "identity(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) = sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))",
        )
        self.assertEqual(square.open_gaps, ())
        sibling = run(Request(ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(5) - sqrt(2))))))", seed=1))
        self.assertEqual(sibling.claims[0].atom, "cauchy(sqrt(sqrt(sqrt(sqrt(sqrt(-sqrt(2) + sqrt(5)))))))")
        self.assertEqual(sibling.open_gaps, ())
        product = run(
            Request(
                ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(5) - sqrt(2))))))",
                seed=1,
            )
        )
        self.assertEqual(product.claims[0].atom, "cauchy(sqrt(sqrt(sqrt(sqrt(sqrt(3))))))")
        self.assertEqual(product.open_gaps, ())
        scaled = run(Request(ask="what is sqrt(4 * sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))", seed=1))
        self.assertEqual(scaled.claims[0].atom, "cauchy(2 * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))")
        self.assertEqual(scaled.open_gaps, ())
        absorbed = run(Request(ask="what is sqrt(2) * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))", seed=1))
        self.assertEqual(absorbed.claims[0].atom, "cauchy(sqrt(2 * sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))")
        direct = run(Request(ask="what is sqrt(2 * sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))", seed=1))
        self.assertEqual(direct.claims[0].atom, absorbed.claims[0].atom)
        inverse = run(Request(ask="what is 1 / sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))", seed=1))
        self.assertEqual(
            inverse.claims[0].atom,
            "cauchy(1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))))))",
        )
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(
            Request(
                ask="prove sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) * (1 / sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            back.claims[0].atom,
            "identity(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) * (1 / sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        added = run(Request(ask="what is 1 + sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))", seed=1))
        self.assertEqual(added.claims[0].atom, "cauchy(1 + sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))")
        self.assertEqual(added.open_gaps, ())
        below = run(Request(ask="prove sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) <= 2", seed=1))
        self.assertEqual(below.claims[0].atom, "le(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))),2)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask="prove sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_le(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))),1)")
        self.assertEqual(above.open_gaps, ())
        members = run(Request(ask="what is {sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))}", seed=1))
        self.assertEqual(members.claims[0].atom, f"set({{{shown}}})")
        bound = run(Request(ask="what is sup {x. x <= sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))}", seed=1))
        self.assertEqual(bound.claims[0].atom, f"cauchy({shown})")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        self.assertEqual(bound.open_gaps, ())
        negative = run(Request(ask="what is sqrt(-sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in negative.claims))
        quotient = run(Request(ask="what is 1 / (1 + sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))", seed=1))
        self.assertIn("this quotient stays outside", quotient.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in quotient.claims))
        five = run(Request(ask="what is sqrt(1 + sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(five.claims[0].atom, "cauchy(sqrt(1 + sqrt(2) + sqrt(5)))")
        self.assertEqual(five.open_gaps, ())
        nest_pair = run(Request(ask="what is sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(nest_pair.claims[0].atom, "cauchy(sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)))")
        self.assertEqual(nest_pair.open_gaps, ())

    def test_denesting_sqrt_of_summit(self) -> None:
        nested = run(Request(ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))", seed=1))
        shown = "sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))"
        self.assertEqual(nested.claims[0].atom, f"cauchy({shown})")
        detail = nested.text(lod=2)
        self.assertIn("real_sqrt_unique", detail)
        self.assertIn("real_sqrt_pow2", detail)
        self.assertIn("real_sqrt_ge_zero", detail)
        self.assertIn("real_le_lsqrt", detail)
        self.assertIn("eq_Real", detail)
        self.assertNotIn("real_sqrt_le_iff", detail)
        self.assertNotIn("real_sqrt_minus", detail)
        self.assertEqual(nested.open_gaps, ())
        built = eval_real(parse_term("sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))"))
        self.assertEqual(built.form.apexes, ((Ratio(1, 1), 1, 1, 1, 1, 1, 1, 2, 1, 5),))
        self.assertEqual(built.form.summits, ())
        self.assertEqual(real_sqrt(eval_real(parse_term("sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))"))).form, built.form)
        square = run(
            Request(
                ask="prove sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) = sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))",
                seed=1,
            )
        )
        self.assertEqual(
            square.claims[0].atom,
            "identity(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) = sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))",
        )
        self.assertEqual(square.open_gaps, ())
        sibling = run(Request(ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(5) - sqrt(2)))))))", seed=1))
        self.assertEqual(sibling.claims[0].atom, "cauchy(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(-sqrt(2) + sqrt(5))))))))")
        self.assertEqual(sibling.open_gaps, ())
        product = run(
            Request(
                ask="what is sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(5) - sqrt(2)))))))",
                seed=1,
            )
        )
        self.assertEqual(product.claims[0].atom, "cauchy(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(3)))))))")
        self.assertEqual(product.open_gaps, ())
        scaled = run(Request(ask="what is sqrt(4 * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))", seed=1))
        self.assertEqual(scaled.claims[0].atom, "cauchy(2 * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))")
        self.assertEqual(scaled.open_gaps, ())
        absorbed = run(Request(ask="what is sqrt(2) * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))", seed=1))
        self.assertEqual(absorbed.claims[0].atom, "cauchy(sqrt(2 * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))")
        direct = run(Request(ask="what is sqrt(2 * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))", seed=1))
        self.assertEqual(direct.claims[0].atom, absorbed.claims[0].atom)
        inverse = run(Request(ask="what is 1 / sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))", seed=1))
        self.assertEqual(
            inverse.claims[0].atom,
            "cauchy(1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))))))",
        )
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(
            Request(
                ask="prove sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) * (1 / sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            back.claims[0].atom,
            "identity(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) * (1 / sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))) = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        added = run(Request(ask="what is 1 + sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))", seed=1))
        self.assertEqual(added.claims[0].atom, "cauchy(1 + sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))")
        self.assertEqual(added.open_gaps, ())
        below = run(Request(ask="prove sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) <= 2", seed=1))
        self.assertEqual(below.claims[0].atom, "le(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))),2)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask="prove sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, "not_le(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))),1)")
        self.assertEqual(above.open_gaps, ())
        members = run(Request(ask="what is {sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))}", seed=1))
        self.assertEqual(members.claims[0].atom, f"set({{{shown}}})")
        bound = run(Request(ask="what is sup {x. x <= sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))}", seed=1))
        self.assertEqual(bound.claims[0].atom, f"cauchy({shown})")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        self.assertEqual(bound.open_gaps, ())
        negative = run(Request(ask="what is sqrt(-sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in negative.claims))
        quotient = run(Request(ask="what is 1 / (1 + sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))", seed=1))
        self.assertIn("this quotient stays outside", quotient.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in quotient.claims))
        five = run(Request(ask="what is sqrt(1 + sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(five.claims[0].atom, "cauchy(sqrt(1 + sqrt(2) + sqrt(5)))")
        self.assertEqual(five.open_gaps, ())
        nest_pair = run(Request(ask="what is sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(nest_pair.claims[0].atom, "cauchy(sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)))")
        self.assertEqual(nest_pair.open_gaps, ())

    def test_iterated_square_root(self) -> None:
        def wrap(body: str, count: int) -> str:
            for _ in range(count):
                body = f"sqrt({body})"
            return body

        apex = wrap("sqrt(2) + sqrt(5)", 6)
        eighth = wrap(apex, 1)
        ninth = wrap(eighth, 1)
        tenth = wrap(ninth, 1)
        nested = run(Request(ask=f"what is {eighth}", seed=1))
        self.assertEqual(nested.claims[0].atom, f"cauchy({eighth})")
        detail = nested.text(lod=2)
        self.assertIn("real_sqrt_unique", detail)
        self.assertIn("real_sqrt_pow2", detail)
        self.assertIn("real_sqrt_ge_zero", detail)
        self.assertIn("real_le_lsqrt", detail)
        self.assertIn("eq_Real", detail)
        self.assertNotIn("real_sqrt_le_iff", detail)
        self.assertNotIn("real_sqrt_minus", detail)
        self.assertEqual(nested.open_gaps, ())
        built = eval_real(parse_term(eighth))
        self.assertEqual(
            built.form.shells,
            ((Ratio(1, 1), (1,), 1, 1, 1, 1, 1, 1, 2, 1, 5),),
        )
        self.assertEqual(built.form.apexes, ())
        self.assertEqual(real_sqrt(eval_real(parse_term(apex))).form, built.form)
        again = run(Request(ask=f"what is {ninth}", seed=1))
        self.assertEqual(again.claims[0].atom, f"cauchy({ninth})")
        self.assertEqual(again.open_gaps, ())
        self.assertEqual(
            eval_real(parse_term(ninth)).form.shells,
            ((Ratio(1, 1), (1, 1), 1, 1, 1, 1, 1, 1, 2, 1, 5),),
        )
        further = run(Request(ask=f"what is {tenth}", seed=1))
        self.assertEqual(further.claims[0].atom, f"cauchy({tenth})")
        self.assertEqual(further.open_gaps, ())
        self.assertEqual(
            eval_real(parse_term(tenth)).form.shells[0][1],
            (1, 1, 1),
        )
        square = run(Request(ask=f"prove {eighth} * {eighth} = {apex}", seed=1))
        self.assertEqual(square.claims[0].atom, f"identity({eighth} * {eighth} = {apex})")
        self.assertEqual(square.open_gaps, ())
        square_again = run(Request(ask=f"prove {ninth} * {ninth} = {eighth}", seed=1))
        self.assertEqual(square_again.claims[0].atom, f"identity({ninth} * {ninth} = {eighth})")
        self.assertEqual(square_again.open_gaps, ())
        conj = wrap("-sqrt(2) + sqrt(5)", 7)
        sibling = run(Request(ask=f"what is {wrap('sqrt(5) - sqrt(2)', 7)}", seed=1))
        self.assertEqual(sibling.claims[0].atom, f"cauchy({conj})")
        self.assertEqual(sibling.open_gaps, ())
        three = wrap("3", 7)
        product = run(
            Request(ask=f"what is {eighth} * {wrap('sqrt(5) - sqrt(2)', 7)}", seed=1)
        )
        self.assertEqual(product.claims[0].atom, f"cauchy({three})")
        self.assertEqual(product.open_gaps, ())
        scaled = run(Request(ask=f"what is sqrt(4 * {apex})", seed=1))
        self.assertEqual(scaled.claims[0].atom, f"cauchy(2 * {eighth})")
        self.assertEqual(scaled.open_gaps, ())
        absorbed = run(Request(ask=f"what is sqrt(2) * {eighth}", seed=1))
        self.assertEqual(absorbed.claims[0].atom, f"cauchy(sqrt(2 * {apex}))")
        direct = run(Request(ask=f"what is sqrt(2 * {apex})", seed=1))
        self.assertEqual(direct.claims[0].atom, absorbed.claims[0].atom)
        inverse = run(Request(ask=f"what is 1 / {eighth}", seed=1))
        inverse_shown = (
            "1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))))))"
        )
        self.assertEqual(inverse.claims[0].atom, f"cauchy({inverse_shown})")
        self.assertEqual(
            eval_real(parse_term(f"1 / ({eighth})")).form.shells,
            ((Ratio(1, 3), (3,), 3, 3, 3, 3, 3, -3, 2, 3, 5),),
        )
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(Request(ask=f"prove {eighth} * (1 / {eighth}) = 1", seed=1))
        self.assertEqual(back.claims[0].atom, f"identity({eighth} * (1 / {eighth}) = 1)")
        self.assertEqual(back.open_gaps, ())
        below = run(Request(ask=f"prove {eighth} <= 2", seed=1))
        self.assertEqual(below.claims[0].atom, f"le({eighth},2)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask=f"prove {eighth} <= 1", seed=1))
        self.assertEqual(above.claims[0].atom, f"not_le({eighth},1)")
        self.assertEqual(above.open_gaps, ())
        members = run(Request(ask=f"what is {{{eighth}}}", seed=1))
        self.assertEqual(members.claims[0].atom, f"set({{{eighth}}})")
        bound = run(Request(ask=f"what is sup {{x. x <= {eighth}}}", seed=1))
        self.assertEqual(bound.claims[0].atom, f"cauchy({eighth})")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        self.assertEqual(bound.open_gaps, ())
        negative = run(Request(ask=f"what is sqrt(-{eighth})", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in negative.claims))
        quotient = run(Request(ask=f"what is 1 / (1 + {eighth})", seed=1))
        self.assertIn("this quotient stays outside", quotient.text(lod=1))
        five = run(Request(ask="what is sqrt(1 + sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(five.claims[0].atom, "cauchy(sqrt(1 + sqrt(2) + sqrt(5)))")
        self.assertEqual(five.open_gaps, ())
        nest_pair = run(Request(ask="what is sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(nest_pair.claims[0].atom, "cauchy(sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)))")
        self.assertEqual(nest_pair.open_gaps, ())

    def test_further_square_root_of_the_nested_binomial(self) -> None:
        triple = "sqrt(sqrt(sqrt(2 + sqrt(2))))"
        fourth = f"sqrt({triple})"
        nested = run(Request(ask=f"what is {fourth}", seed=1))
        self.assertEqual(nested.claims[0].atom, f"cauchy({fourth})")
        self.assertIn("real_sqrt_unique", nested.text(lod=2))
        self.assertEqual(nested.open_gaps, ())
        self.assertEqual(
            eval_real(parse_term(fourth)).form.folds,
            ((Ratio(1, 1), (1, 1), 1, 2, 1, 2),),
        )
        square = run(Request(ask=f"prove {fourth} * {fourth} = {triple}", seed=1))
        self.assertEqual(square.claims[0].atom, f"identity({fourth} * {fourth} = {triple})")
        self.assertEqual(square.open_gaps, ())
        product = run(
            Request(
                ask="what is sqrt(sqrt(sqrt(2 + sqrt(2)))) * sqrt(sqrt(sqrt(2 - sqrt(2))))",
                seed=1,
            )
        )
        self.assertEqual(product.claims[0].atom, "cauchy(sqrt(sqrt(sqrt(2))))")
        self.assertEqual(product.open_gaps, ())
        other = run(Request(ask="what is 1 / sqrt(sqrt(6) + sqrt(2))", seed=1))
        self.assertEqual(
            other.claims[0].atom,
            "cauchy(-1/4 * sqrt(-4 + 2 * sqrt(6)) + 1/4 * sqrt(4 + 2 * sqrt(6)))",
        )
        self.assertEqual(other.open_gaps, ())
        back = run(
            Request(
                ask="prove (1 / sqrt(sqrt(6) + sqrt(2))) * sqrt(sqrt(6) + sqrt(2)) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            back.claims[0].atom,
            "identity(1 / sqrt(sqrt(6) + sqrt(2)) * sqrt(sqrt(6) + sqrt(2)) = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        quotient = run(Request(ask=f"what is 1 / (1 + {triple})", seed=1))
        self.assertIn("this quotient stays outside", quotient.text(lod=1))
        negative = run(Request(ask=f"what is sqrt(-{triple})", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))

    def test_inverse_of_a_further_nested_binomial(self) -> None:
        triple = "sqrt(sqrt(sqrt(2 + sqrt(2))))"
        shown = (
            "sqrt(sqrt(2 * sqrt(676 + 478 * sqrt(2)))) "
            "- 1/2 * sqrt(2 * sqrt(2 * sqrt(676 + 478 * sqrt(2))))"
        )
        inverse = run(Request(ask=f"what is 1 / {triple}", seed=1))
        self.assertEqual(inverse.claims[0].atom, f"cauchy({shown})")
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(
            Request(
                ask=f"prove (1 / {triple}) * {triple} = 1",
                seed=1,
            )
        )
        self.assertEqual(
            back.claims[0].atom,
            f"identity(1 / {triple} * {triple} = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        fourth = f"sqrt({triple})"
        deeper_shown = (
            "sqrt(sqrt(2 * sqrt(2 * sqrt(780100 + 551614 * sqrt(2))))) "
            "- 1/2 * sqrt(2 * sqrt(2 * sqrt(2 * sqrt(780100 + 551614 * sqrt(2)))))"
        )
        deeper = run(Request(ask=f"what is 1 / {fourth}", seed=1))
        self.assertEqual(deeper.claims[0].atom, f"cauchy({deeper_shown})")
        self.assertIn("inverse_unique", deeper.text(lod=2))
        self.assertEqual(deeper.open_gaps, ())
        deeper_back = run(
            Request(
                ask=f"prove (1 / {fourth}) * {fourth} = 1",
                seed=1,
            )
        )
        self.assertEqual(
            deeper_back.claims[0].atom,
            f"identity(1 / {fourth} * {fourth} = 1)",
        )
        self.assertEqual(deeper_back.open_gaps, ())
        shifted = run(Request(ask=f"what is 1 / (1 + {triple})", seed=1))
        self.assertIn("this quotient stays outside", shifted.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in shifted.claims))

    def test_sqrt_of_one_plus_sqrt_two_plus_sqrt_five(self) -> None:
        shown = "sqrt(1 + sqrt(2) + sqrt(5))"
        nested = run(Request(ask=f"what is {shown}", seed=1))
        self.assertEqual(nested.claims[0].atom, f"cauchy({shown})")
        self.assertIn("real_sqrt_unique", nested.text(lod=2))
        self.assertEqual(nested.open_gaps, ())
        self.assertEqual(
            eval_real(parse_term(shown)).form.quads,
            ((Ratio(1, 1), Ratio(1, 1), Ratio(1, 1), 2, Ratio(1, 1), 5, Ratio(0, 1)),),
        )
        square = run(Request(ask=f"prove {shown} * {shown} = 1 + sqrt(2) + sqrt(5)", seed=1))
        self.assertEqual(
            square.claims[0].atom,
            f"identity({shown} * {shown} = 1 + sqrt(2) + sqrt(5))",
        )
        self.assertEqual(square.open_gaps, ())
        denested = run(
            Request(
                ask="what is sqrt(8 + 2 * sqrt(2) + 2 * sqrt(5) + 2 * sqrt(10))",
                seed=1,
            )
        )
        self.assertEqual(denested.claims[0].atom, "cauchy(1 + sqrt(2) + sqrt(5))")
        self.assertEqual(denested.open_gaps, ())
        scaled = run(Request(ask="what is sqrt(4 + 4 * sqrt(2) + 4 * sqrt(5))", seed=1))
        self.assertEqual(scaled.claims[0].atom, f"cauchy(2 * {shown})")
        self.assertEqual(scaled.open_gaps, ())
        absorbed = run(Request(ask=f"what is sqrt(2) * {shown}", seed=1))
        self.assertEqual(absorbed.claims[0].atom, "cauchy(sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5)))")
        direct = run(Request(ask="what is sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5))", seed=1))
        self.assertEqual(direct.claims[0].atom, absorbed.claims[0].atom)
        inverse_shown = (
            "3/2 * sqrt(1 + sqrt(2) + sqrt(5)) + sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5))"
            " - 1/2 * sqrt(5 + 5 * sqrt(2) + 5 * sqrt(5))"
            " - 1/2 * sqrt(10 + 10 * sqrt(2) + 10 * sqrt(5))"
        )
        inverse = run(Request(ask=f"what is 1 / {shown}", seed=1))
        self.assertEqual(inverse.claims[0].atom, f"cauchy({inverse_shown})")
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(Request(ask=f"prove (1 / {shown}) * {shown} = 1", seed=1))
        self.assertEqual(
            back.claims[0].atom,
            f"identity(1 / {shown} * {shown} = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        below = run(Request(ask=f"prove {shown} <= 3", seed=1))
        self.assertEqual(below.claims[0].atom, f"le({shown},3)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask=f"prove {shown} <= 2", seed=1))
        self.assertEqual(above.claims[0].atom, f"not_le({shown},2)")
        self.assertEqual(above.open_gaps, ())
        members = run(Request(ask=f"what is {{{shown}}}", seed=1))
        self.assertEqual(members.claims[0].atom, f"set({{{shown}}})")
        bound = run(Request(ask=f"what is sup {{x. x <= {shown}}}", seed=1))
        self.assertEqual(bound.claims[0].atom, f"cauchy({shown})")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        self.assertEqual(bound.open_gaps, ())
        negative = run(Request(ask=f"what is sqrt(-{shown})", seed=1))
        self.assertIn("square root of a negative stays open", negative.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in negative.claims))
        shifted_shown = (
            "1/3 * sqrt(2) - 1/3 * sqrt(5)"
            " - 1/3 * sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5))"
            " + 1/3 * sqrt(5 + 5 * sqrt(2) + 5 * sqrt(5))"
        )
        shifted = run(Request(ask=f"what is 1 / (1 + {shown})", seed=1))
        self.assertEqual(shifted.claims[0].atom, f"cauchy({shifted_shown})")
        self.assertIn("inverse_unique", shifted.text(lod=2))
        self.assertEqual(shifted.open_gaps, ())
        shifted_back = run(
            Request(
                ask=f"prove (1 / (1 + {shown})) * (1 + {shown}) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            shifted_back.claims[0].atom,
            f"identity(1 / (1 + {shown}) * (1 + {shown}) = 1)",
        )
        self.assertEqual(shifted_back.open_gaps, ())
        nest_pair = run(Request(ask="what is sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))", seed=1))
        self.assertEqual(nest_pair.claims[0].atom, "cauchy(sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)))")
        self.assertEqual(nest_pair.open_gaps, ())

    def test_nest_times_the_pair(self) -> None:
        ask = "sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))"
        shown = "sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10))"
        product = run(Request(ask=f"what is {ask}", seed=1))
        self.assertEqual(product.claims[0].atom, f"cauchy({shown})")
        self.assertIn("real_sqrt_unique", product.text(lod=2))
        self.assertEqual(product.open_gaps, ())
        self.assertEqual(
            eval_real(parse_term(ask)).form.quads,
            ((Ratio(1, 1), Ratio(2, 1), Ratio(2, 1), 2, Ratio(2, 1), 5, Ratio(1, 1)),),
        )
        direct = run(Request(ask=f"what is {shown}", seed=1))
        self.assertEqual(direct.claims[0].atom, product.claims[0].atom)
        reversed_ask = run(Request(ask="what is sqrt(sqrt(2) + sqrt(5)) * sqrt(2 + sqrt(2))", seed=1))
        self.assertEqual(reversed_ask.claims[0].atom, product.claims[0].atom)
        square = run(Request(ask=f"prove ({ask}) * ({ask}) = 2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)", seed=1))
        self.assertEqual(
            square.claims[0].atom,
            "identity(sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5)) * (sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))) = 2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10))",
        )
        self.assertEqual(square.open_gaps, ())
        inverse_shown = (
            "1/3 * sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10))"
            " - 1/3 * sqrt(4 + 4 * sqrt(2) + 4 * sqrt(5) + 2 * sqrt(10))"
            " + 1/3 * sqrt(10 + 10 * sqrt(2) + 10 * sqrt(5) + 5 * sqrt(10))"
            " - 1/6 * sqrt(20 + 20 * sqrt(2) + 20 * sqrt(5) + 10 * sqrt(10))"
        )
        inverse = run(Request(ask=f"what is 1 / ({ask})", seed=1))
        self.assertEqual(inverse.claims[0].atom, f"cauchy({inverse_shown})")
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(Request(ask=f"prove (1 / ({ask})) * ({ask}) = 1", seed=1))
        self.assertEqual(
            back.claims[0].atom,
            "identity(1 / (sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))) * (sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))) = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        below = run(Request(ask=f"prove {ask} <= 4", seed=1))
        self.assertEqual(below.claims[0].atom, f"le({ask},4)")
        self.assertEqual(below.open_gaps, ())
        above = run(Request(ask=f"prove {ask} <= 3", seed=1))
        self.assertEqual(above.claims[0].atom, f"not_le({ask},3)")
        self.assertEqual(above.open_gaps, ())
        members = run(Request(ask=f"what is {{{shown}}}", seed=1))
        self.assertEqual(members.claims[0].atom, f"set({{{shown}}})")
        bound = run(Request(ask=f"what is sup {{x. x <= {shown}}}", seed=1))
        self.assertEqual(bound.claims[0].atom, f"cauchy({shown})")
        self.assertIn("cSup_atMost", bound.text(lod=2))
        self.assertEqual(bound.open_gaps, ())
        shifted_shown = (
            "43/71 - 26/71 * sqrt(2) + 10/71 * sqrt(5) - 11/71 * sqrt(10)"
            " - 43/71 * sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10))"
            " + 26/71 * sqrt(4 + 4 * sqrt(2) + 4 * sqrt(5) + 2 * sqrt(10))"
            " - 10/71 * sqrt(10 + 10 * sqrt(2) + 10 * sqrt(5) + 5 * sqrt(10))"
            " + 11/71 * sqrt(20 + 20 * sqrt(2) + 20 * sqrt(5) + 10 * sqrt(10))"
        )
        shifted = run(Request(ask=f"what is 1 / (1 + {shown})", seed=1))
        self.assertEqual(shifted.claims[0].atom, f"cauchy({shifted_shown})")
        self.assertIn("inverse_unique", shifted.text(lod=2))
        self.assertEqual(shifted.open_gaps, ())
        shifted_back = run(
            Request(
                ask=f"prove (1 / (1 + {shown})) * (1 + {shown}) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            shifted_back.claims[0].atom,
            f"identity(1 / (1 + {shown}) * (1 + {shown}) = 1)",
        )
        self.assertEqual(shifted_back.open_gaps, ())
        ladder = run(Request(ask="what is 1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))", seed=1))
        self.assertIn("this quotient stays outside", ladder.text(lod=1))


    def test_inverse_of_one_plus_a_shifted_radical(self) -> None:
        pair = "sqrt(sqrt(2) + sqrt(5))"
        pair_shown = (
            "3/2 - sqrt(2) + 1/2 * sqrt(5) - 1/2 * sqrt(10)"
            " - 3/2 * sqrt(sqrt(2) + sqrt(5)) + sqrt(2 * sqrt(2) + 2 * sqrt(5))"
            " - 1/2 * sqrt(5 * sqrt(2) + 5 * sqrt(5)) + 1/2 * sqrt(10 * sqrt(2) + 10 * sqrt(5))"
        )
        inverse = run(Request(ask=f"what is 1 / (1 + {pair})", seed=1))
        self.assertEqual(inverse.claims[0].atom, f"cauchy({pair_shown})")
        self.assertIn("inverse_unique", inverse.text(lod=2))
        self.assertEqual(inverse.open_gaps, ())
        back = run(
            Request(
                ask=f"prove (1 / (1 + {pair})) * (1 + {pair}) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            back.claims[0].atom,
            f"identity(1 / (1 + {pair}) * (1 + {pair}) = 1)",
        )
        self.assertEqual(back.open_gaps, ())
        product = run(
            Request(
                ask="what is sqrt(sqrt(sqrt(2 + sqrt(2)))) * sqrt(2 + sqrt(2))",
                seed=1,
            )
        )
        self.assertEqual(
            product.claims[0].atom,
            "cauchy(sqrt(sqrt(2 * sqrt(58 + 41 * sqrt(2)))))",
        )
        self.assertEqual(product.open_gaps, ())
        reversed_ask = run(
            Request(
                ask="what is sqrt(2 + sqrt(2)) * sqrt(sqrt(sqrt(2 + sqrt(2))))",
                seed=1,
            )
        )
        self.assertEqual(reversed_ask.claims[0].atom, product.claims[0].atom)
        fold = run(Request(ask="what is 1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))", seed=1))
        self.assertIn("this quotient stays outside", fold.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in fold.claims))
        peak = run(
            Request(
                ask="what is 1 / (1 + sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))",
                seed=1,
            )
        )
        self.assertIn("this quotient stays outside", peak.text(lod=1))
        self.assertFalse(any(claim.atom.startswith("cauchy(") for claim in peak.claims))

    def test_integer_order_is_unchanged(self) -> None:

        held = run(Request(ask="prove 2 <= 5", seed=1))
        self.assertEqual(held.claims[0].atom, "le(2,5)")
        self.assertNotIn("cauchy", held.text(lod=2))
        quotient = run(Request(ask="what is 8 / 2", seed=1))
        self.assertEqual(quotient.claims[0].atom, "value(4)")
        self.assertIn("Int.ediv", quotient.text(lod=2))

    def test_anchors_and_clashes(self) -> None:
        measured = run(Request(ask="what is sqrt(length)", facts=("length=4@meter stick",), seed=1))
        self.assertEqual(measured.claims[0].atom, "value(2)")
        self.assertIn("meter stick", measured.text(lod=2))
        self.assertEqual(measured.open_gaps, ())
        clash = run(
            Request(
                ask="what is sqrt(length)",
                facts=("length=4@first tape", "length=5@second tape"),
                seed=1,
            )
        )
        self.assertEqual(clash.claims, ())
        self.assertIn("value(4)", clash.retracted)
        self.assertIn("value(5)", clash.retracted)
        self.assertNotIn("cauchy(", clash.text(lod=1))
        free = run(Request(ask="prove sqrt(x) = x", seed=1))
        self.assertIn("is not a theorem", free.text(lod=1))

    def test_forged_real_is_rejected(self) -> None:
        with self.assertRaises(KernelError):
            RealTheorem(RealForm(Ratio(2, 4), ()), "Real.of_rat")
        with self.assertRaises(KernelError):
            RealTheorem(RealForm(Ratio(0, 1), ((Ratio(1, 1), 4),)), "Real.sqrt", (real_of_rat(Ratio(4, 1)),))
        with self.assertRaises(KernelError):
            RealTheorem(RealForm(Ratio(2, 1), ()), "Real.sqrt", (real_of_rat(Ratio(3, 1)),))
        shown = real_of_rat(Ratio(2, 4))
        self.assertEqual(shown.form.constant, Ratio(1, 2))
        root = real_sqrt(real_of_rat(Ratio(2, 1)))
        with self.assertRaises(KernelError):
            RealTheorem(RealForm(Ratio(0, 1), (), ((Ratio(1, 1), 2, 1, 3),)), "Real.sqrt", (root,))
        three = real_sqrt(real_of_rat(Ratio(3, 1)))
        built = real_div(root, three)
        self.assertEqual(show_form(built.form), "1/3 * sqrt(6)")
        accepted = RealTheorem(built.form, "Real.div", (root, three))
        self.assertEqual(show_form(accepted.form), "1/3 * sqrt(6)")
        with self.assertRaises(KernelError):
            RealTheorem(RealForm(Ratio(1, 1), ()), "Real.div", (root, three))
        with self.assertRaises(KernelError):
            RealTheorem(RealForm(Ratio(1, 1), ()), "Real.div", (root, real_of_rat(Ratio(0, 1))))
        fourth = real_sqrt(root)
        fourth_three = real_sqrt(three)
        built_product = real_mul(root, fourth_three)
        self.assertEqual(show_form(built_product.form), "sqrt(sqrt(12))")
        self.assertEqual(built_product.form.towers, ((Ratio(1, 1), 12, 1, 2),))
        accepted_product = RealTheorem(built_product.form, "Real.mul", (root, fourth_three))
        self.assertEqual(show_form(accepted_product.form), "sqrt(sqrt(12))")
        with self.assertRaises(KernelError):
            RealTheorem(RealForm(Ratio(1, 1), ()), "Real.mul", (root, fourth_three))
        forged_power = RealForm(Ratio(0, 1), (), ((Ratio(1, 1), 8, 1, 2),))
        self.assertFalse(_canonical(forged_power))
        self.assertTrue(_canonical(RealForm(Ratio(0, 1), (), ((Ratio(1, 1), 2, 3, 2),))))
        self.assertTrue(_canonical(built_product.form))
        with self.assertRaises(KernelError):
            RealTheorem(forged_power, "Real.mul", (root, fourth_three))
        preserved = real_mul(root, fourth)
        self.assertEqual(preserved.form.towers, ((Ratio(1, 1), 2, 3, 2),))
        self.assertEqual(show_form(preserved.form), "sqrt(sqrt(8))")
        built_quotient = real_div(fourth, fourth_three)
        self.assertEqual(show_form(built_quotient.form), "1/3 * sqrt(sqrt(54))")
        accepted_quotient = RealTheorem(built_quotient.form, "Real.div", (fourth, fourth_three))
        self.assertEqual(show_form(accepted_quotient.form), "1/3 * sqrt(sqrt(54))")
        with self.assertRaises(KernelError):
            RealTheorem(RealForm(Ratio(1, 1), ()), "Real.div", (fourth, fourth_three))
        binomial = eval_real(parse_term("2 + sqrt(2)"))
        built_nest = real_sqrt(binomial)
        self.assertEqual(show_form(built_nest.form), "sqrt(2 + sqrt(2))")
        self.assertEqual(
            built_nest.form.nests,
            ((Ratio(1, 1), Ratio(2, 1), Ratio(1, 1), 2),),
        )
        accepted_nest = RealTheorem(built_nest.form, "Real.sqrt", (binomial,))
        self.assertEqual(show_form(accepted_nest.form), "sqrt(2 + sqrt(2))")
        with self.assertRaises(KernelError):
            RealTheorem(RealForm(Ratio(2, 1), ()), "Real.sqrt", (binomial,))
        with self.assertRaises(KernelError):
            RealTheorem(RealForm(Ratio(1, 1), ((Ratio(1, 1), 2),)), "Real.sqrt", (binomial,))
        with self.assertRaises(KernelError):
            RealTheorem(
                RealForm(Ratio(0, 1), (), ((Ratio(1, 1), 12, 1, 2),)),
                "Real.sqrt",
                (binomial,),
            )
        forged_denest = RealForm(
            Ratio(0, 1),
            (),
            (),
            ((Ratio(1, 1), Ratio(3, 1), Ratio(2, 1), 2),),
        )
        self.assertFalse(_canonical(forged_denest))
        with self.assertRaises(KernelError):
            RealTheorem(forged_denest, "Real.sqrt", (binomial,))
        forged_content = RealForm(
            Ratio(0, 1),
            (),
            (),
            ((Ratio(1, 1), Ratio(8, 1), Ratio(8, 1), 2),),
        )
        self.assertFalse(_canonical(forged_content))
        self.assertTrue(_canonical(built_nest.form))
        pair = eval_real(parse_term("sqrt(2) + sqrt(3)"))
        built_pair = real_sqrt(pair)
        pair_shown = "1/2 * sqrt(-2 + 2 * sqrt(3)) + 1/2 * sqrt(2 + 2 * sqrt(3))"
        self.assertEqual(show_form(built_pair.form), pair_shown)
        accepted_pair = RealTheorem(built_pair.form, "Real.sqrt", (pair,))
        self.assertEqual(show_form(accepted_pair.form), pair_shown)
        self.assertTrue(_canonical(built_pair.form))
        with self.assertRaises(KernelError):
            RealTheorem(built_nest.form, "Real.sqrt", (pair,))
        one_half = RealForm(
            Ratio(0, 1),
            (),
            (),
            ((Ratio(1, 2), Ratio(-2, 1), Ratio(2, 1), 3),),
        )
        self.assertTrue(_canonical(one_half))
        with self.assertRaises(KernelError):
            RealTheorem(one_half, "Real.sqrt", (pair,))
        swapped = RealForm(
            Ratio(0, 1),
            (),
            (),
            (
                (Ratio(-1, 2), Ratio(-2, 1), Ratio(2, 1), 3),
                (Ratio(1, 2), Ratio(2, 1), Ratio(2, 1), 3),
            ),
        )
        self.assertTrue(_canonical(swapped))
        with self.assertRaises(KernelError):
            RealTheorem(swapped, "Real.sqrt", (pair,))
        radical = eval_real(parse_term("sqrt(2) + sqrt(5)"))
        built_radical = real_sqrt(radical)
        self.assertEqual(show_form(built_radical.form), "sqrt(sqrt(2) + sqrt(5))")
        self.assertEqual(built_radical.form.pairs, ((Ratio(1, 1), 1, 2, 1, 5),))
        accepted_radical = RealTheorem(built_radical.form, "Real.sqrt", (radical,))
        self.assertEqual(show_form(accepted_radical.form), "sqrt(sqrt(2) + sqrt(5))")
        self.assertTrue(_canonical(built_radical.form))
        with self.assertRaises(KernelError):
            RealTheorem(radical.form, "Real.sqrt", (radical,))
        with self.assertRaises(KernelError):
            RealTheorem(built_nest.form, "Real.sqrt", (radical,))
        denestable_pair = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 2, 1, 3),),
        )
        self.assertFalse(_canonical(denestable_pair))
        with self.assertRaises(KernelError):
            RealTheorem(denestable_pair, "Real.sqrt", (radical,))
        unreduced_pair = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            ((Ratio(1, 1), 4, 2, 4, 5),),
        )
        self.assertFalse(_canonical(unreduced_pair))
        with self.assertRaises(KernelError):
            RealTheorem(unreduced_pair, "Real.sqrt", (radical,))
        swapped_rads = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 5, 1, 2),),
        )
        self.assertFalse(_canonical(swapped_rads))
        other_pair = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 3, 1, 5),),
        )
        self.assertTrue(_canonical(other_pair))
        with self.assertRaises(KernelError):
            RealTheorem(other_pair, "Real.sqrt", (radical,))
        conjugate_pair = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            ((Ratio(1, 1), -1, 2, 1, 5),),
        )
        self.assertTrue(_canonical(conjugate_pair))
        with self.assertRaises(KernelError):
            RealTheorem(conjugate_pair, "Real.sqrt", (radical,))
        built_deep = real_sqrt(built_nest)
        self.assertEqual(show_form(built_deep.form), "sqrt(sqrt(2 + sqrt(2)))")
        self.assertEqual(built_deep.form.deeps, ((Ratio(1, 1), 1, 2, 1, 2),))
        accepted_deep = RealTheorem(built_deep.form, "Real.sqrt", (built_nest,))
        self.assertEqual(show_form(accepted_deep.form), "sqrt(sqrt(2 + sqrt(2)))")
        self.assertTrue(_canonical(built_deep.form))
        with self.assertRaises(KernelError):
            RealTheorem(built_nest.form, "Real.sqrt", (built_nest,))
        denestable_deep = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 3, 2, 2),),
        )
        self.assertFalse(_canonical(denestable_deep))
        with self.assertRaises(KernelError):
            RealTheorem(denestable_deep, "Real.sqrt", (built_nest,))
        unreduced_deep = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 4, 2, 1, 2),),
        )
        self.assertFalse(_canonical(unreduced_deep))
        with self.assertRaises(KernelError):
            RealTheorem(unreduced_deep, "Real.sqrt", (built_nest,))
        other_deep = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 3, 1, 2),),
        )
        self.assertTrue(_canonical(other_deep))
        with self.assertRaises(KernelError):
            RealTheorem(other_deep, "Real.sqrt", (built_nest,))
        with self.assertRaises(KernelError):
            RealTheorem(built_radical.form, "Real.sqrt", (built_nest,))
        built_high = real_sqrt(built_radical)
        self.assertEqual(show_form(built_high.form), "sqrt(sqrt(sqrt(2) + sqrt(5)))")
        self.assertEqual(built_high.form.highs, ((Ratio(1, 1), 1, 1, 2, 1, 5),))
        self.assertEqual(built_high.form.pairs, ())
        self.assertEqual(built_high.form.deeps, ())
        accepted_high = RealTheorem(built_high.form, "Real.sqrt", (built_radical,))
        self.assertEqual(show_form(accepted_high.form), "sqrt(sqrt(sqrt(2) + sqrt(5)))")
        self.assertTrue(_canonical(built_high.form))
        with self.assertRaises(KernelError):
            RealTheorem(built_radical.form, "Real.sqrt", (built_radical,))
        denestable_high = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 2, 1, 3),),
        )
        self.assertFalse(_canonical(denestable_high))
        with self.assertRaises(KernelError):
            RealTheorem(denestable_high, "Real.sqrt", (built_radical,))
        unreduced_high = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 4, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_high))
        with self.assertRaises(KernelError):
            RealTheorem(unreduced_high, "Real.sqrt", (built_radical,))
        other_high = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 3, 1, 5),),
        )
        self.assertTrue(_canonical(other_high))
        with self.assertRaises(KernelError):
            RealTheorem(other_high, "Real.sqrt", (built_radical,))
        swapped_high = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 5, 1, 2),),
        )
        self.assertFalse(_canonical(swapped_high))
        with self.assertRaises(KernelError):
            RealTheorem(built_deep.form, "Real.sqrt", (built_radical,))
        built_peak = real_sqrt(built_high)
        self.assertEqual(show_form(built_peak.form), "sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))")
        self.assertEqual(built_peak.form.peaks, ((Ratio(1, 1), 1, 1, 1, 2, 1, 5),))
        self.assertEqual(built_peak.form.highs, ())
        accepted_peak = RealTheorem(built_peak.form, "Real.sqrt", (built_high,))
        self.assertEqual(show_form(accepted_peak.form), "sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))")
        self.assertTrue(_canonical(built_peak.form))
        inverted = real_div(real_of_rat(Ratio(1, 1)), built_peak)
        self.assertEqual(
            show_form(inverted.form),
            "1/3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))",
        )
        self.assertEqual(inverted.form.peaks, ((Ratio(1, 3), 3, 3, -3, 2, 3, 5),))
        with self.assertRaises(KernelError):
            RealTheorem(built_high.form, "Real.sqrt", (built_high,))
        denestable_peak = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 2, 1, 3),),
        )
        self.assertFalse(_canonical(denestable_peak))
        with self.assertRaises(KernelError):
            RealTheorem(denestable_peak, "Real.sqrt", (built_high,))
        unreduced_pmult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 4, 1, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_pmult))
        unreduced_hmult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 4, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_hmult))
        with self.assertRaises(KernelError):
            RealTheorem(unreduced_pmult, "Real.sqrt", (built_high,))
        other_peak = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 3, 1, 5),),
        )
        self.assertTrue(_canonical(other_peak))
        with self.assertRaises(KernelError):
            RealTheorem(other_peak, "Real.sqrt", (built_high,))
        swapped_peak = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 5, 1, 2),),
        )
        self.assertFalse(_canonical(swapped_peak))
        with self.assertRaises(KernelError):
            RealTheorem(swapped_peak, "Real.sqrt", (built_high,))
        built_crest = real_sqrt(built_peak)
        self.assertEqual(show_form(built_crest.form), "sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))")
        self.assertEqual(built_crest.form.crests, ((Ratio(1, 1), 1, 1, 1, 1, 2, 1, 5),))
        self.assertEqual(built_crest.form.peaks, ())
        self.assertEqual(built_crest.form.highs, ())
        accepted_crest = RealTheorem(built_crest.form, "Real.sqrt", (built_peak,))
        self.assertEqual(show_form(accepted_crest.form), "sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))")
        self.assertTrue(_canonical(built_crest.form))
        inverted_crest = real_div(real_of_rat(Ratio(1, 1)), built_crest)
        self.assertEqual(
            show_form(inverted_crest.form),
            "1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))))",
        )
        self.assertEqual(inverted_crest.form.crests, ((Ratio(1, 3), 3, 3, 3, -3, 2, 3, 5),))
        with self.assertRaises(KernelError):
            RealTheorem(built_peak.form, "Real.sqrt", (built_peak,))
        denestable_crest = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 1, 2, 1, 3),),
        )
        self.assertFalse(_canonical(denestable_crest))
        with self.assertRaises(KernelError):
            RealTheorem(denestable_crest, "Real.sqrt", (built_peak,))
        unreduced_qmult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 4, 1, 1, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_qmult))
        unreduced_crest_pmult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 4, 1, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_crest_pmult))
        unreduced_crest_hmult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 4, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_crest_hmult))
        with self.assertRaises(KernelError):
            RealTheorem(unreduced_qmult, "Real.sqrt", (built_peak,))
        other_crest = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 1, 3, 1, 5),),
        )
        self.assertTrue(_canonical(other_crest))
        with self.assertRaises(KernelError):
            RealTheorem(other_crest, "Real.sqrt", (built_peak,))
        swapped_crest = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 1, 5, 1, 2),),
        )
        self.assertFalse(_canonical(swapped_crest))
        with self.assertRaises(KernelError):
            RealTheorem(swapped_crest, "Real.sqrt", (built_peak,))

        built_summit = real_sqrt(built_crest)
        self.assertEqual(
            show_form(built_summit.form),
            "sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))",
        )
        self.assertEqual(built_summit.form.summits, ((Ratio(1, 1), 1, 1, 1, 1, 1, 2, 1, 5),))
        self.assertEqual(built_summit.form.crests, ())
        accepted_summit = RealTheorem(built_summit.form, "Real.sqrt", (built_crest,))
        self.assertEqual(
            show_form(accepted_summit.form),
            "sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))",
        )
        self.assertTrue(_canonical(built_summit.form))
        inverted_summit = real_div(real_of_rat(Ratio(1, 1)), built_summit)
        self.assertEqual(
            show_form(inverted_summit.form),
            "1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))))",
        )
        self.assertEqual(
            inverted_summit.form.summits,
            ((Ratio(1, 3), 3, 3, 3, 3, -3, 2, 3, 5),),
        )
        with self.assertRaises(KernelError):
            RealTheorem(built_crest.form, "Real.sqrt", (built_crest,))
        denestable_summit = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 1, 1, 2, 1, 3),),
        )
        self.assertFalse(_canonical(denestable_summit))
        with self.assertRaises(KernelError):
            RealTheorem(denestable_summit, "Real.sqrt", (built_crest,))
        unreduced_smult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 4, 1, 1, 1, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_smult))
        unreduced_summit_qmult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 4, 1, 1, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_summit_qmult))
        unreduced_summit_pmult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 4, 1, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_summit_pmult))
        unreduced_summit_hmult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 4, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_summit_hmult))
        with self.assertRaises(KernelError):
            RealTheorem(unreduced_smult, "Real.sqrt", (built_crest,))
        other_summit = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 1, 1, 3, 1, 5),),
        )
        self.assertTrue(_canonical(other_summit))
        with self.assertRaises(KernelError):
            RealTheorem(other_summit, "Real.sqrt", (built_crest,))
        swapped_summit = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 1, 1, 5, 1, 2),),
        )
        self.assertFalse(_canonical(swapped_summit))
        with self.assertRaises(KernelError):
            RealTheorem(swapped_summit, "Real.sqrt", (built_crest,))

        built_apex = real_sqrt(built_summit)
        self.assertEqual(
            show_form(built_apex.form),
            "sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))",
        )
        self.assertEqual(built_apex.form.apexes, ((Ratio(1, 1), 1, 1, 1, 1, 1, 1, 2, 1, 5),))
        self.assertEqual(built_apex.form.summits, ())
        accepted_apex = RealTheorem(built_apex.form, "Real.sqrt", (built_summit,))
        self.assertEqual(
            show_form(accepted_apex.form),
            "sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))",
        )
        self.assertTrue(_canonical(built_apex.form))
        inverted_apex = real_div(real_of_rat(Ratio(1, 1)), built_apex)
        self.assertEqual(
            show_form(inverted_apex.form),
            "1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))))))",
        )
        self.assertEqual(
            inverted_apex.form.apexes,
            ((Ratio(1, 3), 3, 3, 3, 3, 3, -3, 2, 3, 5),),
        )
        with self.assertRaises(KernelError):
            RealTheorem(built_summit.form, "Real.sqrt", (built_summit,))
        denestable_apex = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 1, 1, 1, 2, 1, 3),),
        )
        self.assertFalse(_canonical(denestable_apex))
        with self.assertRaises(KernelError):
            RealTheorem(denestable_apex, "Real.sqrt", (built_summit,))
        unreduced_amult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 4, 1, 1, 1, 1, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_amult))
        unreduced_apex_smult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 4, 1, 1, 1, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_apex_smult))
        unreduced_apex_qmult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 4, 1, 1, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_apex_qmult))
        unreduced_apex_pmult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 4, 1, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_apex_pmult))
        unreduced_apex_hmult = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 1, 4, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_apex_hmult))
        with self.assertRaises(KernelError):
            RealTheorem(unreduced_amult, "Real.sqrt", (built_summit,))
        other_apex = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 1, 1, 1, 3, 1, 5),),
        )
        self.assertTrue(_canonical(other_apex))
        with self.assertRaises(KernelError):
            RealTheorem(other_apex, "Real.sqrt", (built_summit,))
        swapped_apex = RealForm(
            Ratio(0, 1),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            ((Ratio(1, 1), 1, 1, 1, 1, 1, 1, 5, 1, 2),),
        )
        self.assertFalse(_canonical(swapped_apex))
        with self.assertRaises(KernelError):
            RealTheorem(swapped_apex, "Real.sqrt", (built_summit,))

        built_shell = real_sqrt(built_apex)
        self.assertEqual(len(built_shell.form.shells[0][1]), 1)
        self.assertTrue(_canonical(built_shell.form))
        accepted_shell = RealTheorem(built_shell.form, "Real.sqrt", (built_apex,))
        self.assertEqual(show_form(accepted_shell.form), show_form(built_shell.form))
        with self.assertRaises(KernelError):
            RealTheorem(built_apex.form, "Real.sqrt", (built_apex,))
        unreduced_shell = RealForm(
            Ratio(0, 1),
            (),
            shells=((Ratio(1, 1), (4,), 1, 1, 1, 1, 1, 1, 2, 1, 5),),
        )
        self.assertFalse(_canonical(unreduced_shell))
        with self.assertRaises(KernelError):
            RealTheorem(unreduced_shell, "Real.sqrt", (built_apex,))
        denestable_shell = RealForm(
            Ratio(0, 1),
            (),
            shells=((Ratio(1, 1), (1,), 1, 1, 1, 1, 1, 1, 2, 1, 3),),
        )
        self.assertFalse(_canonical(denestable_shell))
        other_shell = RealForm(
            Ratio(0, 1),
            (),
            shells=((Ratio(1, 1), (1,), 1, 1, 1, 1, 1, 1, 3, 1, 5),),
        )
        self.assertTrue(_canonical(other_shell))
        with self.assertRaises(KernelError):
            RealTheorem(other_shell, "Real.sqrt", (built_apex,))
        deeper_shell = RealForm(
            Ratio(0, 1),
            (),
            shells=((Ratio(1, 1), (1, 1), 1, 1, 1, 1, 1, 1, 2, 1, 5),),
        )
        self.assertTrue(_canonical(deeper_shell))
        with self.assertRaises(KernelError):
            RealTheorem(deeper_shell, "Real.sqrt", (built_apex,))


if __name__ == "__main__":
    unittest.main()
