"""Action density, Euler–Lagrange, and Noether identities for admitted Lagrangians."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


HO = "lagrangian(1 / 2 * v^2 - 1 / 2 * q^2, q, v, t)"
FREE = "lagrangian(1 / 2 * v^2, q, v, t)"
PEN = "lagrangian(1 / 2 * v^2 + cos(q), q, v, t)"


class VaryTests(unittest.TestCase):
    def test_euler_lagrange_and_noether_identities(self) -> None:
        self.assertEqual(
            run(Request(ask=f"what is euler({HO})", seed=1)).claims[0].atom,
            "accel(q, t) + q",
        )
        self.assertEqual(
            run(Request(ask=f"prove euler({HO}) = accel(q, t) + q", seed=1)).claims[0].atom,
            f"identity(euler({HO}) = accel(q, t) + q)",
        )
        self.assertEqual(
            run(Request(ask=f"what is energy({HO})", seed=1)).claims[0].atom,
            "1/2 * q^2 + 1/2 * vel(q, t)^2",
        )
        self.assertEqual(
            run(Request(ask=f"prove energy({HO}) = 1 / 2 * q^2 + 1 / 2 * vel(q, t)^2", seed=1)).claims[0].atom,
            f"identity(energy({HO}) = 1 / 2 * q^2 + 1 / 2 * vel(q, t)^2)",
        )
        self.assertEqual(
            run(Request(ask=f"what is canonical({HO})", seed=1)).claims[0].atom,
            "vel(q, t)",
        )
        self.assertEqual(
            run(Request(ask=f"prove noether({HO}, time) = 0", seed=1)).claims[0].atom,
            f"identity(noether({HO}, time) = 0)",
        )
        self.assertEqual(
            run(Request(ask=f"prove noether({HO}, shift) = 0", seed=1)).claims[0].atom,
            f"identity(noether({HO}, shift) = 0)",
        )
        self.assertEqual(
            run(Request(ask=f"prove noether({HO}, time) = 1", seed=1)).claims[0].atom,
            f"open(noether({HO}, time) = 1 is not a theorem)",
        )
        self.assertEqual(
            run(Request(ask=f"what is euler({FREE})", seed=1)).claims[0].atom,
            "accel(q, t)",
        )
        self.assertEqual(
            run(Request(ask=f"prove canonical({FREE}) = vel(q, t)", seed=1)).claims[0].atom,
            f"identity(canonical({FREE}) = vel(q, t))",
        )
        self.assertEqual(
            run(Request(ask=f"prove noether({FREE}, time) = 0", seed=1)).claims[0].atom,
            f"identity(noether({FREE}, time) = 0)",
        )
        self.assertEqual(
            run(Request(ask=f"what is euler({PEN})", seed=1)).claims[0].atom,
            "sin(q) + accel(q, t)",
        )
        self.assertEqual(
            run(Request(ask=f"prove euler({PEN}) = accel(q, t) + sin(q)", seed=1)).claims[0].atom,
            f"identity(euler({PEN}) = accel(q, t) + sin(q))",
        )
        self.assertEqual(
            run(Request(ask=f"prove noether({PEN}, time) = 0", seed=1)).claims[0].atom,
            f"identity(noether({PEN}, time) = 0)",
        )
        self.assertEqual(
            run(Request(ask=f"what is action({HO})", seed=1)).claims[0].atom,
            "lagrangian(-1/2 * q^2 + 1/2 * vel(q, t)^2, q, v, t)",
        )
