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
