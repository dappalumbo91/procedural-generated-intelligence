"""Finite-dimensional inner product spaces over Q(i) and Q(√d, i)."""

from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.hilbert import HilbTheorem, eval_hilbert_matrix, pauli
from pgi.math.kernel import KernelError
from pgi.math.syntax import parse_term
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class HilbertTests(unittest.TestCase):
    def test_imaginary_unit_and_complex_arithmetic(self) -> None:
        squared = run(Request(ask="prove i * i = -1", seed=1))
        self.assertEqual(squared.claims[0].atom, "identity(i * i = -1)")
        value = run(Request(ask="what is i * i", seed=1))
        self.assertEqual(value.claims[0].atom, "value(-1)")
        phase = run(Request(ask="what is (1 + i) / sqrt(2)", seed=1))
        self.assertEqual(
            phase.claims[0].atom,
            "cnum(1/2 * sqrt(2) + 1/2 * sqrt(2) * i)",
        )

    def test_inner_product_axioms(self) -> None:
        unit = run(Request(ask="what is inner(ket(0), ket(0))", seed=1))
        self.assertEqual(unit.claims[0].atom, "value(1)")
        orthogonal = run(Request(ask="what is inner(ket(plus), ket(minus))", seed=1))
        self.assertEqual(orthogonal.claims[0].atom, "value(0)")
        linear = run(
            Request(ask="what is inner(ket(0), 2 * ket(0) + i * ket(1))", seed=1)
        )
        self.assertEqual(linear.claims[0].atom, "value(2)")
        second = run(Request(ask="prove inner(ket(0), i * ket(0)) = i", seed=1))
        self.assertEqual(second.claims[0].atom, "identity(inner(ket(0), i * ket(0)) = i)")
        first = run(Request(ask="prove inner(i * ket(0), ket(0)) = -i", seed=1))
        self.assertEqual(
            first.claims[0].atom,
            "identity(inner(i * ket(0), ket(0)) = (-i))",
        )

    def test_gram_schmidt_is_kept_only_when_orthonormal(self) -> None:
        orthonormal = run(Request(ask="what is gramschmidt([[1, 1], [0, 1]])", seed=1))
        self.assertEqual(orthonormal.claims[0].atom, "cmatrix([[1, 0], [0, 1]])")
        hadamard = run(Request(ask="what is gramschmidt([[1, 1], [1, 0]])", seed=1))
        self.assertEqual(
            hadamard.claims[0].atom,
            "cmatrix([[1/2 * sqrt(2), 1/2 * sqrt(2)], [1/2 * sqrt(2), -1/2 * sqrt(2)]])",
        )
        dependent = run(Request(ask="what is gramschmidt([[1, 2], [2, 4]])", seed=1))
        self.assertEqual(
            dependent.claims[0].atom,
            "open(Gram–Schmidt met a linearly dependent vector)",
        )

    def test_hermitian_and_unitary_checks(self) -> None:
        self.assertEqual(
            run(Request(ask="what is hermitian(pauli(y))", seed=1)).claims[0].atom,
            "value(1)",
        )
        self.assertEqual(
            run(Request(ask="what is unitary(pauli(y))", seed=1)).claims[0].atom,
            "value(1)",
        )
        self.assertEqual(
            run(Request(ask="prove dagger(pauli(y)) = pauli(y)", seed=1)).claims[0].atom,
            "identity(dagger(pauli(y)) = pauli(y))",
        )
        self.assertEqual(
            run(Request(ask="prove hermitian([[0, -i], [i, 0]]) = 1", seed=1)).claims[0].atom,
            "identity(hermitian([[0, (-i)], [i, 0]]) = 1)",
        )
        self.assertEqual(
            run(Request(ask="what is hermitian([[0, 1], [0, 0]])", seed=1)).claims[0].atom,
            "value(0)",
        )

    def test_pauli_commutation_and_squares(self) -> None:
        xy = run(
            Request(ask="prove commutator(pauli(x), pauli(y)) = 2 * i * pauli(z)", seed=1)
        )
        self.assertEqual(
            xy.claims[0].atom,
            "identity(commutator(pauli(x), pauli(y)) = 2 * i * pauli(z))",
        )
        yz = run(
            Request(ask="prove commutator(pauli(y), pauli(z)) = 2 * i * pauli(x)", seed=1)
        )
        self.assertEqual(
            yz.claims[0].atom,
            "identity(commutator(pauli(y), pauli(z)) = 2 * i * pauli(x))",
        )
        zx = run(
            Request(ask="prove commutator(pauli(z), pauli(x)) = 2 * i * pauli(y)", seed=1)
        )
        self.assertEqual(
            zx.claims[0].atom,
            "identity(commutator(pauli(z), pauli(x)) = 2 * i * pauli(y))",
        )
        self.assertEqual(
            run(Request(ask="prove pauli(x)^2 = [[1, 0], [0, 1]]", seed=1)).claims[0].atom,
            "identity(pauli(x)^2 = [[1, 0], [0, 1]])",
        )
        self.assertEqual(
            run(Request(ask="what is pauli(x)", seed=1)).claims[0].atom,
            "cmatrix([[0, 1], [1, 0]])",
        )
        self.assertEqual(
            run(Request(ask="what is det([[0, -i], [i, 0]])", seed=1)).claims[0].atom,
            "value(-1)",
        )

    def test_spectral_decomposition_of_a_hermitian_matrix(self) -> None:
        unitary = run(Request(ask="what is spectral(pauli(x))", seed=1))
        self.assertEqual(
            unitary.claims[0].atom,
            "cmatrix([[1/2 * sqrt(2), 1/2 * sqrt(2)], [1/2 * sqrt(2), -1/2 * sqrt(2)]])",
        )
        diagonal = run(Request(ask="what is eigendiag(pauli(x))", seed=1))
        self.assertEqual(diagonal.claims[0].atom, "cmatrix([[1, 0], [0, -1]])")
        rebuilt = run(
            Request(
                ask="prove spectral(pauli(x)) * eigendiag(pauli(x)) * dagger(spectral(pauli(x))) = pauli(x)",
                seed=1,
            )
        )
        self.assertEqual(
            rebuilt.claims[0].atom,
            "identity(spectral(pauli(x)) * eigendiag(pauli(x)) * dagger(spectral(pauli(x))) = pauli(x))",
        )
        not_hermitian = run(Request(ask="what is spectral([[0, 1], [0, 0]])", seed=1))
        self.assertEqual(not_hermitian.claims[0].atom, "open(this matrix is not Hermitian)")
        larger = run(
            Request(
                ask="what is spectral([[1, 0, 0], [0, 1, 0], [0, 0, 1]])",
                seed=1,
            )
        )
        self.assertEqual(
            larger.claims[0].atom,
            "open(spectral decomposition is exact here only for 2×2 Hermitian matrices)",
        )

    def test_tensor_products_and_spin_half(self) -> None:
        product = run(Request(ask="what is tensor(ket(0), ket(1))", seed=1))
        self.assertEqual(product.claims[0].atom, "cmatrix([[0], [1], [0], [0]])")
        identity = run(
            Request(
                ask="prove tensor([[1, 0], [0, 1]], [[1, 0], [0, 1]]) = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]",
                seed=1,
            )
        )
        self.assertEqual(
            identity.claims[0].atom,
            "identity(tensor([[1, 0], [0, 1]], [[1, 0], [0, 1]]) = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])",
        )
        plus = run(Request(ask="what is ket(plus)", seed=1))
        self.assertEqual(
            plus.claims[0].atom,
            "cmatrix([[1/2 * sqrt(2)], [1/2 * sqrt(2)]])",
        )
        eigen_plus = run(Request(ask="prove pauli(x) * ket(plus) = ket(plus)", seed=1))
        self.assertEqual(
            eigen_plus.claims[0].atom,
            "identity(pauli(x) * ket(+) = ket(+))",
        )
        eigen_minus = run(
            Request(ask="prove pauli(x) * ket(minus) = -1 * ket(minus)", seed=1)
        )
        self.assertEqual(
            eigen_minus.claims[0].atom,
            "identity(pauli(x) * ket(-) = -1 * ket(-))",
        )
        up = run(Request(ask="prove pauli(z) * ket(0) = ket(0)", seed=1))
        self.assertEqual(up.claims[0].atom, "identity(pauli(z) * ket(0) = ket(0))")

    def test_polynomial_variable_i_is_not_stolen(self) -> None:
        derivative = run(Request(ask="what is d(i^2, i)", seed=1))
        self.assertEqual(derivative.claims[0].atom, "poly(2 * i)")
        rational = run(Request(ask="what is det([[1, 2], [3, 4]])", seed=1))
        self.assertEqual(rational.claims[0].atom, "value(-2)")

    def test_hilbert_results_refuse_forgery(self) -> None:
        origin = parse_term("pauli(x)")
        actual = eval_hilbert_matrix(origin)
        with self.assertRaises(KernelError):
            HilbTheorem(pauli("z"), origin)
        self.assertEqual(actual.rows, pauli("x").rows)
