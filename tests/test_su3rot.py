"""Non-constant SU(3) gauge transformation, checked identically."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class Su3RotTests(unittest.TestCase):
    def test_nonconstant_su3_acts_covariantly_on_the_field_strength(self) -> None:
        self.assertEqual(
            run(
                Request(
                    ask=(
                        "prove fieldstrength(su3, gauge(su3rot, su3(1), x), gauge(su3rot, su3(2), y)) "
                        "= adjoint(su3rot, fieldstrength(su3, su3(1), su3(2)))"
                    ),
                    seed=1,
                )
            ).claims[0].atom,
            "identity(fieldstrength(su3, gauge(su3rot, su3(1), x), gauge(su3rot, su3(2), y)) = adjoint(su3rot, fieldstrength(su3, su3(1), su3(2))))",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove fieldstrength(su3, gauge(su3rot, su3(1), x), gauge(su3rot, su3(2), y)) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "open(fieldstrength(su3, gauge(su3rot, su3(1), x), gauge(su3rot, su3(2), y)) = 0 is not a theorem)",
        )
