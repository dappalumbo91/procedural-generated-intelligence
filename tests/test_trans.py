from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


def _parse_enclose(atom: str) -> tuple[tuple[int, int], tuple[int, int]]:
    if not atom.startswith("enclose(") or not atom.endswith(")"):
        raise AssertionError(f"expected an enclosure, got {atom}")
    inner = atom[len("enclose(") : -1]
    depth = 0
    split = None
    for index, char in enumerate(inner):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            split = index
            break
    if split is None:
        raise AssertionError(f"expected two ends, got {atom}")
    def as_ratio(text: str) -> tuple[int, int]:
        text = text.strip()
        if "/" in text:
            num, den = text.split("/", 1)
            return int(num), int(den)
        return int(text), 1
    return as_ratio(inner[:split]), as_ratio(inner[split + 1 :])


def _lt(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] * right[1] < right[0] * left[1]


def _le(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] * right[1] <= right[0] * left[1]


def _width(ends: tuple[tuple[int, int], tuple[int, int]]) -> float:
    (ln, ld), (hn, hd) = ends
    return hn / hd - ln / ld


class ElementaryFunctionTests(unittest.TestCase):
    def test_special_values_are_exact_rationals(self) -> None:
        self.assertEqual(run(Request(ask="what is sin(0)", seed=1)).claims[0].atom, "value(0)")
        self.assertEqual(run(Request(ask="what is cos(0)", seed=1)).claims[0].atom, "value(1)")
        self.assertEqual(run(Request(ask="what is exp(0)", seed=1)).claims[0].atom, "value(1)")
        self.assertEqual(run(Request(ask="what is log(1)", seed=1)).claims[0].atom, "value(0)")
        self.assertEqual(run(Request(ask="what is sin(pi)", seed=1)).claims[0].atom, "value(0)")
        self.assertEqual(run(Request(ask="what is cos(pi)", seed=1)).claims[0].atom, "value(-1)")
        self.assertEqual(run(Request(ask="what is sin(pi / 2)", seed=1)).claims[0].atom, "value(1)")
        self.assertEqual(run(Request(ask="what is cos(pi / 2)", seed=1)).claims[0].atom, "value(0)")
        self.assertEqual(run(Request(ask="what is sin(pi / 6)", seed=1)).claims[0].atom, "ratio(1,2)")
        self.assertEqual(run(Request(ask="what is cos(pi / 3)", seed=1)).claims[0].atom, "ratio(1,2)")
        self.assertEqual(run(Request(ask="what is sin(3 * pi / 2)", seed=1)).claims[0].atom, "value(-1)")

    def test_symbolic_identities(self) -> None:
        pythagoras = run(Request(ask="prove sin(x)^2 + cos(x)^2 = 1", seed=1))
        self.assertEqual(pythagoras.claims[0].atom, "identity(sin(x)^2 + cos(x)^2 = 1)")
        self.assertEqual(pythagoras.open_gaps, ())

        sine = run(Request(ask="prove d(sin(x), x) = cos(x)", seed=1))
        self.assertEqual(sine.claims[0].atom, "identity(d(sin(x), x) = cos(x))")

        cosine = run(Request(ask="prove d(cos(x), x) = -sin(x)", seed=1))
        self.assertEqual(cosine.claims[0].atom, "identity(d(cos(x), x) = (-sin(x)))")

        expo = run(Request(ask="prove d(exp(x), x) = exp(x)", seed=1))
        self.assertEqual(expo.claims[0].atom, "identity(d(exp(x), x) = exp(x))")

        log = run(Request(ask="prove d(log(x), x) = 1 / x", seed=1))
        self.assertEqual(log.claims[0].atom, "identity(d(log(x), x) = 1 / x)")

        addition = run(Request(ask="prove exp(x + y) = exp(x) * exp(y)", seed=1))
        self.assertEqual(addition.claims[0].atom, "identity(exp(x + y) = exp(x) * exp(y))")

        power = run(Request(ask="prove exp(2 * x) = exp(x)^2", seed=1))
        self.assertEqual(power.claims[0].atom, "identity(exp(2 * x) = exp(x)^2)")

        reduced = run(Request(ask="what is sin(x)^2 + cos(x)^2", seed=1))
        self.assertEqual(reduced.claims[0].atom, "value(1)")

        derived = run(Request(ask="what is d(sin(x), x)", seed=1))
        self.assertEqual(derived.claims[0].atom, "trans(cos(x))")
        self.assertIn("chain rule", derived.text(lod=2))

    def test_polynomial_derivatives_are_not_stolen(self) -> None:
        poly = run(Request(ask="what is d(x^2, x)", seed=1))
        self.assertEqual(poly.claims[0].atom, "poly(2 * x)")
        imaginary = run(Request(ask="what is d(i^2, i)", seed=1))
        self.assertEqual(imaginary.claims[0].atom, "poly(2 * i)")

    def test_closed_values_have_rational_enclosures(self) -> None:
        pi = run(Request(ask="what is pi", seed=1))
        ends = _parse_enclose(pi.claims[0].atom)
        self.assertTrue(_lt((3, 1), ends[0]) and _lt(ends[1], (22, 7)))
        self.assertTrue(_le(ends[0], ends[1]))
        self.assertLess(_width(ends), 1e-18)
        self.assertIn("Machin", pi.text(lod=2))

        exp_one = run(Request(ask="what is exp(1)", seed=1))
        ends = _parse_enclose(exp_one.claims[0].atom)
        self.assertTrue(_lt((27, 10), ends[0]) and _lt(ends[1], (28, 10)))
        self.assertLess(_width(ends), 1e-18)

        log_two = run(Request(ask="what is log(2)", seed=1))
        ends = _parse_enclose(log_two.claims[0].atom)
        self.assertTrue(_lt((6, 10), ends[0]) and _lt(ends[1], (7, 10)))
        self.assertLess(_width(ends), 1e-18)

        sine = run(Request(ask="what is sin(1)", seed=1))
        ends = _parse_enclose(sine.claims[0].atom)
        self.assertTrue(_lt((8, 10), ends[0]) and _lt(ends[1], (9, 10)))
        self.assertLess(_width(ends), 1e-18)

        pythagoras = run(Request(ask="what is sin(1)^2 + cos(1)^2", seed=1))
        self.assertEqual(pythagoras.claims[0].atom, "value(1)")

        greater = run(Request(ask="prove pi >= 3", seed=1))
        self.assertEqual(greater.claims[0].atom, "identity(3 <= pi)")
        less = run(Request(ask="prove pi <= 22 / 7", seed=1))
        self.assertEqual(less.claims[0].atom, "identity(pi <= 22 / 7)")
        false = run(Request(ask="prove pi <= 3", seed=1))
        self.assertEqual(false.claims[0].atom, "open(pi <= 3 is not a theorem)")

    def test_logarithm_and_zero_stay_open(self) -> None:
        zero = run(Request(ask="what is log(0)", seed=1))
        self.assertEqual(zero.claims[0].atom, "open(the logarithm of a non-positive number stays open)")
        negative = run(Request(ask="what is log(-1)", seed=1))
        self.assertEqual(negative.claims[0].atom, "open(the logarithm of a non-positive number stays open)")
        divided = run(Request(ask="what is 1 / sin(0)", seed=1))
        self.assertEqual(divided.claims[0].atom, "open(division by zero)")
        mismatch = run(Request(ask="prove sin(x) = x", seed=1))
        self.assertEqual(mismatch.claims[0].atom, "open(sin(x) = x is not a theorem)")

    def test_formal_scale_factor_derivatives(self) -> None:
        scale = run(Request(ask="what is a(t)", seed=1))
        self.assertEqual(scale.claims[0].atom, "trans(a(t))")
        first = run(Request(ask="what is d(a(t), t)", seed=1))
        self.assertEqual(first.claims[0].atom, "trans(d(a(t), t))")
        second = run(Request(ask="what is d(a(t), t, 2)", seed=1))
        self.assertEqual(second.claims[0].atom, "trans(d(a(t), t, 2))")
        ignored = run(Request(ask="what is d(a(t), x)", seed=1))
        self.assertEqual(ignored.claims[0].atom, "value(0)")
        proved = run(
            Request(ask="prove d(a(t)^2, t) = 2 * a(t) * d(a(t), t)", seed=1)
        )
        self.assertEqual(
            proved.claims[0].atom,
            "identity(d(a(t)^2, t) = 2 * a(t) * d(a(t), t))",
        )
