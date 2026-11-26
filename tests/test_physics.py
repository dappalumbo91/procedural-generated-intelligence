from __future__ import annotations

import unittest
from fractions import Fraction

from pgi.corpus.formulas import FORMULAS, audit_formulas, formula, planck_u, rayleigh_jeans_u
from pgi.corpus.measured import BOUNDS, CIAAW_H_KR, QUANTITIES, Quantity, audit_quantities, parse_concise, parse_decimal, parse_truncated, quantity
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
            if item.truncated:
                with self.assertRaises(ValueError):
                    item.value
                low, high = item.truncation_bounds
                self.assertLess(low, high)
            else:
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


class MercuryModernTests(unittest.TestCase):
    def test_modern_records_load_with_their_kinds(self) -> None:
        self.assertEqual(quantity("mercury.park2017.total_precession").value, Fraction(5753100, 10**4))
        self.assertEqual(quantity("mercury.park2017.beta_minus_1").value, Fraction(-27, 10**6))
        self.assertIn("-2.6", " ".join(quantity("mercury.park2017.beta_minus_1").notes))
        self.assertEqual(quantity("mercury.epm2011.beta_minus_1").uncertainty_kind, "3 sigma")
        self.assertEqual(quantity("mercury.epm2011.gamma_minus_1").value, Fraction(4, 10**5))
        self.assertEqual(
            quantity("mercury.epm2011.extra_perihelion_precession").uncertainty_kind, "standard uncertainty"
        )
        # Clemence stays on the board beside the modern numbers.
        self.assertEqual(quantity("mercury.clemence1947.residual").value, Fraction(4256, 100))

    def test_the_modern_residual_is_inside_its_uncertainty(self) -> None:
        extra = quantity("mercury.epm2011.extra_perihelion_precession")
        self.assertLess(abs(extra.value), extra.uncertainty)

    def test_ppn_determinations_overlap(self) -> None:
        def overlap(a: Quantity, b: Quantity) -> bool:
            return a.value - a.lower_uncertainty <= b.value + b.uncertainty and b.value - b.lower_uncertainty <= a.value + a.uncertainty

        self.assertTrue(overlap(quantity("mercury.park2017.beta_minus_1"), quantity("mercury.epm2011.beta_minus_1")))
        self.assertTrue(overlap(quantity("cassini.bertotti2003.gamma_minus_1"), quantity("mercury.epm2011.gamma_minus_1")))
        for id in ("mercury.park2017.beta_minus_1", "mercury.epm2011.beta_minus_1", "cassini.bertotti2003.gamma_minus_1", "mercury.epm2011.gamma_minus_1"):
            item = quantity(id)
            self.assertLessEqual(item.value - item.lower_uncertainty, 0, id)
            self.assertLessEqual(0, item.value + item.uncertainty, id)


class CosmologyTests(unittest.TestCase):
    def test_planck_densities_close_and_h2_scales(self) -> None:
        omega_m = quantity("planck2018.omega_m")
        omega_l = quantity("planck2018.omega_lambda")
        self.assertEqual(omega_m.value + omega_l.value, 1)
        h0 = quantity("planck2018.h0")
        omega_m_h2 = quantity("planck2018.omega_m_h2")
        h = h0.value / 100
        self.assertTrue(_agrees(omega_m_h2, omega_m.value * h**2, _rel2(omega_m) + 4 * _rel2(h0)))
        sigma_8 = quantity("planck2018.sigma_8")
        s_8 = quantity("planck2018.s_8")
        derived = float(sigma_8.value) * (float(omega_m.value) / 0.3) ** 0.5
        self.assertLess(abs(derived - float(s_8.value)), float(s_8.uncertainty))
        for id in ("planck2018.h0", "planck2018.omega_b_h2", "planck2018.omega_c_h2", "planck2018.n_s", "planck2018.tau"):
            self.assertEqual(quantity(id).uncertainty_kind, "68% interval")

    def test_ladder_and_cmb_h0_disagree_and_both_stay(self) -> None:
        planck, sh0es = quantity("planck2018.h0"), quantity("sh0es2022.h0")
        gap2 = (sh0es.value - planck.value) ** 2
        self.assertGreater(gap2, 16 * (planck.uncertainty**2 + sh0es.uncertainty**2))
        session = unfold(Request(ask="what is the hubble constant", seed=1))
        atoms = [claim.atom for claim in session.claims]
        self.assertIn("record(planck2018.h0)", atoms)
        self.assertIn("record(sh0es2022.h0)", atoms)
        self.assertEqual(session.retracted, ())

    def test_desi_w0_sits_above_minus_one_in_every_combination(self) -> None:
        combos = ("cmb", "cmb_pantheonplus", "cmb_union3", "cmb_desy5")
        for combo in combos:
            w0 = quantity(f"desi_dr2.{combo}.w0")
            wa = quantity(f"desi_dr2.{combo}.wa")
            self.assertGreater(w0.value, -1, combo)
            self.assertLess(wa.value, 0, combo)
            self.assertEqual(w0.uncertainty_kind, "68% interval")
        self.assertEqual(quantity("desi_dr2.cmb_desy5.wa").lower_uncertainty, Fraction(20, 100))

    def test_cmb_temperature(self) -> None:
        t0 = quantity("fixsen2009.t_cmb")
        self.assertEqual(t0.value, Fraction(272548, 10**5))
        self.assertEqual(t0.unit, "K")


def _split_sigma2(item: Quantity) -> Fraction:
    """Statistical and systematic parts in quadrature, taking the larger systematic side."""
    systematic = max(item.systematic or 0, item.systematic_lower or 0)
    return item.uncertainty**2 + systematic**2


class ParticlePrecisionTests(unittest.TestCase):
    def test_split_uncertainties_load_as_printed(self) -> None:
        ucn = quantity("ucntau2021.neutron_lifetime")
        self.assertEqual(ucn.uncertainty_kind, "statistical and systematic, printed separately")
        self.assertEqual((ucn.uncertainty, ucn.systematic, ucn.systematic_lower), (Fraction(28, 100), Fraction(22, 100), Fraction(16, 100)))
        beam = quantity("nist_beam2013.neutron_lifetime")
        self.assertEqual(beam.systematic, beam.systematic_lower)
        board = {record.id: record for record in RECORDS}
        self.assertIn("+0.20 -0.17 s, printed separately", " ".join(board["ucntau2025.neutron_lifetime"].statement))
        planted = Quantity(**{**ucn.__dict__, "id": "planted.split", "systematic_text": ""})
        with self.assertRaises(ValueError):
            audit_quantities((planted,))

    def test_neutron_lifetime_bottle_and_beam(self) -> None:
        pdg_tau = quantity("pdg2026.neutron_lifetime")
        ucn = quantity("ucntau2025.neutron_lifetime")
        beam = quantity("nist_beam2013.neutron_lifetime")
        self.assertLessEqual((pdg_tau.value - ucn.value) ** 2, pdg_tau.uncertainty**2 + _split_sigma2(ucn))
        gap2 = (beam.value - ucn.value) ** 2
        self.assertGreater(gap2, 16 * (_split_sigma2(beam) + _split_sigma2(ucn)))
        session = unfold(Request(ask="what is the neutron lifetime", seed=1))
        atoms = [claim.atom for claim in session.claims]
        for id in ("pdg2026.neutron_lifetime", "ucntau2021.neutron_lifetime", "ucntau2025.neutron_lifetime", "nist_beam2013.neutron_lifetime"):
            self.assertIn(f"record({id})", atoms)
        self.assertEqual(session.retracted, ())

    def test_axial_coupling_ratio(self) -> None:
        lam = quantity("pdg2026.lambda_ga_gv")
        self.assertEqual(lam.value, Fraction(-12753, 10000))
        self.assertIn("scale factor of 2.7", " ".join(lam.notes))

    def test_muon_anomaly_sources_agree(self) -> None:
        fnal = quantity("fnal2025.a_mu")
        world = quantity("fnal2025.a_mu_world_average")
        self.assertEqual(parse_concise(world.printed), (Fraction(1165920715, 10**12), Fraction(145, 10**12)))
        self.assertTrue(_agrees(world, fnal.value, _rel2(fnal)))
        self.assertTrue(_agrees(world, quantity("pdg2026.a_mu").value, _rel2(quantity("pdg2026.a_mu"))))
        self.assertTrue(_agrees(world, quantity("codata2022.a_mu").value, _rel2(quantity("codata2022.a_mu"))))
        session = unfold(Request(ask="what is the muon g-2", seed=1))
        atoms = [claim.atom for claim in session.claims]
        self.assertIn("record(fnal2025.a_mu)", atoms)
        self.assertIn("record(fnal2025.a_mu_world_average)", atoms)

    def test_electron_moment_matches_the_anomaly(self) -> None:
        fan = quantity("fan2023.electron_g_over_2")
        anomaly = fan.value - 1
        sigma2 = fan.uncertainty**2
        for id in ("codata2022.a_e", "pdg2026.a_e"):
            other = quantity(id)
            self.assertLessEqual((other.value - anomaly) ** 2, other.uncertainty**2 + sigma2, id)

    def test_proton_radius_in_two_units(self) -> None:
        codata = quantity("codata2022.r_p")
        pdg_r = quantity("pdg2026.proton_radius")
        in_metres = pdg_r.value * Fraction(1, 10**15)
        self.assertLessEqual(abs(codata.value - in_metres), pdg_r.uncertainty * Fraction(1, 10**15))
        session = unfold(Request(ask="what is the proton charge radius", seed=1))
        atoms = [claim.atom for claim in session.claims]
        self.assertIn("record(codata2022.r_p)", atoms)
        self.assertIn("record(pdg2026.proton_radius)", atoms)


class AsdIonizationTests(unittest.TestCase):
    SYMBOLS = ("h", "he", "li", "be", "b", "c", "n", "o", "f", "ne")

    def test_rows_load_with_their_uncertainties(self) -> None:
        energies = {}
        for symbol in self.SYMBOLS:
            item = quantity(f"asd512.ie.{symbol}")
            self.assertEqual(item.unit, "eV")
            self.assertEqual(item.uncertainty_kind, "uncertainty as printed, level not stated")
            self.assertGreater(item.uncertainty, 0)
            self.assertIn("version 5.12", item.edition)
            energies[symbol] = item.value
        self.assertEqual(energies["he"], Fraction(24587389011, 10**9))
        self.assertEqual(quantity("asd512.ie.ne").uncertainty, Fraction(7, 10**6))
        self.assertEqual(max(energies, key=energies.get), "he")
        self.assertEqual(min(energies, key=energies.get), "li")
        self.assertIn("parentheses", " ".join(quantity("asd512.ie.h").notes))
        self.assertNotIn("parentheses", " ".join(quantity("asd512.ie.he").notes))

    def test_hydrogen_sits_just_below_the_rydberg_energy(self) -> None:
        hydrogen = quantity("asd512.ie.h").value
        rydberg = quantity("codata2022.ryd_hc_ev").value
        mass_ratio = quantity("codata2022.m_p_over_m_e").value
        alpha = quantity("codata2022.alpha").value
        ratio = hydrogen / rydberg
        self.assertLess(ratio, 1)
        reduced = mass_ratio / (1 + mass_ratio)
        # A loose window only: the gap from the reduced-mass ratio is far below alpha^2.
        self.assertLess(abs(ratio - reduced), alpha**2)

    def test_third_and_fourth_rows_load_as_printed(self) -> None:
        period3 = ("na", "mg", "al", "si", "p", "s", "cl", "ar")
        period4 = ("k", "ca", "sc", "ti", "v", "cr", "mn", "fe", "co", "ni", "cu", "zn", "ga", "ge", "as", "se", "br", "kr")
        for period, alkali, noble in ((period3, "na", "ar"), (period4, "k", "kr")):
            energies = {symbol: quantity(f"asd512.ie.{symbol}").value for symbol in period}
            self.assertEqual(min(energies, key=energies.get), alkali)
            self.assertEqual(max(energies, key=energies.get), noble)
        for symbol in period3 + period4:
            item = quantity(f"asd512.ie.{symbol}")
            self.assertGreater(item.uncertainty, 0, symbol)
            self.assertIn("spectra=Na-Kr", item.url)
            self.assertNotIn("parentheses", " ".join(item.notes))
        self.assertEqual(quantity("asd512.ie.ca").uncertainty, Fraction(5, 10**10))
        self.assertEqual(quantity("asd512.ie.fe").value_text, "7.9024681")
        self.assertEqual(len([item for item in QUANTITIES if item.id.startswith("asd512.ie.")]), 36)

    def test_an_ask_links_the_row(self) -> None:
        session = unfold(Request(ask="what is the ionization energy of neon", seed=1))
        text = session.text(lod=2)
        self.assertIn("record(asd512.ie.ne)", text)
        self.assertIn("21.564541", text)
        self.assertIn("0.000007", text)
        self.assertNotIn("value(", text)


def _bound(id: str):
    for item in BOUNDS:
        if item.id == id:
            return item
    raise KeyError(id)


def _contains(item: Quantity, x: Fraction) -> bool:
    return item.value - item.lower_uncertainty <= x <= item.value + item.uncertainty


class InpopTests(unittest.TestCase):
    PPN = (
        "inpop20a.wrss.beta_minus_1", "inpop20a.wrss.gamma_minus_1", "inpop20a.ls.beta_minus_1", "inpop20a.ls.gamma_minus_1",
        "ppn.fienga_minazzoli2024.beta_minus_1", "ppn.fienga_minazzoli2024.gamma_minus_1",
    )

    def test_kinds_are_the_stated_ones(self) -> None:
        self.assertEqual(quantity("inpop20a.wrss.beta_minus_1").uncertainty_kind, "99.7% interval")
        self.assertEqual(quantity("inpop20a.ls.gamma_minus_1").uncertainty_kind, "uncertainty as printed, level not stated")
        self.assertEqual(quantity("mercury.inpop15a.extra_perihelion_c1").uncertainty_kind, "acceptance interval")
        self.assertEqual(quantity("inpop19a.solar_j2").uncertainty_kind, "standard uncertainty")
        self.assertIn("plus sign", " ".join(quantity("inpop20a.ls.beta_minus_1").notes))

    def test_every_printed_interval_contains_zero(self) -> None:
        for id in self.PPN + ("mercury.inpop15a.extra_perihelion_c1", "mercury.inpop15a.extra_perihelion_c2"):
            self.assertTrue(_contains(quantity(id), Fraction(0)), id)

    def test_nesting_as_printed(self) -> None:
        tight = quantity("mercury.inpop15a.extra_perihelion_c2")
        loose = quantity("mercury.inpop15a.extra_perihelion_c1")
        self.assertLess(tight.uncertainty, loose.uncertainty)
        for name in ("beta_minus_1", "gamma_minus_1"):
            overlap = quantity(f"ppn.fienga_minazzoli2024.{name}")
            wrss = quantity(f"inpop20a.wrss.{name}")
            self.assertTrue(_contains(wrss, overlap.value - overlap.uncertainty))
            self.assertTrue(_contains(wrss, overlap.value + overlap.uncertainty))
        uppers = [_bound(f"bound.binpop21a.one_minus_gamma_{level}").upper for level in ("66_7", "95", "99_7")]
        self.assertEqual(uppers, sorted(uppers))
        self.assertTrue(all(_bound(f"bound.binpop21a.one_minus_gamma_{level}").lower == 0 for level in ("66_7", "95", "99_7")))

    def test_inpop15a_mercury_window_is_far_inside_the_classical_residual_error(self) -> None:
        # mas per century against Clemence's arcsec per century: 3.1 mas is 0.0031 arcsec.
        loose = quantity("mercury.inpop15a.extra_perihelion_c1")
        clemence = quantity("mercury.clemence1947.residual")
        self.assertLess(loose.uncertainty / 1000, clemence.uncertainty)

    def test_ppn_ask_links_inpop_and_cassini(self) -> None:
        session = unfold(Request(ask="what is the ppn gamma", seed=1))
        atoms = [claim.atom for claim in session.claims]
        for id in ("inpop20a.wrss.gamma_minus_1", "cassini.bertotti2003.gamma_minus_1", "bound.binpop21a.one_minus_gamma_99_7"):
            self.assertIn(f"record({id})", atoms)
        self.assertEqual(session.retracted, ())


class Ame2020Tests(unittest.TestCase):
    NUCLIDES = (("h2", 1, 1), ("h3", 1, 2), ("he3", 2, 1), ("he4", 2, 2), ("c12", 6, 6), ("o16", 8, 8),
                ("fe56", 26, 30), ("fe58", 26, 32), ("ni62", 28, 34), ("pb208", 82, 126))

    def test_carbon_12_is_exactly_12_u(self) -> None:
        carbon = quantity("ame2020.c12.atomic_mass")
        self.assertTrue(carbon.exact)
        self.assertEqual(carbon.value, 12 * 10**6)
        self.assertEqual(quantity("ame2020.c12.mass_excess").value, 0)
        board = {record.id: record for record in RECORDS}
        self.assertIn("derived(ame2020.c12.atomic_mass)", board["ame2020.c12.atomic_mass"].forbids)
        for id in ("ame2020.n.atomic_mass", "ame2020.h1.atomic_mass", "ame2020.pb208.binding_per_nucleon"):
            self.assertEqual(quantity(id).uncertainty_kind, "standard uncertainty")

    def test_iron_and_nickel_sit_at_the_binding_peak_as_printed(self) -> None:
        per_nucleon = {nid: quantity(f"ame2020.{nid}.binding_per_nucleon").value for nid, _, _ in self.NUCLIDES}
        ranked = sorted(per_nucleon, key=per_nucleon.get, reverse=True)
        self.assertEqual(ranked[:3], ["ni62", "fe58", "fe56"])
        self.assertLess(per_nucleon["ni62"] - per_nucleon["fe56"], 5)
        self.assertGreater(per_nucleon["fe56"] - per_nucleon["pb208"], 900)

    def test_binding_per_nucleon_follows_from_the_mass_excesses(self) -> None:
        hydrogen = quantity("ame2020.h1.mass_excess")
        neutron = quantity("ame2020.n.mass_excess")
        unit = quantity("ame2020.u_kev")
        for nid, z, n in self.NUCLIDES:
            a = z + n
            excess = quantity(f"ame2020.{nid}.mass_excess")
            binding = quantity(f"ame2020.{nid}.binding_per_nucleon")
            computed = (z * hydrogen.value + n * neutron.value - excess.value) / a
            self.assertLessEqual(abs(computed - binding.value), binding.uncertainty, nid)
            mass = quantity(f"ame2020.{nid}.atomic_mass")
            from_excess = a * 10**6 + excess.value / unit.value * 10**6
            self.assertLessEqual(abs(from_excess - mass.value), mass.uncertainty or 0, nid)

    def test_an_ask_links_the_peak(self) -> None:
        session = unfold(Request(ask="what is the binding energy per nucleon", seed=1))
        atoms = [claim.atom for claim in session.claims]
        for nid in ("fe56", "fe58", "ni62"):
            self.assertIn(f"record(ame2020.{nid}.binding_per_nucleon)", atoms)


class Pdg2026HadronTests(unittest.TestCase):
    def test_nucleon_masses_and_their_difference(self) -> None:
        proton, neutron = quantity("pdg2026.m_p"), quantity("pdg2026.m_n")
        difference = quantity("pdg2026.m_n_minus_m_p")
        gap = neutron.value - proton.value
        self.assertLessEqual((gap - difference.value) ** 2, neutron.uncertainty**2 + proton.uncertainty**2 + difference.uncertainty**2)
        self.assertEqual(proton.value, quantity("codata2022.m_p_c2_mev").value)
        self.assertEqual(proton.uncertainty, quantity("codata2022.m_p_c2_mev").uncertainty)
        codata_gap = quantity("codata2022.m_n_c2_mev").value - quantity("codata2022.m_p_c2_mev").value
        self.assertLessEqual(abs(codata_gap - difference.value), Fraction(1, 10**6))

    def test_isospin_splittings_as_printed(self) -> None:
        self.assertGreater(quantity("pdg2026.m_pi_charged").value, quantity("pdg2026.m_pi0").value)
        self.assertGreater(quantity("pdg2026.m_k0").value, quantity("pdg2026.m_k_charged").value)
        self.assertGreater(quantity("pdg2026.m_n").value, quantity("pdg2026.m_p").value)
        order = ["pdg2026.m_pi0", "pdg2026.m_pi_charged", "pdg2026.m_k_charged", "pdg2026.m_k0", "pdg2026.m_eta",
                 "pdg2026.m_rho770", "pdg2026.m_omega782", "pdg2026.m_p", "pdg2026.m_n", "pdg2026.m_lambda", "pdg2026.m_delta1232"]
        values = [quantity(id).value for id in order]
        self.assertEqual(values, sorted(values))

    def test_delta_is_a_range_not_an_uncertainty(self) -> None:
        delta = quantity("pdg2026.m_delta1232")
        self.assertEqual(delta.uncertainty_kind, "PDG estimated range")
        self.assertEqual((delta.value - delta.lower_uncertainty, delta.value + delta.uncertainty), (1230, 1234))
        self.assertIn("1230 TO 1232 TO 1234", " ".join(delta.notes))

    def test_pion_ask_links_both_pions(self) -> None:
        session = unfold(Request(ask="what is the pion mass", seed=1))
        atoms = [claim.atom for claim in session.claims]
        self.assertIn("record(pdg2026.m_pi_charged)", atoms)
        self.assertIn("record(pdg2026.m_pi0)", atoms)
        self.assertEqual(session.retracted, ())


class GravityTestsTests(unittest.TestCase):
    def test_pulsar_ratios_sit_near_one_as_printed(self) -> None:
        hulse = quantity("psr_b1913.pbdot_ratio")
        double = quantity("double_pulsar.pbdot_ratio")
        self.assertLessEqual(abs(hulse.value - 1), 2 * hulse.uncertainty)
        self.assertLessEqual(abs(double.value - 1), 2 * double.uncertainty)
        self.assertLess(double.uncertainty * 25, hulse.uncertainty * 1)
        for key in ("pbdot", "omdot", "shapiro_s", "shapiro_r", "gamma_e"):
            item = quantity(f"double_pulsar.{key}_ratio")
            self.assertEqual(parse_concise(item.printed), (item.value, item.uncertainty))

    def test_gravity_probe_b_and_vlbi(self) -> None:
        geodetic, drag = quantity("gpb.geodetic"), quantity("gpb.frame_dragging")
        self.assertEqual(geodetic.uncertainty_kind, "standard uncertainty")
        self.assertLess(drag.value, 0)
        self.assertGreater(abs(drag.value), 5 * drag.uncertainty)
        gamma = quantity("vlbi.lambert2011.gamma")
        self.assertLessEqual(abs(gamma.value - 1), gamma.uncertainty)
        cassini = quantity("cassini.bertotti2003.gamma_minus_1")
        self.assertLessEqual((gamma.value - 1 - cassini.value) ** 2, gamma.uncertainty**2 + cassini.uncertainty**2)

    def test_big_g_spread_and_the_codata_expansion_factor(self) -> None:
        inputs = [item for item in QUANTITIES if item.id.startswith("g_input.")]
        self.assertEqual(len(inputs), 16)
        g = quantity("codata2022.g")
        residual = {item.id: (item.value - g.value) / item.uncertainty for item in inputs}
        self.assertEqual(residual["g_input.bipm14"], Fraction(775, 100))
        self.assertEqual(residual["g_input.jila18"], Fraction(-680, 100))
        self.assertEqual(max(residual, key=residual.get), "g_input.bipm14")
        self.assertEqual(min(residual, key=residual.get), "g_input.jila18")
        self.assertTrue(all(abs(r) <= 2 * Fraction(39, 10) for r in residual.values()))
        self.assertTrue(any(abs(r) > 2 for r in residual.values()))
        spread = max(item.value for item in inputs) - min(item.value for item in inputs)
        self.assertGreater(spread, 20 * g.uncertainty)
        for item in inputs:
            self.assertEqual(parse_concise(item.printed), (item.value, item.uncertainty))

    def test_big_g_ask_links_every_input(self) -> None:
        session = unfold(Request(ask="show the big g measurements", seed=1))
        atoms = [claim.atom for claim in session.claims]
        self.assertEqual(len([a for a in atoms if a.startswith("record(g_input.")]), 16)
        self.assertEqual(session.retracted, ())


class AtomicSpectroscopyTests(unittest.TestCase):
    def test_printed_forms_and_levels(self) -> None:
        for item in QUANTITIES:
            if item.printed and item.id.split(".")[0] in {"parthey2011", "matveev2013", "bezginov2019", "lundeen1981", "antognini2013", "crema2013"}:
                self.assertEqual(parse_concise(item.printed), (item.value, item.uncertainty), item.id)
                self.assertEqual(item.uncertainty_kind, "standard uncertainty", item.id)
        self.assertEqual(quantity("bezginov2019.h_lamb_shift").uncertainty, Fraction(32, 10))
        self.assertEqual(quantity("antognini2013.mu_h_f0_f1").uncertainty, Fraction(105, 100))

    def test_1s_2s_frequencies_agree_and_follow_the_rydberg_scale(self) -> None:
        parthey, matveev = quantity("parthey2011.h_1s2s"), quantity("matveev2013.h_1s2s")
        p_hz, m_hz = parthey.value, matveev.value * 1000
        self.assertEqual(p_hz - m_hz, 17)
        self.assertLessEqual((p_hz - m_hz) ** 2, 4 * (parthey.uncertainty**2 + (matveev.uncertainty * 1000) ** 2))
        # Gross structure: f = (3/4) R_inf c times the reduced-mass factor, up to alpha^2-sized corrections.
        r_inf, c = quantity("codata2022.r_inf"), quantity("codata2022.c")
        ratio_mass = quantity("codata2022.m_p_over_m_e").value
        reduced = ratio_mass / (ratio_mass + 1)
        bohr = Fraction(3, 4) * r_inf.value * c.value * reduced
        alpha = quantity("codata2022.alpha").value
        self.assertLess(abs(p_hz / bohr - 1), alpha**2)
        self.assertGreater(abs(p_hz / bohr - 1), alpha**3)

    def test_lamb_shift_measurements(self) -> None:
        york, harvard = quantity("bezginov2019.h_lamb_shift"), quantity("lundeen1981.h_lamb_shift")
        self.assertEqual(york.unit, "kHz")
        self.assertLessEqual((york.value - harvard.value) ** 2, 4 * (york.uncertainty**2 + harvard.uncertainty**2))
        self.assertGreater((york.value - harvard.value) ** 2, york.uncertainty**2 + harvard.uncertainty**2)
        # About one GHz, roughly a tenth of the 2P fine-structure splitting.
        self.assertTrue(1_057_000 < york.value < 1_058_000)

    def test_21_cm_line_is_twenty_one_centimetres(self) -> None:
        nu, c = quantity("hellwig1970.h_21cm"), quantity("codata2022.c")
        self.assertEqual(nu.uncertainty, Fraction(2, 1000))
        wavelength = c.value / nu.value
        self.assertTrue(Fraction(2110, 10000) < wavelength < Fraction(2111, 10000))

    def test_h_alpha_components_and_blend(self) -> None:
        blend, ritz = quantity("asd512.h_alpha.blend"), quantity("asd512.h_alpha.blend_ritz")
        strong = quantity("asd512.h_alpha.2p32_3d52")
        self.assertLessEqual((blend.value - ritz.value) ** 2, blend.uncertainty**2 + ritz.uncertainty**2)
        self.assertLessEqual(abs(strong.value - blend.value), 3 * blend.uncertainty)
        # Balmer formula with R_inf, vacuum: 1/lambda = R_inf (1/4 - 1/9) reduced; air is shorter by ~0.03%.
        r_inf = quantity("codata2022.r_inf").value
        ratio_mass = quantity("codata2022.m_p_over_m_e").value
        vacuum_nm = 1 / (r_inf * ratio_mass / (ratio_mass + 1) * Fraction(5, 36)) * 10**9
        self.assertTrue(0 < vacuum_nm - ritz.value < Fraction(2, 10))

    def test_muonic_radius_against_codata_pdg_and_york(self) -> None:
        muonic = quantity("antognini2013.proton_charge_radius")
        self.assertTrue(_agrees(muonic, quantity("pdg2026.proton_radius").value, _rel2(quantity("pdg2026.proton_radius"))))
        codata = quantity("codata2022.r_p")
        self.assertTrue(_agrees(muonic, codata.value * 10**15, _rel2(codata)))
        york = Fraction(833, 1000), Fraction(10, 1000)  # Bezginov et al. abstract, r_p = 0.833 +- 0.010 fm
        self.assertLessEqual((muonic.value - york[0]) ** 2, muonic.uncertainty**2 + york[1] ** 2)
        self.assertLess(quantity("antognini2013.proton_charge_radius").value, quantity("antognini2013.proton_zemach_radius").value)
        lamb = quantity("crema2013.mu_h_lamb_shift")
        self.assertEqual(lamb.unit, "meV")
        self.assertTrue(202 < lamb.value < 203)

    def test_spectroscopy_asks_link(self) -> None:
        muonic = {"antognini2013.mu_h_f0_f1", "antognini2013.mu_h_f1_f2", "antognini2013.proton_charge_radius", "antognini2013.proton_zemach_radius", "crema2013.mu_h_lamb_shift"}
        halpha = {"asd512.h_alpha.blend", "asd512.h_alpha.blend_ritz", "asd512.h_alpha.2p32_3d52"}
        for ask, expected in (("show the h-alpha line", halpha), ("what does muonic hydrogen say", muonic), ("hydrogen spectroscopy", None)):
            session = unfold(Request(ask=ask, seed=1))
            linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
            if expected is None:
                self.assertTrue({"parthey2011.h_1s2s", "bezginov2019.h_lamb_shift", "hellwig1970.h_21cm"} <= linked)
            else:
                self.assertEqual(linked, expected, ask)
            self.assertEqual(session.retracted, ())


class NuclearCodataTests(unittest.TestCase):
    def test_deuteron_binding_from_masses_and_ame(self) -> None:
        binding = quantity("codata2022.e_b_deuteron")
        self.assertEqual(parse_concise(binding.printed), (binding.value, binding.uncertainty))
        n, p, d = quantity("codata2022.m_n_c2_mev"), quantity("codata2022.m_p_c2_mev"), quantity("codata2022.m_d_c2_mev")
        from_masses = (n.value + p.value - d.value) * 1000
        sigma2 = (n.uncertainty**2 + p.uncertainty**2 + d.uncertainty**2) * 10**6
        self.assertLessEqual((from_masses - binding.value) ** 2, sigma2 + binding.uncertainty**2)
        ame = quantity("ame2020.h2.binding_per_nucleon")
        self.assertLessEqual((2 * ame.value - binding.value) ** 2, (2 * ame.uncertainty) ** 2 + binding.uncertainty**2)

    def test_alpha_mass_units_agree_and_match_ame_helium_4(self) -> None:
        kg, u, mev = quantity("codata2022.m_alpha"), quantity("codata2022.m_alpha_u"), quantity("codata2022.m_alpha_c2_mev")
        c, e = quantity("codata2022.c").value, quantity("codata2022.e").value
        from_kg = kg.value * c**2 / e / 10**6
        self.assertLessEqual((from_kg - mev.value) ** 2, mev.uncertainty**2 + (kg.uncertainty * c**2 / e / 10**6) ** 2)
        # AME2020's u in keV is the CODATA 2018 conversion; against CODATA 2022 it reads about 5 eV low for the alpha.
        u_kev = quantity("ame2020.u_kev")
        from_u = u.value * u_kev.value / 1000
        self.assertGreater((mev.value - from_u) ** 2, 9 * (mev.uncertainty**2 + (u.value * u_kev.uncertainty / 1000) ** 2))
        # Atom = nucleus + 2 electrons - electron binding; the binding is He I plus a hydrogen-like He II.
        m_e_u = quantity("codata2022.m_e").value * u.value / kg.value
        atom = quantity("ame2020.he4.atomic_mass")
        binding_ev = (u.value + 2 * m_e_u - atom.value / 10**6) * u_kev.value * 1000
        expected = quantity("asd512.ie.he").value + 4 * quantity("codata2022.ryd_hc_ev").value
        atom_sigma_ev = atom.uncertainty / 10**6 * u_kev.value * 1000
        self.assertLessEqual(abs(binding_ev - expected), 3 * atom_sigma_ev)
        self.assertTrue(78 < binding_ev < 80)

    def test_magnetic_moments_are_consistent(self) -> None:
        mu_p, mu_n, mu_nuc = quantity("codata2022.mu_p"), quantity("codata2022.mu_n"), quantity("codata2022.mu_n_nuclear")
        p_ratio, n_ratio = quantity("codata2022.mu_p_over_mu_n_nuclear"), quantity("codata2022.mu_n_over_mu_n_nuclear")
        ratio = quantity("codata2022.mu_n_over_mu_p")
        self.assertGreater(mu_p.value, 0)
        self.assertLess(mu_n.value, 0)
        self.assertLessEqual((p_ratio.value * mu_nuc.value - mu_p.value) ** 2, mu_p.uncertainty**2)
        self.assertLessEqual((n_ratio.value * mu_nuc.value - mu_n.value) ** 2, mu_n.uncertainty**2)
        self.assertLessEqual((n_ratio.value / p_ratio.value - ratio.value) ** 2, ratio.uncertainty**2)
        self.assertLessEqual((mu_n.value / mu_p.value - ratio.value) ** 2, ratio.uncertainty**2)
        # Both moments are far from the Dirac values 1 and 0.
        self.assertGreater(p_ratio.value - 1, Fraction(17, 10))

    def test_nucleon_moment_ask_links(self) -> None:
        session = unfold(Request(ask="nucleon magnetic moment", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertEqual(linked, {"codata2022.mu_p", "codata2022.mu_n", "codata2022.mu_p_over_mu_n_nuclear", "codata2022.mu_n_over_mu_n_nuclear", "codata2022.mu_n_over_mu_p"})
        self.assertEqual(session.retracted, ())


def _exp_enclosure(y: Fraction, terms: int = 60) -> tuple[Fraction, Fraction]:
    """e^y for 0 <= y < terms + 2: the Taylor partial sum, and that sum plus a geometric bound on the tail."""
    total, term = Fraction(0), Fraction(1)
    for n in range(terms + 1):
        total += term
        term = term * y / (n + 1)
    return total, total + term / (1 - y / (terms + 2))


def _wien_root(n: int, guess: float) -> tuple[Fraction, Fraction]:
    """Enclose the positive root of x = n (1 - e^-x), checked in exact rationals:
    f(x) = x - n + n e^-x is increasing past ln n, negative below the root and positive above it."""
    low = Fraction(round(guess * 10**15) - 100, 10**15)
    high = Fraction(round(guess * 10**15) + 100, 10**15)
    exp_low_lo, exp_low_hi = _exp_enclosure(low)
    exp_high_lo, exp_high_hi = _exp_enclosure(high)
    assert low - n + n / exp_low_lo < 0  # largest possible e^-low still leaves f(low) < 0
    assert high - n + n / exp_high_hi > 0  # smallest possible e^-high still leaves f(high) > 0
    return low, high


class RadiationConstantTests(unittest.TestCase):
    def test_truncated_print_is_read_as_a_half_open_interval(self) -> None:
        self.assertEqual(parse_truncated("5.670 374 419... e-8"), (Fraction(5670374419, 10**17), Fraction(5670374420, 10**17)))
        with self.assertRaises(ValueError):
            parse_truncated("5.670 374 419 e-8")
        for id in ("codata2022.sigma", "codata2022.b_wien", "codata2022.b_prime_wien"):
            item = quantity(id)
            self.assertTrue(item.exact and item.truncated, id)
            self.assertEqual(item.uncertainty_kind, "exact, printed truncated")
            self.assertIsNone(item.uncertainty)
            record = {r.id: r for r in RECORDS}[id]
            self.assertEqual(record.forbids, (f"derived({id})",))

    def test_stefan_boltzmann_follows_from_h_c_k_with_an_exact_pi_enclosure(self) -> None:
        h, c, k = (quantity(f"codata2022.{x}").value for x in ("h", "c", "k"))
        pi_low, pi_high = _pi_enclosure(30)
        factor = 2 * k**4 / (15 * h**3 * c**2)
        low, high = quantity("codata2022.sigma").truncation_bounds
        self.assertLessEqual(low, factor * pi_low**5)
        self.assertLess(factor * pi_high**5, high)

    def test_wien_constants_follow_from_h_c_k_and_the_exact_roots(self) -> None:
        h, c, k = (quantity(f"codata2022.{x}").value for x in ("h", "c", "k"))
        x5_low, x5_high = _wien_root(5, 4.965114231744276)
        x3_low, x3_high = _wien_root(3, 2.821439372122079)
        b_low, b_high = quantity("codata2022.b_wien").truncation_bounds
        self.assertLessEqual(b_low, h * c / (k * x5_high))
        self.assertLess(h * c / (k * x5_low), b_high)
        bp_low, bp_high = quantity("codata2022.b_prime_wien").truncation_bounds
        self.assertLessEqual(bp_low, x3_low * k / h)
        self.assertLess(x3_high * k / h, bp_high)
        # The two peaks differ: b' b / c = x3 / x5, well below 1.
        self.assertLess(bp_high * b_high / c, Fraction(6, 10))

    def test_radiation_constant_ask_links(self) -> None:
        session = unfold(Request(ask="show the radiation constant values", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"codata2022.sigma", "codata2022.b_wien", "codata2022.b_prime_wien"} <= linked)
        self.assertEqual(session.retracted, ())


class ChemistryTests(unittest.TestCase):
    def _span(self, sym: str) -> tuple[Fraction, Fraction]:
        id = f"iupac2021.ar.{sym.lower()}"
        for bound in BOUNDS:
            if bound.id == id:
                return bound.lower, bound.upper
        item = quantity(id)
        return item.value - item.uncertainty, item.value + item.uncertainty

    def test_atomic_weights_h_to_kr_are_all_there_as_printed(self) -> None:
        self.assertEqual([row[0] for row in CIAAW_H_KR], list(range(1, 37)))
        intervals = [b for b in BOUNDS if b.id.startswith("iupac2021.ar.")]
        values = [q for q in QUANTITIES if q.id.startswith("iupac2021.ar.")]
        self.assertEqual((len(intervals), len(values)), (12, 24))
        for item in values:
            self.assertEqual(parse_concise(item.printed), (item.value, item.uncertainty), item.id)
            self.assertEqual(item.uncertainty_kind, "IUPAC standard atomic weight uncertainty")
        for bound in intervals:
            self.assertLess(bound.lower, bound.upper, bound.id)
        self.assertEqual(self._span("C"), (Fraction("12.0096"), Fraction("12.0116")))
        self.assertEqual(quantity("iupac2021.ar.co").uncertainty, Fraction(3, 10**6))

    def test_atomic_weight_rises_with_z_except_argon_and_cobalt(self) -> None:
        inversions = []
        for (z1, s1, *_), (z2, s2, *_) in zip(CIAAW_H_KR, CIAAW_H_KR[1:]):
            low1, high1 = self._span(s1)
            low2, high2 = self._span(s2)
            if low2 > high1:
                continue
            self.assertGreater(low1, high2, (s1, s2))
            inversions.append((s1, s2))
        self.assertEqual(inversions, [("Ar", "K"), ("Co", "Ni")])

    def test_diatomic_data_rows(self) -> None:
        for mol in ("h2", "n2", "o2", "co", "hcl"):
            r_e = quantity(f"hh1979.{mol}.r_e")
            self.assertIsNone(r_e.uncertainty)
            self.assertEqual(r_e.uncertainty_kind, "no uncertainty printed")
            d0 = quantity(f"cccbdb.{mol}.d0")
            row = next(note for note in d0.notes if note.startswith("CCCBDB row"))
            at_298 = parse_decimal(row.split("298 K ")[1].split(",")[0])
            self.assertGreater(at_298, d0.value, mol)
        self.assertIsNone(quantity("cccbdb.h2.d0").uncertainty)
        self.assertEqual(quantity("cccbdb.n2.d0").uncertainty, Fraction(8, 10))
        self.assertEqual(max((quantity(f"cccbdb.{m}.d0") for m in ("h2", "n2", "o2", "co", "hcl")), key=lambda q: q.value).id, "cccbdb.co.d0")

    def test_pka_pkw_and_enthalpy_rows_agree_where_they_overlap(self) -> None:
        iupac, crc = quantity("iupac_pka.phenol"), quantity("crc91.pka.phenol")
        self.assertLessEqual(abs(iupac.value - crc.value), Fraction(5, 1000))
        water, iapws = quantity("crc91.pka.water"), quantity("iapws2024.pkw_25c")
        self.assertLessEqual(abs(water.value - iapws.value), Fraction(5, 1000))
        janaf, gurvich = quantity("janaf1998.ch4_g.dfh"), quantity("gurvich1991.ch4_g.dfh")
        self.assertLessEqual(abs(janaf.value - gurvich.value), gurvich.uncertainty)
        for id in ("codata_key.h2o_l.dfh", "codata_key.co2_g.dfh", "janaf1998.ch4_g.dfh"):
            self.assertLess(quantity(id).value, 0, id)

    def test_chemistry_asks_link(self) -> None:
        session = unfold(Request(ask="show the standard atomic weights", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertEqual(len([x for x in linked if x.startswith("iupac2021.ar.")]), 36)
        self.assertEqual(session.retracted, ())
        session = unfold(Request(ask="what is the phenol pka", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertEqual(linked, {"iupac_pka.phenol", "crc91.pka.phenol"})


class CondensedMatterTests(unittest.TestCase):
    def test_silicon_lattice_entries_match_codata_table_definitions(self) -> None:
        # CODATA's own table defines d220 = a/sqrt(8) and V_m = N_A a^3 / 8; check the printed values against those definitions.
        a, d, vm = quantity("codata2022.a_si"), quantity("codata2022.d220_si"), quantity("codata2022.vm_si")
        self.assertLessEqual((a.value**2 - 8 * d.value**2) ** 2, (2 * a.value * a.uncertainty + 16 * d.value * d.uncertainty) ** 2)
        n_a = quantity("codata2022.n_a").value
        self.assertLessEqual(abs(n_a * a.value**3 / 8 - vm.value), vm.uncertainty + 3 * n_a * a.value**2 * a.uncertainty / 8)

    def test_quantum_electrical_constants(self) -> None:
        for id in ("codata2022.r_k", "codata2022.k_j"):
            self.assertTrue(quantity(id).truncated, id)
        for id in ("codata2022.r_k_90", "codata2022.k_j_90"):
            item = quantity(id)
            self.assertTrue(item.exact and not item.truncated, id)
        low, high = quantity("codata2022.r_k").truncation_bounds
        self.assertFalse(low <= quantity("codata2022.r_k_90").value < high)
        low, high = quantity("codata2022.k_j").truncation_bounds
        self.assertFalse(low <= quantity("codata2022.k_j_90").value < high)

    def test_printed_condensed_matter_values(self) -> None:
        gaps = {m: quantity(f"ioffe.{m}.band_gap_300k").value for m in ("si", "ge", "gaas")}
        self.assertEqual(sorted(gaps, key=gaps.get), ["ge", "si", "gaas"])
        tc = {e: quantity(f"srm767a.{e}.tc").value for e in ("niobium", "lead", "aluminum")}
        self.assertEqual(sorted(tc, key=tc.get), ["aluminum", "lead", "niobium"])
        self.assertGreater(quantity("wu1987.ybco.tc").value, 10 * tc["niobium"])
        for id in ("srm767a.niobium.tc", "wu1987.ybco.tc", "ioffe.si.band_gap_300k", "iapws2011.h2o.t_t", "iapws2011.h2o.p_t"):
            self.assertIsNone(quantity(id).uncertainty, id)
        self.assertEqual(quantity("arajs1964.fe.curie").uncertainty, 2)

    def test_water_triple_point_sits_below_the_critical_point(self) -> None:
        t_t, p_t = quantity("iapws2011.h2o.t_t"), quantity("iapws2011.h2o.p_t")
        t_c, p_c = quantity("iapws1992.h2o.t_c"), quantity("iapws1992.h2o.p_c")
        self.assertLess(t_t.value, t_c.value - t_c.uncertainty)
        self.assertLess(p_t.value, (p_c.value - p_c.uncertainty) * 10**6)
        self.assertEqual(quantity("iapws1992.h2o.rho_c").uncertainty, 3)

    def test_condensed_matter_asks_link(self) -> None:
        session = unfold(Request(ask="list the superconducting transition temperatures", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertEqual(linked, {"srm767a.niobium.tc", "srm767a.lead.tc", "srm767a.aluminum.tc", "wu1987.ybco.tc", "nagamatsu2001.mgb2.tc", "drozdov2015.h3s.tc"})
        session = unfold(Request(ask="what is the critical point of water", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertEqual(linked, {"iapws1992.h2o.t_c", "iapws1992.h2o.p_c", "iapws1992.h2o.rho_c"})
        self.assertEqual(session.retracted, ())


class ParticleBatchFiveTests(unittest.TestCase):
    @staticmethod
    def _combined(item):
        # Use the source's own printed total where it prints one; otherwise the single printed error.
        totals = {"cdf2022.m_w": Fraction("9.4"), "atlas2024.m_w": Fraction("15.9")}
        return totals.get(item.id, item.uncertainty)

    def test_w_mass_measurements_show_the_cdf_tension(self) -> None:
        cdf, atlas, cms = (quantity(id) for id in ("cdf2022.m_w", "atlas2024.m_w", "cms2026.m_w"))
        for item in (cdf, atlas, cms):
            self.assertEqual(item.unit, "MeV")
        for other in (atlas, cms):
            gap = cdf.value - other.value
            self.assertGreater(gap**2, 9 * (self._combined(cdf) ** 2 + self._combined(other) ** 2), other.id)
        gap = atlas.value - cms.value
        self.assertLess(gap**2, self._combined(atlas) ** 2 + self._combined(cms) ** 2)
        pdg = quantity("pdg2026.m_w")
        self.assertLess(abs(cms.value - pdg.value * 1000), cms.uncertainty)

    def test_neutrino_parameters_as_printed(self) -> None:
        for id in ("pdg2026.nu.sin2_theta12", "pdg2026.nu.sin2_theta23_no", "pdg2026.nu.sin2_theta23_io", "pdg2026.nu.sin2_theta13"):
            item = quantity(id)
            self.assertTrue(0 <= item.value - item.lower_uncertainty and item.value + item.uncertainty <= 1, id)
        self.assertGreater(quantity("pdg2026.nu.dm2_32_no").value, 0)
        self.assertLess(quantity("pdg2026.nu.dm2_32_io").value, 0)
        self.assertEqual(quantity("pdg2026.nu.sin2_theta23_io").lower_uncertainty, Fraction("0.027"))

    def test_higgs_width_value_sits_inside_the_listed_bound(self) -> None:
        width = quantity("pdg2026.gamma_h")
        bound = next(b for b in BOUNDS if b.id == "bound.atlas2025e.higgs_width")
        self.assertLess(width.value + width.uncertainty, bound.upper)
        self.assertEqual(width.uncertainty_kind, "asymmetric standard uncertainty")

    def test_lifetimes_and_lattice_alpha_s(self) -> None:
        tau = {id: quantity(f"pdg2026.{id}_lifetime").value for id in ("tau", "b_plus", "b0", "bs")}
        self.assertEqual(min(tau, key=tau.get), "tau")
        self.assertGreater(tau["b_plus"], tau["b0"])
        flag, pdg = quantity("flag2024.alpha_s_mz"), quantity("pdg2026.alpha_s_mz")
        self.assertEqual(flag.printed, "0.11833(67)")
        self.assertLess((flag.value - pdg.value) ** 2, flag.uncertainty**2 + pdg.uncertainty**2)

    def test_particle_asks_link(self) -> None:
        session = unfold(Request(ask="compare the w mass measurements", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"cdf2022.m_w", "atlas2024.m_w", "cms2026.m_w"} <= linked)
        session = unfold(Request(ask="what are the neutrino oscillation parameters", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({id for id in linked if id.startswith("pdg2026.nu.")} == {
            "pdg2026.nu.sin2_theta12", "pdg2026.nu.dm2_21", "pdg2026.nu.sin2_theta23_no", "pdg2026.nu.sin2_theta23_io",
            "pdg2026.nu.dm2_32_no", "pdg2026.nu.dm2_32_io", "pdg2026.nu.sin2_theta13"})
        self.assertEqual(session.retracted, ())


class AstrophysicsTests(unittest.TestCase):
    def test_nominal_values_are_exact_and_sit_inside_the_estimates_they_round(self) -> None:
        nominal = [item for item in QUANTITIES if item.id.startswith("iau2015.nominal.")]
        self.assertEqual(len(nominal), 11)
        self.assertTrue(all(item.exact for item in nominal))
        self.assertTrue(quantity("iau2012.au").exact)
        self.assertEqual(quantity("iau2012.au").value, 149597870700)
        for nominal_id, estimate_id, scale in (
            ("iau2015.nominal.s_sun", "iau2015.cbe.s_sun", 1),
            ("iau2015.nominal.l_sun", "iau2015.cbe.l_sun", 1),
            ("iau2015.nominal.teff_sun", "iau2015.cbe.teff_sun", 1),
            ("iau2015.nominal.r_sun", "haberreiter2008.r_sun", 1000),
        ):
            estimate = quantity(estimate_id)
            self.assertLessEqual(abs(quantity(nominal_id).value - estimate.value * scale), estimate.uncertainty * scale, nominal_id)
        self.assertEqual(quantity("iau2015.cbe.s_sun").uncertainty_kind, "2 sigma")

    def test_nominal_mass_parameters_are_the_digits_where_time_scales_agree(self) -> None:
        # Resolution B3: (GM)_sun^N and (GM)_E^N are given to the precision within which the TCB and TDB values agree.
        for nominal_id, ids in (
            ("iau2015.nominal.gm_sun", ("iau2026.gm_sun_tcb", "iau2026.gm_sun_tdb")),
            ("iau2015.nominal.gm_earth", ("iau2026.gm_earth_tcb", "iau2026.gm_earth_tt", "iau2026.gm_earth_tdb")),
        ):
            nominal = quantity(nominal_id)
            step = Fraction(10) ** (len(nominal.value_text.split("e")[0].replace(" ", "").split(".")[1]) - int(nominal.value_text.split("e")[1]))
            for id in ids:
                value = quantity(id).value
                self.assertEqual(Fraction(int(value * step)) / step, nominal.value, id)

    def test_compact_objects_and_the_moon(self) -> None:
        bond, joyce = quantity("bond2017.sirius_b.mass"), quantity("joyce2018.sirius_b.mass")
        self.assertLess((bond.value - joyce.value) ** 2, bond.uncertainty**2 + joyce.uncertainty**2)
        r_bond, r_joyce = quantity("bond2017.sirius_b.radius"), quantity("joyce2018.sirius_b.radius")
        self.assertEqual(r_joyce.unit, "R_sun/100")
        self.assertLess((r_bond.value - r_joyce.value / 100) ** 2, r_bond.uncertainty**2 + (r_joyce.uncertainty / 100) ** 2)
        radii = [quantity(f"{id}.j0740.radius") for id in ("riley2021", "miller2021", "salmi2024", "dittmann2024")]
        for a in radii:
            for b in radii:
                self.assertLess(a.value - a.lower_uncertainty, b.value + b.uncertainty, (a.id, b.id))
        self.assertGreater(quantity("fonseca2021.j0740.mass").value, 2 * bond.value)
        self.assertLessEqual(abs(quantity("nssdc.moon.recession").value * 10 - quantity("williams2016.lunar_da_dt").value), Fraction(1, 2))

    def test_astrophysics_asks_link(self) -> None:
        session = unfold(Request(ask="what is the radius of psr j0740+6620", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"riley2021.j0740.radius", "miller2021.j0740.radius", "salmi2024.j0740.radius", "dittmann2024.j0740.radius"} <= linked)
        session = unfold(Request(ask="how fast is the lunar recession", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"williams2016.lunar_da_dt", "nssdc.moon.recession"} <= linked)
        self.assertEqual(session.retracted, ())


class NuclearParticleBatchSixTests(unittest.TestCase):
    LIGHT = ("li6", "li7", "be9", "b10", "b11", "c13", "n14", "n15", "o17", "o18")

    def test_light_nuclei_rows_are_complete_and_consistent_with_their_mass_numbers(self) -> None:
        for sym in self.LIGHT:
            mass = quantity(f"ame2020.{sym}.atomic_mass")
            a = int("".join(ch for ch in sym if ch.isdigit()))
            self.assertLess(abs(mass.value / 10**6 - a), Fraction(1, 50), sym)
            # AME's mass excess is M - A u; both columns are in the same file row, so they must agree to the file's own precision.
            excess = quantity(f"ame2020.{sym}.mass_excess")
            u_kev = quantity("ame2020.u_kev")
            offset = mass.value / 10**6 - a
            allowance = excess.uncertainty + mass.uncertainty / 10**6 * u_kev.value + abs(offset) * u_kev.uncertainty
            self.assertLessEqual(abs(offset * u_kev.value - excess.value), allowance, sym)
        binding = {sym: quantity(f"ame2020.{sym}.binding_per_nucleon").value for sym in self.LIGHT + ("o16",)}
        self.assertEqual(max(binding, key=binding.get), "o16")
        self.assertEqual(min(binding, key=binding.get), "li6")

    def test_neutron_beta_energy_is_the_mass_excess_difference(self) -> None:
        # AME defines Q(beta-) as the atomic mass difference, so the column must equal Delta(n) - Delta(1H) to its printed precision.
        q = quantity("ame2020.n.beta_decay_energy")
        gap = quantity("ame2020.n.mass_excess").value - quantity("ame2020.h1.mass_excess").value
        self.assertLessEqual(abs(gap - q.value), q.uncertainty)

    def test_lifetimes(self) -> None:
        order = ["pi0", "k_short", "k_plus", "pi_plus", "k_long", "mu"]
        values = [quantity(f"pdg2026.{name}_lifetime").value for name in order]
        self.assertEqual(values, sorted(values))
        mulan, pdg = quantity("mulan2013.mu_lifetime"), quantity("pdg2026.mu_lifetime")
        self.assertEqual(mulan.unit, "ps")
        gap = mulan.value * Fraction(1, 10**12) - pdg.value
        self.assertLess(gap**2, (mulan.uncertainty * Fraction(1, 10**12)) ** 2 + pdg.uncertainty**2)

    def test_nuclear_particle_asks_link(self) -> None:
        session = unfold(Request(ask="what is the kaon lifetime", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"pdg2026.k_plus_lifetime", "pdg2026.k_short_lifetime", "pdg2026.k_long_lifetime"} <= linked)
        self.assertEqual(session.retracted, ())


class AtomicMolecularBatchSixTests(unittest.TestCase):
    SYMBOLS = ("he", "li", "be", "b", "c", "n", "o", "f", "ne")

    def test_second_ionization_energies_exceed_the_first(self) -> None:
        for sym in self.SYMBOLS:
            second, first = quantity(f"asd512.ie2.{sym}"), quantity(f"asd512.ie.{sym}")
            self.assertGreater(second.value - second.uncertainty, first.value + first.uncertainty, sym)
        self.assertNotIn("asd512.ie2.h", {item.id for item in QUANTITIES})
        self.assertTrue(any("square brackets" in note for note in quantity("asd512.ie2.n").notes))

    def test_electron_affinities_as_printed(self) -> None:
        ea = {sym: quantity(f"rk2002.ea.{sym}") for sym in ("h", "c", "o", "f", "cl")}
        self.assertEqual(sorted(ea, key=lambda sym: ea[sym].value), ["h", "c", "o", "f", "cl"])
        self.assertEqual(ea["f"].value_text, "3.401290")
        for sym, item in ea.items():
            self.assertLess(item.value, quantity(f"asd512.ie.{sym}").value, sym)

    def test_h2_dissociation_energy(self) -> None:
        item = quantity("holsch2019.h2.d0_ortho")
        self.assertEqual(item.printed, "35 999.582 834(11)")
        self.assertEqual(item.uncertainty, Fraction(11, 10**6))

    def test_atomic_asks_link(self) -> None:
        session = unfold(Request(ask="list the second ionization energies", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertEqual({id for id in linked if id.startswith("asd512.ie2.")}, {f"asd512.ie2.{sym}" for sym in self.SYMBOLS})
        session = unfold(Request(ask="what are the electron affinities", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({f"rk2002.ea.{sym}" for sym in ("h", "c", "o", "f", "cl")} <= linked)
        self.assertEqual(session.retracted, ())


class EarlyUniverseTests(unittest.TestCase):
    def test_fluorine_affinities_kept_apart(self) -> None:
        review, primary = quantity("rk2002.ea.f"), quantity("blondel2001.ea.f")
        self.assertEqual(review.value_text, "3.401290")
        self.assertEqual(primary.printed, "3.401 1895(25)")
        self.assertEqual(review.name, primary.name)
        gap = review.value - primary.value
        self.assertGreater(gap, 10 * (review.uncertainty + primary.uncertainty))
        self.assertTrue(any("rk2002.ea.f" in note for note in primary.notes))
        self.assertTrue(any("Blondel" in note for note in review.notes))

    def test_helium_and_deuterium_sources_agree(self) -> None:
        for a, b in (("pdg2026.bbn.y_p", "aver2021.y_p"), ("pdg2026.bbn.d_h", "cooke2018.d_h")):
            x, y = quantity(a), quantity(b)
            self.assertLess(abs(x.value - y.value), x.uncertainty + y.uncertainty, (a, b))

    def test_lithium_gap_matches_the_printed_wording(self) -> None:
        stars, bbn = quantity("pdg2026.bbn.li_h"), quantity("fields2020.li_h")
        self.assertEqual(round(float(bbn.value / stars.value), 1), 3.3)
        sigma = float((bbn.value - stars.value) ** 2 / (bbn.uncertainty ** 2 + stars.uncertainty ** 2)) ** 0.5
        self.assertEqual(round(sigma, 1), 4.4)
        self.assertTrue(any("lower bound" in note for note in stars.notes))

    def test_n_eff_intervals(self) -> None:
        inner, outer = quantity("planck2018.n_eff"), quantity("planck2018.n_eff_95")
        self.assertEqual(outer.uncertainty_kind, "95% interval")
        self.assertEqual((outer.uncertainty, outer.lower_uncertainty), (Fraction(34, 100), Fraction(33, 100)))
        self.assertEqual(inner.value, outer.value)
        self.assertLess(inner.uncertainty, outer.lower_uncertainty)

    def test_early_universe_asks_link(self) -> None:
        session = unfold(Request(ask="what is the lithium problem", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"pdg2026.bbn.li_h", "fields2020.li_h"} <= linked)
        session = unfold(Request(ask="list the primordial abundances", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"pdg2026.bbn.y_p", "pdg2026.bbn.d_h", "pdg2026.bbn.li_h"} <= linked)
        session = unfold(Request(ask="what is the electron affinity of fluorine", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"rk2002.ea.f", "blondel2001.ea.f"} <= linked)


class ExoticQedTests(unittest.TestCase):
    def test_positronium_hyperfine_records_disagree_as_printed(self) -> None:
        new, old = quantity("ishida2014.ps.hfs"), quantity("ritter1984.ps.hfs")
        self.assertEqual(new.uncertainty_kind, "statistical and systematic, printed separately")
        self.assertEqual((new.uncertainty, new.systematic), (Fraction(16, 10000), Fraction(13, 10000)))
        self.assertEqual(old.printed, "203.389 10(74)")
        self.assertGreater(new.value - old.value, new.uncertainty + new.systematic + old.uncertainty)

    def test_positronium_decay_rates(self) -> None:
        para, ortho = quantity("alramadhan1994.pps.decay_rate"), quantity("kataoka2009.ops.decay_rate")
        self.assertEqual(para.unit, ortho.unit)
        self.assertGreater(para.value / ortho.value, 1000)

    def test_muonium_as_printed(self) -> None:
        item = quantity("liu1999.mu.hfs")
        self.assertEqual((item.value, item.uncertainty, item.unit), (4463302765, 53, "Hz"))
        self.assertEqual(quantity("liu1999.mu_moment_ratio").uncertainty, Fraction(39, 10**8))

    def test_helium_thesis_intervals_close(self) -> None:
        f12, f01, f02 = (quantity(f"zelevinsky2004.he.{k}") for k in ("f12", "f01", "f02"))
        self.assertLessEqual(abs(f01.value + f12.value - f02.value), f01.uncertainty + f12.uncertainty + f02.uncertainty)

    def test_helium_interval_records_side_by_side(self) -> None:
        khz = Fraction(1000)
        f01_new = quantity("heydarizadmotlagh2024.he.f01")
        f01_old = quantity("zelevinsky2004.he.f01")
        self.assertGreater(f01_new.value / khz - f01_old.value, 3 * (f01_new.uncertainty / khz + f01_old.uncertainty))
        self.assertLess(abs(quantity("george2001.he.f01").value - f01_old.value), quantity("george2001.he.f01").uncertainty + f01_old.uncertainty)
        f12_new, f12_old = quantity("kato2018.he.f12"), quantity("zelevinsky2004.he.f12")
        self.assertLess(abs(f12_new.value / khz - f12_old.value), 3 * (f12_new.uncertainty / khz + f12_old.uncertainty))

    def test_exotic_asks_link(self) -> None:
        session = unfold(Request(ask="what is the positronium hyperfine interval", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"ishida2014.ps.hfs", "ritter1984.ps.hfs"} <= linked)
        session = unfold(Request(ask="list the helium fine structure intervals", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"zelevinsky2004.he.f12", "kato2018.he.f12", "heydarizadmotlagh2024.he.f01"} <= linked)
        session = unfold(Request(ask="what is the muonium hyperfine interval", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertIn("liu1999.mu.hfs", linked)


class NullResultTests(unittest.TestCase):
    @staticmethod
    def _bound(id: str):
        (item,) = [b for b in BOUNDS if b.id == id]
        return item

    def test_edm_values_sit_inside_their_bounds(self) -> None:
        for value_id, bound_id in (("jila2023.d_e", "bound.jila2023.electron_edm"), ("abel2020.d_n", "bound.abel2020.neutron_edm")):
            item, bound = quantity(value_id), self._bound(bound_id)
            self.assertEqual(item.uncertainty_kind, "statistical and systematic, printed separately")
            self.assertEqual(item.unit, bound.unit)
            self.assertLess(abs(item.value), bound.upper, value_id)
            self.assertEqual(bound.lower, 0)

    def test_proton_bound_is_lower_only(self) -> None:
        bound = self._bound("bound.superk2020.proton_e_pi0")
        self.assertIsNone(bound.upper)
        self.assertEqual(bound.lower, Fraction(24 * 10**33))
        from pgi.corpus.records import RECORDS
        (record,) = [r for r in RECORDS if r.id == bound.id]
        self.assertIn("is at least 2.4 e34 years", record.statement[0])

    def test_mass_bounds_as_printed(self) -> None:
        self.assertEqual(self._bound("bound.pdg2026.photon_mass").upper, Fraction(1, 10**18))
        self.assertEqual(self._bound("bound.katrin2025.nu_mass").upper, Fraction(45, 100))
        gwtc3, pdg = self._bound("bound.gwtc3.graviton_mass"), self._bound("bound.pdg2026.graviton_mass")
        self.assertEqual(gwtc3.upper_text, "2.42 e-23")
        self.assertEqual(pdg.upper_text, "1.76 e-23")
        self.assertTrue(any("1.27" in condition for condition in gwtc3.conditions))

    def test_microscope_eta(self) -> None:
        eta = quantity("microscope2022.eta_ti_pt")
        self.assertEqual((eta.value, eta.uncertainty, eta.systematic), (Fraction(-15, 10**16), Fraction(23, 10**16), Fraction(15, 10**16)))
        self.assertLess(abs(eta.value), eta.uncertainty)

    def test_null_asks_link(self) -> None:
        session = unfold(Request(ask="list the null results", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"bound.jila2023.electron_edm", "bound.superk2020.proton_e_pi0", "microscope2022.eta_ti_pt"} <= linked)
        session = unfold(Request(ask="what is the graviton mass bound", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"bound.gwtc3.graviton_mass", "bound.pdg2026.graviton_mass"} <= linked)


class ThermoFluidsTests(unittest.TestCase):
    def _exact(self, id: str) -> Fraction:
        item = quantity(id)
        self.assertEqual(item.uncertainty_kind, "exact", id)
        return item.value

    def test_codata_gas_constants_match_their_definitions(self) -> None:
        n_a, k = self._exact("codata2022.n_a"), self._exact("codata2022.k")
        r = n_a * k
        low, high = quantity("codata2022.r_gas").truncation_bounds
        self.assertTrue(low <= r < high)
        for id, pressure in (("codata2022.v_m_100kpa", 100000), ("codata2022.v_m_101kpa", 101325)):
            low, high = quantity(id).truncation_bounds
            self.assertTrue(low <= r * Fraction(27315, 100) / pressure < high, id)
        for id, pressure in (("codata2022.n0_100kpa", 100000), ("codata2022.n0_101kpa", 101325)):
            low, high = quantity(id).truncation_bounds
            self.assertTrue(low <= pressure / (k * Fraction(27315, 100)) < high, id)
        self.assertEqual(quantity("codata2022.std_atm").value, 101325)

    def test_its90_columns_agree_and_rise(self) -> None:
        points = [item for item in QUANTITIES if item.id.startswith("its90.fp.")]
        self.assertEqual(len(points), 14)
        values = [item.value for item in points]
        self.assertEqual(values, sorted(values))
        for item in points:
            self.assertTrue(item.exact)
            celsius = item.value - Fraction(27315, 100)
            text = item.notes[0].split("t_90/degC = ")[1].split(" ")[0].rstrip(",").replace(",", ".")
            self.assertEqual(Fraction(text), celsius, item.id)
        self.assertEqual(quantity("its90.fp.h2o").value, quantity("iapws2011.h2o.t_t").value)

    def test_water_tables(self) -> None:
        self.assertGreater(quantity("webbook.h2o.viscosity_20c").value, quantity("webbook.h2o.viscosity_25c").value)
        tensions = [quantity(f"iapws2014.h2o.surface_tension_{t}c").value for t in ("0_01", "20", "25", "100")]
        self.assertEqual(tensions, sorted(tensions, reverse=True))
        self.assertIsNone(quantity("webbook.h2o.density_25c").uncertainty)

    def test_air_sound_speeds_disagree_beyond_wongs_ppm(self) -> None:
        wong, greenspan = quantity("wong1986.air.sound_speed"), quantity("greenspan1987.air.sound_speed")
        self.assertIsNone(wong.uncertainty)
        self.assertEqual(wong.relative_uncertainty, Fraction(200, 10**6))
        self.assertGreater((greenspan.value - wong.value) / wong.value, wong.relative_uncertainty)

    def test_thermo_asks_link(self) -> None:
        session = unfold(Request(ask="list the its-90 fixed points", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"its90.fp.ga", "its90.fp.cu", "its90.fp.h2o"} <= linked)
        session = unfold(Request(ask="what is the speed of sound in air", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"wong1986.air.sound_speed", "greenspan1987.air.sound_speed"} <= linked)


class CoverageTests(unittest.TestCase):
    def test_every_record_has_a_domain_and_the_file_matches(self) -> None:
        from pathlib import Path

        from pgi.corpus.coverage import DOMAINS, counts, table
        from pgi.corpus.records import RECORDS

        tally = counts()
        self.assertEqual(sum(tally.values()), len(RECORDS))
        self.assertEqual(tuple(tally), DOMAINS)
        text = (Path(__file__).resolve().parents[1] / "COVERAGE.md").read_text(encoding="utf-8")
        block = text.split("<!-- counts:start -->\n", 1)[1].split("\n<!-- counts:end -->", 1)[0]
        self.assertEqual(block, table())

    def test_gap_text_is_generated_from_the_board(self) -> None:
        from pathlib import Path

        from pgi.corpus.coverage import gap_table

        text = (Path(__file__).resolve().parents[1] / "COVERAGE.md").read_text(encoding="utf-8")
        block = text.split("<!-- gaps:start -->\n", 1)[1].split("\n<!-- gaps:end -->", 1)[0]
        self.assertEqual(block, gap_table())

    def test_every_record_is_described_and_every_entry_is_used(self) -> None:
        from pgi.corpus.coverage import held
        from pgi.corpus.records import RECORDS

        self.assertEqual(sum(n for entries in held().values() for _, n in entries), len(RECORDS))

    def test_a_gap_closes_when_a_matching_record_lands(self) -> None:
        from dataclasses import replace

        from pgi.corpus.coverage import GAPS, closing, open_gaps
        from pgi.corpus.records import RECORDS

        gap = next(g for g in GAPS["optics"] if "verdet" in g.terms)
        if gap in open_gaps()["optics"]:
            probe = replace(next(r for r in RECORDS if r.id.startswith("schott.")), id="schott.probe", title="Verdet constant probe")
            self.assertEqual(closing(gap, "optics", RECORDS + (probe,)), ["schott.probe"])
            self.assertNotIn(gap, open_gaps(RECORDS + (probe,))["optics"])
        # A matching record in another domain does not close the gap.
        other = replace(next(r for r in RECORDS if r.id.startswith("ame2020.")), id="ame2020.probe", title="Verdet constant probe")
        self.assertEqual(closing(gap, "optics", (other,)), [])


class OpticsTests(unittest.TestCase):
    BK7 = (("g", 4358), ("f", 4861), ("e", 5461), ("d", 5876), ("big_d", 5893), ("632_8", 6328), ("c", 6563), ("1060", 10600))

    def test_glass_lines_are_the_asd_lines(self) -> None:
        for line, label in (("he_d", "587.6"), ("hg_e", "546.1"), ("h_beta", "486.1"), ("hg_g", "435.8"), ("cd_c_prime", "643.8"), ("cd_f_prime", "480.0")):
            self.assertEqual(round(quantity(f"asd512.line.{line}").value, 1), Fraction(label), line)
        self.assertEqual(round(quantity("asd512.h_alpha.blend").value, 1), Fraction("656.3"))
        d2, d1 = quantity("asd512.line.na_d2"), quantity("asd512.line.na_d1")
        self.assertLess(d2.value + d2.uncertainty, d1.value - d1.uncertainty)

    def test_bk7_dispersion_and_abbe_number(self) -> None:
        indices = [quantity(f"schott.nbk7.n_{key}").value for key, _ in self.BK7]
        self.assertEqual(indices, sorted(indices, reverse=True))
        n_d, n_f, n_c = (quantity(f"schott.nbk7.n_{k}").value for k in ("d", "f", "c"))
        dispersion = quantity("schott.nbk7.principal_dispersion").value
        self.assertLessEqual(abs((n_f - n_c) - dispersion), Fraction(1, 10**5))
        self.assertEqual(round((n_d - 1) / dispersion, 2), quantity("schott.nbk7.abbe_d").value)

    def test_water_index_falls_with_wavelength(self) -> None:
        values = [quantity(f"iapws1997.h2o.n_{k}").value for k in ("226_5nm", "589nm", "1014nm")]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_standard_frequencies(self) -> None:
        f, lam = quantity("bipm2003.i2_633.frequency"), quantity("bipm2003.i2_633.wavelength")
        c = quantity("codata2022.c").value
        product = f.value * 1000 * lam.value / 10**15
        allowance = c * (f.uncertainty / f.value + lam.uncertainty / lam.value)
        self.assertLessEqual(abs(product - c), allowance)
        for id in ("bipm2025.sr87.frequency", "bipm2025.yb171.frequency"):
            item = quantity(id)
            self.assertIsNone(item.uncertainty)
            self.assertEqual(item.relative_uncertainty, Fraction(17, 10**17))

    def test_optics_asks_link(self) -> None:
        session = unfold(Request(ask="what are the sodium d lines", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"asd512.line.na_d1", "asd512.line.na_d2"} <= linked)
        session = unfold(Request(ask="what is the refractive index of n-bk7", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertIn("schott.nbk7.n_d", linked)
        session = unfold(Request(ask="list the optical clock frequencies", seed=1))
        linked = {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}
        self.assertTrue({"bipm2025.sr87.frequency", "bipm2025.yb171.frequency"} <= linked)


class MechanicsEmTests(unittest.TestCase):
    SITES = ("leaman2015.nist4.g", "liu2024.nim_changping.g_r", "liu2024.thu.g0")

    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_standard_gravity_and_grs80_are_stored_exact(self) -> None:
        self.assertEqual(quantity("codata2022.g_n").value, Fraction("9.80665"))
        self.assertIsNone(quantity("codata2022.g_n").uncertainty)
        self.assertEqual(quantity("grs80.a").value, 6378137)
        self.assertEqual(quantity("grs80.gm").value, 3986005 * 10**8)
        self.assertEqual(quantity("grs80.j2").value, Fraction(108263, 10**8))
        self.assertEqual(quantity("grs80.omega").value, Fraction(7292115, 10**11))

    def test_measured_sites_lie_between_grs80_equator_and_pole(self) -> None:
        gamma_e, gamma_p = quantity("grs80.gamma_e").value, quantity("grs80.gamma_p").value
        self.assertLess(gamma_e, quantity("codata2022.g_n").value)
        self.assertLess(quantity("codata2022.g_n").value, gamma_p)
        for id in self.SITES:
            item = quantity(id)
            self.assertEqual(item.unit, "uGal")
            self.assertTrue(gamma_e < item.value / 10**8 < gamma_p, id)

    def test_codata_definitional_relations(self) -> None:
        n_a, e, h = (quantity(f"codata2022.{k}").value for k in ("n_a", "e", "h"))
        low, high = quantity("codata2022.f_faraday").truncation_bounds
        self.assertTrue(low <= n_a * e < high)
        low, high = quantity("codata2022.phi_0").truncation_bounds
        self.assertTrue(low <= h / (2 * e) < high)
        mu_0, z_0, c = quantity("codata2022.mu_0"), quantity("codata2022.z_0"), quantity("codata2022.c").value
        self.assertLessEqual(abs(mu_0.value * c - z_0.value), mu_0.uncertainty * c + z_0.uncertainty)

    def test_igrf_axial_dipole_coefficient_shrinks(self) -> None:
        values = [quantity(f"igrf14.g10_{epoch}").value for epoch in ("1900", "2020", "2025")]
        self.assertTrue(all(v < 0 for v in values))
        self.assertEqual([abs(v) for v in values], sorted((abs(v) for v in values), reverse=True))
        self.assertGreater(quantity("igrf14.g10_sv_2025").value, 0)

    def test_mechanics_em_asks_link(self) -> None:
        self.assertIn("codata2022.g_n", self._linked("what is standard gravity"))
        self.assertTrue({"grs80.gamma_e", "grs80.gamma_p"} <= self._linked("what is the normal gravity in grs80"))
        self.assertTrue(set(self.SITES) <= self._linked("list the measured local g at sites"))
        self.assertTrue({"igrf14.g10_2025", "igrf14.g11_2025", "igrf14.h11_2025"} <= self._linked("what are the igrf coefficients of the earth magnetic dipole"))
        self.assertIn("codata2022.mu_b", self._linked("what is the bohr magneton"))


class EarthRotationTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_wgs84_shares_grs80_axis_and_rate_but_not_flattening(self) -> None:
        self.assertEqual(quantity("wgs84.a").value, quantity("grs80.a").value)
        self.assertEqual(quantity("wgs84.omega").value, quantity("grs80.omega").value)
        self.assertNotEqual(quantity("wgs84.inv_f").value, quantity("grs80.inv_f").value)
        self.assertEqual(quantity("wgs84.gm").value, quantity("iers2010.gm_earth").value)
        for id in ("wgs84.a", "wgs84.inv_f", "wgs84.omega", "wgs84.gm", "iers2010.era_rate", "iers2010.era_0"):
            self.assertIsNone(quantity(id).uncertainty, id)

    def test_c04_nominal_rate_is_close_to_the_era_rate(self) -> None:
        from pgi.math.trans import enclose_fexpr, pi_fexpr
        pi = enclose_fexpr(pi_fexpr())
        rate = quantity("iers2010.era_rate").value
        scale = rate * 2 * 10**12 / 86400
        low = scale * Fraction(pi.low.num, pi.low.den)
        high = scale * Fraction(pi.high.num, pi.high.den)
        printed = quantity("iersc04.omega_nominal").value
        # 2 pi times the ERA rate per 86 400 s gives 72921151.4670698 picorad/s; C04's footnote prints
        # 72921151.467064, so the two agree to about 1e-13 but not in the last printed digit.
        self.assertTrue(printed < low and high - printed < Fraction(1, 10**5))

    def test_length_of_day_rows(self) -> None:
        short, long_, last = (quantity(f"iersc04.lod_{d}") for d in ("2024_07_05", "1972_04_12", "2026_10_26"))
        self.assertLess(short.value, 0)
        self.assertLess(short.value + short.uncertainty, last.value - last.uncertainty)
        self.assertLess(last.value + last.uncertainty, long_.value - long_.uncertainty)

    def test_love_numbers(self) -> None:
        k20, k21, k22 = (quantity(f"iers2010.k2{m}").value for m in range(3))
        self.assertLess(quantity("iers2010.k20").value, quantity("iers2010.k20_anelastic").value)
        self.assertTrue(all(Fraction(29, 100) < k < Fraction(3, 10) for k in (k20, k21, k22)))
        self.assertGreater(quantity("iers2010.h2").value, k20)
        self.assertLess(quantity("iers2010.l2").value, k20)

    def test_earth_rotation_asks_link(self) -> None:
        self.assertTrue({"wgs84.a", "wgs84.inv_f", "wgs84.omega", "wgs84.gm"} <= self._linked("what are the wgs84 constants"))
        self.assertTrue({"iers2010.k20", "iers2010.h2", "iers2010.l2"} <= self._linked("what are the earth's tidal love numbers"))
        self.assertIn("iersc04.lod_2024_07_05", self._linked("what is the length of day"))
        self.assertIn("iers2010.psi_a_rate", self._linked("what is the precession constant"))


class RedshiftZPoleTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_galileo_results_are_within_gpa_level_and_consistent_with_zero(self) -> None:
        gpa = next(item for item in BOUNDS if item.id == "bound.vessot1980.redshift").upper
        for id in ("delva2018.redshift_alpha", "herrmann2018.redshift_alpha", "herrmann2018.redshift_alpha_rs"):
            item = quantity(id)
            self.assertLess(item.uncertainty, gpa, id)
            self.assertLessEqual(abs(item.value), 2 * item.uncertainty, id)

    def test_pound_snider_ratio_is_one_within_its_errors(self) -> None:
        item = quantity("pound1965.redshift_ratio")
        self.assertLessEqual(abs(item.value - 1), item.uncertainty + Fraction("0.010"))

    def test_lep_and_pdg_z_parameters(self) -> None:
        for lep, pdg_id in (("m_z", "m_z"), ("gamma_z", "gamma_z")):
            a, b = quantity(f"lep2005.{lep}"), quantity(f"pdg2026.{pdg_id}")
            self.assertLessEqual(abs(a.value - b.value), a.uncertainty + b.uncertainty, lep)
        lep_sigma, pdg_sigma = quantity("lep2005.sigma_had0"), quantity("pdg2026.sigma_had0")
        self.assertGreater(abs(lep_sigma.value - pdg_sigma.value), lep_sigma.uncertainty)
        self.assertEqual(quantity("pdg2026.a_fb0_l").value / 100, quantity("lep2005.a_fb0_l").value)
        n_nu = quantity("lep2005.n_nu")
        self.assertLess(abs(n_nu.value - 3), 2 * n_nu.uncertainty + Fraction(1, 100))

    def test_redshift_and_z_asks_link(self) -> None:
        self.assertTrue({"delva2018.redshift_alpha", "herrmann2018.redshift_alpha", "pound1965.redshift_ratio"} <= self._linked("list the gravitational redshift tests"))
        self.assertTrue({"lep2005.gamma_z", "lep2005.sigma_had0", "lep2005.r_l0", "lep2005.a_fb0_l"} <= self._linked("what are the z lineshape parameters"))


class NuclearDecayRadiiTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_ddep_and_ensdf_half_lives_agree_where_units_match(self) -> None:
        for key in ("h3", "c14", "k40", "u238", "th232"):
            a, b = quantity(f"ddep.t_half_{key}"), quantity(f"ensdf.t_half_{key}")
            self.assertEqual(a.unit, b.unit)
            self.assertLessEqual(abs(a.value - b.value), a.uncertainty + b.uncertainty, key)
        self.assertEqual(quantity("ddep.t_half_co60").unit, "a")
        self.assertEqual(quantity("ensdf.t_half_co60").unit, "d")

    def test_half_lives_span_from_minutes_to_the_age_scale(self) -> None:
        self.assertEqual(quantity("ensdf.t_half_n").unit, "s")
        ordered = [quantity(f"ddep.t_half_{k}").value for k in ("co60", "h3", "c14", "k40", "u238", "th232")]
        self.assertEqual(ordered, sorted(ordered))

    def test_charge_radii(self) -> None:
        ca40, ca48 = quantity("am2013.r_ca40"), quantity("am2013.r_ca48")
        self.assertLessEqual(abs(ca40.value - ca48.value), ca40.uncertainty + ca48.uncertainty)
        heavy = [quantity(f"am2013.r_{k}").value for k in ("pb208", "th232", "u238")]
        self.assertEqual(heavy, sorted(heavy))
        self.assertGreater(quantity("am2013.r_t").value, quantity("am2013.r_he4").value)
        old, muonic = quantity("am2013.r_p"), quantity("antognini2013.proton_charge_radius")
        self.assertGreater(old.value - old.uncertainty, muonic.value + muonic.uncertainty)

    def test_nuclear_asks_link(self) -> None:
        self.assertTrue({"ddep.t_half_c14", "ensdf.t_half_c14", "ddep.t_half_u238"} <= self._linked("list the nuclear half-lives"))
        self.assertTrue({"am2013.r_pb208", "am2013.r_ca48", "am2013.r_he4"} <= self._linked("list the nuclear charge radii"))


class EmExtrasTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_conductance_quantum_definitions(self) -> None:
        e, h = quantity("codata2022.e").value, quantity("codata2022.h").value
        low, high = quantity("codata2022.g_0").truncation_bounds
        self.assertTrue(low <= 2 * e * e / h < high)
        low, high = quantity("codata2022.g_0_inverse").truncation_bounds
        self.assertTrue(low <= h / (2 * e * e) < high)

    def test_iacs_is_one_over_58(self) -> None:
        rho = quantity("nbs1966.iacs_volume_resistivity").value
        self.assertLess(abs(rho - Fraction(100, 58)), Fraction(1, 10**4))
        self.assertIsNone(quantity("nbs1966.iacs_volume_resistivity").uncertainty)

    def test_water_permittivity_falls_with_temperature(self) -> None:
        values = [quantity(f"iapwsr897.h2o.eps_{t}k").value for t in (300, 323, 373)]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_coulomb_tests_are_null(self) -> None:
        q = quantity("williams1971.coulomb_q")
        self.assertLessEqual(abs(q.value), q.uncertainty)
        plimpton = next(item for item in BOUNDS if item.id == "bound.plimpton1936.coulomb_exponent").upper
        self.assertLess(q.value + q.uncertainty, plimpton)

    def test_em_extras_asks_link(self) -> None:
        self.assertIn("codata2022.g_0", self._linked("what is the conductance quantum"))
        self.assertIn("nbs1966.iacs_volume_resistivity", self._linked("what is the resistivity of copper"))
        self.assertTrue({"iapwsr897.h2o.eps_300k", "iapwsr897.h2o.eps_323k"} <= self._linked("what is the static permittivity of water"))
        self.assertIn("williams1971.coulomb_q", self._linked("list the coulomb's law tests"))


class CondensedExtrasTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def _c(self, prefix: str) -> tuple[Fraction, Fraction, Fraction]:
        return tuple(quantity(f"{prefix}.c{ij}").value for ij in ("11", "12", "44"))

    def test_cubic_stiffness_orderings(self) -> None:
        si, cu, dia = self._c("knowles2017.si"), self._c("knowles2017.cu"), self._c("migliori2008.diamond")
        for c11, c12, c44 in (si, cu, dia):
            self.assertGreater(c11, c12)
            self.assertGreater(c11, c44)
        # Zener anisotropy 2 c44 / (c11 - c12), as Knowles's Table 1 defines A: copper is far more anisotropic than silicon.
        zener = lambda c: 2 * c[2] / (c[0] - c[1])
        self.assertEqual(round(zener(si), 2), Fraction("1.56"))
        self.assertEqual(round(zener(cu), 2), Fraction("3.21"))
        self.assertTrue(all(d > max(a, b) for d, a, b in zip(dia, si, cu)))

    def test_aluminium_sources_share_a_unit(self) -> None:
        # 10^11 dyn/cm^2 and 10^10 N/m^2 are the same unit (1 N/m^2 = 10 dyn/cm^2).
        kamm = [quantity(f"kamm1964.al.c{ij}_0k") for ij in ("11", "12", "44")]
        vallin = [quantity(f"vallin1964.al.c{ij}_4k") for ij in ("11", "12", "44")]
        for k, v in zip(kamm, vallin):
            self.assertLess(abs(k.value - v.value) / k.value, Fraction(1, 10))
        self.assertLess(abs(quantity("kamm1964.al.theta_d").value - quantity("vallin1964.al.theta_d").value), 10)
        self.assertGreater(quantity("migliori2008.diamond.theta_d").value, 5 * quantity("kamm1964.al.theta_d").value)

    def test_superconductors_and_qhe(self) -> None:
        self.assertLess(quantity("nagamatsu2001.mgb2.tc").value, quantity("wu1987.ybco.tc").value)
        self.assertLess(quantity("wu1987.ybco.tc").value, quantity("drozdov2015.h3s.tc").value)
        for id in ("ribeiropalau2015.qhe.graphene_gaas", "ribeiropalau2015.qhe.combined_with_janssen"):
            item = quantity(id)
            self.assertLessEqual(abs(item.value), item.uncertainty, id)
        opacity = 100 - quantity("nair2008.graphene.transmittance").value
        self.assertEqual(opacity, Fraction("2.3"))

    def test_condensed_asks_link(self) -> None:
        self.assertTrue({"knowles2017.cu.c11", "knowles2017.si.c44", "migliori2008.diamond.c11"} <= self._linked("list the elastic constants"))
        self.assertTrue({"kamm1964.al.theta_d", "migliori2008.diamond.theta_d"} <= self._linked("list the debye temperatures"))
        self.assertIn("nair2008.graphene.transmittance", self._linked("what is graphene's opacity"))
        self.assertIn("ribeiropalau2015.qhe.graphene_gaas", self._linked("what is the quantum hall plateau precision"))


class FluidsHeliumTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_air_transport_values(self) -> None:
        air, n2, o2 = (quantity(f"lemmon2004.{f}.viscosity_300k_dilute").value for f in ("air", "n2", "o2"))
        self.assertTrue(n2 < air < o2)
        self.assertLess(air, quantity("lemmon2004.air.viscosity_300k_5mol").value)
        self.assertLess(quantity("lemmon2004.air.thermal_conductivity_300k_dilute").value, quantity("lemmon2004.air.thermal_conductivity_300k_5mol").value)

    def test_two_fluid_densities_add_up(self) -> None:
        # rho = rho_s + rho_n is the two-fluid model's own definition; the two tables agree to their printed digits.
        total = quantity("db1998.he4.rho_s_1_5k").value + quantity("db1998.he4.rho_n_1_5k").value
        self.assertLessEqual(abs(total - quantity("db1998.he4.rho_1_5k").value), Fraction(1, 10**5))
        self.assertLess(quantity("db1998.he4.rho_0k").value, quantity("db1998.he4.rho_lambda").value)
        self.assertLess(quantity("db1998.he4.u2_1_5k").value * 10, quantity("db1998.he4.u1_1_5k").value)
        u = [quantity(f"db1998.he4.u2_{k}").value for k in ("1_0k", "1_5k", "2_0k")]
        self.assertTrue(u[2] < u[0] < u[1])

    def test_fluids_asks_link(self) -> None:
        self.assertTrue({"lemmon2004.air.viscosity_300k_dilute"} <= self._linked("what is the viscosity of air"))
        self.assertIn("lemmon2004.air.thermal_conductivity_300k_dilute", self._linked("what is the thermal conductivity of air"))
        self.assertTrue({"db1998.he4.u2_1_5k", "db1998.he4.rho_s_1_5k"} <= self._linked("list the superfluid helium properties"))


class ClocksFrameLlrTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_records_as_printed(self) -> None:
        mu = quantity("ciufolini2016.frame_dragging_mu")
        self.assertEqual((mu.value, mu.uncertainty, mu.systematic), (Fraction(994, 1000), Fraction(2, 1000), Fraction(5, 100)))
        self.assertEqual(quantity("hofmann2018.g_dot_over_g").unit, "yr^-1")
        self.assertLess(quantity("hofmann2018.nordtvedt_eta").uncertainty, quantity("williams2004.nordtvedt_eta").uncertainty)
        self.assertLess(quantity("hofmann2018.g_dot_over_g").uncertainty, quantity("williams2004.g_dot_over_g").uncertainty)
        self.assertLess(quantity("bothwell2022.redshift_gradient").value, 0)

    def test_asks_link(self) -> None:
        self.assertTrue({"ciufolini2016.frame_dragging_mu", "gpb.frame_dragging"} <= self._linked("what is the measured frame dragging"))
        self.assertTrue({"williams2004.nordtvedt_eta", "hofmann2018.nordtvedt_eta"} <= self._linked("what is the nordtvedt parameter"))
        self.assertIn("hofmann2018.g_dot_over_g", self._linked("what is the time variation of g from lunar laser ranging"))
        self.assertIn("chou2010.height_shift", self._linked("what did the optical clock height test measure"))


class ParticleExtrasTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_lep_and_pdg_agree_where_pdg_quotes_the_fit(self) -> None:
        self.assertEqual(quantity("lep2005.r_b0").value, quantity("pdg2026.r_b0").value)
        self.assertEqual(quantity("lep2005.r_l0").value, quantity("pdg2026.r_l0").value)
        # PDG prints the heavy-flavour pole asymmetries in percent.
        self.assertEqual(quantity("lep2005.a_fb0_b").value * 100, quantity("pdg2026.a_fb0_b").value)
        self.assertEqual(quantity("lep2005.a_fb0_c").value * 100, quantity("pdg2026.a_fb0_c").value)

    def test_asymmetric_and_split_values(self) -> None:
        width = quantity("pdg2026.gamma_t")
        self.assertEqual((width.value, width.uncertainty, width.lower_uncertainty), (Fraction(142, 100), Fraction(19, 100), Fraction(15, 100)))
        self.assertEqual(quantity("cms2022.higgs_mu").value, Fraction(1002, 1000))

    def test_asks_link(self) -> None:
        self.assertTrue({"atlas2022.higgs_mu", "cms2022.higgs_mu", "pdg2026.higgs_mu.combined"} <= self._linked("what is the higgs signal strength"))
        self.assertIn("pdg2026.gamma_t", self._linked("what is the top quark width"))
        self.assertIn("lep2005.a_l_sld", self._linked("what is the sld a_l"))
        self.assertTrue({"lep2005.a_fb0_b", "lep2005.r_b0"} <= self._linked("list the z heavy flavour asymmetries"))


class OpticsExtrasTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_malitson_formula_is_normal_dispersion_over_its_range(self) -> None:
        b = [quantity(f"malitson1965.fused_silica.b{i}").value for i in (1, 2, 3)]
        c = [quantity(f"malitson1965.fused_silica.c{i}").value for i in (1, 2, 3)]

        def n2(lam: Fraction) -> Fraction:
            return 1 + sum(bi * lam**2 / (lam**2 - ci**2) for bi, ci in zip(b, c))

        grid = [Fraction(k, 100) for k in (21, 30, 40, 50, 60, 80, 100, 150, 200, 300, 371)]
        values = [n2(lam) for lam in grid]
        self.assertTrue(all(v > 1 for v in values))
        self.assertEqual(values, sorted(values, reverse=True))

    def test_air_index_rows(self) -> None:
        q = lambda k: quantity(f"nist_emt.air_n.ciddor.{k}").value
        self.assertTrue(q("20c_0rh_101325_300nm") > q("20c_0rh_101325_633nm") > q("20c_0rh_101325_1700nm"))
        self.assertTrue(q("20c_0rh_60_633nm") < q("20c_0rh_101325_633nm") < q("20c_0rh_120_633nm"))
        # Table 1 prints the Ciddor - Edlen difference at this row as 0.1 x 10^-8.
        self.assertEqual(q("20c_0rh_101325_633nm") - quantity("nist_emt.air_n.edlen.20c_0rh_101325_633nm").value, Fraction(1, 10**9))

    def test_verdet_rises_toward_the_ultraviolet(self) -> None:
        v = [quantity(f"sivaramakrishnan1956.fused_silica.verdet_{a}a").value for a in (5780, 5461, 4358, 3650)]
        self.assertEqual(v, sorted(v))

    def test_asks_link(self) -> None:
        self.assertIn("malitson1965.fused_silica.b1", self._linked("what is the refractive index of fused silica"))
        self.assertIn("nist_emt.air_n.ciddor.20c_0rh_101325_633nm", self._linked("what is the refractive index of air"))
        self.assertTrue({"turvey1993.water.verdet_643nm", "sivaramakrishnan1956.fused_silica.verdet_5461a"} <= self._linked("list the verdet constants"))
        self.assertIn("asd512.line.ne_632_8", self._linked("what is the he-ne laser line wavelength"))


class ParticleHadronsBrTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_isospin_partners_as_printed(self) -> None:
        m = lambda k: quantity(f"pdg2026.m_{k}").value
        self.assertTrue(m("sigma_minus") > m("sigma0") > m("sigma_plus"))
        self.assertGreater(m("xi_minus"), m("xi0"))
        self.assertGreater(m("d_plus"), m("d0"))
        self.assertGreater(m("b0"), m("b_plus"))

    def test_z_invisible_width_and_branching_fraction_agree(self) -> None:
        # B(Z -> invisible) is Gamma_inv / Gamma_Z by definition; PDG's two entries agree within their uncertainties.
        width, total, br = quantity("pdg2026.gamma_z_invisible"), quantity("pdg2026.gamma_z"), quantity("pdg2026.br.z_invisible")
        ratio = width.value / (total.value * 1000) * 100
        allowed = br.uncertainty + width.uncertainty / (total.value * 1000) * 100 + ratio * total.uncertainty / total.value
        self.assertLessEqual(abs(ratio - br.value), allowed)

    def test_asymmetric_tau_branching_fraction(self) -> None:
        tau = quantity("pdg2026.br.h_tautau")
        self.assertEqual((tau.value, tau.uncertainty, tau.lower_uncertainty), (Fraction(6), Fraction(8, 10), Fraction(7, 10)))

    def test_asks_link(self) -> None:
        self.assertIn("pdg2026.m_jpsi", self._linked("what is the j/psi mass"))
        self.assertIn("pdg2026.m_lambda_b", self._linked("what is the lambda_b mass"))
        self.assertTrue({"pdg2026.br.h_bb", "pdg2026.br.h_ww"} <= self._linked("list the higgs branching ratios"))
        self.assertTrue({"pdg2026.br.z_invisible", "pdg2026.gamma_z_invisible"} <= self._linked("what is the z invisible width"))


class GravEventsSkytreeTests(unittest.TestCase):
    EVENTS = ("gw170817", "gw190521", "gw190814", "gw190425", "gw200115", "gw230529", "gw231123", "gw250114")

    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_catalogue_conventions(self) -> None:
        for event in self.EVENTS:
            m1, m2, d = (quantity(f"{event}.{k}") for k in ("m1_source", "m2_source", "luminosity_distance"))
            self.assertGreaterEqual(m1.value, m2.value, event)  # m_1 is the heavier component by the catalogue's own labelling
            self.assertEqual(m1.uncertainty_kind, "90% credible interval")
            self.assertGreater(d.value - d.lower_uncertainty, 0, event)
        nearest = min(self.EVENTS, key=lambda e: quantity(f"{e}.luminosity_distance").value)
        self.assertEqual(nearest, "gw170817")

    def test_skytree_heights_agree_as_printed(self) -> None:
        clock, ranging = quantity("takamoto2020.clock_height"), quantity("takamoto2020.laser_ranging_height")
        self.assertLessEqual(abs(clock.value - ranging.value), clock.uncertainty)

    def test_asks_link(self) -> None:
        self.assertIn("takamoto2020.redshift_alpha", self._linked("what did the tokyo skytree clock test measure"))
        self.assertTrue({"gw170817.m1_source", "gw170817.luminosity_distance"} <= self._linked("what are the gw170817 masses and distance"))
        self.assertIn("gw231123.m1_source", self._linked("what is the gw231123 primary source-frame mass"))


class EmMaterialsTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_room_temperature_resistivities(self) -> None:
        rho = {m: quantity(f"{src}.{m}.rho_293k").value for src, m in (("matula1979", "ag"), ("matula1979", "cu"), ("matula1979", "au"), ("desai1984", "al"), ("desai1984", "w"))}
        self.assertEqual(sorted(rho, key=rho.get), ["ag", "cu", "au", "al", "w"])
        for src, metal, temps in (("matula1979", "cu", ("100", "273_15", "293", "300")), ("matula1979", "ag", ("273_15", "293", "300")),
                                  ("matula1979", "au", ("273_15", "293", "300")), ("desai1984", "al", ("273", "293", "300")), ("desai1984", "w", ("273", "293", "300"))):
            values = [quantity(f"{src}.{metal}.rho_{t}k").value for t in temps]
            self.assertEqual(values, sorted(values), metal)

    def test_permittivity_rows(self) -> None:
        e = lambda k: quantity(f"nist_tn1512.{k}").value
        self.assertGreater(e("sapphire.parallel_c_12_4ghz"), e("sapphire.perp_c_12_4ghz"))
        self.assertGreater(e("rutile.parallel_c_4_2ghz"), e("rutile.perp_c_4_2ghz"))
        self.assertEqual(quantity("nist_tn1512.ptfe.pp_9_93ghz").uncertainty_kind, "relative standard uncertainty")

    def test_asks_link(self) -> None:
        self.assertIn("desai1984.w.rho_293k", self._linked("what is the resistivity of tungsten"))
        self.assertIn("matula1979.ag.rho_293k", self._linked("what is the resistivity of silver"))
        self.assertIn("nist_tn1512.ptfe.pp_9_93ghz", self._linked("what is the permittivity of ptfe"))
        self.assertIn("nist_tn1512.corning7980.pp_5_07ghz", self._linked("what is the permittivity of fused silica"))


class DesiBaoTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_rows(self) -> None:
        ids = [r.id for r in QUANTITIES if r.id.startswith("desi_dr2.bao.")]
        self.assertEqual(len(ids), 19)
        self.assertEqual(quantity("desi_dr2.bao.lya.dm_rd").value_text, "38.988")

    def test_dv_is_the_definitional_combination(self) -> None:
        # D_V = (z D_M^2 D_H)^(1/3) by definition; the printed means agree with it to well inside one printed sigma.
        for key, z in (("lrg1", "0.510"), ("lrg2", "0.706"), ("lrg3_elg1", "0.934"), ("elg2", "1.321"), ("qso", "1.484"), ("lya", "2.330")):
            dv = quantity(f"desi_dr2.bao.{key}.dv_rd")
            dm, dh = quantity(f"desi_dr2.bao.{key}.dm_rd").value, quantity(f"desi_dr2.bao.{key}.dh_rd").value
            cube = Fraction(z) * dm * dm * dh
            self.assertLess(abs(float(cube) ** (1 / 3) - float(dv.value)), float(dv.uncertainty), key)

    def test_asks_link(self) -> None:
        self.assertIn("desi_dr2.bao.lrg1.dm_rd", self._linked("what are the DESI BAO distance measurements"))


class BorexinoTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_split_and_asymmetric_parts_as_printed(self) -> None:
        pp = quantity("borexino.phase2.phi_pp")
        self.assertEqual((pp.value_text, pp.uncertainty_text, pp.systematic_text, pp.systematic_lower_text), ("6.1 e10", "0.5 e10", "0.3 e10", "0.5 e10"))
        b8 = quantity("borexino.b8.phi_es")
        self.assertEqual((b8.uncertainty, b8.lower_uncertainty, b8.systematic, b8.systematic_lower), (170000, 180000, 70000, 70000))
        self.assertEqual(quantity("borexino.cno2020.phi_cno").uncertainty_kind, "asymmetric, level not stated")
        self.assertEqual(quantity("borexino.cno2022.phi_cno").uncertainty_kind, "68% interval")

    def test_flux_order_as_printed(self) -> None:
        # The measured fluxes fall in the printed order pp > 7Be > CNO > pep > 8B (no-conversion equivalent).
        order = ["phase2.phi_pp", "phase2.phi_be7", "cno2022.phi_cno", "phase2.phi_pep_hz", "b8.phi_es"]
        values = [quantity(f"borexino.{k}").value for k in order]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_asks_link(self) -> None:
        linked = self._linked("what is the borexino solar neutrino flux")
        self.assertTrue({"borexino.phase2.phi_pp", "borexino.cno2022.phi_cno"} & linked)


class BoltzmannPenningTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_printed_relative_uncertainties_match_the_concise_form(self) -> None:
        # Table 1 prints both the concise uncertainty and u_r; the two agree to the two printed figures.
        for record in QUANTITIES:
            if not record.id.startswith("codata2017.k_input."):
                continue
            rel = float(record.uncertainty / abs(record.value))
            printed = record.notes[0].split("relative standard uncertainty ")[1].rstrip(".")
            mantissa, _, exponent = printed.partition(" x 10^")
            self.assertAlmostEqual(rel / (float(mantissa) * 10 ** int(exponent)), 1, delta=0.06, msg=record.id)

    def test_codata_2017_k_rounds_to_the_defining_value(self) -> None:
        # Definitional: Table 3 fixes k by truncating the Table 2 adjusted value to 1.380 649 x 10^-23 J/K.
        adjusted, fixed = quantity("codata2017.k"), quantity("codata2022.k")
        self.assertEqual(round(adjusted.value * 10**29), fixed.value * 10**29)

    def test_penning_parts_as_printed(self) -> None:
        me = quantity("sturm2014.m_e")
        self.assertEqual((me.value_text, me.uncertainty_text, me.systematic_text), ("0.000 548 579 909 067", "0.000 000 000 000 014", "0.000 000 000 000 009"))

    def test_asks_link(self) -> None:
        self.assertIn("codata2017.k_input.nim_nist17", self._linked("johnson noise thermometry boltzmann constant"))
        self.assertIn("sturm2014.m_e", self._linked("what is the electron mass in u from a penning trap"))


class SmePoundRebkaTests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_sme_entries_are_printed_powers_of_ten(self) -> None:
        rows = [r for r in QUANTITIES if r.id.startswith("sme2026.")]
        self.assertEqual(len(rows), 18)
        for r in rows:
            self.assertTrue(r.value_text.startswith("1 e-"), r.id)
            self.assertEqual(r.uncertainty_kind, "no uncertainty printed")
        # Table S2 as printed: the neutron b~_X scale is the deepest of the three species.
        b_x = {sp: quantity(f"sme2026.matter.{sp}.b_x").value for sp in ("electron", "proton", "neutron")}
        self.assertEqual(sorted(b_x, key=b_x.get), ["neutron", "proton", "electron"])

    def test_pound_rebka_1960_as_printed(self) -> None:
        self.assertEqual(quantity("pound1960.net_shift").value_text, "-5.13 e-15")
        ratio = quantity("pound1960.redshift_ratio")
        self.assertEqual((ratio.value_text, ratio.uncertainty_text), ("1.05", "0.10"))

    def test_asks_link(self) -> None:
        self.assertTrue(any(i.startswith("sme2026.") for i in self._linked("what are the lorentz invariance limits on sme coefficients")))
        self.assertIn("pound1960.redshift_ratio", self._linked("what did pound-rebka 1960 measure"))


class NullB13Tests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_bounds_as_printed(self) -> None:
        from pgi.corpus.measured import BOUNDS
        by_id = {b.id: b for b in BOUNDS}
        klz = by_id["bound.kamlandzen2023.xe136_0vbb"]
        self.assertEqual((klz.lower_text, klz.upper_text), ("2.3 e26", ""))
        self.assertTrue(any("lower limit only" in c for c in klz.conditions))
        self.assertEqual(by_id["bound.lz2025.wimp_si_40gev"].upper_text, "2.2 e-48")
        self.assertEqual(by_id["bound.cast2017.g_agamma"].upper_text, "0.66 e-10")
        self.assertEqual(by_id["bound.eotwash2020.yukawa_range"].upper_text, "38.6")
        self.assertEqual(by_id["bound.pdg2026.n_nbar_free"].lower_text, "8.6 e7")

    def test_measured_nulls_as_printed(self) -> None:
        a = quantity("filzinger2023.alpha_dot")
        self.assertEqual((a.value_text, a.uncertainty_text, a.uncertainty_kind), ("1.8 e-19", "2.5 e-19", "uncertainty as printed, level not stated"))
        self.assertEqual(quantity("pdg2026.null.n_charge").value_text, "-0.2 e-21")

    def test_asks_link(self) -> None:
        self.assertIn("bound.kamlandzen2023.xe136_0vbb", self._linked("what is the neutrinoless double beta decay half-life limit"))
        self.assertIn("bound.cast2017.g_agamma", self._linked("what is the axion-photon coupling limit"))


class CosmoB13Tests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_s8_both_sides_kept_as_printed(self) -> None:
        planck = quantity("planck2018.s_8")
        lensing = [quantity(i) for i in ("kids2021.s8", "desy3.s8_shear", "desy3.s8_3x2pt")]
        # The printed values sit on opposite sides; both are kept and nothing is retracted.
        self.assertTrue(all(l.value < planck.value for l in lensing))
        self.assertEqual([(l.value_text, l.uncertainty_text, l.lower_text) for l in lensing],
                         [("0.759", "0.024", "0.021"), ("0.759", "0.025", "0.023"), ("0.776", "0.017", "0.017")])

    def test_eta10_rows_as_printed(self) -> None:
        self.assertEqual(quantity("cooke2018.eta10").value_text, "5.931")
        self.assertEqual(quantity("fields2020.eta10_bbn_d").uncertainty_text, "0.191")

    def test_planck_extras(self) -> None:
        self.assertEqual(quantity("planck2018.age").value_text, "13.797")
        self.assertEqual(quantity("planck2018.z_re").value_text, "7.67")
        self.assertEqual(quantity("planck2018.omega_k").value_text, "0.0007")

    def test_asks_link(self) -> None:
        self.assertIn("planck2018.age", self._linked("what is the age of the universe"))
        self.assertIn("kids2021.s8", self._linked("what is S8 from kids weak lensing"))


class QedB13Tests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_values_as_printed(self) -> None:
        rows = {i: (quantity(i).value_text, quantity(i).uncertainty_text, quantity(i).unit) for i in (
            "fee1993.ps_1s2s", "meyer2000.mu_1s2s", "patra2020.hd_plus_v0_9", "vanderwerf2025.he3_2s_transition", "vanderwerf2025.delta_r2")}
        self.assertEqual(rows["fee1993.ps_1s2s"], ("1 233 607 216.4", "3.2", "MHz"))
        self.assertEqual(rows["meyer2000.mu_1s2s"], ("2 455 528 941.0", "9.8", "MHz"))
        self.assertEqual(rows["patra2020.hd_plus_v0_9"], ("415 264 925 500.5", "1.2", "kHz"))
        self.assertEqual(rows["vanderwerf2025.he3_2s_transition"], ("192 504 914 418.96", "0.17", "kHz"))
        self.assertEqual(rows["vanderwerf2025.delta_r2"], ("1.0757", "0.0015", "fm^2"))

    def test_asks_link(self) -> None:
        self.assertIn("fee1993.ps_1s2s", self._linked("what is the positronium 1S-2S interval"))
        self.assertIn("meyer2000.mu_1s2s", self._linked("what is the muonium 1S-2S interval"))


class AstroB13Tests(unittest.TestCase):
    def _linked(self, ask: str) -> set[str]:
        session = unfold(Request(ask=ask, seed=1))
        return {claim.atom[len("record("):-1] for claim in session.claims if claim.atom.startswith("record(")}

    def test_split_stat_sys_as_printed(self) -> None:
        r0 = quantity("gravity2019.r0")
        self.assertEqual((r0.value_text, r0.uncertainty_text, r0.systematic_text), ("8178", "13", "22"))
        f = quantity("gravity2018.f_redshift")
        self.assertEqual((f.value_text, f.uncertainty_text, f.systematic_text), ("0.90", "0.09", "0.15"))

    def test_eht_diameters(self) -> None:
        self.assertEqual(quantity("eht2019.m87_ring_diameter").value_text, "42")
        self.assertEqual(quantity("eht2022.sgra_ring_diameter").uncertainty_kind, "68% interval")
        self.assertEqual(quantity("eht2022.sgra_shadow_diameter").uncertainty_text, "7.0")

    def test_both_gravity_editions_kept(self) -> None:
        self.assertEqual({quantity(i).value_text for i in ("gravity2019.m_bh", "gravity2022.m_bh")}, {"4.152 e6", "4.297 e6"})

    def test_asks_link(self) -> None:
        self.assertIn("eht2022.sgra_shadow_diameter", self._linked("what is the sgr a* shadow diameter"))


class FluidsB14Tests(unittest.TestCase):
    def test_values_as_printed(self) -> None:
        self.assertEqual(quantity("jones1984.air_eta_20c_1atm").value_text, "181.94")
        self.assertEqual((quantity("berg2012.eta_ar").value_text, quantity("berg2012.eta_ar").uncertainty_text), ("22.5666", "0.0060"))
        self.assertEqual(quantity("teos10.s_so").value_text, "35.165 04")

    def test_pressure_raises_air_viscosity_as_printed(self) -> None:
        # The two 20.00 C points from the same table, 1.00 atm and 34.97 atm.
        self.assertLess(quantity("jones1984.air_eta_20c_1atm").value, quantity("jones1984.air_eta_20c_35atm").value)

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

    def test_mercury_asks_link_both_eras(self) -> None:
        text = unfold(Request(ask="what is the mercury perihelion residual", seed=1)).text(lod=2)
        self.assertIn("record(mercury.clemence1947.residual)", text)
        self.assertIn("record(mercury.park2017.total_precession)", text)
        self.assertIn("record(mercury.epm2011.extra_perihelion_precession)", text)
        self.assertIn("575.3100", text)
        self.assertIn("-0.020", text)

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
