"""Continuum L2 identities and finite-mode Fock operators, checked exactly."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class ContinuumTests(unittest.TestCase):
    def test_gaussian_and_exponential_integrals(self) -> None:
        self.assertEqual(
            run(Request(ask="what is gaussint(1, 1)", seed=1)).claims[0].atom,
            "sqrt(pi)",
        )
        self.assertEqual(
            run(Request(ask="prove gaussint(1, 1) = sqrt(pi)", seed=1)).claims[0].atom,
            "identity(gaussint(1, 1) = sqrt(pi))",
        )
        self.assertEqual(
            run(Request(ask="prove gaussint(x, 1) = 0", seed=1)).claims[0].atom,
            "identity(gaussint(x, 1) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove gaussint(x^2, 1) = sqrt(pi) / 2", seed=1)).claims[0].atom,
            "identity(gaussint(x^2, 1) = sqrt(pi) / 2)",
        )
        self.assertEqual(
            run(Request(ask="prove gaussint(1, 2) = sqrt(pi) / sqrt(2)", seed=1)).claims[0].atom,
            "identity(gaussint(1, 2) = sqrt(pi) / sqrt(2))",
        )
        self.assertEqual(
            run(Request(ask="prove expint(0) = 1", seed=1)).claims[0].atom,
            "identity(expint(0) = 1)",
        )
        self.assertEqual(
            run(Request(ask="prove expint(3) = 6", seed=1)).claims[0].atom,
            "identity(expint(3) = 6)",
        )
        self.assertEqual(
            run(Request(ask="prove gaussint(1, 1) = 0", seed=1)).claims[0].atom,
            "open(gaussint(1, 1) = 0 is not a theorem)",
        )

    def test_hermite_inner_products_fourier_and_canonical_commutator(self) -> None:
        self.assertEqual(
            run(Request(ask="prove l2inner(hermite(0), hermite(0)) = 1", seed=1)).claims[0].atom,
            "identity(l2inner(hermite(0), hermite(0)) = 1)",
        )
        self.assertEqual(
            run(Request(ask="prove l2inner(hermite(0), hermite(1)) = 0", seed=1)).claims[0].atom,
            "identity(l2inner(hermite(0), hermite(1)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove l2inner(hermite(2), hermite(2)) = 1", seed=1)).claims[0].atom,
            "identity(l2inner(hermite(2), hermite(2)) = 1)",
        )
        self.assertEqual(
            run(Request(ask="prove fourier(hermite(0)) = hermite(0)", seed=1)).claims[0].atom,
            "identity(fourier(hermite(0)) = hermite(0))",
        )
        self.assertEqual(
            run(Request(ask="prove fourier(hermite(1)) = (-i) * hermite(1)", seed=1)).claims[0].atom,
            "identity(fourier(hermite(1)) = (-i) * hermite(1))",
        )
        self.assertEqual(
            run(Request(ask="prove fourier(hermite(2)) = -1 * hermite(2)", seed=1)).claims[0].atom,
            "identity(fourier(hermite(2)) = -1 * hermite(2))",
        )
        self.assertEqual(
            run(Request(ask="prove l2comm(hermite(0)) = 0", seed=1)).claims[0].atom,
            "identity(l2comm(hermite(0)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove l2comm(hermite(2)) = 0", seed=1)).claims[0].atom,
            "identity(l2comm(hermite(2)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove l2inner(hermite(0), hermite(1)) = 1", seed=1)).claims[0].atom,
            "open(l2inner(hermite(0), hermite(1)) = 1 is not a theorem)",
        )

    def test_free_particle_and_finite_mode_fock(self) -> None:
        self.assertEqual(
            run(Request(ask="prove freeenergy(planewave(k)) = k^2 / 2", seed=1)).claims[0].atom,
            "identity(freeenergy(planewave(k)) = k^2 / 2)",
        )
        self.assertEqual(
            run(Request(ask="prove schresidual(freepacket) = 0", seed=1)).claims[0].atom,
            "identity(schresidual(freepacket) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove schresidual(planewave(k)) = 0", seed=1)).claims[0].atom,
            "identity(schresidual(planewave(k)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove fockinner(fockket(1, 0), fockket(1, 0)) = 1", seed=1)).claims[0].atom,
            "identity(fockinner(fockket(1, 0), fockket(1, 0)) = 1)",
        )
        self.assertEqual(
            run(Request(ask="prove fockinner(fockket(1, 0), fockket(0, 1)) = 0", seed=1)).claims[0].atom,
            "identity(fockinner(fockket(1, 0), fockket(0, 1)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove fockapply(focka(0), fockket(1, 0)) = fockket(0, 0)", seed=1)).claims[0].atom,
            "identity(fockapply(focka(0), fockket(1, 0)) = fockket(0, 0))",
        )
        self.assertEqual(
            run(Request(ask="prove fockapply(fockadag(0), fockket(0, 0)) = fockket(1, 0)", seed=1)).claims[0].atom,
            "identity(fockapply(fockadag(0), fockket(0, 0)) = fockket(1, 0))",
        )
        self.assertEqual(
            run(Request(ask="prove fockcomm(0, 0) = 1", seed=1)).claims[0].atom,
            "identity(fockcomm(0, 0) = 1)",
        )
        self.assertEqual(
            run(Request(ask="prove fockcomm(0, 1) = 0", seed=1)).claims[0].atom,
            "identity(fockcomm(0, 1) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove fieldcomm(0) = i", seed=1)).claims[0].atom,
            "identity(fieldcomm(0) = i)",
        )
        self.assertEqual(
            run(Request(ask="prove fockcomm(0, 0) = 0", seed=1)).claims[0].atom,
            "open(fockcomm(0, 0) = 0 is not a theorem)",
        )


if __name__ == "__main__":
    unittest.main()
