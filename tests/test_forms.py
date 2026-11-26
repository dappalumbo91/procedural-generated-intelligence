"""Differential forms, d² = 0, and Maxwell's homogeneous equation on flat spacetime."""

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

    def test_form_results_refuse_forgery(self) -> None:
        _standing()
        origin = parse_term("faraday(potential(0, -y, x, 0))")
        zero = _eval_form(parse_term("form(0)"))
        with self.assertRaises(KernelError):
            FormTheorem(zero, origin)
