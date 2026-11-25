from __future__ import annotations

import unittest

from pgi.engine import unfold
from pgi.math.kernel import KernelError
from pgi.math.matrix import DetTheorem, Matrix, RankTheorem, Ratio, matrix_inv, matrix_mul, matrix_of
from pgi.math.syntax import parse_term, pretty
from pgi.model import Request


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


class RationalMatrixTests(unittest.TestCase):
    def test_determinant_rank_and_inverse(self) -> None:
        det = run(Request(ask="what is det([[1, 2], [3, 4]])", seed=1))
        self.assertEqual(det.claims[0].atom, "value(-2)")
        self.assertIn("Bareiss", det.text(lod=2))
        self.assertIn("cofactor expansion agrees", det.text(lod=2))
        self.assertEqual(det.open_gaps, ())

        identity = run(Request(ask="what is det([[1, 0, 0], [0, 1, 0], [0, 0, 1]])", seed=1))
        self.assertEqual(identity.claims[0].atom, "value(1)")

        cubic = run(Request(ask="what is det([[1, 2, 3], [4, 5, 6], [7, 8, 10]])", seed=1))
        self.assertEqual(cubic.claims[0].atom, "value(-3)")

        fraction = run(Request(ask="what is det([[1/2, 0], [0, 1/3]])", seed=1))
        self.assertEqual(fraction.claims[0].atom, "ratio(1,6)")

        full = run(Request(ask="what is rank([[1, 2], [3, 4]])", seed=1))
        self.assertEqual(full.claims[0].atom, "value(2)")
        dependent = run(Request(ask="what is rank([[1, 2], [2, 4]])", seed=1))
        self.assertEqual(dependent.claims[0].atom, "value(1)")
        deficient = run(Request(ask="what is rank([[1, 0, 0], [0, 1, 0], [1, 1, 0]])", seed=1))
        self.assertEqual(deficient.claims[0].atom, "value(2)")
        zero = run(Request(ask="what is rank([[0, 0], [0, 0]])", seed=1))
        self.assertEqual(zero.claims[0].atom, "value(0)")

        inverse = run(Request(ask="what is inv([[1, 2], [3, 4]])", seed=1))
        self.assertEqual(inverse.claims[0].atom, "matrix([[-2, 1], [3/2, -1/2]])")
        self.assertIn("both products are the identity", inverse.text(lod=2))
        product = run(Request(ask="what is [[1, 2], [3, 4]] * inv([[1, 2], [3, 4]])", seed=1))
        self.assertEqual(product.claims[0].atom, "matrix([[1, 0], [0, 1]])")
        back = run(Request(ask="what is inv([[1, 2], [3, 4]]) * [[1, 2], [3, 4]]", seed=1))
        self.assertEqual(back.claims[0].atom, "matrix([[1, 0], [0, 1]])")

        tridiagonal = run(
            Request(ask="what is inv([[2, -1, 0], [-1, 2, -1], [0, -1, 2]])", seed=1)
        )
        self.assertEqual(
            tridiagonal.claims[0].atom,
            "matrix([[3/4, 1/2, 1/4], [1/2, 1, 1/2], [1/4, 1/2, 3/4]])",
        )

        proved = run(Request(ask="prove det([[1, 2], [3, 4]]) = -2", seed=1))
        self.assertEqual(proved.claims[0].atom, "identity(det([[1, 2], [3, 4]]) = -2)")
        proved_inv = run(
            Request(ask="prove inv([[1, 2], [3, 4]]) = [[-2, 1], [3/2, -1/2]]", seed=1)
        )
        self.assertTrue(proved_inv.claims[0].atom.startswith("identity(inv([[1, 2], [3, 4]]) = "))

        times = run(Request(ask="what is [[1, 2], [3, 4]] * [[0, 1], [1, 0]]", seed=1))
        self.assertEqual(times.claims[0].atom, "matrix([[2, 1], [4, 3]])")
        added = run(Request(ask="what is [[1, 2], [3, 4]] + [[4, 3], [2, 1]]", seed=1))
        self.assertEqual(added.claims[0].atom, "matrix([[5, 5], [5, 5]])")
        scaled = run(Request(ask="what is 2 * [[1, 2], [3, 4]]", seed=1))
        self.assertEqual(scaled.claims[0].atom, "matrix([[2, 4], [6, 8]])")
        flipped = run(Request(ask="what is transpose([[1, 2], [3, 4]])", seed=1))
        self.assertEqual(flipped.claims[0].atom, "matrix([[1, 3], [2, 4]])")

    def test_singular_and_non_square_stay_open(self) -> None:
        singular = run(Request(ask="what is inv([[1, 2], [2, 4]])", seed=1))
        self.assertEqual(singular.claims[0].atom, "open(a singular matrix has no inverse)")
        wide = run(Request(ask="what is det([1, 2])", seed=1))
        self.assertEqual(wide.claims[0].atom, "open(a non-square matrix has no determinant here)")
        mismatch = run(Request(ask="what is [[1, 2], [3, 4]] * [[1], [2], [3]]", seed=1))
        self.assertEqual(mismatch.claims[0].atom, "open(these matrices do not multiply)")

    def test_inverse_and_determinant_refuse_forgery(self) -> None:
        source = Matrix(((Ratio(1, 1), Ratio(2, 1)), (Ratio(3, 1), Ratio(4, 1))))
        with self.assertRaises(KernelError):
            DetTheorem(Ratio(0, 1), source)
        with self.assertRaises(KernelError):
            RankTheorem(2, source, (0,), (0,))
        inverse = matrix_inv(source)
        product = matrix_mul(matrix_of(source), matrix_of(inverse.value)).value
        self.assertEqual(product.rows, ((Ratio(1, 1), Ratio(0, 1)), (Ratio(0, 1), Ratio(1, 1))))

    def test_matrix_terms_pretty_print(self) -> None:
        term = parse_term("det([[1, 2], [3, 4]])")
        self.assertIsNotNone(term)
        self.assertEqual(pretty(term), "det([[1, 2], [3, 4]])")
        ragged = run(Request(ask="what is [[1, 2], [3]]", seed=1))
        self.assertEqual(ragged.claims[0].atom, "open(matrix rows must have the same length)")


if __name__ == "__main__":
    unittest.main()
