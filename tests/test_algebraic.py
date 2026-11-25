from __future__ import annotations

import unittest

from pgi.math.algebraic import (
    AlgebraicReal,
    KernelError,
    compare_algebraic_to_ratio,
    isolate_interval,
    roots_of_rational_polynomial,
    show_algebraic,
    square_free_factors,
    sturm_count,
)
from pgi.math.rational import Ratio
from pgi.math.real import form_of_algebraic, show_form, try_radical_form


class AlgebraicKernelTest(unittest.TestCase):
    def test_square_free_factors_and_rational_roots(self) -> None:
        factors = square_free_factors((-2, 0, 1))
        self.assertEqual(len(factors), 1)
        self.assertEqual(factors[0][1], 1)

        square = square_free_factors((0, 0, 1))
        self.assertEqual(square, (((0, 1), 2),))

        roots = roots_of_rational_polynomial((0, -1, 0, 1))
        self.assertEqual(tuple(root for root, _mult in roots), (Ratio(-1, 1), Ratio(0, 1), Ratio(1, 1)))
        self.assertEqual(tuple(mult for _root, mult in roots), (1, 1, 1))

        repeated = roots_of_rational_polynomial((0, 0, 1))
        self.assertEqual(repeated, ((Ratio(0, 1), 2),))

    def test_sturm_isolation_and_algebraic_real(self) -> None:
        cube = AlgebraicReal((-2, 0, 0, 1), 1)
        self.assertEqual(show_algebraic(cube), "root(x^3 - 2, 1)")
        low, high = isolate_interval(cube.coeffs, cube.index)
        self.assertEqual(sturm_count((-2, 0, 0, 1), low, high), 1)
        width = high.num / high.den - low.num / low.den
        self.assertLessEqual(width, 0.5)
        self.assertEqual(compare_algebraic_to_ratio(cube, Ratio(1, 1)), "gt")
        self.assertEqual(compare_algebraic_to_ratio(cube, Ratio(2, 1)), "lt")

        with self.assertRaises(KernelError):
            AlgebraicReal((-2, 0, 1), 0)
        with self.assertRaises(KernelError):
            AlgebraicReal((0, 0, 1), 1)

    def test_radical_forms_are_preferred(self) -> None:
        positive = try_radical_form((-2, 0, 1), 2)
        self.assertIsNotNone(positive)
        self.assertEqual(show_form(positive), "sqrt(2)")
        negative = try_radical_form((-2, 0, 1), 1)
        self.assertIsNotNone(negative)
        self.assertEqual(show_form(negative), "-sqrt(2)")
        nested = try_radical_form((-2, 0, 0, 0, 1), 2)
        self.assertIsNotNone(nested)
        self.assertEqual(show_form(nested), "sqrt(sqrt(2))")
        cube = form_of_algebraic((-2, 0, 0, 1), 1)
        self.assertEqual(show_form(cube), "root(x^3 - 2, 1)")
        self.assertIsNone(try_radical_form((-2, 0, 0, 1), 1))


if __name__ == "__main__":
    unittest.main()
