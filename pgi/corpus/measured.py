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
        "99.7% interval",
        "acceptance interval",
        "PDG estimated range",
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
    parentheses are the uncertainty in the last printed places. A decimal point
    inside the parentheses, as in `1 057 829.8(3.2)`, gives the uncertainty in
    the value's own units."""
    cleaned = text.replace(" ", "").replace("\u2212", "-")
    head, _, rest = cleaned.partition("(")
    digits, _, tail = rest.partition(")")
    aligned = digits.count(".") == 1 and digits.replace(".", "").isdigit()
    if not head or not (digits.isdigit() or aligned) or (tail and not tail.startswith("e")):
        raise ValueError(f"not a concise value: {text!r}")
    places = len(head.partition(".")[2])
    scale = Fraction(10) ** int(tail[1:]) if tail else Fraction(1)
    if aligned:
        # `829.8(3.2)`: a decimal point inside the parentheses aligns the uncertainty with the value's units.
        return Fraction(head) * scale, Fraction(digits) * scale
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
            "Mariani et al., A&A 682, A175 (2024), Section 3.1, describe this constraint as given at 1 sigma, assuming Gaussian noise. That is a later reading, not the paper's own statement, so the label is unchanged.",
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
ASD_QUERY_NA_KR = (
    "https://physics.nist.gov/cgi-bin/ASD/ie.pl?spectra=Na-Kr&submit=Retrieve+Data&units=1&format=2&order=0"
    "&at_num_out=on&sp_name_out=on&ion_charge_out=on&el_name_out=on&seq_out=on&shells_out=on&level_out=on"
    "&ion_conf_out=on&e_out=0&unc_out=on&biblio=on"
)
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
    query = ASD_QUERY if z <= 10 else ASD_QUERY_NA_KR
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
        url=query,
        retrieved_from=query,
        keys=(),
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
    _asd("asd512.ie.na", 11, "Sodium", "Na I", "5.13907696", "0.00000025",
         notes=(
            'ASD ground shells [Ne].3s, ground level 2S<1/2>, ionized level 2p6 1S<0>.',
            'ASD bibliography codes: L10921,L9648.',
            _ASD_EV,
         )),
    _asd("asd512.ie.mg", 12, "Magnesium", "Mg I", "7.646236", "0.000004",
         notes=(
            'ASD ground shells [Ne].3s2, ground level 1S0, ionized level 3s 2S<1/2>.',
            'ASD bibliography codes: L10635,L6969.',
            _ASD_EV,
         )),
    _asd("asd512.ie.al", 13, "Aluminum", "Al I", "5.985769", "0.000003",
         notes=(
            'ASD ground shells [Ne].3s2.3p, ground level 2P*<1/2>, ionized level 3s2 1S<0>.',
            'ASD bibliography codes: L7215,L10321.',
            _ASD_EV,
         )),
    _asd("asd512.ie.si", 14, "Silicon", "Si I", "8.15168", "0.00003",
         notes=(
            'ASD ground shells [Ne].3s2.3p2, ground level 3P0, ionized level 3p 2P*<1/2>.',
            'ASD bibliography codes: L5815.',
            _ASD_EV,
         )),
    _asd("asd512.ie.p", 15, "Phosphorus", "P I", "10.486686", "0.000015",
         notes=(
            'ASD ground shells [Ne].3s2.3p3, ground level 4S*<3/2>, ionized level 3p2 3P<0>.',
            'ASD bibliography codes: L5148.',
            _ASD_EV,
         )),
    _asd("asd512.ie.s", 16, "Sulfur", "S I", "10.3600167", "0.0000014",
         notes=(
            'ASD ground shells [Ne].3s2.3p4, ground level 3P<2>, ionized level 3p3 4S*<3/2>.',
            'ASD bibliography codes: L23116.',
            _ASD_EV,
         )),
    _asd("asd512.ie.cl", 17, "Chlorine", "Cl I", "12.967633", "0.000016",
         notes=(
            'ASD ground shells [Ne].3s2.3p5, ground level 2P*<3/2>, ionized level 3p4 3P<2>.',
            'ASD bibliography codes: L19191.',
            _ASD_EV,
         )),
    _asd("asd512.ie.ar", 18, "Argon", "Ar I", "15.7596119", "0.0000005",
         notes=(
            'ASD ground shells [Ne].3s2.3p6, ground level 1S0, ionized level 3p5 2P*<3/2>.',
            'ASD bibliography codes: L9217.',
            _ASD_EV,
         )),
    _asd("asd512.ie.k", 19, "Potassium", "K I", "4.34066373", "0.00000009",
         notes=(
            'ASD ground shells [Ar].4s, ground level 2S<1/2>, ionized level 3p6 1S<0>.',
            'ASD bibliography codes: L5451,L5783,L7185.',
            _ASD_EV,
         )),
    _asd("asd512.ie.ca", 20, "Calcium", "Ca I", "6.1131549210", "0.0000000005",
         notes=(
            'ASD ground shells [Ar].4s2, ground level 1S0, ionized level 4s 2S<1/2>.',
            'ASD bibliography codes: L22848.',
            _ASD_EV,
         )),
    _asd("asd512.ie.sc", 21, "Scandium", "Sc I", "6.56149", "0.00006",
         notes=(
            'ASD ground shells [Ar].3d.4s2, ground level 2D<3/2>, ionized level 3d.4s 3D<1>.',
            'ASD bibliography codes: L7185,L2110.',
            _ASD_EV,
         )),
    _asd("asd512.ie.ti", 22, "Titanium", "Ti I", "6.828120", "0.000012",
         notes=(
            'ASD ground shells [Ar].3d2.4s2, ground level 3F<2>, ionized level 3d2.4s 4F<3/2>.',
            'ASD bibliography codes: L17996.',
            _ASD_EV,
         )),
    _asd("asd512.ie.v", 23, "Vanadium", "V I", "6.746187", "0.000021",
         notes=(
            'ASD ground shells [Ar].3d3.4s2, ground level 4F<3/2>, ionized level 3d4 5D<0>.',
            'ASD bibliography codes: L17712,L20010.',
            _ASD_EV,
         )),
    _asd("asd512.ie.cr", 24, "Chromium", "Cr I", "6.76651", "0.00004",
         notes=(
            'ASD ground shells [Ar].3d5.4s, ground level 7S<3>, ionized level 3d5 6S<5/2>.',
            'ASD bibliography codes: L7185,L2832.',
            _ASD_EV,
         )),
    _asd("asd512.ie.mn", 25, "Manganese", "Mn I", "7.4340380", "0.0000012",
         notes=(
            'ASD ground shells [Ar].3d5.4s2, ground level 6S<5/2>, ionized level 3d5.4s 7S<3>.',
            'ASD bibliography codes: L19057.',
            _ASD_EV,
         )),
    _asd("asd512.ie.fe", 26, "Iron", "Fe I", "7.9024681", "0.0000012",
         notes=(
            'ASD ground shells [Ar].3d6.4s2, ground level 5D<4>, ionized level 3d6.4s 6D<9/2>.',
            'ASD bibliography codes: L7743c109.',
            _ASD_EV,
         )),
    _asd("asd512.ie.co", 27, "Cobalt", "Co I", "7.88101", "0.00012",
         notes=(
            'ASD ground shells [Ar].3d7.4s2, ground level 4F<9/2>, ionized level 3d8 3F<4>.',
            'ASD bibliography codes: L10545.',
            _ASD_EV,
         )),
    _asd("asd512.ie.ni", 28, "Nickel", "Ni I", "7.639878", "0.000017",
         notes=(
            'ASD ground shells [Ar].3d8.4s2, ground level 3F<4>, ionized level 3d9 2D<5/2>.',
            'ASD bibliography codes: L12369.',
            _ASD_EV,
         )),
    _asd("asd512.ie.cu", 29, "Copper", "Cu I", "7.726380", "0.000004",
         notes=(
            'ASD ground shells [Ar].3d10.4s, ground level 2S<1/2>, ionized level 3d10 1S<0>.',
            'ASD bibliography codes: L14897.',
            _ASD_EV,
         )),
    _asd("asd512.ie.zn", 30, "Zinc", "Zn I", "9.394197", "0.000006",
         notes=(
            'ASD ground shells [Ar].3d10.4s2, ground level 1S0, ionized level 4s 2S<1/2>.',
            'ASD bibliography codes: L13951.',
            _ASD_EV,
         )),
    _asd("asd512.ie.ga", 31, "Gallium", "Ga I", "5.9993020", "0.0000012",
         notes=(
            'ASD ground shells [Ar].3d10.4s2.4p, ground level 2P*<1/2>, ionized level 4s2 1S<0>.',
            'ASD bibliography codes: L5566.',
            _ASD_EV,
         )),
    _asd("asd512.ie.ge", 32, "Germanium", "Ge I", "7.899435", "0.000012",
         notes=(
            'ASD ground shells [Ar].3d10.4s2.4p2, ground level 3P0, ionized level 4p 2P*<1/2>.',
            'ASD bibliography codes: L3935,L12369.',
            _ASD_EV,
         )),
    _asd("asd512.ie.as", 33, "Arsenic", "As I", "9.78855", "0.00025",
         notes=(
            'ASD ground shells [Ar].3d10.4s2.4p3, ground level 4S*<3/2>, ionized level 4p2 3P<0>.',
            'ASD bibliography codes: L1351.',
            _ASD_EV,
         )),
    _asd("asd512.ie.se", 34, "Selenium", "Se I", "9.752368", "0.000006",
         notes=(
            'ASD ground shells [Ar].3d10.4s2.4p4, ground level 3P<2>, ionized level 4p3 4S*<3/2>.',
            'ASD bibliography codes: L21645.',
            _ASD_EV,
         )),
    _asd("asd512.ie.br", 35, "Bromine", "Br I", "11.81381", "0.00006",
         notes=(
            'ASD ground shells [Ar].3d10.4s2.4p5, ground level 2P*<3/2>, ionized level 4p4 3P<2>.',
            'ASD bibliography codes: L351,L67.',
            _ASD_EV,
         )),
    _asd("asd512.ie.kr", 36, "Krypton", "Kr I", "13.9996055", "0.0000020",
         notes=(
            'ASD ground shells [Ar].3d10.4s2.4p6, ground level 1S0, ionized level 4p5 2P*<3/2>.',
            'ASD bibliography codes: L12196.',
            _ASD_EV,
         )),
)

INPOP20A_SOURCE = (
    "A. Fienga, L. Bigot, D. Mary, P. Deram, A. Di Ruscio, L. Bernus, M. Gastineau, and J. Laskar, Evolution of INPOP "
    "planetary ephemerides and Bepi-Colombo simulations, Proc. IAU Symposium 364, 31-51, doi:10.1017/S1743921321001277, "
    "arXiv:2111.04499, Table 4."
)
INPOP20A_EDITION = "INPOP20a ephemeris, Proc. IAU Symposium 364"
INPOP20A_URL = "https://doi.org/10.1017/S1743921321001277"
INPOP20A_ARXIV = "https://arxiv.org/abs/2111.04499"
_INPOP20A_WRSS = (
    "Table 4 is captioned: PPN beta and gamma confidence intervals given at 99.7 % of the reference WRSS distribution. "
    "This row is the 3-sigma WRSS selection: 3800 alternative ephemerides with beta and gamma drawn from uniform priors, "
    "each refitted, and the 23% compatible at 99.7% with the INPOP20a residual distribution kept."
)
_INPOP20A_LS = (
    "This row is the direct least-squares fit with beta and gamma added to the 402 other INPOP20a parameters (non-GRT LS). "
    "The caption ties the 99.7% level to the reference WRSS distribution. This row is not a WRSS selection, and the paper names no level for it, so none is assigned."
)
INPOP15A_SOURCE = (
    "A. Fienga, J. Laskar, H. Manche, and M. Gastineau, Tests of GR with INPOP15a planetary ephemerides: estimations of "
    "possible supplementary advances of perihelia for Mercury and Saturn, Proc. 14th Marcel Grossmann Meeting (2017), "
    "pp. 3694-3695, doi:10.1142/9789813226609_0482, arXiv:1601.00947, Table 1."
)
INPOP15A_EDITION = "INPOP15a ephemeris, Proc. 14th Marcel Grossmann Meeting"
INPOP_NOTE_19A = "https://www.imcce.fr/content/medias/recherche/equipes/asd/inpop/inpop19a_20191214.pdf"
INPOP_NOTE_21A = "https://www.imcce.fr/content/medias/recherche/equipes/asd/inpop/inpop21a.pdf"
FIENGA_MINAZZOLI_SOURCE = (
    "A. Fienga and O. Minazzoli, Testing theories of gravity with planetary ephemerides, Living Rev. Relativ. 27, 1 (2024), "
    "doi:10.1007/s41114-023-00047-0, arXiv:2303.01821, Section 4.1.3, Eq. (102)."
)
_FM_OVERLAP = (
    "Printed as the constraint from the common overlap of all the recently published planetary-ephemeris intervals in the review's Table 5. "
    "It is an overlap of intervals with different methods and levels, not a fit, and the review names no confidence level for it."
)

INPOP: tuple[Quantity, ...] = (
    _q("inpop20a.wrss.beta_minus_1", "PPN beta minus one, INPOP20a 3-sigma WRSS selection", "beta - 1", "-1.12 e-5", "7.16 e-5", "",
       kind="99.7% interval", source=INPOP20A_SOURCE, edition=INPOP20A_EDITION, url=INPOP20A_URL, retrieved_from=INPOP20A_ARXIV,
       keys=("inpop", "ppn"), phrases=("ppn beta", "post-newtonian beta"),
       notes=("Printed in Table 4 as (beta - 1) x 10^5 = -1.12 +- 7.16.", _INPOP20A_WRSS)),
    _q("inpop20a.wrss.gamma_minus_1", "PPN gamma minus one, INPOP20a 3-sigma WRSS selection", "gamma - 1", "-1.69 e-5", "7.49 e-5", "",
       kind="99.7% interval", source=INPOP20A_SOURCE, edition=INPOP20A_EDITION, url=INPOP20A_URL, retrieved_from=INPOP20A_ARXIV,
       keys=("inpop", "ppn"), phrases=("ppn gamma", "post-newtonian gamma"),
       notes=("Printed in Table 4 as (gamma - 1) x 10^5 = -1.69 +- 7.49.", _INPOP20A_WRSS)),
    _q("inpop20a.ls.beta_minus_1", "PPN beta minus one, INPOP20a direct least-squares fit", "beta - 1", "-1.9 e-5", "6.28 e-5", "",
       kind="uncertainty as printed, level not stated", source=INPOP20A_SOURCE, edition=INPOP20A_EDITION, url=INPOP20A_URL, retrieved_from=INPOP20A_ARXIV,
       keys=("inpop", "ppn"), phrases=("ppn beta", "post-newtonian beta"),
       notes=("Printed in Table 4 as (beta - 1) x 10^5 = -1.9 +- 6.28.", _INPOP20A_LS,
              "The Living Reviews table (Fienga and Minazzoli 2024, Table 5) prints this entry as 1.9 +- 6.28, with a plus sign. The sign here is the one in the original paper.")),
    _q("inpop20a.ls.gamma_minus_1", "PPN gamma minus one, INPOP20a direct least-squares fit", "gamma - 1", "2.64 e-5", "3.44 e-5", "",
       kind="uncertainty as printed, level not stated", source=INPOP20A_SOURCE, edition=INPOP20A_EDITION, url=INPOP20A_URL, retrieved_from=INPOP20A_ARXIV,
       keys=("inpop", "ppn"), phrases=("ppn gamma", "post-newtonian gamma"),
       notes=("Printed in Table 4 as (gamma - 1) x 10^5 = 2.64 +- 3.44.", _INPOP20A_LS)),
    _q("mercury.inpop15a.extra_perihelion_c1", "possible supplementary advance of Mercury's perihelion, INPOP15a, criterion 1", "varpi_sup Mercury", "0.0", "3.1", "mas per century",
       kind="acceptance interval", source=INPOP15A_SOURCE, edition=INPOP15A_EDITION, url="https://doi.org/10.1142/9789813226609_0482", retrieved_from="https://arxiv.org/abs/1601.00947",
       keys=("mercury", "perihelion", "inpop"), phrases=("perihelion of mercury", "mercury perihelion", "supplementary perihelion"),
       notes=("Printed in Table 1 as (0.0 +- 3.1) mas.cy^-1. The interval holds the supplementary advances whose refitted ephemerides keep postfit residuals within 35% of INPOP15a's, Delta(O - C) < 35%. It is an acceptance range, not a confidence interval.",)),
    _q("mercury.inpop15a.extra_perihelion_c2", "possible supplementary advance of Mercury's perihelion, INPOP15a, criterion 2", "varpi_sup Mercury", "0.0", "1.05", "mas per century",
       kind="acceptance interval", source=INPOP15A_SOURCE, edition=INPOP15A_EDITION, url="https://doi.org/10.1142/9789813226609_0482", retrieved_from="https://arxiv.org/abs/1601.00947",
       keys=("mercury", "perihelion", "inpop"), phrases=("perihelion of mercury", "mercury perihelion", "supplementary perihelion"),
       notes=("Printed in Table 1 as (0.0 +- 1.05) mas.cy^-1, under the tighter criterion Delta(O - C) < 5%. It is an acceptance range, not a confidence interval.",)),
    _q("inpop19a.solar_j2", "solar oblateness J2 fitted in INPOP19a", "J2_sun", "2.010 e-7", "0.010 e-7", "",
       kind="standard uncertainty", source="A. Fienga, P. Deram, V. Viswanathan, A. Di Ruscio, L. Bernus, D. Durante, M. Gastineau, and J. Laskar, INPOP19a planetary ephemerides, Notes Scientifiques et Techniques de l'Institut de mecanique celeste S109 (14 December 2019), ISBN 978-2-910015-81-7, Table 3.",
       edition="INPOP19a, NST IMCCE S109 (2019)", url=INPOP_NOTE_19A, retrieved_from=INPOP_NOTE_19A,
       keys=("inpop",), phrases=("solar quadrupole", "solar oblateness", "solar j2"),
       notes=("Printed in Table 3 as J2 x 10^-7 (2.010 +- 0.010) in a column headed +- 1sigma.",
              "The INPOP19a note gives no PPN beta or gamma. Its Table 3 also prints GM_sun - 132712440000 = 40.042 +- 0.01 km^3 s^-2 for INPOP19a, while the INPOP21a note's Table 2 prints 42.0322 +- 0.13 for INPOP19a. The two IMCCE notes disagree and neither GM value is stored.")),
    _q("inpop21a.solar_j2", "solar oblateness J2 fitted in INPOP21a with the Lense-Thirring term", "J2_sun", "2.2180 e-7", "0.01 e-7", "",
       kind="uncertainty as printed, level not stated", source="A. Fienga, P. Deram, A. Di Ruscio, V. Viswanathan, J. I. B. Camargo, L. Bernus, M. Gastineau, and J. Laskar, INPOP21a planetary ephemerides, Notes Scientifiques et Techniques de l'Institut de mecanique celeste S110 (2021), ISBN 978-2-910015-84-8, Table 1.",
       edition="INPOP21a, NST IMCCE S110 (2021)", url=INPOP_NOTE_21A, retrieved_from=INPOP_NOTE_21A,
       keys=("inpop",), phrases=("solar quadrupole", "solar oblateness", "solar j2"),
       notes=("Printed in Table 1 as J2 x 10^7 = 2.2180 +- 0.01, with S = 1.90 +- 1.5 x 10^48 g cm^-2 s^-1; the text writes (2.2180 +- 0.010) x 10^-7. Table 1 names no confidence level.",
              "The INPOP21a note gives no PPN beta or gamma.")),
    _q("ppn.fienga_minazzoli2024.beta_minus_1", "PPN beta minus one, overlap of planetary-ephemeris intervals", "beta - 1", "-0.45 e-5", "1.75 e-5", "",
       kind="uncertainty as printed, level not stated", source=FIENGA_MINAZZOLI_SOURCE, edition="Living Rev. Relativ. 27 (2024)", url="https://doi.org/10.1007/s41114-023-00047-0", retrieved_from="https://arxiv.org/abs/2303.01821",
       keys=("inpop", "ppn"), phrases=("ppn beta", "post-newtonian beta"), notes=("Printed as (beta - 1) = (-0.45 +- 1.75) x 10^-5.", _FM_OVERLAP)),
    _q("ppn.fienga_minazzoli2024.gamma_minus_1", "PPN gamma minus one, overlap of planetary-ephemeris intervals", "gamma - 1", "0.55 e-5", "1.35 e-5", "",
       kind="uncertainty as printed, level not stated", source=FIENGA_MINAZZOLI_SOURCE, edition="Living Rev. Relativ. 27 (2024)", url="https://doi.org/10.1007/s41114-023-00047-0", retrieved_from="https://arxiv.org/abs/2303.01821",
       keys=("inpop", "ppn"), phrases=("ppn gamma", "post-newtonian gamma"), notes=("Printed as (gamma - 1) = (0.55 +- 1.35) x 10^-5.", _FM_OVERLAP)),
)

AME2020_SOURCE = (
    "W. J. Huang, M. Wang, F. G. Kondev, G. Audi, and S. Naimi, The AME 2020 atomic mass evaluation (I), Chinese Phys. C 45, "
    "030002 (2021), doi:10.1088/1674-1137/abddb0; M. Wang, W. J. Huang, F. G. Kondev, G. Audi, and S. Naimi, The AME 2020 "
    "atomic mass evaluation (II), Chinese Phys. C 45, 030003 (2021), doi:10.1088/1674-1137/abddaf. Values from the AMDC "
    "file mass.mas20, the unrounded version of the published table."
)
AME2020_EDITION = "AME2020, Chinese Phys. C 45 (2021)"
AME2020_FILE = "https://www-nds.iaea.org/amdc/ame2020/mass_1.mas20.txt"
AME2020_PAPER_II = "https://doi.org/10.1088/1674-1137/abddaf"
_AME_SIGMA = "AME2020 Part I, Section 1: all uncertainties are one-standard deviation (1 sigma)."
_AME_FILE = (
    "The printed table in Part II rounds values whose leading uncertainty digit exceeds 3 and writes 'a' for uncertainties below 0.5 eV. "
    "Part II points to the AMDC ASCII file for full precision; the value here is that file's, as written."
)


def _ame(id: str, name: str, symbol: str, value_text: str, uncertainty_text: str, unit: str, *, z: int, n: int, a: int, phrases: tuple[str, ...]) -> Quantity:
    exact = id in {"ame2020.c12.atomic_mass", "ame2020.c12.mass_excess"} and uncertainty_text == "0.0"
    notes = [f"Z = {z}, N = {n}, A = {a}.", _AME_FILE]
    if id.endswith("binding_per_nucleon"):
        notes.insert(1, "Part II defines the tabulated value as B/A = (1/A)[Z M(1H) + N M(n) - M(A, Z)], with atomic masses.")
    if exact:
        notes.insert(1, "AME prints the uncertainty as 0.0. The unified atomic mass unit is defined by 1 u = m(12C)/12, so this value is exact by definition.")
    else:
        notes.insert(1, _AME_SIGMA)
    return _q(
        id,
        name,
        symbol,
        value_text,
        "exact" if exact else uncertainty_text,
        unit,
        kind="exact" if exact else "standard uncertainty",
        source=AME2020_SOURCE,
        edition=AME2020_EDITION,
        url=AME2020_PAPER_II,
        retrieved_from=AME2020_FILE,
        keys=("ame2020",),
        phrases=phrases,
        notes=tuple(notes),
    )


AME2020: tuple[Quantity, ...] = (
    _q("ame2020.u_kev", "energy equivalent of the unified atomic mass unit used in AME2020", "1 u", "931 494.10242", "0.00028", "keV",
       kind="standard uncertainty", source=AME2020_SOURCE.replace("Values from the AMDC file mass.mas20, the unrounded version of the published table.", "Part I, Section 2, units table."),
       edition=AME2020_EDITION, url="https://doi.org/10.1088/1674-1137/abddb0", retrieved_from="https://iopscience.iop.org/article/10.1088/1674-1137/abddb0/pdf",
       keys=("ame2020",), phrases=("atomic mass unit in kev",),
       notes=("Printed in Part I as 1 u = 931 494.10242 +- 0.00028 keV (0.3 ppb), from CODATA 2018 with 2e/h = 483597.8484 GHz/V exact.", _AME_SIGMA)),
    _ame("ame2020.n.atomic_mass", "atomic mass of the neutron", "M(1n)", "1 008664.91590", "0.00047", "micro-u", z=0, n=1, a=1, phrases=('atomic mass of neutron',)),
    _ame("ame2020.n.mass_excess", "mass excess of the neutron", "Delta(1n)", "8071.31806", "0.00044", "keV", z=0, n=1, a=1, phrases=('mass excess of neutron',)),
    _ame("ame2020.h1.atomic_mass", "atomic mass of hydrogen-1", "M(1H)", "1 007825.031898", "0.000014", "micro-u", z=1, n=0, a=1, phrases=('atomic mass of hydrogen-1',)),
    _ame("ame2020.h1.mass_excess", "mass excess of hydrogen-1", "Delta(1H)", "7288.971064", "0.000013", "keV", z=1, n=0, a=1, phrases=('mass excess of hydrogen-1',)),
    _ame("ame2020.h2.atomic_mass", "atomic mass of hydrogen-2", "M(2H)", "2 014101.777844", "0.000015", "micro-u", z=1, n=1, a=2, phrases=('atomic mass of hydrogen-2', 'atomic mass of deuterium')),
    _ame("ame2020.h2.mass_excess", "mass excess of hydrogen-2", "Delta(2H)", "13135.722895", "0.000015", "keV", z=1, n=1, a=2, phrases=('mass excess of hydrogen-2', 'mass excess of deuterium')),
    _ame("ame2020.h2.binding_per_nucleon", "binding energy per nucleon of hydrogen-2", "B/A(2H)", "1112.2831", "0.0002", "keV", z=1, n=1, a=2, phrases=('binding energy per nucleon of hydrogen-2', 'binding energy per nucleon of deuterium')),
    _ame("ame2020.h3.atomic_mass", "atomic mass of hydrogen-3", "M(3H)", "3 016049.28132", "0.00008", "micro-u", z=1, n=2, a=3, phrases=('atomic mass of hydrogen-3', 'atomic mass of tritium')),
    _ame("ame2020.h3.mass_excess", "mass excess of hydrogen-3", "Delta(3H)", "14949.81090", "0.00008", "keV", z=1, n=2, a=3, phrases=('mass excess of hydrogen-3', 'mass excess of tritium')),
    _ame("ame2020.h3.binding_per_nucleon", "binding energy per nucleon of hydrogen-3", "B/A(3H)", "2827.2654", "0.0003", "keV", z=1, n=2, a=3, phrases=('binding energy per nucleon of hydrogen-3', 'binding energy per nucleon of tritium')),
    _ame("ame2020.he3.atomic_mass", "atomic mass of helium-3", "M(3He)", "3 016029.32197", "0.00006", "micro-u", z=2, n=1, a=3, phrases=('atomic mass of helium-3',)),
    _ame("ame2020.he3.mass_excess", "mass excess of helium-3", "Delta(3He)", "14931.21888", "0.00006", "keV", z=2, n=1, a=3, phrases=('mass excess of helium-3',)),
    _ame("ame2020.he3.binding_per_nucleon", "binding energy per nucleon of helium-3", "B/A(3He)", "2572.68044", "0.00015", "keV", z=2, n=1, a=3, phrases=('binding energy per nucleon of helium-3',)),
    _ame("ame2020.he4.atomic_mass", "atomic mass of helium-4", "M(4He)", "4 002603.25413", "0.00016", "micro-u", z=2, n=2, a=4, phrases=('atomic mass of helium-4',)),
    _ame("ame2020.he4.mass_excess", "mass excess of helium-4", "Delta(4He)", "2424.91587", "0.00015", "keV", z=2, n=2, a=4, phrases=('mass excess of helium-4',)),
    _ame("ame2020.he4.binding_per_nucleon", "binding energy per nucleon of helium-4", "B/A(4He)", "7073.9156", "0.0002", "keV", z=2, n=2, a=4, phrases=('binding energy per nucleon of helium-4',)),
    _ame("ame2020.c12.atomic_mass", "atomic mass of carbon-12", "M(12C)", "12 000000.0", "0.0", "micro-u", z=6, n=6, a=12, phrases=('atomic mass of carbon-12',)),
    _ame("ame2020.c12.mass_excess", "mass excess of carbon-12", "Delta(12C)", "0.0", "0.0", "keV", z=6, n=6, a=12, phrases=('mass excess of carbon-12',)),
    _ame("ame2020.c12.binding_per_nucleon", "binding energy per nucleon of carbon-12", "B/A(12C)", "7680.1446", "0.0002", "keV", z=6, n=6, a=12, phrases=('binding energy per nucleon of carbon-12',)),
    _ame("ame2020.o16.atomic_mass", "atomic mass of oxygen-16", "M(16O)", "15 994914.61926", "0.00032", "micro-u", z=8, n=8, a=16, phrases=('atomic mass of oxygen-16',)),
    _ame("ame2020.o16.mass_excess", "mass excess of oxygen-16", "Delta(16O)", "-4737.00217", "0.00030", "keV", z=8, n=8, a=16, phrases=('mass excess of oxygen-16',)),
    _ame("ame2020.o16.binding_per_nucleon", "binding energy per nucleon of oxygen-16", "B/A(16O)", "7976.2072", "0.0002", "keV", z=8, n=8, a=16, phrases=('binding energy per nucleon of oxygen-16',)),
    _ame("ame2020.fe56.atomic_mass", "atomic mass of iron-56", "M(56Fe)", "55 934935.537", "0.287", "micro-u", z=26, n=30, a=56, phrases=('atomic mass of iron-56',)),
    _ame("ame2020.fe56.mass_excess", "mass excess of iron-56", "Delta(56Fe)", "-60607.163", "0.268", "keV", z=26, n=30, a=56, phrases=('mass excess of iron-56',)),
    _ame("ame2020.fe56.binding_per_nucleon", "binding energy per nucleon of iron-56", "B/A(56Fe)", "8790.3563", "0.0048", "keV", z=26, n=30, a=56, phrases=('binding energy per nucleon of iron-56', 'binding energy per nucleon')),
    _ame("ame2020.fe58.atomic_mass", "atomic mass of iron-58", "M(58Fe)", "57 933273.575", "0.339", "micro-u", z=26, n=32, a=58, phrases=('atomic mass of iron-58',)),
    _ame("ame2020.fe58.mass_excess", "mass excess of iron-58", "Delta(58Fe)", "-62155.271", "0.316", "keV", z=26, n=32, a=58, phrases=('mass excess of iron-58',)),
    _ame("ame2020.fe58.binding_per_nucleon", "binding energy per nucleon of iron-58", "B/A(58Fe)", "8792.2534", "0.0055", "keV", z=26, n=32, a=58, phrases=('binding energy per nucleon of iron-58', 'binding energy per nucleon')),
    _ame("ame2020.ni62.atomic_mass", "atomic mass of nickel-62", "M(62Ni)", "61 928344.753", "0.455", "micro-u", z=28, n=34, a=62, phrases=('atomic mass of nickel-62',)),
    _ame("ame2020.ni62.mass_excess", "mass excess of nickel-62", "Delta(62Ni)", "-66746.440", "0.425", "keV", z=28, n=34, a=62, phrases=('mass excess of nickel-62',)),
    _ame("ame2020.ni62.binding_per_nucleon", "binding energy per nucleon of nickel-62", "B/A(62Ni)", "8794.5555", "0.0069", "keV", z=28, n=34, a=62, phrases=('binding energy per nucleon of nickel-62', 'binding energy per nucleon')),
    _ame("ame2020.pb208.atomic_mass", "atomic mass of lead-208", "M(208Pb)", "207 976652.005", "1.232", "micro-u", z=82, n=126, a=208, phrases=('atomic mass of lead-208',)),
    _ame("ame2020.pb208.mass_excess", "mass excess of lead-208", "Delta(208Pb)", "-21748.519", "1.148", "keV", z=82, n=126, a=208, phrases=('mass excess of lead-208',)),
    _ame("ame2020.pb208.binding_per_nucleon", "binding energy per nucleon of lead-208", "B/A(208Pb)", "7867.4530", "0.0055", "keV", z=82, n=126, a=208, phrases=('binding energy per nucleon of lead-208',)),
)

_FIT = "PDG 2026 OUR FIT value, the summary value PDG lists first for this mass."
_SF = "The error includes a scale factor of {0}."

PDG_2026_HADRONS: tuple[Quantity, ...] = (
    _pdg("pdg2026.m_pi_charged", "charged pion mass", "m_pi+-", "139.57039", "0.00018", "MeV", node="S008M", phrases=("charged pion mass", "pion mass", "mass of the pion"), notes=(_FIT, _SF.format("1.8"), "PDG's OUR AVERAGE for the same mass is 139.57039 +- 0.00017 MeV (S = 1.6).", _API_NOTE)),
    _pdg("pdg2026.m_pi0", "neutral pion mass", "m_pi0", "134.9768", "0.0005", "MeV", node="S009M", phrases=("neutral pion mass", "pion mass", "pi0 mass"), notes=(_FIT, _SF.format("1.1"), _API_NOTE)),
    _pdg("pdg2026.m_k_charged", "charged kaon mass", "m_K+-", "493.677", "0.015", "MeV", node="S010M", phrases=("charged kaon mass", "kaon mass", "mass of the kaon"), notes=(_FIT, _SF.format("2.8"), "PDG's OUR AVERAGE for the same mass is 493.677 +- 0.013 MeV (S = 2.4).", _API_NOTE)),
    _pdg("pdg2026.m_k0", "neutral kaon mass", "m_K0", "497.611", "0.013", "MeV", node="S011M", phrases=("neutral kaon mass", "kaon mass", "k0 mass"), notes=(_FIT, _SF.format("1.2"), _API_NOTE)),
    _pdg("pdg2026.m_eta", "eta meson mass", "m_eta", "547.862", "0.017", "MeV", node="S014M", phrases=("eta mass", "eta meson"), notes=("PDG 2026 OUR AVERAGE.", _API_NOTE)),
    _pdg("pdg2026.m_rho770", "rho(770) mass, neutral only, e+ e-", "m_rho(770)", "775.26", "0.23", "MeV", node="M009M0", phrases=("rho mass", "rho(770)", "rho meson"), notes=("PDG 2026 OUR AVERAGE for the neutral rho from e+ e- data. PDG lists other averages by charge and reaction: mixed charges, other reactions 763.0 +- 1.2; neutral photoproduced 769.6 +- 0.8; neutral other reactions 769.0 +- 0.9 MeV. Only the e+ e- value is stored. A broad resonance's mass depends on how it is extracted.", _API_NOTE)),
    _pdg("pdg2026.m_omega782", "omega(782) mass", "m_omega(782)", "782.66", "0.13", "MeV", node="M001M", phrases=("omega mass", "omega(782)", "omega meson"), notes=("PDG 2026 OUR AVERAGE.", _SF.format("2.0"), _API_NOTE)),
    _pdg("pdg2026.m_p", "proton mass", "m_p", "938.27208943", "0.00000029", "MeV", node="S016M", phrases=("proton mass", "mass of the proton"), notes=("PDG 2026 OUR EVALUATION, taken from CODATA 2022.", _API_NOTE)),
    _pdg("pdg2026.m_n", "neutron mass", "m_n", "939.5654219", "0.0000005", "MeV", node="S017M", phrases=("neutron mass", "mass of the neutron"), notes=("PDG 2026 OUR AVERAGE, printed as 939.5654219 +- 0.0000005 MeV.", _API_NOTE)),
    _pdg("pdg2026.m_lambda", "Lambda baryon mass", "m_Lambda", "1115.683", "0.006", "MeV", node="S018M", phrases=("lambda mass", "lambda baryon", "mass of the lambda"), notes=(_FIT, _API_NOTE)),
    _pdg("pdg2026.m_delta1232", "Delta(1232) Breit-Wigner mass, mixed charges", "m_Delta(1232)", "1232", "2", "MeV", node="B033M", kind="PDG estimated range", phrases=("delta mass", "delta(1232)", "delta baryon"), notes=("PDG prints this as 1230 TO 1232 TO 1234 MeV, its estimate of the range, not a statistical uncertainty. It is stored as 1232 with the half-width of the printed range.", _API_NOTE)),
    _pdg("pdg2026.m_n_minus_m_p", "neutron-proton mass difference", "m_n - m_p", "1.2933325", "0.0000004", "MeV", node="S017D", phrases=("neutron-proton mass difference", "neutron proton mass difference", "m_n - m_p"), notes=("PDG 2026 OUR AVERAGE of the measured difference. It is not computed from the two masses.", _API_NOTE)),
)

WEISBERG_2016_SOURCE = (
    "J. M. Weisberg and Y. Huang, Relativistic Measurements from Timing the Binary Pulsar PSR B1913+16, "
    "Astrophys. J. 829, 55 (2016), doi:10.3847/0004-637X/829/1/55, arXiv:1606.02744, Eq. (23)."
)
KRAMER_2021_SOURCE = (
    "M. Kramer et al., Strong-Field Gravity Tests with the Double Pulsar, Phys. Rev. X 11, 041050 (2021), "
    "doi:10.1103/PhysRevX.11.041050, arXiv:2112.06795, Table V."
)
_KRAMER_LEVEL = (
    "Table V prints the ratio with its uncertainty in parentheses and does not name the level. The paper states the Pb-dot test "
    "as agreement at 1.3 x 10^-4 with 95% confidence. No level is assigned here."
)
_RATIO_NOTE = "The ratio is the paper's own comparison of an observed quantity with the general-relativity prediction the paper computes. No prediction is stored on the board."
GPB_SOURCE = (
    "C. W. F. Everitt et al., Gravity Probe B: Final Results of a Space Experiment to Test General Relativity, "
    "Phys. Rev. Lett. 106, 221101 (2011), doi:10.1103/PhysRevLett.106.221101, arXiv:1105.3456, Table II."
)
_GPB_SIGMA = "The paper states that the 1 sigma uncertainties of the joint result in Table II are the square roots of the diagonal of the total covariance matrix: statistical, sensitivity, and unmodeled systematic."
LAMBERT_2011_SOURCE = (
    "S. B. Lambert and C. Le Poncin-Lafitte, Improved determination of gamma by VLBI, Astron. Astrophys. 529, A70 (2011), "
    "doi:10.1051/0004-6361/201016370, open copy hal-03785812."
)
CODATA_2022_G_SOURCE = (
    "P. J. Mohr, D. B. Newell, B. N. Taylor, and E. Tiesinga, CODATA recommended values of the fundamental physical constants: 2022, "
    "Rev. Mod. Phys. 97, 025002 (2025), doi:10.1103/RevModPhys.97.025002, arXiv:2409.03787, Table XXX."
)


def _g_input(key: str, reference: str, label: str, method: str, value_text: str, uncertainty_text: str, printed: str) -> Quantity:
    return _q(
        f"g_input.{key}",
        f"Newtonian constant of gravitation, {label}",
        "G",
        value_text,
        uncertainty_text,
        "m^3 kg^-1 s^-2",
        kind="standard uncertainty",
        printed=printed,
        source=CODATA_2022_G_SOURCE + f" Original measurement: {reference}.",
        edition="CODATA 2022 input datum " + label,
        url="https://doi.org/10.1103/RevModPhys.97.025002",
        retrieved_from="https://arxiv.org/abs/2409.03787",
        keys=("big-g",),
        phrases=("measurements of big g", "big g", "big-g", "gravitational constant measurements"),
        notes=(
            f"Method: {method}. CODATA 2022 Table XXX lists it as one of the 16 input data for G, unchanged since the 2018 adjustment.",
            "CODATA's Fig. 4 caption: error bars correspond to one-standard-deviation uncertainties as reported in Table XXX.",
            "Correlations in the table caption: r(NIST-82, LANL-97) = 0.351, r(HUST-05, HUST-09) = 0.134, r(HUST-09, HUST_T-18) = 0.068.",
        ),
    )


GRAVITY_TESTS: tuple[Quantity, ...] = (
    _q("psr_b1913.pbdot_ratio", "PSR B1913+16 intrinsic orbital decay over the GR prediction", "Pb_dot_intr / Pb_dot_GR", "0.9983", "0.0016", "",
       kind="uncertainty as printed, level not stated", source=WEISBERG_2016_SOURCE, edition="ApJ 829:55 (2016)",
       url="https://doi.org/10.3847/0004-637X/829/1/55", retrieved_from="https://arxiv.org/abs/1606.02744",
       keys=("hulse-taylor", "b1913+16"), phrases=("hulse-taylor", "hulse taylor", "binary pulsar", "orbital decay"),
       notes=("Printed as (-2.398 +- 0.004) x 10^-12 over (-2.40263 +- 0.00005) x 10^-12 = 0.9983 +- 0.0016, the observed decay corrected by a kinematic term. The paper calls this within about 1 sigma of the GR rate but does not name the level of the +- itself.", _RATIO_NOTE)),
) + tuple(
    _q(f"double_pulsar.{key}_ratio", f"Double Pulsar {name}, observed over GR prediction", f"{symbol} obs/GR", value, unc, "",
       kind="uncertainty as printed, level not stated", printed=printed, source=KRAMER_2021_SOURCE, edition="Phys. Rev. X 11 (2021)",
       url="https://doi.org/10.1103/PhysRevX.11.041050", retrieved_from="https://arxiv.org/abs/2112.06795",
       keys=("j0737-3039",), phrases=("double pulsar",) + extra,
       notes=(f"Table V prints {printed}.", _KRAMER_LEVEL, _RATIO_NOTE))
    for key, name, symbol, value, unc, printed, extra in (
        ("pbdot", "orbital period decay from GW emission", "Pb_dot", "0.999963", "0.000063", "0.999963(63)", ("orbital decay",)),
        ("omdot", "periastron advance", "omega_dot", "1.000015", "0.000026", "1.000015(26)", ()),
        ("shapiro_s", "Shapiro delay shape", "s", "1.00009", "0.00018", "1.00009(18)", ()),
        ("shapiro_r", "Shapiro delay range", "r", "1.0016", "0.0034", "1.0016(34)", ()),
        ("gamma_e", "time dilation parameter", "gamma_E", "1.00012", "0.00025", "1.00012(25)", ()),
    )
) + (
    _q("gpb.geodetic", "Gravity Probe B geodetic drift rate, joint four-gyroscope result", "r_NS", "-6601.8", "18.3", "mas/yr",
       kind="standard uncertainty", source=GPB_SOURCE, edition="Phys. Rev. Lett. 106 (2011)", url="https://doi.org/10.1103/PhysRevLett.106.221101",
       retrieved_from="https://arxiv.org/abs/1105.3456", keys=("gravity-probe-b",), phrases=("gravity probe b", "geodetic effect", "geodetic drift"),
       notes=("Printed as -6,601.8 +- 18.3 mas/yr. The paper sets it beside its GR prediction, -6,606.1 mas/yr, which is not stored.", _GPB_SIGMA)),
    _q("gpb.frame_dragging", "Gravity Probe B frame-dragging drift rate, joint four-gyroscope result", "r_WE", "-37.2", "7.2", "mas/yr",
       kind="standard uncertainty", source=GPB_SOURCE, edition="Phys. Rev. Lett. 106 (2011)", url="https://doi.org/10.1103/PhysRevLett.106.221101",
       retrieved_from="https://arxiv.org/abs/1105.3456", keys=("gravity-probe-b",), phrases=("gravity probe b", "frame dragging", "frame-dragging", "lense-thirring"),
       notes=("Printed as -37.2 +- 7.2 mas/yr. The paper sets it beside its GR prediction, -39.2 mas/yr, which is not stored.", _GPB_SIGMA)),
    _q("vlbi.lambert2011.gamma", "PPN gamma from VLBI light deflection, solution S5", "gamma", "0.99992", "0.00012", "",
       kind="uncertainty as printed, level not stated", source=LAMBERT_2011_SOURCE, edition="A&A 529, A70 (2011)",
       url="https://doi.org/10.1051/0004-6361/201016370", retrieved_from="https://hal.science/hal-03785812",
       keys=("vlbi", "ppn"), phrases=("ppn gamma", "post-newtonian gamma", "light deflection"),
       notes=("Printed in the abstract as gamma = 0.99992 +- 0.00012, from more than seven million group delays, August 1979 to August 2010, least-squares fitted. The paper calls the uncertainty the formal error and names no level.", "The 2009 paper by the same authors gave 0.99984 +- 0.00015, not stored.")),
) + (
    _g_input("nist82", "Luther and Towler (1982)", "NIST-82", "Fiber torsion balance, dynamic mode", "6.672 48 e-11", "0.000 43 e-11", "6.672 48(43) e-11"),
    _g_input("trd96", "Karagioz and Izmailov (1996)", "TR&D-96", "Fiber torsion balance, dynamic mode", "6.672 9 e-11", "0.000 5 e-11", "6.672 9(5) e-11"),
    _g_input("lanl97", "Bagley and Luther (1997)", "LANL-97", "Fiber torsion balance, dynamic mode", "6.673 98 e-11", "0.000 70 e-11", "6.673 98(70) e-11"),
    _g_input("uwash00", "Gundlach and Merkowitz (2000); Gundlach and Merkowitz (2002)", "UWash-00", "Fiber torsion balance, dynamic compensation", "6.674 255 e-11", "0.000 092 e-11", "6.674 255(92) e-11"),
    _g_input("bipm01", "Quinn et al. (2001)", "BIPM-01", "Strip torsion balance, compensation mode, static deflection", "6.675 59 e-11", "0.000 27 e-11", "6.675 59(27) e-11"),
    _g_input("uwup02", "Kleinevoss (2002); Kleinevoss et al. (2002)", "UWup-02", "Suspended body, displacement", "6.674 22 e-11", "0.000 98 e-11", "6.674 22(98) e-11"),
    _g_input("msl03", "Armstrong and Fitzgerald (2003)", "MSL-03", "Strip torsion balance, compensation mode", "6.673 87 e-11", "0.000 27 e-11", "6.673 87(27) e-11"),
    _g_input("hust05", "Hu et al. (2005)", "HUST-05", "Fiber torsion balance, dynamic mode", "6.672 22 e-11", "0.000 87 e-11", "6.672 22(87) e-11"),
    _g_input("uzur06", "Schlamminger et al. (2006)", "UZur-06", "Stationary body, weight change", "6.674 25 e-11", "0.000 12 e-11", "6.674 25(12) e-11"),
    _g_input("hust09", "Luo et al. (2009); Tu et al. (2010)", "HUST-09", "Fiber torsion balance, dynamic mode", "6.673 49 e-11", "0.000 18 e-11", "6.673 49(18) e-11"),
    _g_input("bipm14", "Quinn et al. (2013, 2014)", "BIPM-14", "Strip torsion balance, compensation mode, static deflection", "6.675 54 e-11", "0.000 16 e-11", "6.675 54(16) e-11"),
    _g_input("lens14", "Prevedelli et al. (2014); Rosi et al. (2014)", "LENS-14", "Double atom interferometer, gravity gradiometer", "6.671 91 e-11", "0.000 99 e-11", "6.671 91(99) e-11"),
    _g_input("uci14", "Newman et al. (2014)", "UCI-14", "Cryogenic torsion balance, dynamic mode", "6.674 35 e-11", "0.000 13 e-11", "6.674 35(13) e-11"),
    _g_input("hustt18", "Li et al. (2018)", "HUST_T-18", "Fiber torsion balance, dynamic mode", "6.674 184 e-11", "0.000 078 e-11", "6.674 184(78) e-11"),
    _g_input("husta18", "Li et al. (2018)", "HUST_A-18", "Fiber torsion balance, dynamic compensation", "6.674 484 e-11", "0.000 077 e-11", "6.674 484(77) e-11"),
    _g_input("jila18", "Parks and Faller (2019)", "JILA-18", "Suspended body, displacement", "6.672 60 e-11", "0.000 25 e-11", "6.672 60(25) e-11"),
)

PARTHEY_2011_SOURCE = (
    "C. G. Parthey et al., Improved Measurement of the Hydrogen 1S-2S Transition Frequency, Phys. Rev. Lett. 107, 203001 (2011), "
    "doi:10.1103/PhysRevLett.107.203001, arXiv:1107.3101."
)
_CODATA_TABLE_XI = "Listed as an input datum in CODATA 2022 (Rev. Mod. Phys. 97, 025002 (2025), arXiv:2409.03787) Table XI, with its relative standard uncertainty."
ANTOGNINI_2013_SOURCE = (
    "A. Antognini et al., Proton Structure from the Measurement of 2S-2P Transition Frequencies of Muonic Hydrogen, "
    "Science 339, 417-420 (2013), doi:10.1126/science.1230016, abstract as indexed in PubMed 23349284."
)
_ANTOGNINI_SIGMA = "The abstract states that numbers in parentheses indicate one standard deviation of uncertainty."
HELLWIG_1970_SOURCE = (
    "H. Hellwig, R. F. C. Vessot, M. W. Levine, P. W. Zitzewitz, D. W. Allan, and D. J. Glaze, Measurement of the Unperturbed "
    "Hydrogen Hyperfine Transition Frequency, IEEE Trans. Instrum. Meas. IM-19, 200-209 (1970), doi:10.1109/TIM.1970.4313902, Section IV."
)
ASD_HALPHA_QUERY = (
    "https://physics.nist.gov/cgi-bin/ASD/lines1.pl?spectra=H+I&limits_type=0&low_w=656.2&upp_w=656.3&unit=1&submit=Retrieve+Data"
    "&de=0&format=2&line_out=0&remove_js=on&en_unit=0&output=0&bibrefs=1&page_size=15&show_obs_wl=1&show_calc_wl=1&unc_out=1"
    "&order_out=0&show_av=2&tsb_value=0&A_out=0&intens_out=on&allowed_out=1&forbid_out=1&conf_out=on&term_out=on&enrg_out=on&J_out=on"
)
_HALPHA_NOTE = "Wavelengths are in standard air, as ASD serves them with show_av=2. ASD does not name a confidence level for its wavelength uncertainties."


def _codata_xi(id: str, name: str, symbol: str, value_text: str, uncertainty_text: str, unit: str, printed: str, reference: str, lab: str, *, phrases: tuple[str, ...], notes: tuple[str, ...] = ()) -> Quantity:
    return _q(
        id, name, symbol, value_text, uncertainty_text, unit,
        kind="standard uncertainty", printed=printed,
        source=CODATA_2022_G_SOURCE.replace("Table XXX.", f"Table XI, {lab}. Original measurement: {reference}."),
        edition=f"CODATA 2022 input datum, {lab}",
        url="https://doi.org/10.1103/RevModPhys.97.025002", retrieved_from="https://arxiv.org/abs/2409.03787",
        phrases=("hydrogen spectroscopy",) + phrases, notes=notes,
    )


ATOMIC_SPECTROSCOPY: tuple[Quantity, ...] = (
    _q("parthey2011.h_1s2s", "hydrogen 1S-2S transition frequency, hyperfine centroid", "f_1S-2S", "2 466 061 413 187 035", "10", "Hz",
       kind="standard uncertainty", printed="2 466 061 413 187 035(10)", source=PARTHEY_2011_SOURCE, edition="Phys. Rev. Lett. 107 (2011)",
       url="https://doi.org/10.1103/PhysRevLett.107.203001", retrieved_from="https://arxiv.org/abs/1107.3101",
       phrases=("hydrogen spectroscopy", "1s-2s", "1s - 2s", "1s2s"),
       notes=("Printed as f_1S-2S = 2 466 061 413 187 035 (10) Hz, a fractional uncertainty of 4.2 x 10^-15. The paper's Table I is headed 'sigma - uncertainty'.", _CODATA_TABLE_XI + " Label A6.")),
    _codata_xi("matveev2013.h_1s2s", "hydrogen 1S-2S transition frequency, fiber-link remeasurement", "f_1S-2S", "2 466 061 413 187.018", "0.011", "kHz",
       "2 466 061 413 187.018(11)", "Matveev et al. (2013), Phys. Rev. Lett. 110, 230801, doi:10.1103/PhysRevLett.110.230801", "MPQ, label A7",
       phrases=("1s-2s", "1s - 2s", "1s2s"), notes=("Printed in Table XI as 2 466 061 413 187.018(11) kHz.",)),
    _codata_xi("bezginov2019.h_lamb_shift", "hydrogen n = 2 Lamb shift, 2P1/2 - 2S1/2", "Delta E_H(2P1/2 - 2S1/2)/h", "1 057 829.8", "3.2", "kHz",
       "1 057 829.8(3.2)", "Bezginov et al. (2019), Science 365, 1007, doi:10.1126/science.aau7807", "York, label A29",
       phrases=("lamb shift",), notes=("Printed in Table XI as 1 057 829.8(3.2) kHz. The Science abstract gives only the proton radius it implies, r_p = 0.833 +- 0.010 fm; the interval itself is taken from CODATA's table.",)),
    _codata_xi("lundeen1981.h_lamb_shift", "hydrogen n = 2 Lamb shift, 2P1/2 - 2S1/2, Harvard", "Delta E_H(2P1/2 - 2S1/2)/h", "1 057 845.0", "9.0", "kHz",
       "1 057 845.0(9.0)", "Lundeen and Pipkin (1981), Phys. Rev. Lett. 46, 232, doi:10.1103/PhysRevLett.46.232", "Harvard, label A27",
       phrases=("lamb shift",), notes=("Printed in Table XI as 1 057 845.0(9.0) kHz.",)),
    _q("hellwig1970.h_21cm", "unperturbed hydrogen ground-state hyperfine frequency (21 cm line)", "nu_H", "1 420 405 751.768", "0.002", "Hz",
       kind="standard uncertainty", source=HELLWIG_1970_SOURCE, edition="IEEE Trans. Instrum. Meas. IM-19 (1970)",
       url="https://doi.org/10.1109/TIM.1970.4313902", retrieved_from="https://tf.nist.gov/general/pdf/13.pdf",
       phrases=("hydrogen spectroscopy", "21 cm", "21-cm", "hydrogen hyperfine", "hyperfine frequency of hydrogen", "hydrogen maser"),
       notes=("Printed in the Conclusions as nu_H = 1420 405 751.768 +- 0.002 Hz, the mean of two independent wall-shift evaluations against the cesium definition.",
              "The abstract calls the uncertainty one-sigma. In the NIST scan its exponent reads '2 X 10-2 Hz'; the Conclusions print +- 0.002 Hz, and that is the value stored.")),
    _q("asd512.h_alpha.blend", "hydrogen Balmer H-alpha, n = 2 - 3, observed air wavelength of the blend", "lambda_air(H-alpha)", "656.279", "0.003", "nm",
       kind="uncertainty as printed, level not stated", source=ASD_SOURCE.replace("Ionization Energies Data.", "Lines Data, H I."), edition=ASD_EDITION,
       url=ASD_HALPHA_QUERY, retrieved_from=ASD_HALPHA_QUERY, keys=("balmer",), phrases=("h-alpha", "h alpha", "balmer alpha", "hydrogen alpha"),
       notes=("ASD row with lower level 2 and upper level 3, relative intensity 500000, A_ki = 4.4101e+07 s^-1, references T8637 and L7400c29.", _HALPHA_NOTE)),
    _q("asd512.h_alpha.blend_ritz", "hydrogen Balmer H-alpha, n = 2 - 3, Ritz air wavelength of the blend", "lambda_Ritz,air(H-alpha)", "656.2819", "0.0007", "nm",
       kind="uncertainty as printed, level not stated", source=ASD_SOURCE.replace("Ionization Energies Data.", "Lines Data, H I."), edition=ASD_EDITION,
       url=ASD_HALPHA_QUERY, retrieved_from=ASD_HALPHA_QUERY, keys=("balmer",), phrases=("h-alpha", "h alpha", "balmer alpha", "hydrogen alpha"),
       notes=("Same ASD row as asd512.h_alpha.blend: the Ritz wavelength computed by ASD from the level energies.", _HALPHA_NOTE)),
    _q("asd512.h_alpha.2p32_3d52", "hydrogen H-alpha strongest fine-structure component, 2p 2P3/2 - 3d 2D5/2", "lambda_air", "656.285175", "0.000007", "nm",
       kind="uncertainty as printed, level not stated", source=ASD_SOURCE.replace("Ionization Energies Data.", "Lines Data, H I."), edition=ASD_EDITION,
       url=ASD_HALPHA_QUERY, retrieved_from=ASD_HALPHA_QUERY, keys=("balmer",), phrases=("h-alpha", "h alpha", "balmer alpha", "hydrogen alpha"),
       notes=("Observed air wavelength; ASD's Ritz value is 656.285177(3) nm. A_ki = 6.4651e+07 s^-1, the largest in the multiplet. References T7771 and L2752.", _HALPHA_NOTE)),
    _q("antognini2013.mu_h_f0_f1", "muonic hydrogen 2S1/2(F=0) - 2P3/2(F=1) transition frequency", "nu_s", "54611.16", "1.05", "GHz",
       kind="standard uncertainty", printed="54611.16(1.05)", source=ANTOGNINI_2013_SOURCE, edition="Science 339 (2013)",
       url="https://doi.org/10.1126/science.1230016", retrieved_from="https://pubmed.ncbi.nlm.nih.gov/23349284/",
       keys=("muonic",), phrases=("muonic hydrogen", "muonic-hydrogen"), notes=("Printed as 54611.16(1.05) gigahertz.", _ANTOGNINI_SIGMA)),
    _q("antognini2013.mu_h_f1_f2", "muonic hydrogen 2S1/2(F=1) - 2P3/2(F=2) transition frequency, reevaluated", "nu_t", "49881.35", "0.65", "GHz",
       kind="standard uncertainty", printed="49881.35(65)", source=ANTOGNINI_2013_SOURCE, edition="Science 339 (2013)",
       url="https://doi.org/10.1126/science.1230016", retrieved_from="https://pubmed.ncbi.nlm.nih.gov/23349284/",
       keys=("muonic",), phrases=("muonic hydrogen", "muonic-hydrogen"), notes=("Printed as 49881.35(65) gigahertz, a reevaluation of the 2010 measurement.", _ANTOGNINI_SIGMA)),
    _q("antognini2013.proton_charge_radius", "proton charge radius from muonic hydrogen", "r_E", "0.84087", "0.00039", "fm",
       kind="standard uncertainty", printed="0.84087(39)", source=ANTOGNINI_2013_SOURCE, edition="Science 339 (2013)",
       url="https://doi.org/10.1126/science.1230016", retrieved_from="https://pubmed.ncbi.nlm.nih.gov/23349284/",
       keys=("muonic",), phrases=("muonic hydrogen", "proton charge radius", "proton radius"),
       notes=("Printed as r(E) = 0.84087(39) femtometer. The abstract says this is at 7 sigma variance with the 2010 CODATA value, which is not stored.", _ANTOGNINI_SIGMA)),
    _q("antognini2013.proton_zemach_radius", "proton Zemach radius from muonic hydrogen", "r_Z", "1.082", "0.037", "fm",
       kind="standard uncertainty", printed="1.082(37)", source=ANTOGNINI_2013_SOURCE, edition="Science 339 (2013)",
       url="https://doi.org/10.1126/science.1230016", retrieved_from="https://pubmed.ncbi.nlm.nih.gov/23349284/",
       keys=("muonic",), phrases=("muonic hydrogen", "zemach radius"), notes=("Printed as r(Z) = 1.082(37) femtometers.", _ANTOGNINI_SIGMA)),
    _q("crema2013.mu_h_lamb_shift", "muonic hydrogen Lamb shift, experimental", "E_L(mu H)", "202.3706", "0.0023", "meV",
       kind="standard uncertainty", printed="202.3706(23)", source=CODATA_2022_G_SOURCE.replace("Table XXX.", "Table XIV, label C1. Original measurement: Antognini et al. (2013), Science 339, 417 (CREMA-13)."),
       edition="CODATA 2022 input datum, CREMA-13", url="https://doi.org/10.1103/RevModPhys.97.025002", retrieved_from="https://arxiv.org/abs/2409.03787",
       keys=("muonic",), phrases=("muonic hydrogen lamb shift", "muonic lamb shift", "muonic hydrogen"),
       notes=("Printed in CODATA 2022 Table XIV as E_L^(exp)(mu H) = 202.3706(23) meV, relative standard uncertainty 1.1 x 10^-5. The Science abstract does not print the Lamb shift, and the paper body was not reachable, so the value is taken from CODATA's input table.",)),
)

_NUCLEAR = ("nuclear",)

NUCLEAR_CODATA: tuple[Quantity, ...] = (
    _q("codata2022.e_b_deuteron", "deuteron binding energy", "E_B(d)", "2224.566 40", "0.000 38", "keV",
       kind="standard uncertainty", printed="2224.566 40(38)",
       source=CODATA_2022_G_SOURCE.replace("Table XXX.", "Sec. II.B, text after Eq. (7)."), edition=CODATA_2022_EDITION,
       url="https://doi.org/10.1103/RevModPhys.97.025002", retrieved_from="https://arxiv.org/abs/2409.03787",
       keys=_NUCLEAR, phrases=("deuteron binding", "binding energy of the deuteron"),
       notes=("Printed as 'We find E_B(d) = 2224.566 40(38) keV with a relative uncertainty of 1.7 x 10^-7.' It follows from the Kessler et al. (1999) neutron-capture gamma-ray wavelength, input datum D14. The NIST constants table has no separate entry for it.",)),
    _codata("codata2022.m_d", "deuteron mass", "m_d", "3.343 583 7768 e-27", "0.000 000 0010 e-27", "kg", "md",
            keys=_NUCLEAR, phrases=("deuteron mass",)),
    _codata("codata2022.m_d_u", "deuteron mass in u", "m_d", "2.013 553 212 544", "0.000 000 000 015", "u", "mdu",
            keys=_NUCLEAR, phrases=("deuteron mass",)),
    _codata("codata2022.m_d_c2_mev", "deuteron mass energy equivalent in MeV", "m_d c^2", "1875.612 945 00", "0.000 000 58", "MeV", "mdc2mev",
            keys=_NUCLEAR, phrases=("deuteron mass",)),
    _codata("codata2022.m_alpha", "alpha particle mass", "m_alpha", "6.644 657 3450 e-27", "0.000 000 0021 e-27", "kg", "mal",
            keys=_NUCLEAR, phrases=("alpha particle mass", "alpha-particle mass", "helium-4 nucleus")),
    _codata("codata2022.m_alpha_u", "alpha particle mass in u", "m_alpha", "4.001 506 179 129", "0.000 000 000 062", "u", "malu",
            keys=_NUCLEAR, phrases=("alpha particle mass", "alpha-particle mass", "helium-4 nucleus")),
    _codata("codata2022.m_alpha_c2_mev", "alpha particle mass energy equivalent in MeV", "m_alpha c^2", "3727.379 4118", "0.000 0012", "MeV", "malc2mev",
            keys=_NUCLEAR, phrases=("alpha particle mass", "alpha-particle mass", "helium-4 nucleus")),
    _codata("codata2022.mu_n_nuclear", "nuclear magneton", "mu_N", "5.050 783 7393 e-27", "0.000 000 0016 e-27", "J T^-1", "mun",
            keys=("magneton",), phrases=("nuclear magneton",)),
    _codata("codata2022.mu_p", "proton magnetic moment", "mu_p", "1.410 606 795 45 e-26", "0.000 000 000 60 e-26", "J T^-1", "mup",
            keys=_NUCLEAR, phrases=("proton magnetic moment", "magnetic moment of the proton", "nucleon magnetic moment")),
    _codata("codata2022.mu_n", "neutron magnetic moment", "mu_n", "-9.662 3653 e-27", "0.000 0023 e-27", "J T^-1", "munn",
            keys=_NUCLEAR, phrases=("neutron magnetic moment", "magnetic moment of the neutron", "nucleon magnetic moment")),
    _codata("codata2022.mu_p_over_mu_n_nuclear", "proton magnetic moment to nuclear magneton ratio", "mu_p/mu_N", "2.792 847 344 63", "0.000 000 000 82", "", "mupsmun",
            keys=_NUCLEAR, phrases=("proton magnetic moment", "nucleon magnetic moment")),
    _codata("codata2022.mu_n_over_mu_n_nuclear", "neutron magnetic moment to nuclear magneton ratio", "mu_n/mu_N", "-1.913 042 76", "0.000 000 45", "", "munsmun",
            keys=_NUCLEAR, phrases=("neutron magnetic moment", "nucleon magnetic moment")),
    _codata("codata2022.mu_n_over_mu_p", "neutron-proton magnetic moment ratio", "mu_n/mu_p", "-0.684 979 35", "0.000 000 16", "", "munsmup",
            keys=_NUCLEAR, phrases=("neutron magnetic moment", "proton magnetic moment", "nucleon magnetic moment")),
)

QUANTITIES: tuple[Quantity, ...] = (
    CODATA_2022 + PDG_2026 + MERCURY + MERCURY_MODERN + GW150914 + PLANCK_2018 + SH0ES_2022 + DESI_DR2 + FIXSEN_2009
    + PARTICLE_PRECISION + ASD_IONIZATION + INPOP + AME2020 + PDG_2026_HADRONS + GRAVITY_TESTS + ATOMIC_SPECTROSCOPY + NUCLEAR_CODATA
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


_BINPOP_SOURCE = (
    "V. Mariani, O. Minazzoli, A. Fienga, J. Laskar, and M. Gastineau, Bayesian test of Brans-Dicke theories with planetary "
    "ephemerides: Investigating the strong equivalence principle, Astron. Astrophys. 682, A175 (2024), "
    "doi:10.1051/0004-6361/202348082, arXiv:2310.00719, Section 3.1 and Fig. 1."
)
_BINPOP_CONDITIONS = (
    "INPOP21a planetary ephemeris, refitted inside an MCMC (B-INPOP), without strong-equivalence-principle violation (eta = 0).",
    "The prior for 1 - gamma is uniform between 0 and 15 x 10^-5, so only gamma <= 1 is explored and the lower end is the prior edge, not a measurement.",
    "The paper states the limits as C.L. of the MCMC posterior: 1.73 x 10^-5 at 66.7%, 2.40 x 10^-5 at 95%, and 2.50 x 10^-5 at 99.7%.",
)


def _binpop(level: str, upper: str) -> Bound:
    return Bound(
        id=f"bound.binpop21a.one_minus_gamma_{level.replace('.', '_')}",
        name=f"PPN 1 - gamma upper limit at {level}% C.L. from the B-INPOP posterior",
        symbol="1 - gamma",
        lower_text="0",
        upper_text=upper,
        unit="",
        source=_BINPOP_SOURCE,
        edition="INPOP21a with B-INPOP, A&A 682 A175 (2024)",
        url="https://doi.org/10.1051/0004-6361/202348082",
        retrieved_from="https://arxiv.org/abs/2310.00719",
        retrieved=RETRIEVED,
        keys=("inpop", "ppn"),
        phrases=("ppn gamma", "post-newtonian gamma"),
        conditions=_BINPOP_CONDITIONS,
        forbids=(),
    )

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
    _binpop("66.7", "1.73 e-5"),
    _binpop("95", "2.40 e-5"),
    _binpop("99.7", "2.50 e-5"),
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
