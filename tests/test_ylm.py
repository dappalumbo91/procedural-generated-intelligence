"""Solid spherical harmonics: L^2 and Lz eigen-identities."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class YlmTests(unittest.TestCase):
    def test_solid_harmonics_are_l2_and_lz_eigenfunctions(self) -> None:
        self.assertEqual(
            run(Request(ask="what is ylm(0, 0)", seed=1)).claims[0].atom,
            "1",
        )
        self.assertEqual(
            run(Request(ask="what is ylm(1, 0)", seed=1)).claims[0].atom,
            "z",
        )
        self.assertEqual(
            run(Request(ask="what is ylm(1, 1)", seed=1)).claims[0].atom,
            "i * y + x",
        )
        self.assertEqual(
            run(Request(ask="what is ylm(1, -1)", seed=1)).claims[0].atom,
            "-i * y + x",
        )
        self.assertEqual(
            run(Request(ask="what is ylm(2, 0)", seed=1)).claims[0].atom,
            "2 * z^2 - y^2 - x^2",
        )
        self.assertEqual(
            run(Request(ask="prove l2(ylm(0, 0)) = 0", seed=1)).claims[0].atom,
            "identity(l2(ylm(0, 0)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove l2(ylm(1, 0)) = 2 * ylm(1, 0)", seed=1)).claims[0].atom,
            "identity(l2(ylm(1, 0)) = 2 * ylm(1, 0))",
        )
        self.assertEqual(
            run(Request(ask="prove lz(ylm(1, 0)) = 0", seed=1)).claims[0].atom,
            "identity(lz(ylm(1, 0)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove lz(ylm(1, 1)) = ylm(1, 1)", seed=1)).claims[0].atom,
            "identity(lz(ylm(1, 1)) = ylm(1, 1))",
        )
        self.assertEqual(
            run(Request(ask="prove lz(ylm(1, -1)) = -1 * ylm(1, -1)", seed=1)).claims[0].atom,
            "identity(lz(ylm(1, -1)) = -1 * ylm(1, -1))",
        )
        self.assertEqual(
            run(Request(ask="prove l2(ylm(2, 0)) = 6 * ylm(2, 0)", seed=1)).claims[0].atom,
            "identity(l2(ylm(2, 0)) = 6 * ylm(2, 0))",
        )
        self.assertEqual(
            run(Request(ask="prove l2(ylm(2, 2)) = 6 * ylm(2, 2)", seed=1)).claims[0].atom,
            "identity(l2(ylm(2, 2)) = 6 * ylm(2, 2))",
        )
        self.assertEqual(
            run(Request(ask="prove lz(ylm(2, 2)) = 2 * ylm(2, 2)", seed=1)).claims[0].atom,
            "identity(lz(ylm(2, 2)) = 2 * ylm(2, 2))",
        )
        self.assertEqual(
            run(Request(ask="prove lz(ylm(2, -2)) = -2 * ylm(2, -2)", seed=1)).claims[0].atom,
            "identity(lz(ylm(2, -2)) = -2 * ylm(2, -2))",
        )
        self.assertEqual(
            run(Request(ask="prove l2(ylm(1, 0)) = 0", seed=1)).claims[0].atom,
            "open(l2(ylm(1, 0)) = 0 is not a theorem)",
        )
        self.assertEqual(
            run(Request(ask="what is ylm(3, 0)", seed=1)).claims[0].atom,
            "open(a spherical harmonic is admitted here only for l = 0, 1, or 2, with |m| <= l)",
        )
