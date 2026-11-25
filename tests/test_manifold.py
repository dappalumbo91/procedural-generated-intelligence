"""Charts, transition maps, and Jacobians of rational maps."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.manifold import jac_inv, jac_is_identity, map_jacobian, transition_map
from pgi.math.syntax import parse_term, pretty
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class ManifoldTests(unittest.TestCase):
    def test_stereographic_and_plane_transitions_compose_to_the_identity(self) -> None:
        sphere = run(
            Request(
                ask="what is compose(transition(s2, south, north), transition(s2, north, south))",
                seed=1,
            )
        )
        self.assertEqual(sphere.claims[0].atom, "identity(u, v)")

        circle = run(
            Request(
                ask="what is compose(transition(s1, south, north), transition(s1, north, south))",
                seed=1,
            )
        )
        self.assertEqual(circle.claims[0].atom, "identity(u)")

        plane = run(
            Request(
                ask="what is compose(transition(r2, uv, xy), transition(r2, xy, uv))",
                seed=1,
            )
        )
        self.assertEqual(plane.claims[0].atom, "identity(x, y)")

        projective = run(
            Request(
                ask="what is compose(transition(rp1, u1, u0), transition(rp1, u0, u1))",
                seed=1,
            )
        )
        self.assertEqual(projective.claims[0].atom, "identity(t)")

        involution = run(
            Request(
                ask="what is compose(transition(s2, north, south), transition(s2, south, north))",
                seed=1,
            )
        )
        self.assertEqual(involution.claims[0].atom, "identity(p, q)")

    def test_plane_cocycle_and_a_linear_jacobian(self) -> None:
        cocycle = run(
            Request(
                ask=(
                    "prove compose(transition(r2, uv, pq), transition(r2, xy, uv)) "
                    "= transition(r2, xy, pq)"
                ),
                seed=1,
            )
        )
        self.assertEqual(
            cocycle.claims[0].atom,
            "identity(compose(transition(r2, uv, pq), transition(r2, xy, uv)) = transition(r2, xy, pq))",
        )

        jacobian = run(Request(ask="what is jacobian(transition(r2, xy, uv))", seed=1))
        self.assertEqual(jacobian.claims[0].atom, "jac([[1, 1], [1, -1]])")

        determinant = run(Request(ask="what is det(jacobian(transition(r2, xy, uv)))", seed=1))
        self.assertEqual(determinant.claims[0].atom, "value(-2)")

        identity_jac = run(Request(ask="what is jacobian(identity(u, v))", seed=1))
        self.assertEqual(identity_jac.claims[0].atom, "jac([[1, 0], [0, 1]])")

        proved = run(
            Request(
                ask="prove compose(transition(s2, south, north), transition(s2, north, south)) = identity(u, v)",
                seed=1,
            )
        )
        self.assertEqual(
            proved.claims[0].atom,
            "identity(compose(transition(s2, south, north), transition(s2, north, south)) = identity(u, v))",
        )

    def test_sphere_jacobian_determinant_and_inverse(self) -> None:
        determinant = run(
            Request(ask="what is det(jacobian(transition(s2, north, south)))", seed=1)
        )
        self.assertEqual(
            determinant.claims[0].atom,
            "rat(-1 / (u^4 + 2 * u^2 * v^2 + v^4))",
        )
        closed = run(
            Request(
                ask="prove det(jacobian(transition(s2, north, south))) = -1 / (u^2 + v^2)^2",
                seed=1,
            )
        )
        self.assertEqual(
            closed.claims[0].atom,
            "identity(det(jacobian(transition(s2, north, south))) = -1 / (u^2 + v^2)^2)",
        )

        inverse = transition_map("s2", "north", "south")
        jac = map_jacobian(inverse)
        from pgi.math.manifold import jac_mul

        self.assertTrue(jac_is_identity(jac_mul(jac_inv(jac), jac)))
        self.assertTrue(jac_is_identity(jac_mul(jac, jac_inv(jac))))

    def test_a_non_inverse_composition_and_an_unknown_chart_stay_open(self) -> None:
        not_identity = run(
            Request(
                ask="prove compose(transition(r2, xy, uv), transition(r2, xy, uv)) = identity(x, y)",
                seed=1,
            )
        )
        self.assertTrue(not_identity.claims[0].atom.startswith("open("))

        unknown = run(Request(ask="what is transition(s2, north, east)", seed=1))
        self.assertEqual(unknown.claims[0].atom, "open(this chart is not in the atlas)")

        angular = run(Request(ask="what is transition(s2, north, spherical)", seed=1))
        self.assertEqual(angular.claims[0].atom, "open(this chart is not in the atlas)")

        shown = pretty(parse_term("compose(transition(s2, south, north), transition(s2, north, south))"))
        self.assertEqual(
            shown,
            "compose(transition(s2, south, north), transition(s2, north, south))",
        )


if __name__ == "__main__":
    unittest.main()
