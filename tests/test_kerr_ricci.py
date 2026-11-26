"""Ricci = 0 for the Kerr metric, checked exactly in the rational x = cos(theta) chart."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class KerrRicciTests(unittest.TestCase):
    def test_kerr_ricci_and_einstein_vanish(self) -> None:
        ricci = run(Request(ask="what is ricci(metric(kerr))", seed=1))
        self.assertEqual(ricci.claims[0].atom, "ricci(0)")
        proved = run(Request(ask="prove ricci(metric(kerr)) = 0", seed=1))
        self.assertEqual(
            proved.claims[0].atom,
            "identity(ricci(metric(kerr)) = 0)",
        )
        scalar = run(Request(ask="what is scalar(metric(kerr))", seed=1))
        self.assertEqual(scalar.claims[0].atom, "value(0)")
        einstein = run(Request(ask="what is einstein(metric(kerr))", seed=1))
        self.assertEqual(einstein.claims[0].atom, "einstein(0)")
        proved_g = run(Request(ask="prove einstein(metric(kerr)) = 0", seed=1))
        self.assertEqual(
            proved_g.claims[0].atom,
            "identity(einstein(metric(kerr)) = 0)",
        )
        false = run(Request(ask="prove ricci(metric(kerr)) = metric(kerr)", seed=1))
        self.assertEqual(
            false.claims[0].atom,
            "open(ricci(metric(kerr)) = metric(kerr) is not a theorem)",
        )


if __name__ == "__main__":
    unittest.main()
