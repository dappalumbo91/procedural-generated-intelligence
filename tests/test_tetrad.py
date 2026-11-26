"""Tetrad, spin connection, and the curved Dirac operator on Minkowski and flat FLRW."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class TetradTests(unittest.TestCase):
    def test_minkowski_tetrad_is_flat(self) -> None:
        self.assertEqual(
            run(Request(ask="prove tetradmetric(tetrad(minkowski4)) = metric(minkowski4)", seed=1)).claims[0].atom,
            "identity(tetradmetric(tetrad(minkowski4)) = metric(minkowski4))",
        )
        self.assertEqual(
            run(Request(ask="prove torsion(tetrad(minkowski4)) = 0", seed=1)).claims[0].atom,
            "identity(torsion(tetrad(minkowski4)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="what is spinconnection(tetrad(minkowski4))", seed=1)).claims[0].atom,
            "0",
        )
        self.assertEqual(
            run(Request(ask="prove dirac(tetrad(minkowski4), spinor(1, 0, 0, 0)) = 0", seed=1)).claims[0].atom,
            "identity(dirac(tetrad(minkowski4), spinor(1, 0, 0, 0)) = 0)",
        )

    def test_flrw_tetrad_spin_connection_and_dirac(self) -> None:
        self.assertEqual(
            run(Request(ask="prove tetradmetric(tetrad(flrw)) = metric(flrw)", seed=1)).claims[0].atom,
            "identity(tetradmetric(tetrad(flrw)) = metric(flrw))",
        )
        self.assertEqual(
            run(Request(ask="prove torsion(tetrad(flrw)) = 0", seed=1)).claims[0].atom,
            "identity(torsion(tetrad(flrw)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="what is dirac(tetrad(flrw), spinor(1, 0, 0, 0))", seed=1)).claims[0].atom,
            "[0, 0, -3/2 * d(a(t), t) / a(t), 0]",
        )
        self.assertEqual(
            run(Request(ask="prove torsion(tetrad(flrw)) = 1", seed=1)).claims[0].atom,
            "open(torsion(tetrad(flrw)) = 1 is not a theorem)",
        )
