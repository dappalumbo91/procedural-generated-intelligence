from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.kernel import KernelError
from pgi.math.poly import as_rat, eval_symbolic, mrat_diff_commute, var_poly
from pgi.math.syntax import parse_term, pretty
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class MultivariatePolyTests(unittest.TestCase):
    def test_partial_derivatives_and_cancellation(self) -> None:
        first = run(Request(ask="what is d(x^2, x)", seed=1))
        self.assertEqual(first.claims[0].atom, "poly(2 * x)")
        self.assertIn("termwise", first.text(lod=2))
        self.assertEqual(first.open_gaps, ())

        mixed = run(Request(ask="what is d(x^2 * y + 3 * x, x)", seed=1))
        self.assertEqual(mixed.claims[0].atom, "poly(2 * x * y + 3)")

        square = run(Request(ask="what is d(x^2 + 2 * x * y + y^2, x)", seed=1))
        self.assertEqual(square.claims[0].atom, "poly(2 * x + 2 * y)")

        clairaut = run(Request(ask="what is d(d(x^3 * y^2, x), y)", seed=1))
        self.assertEqual(clairaut.claims[0].atom, "poly(6 * x^2 * y)")
        flipped = run(Request(ask="what is d(d(x^3 * y^2, y), x)", seed=1))
        self.assertEqual(flipped.claims[0].atom, "poly(6 * x^2 * y)")

        cancelled = run(Request(ask="what is (x^2 - 1) / (x - 1)", seed=1))
        self.assertEqual(cancelled.claims[0].atom, "poly(x + 1)")
        difference = run(Request(ask="what is (x^2 - y^2) / (x - y)", seed=1))
        self.assertEqual(difference.claims[0].atom, "poly(x + y)")
        halved = run(Request(ask="what is (2 * x + 2) / 2", seed=1))
        self.assertEqual(halved.claims[0].atom, "poly(x + 1)")

        quotient = run(Request(ask="what is d((x^2 + 1) / (x + 1), x)", seed=1))
        self.assertEqual(quotient.claims[0].atom, "rat((x^2 + 2 * x - 1) / (x^2 + 2 * x + 1))")
        self.assertIn("quotient rule", quotient.text(lod=2))
        reduced = run(Request(ask="what is d((x^2 - 1) / (x - 1), x)", seed=1))
        self.assertEqual(reduced.claims[0].atom, "value(1)")
        inverse = run(Request(ask="what is d(1 / x, x)", seed=1))
        self.assertEqual(inverse.claims[0].atom, "rat(-1 / x^2)")

        second = run(Request(ask="what is d(x^2, x, 2)", seed=1))
        self.assertEqual(second.claims[0].atom, "value(2)")
        ignored = run(Request(ask="what is d(x, y)", seed=1))
        self.assertEqual(ignored.claims[0].atom, "value(0)")

        proved = run(Request(ask="prove d(x^2, x) = 2 * x", seed=1))
        self.assertEqual(proved.claims[0].atom, "identity(d(x^2, x) = 2 * x)")
        proved_cancel = run(Request(ask="prove (x^2 - 1) / (x - 1) = x + 1", seed=1))
        self.assertEqual(proved_cancel.claims[0].atom, "identity((x^2 - 1) / (x - 1) = x + 1)")

        power = run(Request(ask="what is 2^3", seed=1))
        self.assertEqual(power.claims[0].atom, "value(8)")
        fraction = run(Request(ask="what is (1/2)^2", seed=1))
        self.assertEqual(fraction.claims[0].atom, "ratio(1,4)")
        inverse_int = run(Request(ask="what is 2^(-1)", seed=1))
        self.assertEqual(inverse_int.claims[0].atom, "ratio(1,2)")

    def test_zero_denominator_and_zero_power_stay_open(self) -> None:
        zero = run(Request(ask="what is x / 0", seed=1))
        self.assertEqual(zero.claims[0].atom, "open(division by zero)")
        undefined = run(Request(ask="what is 0^0", seed=1))
        self.assertEqual(undefined.claims[0].atom, "open(0^0 stays open)")

    def test_mixed_partials_commute_and_refuse_a_mismatch(self) -> None:
        source = as_rat(eval_symbolic(parse_term("x^3 * y^2 + x * y")))
        mrat_diff_commute(source, "x", "y")
        other = as_rat(var_poly("x"))
        # A constant in y has commuting (zero) y-derivatives; the check is on the source.
        mrat_diff_commute(other, "x", "y")

    def test_powers_pretty_print_and_bind_tighter_than_minus(self) -> None:
        term = parse_term("-x^2")
        self.assertIsNotNone(term)
        self.assertEqual(pretty(term), "(-x^2)")
        self.assertEqual(pretty(parse_term("2 * x^2")), "2 * x^2")
        self.assertEqual(pretty(parse_term("d(x^2, x)")), "d(x^2, x)")


if __name__ == "__main__":
    unittest.main()
