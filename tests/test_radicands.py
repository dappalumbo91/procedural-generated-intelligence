"""Checked Hermitian spectra in the tri-quadratic tower, including denesting norms."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.cnum import c_add, c_inv, c_mul, c_one, c_sqrt_ratio, show_cnum
from pgi.math.kernel import NotExact
from pgi.math.rational import Ratio
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class RadicandTowerTests(unittest.TestCase):
    def test_three_radicand_inverse_multiplies_to_one(self) -> None:
        proved = run(
            Request(
                ask="prove (sqrt(2) + sqrt(3) + sqrt(5)) * (1 / (sqrt(2) + sqrt(3) + sqrt(5))) = 1",
                seed=1,
            )
        )
        self.assertEqual(
            proved.claims[0].atom,
            "identity((sqrt(2) + sqrt(3) + sqrt(5)) * (1 / (sqrt(2) + sqrt(3) + sqrt(5))) = 1)",
        )
        value = run(Request(ask="what is 1 / (sqrt(2) + sqrt(3) + sqrt(5))", seed=1))
        self.assertEqual(
            value.claims[0].atom,
            "cauchy(1/4 * sqrt(2) + 1/6 * sqrt(3) - 1/12 * sqrt(30))",
        )

    def test_denesting_square_root_is_checked(self) -> None:
        proved = run(Request(ask="prove sqrt(4 + 2 * sqrt(3)) = 1 + sqrt(3)", seed=1))
        self.assertEqual(
            proved.claims[0].atom,
            "identity(sqrt(4 + 2 * sqrt(3)) = 1 + sqrt(3))",
        )
        value = run(Request(ask="what is sqrt(4 + 2 * sqrt(3))", seed=1))
        self.assertEqual(value.claims[0].atom, "cauchy(1 + sqrt(3))")

    def test_spectral_decomposition_with_three_radicands(self) -> None:
        matrix = "[[0, sqrt(2) + sqrt(3) + sqrt(5)], [sqrt(2) + sqrt(3) + sqrt(5), 0]]"
        unitary = run(Request(ask=f"what is spectral({matrix})", seed=1))
        self.assertEqual(
            unitary.claims[0].atom,
            "cmatrix([[1/2 * sqrt(2), 1/2 * sqrt(2)], [1/2 * sqrt(2), -1/2 * sqrt(2)]])",
        )
        diag = run(Request(ask=f"what is eigendiag({matrix})", seed=1))
        self.assertEqual(
            diag.claims[0].atom,
            "cmatrix([[sqrt(2) + sqrt(3) + sqrt(5), 0], [0, -sqrt(2) - sqrt(3) - sqrt(5)]])",
        )
        proved = run(
            Request(
                ask=(
                    f"prove spectral({matrix}) * eigendiag({matrix}) * dagger(spectral({matrix})) "
                    f"= {matrix}"
                ),
                seed=1,
            )
        )
        self.assertEqual(
            proved.claims[0].atom,
            f"identity(spectral({matrix}) * eigendiag({matrix}) * dagger(spectral({matrix})) = {matrix})",
        )

    def test_spectral_decomposition_with_a_denesting_norm(self) -> None:
        matrix = "[[2 + sqrt(3), 1], [1, 2 - sqrt(3)]]"
        unitary = run(Request(ask=f"what is spectral({matrix})", seed=1))
        self.assertEqual(
            unitary.claims[0].atom,
            "cmatrix([[1/4 * sqrt(2) + 1/4 * sqrt(6), -1/4 * sqrt(2) + 1/4 * sqrt(6)], [-1/4 * sqrt(2) + 1/4 * sqrt(6), -1/4 * sqrt(2) - 1/4 * sqrt(6)]])",
        )
        diag = run(Request(ask=f"what is eigendiag({matrix})", seed=1))
        self.assertEqual(diag.claims[0].atom, "cmatrix([[4, 0], [0, 0]])")
        proved = run(
            Request(
                ask=(
                    f"prove spectral({matrix}) * eigendiag({matrix}) * dagger(spectral({matrix})) "
                    f"= {matrix}"
                ),
                seed=1,
            )
        )
        self.assertEqual(
            proved.claims[0].atom,
            f"identity(spectral({matrix}) * eigendiag({matrix}) * dagger(spectral({matrix})) = {matrix})",
        )

    def test_four_independent_radicands_stay_open(self) -> None:
        closed = run(
            Request(ask="prove sqrt(2) + sqrt(3) + sqrt(5) + sqrt(7) = 0", seed=1)
        )
        self.assertTrue(closed.claims[0].atom.startswith("open("))
        with self.assertRaises(NotExact):
            c_add(
                c_add(c_add(c_sqrt_ratio(Ratio(2, 1)), c_sqrt_ratio(Ratio(3, 1))), c_sqrt_ratio(Ratio(5, 1))),
                c_sqrt_ratio(Ratio(7, 1)),
            )
        tower = c_add(
            c_add(c_sqrt_ratio(Ratio(2, 1)), c_sqrt_ratio(Ratio(3, 1))),
            c_sqrt_ratio(Ratio(5, 1)),
        )
        self.assertEqual(show_cnum(c_mul(tower, c_inv(tower))), "1")
        self.assertEqual(show_cnum(c_one()), "1")


if __name__ == "__main__":
    unittest.main()
