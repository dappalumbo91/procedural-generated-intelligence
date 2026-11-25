"""Metrics, tangent vectors, and curvature of rational charts."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


_SPHERE_FACTOR = "4 / (u^4 + 2 * u^2 * v^2 + v^4 + 2 * u^2 + 2 * v^2 + 1)"


class MetricTests(unittest.TestCase):
    def test_euclidean_minkowski_and_stereographic_metrics(self) -> None:
        euclidean = run(Request(ask="what is metric(e2)", seed=1))
        self.assertEqual(euclidean.claims[0].atom, "g([[1, 0], [0, 1]])")

        changed = run(Request(ask="what is metric(e2, uv)", seed=1))
        self.assertEqual(changed.claims[0].atom, "g([[1/2, 0], [0, 1/2]])")

        minkowski = run(Request(ask="what is metric(minkowski2)", seed=1))
        self.assertEqual(minkowski.claims[0].atom, "g([[-1, 0], [0, 1]])")

        null = run(Request(ask="what is metric(minkowski2, uv)", seed=1))
        self.assertEqual(null.claims[0].atom, "g([[0, -1/2], [-1/2, 0]])")

        sphere = run(Request(ask="what is metric(s2, north)", seed=1))
        self.assertEqual(
            sphere.claims[0].atom,
            f"g([[{_SPHERE_FACTOR}, 0], [0, {_SPHERE_FACTOR}]])",
        )

        pulled = run(
            Request(
                ask="prove pullback(metric(e3), embedding(s2, north)) = metric(s2, north)",
                seed=1,
            )
        )
        self.assertEqual(
            pulled.claims[0].atom,
            "identity(pullback(metric(e3), embedding(s2, north)) = metric(s2, north))",
        )

    def test_tangent_vectors_act_and_pair_with_the_metric(self) -> None:
        applied = run(Request(ask="what is apply(vector(e2, 1, 0), x^2)", seed=1))
        self.assertEqual(applied.claims[0].atom, "poly(2 * x)")

        paired = run(
            Request(ask="what is dot(metric(e2), vector(e2, 1, 0), vector(e2, 1, 0))", seed=1)
        )
        self.assertEqual(paired.claims[0].atom, "value(1)")

        sphere_pair = run(
            Request(
                ask="what is dot(metric(s2, north), vector(s2, north, 1, 0), vector(s2, north, 1, 0))",
                seed=1,
            )
        )
        self.assertEqual(sphere_pair.claims[0].atom, f"rat({_SPHERE_FACTOR})")

    def test_curvature_of_flat_space_and_the_unit_sphere(self) -> None:
        self.assertEqual(
            run(Request(ask="what is christoffel(metric(e2))", seed=1)).claims[0].atom,
            "christoffel(0)",
        )
        self.assertEqual(
            run(Request(ask="what is riemann(metric(e2))", seed=1)).claims[0].atom,
            "riemann(0)",
        )
        self.assertEqual(
            run(Request(ask="what is ricci(metric(e2))", seed=1)).claims[0].atom,
            "ricci(0)",
        )
        self.assertEqual(
            run(Request(ask="what is scalar(metric(e2))", seed=1)).claims[0].atom,
            "value(0)",
        )
        self.assertEqual(
            run(Request(ask="what is scalar(metric(minkowski2))", seed=1)).claims[0].atom,
            "value(0)",
        )
        self.assertEqual(
            run(Request(ask="what is scalar(metric(s2, north))", seed=1)).claims[0].atom,
            "value(2)",
        )

        ricci_equals = run(
            Request(ask="prove ricci(metric(s2, north)) = metric(s2, north)", seed=1)
        )
        self.assertEqual(
            ricci_equals.claims[0].atom,
            "identity(ricci(metric(s2, north)) = metric(s2, north))",
        )
        scalar_equals = run(
            Request(ask="prove scalar(metric(s2, north)) = 2", seed=1)
        )
        self.assertEqual(
            scalar_equals.claims[0].atom,
            "identity(scalar(metric(s2, north)) = 2)",
        )
        flat_on_sphere = run(
            Request(ask="prove scalar(metric(s2, north)) = 0", seed=1)
        )
        self.assertTrue(flat_on_sphere.claims[0].atom.startswith("open("))

    def test_an_unknown_chart_stays_open(self) -> None:
        unknown = run(Request(ask="what is metric(s2, spherical)", seed=1))
        self.assertEqual(unknown.claims[0].atom, "open(this chart is not in the atlas)")


if __name__ == "__main__":
    unittest.main()
