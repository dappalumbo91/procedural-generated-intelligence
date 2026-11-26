"""Exact Coulomb continuum identities: radial 1F1 residual, Gamma modulus, Rutherford |f|^2."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class CoulombTests(unittest.TestCase):
    def test_coulomb_radial_residual_vanishes(self) -> None:
        for ell in (0, 1, 2, 3):
            proved = run(Request(ask=f"prove coulombresidual({ell}) = 0", seed=1))
            self.assertEqual(
                proved.claims[0].atom,
                f"identity(coulombresidual({ell}) = 0)",
            )

    def test_higher_angular_momentum_stays_open(self) -> None:
        closed = run(Request(ask="prove coulombresidual(4) = 0", seed=1))
        self.assertTrue(closed.claims[0].atom.startswith("open("))

    def test_gamma_modulus_identity_is_checked(self) -> None:
        proved = run(
            Request(
                ask="prove gammacabs2(eta) = 2 * pi * eta / (exp(pi * eta) - exp((-pi) * eta))",
                seed=1,
            )
        )
        self.assertEqual(
            proved.claims[0].atom,
            "identity(gammacabs2(eta) = 2 * pi * eta / (exp(pi * eta) - exp((-pi) * eta)))",
        )

    def test_rutherford_modulus_from_the_exact_amplitude(self) -> None:
        proved = run(
            Request(
                ask="prove rutherfordabs2(eta, k, theta) = eta^2 / (4 * k^2 * sin(theta / 2)^4)",
                seed=1,
            )
        )
        self.assertEqual(
            proved.claims[0].atom,
            "identity(rutherfordabs2(eta, k, theta) = eta^2 / (4 * k^2 * sin(theta / 2)^4))",
        )

    def test_false_coulomb_claim_stays_open(self) -> None:
        closed = run(Request(ask="prove coulombresidual(0) = 1", seed=1))
        self.assertTrue(closed.claims[0].atom.startswith("open("))


if __name__ == "__main__":
    unittest.main()
