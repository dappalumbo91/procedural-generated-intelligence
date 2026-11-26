"""Lie algebras su(2) and su(3), and exact U(1) and SU(2) gauge checks."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.gauge import GaugeMatrix, eval_gauge_result, su2_gen
from pgi.math.kernel import KernelError
from pgi.math.syntax import parse_term
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


_U = "[[3/5, -4/5], [4/5, 3/5]]"
_U_PRETTY = "[[3 / 5, -4 / 5], [4 / 5, 3 / 5]]"


class GaugeTests(unittest.TestCase):
    def test_su2_structure_jacobi_and_killing(self) -> None:
        self.assertEqual(
            run(Request(ask="what is su2(x)", seed=1)).claims[0].atom,
            "cmatrix([[0, 1/2], [1/2, 0]])",
        )
        self.assertEqual(
            run(Request(ask="prove commutator(su2(x), su2(y)) = i * su2(z)", seed=1)).claims[0].atom,
            "identity(commutator(su2(x), su2(y)) = i * su2(z))",
        )
        self.assertEqual(
            run(Request(ask="what is structure(su2, x, y, z)", seed=1)).claims[0].atom,
            "value(1)",
        )
        self.assertEqual(
            run(Request(ask="what is killing(su2, x, x)", seed=1)).claims[0].atom,
            "value(2)",
        )
        self.assertEqual(
            run(Request(ask="prove jacobi(su2) = 0", seed=1)).claims[0].atom,
            "identity(jacobi(su2) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove commutator(su2(x), su2(y)) = 2 * i * su2(z)", seed=1)).claims[0].atom,
            "open(commutator(su2(x), su2(y)) = 2 * i * su2(z) is not a theorem)",
        )

    def test_su3_gellmann_structure_jacobi_and_killing(self) -> None:
        self.assertEqual(
            run(Request(ask="what is structure(su3, 4, 5, 8)", seed=1)).claims[0].atom,
            "cnum(1/2 * sqrt(3))",
        )
        self.assertEqual(
            run(Request(ask="what is structure(su3, 1, 5, 6)", seed=1)).claims[0].atom,
            "ratio(-1,2)",
        )
        self.assertEqual(
            run(Request(ask="what is killing(su3, 1, 1)", seed=1)).claims[0].atom,
            "value(3)",
        )
        self.assertEqual(
            run(Request(ask="what is killing(su3, 1, 2)", seed=1)).claims[0].atom,
            "value(0)",
        )
        self.assertEqual(
            run(Request(ask="prove jacobi(su3) = 0", seed=1)).claims[0].atom,
            "identity(jacobi(su3) = 0)",
        )
        self.assertEqual(
            run(Request(ask="what is gellmann(8)", seed=1)).claims[0].atom,
            "cmatrix([[1/3 * sqrt(3), 0, 0], [0, 1/3 * sqrt(3), 0], [0, 0, -2/3 * sqrt(3)]])",
        )

    def test_u1_field_strength_is_gauge_invariant(self) -> None:
        self.assertEqual(
            run(Request(ask="what is fieldstrength(u1, x * y, x)", seed=1)).claims[0].atom,
            "poly(-x + 1)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove fieldstrength(u1, x * y + d(x * y, x), x + d(x * y, y)) = fieldstrength(u1, x * y, x)",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(fieldstrength(u1, x * y + d(x * y, x), x + d(x * y, y)) = fieldstrength(u1, x * y, x))",
        )

    def test_su2_field_strength_transforms_covariantly(self) -> None:
        covariant = run(
            Request(
                ask=(
                    f"prove fieldstrength(su2, adjoint({_U}, su2(x)), adjoint({_U}, su2(y))) "
                    f"= adjoint({_U}, fieldstrength(su2, su2(x), su2(y)))"
                ),
                seed=1,
            )
        )
        self.assertEqual(
            covariant.claims[0].atom,
            f"identity(fieldstrength(su2, adjoint({_U_PRETTY}, su2(x)), adjoint({_U_PRETTY}, su2(y))) = adjoint({_U_PRETTY}, fieldstrength(su2, su2(x), su2(y))))",
        )
        invariant = run(
            Request(
                ask=(
                    f"prove trace(fieldstrength(su2, adjoint({_U}, su2(x)), adjoint({_U}, su2(y)))^2) "
                    f"= trace(fieldstrength(su2, su2(x), su2(y))^2)"
                ),
                seed=1,
            )
        )
        self.assertEqual(
            invariant.claims[0].atom,
            f"identity(trace(fieldstrength(su2, adjoint({_U_PRETTY}, su2(x)), adjoint({_U_PRETTY}, su2(y)))^2) = trace(fieldstrength(su2, su2(x), su2(y))^2))",
        )
        rejected = run(Request(ask="what is adjoint([[1, 0], [0, 2]], su2(x))", seed=1))
        self.assertEqual(
            rejected.claims[0].atom,
            "open(this gauge transformation is not unitary)",
        )

    def test_pure_gauge_connection_has_vanishing_field_strength(self) -> None:
        self.assertEqual(
            run(Request(ask="what is fieldstrength(puregauge(su2rot))", seed=1)).claims[0].atom,
            "cmatrix([[0, 0], [0, 0]])",
        )

    def test_gauge_results_refuse_forgery(self) -> None:
        origin = parse_term("su2(x)")
        with self.assertRaises(KernelError):
            GaugeMatrix(su2_gen("z"), origin)
        self.assertEqual(eval_gauge_result(origin).value.rows, su2_gen("x").rows)

    def test_nonconstant_su2_gauge_transforms_covariantly(self) -> None:
        covariant = run(
            Request(
                ask=(
                    "prove fieldstrength(su2, gauge(su2rot, su2(x), x), gauge(su2rot, su2(y), y)) "
                    "= adjoint(su2rot, fieldstrength(su2, su2(x), su2(y)))"
                ),
                seed=1,
            )
        )
        self.assertEqual(
            covariant.claims[0].atom,
            "identity(fieldstrength(su2, gauge(su2rot, su2(x), x), gauge(su2rot, su2(y), y)) = adjoint(su2rot, fieldstrength(su2, su2(x), su2(y))))",
        )
        rejected = run(
            Request(
                ask="prove fieldstrength(su2, gauge(su2rot, su2(x), x), gauge(su2rot, su2(y), y)) = 0",
                seed=1,
            )
        )
        self.assertEqual(
            rejected.claims[0].atom,
            "open(fieldstrength(su2, gauge(su2rot, su2(x), x), gauge(su2rot, su2(y), y)) = 0 is not a theorem)",
        )

    def test_su3_gauge_transform_on_a_constant_connection(self) -> None:
        u = "[[3/5, -4/5, 0], [4/5, 3/5, 0], [0, 0, 1]]"
        u_pretty = "[[3 / 5, -4 / 5, 0], [4 / 5, 3 / 5, 0], [0, 0, 1]]"
        covariant = run(
            Request(
                ask=(
                    f"prove fieldstrength(su3, adjoint({u}, su3(1)), adjoint({u}, su3(2))) "
                    f"= adjoint({u}, fieldstrength(su3, su3(1), su3(2)))"
                ),
                seed=1,
            )
        )
        self.assertEqual(
            covariant.claims[0].atom,
            f"identity(fieldstrength(su3, adjoint({u_pretty}, su3(1)), adjoint({u_pretty}, su3(2))) = adjoint({u_pretty}, fieldstrength(su3, su3(1), su3(2))))",
        )
        invariant = run(
            Request(
                ask=(
                    f"prove trace(fieldstrength(su3, adjoint({u}, su3(1)), adjoint({u}, su3(2)))^2) "
                    f"= trace(fieldstrength(su3, su3(1), su3(2))^2)"
                ),
                seed=1,
            )
        )
        self.assertEqual(
            invariant.claims[0].atom,
            f"identity(trace(fieldstrength(su3, adjoint({u_pretty}, su3(1)), adjoint({u_pretty}, su3(2)))^2) = trace(fieldstrength(su3, su3(1), su3(2))^2))",
        )
