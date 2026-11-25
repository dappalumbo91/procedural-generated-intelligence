"""The Lorentz group so(3,1) and the Dirac Clifford algebra."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


_I4 = "[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]"
_ETA = "[[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]"
_BOOST_X = "[[5/4, -3/4, 0, 0], [-3/4, 5/4, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]"
_GAMMA0 = "[[0, 0, 1, 0], [0, 0, 0, 1], [-1, 0, 0, 0], [0, -1, 0, 0]]"


class LorentzTests(unittest.TestCase):
    def test_dirac_matrices_satisfy_the_clifford_algebra(self) -> None:
        self.assertEqual(
            run(Request(ask="what is eta()", seed=1)).claims[0].atom,
            f"cmatrix({_ETA})",
        )
        self.assertEqual(
            run(Request(ask="what is gamma(0)", seed=1)).claims[0].atom,
            f"cmatrix({_GAMMA0})",
        )
        self.assertEqual(
            run(Request(ask=f"prove anticommutator(gamma(0), gamma(0)) = -2 * {_I4}", seed=1)).claims[0].atom,
            f"identity(anticommutator(gamma(0), gamma(0)) = -2 * {_I4})",
        )
        self.assertEqual(
            run(Request(ask=f"prove anticommutator(gamma(1), gamma(1)) = 2 * {_I4}", seed=1)).claims[0].atom,
            f"identity(anticommutator(gamma(1), gamma(1)) = 2 * {_I4})",
        )
        self.assertEqual(
            run(Request(ask=f"prove anticommutator(gamma(2), gamma(2)) = 2 * {_I4}", seed=1)).claims[0].atom,
            f"identity(anticommutator(gamma(2), gamma(2)) = 2 * {_I4})",
        )
        self.assertEqual(
            run(Request(ask="prove anticommutator(gamma(0), gamma(1)) = 0 * " + _I4, seed=1)).claims[0].atom,
            f"identity(anticommutator(gamma(0), gamma(1)) = 0 * {_I4})",
        )
        self.assertEqual(
            run(Request(ask="prove clifford() = 0", seed=1)).claims[0].atom,
            "identity(clifford() = 0)",
        )
        self.assertEqual(
            run(Request(ask=f"prove anticommutator(gamma(0), gamma(0)) = 2 * {_I4}", seed=1)).claims[0].atom,
            f"open(anticommutator(gamma(0), gamma(0)) = 2 * {_I4} is not a theorem)",
        )

    def test_a_rational_boost_preserves_the_minkowski_metric(self) -> None:
        self.assertEqual(
            run(Request(ask="what is boost(x, 3/5)", seed=1)).claims[0].atom,
            f"cmatrix({_BOOST_X})",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove transpose(boost(x, 3/5)) * eta() * boost(x, 3/5) = eta()",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(transpose(boost(x, 3 / 5)) * eta() * boost(x, 3 / 5) = eta())",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove boost(x, 3/5) * eta() * transpose(boost(x, 3/5)) = eta()",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(boost(x, 3 / 5) * eta() * transpose(boost(x, 3 / 5)) = eta())",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove transpose(boost(y, 3/5)) * eta() * boost(y, 3/5) = eta()",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(transpose(boost(y, 3 / 5)) * eta() * boost(y, 3 / 5) = eta())",
        )
        self.assertEqual(
            run(Request(ask="what is boost(x, 1/2)", seed=1)).claims[0].atom,
            "open(a boost is kept only when 1 - v^2 is the square of a rational)",
        )

    def test_so31_brackets_are_the_lorentz_algebra(self) -> None:
        self.assertEqual(
            run(Request(ask="prove commutator(so31(jx), so31(jy)) = so31(jz)", seed=1)).claims[0].atom,
            "identity(commutator(so31(jx), so31(jy)) = so31(jz))",
        )
        self.assertEqual(
            run(Request(ask="prove commutator(so31(kx), so31(ky)) = -so31(jz)", seed=1)).claims[0].atom,
            "identity(commutator(so31(kx), so31(ky)) = (-so31(jz)))",
        )
        self.assertEqual(
            run(Request(ask="prove commutator(so31(jx), so31(ky)) = so31(kz)", seed=1)).claims[0].atom,
            "identity(commutator(so31(jx), so31(ky)) = so31(kz))",
        )
        self.assertEqual(
            run(Request(ask="prove so31algebra() = 0", seed=1)).claims[0].atom,
            "identity(so31algebra() = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove commutator(so31(kx), so31(ky)) = so31(jz)", seed=1)).claims[0].atom,
            "open(commutator(so31(kx), so31(ky)) = so31(jz) is not a theorem)",
        )
