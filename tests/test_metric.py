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

    def test_angular_sphere_has_scalar_curvature_two(self) -> None:
        metric = run(Request(ask="what is metric(s2, angular)", seed=1))
        self.assertEqual(metric.claims[0].atom, "g([[1, 0], [0, sin(theta)^2]])")
        self.assertEqual(
            run(Request(ask="what is scalar(metric(s2, angular))", seed=1)).claims[0].atom,
            "value(2)",
        )
        ricci = run(
            Request(ask="prove ricci(metric(s2, angular)) = metric(s2, angular)", seed=1)
        )
        self.assertEqual(
            ricci.claims[0].atom,
            "identity(ricci(metric(s2, angular)) = metric(s2, angular))",
        )
        scalar = run(
            Request(ask="prove scalar(metric(s2, angular)) = 2", seed=1)
        )
        self.assertEqual(
            scalar.claims[0].atom,
            "identity(scalar(metric(s2, angular)) = 2)",
        )


    def test_schwarzschild_is_vacuum_with_the_kretschmann_scalar(self) -> None:
        metric = run(Request(ask="what is metric(schwarzschild)", seed=1))
        self.assertEqual(
            metric.claims[0].atom,
            "g([[(2 * m - r) / r, 0, 0, 0], [0, -r / (2 * m - r), 0, 0], [0, 0, r^2, 0], [0, 0, 0, sin(theta)^2 * r^2]])",
        )
        ricci = run(Request(ask="what is ricci(metric(schwarzschild))", seed=1))
        self.assertEqual(ricci.claims[0].atom, "ricci(0)")
        proved = run(
            Request(ask="prove ricci(metric(schwarzschild)) = 0", seed=1)
        )
        self.assertEqual(
            proved.claims[0].atom,
            "identity(ricci(metric(schwarzschild)) = 0)",
        )
        scalar = run(Request(ask="what is scalar(metric(schwarzschild))", seed=1))
        self.assertEqual(scalar.claims[0].atom, "value(0)")
        kretschmann = run(
            Request(ask="what is kretschmann(metric(schwarzschild))", seed=1)
        )
        self.assertEqual(kretschmann.claims[0].atom, "rat(48 * m^2 / r^6)")
        self.assertIn("Kretschmann", kretschmann.text(lod=2))
        proved_k = run(
            Request(ask="prove kretschmann(metric(schwarzschild)) = 48 * m^2 / r^6", seed=1)
        )
        self.assertEqual(
            proved_k.claims[0].atom,
            "identity(kretschmann(metric(schwarzschild)) = 48 * m^2 / r^6)",
        )
        einstein = run(
            Request(ask="what is einstein(metric(schwarzschild))", seed=1)
        )
        self.assertEqual(einstein.claims[0].atom, "einstein(0)")

    def test_flrw_einstein_tensor_is_exact(self) -> None:
        metric = run(Request(ask="what is metric(flrw)", seed=1))
        self.assertEqual(
            metric.claims[0].atom,
            "g([[-1, 0, 0, 0], [0, a(t)^2, 0, 0], [0, 0, a(t)^2, 0], [0, 0, 0, a(t)^2]])",
        )
        einstein = run(Request(ask="what is einstein(metric(flrw))", seed=1))
        self.assertEqual(
            einstein.claims[0].atom,
            "g([[3 * d(a(t), t)^2 / a(t)^2, 0, 0, 0], [0, -2 * a(t) * d(a(t), t, 2) - d(a(t), t)^2, 0, 0], [0, 0, -2 * a(t) * d(a(t), t, 2) - d(a(t), t)^2, 0], [0, 0, 0, -2 * a(t) * d(a(t), t, 2) - d(a(t), t)^2]])",
        )
        self.assertIn("Einstein", einstein.text(lod=2))

    def test_kerr_and_curved_flrw(self) -> None:
        closed = run(Request(ask="what is metric(flrw, closed)", seed=1))
        self.assertEqual(
            closed.claims[0].atom,
            "g([[-1, 0, 0, 0], [0, -a(t)^2 / (r^2 - 1), 0, 0], [0, 0, a(t)^2 * r^2, 0], [0, 0, 0, a(t)^2 * sin(theta)^2 * r^2]])",
        )
        closed_einstein = run(Request(ask="what is einstein(metric(flrw, closed))", seed=1))
        self.assertEqual(
            closed_einstein.claims[0].atom,
            "g([[(3 * d(a(t), t)^2 + 3) / a(t)^2, 0, 0, 0], [0, (2 * a(t) * d(a(t), t, 2) + d(a(t), t)^2 + 1) / (r^2 - 1), 0, 0], [0, 0, -2 * a(t) * d(a(t), t, 2) * r^2 - d(a(t), t)^2 * r^2 - r^2, 0], [0, 0, 0, 2 * a(t) * d(a(t), t, 2) * cos(theta)^2 * r^2 + d(a(t), t)^2 * cos(theta)^2 * r^2 - 2 * a(t) * d(a(t), t, 2) * r^2 - d(a(t), t)^2 * r^2 + cos(theta)^2 * r^2 - r^2]])",
        )
        opened = run(Request(ask="what is metric(flrw, open)", seed=1))
        self.assertEqual(
            opened.claims[0].atom,
            "g([[-1, 0, 0, 0], [0, a(t)^2 / (r^2 + 1), 0, 0], [0, 0, a(t)^2 * r^2, 0], [0, 0, 0, a(t)^2 * sin(theta)^2 * r^2]])",
        )
        open_einstein = run(Request(ask="what is einstein(metric(flrw, open))", seed=1))
        self.assertEqual(
            open_einstein.claims[0].atom,
            "g([[(3 * d(a(t), t)^2 - 3) / a(t)^2, 0, 0, 0], [0, (-2 * a(t) * d(a(t), t, 2) - d(a(t), t)^2 + 1) / (r^2 + 1), 0, 0], [0, 0, -2 * a(t) * d(a(t), t, 2) * r^2 - d(a(t), t)^2 * r^2 + r^2, 0], [0, 0, 0, 2 * a(t) * d(a(t), t, 2) * cos(theta)^2 * r^2 + d(a(t), t)^2 * cos(theta)^2 * r^2 - 2 * a(t) * d(a(t), t, 2) * r^2 - d(a(t), t)^2 * r^2 - cos(theta)^2 * r^2 + r^2]])",
        )
        kerr = run(Request(ask="what is metric(kerr)", seed=1))
        self.assertEqual(
            kerr.claims[0].atom,
            "g([[(-cos(theta)^2 * a^2 + 2 * m * r - r^2) / (cos(theta)^2 * a^2 + r^2), 0, 0, (2 * cos(theta)^2 * a * m * r - 2 * a * m * r) / (cos(theta)^2 * a^2 + r^2)], [0, (cos(theta)^2 * a^2 + r^2) / (a^2 - 2 * m * r + r^2), 0, 0], [0, 0, cos(theta)^2 * a^2 + r^2, 0], [(2 * cos(theta)^2 * a * m * r - 2 * a * m * r) / (cos(theta)^2 * a^2 + r^2), 0, 0, (-cos(theta)^4 * a^4 + 2 * cos(theta)^4 * a^2 * m * r - cos(theta)^4 * a^2 * r^2 + cos(theta)^2 * a^4 - 4 * cos(theta)^2 * a^2 * m * r - cos(theta)^2 * r^4 + 2 * a^2 * m * r + a^2 * r^2 + r^4) / (cos(theta)^2 * a^2 + r^2)]])",
        )



if __name__ == "__main__":
    unittest.main()
