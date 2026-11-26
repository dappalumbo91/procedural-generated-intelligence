"""A general non-constant SU(2) family, other than the rational rotation already checked."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class Su2AxisTests(unittest.TestCase):
    def test_su2axis_acts_covariantly_on_the_field_strength(self) -> None:
        proved = run(
            Request(
                ask=(
                    "prove fieldstrength(su2, gauge(su2axis, su2(x), x), gauge(su2axis, su2(y), y)) "
                    "= adjoint(su2axis, fieldstrength(su2, su2(x), su2(y)))"
                ),
                seed=1,
            )
        )
        self.assertEqual(
            proved.claims[0].atom,
            "identity(fieldstrength(su2, gauge(su2axis, su2(x), x), gauge(su2axis, su2(y), y)) = adjoint(su2axis, fieldstrength(su2, su2(x), su2(y))))",
        )
        false = run(
            Request(
                ask="prove fieldstrength(su2, gauge(su2axis, su2(x), x), gauge(su2axis, su2(y), y)) = 0",
                seed=1,
            )
        )
        self.assertEqual(
            false.claims[0].atom,
            "open(fieldstrength(su2, gauge(su2axis, su2(x), x), gauge(su2axis, su2(y), y)) = 0 is not a theorem)",
        )
        # The original rational rotation is unchanged.
        old = run(
            Request(
                ask=(
                    "prove fieldstrength(su2, gauge(su2rot, su2(x), x), gauge(su2rot, su2(y), y)) "
                    "= adjoint(su2rot, fieldstrength(su2, su2(x), su2(y)))"
                ),
                seed=1,
            )
        )
        self.assertEqual(
            old.claims[0].atom,
            "identity(fieldstrength(su2, gauge(su2rot, su2(x), x), gauge(su2rot, su2(y), y)) = adjoint(su2rot, fieldstrength(su2, su2(x), su2(y))))",
        )


if __name__ == "__main__":
    unittest.main()
