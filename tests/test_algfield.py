"""Checked resultants and algebraic-coefficient polynomials."""

from __future__ import annotations

import unittest

from pgi.math.algfield import (
    interval_of,
    is_root_of_poly,
    norm_polynomial,
    roots_of_algebraic_polynomial,
)
from pgi.math.algebraic import AlgebraicReal, show_algebraic, show_poly
from pgi.math.arbitrary import _poly_add, _poly_neg, _poly_term, _poly_trim
from pgi.math.collect import eval_collect
from pgi.math.rational import Ratio
from pgi.math.real import algebraic_of_form
from pgi.math.syntax import parse_term


class AlgebraicFieldTest(unittest.TestCase):
    def _coeffs(self, ask: str):
        form = eval_collect(parse_term(ask))
        left = _poly_term(form.left, form.binder)
        right = _poly_term(form.right, form.binder)
        coeffs = _poly_trim(_poly_add(left, _poly_neg(right)))
        return tuple(algebraic_of_form(coeff) for coeff in coeffs)

    def test_cubic_with_sqrt_two_coefficient(self) -> None:
        coeffs = self._coeffs("{x. x * x * x <= sqrt(2)}")
        found = roots_of_algebraic_polynomial(coeffs)
        self.assertEqual(len(found), 1)
        root, _mult = found[0]
        self.assertIsInstance(root, AlgebraicReal)
        self.assertEqual(show_algebraic(root), "root(x^6 - 2, 2)")
        self.assertTrue(is_root_of_poly(coeffs, root))

    def test_related_algebraic_coefficients_keep_only_true_roots(self) -> None:
        coeffs = self._coeffs("{x. (x * x - 2) * (x - sqrt(2)) <= 0}")
        found = roots_of_algebraic_polynomial(coeffs)
        # The original has roots -sqrt(2) and sqrt(2). Extra conjugate
        # candidates from an independent-symbol eliminant must be dropped.
        self.assertEqual(len(found), 2)
        self.assertTrue(all(is_root_of_poly(coeffs, root) for root, _ in found))
        mids = []
        for root, _mult in found:
            low, high = interval_of(root, 8)
            mids.append((low.num / low.den + high.num / high.den) / 2)
        self.assertLess(mids[0], 0)
        self.assertGreater(mids[1], 0)
        self.assertAlmostEqual(abs(mids[0]), 2 ** 0.5, delta=0.1)
        self.assertAlmostEqual(mids[1], 2 ** 0.5, delta=0.1)

    def test_norm_of_a_rational_quadratic(self) -> None:
        minus_two = Ratio(-2, 1)
        one = Ratio(1, 1)
        zero = Ratio(0, 1)
        norm = norm_polynomial((minus_two, zero, one))
        self.assertEqual(show_poly(norm), "x^2 - 2")


if __name__ == "__main__":
    unittest.main()
