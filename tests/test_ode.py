"""Exact ODE checks for the harmonic oscillator and hydrogen radial functions."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class OdeTests(unittest.TestCase):
    def test_harmonic_oscillator_residuals_vanish(self) -> None:
        self.assertEqual(
            run(Request(ask="what is harmonic(0)", seed=1)).claims[0].atom,
            "trans(exp(-1/2 * x^2))",
        )
        self.assertEqual(
            run(Request(ask="what is harmonic(1)", seed=1)).claims[0].atom,
            "trans(exp(-1/2 * x^2) * x)",
        )
        self.assertEqual(
            run(Request(ask="prove ode(harmonic(0)) = 0", seed=1)).claims[0].atom,
            "identity(ode(harmonic(0)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove ode(harmonic(1)) = 0", seed=1)).claims[0].atom,
            "identity(ode(harmonic(1)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove ode(harmonic(2)) = 0", seed=1)).claims[0].atom,
            "identity(ode(harmonic(2)) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove d(d(exp(-x^2 / 2), x), x) - (x^2 - 1) * exp(-x^2 / 2) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(d(d(exp((-x^2) / 2), x), x) - (x^2 - 1) * exp((-x^2) / 2) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove ode(harmonic(0)) = 1", seed=1)).claims[0].atom,
            "open(ode(harmonic(0)) = 1 is not a theorem)",
        )
        self.assertEqual(
            run(Request(ask="what is ode(harmonic(3))", seed=1)).claims[0].atom,
            "open(a harmonic-oscillator check is admitted here only for n = 0, 1, or 2)",
        )

    def test_hydrogen_radial_residuals_vanish(self) -> None:
        self.assertEqual(
            run(Request(ask="what is hydrogen(1, 0)", seed=1)).claims[0].atom,
            "trans(exp(-r) * r)",
        )
        self.assertEqual(
            run(Request(ask="what is hydrogen(2, 1)", seed=1)).claims[0].atom,
            "trans(exp(-1/2 * r) * r^2)",
        )
        self.assertEqual(
            run(Request(ask="prove ode(hydrogen(1, 0)) = 0", seed=1)).claims[0].atom,
            "identity(ode(hydrogen(1, 0)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove ode(hydrogen(2, 0)) = 0", seed=1)).claims[0].atom,
            "identity(ode(hydrogen(2, 0)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove ode(hydrogen(2, 1)) = 0", seed=1)).claims[0].atom,
            "identity(ode(hydrogen(2, 1)) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove d(d(r * exp(-r), r), r) - (1 - 2 / r) * r * exp(-r) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(d(d(r * exp((-r)), r), r) - (1 - 2 / r) * r * exp((-r)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="what is ode(hydrogen(3, 0))", seed=1)).claims[0].atom,
            "open(a hydrogen radial check is admitted here only for (n, l) = (1, 0), (2, 0), or (2, 1))",
        )
