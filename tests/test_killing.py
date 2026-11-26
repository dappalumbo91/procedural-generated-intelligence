"""Killing vectors and the Lie derivative of a metric."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.kernel import KernelError
from pgi.math.killing import KillingVectorTheorem, _eval, _standing, named_killing
from pgi.math.syntax import parse_term
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class KillingTests(unittest.TestCase):
    def test_schwarzschild_time_and_rotation_are_killing(self) -> None:
        self.assertEqual(
            run(Request(ask="what is killingfield(schwarzschild, t)", seed=1)).claims[0].atom,
            "vector(1, 0, 0, 0)",
        )
        self.assertEqual(
            run(Request(ask="what is killingfield(schwarzschild, phi)", seed=1)).claims[0].atom,
            "vector(0, 0, 0, 1)",
        )
        self.assertEqual(
            run(Request(ask="what is killingfield(schwarzschild, jx)", seed=1)).claims[0].atom,
            "vector(0, 0, -sin(phi), -cos(theta) * cos(phi) / sin(theta))",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove lie(killingfield(schwarzschild, t), metric(schwarzschild)) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(lie(killingfield(schwarzschild, t), metric(schwarzschild)) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove lie(killingfield(schwarzschild, phi), metric(schwarzschild)) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(lie(killingfield(schwarzschild, phi), metric(schwarzschild)) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove lie(killingfield(schwarzschild, jx), metric(schwarzschild)) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(lie(killingfield(schwarzschild, jx), metric(schwarzschild)) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove lie(killingfield(schwarzschild, jy), metric(schwarzschild)) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(lie(killingfield(schwarzschild, jy), metric(schwarzschild)) = 0)",
        )

    def test_euclidean_rotation_is_killing_and_a_dilation_is_not(self) -> None:
        self.assertEqual(
            run(Request(ask="what is killingfield(e2, j)", seed=1)).claims[0].atom,
            "vector(-y, x)",
        )
        self.assertEqual(
            run(Request(ask="prove lie(killingfield(e2, j), metric(e2)) = 0", seed=1)).claims[0].atom,
            "identity(lie(killingfield(e2, j), metric(e2)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove lie(vector(e2, -y, x), metric(e2)) = 0", seed=1)).claims[0].atom,
            "identity(lie(vector(e2, (-y), x), metric(e2)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove lie(vector(e2, x, 0), metric(e2)) = 0", seed=1)).claims[0].atom,
            "open(lie(vector(e2, x, 0), metric(e2)) = 0 is not a theorem)",
        )

    def test_killing_results_refuse_forgery(self) -> None:
        _standing()
        origin = parse_term("killingfield(schwarzschild, t)")
        with self.assertRaises(KernelError):
            KillingVectorTheorem(named_killing("schwarzschild", "phi"), origin)
        self.assertEqual(_eval(origin).components, named_killing("schwarzschild", "t").components)
