"""Sourced numbers for the board.

Each quantity is copied from its source as the source prints it. The text is
kept, and the rational is parsed from that text. Nothing here is rounded,
converted, or computed. An exact defined value is stored as an exact rational.
A measured value is stored as a rational with the uncertainty the source
quotes, under the name the source gives that uncertainty.

A quantity is data. It is not a theorem, and it is not derived by this system.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

RETRIEVED = "2026-11-25"

UNCERTAINTY_KINDS = frozenset(
    {
        "exact",
        "standard uncertainty",
        "asymmetric standard uncertainty",
        "uncertainty at CL = 90%",
        "probable error",
        "90% credible interval",
        "uncertainty as printed, level not stated",
        "3 sigma",
        "68% interval",
        "statistical and systematic, printed separately",
    }
)
_ASYMMETRIC_KINDS = frozenset({"asymmetric standard uncertainty", "90% credible interval", "68% interval"})
_SPLIT_KIND = "statistical and systematic, printed separately"


@dataclass(frozen=True)
class Quantity:
    id: str
    name: str
    symbol: str
    value_text: str
    uncertainty_text: str
    unit: str
    uncertainty_kind: str
    source: str
    edition: str
    url: str
    retrieved_from: str
    retrieved: str
    keys: tuple[str, ...]
    phrases: tuple[str, ...]
    notes: tuple[str, ...] = ()
    lower_text: str = ""
    record: bool = True
    printed: str = ""
    forbids: tuple[str, ...] = ()
    systematic_text: str = ""
    systematic_lower_text: str = ""

    @property
    def exact(self) -> bool:
        return self.uncertainty_kind == "exact"

    @property
    def value(self) -> Fraction:
        return parse_decimal(self.value_text)

    @property
    def uncertainty(self) -> Fraction | None:
        if self.exact:
            return None
        return parse_decimal(self.uncertainty_text)

    @property
    def lower_uncertainty(self) -> Fraction | None:
        if self.exact:
            return None
        if self.lower_text:
            return parse_decimal(self.lower_text)
        return self.uncertainty

    @property
    def systematic(self) -> Fraction | None:
        return parse_decimal(self.systematic_text) if self.systematic_text else None

    @property
    def systematic_lower(self) -> Fraction | None:
        if not self.systematic_text:
            return None
        return parse_decimal(self.systematic_lower_text or self.systematic_text)


def parse_decimal(text: str) -> Fraction:
    """Read a decimal as printed, with spaces between digit groups and an
    optional e exponent, and return the exact rational it names."""
    cleaned = text.replace(" ", "").replace("\u2212", "-").lstrip("+")
    if not cleaned or "..." in cleaned or "(" in cleaned:
        raise ValueError(f"not an exact decimal: {text!r}")
    return Fraction(cleaned)


def parse_concise(text: str) -> tuple[Fraction, Fraction]:
    """Read the concise form `0.1180(9)` or `1.166 378 5(6) e-5`: the digits in
    parentheses are the uncertainty in the last printed places."""
    cleaned = text.replace(" ", "").replace("\u2212", "-")
    head, _, rest = cleaned.partition("(")
    digits, _, tail = rest.partition(")")
    if not head or not digits.isdigit() or (tail and not tail.startswith("e")):
        raise ValueError(f"not a concise value: {text!r}")
    places = len(head.partition(".")[2])
    scale = Fraction(10) ** int(tail[1:]) if tail else Fraction(1)
    return Fraction(head) * scale, Fraction(int(digits), 10**places) * scale


CODATA_2022_SOURCE = (
    "P. J. Mohr, D. B. Newell, B. N. Taylor, and E. Tiesinga, CODATA recommended values of the fundamental "
    "physical constants: 2022, Rev. Mod. Phys. 97, 025002 (2025), doi:10.1103/RevModPhys.97.025002, "
    "arXiv:2409.03787. Values as served by the NIST Reference on Constants, Units, and Uncertainty."
)
CODATA_2022_EDITION = "CODATA 2022 adjustment"
CODATA_2022_TABLE = "https://physics.nist.gov/cuu/Constants/Table/allascii.txt"


def _codata(
    id: str,
    name: str,
    symbol: str,
    value_text: str,
    uncertainty_text: str,
    unit: str,
    code: str,
    *,
    keys: tuple[str, ...],
    phrases: tuple[str, ...],
    notes: tuple[str, ...] = (),
    record: bool = True,
) -> Quantity:
    exact = uncertainty_text == "(exact)"
    return Quantity(
        id=id,
        name=name,
        symbol=symbol,
        value_text=value_text,
        uncertainty_text="exact" if exact else uncertainty_text,
        unit=unit,
        uncertainty_kind="exact" if exact else "standard uncertainty",
        source=CODATA_2022_SOURCE,
        edition=CODATA_2022_EDITION,
        url=f"https://physics.nist.gov/cgi-bin/cuu/Value?{code}",
        retrieved_from=CODATA_2022_TABLE,
        retrieved=RETRIEVED,
        keys=keys,
        phrases=phrases,
        notes=notes,
        record=record,
    )


_SI_DEFINING = (
    "This is one of the seven defining constants of the 2019 SI. Its numerical value is fixed by definition.",
)

CODATA_2022: tuple[Quantity, ...] = (
    _codata('codata2022.delta_nu_cs', 'hyperfine transition frequency of Cs-133', 'Delta nu_Cs', '9 192 631 770', '(exact)', 'Hz', 'nucs', keys=('caesium', 'cesium'), phrases=('hyperfine transition frequency', 'caesium frequency'), notes=_SI_DEFINING),
    _codata('codata2022.c', 'speed of light in vacuum', 'c', '299 792 458', '(exact)', 'm s^-1', 'c', keys=(), phrases=(), notes=_SI_DEFINING + ("The board record for this constant is anchor.c_si.",), record=False),
    _codata('codata2022.h', 'Planck constant', 'h', '6.626 070 15 e-34', '(exact)', 'J Hz^-1', 'h', keys=(), phrases=('planck constant',), notes=_SI_DEFINING),
    _codata('codata2022.e', 'elementary charge', 'e', '1.602 176 634 e-19', '(exact)', 'C', 'e', keys=(), phrases=('elementary charge',), notes=_SI_DEFINING),
    _codata('codata2022.k', 'Boltzmann constant', 'k', '1.380 649 e-23', '(exact)', 'J K^-1', 'k', keys=('boltzmann',), phrases=('boltzmann constant',), notes=_SI_DEFINING),
    _codata('codata2022.n_a', 'Avogadro constant', 'N_A', '6.022 140 76 e23', '(exact)', 'mol^-1', 'na', keys=('avogadro',), phrases=('avogadro constant',), notes=_SI_DEFINING),
    _codata('codata2022.k_cd', 'luminous efficacy', 'K_cd', '683', '(exact)', 'lm W^-1', 'kcd', keys=(), phrases=('luminous efficacy',), notes=_SI_DEFINING),
    _codata('codata2022.g', 'Newtonian constant of gravitation', 'G', '6.674 30 e-11', '0.000 15 e-11', 'm^3 kg^-1 s^-2', 'bg', keys=(), phrases=('gravitational constant', 'newtonian constant of gravitation', 'constant of gravitation')),
    _codata('codata2022.alpha', 'fine-structure constant', 'alpha', '7.297 352 5643 e-3', '0.000 000 0011 e-3', '', 'alph', keys=(), phrases=('fine-structure constant', 'fine structure constant')),
    _codata('codata2022.alpha_inverse', 'inverse fine-structure constant', '1/alpha', '137.035 999 177', '0.000 000 021', '', 'alphinv', keys=(), phrases=('inverse fine-structure constant', 'inverse fine structure constant')),
    _codata('codata2022.m_e', 'electron mass', 'm_e', '9.109 383 7139 e-31', '0.000 000 0028 e-31', 'kg', 'me', keys=(), phrases=('electron mass', 'mass of the electron')),
    _codata('codata2022.m_p', 'proton mass', 'm_p', '1.672 621 925 95 e-27', '0.000 000 000 52 e-27', 'kg', 'mp', keys=(), phrases=('proton mass', 'mass of the proton')),
    _codata('codata2022.m_n', 'neutron mass', 'm_n', '1.674 927 500 56 e-27', '0.000 000 000 85 e-27', 'kg', 'mn', keys=(), phrases=('neutron mass', 'mass of the neutron')),
    _codata('codata2022.m_e_c2_mev', 'electron mass energy equivalent in MeV', 'm_e c^2', '0.510 998 950 69', '0.000 000 000 16', 'MeV', 'mec2mev', keys=(), phrases=('electron mass',)),
    _codata('codata2022.m_p_c2_mev', 'proton mass energy equivalent in MeV', 'm_p c^2', '938.272 089 43', '0.000 000 29', 'MeV', 'mpc2mev', keys=(), phrases=('proton mass',)),
    _codata('codata2022.m_n_c2_mev', 'neutron mass energy equivalent in MeV', 'm_n c^2', '939.565 421 94', '0.000 000 48', 'MeV', 'mnc2mev', keys=(), phrases=('neutron mass',)),
    _codata('codata2022.m_p_over_m_e', 'proton-electron mass ratio', 'm_p/m_e', '1836.152 673 426', '0.000 000 032', '', 'mpsme', keys=(), phrases=('proton-electron mass ratio',)),
    _codata('codata2022.r_inf', 'Rydberg constant', 'R_inf', '10 973 731.568 157', '0.000 012', 'm^-1', 'ryd', keys=('rydberg',), phrases=('rydberg constant',)),
    _codata('codata2022.a_0', 'Bohr radius', 'a_0', '5.291 772 105 44 e-11', '0.000 000 000 82 e-11', 'm', 'bohrrada0', keys=(), phrases=('bohr radius',)),
    _codata('codata2022.a_e', 'electron magnetic moment anomaly', 'a_e', '1.159 652 180 46 e-3', '0.000 000 000 18 e-3', '', 'ae', keys=(), phrases=('electron magnetic moment anomaly', 'electron anomaly')),
    _codata('codata2022.a_mu', 'muon magnetic moment anomaly', 'a_mu', '1.165 920 62 e-3', '0.000 000 41 e-3', '', 'amu', keys=(), phrases=('muon magnetic moment anomaly', 'muon anomaly'), notes=("CODATA 2022 has a cutoff of 31 December 2022. It predates the 2023 and 2025 Fermilab results.",)),
    _codata('codata2022.r_p', 'proton rms charge radius', 'r_p', '8.4075 e-16', '0.0064 e-16', 'm', 'rp', keys=(), phrases=('proton charge radius', 'proton radius', 'proton rms charge radius')),
    _codata('codata2022.ryd_hc_ev', 'Rydberg constant times hc in eV', 'R_inf hc', '13.605 693 122 990', '0.000 000 000 015', 'eV', 'rydhcev', keys=(), phrases=('rydberg energy', 'rydberg constant times hc')),
    _codata('codata2022.mu_0', 'vacuum magnetic permeability', 'mu_0', '1.256 637 061 27 e-6', '0.000 000 000 20 e-6', 'N A^-2', 'mu0', keys=('permeability',), phrases=('vacuum magnetic permeability', 'magnetic constant'), notes=("Since the 2019 SI, mu_0 is measured. It is no longer fixed at 4 pi x 10^-7 N A^-2.",)),
    _codata('codata2022.epsilon_0', 'vacuum electric permittivity', 'epsilon_0', '8.854 187 8188 e-12', '0.000 000 0014 e-12', 'F m^-1', 'ep0', keys=('permittivity',), phrases=('vacuum electric permittivity', 'electric constant'), notes=("Since the 2019 SI, epsilon_0 is measured. It is no longer exact.",)),
    _codata('codata2022.g_f', 'Fermi coupling constant', 'G_F/(hbar c)^3', '1.166 3787 e-5', '0.000 0006 e-5', 'GeV^-2', 'gf', keys=(), phrases=('fermi coupling constant', 'fermi constant')),
)

PDG_2026_SOURCE = (
    "F. Takahashi et al. (Particle Data Group), Review of Particle Physics, Int. J. Mod. Phys. A 41, 2630011 (2026)."
)
PDG_2026_EDITION = "PDG 2026 Review of Particle Physics"
PDG_2026_API = "https://pypi.org/project/pdg/2026.0/"
PDG_2026_CONSTANTS = "https://pdg.lbl.gov/2026/reviews/rpp2026-rev-phys-constants.pdf"
PDG_2026_CKM = "https://pdg.lbl.gov/2026/reviews/rpp2026-rev-ckm-matrix.pdf"

_API_NOTE = "Read from the PDG API database shipped as the pdg Python package 2026.0, data release of 2026-05-30, summary-table value."


def _pdg(
    id: str,
    name: str,
    symbol: str,
    value_text: str,
    uncertainty_text: str,
    unit: str,
    *,
    node: str = "",
    url: str = "",
    retrieved_from: str = PDG_2026_API,
    kind: str = "standard uncertainty",
    lower_text: str = "",
    printed: str = "",
    keys: tuple[str, ...] = (),
    phrases: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
) -> Quantity:
    return Quantity(
        id=id,
        name=name,
        symbol=symbol,
        value_text=value_text,
        uncertainty_text=uncertainty_text,
        unit=unit,
        uncertainty_kind=kind,
        source=PDG_2026_SOURCE,
        edition=PDG_2026_EDITION,
        url=url or f"https://pdglive.lbl.gov/DataBlock.action?node={node}",
        retrieved_from=retrieved_from,
        retrieved=RETRIEVED,
        keys=keys,
        phrases=phrases,
        notes=notes,
        lower_text=lower_text,
        printed=printed,
    )


_QUARK_SCHEME_LIGHT = "PDG states the u, d, and s masses as MSbar current-quark masses normalized at mu = 2 GeV."
_QUARK_CL = "PDG prints this evaluation with (CL = 90%). The interval is not a one-standard-deviation uncertainty."
_TABLE_NOTE = "PDG Table 1.1, Physical Constants, revised May 2026 by D. Robinson and P. A. Zyla. This entry is in the set that comes from the Particle Data Group."
_CKM_FIT = "PDG review 12, CKM Quark-Mixing Matrix, revised March 2026 by A. Ceccucci, Z. Ligeti, and Y. Sakai: the global fit imposing three-generation unitarity, Eq. (12.26) and Eq. (12.27)."

PDG_2026: tuple[Quantity, ...] = (
    _pdg("pdg2026.m_w", "W boson mass", "m_W", "80.3625", "0.0077", "GeV", node="S043M", phrases=("w boson", "w-boson", "mass of the w"), notes=("PDG evaluation, from the LHC-Tevatron M_W Working Group.", _API_NOTE)),
    _pdg("pdg2026.m_z", "Z boson mass", "m_Z", "91.1879", "0.0020", "GeV", node="S044M", phrases=("z boson", "z-boson", "mass of the z"), notes=(_API_NOTE,)),
    _pdg("pdg2026.m_w_over_m_z", "W/Z mass ratio", "m_W/m_Z", "0.88136", "0.00015", "", node="S043MR", phrases=("w/z mass ratio",), notes=("PDG average of the measured ratio. It is not computed from the two masses.", _API_NOTE)),
    _pdg("pdg2026.m_h", "Higgs boson mass", "m_H", "125.13", "0.11", "GeV", node="S126M", keys=("higgs",), phrases=("higgs mass",), notes=("PDG average. The error includes a scale factor of 1.5.", _API_NOTE)),
    _pdg("pdg2026.m_t", "top quark mass from direct measurements", "m_t", "172.60", "0.27", "GeV", node="Q007TP", phrases=("top quark", "top-quark"), notes=("PDG average of direct measurements. The error includes a scale factor of 1.5. PDG warns that the relation of this mass to a field-theory mass scheme is hard to quantify.", _API_NOTE)),
    _pdg("pdg2026.m_e", "electron mass", "m_e", "0.51099895069", "0.00000000016", "MeV", node="S003M", phrases=("electron mass", "mass of the electron"), notes=(_API_NOTE,)),
    _pdg("pdg2026.m_mu", "muon mass", "m_mu", "105.6583755", "0.0000023", "MeV", node="S004M", keys=("muon",), phrases=("muon mass",), notes=(_API_NOTE,)),
    _pdg("pdg2026.m_tau", "tau lepton mass", "m_tau", "1776.93", "0.09", "MeV", node="S035M", phrases=("tau mass", "tau lepton"), notes=(_API_NOTE,)),
    _pdg("pdg2026.m_u", "u quark mass", "m_u", "2.16", "0.07", "MeV", node="Q002M", kind="uncertainty at CL = 90%", phrases=("up quark", "u-quark", "light quark"), notes=(_QUARK_SCHEME_LIGHT, _QUARK_CL, _API_NOTE)),
    _pdg("pdg2026.m_d", "d quark mass", "m_d", "4.70", "0.07", "MeV", node="Q001M", kind="uncertainty at CL = 90%", phrases=("down quark", "d-quark", "light quark"), notes=(_QUARK_SCHEME_LIGHT, _QUARK_CL, _API_NOTE)),
    _pdg("pdg2026.m_s", "s quark mass", "m_s", "92.9", "0.7", "MeV", node="Q003M", kind="uncertainty at CL = 90%", phrases=("strange quark", "s-quark", "light quark"), notes=(_QUARK_SCHEME_LIGHT, _QUARK_CL, _API_NOTE)),
    _pdg("pdg2026.m_c", "c quark mass", "m_c(m_c)", "1.2729", "0.0045", "GeV", node="Q004M", kind="uncertainty at CL = 90%", phrases=("charm quark", "c-quark"), notes=("PDG states this as the MSbar running mass at mu = m_c.", _QUARK_CL, _API_NOTE)),
    _pdg("pdg2026.m_b", "b quark mass", "m_b(m_b)", "4.186", "0.006", "GeV", node="Q005M", kind="uncertainty at CL = 90%", phrases=("bottom quark", "b-quark"), notes=("PDG states this as the MSbar running mass at mu = m_b.", _QUARK_CL, _API_NOTE)),
    _pdg("pdg2026.alpha_s_mz", "strong coupling constant at m_Z", "alpha_s(m_Z)", "0.1180", "0.0009", "", url=PDG_2026_CONSTANTS, retrieved_from=PDG_2026_CONSTANTS, printed="0.1180(9)", phrases=("strong coupling",), notes=(_TABLE_NOTE,)),
    _pdg("pdg2026.g_f", "Fermi coupling constant", "G_F/(hbar c)^3", "1.166 378 5 e-5", "0.000 000 6 e-5", "GeV^-2", url=PDG_2026_CONSTANTS, retrieved_from=PDG_2026_CONSTANTS, printed="1.166 378 5(6) e-5", phrases=("fermi coupling constant", "fermi constant"), notes=(_TABLE_NOTE,)),
    _pdg("pdg2026.sin2_theta_w", "weak-mixing angle, MSbar at m_Z", "sin^2 theta_W(m_Z) MSbar", "0.231 22", "0.000 06", "", url=PDG_2026_CONSTANTS, retrieved_from=PDG_2026_CONSTANTS, printed="0.231 22(6)", phrases=("weak mixing angle", "weak-mixing angle", "sin2 theta", "sin^2 theta"), notes=(_TABLE_NOTE, "PDG notes that it is derived from the effective angle, sin^2 theta_eff = 0.23154(6). That effective value is not stored here.")),
    _pdg("pdg2026.ckm.lambda", "Wolfenstein parameter lambda", "lambda", "0.22517", "0.00068", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, keys=("ckm", "wolfenstein"), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.a", "Wolfenstein parameter A", "A", "0.826", "0.017", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, kind="asymmetric standard uncertainty", lower_text="0.015", keys=("ckm", "wolfenstein"), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.rho_bar", "Wolfenstein parameter rho-bar", "rho_bar", "0.1576", "0.0092", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, kind="asymmetric standard uncertainty", lower_text="0.0091", keys=("ckm", "wolfenstein"), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.eta_bar", "Wolfenstein parameter eta-bar", "eta_bar", "0.3556", "0.0071", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, kind="asymmetric standard uncertainty", lower_text="0.0069", keys=("ckm", "wolfenstein"), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.v_ud", "CKM magnitude |V_ud|", "|V_ud|", "0.97431", "0.00016", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, keys=("ckm",), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.v_us", "CKM magnitude |V_us|", "|V_us|", "0.22517", "0.00068", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, keys=("ckm",), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.v_ub", "CKM magnitude |V_ub|", "|V_ub|", "0.003763", "0.000088", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, kind="asymmetric standard uncertainty", lower_text="0.000083", keys=("ckm",), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.v_cd", "CKM magnitude |V_cd|", "|V_cd|", "0.22503", "0.00068", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, keys=("ckm",), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.v_cs", "CKM magnitude |V_cs|", "|V_cs|", "0.97345", "0.00016", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, keys=("ckm",), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.v_cb", "CKM magnitude |V_cb|", "|V_cb|", "0.04189", "0.00081", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, kind="asymmetric standard uncertainty", lower_text="0.00069", keys=("ckm",), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.v_td", "CKM magnitude |V_td|", "|V_td|", "0.00863", "0.00019", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, kind="asymmetric standard uncertainty", lower_text="0.00017", keys=("ckm",), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.v_ts", "CKM magnitude |V_ts|", "|V_ts|", "0.04117", "0.00079", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, kind="asymmetric standard uncertainty", lower_text="0.00068", keys=("ckm",), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.v_tb", "CKM magnitude |V_tb|", "|V_tb|", "0.999115", "0.000029", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, kind="asymmetric standard uncertainty", lower_text="0.000034", keys=("ckm",), notes=(_CKM_FIT,)),
    _pdg("pdg2026.ckm.jarlskog", "Jarlskog invariant", "J", "3.16 e-5", "0.13 e-5", "", url=PDG_2026_CKM, retrieved_from=PDG_2026_CKM, kind="asymmetric standard uncertainty", lower_text="0.11 e-5", keys=("ckm", "jarlskog"), notes=("PDG review 12, CKM Quark-Mixing Matrix, revised March 2026, from the same global fit.",)),
)

CLEMENCE_1947_SOURCE = (
    "G. M. Clemence, The Relativity Effect in Planetary Motions, Rev. Mod. Phys. 19, 361-364 (1947), "
    "doi:10.1103/RevModPhys.19.361, Table II."
)
CLEMENCE_1947_EDITION = "Rev. Mod. Phys. 19 (1947), October issue"
CLEMENCE_1947_URL = "https://doi.org/10.1103/RevModPhys.19.361"
CLEMENCE_1947_SCAN = "https://alternativephysics.org/book/documents/Clemence-RevModPhys.19.361.pdf"

_CLEMENCE_PE = (
    "Clemence's uncertainties are probable errors in his own sense: a range that contains the true value with probability one half, "
    "widened by his judgment of the largest systematic error. They are not standard uncertainties, and no conversion is stored.",
    "Clemence notes that de Sitter in 1938 estimated the probable error attached to Mercury fifty percent larger.",
    "The page text was read from a scan of the journal pages, because the APS page is behind a login.",
)


def _clemence(id: str, name: str, value_text: str, pe_text: str, notes: tuple[str, ...], **extra) -> Quantity:
    return Quantity(
        id=id,
        name=name,
        symbol="dot(omega) Mercury",
        value_text=value_text,
        uncertainty_text=pe_text,
        unit="arcsec per Julian century",
        uncertainty_kind="probable error",
        source=CLEMENCE_1947_SOURCE,
        edition=CLEMENCE_1947_EDITION,
        url=CLEMENCE_1947_URL,
        retrieved_from=CLEMENCE_1947_SCAN,
        retrieved=RETRIEVED,
        keys=("mercury", "perihelion", "clemence"),
        phrases=("perihelion of mercury", "mercury perihelion"),
        notes=notes + _CLEMENCE_PE,
        **extra,
    )


MERCURY: tuple[Quantity, ...] = (
    _clemence(
        "mercury.clemence1947.observed",
        "observed motion of Mercury's perihelion at 1850, referred to the moving equinox",
        "5599.74",
        "0.41",
        ("From meridian observations 1765 to 1937 and 17 transits 1799 to 1940. A Julian century is 36,525 mean solar days.",),
    ),
    _clemence(
        "mercury.clemence1947.computed",
        "sum of general precession and the Newtonian planetary and solar-oblateness contributions, without relativity",
        "5557.18",
        "0.85",
        ("General precession is 5025.645 +- 0.50 of that sum, after Oort. The planetary terms use Doolittle's calculation with Clemence's masses.",),
    ),
    _clemence(
        "mercury.clemence1947.residual",
        "observed minus computed motion of Mercury's perihelion, the residual that Newtonian theory leaves",
        "42.56",
        "0.94",
        (
            "This is Clemence's line Difference: observed motion minus the sum of every non-relativistic contribution.",
            "Clemence prints a relativity effect beside it. That theory value is not stored here; only the observed residual is admitted.",
        ),
        forbids=("law(newtonian_perturbations_explain_mercury_perihelion)",),
    ),
)

GWTC1_SOURCE = (
    "B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration), GWTC-1: A Gravitational-Wave Transient Catalog "
    "of Compact Binary Mergers Observed by LIGO and Virgo during the First and Second Observing Runs, Phys. Rev. X 9, 031040 (2019), "
    "arXiv:1811.12907, Table III."
)
GWTC1_EDITION = "GWTC-1-confident, GW150914 version 3"
GWTC1_EVENT = "https://gwosc.org/eventapi/json/GWTC-1-confident/GW150914/v3/"
_GWTC1_NOTE = (
    "GWTC-1 Table III reports the median with a 90% credible interval that includes statistical errors and the systematic error from averaging two waveform models.",
    "The same numbers were read from the GWOSC event API and checked against Table III of arXiv:1811.12907.",
)


def _gw150914(id: str, name: str, symbol: str, value_text: str, upper: str, lower: str, unit: str, notes: tuple[str, ...] = ()) -> Quantity:
    return Quantity(
        id=id,
        name=name,
        symbol=symbol,
        value_text=value_text,
        uncertainty_text=upper,
        lower_text=lower,
        unit=unit,
        uncertainty_kind="90% credible interval",
        source=GWTC1_SOURCE,
        edition=GWTC1_EDITION,
        url="https://doi.org/10.1103/PhysRevX.9.031040",
        retrieved_from=GWTC1_EVENT,
        retrieved=RETRIEVED,
        keys=("gw150914",),
        phrases=("first gravitational wave", "first gravitational-wave"),
        notes=notes + _GWTC1_NOTE,
    )


GW150914: tuple[Quantity, ...] = (
    _gw150914("gw150914.m1_source", "GW150914 primary source-frame mass", "m_1", "35.6", "4.7", "3.1", "M_sun"),
    _gw150914("gw150914.m2_source", "GW150914 secondary source-frame mass", "m_2", "30.6", "3.0", "4.4", "M_sun"),
    _gw150914("gw150914.chirp_mass_source", "GW150914 source-frame chirp mass", "M_chirp", "28.6", "1.7", "1.5", "M_sun"),
    _gw150914("gw150914.final_mass_source", "GW150914 final source-frame mass", "M_f", "63.1", "3.4", "3.0", "M_sun"),
    _gw150914("gw150914.final_spin", "GW150914 final dimensionless spin", "a_f", "0.69", "0.05", "0.04", ""),
    _gw150914("gw150914.radiated_energy", "GW150914 radiated energy", "E_rad", "3.1", "0.4", "0.4", "M_sun c^2", notes=("Read from Table III; the GWOSC event API does not list it.",)),
    _gw150914("gw150914.chi_eff", "GW150914 effective aligned spin", "chi_eff", "-0.01", "0.12", "0.13", ""),
    _gw150914("gw150914.luminosity_distance", "GW150914 luminosity distance", "d_L", "440", "150", "170", "Mpc"),
    _gw150914("gw150914.redshift", "GW150914 redshift", "z", "0.09", "0.03", "0.03", "", notes=("GWTC-1 computes this redshift from the luminosity distance under its assumed cosmology.",)),
)

def _q(
    id: str,
    name: str,
    symbol: str,
    value_text: str,
    uncertainty_text: str,
    unit: str,
    *,
    kind: str,
    source: str,
    edition: str,
    url: str,
    retrieved_from: str,
    keys: tuple[str, ...] = (),
    phrases: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
    lower_text: str = "",
    printed: str = "",
    forbids: tuple[str, ...] = (),
    systematic_text: str = "",
    systematic_lower_text: str = "",
) -> Quantity:
    return Quantity(
        id=id,
        name=name,
        symbol=symbol,
        value_text=value_text,
        uncertainty_text=uncertainty_text,
        unit=unit,
        uncertainty_kind=kind,
        source=source,
        edition=edition,
        url=url,
        retrieved_from=retrieved_from,
        retrieved=RETRIEVED,
        keys=keys,
        phrases=phrases,
        notes=notes,
        lower_text=lower_text,
        printed=printed,
        forbids=forbids,
        systematic_text=systematic_text,
        systematic_lower_text=systematic_lower_text,
    )


PARK_2017_SOURCE = (
    "R. S. Park, W. M. Folkner, A. S. Konopliv, J. G. Williams, D. E. Smith, and M. T. Zuber, Precession of Mercury's "
    "Perihelion from Ranging to the MESSENGER Spacecraft, Astron. J. 153, 121 (2017), doi:10.3847/1538-3881/aa5be2."
)
PARK_2017_EDITION = "AJ 153:121 (2017 March)"
PARK_2017_URL = "https://doi.org/10.3847/1538-3881/aa5be2"
PARK_2017_PDF = "https://iopscience.iop.org/article/10.3847/1538-3881/aa5be2/pdf"
_PARK_LEVEL = "The paper prints this uncertainty without naming a confidence level, so none is assigned here."
_PARK_GAMMA = "The fit holds gamma as a considered parameter with the Cassini a priori uncertainty 2.3 e-5, and the solar angular momentum from helioseismology."

PITJEVA_2013_SOURCE = (
    "E. V. Pitjeva and N. P. Pitjev, Relativistic effects and dark matter in the Solar system from observations of planets "
    "and spacecraft, Mon. Not. R. Astron. Soc. 432, 3431-3437 (2013), doi:10.1093/mnras/stt695, arXiv:1306.3043."
)
PITJEVA_2013_EDITION = "EPM2011 ephemeris, MNRAS 432 (2013)"
PITJEVA_2013_URL = "https://doi.org/10.1093/mnras/stt695"
PITJEVA_2013_PDF = "https://arxiv.org/pdf/1306.3043"

BERTOTTI_2003_SOURCE = (
    "B. Bertotti, L. Iess, and P. Tortora, A test of general relativity using radio links with the Cassini spacecraft, "
    "Nature 425, 374-376 (2003), doi:10.1038/nature01997."
)

MERCURY_MODERN: tuple[Quantity, ...] = (
    _q(
        "mercury.park2017.total_precession",
        "total precession rate of Mercury's perihelion in the frame of Mercury's mean orbit plane",
        "dot(omega) Mercury",
        "575.3100",
        "0.0015",
        "arcsec per Julian century",
        kind="uncertainty as printed, level not stated",
        source=PARK_2017_SOURCE + " Table 3, Total.",
        edition=PARK_2017_EDITION,
        url=PARK_2017_URL,
        retrieved_from=PARK_2017_PDF,
        keys=("mercury", "perihelion", "messenger"),
        phrases=("perihelion of mercury", "mercury perihelion"),
        notes=(
            "The rate comes from JPL's ephemeris fit that includes MESSENGER ranging, 2011 March to 2014 August.",
            "It is measured along Mercury's mean orbit plane, not against the moving equinox, so it does not contain general precession and is not comparable to Clemence's 5599.74.",
            "Table 3 splits the total into contributions computed in that fit, including relativistic terms. Those computed terms are not stored.",
            "The uncertainty is the root-sum-square of the Table 3 uncertainties, as the paper states.",
            _PARK_LEVEL,
        ),
    ),
    _q(
        "mercury.park2017.beta_minus_1",
        "PPN parameter beta minus one from MESSENGER ranging",
        "beta - 1",
        "-2.7 e-5",
        "3.9 e-5",
        "",
        kind="uncertainty as printed, level not stated",
        source=PARK_2017_SOURCE + " Abstract and Section 5.",
        edition=PARK_2017_EDITION,
        url=PARK_2017_URL,
        retrieved_from=PARK_2017_PDF,
        keys=("mercury", "messenger", "ppn"),
        phrases=("ppn beta", "post-newtonian beta"),
        notes=(
            "The abstract and the conclusions print (beta - 1) = (-2.7 +- 3.9) x 10^-5. Table 1 of the same paper prints -2.6 +- 3.9 in units of 10^-5. The abstract value is stored and the difference is recorded here.",
            _PARK_GAMMA,
            _PARK_LEVEL,
        ),
    ),
    _q(
        "mercury.park2017.solar_j2",
        "solar quadrupole moment from MESSENGER ranging",
        "J2_sun",
        "2.25 e-7",
        "0.09 e-7",
        "",
        kind="uncertainty as printed, level not stated",
        source=PARK_2017_SOURCE + " Abstract and Table 1.",
        edition=PARK_2017_EDITION,
        url=PARK_2017_URL,
        retrieved_from=PARK_2017_PDF,
        keys=("mercury", "messenger"),
        phrases=("solar quadrupole", "solar oblateness", "solar j2"),
        notes=(_PARK_GAMMA, _PARK_LEVEL),
    ),
    _q(
        "mercury.epm2011.extra_perihelion_precession",
        "additional perihelion precession of Mercury beyond all modeled effects, EPM2011",
        "Delta dot(pi) Mercury",
        "-0.020",
        "0.030",
        "mas per year",
        kind="standard uncertainty",
        source=PITJEVA_2013_SOURCE + " Table 4.",
        edition=PITJEVA_2013_EDITION,
        url=PITJEVA_2013_URL,
        retrieved_from=PITJEVA_2013_PDF,
        keys=("mercury", "perihelion", "epm2011"),
        phrases=("perihelion of mercury", "mercury perihelion", "supplementary perihelion"),
        notes=(
            "This is the residual of the modern ephemeris: a correction fitted on top of every known effect, relativistic ones included, from about 780 thousand observations.",
            "The paper calls the printed uncertainty sigma and says it can be treated as an upper limit on an additional secular drift.",
        ),
    ),
    _q(
        "mercury.epm2011.beta_minus_1",
        "PPN parameter beta minus one, EPM2011",
        "beta - 1",
        "-0.00002",
        "0.00003",
        "",
        kind="3 sigma",
        source=PITJEVA_2013_SOURCE + " Eq. (3).",
        edition=PITJEVA_2013_EDITION,
        url=PITJEVA_2013_URL,
        retrieved_from=PITJEVA_2013_PDF,
        keys=("epm2011", "ppn"),
        phrases=("ppn beta", "post-newtonian beta"),
        notes=("Beta and gamma were fitted together. The paper prints the uncertainty as 3 sigma.",),
    ),
    _q(
        "mercury.epm2011.gamma_minus_1",
        "PPN parameter gamma minus one, EPM2011",
        "gamma - 1",
        "+0.00004",
        "0.00006",
        "",
        kind="3 sigma",
        source=PITJEVA_2013_SOURCE + " Eq. (3).",
        edition=PITJEVA_2013_EDITION,
        url=PITJEVA_2013_URL,
        retrieved_from=PITJEVA_2013_PDF,
        keys=("epm2011", "ppn"),
        phrases=("ppn gamma", "post-newtonian gamma"),
        notes=("Beta and gamma were fitted together. The paper prints the uncertainty as 3 sigma.",),
    ),
    _q(
        "cassini.bertotti2003.gamma_minus_1",
        "PPN parameter gamma minus one from the Cassini radio frequency shift",
        "gamma - 1",
        "2.1 e-5",
        "2.3 e-5",
        "",
        kind="uncertainty as printed, level not stated",
        source=BERTOTTI_2003_SOURCE + " Abstract.",
        edition="Nature 425 (2003 September)",
        url="https://doi.org/10.1038/nature01997",
        retrieved_from="https://www.nature.com/articles/nature01997",
        keys=("cassini", "ppn", "shapiro"),
        phrases=("ppn gamma", "post-newtonian gamma"),
        notes=(
            "The abstract prints gamma = 1 + (2.1 +- 2.3) x 10^-5, from the frequency shift of radio photons to and from Cassini near solar conjunction in 2002.",
            "The abstract does not name a confidence level for the uncertainty, so none is assigned here.",
        ),
    ),
)

PLANCK_2018_SOURCE = (
    "Planck Collaboration, N. Aghanim et al., Planck 2018 results. VI. Cosmological parameters, "
    "Astron. Astrophys. 641, A6 (2020), doi:10.1051/0004-6361/201833910, arXiv:1807.06209, Table 2."
)
PLANCK_2018_EDITION = "Planck 2018 VI, base-LCDM, TT,TE,EE+lowE+lensing"
PLANCK_2018_URL = "https://doi.org/10.1051/0004-6361/201833910"
PLANCK_2018_PDF = "https://arxiv.org/pdf/1807.06209"
_PLANCK_NOTES = (
    "Table 2 column TT,TE,EE+lowE+lensing, the paper's baseline, printed as a 68% interval.",
    "The number is a fit of the base-LCDM model to Planck data. It is a measured anchor inside that model, not a model-free measurement.",
)
_PLANCK_KEYS = ("planck2018", "lcdm", "cosmology")


def _planck(id: str, name: str, symbol: str, value_text: str, sigma: str, unit: str = "", *, phrases: tuple[str, ...] = (), notes: tuple[str, ...] = ()) -> Quantity:
    return _q(
        id, name, symbol, value_text, sigma, unit,
        kind="68% interval",
        source=PLANCK_2018_SOURCE,
        edition=PLANCK_2018_EDITION,
        url=PLANCK_2018_URL,
        retrieved_from=PLANCK_2018_PDF,
        keys=_PLANCK_KEYS,
        phrases=phrases,
        notes=notes + _PLANCK_NOTES,
    )


PLANCK_2018: tuple[Quantity, ...] = (
    _planck("planck2018.h0", "Hubble constant", "H0", "67.36", "0.54", "km s^-1 Mpc^-1", phrases=("hubble constant", "hubble tension")),
    _planck("planck2018.omega_b_h2", "physical baryon density", "Omega_b h^2", "0.02237", "0.00015", phrases=("baryon density",)),
    _planck("planck2018.omega_c_h2", "physical cold dark matter density", "Omega_c h^2", "0.1200", "0.0012", phrases=("dark matter density",)),
    _planck("planck2018.theta_mc", "approximate acoustic angular scale", "100 theta_MC", "1.04092", "0.00031"),
    _planck("planck2018.tau", "reionization optical depth", "tau", "0.0544", "0.0073", phrases=("optical depth", "reionization")),
    _planck("planck2018.ln_as", "primordial scalar amplitude", "ln(10^10 A_s)", "3.044", "0.014"),
    _planck("planck2018.n_s", "scalar spectral index", "n_s", "0.9649", "0.0042", phrases=("spectral index",)),
    _planck("planck2018.omega_lambda", "dark energy density parameter", "Omega_Lambda", "0.6847", "0.0073", phrases=("dark energy density",)),
    _planck("planck2018.omega_m", "matter density parameter", "Omega_m", "0.3153", "0.0073", phrases=("matter density",)),
    _planck("planck2018.omega_m_h2", "physical matter density", "Omega_m h^2", "0.1430", "0.0011"),
    _planck("planck2018.sigma_8", "amplitude of matter fluctuations on 8 h^-1 Mpc", "sigma_8", "0.8111", "0.0060", phrases=("sigma8", "sigma_8")),
    _planck("planck2018.s_8", "S8, defined as sigma_8 (Omega_m/0.3)^0.5", "S_8", "0.832", "0.013", phrases=("s8",)),
)

SH0ES_2022: tuple[Quantity, ...] = (
    _q(
        "sh0es2022.h0",
        "Hubble constant from the Cepheid and type Ia supernova distance ladder",
        "H0",
        "73.04",
        "1.04",
        "km s^-1 Mpc^-1",
        kind="uncertainty as printed, level not stated",
        source=(
            "A. G. Riess et al., A Comprehensive Measurement of the Local Value of the Hubble Constant with 1 km/s/Mpc Uncertainty "
            "from the Hubble Space Telescope and the SH0ES Team, Astrophys. J. Lett. 934, L7 (2022), doi:10.3847/2041-8213/ac5c5b, "
            "arXiv:2112.04510. Abstract, baseline result."
        ),
        edition="ApJL 934, L7 (2022)",
        url="https://doi.org/10.3847/2041-8213/ac5c5b",
        retrieved_from="https://arxiv.org/abs/2112.04510",
        keys=("sh0es", "cepheid"),
        phrases=("hubble constant", "hubble tension", "distance ladder"),
        notes=(
            "The abstract calls this the baseline Cepheid-SN result. It includes systematics and lies near the median of about 70 analysis variants.",
            "The same abstract states a 5-sigma difference from H0 predicted by Planck+LCDM, and says the source of the discrepancy remains unknown.",
            "The abstract does not name a confidence level for the uncertainty, so none is assigned here.",
        ),
    ),
)

DESI_DR2_SOURCE = (
    "DESI Collaboration, M. Abdul-Karim et al., DESI DR2 Results II: Measurements of Baryon Acoustic Oscillations and "
    "Cosmological Constraints, Phys. Rev. D 112, 083515 (2025), doi:10.1103/tr6y-kpc6, arXiv:2503.14738."
)
_DESI_NOTES = (
    "Marginalized posterior in the w0waCDM model, w(a) = w0 + wa (1 - a), printed with 68% limits.",
    "The value depends on which data are combined. Each combination is a separate record.",
)


def _desi(combo: str, label: str, eq: str, w0: str, w0_sigma: str, wa: str, wa_up: str, wa_low: str = "") -> tuple[Quantity, Quantity]:
    common = dict(
        kind="68% interval",
        source=f"{DESI_DR2_SOURCE} Eq. ({eq}) and Table V, {label}.",
        edition=f"DESI DR2 BAO, {label}",
        url="https://doi.org/10.1103/tr6y-kpc6",
        retrieved_from="https://arxiv.org/pdf/2503.14738",
        keys=("desi",),
        phrases=("dark energy equation of state", "dynamical dark energy", "w0wa"),
        notes=_DESI_NOTES,
    )
    return (
        _q(f"desi_dr2.{combo}.w0", f"dark energy w0, {label}", "w0", w0, w0_sigma, "", **common),
        _q(f"desi_dr2.{combo}.wa", f"dark energy wa, {label}", "wa", wa, wa_up, "", lower_text=wa_low, **common),
    )


DESI_DR2: tuple[Quantity, ...] = (
    *_desi("cmb", "DESI+CMB", "25", "-0.42", "0.21", "-1.75", "0.58"),
    *_desi("cmb_pantheonplus", "DESI+CMB+Pantheon+", "26", "-0.838", "0.055", "-0.62", "0.22", "0.19"),
    *_desi("cmb_union3", "DESI+CMB+Union3", "27", "-0.667", "0.088", "-1.09", "0.31", "0.27"),
    *_desi("cmb_desy5", "DESI+CMB+DESY5", "28", "-0.752", "0.057", "-0.86", "0.23", "0.20"),
)

FIXSEN_2009: tuple[Quantity, ...] = (
    _q(
        "fixsen2009.t_cmb",
        "temperature of the cosmic microwave background",
        "T_0",
        "2.72548",
        "0.00057",
        "K",
        kind="uncertainty as printed, level not stated",
        source=(
            "D. J. Fixsen, The Temperature of the Cosmic Microwave Background, Astrophys. J. 707, 916-920 (2009), "
            "doi:10.1088/0004-637X/707/2/916, arXiv:0911.1955. Abstract and Table 2 mean."
        ),
        edition="ApJ 707 (2009)",
        url="https://doi.org/10.1088/0004-637X/707/2/916",
        retrieved_from="https://arxiv.org/pdf/0911.1955",
        keys=("cmb", "fixsen", "firas"),
        phrases=("cmb temperature", "cosmic microwave background temperature", "temperature of the cosmic microwave background"),
        notes=(
            "This is the combination of the measurements reviewed in the paper. The FIRAS data recalibrated with WMAP alone give 2.7260 +- 0.0013 K, which is not stored separately.",
            "The paper does not name a confidence level for the combined uncertainty, so none is assigned here.",
        ),
    ),
)

_SPLIT_NOTE = "The source prints the statistical and systematic parts separately. They are stored as printed and are not combined here."
_PDG_SCALE = "PDG average. The error includes a scale factor of {0}, which PDG applies when the measurements disagree more than their errors allow."

PARTICLE_PRECISION: tuple[Quantity, ...] = (
    _q(
        "ucntau2021.neutron_lifetime",
        "free neutron lifetime, UCNtau 2017-2018 campaigns",
        "tau_n",
        "877.75",
        "0.28",
        "s",
        kind=_SPLIT_KIND,
        systematic_text="0.22",
        systematic_lower_text="0.16",
        source="F. M. Gonzalez et al. (UCNtau Collaboration), Improved Neutron Lifetime Measurement with UCNtau, Phys. Rev. Lett. 127, 162501 (2021), doi:10.1103/PhysRevLett.127.162501, arXiv:2106.10375.",
        edition="Phys. Rev. Lett. 127 (2021)",
        url="https://doi.org/10.1103/PhysRevLett.127.162501",
        retrieved_from="https://arxiv.org/abs/2106.10375",
        keys=("ucntau",),
        phrases=("neutron lifetime", "neutron mean life"),
        notes=("Printed in the abstract as tau_n = 877.75 +- 0.28 stat +0.22/-0.16 syst s. Magneto-gravitational trap of ultracold neutrons; surviving neutrons were counted.", _SPLIT_NOTE),
    ),
    _q(
        "ucntau2025.neutron_lifetime",
        "free neutron lifetime, all UCNtau data averaged",
        "tau_n",
        "877.82",
        "0.22",
        "s",
        kind=_SPLIT_KIND,
        systematic_text="0.20",
        systematic_lower_text="0.17",
        source="R. Musedinovic et al. (UCNtau Collaboration), Measurement of the free neutron lifetime in a magneto-gravitational trap with in situ detection, Phys. Rev. C 111, 045501 (2025), doi:10.1103/PhysRevC.111.045501, arXiv:2409.05560.",
        edition="Phys. Rev. C 111 (2025)",
        url="https://doi.org/10.1103/PhysRevC.111.045501",
        retrieved_from="https://arxiv.org/abs/2409.05560",
        keys=("ucntau",),
        phrases=("neutron lifetime", "neutron mean life"),
        notes=("Printed in the abstract as 877.82+/-0.22 (statistical)+0.20-0.17 (systematic) s, when all the data from UCNtau are averaged. It includes the 2021 data, so it is not independent of ucntau2021.neutron_lifetime. The 2020-2022 runs alone gave 877.94+/-0.37 s.", _SPLIT_NOTE),
    ),
    _q(
        "nist_beam2013.neutron_lifetime",
        "free neutron lifetime, NIST beam method, updated",
        "tau_n",
        "887.7",
        "1.2",
        "s",
        kind=_SPLIT_KIND,
        systematic_text="1.9",
        source="A. T. Yue et al., Improved Determination of the Neutron Lifetime, Phys. Rev. Lett. 111, 222501 (2013), doi:10.1103/PhysRevLett.111.222501, arXiv:1309.2623.",
        edition="Phys. Rev. Lett. 111 (2013)",
        url="https://doi.org/10.1103/PhysRevLett.111.222501",
        retrieved_from="https://arxiv.org/abs/1309.2623",
        keys=("beam",),
        phrases=("neutron lifetime", "neutron mean life"),
        notes=("Printed in the abstract as tau_n = (887.7 +- 1.2 [stat] +- 1.9 [syst]) s. It counts decay protons from a cold neutron beam, a different method from counting stored neutrons.", _SPLIT_NOTE),
    ),
    _pdg("pdg2026.neutron_lifetime", "neutron mean life", "tau_n", "878.3", "0.4", "s", node="S017T", phrases=("neutron lifetime", "neutron mean life"), notes=(_PDG_SCALE.format("1.8"), "PDG's average uses eight stored-neutron results, ucntau2025.neutron_lifetime among them. The 2021 UCNtau result and the beam results, nist_beam2013.neutron_lifetime among them, are listed but not used in the average.", _API_NOTE)),
    _pdg("pdg2026.lambda_ga_gv", "ratio of axial to vector coupling in neutron decay", "lambda = g_A/g_V", "-1.2753", "0.0013", "", node="S017AV", keys=("g_a",), phrases=("axial coupling", "axial-vector coupling", "g_a/g_v", "ga/gv"), notes=(_PDG_SCALE.format("2.7"), "PDG labels this lambda == g_A / g_V for the neutron. The sign follows PDG's convention.", _API_NOTE)),
    _q(
        "fnal2025.a_mu",
        "positive muon magnetic anomaly, Fermilab Runs 1-6 combined",
        "a_mu",
        "116 592 0705 e-12",
        "148 e-12",
        "",
        kind="uncertainty as printed, level not stated",
        printed="116 592 0705(148) e-12",
        source="D. P. Aguillard et al. (Muon g-2 Collaboration), Measurement of the Positive Muon Anomalous Magnetic Moment to 127 ppb, Phys. Rev. Lett. 135, 101802 (2025), doi:10.1103/7clf-sm2v, arXiv:2506.03069.",
        edition="Phys. Rev. Lett. 135 (2025)",
        url="https://doi.org/10.1103/7clf-sm2v",
        retrieved_from="https://arxiv.org/abs/2506.03069",
        keys=("fermilab",),
        phrases=("muon g-2", "muon g - 2", "muon anomalous magnetic moment", "muon magnetic anomaly"),
        notes=("Printed in the abstract as a_mu = 116 592 0705(148) x 10^-12 (127 ppb) when combined with the earlier Fermilab results. The 2020-2023 data alone gave 116 592 0710(162) x 10^-12 (139 ppb).",),
    ),
    _q(
        "fnal2025.a_mu_world_average",
        "muon magnetic anomaly, experimental world average after the final Fermilab result",
        "a_mu(exp)",
        "116 592 0715 e-12",
        "145 e-12",
        "",
        kind="uncertainty as printed, level not stated",
        printed="116 592 0715(145) e-12",
        source="D. P. Aguillard et al. (Muon g-2 Collaboration), Measurement of the Positive Muon Anomalous Magnetic Moment to 127 ppb, Phys. Rev. Lett. 135, 101802 (2025), doi:10.1103/7clf-sm2v, arXiv:2506.03069.",
        edition="Phys. Rev. Lett. 135 (2025)",
        url="https://doi.org/10.1103/7clf-sm2v",
        retrieved_from="https://arxiv.org/abs/2506.03069",
        keys=("fermilab",),
        phrases=("muon g-2", "muon g - 2", "muon anomalous magnetic moment", "muon magnetic anomaly"),
        notes=("Printed in the abstract as a_mu(exp) = 116 592 0715(145) x 10^-12 (124 ppb), dominated by the Fermilab measurements, with Brookhaven E821 included. No Standard Model prediction is stored here.",),
    ),
    _pdg("pdg2026.a_mu", "muon magnetic anomaly", "(g_mu - 2)/2", "0.00116592072", "0.00000000015", "", node="S004MM", phrases=("muon g-2", "muon anomalous magnetic moment"), notes=("PDG lists the combined Fermilab and Brookhaven value of Phys. Rev. Lett. 135, 101802 (2025), (11659207.15 +- 1.45) E-10, and prints its average to fewer digits.", _API_NOTE)),
    _q(
        "fan2023.electron_g_over_2",
        "electron magnetic moment in Bohr magnetons",
        "-mu/mu_B = g/2",
        "1.001 159 652 180 59",
        "0.000 000 000 000 13",
        "",
        kind="uncertainty as printed, level not stated",
        printed="1.001 159 652 180 59(13)",
        source="X. Fan, T. G. Myers, B. A. D. Sukra, and G. Gabrielse, Measurement of the Electron Magnetic Moment, Phys. Rev. Lett. 130, 071801 (2023), doi:10.1103/PhysRevLett.130.071801, arXiv:2209.13084.",
        edition="Phys. Rev. Lett. 130 (2023)",
        url="https://doi.org/10.1103/PhysRevLett.130.071801",
        retrieved_from="https://arxiv.org/abs/2209.13084",
        keys=("gabrielse",),
        phrases=("electron g-2", "electron g - 2", "electron magnetic moment"),
        notes=("Printed in the abstract as -mu/mu_B = g/2 = 1.001 159 652 180 59 (13) [0.13 ppt]. A single electron in a Penning trap. The abstract also gives an alpha inferred with Standard Model theory; that inferred value is not stored here.",),
    ),
    _pdg("pdg2026.a_e", "electron magnetic moment anomaly", "(g - 2)/2", "0.00115965218062", "0.00000000000012", "", node="S003MM", phrases=("electron g-2", "electron magnetic moment anomaly"), notes=("PDG average of the single-electron measurements.", _API_NOTE)),
    _pdg("pdg2026.proton_radius", "proton charge radius", "r_p", "0.8407", "0.0006", "fm", node="S016CR", phrases=("proton charge radius", "proton radius"), notes=("The only entry PDG uses in this average is the CODATA 2022 value, 0.84075 +- 0.00064 fm. PDG prints the average as 0.8407 +- 0.0006 fm.", _API_NOTE)),
)

ASD_SOURCE = (
    "A. Kramida, Yu. Ralchenko, J. Reader, and NIST ASD Team, NIST Atomic Spectra Database (version 5.12), "
    "National Institute of Standards and Technology, Gaithersburg, MD (2024), doi:10.18434/T4W30F, "
    "Ionization Energies Data."
)
ASD_EDITION = "NIST ASD version 5.12 (7 November 2024)"
ASD_QUERY = (
    "https://physics.nist.gov/cgi-bin/ASD/ie.pl?spectra=H-Ne&submit=Retrieve+Data&units=1&format=2&order=0"
    "&at_num_out=on&sp_name_out=on&ion_charge_out=on&el_name_out=on&seq_out=on&shells_out=on&level_out=on"
    "&ion_conf_out=on&e_out=0&unc_out=on&biblio=on"
)
_ASD_EV = (
    "ASD stores ionization energies in cm^-1. In eV output, ASD combines the uncertainty of the CODATA conversion factor "
    "in quadrature with the stored uncertainty and rounds the value to the combined uncertainty. The value and uncertainty "
    "here are the eV output as served. The ASD help does not state a confidence level for the uncertainty column."
)


def _asd(id: str, z: int, element: str, spectrum: str, value_text: str, uncertainty_text: str, *, notes: tuple[str, ...]) -> Quantity:
    lower = element.lower()
    return _q(
        id,
        f"first ionization energy of {lower} ({spectrum}, Z = {z})",
        f"E_i({spectrum})",
        value_text,
        uncertainty_text,
        "eV",
        kind="uncertainty as printed, level not stated",
        source=ASD_SOURCE,
        edition=ASD_EDITION,
        url=ASD_QUERY,
        retrieved_from=ASD_QUERY,
        keys=("ionization",),
        phrases=(f"ionization energy of {lower}", f"{lower} ionization energy", f"ionisation energy of {lower}"),
        notes=notes,
    )


ASD_IONIZATION: tuple[Quantity, ...] = (
    _asd("asd512.ie.h", 1, "Hydrogen", "H I", "13.598434599702", "0.000000000012",
         notes=(
            'ASD ground shells 1s, ground level 2S<1/2>.',
            'ASD bibliography codes: HDEL.',
            'ASD prints this energy in parentheses. The ASD help says parentheses mark energies from an ab-initio calculation, or otherwise not derived from evaluated experimental data.',
            _ASD_EV,
         )),
    _asd("asd512.ie.he", 2, "Helium", "He I", "24.587389011", "0.000000025",
         notes=(
            'ASD ground shells 1s2, ground level 1S0, ionized level 1s 2S<1/2>.',
            'ASD bibliography codes: L17714.',
            _ASD_EV,
         )),
    _asd("asd512.ie.li", 3, "Lithium", "Li I", "5.391714996", "0.000000022",
         notes=(
            'ASD ground shells 1s2.2s, ground level 2S<1/2>, ionized level 1s2 1S<0>.',
            'ASD bibliography codes: L12261.',
            _ASD_EV,
         )),
    _asd("asd512.ie.be", 4, "Beryllium", "Be I", "9.322699", "0.000007",
         notes=(
            'ASD ground shells 1s2.2s2, ground level 1S0, ionized level 2s 2S<1/2>.',
            'ASD bibliography codes: L5964.',
            _ASD_EV,
         )),
    _asd("asd512.ie.b", 5, "Boron", "B I", "8.298019", "0.000003",
         notes=(
            'ASD ground shells 1s2.2s2.2p, ground level 2P*<1/2>, ionized level 2s2 1S<0>.',
            'ASD bibliography codes: L12312.',
            _ASD_EV,
         )),
    _asd("asd512.ie.c", 6, "Carbon", "C I", "11.2602880", "0.0000011",
         notes=(
            'ASD ground shells 1s2.2s2.2p2, ground level 3P0, ionized level 2s2.2p 2P*<1/2>.',
            'ASD bibliography codes: L20057.',
            _ASD_EV,
         )),
    _asd("asd512.ie.n", 7, "Nitrogen", "N I", "14.53413", "0.00004",
         notes=(
            'ASD ground shells 1s2.2s2.2p3, ground level 4S*<3/2>, ionized level 2p2 3P<0>.',
            'ASD bibliography codes: L1411.',
            _ASD_EV,
         )),
    _asd("asd512.ie.o", 8, "Oxygen", "O I", "13.618055", "0.000007",
         notes=(
            'ASD ground shells 1s2.2s2.2p4, ground level 3P<2>, ionized level 2p3 4S*<3/2>.',
            'ASD bibliography codes: L74,L3760.',
            _ASD_EV,
         )),
    _asd("asd512.ie.f", 9, "Fluorine", "F I", "17.42282", "0.00005",
         notes=(
            'ASD ground shells 1s2.2s2.2p5, ground level 2P*<3/2>, ionized level 2p4 3P<2>.',
            'ASD bibliography codes: L7481,L526.',
            _ASD_EV,
         )),
    _asd("asd512.ie.ne", 10, "Neon", "Ne I", "21.564541", "0.000007",
         notes=(
            'ASD ground shells 1s2.2s2.2p6, ground level 1S0, ionized level 2p5 2P*<3/2>.',
            'ASD bibliography codes: L8826,L1407.',
            _ASD_EV,
         )),
)

QUANTITIES: tuple[Quantity, ...] = (
    CODATA_2022 + PDG_2026 + MERCURY + MERCURY_MODERN + GW150914 + PLANCK_2018 + SH0ES_2022 + DESI_DR2 + FIXSEN_2009
    + PARTICLE_PRECISION + ASD_IONIZATION
)


@dataclass(frozen=True)
class Bound:
    id: str
    name: str
    symbol: str
    lower_text: str
    upper_text: str
    unit: str
    source: str
    edition: str
    url: str
    retrieved_from: str
    retrieved: str
    keys: tuple[str, ...]
    phrases: tuple[str, ...]
    conditions: tuple[str, ...]
    forbids: tuple[str, ...]

    @property
    def lower(self) -> Fraction:
        return parse_decimal(self.lower_text)

    @property
    def upper(self) -> Fraction:
        return parse_decimal(self.upper_text)


BOUNDS: tuple[Bound, ...] = (
    Bound(
        id="bound.gw170817_speed_of_gravity",
        name="fractional difference between the speed of gravity and the speed of light",
        symbol="(v_GW - v_EM)/v_EM",
        lower_text="-3 e-15",
        upper_text="+7 e-16",
        unit="",
        source=(
            "B. P. Abbott et al. (LIGO Scientific Collaboration, Virgo Collaboration, Fermi Gamma-ray Burst Monitor, and INTEGRAL), "
            "Gravitational Waves and Gamma-Rays from a Binary Neutron Star Merger: GW170817 and GRB 170817A, "
            "Astrophys. J. Lett. 848, L13 (2017), doi:10.3847/2041-8213/aa920c, arXiv:1710.05834, Section 4.1, Eq. (2)."
        ),
        edition="ApJL 848 L13 (2017)",
        url="https://doi.org/10.3847/2041-8213/aa920c",
        retrieved_from="https://arxiv.org/abs/1710.05834",
        retrieved=RETRIEVED,
        keys=("gw170817",),
        phrases=("speed of gravity", "speed of gravitational waves", "grb 170817a"),
        conditions=(
            "The observed delay of GRB 170817A after GW170817 is (+1.74 +- 0.05) s.",
            "The distance is taken conservatively as D = 26 Mpc, the lower end of the 90% credible interval on the gravitational-wave luminosity distance.",
            "The upper end assumes both signals left together. The lower end assumes the gamma rays left 10 s after the gravitational-wave peak.",
            "The paper notes that exotic emission models can widen the delay window to (-100 s, 1000 s), which loosens the bound.",
        ),
        forbids=("law(gravity_outruns_light_beyond_gw170817_bound)", "law(light_outruns_gravity_beyond_gw170817_bound)"),
    ),
)


def quantity(id: str) -> Quantity:
    for item in QUANTITIES:
        if item.id == id:
            return item
    raise KeyError(id)


def audit_quantities(items: tuple[Quantity, ...] = QUANTITIES) -> None:
    seen: set[str] = set()
    for item in items:
        if not item.id or item.id in seen:
            raise ValueError(f"bad quantity id {item.id}")
        seen.add(item.id)
        if item.uncertainty_kind not in UNCERTAINTY_KINDS:
            raise ValueError(f"{item.id} has uncertainty kind {item.uncertainty_kind}")
        if not item.source.strip() or not item.edition.strip():
            raise ValueError(f"{item.id} needs a source and an edition")
        for url in (item.url, item.retrieved_from):
            if not url.startswith("https://"):
                raise ValueError(f"{item.id} needs https urls")
        if len(item.retrieved) != 10 or item.retrieved[4] != "-" or item.retrieved[7] != "-":
            raise ValueError(f"{item.id} needs a retrieval date")
        item.value
        if not item.exact:
            upper = item.uncertainty
            lower = item.lower_uncertainty
            if upper is None or lower is None or upper <= 0 or lower <= 0:
                raise ValueError(f"{item.id} needs a positive uncertainty")
        elif item.lower_text:
            raise ValueError(f"{item.id} is exact and cannot carry an interval")
        if item.lower_text and item.uncertainty_kind not in _ASYMMETRIC_KINDS:
            raise ValueError(f"{item.id} has a lower bound but a symmetric kind")
        if (item.uncertainty_kind == _SPLIT_KIND) != bool(item.systematic_text):
            raise ValueError(f"{item.id} carries a systematic part only under the split kind")
        if item.systematic_lower_text and not item.systematic_text:
            raise ValueError(f"{item.id} has a lower systematic part without an upper one")
        if item.systematic_text and (item.systematic <= 0 or item.systematic_lower <= 0):
            raise ValueError(f"{item.id} needs a positive systematic part")
        if item.printed:
            value, sigma = parse_concise(item.printed)
            if value != item.value or sigma != item.uncertainty:
                raise ValueError(f"{item.id} does not match its printed form {item.printed}")


def audit_bounds(items: tuple[Bound, ...] = BOUNDS) -> None:
    for item in items:
        if not item.source.strip() or not item.edition.strip() or not item.conditions:
            raise ValueError(f"{item.id} needs a source, an edition, and its conditions")
        if not item.url.startswith("https://") or not item.retrieved_from.startswith("https://"):
            raise ValueError(f"{item.id} needs https urls")
        if not item.lower < item.upper:
            raise ValueError(f"{item.id} has an empty interval")


audit_quantities()
audit_bounds()
