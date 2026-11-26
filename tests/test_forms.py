"""Differential forms, d² = 0, the Hodge star, and Maxwell's equations in form language."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.forms import FormTheorem, _eval_form, _standing
from pgi.math.kernel import KernelError
from pgi.math.syntax import parse_term
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class FormsTests(unittest.TestCase):
    def test_exterior_square_vanishes_and_is_maxwell_on_flat_spacetime(self) -> None:
        self.assertEqual(
            run(Request(ask="what is exterior(exterior(potential(t * x, x * y, y * z, z * t)))", seed=1)).claims[0].atom,
            "form(0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove exterior(exterior(potential(t * x, x * y, y * z, z * t))) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(exterior(exterior(potential(t * x, x * y, y * z, z * t))) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove exterior(faraday(potential(t * x, x * y, y * z, z * t))) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(exterior(faraday(potential(t * x, x * y, y * z, z * t))) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove exterior(faraday(potential(sin(t + x), 0, 0, 0))) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(exterior(faraday(potential(sin(t + x), 0, 0, 0))) = 0)",
        )
        self.assertEqual(
            run(Request(ask="what is faraday(potential(0, -y, x, 0))", seed=1)).claims[0].atom,
            "2 * coframe(x) ^ coframe(y)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove exterior(faraday(potential(0, -y, x, 0))) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(exterior(faraday(potential(0, (-y), x, 0))) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove exterior(faraday(potential(t * x, x * y, y * z, z * t))) = 1",
                    seed=1,
                )
            ).claims[0].atom,
            "open(exterior(faraday(potential(t * x, x * y, y * z, z * t))) = 1 is not a theorem)",
        )

    def test_wedge_is_alternating_and_d_of_a_zeroform_is_exact(self) -> None:
        self.assertEqual(
            run(
                Request(
                    ask="prove wedge(coframe(x), coframe(y)) + wedge(coframe(y), coframe(x)) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(wedge(coframe(x), coframe(y)) + wedge(coframe(y), coframe(x)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="what is exterior(zeroform(x^2 * y, x, y))", seed=1)).claims[0].atom,
            "oneform(2 * x * y, x^2; x, y)",
        )

    def test_hodge_star_and_inhomogeneous_maxwell(self) -> None:
        self.assertEqual(
            run(Request(ask="what is hodge(coframe(t), minkowski4)", seed=1)).claims[0].atom,
            "-coframe(x) ^ coframe(y) ^ coframe(z)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="what is hodge(faraday(potential((-1/2) * x^2, 0, 0, 0)), minkowski4)",
                    seed=1,
                )
            ).claims[0].atom,
            "-x * coframe(y) ^ coframe(z)",
        )
        self.assertEqual(
            run(
                Request(
                    ask=(
                        "prove exterior(hodge(faraday(potential((-1/2) * x^2, 0, 0, 0)), minkowski4)) "
                        "= hodge(coframe(t), minkowski4)"
                    ),
                    seed=1,
                )
            ).claims[0].atom,
            "identity(exterior(hodge(faraday(potential(-1 / 2 * x^2, 0, 0, 0)), minkowski4)) = hodge(coframe(t), minkowski4))",
        )
        self.assertEqual(
            run(
                Request(
                    ask="what is hodge(faraday(oneform(1/r, 0, 0, 0, t, r, theta, phi)), schwarzschild)",
                    seed=1,
                )
            ).claims[0].atom,
            "-sin(theta) * coframe(theta) ^ coframe(phi)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove exterior(hodge(faraday(oneform(1/r, 0, 0, 0, t, r, theta, phi)), schwarzschild)) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(exterior(hodge(faraday(oneform(1 / r, 0, 0, 0, t, r, theta, phi)), schwarzschild)) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove hodge(hodge(faraday(potential(0, -y, x, 0)), minkowski4), minkowski4) = -faraday(potential(0, -y, x, 0))",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(hodge(hodge(faraday(potential(0, (-y), x, 0)), minkowski4), minkowski4) = (-faraday(potential(0, (-y), x, 0))))",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove exterior(hodge(faraday(potential((-1/2) * x^2, 0, 0, 0)), minkowski4)) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "open(exterior(hodge(faraday(potential(-1 / 2 * x^2, 0, 0, 0)), minkowski4)) = 0 is not a theorem)",
        )

    def test_form_results_refuse_forgery(self) -> None:
        _standing()
        origin = parse_term("faraday(potential(0, -y, x, 0))")
        zero = _eval_form(parse_term("form(0)"))
        with self.assertRaises(KernelError):
            FormTheorem(zero, origin)
