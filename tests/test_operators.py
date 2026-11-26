"""Canonical commutators, angular momentum, and oscillator ladder operators."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.kernel import KernelError
from pgi.math.operators import OperatorTheorem, _eval_op, _standing, angmom, commutator, op_zero
from pgi.math.syntax import parse_term
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class OperatorTests(unittest.TestCase):
    def test_canonical_commutators_are_exact(self) -> None:
        self.assertEqual(
            run(Request(ask="what is commutator(position(x), momentum(x))", seed=1)).claims[0].atom,
            "i",
        )
        self.assertEqual(
            run(Request(ask="prove commutator(position(x), momentum(x)) = i", seed=1)).claims[0].atom,
            "identity(commutator(position(x), momentum(x)) = i)",
        )
        self.assertEqual(
            run(Request(ask="prove commutator(position(x), momentum(y)) = 0", seed=1)).claims[0].atom,
            "identity(commutator(position(x), momentum(y)) = 0)",
        )
        self.assertEqual(
            run(Request(ask="prove commutator(position(x), position(y)) = 0", seed=1)).claims[0].atom,
            "identity(commutator(position(x), position(y)) = 0)",
        )

    def test_angular_momentum_and_ladder_algebras(self) -> None:
        self.assertEqual(
            run(Request(ask="prove commutator(angmom(x), angmom(y)) = i * angmom(z)", seed=1)).claims[0].atom,
            "identity(commutator(angmom(x), angmom(y)) = i * angmom(z))",
        )
        self.assertEqual(
            run(Request(ask="prove commutator(angmom(y), angmom(z)) = i * angmom(x)", seed=1)).claims[0].atom,
            "identity(commutator(angmom(y), angmom(z)) = i * angmom(x))",
        )
        self.assertEqual(
            run(Request(ask="prove commutator(angmom(z), angmom(x)) = i * angmom(y)", seed=1)).claims[0].atom,
            "identity(commutator(angmom(z), angmom(x)) = i * angmom(y))",
        )
        self.assertEqual(
            run(Request(ask="prove commutator(ladder(lower), ladder(raise)) = 1", seed=1)).claims[0].atom,
            "identity(commutator(ladder(lower), ladder(raise)) = 1)",
        )
        self.assertEqual(
            run(Request(ask="prove commutator(angmom(x), angmom(y)) = 0", seed=1)).claims[0].atom,
            "open(commutator(angmom(x), angmom(y)) = 0 is not a theorem)",
        )

    def test_operator_results_refuse_forgery_and_leave_matrix_commutators_alone(self) -> None:
        _standing()
        origin = parse_term("angmom(x)")
        with self.assertRaises(KernelError):
            OperatorTheorem(angmom("z"), origin)
        self.assertEqual(
            run(Request(ask="what is commutator(pauli(x), pauli(y))", seed=1)).claims[0].atom,
            "cmatrix([[2 * i, 0], [0, -2 * i]])",
        )
