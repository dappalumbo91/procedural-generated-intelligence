"""Stokes' theorem on admitted chart rectangles, checked exactly."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class StokesTests(unittest.TestCase):
    def test_fundamental_theorem_on_an_interval(self) -> None:
        self.assertEqual(
            run(Request(ask="what is integral(exterior(zeroform(x^2, x)), box(x, 0, 2))", seed=1)).claims[0].atom,
            "4",
        )
        self.assertEqual(
            run(Request(ask="what is integral(zeroform(x^2, x), boundary(box(x, 0, 2)))", seed=1)).claims[0].atom,
            "4",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove integral(exterior(zeroform(x^2, x)), box(x, 0, 2)) = integral(zeroform(x^2, x), boundary(box(x, 0, 2)))",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(integral(exterior(zeroform(x^2, x)), box(x, 0, 2)) = integral(zeroform(x^2, x), boundary(box(x, 0, 2))))",
        )
        self.assertEqual(
            run(Request(ask="prove stokes(zeroform(x^2, x), box(x, 0, 2)) = 0", seed=1)).claims[0].atom,
            "identity(stokes(zeroform(x^2, x), box(x, 0, 2)) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove integral(exterior(zeroform(-cos(x), x)), box(x, 0, pi)) = 2",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(integral(exterior(zeroform((-cos(x)), x)), box(x, 0, pi)) = 2)",
        )

    def test_stokes_on_the_unit_square_and_unit_cube(self) -> None:
        self.assertEqual(
            run(
                Request(
                    ask="what is integral(exterior((-y) * coframe(x, x, y) + x * coframe(y, x, y)), box(x, 0, 1, y, 0, 1))",
                    seed=1,
                )
            ).claims[0].atom,
            "2",
        )
        self.assertEqual(
            run(
                Request(
                    ask="what is integral((-y) * coframe(x, x, y) + x * coframe(y, x, y), boundary(box(x, 0, 1, y, 0, 1)))",
                    seed=1,
                )
            ).claims[0].atom,
            "2",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove integral(exterior((-y) * coframe(x, x, y) + x * coframe(y, x, y)), box(x, 0, 1, y, 0, 1)) = integral((-y) * coframe(x, x, y) + x * coframe(y, x, y), boundary(box(x, 0, 1, y, 0, 1)))",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(integral(exterior((-y) * coframe(x, x, y) + x * coframe(y, x, y)), box(x, 0, 1, y, 0, 1)) = integral((-y) * coframe(x, x, y) + x * coframe(y, x, y), boundary(box(x, 0, 1, y, 0, 1))))",
        )
        self.assertEqual(
            run(Request(ask="prove stokes((-y) * coframe(x, x, y) + x * coframe(y, x, y), box(x, 0, 1, y, 0, 1)) = 0", seed=1)).claims[0].atom,
            "identity(stokes((-y) * coframe(x, x, y) + x * coframe(y, x, y), box(x, 0, 1, y, 0, 1)) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove stokes(x * coframe(y, x, y), box(x, 0, 1, y, 0, 1)) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(stokes(x * coframe(y, x, y), box(x, 0, 1, y, 0, 1)) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove stokes(x * wedge(coframe(y, x, y, z), coframe(z, x, y, z)), box(x, 0, 1, y, 0, 1, z, 0, 1)) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(stokes(x * wedge(coframe(y, x, y, z), coframe(z, x, y, z)), box(x, 0, 1, y, 0, 1, z, 0, 1)) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="what is integral(exterior(x * wedge(coframe(y, x, y, z), coframe(z, x, y, z))), box(x, 0, 1, y, 0, 1, z, 0, 1))",
                    seed=1,
                )
            ).claims[0].atom,
            "1",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove integral(exterior((-y) * coframe(x, x, y) + x * coframe(y, x, y)), box(x, 0, 1, y, 0, 1)) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "open(integral(exterior((-y) * coframe(x, x, y) + x * coframe(y, x, y)), box(x, 0, 1, y, 0, 1)) = 0 is not a theorem)",
        )

    def test_stokes_on_an_angular_rectangle_and_the_sphere_area(self) -> None:
        self.assertEqual(
            run(
                Request(
                    ask="prove stokes((-cos(theta)) * coframe(phi, theta, phi), box(theta, 1, 2, phi, 0, 1)) = 0",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(stokes((-cos(theta)) * coframe(phi, theta, phi), box(theta, 1, 2, phi, 0, 1)) = 0)",
        )
        self.assertEqual(
            run(
                Request(
                    ask="what is integral(exterior((-cos(theta)) * coframe(phi, theta, phi)), box(theta, 0, pi, phi, 0, 2 * pi))",
                    seed=1,
                )
            ).claims[0].atom,
            "4 * pi",
        )
        self.assertEqual(
            run(
                Request(
                    ask="prove integral(exterior((-cos(theta)) * coframe(phi, theta, phi)), box(theta, 0, pi, phi, 0, 2 * pi)) = 4 * pi",
                    seed=1,
                )
            ).claims[0].atom,
            "identity(integral(exterior((-cos(theta)) * coframe(phi, theta, phi)), box(theta, 0, pi, phi, 0, 2 * pi)) = 4 * pi)",
        )
