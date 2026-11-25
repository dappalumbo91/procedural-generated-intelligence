from __future__ import annotations

import unittest
from fractions import Fraction

from pgi.corpus.formulas import FORMULAS, audit_formulas, formula, planck_u, rayleigh_jeans_u
from pgi.corpus.measured import BOUNDS, QUANTITIES, Quantity, audit_quantities, parse_concise, parse_decimal, quantity
from pgi.corpus.records import RECORDS, audit_records
from pgi.engine import unfold
from pgi.model import Request


def _pi_enclosure(digits: int = 40) -> tuple[Fraction, Fraction]:
    """Machin: pi = 16 atan(1/5) - 4 atan(1/239), with alternating-series bounds."""

    def atan_inv(n: int) -> tuple[Fraction, Fraction]:
        total = Fraction(0)
        k = 0
        limit = Fraction(1, 10 ** (digits + 5))
        while True:
            term = Fraction(1, (2 * k + 1) * n ** (2 * k + 1))
            if term < limit:
                return total - term, total + term
            total += term if k % 2 == 0 else -term
            k += 1

    low5, high5 = atan_inv(5)
    low239, high239 = atan_inv(239)
    return 16 * low5 - 4 * high239, 16 * high5 - 4 * low239


def _rel2(item: Quantity) -> Fraction:
    sigma = item.uncertainty
    if sigma is None:
        return Fraction(0)
    return (sigma / item.value) ** 2


def _agrees(target: Quantity, value: Fraction, rel2: Fraction) -> bool:
    """|target - value| is inside the combined standard uncertainty, compared as squares."""
    sigma2 = (target.uncertainty or 0) ** 2 + rel2 * value**2
    return (target.value - value) ** 2 <= sigma2


class QuantityLoadTests(unittest.TestCase):
    def test_every_quantity_loads_and_cites(self) -> None:
        audit_quantities()
        audit_records()
        board = {record.id: record for record in RECORDS}
        for item in QUANTITIES:
            self.assertTrue(item.url.startswith("https://"), item.id)
            self.assertTrue(item.retrieved_from.startswith("https://"), item.id)
            self.assertEqual(item.retrieved, "2026-11-25")
            self.assertTrue(item.edition)
            self.assertEqual(item.value, parse_decimal(item.value_text))
            if item.record:
                record = board[item.id]
                self.assertIn(item.value_text, " ".join(record.statement))
                self.assertIn(item.edition, record.source)
                self.assertEqual(record.url, item.url)
                self.assertNotIn("value(", " ".join(record.statement))
                if item.exact:
                    self.assertEqual(record.kind, "definitional_anchor")
                    self.assertEqual(record.forbids, (f"derived({item.id})",))
                else:
                    self.assertIn(item.uncertainty_text, " ".join(record.statement))

    def test_parse_is_exact_and_refuses_truncation(self) -> None:
        self.assertEqual(parse_decimal("6.626 070 15 e-34"), Fraction(662607015, 10**42))
        self.assertEqual(parse_decimal("10 973 731.568 157"), Fraction(10973731568157, 10**6))
        with self.assertRaises(ValueError):
            parse_decimal("1.054 571 817... e-34")
        with self.assertRaises(ValueError):
            parse_decimal("0.1180(9)")


class Codata2022Tests(unittest.TestCase):
    def test_si_defining_constants_are_exact(self) -> None:
        expected = {
            "codata2022.delta_nu_cs": Fraction(9192631770),
            "codata2022.c": Fraction(299792458),
            "codata2022.h": Fraction(662607015, 10**42),
            "codata2022.e": Fraction(1602176634, 10**28),
            "codata2022.k": Fraction(1380649, 10**29),
            "codata2022.n_a": Fraction(602214076 * 10**15),
            "codata2022.k_cd": Fraction(683),
        }
        for id, value in expected.items():
            item = quantity(id)
            self.assertTrue(item.exact, id)
            self.assertIsNone(item.uncertainty, id)
            self.assertEqual(item.value, value, id)
        board = {record.id: record for record in RECORDS}
        self.assertNotIn("codata2022.c", board)
        self.assertIn("299792458", " ".join(board["anchor.c_si"].statement))
        self.assertEqual(Fraction(299792458), quantity("codata2022.c").value)

    def test_measured_core_set_is_present(self) -> None:
        for id in (
            "codata2022.g",
            "codata2022.alpha",
            "codata2022.m_e",
            "codata2022.m_p",
            "codata2022.m_n",
            "codata2022.r_inf",
            "codata2022.a_0",
            "codata2022.mu_0",
            "codata2022.epsilon_0",
        ):
            item = quantity(id)
            self.assertFalse(item.exact, id)
            self.assertEqual(item.uncertainty_kind, "standard uncertainty")
            self.assertGreater(item.uncertainty, 0)

    def test_alpha_from_e_h_c_epsilon0(self) -> None:
        e, h, c = (quantity(n).value for n in ("codata2022.e", "codata2022.h", "codata2022.c"))
        eps0 = quantity("codata2022.epsilon_0")
        alpha = quantity("codata2022.alpha")
        derived = e**2 / (2 * eps0.value * h * c)
        self.assertTrue(_agrees(alpha, derived, _rel2(eps0)))
        self.assertNotEqual(derived, alpha.value)

    def test_mu0_epsilon0_c2_is_one(self) -> None:
        e, h, c = (quantity(n).value for n in ("codata2022.e", "codata2022.h", "codata2022.c"))
        alpha = quantity("codata2022.alpha")
        mu0 = quantity("codata2022.mu_0")
        eps0 = quantity("codata2022.epsilon_0")
        self.assertTrue(_agrees(mu0, 2 * alpha.value * h / (e**2 * c), _rel2(alpha)))
        product = mu0.value * eps0.value * c**2
        self.assertLessEqual((product - 1) ** 2, _rel2(mu0) + _rel2(eps0))

    def test_inverse_alpha(self) -> None:
        alpha = quantity("codata2022.alpha")
        inverse = quantity("codata2022.alpha_inverse")
        self.assertTrue(_agrees(inverse, 1 / alpha.value, _rel2(alpha)))

    def test_rydberg_and_bohr_radius(self) -> None:
        h, c = quantity("codata2022.h").value, quantity("codata2022.c").value
        alpha, m_e = quantity("codata2022.alpha"), quantity("codata2022.m_e")
        rydberg = quantity("codata2022.r_inf")
        derived = alpha.value**2 * m_e.value * c / (2 * h)
        self.assertTrue(_agrees(rydberg, derived, 4 * _rel2(alpha) + _rel2(m_e)))
        low, high = _pi_enclosure()
        a_0 = quantity("codata2022.a_0")
        rel2 = _rel2(alpha) + _rel2(rydberg)
        for pi in (low, high):
            self.assertTrue(_agrees(a_0, alpha.value / (4 * pi * rydberg.value), rel2))

    def test_mass_ratio_and_energy_equivalents(self) -> None:
        c, e = quantity("codata2022.c").value, quantity("codata2022.e").value
        m_e, m_p = quantity("codata2022.m_e"), quantity("codata2022.m_p")
        ratio = quantity("codata2022.m_p_over_m_e")
        self.assertTrue(_agrees(ratio, m_p.value / m_e.value, _rel2(m_p) + _rel2(m_e)))
        for mass, energy in (
            ("codata2022.m_e", "codata2022.m_e_c2_mev"),
            ("codata2022.m_p", "codata2022.m_p_c2_mev"),
            ("codata2022.m_n", "codata2022.m_n_c2_mev"),
        ):
            item = quantity(mass)
            self.assertTrue(_agrees(quantity(energy), item.value * c**2 / (e * 10**6), _rel2(item)), energy)

    def test_a_planted_error_is_caught(self) -> None:
        alpha = quantity("codata2022.alpha")
        e, h, c = (quantity(n).value for n in ("codata2022.e", "codata2022.h", "codata2022.c"))
        eps0 = quantity("codata2022.epsilon_0")
        wrong = e**2 / (2 * (eps0.value + 10 * eps0.uncertainty) * h * c)
        self.assertFalse(_agrees(alpha, wrong, _rel2(eps0)))


class Pdg2026Tests(unittest.TestCase):
    def test_concise_forms_match_the_stored_numbers(self) -> None:
        self.assertEqual(parse_concise("0.1180(9)"), (Fraction(1180, 10**4), Fraction(9, 10**4)))
        self.assertEqual(
            parse_concise("1.166 378 5(6) e-5"), (Fraction(11663785, 10**12), Fraction(6, 10**12))
        )
        with self.assertRaises(ValueError):
            parse_concise("0.1180+-0.0009")
        for item in QUANTITIES:
            if item.printed:
                self.assertEqual(parse_concise(item.printed), (item.value, item.uncertainty), item.id)

    def test_requested_set_is_present_with_its_kind(self) -> None:
        for id in ("pdg2026.m_w", "pdg2026.m_z", "pdg2026.m_h", "pdg2026.m_t", "pdg2026.m_e", "pdg2026.m_mu", "pdg2026.m_tau", "pdg2026.alpha_s_mz", "pdg2026.g_f", "pdg2026.sin2_theta_w", "pdg2026.ckm.lambda", "pdg2026.ckm.v_ud"):
            self.assertEqual(quantity(id).uncertainty_kind, "standard uncertainty", id)
        for id in ("pdg2026.m_u", "pdg2026.m_d", "pdg2026.m_s", "pdg2026.m_c", "pdg2026.m_b"):
            item = quantity(id)
            self.assertEqual(item.uncertainty_kind, "uncertainty at CL = 90%", id)
            self.assertIn("CL = 90%", " ".join(item.notes))
        a = quantity("pdg2026.ckm.a")
        self.assertEqual((a.uncertainty, a.lower_uncertainty), (Fraction(17, 1000), Fraction(15, 1000)))
        self.assertIn("MSbar", " ".join(quantity("pdg2026.m_u").notes))
        self.assertIn("2 GeV", " ".join(quantity("pdg2026.m_u").notes))

    def test_w_over_z_ratio_agrees_with_the_masses(self) -> None:
        w, z = quantity("pdg2026.m_w"), quantity("pdg2026.m_z")
        ratio = quantity("pdg2026.m_w_over_m_z")
        self.assertTrue(_agrees(ratio, w.value / z.value, _rel2(w) + _rel2(z)))

    def test_electron_mass_agrees_across_codata_and_pdg(self) -> None:
        pdg = quantity("pdg2026.m_e")
        codata = quantity("codata2022.m_e_c2_mev")
        self.assertEqual(pdg.value, codata.value)
        self.assertEqual(pdg.uncertainty, codata.uncertainty)

    def test_fermi_constant_agrees_across_codata_and_pdg(self) -> None:
        pdg = quantity("pdg2026.g_f")
        codata = quantity("codata2022.g_f")
        self.assertNotEqual(pdg.value, codata.value)
        self.assertTrue(_agrees(pdg, codata.value, _rel2(codata)))

    def test_ckm_fit_rows_and_columns_are_unitary_within_uncertainty(self) -> None:
        names = (("v_ud", "v_us", "v_ub"), ("v_cd", "v_cs", "v_cb"), ("v_td", "v_ts", "v_tb"))
        grid = [[quantity(f"pdg2026.ckm.{n}") for n in row] for row in names]

        def check(line: list[Quantity]) -> None:
            total = sum(item.value**2 for item in line)
            sigma2 = sum((2 * item.value * max(item.uncertainty, item.lower_uncertainty)) ** 2 for item in line)
            self.assertLessEqual((total - 1) ** 2, sigma2, [item.id for item in line])

        for row in grid:
            check(row)
        for column in zip(*grid):
            check(list(column))
        lam, v_us = quantity("pdg2026.ckm.lambda"), quantity("pdg2026.ckm.v_us")
        self.assertEqual(lam.value, v_us.value)


class MercuryTests(unittest.TestCase):
    def test_residual_is_observed_minus_computed(self) -> None:
        observed = quantity("mercury.clemence1947.observed")
        computed = quantity("mercury.clemence1947.computed")
        residual = quantity("mercury.clemence1947.residual")
        self.assertEqual(observed.value - computed.value, residual.value)
        self.assertEqual(residual.value, Fraction(4256, 100))
        for item in (observed, computed, residual):
            self.assertEqual(item.uncertainty_kind, "probable error")
            self.assertEqual(item.unit, "arcsec per Julian century")
        # Clemence combines independent probable errors in quadrature: 0.41 and 0.85 give 0.94 to his printed places.
        combined2 = observed.uncertainty**2 + computed.uncertainty**2
        self.assertLessEqual((residual.uncertainty - Fraction(5, 1000)) ** 2, combined2)
        self.assertLessEqual(combined2, (residual.uncertainty + Fraction(5, 1000)) ** 2)

    def test_residual_is_far_outside_its_probable_error(self) -> None:
        residual = quantity("mercury.clemence1947.residual")
        self.assertGreater(residual.value, 40 * residual.uncertainty)
        self.assertIn("law(newtonian_perturbations_explain_mercury_perihelion)", residual.forbids)
        text = " ".join(residual.notes)
        self.assertIn("not stored", text)
        self.assertNotIn("43.03", text)


class Gw150914Tests(unittest.TestCase):
    def test_intervals_are_ninety_percent_and_well_formed(self) -> None:
        for item in QUANTITIES:
            if item.id.startswith("gw150914."):
                self.assertEqual(item.uncertainty_kind, "90% credible interval", item.id)
                self.assertGreater(item.uncertainty, 0)
                self.assertGreater(item.lower_uncertainty, 0)

    def test_chirp_mass_and_energy_budget_from_the_medians(self) -> None:
        m1 = quantity("gw150914.m1_source")
        m2 = quantity("gw150914.m2_source")
        chirp = quantity("gw150914.chirp_mass_source")
        a, b = float(m1.value), float(m2.value)
        derived = (a * b) ** 0.6 / (a + b) ** 0.2
        self.assertLessEqual(float(chirp.value - chirp.lower_uncertainty), derived)
        self.assertLessEqual(derived, float(chirp.value + chirp.uncertainty))
        final = quantity("gw150914.final_mass_source")
        radiated = quantity("gw150914.radiated_energy")
        self.assertEqual(m1.value + m2.value - final.value, radiated.value)
        self.assertLess(final.value, m1.value + m2.value)


class Gw170817BoundTests(unittest.TestCase):
    def test_speed_of_gravity_bound(self) -> None:
        (bound,) = [item for item in BOUNDS if item.id == "bound.gw170817_speed_of_gravity"]
        self.assertEqual(bound.lower, Fraction(-3, 10**15))
        self.assertEqual(bound.upper, Fraction(7, 10**16))
        self.assertLess(bound.lower, 0)
        self.assertLess(0, bound.upper)
        board = {record.id: record for record in RECORDS}
        record = board[bound.id]
        self.assertEqual(record.kind, "experimental_bound")
        self.assertIn("26 Mpc", " ".join(record.statement))
        self.assertIn("10 s", " ".join(record.statement))


class SpectralFormulaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.h = quantity("codata2022.h").value
        self.k = quantity("codata2022.k").value
        self.c = quantity("codata2022.c").value

    def test_formulas_load_and_cite(self) -> None:
        audit_formulas()
        board = {record.id: record for record in RECORDS}
        for item in FORMULAS:
            record = board[item.id]
            self.assertEqual(record.kind, "stored_formula")
            self.assertEqual(record.standing, item.standing)
            self.assertIn(item.text, " ".join(record.statement))
            self.assertIn("doi:10.1002/andp.19013090310", record.source)
        self.assertEqual(formula("formula.planck_spectrum").standing, "stored")
        failed = formula("formula.rayleigh_jeans")
        self.assertEqual(failed.standing, "failed")
        self.assertIn("law(rayleigh_jeans_at_high_frequency)", failed.forbids)

    def test_the_two_formulas_meet_only_at_low_frequency(self) -> None:
        theta = 5000.0
        kt = float(self.k) * theta
        low = 1e-4 * kt / float(self.h)
        ratio = rayleigh_jeans_u(low, theta, self.k, self.c) / planck_u(low, theta, self.h, self.k, self.c)
        self.assertLess(abs(ratio - 1), 1e-3)
        high = 20 * kt / float(self.h)
        ratio = rayleigh_jeans_u(high, theta, self.k, self.c) / planck_u(high, theta, self.h, self.k, self.c)
        self.assertGreater(ratio, 1e6)

    def test_rayleigh_jeans_total_diverges_and_planck_falls(self) -> None:
        theta = 5000.0
        kt = float(self.k) * theta
        # The stored Rayleigh-Jeans density is a constant times nu^2, so its integral to nu_max is that constant times nu_max^3 / 3.
        # Doubling the cutoff multiplies the total by exactly 8, with no limit.
        coefficient = rayleigh_jeans_u(1.0, theta, self.k, self.c)
        totals = [coefficient * (2.0**n) ** 3 / 3 for n in range(40, 50)]
        for before, after in zip(totals, totals[1:]):
            self.assertAlmostEqual(after / before, 8.0)
        tail = [planck_u(x * kt / float(self.h), theta, self.h, self.k, self.c) for x in (10, 20, 40, 80)]
        self.assertEqual(tail, sorted(tail, reverse=True))
        self.assertLess(tail[-1], 1e-25 * tail[0])


class PhysicsBoardTests(unittest.TestCase):
    def test_a_constant_is_linked_not_settled(self) -> None:
        session = unfold(Request(ask="what is the fine-structure constant", seed=1))
        atoms = [claim.atom for claim in session.claims]
        self.assertIn("record(codata2022.alpha)", atoms)
        text = session.text(lod=2)
        self.assertIn("7.297 352 5643 e-3", text)
        self.assertIn("0.000 000 0011 e-3", text)
        self.assertIn("https://physics.nist.gov/cgi-bin/cuu/Value?alph", text)
        self.assertIn("Retrieved 2026-11-25", text)
        self.assertNotIn("value(", text)
        self.assertIn("Linked records are on the board. None of them is a settled answer.", session.open_gaps)

    def test_a_claimed_derivation_of_a_defining_constant_is_contested(self) -> None:
        contested = unfold(
            Request(ask="what is the planck constant", facts=("derived(codata2022.h)",), seed=1)
        )
        self.assertIn("derived(codata2022.h)", contested.retracted)
        self.assertIn("record(codata2022.h)", [claim.atom for claim in contested.claims])

    def test_a_quark_mass_carries_its_scheme_and_confidence(self) -> None:
        session = unfold(Request(ask="what is the strange quark mass", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(pdg2026.m_s)", text)
        self.assertIn("92.9", text)
        self.assertIn("CL = 90%", text)
        self.assertIn("mu = 2 GeV", text)
        self.assertNotIn("value(", text)

    def test_ckm_asks_link_the_fit(self) -> None:
        session = unfold(Request(ask="what is the ckm matrix", seed=1))
        atoms = [claim.atom for claim in session.claims]
        self.assertIn("record(pdg2026.ckm.v_ub)", atoms)
        self.assertIn("+0.000088 -0.000083", session.text(lod=2))

    def test_a_newtonian_account_of_mercury_is_contested(self) -> None:
        session = unfold(
            Request(
                ask="what is the mercury perihelion residual",
                facts=("law(newtonian_perturbations_explain_mercury_perihelion)",),
                seed=1,
            )
        )
        self.assertIn("law(newtonian_perturbations_explain_mercury_perihelion)", session.retracted)
        self.assertIn("record(mercury.clemence1947.residual)", [claim.atom for claim in session.claims])
        self.assertIn("42.56", session.text(lod=2))

    def test_speed_of_gravity_links_the_bound(self) -> None:
        session = unfold(Request(ask="what is the speed of gravity", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(bound.gw170817_speed_of_gravity)", text)
        self.assertIn("-3 e-15", text)
        self.assertIn("+7 e-16", text)
        self.assertNotIn("value(", text)

    def test_gw150914_links_its_masses(self) -> None:
        session = unfold(Request(ask="what were the gw150914 masses", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(gw150914.m1_source)", text)
        self.assertIn("+4.7 -3.1", text)
        self.assertIn("90% credible interval", text)

    def test_the_failed_formula_stays_failed(self) -> None:
        session = unfold(Request(ask="what is the rayleigh-jeans law", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(formula.rayleigh_jeans)", text)
        self.assertIn("record(known.rayleigh_jeans)", text)
        self.assertIn("standing failed", text)
        contested = unfold(
            Request(
                ask="what is the rayleigh-jeans law",
                facts=("law(rayleigh_jeans_at_high_frequency)",),
                seed=1,
            )
        )
        self.assertIn("law(rayleigh_jeans_at_high_frequency)", contested.retracted)
        planck = unfold(Request(ask="what is planck's law", seed=1)).text(lod=2)
        self.assertIn("record(formula.planck_spectrum)", planck)
        self.assertIn("standing stored", planck)
        self.assertNotIn("value(", planck)

    def test_gravitation_is_measured(self) -> None:
        session = unfold(Request(ask="what is the gravitational constant", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(codata2022.g)", text)
        self.assertIn("6.674 30 e-11", text)
        self.assertIn("measured anchor", text)


if __name__ == "__main__":
    unittest.main()
