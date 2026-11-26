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
        "exact, printed truncated",
        "no uncertainty printed",
        "IUPAC standard atomic weight uncertainty",
        "2 sigma",
        "68.3% credible interval",
        "95% interval",
        "maximum relative uncertainty, ppm as printed",
        "relative standard uncertainty",
        "asymmetric, level not stated",
    }
)
_NONE_KIND = "no uncertainty printed"
_TRUNCATED_KIND = "exact, printed truncated"
_ASYMMETRIC_KINDS = frozenset({"asymmetric, level not stated", "asymmetric standard uncertainty", "90% credible interval", "68% interval", "68.3% credible interval", "95% interval"})
_SPLIT_KIND = "statistical and systematic, printed separately"
_RELATIVE_PPM_KIND = "maximum relative uncertainty, ppm as printed"
_RELATIVE_KINDS = {_RELATIVE_PPM_KIND: 10**6, "relative standard uncertainty": 1}


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
        return self.uncertainty_kind in {"exact", _TRUNCATED_KIND}

    @property
    def truncated(self) -> bool:
        """Exact by definition, but the source prints only leading digits and '...'."""
        return self.uncertainty_kind == _TRUNCATED_KIND

    @property
    def value(self) -> Fraction:
        if self.truncated:
            raise ValueError(f"{self.id} is printed truncated; use truncation_bounds")
        return parse_decimal(self.value_text)

    @property
    def truncation_bounds(self) -> tuple[Fraction, Fraction]:
        """For a truncated print such as `5.670 374 419... e-8`: the printed digits and
        one more unit in the last printed place. The exact value lies in [low, high)."""
        if not self.truncated:
            raise ValueError(f"{self.id} is not printed truncated")
        return parse_truncated(self.value_text)

    @property
    def uncertainty(self) -> Fraction | None:
        if self.exact or self.uncertainty_kind == _NONE_KIND or self.uncertainty_kind in _RELATIVE_KINDS:
            return None
        return parse_decimal(self.uncertainty_text)

    @property
    def lower_uncertainty(self) -> Fraction | None:
        if self.exact or self.uncertainty_kind == _NONE_KIND or self.uncertainty_kind in _RELATIVE_KINDS:
            return None
        if self.lower_text:
            return parse_decimal(self.lower_text)
        return self.uncertainty

    @property
    def relative_uncertainty(self) -> Fraction | None:
        """Only for a source that prints its uncertainty relative to the value (as ppm, or as a bare ratio)."""
        if self.uncertainty_kind not in _RELATIVE_KINDS:
            return None
        return parse_decimal(self.uncertainty_text) / _RELATIVE_KINDS[self.uncertainty_kind]

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


def parse_truncated(text: str) -> tuple[Fraction, Fraction]:
    """Read `5.670 374 419... e-8`, digits cut off with '...', as the half-open
    interval [printed digits, printed digits + one unit in the last place) for a
    positive value."""
    cleaned = text.replace(" ", "")
    head, sep, tail = cleaned.partition("...")
    if not sep or not head or head.startswith("-") or (tail and not tail.startswith("e")):
        raise ValueError(f"not a truncated value: {text!r}")
    places = len(head.partition(".")[2])
    scale = Fraction(10) ** int(tail[1:]) if tail else Fraction(1)
    low = Fraction(head) * scale
    return low, low + Fraction(1, 10**places) * scale


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
    kind = (_TRUNCATED_KIND if "..." in value_text else "exact") if exact else "standard uncertainty"
    return Quantity(
        id=id,
        name=name,
        symbol=symbol,
        value_text=value_text,
        uncertainty_text="exact" if exact else uncertainty_text,
        unit=unit,
        uncertainty_kind=kind,
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

_EXACT_DERIVED = (
    "CODATA lists this constant as exact: it is fixed by the defining constants h, c, and k of the 2019 SI. "
    "The table prints its leading digits followed by '...', and those digits are stored as printed.",
)

RADIATION_CONSTANTS: tuple[Quantity, ...] = (
    _codata("codata2022.sigma", "Stefan-Boltzmann constant", "sigma", "5.670 374 419... e-8", "(exact)", "W m^-2 K^-4", "sigma",
            keys=("stefan",), phrases=("stefan-boltzmann", "stefan boltzmann", "radiation constant"), notes=_EXACT_DERIVED),
    _codata("codata2022.b_wien", "Wien wavelength displacement law constant", "b", "2.897 771 955... e-3", "(exact)", "m K", "bwien",
            keys=("wien",), phrases=("wien displacement", "wien constant", "radiation constant"), notes=_EXACT_DERIVED),
    _codata("codata2022.b_prime_wien", "Wien frequency displacement law constant", "b'", "5.878 925 757... e10", "(exact)", "Hz K^-1", "bpwien",
            keys=("wien",), phrases=("wien displacement", "wien constant", "radiation constant"), notes=_EXACT_DERIVED),
)

QUANTITIES: tuple[Quantity, ...] = (
    CODATA_2022 + PDG_2026 + MERCURY + MERCURY_MODERN + GW150914 + PLANCK_2018 + SH0ES_2022 + DESI_DR2 + FIXSEN_2009
    + PARTICLE_PRECISION + ASD_IONIZATION + INPOP + AME2020 + PDG_2026_HADRONS + GRAVITY_TESTS + ATOMIC_SPECTROSCOPY + NUCLEAR_CODATA + RADIATION_CONSTANTS
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
    def upper(self) -> Fraction | None:
        return parse_decimal(self.upper_text) if self.upper_text else None


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


# ---- Batch 5: chemistry. Defined after Bound, because interval atomic weights are bounds. ----

CIAAW_SOURCE = (
    "T. Prohaska et al., Standard atomic weights of the elements 2021 (IUPAC Technical Report), Pure Appl. Chem. 94, 573-600 (2022), "
    "doi:10.1515/pac-2019-0603, as tabulated by the IUPAC Commission on Isotopic Abundances and Atomic Weights (CIAAW)."
)
CIAAW_URL = "https://www.ciaaw.org/atomic-weights.htm"
_CIAAW_EDITION = "IUPAC standard atomic weights 2021 (CIAAW table)"
_CIAAW_FOOTNOTES = {
    "g": "Footnote g: geological and biological materials are known in which the element has an isotopic composition outside the limits for normal material, and the atomic weight there may exceed the stated uncertainty.",
    "m": "Footnote m: modified isotopic compositions may be found in commercially available material, and substantial deviations in atomic weight can occur.",
    "r": "Footnote r: the range in isotopic composition of normal terrestrial material prevents a more precise standard atomic weight; the tabulated value and uncertainty should apply to normal material.",
}
_CIAAW_TABLE_NOTE = (
    "The CIAAW page heads its table 'Standard Atomic Weights 2024' and says it is based on the 'Atomic Weights 2021' report, "
    "with 2024 revisions only for gadolinium, lutetium, and zirconium, none of which is between H and Kr."
)
_CIAAW_LEVEL = (
    "CIAAW: 'The reported uncertainties of the standard atomic weights are such that the atomic-weight values of normal materials "
    "are expected to lie in the given interval with great certitude.' It is not a standard uncertainty."
)

# (Z, symbol, name, standard atomic weight as printed, footnotes), H through Kr, as printed by CIAAW.
CIAAW_H_KR: tuple[tuple[int, str, str, str, str], ...] = (
    (1, "H", "hydrogen", "[1.007 84, 1.008 11]", "m"),
    (2, "He", "helium", "4.002 602(2)", "gr"),
    (3, "Li", "lithium", "[6.938, 6.997]", "m"),
    (4, "Be", "beryllium", "9.012 1831(5)", ""),
    (5, "B", "boron", "[10.806, 10.821]", "m"),
    (6, "C", "carbon", "[12.0096, 12.0116]", ""),
    (7, "N", "nitrogen", "[14.006 43, 14.007 28]", "m"),
    (8, "O", "oxygen", "[15.999 03, 15.999 77]", "m"),
    (9, "F", "fluorine", "18.998 403 162(5)", ""),
    (10, "Ne", "neon", "20.1797(6)", "gm"),
    (11, "Na", "sodium", "22.989 769 28(2)", ""),
    (12, "Mg", "magnesium", "[24.304, 24.307]", ""),
    (13, "Al", "aluminium", "26.981 5384(3)", ""),
    (14, "Si", "silicon", "[28.084, 28.086]", ""),
    (15, "P", "phosphorus", "30.973 761 998(5)", ""),
    (16, "S", "sulfur", "[32.059, 32.076]", ""),
    (17, "Cl", "chlorine", "[35.446, 35.457]", "m"),
    (18, "Ar", "argon", "[39.792, 39.963]", ""),
    (19, "K", "potassium", "39.0983(1)", ""),
    (20, "Ca", "calcium", "40.078(4)", "g"),
    (21, "Sc", "scandium", "44.955 907(4)", ""),
    (22, "Ti", "titanium", "47.867(1)", ""),
    (23, "V", "vanadium", "50.9415(1)", ""),
    (24, "Cr", "chromium", "51.9961(6)", ""),
    (25, "Mn", "manganese", "54.938 043(2)", ""),
    (26, "Fe", "iron", "55.845(2)", ""),
    (27, "Co", "cobalt", "58.933 194(3)", ""),
    (28, "Ni", "nickel", "58.6934(4)", "r"),
    (29, "Cu", "copper", "63.546(3)", "r"),
    (30, "Zn", "zinc", "65.38(2)", "r"),
    (31, "Ga", "gallium", "69.723(1)", ""),
    (32, "Ge", "germanium", "72.630(8)", ""),
    (33, "As", "arsenic", "74.921 595(6)", ""),
    (34, "Se", "selenium", "78.971(8)", "r"),
    (35, "Br", "bromine", "[79.901, 79.907]", ""),
    (36, "Kr", "krypton", "83.798(2)", "gm"),
)


def _ciaaw_notes(z: int, printed: str, flags: str) -> tuple[str, ...]:
    return (f"Z = {z}. Printed by CIAAW as {printed}.", _CIAAW_TABLE_NOTE) + tuple(_CIAAW_FOOTNOTES[f] for f in flags)


def _ciaaw_quantity(z: int, sym: str, name: str, printed: str, flags: str) -> Quantity:
    value_text, _, rest = printed.partition("(")
    digits = rest.rstrip(")")
    places = len(value_text.replace(" ", "").partition(".")[2])
    uncertainty_text = f"0.{'0' * (places - len(digits))}{digits}" if places else digits
    return _q(
        f"iupac2021.ar.{sym.lower()}", f"standard atomic weight of {name}", f"A_r({sym})", value_text.strip(), uncertainty_text, "",
        kind="IUPAC standard atomic weight uncertainty", printed=printed, source=CIAAW_SOURCE, edition=_CIAAW_EDITION,
        url="https://doi.org/10.1515/pac-2019-0603", retrieved_from=CIAAW_URL,
        phrases=(f"atomic weight of {name}", "standard atomic weights"), notes=_ciaaw_notes(z, printed, flags) + (_CIAAW_LEVEL,),
    )


def _ciaaw_bound(z: int, sym: str, name: str, printed: str, flags: str) -> Bound:
    low, high = (part.strip() for part in printed.strip("[]").split(","))
    return Bound(
        id=f"iupac2021.ar.{sym.lower()}", name=f"standard atomic weight interval of {name}", symbol=f"A_r({sym})",
        lower_text=low, upper_text=high, unit="", source=CIAAW_SOURCE, edition=_CIAAW_EDITION,
        url="https://doi.org/10.1515/pac-2019-0603", retrieved_from=CIAAW_URL, retrieved=RETRIEVED,
        keys=(), phrases=(f"atomic weight of {name}", "standard atomic weights"),
        conditions=_ciaaw_notes(z, printed, flags) + (
            "IUPAC gives an interval because of well-documented natural variation in isotopic abundance. Normal materials are expected to lie inside it. No central value is given.",
        ),
        forbids=(),
    )


IUPAC_ATOMIC_WEIGHTS: tuple[Quantity, ...] = tuple(_ciaaw_quantity(*row) for row in CIAAW_H_KR if not row[3].startswith("["))
IUPAC_ATOMIC_WEIGHT_INTERVALS: tuple[Bound, ...] = tuple(_ciaaw_bound(*row) for row in CIAAW_H_KR if row[3].startswith("["))


WEBBOOK_DIATOMIC_SOURCE = (
    "K. P. Huber and G. Herzberg, Constants of Diatomic Molecules (data prepared by J. W. Gallagher and R. D. Johnson, III), "
    "in NIST Chemistry WebBook, NIST Standard Reference Database Number 69, eds. P. J. Linstrom and W. G. Mallard, doi:10.18434/T4D303. "
    "Ground-state row of the 'Diatomic constants' table."
)
_WEBBOOK_EDITION = "NIST Chemistry WebBook, SRD 69 (Huber-Herzberg diatomic constants)"
_RE_NOTE = "Huber and Herzberg print r_e with no uncertainty; the trailing superscripts on the WebBook row are footnote numbers, not digits."
CCCBDB_SOURCE = (
    "NIST Computational Chemistry Comparison and Benchmark Database, NIST Standard Reference Database Number 101, Release 22, "
    "ed. R. D. Johnson III, doi:10.18434/T47C7Z, Experimental > Energy > Atomization Energy."
)
_CCCBDB_EDITION = "NIST CCCBDB Release 22"
_D0_NOTE = (
    "For a diatomic molecule the atomization energy at 0 K is the dissociation energy D_0. CCCBDB lists it beside the 298 K value; "
    "the uncertainty column carries no stated level."
)


def _webbook_re(mol: str, cas: str, state: str, value: str, extra: str = "") -> Quantity:
    return _q(
        f"hh1979.{mol.lower()}.r_e", f"equilibrium internuclear distance of {mol}, ground state {state}", f"r_e({mol})", value, "", "Angstrom",
        kind="no uncertainty printed", source=WEBBOOK_DIATOMIC_SOURCE, edition=_WEBBOOK_EDITION,
        url=f"https://webbook.nist.gov/cgi/cbook.cgi?ID={cas}&Mask=1000#Diatomic", retrieved_from=f"https://webbook.nist.gov/cgi/cbook.cgi?ID={cas}&Mask=1000",
        phrases=(f"bond length of {mol.lower()}", f"{mol.lower()} bond length", "diatomic bond lengths"),
        notes=(f"Ground state {state}, r_e = {value} Angstrom as printed.", _RE_NOTE) + ((extra,) if extra else ()),
    )


def _cccbdb_d0(mol: str, cas: str, value0: str, value298: str, unc: str) -> Quantity:
    printed = f"0 K {value0}, 298 K {value298}, unc. {unc or '(blank)'} kJ mol-1"
    return _q(
        f"cccbdb.{mol.lower()}.d0", f"dissociation energy of {mol} at 0 K (experimental atomization energy)", f"D_0({mol})", value0, unc, "kJ mol^-1",
        kind="uncertainty as printed, level not stated" if unc else "no uncertainty printed",
        source=CCCBDB_SOURCE, edition=_CCCBDB_EDITION,
        url=f"https://cccbdb.nist.gov/exp2x.asp?casno={cas.lstrip('C')}&charge=0", retrieved_from="https://cccbdb.nist.gov/ea2x.asp",
        phrases=(f"dissociation energy of {mol.lower()}", f"{mol.lower()} dissociation energy", "bond dissociation energies"),
        notes=(f"CCCBDB row: {printed}.", _D0_NOTE),
    )


CODATA_KEY_SOURCE = (
    "J. D. Cox, D. D. Wagman, and V. A. Medvedev, CODATA Key Values for Thermodynamics, Hemisphere, New York (1989), "
    "as tabulated by CODATA."
)
_CODATA_KEY_URL = "https://www.codata.info/resources/databases/key1.html"
_CODATA_KEY_NOTE = (
    "CODATA: 'we believe there is a high probability that the true values fall within the stated uncertainty limits.' "
    "The standard-state pressure is 100000 Pa (1 bar), at 298.15 K."
)
IUPAC_PKA_SOURCE = (
    "IUPAC Digitized pKa Dataset, v2.4 (2026), high-confidence file, from E. P. Serjeant and B. Dempsey, Ionization Constants of Organic Acids "
    "in Aqueous Solution, IUPAC Chemical Data Series No. 23, Pergamon (1979), entry serjeant2825; original measurement reference F12: "
    "M. J. Fickling, A. Fischer, B. R. Mann, J. Packer, and J. Vaughan, J. Am. Chem. Soc. 81, 4226 (1959)."
)
CRC91_INORGANIC = (
    "D. R. Lide (ed.), CRC Handbook of Chemistry and Physics, 91st Edition (2010-2011), Dissociation Constants of Inorganic Acids and Bases, "
    "p. 8-40 to 8-41, from D. D. Perrin, Ionization Constants of Inorganic Acids and Bases in Aqueous Solution, 2nd ed., Pergamon (1982)."
)
CRC91_ORGANIC = (
    "D. R. Lide (ed.), CRC Handbook of Chemistry and Physics, 91st Edition (2010-2011), Dissociation Constants of Organic Acids and Bases, p. 8-43 ff."
)
_CRC_DIR = "https://diverdi.colostate.edu/all_courses/CRC%20reference%20data/"
IAPWS_KW_SOURCE = (
    "International Association for the Properties of Water and Steam, IAPWS R11-24, Revised Release on the Ionization Constant of H2O (2024), Table 3."
)
_WEBBOOK_CH4 = "https://webbook.nist.gov/cgi/cbook.cgi?ID=C74828&Mask=1"

CHEMISTRY: tuple[Quantity, ...] = (
    _webbook_re("H2", "C1333740", "X 1Sigma_g+", "0.74144"),
    _webbook_re("N2", "C7727379", "X 1Sigma_g+", "1.097685"),
    _webbook_re("O2", "C7782447", "X 3Sigma_g-", "1.20752"),
    _webbook_re("CO", "C630080", "X 1Sigma+", "1.128323"),
    _webbook_re("HCl", "C7647010", "X 1Sigma+", "1.274552", "The WebBook page lists constants for H35Cl."),
    _cccbdb_d0("H2", "1333740", "432.1", "436.0", ""),
    _cccbdb_d0("N2", "7727379", "941.6", "945.4", "0.8"),
    _cccbdb_d0("O2", "7782447", "493.7", "498.5", "0.2"),
    _cccbdb_d0("CO", "630080", "1071.8", "1076.4", "0.5"),
    _cccbdb_d0("HCl", "7647010", "427.8", "431.6", "0.1"),
    _q("iupac_pka.phenol", "phenol acid dissociation constant, pKa, water, 25 C", "pK_a(C6H5OH)", "9.994", "", "",
       kind="no uncertainty printed", source=IUPAC_PKA_SOURCE, edition="IUPAC Digitized pKa Dataset v2.4",
       url="https://github.com/IUPAC/Dissociation-Constants", retrieved_from="https://raw.githubusercontent.com/IUPAC/Dissociation-Constants/main/iupac_high-confidence_v2_4.csv",
       phrases=("phenol pka", "pka of phenol", "acid dissociation constants"),
       notes=("Dataset row: pka_type pKa1, T 25 (deg C), method O5a, assessment Reliable, remarks 'm=0.0004-0.0008, I=0.01-0.05'. Other values in the same entry run 9.97 to 10.02 at 25 C.",)),
    _q("crc91.pka.phenol", "phenol pKa, water, 25 C, CRC table", "pK_a(C6H5OH)", "9.99", "", "",
       kind="no uncertainty printed", source=CRC91_ORGANIC, edition="CRC Handbook, 91st Edition",
       url=_CRC_DIR + "dissociation%20constants%20of%20organic%20acids%20and%20bases.pdf", retrieved_from=_CRC_DIR + "dissociation%20constants%20of%20organic%20acids%20and%20bases.pdf",
       phrases=("phenol pka", "pka of phenol", "acid dissociation constants"),
       notes=("Row: C6H6O, Phenol, t/C 25, pKa 9.99. All values refer to dilute aqueous solutions.",)),
    _q("crc91.pka.water", "water pKa, 25 C, CRC table", "pK_a(H2O)", "13.995", "", "",
       kind="no uncertainty printed", source=CRC91_INORGANIC, edition="CRC Handbook, 91st Edition",
       url=_CRC_DIR + "dissociation%20constants%20of%20inorganic%20acids%20and%20bases.pdf", retrieved_from=_CRC_DIR + "dissociation%20constants%20of%20inorganic%20acids%20and%20bases.pdf",
       phrases=("water pka", "pka of water", "acid dissociation constants"),
       notes=("Row: Water, H2O, t/C 25, pKa 13.995. The table preface says all values refer to dilute aqueous solutions at zero ionic strength, and gives K_water = 1.01 x 10^-14 at 25 C.",)),
    _q("iapws2024.pkw_25c", "ionization constant of water, pKw, at 25 C and 0.1 MPa", "pK_w", "13.99", "", "",
       kind="no uncertainty printed", source=IAPWS_KW_SOURCE, edition="IAPWS R11-24 (2024)",
       url="https://iapws.org/technical-guidance/release/Ionization.download", retrieved_from="https://iapws.org/technical-guidance/release/Ionization.download",
       phrases=("pkw", "ionization constant of water", "ion product of water"),
       notes=("Table 3, row psat, column 25 C: 13.99. Footnote (b): values use the density of the liquid at 0.1 MPa below 100 C.",
              "Section 5: in the liquid region below 200 C and 200 MPa the deviations of experimental data from the formulation 'do not generally exceed 0.05'. That is a statement about the fit, not a printed uncertainty on this entry.")),
    _q("codata_key.h2o_l.dfh", "standard enthalpy of formation of liquid water at 298.15 K", "Delta_f H(H2O, l)", "-285.830", "0.040", "kJ mol^-1",
       kind="uncertainty as printed, level not stated", source=CODATA_KEY_SOURCE, edition="CODATA Key Values for Thermodynamics (1989)",
       url=_CODATA_KEY_URL, retrieved_from=_CODATA_KEY_URL, phrases=("enthalpy of formation of water", "heat of formation of water", "standard enthalpies of formation"),
       notes=("Row: H2O, l, -285.830 +- 0.040 kJ mol-1.", _CODATA_KEY_NOTE)),
    _q("codata_key.co2_g.dfh", "standard enthalpy of formation of gaseous carbon dioxide at 298.15 K", "Delta_f H(CO2, g)", "-393.51", "0.13", "kJ mol^-1",
       kind="uncertainty as printed, level not stated", source=CODATA_KEY_SOURCE, edition="CODATA Key Values for Thermodynamics (1989)",
       url=_CODATA_KEY_URL, retrieved_from=_CODATA_KEY_URL, phrases=("enthalpy of formation of carbon dioxide", "heat of formation of co2", "standard enthalpies of formation"),
       notes=("Row: CO2, g, -393.51 +- 0.13 kJ mol-1.", _CODATA_KEY_NOTE)),
    _q("janaf1998.ch4_g.dfh", "standard enthalpy of formation of gaseous methane at 298.15 K, JANAF", "Delta_f H(CH4, g)", "-74.87", "", "kJ mol^-1",
       kind="no uncertainty printed", source="M. W. Chase, Jr., NIST-JANAF Thermochemical Tables, Fourth Edition, J. Phys. Chem. Ref. Data Monograph 9 (1998), as listed in the NIST Chemistry WebBook (SRD 69), gas phase thermochemistry of methane.",
       edition="NIST-JANAF 4th ed. via NIST WebBook", url=_WEBBOOK_CH4, retrieved_from=_WEBBOOK_CH4,
       phrases=("enthalpy of formation of methane", "heat of formation of methane", "standard enthalpies of formation"),
       notes=("WebBook row: Delta_fH(gas) -74.87 kJ/mol, Review, Chase, 1998, 'Data last reviewed in March, 1961'. Methane is not among the CODATA key values.",)),
    _q("gurvich1991.ch4_g.dfh", "standard enthalpy of formation of gaseous methane at 298.15 K, Gurvich recommendation", "Delta_f H(CH4, g)", "-74.6", "0.3", "kJ mol^-1",
       kind="uncertainty as printed, level not stated", source="J. A. Manion, J. Phys. Chem. Ref. Data 31, 123 (2002), adopting the recommendation of L. V. Gurvich, I. V. Veyts, et al. (1991), as listed in the NIST Chemistry WebBook (SRD 69).",
       edition="Manion 2002 via NIST WebBook", url=_WEBBOOK_CH4, retrieved_from=_WEBBOOK_CH4,
       phrases=("enthalpy of formation of methane", "heat of formation of methane", "standard enthalpies of formation"),
       notes=("WebBook row: Delta_fH(gas) -74.6 +- 0.3 kJ/mol, Review, Manion, 2002, 'adopted recommendation of Gurvich, Veyts, et al., 1991'.",)),
)


# ---- Batch 5: condensed matter ----

_SI_X_RAY = (
    "CODATA 2022 Table XXXIV lists a, d220 = a/sqrt(8), and V_m(Si) = N_A a^3/8 for an ideal single crystal of naturally occurring Si, "
    "free of impurities and imperfections, in vacuum at 22.5 C."
)
_QHE_NOTE = (
    "CODATA lists this constant as exact in the 2019 SI and prints leading digits followed by '...'; those digits are stored as printed.",
)
_CONVENTIONAL_NOTE = (
    "CODATA lists this conventional value as exact, under its own name, separate from the SI constant.",
)
IOFFE_SOURCE = "Ioffe Institute, NSM Archive - Physical Properties of Semiconductors, {name}: Band structure and carrier concentration, Basic Parameters."
_IOFFE_ARCHIVE = {
    "Si": "https://web.archive.org/web/20250209210838/http://www.ioffe.ru/SVA/NSM/Semicond/Si/bandstr.html",
    "Ge": "https://web.archive.org/web/20241224191848/http://www.ioffe.ru/SVA/NSM/Semicond/Ge/bandstr.html",
    "GaAs": "https://web.archive.org/web/20250123110509/http://www.ioffe.ru/SVA/NSM/Semicond/GaAs/bandstr.html",
}
_IOFFE_REACH = "ioffe.ru did not answer from this machine on 2026-11-25; the page was read from the Internet Archive copy named in retrieved_from."
SRM767A_SOURCE = (
    "NIST Certificate, Standard Reference Material 767a, Superconductive Thermometric Fixed Point Device, Device No. PP, "
    "Gaithersburg, MD, February 14, 1992 (revision of certificate dated 8-13-90)."
)
_SRM767A_URL = "https://tsapps.nist.gov/srmext/certificates/archives/767a.%20Feb%2014,%201992.pdf"
_SRM767A_NOTE = (
    "The certificate prints the measured transition temperature with no uncertainty. It certifies each transition reproducible to +-0.3 mK "
    "when measured as recommended, on ITS-90 after the 1990 conversion from IPTS-68; the thermometer was calibrated against EPT-76."
)
IAPWS_CRIT_SOURCE = (
    "IAPWS R2-83(1992), Revised Release on the Values of Temperature, Pressure and Density of Ordinary and Heavy Water Substances "
    "at their Respective Critical Points, Table 1; method and uncertainties in J. M. H. Levelt Sengers et al., J. Phys. Chem. Ref. Data 14, 193 (1985)."
)
_IAPWS_CRIT_URL = "https://iapws.org/technical-guidance/release/crits.download"
_IAPWS_CRIT_NOTE = "The release calls these 'estimated uncertainties' and states no level."
IAPWS_MELT_SOURCE = (
    "IAPWS R14-08(2011), Revised Release on the Pressure along the Melting and Sublimation Curves of Ordinary Water Substance, Section 3.1."
)
_IAPWS_MELT_URL = "https://iapws.org/technical-guidance/release/MeltSub.download"


def _ioffe_gap(mol: str, value: str, extra: str) -> Quantity:
    return _q(
        f"ioffe.{mol.lower()}.band_gap_300k", f"band gap of {mol} at 300 K", f"E_g({mol})", value, "", "eV",
        kind="no uncertainty printed", source=IOFFE_SOURCE.format(name=mol), edition="Ioffe NSM Archive",
        url=f"https://www.ioffe.ru/SVA/NSM/Semicond/{mol}/bandstr.html", retrieved_from=_IOFFE_ARCHIVE[mol],
        phrases=(f"band gap of {mol.lower()}", f"{mol.lower()} band gap", "semiconductor band gaps"),
        notes=(f"Basic Parameters table: 'Energy gap {value} eV'.", extra, _IOFFE_REACH),
    )


def _srm_tc(element: str, value: str, width: str) -> Quantity:
    return _q(
        f"srm767a.{element.lower()}.tc", f"superconducting transition temperature of {element}", f"T_c({element})", value, "", "K",
        kind="no uncertainty printed", source=SRM767A_SOURCE, edition="NIST SRM 767a (1992)", url=_SRM767A_URL, retrieved_from=_SRM767A_URL,
        phrases=(f"{element.lower()} superconducting", f"superconducting transition of {element.lower()}", "superconducting transition temperatures"),
        notes=(f"Row: {element}, measured transition temp. T_c = {value} K, measured transition width W = {width} mK.", _SRM767A_NOTE),
    )


CONDENSED_MATTER: tuple[Quantity, ...] = (
    _codata("codata2022.a_si", "lattice parameter of silicon", "a", "5.431 020 511 e-10", "0.000 000 089 e-10", "m", "asil",
            keys=("silicon",), phrases=("silicon lattice", "lattice parameter of silicon", "lattice constant of silicon"), notes=(_SI_X_RAY,)),
    _codata("codata2022.d220_si", "lattice spacing of ideal Si (220)", "d_220", "1.920 155 716 e-10", "0.000 000 032 e-10", "m", "d220sil",
            keys=("silicon",), phrases=("silicon lattice", "d220", "220 lattice spacing"), notes=(_SI_X_RAY,)),
    _codata("codata2022.vm_si", "molar volume of silicon", "V_m(Si)", "1.205 883 199 e-5", "0.000 000 060 e-5", "m^3 mol^-1", "mvolsil",
            keys=("silicon",), phrases=("molar volume of silicon",), notes=(_SI_X_RAY,)),
    _codata("codata2022.r_k", "von Klitzing constant", "R_K", "25 812.807 45...", "(exact)", "ohm", "rk",
            keys=("klitzing",), phrases=("von klitzing", "quantum hall resistance", "quantum electrical standards"), notes=_QHE_NOTE),
    _codata("codata2022.k_j", "Josephson constant", "K_J", "483 597.848 4... e9", "(exact)", "Hz V^-1", "kjos",
            keys=("josephson",), phrases=("josephson constant", "quantum electrical standards"), notes=_QHE_NOTE),
    _codata("codata2022.r_k_90", "conventional value of von Klitzing constant", "R_K-90", "25 812.807", "(exact)", "ohm", "rk90",
            keys=("klitzing",), phrases=("von klitzing", "conventional electrical units"), notes=_CONVENTIONAL_NOTE),
    _codata("codata2022.k_j_90", "conventional value of Josephson constant", "K_J-90", "483 597.9 e9", "(exact)", "Hz V^-1", "kj90",
            keys=("josephson",), phrases=("josephson constant", "conventional electrical units"), notes=_CONVENTIONAL_NOTE),
    _ioffe_gap("Si", "1.12", "The band-structure figure caption reads 'Band structure of Si at 300 K. Eg = 1.12 eV'."),
    _ioffe_gap("Ge", "0.661", "The bandstr page does not print a temperature beside this table; the Ioffe Ge Basic Parameters page is headed 'Basic Parameters at 300 K'."),
    _ioffe_gap("GaAs", "1.424", "The band-structure figure caption reads '... of GaAs. 300 K Eg = 1.42 eV'."),
    _srm_tc("Niobium", "9.2488", "23"),
    _srm_tc("Lead", "7.19974", "0.2"),
    _srm_tc("Aluminum", "1.18074", "0.3"),
    _q("wu1987.ybco.tc", "superconducting transition of the Y-Ba-Cu-O system, as titled", "T_c(Y-Ba-Cu-O)", "93", "", "K",
       kind="no uncertainty printed",
       source="M. K. Wu, J. R. Ashburn, C. J. Torng, P. H. Hor, R. L. Meng, L. Gao, Z. J. Huang, Y. Q. Wang, and C. W. Chu, Superconductivity at 93 K in a new mixed-phase Y-Ba-Cu-O compound system at ambient pressure, Phys. Rev. Lett. 58, 908 (1987), doi:10.1103/PhysRevLett.58.908.",
       edition="Phys. Rev. Lett. 58 (1987)", url="https://doi.org/10.1103/PhysRevLett.58.908", retrieved_from="https://api.crossref.org/works/10.1103/PhysRevLett.58.908",
       phrases=("ybco", "y-ba-cu-o", "yttrium barium copper oxide", "high-temperature superconductor", "superconducting transition temperatures"),
       notes=("The value is the one printed in the title. The APS page is behind a bot check and Crossref carries no abstract, so the abstract's transition range was not read.", "PubMed 10035069 indexes the title with 'Yb-Ba-Cu-O'; the Crossref and DOI title read 'Y-Ba-Cu-O'.")),
    _q("arajs1964.fe.curie", "ferromagnetic Curie temperature of iron", "T_FC(Fe)", "1044", "2", "K",
       kind="uncertainty as printed, level not stated",
       source="S. Arajs and R. V. Colvin, Ferromagnetic-Paramagnetic Transition in Iron, J. Appl. Phys. 35, 2424-2426 (1964), doi:10.1063/1.1702873, abstract.",
       edition="J. Appl. Phys. 35 (1964)", url="https://doi.org/10.1063/1.1702873", retrieved_from="https://api.crossref.org/works/10.1063/1.1702873",
       phrases=("curie temperature of iron", "iron curie", "curie point of iron"),
       notes=("Printed as 'The temperature T_FC, appearing as an abrupt decrease in the sigma vs T curves, occurs at 1044+-2 K', for an iron sphere in fields from 180 to 1360 Oe.",)),
    _q("iapws1992.h2o.t_c", "critical temperature of ordinary water", "T_c(H2O)", "647.096", "0.100", "K",
       kind="uncertainty as printed, level not stated", source=IAPWS_CRIT_SOURCE, edition="IAPWS R2-83(1992)", url=_IAPWS_CRIT_URL, retrieved_from=_IAPWS_CRIT_URL,
       phrases=("critical point of water", "water critical point", "critical temperature of water"),
       notes=("Printed as (647.096 + delta_1) K on ITS-90, with delta_1 = 0.000 +- 0.100.", _IAPWS_CRIT_NOTE, "The release adds that the number of decimal places bears no relation to the accuracy with which T_c is known.")),
    _q("iapws1992.h2o.p_c", "critical pressure of ordinary water", "p_c(H2O)", "22.064", "0.005", "MPa",
       kind="uncertainty as printed, level not stated", source=IAPWS_CRIT_SOURCE, edition="IAPWS R2-83(1992)", url=_IAPWS_CRIT_URL, retrieved_from=_IAPWS_CRIT_URL,
       phrases=("critical point of water", "water critical point", "critical pressure of water"),
       notes=("Printed as (22.064 + 0.27 delta_1 +- 0.005) MPa: the +-0.005 is stored, and the 0.27 delta_1 term ties p_c to the T_c uncertainty through the vapor-pressure curve.", _IAPWS_CRIT_NOTE)),
    _q("iapws1992.h2o.rho_c", "critical density of ordinary water", "rho_c(H2O)", "322", "3", "kg m^-3",
       kind="uncertainty as printed, level not stated", source=IAPWS_CRIT_SOURCE, edition="IAPWS R2-83(1992)", url=_IAPWS_CRIT_URL, retrieved_from=_IAPWS_CRIT_URL,
       phrases=("critical point of water", "water critical point", "critical density of water"),
       notes=("Printed as (322 +- 3) kg m^-3.", _IAPWS_CRIT_NOTE)),
    _q("iapws2011.h2o.t_t", "triple-point temperature of ordinary water (solid-liquid-gas)", "T_t(H2O)", "273.16", "", "K",
       kind="no uncertainty printed", source=IAPWS_MELT_SOURCE, edition="IAPWS R14-08(2011)", url=_IAPWS_MELT_URL, retrieved_from=_IAPWS_MELT_URL,
       phrases=("triple point of water", "water triple point"),
       notes=("Printed as 'T* = T_t = 273.16 K and p* = p_t = 611.657 Pa; T_t and p_t are the values of the \"normal\" triple point (S-L-G)'. T is on ITS-90.",)),
    _q("iapws2011.h2o.p_t", "triple-point pressure of ordinary water (solid-liquid-gas)", "p_t(H2O)", "611.657", "", "Pa",
       kind="no uncertainty printed", source=IAPWS_MELT_SOURCE, edition="IAPWS R14-08(2011)", url=_IAPWS_MELT_URL, retrieved_from=_IAPWS_MELT_URL,
       phrases=("triple point of water", "water triple point"),
       notes=("Printed in Section 3.1 with no uncertainty. IAPWS-95 (R6-95(2018)) separately reports that its equation of state yields p_t = 611.654 771 Pa; that calculated value is not stored.",)),
)

_NU_NOTE = "PDG 2026 summary-table value from the neutrino mixing listings."
_NU_SCALE = "The PDG database stores a scale factor of {0} for this error."
_ORDERING = "PDG gives this value only under the stated assumption: '{0}'."
_HFLAV = "PDG summary-table value marked '(Produced by HFLAV)'. PDG's own average of the listed measurements, {0}, is in the database but not stored here."


def _nu(id: str, name: str, symbol: str, value: str, unc: str, unit: str, node: str, *, lower: str = "", notes: tuple[str, ...] = ()) -> Quantity:
    return _pdg(
        id, name, symbol, value, unc, unit, node=node,
        kind="asymmetric standard uncertainty" if lower else "standard uncertainty", lower_text=lower,
        keys=("neutrino", "oscillation"), phrases=("neutrino oscillation", "neutrino mixing"),
        notes=(_NU_NOTE, *notes, _API_NOTE),
    )


PARTICLE_B5: tuple[Quantity, ...] = (
    _nu("pdg2026.nu.sin2_theta12", "solar mixing parameter", "sin^2(theta_12)", "0.307", "0.012", "", "S067P12", notes=("Printed as 0.307+-0.012.",)),
    _nu("pdg2026.nu.dm2_21", "solar mass-squared splitting", "Delta m^2_21", "7.60 e-5", "0.17 e-5", "eV^2", "S067DM3", notes=("Printed as (7.60+-0.17)E-5 eV**2.", _NU_SCALE.format("1.000296"))),
    _nu("pdg2026.nu.sin2_theta23_no", "atmospheric mixing parameter, normal ordering", "sin^2(theta_23)", "0.533", "0.018", "", "S067P23", notes=("Printed as 0.533+-0.018.", _ORDERING.format("Assuming normal mass ordering"))),
    _nu("pdg2026.nu.sin2_theta23_io", "atmospheric mixing parameter, inverted ordering", "sin^2(theta_23)", "0.523", "0.031", "", "S067P23", lower="0.027", notes=("Printed as 0.523+0.031-0.027.", _ORDERING.format("Assuming inverted mass ordering"), _NU_SCALE.format("1.300628"))),
    _nu("pdg2026.nu.dm2_32_no", "atmospheric mass-squared splitting, normal ordering", "Delta m^2_32", "0.002445", "0.000023", "eV^2", "S067DM1", notes=("Printed as 0.002445+-0.000023 eV**2.", _ORDERING.format("Assuming normal ordering"), _NU_SCALE.format("1.005552"))),
    _nu("pdg2026.nu.dm2_32_io", "atmospheric mass-squared splitting, inverted ordering", "Delta m^2_32", "-0.00252", "0.00004", "eV^2", "S067DM1", notes=("Printed as -0.00252+-0.00004 eV**2.", _ORDERING.format("Assuming inverted ordering"), _NU_SCALE.format("1.259586"))),
    _nu("pdg2026.nu.sin2_theta13", "reactor mixing parameter", "sin^2(theta_13)", "0.0217", "0.0007", "", "S067P13", notes=("Printed as 0.0217+-0.0007.", _NU_SCALE.format("1.430974"))),
    _pdg("pdg2026.gamma_h", "Higgs boson total width", "Gamma_H", "3.0", "1.5", "MeV", node="S126W", kind="asymmetric standard uncertainty", lower_text="0.7",
         keys=("higgs",), phrases=("higgs width", "width of the higgs"),
         notes=("Printed as 3.0+1.5-0.7 MeV. PDG average of the three off-shell measurements it uses: ATLAS 2025AQ 4.3+2.7-1.9, ATLAS 2025AV 0.9+3.4-0.9, CMS 2025L 3.0+2.0-1.5 MeV.", _API_NOTE)),
    _pdg("pdg2026.tau_lifetime", "tau lepton mean life", "tau_tau", "2.903 e-13", "0.005 e-13", "s", node="S035T", phrases=("tau lifetime", "tau mean life"), notes=("Printed as (2.903+-0.005)E-13 s.", _API_NOTE)),
    _pdg("pdg2026.b_plus_lifetime", "B+ meson mean life", "tau_B+", "1637 e-15", "4 e-15", "s", node="S041T", keys=("b meson",), phrases=("b lifetime", "b meson lifetime", "b+ lifetime"), notes=("Printed as 1637+-4E-15 s.", _HFLAV.format("(1.638+-0.004)E-12 s"), _API_NOTE)),
    _pdg("pdg2026.b0_lifetime", "B0 meson mean life", "tau_B0", "1511.3 e-15", "2.7 e-15", "s", node="S042T", keys=("b meson",), phrases=("b lifetime", "b meson lifetime", "b0 lifetime"), notes=("Printed as 1511.3+-2.7E-15 s.", _HFLAV.format("(1.5116+-0.0031)E-12 s, with a scale factor of 1.213616,"), _API_NOTE)),
    _pdg("pdg2026.bs_lifetime", "B_s0 meson mean life", "tau_Bs", "1.515 e-12", "0.006 e-12", "s", node="S086T", keys=("b meson",), phrases=("b lifetime", "b meson lifetime", "bs lifetime"), notes=("Printed as 1.515+-0.006E-12 s.", "PDG summary-table value marked '(Produced by HFLAV)'.", _API_NOTE)),
    _q(
        "cdf2022.m_w", "W boson mass, CDF II", "m_W", "80433.5", "6.4", "MeV", kind=_SPLIT_KIND, systematic_text="6.9",
        source="T. Aaltonen et al. (CDF Collaboration), High-precision measurement of the W boson mass with the CDF II detector, Science 376, 170 (2022), doi:10.1126/science.abk1781.",
        edition="Science 376 (2022)", url="https://doi.org/10.1126/science.abk1781",
        retrieved_from="https://api.crossref.org/works/10.1126/science.abk1781",
        keys=("cdf", "w mass"), phrases=("w boson mass", "w mass measurements", "cdf w mass"),
        notes=("Printed in the abstract as M W = 80,433.5 ± 6.4 stat ± 6.9 syst = 80,433.5 ± 9.4 MeV/c². The combined ± 9.4 is the paper's own and is kept here, not recomputed.", _SPLIT_NOTE),
    ),
    _q(
        "atlas2024.m_w", "W boson mass, ATLAS 7 TeV reanalysis", "m_W", "80366.5", "9.8", "MeV", kind=_SPLIT_KIND, systematic_text="12.5",
        source="ATLAS Collaboration, Measurement of the W-boson mass and width with the ATLAS detector using proton-proton collisions at sqrt(s) = 7 TeV, Eur. Phys. J. C 84, 1309 (2024), arXiv:2403.15085.",
        edition="Eur. Phys. J. C 84 (2024)", url="https://arxiv.org/abs/2403.15085",
        retrieved_from="https://export.arxiv.org/api/query?id_list=2403.15085",
        keys=("atlas", "w mass"), phrases=("w boson mass", "w mass measurements", "atlas w mass"),
        notes=("Printed in the abstract as m_W = 80366.5 ± 9.8 (stat.) ± 12.5 (syst.) MeV = 80366.5 ± 15.9 MeV. The combined ± 15.9 is the paper's own.", "It supersedes the earlier ATLAS result from the same 2011 data.", _SPLIT_NOTE),
    ),
    _q(
        "cms2026.m_w", "W boson mass, CMS", "m_W", "80 360.2", "9.9", "MeV", kind="uncertainty as printed, level not stated",
        source="CMS Collaboration, High-precision measurement of the W boson mass with the CMS experiment, Nature 652, 321 (2026), doi:10.1038/s41586-026-10168-5, arXiv:2412.13872.",
        edition="Nature 652 (2026)", url="https://doi.org/10.1038/s41586-026-10168-5",
        retrieved_from="https://export.arxiv.org/api/query?id_list=2412.13872",
        keys=("cms", "w mass"), phrases=("w boson mass", "w mass measurements", "cms w mass"),
        notes=("Printed in the abstract as 80 360.2 ± 9.9 MeV. W to mu nu events from 2016 at 13 TeV. The abstract gives one combined uncertainty and does not name its level.",),
    ),
    _q(
        "flag2024.alpha_s_mz", "strong coupling at m_Z, FLAG lattice estimate", "alpha_s^(5)(M_Z)", "0.11833", "0.00067", "", kind="uncertainty as printed, level not stated",
        printed="0.11833(67)",
        source="FLAG Working Group, FLAG Review 2024, arXiv:2411.04268, doi:10.1103/nfzp-p5dn, Section 9.10, Eq. (399).",
        edition="FLAG Review 2024", url="https://doi.org/10.1103/nfzp-p5dn",
        retrieved_from="https://arxiv.org/abs/2411.04268",
        keys=("flag", "lattice"), phrases=("strong coupling", "alpha_s from lattice"),
        notes=("Printed as alpha_MSbar^(5)(M_Z) = 0.11833(67) = 0.1183(7). Both forms are the source's; the longer one is stored.", "FLAG calls the error 'our range': the statistics-dominated error of the combined decoupling and step-scaling results, used instead of the 25 percent smaller error from the weighted average."),
    ),
)

HIGGS_WIDTH_BOUNDS: tuple[Bound, ...] = (
    Bound(
        id="bound.atlas2025e.higgs_width", name="Higgs boson total width, on-shell Higgs and four-top constraint", symbol="Gamma_H",
        lower_text="0", upper_text="160", unit="MeV",
        source="G. Aad et al. (ATLAS Collaboration), Constraint on the total width of the Higgs boson from Higgs boson and four-top-quark measurements in pp collisions at sqrt(s) = 13 TeV with the ATLAS detector, Phys. Lett. B 861, 139277 (2025), doi:10.1016/j.physletb.2025.139277, as listed by PDG 2026 (AAD 2025E).",
        edition="PL B861 139277 (2025), PDG 2026 listing",
        url="https://doi.org/10.1016/j.physletb.2025.139277", retrieved_from=PDG_2026_API, retrieved=RETRIEVED,
        keys=("higgs",), phrases=("higgs width", "width of the higgs", "higgs width bound"),
        conditions=(
            "PDG lists it as <160 MeV at CL = 95%, from p p at 13 TeV, on-shell Higgs and t tbar t tbar.",
            "PDG does not use this limit in its average.",
            "Only the upper limit is printed. The lower end 0 is the edge of a width, not a measurement.",
        ),
        forbids=(),
    ),
)


IAU2015_B3_SOURCE = (
    "IAU 2015 Resolution B3 on Recommended Nominal Conversion Constants for Selected Solar and Planetary Properties, "
    "XXIXth IAU General Assembly, Honolulu (2015), arXiv:1510.07674; rationale in A. Prsa et al., AJ 152, 41 (2016), doi:10.3847/0004-6256/152/2/41."
)
_B3_URL = "https://arxiv.org/abs/1510.07674"
_B3_PDF = "https://arxiv.org/pdf/1510.07674"
_B3_NOMINAL = "The resolution adopts this nominal value as an exact SI conversion constant. It is a conversion factor, not the current best estimate."


def _b3(id: str, name: str, symbol: str, value: str, unit: str, printed_line: str, *, phrases: tuple[str, ...], notes: tuple[str, ...] = ()) -> Quantity:
    return _q(id, name, symbol, value, "exact", unit, kind="exact", source=IAU2015_B3_SOURCE, edition="IAU 2015 Resolution B3",
              url=_B3_URL, retrieved_from=_B3_PDF, keys=("iau", "nominal"), phrases=phrases,
              notes=(f"Printed in the resolution as {printed_line}.", _B3_NOMINAL, *notes))


def _b3_cbe(id: str, name: str, symbol: str, value: str, unc: str, unit: str, kind: str, printed_line: str, *, phrases: tuple[str, ...], notes: tuple[str, ...] = ()) -> Quantity:
    return _q(id, name, symbol, value, unc, unit, kind=kind, source=IAU2015_B3_SOURCE, edition="IAU 2015 Resolution B3, explanatory notes",
              url=_B3_URL, retrieved_from=_B3_PDF, keys=("iau", "current best estimate"), phrases=phrases,
              notes=(f"Printed in the resolution's notes as {printed_line}.", "This is the 2015 current best estimate behind the nominal value. It is not the nominal value.", *notes))


IAU2026_SOURCE = "IAU Commission A3, IAU 2026 System of Astronomical Constants, Numerical Standards for Fundamental Astronomy (page last updated 2026-11-20)."
_IAU2026_URL = "https://iau-a3.gitlab.io/NSFA/IAU2026_consts.html"
_IAU2026_UNC = "The table gives an uncertainty in the same units as the value and does not state its level."


def _iau26(id: str, name: str, symbol: str, value: str, unc: str, scale: str, printed: str, ref: str, *, phrases: tuple[str, ...]) -> Quantity:
    return _q(id, name, symbol, value, unc, "m^3 s^-2", kind="uncertainty as printed, level not stated", source=IAU2026_SOURCE,
              edition="IAU 2026 System of Astronomical Constants", url=_IAU2026_URL, retrieved_from=_IAU2026_URL,
              keys=("iau", "mass parameter"), phrases=phrases,
              notes=(f"Printed as {printed}, uncertainty {scale}.", f"The table's reference for this value: {ref}.", _IAU2026_UNC))


_SIRIUS_BOND = (
    "H. E. Bond, G. H. Schaefer, R. L. Gilliland, J. B. Holberg, B. D. Mason, I. W. Lindenblad, M. Seitz-McLeese, W. D. Arnett, "
    "P. Demarque, F. Spada, P. A. Young, M. A. Barstow, M. R. Burleigh, and D. Gudehus, The Sirius System and Its Astrophysical Puzzles: "
    "Hubble Space Telescope and Ground-based Astrometry, ApJ 840, 70 (2017), doi:10.3847/1538-4357/aa6af8, arXiv:1703.10625."
)
_SIRIUS_JOYCE = (
    "S. R. G. Joyce, M. A. Barstow, J. B. Holberg, H. E. Bond, S. L. Casewell, and M. R. Burleigh, The gravitational redshift of Sirius B, "
    "MNRAS 481, 2361 (2018), doi:10.1093/mnras/sty2404, arXiv:1809.01240."
)
_J0740_KEYS = ("psr j0740+6620", "j0740", "neutron star")
_J0740_PHRASES = ("psr j0740+6620", "neutron star maximum mass", "neutron star radius", "heaviest neutron star")


def _j0740(id: str, name: str, symbol: str, value: str, up: str, low: str, unit: str, kind: str, source: str, edition: str, doi: str, arxiv: str, notes: tuple[str, ...]) -> Quantity:
    return _q(id, name, symbol, value, up, unit, kind=kind, lower_text=low, source=source, edition=edition,
              url=f"https://doi.org/{doi}" if doi else f"https://arxiv.org/abs/{arxiv}", retrieved_from=f"https://export.arxiv.org/api/query?id_list={arxiv}",
              keys=_J0740_KEYS, phrases=_J0740_PHRASES, notes=notes)


ASTROPHYSICS: tuple[Quantity, ...] = (
    _b3("iau2015.nominal.r_sun", "nominal solar radius", "R_sun^N", "6.957 e8", "m", "1 R_sun^N = 6.957 x 10^8 m", phrases=("solar radius", "radius of the sun"),
        notes=("Note 2: it corresponds to the solar photospheric radius of Haberreiter et al. (2008).",)),
    _b3("iau2015.nominal.s_sun", "nominal total solar irradiance", "S_sun^N", "1361", "W m^-2", "1 S_sun^N = 1361 W m^-2", phrases=("solar constant", "total solar irradiance")),
    _b3("iau2015.nominal.l_sun", "nominal solar luminosity", "L_sun^N", "3.828 e26", "W", "1 L_sun^N = 3.828 x 10^26 W", phrases=("solar luminosity", "luminosity of the sun")),
    _b3("iau2015.nominal.teff_sun", "nominal solar effective temperature", "T_eff,sun^N", "5772", "K", "1 T_eff,sun^N = 5772 K", phrases=("solar effective temperature", "temperature of the sun")),
    _b3("iau2015.nominal.gm_sun", "nominal solar mass parameter", "(GM)_sun^N", "1.327 124 4 e20", "m^3 s^-2", "1 (GM)_sun^N = 1.327 124 4 x 10^20 m^3 s^-2",
        phrases=("solar mass parameter", "gm of the sun", "gm sun"),
        notes=("Explanation 1: adopted as an exact number, given with a precision within which its TCB and TDB values agree.",)),
    _b3("iau2015.nominal.r_earth_eq", "nominal terrestrial equatorial radius", "R_eE^N", "6.3781 e6", "m", "1 R_eE^N = 6.3781 x 10^6 m", phrases=("earth radius", "equatorial radius of the earth"),
        notes=("Explanation 6: the Earth's 'zero tide' equatorial radius.",)),
    _b3("iau2015.nominal.r_earth_pol", "nominal terrestrial polar radius", "R_pE^N", "6.3568 e6", "m", "1 R_pE^N = 6.3568 x 10^6 m", phrases=("earth radius", "polar radius of the earth")),
    _b3("iau2015.nominal.r_jup_eq", "nominal jovian equatorial radius", "R_eJ^N", "7.1492 e7", "m", "1 R_eJ^N = 7.1492 x 10^7 m", phrases=("jupiter radius", "equatorial radius of jupiter"),
        notes=("Explanation 7: the one-bar equatorial radius of Jupiter.",)),
    _b3("iau2015.nominal.r_jup_pol", "nominal jovian polar radius", "R_pJ^N", "6.6854 e7", "m", "1 R_pJ^N = 6.6854 x 10^7 m", phrases=("jupiter radius", "polar radius of jupiter")),
    _b3("iau2015.nominal.gm_earth", "nominal terrestrial mass parameter", "(GM)_E^N", "3.986 004 e14", "m^3 s^-2", "1 (GM)_E^N = 3.986 004 x 10^14 m^3 s^-2",
        phrases=("earth mass parameter", "gm of the earth", "gm earth"),
        notes=("Explanation 8: from the IAU 2009 system, rounded to the precision within which its TCB and TDB values agree.",)),
    _b3("iau2015.nominal.gm_jup", "nominal jovian mass parameter", "(GM)_J^N", "1.266 865 3 e17", "m^3 s^-2", "1 (GM)_J^N = 1.266 865 3 x 10^17 m^3 s^-2",
        phrases=("jupiter mass parameter", "gm of jupiter")),
    _b3_cbe("iau2015.cbe.s_sun", "cycle 23 mean total solar irradiance", "S_sun", "1361", "1", "W m^-2", "2 sigma", "S_sun = 1361 W m^-2 (+- 1 W m^-2; 2 sigma)",
            phrases=("solar constant", "total solar irradiance"), notes=("Note 3 names Kopp et al. (in prep.) and the TIM/SORCE scale.",)),
    _b3_cbe("iau2015.cbe.l_sun", "mean solar radiative luminosity", "L_sun", "3.8275 e26", "0.0014 e26", "W", "uncertainty as printed, level not stated",
            "L_sun = 4 pi (1 au)^2 S_sun = 3.8275 (+- 0.0014) x 10^26 W", phrases=("solar luminosity", "luminosity of the sun"),
            notes=("The resolution computes it from the TSI and the au; it is stored as printed and not recomputed here.",)),
    _b3_cbe("iau2015.cbe.teff_sun", "solar effective temperature", "T_eff,sun", "5772.0", "0.8", "K", "uncertainty as printed, level not stated",
            "T_eff,sun = 5772.0 (+- 0.8) K", phrases=("solar effective temperature", "temperature of the sun"),
            notes=("The resolution calculates it from the luminosity, the photospheric radius and the CODATA 2014 Stefan-Boltzmann constant; it is stored as printed.",)),
    _b3_cbe("haberreiter2008.r_sun", "solar photospheric radius (tau_Ross = 2/3)", "R_sun", "695 658", "140", "km", "uncertainty as printed, level not stated",
            "695 658 (+- 140) km", phrases=("solar radius", "radius of the sun"),
            notes=("Note 2 quotes M. Haberreiter et al. (2008); the original paper was not read here.",)),
    _q("iau2012.au", "astronomical unit", "au", "149 597 870 700", "exact", "m", kind="exact",
       source="IAU 2012 Resolution B2, XXVIIIth IAU General Assembly, Beijing (2012), as quoted in note 4 of IAU 2015 Resolution B3 (arXiv:1510.07674) and in the IAU 2026 System of Astronomical Constants.",
       edition="IAU 2012 Resolution B2", url=_IAU2026_URL, retrieved_from=_B3_PDF,
       keys=("iau",), phrases=("astronomical unit", "earth-sun distance", "au in meters"),
       notes=("Printed as 'a conventional unit of length equal to 149 597 870 700 m exactly'.", "The IAU 2026 table lists it as 1.495 978 707 00 x 10^11 m, 'defined', citing the IAU 2012 Transactions.", "The IAU copy of the 2012 resolution text did not resolve from the box, so the wording is the one quoted in IAU 2015 B3.")),
    _iau26("iau2026.gm_sun_tcb", "solar mass parameter, TCB-compatible", "GM_S", "1.327 124 420 995 e20", "1.0 e8", "1.0 x 10^8",
           "1.327 124 420 995 x 10^20 m^3 s^-2 [TCB]", "Fienga et al., INPOP21a Planetary Ephemerides (2021)", phrases=("solar mass parameter", "gm of the sun", "gm sun")),
    _iau26("iau2026.gm_sun_tdb", "solar mass parameter, TDB-compatible", "GM_S", "1.327 124 400 418 e20", "1.0 e8", "1.0 x 10^8",
           "1.327 124 400 418 x 10^20 m^3 s^-2 [TDB]", "Fienga et al., INPOP21a Planetary Ephemerides (2021)", phrases=("solar mass parameter", "gm of the sun", "gm sun")),
    _iau26("iau2026.gm_earth_tcb", "geocentric gravitational constant, TCB-compatible", "GM_E", "3.986 004 417 e14", "3 e5", "3 x 10^5",
           "3.986 004 417 x 10^14 m^3 s^-2 [TCB]", "Park et al., The JPL Planetary and Lunar Ephemerides DE440 and DE441, AJ 161, 105 (2021)", phrases=("earth mass parameter", "gm of the earth", "gm earth")),
    _iau26("iau2026.gm_earth_tt", "geocentric gravitational constant, TT-compatible", "GM_E", "3.986 004 414 e14", "3 e5", "3 x 10^5",
           "3.986 004 414 x 10^14 m^3 s^-2 [TT]", "Park et al., The JPL Planetary and Lunar Ephemerides DE440 and DE441, AJ 161, 105 (2021)", phrases=("earth mass parameter", "gm of the earth", "gm earth")),
    _iau26("iau2026.gm_earth_tdb", "geocentric gravitational constant, TDB-compatible", "GM_E", "3.986 004 355 e14", "3 e5", "3 x 10^5",
           "3.986 004 355 x 10^14 m^3 s^-2 [TDB]", "Park et al., The JPL Planetary and Lunar Ephemerides DE440 and DE441, AJ 161, 105 (2021)", phrases=("earth mass parameter", "gm of the earth", "gm earth")),
    _q("williams2016.lunar_da_dt", "secular rate of the lunar semimajor axis from lunar laser ranging", "da/dt", "38.30", "0.08", "mm/year",
       kind="uncertainty as printed, level not stated",
       source="J. G. Williams and D. H. Boggs, Secular tidal changes in lunar orbit and Earth rotation, Celest. Mech. Dyn. Astron. 126, 89-129 (2016), doi:10.1007/s10569-016-9702-3.",
       edition="Celest. Mech. Dyn. Astron. 126 (2016)", url="https://doi.org/10.1007/s10569-016-9702-3",
       retrieved_from="https://discovery.researcher.life/article/secular-tidal-changes-in-lunar-orbit-and-earth-rotation/7d0bf781b53f32dcaa68c4bde99bc325",
       keys=("lunar laser ranging", "llr"), phrases=("lunar recession", "moon recession", "moon moving away", "earth-moon distance"),
       notes=("Printed in the abstract as da/dt = 38.30 +- 0.08 mm/year, from LLR dissipation parameters converted to secular rates.", "The abstract was read from a mirror of the publisher's abstract, because Springer and ADS did not serve it to the box.")),
    _q("nssdc.moon.semimajor_axis", "semimajor axis of the Moon's orbit about the Earth", "a_Moon", "0.3844 e6", "", "km", kind="no uncertainty printed",
       source="D. R. Williams, Moon Fact Sheet, NASA Space Science Data Coordinated Archive (last updated 11 January 2024).",
       edition="NSSDCA Moon Fact Sheet (2024-01-11)", url="https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html",
       retrieved_from="https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html",
       keys=("moon",), phrases=("earth-moon distance", "distance to the moon", "lunar distance"),
       notes=("Printed as 'Semimajor axis (10^6 km) 0.3844'. The same sheet gives mean perigee 0.3633 and mean apogee 0.4055 (10^6 km).",)),
    _q("nssdc.moon.recession", "recession rate of the Moon from Earth", "da/dt", "3.8", "", "cm/yr", kind="no uncertainty printed",
       source="D. R. Williams, Moon Fact Sheet, NASA Space Science Data Coordinated Archive (last updated 11 January 2024).",
       edition="NSSDCA Moon Fact Sheet (2024-01-11)", url="https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html",
       retrieved_from="https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html",
       keys=("moon",), phrases=("lunar recession", "moon recession", "moon moving away"),
       notes=("Printed as 'Recession rate from Earth (cm/yr) 3.8'.",)),
    _q("bond2017.sirius_b.mass", "dynamical mass of Sirius B", "M_B", "1.018", "0.011", "M_sun", kind="uncertainty as printed, level not stated",
       source=_SIRIUS_BOND, edition="ApJ 840, 70 (2017)", url="https://doi.org/10.3847/1538-4357/aa6af8", retrieved_from="https://arxiv.org/pdf/1703.10625",
       keys=("sirius b", "white dwarf"), phrases=("sirius b", "white dwarf mass", "mass of sirius b"),
       notes=("Printed in the abstract and Table 6 as 1.018 +- 0.011 M_sun, from the visual-binary orbit and parallax.",)),
    _q("bond2017.sirius_b.radius", "radius of Sirius B from its absolute flux", "R_B", "0.008098", "0.000046", "R_sun", kind="uncertainty as printed, level not stated",
       source=_SIRIUS_BOND, edition="ApJ 840, 70 (2017)", url="https://doi.org/10.3847/1538-4357/aa6af8", retrieved_from="https://arxiv.org/pdf/1703.10625",
       keys=("sirius b", "white dwarf"), phrases=("sirius b", "white dwarf radius", "radius of sirius b"),
       notes=("Printed as 'the implied radius of Sirius B is 0.008098 +- 0.000046 R_sun'.", "The paper says the quoted uncertainties are internal errors of the model fits and do not include the modestly larger systematic uncertainties.")),
    _q("joyce2018.sirius_b.mass", "gravitational-redshift mass of Sirius B", "M_B", "1.017", "0.025", "M_sun", kind="uncertainty as printed, level not stated",
       source=_SIRIUS_JOYCE, edition="MNRAS 481, 2361 (2018)", url="https://doi.org/10.1093/mnras/sty2404", retrieved_from="https://arxiv.org/pdf/1809.01240",
       keys=("sirius b", "white dwarf"), phrases=("sirius b", "white dwarf mass", "mass of sirius b"),
       notes=("Printed in the abstract as 1.017 +- 0.025 M_sun, from a measured gravitational redshift of 80.65 +- 0.77 km s^-1 and the radius below.",)),
    _q("joyce2018.sirius_b.radius", "radius of Sirius B used for the redshift mass", "R_B", "0.803", "0.011", "R_sun/100", kind="uncertainty as printed, level not stated",
       source=_SIRIUS_JOYCE, edition="MNRAS 481, 2361 (2018)", url="https://doi.org/10.1093/mnras/sty2404", retrieved_from="https://arxiv.org/pdf/1809.01240",
       keys=("sirius b", "white dwarf"), phrases=("sirius b", "white dwarf radius", "radius of sirius b"),
       notes=("Printed as 'The radius of 0.803 +- 0.011 R_sun/100', from the G430L flux and the Bond et al. (2017) parallax. The unit is kept as printed.",)),
    _j0740("fonseca2021.j0740.mass", "mass of PSR J0740+6620 from Shapiro delay", "m_p", "2.08", "0.07", "0.07", "M_sun", "68.3% credible interval",
           "E. Fonseca et al., Refined Mass and Geometric Measurements of the High-mass PSR J0740+6620, ApJL 915, L12 (2021), doi:10.3847/2041-8213/ac03b8, arXiv:2104.00880.",
           "ApJL 915, L12 (2021)", "10.3847/2041-8213/ac03b8", "2104.00880",
           ("Printed in the abstract as m_p = 2.08^{+0.07}_{-0.07} M_sun (68.3% credibility), from the relativistic Shapiro time delay.",)),
    _j0740("riley2021.j0740.radius", "equatorial radius of PSR J0740+6620, NICER and XMM (Riley et al.)", "R_eq", "12.39", "1.30", "0.98", "km", "68% interval",
           "T. E. Riley et al., A NICER View of the Massive Pulsar PSR J0740+6620 Informed by Radio Timing and XMM-Newton Spectroscopy, ApJL 918, L27 (2021), doi:10.3847/2041-8213/ac0a81, arXiv:2105.06980.",
           "ApJL 918 (2021)", "10.3847/2041-8213/ac0a81", "2105.06980",
           ("Printed in the abstract as 12.39_{-0.98}^{+1.30} km, the posterior credible interval bounded by the 16% and 84% quantiles.", "The radius prior is truncated at 16 km.")),
    _j0740("miller2021.j0740.radius", "equatorial radius of PSR J0740+6620, NICER and XMM (Miller et al.)", "R_eq", "13.7", "2.6", "1.5", "km", "68% interval",
           "M. C. Miller et al., The Radius of PSR J0740+6620 from NICER and XMM-Newton Data, ApJL 918, L28 (2021), doi:10.3847/2041-8213/ac089b, arXiv:2105.06979.",
           "ApJL 918 (2021)", "10.3847/2041-8213/ac089b", "2105.06979",
           ("Printed in the abstract as 13.7^{+2.6}_{-1.5} km (68%).",)),
    _j0740("salmi2024.j0740.radius", "equatorial radius of PSR J0740+6620, 3.6 yr of NICER data (Salmi et al.)", "R_eq", "12.49", "1.28", "0.88", "km", "68% interval",
           "T. Salmi et al., The Radius of the High-mass Pulsar PSR J0740+6620 with 3.6 yr of NICER Data, ApJ 974, 294 (2024), doi:10.3847/1538-4357/ad5f1f, arXiv:2406.14466.",
           "ApJ 974, 294 (2024)", "10.3847/1538-4357/ad5f1f", "2406.14466",
           ("Printed in the abstract as 12.49_{-0.88}^{+1.28} km, bounded by the 16% and 84% quantiles, with an estimated systematic error <~ 0.1 km.",)),
    _j0740("dittmann2024.j0740.radius", "equatorial radius of PSR J0740+6620, updated NICER data (Dittmann et al.)", "R_eq", "12.92", "2.09", "1.13", "km", "68% interval",
           "A. J. Dittmann et al., A More Precise Measurement of the Radius of PSR J0740+6620 Using Updated NICER Data, arXiv:2406.14467 (2024).",
           "arXiv:2406.14467 (2024)", "", "2406.14467",
           ("Printed in the abstract as 12.92_{-1.13}^{+2.09} km (68% credibility).", "With the radius required below 16 km, the abstract gives 12.76_{-1.02}^{+1.49} km; that variant is not stored separately.")),
)


_AME_LIGHT = (
    # (sym, name, z, n, a, mass excess keV, unc, B/A keV, unc, atomic mass micro-u, unc), from mass_1.mas20.txt
    ("li6", "lithium-6", 3, 3, 6, "14086.88044", "0.00144", "5332.3312", "0.0003", "6 015122.88742", "0.00155"),
    ("li7", "lithium-7", 3, 4, 7, "14907.10463", "0.00419", "5606.4401", "0.0006", "7 016003.43426", "0.00450"),
    ("be9", "beryllium-9", 4, 5, 9, "11348.451", "0.076", "6462.6693", "0.0085", "9 012183.062", "0.082"),
    ("b10", "boron-10", 5, 5, 10, "12050.611", "0.015", "6475.0835", "0.0015", "10 012936.862", "0.016"),
    ("b11", "boron-11", 5, 6, 11, "8667.708", "0.012", "6927.7323", "0.0011", "11 009305.166", "0.013"),
    ("c13", "carbon-13", 6, 7, 13, "3125.00933", "0.00023", "7469.8495", "0.0002", "13 003354.83534", "0.00025"),
    ("n14", "nitrogen-14", 7, 7, 14, "2863.41683", "0.00022", "7475.6148", "0.0002", "14 003074.00425", "0.00024"),
    ("n15", "nitrogen-15", 7, 8, 15, "101.43809", "0.00058", "7699.4603", "0.0002", "15 000108.89827", "0.00062"),
    ("o17", "oxygen-17", 8, 9, 17, "-808.76421", "0.00064", "7750.7291", "0.0002", "16 999131.75595", "0.00069"),
    ("o18", "oxygen-18", 8, 10, 18, "-782.81634", "0.00064", "7767.0981", "0.0002", "17 999159.61214", "0.00069"),
)


def _ame_light(sym: str, name: str, z: int, n: int, a: int, dm: str, dmu: str, ba: str, bau: str, m: str, mu: str) -> tuple[Quantity, ...]:
    label = sym[0].upper() + sym[1:].rstrip("0123456789")
    tag = f"{a}{label}"
    return (
        _ame(f"ame2020.{sym}.atomic_mass", f"atomic mass of {name}", f"M({tag})", m, mu, "micro-u", z=z, n=n, a=a, phrases=(f"atomic mass of {name}",)),
        _ame(f"ame2020.{sym}.mass_excess", f"mass excess of {name}", f"Delta({tag})", dm, dmu, "keV", z=z, n=n, a=a, phrases=(f"mass excess of {name}",)),
        _ame(f"ame2020.{sym}.binding_per_nucleon", f"binding energy per nucleon of {name}", f"B/A({tag})", ba, bau, "keV", z=z, n=n, a=a,
             phrases=(f"binding energy per nucleon of {name}", "binding energy per nucleon")),
    )


_PDG_LIFE_NOTE = "PDG 2026 summary-table value."
_PDG_SF = "The PDG database stores a scale factor of {0} for this error."

NUCLEAR_PARTICLE_B6: tuple[Quantity, ...] = tuple(q for row in _AME_LIGHT for q in _ame_light(*row)) + (
    _q("ame2020.n.beta_decay_energy", "beta-decay energy of the free neutron", "Q_beta-(n)", "782.3470", "0.0004", "keV", kind="standard uncertainty",
       source=AME2020_SOURCE, edition=AME2020_EDITION, url=AME2020_PAPER_II, retrieved_from=AME2020_FILE, keys=("ame2020", "neutron decay"),
       phrases=("neutron beta decay", "neutron beta-decay energy", "neutron decay endpoint", "beta-decay endpoint"),
       notes=("Read from the 'B- beta' column of the neutron row in mass.mas20: 782.3470 with uncertainty 0.0004 keV.", _AME_SIGMA,
              "AME tabulates the beta-decay energy Q; the record stores that column and does not compute an electron endpoint from it.", _AME_FILE)),
    _pdg("pdg2026.pi_plus_lifetime", "charged pion mean life", "tau_pi+-", "2.6033 e-8", "0.0005 e-8", "s", node="S008T", keys=("pion",), phrases=("pion lifetime", "charged pion lifetime", "pion mean life"),
         notes=("Printed as (2.6033+-0.0005)E-8 s.", _PDG_LIFE_NOTE, _PDG_SF.format("1.174286"), _API_NOTE)),
    _pdg("pdg2026.pi0_lifetime", "neutral pion mean life", "tau_pi0", "8.43 e-17", "0.13 e-17", "s", node="S009T", keys=("pion",), phrases=("pion lifetime", "neutral pion lifetime", "pi0 lifetime"),
         notes=("Printed as (8.43+-0.13)E-17 s.", _PDG_LIFE_NOTE, _PDG_SF.format("1.245535"), _API_NOTE)),
    _pdg("pdg2026.k_plus_lifetime", "charged kaon mean life", "tau_K+-", "1.2380 e-8", "0.0020 e-8", "s", node="S010T", keys=("kaon",), phrases=("kaon lifetime", "charged kaon lifetime", "kaon mean life"),
         notes=("Printed as (1.2380+-0.0020)E-8 s, PDG's fit value. PDG's average, (1.2379+-0.0021)E-8 s, is in the database but not stored.", _PDG_SF.format("1.839949"), _API_NOTE)),
    _pdg("pdg2026.k_short_lifetime", "K_S mean life, assuming CPT", "tau_KS", "8.954 e-11", "0.004 e-11", "s", node="S012T", keys=("kaon",), phrases=("kaon lifetime", "k short lifetime", "ks lifetime"),
         notes=("Printed as (8.954+-0.004)E-11 s under 'Assuming CPT'. Without assuming CPT PDG prints (8.9564+-0.0033)E-11 s; that value is not stored.", _PDG_SF.format("1.122566"), _API_NOTE)),
    _pdg("pdg2026.k_long_lifetime", "K_L mean life", "tau_KL", "5.116 e-8", "0.021 e-8", "s", node="S013T", keys=("kaon",), phrases=("kaon lifetime", "k long lifetime", "kl lifetime"),
         notes=("Printed as (5.116+-0.021)E-8 s, PDG's fit value. PDG's average, (5.099+-0.021)E-8 s, is in the database but not stored.", _PDG_SF.format("1.067168"), _API_NOTE)),
    _pdg("pdg2026.mu_lifetime", "muon mean life", "tau_mu", "2.1969811 e-6", "0.0000022 e-6", "s", node="S004T", keys=("muon",), phrases=("muon lifetime", "muon mean life"),
         notes=("Printed as (2.1969811+-0.0000022)E-6 s. PDG lists MuLan (TISHCHENKO 2013) as (2.1969803+-0.0000021+-0.0000007) E-6 s and uses it in the average.", _API_NOTE)),
    _q("mulan2013.mu_lifetime", "positive muon lifetime, MuLan", "tau_mu+", "2196980.3", "2.2", "ps", kind="uncertainty as printed, level not stated", printed="2196980.3(2.2)",
       source="V. Tishchenko et al. (MuLan Collaboration), Detailed report of the MuLan measurement of the positive muon lifetime and determination of the Fermi constant, Phys. Rev. D 87, 052003 (2013), doi:10.1103/PhysRevD.87.052003, arXiv:1211.0960.",
       edition="Phys. Rev. D 87 (2013)", url="https://doi.org/10.1103/PhysRevD.87.052003", retrieved_from="https://export.arxiv.org/api/query?id_list=1211.0960",
       keys=("mulan", "muon"), phrases=("muon lifetime", "muon mean life", "mulan"),
       notes=("Printed in the abstract as tau_mu(MuLan) = 2196980.3(2.2) ps (1.0 ppm).", "The abstract also gives G_F(MuLan) = 1.1663787(6) x 10^-5 GeV^-2; that is a derived quantity and is not stored here.")),
)


ASD_QUERY_IE2 = (
    "https://physics.nist.gov/cgi-bin/ASD/ie.pl?spectra=He-Ne+II&submit=Retrieve+Data&units=1&format=2&order=0"
    "&at_num_out=on&sp_name_out=on&ion_charge_out=on&el_name_out=on&seq_out=on&shells_out=on&level_out=on"
    "&ion_conf_out=on&e_out=0&unc_out=on&biblio=on"
)


def _asd2(id: str, z: int, element: str, spectrum: str, value_text: str, uncertainty_text: str, *, notes: tuple[str, ...]) -> Quantity:
    lower = element.lower()
    return _q(
        id, f"second ionization energy of {lower} ({spectrum}, Z = {z})", f"E_i({spectrum})", value_text, uncertainty_text, "eV",
        kind="uncertainty as printed, level not stated", source=ASD_SOURCE, edition=ASD_EDITION, url=ASD_QUERY_IE2, retrieved_from=ASD_QUERY_IE2,
        keys=("second ionization energy",), phrases=(f"second ionization energy of {lower}", "second ionization energies", f"{lower} second ionization energy"),
        notes=("Ionization energy of the singly charged ion (ASD ion charge +1).", *notes),
    )


_RK2002_SOURCE = (
    "J. C. Rienstra-Kiracofe, G. S. Tschumper, H. F. Schaefer III, S. Nandi, and G. B. Ellison, Atomic and Molecular Electron Affinities: "
    "Photoelectron Experiments and Theoretical Computations, Chem. Rev. 102, 231-282 (2002), doi:10.1021/cr990044u, Table 10."
)
_RK_COPY = (
    "https://web.archive.org/web/20250708031823/https://scholarsmine.mst.edu/cgi/viewcontent.cgi?article=4920&context=chem_facwork"
)
_RK_NOTE = "Table 10 lists photoelectron and threshold-detachment values reviewed through January 2000. The review does not state a confidence level for the +- column."


def _rk(sym: str, name: str, value: str, unc: str, ref: str, extra: tuple[str, ...] = ()) -> Quantity:
    return _q(
        f"rk2002.ea.{sym.lower()}", f"electron affinity of {name}", f"EA({sym})", value, unc, "eV", kind="uncertainty as printed, level not stated",
        source=_RK2002_SOURCE, edition="Chem. Rev. 102 (2002), Table 10", url="https://doi.org/10.1021/cr990044u", retrieved_from=_RK_COPY,
        keys=("electron affinity",), phrases=(f"electron affinity of {name}", "electron affinities", f"{name} electron affinity"),
        notes=(f"Printed in Table 10 as {value} +- {unc} eV, method ThD, Table 10 reference {ref}.", _RK_NOTE,
               "Read from the authors' institutional repository copy (Missouri S&T Scholars' Mine) through the Internet Archive, since the live repository served a bot check.", *extra),
    )


ATOMIC_MOLECULAR_B6: tuple[Quantity, ...] = (
    _asd2("asd512.ie2.he", 2, "Helium", "He II", "54.4177655282", "0.0000000010", notes=('ASD ground shells 1s, ground level 2S<1/2>.', 'ASD bibliography codes: L19200.', 'ASD prints this energy in parentheses. The ASD help says parentheses mark energies from an ab-initio calculation, or otherwise not derived from evaluated experimental data.', _ASD_EV)),
    _asd2("asd512.ie2.li", 3, "Lithium", "Li II", "75.6400970", "0.0000012", notes=('ASD ground shells 1s2, ground level 1S0, ionized level 1s 2S<1/2>.', 'ASD bibliography codes: L10054.', 'ASD prints this energy in parentheses. The ASD help says parentheses mark energies from an ab-initio calculation, or otherwise not derived from evaluated experimental data.', _ASD_EV)),
    _asd2("asd512.ie2.be", 4, "Beryllium", "Be II", "18.21115", "0.00004", notes=('ASD ground shells 1s2.2s, ground level 2S<1/2>, ionized level 1s2 1S<0>.', 'ASD bibliography codes: L12158.', _ASD_EV)),
    _asd2("asd512.ie2.b", 5, "Boron", "B II", "25.15483", "0.00005", notes=('ASD ground shells 1s2.2s2, ground level 1S0, ionized level 2s 2S<1/2>.', 'ASD bibliography codes: L12120.', _ASD_EV)),
    _asd2("asd512.ie2.c", 6, "Carbon", "C II", "24.383143", "0.000012", notes=('ASD ground shells 1s2.2s2.2p, ground level 2P*<1/2>, ionized level 2s2 1S<0>.', 'ASD bibliography codes: L22145.', _ASD_EV)),
    _asd2("asd512.ie2.n", 7, "Nitrogen", "N II", "29.60125", "0.00009", notes=('ASD ground shells 1s2.2s2.2p2, ground level 3P0, ionized level 2p 2P*<1/2>.', 'ASD bibliography codes: L11770.', 'ASD prints this energy in square brackets. The ASD help says brackets mark energies determined by interpolation, extrapolation, or another semi-empirical procedure relying on some known experimental values.', _ASD_EV)),
    _asd2("asd512.ie2.o", 8, "Oxygen", "O II", "35.12112", "0.00006", notes=('ASD ground shells 1s2.2s2.2p3, ground level 4S*<3/2>, ionized level 2p2 3P<0>.', 'ASD bibliography codes: L11267,L10621.', _ASD_EV)),
    _asd2("asd512.ie2.f", 9, "Fluorine", "F II", "34.97081", "0.00012", notes=('ASD ground shells 1s2.2s2.2p4, ground level 3P<2>, ionized level 2p3 4S*<3/2>.', 'ASD bibliography codes: L369.', _ASD_EV)),
    _asd2("asd512.ie2.ne", 10, "Neon", "Ne II", "40.96297", "0.00004", notes=('ASD ground shells 1s2.2s2.2p5, ground level 2P*<3/2>, ionized level 2p4 3P<2>.', 'ASD bibliography codes: L1406.', _ASD_EV)),
    _rk("H", "hydrogen", "0.75419", "0.00002", "47"),
    _rk("C", "carbon", "1.262119", "0.000020", "286"),
    _rk("O", "oxygen", "1.4611100", "0.00000007", "40"),
    _rk("F", "fluorine", "3.401290", "0.000003", "40",
        ("Kept as printed. The NIST Chemistry WebBook lists Blondel, Delsart, et al. (2001) as 'Given: 3.4011895(25) eV', which differs from the printed 3.401290 in the fourth decimal; the difference is not resolved here.",)),
    _rk("Cl", "chlorine", "3.612724", "0.00003", "305"),
    _q("holsch2019.h2.d0_ortho", "dissociation energy of ortho-H2 (N = 1)", "D_0^{N=1}(H2)", "35 999.582 834", "0.000 011", "cm^-1",
       kind="uncertainty as printed, level not stated", printed="35 999.582 834(11)",
       source="N. Hoelsch, M. Beyer, E. J. Salumbides, K. S. E. Eikema, W. Ubachs, C. Jungen, and F. Merkt, Benchmarking Theory with an Improved Measurement of the Ionization and Dissociation Energies of H2, Phys. Rev. Lett. 122, 103002 (2019), doi:10.1103/PhysRevLett.122.103002, arXiv:1902.09471.",
       edition="Phys. Rev. Lett. 122 (2019)", url="https://doi.org/10.1103/PhysRevLett.122.103002", retrieved_from="https://export.arxiv.org/api/query?id_list=1902.09471",
       keys=("h2", "hydrogen molecule"), phrases=("h2 dissociation energy", "dissociation energy of h2", "hydrogen molecule dissociation"),
       notes=("Printed in the abstract as 35 999.582 834(11) cm-1 for D_0^{N=1} of ortho-H2; the paper gives the uncertainty as 340 kHz.",
              "This is the measured value. The theoretical value the abstract compares it with (Puchalski et al. 2019) is a calculation and is not stored.",
              "It is ortho-H2 (N = 1), so it is not the same quantity as the para-H2 ground-state D0, and it is not compared with the CCCBDB 0 K value on the board.")),
)


_BLONDEL2001_SOURCE = (
    "C. Blondel, C. Delsart, and F. Goldfarb, Electron spectrometry at the mu eV level and the electron affinities of Si and F, "
    "J. Phys. B: At. Mol. Opt. Phys. 34, L281-L288 (2001), doi:10.1088/0953-4075/34/9/101, as cited in the NIST Chemistry WebBook (SRD 69), fluorine atom, electron affinity determinations."
)
_PDG_BBN_SOURCE = (
    "B. D. Fields, P. Molaro, and S. Sarkar, 24. Big-Bang Nucleosynthesis, in Review of Particle Physics (Particle Data Group), revised August 2025, "
    "pdg.lbl.gov 2026 edition."
)
_PDG_BBN_URL = "https://pdg.lbl.gov/2026/reviews/rpp2026-rev-bbang-nucleosynthesis.pdf"
_BBN_KEYS = ("bbn", "big bang nucleosynthesis", "primordial abundance", "early universe")


def _bbn(id: str, name: str, symbol: str, value: str, unc: str, unit: str, *, phrases: tuple[str, ...], notes: tuple[str, ...]) -> Quantity:
    return _q(id, name, symbol, value, unc, unit, kind="uncertainty as printed, level not stated", source=_PDG_BBN_SOURCE,
              edition="PDG 2026 review 24 (revised August 2025)", url=_PDG_BBN_URL, retrieved_from=_PDG_BBN_URL,
              keys=_BBN_KEYS, phrases=phrases, notes=notes)


EARLY_UNIVERSE: tuple[Quantity, ...] = (
    _q("blondel2001.ea.f", "electron affinity of fluorine", "EA(F)", "3.401 1895", "0.000 0025", "eV",
       kind="uncertainty as printed, level not stated", printed="3.401 1895(25)",
       source=_BLONDEL2001_SOURCE, edition="J. Phys. B 34 (2001), via NIST WebBook", url="https://doi.org/10.1088/0953-4075/34/9/101",
       retrieved_from="https://webbook.nist.gov/cgi/cbook.cgi?ID=C14762948&Mask=20",
       keys=("electron affinity",), phrases=("electron affinity of fluorine", "fluorine electron affinity", "electron affinities"),
       notes=("The WebBook lists this paper as 'Given: 3.4011895(25) eV, or 27432.446(19) cm-1, or 78.433266(577) kcal/mol' and tabulates it as 3.401191 +- 0.000026 eV; the record keeps the paper's own printed value.",
              "The journal's abstract page could not be read (the IOP article page returned an error and Crossref carries no abstract). The corrigendum, J. Phys. B 34, 2757 (2001), doi:10.1088/0953-4075/34/13/701, concerns the Doppler-broadening contrast factor; its page prints no new affinity.",
              "Stored next to rk2002.ea.f, which prints 3.401290 +- 0.000003 eV for the same quantity and cites Blondel, Phys. Scr. 1995 (Table 10 ref. 40). The two printed values differ by about 1.0e-4 eV, far outside either uncertainty. The board keeps both as printed and does not decide between them.",
              "The WebBook also lists Blondel, Cacciani, et al. 1989 as 'Reported: 3.401190+-0.000004 eV'. That line is not stored as a record.")),
    _bbn("pdg2026.bbn.y_p", "primordial helium-4 mass fraction", "Y_p", "0.245", "0.003", "",
         phrases=("primordial helium", "helium abundance", "y_p", "primordial abundances"),
         notes=("Printed as eq. 24.3, the review's recommended value.",
                "The review says the uncertainty reflects the combined statistical and systematic errors, with the systematic part, estimated at +-0.002, dominant.")),
    _q("aver2021.y_p", "primordial helium-4 mass fraction", "Y_p", "0.2453", "0.0034", "",
       kind="uncertainty as printed, level not stated",
       source="E. Aver, D. A. Berg, K. A. Olive, R. W. Pogge, J. J. Salzer, and E. D. Skillman, Improving helium abundance determinations with Leo P as a case study, JCAP 03 (2021) 027, doi:10.1088/1475-7516/2021/03/027, arXiv:2010.04180.",
       edition="JCAP 2021", url="https://doi.org/10.1088/1475-7516/2021/03/027", retrieved_from="https://export.arxiv.org/api/query?id_list=2010.04180",
       keys=_BBN_KEYS, phrases=("primordial helium", "helium abundance", "y_p", "primordial abundances"),
       notes=("Printed in the abstract as Y_p = 0.2453 +- 0.0034. The PDG review's Table 24.2 lists it with 16 systems.",)),
    _bbn("pdg2026.bbn.d_h", "primordial deuterium-to-hydrogen ratio", "D/H|_p", "25.08 e-6", "0.29 e-6", "",
         phrases=("primordial deuterium", "deuterium abundance", "d/h", "primordial abundances"),
         notes=("Printed as eq. 24.2: D/H|p x 10^6 = 25.08 (+-0.27 x S) = 25.08 (+-0.29), the weighted mean of the 12 systems in Table 24.1 with the error scaled by S = 1.08.",)),
    _q("cooke2018.d_h", "primordial deuterium-to-hydrogen ratio", "(D/H)_P", "2.527 e-5", "0.030 e-5", "",
       kind="uncertainty as printed, level not stated",
       source="R. J. Cooke, M. Pettini, and C. C. Steidel, One percent determination of the primordial deuterium abundance, Astrophys. J. 855, 102 (2018), doi:10.3847/1538-4357/aaab53, arXiv:1710.11129.",
       edition="ApJ 855 (2018)", url="https://doi.org/10.3847/1538-4357/aaab53", retrieved_from="https://export.arxiv.org/api/query?id_list=1710.11129",
       keys=_BBN_KEYS, phrases=("primordial deuterium", "deuterium abundance", "d/h", "primordial abundances"),
       notes=("Printed in the abstract as (D/H)_P = (2.527+/-0.030)x10^-5, and as log10(D/H)_P = -4.5974+/-0.0052; only the linear form is stored.",)),
    _bbn("pdg2026.bbn.li_h", "primordial lithium-7-to-hydrogen ratio (Spite plateau)", "Li/H|_p", "1.45 e-10", "0.25 e-10", "",
         phrases=("primordial lithium", "lithium abundance", "spite plateau", "lithium problem", "primordial abundances"),
         notes=("Printed as eq. 24.4, from halo stars with -3.5 < [Fe/H] < -1.5.",
                "The review says this inferred primordial abundance should strictly be regarded as a lower bound rather than a direct measurement, since 7Li in Population II stars may have been partly destroyed.")),
    _bbn("fields2020.li_h", "standard BBN lithium-7-to-hydrogen ratio (as quoted by PDG)", "Li/H|_p (BBN)", "4.72 e-10", "0.7 e-10", "",
         phrases=("lithium problem", "bbn lithium prediction", "primordial abundances"),
         notes=("Printed as eq. 24.10, 'the primordial value from [45]', ref. 45 being B. D. Fields et al., JCAP 03 (2020) 010, arXiv:1912.01132. It is the source's standard-BBN value for the D/H and CMB baryon density; it is not computed here.",
                "The review says it exceeds the value of eq. 24.4 by a factor of 3.3, corresponding to a 4.4 sigma discrepancy. This is the lithium problem.")),
    _q("planck2018.n_eff", "effective number of relativistic species", "N_eff", "2.99", "0.17", "",
       kind="68% interval", source=PLANCK_2018_SOURCE.replace(", Table 2.", ", abstract."), edition="Planck 2018 VI, base-LCDM+N_eff, Planck+BAO",
       url=PLANCK_2018_URL, retrieved_from=PLANCK_2018_PDF, keys=_PLANCK_KEYS + ("early universe",),
       phrases=("effective number of neutrino species", "n_eff", "neff", "relativistic degrees of freedom"),
       notes=("Printed in the abstract as Neff = 2.99 +- 0.17, from combining Planck with BAO; the abstract quotes 68% intervals.",
              "The number is a fit of the LCDM+N_eff model, not a model-free measurement. The abstract's comparison value 3.046 is a theory number and is not stored.")),
    _q("planck2018.n_eff_95", "effective number of relativistic species (95% interval)", "N_eff", "2.99", "0.34", "",
       kind="95% interval", lower_text="0.33", source=PLANCK_2018_SOURCE.replace(", Table 2.", ", eq. 67b."), edition="Planck 2018 VI, base-LCDM+N_eff, TT,TE,EE+lowE+lensing+BAO",
       url=PLANCK_2018_URL, retrieved_from=PLANCK_2018_PDF, keys=_PLANCK_KEYS + ("early universe",),
       phrases=("effective number of neutrino species", "n_eff", "neff"),
       notes=("Printed as eq. 67b: Neff = 2.99 +0.34 -0.33 (95%, TT,TE,EE+lowE+lensing+BAO).",
              "Same data combination as planck2018.n_eff, at 95% rather than 68%.")),
)


def _inspire(doi: str) -> str:
    return f"https://inspirehep.net/api/literature?q=doi:{doi}"


_PS_KEYS = ("positronium", "exotic atom", "bound-state qed")
_HE_FS_KEYS = ("helium fine structure", "helium 2 3p")
_HE_NOTE = "Measured interval of 4He 2 3P; QED theory values the paper compares it with are calculations and are not stored."
_ZEL_SOURCE = "T. Zelevinsky, Helium 2 3P Fine Structure Measurement in a Discharge Cell, Ph.D. thesis, Harvard University (2004), abstract."
_ZEL_URL = "https://cfp.physics.northwestern.edu/documents/2004_Zelevinsky_Tanya.pdf"


def _zel(id: str, name: str, symbol: str, value: str, unc: str, printed: str, label: str) -> Quantity:
    return _q(id, name, symbol, value, unc, "kHz", kind="uncertainty as printed, level not stated", printed=printed,
              source=_ZEL_SOURCE, edition="Harvard Ph.D. thesis 2004", url=_ZEL_URL, retrieved_from=_ZEL_URL,
              keys=_HE_FS_KEYS, phrases=(f"helium {label} interval", "helium fine structure", "helium 2 3p fine structure"),
              notes=(f"Printed in the thesis abstract as {printed} kHz for the {label} interval, measured by saturation spectroscopy in a discharge cell.",
                     "The thesis abstract says it is the only experiment to measure all three intervals directly at the 1 kHz level. The journal version, Phys. Rev. Lett. 95, 203001 (2005), and its erratum were not read (APS served a bot check).",
                     _HE_NOTE))


EXOTIC_QED: tuple[Quantity, ...] = (
    _q("ishida2014.ps.hfs", "positronium ground-state hyperfine interval", "Delta_HFS(Ps)", "203.394 2", "0.001 6", "GHz",
       kind=_SPLIT_KIND, systematic_text="0.001 3",
       source="A. Ishida, T. Namba, S. Asai, T. Kobayashi, H. Saito, M. Yoshida, K. Tanaka, and A. Yamamoto, New precision measurement of hyperfine splitting of positronium, Phys. Lett. B 734, 338-344 (2014), doi:10.1016/j.physletb.2014.05.083, arXiv:1310.6923.",
       edition="Phys. Lett. B 734 (2014)", url="https://doi.org/10.1016/j.physletb.2014.05.083", retrieved_from="https://export.arxiv.org/api/query?id_list=1310.6923",
       keys=_PS_KEYS, phrases=("positronium hyperfine", "positronium hyperfine splitting", "positronium hyperfine interval"),
       notes=("Printed in the abstract as 203.394 2 +- 0.001 6 (stat., 8.0 ppm) +- 0.001 3 (sys., 6.4 ppm) GHz, after a measured non-thermalization correction of 10 +- 2 ppm.",
              "The abstract says the result disfavors the previous experimental average by 2.6 s.d. and favors the QED prediction within 1.2 s.d.; the prediction is not stored.", _SPLIT_NOTE)),
    _q("ritter1984.ps.hfs", "positronium ground-state hyperfine interval", "Delta_nu(Ps)", "203.389 10", "0.000 74", "GHz",
       kind="uncertainty as printed, level not stated", printed="203.389 10(74)",
       source="M. W. Ritter, P. O. Egan, V. W. Hughes, and K. A. Woodle, Precision determination of the hyperfine-structure interval in the ground state of positronium. V, Phys. Rev. A 30, 1331 (1984), doi:10.1103/PhysRevA.30.1331.",
       edition="Phys. Rev. A 30 (1984)", url="https://doi.org/10.1103/PhysRevA.30.1331", retrieved_from=_inspire("10.1103/PhysRevA.30.1331"),
       keys=_PS_KEYS, phrases=("positronium hyperfine", "positronium hyperfine interval"),
       notes=("Printed in the abstract as Delta nu = 203.38910(74) GHz (3.6 ppm), from the Yale gas-cell data.",
              "Read from INSPIRE's copy of the APS abstract; the APS page served a bot check. The 1984 theory value in the abstract is not stored.")),
    _q("kataoka2009.ops.decay_rate", "orthopositronium decay rate (combined with three earlier results)", "lambda(o-Ps)", "7.0401", "0.0007", "us^-1",
       kind="uncertainty as printed, level not stated",
       source="Y. Kataoka, S. Asai, and T. Kobayashi, First test of O(alpha^2) correction of the orthopositronium decay rate, Phys. Lett. B 671, 219-223 (2009), doi:10.1016/j.physletb.2008.12.008, arXiv:0809.1594.",
       edition="Phys. Lett. B 671 (2009)", url="https://doi.org/10.1016/j.physletb.2008.12.008", retrieved_from="https://export.arxiv.org/api/query?id_list=0809.1594",
       keys=_PS_KEYS, phrases=("orthopositronium decay rate", "orthopositronium lifetime", "positronium lifetimes", "ortho-positronium"),
       notes=("Printed in the abstract as 7.0401 +- 0.0007 us^-1 (100 ppm): the paper's 150 ppm result combined with the last three results.",
              "This is a combination made by the source, not here. Vallery et al., PRL 90, 203402 (2003), print 7.0404(10)(8) us^-1 with two unlabeled uncertainty terms; that record is not stored, since the abstract does not name the terms.")),
    _q("alramadhan1994.pps.decay_rate", "parapositronium (singlet) decay rate", "lambda_S(p-Ps)", "7990.9", "1.7", "us^-1",
       kind="uncertainty as printed, level not stated",
       source="A. H. Al-Ramadhan and D. W. Gidley, New precision measurement of the decay rate of singlet positronium, Phys. Rev. Lett. 72, 1632 (1994), doi:10.1103/PhysRevLett.72.1632.",
       edition="Phys. Rev. Lett. 72 (1994)", url="https://doi.org/10.1103/PhysRevLett.72.1632", retrieved_from=_inspire("10.1103/PhysRevLett.72.1632"),
       keys=_PS_KEYS, phrases=("parapositronium decay rate", "parapositronium lifetime", "positronium lifetimes", "para-positronium"),
       notes=("Printed in the abstract as lambda_s = 7990.9 +- 1.7 us^-1 (215 ppm), using magnetic singlet-triplet mixing in a N2-isobutane gas mixture.",
              "Read from INSPIRE's copy of the APS abstract; the APS page served a bot check.")),
    _q("liu1999.mu.hfs", "muonium ground-state hyperfine interval", "Delta_nu(Mu)", "4 463 302 765", "53", "Hz",
       kind="uncertainty as printed, level not stated", printed="4 463 302 765(53)",
       source="W. Liu et al., High precision measurements of the ground state hyperfine structure interval of muonium and of the muon magnetic moment, Phys. Rev. Lett. 82, 711 (1999), doi:10.1103/PhysRevLett.82.711.",
       edition="Phys. Rev. Lett. 82 (1999)", url="https://doi.org/10.1103/PhysRevLett.82.711", retrieved_from=_inspire("10.1103/PhysRevLett.82.711"),
       keys=("muonium", "exotic atom", "bound-state qed"), phrases=("muonium hyperfine", "muonium hyperfine interval", "muonium hyperfine splitting"),
       notes=("Printed in the abstract as Delta nu = 4463302765(53) Hz (12 ppb), from two Zeeman hyperfine transitions in a strong field at LAMPF.",
              "Read from INSPIRE's copy of the APS abstract; the APS page served a bot check.")),
    _q("liu1999.mu_moment_ratio", "muon-to-proton magnetic moment ratio", "mu_mu/mu_p", "3.183 345 13", "0.000 000 39", "",
       kind="uncertainty as printed, level not stated", printed="3.183 345 13(39)",
       source="W. Liu et al., High precision measurements of the ground state hyperfine structure interval of muonium and of the muon magnetic moment, Phys. Rev. Lett. 82, 711 (1999), doi:10.1103/PhysRevLett.82.711.",
       edition="Phys. Rev. Lett. 82 (1999)", url="https://doi.org/10.1103/PhysRevLett.82.711", retrieved_from=_inspire("10.1103/PhysRevLett.82.711"),
       keys=("muonium",), phrases=("muon to proton magnetic moment ratio",),
       notes=("Printed in the abstract as mu_mu/mu_p = 3.18334513(39) (120 ppb). The m_mu/m_e and alpha values the abstract derives from it are not stored.",)),
    _zel("zelevinsky2004.he.f12", "helium 2 3P1 - 2 3P2 interval", "nu_12(He)", "2 291 175.4", "0.6", "2 291 175.4(6)", "2 3P1 - 2 3P2"),
    _zel("zelevinsky2004.he.f01", "helium 2 3P0 - 2 3P1 interval", "nu_01(He)", "29 616 951.5", "0.8", "29 616 951.5(8)", "2 3P0 - 2 3P1"),
    _zel("zelevinsky2004.he.f02", "helium 2 3P0 - 2 3P2 interval", "nu_02(He)", "31 908 126.6", "1.0", "31 908 126.6(1.0)", "2 3P0 - 2 3P2"),
    _q("george2001.he.f01", "helium 2 3P0 - 2 3P1 interval", "nu_01(He)", "29616950.9", "0.9", "kHz",
       kind="uncertainty as printed, level not stated",
       source="M. C. George, L. D. Lombardi, and E. A. Hessels, Precision microwave measurement of the 2 3P1-2 3P0 interval in atomic helium: a determination of the fine-structure constant, Phys. Rev. Lett. 87, 173002 (2001), doi:10.1103/PhysRevLett.87.173002.",
       edition="Phys. Rev. Lett. 87 (2001)", url="https://doi.org/10.1103/PhysRevLett.87.173002", retrieved_from=_inspire("10.1103/PhysRevLett.87.173002"),
       keys=_HE_FS_KEYS, phrases=("helium 2 3P0 - 2 3P1 interval", "helium fine structure"),
       notes=("Printed in the abstract as 29616950.9+-0.9 kHz, microwave spectroscopy in a thermal metastable beam.",
              "The alpha value the abstract derives from it is not stored. Read from INSPIRE's copy of the APS abstract.", _HE_NOTE)),
    _q("kato2018.he.f12", "helium 2 3P1 - 2 3P2 interval", "nu_12(He)", "2 291 176 590", "25", "Hz",
       kind="uncertainty as printed, level not stated", printed="2 291 176 590(25)",
       source="K. Kato, T. D. G. Skinner, and E. A. Hessels, Ultrahigh-precision measurement of the n=2 triplet P fine structure of atomic helium using frequency-offset separated oscillatory fields, Phys. Rev. Lett. 121, 143002 (2018), doi:10.1103/PhysRevLett.121.143002, arXiv:1807.07923.",
       edition="Phys. Rev. Lett. 121 (2018)", url="https://doi.org/10.1103/PhysRevLett.121.143002", retrieved_from="https://export.arxiv.org/api/query?id_list=1807.07923",
       keys=_HE_FS_KEYS, phrases=("helium 2 3P1 - 2 3P2 interval", "helium fine structure", "helium 2 3p fine structure"),
       notes=("Printed in the abstract as 2 291 176 590(25) Hz for the 2 3P2 -> 2 3P1 interval, by frequency-offset separated oscillatory fields (FOSOF).", _HE_NOTE)),
    _q("heydarizadmotlagh2024.he.f01", "helium 2 3P0 - 2 3P1 interval", "nu_01(He)", "29 616 955 018", "60", "Hz",
       kind="uncertainty as printed, level not stated", printed="29 616 955 018(60)",
       source="F. Heydarizadmotlagh, T. D. G. Skinner, K. Kato, M. C. George, and E. A. Hessels, Precision measurement of the n=2 triplet P J=1-to-J=0 fine structure of atomic helium using frequency-offset separated oscillatory fields, Phys. Rev. Lett. 132, 163001 (2024), doi:10.1103/PhysRevLett.132.163001, arXiv:2310.17040.",
       edition="Phys. Rev. Lett. 132 (2024)", url="https://doi.org/10.1103/PhysRevLett.132.163001", retrieved_from="https://export.arxiv.org/api/query?id_list=2310.17040",
       keys=_HE_FS_KEYS, phrases=("helium 2 3P0 - 2 3P1 interval", "helium fine structure", "helium 2 3p fine structure"),
       notes=("Printed in the abstract as 29 616 955 018(60) Hz (2 ppb) for the J=1-to-J=0 interval, by FOSOF.", _HE_NOTE)),
)


_ZERO_EDGE = "Only the upper limit is printed. The lower end 0 is the edge of a magnitude or mass, not a measurement."


def _null_bound(id: str, name: str, symbol: str, upper: str, unit: str, *, source: str, edition: str, url: str, retrieved_from: str,
                keys: tuple[str, ...], phrases: tuple[str, ...], conditions: tuple[str, ...]) -> Bound:
    return Bound(id=id, name=name, symbol=symbol, lower_text="0", upper_text=upper, unit=unit, source=source, edition=edition, url=url,
                 retrieved_from=retrieved_from, retrieved=RETRIEVED, keys=keys + ("null result",), phrases=phrases + ("null results", "experimental bounds"),
                 conditions=conditions + (_ZERO_EDGE,), forbids=())


_JILA2023_SOURCE = "T. S. Roussy et al., An improved bound on the electron's electric dipole moment, Science 381, 46-50 (2023), doi:10.1126/science.adg4084, arXiv:2212.11841."
_ABEL2020_SOURCE = "C. Abel et al., Measurement of the permanent electric dipole moment of the neutron, Phys. Rev. Lett. 124, 081803 (2020), doi:10.1103/PhysRevLett.124.081803, arXiv:2001.11966."
_MICROSCOPE_SOURCE = "P. Touboul et al. (MICROSCOPE Collaboration), MICROSCOPE mission: final results of the test of the equivalence principle, Phys. Rev. Lett. 129, 121102 (2022), doi:10.1103/PhysRevLett.129.121102, arXiv:2209.15487."

NULL_RESULTS: tuple[Quantity, ...] = (
    _q("jila2023.d_e", "electron electric dipole moment, measured value", "d_e", "-1.3 e-30", "2.0 e-30", "e cm",
       kind=_SPLIT_KIND, systematic_text="0.6 e-30", source=_JILA2023_SOURCE, edition="Science 381 (2023)",
       url="https://doi.org/10.1126/science.adg4084", retrieved_from="https://arxiv.org/pdf/2212.11841",
       keys=("edm", "electron edm", "cp violation", "null result"), phrases=("electron edm", "electron electric dipole moment", "null results"),
       notes=("Printed as d_e = (-1.3 +- 2.0_stat +- 0.6_syst) x 10^-30 e cm (eq. 3), from trapped 180Hf19F+ ions; the paper calls it consistent with zero.",
              "The 90% bound derived by the paper is stored as bound.jila2023.electron_edm.", _SPLIT_NOTE)),
    _q("abel2020.d_n", "neutron electric dipole moment, measured value", "d_n", "0.0 e-26", "1.1 e-26", "e cm",
       kind=_SPLIT_KIND, systematic_text="0.2 e-26", source=_ABEL2020_SOURCE, edition="Phys. Rev. Lett. 124 (2020)",
       url="https://doi.org/10.1103/PhysRevLett.124.081803", retrieved_from="https://export.arxiv.org/api/query?id_list=2001.11966",
       keys=("edm", "neutron edm", "cp violation", "null result"), phrases=("neutron edm", "neutron electric dipole moment", "null results"),
       notes=("Printed in the abstract as d_n = (0.0 +- 1.1_stat +- 0.2_sys) x 10^-26 e cm, ultracold neutrons at PSI with a 199Hg co-magnetometer.",
              "The paper's 90% C.L. bound is stored as bound.abel2020.neutron_edm.", _SPLIT_NOTE)),
    _q("microscope2022.eta_ti_pt", "Eotvos parameter for titanium and platinum test masses", "eta(Ti,Pt)", "-1.5 e-15", "2.3 e-15", "",
       kind=_SPLIT_KIND, systematic_text="1.5 e-15", source=_MICROSCOPE_SOURCE, edition="Phys. Rev. Lett. 129 (2022)",
       url="https://doi.org/10.1103/PhysRevLett.129.121102", retrieved_from="https://export.arxiv.org/api/query?id_list=2209.15487",
       keys=("equivalence principle", "microscope", "null result"), phrases=("equivalence principle", "eotvos parameter", "weak equivalence principle", "null results"),
       notes=("Printed in the abstract as eta(Ti, Pt) = [-1.5 +- 2.3 (stat) +- 1.5 (syst)] x 10^-15 'at 1 sigma in statistical errors'.",
              "The abstract says no violation of the weak equivalence principle was found. The level of the systematic term is not restated in the abstract.", _SPLIT_NOTE)),
)

NULL_BOUNDS: tuple[Bound, ...] = (
    _null_bound("bound.jila2023.electron_edm", "electron electric dipole moment magnitude", "|d_e|", "4.1 e-30", "e cm",
                source=_JILA2023_SOURCE, edition="Science 381 (2023)", url="https://doi.org/10.1126/science.adg4084", retrieved_from="https://arxiv.org/pdf/2212.11841",
                keys=("edm", "electron edm", "cp violation"), phrases=("electron edm", "electron electric dipole moment", "electron edm bound"),
                conditions=("Printed as |d_e| < 4.1 x 10^-30 e cm (90% confidence), eq. 4, from the HfF+ measurement d_e = (-1.3 +- 2.0_stat +- 0.6_syst) x 10^-30 e cm.",
                            "The abstract says it improves on the previous best upper bound by a factor of about 2.4. ACME 2018 is not stored.")),
    _null_bound("bound.abel2020.neutron_edm", "neutron electric dipole moment magnitude", "|d_n|", "1.8 e-26", "e cm",
                source=_ABEL2020_SOURCE, edition="Phys. Rev. Lett. 124 (2020)", url="https://doi.org/10.1103/PhysRevLett.124.081803", retrieved_from="https://arxiv.org/pdf/2001.11966",
                keys=("edm", "neutron edm", "cp violation"), phrases=("neutron edm", "neutron electric dipole moment", "neutron edm bound"),
                conditions=("Printed as |d_n| < 1.8 x 10^-26 e cm (90% C.L.), interpreting d_n = (0.0 +- 1.1_stat +- 0.2_sys) x 10^-26 e cm.",)),
    Bound(id="bound.superk2020.proton_e_pi0", name="partial lifetime of the proton for p -> e+ pi0", symbol="tau/B(p -> e+ pi0)",
          lower_text="2.4 e34", upper_text="", unit="years",
          source="A. Takenaka et al. (Super-Kamiokande Collaboration), Search for proton decay via p -> e+ pi0 and p -> mu+ pi0 with an enlarged fiducial volume in Super-Kamiokande I-IV, Phys. Rev. D 102, 112011 (2020), doi:10.1103/PhysRevD.102.112011, arXiv:2010.16098.",
          edition="Phys. Rev. D 102 (2020)", url="https://doi.org/10.1103/PhysRevD.102.112011", retrieved_from="https://export.arxiv.org/api/query?id_list=2010.16098",
          retrieved=RETRIEVED, keys=("proton decay", "proton lifetime", "null result"), phrases=("proton lifetime", "proton decay", "proton lifetime bound", "null results", "experimental bounds"),
          conditions=("Printed as tau/B(p -> e+ pi0) > 2.4 x 10^34 years at 90% confidence level, from 450 kton-years of Super-K I-IV data with no candidates.",
                      "This is a lower limit only. No upper end exists, and a lifetime above this value is allowed.",
                      "The same paper gives tau/B(p -> mu+ pi0) > 1.6 x 10^34 years; that mode is not stored."),
          forbids=()),
    _null_bound("bound.pdg2026.photon_mass", "photon mass", "m_gamma", "1 e-18", "eV",
                source="Particle Data Group, Review of Particle Physics, 2026 edition, gamma MASS summary (PDG id S000M), from D. D. Ryutov, Plasma Phys. Control. Fusion 49, B429 (2007), doi:10.1088/0741-3335/49/12B/S40.",
                edition="PDG 2026, S000M", url="https://pdg.lbl.gov/2026/listings/contents_listings.html", retrieved_from=PDG_2026_API,
                keys=("photon", "photon mass"), phrases=("photon mass", "photon mass bound"),
                conditions=("PDG prints the summary as < 1 E-18 eV, from MHD of the solar wind (RYUTOV 2007). The PDG record gives no confidence level for it.",)),
    _null_bound("bound.katrin2025.nu_mass", "effective electron antineutrino mass", "m_nu", "0.45", "eV",
                source="KATRIN Collaboration, Direct neutrino-mass measurement based on 259 days of KATRIN data, Science 388, 180-185 (2025), doi:10.1126/science.adq9592, arXiv:2406.13516.",
                edition="Science 388 (2025)", url="https://doi.org/10.1126/science.adq9592", retrieved_from="https://export.arxiv.org/api/query?id_list=2406.13516",
                keys=("neutrino mass", "katrin"), phrases=("neutrino mass", "neutrino mass bound", "katrin"),
                conditions=("Printed as m_nu < 0.45 eV at 90% confidence level, from tritium beta-decay spectroscopy over the first five campaigns.",
                            "The best fit is printed as m_nu^2 = -0.14 +0.13 -0.15 eV^2; it is not stored, since the abstract does not state its level.")),
    _null_bound("bound.gwtc3.graviton_mass", "graviton mass", "m_g", "2.42 e-23", "eV/c^2",
                source="LIGO Scientific, Virgo, and KAGRA Collaborations, Tests of General Relativity with GWTC-3, Phys. Rev. D 112, 084080 (2025), doi:10.1103/PhysRevD.112.084080, arXiv:2112.06861v3.",
                edition="Phys. Rev. D 112 (2025), arXiv v3", url="https://doi.org/10.1103/PhysRevD.112.084080", retrieved_from="https://arxiv.org/pdf/2112.06861v3",
                keys=("graviton", "graviton mass", "gravitational waves"), phrases=("graviton mass", "graviton mass bound"),
                conditions=("Printed as m_g <= 2.42 x 10^-23 eV/c^2 at 90% credibility, from the modified-dispersion analysis of 43 GWTC-3 events (Table VII).",
                            "arXiv v1 (2021) printed 1.27 x 10^-23 eV/c^2. The v3 comment says 'fixed graviton mass bound in abstract', and the v3 text and table give 2.42; the record keeps v3.")),
    _null_bound("bound.pdg2026.graviton_mass", "graviton mass (PDG summary)", "m_g", "1.76 e-23", "eV",
                source="Particle Data Group, Review of Particle Physics, 2026 edition, graviton MASS summary (PDG id G033M), from R. Abbott et al., Phys. Rev. D 103, 122002 (2021), doi:10.1103/PhysRevD.103.122002 (GWTC-2).",
                edition="PDG 2026, G033M", url="https://pdg.lbl.gov/2026/listings/contents_listings.html", retrieved_from=PDG_2026_API,
                keys=("graviton", "graviton mass"), phrases=("graviton mass", "graviton mass bound"),
                conditions=("PDG prints the summary as < 1.76 E-23 eV, from the LIGO-Virgo GWTC-2 catalog. The PDG record gives no confidence level for it.",
                            "PDG 2026 still uses GWTC-2 here; the GWTC-3 bound is stored separately and is not compared or chosen.")),
)


_CODATA_THERMO_NOTE = _EXACT_DERIVED[0].replace("h, c, and k", "N_A, k, h, and c")
_ITS90_SOURCE = (
    "H. Preston-Thomas, The International Temperature Scale of 1990 (ITS-90), Metrologia 27, 3-10 (1990), doi:10.1088/0026-1394/27/1/002, "
    "with the textual corrections of Metrologia 27, 107 (1990); Table 1, Defining fixed points of the ITS-90."
)
_ITS90_COPY = "https://www.nist.gov/system/files/documents/pml/div685/grp01/ITS-90_metrologia.pdf"


def _its90(key: str, name: str, substance: str, state: str, kelvin: str, celsius: str) -> Quantity:
    return _q(f"its90.fp.{key}", f"ITS-90 {state} of {name}", f"T_90({substance})", kelvin, "", "K", kind="exact",
              source=_ITS90_SOURCE, edition="ITS-90 (1990), Table 1", url="https://doi.org/10.1088/0026-1394/27/1/002", retrieved_from=_ITS90_COPY,
              keys=("its-90", "temperature scale", "fixed point"), phrases=("its-90 fixed points", "temperature fixed points", f"{name} {state}", "defining fixed points"),
              notes=(f"Table 1 prints T_90/K = {kelvin.replace('.', ',')} and t_90/degC = {celsius.replace('.', ',')}, with the decimal comma; substance {substance}, state {state}.",
                     "The value is assigned by the scale's definition, so it is exact on ITS-90. It is not a statement about thermodynamic temperature, which the scale only approximates.",
                     "Melting and freezing points are at a pressure of 101 325 Pa; the ITS-90 is a scanned copy and the table was read from the page image."))


_WEBBOOK_WATER = (
    "NIST Chemistry WebBook, SRD 69, Thermophysical Properties of Fluid Systems, water, isobaric data at 0.101325 MPa, "
    "computed from the IAPWS-95 equation of state (W. Wagner and A. Pruss, J. Phys. Chem. Ref. Data 31, 387 (2002), doi:10.1063/1.1461829), "
    "the IAPWS 2008 viscosity formulation (M. L. Huber et al., J. Phys. Chem. Ref. Data 38, 101 (2009), doi:10.1063/1.3088050), "
    "and the IAPWS 2011 thermal-conductivity formulation (M. L. Huber et al., J. Phys. Chem. Ref. Data 41, 033102 (2012), doi:10.1063/1.4738955)."
)
_WEBBOOK_WATER_URL = (
    "https://webbook.nist.gov/cgi/fluid.cgi?Action=Load&ID=C7732185&Type=IsoBar&Digits=5&P=0.101325&THigh=25&TLow=20&TInc=5&RefState=DEF"
    "&TUnit=C&PUnit=MPa&DUnit=kg%2Fm3&HUnit=kJ%2Fkg&WUnit=m%2Fs&VisUnit=Pa*s&STUnit=N%2Fm"
)
_WEBBOOK_WATER_NOTE = (
    "This is a reference-formulation value, computed by the WebBook from IAPWS formulations fitted to measurements; the WebBook prints it to its default five digits and prints no uncertainty beside it."
)


def _water(key: str, name: str, symbol: str, celsius: str, value: str, unit: str, extra: str) -> Quantity:
    return _q(f"webbook.h2o.{key}_{celsius}c", f"{name} of liquid water at {celsius} degC and 0.101325 MPa", symbol, value, "", unit,
              kind="no uncertainty printed", source=_WEBBOOK_WATER, edition="NIST WebBook SRD 69 fluid data", url=_WEBBOOK_WATER_URL, retrieved_from=_WEBBOOK_WATER_URL,
              keys=("fluid properties", "iapws"), phrases=(f"{name} of water", f"water {name}", "water properties", "fluid properties"),
              notes=(_WEBBOOK_WATER_NOTE, extra))


_IAPWS_SURF_URL = "https://iapws.org/documents/release/Surf-H2O.download"


def _surf(celsius: str, value: str, unc: str) -> Quantity:
    key = celsius.replace(".", "_")
    return _q(f"iapws2014.h2o.surface_tension_{key}c", f"surface tension of water at {celsius} degC", "sigma(H2O)", value, unc, "mN/m",
              kind="uncertainty as printed, level not stated",
              source="IAPWS R1-76(2014), Revised Release on Surface Tension of Ordinary Water Substance, Moscow (2014), Table 1, column 2 (experimental) and column 3 (uncertainty).",
              edition="IAPWS R1-76(2014)", url=_IAPWS_SURF_URL, retrieved_from=_IAPWS_SURF_URL,
              keys=("surface tension", "iapws"), phrases=("surface tension of water", "water surface tension", "water properties", "fluid properties"),
              notes=(f"Table 1 prints {value} mN/m (column 2, recommended experimental value) with uncertainty {unc} mN/m (column 3) at t = {celsius} degC; the release does not state a coverage level.",
                     "Column 4 of the table gives the release's interpolating-equation value; that calculated column is not stored."))


THERMO_FLUIDS: tuple[Quantity, ...] = (
    _codata("codata2022.r_gas", "molar gas constant", "R", "8.314 462 618...", "(exact)", "J mol^-1 K^-1", "r",
            keys=("gas constant",), phrases=("molar gas constant", "gas constant", "ideal gas"), notes=(_CODATA_THERMO_NOTE,)),
    _codata("codata2022.v_m_100kpa", "molar volume of ideal gas (273.15 K, 100 kPa)", "V_m", "22.710 954 64... e-3", "(exact)", "m^3 mol^-1", "mvol",
            keys=("ideal gas",), phrases=("molar volume of ideal gas", "ideal gas"), notes=(_CODATA_THERMO_NOTE,)),
    _codata("codata2022.v_m_101kpa", "molar volume of ideal gas (273.15 K, 101.325 kPa)", "V_m", "22.413 969 54... e-3", "(exact)", "m^3 mol^-1", "mvolstd",
            keys=("ideal gas",), phrases=("molar volume of ideal gas", "ideal gas"), notes=(_CODATA_THERMO_NOTE,)),
    _codata("codata2022.n0_100kpa", "Loschmidt constant (273.15 K, 100 kPa)", "n_0", "2.651 645 804... e25", "(exact)", "m^-3", "n0",
            keys=("ideal gas",), phrases=("loschmidt constant", "ideal gas"), notes=(_CODATA_THERMO_NOTE,)),
    _codata("codata2022.n0_101kpa", "Loschmidt constant (273.15 K, 101.325 kPa)", "n_0", "2.686 780 111... e25", "(exact)", "m^-3", "n0std",
            keys=("ideal gas",), phrases=("loschmidt constant", "ideal gas"), notes=(_CODATA_THERMO_NOTE,)),
    _codata("codata2022.c1", "first radiation constant", "c_1", "3.741 771 852... e-16", "(exact)", "W m^2", "c11strc",
            keys=("radiation constant",), phrases=("first radiation constant", "radiation constant"), notes=_EXACT_DERIVED),
    _codata("codata2022.c2", "second radiation constant", "c_2", "1.438 776 877... e-2", "(exact)", "m K", "c22ndrc",
            keys=("radiation constant",), phrases=("second radiation constant", "radiation constant"), notes=_EXACT_DERIVED),
    _codata("codata2022.std_atm", "standard atmosphere", "atm", "101 325", "(exact)", "Pa", "stdatm",
            keys=("pressure",), phrases=("standard atmosphere", "standard pressure"),
            notes=("CODATA lists this adopted value as exact. It is a conventional unit, defined by the 10th CGPM (1954), not a measured pressure.",)),
    _its90("h2", "equilibrium hydrogen", "e-H2", "triple point", "13.8033", "-259.3467"),
    _its90("ne", "neon", "Ne", "triple point", "24.5561", "-248.5939"),
    _its90("o2", "oxygen", "O2", "triple point", "54.3584", "-218.7916"),
    _its90("ar", "argon", "Ar", "triple point", "83.8058", "-189.3442"),
    _its90("hg", "mercury", "Hg", "triple point", "234.3156", "-38.8344"),
    _its90("h2o", "water", "H2O", "triple point", "273.16", "0.01"),
    _its90("ga", "gallium", "Ga", "melting point", "302.9146", "29.7646"),
    _its90("in", "indium", "In", "freezing point", "429.7485", "156.5985"),
    _its90("sn", "tin", "Sn", "freezing point", "505.078", "231.928"),
    _its90("zn", "zinc", "Zn", "freezing point", "692.677", "419.527"),
    _its90("al", "aluminium", "Al", "freezing point", "933.473", "660.323"),
    _its90("ag", "silver", "Ag", "freezing point", "1234.93", "961.78"),
    _its90("au", "gold", "Au", "freezing point", "1337.33", "1064.18"),
    _its90("cu", "copper", "Cu", "freezing point", "1357.77", "1084.62"),
    _q("its90.he4_lambda_point", "lambda point of helium-4 as used by ITS-90", "T_lambda(4He)", "2.1768", "", "K", kind="no uncertainty printed",
       source=_ITS90_SOURCE.replace("Table 1, Defining fixed points of the ITS-90.", "Sect. 3.1."), edition="ITS-90 (1990), Sect. 3.1",
       url="https://doi.org/10.1088/0026-1394/27/1/002", retrieved_from=_ITS90_COPY,
       keys=("its-90", "helium", "superfluid"), phrases=("lambda point", "helium lambda point", "superfluid transition"),
       notes=("Sect. 3.1 prints the 4He vapour-pressure ranges as 1,25 K to 2,1768 K and 2,1768 K to 5,0 K, naming 2,1768 K 'the lambda point'.",
              "It bounds two equations of the scale; it is not one of the defining fixed points of Table 1.")),
    _water("density", "density", "rho", "25", "997.05", "kg/m^3", "The WebBook gives the equation of state's density uncertainty as 0.0001% at 1 atm in the liquid phase."),
    _water("cp", "isobaric heat capacity", "c_p", "25", "4.1813", "J/(g K)", "The WebBook gives the isobaric heat capacity uncertainty as 0.1% in the liquid."),
    _water("sound_speed", "speed of sound", "w", "25", "1496.7", "m/s", "The WebBook gives the speed-of-sound uncertainty as 0.1% or less in the liquid."),
    _water("viscosity", "viscosity", "eta", "25", "0.00089002", "Pa s", "For the viscosity uncertainty the WebBook points to IAPWS R12-08, which states its uncertainties as expanded with coverage factor two."),
    _water("viscosity", "viscosity", "eta", "20", "0.0010016", "Pa s", "IAPWS R12-08 says the formulation reproduces the ISO recommended viscosity at 20 degC and standard atmospheric pressure within the digits of that reference."),
    _water("thermal_conductivity", "thermal conductivity", "lambda", "25", "0.60652", "W/(m K)", "For the thermal-conductivity uncertainty the WebBook points to the IAPWS 2011 release."),
    _surf("0.01", "75.64", "0.38"),
    _surf("20", "72.74", "0.36"),
    _surf("25", "71.98", "0.36"),
    _surf("100", "58.92", "0.29"),
    _q("wong1986.air.sound_speed", "speed of sound in standard dry air at 0 degC and 101.325 kPa", "c_0", "331.29", "200", "m/s",
       kind="maximum relative uncertainty, ppm as printed",
       source="G. S. K. Wong, Speed of sound in standard air, J. Acoust. Soc. Am. 79, 1359-1366 (1986), doi:10.1121/1.393664.",
       edition="J. Acoust. Soc. Am. 79 (1986)", url="https://doi.org/10.1121/1.393664", retrieved_from="https://api.crossref.org/works/10.1121/1.393664",
       keys=("air", "speed of sound", "acoustics"), phrases=("speed of sound in air", "sound speed in air", "speed of sound"),
       notes=("The abstract prints c0 = 331.29 m s^-1 for standard dry air at 0 degC and 101.325 kPa, with a maximum uncertainty estimated to be approximately 200 ppm.",
              "The abstract calls it a calculation from the equation of state and published thermodynamic data on the constituents of air, not a direct acoustic measurement.",
              "Greenspan's 1987 comment disputes it and keeps 331.44 m/s; that value is greenspan1987.air.sound_speed. Wong's 1995 comment on Cramer 1993 (J. Acoust. Soc. Am. 97, 3177, doi:10.1121/1.411818) says 331.29 m/s is within the re-assessed uncertainties.")),
    _q("greenspan1987.air.sound_speed", "speed of sound in standard dry air at STP (the older value)", "c_0", "331.44", "", "m/s", kind="no uncertainty printed",
       source="M. Greenspan, Comments on 'Speed of sound in standard air' [J. Acoust. Soc. Am. 79, 1359-1366 (1986)], J. Acoust. Soc. Am. 82, 370-372 (1987), doi:10.1121/1.395521.",
       edition="J. Acoust. Soc. Am. 82 (1987)", url="https://doi.org/10.1121/1.395521", retrieved_from="https://api.crossref.org/works/10.1121/1.395521",
       keys=("air", "speed of sound", "acoustics"), phrases=("speed of sound in air", "sound speed in air", "speed of sound"),
       notes=("The abstract says Wong's allowance for gas imperfection is incorrect and that the old value, c0 = 331.44 m/s, is correct. It prints no uncertainty.",
              "Kept beside wong1986.air.sound_speed; the board does not decide between them.")),
)


def _asd_line_query(spectrum: str, low: str, high: str) -> str:
    return (
        f"https://physics.nist.gov/cgi-bin/ASD/lines1.pl?spectra={spectrum.replace(' ', '+')}&output_type=0&low_w={low}&upp_w={high}&unit=1&de=0&format=2"
        "&line_out=0&remove_js=on&en_unit=0&output=0&bibrefs=1&page_size=15&show_obs_wl=1&show_calc_wl=1&unc_out=1&order_out=0&show_av=2"
        "&tsb_value=0&A_out=0&intens_out=on&allowed_out=1&forbid_out=1&conf_out=on&term_out=on&enrg_out=on&J_out=on&submit=Retrieve+Data"
    )


def _line(key: str, name: str, spectrum: str, symbol: str, value: str, unc: str, low: str, high: str, row: str, *, phrases: tuple[str, ...], extra: tuple[str, ...] = ()) -> Quantity:
    query = _asd_line_query(spectrum, low, high)
    return _q(f"asd512.line.{key}", name, symbol, value, unc, "nm",
              kind="uncertainty as printed, level not stated" if unc else "no uncertainty printed",
              source=ASD_SOURCE.replace("Ionization Energies Data.", f"Lines Data, {spectrum}."), edition=ASD_EDITION, url=query, retrieved_from=query,
              keys=("spectral line", "reference line"), phrases=phrases + ("reference spectral lines", "fraunhofer lines"),
              notes=(f"ASD row: {row}.", "This is the observed air wavelength." + (" ASD prints no uncertainty for it." if not unc else ""), _HALPHA_NOTE) + extra)


_SCHOTT_SOURCE = "SCHOTT AG, Optical Glass Data Sheet, SCHOTT N-BK7, 'As of 02/01/2014, Subject to change', glass code 517642.251."
_SCHOTT_URL = (
    "https://shop.schott.com/medias/schott-datasheet-n-bk7-eng.pdf?context=bWFzdGVyfHJvb3R8NjkxODAwfGFwcGxpY2F0aW9uL3BkZnxoZTUvaDM4Lzg4MTAzMTYxMDM3MTAucGRmfGJjNmI4ZjFmY2Q1NjMxMTE0MjkzMTUwOGRmMTUzOTg2NWJjZTgzMjA0OTc2NTNiMThjN2RhMjI4NGZmMWM4MWU"
)
_SCHOTT_NOTE = "Catalogue (nominal) value for the glass type; a given melt differs within SCHOTT's tolerance classes, and the data sheet prints no uncertainty."


def _bk7(key: str, label: str, wavelength: str, value: str) -> Quantity:
    return _q(f"schott.nbk7.n_{key}", f"refractive index of SCHOTT N-BK7 at {wavelength} nm ({label})", f"n_{label}(N-BK7)", value, "", "",
              kind="no uncertainty printed", source=_SCHOTT_SOURCE, edition="SCHOTT data sheet N-BK7 (2014)", url=_SCHOTT_URL, retrieved_from=_SCHOTT_URL,
              keys=("refractive index", "optical glass"), phrases=("refractive index of n-bk7", "bk7 refractive index", "refractive indices", "optical glass"),
              notes=(f"The Refractive Indices table prints {label} at {wavelength} nm as {value}.", _SCHOTT_NOTE))


_IAPWS_RINDEX_URL = "https://iapws.org/documents/release/Rindex.download"


def _water_n(key: str, micron: str, value: str, table2: str) -> Quantity:
    return _q(f"iapws1997.h2o.n_{key}", f"refractive index of liquid water at {micron} um, 0 degC, 0.1 MPa (formulation value)", "n(H2O)", value, "", "",
              kind="no uncertainty printed",
              source="IAPWS R9-97, Release on the Refractive Index of Ordinary Water Substance as a Function of Wavelength, Temperature and Pressure, Erlangen (1997), Table 3.",
              edition="IAPWS R9-97", url=_IAPWS_RINDEX_URL, retrieved_from=_IAPWS_RINDEX_URL,
              keys=("refractive index",), phrases=("refractive index of water", "water refractive index", "refractive indices"),
              notes=(f"Table 3 prints {value} at {micron} um, 0 degC, 0.1 MPa. Table 3 values are calculated from the formulation, Eq. (1), and are given for program verification.",
                     f"Table 2 gives the formulation's estimated absolute uncertainty for this range as {table2}; the release says the estimate is the largest departure of the most reliable data from the formulation."))


_BIPM_SF = "https://www.bipm.org/en/publications/mises-en-pratique/standard-frequencies"
_BIPM_I2 = "https://www.bipm.org/documents/20126/41549560/M-e-P_I2_633.pdf/c4c25f25-ae65-e05d-402a-9bfc84c715c3"
_BIPM_SR = "https://www.bipm.org/documents/20126/288515313/87Sr_429THz_2025/bbd827f7-3e1e-5fbe-6bd8-0eadd9b5b674"
_BIPM_YB = "https://www.bipm.org/documents/20126/288516347/171Yb_518THz_2025/73007ecc-49f5-4d1d-d8ee-6793a4748598"
_I2_SOURCE = "BIPM, Mise en pratique of the metre, Recommended values of standard frequencies: Iodine (lambda ~ 633 nm), 127I2 a16 or f component, R(127) 11-5 transition, MEP 2003, Sect. 2 Source data."

OPTICS: tuple[Quantity, ...] = (
    _line("na_d2", "sodium D2 line, 3s 2S1/2 - 3p 2P3/2", "Na I", "lambda_air(Na D2)", "588.995095", "0.000003", "588", "590",
          "Na I, 2p6.3s 2S 1/2 - 2p6.3p 2P* 3/2, Ritz 588.995094(3) nm, intensity 80000, A_ki 6.16e+07 s^-1", phrases=("sodium d lines", "sodium d2", "na d lines")),
    _line("na_d1", "sodium D1 line, 3s 2S1/2 - 3p 2P1/2", "Na I", "lambda_air(Na D1)", "589.592424", "0.000003", "588", "590",
          "Na I, 2p6.3s 2S 1/2 - 2p6.3p 2P* 1/2, Ritz 589.592424(3) nm, intensity 40000, A_ki 6.14e+07 s^-1", phrases=("sodium d lines", "sodium d1", "na d lines")),
    _line("hg_e", "mercury green line (Fraunhofer e), 6s6p 3P2 - 6s7s 3S1", "Hg I", "lambda_air(Hg e)", "546.0750", "0.0001", "546", "546.2",
          "Hg I, 5d10.6s.6p 3P* 2 - 5d10.6s.7s 3S 1, Ritz 546.07498(9) nm, intensity 6000", phrases=("mercury green line", "mercury e line")),
    _line("hg_g", "mercury blue line (Fraunhofer g), 6s6p 3P1 - 6s7s 3S1", "Hg I", "lambda_air(Hg g)", "435.8335", "0.0001", "435.7", "435.9",
          "Hg I, 5d10.6s.6p 3P* 1 - 5d10.6s.7s 3S 1, Ritz 435.83363(8) nm, intensity 12000", phrases=("mercury blue line", "mercury g line")),
    _line("he_d", "helium yellow line (Fraunhofer d), 1s2p 3P - 1s3d 3D blend", "He I", "lambda_air(He d)", "587.5621", "", "587.5", "587.6",
          "He I, observed 587.5621 nm, shared by four 1s.2p 3P* - 1s.3d 3D fine-structure components with Ritz wavelengths 587.561397 to 587.564036 nm", phrases=("helium d line", "helium yellow line"),
          extra=("The d line is the wavelength at which glass catalogues quote n_d; SCHOTT prints it as 587.6 nm.",)),
    _line("cd_c_prime", "cadmium red line (C'), 5s5p 1P1 - 5s5d 1D2", "Cd I", "lambda_air(Cd C')", "643.84695", "", "643.8", "643.9",
          "Cd I, 4d10.5s.5p 1P* 1 - 4d10.5s.5d 1D 2, Ritz 643.84695 nm, intensity 2000; ASD prints no wavelength uncertainty in this table", phrases=("cadmium red line",)),
    _line("cd_f_prime", "cadmium blue line (F'), 5s5p 3P1 - 5s6s 3S1", "Cd I", "lambda_air(Cd F')", "479.99123", "", "479.9", "480.0",
          "Cd I, 4d10.5s.5p 3P* 1 - 4d10.5s.6s 3S 1, Ritz 479.99121 nm, intensity 300", phrases=("cadmium blue line",)),
    _line("h_beta", "hydrogen Balmer H-beta (Fraunhofer F), n = 2 - 4 blend", "H I", "lambda_air(H-beta)", "486.135", "0.005", "486.1", "486.2",
          "H I, lower level 2, upper level 4, Ritz 486.1333(3) nm, intensity 180000, A_ki 8.4193e+06 s^-1", phrases=("h-beta", "h beta", "balmer beta", "hydrogen f line")),
    _bk7("d", "d", "587.6", "1.51680"),
    _bk7("big_d", "D", "589.3", "1.51673"),
    _bk7("e", "e", "546.1", "1.51872"),
    _bk7("f", "F", "486.1", "1.52238"),
    _bk7("c", "C", "656.3", "1.51432"),
    _bk7("g", "g", "435.8", "1.52668"),
    _bk7("632_8", "632.8", "632.8", "1.51509"),
    _bk7("1060", "1060.0", "1060.0", "1.50669"),
    _q("schott.nbk7.abbe_d", "Abbe number of SCHOTT N-BK7 at d", "nu_d(N-BK7)", "64.17", "", "", kind="no uncertainty printed",
       source=_SCHOTT_SOURCE, edition="SCHOTT data sheet N-BK7 (2014)", url=_SCHOTT_URL, retrieved_from=_SCHOTT_URL,
       keys=("abbe number", "optical glass"), phrases=("abbe number", "abbe number of n-bk7", "dispersion of bk7", "optical glass"),
       notes=("Printed in the header as nu_d = 64.17.", _SCHOTT_NOTE)),
    _q("schott.nbk7.principal_dispersion", "principal dispersion n_F - n_C of SCHOTT N-BK7", "n_F - n_C (N-BK7)", "0.008054", "", "", kind="no uncertainty printed",
       source=_SCHOTT_SOURCE, edition="SCHOTT data sheet N-BK7 (2014)", url=_SCHOTT_URL, retrieved_from=_SCHOTT_URL,
       keys=("dispersion", "optical glass"), phrases=("principal dispersion", "dispersion of bk7", "optical glass"),
       notes=("Printed in the header as n_F - n_C = 0.008054, to one more decimal than the tabulated indices.", _SCHOTT_NOTE)),
    _water_n("226_5nm", "0.226 50", "1.394 527", "5 x 10^-4 (0.21 to 0.40 um, 0 to 100 degC, ambient, liquid)"),
    _water_n("589nm", "0.589 00", "1.334 344", "< 6 x 10^-5 (0.40 to 0.70 um, -12 to 5 degC, ambient, liquid)"),
    _water_n("1014nm", "1.013 98", "1.326 135", "1 x 10^-3 (0.70 to 1.1 um, ambient, liquid)"),
    _q("bipm2003.i2_633.frequency", "iodine-stabilised He-Ne laser frequency, 633 nm, R(127) 11-5 f component", "f(I2 633)", "473 612 353 604", "10", "kHz",
       kind="standard uncertainty", printed="473 612 353 604(10)", source=_I2_SOURCE, edition="CIPM MEP 2003, I2 633 nm", url=_BIPM_I2, retrieved_from=_BIPM_I2,
       keys=("standard frequency", "he-ne laser", "metre"), phrases=("iodine stabilized he-ne", "633 nm standard", "standard frequencies", "he-ne laser frequency"),
       notes=("Sect. 2 prints the adopted value f = 473 612 353 604 (10) kHz, u_c/y = 2.1 x 10^-11; Sect. 1 lists it as the CIPM recommended value under stated operating conditions.",
              "The MEP notes that the +- figures in the operating conditions are tolerances, not uncertainties.")),
    _q("bipm2003.i2_633.wavelength", "iodine-stabilised He-Ne laser vacuum wavelength, 633 nm, R(127) 11-5 f component", "lambda(I2 633)", "632 991 212.579", "0.013", "fm",
       kind="standard uncertainty", printed="632 991 212.579(13)", source=_I2_SOURCE, edition="CIPM MEP 2003, I2 633 nm", url=_BIPM_I2, retrieved_from=_BIPM_I2,
       keys=("standard frequency", "he-ne laser", "metre"), phrases=("iodine stabilized he-ne", "633 nm standard", "he-ne laser wavelength"),
       notes=("Sect. 2 prints lambda = 632 991 212.579 (13) fm, u_c/y = 2.1 x 10^-11, 'for which' the adopted frequency; Sect. 1 rounds it to 632 991 212.58 fm.",)),
    _q("bipm2025.sr87.frequency", "87Sr 5s2 1S0 - 5s5p 3P0 clock transition frequency (CIPM recommended)", "f(87Sr)", "429 228 004 229 872.992", "1.7 e-16", "Hz",
       kind="relative standard uncertainty", source="BIPM, Recommended values of standard frequencies, Strontium 87 atom (f ~ 429 THz), approved by the CCTF in September 2025, active on March 27, 2026.",
       edition="CIPM list of standard frequencies, 2025", url=_BIPM_SR, retrieved_from=_BIPM_SR,
       keys=("standard frequency", "optical clock", "strontium"), phrases=("strontium clock frequency", "optical clock frequencies", "standard frequencies"),
       notes=("Printed as f(87Sr) = 429 228 004 229 872.992 Hz, equivalent to lambda = 698 445 709.612 754 425 fm, with a relative standard uncertainty of 1.7 x 10^-16. It is a secondary representation of the second.",
              "The 2021 list (CCTF PSFS 2) gave 429 228 004 229 872.99 Hz with 1.9 x 10^-16; it is not stored separately.")),
    _q("bipm2025.yb171.frequency", "171Yb 6s2 1S0 - 6s6p 3P0 clock transition frequency (CIPM recommended)", "f(171Yb)", "518 295 836 590 863.632", "1.7 e-16", "Hz",
       kind="relative standard uncertainty", source="BIPM, Recommended values of standard frequencies, Ytterbium 171 atom (f ~ 518 THz), approved by the CCTF in September 2025, active on March 27, 2026.",
       edition="CIPM list of standard frequencies, 2025", url=_BIPM_YB, retrieved_from=_BIPM_YB,
       keys=("standard frequency", "optical clock", "ytterbium"), phrases=("ytterbium clock frequency", "optical clock frequencies", "standard frequencies"),
       notes=("Printed as f(171Yb) = 518 295 836 590 863.632 Hz, equivalent to lambda = 578 419 575.916 162 499 fm, with a relative standard uncertainty of 1.7 x 10^-16. It is a secondary representation of the second.",)),
)


_GRS80_SOURCE = "H. Moritz, Geodetic Reference System 1980, J. Geodesy 74, 128-133 (2000), doi:10.1007/s001900050278 (The Geodesist's Handbook), Sect. 4, Numerical values."
_GRS80_COPY = "https://ciencias.ulisboa.pt/sites/default/files/fcul/dep/dqb/doc/GRS80_Moritz.pdf"
_GRS80_DERIVED = "Sect. 4 lists this as a derived constant, 'accurate to the number of decimal places given'; it is computed from the four defining constants, and is stored as printed."


def _grs80(key: str, name: str, symbol: str, value: str, unit: str, *, defining: bool, phrases: tuple[str, ...]) -> Quantity:
    return _q(f"grs80.{key}", f"GRS80 {name}", symbol, value, "", unit, kind="exact" if defining else "no uncertainty printed",
              source=_GRS80_SOURCE, edition="GRS80 (IUGG 1979), Moritz 2000", url="https://doi.org/10.1007/s001900050278", retrieved_from=_GRS80_COPY,
              keys=("grs80", "earth figure", "geodesy"), phrases=phrases + ("geodetic reference system", "grs80 constants"),
              notes=(("Listed under 'Defining Constants (exact)'. It is a conventional value adopted by the IUGG, not a measurement." if defining else _GRS80_DERIVED),))


_IGRF_URL = "https://www.ngdc.noaa.gov/IAGA/vmod/coeffs/igrf14coeffs.txt"
_IGRF_SOURCE = "IAGA Division V-MOD, International Geomagnetic Reference Field, 14th generation (IGRF-14), Schmidt semi-normalised spherical harmonic coefficients, coefficient file igrf14coeffs.txt."


def _igrf(key: str, coefficient: str, epoch: str, label: str, value: str, unit: str = "nT", extra: str = "") -> Quantity:
    return _q(f"igrf14.{key}", f"IGRF-14 Gauss coefficient {coefficient}, {epoch} ({label})", coefficient, value, "", unit, kind="no uncertainty printed",
              source=_IGRF_SOURCE, edition=f"IGRF-14, {label} {epoch}", url=_IGRF_URL, retrieved_from=_IGRF_URL,
              keys=("geomagnetic field", "igrf"), phrases=("earth's magnetic field", "earth magnetic dipole", "geomagnetic dipole", "igrf coefficients"),
              notes=(f"The file prints {value} for {coefficient} in the {epoch} column, headed {label}. The file prints no uncertainties.",
                     "The degree-1 coefficients describe the dipole part of the main field. The board does not compute a dipole moment or tilt from them.") + ((extra,) if extra else ()))


_LEAMAN_SOURCE = "E. J. Leaman, D. Haddad, F. Seifert, L. S. Chao, A. Cao, J. R. Pratt, S. Schlamminger, and D. B. Newell, A determination of the local acceleration of gravity for the NIST-4 watt balance, IEEE Trans. Instrum. Meas. 64, 1663-1669 (2015), doi:10.1109/TIM.2014.2383111, arXiv:1412.4143, Sect. VII."
_LIU_SOURCE = "W. Liu, N. Li, Y. Ma, R. Hu, S. Wu, W. Zhao et al., A determination of the local gravitational acceleration for the Tsinghua tabletop Kibble balance, arXiv:2405.08541 (2024), Sect. III."

MECHANICS_EM: tuple[Quantity, ...] = (
    _codata("codata2022.g_n", "standard acceleration of gravity", "g_n", "9.806 65", "(exact)", "m s^-2", "gn",
            keys=("gravity",), phrases=("standard gravity", "standard acceleration of gravity", "acceleration of gravity"),
            notes=("CODATA lists this adopted value as exact. It is an adopted conventional value, not a measured local g.",)),
    _grs80("a", "semimajor axis", "a", "6378 137", "m", defining=True, phrases=("earth equatorial radius", "semimajor axis of the earth")),
    _grs80("gm", "geocentric gravitational constant", "GM", "3 986 005 e8", "m^3 s^-2", defining=True, phrases=("geocentric gravitational constant",)),
    _grs80("j2", "dynamic form factor", "J_2", "108 263 e-8", "", defining=True, phrases=("earth j2", "dynamic form factor")),
    _grs80("omega", "angular velocity", "omega", "7 292 115 e-11", "rad s^-1", defining=True, phrases=("earth rotation rate", "angular velocity of the earth")),
    _grs80("inv_f", "reciprocal flattening", "1/f", "298.257 222 101", "", defining=False, phrases=("earth flattening", "reciprocal flattening")),
    _grs80("gamma_e", "normal gravity at the equator", "gamma_e", "9.780 326 7715", "m s^-2", defining=False, phrases=("normal gravity", "gravity at the equator")),
    _grs80("gamma_p", "normal gravity at the pole", "gamma_p", "9.832 186 3685", "m s^-2", defining=False, phrases=("normal gravity", "gravity at the pole")),
    _q("leaman2015.nist4.g", "local acceleration of gravity at the NIST-4 watt balance test mass (Gaithersburg)", "g(NIST-4)", "980103140.2", "4.3", "uGal",
       kind="uncertainty as printed, level not stated", printed="980103140.2(4.3)", source=_LEAMAN_SOURCE, edition="IEEE Trans. Instrum. Meas. 64(6), June 2015 (year, volume, and pages confirmed from Crossref); arXiv:1412.4143",
       url="https://doi.org/10.1109/TIM.2014.2383111", retrieved_from="https://arxiv.org/pdf/1412.4143",
       keys=("local gravity", "absolute gravimetry"), phrases=("measured local g", "local acceleration of gravity", "measured gravity at sites"),
       notes=("Sect. VII prints the best estimate as 980103140.2(4.3) uGal (4.4 x 10^-9 relative uncertainty), tied from absolute gravimeter measurements to the test-mass position.",
              "1 uGal = 10^-8 m s^-2; the value is stored in the paper's unit.")),
    _q("liu2024.nim_changping.g_r", "absolute gravity at the NIM Changping key-comparison site (as quoted)", "g_r(NIM)", "980 122 922.8", "1.0", "uGal",
       kind="standard uncertainty", source=_LIU_SOURCE, edition="arXiv:2405.08541 (2024)", url="https://arxiv.org/abs/2405.08541", retrieved_from="https://arxiv.org/pdf/2405.08541",
       keys=("local gravity", "absolute gravimetry"), phrases=("measured local g", "measured gravity at sites"),
       notes=("The paper says the reference value at the Changping CCM.G-K2.2017 key-comparison point 'is recorded as 980 122 922.8 uGal with a standard uncertainty of 1.0 uGal'. The key-comparison report itself was not read.",)),
    _q("liu2024.thu.g0", "absolute gravity at the Tsinghua Kibble balance reference point (tide-correction transfer)", "g_0(THU)", "980 139 581.2", "2.3", "uGal",
       kind="standard uncertainty", source=_LIU_SOURCE, edition="arXiv:2405.08541 (2024)", url="https://arxiv.org/abs/2405.08541", retrieved_from="https://arxiv.org/pdf/2405.08541",
       keys=("local gravity", "absolute gravimetry"), phrases=("measured local g", "measured gravity at sites"),
       notes=("Printed as g0 = (980 139 581.2 +- 2.3) uGal (k = 1), from the NIM value plus a CG6 relative-gravimeter transfer with tide correction.",
              "The paper's blind polynomial-fit transfer gives (980 139 580.4 +- 1.6) uGal (k = 1); that alternative is not stored separately.")),
    _codata("codata2022.f_faraday", "Faraday constant", "F", "96 485.332 12...", "(exact)", "C mol^-1", "f",
            keys=("faraday",), phrases=("faraday constant",), notes=(_EXACT_DERIVED[0].replace("h, c, and k", "N_A and e"),)),
    _codata("codata2022.z_0", "characteristic impedance of vacuum", "Z_0", "376.730 313 412", "0.000 000 059", "ohm", "z0",
            keys=("vacuum impedance",), phrases=("impedance of free space", "characteristic impedance of vacuum")),
    _codata("codata2022.phi_0", "magnetic flux quantum", "Phi_0", "2.067 833 848... e-15", "(exact)", "Wb", "flxquhs2e",
            keys=("flux quantum",), phrases=("magnetic flux quantum", "flux quantum"), notes=(_EXACT_DERIVED[0].replace("h, c, and k", "h and e"),)),
    _codata("codata2022.mu_b", "Bohr magneton", "mu_B", "9.274 010 0657 e-24", "0.000 000 0029 e-24", "J T^-1", "mub",
            keys=("magneton",), phrases=("bohr magneton",)),
    _igrf("g10_2025", "g_1^0", "2025.0", "IGRF", "-29350.0"),
    _igrf("g11_2025", "g_1^1", "2025.0", "IGRF", "-1410.3"),
    _igrf("h11_2025", "h_1^1", "2025.0", "IGRF", "4545.5"),
    _igrf("g10_2020", "g_1^0", "2020.0", "DGRF", "-29403.41", extra="DGRF marks a definitive model for that epoch."),
    _igrf("g10_1900", "g_1^0", "1900.0", "IGRF", "-31543", extra="The 1900 model is an IGRF (non-definitive) column in the file."),
    _igrf("g10_sv_2025", "dg_1^0/dt", "2025-30", "secular variation", "12.6", "nT/yr", extra="The secular-variation column is a forecast for 2025-2030."),
)


_IERS_SOURCE = "G. Petit and B. Luzum (eds.), IERS Conventions (2010), IERS Technical Note No. 36, Verlag des Bundesamts fuer Kartographie und Geodaesie, Frankfurt am Main (2010), with updates to 2017/11/06"
_IERS_SITE = "https://iers-conventions.obspm.fr/"


def _iers(key: str, name: str, symbol: str, value: str, uncertainty: str, unit: str, *, chapter: int, where: str,
          phrases: tuple[str, ...], kind: str = "uncertainty as printed, level not stated", notes: tuple[str, ...] = ()) -> Quantity:
    url = f"https://iers-conventions.obspm.fr/content/chapter{chapter}/icc{chapter}.pdf"
    if kind == "exact" or kind == "no uncertainty printed":
        uncertainty = ""
    return _q(f"iers2010.{key}", f"IERS Conventions (2010) {name}", symbol, value, uncertainty, unit, kind=kind,
              source=f"{_IERS_SOURCE}, Chapter {chapter}, {where}.", edition="IERS Conventions (2010), TN36", url=url, retrieved_from=url,
              keys=("iers conventions",), phrases=phrases + ("iers constants",), notes=notes)


_C04_URL = "https://hpiers.obspm.fr/iers/eop/eopc04/eopc04.1962-now"
_C04_SOURCE = "IERS Earth Orientation Centre (Paris Observatory), EOP 20 C04 combined series, consistent with ITRF 2020, sampled at 0h UTC; C. Bizouard et al., J. Geod. 93, 621-633 (2019), doi:10.1007/s00190-018-1186-3 (series description)"


def _lod(date: str, value: str, error: str, why: str) -> Quantity:
    return _q(f"iersc04.lod_{date.replace('-', '_')}", f"excess length of day on {date} (IERS EOP 20 C04)", f"LOD({date})", value, error, "s",
              kind="uncertainty as printed, level not stated", source=_C04_SOURCE, edition="EOP 20 C04, file as served 2026-11-25 (last row 2026-10-26)",
              url=_C04_URL, retrieved_from=_C04_URL, keys=("length of day", "lod"), phrases=("length of day", "excess length of day", "earth rotation rate"),
              notes=(f"The C04 row for {date} prints LOD(s) {value} and LOD Er {error}. LOD is the excess of the day over 86 400 s TAI (C04 page footnote).", why))


_WGS84_PAGE = "https://earth-info.nga.mil/index.php?action=wgs84&dir=wgs84"
_WGS84_COPY = "https://web.archive.org/web/20260105104748/https://earth-info.nga.mil/index.php?dir=wgs84&action=wgs84"
_WGS84_SOURCE = "National Geospatial-Intelligence Agency, World Geodetic System 1984 Reference System page, 'Defining Parameters' table (standard: NGA.STND.0036_1.0.0_WGS84, 8 July 2014)"


def _wgs84(key: str, name: str, symbol: str, value: str, unit: str, phrases: tuple[str, ...], extra: tuple[str, ...] = ()) -> Quantity:
    return _q(f"wgs84.{key}", f"WGS 84 {name}", symbol, value, "", unit, kind="exact", source=_WGS84_SOURCE, edition="NGA.STND.0036_1.0.0_WGS84 (2014)",
              url=_WGS84_PAGE, retrieved_from=_WGS84_COPY, keys=("wgs84", "earth figure"), phrases=phrases + ("wgs84 constants", "world geodetic system"),
              notes=("One of WGS 84's four defining parameters. It is an adopted value, not a measurement. The live NGA page timed out from the box, so the 2026-01-05 Wayback copy was read.",) + extra)


EARTH_ROTATION: tuple[Quantity, ...] = (
    _iers("gm_earth", "geocentric gravitational constant", "GM_E", "3.986004418 e14", "8 e5", "m^3 s^-2", chapter=1, where="Table 1.1", phrases=("geocentric gravitational constant",),
          notes=("TCG-compatible value. Reference [7] notes that recent studies indicate an uncertainty of 4 x 10^5 m^3 s^-2.",)),
    _iers("a_e", "equatorial radius of the Earth", "a_E", "6378136.6", "0.1", "m", chapter=1, where="Table 1.1", phrases=("earth equatorial radius",),
          notes=("A 'zero tide' value (Sect. 1.1).",)),
    _iers("j2", "dynamical form factor of the Earth", "J_2", "1.0826359 e-3", "1 e-10", "", chapter=1, where="Table 1.1", phrases=("earth j2", "dynamic form factor"), notes=("A 'zero tide' value.",)),
    _iers("inv_f", "flattening factor of the Earth", "1/f", "298.25642", "0.00001", "", chapter=1, where="Table 1.1", phrases=("earth flattening", "reciprocal flattening"), notes=("A 'zero tide' value.",)),
    _iers("g_e", "mean equatorial gravity", "g_E", "9.7803278", "1 e-6", "m s^-2", chapter=1, where="Table 1.1", phrases=("gravity at the equator", "mean equatorial gravity"), notes=("A 'zero tide' value.",)),
    _iers("w0", "potential of the geoid", "W_0", "62636853.4", "0.02", "m^2 s^-2", chapter=1, where="Table 1.1 (2017/11/06 update, IAG 2015 Resolution 1)", phrases=("potential of the geoid",)),
    _iers("h_dyn", "dynamical flattening", "H", "3273795 e-9", "1 e-9", "", chapter=1, where="Table 1.1", phrases=("dynamical flattening", "precession constant")),
    _iers("eps0", "obliquity of the ecliptic at J2000.0", "epsilon_0", "84381.406", "0.001", "arcsec", chapter=1, where="Table 1.1", phrases=("obliquity of the ecliptic",),
          notes=("Table 1.1 prints 84381.406 and 0.001 with the arcsecond sign (rendered by pdftotext as trailing 00).",)),
    _iers("era_rate", "rate of advance of the Earth Rotation Angle", "dtheta/dt", "1.00273781191135448", "", "rev per UT1 day", chapter=1, where="Table 1.1", kind="exact",
          phrases=("earth rotation angle", "earth rotation rate"), notes=("Listed as 'Defining', citing reference [3] (IAU XXIV General Assembly resolution).",)),
    _iers("era_0", "Earth Rotation Angle at J2000.0", "theta_0", "0.7790572732640", "", "rev", chapter=1, where="Table 1.1", kind="exact",
          phrases=("earth rotation angle",), notes=("Listed as 'Defining'.",)),
    _iers("psi_a_rate", "IAU 2006 precession of the equator in longitude, linear coefficient", "psi_A/t", "5038.481507", "", "arcsec per Julian century", chapter=5, where="Eq. (5.39)",
          kind="no uncertainty printed", phrases=("precession constant", "precession of the equinoxes", "precession rate"),
          notes=("Eq. (5.39) prints psi_A = 5038.481507'' t - 1.0790069'' t^2 - ..., t in Julian centuries TT from J2000.0. Only the linear coefficient is stored.",
                 "This is the precession of the equator in longitude, not the general precession in longitude p_A, which the chapter does not print.")),
    _iers("delta_psi_a_2000", "IAU 2000 correction to the IAU 1976 precession rate in longitude", "delta psi_A", "-0.29965", "0.00040", "arcsec per century", chapter=5, where="Sect. 5.6.2",
          phrases=("precession constant", "precession rate"), notes=("Sect. 5.6.2: the precession part of IAU 2000A consists only of corrections to the IAU 1976 precession rates; this is the longitude one, printed as (-0.29965 +- 0.00040)''/century.",)),
    _iers("k20", "nominal Love number k20, elastic Earth", "k_20", "0.29525", "", "", chapter=6, where="Table 6.3", kind="no uncertainty printed",
          phrases=("love numbers", "tidal love number", "tidal love numbers"), notes=("A nominal model value chosen for the Step 1 tidal computation, not a measurement.",)),
    _iers("k21", "nominal Love number k21, elastic Earth", "k_21", "0.29470", "", "", chapter=6, where="Table 6.3", kind="no uncertainty printed",
          phrases=("love numbers", "tidal love numbers"), notes=("A nominal model value.",)),
    _iers("k22", "nominal Love number k22, elastic Earth", "k_22", "0.29801", "", "", chapter=6, where="Table 6.3", kind="no uncertainty printed",
          phrases=("love numbers", "tidal love numbers"), notes=("A nominal model value.",)),
    _iers("k20_anelastic", "nominal Love number Re k20, anelastic Earth", "Re k_20", "0.30190", "", "", chapter=6, where="Table 6.3", kind="no uncertainty printed",
          phrases=("love numbers", "tidal love numbers"), notes=("A nominal model value.",)),
    _iers("h2", "nominal degree-2 displacement Love number h2", "h_2", "0.6078", "", "", chapter=7, where="Table 7.3a heading", kind="no uncertainty printed",
          phrases=("love numbers", "tidal love numbers", "shida number"), notes=("Printed as the nominal real part, h2 = 0.6078; imaginary part -0.0025.",)),
    _iers("l2", "nominal degree-2 Shida number l2", "l_2", "0.0847", "", "", chapter=7, where="Table 7.3a heading", kind="no uncertainty printed",
          phrases=("love numbers", "tidal love numbers", "shida number"), notes=("Printed as the nominal real part, l2 = 0.0847; imaginary part -0.0007.",)),
    _q("iersc04.omega_nominal", "nominal Earth angular velocity used by EOP C04", "Omega_nominal", "72921151.467064", "", "picorad s^-1", kind="no uncertainty printed",
       source="IERS Earth Orientation Centre, EOP C04 combined series page, footnote 3", edition="page as served 2026-11-25",
       url="https://hpiers.obspm.fr/eop-pc/index.php?index=C04&lang=en", retrieved_from="https://hpiers.obspm.fr/eop-pc/index.php?index=C04&lang=en",
       keys=("earth rotation",), phrases=("earth rotation rate", "angular velocity of the earth"),
       notes=("Footnote 3: 'Earth angular velocity refered to the nominal value of 72921151.467064 picorad/s'.",)),
    _lod("2024-07-05", "-0.0016508", "0.0000246", "This is the most negative LOD in the series as served (the shortest day since 1962)."),
    _lod("1972-04-12", "0.0043550", "0.0007000", "This is the largest LOD in the series as served."),
    _lod("2026-10-26", "0.0014827", "0.0000095", "This is the last row in the file as served on 2026-11-25."),
    _wgs84("a", "semi-major axis", "a", "6378137.0", "m", ("earth equatorial radius", "semimajor axis of the earth")),
    _wgs84("inv_f", "flattening factor", "1/f", "298.257223563", "", ("earth flattening", "reciprocal flattening")),
    _wgs84("omega", "nominal mean angular velocity of the Earth", "omega", "7292115 e-11", "rad s^-1", ("earth rotation rate", "angular velocity of the earth")),
    _wgs84("gm", "geocentric gravitational constant (atmosphere included)", "GM", "3.986004418 e14", "m^3 s^-2", ("geocentric gravitational constant",),
           ("The page adds that the value of GM for GPS users is 3.9860050 x 10^14 m^3 s^-2.",)),
)


_DELVA_SOURCE = "P. Delva, N. Puchades, E. Schoenemann, F. Dilssner, C. Courde et al., Gravitational redshift test using eccentric Galileo satellites, Phys. Rev. Lett. 121, 231101 (2018), doi:10.1103/PhysRevLett.121.231101, arXiv:1812.03711."
_HERRMANN_SOURCE = "S. Herrmann, F. Finke, M. Luelf, O. Kichakova, D. Puetzfeld et al., Test of the gravitational redshift with Galileo satellites in an eccentric orbit, Phys. Rev. Lett. 121, 231102 (2018), doi:10.1103/PhysRevLett.121.231102, arXiv:1812.09161."
_LEP_SOURCE = "ALEPH, DELPHI, L3, OPAL, and SLD Collaborations, LEP Electroweak Working Group, SLD Electroweak and Heavy Flavour Groups, Precision electroweak measurements on the Z resonance, Phys. Rept. 427, 257-454 (2006), doi:10.1016/j.physrep.2005.12.006, arXiv:hep-ex/0509008"
_LEP_URL = "https://doi.org/10.1016/j.physrep.2005.12.006"
_LEP_COPY = "https://arxiv.org/pdf/hep-ex/0509008"
_Z_PHRASES = ("z lineshape", "z line shape", "z resonance", "z pole")


def _lep(key: str, name: str, symbol: str, value: str, error: str, unit: str, where: str, phrases: tuple[str, ...], extra: tuple[str, ...] = ()) -> Quantity:
    return _q(f"lep2005.{key}", f"{name} (LEP combination)", symbol, value, error, unit, kind="uncertainty as printed, level not stated",
              source=f"{_LEP_SOURCE}, {where}.", edition="Phys. Rept. 427 (2006); arXiv v3", url=_LEP_URL, retrieved_from=_LEP_COPY,
              keys=("z boson", "lep"), phrases=phrases + _Z_PHRASES + ("lep z parameters",),
              notes=(f"Printed as {value} +- {error}" + (f" {unit}" if unit else "") + f" in {where}.",) + extra)


_TABLE_213 = "Table 2.13, combination with lepton universality"
_TABLE_213_NOTE = "Table 2.13's caption: 'The errors include all common errors except the parametric uncertainty on mZ due to the choice of mH.' Correlations with m_Z, Gamma_Z, sigma_had0, R_l0, A_FB0l are printed beside the values (for example -0.297 between Gamma_Z and sigma_had0) and are not stored."

REDSHIFT_ZPOLE: tuple[Quantity, ...] = (
    _q("delva2018.redshift_alpha", "fractional deviation of the gravitational redshift from GR (Galileo 5 and 6)", "alpha", "0.19 e-5", "2.48 e-5", "",
       kind="standard uncertainty", source=_DELVA_SOURCE, edition="Phys. Rev. Lett. 121 (2018)", url="https://doi.org/10.1103/PhysRevLett.121.231101",
       retrieved_from="https://export.arxiv.org/api/query?id_list=1812.03711", keys=("gravitational redshift", "local position invariance"),
       phrases=("gravitational redshift", "redshift test", "galileo redshift", "clock redshift test"),
       notes=("The abstract prints (+0.19 +- 2.48) x 10^-5 'at 1 sigma', from 1008 days of two eccentric-orbit Galileo satellites (GSAT-0201 and GSAT-0202).",
              "It says this improves on Gravity Probe A by a factor of about 5.6.")),
    _q("herrmann2018.redshift_alpha", "redshift test parameter, combined redshift and Doppler (Galileo clock 5)", "alpha", "2.2 e-5", "1.6 e-5", "",
       kind="uncertainty as printed, level not stated", source=_HERRMANN_SOURCE, edition="Phys. Rev. Lett. 121 (2018); arXiv v1",
       url="https://doi.org/10.1103/PhysRevLett.121.231102", retrieved_from="https://arxiv.org/pdf/1812.09161",
       keys=("gravitational redshift", "local position invariance"), phrases=("gravitational redshift", "redshift test", "galileo redshift", "clock redshift test"),
       notes=("The paper takes its final result from clock 5 only: alpha = (2.2 +- 1.6) x 10^-5. The combined posterior of all three clocks is alpha = (-0.9 +- 1.4) x 10^-5, not stored.",
              "This alpha tests the combined gravitational redshift and relativistic Doppler effect, as in the GP-A analysis.")),
    _q("herrmann2018.redshift_alpha_rs", "redshift test parameter, gravitational redshift only (Galileo)", "alpha_rs", "4.5 e-5", "3.1 e-5", "",
       kind="uncertainty as printed, level not stated", source=_HERRMANN_SOURCE, edition="Phys. Rev. Lett. 121 (2018); arXiv v1",
       url="https://doi.org/10.1103/PhysRevLett.121.231102", retrieved_from="https://arxiv.org/pdf/1812.09161",
       keys=("gravitational redshift", "local position invariance"), phrases=("gravitational redshift", "redshift test", "galileo redshift"),
       notes=("Printed as alpha_rs = (4.5 +- 3.1) x 10^-5 when the violation model is restricted to the redshift part, compared there with GP-A's alpha_rs < 1.4 x 10^-4.",)),
    _q("pound1965.redshift_ratio", "measured gravitational shift of the 14.4 keV 57Fe line over 75 ft, relative to 2gh/c^2", "Delta nu_obs / Delta nu_EP", "0.9990", "0.0076", "",
       kind=_SPLIT_KIND, systematic_text="0.010", source="R. V. Pound and J. L. Snider, Effect of gravity on gamma radiation, Phys. Rev. 140, B788-B803 (1965), doi:10.1103/PhysRev.140.B788.",
       edition="Phys. Rev. 140 (1965)", url="https://doi.org/10.1103/PhysRev.140.B788",
       retrieved_from="https://inspirehep.net/api/literature?q=doi:10.1103/PhysRev.140.B788",
       keys=("gravitational redshift", "pound-rebka"), phrases=("gravitational redshift", "pound rebka", "pound-rebka", "redshift test"),
       notes=("The abstract prints '(0.9990+-0.0076) times the value 4.905x10^-15 of 2gh/c^2 predicted from the principle of equivalence', where 0.0076 is the statistical standard deviation; 'an estimated limit of systematic error is 0.010', stored as the systematic term.",
              "The original Pound-Rebka 1960 result (Phys. Rev. Lett. 4, 337) is stored separately as pound1960.redshift_ratio and pound1960.net_shift.", _SPLIT_NOTE)),
    _lep("m_z", "Z boson mass", "m_Z", "91.1875", "0.0021", "GeV", _TABLE_213, ("z boson mass", "mass of the z"), (_TABLE_213_NOTE,)),
    _lep("gamma_z", "Z boson total width", "Gamma_Z", "2.4952", "0.0023", "GeV", _TABLE_213, ("z width", "z boson width"), (_TABLE_213_NOTE,)),
    _lep("sigma_had0", "hadronic pole cross section", "sigma_had^0", "41.540", "0.037", "nb", _TABLE_213, ("hadronic pole cross section",), (_TABLE_213_NOTE,)),
    _lep("r_l0", "ratio of hadronic to leptonic Z width", "R_l^0", "20.767", "0.025", "", _TABLE_213, ("r_l", "hadronic to leptonic width ratio"), (_TABLE_213_NOTE,)),
    _lep("a_fb0_l", "leptonic pole forward-backward asymmetry", "A_FB^0,l", "0.0171", "0.0010", "", _TABLE_213, ("forward-backward asymmetry",), (_TABLE_213_NOTE,)),
    _lep("n_nu", "number of light neutrino species", "N_nu", "2.9840", "0.0082", "", "abstract and eq. (7.8)", ("number of light neutrinos", "neutrino species"),
         ("The abstract says this is 'in agreement with the three observed generations of fundamental fermions'.",)),
    _lep("sin2_theta_eff", "effective leptonic weak mixing angle", "sin^2 theta_eff^lept", "0.23153", "0.00016", "", "abstract", ("effective weak mixing angle", "sin2 theta eff")),
    _pdg("pdg2026.gamma_z", "Z boson total width", "Gamma_Z", "2.4955", "0.0023", "GeV", node="S044W", keys=("z boson",), phrases=("z width", "z boson width") + _Z_PHRASES, notes=(_API_NOTE,)),
    _pdg("pdg2026.sigma_had0", "Z hadronic pole cross section", "sigma_had^0", "41.4802", "0.0325", "nb", node="S044SH", keys=("z boson",), phrases=("hadronic pole cross section",) + _Z_PHRASES,
         notes=(_API_NOTE, "PDG's value differs from the 2006 LEP combination (41.540 +- 0.037 nb); the reason is not given in the API record, and both are stored.")),
    _pdg("pdg2026.a_fb0_l", "Z leptonic pole forward-backward asymmetry", "A_FB^0,l", "1.71", "0.10", "%", node="S044Z0L", keys=("z boson",), phrases=("forward-backward asymmetry",) + _Z_PHRASES,
         notes=(_API_NOTE, "The pdgLive listing heads the column 'ASYMMETRY (%)'; the API record carries no unit, so the percent comes from the listing page.")),
)

GPA_BOUND: tuple[Bound, ...] = (
    _null_bound("bound.vessot1980.redshift", "Gravity Probe A agreement of the relativistic frequency shift with prediction", "|alpha|", "70 e-6", "",
                source="R. F. C. Vessot, M. W. Levine, E. M. Mattison, E. L. Blomberg, T. E. Hoffman et al., Test of relativistic gravitation with a space-borne hydrogen maser, Phys. Rev. Lett. 45, 2081-2084 (1980), doi:10.1103/PhysRevLett.45.2081.",
                edition="Phys. Rev. Lett. 45 (1980)", url="https://doi.org/10.1103/PhysRevLett.45.2081", retrieved_from="https://inspirehep.net/api/literature?q=doi:10.1103/PhysRevLett.45.2081",
                keys=("gravitational redshift", "gravity probe a"), phrases=("gravitational redshift", "gravity probe a", "redshift test"),
                conditions=("The abstract says 'the agreement of the observed relativistic frequency shift with prediction is at the 70x10^-6 level'. It states no confidence level, and this record reads that agreement level as the bound.",
                            "Herrmann et al. (2018) quote GP-A's redshift-only bound as alpha_rs < 1.4 x 10^-4; that quotation is kept in herrmann2018.redshift_alpha_rs's notes, not as a separate record.")),
)


_LIVECHART_URL = "https://www-nds.iaea.org/relnsd/v1/data?fields=ground_states&nuclides=all"
_LIVECHART_NOTE = "Read from the IAEA LiveChart of Nuclides API, ground_states set (rows extracted 2023-10-18); the API guide credits charge radii to Angeli and Marinova (2013) and half-lives to ENSDF. The IAEA radii page itself is behind a browser check, so the API copy was read."
_AM2013_SOURCE = "I. Angeli and K. P. Marinova, Table of experimental nuclear ground state charge radii: an update, At. Data Nucl. Data Tables 99, 69-95 (2013), doi:10.1016/j.adt.2011.12.006, as served by the IAEA LiveChart of Nuclides API"
_DDEP_SOURCE = "LNE-LNHB/CEA, Table de Radionucleides (Decay Data Evaluation Project, DDEP), recommended data"


def _am2013(key: str, nuclide: str, value: str, error: str) -> Quantity:
    return _q(f"am2013.r_{key}", f"root-mean-square nuclear charge radius of {nuclide}", f"R({nuclide})", value, error, "fm",
              kind="uncertainty as printed, level not stated", source=_AM2013_SOURCE, edition="ADNDT 99 (2013), via LiveChart API",
              url="https://doi.org/10.1016/j.adt.2011.12.006", retrieved_from=_LIVECHART_URL, keys=("charge radius", "nuclear charge radius"),
              phrases=("nuclear charge radii", "charge radius", "angeli marinova"),
              notes=(f"The API row prints radius {value} and unc_r {error} (fm).", _LIVECHART_NOTE))


def _ensdf(key: str, nuclide: str, value: str, error: str, unit: str, ensdf_style: str, cutoff: str) -> Quantity:
    return _q(f"ensdf.t_half_{key}", f"half-life of {nuclide} (ENSDF)", f"T1/2({nuclide})", value, error, unit, kind="uncertainty as printed, level not stated",
              source="Evaluated Nuclear Structure Data File (ENSDF), as served by the IAEA LiveChart of Nuclides API", edition=f"ENSDF, publication cut-off {cutoff}",
              url="https://www.nndc.bnl.gov/ensdf/", retrieved_from=_LIVECHART_URL, keys=("half-life", "half life"), phrases=("nuclear half-lives", "half-lives", "half-life"),
              notes=(f"The API row prints half_life {ensdf_style}; unc_hl is in ENSDF style (last digits), stored here as {error} {unit}.", _LIVECHART_NOTE))


def _ddep(key: str, nuclide: str, value: str, error: str, unit: str, printed: str, pdf: str, evaluator: str, extra: tuple[str, ...] = ()) -> Quantity:
    url = f"https://www.lnhb.fr/nuclides/{pdf}_tables.pdf"
    return _q(f"ddep.t_half_{key}", f"half-life of {nuclide} (DDEP)", f"T1/2({nuclide})", value, error, unit, kind="uncertainty as printed, level not stated",
              source=f"{_DDEP_SOURCE}, {pdf} tables, evaluation by {evaluator}", edition=f"DDEP {pdf} tables as served 2026-11-25", url=url, retrieved_from=url,
              keys=("half-life", "half life"), phrases=("nuclear half-lives", "half-lives", "half-life"),
              notes=(f"Section 2 prints {printed} (decimal comma, uncertainty in the last digits).",) + extra)


NUCLEAR_DECAY_RADII: tuple[Quantity, ...] = (
    _ddep("h3", "tritium", "12.312", "0.025", "a", "T1/2 (3H) : 12,312 (25) a", "H-3", "V. P. Chechev (KRI), 1998-2006"),
    _ddep("c14", "carbon-14", "5700", "30", "a", "T1/2 (14C) : 5700 (30) a", "C-14", "V. P. Chechev and M. M. Be (KRI, LNHB), 1998-2012"),
    _ddep("k40", "potassium-40", "1.2522 e9", "0.0027 e9", "a", "T1/2 (40K) : 1,2522 (27) 10^9 a", "K-40", "X. Mougeot (CEA-LNHB), 1998-2025",
          ("The table asks to cite X. Mougeot et al., Metrologia 63 (2026) 019001.",)),
    _ddep("co60", "cobalt-60", "5.2711", "0.0008", "a", "T1/2 (60Co) : 5,2711 (8) a", "Co-60", "R. G. Helmer (INEEL), 1998-2010"),
    _ddep("u238", "uranium-238", "4.468 e9", "0.005 e9", "a", "T1/2 (238U) : 4,468 (5) 10^9 a", "U-238", "V. Chiste and M. M. Be (LNHB), 2005-2006"),
    _ddep("th232", "thorium-232", "14.02 e9", "0.06 e9", "a", "T1/2 (232Th) : 14,02 (6) 10^9 a", "Th-232", "A. Arinc (NPL), 2008-2012"),
    _ensdf("n", "the free neutron", "613.9", "0.6", "s", "613.9 (6) s", "31-Oct-2005"),
    _ensdf("h3", "tritium", "12.32", "0.02", "a", "12.32 (2) Y", "30-Jun-2015"),
    _ensdf("c14", "carbon-14", "5700", "30", "a", "5700 (30) Y", "1-JUL-1990"),
    _ensdf("k40", "potassium-40", "1.248 e9", "0.003 e9", "a", "1.248E+9 (3) Y", "30-Sep-2015"),
    _ensdf("co60", "cobalt-60", "1925.28", "0.14", "d", "1925.28 (14) d", "31-Dec-2012"),
    _ensdf("u238", "uranium-238", "4.468 e9", "0.006 e9", "a", "4.468E9 (6) Y", "1-Jun-2014"),
    _ensdf("th232", "thorium-232", "1.40 e10", "0.01 e10", "a", "1.40E10 (1) Y", "1-Nov-2004"),
    _am2013("p", "the proton (1H)", "0.8783", "0.0086"),
    _am2013("d", "the deuteron (2H)", "2.1421", "0.0088"),
    _am2013("t", "the triton (3H)", "1.7591", "0.0363"),
    _am2013("he4", "4He", "1.6755", "0.0028"),
    _am2013("c12", "12C", "2.4702", "0.0022"),
    _am2013("c14", "14C", "2.5025", "0.0087"),
    _am2013("o16", "16O", "2.6991", "0.0052"),
    _am2013("k40", "40K", "3.4381", "0.0028"),
    _am2013("ca40", "40Ca", "3.4776", "0.0019"),
    _am2013("ca48", "48Ca", "3.4771", "0.0020"),
    _am2013("pb208", "208Pb", "5.5012", "0.0013"),
    _am2013("th232", "232Th", "5.7848", "0.0124"),
    _am2013("u238", "238U", "5.8571", "0.0033"),
)


_HB100_SOURCE = "National Bureau of Standards, Copper Wire Tables, NBS Handbook 100 (1966), Sect. 1, International Annealed Copper Standard"
_HB100_URL = "https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf"
_IACS_NOTE = "The International Annealed Copper Standard is an adopted reference value (IEC, 1913), not a measurement of any sample; the handbook prints it with no uncertainty."


def _iacs(key: str, name: str, symbol: str, value: str, unit: str, printed: str) -> Quantity:
    return _q(f"nbs1966.iacs_{key}", f"International Annealed Copper Standard {name}", symbol, value, "", unit, kind="no uncertainty printed",
              source=_HB100_SOURCE, edition="NBS Handbook 100 (1966)", url=_HB100_URL, retrieved_from=_HB100_URL,
              keys=("copper", "iacs"), phrases=("resistivity of copper", "copper resistivity", "annealed copper standard"),
              notes=(f"Printed as {printed}.", _IACS_NOTE))


_DIELEC_SOURCE = "IAPWS R8-97, Release on the Static Dielectric Constant of Ordinary Water Substance for Temperatures from 238 K to 873 K and Pressures up to 1000 MPa (Erlangen, 1997); formulation of D. P. Fernandez et al., J. Phys. Chem. Ref. Data 26, 1125-1169 (1997)"
_DIELEC_URL = "https://iapws.org/documents/release/Dielec.download"
_WILLIAMS_SOURCE = "E. R. Williams, J. E. Faller, and H. A. Hill, New experimental test of Coulomb's law: a laboratory upper limit on the photon rest mass, Phys. Rev. Lett. 26, 721-724 (1971), doi:10.1103/PhysRevLett.26.721."
_WILLIAMS_FROM = "https://inspirehep.net/api/literature?q=doi:10.1103/PhysRevLett.26.721"

EM_EXTRAS: tuple[Quantity, ...] = (
    _codata("codata2022.g_0", "conductance quantum", "G_0", "7.748 091 729... e-5", "(exact)", "S", "conqu2e2sh",
            keys=("conductance quantum",), phrases=("conductance quantum", "quantum of conductance"), notes=(_EXACT_DERIVED[0].replace("h, c, and k", "h and e"),)),
    _codata("codata2022.g_0_inverse", "inverse of conductance quantum", "G_0^-1", "12 906.403 72...", "(exact)", "ohm", "invconqu",
            keys=("conductance quantum",), phrases=("inverse conductance quantum",), notes=(_EXACT_DERIVED[0].replace("h, c, and k", "h and e"),)),
    _iacs("volume_resistivity", "volume resistivity at 20 C", "rho_IACS", "1.7241", "microhm cm", "1.7241 microhm-cm at 20 C (Sect. 1); p. 10 also prints 'Volume resistivity of annealed copper at 20 C = 100/58 = 1.7241 microhm-cm'"),
    _iacs("mass_resistivity", "mass resistivity at 20 C", "rho_m,IACS", "0.15328", "ohm g m^-2", "0.153 28 ohm-gram/meter2 at 20 C, 'the fundamental resistivity used in calculating the tables'"),
    _iacs("density", "density at 20 C", "d_IACS", "8.89", "g cm^-3", "8.89 grams/cm3 at 20 C, as taken by the IEC"),
    _iacs("temperature_coefficient", "temperature coefficient of resistance at 20 C", "alpha_20", "0.00393", "per degree C", "0.00393 at 20 C, as specified by the IEC for standard copper"),
    _q("iapwsr897.h2o.eps_300k", "static dielectric constant of water at 300 K and 0.101 325 MPa (program-verification value)", "epsilon(300 K)", "77.74735", "", "",
       kind="no uncertainty printed", source=_DIELEC_SOURCE + ", Table 4", edition="IAPWS R8-97 (1997)", url=_DIELEC_URL, retrieved_from=_DIELEC_URL,
       keys=("dielectric constant", "permittivity"), phrases=("static permittivity of water", "dielectric constant of water", "relative permittivity of water"),
       notes=("Table 4 prints 77.747 35 at 0.101 325 MPa and 300 K (density 55.317 35 mol/dm3). The release says 'the large number of digits is for the purpose of code verification; it does not reflect the uncertainty of the values'.",
              "It is calculated from the formulation, not measured. The scanned release was read from rendered page images.")),
    _q("iapwsr897.h2o.eps_323k", "static dielectric constant of water at 323 K and 0.101 325 MPa", "epsilon(323 K)", "69.96", "0.04", "",
       kind="uncertainty as printed, level not stated", source=_DIELEC_SOURCE + ", Table 3", edition="IAPWS R8-97 (1997)", url=_DIELEC_URL, retrieved_from=_DIELEC_URL,
       keys=("dielectric constant", "permittivity"), phrases=("static permittivity of water", "dielectric constant of water", "relative permittivity of water"),
       notes=("Table 3 prints epsilon_pred = 69.96 and estimated absolute uncertainty U = 0.04 at 0.101 325 MPa, 323 K, 988.10 kg/m3.",
              "Sect. 5 says the estimates 'could not be based on rigorous statistics'. The scanned release was read from rendered page images.")),
    _q("iapwsr897.h2o.eps_373k", "static dielectric constant of water at 373 K and 0.101 325 MPa", "epsilon(373 K)", "55.57", "0.2", "",
       kind="uncertainty as printed, level not stated", source=_DIELEC_SOURCE + ", Table 3", edition="IAPWS R8-97 (1997)", url=_DIELEC_URL, retrieved_from=_DIELEC_URL,
       keys=("dielectric constant", "permittivity"), phrases=("static permittivity of water", "dielectric constant of water", "relative permittivity of water"),
       notes=("Table 3 prints epsilon_pred = 55.57 and U = 0.2 at 0.101 325 MPa, 373 K, 958.46 kg/m3.", "Sect. 5 says the estimates 'could not be based on rigorous statistics'.")),
    _q("williams1971.coulomb_q", "deviation q from Coulomb's inverse-square law, 1/r^(2+q)", "q", "2.7 e-16", "3.1 e-16", "",
       kind="uncertainty as printed, level not stated", source=_WILLIAMS_SOURCE, edition="Phys. Rev. Lett. 26 (1971)", url="https://doi.org/10.1103/PhysRevLett.26.721",
       retrieved_from=_WILLIAMS_FROM, keys=("coulomb's law", "inverse square law"), phrases=("coulomb's law tests", "coulomb inverse square", "test of coulomb's law", "null results"),
       notes=("The abstract prints q = (2.7 +- 3.1) x 10^-16 for a deviation of the form 1/r^(2+q), and calls it a null result.",)),
    _q("williams1971.photon_mass_sq", "photon rest mass squared from the Coulomb's-law test (Proca)", "mu^2", "1.04 e-19", "1.2 e-19", "cm^-2",
       kind="uncertainty as printed, level not stated", source=_WILLIAMS_SOURCE, edition="Phys. Rev. Lett. 26 (1971)", url="https://doi.org/10.1103/PhysRevLett.26.721",
       retrieved_from=_WILLIAMS_FROM, keys=("coulomb's law", "photon mass"), phrases=("coulomb's law tests", "test of coulomb's law"),
       notes=("The abstract prints mu^2 = (1.04 +- 1.2) x 10^-19 cm^-2, from the Proca equations.",)),
)

COULOMB_BOUNDS: tuple[Bound, ...] = (
    _null_bound("bound.plimpton1936.coulomb_exponent", "relative deviation of the exponent 2 in Coulomb's law", "|delta n|/2", "1 e-9", "",
                source="S. J. Plimpton and W. E. Lawton, A very accurate test of Coulomb's law of force between charges, Phys. Rev. 50, 1066 (1936), doi:10.1103/PhysRev.50.1066.",
                edition="Phys. Rev. 50 (1936)", url="https://doi.org/10.1103/PhysRev.50.1066", retrieved_from="https://inspirehep.net/api/literature?q=doi:10.1103/PhysRev.50.1066",
                keys=("coulomb's law", "inverse square law"), phrases=("coulomb's law tests", "test of coulomb's law", "coulomb inverse square"),
                conditions=("The abstract says the exponent 2 'has been found experimentally to be correct to within 1 part in 10^9'. It states no confidence level; this record reads that as a bound on the relative deviation of the exponent.",)),
)


_KNOWLES_SOURCE = "K. M. Knowles, The plane strain Young's modulus in cubic materials, J. Elast. 128, 147-173 (2017), doi:10.1007/s10659-017-9621-x, Table 1 (data for Si and Cu from Table 6.1 of A. Kelly and K. M. Knowles, Crystallography and Crystal Defects, 2nd edn., Wiley, 2012)"
_KNOWLES_COPY = "https://api.repository.cam.ac.uk/server/api/core/bitstreams/8827434c-079f-47a8-a5c5-1e3597416a22/content"
_TANIGAKI_SOURCE = "T. Tanigaki et al., Observation of higher stiffness in nanopolycrystal diamond than monocrystal diamond, Nat. Commun. 4, 2343 (2013), doi:10.1038/ncomms3343, quoting A. Migliori, H. Ledbetter, R. G. Leisure et al., Diamond's elastic stiffnesses from 322 K to 10 K, J. Appl. Phys. 104, 053512 (2008), doi:10.1063/1.2975190"
_KAMM_SOURCE = "G. N. Kamm and G. A. Alers, Low-temperature elastic moduli of aluminum, J. Appl. Phys. 35, 327-330 (1964), doi:10.1063/1.1713309, abstract"
_VALLIN_SOURCE = "J. Vallin, M. Mongy, K. Salama, and O. Beckman, Elastic constants of aluminum, J. Appl. Phys. 35, 1825-1826 (1964), doi:10.1063/1.1713749, abstract"
_ELASTIC = ("elastic constants", "elastic constant")


def _cij(id: str, material: str, ij: str, value: str, unit: str, *, source: str, edition: str, url: str, retrieved_from: str, where: str, extra: tuple[str, ...] = ()) -> Quantity:
    return _q(id, f"elastic stiffness c{ij} of {material}", f"c{ij}({material})", value, "", unit, kind="no uncertainty printed", source=source, edition=edition,
              url=url, retrieved_from=retrieved_from, keys=_ELASTIC, phrases=("elastic constants", "elastic stiffness", f"elastic constants of {material.split(' ')[0].lower()}"),
              notes=(f"{where} prints c{ij} = {value}" + (f" {unit}" if unit else "") + " with no uncertainty.",) + extra)


def _knowles(mat: str, material: str, c11: str, c12: str, c44: str) -> tuple[Quantity, ...]:
    return tuple(_cij(f"knowles2017.{mat}.c{ij}", material, ij, v, "GPa", source=_KNOWLES_SOURCE, edition="J. Elast. 128 (2017), open-access copy",
                      url="https://doi.org/10.1007/s10659-017-9621-x", retrieved_from=_KNOWLES_COPY, where="Table 1",
                      extra=("Table 1's caption gives no temperature for Si and Cu; the values are a textbook compilation, not a single measurement.",))
                 for ij, v in (("11", c11), ("12", c12), ("44", c44)))


CONDENSED_EXTRAS: tuple[Quantity, ...] = (
    *_knowles("si", "silicon", "165.7", "63.9", "79.6"),
    *_knowles("cu", "copper", "168.4", "121.4", "75.4"),
    *(_cij(f"migliori2008.diamond.c{ij}", "diamond", ij, v, "GPa", source=_TANIGAKI_SOURCE, edition="Nat. Commun. 4 (2013), quoting J. Appl. Phys. 104 (2008)",
           url="https://doi.org/10.1063/1.2975190", retrieved_from="https://www.nature.com/articles/ncomms3343.pdf",
           where="Tanigaki et al. (2013), quoting Migliori et al.'s room-temperature resonant-ultrasound values,",
           extra=("The Migliori paper itself was not read; its abstract (Crossref) confirms the method and the 322-10 K range.",))
      for ij, v in (("11", "1078.6"), ("12", "126.6"), ("44", "577.6"))),
    *(_cij(f"kamm1964.al.c{ij}_0k", "aluminium (extrapolated to 0 K)", ij, v, "10^11 dyn cm^-2", source=_KAMM_SOURCE, edition="J. Appl. Phys. 35 (1964)",
           url="https://doi.org/10.1063/1.1713309", retrieved_from="https://api.crossref.org/works/10.1063/1.1713309", where="The abstract",
           extra=("Measured by ultrasonic pulse echo from 4.2 K to 300 K and extrapolated to 0 K.",))
      for ij, v in (("11", "11.430"), ("12", "6.192"), ("44", "3.162"))),
    *(_cij(f"vallin1964.al.c{ij}_4k", "aluminium (4 K)", ij, v, "10^10 N m^-2", source=_VALLIN_SOURCE, edition="J. Appl. Phys. 35 (1964)",
           url="https://doi.org/10.1063/1.1713749", retrieved_from="https://api.crossref.org/works/10.1063/1.1713749", where="The abstract")
      for ij, v in (("11", "11.63"), ("12", "6.48"), ("44", "3.09"))),
    _q("kamm1964.al.theta_d", "Debye temperature of aluminium from the 0 K elastic moduli", "theta_D(Al)", "430.3", "", "K", kind="no uncertainty printed",
       source=_KAMM_SOURCE, edition="J. Appl. Phys. 35 (1964)", url="https://doi.org/10.1063/1.1713309", retrieved_from="https://api.crossref.org/works/10.1063/1.1713309",
       keys=("debye temperature",), phrases=("debye temperatures", "debye temperature"),
       notes=("The abstract: 'The Debye temperature obtained from the 0 K modulus values is 430.3 K, in excellent agreement with the value from heat-capacity measurements.' The heat-capacity value is not stored.",)),
    _q("vallin1964.al.theta_d", "Debye temperature of aluminium from the 4 K elastic constants", "theta_D(Al)", "425", "", "K", kind="no uncertainty printed",
       source=_VALLIN_SOURCE, edition="J. Appl. Phys. 35 (1964)", url="https://doi.org/10.1063/1.1713749", retrieved_from="https://api.crossref.org/works/10.1063/1.1713749",
       keys=("debye temperature",), phrases=("debye temperatures", "debye temperature"), notes=("The abstract prints theta = 425 K, calculated from its 4 K elastic constants.",)),
    _q("migliori2008.diamond.theta_d", "Debye temperature of diamond from the zero-temperature elastic stiffnesses", "theta_D(C)", "2244", "", "K", kind="no uncertainty printed",
       source="A. Migliori, H. Ledbetter, R. G. Leisure et al., Diamond's elastic stiffnesses from 322 K to 10 K, J. Appl. Phys. 104, 053512 (2008), doi:10.1063/1.2975190, abstract",
       edition="J. Appl. Phys. 104 (2008)", url="https://doi.org/10.1063/1.2975190", retrieved_from="https://api.crossref.org/works/10.1063/1.2975190",
       keys=("debye temperature",), phrases=("debye temperatures", "debye temperature"), notes=("The abstract: 'Zero-temperature Cij correspond to a 2244-K Debye characteristic temperature.'",)),
    _q("nagamatsu2001.mgb2.tc", "superconducting transition temperature of MgB2", "T_c(MgB2)", "39", "", "K", kind="no uncertainty printed",
       source="J. Nagamatsu, N. Nakagawa, T. Muranaka, Y. Zenitani, and J. Akimitsu, Superconductivity at 39 K in magnesium diboride, Nature 410, 63-64 (2001), doi:10.1038/35065039, abstract",
       edition="Nature 410 (2001)", url="https://doi.org/10.1038/35065039", retrieved_from="https://www.nature.com/articles/35065039",
       keys=("superconductor", "mgb2"), phrases=("superconductors", "superconducting transition", "mgb2"),
       notes=("The abstract: 'Magnetization and resistivity measurements establish a transition temperature of 39 K.'",)),
    _q("drozdov2015.h3s.tc", "superconducting transition temperature of sulfur hydride (H3S) at 155 GPa", "T_c(H3S)", "203", "", "K", kind="no uncertainty printed",
       source="A. P. Drozdov, M. I. Eremets, I. A. Troyan, V. Ksenofontov, and S. I. Shylin, Conventional superconductivity at 203 kelvin at high pressures in the sulfur hydride system, Nature 525, 73-76 (2015), doi:10.1038/nature14964, arXiv:1506.08190",
       edition="Nature 525 (2015); arXiv v1", url="https://doi.org/10.1038/nature14964", retrieved_from="https://arxiv.org/pdf/1506.08190",
       keys=("superconductor", "h3s"), phrases=("superconductors", "superconducting transition", "h3s", "hydride superconductor"),
       notes=("The abstract says superconductivity 'has been confirmed by magnetic susceptibility measurements with Tc=203 K'; the magnetization figure is at 155 GPa.",
              "The abstract attributes it 'most likely' to H3S formed from H2S under pressure.")),
    _q("nair2008.graphene.transmittance", "white-light transmittance of suspended single-layer graphene", "T(graphene)", "97.7", "0.1", "%",
       kind="uncertainty as printed, level not stated",
       source="R. R. Nair, P. Blake, A. N. Grigorenko, K. S. Novoselov, T. J. Booth, T. Stauber, N. M. R. Peres, and A. K. Geim, Fine structure constant defines visual transparency of graphene, Science 320, 1308 (2008), doi:10.1126/science.1156965, arXiv:0803.3718",
       edition="Science 320 (2008); arXiv v1", url="https://doi.org/10.1126/science.1156965", retrieved_from="https://arxiv.org/pdf/0803.3718",
       keys=("graphene", "opacity"), phrases=("graphene opacity", "graphene transparency", "graphene fine structure"),
       notes=("The text: 'we have found T = 97.7% with an accuracy of +-0.1%'. The abstract says graphene absorbs 'pi times alpha = 2.3%' of white light; the board does not compute pi alpha.",)),
    _q("nair2008.graphene.g_over_g0", "dynamic conductivity of graphene over e^2/4hbar, white light", "G/G_0", "1.01", "0.04", "",
       kind="relative standard uncertainty",
       source="R. R. Nair et al., Fine structure constant defines visual transparency of graphene, Science 320, 1308 (2008), doi:10.1126/science.1156965, arXiv:0803.3718",
       edition="Science 320 (2008); arXiv v1", url="https://doi.org/10.1126/science.1156965", retrieved_from="https://arxiv.org/pdf/0803.3718",
       keys=("graphene",), phrases=("graphene opacity", "graphene conductivity"),
       notes=("The text: 'G = 1.01 G0 over the white-light region (450 nm < lambda < 800 nm) and the standard error of +-4%'; stored as a relative standard uncertainty of 0.04.",)),
    _q("ribeiropalau2015.qhe.graphene_gaas", "relative deviation of the quantized Hall resistance in graphene from GaAs/AlGaAs", "(R_H-G - R_H-GaAs)/R_H", "-0.9 e-11", "8.2 e-11", "",
       kind="standard uncertainty",
       source="R. Ribeiro-Palau, F. Lafont, J. Brun-Picard, D. Kazazis et al., Quantum Hall resistance standard in graphene devices under relaxed experimental conditions, Nat. Nanotechnol. 10, 965-971 (2015), doi:10.1038/nnano.2015.192, arXiv:1504.06511",
       edition="Nat. Nanotechnol. 10 (2015); arXiv v1", url="https://doi.org/10.1038/nnano.2015.192", retrieved_from="https://arxiv.org/pdf/1504.06511",
       keys=("quantum hall", "qhe universality"), phrases=("quantum hall plateau precision", "quantum hall universality", "quantized hall resistance"),
       notes=("The text: the weighted mean of 28 measurements 'shows an agreement between RH-G and RH-GaAs to -0.9x10^-11 within uc=8.2x10^-11', uc being the combined standard uncertainty.",
              "The same paper says the Hall resistance is quantized 'within 1x10^-9' over a 10 T range in this device; that is not stored separately.")),
    _q("ribeiropalau2015.qhe.combined_with_janssen", "QHE universality, graphene versus GaAs, combined with Janssen et al.", "(R_H-G - R_H-GaAs)/R_H", "-2.7 e-11", "6.0 e-11", "",
       kind="standard uncertainty",
       source="R. Ribeiro-Palau et al., Nat. Nanotechnol. 10, 965-971 (2015), doi:10.1038/nnano.2015.192, arXiv:1504.06511",
       edition="Nat. Nanotechnol. 10 (2015); arXiv v1", url="https://doi.org/10.1038/nnano.2015.192", retrieved_from="https://arxiv.org/pdf/1504.06511",
       keys=("quantum hall", "qhe universality"), phrases=("quantum hall plateau precision", "quantum hall universality"),
       notes=("The text combines this result with Janssen et al.'s 8.7x10^-11 test: 'agreement between RH-G and RH-GaAs to -2.7x10^-11 within uc=6.0x10^-11'.",)),
)


_LEMMON_SOURCE = "E. W. Lemmon and R. T. Jacobsen, Viscosity and thermal conductivity equations for nitrogen, oxygen, argon, and air, Int. J. Thermophys. 25, 21-69 (2004), doi:10.1023/B:IJOT.0000022327.04529.f3, Table V"
_LEMMON_URL = "https://trc.nist.gov/refprop/FAQ/NAO.PDF"
_LEMMON_NOTES = ("Table V lists values 'calculated from the equations' for program verification; 'the additional digits do not reflect the accuracy of the equations'.",
                 "For air the paper puts the uncertainty of viscosity at 1% in the dilute gas and about 2% between 270 and 300 K elsewhere, and the overall uncertainty within 5% for oxygen and air.",
                 "The PDF renders the viscosity unit as 'mPa s' in a symbol font; the values are in micropascal seconds (air at 300 K is 18.5 uPa s), and are stored in uPa s.")


def _lemmon(key: str, fluid: str, what: str, t: str, rho: str, value: str) -> Quantity:
    unit = "uPa s" if what == "viscosity" else "mW m^-1 K^-1"
    state = "dilute gas (zero density)" if rho == "0" else f"{rho} mol/dm^3"
    return _q(f"lemmon2004.{key}", f"{what} of {fluid} at {t} K, {state}", f"{'eta' if what == 'viscosity' else 'lambda'}({fluid}, {t} K)", value, "", unit,
              kind="no uncertainty printed", source=_LEMMON_SOURCE, edition="Int. J. Thermophys. 25 (2004), NIST copy", url="https://doi.org/10.1023/B:IJOT.0000022327.04529.f3",
              retrieved_from=_LEMMON_URL, keys=("transport properties",), phrases=(f"{what} of {fluid}", f"{fluid} {what}", "transport properties of air"),
              notes=(f"Table V prints {value} at T = {t} K, density {rho} mol/dm^3.",) + _LEMMON_NOTES)


_DB98_SOURCE = "R. J. Donnelly and C. F. Barenghi, The observed properties of liquid helium at the saturated vapor pressure, J. Phys. Chem. Ref. Data 27, 1217-1274 (1998), doi:10.1063/1.556028"
_DB98_URL = "https://srd.nist.gov/jpcrdreprint/1.556028.pdf"


def _db98(key: str, name: str, symbol: str, value: str, unit: str, where: str, printed: str, phrases: tuple[str, ...]) -> Quantity:
    return _q(f"db1998.he4.{key}", f"liquid helium-4 at saturated vapour pressure: {name}", symbol, value, "", unit, kind="no uncertainty printed",
              source=f"{_DB98_SOURCE}, {where}", edition="J. Phys. Chem. Ref. Data 27 (1998)", url="https://doi.org/10.1063/1.556028", retrieved_from=_DB98_URL,
              keys=("helium-4", "superfluid helium"), phrases=phrases + ("superfluid helium", "helium ii", "liquid helium properties"),
              notes=(f"{where} prints {printed}. These are recommended values from spline fits to an adopted database; the tables print no uncertainty for them.",))


FLUIDS_HELIUM: tuple[Quantity, ...] = (
    _lemmon("air.viscosity_300k_dilute", "air", "viscosity", "300.0", "0", "18.5230"),
    _lemmon("air.thermal_conductivity_300k_dilute", "air", "thermal conductivity", "300.0", "0", "26.3529"),
    _lemmon("air.viscosity_300k_5mol", "air", "viscosity", "300.0", "5.0", "21.3241"),
    _lemmon("air.thermal_conductivity_300k_5mol", "air", "thermal conductivity", "300.0", "5.0", "32.6062"),
    _lemmon("n2.viscosity_300k_dilute", "nitrogen", "viscosity", "300.0", "0", "17.8771"),
    _lemmon("o2.viscosity_300k_dilute", "oxygen", "viscosity", "300.0", "0", "20.6307"),
    _db98("rho_0k", "density at 0 K", "rho(0 K)", "0.1451397", "g cm^-3", "Table 1.2", "1.451 397E-1 g/cm3", ("helium density",)),
    _db98("rho_1_5k", "density at 1.50 K", "rho(1.5 K)", "0.1451646", "g cm^-3", "Table 1.2", "1.451 646E-1 g/cm3", ("helium density",)),
    _db98("rho_lambda", "density at the lambda point (fit parameter)", "rho_lambda", "0.1461087", "g cm^-3", "Sect. 1, text to Eq. (1.4)",
          "'Here, T_lambda = 2.1768 K and rho_lambda = 0.146 108 7 g/cm3'", ("helium density", "lambda point")),
    _db98("rho_s_1_5k", "superfluid density at 1.5 K", "rho_s(1.5 K)", "0.12900", "g cm^-3", "Table 2.3", "0.129 00 g/cm3", ("superfluid density", "two-fluid model")),
    _db98("rho_n_1_5k", "normal-fluid density at 1.5 K", "rho_n(1.5 K)", "0.01617", "g cm^-3", "Table 2.3", "0.016 17 g/cm3", ("normal fluid density", "two-fluid model")),
    _db98("u1_1_5k", "first sound velocity at 1.5000 K", "u_1(1.5 K)", "235.5", "m s^-1", "Table 3.3", "2.355E+2 m/s", ("first sound", "speed of sound in helium")),
    _db98("u2_1_0k", "second sound velocity at 1.0000 K", "u_2(1.0 K)", "18.93", "m s^-1", "Table 4.3", "1.893E+1 m/s", ("second sound",)),
    _db98("u2_1_5k", "second sound velocity at 1.5000 K", "u_2(1.5 K)", "20.03", "m s^-1", "Table 4.3", "2.003E+1 m/s", ("second sound",)),
    _db98("u2_2_0k", "second sound velocity at 2.0000 K", "u_2(2.0 K)", "16.78", "m s^-1", "Table 4.3", "1.678E+1 m/s", ("second sound",)),
)


_CHOU_SOURCE = "C. W. Chou, D. B. Hume, T. Rosenband, and D. J. Wineland, Optical clocks and relativity, Science 329, 1630-1633 (2010), doi:10.1126/science.1192720"
_BOTHWELL_SOURCE = "T. Bothwell, C. J. Kennedy, A. Aeppli, D. Kedar, J. M. Robinson, E. Oelker, A. Staron, and J. Ye, Resolving the gravitational redshift across a millimetre-scale atomic sample, Nature 602, 420-424 (2022), doi:10.1038/s41586-021-04349-7"
_WTB_SOURCE = "J. G. Williams, S. G. Turyshev, and D. H. Boggs, Progress in lunar laser ranging tests of relativistic gravity, Phys. Rev. Lett. 93, 261101 (2004), doi:10.1103/PhysRevLett.93.261101"
_HM_SOURCE = "F. Hofmann and J. Mueller, Relativistic tests with lunar laser ranging, Class. Quantum Grav. 35, 035015 (2018), doi:10.1088/1361-6382/aa8f7a"
_LEVEL = "uncertainty as printed, level not stated"

CLOCKS_FRAME_LLR: tuple[Quantity, ...] = (
    _q("chou2010.height_shift", "fractional frequency change of an Al+ optical clock raised by 33 cm, relative to a second Al+ clock", "df/f0", "4.1 e-17", "1.6 e-17", "",
       kind=_LEVEL, source=_CHOU_SOURCE, edition="Science 329 (2010), NIST copy", url="https://doi.org/10.1126/science.1192720", retrieved_from="https://tf.nist.gov/general/pdf/2447.pdf",
       keys=("gravitational redshift", "optical clock"), phrases=("gravitational redshift", "optical clock height", "clock height test", "time dilation at 33 cm", "redshift test"),
       notes=("The text prints 'a fractional frequency change of (4.1 +- 1.6) x 10^-17' between about 100,000 s of low-height and 40,000 s of high-height data; the 33 cm rise is from an original height difference of -17 cm measured with a laser level.",
              "The Fig. 3 caption says the vertical error bars represent statistical uncertainties; the text does not name the level of the 1.6.")),
    _q("chou2010.inferred_height", "height change of the Al-Mg clock inferred from its frequency shift", "Delta h", "37", "15", "cm",
       kind=_LEVEL, source=_CHOU_SOURCE, edition="Science 329 (2010), NIST copy", url="https://doi.org/10.1126/science.1192720", retrieved_from="https://tf.nist.gov/general/pdf/2447.pdf",
       keys=("gravitational redshift", "optical clock"), phrases=("optical clock height", "clock height test", "chronometric levelling"),
       notes=("The text prints 'the result of 37 +- 15 cm agrees well with the known value of 33 cm'.",)),
    _q("bothwell2022.redshift_gradient", "fractional frequency gradient measured vertically across a millimetre-scale Sr lattice clock sample, after systematic corrections", "d(df/f)/dz", "-9.8 e-20", "2.3 e-20", "mm^-1",
       kind=_LEVEL, source=_BOTHWELL_SOURCE, edition="arXiv:2109.12238 v1 (published as Nature 602, 420)", url="https://doi.org/10.1038/s41586-021-04349-7", retrieved_from="https://arxiv.org/pdf/2109.12238",
       keys=("gravitational redshift", "optical clock"), phrases=("gravitational redshift", "redshift within a millimeter", "millimetre redshift", "clock height test", "redshift test"),
       notes=("The preprint prints a weighted-mean gradient of -1.00(12)x10^-19/mm (standard error of the weighted mean) over 14 datasets, and 'a final frequency gradient of -9.8(2.3)x10-20/mm, consistent with the predicted redshift'.",
              "It states the expected redshift gradient at Earth's surface as -1.09x10^-19/mm in the coordinate system of its Fig. 1a. Values are from the arXiv v1 text; the published version was not reachable.")),
    _q("bothwell2022.redshift_gradient_synchronous", "fractional frequency gradient from the synchronous comparison of two regions of the same Sr sample, after systematic corrections", "d(df/f)/dz", "-1.28 e-19", "0.27 e-19", "mm^-1",
       kind=_LEVEL, source=_BOTHWELL_SOURCE, edition="arXiv:2109.12238 v1 (published as Nature 602, 420)", url="https://doi.org/10.1038/s41586-021-04349-7", retrieved_from="https://arxiv.org/pdf/2109.12238",
       keys=("gravitational redshift", "optical clock"), phrases=("redshift within a millimeter", "millimetre redshift", "synchronous clock comparison"),
       notes=("The preprint prints -1.30(18)x10^-19/mm before and 'a gradient of -1.28(27)x10-19/mm' after the additional systematic corrections, from 92 hours of data at a fractional frequency uncertainty of 7.6x10^-21.",)),
    _q("ciufolini2016.frame_dragging_mu", "Earth's frame dragging from LARES, LAGEOS and LAGEOS 2 with the GGM05S gravity model, normalised to its general-relativity value", "mu", "0.994", "0.002", "",
       kind=_SPLIT_KIND, systematic_text="0.05",
       source="I. Ciufolini, A. Paolozzi, E. C. Pavlis, R. Koenig, J. Ries, V. Gurzadyan, R. Matzner, R. Penrose, G. Sindoni, C. Paris, H. Khachatryan, and S. Mirzoyan, A test of general relativity using the LARES and LAGEOS satellites and a GRACE Earth gravity model, Eur. Phys. J. C 76, 120 (2016), doi:10.1140/epjc/s10052-016-3961-8",
       edition="Eur. Phys. J. C 76 (2016); arXiv abstract", url="https://doi.org/10.1140/epjc/s10052-016-3961-8", retrieved_from="https://arxiv.org/abs/1603.09674",
       keys=("frame dragging", "lageos", "lares"), phrases=("frame dragging", "frame-dragging", "lense-thirring", "lageos", "lares"),
       notes=("The abstract prints 'mu = (0.994 +- 0.002) +- 0.05', where 0.002 is the 1-sigma formal error and 0.05 the estimated systematic error, mainly from the GGM05S gravity model.", _SPLIT_NOTE)),
    _q("williams2004.nordtvedt_eta", "strong-equivalence-principle violation parameter from lunar laser ranging", "eta", "4.4 e-4", "4.5 e-4", "",
       kind=_LEVEL, source=_WTB_SOURCE, edition="Phys. Rev. Lett. 93 (2004); arXiv abstract", url="https://doi.org/10.1103/PhysRevLett.93.261101", retrieved_from="https://arxiv.org/abs/gr-qc/0411113",
       keys=("lunar laser ranging", "nordtvedt"), phrases=("nordtvedt parameter", "nordtvedt effect", "lunar laser ranging", "strong equivalence principle"),
       notes=("The abstract prints 'the corresponding SEP violation parameter eta is (4.4 +/- 4.5) x 10^{-4}, where eta=4beta-gamma-3'.",)),
    _q("williams2004.g_dot_over_g", "time variation of the gravitational constant from lunar laser ranging", "Gdot/G", "4 e-13", "9 e-13", "yr^-1",
       kind=_LEVEL, source=_WTB_SOURCE, edition="Phys. Rev. Lett. 93 (2004); arXiv abstract", url="https://doi.org/10.1103/PhysRevLett.93.261101", retrieved_from="https://arxiv.org/abs/gr-qc/0411113",
       keys=("lunar laser ranging", "varying g"), phrases=("gdot/g", "g dot over g", "time variation of g", "variation of the gravitational constant", "lunar laser ranging"),
       notes=("The abstract prints '\\dot G/G=(4 +/- 9) x 10^{-13} yr^{-1}'.",)),
    _q("hofmann2018.nordtvedt_eta", "Nordtvedt parameter from lunar laser ranging, 1970 to January 2015", "eta", "-0.2 e-4", "1.1 e-4", "",
       kind=_LEVEL, source=_HM_SOURCE, edition="Class. Quantum Grav. 35 (2018); publisher abstract", url="https://doi.org/10.1088/1361-6382/aa8f7a", retrieved_from="https://api.crossref.org/works/10.1088/1361-6382/aa8f7a",
       keys=("lunar laser ranging", "nordtvedt"), phrases=("nordtvedt parameter", "nordtvedt effect", "lunar laser ranging", "strong equivalence principle"),
       notes=("The abstract prints 'the Nordtvedt parameter eta = (-0.2 +- 1.1) x 10^-4'.",)),
    _q("hofmann2018.g_dot_over_g", "relative time variation of the gravitational constant from lunar laser ranging, 1970 to January 2015", "Gdot/G0", "7.1 e-14", "7.6 e-14", "yr^-1",
       kind=_LEVEL, source=_HM_SOURCE, edition="Class. Quantum Grav. 35 (2018); publisher abstract", url="https://doi.org/10.1088/1361-6382/aa8f7a", retrieved_from="https://api.crossref.org/works/10.1088/1361-6382/aa8f7a",
       keys=("lunar laser ranging", "varying g"), phrases=("gdot/g", "g dot over g", "time variation of g", "variation of the gravitational constant", "lunar laser ranging"),
       notes=("The abstract prints 'Gdot/G0 = (7.1 +- 7.6) x 10^-14 yr^-1', estimated with the station coordinates and the initial core rotation vector constrained.",)),
)


_T510 = "Table 5.10, 14-parameter fit to the LEP/SLD heavy flavour data"
_T510_NOTE = "Table 5.10's fit has chi2/dof = 53/(105 - 14); correlations are in Table 5.11 and are not stored."
_HF = ("heavy flavour", "heavy-flavour asymmetries", "z heavy flavour")
_HIGGS_MU = ("higgs signal strength", "signal strength", "higgs couplings")


def _higgs_pdg(key: str, final: str, node: str, value: str, error: str, phrases: tuple[str, ...]) -> Quantity:
    return _pdg(f"pdg2026.higgs_mu.{key}", f"Higgs signal strength, {final} final state (PDG average)", f"mu({final})", value, error, "", node=node,
                keys=("higgs boson",), phrases=phrases + _HIGGS_MU,
                notes=(_API_NOTE, f"PDG node {node} prints '{value}+-{error}' (OUR AVERAGE). A signal strength is the observed yield over the Standard Model expectation for that final state."))


PARTICLE_EXTRAS: tuple[Quantity, ...] = (
    _q("lep2005.a_l_sld", "leptonic asymmetry parameter A_l from SLD (left-right and polarised forward-backward asymmetries, lepton universality)", "A_l(SLD)", "0.1513", "0.0021", "",
       kind="uncertainty as printed, level not stated", source=f"{_LEP_SOURCE}, Eq. (3.15).", edition="Phys. Rept. 427 (2006); arXiv v3", url=_LEP_URL, retrieved_from=_LEP_COPY,
       keys=("z boson", "sld"), phrases=("sld a_l", "a_l sld", "left-right asymmetry", "sld leptonic asymmetry", "leptonic asymmetry parameter") + _Z_PHRASES,
       notes=("Eq. (3.15) prints 'A_l = 0.1513 +- 0.0021, where the total error includes the systematic error of +-0.0011'.",)),
    _lep("r_b0", "Z partial-width ratio Gamma(b bbar)/Gamma(had)", "R_b^0", "0.21629", "0.00066", "", _T510, ("r_b", "rb0") + _HF, (_T510_NOTE,)),
    _lep("r_c0", "Z partial-width ratio Gamma(c cbar)/Gamma(had)", "R_c^0", "0.1721", "0.0030", "", _T510, ("r_c", "rc0") + _HF, (_T510_NOTE,)),
    _lep("a_fb0_b", "b-quark pole forward-backward asymmetry", "A_FB^0,b", "0.0992", "0.0016", "", _T510, ("forward-backward asymmetry", "b quark asymmetry") + _HF, (_T510_NOTE,)),
    _lep("a_fb0_c", "c-quark pole forward-backward asymmetry", "A_FB^0,c", "0.0707", "0.0035", "", _T510, ("forward-backward asymmetry", "c quark asymmetry") + _HF, (_T510_NOTE,)),
    _lep("a_b", "b-quark asymmetry parameter (SLD polarised measurements enter)", "A_b", "0.923", "0.020", "", _T510, ("a_b",) + _HF, (_T510_NOTE,)),
    _lep("a_c", "c-quark asymmetry parameter (SLD polarised measurements enter)", "A_c", "0.670", "0.027", "", _T510, ("a_c",) + _HF, (_T510_NOTE,)),
    _pdg("pdg2026.r_l0", "Z partial-width ratio Gamma(hadrons)/Gamma(lepton+ lepton-)", "R_l", "20.767", "0.025", "", node="S044R20", keys=("z boson",),
         phrases=("r_l", "hadronic to leptonic width ratio") + _Z_PHRASES, notes=(_API_NOTE, "PDG node S044R20 prints 20.767+-0.025 (OUR FIT).")),
    _pdg("pdg2026.r_b0", "Z partial-width ratio R(b) = Gamma(b bbar)/Gamma(hadrons)", "R_b", "0.21629", "0.00066", "", node="S044R18", keys=("z boson",),
         phrases=("r_b",) + _HF, notes=(_API_NOTE, "PDG node S044R18 prints 0.21629+-0.00066 (OUR FIT).")),
    _pdg("pdg2026.a_fb0_b", "Z b-quark pole forward-backward charge asymmetry", "A_FB^0,b", "9.92", "0.16", "%", node="S044Z0B", keys=("z boson",),
         phrases=("forward-backward asymmetry", "b quark asymmetry") + _HF, notes=(_API_NOTE, "PDG node S044Z0B prints 9.92+-0.16 in percent (OUR FIT).")),
    _pdg("pdg2026.a_fb0_c", "Z c-quark pole forward-backward charge asymmetry", "A_FB^0,c", "7.07", "0.35", "%", node="S044Z0C", keys=("z boson",),
         phrases=("forward-backward asymmetry", "c quark asymmetry") + _HF, notes=(_API_NOTE, "PDG node S044Z0C prints 7.07+-0.35 in percent (OUR FIT).")),
    _pdg("pdg2026.z.a_e", "electron asymmetry parameter A(e) from Z data", "A_e", "0.1515", "0.0019", "", node="S044AE", keys=("z boson",),
         phrases=("z electron asymmetry", "leptonic asymmetry parameter", "left-right asymmetry") + _Z_PHRASES, notes=(_API_NOTE, "PDG node S044AE prints 0.1515+-0.0019 (OUR AVERAGE).")),
    _pdg("pdg2026.gamma_t", "top-quark decay width", "Gamma_t", "1.42", "0.19", "GeV", node="Q007W", kind="asymmetric standard uncertainty", lower_text="0.15",
         keys=("top quark",), phrases=("top width", "top quark width", "top-quark decay width", "width of the top quark"),
         notes=(_API_NOTE, "PDG node Q007W prints 1.42+0.19-0.15 GeV (OUR AVERAGE).")),
    _higgs_pdg("combined", "combined", "S126SA", "1.03", "0.04", ("combined higgs signal strength",)),
    _higgs_pdg("ww", "W W*", "S126SWW", "1.00", "0.08", ("higgs to ww", "h to ww")),
    _higgs_pdg("zz", "Z Z*", "S126SZZ", "1.02", "0.08", ("higgs to zz", "h to zz")),
    _higgs_pdg("gamma_gamma", "gamma gamma", "S126SGG", "1.10", "0.06", ("higgs to two photons", "h to gamma gamma", "diphoton")),
    _higgs_pdg("bb", "b bbar", "S126SBB", "0.94", "0.11", ("higgs to bb", "h to b bbar")),
    _higgs_pdg("tau_tau", "tau+ tau-", "S126STT", "0.91", "0.09", ("higgs to tau tau", "h to tau tau")),
    _higgs_pdg("mu_mu", "mu+ mu-", "S126SMU", "1.31", "0.29", ("higgs to muons", "h to mu mu")),
    _q("atlas2022.higgs_mu", "ATLAS global Higgs signal strength, full Run 2", "mu", "1.05", "0.06", "", kind="uncertainty as printed, level not stated",
       source="ATLAS Collaboration, A detailed map of Higgs boson interactions by the ATLAS experiment ten years after the discovery, Nature 607, 52-59 (2022), doi:10.1038/s41586-022-04893-w",
       edition="Nature 607 (2022); arXiv:2207.00092", url="https://doi.org/10.1038/s41586-022-04893-w", retrieved_from="https://arxiv.org/pdf/2207.00092",
       keys=("higgs boson", "atlas"), phrases=("atlas higgs signal strength", "global signal strength") + _HIGGS_MU,
       notes=("The text prints 'mu = 1.05 +- 0.06 = 1.05 +- 0.03 (stat.) +- 0.03 (exp.) +- 0.04 (sig. th.) +- 0.02 (bkg. th.)'. The total is stored; the components are not.",)),
    _q("cms2022.higgs_mu", "CMS common Higgs signal strength, all Run 2 data", "mu", "1.002", "0.057", "", kind="uncertainty as printed, level not stated",
       source="CMS Collaboration, A portrait of the Higgs boson by the CMS experiment ten years after the discovery, Nature 607, 60-68 (2022), doi:10.1038/s41586-022-04892-x",
       edition="Nature 607 (2022); arXiv:2207.00043", url="https://doi.org/10.1038/s41586-022-04892-x", retrieved_from="https://arxiv.org/pdf/2207.00043",
       keys=("higgs boson", "cms"), phrases=("cms higgs signal strength", "global signal strength") + _HIGGS_MU,
       notes=("The text prints 'The new combination of all Run 2 data yields mu = 1.002 +- 0.057'; theory, statistical and systematic parts 'are 0.036, 0.029, and 0.033, respectively'.",
              "At discovery the common mu 'was found to be 0.87 +- 0.23'; that value is not stored.")),
)


def _line2(key: str, name: str, spectrum: str, symbol: str, value: str, unc: str, low: str, high: str, row: str, phrases: tuple[str, ...]) -> Quantity:
    return _line(key, name, spectrum, symbol, value, unc, low, high, row, phrases=phrases, extra=("Added in batch 11.",))


_MALITSON_SOURCE = ("I. H. Malitson, Interspecimen comparison of the refractive index of fused silica, J. Opt. Soc. Am. 55, 1205-1208 (1965), doi:10.1364/JOSA.55.001205, "
                    "Sellmeier formula as reprinted in the refractiveindex.info database (CC0), file main/SiO2/nk/Malitson.yml")
_MALITSON_COPY = "https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/master/database/data/main/SiO2/nk/Malitson.yml"
_MALITSON_NOTE = ("The reprint gives the formula n^2 - 1 = B1 L^2/(L^2 - C1^2) + B2 L^2/(L^2 - C2^2) + B3 L^2/(L^2 - C3^2), L in micrometres, for fused silica at 20 degC (293 K), "
                  "with coefficients printed as '0 0.6961663 0.0684043 0.4079426 0.1162414 0.8974794 9.896161'. It says the formula 'is reported in Ref. 1 for the 0.21-3.71 um wavelength range'. "
                  "The original JOSA page was not reachable (the publisher blocks the box).")


def _malitson(key: str, name: str, symbol: str, value: str, unit: str) -> Quantity:
    return _q(f"malitson1965.fused_silica.{key}", f"fused silica Sellmeier {name} (Malitson 1965, 20 degC)", symbol, value, "", unit, kind="no uncertainty printed",
              source=_MALITSON_SOURCE, edition="J. Opt. Soc. Am. 55 (1965); refractiveindex.info reprint", url="https://doi.org/10.1364/JOSA.55.001205", retrieved_from=_MALITSON_COPY,
              keys=("refractive index", "fused silica"), phrases=("fused silica", "fused silica refractive index", "refractive index of fused silica", "sellmeier", "malitson"),
              notes=(_MALITSON_NOTE,))


_EMT_URL = "https://emtoolbox.nist.gov/Wavelength/Documentation.asp"
_EMT_SOURCE = "J. A. Stone and J. H. Zimmerman, Index of Refraction of Air, NIST Engineering Metrology Toolbox documentation (last updated 2019-07-01), Table 1"
_EMT_NOTE = ("Table 1 compares the Ciddor equation and NIST's modified Edlen equation at listed conditions, 'assuming 450 umol/mol CO2 concentration'. "
             "The page estimates that 'under typical laboratory atmospheric conditions the relative expanded uncertainty (coverage factor k=2) of both equations is about 2x10^-8', "
             "rising to as much as 1x10^-7 for Ciddor's equation far from standard conditions. Table 1 itself prints no uncertainty.")


def _air_n(key: str, method: str, t: str, rh: str, p: str, nm: str, value: str) -> Quantity:
    who = "Ciddor (1996) equation" if method == "ciddor" else "modified Edlen equation"
    return _q(f"nist_emt.air_n.{method}.{key}", f"refractive index of air at {t} degC, {rh}% RH, {p} kPa, {nm} nm ({who})", f"n_air({nm} nm)", value, "", "",
              kind="no uncertainty printed", source=_EMT_SOURCE, edition="NIST EMT, Refractive Index of Air documentation", url=_EMT_URL, retrieved_from=_EMT_URL,
              keys=("refractive index", "air"), phrases=("refractive index of air", "air refractive index", "index of refraction of air", "ciddor equation" if method == "ciddor" else "edlen equation"),
              notes=(f"Table 1 row: {t} degC, {rh} %, {p} kPa, {nm} nm.", _EMT_NOTE))


_SIVA_SOURCE = "V. Sivaramakrishnan, Dispersion of Faraday rotation in fused quartz, Proc. Indian Acad. Sci. A 44, 206-215 (1956), Table I"
_SIVA_URL = "https://www.ias.ac.in/public/Volumes/seca/044/04/0206-0215.pdf"


def _siva(angstrom: str, value: str) -> Quantity:
    return _q(f"sivaramakrishnan1956.fused_silica.verdet_{angstrom}a", f"Verdet constant of fused silica (fused quartz) at {angstrom} angstrom, measured", f"V({angstrom} A)", value, "", "arcmin cm^-1 Oe^-1",
              kind="no uncertainty printed", source=_SIVA_SOURCE, edition="Proc. Indian Acad. Sci. A 44 (1956), scanned text", url=_SIVA_URL, retrieved_from=_SIVA_URL,
              keys=("verdet constant", "faraday rotation", "fused silica"), phrases=("verdet constant", "verdet constant of fused silica", "faraday rotation", "magneto-optic"),
              notes=(f"Table I ('Magneto-Optical Data for Fused Quartz') prints {value} min./cm./Oersted in the 'Exp.' column at {angstrom} A, beside a calculated value from the author's dispersion formula, which is not stored.",
                     "The scale was set by comparing against water, taking 0.01547 min/cm/Oe at 5461 A and 25 degC from Rodger and Watson. The text is OCR of a scan; digits were read where the scan is clean."))


OPTICS_EXTRAS: tuple[Quantity, ...] = (
    _malitson("b1", "coefficient B1", "B1", "0.6961663", ""),
    _malitson("c1", "resonance wavelength C1", "C1", "0.0684043", "um"),
    _malitson("b2", "coefficient B2", "B2", "0.4079426", ""),
    _malitson("c2", "resonance wavelength C2", "C2", "0.1162414", "um"),
    _malitson("b3", "coefficient B3", "B3", "0.8974794", ""),
    _malitson("c3", "resonance wavelength C3", "C3", "9.896161", "um"),
    _air_n("20c_0rh_101325_633nm", "ciddor", "20", "0", "101.325", "633", "1.000271800"),
    _air_n("20c_0rh_101325_633nm", "edlen", "20", "0", "101.325", "633", "1.000271799"),
    _air_n("20c_0rh_101325_300nm", "ciddor", "20", "0", "101.325", "300", "1.000286581"),
    _air_n("20c_0rh_101325_1700nm", "ciddor", "20", "0", "101.325", "1700", "1.000268479"),
    _air_n("20c_0rh_60_633nm", "ciddor", "20", "0", "60", "633", "1.000160924"),
    _air_n("20c_0rh_120_633nm", "ciddor", "20", "0", "120", "633", "1.000321916"),
    _air_n("20c_100rh_100_633nm", "ciddor", "20", "100", "100", "633", "1.000267394"),
    _siva("5780", "0.01540"),
    _siva("5461", "0.01731"),
    _siva("4358", "0.02837"),
    _siva("3650", "0.04224"),
    _q("turvey1993.water.verdet_643nm", "Verdet constant of deionized water at 643.3 nm and 19 +- 3 degC", "V(H2O, 643.3 nm)", "3.98", "0.03", "urad A^-1",
       kind="uncertainty as printed, level not stated",
       source="K. Turvey, Determination of Verdet constant from combined ac and dc measurements, Rev. Sci. Instrum. 64, 1561-1568 (1993), doi:10.1063/1.1144027, Table I",
       edition="Rev. Sci. Instrum. 64 (1993), scanned copy", url="https://doi.org/10.1063/1.1144027", retrieved_from="https://physlab.org/wp-content/uploads/2016/04/Turvey.pdf",
       keys=("verdet constant", "faraday rotation"), phrases=("verdet constant", "verdet constant of water", "faraday rotation", "magneto-optic"),
       notes=("Table I prints 'Overall mean from the 25 determinations: 3.98 +- 0.03' in urad A^-1 (the scan's OCR renders the micro sign as 'p').",
              "The abstract gives standard errors of the mean of 0.3% and 0.4% for the two methods, plus 0.4% systematic uncertainty from instrument calibration; the text also quotes a literature survey value of 3.97 +- 0.02 urad A^-1, not stored.",
              "In these units V is the rotation per ampere-turn of the solenoid, i.e. the Verdet constant in rad T^-1 m^-1 times mu_0.")),
    _line2("ne_632_8", "neon red line (the He-Ne laser line), 3p - 5s", "Ne I", "lambda_air(Ne 632.8)", "632.81646", "0.00004", "632.7", "632.9",
           "Ne I, 2s2.2p5.(2P*<1/2>).3p 2[3/2] 2 - 2s2.2p5.(2P*<1/2>).5s 2[1/2]* 1, Ritz 632.81639(6) nm, intensity 3000, A_ki 3.39e+06 s^-1", ("neon 632.8", "he-ne laser line", "helium-neon line")),
    _line2("hg_253_7", "mercury resonance line, 6s2 1S0 - 6s6p 3P1", "Hg I", "lambda_air(Hg 253.7)", "253.6521", "0.0001", "253.6", "253.7",
           "Hg I, 5d10.6s2 1S 0 - 5d10.6s.6p 3P* 1, Ritz 253.65209(5) nm, intensity 900000, A_ki 8.40e+06 s^-1", ("mercury 253.7", "mercury resonance line", "mercury uv line")),
    _line2("hg_h", "mercury violet line (the glass-catalogue h line), 6s6p 3P0 - 6s7s 3S1", "Hg I", "lambda_air(Hg h)", "404.6565", "0.0001", "404.6", "404.7",
           "Hg I, 5d10.6s.6p 3P* 0 - 5d10.6s.7s 3S 1, Ritz 404.65643(8) nm, intensity 12000, A_ki 2.07e+07 s^-1", ("mercury violet line", "mercury h line")),
    _line2("ca_ii_k", "ionized calcium K line, 4s 2S1/2 - 4p 2P3/2", "Ca II", "lambda_air(Ca II K)", "393.366", "", "393.3", "393.4",
           "Ca II, 3p6.4s 2S 1/2 - 3p6.4p 2P* 3/2, Ritz 393.3663 nm, intensity 230, A_ki 1.47e+08 s^-1", ("calcium k line", "ca ii k", "fraunhofer k")),
    _line2("ca_ii_h", "ionized calcium H line, 4s 2S1/2 - 4p 2P1/2", "Ca II", "lambda_air(Ca II H)", "396.847", "", "396.8", "396.9",
           "Ca II, 3p6.4s 2S 1/2 - 3p6.4p 2P* 1/2, Ritz 396.8469 nm, intensity 220, A_ki 1.4e+08 s^-1", ("calcium h line", "ca ii h")),
    _line2("k_d2", "potassium D2 line, 4s 2S1/2 - 4p 2P3/2", "K I", "lambda_air(K D2)", "766.489913", "", "766.4", "766.6",
           "K I, 3p6.4s 2S 1/2 - 3p6.4p 2P* 3/2, Ritz 766.48991(3) nm, intensity 25r, A_ki 3.779e+07 s^-1", ("potassium d lines", "potassium d2")),
    _line2("k_d1", "potassium D1 line, 4s 2S1/2 - 4p 2P1/2", "K I", "lambda_air(K D1)", "769.896456", "", "769.8", "770.0",
           "K I, 3p6.4s 2S 1/2 - 3p6.4p 2P* 1/2, Ritz 769.89646(3) nm, intensity 24r, A_ki 3.734e+07 s^-1", ("potassium d lines", "potassium d1")),
)


def _hadron(key: str, name: str, symbol: str, value: str, error: str, node: str, label: str, phrases: tuple[str, ...]) -> Quantity:
    return _pdg(f"pdg2026.{key}", f"{name} mass", symbol, value, error, "MeV", node=node, keys=("hadron masses",),
                phrases=phrases + ("hadron masses", "heavier hadron masses"),
                notes=(_API_NOTE, f"PDG node {node} prints {value}+-{error} MeV ({label})."))


def _br(key: str, decay: str, symbol: str, value: str, error: str, unit: str, node: str, label: str, phrases: tuple[str, ...], *, lower: str = "", printed: str = "", extra: tuple[str, ...] = ()) -> Quantity:
    return _pdg(f"pdg2026.br.{key}", f"branching fraction {decay}", symbol, value, error, unit, node=node,
                kind="asymmetric standard uncertainty" if lower else "standard uncertainty", lower_text=lower,
                keys=("branching ratio",), phrases=phrases + ("branching ratio", "branching fraction"),
                notes=(_API_NOTE, f"PDG node {node} prints {printed or value + '+-' + error}" + (" in percent" if unit == "%" else "") + f" ({label}).") + extra)


_SYM_NOTE = "The API's stored errors for this entry are asymmetric ({0}); PDG's summary display rounds them to the symmetric value stored here."

PARTICLE_HADRONS_BR: tuple[Quantity, ...] = (
    _hadron("m_d_plus", "D+ meson", "m_D+", "1869.66", "0.05", "S031M", "OUR FIT", ("d meson mass", "d+ mass", "charm meson")),
    _hadron("m_d0", "D0 meson", "m_D0", "1864.84", "0.04", "S032M", "OUR FIT", ("d meson mass", "d0 mass", "charm meson")),
    _hadron("m_ds", "D_s+ meson", "m_Ds", "1968.35", "0.07", "S034M", "OUR FIT; the node also prints an OUR AVERAGE of 1969.0+-1.4 MeV, not stored", ("d meson mass", "d_s mass", "charm meson")),
    _hadron("m_b_plus", "B+ meson", "m_B+", "5279.41", "0.07", "S041M", "OUR FIT", ("b meson mass", "b+ mass", "bottom meson")),
    _hadron("m_b0", "B0 meson", "m_B0", "5279.72", "0.08", "S042M", "OUR FIT", ("b meson mass", "b0 mass", "bottom meson")),
    _hadron("m_bs", "B_s0 meson", "m_Bs", "5366.93", "0.10", "S086M", "OUR FIT; the node also prints an OUR AVERAGE of 5366.91+-0.11 MeV, not stored", ("b meson mass", "b_s mass", "bottom meson")),
    _hadron("m_jpsi", "J/psi(1S)", "m_J/psi", "3096.900", "0.006", "M070M", "OUR AVERAGE", ("j/psi", "j/psi mass", "charmonium", "quarkonium")),
    _hadron("m_upsilon1s", "Upsilon(1S)", "m_Upsilon(1S)", "9460.40", "0.10", "M049M", "OUR AVERAGE", ("upsilon", "upsilon mass", "bottomonium", "quarkonium")),
    _hadron("m_sigma_plus", "Sigma+ baryon", "m_Sigma+", "1189.37", "0.07", "S019M", "OUR FIT", ("sigma baryon", "sigma+ mass", "hyperon masses")),
    _hadron("m_sigma0", "Sigma0 baryon", "m_Sigma0", "1192.642", "0.024", "S021M", "OUR FIT", ("sigma baryon", "sigma0 mass", "hyperon masses")),
    _hadron("m_sigma_minus", "Sigma- baryon", "m_Sigma-", "1197.449", "0.029", "S020M", "OUR FIT", ("sigma baryon", "sigma- mass", "hyperon masses")),
    _hadron("m_xi0", "Xi0 baryon", "m_Xi0", "1314.86", "0.20", "S023M", "OUR FIT", ("xi baryon", "xi0 mass", "hyperon masses")),
    _hadron("m_xi_minus", "Xi- baryon", "m_Xi-", "1321.71", "0.07", "S022M", "OUR FIT", ("xi baryon", "xi- mass", "hyperon masses")),
    _hadron("m_omega_minus", "Omega- baryon", "m_Omega-", "1672.45", "0.29", "S024M", "OUR FIT", ("omega baryon", "omega- mass", "hyperon masses")),
    _hadron("m_lambda_c", "Lambda_c+ baryon", "m_Lambda_c", "2286.46", "0.14", "S033M", "OUR FIT; OUR AVERAGE prints the same", ("lambda_c", "lambda_c mass", "charmed baryon")),
    _hadron("m_lambda_b", "Lambda_b0 baryon", "m_Lambda_b", "5619.57", "0.16", "S040M", "OUR AVERAGE", ("lambda_b", "lambda_b mass", "bottom baryon")),
    _br("h_bb", "H -> b bbar", "B(H->bb)", "53", "8", "%", "S126.4", "OUR AVERAGE", ("higgs branching ratio", "higgs to bb", "h to b bbar")),
    _br("h_ww", "H -> W W*", "B(H->WW*)", "25.7", "2.5", "%", "S126.1", "OUR AVERAGE", ("higgs branching ratio", "higgs to ww", "h to ww"), extra=(_SYM_NOTE.format("+0.026, -0.024 as fractions"),)),
    _br("h_zz", "H -> Z Z*", "B(H->ZZ*)", "2.80", "0.30", "%", "S126.2", "OUR AVERAGE", ("higgs branching ratio", "higgs to zz", "h to zz")),
    _br("h_tautau", "H -> tau+ tau-", "B(H->tautau)", "6.0", "0.8", "%", "S126.5", "OUR AVERAGE", ("higgs branching ratio", "higgs to tau tau"), lower="0.7", printed="6.0+0.8-0.7"),
    _br("h_gammagamma", "H -> gamma gamma", "B(H->gammagamma)", "2.50 e-3", "0.20 e-3", "", "S126.3", "OUR AVERAGE", ("higgs branching ratio", "higgs to two photons", "h to gamma gamma"), printed="(2.50+-0.20)E-3"),
    _br("h_mumu", "H -> mu+ mu-", "B(H->mumu)", "3.0 e-4", "0.9 e-4", "", "S126.8", "OUR AVERAGE", ("higgs branching ratio", "higgs to muons", "h to mu mu"), printed="(3.0+-0.9)E-4"),
    _br("z_invisible", "Z -> invisible", "B(Z->invisible)", "20.000", "0.055", "%", "S044.9", "OUR FIT", ("z invisible", "z invisible branching ratio", "invisible z decays")),
    _br("z_hadrons", "Z -> hadrons", "B(Z->hadrons)", "69.911", "0.056", "%", "S044.7", "OUR FIT", ("z hadronic branching ratio", "z to hadrons")),
    _pdg("pdg2026.gamma_z_invisible", "Z invisible partial width", "Gamma(Z->invisible)", "499.3", "1.5", "MeV", node="S044W6", keys=("z boson",),
         phrases=("z invisible", "z invisible width", "invisible width") + _Z_PHRASES, notes=(_API_NOTE, "PDG node S044W6 prints 499.3+-1.5 MeV (OUR AVERAGE).")),
)


def _gw_event(id: str, event: str, what: str, symbol: str, value: str, upper: str, lower: str, unit: str, catalog: str, json_url: str, about: str, field: str) -> Quantity:
    source, doi = _GW_RELEASES[catalog]
    return _q(f"{id}", f"{event} {what} ({catalog})", f"{symbol}({event})", value, upper, unit, kind="90% credible interval", lower_text=lower,
              source=source, edition=f"{catalog} via the GWOSC event API", url=f"https://doi.org/{doi}", retrieved_from=json_url,
              keys=("gravitational waves", "gw events", event.lower()), phrases=(event.lower(), f"{event.lower()} {what}", "gravitational wave events", "gwtc events", "compact binary mergers"),
              notes=(f"The GWOSC event API prints {field} = {value} with lower {('-' + lower)} and upper +{upper} {unit}: the median and the 90% credible interval.",
                     "These are the catalogue's source-frame values under its default cosmology and priors; distances are luminosity distances."))


_GW_RELEASES = {
    "GWTC-1": ("LIGO Scientific and Virgo Collaborations, GWTC-1 data release, doi:10.7935/82H3-HH23 (catalogue paper Phys. Rev. X 9, 031040 (2019))", "10.7935/82H3-HH23"),
    "GWTC-2.1": ("LIGO Scientific and Virgo Collaborations, GWTC-2.1 data release, doi:10.7935/qf3a-3z67 (catalogue paper Phys. Rev. D 109, 022001 (2024))", "10.7935/qf3a-3z67"),
    "GWTC-3": ("LIGO Scientific, Virgo and KAGRA Collaborations, GWTC-3 data release, doi:10.7935/b024-1886 (catalogue paper Phys. Rev. X 13, 041039 (2023))", "10.7935/b024-1886"),
    "GWTC-4.0": ("LIGO Scientific, Virgo and KAGRA Collaborations, GWTC-4.0 data release, doi:10.7935/aes8-px89", "10.7935/aes8-px89"),
    "GWTC-5.0": ("LIGO Scientific, Virgo and KAGRA Collaborations, GWTC-5.0 data release, doi:10.7935/bk00-6a89", "10.7935/bk00-6a89"),
}

_TAK_SOURCE = ("M. Takamoto, I. Ushijima, N. Ohmae, T. Yahagi, K. Kokado, H. Shinkai, and H. Katori, Test of general relativity by a pair of transportable optical lattice clocks, Nature Photon. 14, 411-415 (2020), doi:10.1038/s41566-020-0619-8, "
               "as reported by its authors in H. Shinkai, M. Takamoto, and H. Katori, Int. J. Mod. Phys. D 34, 2540012 (2025), arXiv:2502.06104, Sect. 4.2")
_TAK_URL = "https://arxiv.org/pdf/2502.06104"


def _tak(key: str, name: str, symbol: str, value: str, unc: str, unit: str, printed: str, phrases: tuple[str, ...]) -> Quantity:
    return _q(f"takamoto2020.{key}", name, symbol, value, unc, unit, kind="uncertainty as printed, level not stated", source=_TAK_SOURCE,
              edition="Nature Photon. 14 (2020), numbers from the authors' 2025 review (arXiv v1)", url="https://doi.org/10.1038/s41566-020-0619-8", retrieved_from=_TAK_URL,
              keys=("gravitational redshift", "optical clock", "tokyo skytree"), phrases=phrases + ("tokyo skytree", "skytree clock test", "optical clock height", "clock height test"),
              notes=(f"Sect. 4.2 prints {printed}.", "The Nature Photonics paper itself was not reachable from the box (publisher block); the review is by three of its authors and describes the same 2018 Skytree measurement (its ref. 8)."))


GRAV_EVENTS_SKYTREE: tuple[Quantity, ...] = (
    _tak("redshift_alpha", "redshift violation parameter from two transportable Sr lattice clocks 452 m apart at Tokyo Skytree", "alpha", "1.4 e-5", "9.1 e-5", "",
         "'These results indicate a value of alpha = (1.4+-9.1)x10^-5, giving the best constraint on the gravitational redshift on the ground'", ("redshift test", "gravitational redshift")),
    _tak("clock_height", "Skytree height difference measured by the clocks (chronometric levelling)", "Delta h_clock", "452.650", "0.039", "m",
         "'... to obtain Delta h = (452.650 +- 0.039) m', from clock comparisons over days in October 2018", ("chronometric levelling",)),
    _tak("laser_ranging_height", "Skytree height difference from simultaneous laser ranging", "Delta h_ranging", "452.631", "0.013", "m",
         "'the simultaneous laser ranging value of Delta h = (452.631+-0.013) m', which agrees with the clock value 'within 1 sigma uncertainty'", ()),
    _tak("same_height_beat", "fractional beat note of the two transportable clocks at the same height after the Skytree run", "Delta f/f", "-0.3 e-18", "4.7 e-18", "",
         "'The beat note of two clocks set at the same height (red triangles) demonstrates an excellent reproducibility (-0.3 +- 4.7) x 10^-18'", ("clock reproducibility",)),
    _gw_event("gw170817.m1_source", "GW170817", "primary source-frame mass", "m_1", "1.46", "0.12", "0.1", "M_sun", "GWTC-1", "https://gwosc.org/eventapi/json/GWTC-1-confident/GW170817/v3", "binary neutron star merger with a kilonova", "mass_1_source"),
    _gw_event("gw170817.m2_source", "GW170817", "secondary source-frame mass", "m_2", "1.27", "0.09", "0.09", "M_sun", "GWTC-1", "https://gwosc.org/eventapi/json/GWTC-1-confident/GW170817/v3", "binary neutron star merger with a kilonova", "mass_2_source"),
    _gw_event("gw170817.luminosity_distance", "GW170817", "luminosity distance", "d_L", "40.0", "7.0", "15.0", "Mpc", "GWTC-1", "https://gwosc.org/eventapi/json/GWTC-1-confident/GW170817/v3", "binary neutron star merger with a kilonova", "luminosity_distance"),
    _gw_event("gw190521.m1_source", "GW190521", "primary source-frame mass", "m_1", "98.4", "33.6", "21.7", "M_sun", "GWTC-2.1", "https://gwosc.org/eventapi/json/GWTC-2.1-confident/GW190521/v4", "heaviest O3a binary black hole", "mass_1_source"),
    _gw_event("gw190521.m2_source", "GW190521", "secondary source-frame mass", "m_2", "57.2", "27.1", "30.1", "M_sun", "GWTC-2.1", "https://gwosc.org/eventapi/json/GWTC-2.1-confident/GW190521/v4", "heaviest O3a binary black hole", "mass_2_source"),
    _gw_event("gw190521.luminosity_distance", "GW190521", "luminosity distance", "d_L", "3310.0", "2790.0", "1800.0", "Mpc", "GWTC-2.1", "https://gwosc.org/eventapi/json/GWTC-2.1-confident/GW190521/v4", "heaviest O3a binary black hole", "luminosity_distance"),
    _gw_event("gw190814.m1_source", "GW190814", "primary source-frame mass", "m_1", "23.3", "1.4", "1.4", "M_sun", "GWTC-2.1", "https://gwosc.org/eventapi/json/GWTC-2.1-confident/GW190814/v3", "binary with a 2.6 M_sun secondary", "mass_1_source"),
    _gw_event("gw190814.m2_source", "GW190814", "secondary source-frame mass", "m_2", "2.6", "0.1", "0.1", "M_sun", "GWTC-2.1", "https://gwosc.org/eventapi/json/GWTC-2.1-confident/GW190814/v3", "binary with a 2.6 M_sun secondary", "mass_2_source"),
    _gw_event("gw190814.luminosity_distance", "GW190814", "luminosity distance", "d_L", "230.0", "40.0", "50.0", "Mpc", "GWTC-2.1", "https://gwosc.org/eventapi/json/GWTC-2.1-confident/GW190814/v3", "binary with a 2.6 M_sun secondary", "luminosity_distance"),
    _gw_event("gw190425.m1_source", "GW190425", "primary source-frame mass", "m_1", "2.1", "0.5", "0.4", "M_sun", "GWTC-2.1", "https://gwosc.org/eventapi/json/GWTC-2.1-confident/GW190425/v3", "second binary neutron star candidate", "mass_1_source"),
    _gw_event("gw190425.m2_source", "GW190425", "secondary source-frame mass", "m_2", "1.3", "0.3", "0.2", "M_sun", "GWTC-2.1", "https://gwosc.org/eventapi/json/GWTC-2.1-confident/GW190425/v3", "second binary neutron star candidate", "mass_2_source"),
    _gw_event("gw190425.luminosity_distance", "GW190425", "luminosity distance", "d_L", "150.0", "80.0", "60.0", "Mpc", "GWTC-2.1", "https://gwosc.org/eventapi/json/GWTC-2.1-confident/GW190425/v3", "second binary neutron star candidate", "luminosity_distance"),
    _gw_event("gw200115.m1_source", "GW200115", "primary source-frame mass", "m_1", "5.9", "2.0", "2.5", "M_sun", "GWTC-3", "https://gwosc.org/eventapi/json/GWTC-3-confident/GW200115_042309/v2", "neutron star - black hole merger", "mass_1_source"),
    _gw_event("gw200115.m2_source", "GW200115", "secondary source-frame mass", "m_2", "1.44", "0.85", "0.28", "M_sun", "GWTC-3", "https://gwosc.org/eventapi/json/GWTC-3-confident/GW200115_042309/v2", "neutron star - black hole merger", "mass_2_source"),
    _gw_event("gw200115.luminosity_distance", "GW200115", "luminosity distance", "d_L", "290.0", "150.0", "100.0", "Mpc", "GWTC-3", "https://gwosc.org/eventapi/json/GWTC-3-confident/GW200115_042309/v2", "neutron star - black hole merger", "luminosity_distance"),
    _gw_event("gw230529.m1_source", "GW230529", "primary source-frame mass", "m_1", "3.66", "0.82", "1.21", "M_sun", "GWTC-4.0", "https://gwosc.org/eventapi/json/GWTC-4.0/GW230529_181500/v2", "mass-gap primary with a neutron star", "mass_1_source"),
    _gw_event("gw230529.m2_source", "GW230529", "secondary source-frame mass", "m_2", "1.42", "0.6", "0.22", "M_sun", "GWTC-4.0", "https://gwosc.org/eventapi/json/GWTC-4.0/GW230529_181500/v2", "mass-gap primary with a neutron star", "mass_2_source"),
    _gw_event("gw230529.luminosity_distance", "GW230529", "luminosity distance", "d_L", "203.0", "103.0", "98.0", "Mpc", "GWTC-4.0", "https://gwosc.org/eventapi/json/GWTC-4.0/GW230529_181500/v2", "mass-gap primary with a neutron star", "luminosity_distance"),
    _gw_event("gw231123.m1_source", "GW231123", "primary source-frame mass", "m_1", "137.0", "23.0", "18.0", "M_sun", "GWTC-4.0", "https://gwosc.org/eventapi/json/GWTC-4.0/GW231123_135430/v2", "most massive binary black hole in GWTC-4.0", "mass_1_source"),
    _gw_event("gw231123.m2_source", "GW231123", "secondary source-frame mass", "m_2", "101.0", "22.0", "50.0", "M_sun", "GWTC-4.0", "https://gwosc.org/eventapi/json/GWTC-4.0/GW231123_135430/v2", "most massive binary black hole in GWTC-4.0", "mass_2_source"),
    _gw_event("gw231123.luminosity_distance", "GW231123", "luminosity distance", "d_L", "2200.0", "1900.0", "1500.0", "Mpc", "GWTC-4.0", "https://gwosc.org/eventapi/json/GWTC-4.0/GW231123_135430/v2", "most massive binary black hole in GWTC-4.0", "luminosity_distance"),
    _gw_event("gw250114.m1_source", "GW250114", "primary source-frame mass", "m_1", "33.76", "1.28", "0.9", "M_sun", "GWTC-5.0", "https://gwosc.org/eventapi/json/GWTC-5.0/GW250114_082203/v2", "loudest binary black hole signal to date", "mass_1_source"),
    _gw_event("gw250114.m2_source", "GW250114", "secondary source-frame mass", "m_2", "32.26", "0.95", "1.47", "M_sun", "GWTC-5.0", "https://gwosc.org/eventapi/json/GWTC-5.0/GW250114_082203/v2", "loudest binary black hole signal to date", "mass_2_source"),
    _gw_event("gw250114.luminosity_distance", "GW250114", "luminosity distance", "d_L", "405.0", "84.0", "73.0", "Mpc", "GWTC-5.0", "https://gwosc.org/eventapi/json/GWTC-5.0/GW250114_082203/v2", "loudest binary black hole signal to date", "luminosity_distance"),
)


_MATULA_SOURCE = "R. A. Matula, Electrical resistivity of copper, gold, palladium, and silver, J. Phys. Chem. Ref. Data 8, 1147-1298 (1979), doi:10.1063/1.555614"
_MATULA_URL = "https://srd.nist.gov/jpcrdreprint/1.555614.pdf"
_DESAI_AL_SOURCE = "P. D. Desai, H. M. James, and C. Y. Ho, Electrical resistivity of aluminum and manganese, J. Phys. Chem. Ref. Data 13, 1131-1172 (1984), doi:10.1063/1.555725, Table 1"
_DESAI_AL_URL = "https://srd.nist.gov/jpcrdreprint/1.555725.pdf"
_DESAI_W_SOURCE = "P. D. Desai, T. K. Chu, H. M. James, and C. Y. Ho, Electrical resistivity of selected elements, J. Phys. Chem. Ref. Data 13, 1069-1096 (1984), doi:10.1063/1.555723, Table 5"
_DESAI_W_URL = "https://srd.nist.gov/jpcrdreprint/1.555723.pdf"
_METAL = {"cu": "copper", "ag": "silver", "au": "gold", "al": "aluminium", "w": "tungsten"}


def _rho(prefix: str, metal: str, t: str, value: str, source: str, url: str, edition: str, where: str, note: str) -> Quantity:
    name = _METAL[metal]
    phrases = (f"resistivity of {name}", f"{name} resistivity", f"electrical resistivity of {name}", "resistivity of metals", "electrical resistivity")
    if metal == "al":
        phrases += ("resistivity of aluminum", "aluminum resistivity")
    if metal == "cu":
        phrases += ("copper resistivity versus temperature",)
    key = t.replace(".", "_")
    return _q(f"{prefix}.{metal}.rho_{key}k", f"electrical resistivity of {name} at {t} K (recommended value)", f"rho_{metal.capitalize()}({t} K)", value, "", "1e-8 ohm m",
              kind="no uncertainty printed", source=source, edition=edition, url=url.replace("https://srd.nist.gov/jpcrdreprint/", "https://doi.org/10.1063/").replace(".pdf", ""), retrieved_from=url,
              keys=("electrical resistivity", "metals"), phrases=phrases, notes=(f"{where} prints {value} x 10^-8 ohm m at T = {t} K.", note))


_MATULA_NOTES = {
    "cu": "Table 2 is the total resistivity, corrected for thermal expansion, for annealed 99.999% or purer copper (residual resistivity 0.00200 x 10^-8 ohm m below 55 K). The text puts the uncertainty of the total resistivity at 3% above 10 K to 100 K, 1% above 100 K to 250 K, and 0.5% above 250 K to 350 K.",
    "ag": "Table 11 is the total resistivity, corrected for thermal expansion, for annealed 99.999% or purer silver (residual resistivity 0.00100 x 10^-8 ohm m below 40 K). The text puts the uncertainty of the total resistivity at 1% above 70 K to 400 K.",
    "au": "Table 5 is the total resistivity, corrected for thermal expansion, for annealed 99.999% or purer gold (residual resistivity 0.0220 x 10^-8 ohm m below 293 K). The text puts the uncertainty of the total resistivity at 1% above 50 K to 500 K.",
}
_DESAI_AL_NOTE = ("Table 1's 'uncorrected' column (not corrected for thermal expansion) for well-annealed aluminium of 99.99% purity or higher; at these temperatures the corrected column prints the same value. "
                  "The text estimates the uncertainty 'within +-1% below 400 K'.")
_DESAI_W_NOTE = ("Table 5's 'uncorrected' column for tungsten of 99.99% purity or higher; at these temperatures the corrected column prints the same value. "
                 "The table footnote gives the estimated uncertainty as within +-3% from 100 K to 300 K. Values were checked against the page image, since the text layer is OCR.")

_TN1512_SOURCE = "J. Baker-Jarvis, B. Riddle, and M. D. Janezic, Dielectric and magnetic properties of printed wiring boards and other substrate materials, NIST Technical Note 1512 (March 1999)"
_TN1512_URL = "https://nvlpubs.nist.gov/nistpubs/Legacy/TN/nbstechnicalnote1512.pdf"


def _eps(key: str, material: str, method: str, f_ghz: str, value: str, rel: str, table: str, phrases: tuple[str, ...], extra: tuple[str, ...] = ()) -> Quantity:
    return _q(f"nist_tn1512.{key}", f"relative permittivity (real part) of {material} at {f_ghz} GHz, {method}", f"eps_r'({material})", value, rel, "",
              kind="relative standard uncertainty", source=f"{_TN1512_SOURCE}, {table}", edition="NIST TN 1512 (1999)", url=_TN1512_URL, retrieved_from=_TN1512_URL,
              keys=("permittivity", "dielectric constant"), phrases=phrases + ("relative permittivity", "dielectric constant", "permittivity of dielectrics", "microwave permittivity"),
              notes=(f"{table} prints eps' = {value} at {f_ghz} GHz in the {method} column; its caption gives that method's standard uncertainty (RSS) as U_eps' = {rel_pct(rel)}.",) + extra)


def rel_pct(rel: str) -> str:
    return {"0.005": "0.5%", "0.01": "1%", "0.001": "0.1%"}[rel]


_TN_7980 = ("The table names the specimen 'Corning 7980 34604'; Corning 7980 is Corning's high-purity fused silica (manufacturer's product name, not stated in the table).",)

EM_MATERIALS: tuple[Quantity, ...] = (
    _rho("matula1979", "cu", "100", "0.348", _MATULA_SOURCE + ", Table 2", _MATULA_URL, "J. Phys. Chem. Ref. Data 8 (1979)", "Table 2", _MATULA_NOTES["cu"]),
    _rho("matula1979", "cu", "273.15", "1.543", _MATULA_SOURCE + ", Table 2", _MATULA_URL, "J. Phys. Chem. Ref. Data 8 (1979)", "Table 2", _MATULA_NOTES["cu"]),
    _rho("matula1979", "cu", "293", "1.678", _MATULA_SOURCE + ", Table 2", _MATULA_URL, "J. Phys. Chem. Ref. Data 8 (1979)", "Table 2", _MATULA_NOTES["cu"]),
    _rho("matula1979", "cu", "300", "1.725", _MATULA_SOURCE + ", Table 2", _MATULA_URL, "J. Phys. Chem. Ref. Data 8 (1979)", "Table 2", _MATULA_NOTES["cu"]),
    _rho("matula1979", "ag", "273.15", "1.467", _MATULA_SOURCE + ", Table 11", _MATULA_URL, "J. Phys. Chem. Ref. Data 8 (1979)", "Table 11", _MATULA_NOTES["ag"]),
    _rho("matula1979", "ag", "293", "1.587", _MATULA_SOURCE + ", Table 11", _MATULA_URL, "J. Phys. Chem. Ref. Data 8 (1979)", "Table 11", _MATULA_NOTES["ag"]),
    _rho("matula1979", "ag", "300", "1.629", _MATULA_SOURCE + ", Table 11", _MATULA_URL, "J. Phys. Chem. Ref. Data 8 (1979)", "Table 11", _MATULA_NOTES["ag"]),
    _rho("matula1979", "au", "273.15", "2.051", _MATULA_SOURCE + ", Table 5", _MATULA_URL, "J. Phys. Chem. Ref. Data 8 (1979)", "Table 5", _MATULA_NOTES["au"]),
    _rho("matula1979", "au", "293", "2.214", _MATULA_SOURCE + ", Table 5", _MATULA_URL, "J. Phys. Chem. Ref. Data 8 (1979)", "Table 5", _MATULA_NOTES["au"]),
    _rho("matula1979", "au", "300", "2.271", _MATULA_SOURCE + ", Table 5", _MATULA_URL, "J. Phys. Chem. Ref. Data 8 (1979)", "Table 5", _MATULA_NOTES["au"]),
    _rho("desai1984", "al", "273", "2.417", _DESAI_AL_SOURCE, _DESAI_AL_URL, "J. Phys. Chem. Ref. Data 13 (1984)", "Table 1", _DESAI_AL_NOTE),
    _rho("desai1984", "al", "293", "2.650", _DESAI_AL_SOURCE, _DESAI_AL_URL, "J. Phys. Chem. Ref. Data 13 (1984)", "Table 1", _DESAI_AL_NOTE),
    _rho("desai1984", "al", "300", "2.733", _DESAI_AL_SOURCE, _DESAI_AL_URL, "J. Phys. Chem. Ref. Data 13 (1984)", "Table 1", _DESAI_AL_NOTE),
    _rho("desai1984", "w", "273", "4.82", _DESAI_W_SOURCE, _DESAI_W_URL, "J. Phys. Chem. Ref. Data 13 (1984)", "Table 5", _DESAI_W_NOTE),
    _rho("desai1984", "w", "293", "5.28", _DESAI_W_SOURCE, _DESAI_W_URL, "J. Phys. Chem. Ref. Data 13 (1984)", "Table 5", _DESAI_W_NOTE),
    _rho("desai1984", "w", "300", "5.44", _DESAI_W_SOURCE, _DESAI_W_URL, "J. Phys. Chem. Ref. Data 13 (1984)", "Table 5", _DESAI_W_NOTE),
    _eps("corning7980.pp_5_07ghz", "Corning 7980 fused silica", "parallel-plate dielectric resonator", "5.07", "3.84", "0.005", "Table 4.8 (glass specimens)",
         ("permittivity of fused silica", "fused silica permittivity"), _TN_7980),
    _eps("corning7980.split_cavity_8_85ghz", "Corning 7980 fused silica", "split cavity", "8.85", "3.827", "0.01", "Table 4.8 (glass specimens)",
         ("permittivity of fused silica", "fused silica permittivity"), _TN_7980),
    _eps("ptfe.pp_9_93ghz", "PTFE", "parallel-plate dielectric resonator", "9.93", "2.05", "0.005", "Table 4.9 (plastic specimens)", ("permittivity of ptfe", "ptfe permittivity", "teflon permittivity")),
    _eps("ptfe.te01_9_816ghz", "PTFE", "60 mm TE01 cavity resonator", "9.816", "2.055", "0.01", "Table 4.9 (plastic specimens)", ("permittivity of ptfe", "ptfe permittivity", "teflon permittivity")),
    _eps("pmma.pp_5_721ghz", "PMMA", "parallel-plate dielectric resonator", "5.721", "2.634", "0.005", "Table 4.9 (plastic specimens)", ("permittivity of pmma", "pmma permittivity", "acrylic permittivity")),
    _eps("sapphire.parallel_c_12_4ghz", "sapphire (Al2O3), parallel to the c-axis", "whispering-gallery mode resonator", "12.4", "11.58", "0.001", "Table 4.11 (noncubic single crystals)",
         ("permittivity of sapphire", "sapphire permittivity", "permittivity of alumina"), ("The parallel-plate column prints the same 11.58 at 10.0 GHz.",)),
    _eps("sapphire.perp_c_12_4ghz", "sapphire (Al2O3), perpendicular to the c-axis", "whispering-gallery mode resonator", "12.4", "9.40", "0.001", "Table 4.11 (noncubic single crystals)",
         ("permittivity of sapphire", "sapphire permittivity", "permittivity of alumina")),
    _eps("quartz.perp_c_7_75ghz", "crystalline quartz, perpendicular to the c-axis", "parallel-plate dielectric resonator", "7.75", "4.59", "0.005", "Table 4.11 (noncubic single crystals)", ("permittivity of quartz", "quartz permittivity")),
    _eps("quartz.parallel_c_9_03ghz", "crystalline quartz, parallel to the c-axis", "parallel-plate dielectric resonator", "9.03", "4.443", "0.005", "Table 4.11 (noncubic single crystals)", ("permittivity of quartz", "quartz permittivity")),
    _eps("rutile.parallel_c_4_2ghz", "rutile (TiO2), parallel to the c-axis", "whispering-gallery mode resonator", "4.2", "163.7", "0.001", "Table 4.11 (noncubic single crystals)", ("permittivity of rutile", "rutile permittivity")),
    _eps("rutile.perp_c_4_2ghz", "rutile (TiO2), perpendicular to the c-axis", "whispering-gallery mode resonator", "4.2", "85.6", "0.001", "Table 4.11 (noncubic single crystals)", ("permittivity of rutile", "rutile permittivity")),
)


_DESI_BAO_ROWS = (
    # tracer key, printed tracer, z_eff, DV/rd, DM/rd, DH/rd (value, sigma) as printed in Table IV
    ("bgs", "BGS", "0.295", ("7.942", "0.075"), None, None),
    ("lrg1", "LRG1", "0.510", ("12.720", "0.099"), ("13.588", "0.167"), ("21.863", "0.425")),
    ("lrg2", "LRG2", "0.706", ("16.050", "0.110"), ("17.351", "0.177"), ("19.455", "0.330")),
    ("lrg3_elg1", "LRG3+ELG1", "0.934", ("19.721", "0.091"), ("21.576", "0.152"), ("17.641", "0.193")),
    ("elg2", "ELG2", "1.321", ("24.252", "0.174"), ("27.601", "0.318"), ("14.176", "0.221")),
    ("qso", "QSO", "1.484", ("26.055", "0.398"), ("30.512", "0.760"), ("12.817", "0.516")),
    ("lya", "Lya", "2.330", ("31.267", "0.256"), ("38.988", "0.531"), ("8.632", "0.101")),
)
_DESI_BAO_NAMES = {
    "dv": ("D_V/r_d", "angle-averaged BAO distance over the sound horizon"),
    "dm": ("D_M/r_d", "transverse comoving BAO distance over the sound horizon"),
    "dh": ("D_H/r_d", "Hubble BAO distance c/H(z) over the sound horizon"),
}
_DESI_BAO_NOTES = (
    "Table IV gives the mean and standard deviation of the marginalized posterior; the systematic error budget is included.",
    "Table IV also prints correlation coefficients (r_V,M/H and r_M,H) between quantities of the same row; they are not stored, so each record stands alone without its covariance.",
    "These are the baseline rows used for cosmology. Table IV's separate LRG3 and ELG1 rows, which the combined LRG3+ELG1 row supersedes, are not stored.",
)


def _desi_bao() -> tuple[Quantity, ...]:
    out = []
    for key, tracer, z, *cols in _DESI_BAO_ROWS:
        for (q, pair) in zip(("dv", "dm", "dh"), cols):
            if pair is None:
                continue
            symbol, what = _DESI_BAO_NAMES[q]
            out.append(_q(f"desi_dr2.bao.{key}.{q}_rd", f"BAO distance {symbol}, DESI DR2 {tracer} at z_eff = {z} ({what})", symbol, pair[0], pair[1], "",
                          kind="standard uncertainty", source=f"{DESI_DR2_SOURCE} Table IV, {tracer} row (z_eff = {z}).", edition="DESI DR2 BAO, Table IV",
                          url="https://doi.org/10.1103/tr6y-kpc6", retrieved_from="https://arxiv.org/e-print/2503.14738",
                          keys=("desi", "bao"), phrases=("bao distance", "baryon acoustic oscillation distance", f"desi {tracer.lower()}", "desi bao"),
                          notes=(f"Printed as {pair[0]} +- {pair[1]} at z_eff = {z}.",) + _DESI_BAO_NOTES))
    return tuple(out)


DESI_DR2_BAO: tuple[Quantity, ...] = _desi_bao()


_BX_PHASE2 = "Borexino Collaboration, M. Agostini et al., First simultaneous precision spectroscopy of pp, 7Be, and pep solar neutrinos with Borexino Phase-II, Phys. Rev. D 100, 082004 (2019), doi:10.1103/PhysRevD.100.082004, arXiv:1707.09279, Table II"
_BX_B8 = "Borexino Collaboration, M. Agostini et al., Improved measurement of 8B solar neutrinos with 1.5 kt y of Borexino exposure, Phys. Rev. D 101, 062001 (2020), doi:10.1103/PhysRevD.101.062001, arXiv:1709.00756, abstract"
_BX_CNO2020 = "Borexino Collaboration, M. Agostini et al., Experimental evidence of neutrinos produced in the CNO fusion cycle in the Sun, Nature 587, 577-582 (2020), doi:10.1038/s41586-020-2934-0, arXiv:2006.15115"
_BX_CNO2022 = "Borexino Collaboration, S. Appel et al., Improved measurement of solar neutrinos from the carbon-nitrogen-oxygen cycle by Borexino and its implications for the Standard Solar Model, Phys. Rev. Lett. 129, 252701 (2022), doi:10.1103/PhysRevLett.129.252701, arXiv:2205.15975, abstract"
_BX_UNIT = "cm^-2 s^-1"
_BX_EDITION = {"1707.09279": "Phys. Rev. D 100 (2019)", "1709.00756": "Phys. Rev. D 101 (2020)"}
_BX_PHRASES = ("solar neutrino flux", "borexino", "solar neutrinos")
_BX_PHASE2_NOTE = ("The Phase-II table gives 'fluxes inferred assuming the MSW-LMA oscillation parameters'; the first error is statistical (likelihood profile under Wilks' approximation), the second systematic.",
                   "The same table also prints Standard Solar Model predictions (B16 GS98-HZ and AGSS09-LZ); those are model numbers and are not stored.")


def _bx(key, name, symbol, value, stat, syst, syst_low, src, arxiv, phrases, notes, stat_low=""):
    return _q(f"borexino.{key}", name, symbol, value, stat, _BX_UNIT, kind=_SPLIT_KIND, lower_text=stat_low, systematic_text=syst, systematic_lower_text=syst_low,
              source=src, edition=_BX_EDITION[arxiv],
              url="https://doi.org/" + src.split("doi:")[1].split(",")[0], retrieved_from=f"https://arxiv.org/e-print/{arxiv}",
              keys=("borexino", "solar neutrinos", "neutrino flux"), phrases=_BX_PHRASES + phrases, notes=notes)


BOREXINO: tuple[Quantity, ...] = (
    _bx("phase2.phi_pp", "pp solar neutrino flux at Earth, Borexino Phase-II", "Phi_pp", "6.1 e10", "0.5 e10", "0.3 e10", "0.5 e10", _BX_PHASE2, "1707.09279",
        ("pp neutrino flux", "pp solar neutrinos"), ("Printed as (6.1 +- 0.5 +0.3 -0.5) x 10^10 cm^-2 s^-1.",) + _BX_PHASE2_NOTE),
    _bx("phase2.phi_be7", "7Be solar neutrino flux at Earth (862 + 384 keV lines), Borexino Phase-II", "Phi_7Be", "4.99 e9", "0.11 e9", "0.06 e9", "0.08 e9", _BX_PHASE2, "1707.09279",
        ("7be neutrino flux", "beryllium-7 solar neutrinos"), ("Printed as (4.99 +- 0.11 +0.06 -0.08) x 10^9 cm^-2 s^-1.",) + _BX_PHASE2_NOTE),
    _bx("phase2.phi_pep_hz", "pep solar neutrino flux at Earth, Borexino Phase-II, CNO constrained to the high-metallicity SSM", "Phi_pep(HZ)", "1.27 e8", "0.19 e8", "0.08 e8", "0.12 e8", _BX_PHASE2, "1707.09279",
        ("pep neutrino flux",), ("Printed as (1.27 +- 0.19 +0.08 -0.12) x 10^8 cm^-2 s^-1 in the 'pep (HZ)' row; the pep result depends on the CNO rate assumed in the fit.",) + _BX_PHASE2_NOTE),
    _bx("phase2.phi_pep_lz", "pep solar neutrino flux at Earth, Borexino Phase-II, CNO constrained to the low-metallicity SSM", "Phi_pep(LZ)", "1.39 e8", "0.19 e8", "0.08 e8", "0.13 e8", _BX_PHASE2, "1707.09279",
        ("pep neutrino flux",), ("Printed as (1.39 +- 0.19 +0.08 -0.13) x 10^8 cm^-2 s^-1 in the 'pep (LZ)' row.",) + _BX_PHASE2_NOTE),
    _bx("b8.phi_es", "8B solar neutrino flux, equivalent flux assuming no flavour conversion, Borexino", "Phi_8B^ES", "2.57 e6", "0.17 e6", "0.07 e6", "", _BX_B8, "1709.00756",
        ("8b neutrino flux", "boron-8 solar neutrinos"),
        ("Printed as 2.57 +0.17 -0.18 (stat) +0.07 -0.07 (syst) x 10^6 cm^-2 s^-1, 'an observed solar neutrino flux assuming no neutrino flavor conversion', from electron recoils above 3 MeV.",
         "It is not the oscillation-corrected total 8B flux; the paper does not print one in the abstract. The same paper sets a hep flux limit of < 1.8 x 10^5 cm^-2 s^-1 (90% C.L.), not stored here."),
        stat_low="0.18 e6"),
    _q("borexino.cno2020.phi_cno", "CNO-cycle solar neutrino flux at Earth, Borexino 2020", "Phi_CNO", "7.0 e8", "3.0 e8", _BX_UNIT, lower_text="2.0 e8", kind="asymmetric, level not stated",
       source=_BX_CNO2020, edition="Nature 587 (2020)", url="https://doi.org/10.1038/s41586-020-2934-0", retrieved_from="https://arxiv.org/e-print/2006.15115",
       keys=("borexino", "solar neutrinos", "neutrino flux", "cno"), phrases=_BX_PHRASES + ("cno neutrino flux", "cno cycle neutrinos"),
       notes=("Printed as 7.0 +3.0 -2.0 x 10^8 cm^-2 s^-1, converted from the rate 7.2 +3.0 -1.7 cpd/100 t after folding in the systematic uncertainty, assuming MSW conversion.",
              "The paper calls its statistical-only interval 68% C.L. but does not name a level for the final folded interval, so none is assigned.",
              "Superseded by borexino.cno2022.phi_cno; both are kept.")),
    _q("borexino.cno2022.phi_cno", "CNO-cycle solar neutrino flux at Earth, Borexino Phase-III complete", "Phi_CNO", "6.6 e8", "2.0 e8", _BX_UNIT, lower_text="0.9 e8", kind="68% interval",
       source=_BX_CNO2022, edition="Phys. Rev. Lett. 129 (2022)", url="https://doi.org/10.1103/PhysRevLett.129.252701", retrieved_from="https://arxiv.org/e-print/2205.15975",
       keys=("borexino", "solar neutrinos", "neutrino flux", "cno"), phrases=_BX_PHRASES + ("cno neutrino flux", "cno cycle neutrinos"),
       notes=("Printed as 6.6 +2.0 -0.9 x 10^8 cm^-2 s^-1, converted from the rate 6.7 +2.0 -0.8 cpd/100 t, which the paper says is 'obtained from the 68% quantile of the likelihood profile including the systematic uncertainty'.",)),
)


_CODATA2017_SOURCE = ("D. B. Newell et al. (CODATA Task Group on Fundamental Constants), The CODATA 2017 values of h, e, k, and N_A for the revision of the SI, "
                      "Metrologia 55, L13-L16 (2018), doi:10.1088/1681-7575/aa950a")
_CODATA2017_URL = "https://doi.org/10.1088/1681-7575/aa950a"
_CODATA2017_PDF = "https://iopscience.iop.org/article/10.1088/1681-7575/aa950a/pdf"
_CODATA2017_NOTE = ("Table 1 lists it as a key input datum of the CODATA 2017 Special Adjustment, with the uncertainty in concise form and its relative standard uncertainty; "
                    "the original publication is the one named in the Source column.")


def _k_datum(key, ident, source_col, quantity_name, symbol, value, unc, unit, printed, rel, method, gas, phrases):
    gas_text = f", {gas} gas" if gas else ""
    return _q(f"codata2017.k_input.{key}", f"{quantity_name}, {ident} ({method}{gas_text})", symbol, value, unc, unit,
              kind="standard uncertainty", printed=printed, source=f"{_CODATA2017_SOURCE}, Table 1, row {source_col} ({ident})", edition="Metrologia 55 (2018)",
              url=_CODATA2017_URL, retrieved_from=_CODATA2017_PDF,
              keys=("boltzmann constant", "gas constant", "primary thermometry"), phrases=phrases + ("boltzmann constant determination", "pre-2019 boltzmann constant", "si redefinition"),
              notes=(f"Printed as {printed.replace(' e', ' x 10^')} {unit}, relative standard uncertainty {rel}.", _CODATA2017_NOTE,
                     f"Figure 2 of the same paper marks {ident} as {method}" + (f" in {gas}" if gas else "") + "."))


_AGT = ("acoustic gas thermometry", "molar gas constant measurement")
_R_UNIT = "J mol^-1 K^-1"

BOLTZMANN_PRE2019: tuple[Quantity, ...] = (
    _k_datum("nist88", "NIST-88", "Moldover et al (1988)", "molar gas constant", "R", "8.314 470", "0.000 015", _R_UNIT, "8.314 470(15)", "1.8 x 10^-6", "acoustic gas thermometry", "Ar", _AGT),
    _k_datum("lne09", "LNE-09", "Pitre et al (2009)", "molar gas constant", "R", "8.314 467", "0.000 023", _R_UNIT, "8.314 467(23)", "2.7 x 10^-6", "acoustic gas thermometry", "Ar", _AGT),
    _k_datum("npl10", "NPL-10", "Sutton et al (2010)", "molar gas constant", "R", "8.314 468", "0.000 026", _R_UNIT, "8.314 468(26)", "3.2 x 10^-6", "acoustic gas thermometry", "Ar", _AGT),
    _k_datum("lne11", "LNE-11", "Pitre et al (2011)", "molar gas constant", "R", "8.314 455", "0.000 012", _R_UNIT, "8.314 455(12)", "1.4 x 10^-6", "acoustic gas thermometry", "Ar", _AGT),
    _k_datum("lne15", "LNE-15", "Pitre et al (2015)", "molar gas constant", "R", "8.314 4615", "0.000 0084", _R_UNIT, "8.314 4615(84)", "1.0 x 10^-6", "acoustic gas thermometry", "He", _AGT),
    _k_datum("inrim15", "INRIM-15", "Gavioso et al (2015)", "molar gas constant", "R", "8.314 4743", "0.000 0088", _R_UNIT, "8.314 4743(88)", "1.1 x 10^-6", "acoustic gas thermometry", "He", _AGT),
    _k_datum("lne17", "LNE-17", "Pitre et al (2017)", "molar gas constant", "R", "8.314 4614", "0.000 0050", _R_UNIT, "8.314 4614(50)", "6.0 x 10^-7", "acoustic gas thermometry", "He", _AGT),
    _k_datum("npl17", "NPL-17", "Podesta et al (2017)", "molar gas constant", "R", "8.314 4603", "0.000 0058", _R_UNIT, "8.314 4603(58)", "7.0 x 10^-7", "acoustic gas thermometry", "Ar", _AGT),
    _k_datum("nim17", "NIM-17", "Feng et al (2017)", "molar gas constant", "R", "8.314 459", "0.000 017", _R_UNIT, "8.314 459(17)", "2.0 x 10^-6", "acoustic gas thermometry", "", _AGT),
    _k_datum("ptb17", "PTB-17", "Gaiser et al (2017)", "molar polarizability of 4He over the molar gas constant", "A_epsilon(4He)/R", "6.221 140 e-8", "0.000 012 e-8", "m^3 K J^-1",
             "6.221 140(12) e-8", "1.9 x 10^-6", "dielectric constant gas thermometry", "He", ("dielectric constant gas thermometry", "dcgt")),
    _k_datum("nim_nist17", "NIM/NIST-17", "Qu et al (2017)", "Boltzmann constant over the Planck constant", "k/h", "2.083 6630 e10", "0.000 0056 e10", "Hz K^-1",
             "2.083 6630(56) e10", "2.7 x 10^-6", "Johnson noise thermometry", "", ("johnson noise thermometry", "johnson noise")),
    _q("codata2017.k", "Boltzmann constant, CODATA 2017 Special Adjustment (before it was fixed)", "k", "1.380 649 03 e-23", "0.000 000 51 e-23", "J K^-1",
       kind="standard uncertainty", printed="1.380 649 03(51) e-23", source=f"{_CODATA2017_SOURCE}, Table 2", edition="Metrologia 55 (2018)",
       url=_CODATA2017_URL, retrieved_from=_CODATA2017_PDF, keys=("boltzmann constant",), phrases=("boltzmann constant determination", "pre-2019 boltzmann constant", "codata 2017 boltzmann constant"),
       notes=("Printed in Table 2 (adjusted values) as 1.380 649 03(51) x 10^-23 J K^-1, relative standard uncertainty 3.7 x 10^-7.",
              "Table 3 then gives the exact value 1.380 649 x 10^-23 J K^-1 recommended for the revised SI; that defining value is already on the board under the SI constants.")),
)

ELECTRON_MASS_PENNING: tuple[Quantity, ...] = (
    _q("sturm2014.m_e", "atomic mass of the electron from the g-factor of 12C5+ in a Penning trap", "A_r(e)", "0.000 548 579 909 067", "0.000 000 000 000 014", "u",
       kind=_SPLIT_KIND, systematic_text="0.000 000 000 000 009",
       source="S. Sturm, F. Koehler, J. Zatorski, A. Wagner, Z. Harman, G. Werth, W. Quint, C. H. Keitel, and K. Blaum, High-precision measurement of the atomic mass of the electron, Nature 506, 467-470 (2014), doi:10.1038/nature13026, arXiv:1406.5590, Eq. (5)",
       edition="Nature 506 (2014); arXiv v1", url="https://doi.org/10.1038/nature13026", retrieved_from="https://arxiv.org/pdf/1406.5590",
       keys=("electron mass", "penning trap"), phrases=("electron mass in u", "atomic mass of the electron", "penning trap", "penning-trap electron mass", "electron relative atomic mass"),
       notes=("Printed as m_e = 0.000 548 579 909 067(14)(9)(2) in atomic mass units. 'The first two errors are the statistical and systematic uncertainties of the measurement, while the third value represents the uncertainties of the theoretical prediction of the g-factor and the electron binding energies.'",
              "The split kind holds two parts, so the third (theory) part, 2 in the last digits, is kept in this note rather than in a number field.",
              "The paper quotes a relative precision of 3 x 10^-11 and notes the theory input assumes the correctness of bound-state QED.")),
)


_SME_SOURCE = ("V. A. Kostelecky and N. Russell, Data tables for Lorentz and CPT violation, Rev. Mod. Phys. 83, 11 (2011), doi:10.1103/RevModPhys.83.11, "
               "arXiv:0801.0287v19 (January 2026 edition)")
_SME_URL = "https://arxiv.org/abs/0801.0287v19"
_SME_FROM = "https://arxiv.org/e-print/0801.0287"
_SME_CONVENTION = ("Section II: 'each displayed sensitivity value represents our conservative estimate of a 2 sigma limit, given to the nearest order of magnitude, "
                   "on the modulus of the corresponding coefficient', with logarithmic rounding, and each entry assumes only that one coefficient is nonzero.")


def _sme(key, table, coefficient, symbol, species, upper, unit, phrases=()):
    who = f" for the {species}" if species else ""
    printed = upper.replace("1 e", "10^")
    return _q(f"sme2026.{key}", f"SME coefficient {coefficient}{who}: order of magnitude of the maximal attained two-sided sensitivity (2 sigma limit on the modulus)",
              f"|{symbol}| limit scale", upper, "", unit, kind="no uncertainty printed", source=f"{_SME_SOURCE}, Table {table}",
              edition="Data Tables for Lorentz and CPT Violation, 2026 edition (arXiv v19)", url=_SME_URL, retrieved_from=_SME_FROM,
              keys=("lorentz violation", "sme", "cpt violation", "null result"),
              phrases=("lorentz invariance", "lorentz violation", "sme coefficient", "lorentz-invariance limits", "null results") + phrases,
              notes=(f"Printed in Table {table} as {printed} {unit}".rstrip() + ".", _SME_CONVENTION,
                     "Because the entry is rounded to the nearest power of ten (a factor of 10^0.5 or more rounds up), it is stored as the printed order of magnitude, "
                     "not as a hard interval edge: the underlying 2 sigma limit can sit somewhat above or below it.",
                     "It is not a measured value of the coefficient; the data tables list the individual measurements."))


SME_LIMITS: tuple[Quantity, ...] = (
    *(_sme(f"matter.{sp}.b_{ax.lower()}", "S2", f"b~_{ax}", f"b~_{ax}({sp[0]})", name, up, "GeV", (f"{name} lorentz violation",))
      for sp, name, row in (("electron", "electron", ("1 e-31", "1 e-31", "1 e-29", "1 e-26")),
                            ("proton", "proton", ("1 e-32", "1 e-32", "1 e-29", "1 e-26")),
                            ("neutron", "neutron", ("1 e-33", "1 e-33", "1 e-30", "1 e-27")))
      for ax, up in zip(("X", "Y", "Z", "T"), row)),
    _sme("photon.k3_v00", "S3", "k_(V)00^(3) (isotropic, d = 3)", "k_(V)00^(3)", "", "1 e-44", "GeV", ("photon lorentz violation", "photon birefringence")),
    _sme("photon.k_tr", "S3", "kappa~_tr (d = 4)", "kappa~_tr", "", "1 e-20", "", ("photon lorentz violation", "isotropic speed of light")),
    _sme("photon.k4_e20", "S3", "k_(E)20^(4) (d = 4)", "k_(E)20^(4)", "", "1 e-35", "", ("photon lorentz violation", "vacuum birefringence")),
    _sme("neutrino.re_a_l_t_mutau", "S4", "Re (a_L)^T, mu-tau (d = 3)", "Re (a_L)^T_mutau", "", "1 e-24", "GeV", ("neutrino lorentz violation",)),
    _sme("gravity.electron.a_bar_t", "S5", "alpha a-bar_T (d = 3)", "alpha a-bar_T(e)", "electron", "1 e-13", "GeV", ("gravity lorentz violation",)),
    _sme("gravity.s_bar_tt", "S5", "s-bar^TT", "s-bar^TT", "", "1 e-5", "", ("gravity lorentz violation",)),
)

_POUND1960_SOURCE = "R. V. Pound and G. A. Rebka, Jr., Apparent weight of photons, Phys. Rev. Lett. 4, 337-341 (1960), doi:10.1103/PhysRevLett.4.337"
_POUND1960_FROM = "https://fisica.unipv.it/percorsi/pdf/rebka_1960.pdf"
_POUND1960_NOTE = ("Read from a scan of the printed letter hosted by the University of Pavia physics department (APS blocks the box); values checked against the page image.",)

POUND_REBKA_1960: tuple[Quantity, ...] = (
    _q("pound1960.net_shift", "net fractional frequency shift of the 14.4 keV 57Fe gamma ray, rising minus falling, Harvard tower (two-way 148 ft)", "Delta nu/nu",
       "-5.13 e-15", "0.51 e-15", "", kind="uncertainty as printed, level not stated", source=_POUND1960_SOURCE + ", p. 340", edition="Phys. Rev. Lett. 4 (1960)",
       url="https://doi.org/10.1103/PhysRevLett.4.337", retrieved_from=_POUND1960_FROM,
       keys=("gravitational redshift", "pound-rebka"), phrases=("gravitational redshift", "pound rebka", "pound-rebka", "pound-rebka 1960", "redshift test"),
       notes=("Printed as 'a net fractional shift, -(5.13 +- 0.51) x 10^-15. The error assigned is the rms statistical deviation including that of independent sensitivity calibrations'.",
              "The paper compares it with its own predicted value for the two-way height difference; that prediction is not stored.") + _POUND1960_NOTE),
    _q("pound1960.redshift_ratio", "measured over predicted gravitational shift of the 14.4 keV 57Fe line, Pound-Rebka 1960", "(Delta nu)_exp/(Delta nu)_theor",
       "1.05", "0.10", "", kind="uncertainty as printed, level not stated", source=_POUND1960_SOURCE + ", p. 340", edition="Phys. Rev. Lett. 4 (1960)",
       url="https://doi.org/10.1103/PhysRevLett.4.337", retrieved_from=_POUND1960_FROM,
       keys=("gravitational redshift", "pound-rebka"), phrases=("gravitational redshift", "pound rebka", "pound-rebka", "pound-rebka 1960", "redshift test"),
       notes=("Printed as (Delta nu)_exp/(Delta nu)_theor = +1.05 +- 0.10, 'where the plus sign indicates that the frequency increases in falling, as expected'.",
              "This ratio is the paper's own printed result; no comparison is made by this system. Superseded by pound1965.redshift_ratio (Pound and Snider).") + _POUND1960_NOTE),
)


_KLZ_SOURCE = "KamLAND-Zen Collaboration, S. Abe et al., Search for the Majorana nature of neutrinos in the inverted mass ordering region with KamLAND-Zen, Phys. Rev. Lett. 130, 051801 (2023), doi:10.1103/PhysRevLett.130.051801, arXiv:2203.02139, abstract"
_LZ_SOURCE = "LZ Collaboration, J. Aalbers et al., Dark matter search results from 4.2 tonne-years of exposure of the LUX-ZEPLIN (LZ) experiment, Phys. Rev. Lett. 135, 011802 (2025), doi:10.1103/4dyc-z8zf, arXiv:2410.17036, abstract"
_CAST_SOURCE = "CAST Collaboration, V. Anastassopoulos et al., New CAST limit on the axion-photon interaction, Nature Phys. 13, 584-590 (2017), doi:10.1038/nphys4109, arXiv:1705.02290, abstract"
_EOTWASH_SOURCE = "J. G. Lee, E. G. Adelberger, T. S. Cook, S. M. Fleischer, and B. R. Heckel, New test of the gravitational 1/r^2 law at separations down to 52 um, Phys. Rev. Lett. 124, 101101 (2020), doi:10.1103/PhysRevLett.124.101101, arXiv:2002.11761, abstract"
_FILZINGER_SOURCE = "M. Filzinger, S. Dorscher, R. Lange, J. Klose, M. Steinel, E. Benkler, E. Peik, C. Lisdat, and N. Huntemann, Improved limits on the coupling of ultralight bosonic dark matter to photons from optical atomic clock comparisons, Phys. Rev. Lett. 130, 253001 (2023), doi:10.1103/PhysRevLett.130.253001, arXiv:2301.03433"

NULL_B13_BOUNDS: tuple[Bound, ...] = (
    Bound(id="bound.kamlandzen2023.xe136_0vbb", name="half-life of neutrinoless double-beta decay of 136Xe", symbol="T_1/2^0nu(136Xe)",
          lower_text="2.3 e26", upper_text="", unit="yr", source=_KLZ_SOURCE, edition="Phys. Rev. Lett. 130 (2023)",
          url="https://doi.org/10.1103/PhysRevLett.130.051801", retrieved_from="https://arxiv.org/e-print/2203.02139", retrieved=RETRIEVED,
          keys=("double beta decay", "majorana neutrino", "kamland-zen", "null result"),
          phrases=("double-beta", "double beta", "neutrinoless double beta decay", "0vbb half-life", "kamland-zen", "null results", "experimental bounds"),
          conditions=("Printed as T_1/2^0nu > 2.3 x 10^26 yr at 90% C.L., from 970 kg yr of 136Xe exposure (KamLAND-Zen 400 and 800 combined).",
                      "This is a lower limit only. No upper end exists, and a longer half-life is allowed.",
                      "The abstract's conversion to effective Majorana mass limits (36-156 meV) depends on nuclear matrix elements and is not stored."), forbids=()),
    _null_bound("bound.lz2025.wimp_si_40gev", "spin-independent WIMP-nucleon cross section at a WIMP mass of 40 GeV/c^2", "sigma_SI(40 GeV)", "2.2 e-48", "cm^2",
                source=_LZ_SOURCE, edition="Phys. Rev. Lett. 135 (2025)", url="https://doi.org/10.1103/4dyc-z8zf", retrieved_from="https://arxiv.org/e-print/2410.17036",
                keys=("dark matter", "wimp", "lz"), phrases=("wimp", "dark matter cross section", "wimp-nucleon cross section", "lux-zeplin"),
                conditions=("Printed as 'the strongest SI exclusion set is 2.2 x 10^-48 cm^2 at the 90% confidence level ... for a mass of 40 GeV/c^2', from 4.2 tonne-years of exposure.",
                            "The limit is a curve in WIMP mass; only its strongest point is stored. The median sensitivity 5.1 x 10^-48 cm^2 is not stored.")),
    _null_bound("bound.cast2017.g_agamma", "axion-photon coupling", "g_a gamma", "0.66 e-10", "GeV^-1",
                source=_CAST_SOURCE, edition="Nature Phys. 13 (2017)", url="https://doi.org/10.1038/nphys4109", retrieved_from="https://arxiv.org/e-print/1705.02290",
                keys=("axion", "cast"), phrases=("axion", "axion-photon coupling", "cast helioscope"),
                conditions=("Printed as g_a gamma < 0.66 x 10^-10 GeV^-1 (95% C.L.), from the 2013-2015 solar data; 'this bound applies for m_a <~ 0.02 eV'.",)),
    _null_bound("bound.eotwash2020.yukawa_range", "range of a gravitational-strength (|alpha| = 1) Yukawa interaction", "lambda(|alpha|=1)", "38.6", "um",
                source=_EOTWASH_SOURCE, edition="Phys. Rev. Lett. 124 (2020)", url="https://doi.org/10.1103/PhysRevLett.124.101101", retrieved_from="https://arxiv.org/e-print/2002.11761",
                keys=("inverse-square law", "fifth force", "eot-wash", "short-range gravity"), phrases=("fifth force", "eot-wash", "inverse-square law test", "yukawa range"),
                conditions=("Printed as 'limiting with 95% confidence any gravitational-strength Yukawa interactions to ranges < 38.6 um', torsion balance at 52 um to 3.0 mm separations.",
                            "The full 2 sigma exclusion is a curve in (lambda, |alpha|); only the |alpha| = 1 crossing is stored.")),
    _null_bound("bound.pdg2026.q_p_plus_q_e", "sum of proton and electron charges (charge equality)", "|q_p + q_e|/e", "1 e-21", "",
                source="Particle Data Group, Review of Particle Physics, 2026 edition, p summary |q_p+q_e|/e (PDG id S016DQ), from G. Bressi et al., Phys. Rev. A 83, 052101 (2011), doi:10.1103/PhysRevA.83.052101 (neutrality of SF6).",
                edition="PDG 2026, S016DQ", url="https://pdg.lbl.gov/2026/listings/contents_listings.html", retrieved_from=PDG_2026_API,
                keys=("charge equality", "charge conservation"), phrases=("charge equality", "proton electron charge equality", "neutrality of matter"),
                conditions=("PDG prints the summary as < 1E-21 with the label BEST LIMIT. The PDG record gives no confidence level for it.",)),
    _null_bound("bound.pdg2026.q_eplus_plus_q_eminus", "sum of positron and electron charges", "|q(e+) + q(e-)|/e", "4 e-8", "",
                source="Particle Data Group, Review of Particle Physics, 2026 edition, e summary |q(e+)+q(e-)|/e (PDG id S003DQ).",
                edition="PDG 2026, S003DQ", url="https://pdg.lbl.gov/2026/listings/contents_listings.html", retrieved_from=PDG_2026_API,
                keys=("charge equality", "cpt"), phrases=("charge equality", "positron electron charge equality"),
                conditions=("PDG prints the summary as < 4E-8 with the label BEST LIMIT. The PDG record gives no confidence level for it.",)),
    Bound(id="bound.pdg2026.n_nbar_free", name="mean time for free neutron-antineutron transition", symbol="tau(n -> nbar)",
          lower_text="8.6 e7", upper_text="", unit="s",
          source="Particle Data Group, Review of Particle Physics, 2026 edition, n summary 'Mean Time for n nbar Transition' (PDG id S017NAN), from M. Baldo-Ceolin et al., Z. Phys. C 63, 409 (1994), doi:10.1007/BF01580321 (reactor free neutrons).",
          edition="PDG 2026, S017NAN", url="https://pdg.lbl.gov/2026/listings/contents_listings.html", retrieved_from=PDG_2026_API, retrieved=RETRIEVED,
          keys=("neutron-antineutron", "baryon number violation", "null result"),
          phrases=("neutron-antineutron", "neutron antineutron oscillation", "n-nbar oscillation time", "null results", "experimental bounds"),
          conditions=("PDG prints the summary as > 8.6E7 s, BEST LIMIT, at 90% CL, from free reactor neutrons.",
                      "This is a lower limit only. No upper end exists, and a longer transition time is allowed.",
                      "PDG also lists bound-neutron limits that depend on nuclear-suppression factors, such as Super-Kamiokande 2021 > 4.7E8 s for neutrons bound in oxygen; those are not stored."), forbids=()),
)

NULL_B13: tuple[Quantity, ...] = (
    _q("filzinger2023.alpha_dot", "linear drift of the fine-structure constant from Yb+ E3/E2 optical clock comparisons", "(1/alpha) d alpha/dt", "1.8 e-19", "2.5 e-19", "yr^-1",
       kind="uncertainty as printed, level not stated", source=_FILZINGER_SOURCE, edition="Phys. Rev. Lett. 130 (2023)", url="https://doi.org/10.1103/PhysRevLett.130.253001",
       retrieved_from="https://arxiv.org/e-print/2301.03433",
       keys=("fine-structure constant", "optical clocks", "null result"), phrases=("alpha drift", "variation of the fine-structure constant", "alpha dot", "drift of alpha"),
       notes=("Printed as (1/alpha) d alpha/dt = 1.8(2.5) x 10^-19 /yr, from about 235 days of nu_E3/nu_E2 data (2020-2022) combined with the 2016-2020 data; the paper calls it compatible with zero.",
              "The same paper prints (c^2/alpha) d alpha/d Phi = -2.4(3.0) x 10^-9 for coupling to the solar gravitational potential; that is stored as filzinger2023.alpha_phi.")),
    _q("filzinger2023.alpha_phi", "coupling of the fine-structure constant to the solar gravitational potential, Yb+ clocks", "(c^2/alpha) d alpha/d Phi", "-2.4 e-9", "3.0 e-9", "",
       kind="uncertainty as printed, level not stated", source=_FILZINGER_SOURCE, edition="Phys. Rev. Lett. 130 (2023)", url="https://doi.org/10.1103/PhysRevLett.130.253001",
       retrieved_from="https://arxiv.org/e-print/2301.03433",
       keys=("fine-structure constant", "optical clocks", "null result"), phrases=("variation of the fine-structure constant", "alpha gravitational potential coupling"),
       notes=("Printed as (c^2/alpha) d alpha/d Phi = -2.4(3.0) x 10^-9; 'both values are compatible with zero'.",)),
    _pdg("pdg2026.null.n_charge", "electric charge of the neutron", "q_n", "-0.2 e-21", "0.8 e-21", "e", node="S017Q",
         keys=("neutron", "charge equality", "null result"), phrases=("neutron charge", "charge equality", "neutrality of the neutron"),
         notes=("PDG 2026 prints the summary as -0.2 +- 0.8 (x 10^-21 e), OUR AVERAGE of Bressi 2011 (SF6 neutrality, -0.1 +- 1.1) and Baumann 1988 (cold-neutron deflection, -0.4 +- 1.1).",)),
)


_FIELDS2020_SOURCE = "B. D. Fields, K. A. Olive, T.-H. Yeh, and C. Young, Big-bang nucleosynthesis after Planck, JCAP 03 (2020) 010, doi:10.1088/1475-7516/2020/03/010, arXiv:1912.01132, table 'Constraints on the baryon-to-photon ratio'"
_KIDS_SOURCE = "KiDS Collaboration, M. Asgari et al., KiDS-1000 cosmology: cosmic shear constraints and comparison between two point statistics, Astron. Astrophys. 645, A104 (2021), doi:10.1051/0004-6361/202039070, arXiv:2007.15633"
_DESY3_SHEAR = "DES Collaboration, A. Amon et al., Dark Energy Survey Year 3 results: cosmology from cosmic shear and robustness to data calibration, Phys. Rev. D 105, 023514 (2022), doi:10.1103/PhysRevD.105.023514, arXiv:2105.13543, Conclusions"
_DESY3_3X2 = "DES Collaboration, T. M. C. Abbott et al., Dark Energy Survey Year 3 results: cosmological constraints from galaxy clustering and weak lensing, Phys. Rev. D 105, 023520 (2022), doi:10.1103/PhysRevD.105.023520, arXiv:2105.13549, abstract"
_S8_NOTE = "S8 = sigma_8 (Omega_m/0.3)^0.5 inside flat LCDM. Planck 2018's S8 (planck2018.s_8 = 0.832 +- 0.013) is on the board too; the two sides are kept as printed and not reconciled."

COSMO_B13: tuple[Quantity, ...] = (
    _planck("planck2018.age", "age of the universe", "t_0", "13.797", "0.023", "Gyr", phrases=("age of the universe", "cosmic age"),
            notes=("Table 2 prints Age [Gyr] = 13.797 +- 0.023 in this column, and 13.787 +- 0.020 with BAO added.",)),
    _planck("planck2018.z_re", "redshift of reionization (midpoint)", "z_re", "7.67", "0.73", phrases=("reionization redshift", "reionization")),
    _q("planck2018.omega_k", "spatial curvature density parameter, Planck TT,TE,EE+lowE+lensing+BAO", "Omega_K", "0.0007", "0.0019", "",
       kind="68% interval", source=PLANCK_2018_SOURCE.replace(", Table 2.", ", Sect. 7.3 (curvature)."), edition="Planck 2018 VI, base-LCDM+Omega_K, TT,TE,EE+lowE+lensing+BAO",
       url=PLANCK_2018_URL, retrieved_from=PLANCK_2018_PDF, keys=_PLANCK_KEYS + ("curvature",), phrases=("omega_k", "curvature density", "spatial curvature", "flatness"),
       notes=("Printed as Omega_K = 0.0007 +- 0.0019 (68%, TT,TE,EE+lowE+lensing+BAO).",
              "The same section prints Omega_K = -0.0106 +- 0.0065 without BAO and a Planck-alone preference for closed models; those are not stored.")),
    _q("cooke2018.eta10", "baryon-to-photon ratio from primordial D/H and standard BBN", "eta_10", "5.931", "0.051", "",
       kind="uncertainty as printed, level not stated",
       source="R. J. Cooke, M. Pettini, and C. C. Steidel, One percent determination of the primordial deuterium abundance, Astrophys. J. 855, 102 (2018), doi:10.3847/1538-4357/aaab53, arXiv:1710.11129, Sect. 'Testing the Standard Model'",
       edition="ApJ 855 (2018)", url="https://doi.org/10.3847/1538-4357/aaab53", retrieved_from="https://arxiv.org/e-print/1710.11129",
       keys=_BBN_KEYS, phrases=("baryon-to-photon", "baryon to photon ratio", "eta10", "bbn baryon density"),
       notes=("Printed as 10^10 eta = eta_10 = 5.931 +- 0.051, 'which includes the uncertainty of the nuclear data', converted from (D/H)_P with the Marcucci 2016 d(p,gamma)3He rate.",)),
    _q("fields2020.eta10_bbn_d", "baryon-to-photon ratio from BBN + D/H (mean)", "eta_10", "6.148", "0.191", "",
       kind="uncertainty as printed, level not stated", source=_FIELDS2020_SOURCE, edition="JCAP 03 (2020)", url="https://doi.org/10.1088/1475-7516/2020/03/010",
       retrieved_from="https://arxiv.org/e-print/1912.01132", keys=_BBN_KEYS, phrases=("baryon-to-photon", "baryon to photon ratio", "eta10"),
       notes=("Printed in the row 'BBN+D' as mean eta_10 = 6.148 +- 0.191 (peak 6.145), marginalized over Y_p.",)),
    _q("fields2020.eta10_cmb", "baryon-to-photon ratio from the CMB alone (mean)", "eta_10", "6.104", "0.058", "",
       kind="uncertainty as printed, level not stated", source=_FIELDS2020_SOURCE, edition="JCAP 03 (2020)", url="https://doi.org/10.1088/1475-7516/2020/03/010",
       retrieved_from="https://arxiv.org/e-print/1912.01132", keys=_BBN_KEYS, phrases=("baryon-to-photon", "baryon to photon ratio", "eta10"),
       notes=("Printed in the row 'CMB-only' as mean eta_10 = 6.104 +- 0.058 (peak 6.104), from Planck 2018 chains.",)),
    _q("kids2021.s8", "S8 from KiDS-1000 cosmic shear (COSEBIs, fiducial)", "S_8", "0.759", "0.024", "", lower_text="0.021",
       kind="asymmetric, level not stated", source=_KIDS_SOURCE + ", abstract and Table 'Goodness of fit and S8 constraints'", edition="A&A 645 (2021)",
       url="https://doi.org/10.1051/0004-6361/202039070", retrieved_from="https://arxiv.org/e-print/2007.15633",
       keys=("weak lensing", "kids", "cosmology"), phrases=("weak lensing", "kids", "s8", "cosmic shear", "s8 tension"),
       notes=("Printed as S_8 = 0.759 +0.024 -0.021 'for our fiducial analysis'; the table column is 'S_8, best fit + PJ-HPD'. The abstract calls it in 3 sigma tension with Planck.",
              "The same table gives 0.758 +0.017 -0.026 as 'max + Marginal', called a 68% CI in the conclusions; it is not stored.", _S8_NOTE)),
    _q("desy3.s8_shear", "S8 from DES Y3 cosmic shear (fiducial, LCDM with free neutrino mass)", "S_8", "0.759", "0.025", "", lower_text="0.023",
       kind="68% interval", source=_DESY3_SHEAR, edition="Phys. Rev. D 105, 023514 (2022)", url="https://doi.org/10.1103/PhysRevD.105.023514",
       retrieved_from="https://arxiv.org/e-print/2105.13543", keys=("weak lensing", "des", "cosmology"), phrases=("weak lensing", "s8", "cosmic shear", "des y3", "s8 tension"),
       notes=("Printed as S_8 = 0.759 +0.025 -0.023 (0.755 best-fit) at 68% confidence limits.", _S8_NOTE)),
    _q("desy3.s8_3x2pt", "S8 from DES Y3 3x2pt (cosmic shear, galaxy-galaxy lensing, clustering)", "S_8", "0.776", "0.017", "", lower_text="0.017",
       kind="68% interval", source=_DESY3_3X2, edition="Phys. Rev. D 105, 023520 (2022)", url="https://doi.org/10.1103/PhysRevD.105.023520",
       retrieved_from="https://arxiv.org/e-print/2105.13549", keys=("weak lensing", "des", "cosmology"), phrases=("weak lensing", "s8", "3x2pt", "des y3", "s8 tension"),
       notes=("Printed as S_8 = 0.776 +0.017 -0.017 in LCDM, 'mean with 68% confidence limits'.", _S8_NOTE)),
)


QED_B13: tuple[Quantity, ...] = (
    _q("fee1993.ps_1s2s", "positronium 1 3S1 - 2 3S1 interval", "nu_1S-2S(Ps)", "1 233 607 216.4", "3.2", "MHz",
       kind="uncertainty as printed, level not stated", printed="1 233 607 216.4(3.2)",
       source="M. S. Fee, A. P. Mills Jr., S. Chu, E. D. Shaw, K. Danzmann, R. J. Chichester, and D. M. Zuckerman, Measurement of the positronium 1 3S1-2 3S1 interval by continuous-wave two-photon excitation, Phys. Rev. A 48, 192 (1993), doi:10.1103/PhysRevA.48.192, abstract",
       edition="Phys. Rev. A 48 (1993)", url="https://doi.org/10.1103/PhysRevA.48.192", retrieved_from="https://inspirehep.net/api/literature?q=doi%2010.1103/PhysRevA.48.192",
       keys=("positronium", "qed"), phrases=("positronium 1s-2s", "positronium spectroscopy", "ps 1s-2s"),
       notes=("Printed in the abstract as 1 233 607 216.4 +- 3.2 MHz, a 2.6 ppb uncertainty dominated by the Ps line center relative to the Te2 reference line.",)),
    _q("meyer2000.mu_1s2s", "muonium 1s-2s energy interval", "nu_1s-2s(Mu)", "2 455 528 941.0", "9.8", "MHz",
       kind="uncertainty as printed, level not stated", printed="2 455 528 941.0(9.8)",
       source="V. Meyer et al., Measurement of the 1s-2s energy interval in muonium, Phys. Rev. Lett. 84, 1136 (2000), doi:10.1103/PhysRevLett.84.1136, arXiv:hep-ex/9907013",
       edition="Phys. Rev. Lett. 84 (2000)", url="https://doi.org/10.1103/PhysRevLett.84.1136", retrieved_from="https://arxiv.org/e-print/hep-ex/9907013",
       keys=("muonium", "qed"), phrases=("muonium 1s-2s", "muonium spectroscopy", "mu 1s-2s"),
       notes=("Printed as 'The frequency separation of the states was determined to be 2 455 528 941.0(9.8) MHz'. The paper's theory value 2 455 528 935.4(1.4) MHz is not stored.",)),
    _q("patra2020.hd_plus_v0_9", "HD+ v=0 -> 9 overtone, spin-averaged frequency (experimental)", "nu_SA,exp(HD+)", "415 264 925 500.5", "1.2", "kHz",
       kind="uncertainty as printed, level not stated", printed="415 264 925 500.5(1.2)",
       source="S. Patra et al., Proton-electron mass ratio from laser spectroscopy of HD+ at the part-per-trillion level, Science 369, 1238 (2020), doi:10.1126/science.aba0453, arXiv:2204.10674",
       edition="Science 369 (2020)", url="https://doi.org/10.1126/science.aba0453", retrieved_from="https://arxiv.org/e-print/2204.10674",
       keys=("molecular hydrogen ion", "qed"), phrases=("hd+", "hd+ spectroscopy", "molecular ion spectroscopy"),
       notes=("Printed as nu_SA,exp = 415,264,925,500.5(0.4)exp(1.1)theo(1.2)total kHz; the total is stored. The theo part comes from theoretical hyperfine intervals used to remove the hyperfine shifts.",
              "The paper's derived proton-electron mass ratio is not stored.")),
    _q("vanderwerf2025.he3_2s_transition", "helium-3 2 3S -> 2 1S transition frequency", "nu(3He, 2 3S - 2 1S)", "192 504 914 418.96", "0.17", "kHz",
       kind="uncertainty as printed, level not stated", printed="192 504 914 418.96(17)",
       source="Y. van der Werf et al., Alpha and helion particle charge radius difference determined from quantum-degenerate helium, Science 388, 850 (2025), doi:10.1126/science.adj2462, arXiv:2306.02333",
       edition="arXiv:2306.02333v1 (published as Science 388, 850, 2025)", url="https://doi.org/10.1126/science.adj2462", retrieved_from="https://arxiv.org/e-print/2306.02333",
       keys=("helium", "qed"), phrases=("helium-3 spectroscopy", "helium isotope shift", "3he transition"),
       notes=("Printed in arXiv v1 as 192 504 914 418.96(17) kHz, measured in a quantum-degenerate 3He Fermi gas.",)),
    _q("vanderwerf2025.delta_r2", "helion-alpha squared charge radius difference", "r_h^2 - r_alpha^2", "1.0757", "0.0015", "fm^2",
       kind="uncertainty as printed, level not stated", printed="1.0757(15)",
       source="Y. van der Werf et al., Alpha and helion particle charge radius difference determined from quantum-degenerate helium, Science 388, 850 (2025), doi:10.1126/science.adj2462, arXiv:2306.02333",
       edition="arXiv:2306.02333v1 (published as Science 388, 850, 2025)", url="https://doi.org/10.1126/science.adj2462", retrieved_from="https://arxiv.org/e-print/2306.02333",
       keys=("helium", "nuclear charge radius", "qed"), phrases=("helium isotope shift", "3he-4he isotope shift", "charge radius difference"),
       notes=("Printed in arXiv v1 as delta r^2 = r^2(3He) - r^2(4He) = 1.0757(15) fm^2. That is the paper's own value from the 3He-4He isotope shift of this 3He line and the Rengelink 2018 4He line, with Pachucki 2017 QED theory; it is not recomputed here.",)),
)


_GRAVITY2019 = "GRAVITY Collaboration, R. Abuter et al., A geometric distance measurement to the Galactic center black hole with 0.3% uncertainty, Astron. Astrophys. 625, L10 (2019), doi:10.1051/0004-6361/201935656, arXiv:1904.05721"
_GRAVITY2018 = "GRAVITY Collaboration, R. Abuter et al., Detection of the gravitational redshift in the orbit of the star S2 near the Galactic centre massive black hole, Astron. Astrophys. 615, L15 (2018), doi:10.1051/0004-6361/201833718, arXiv:1807.09409, abstract"
_GRAVITY2022 = "GRAVITY Collaboration, R. Abuter et al., Mass distribution in the Galactic Center based on interferometric astrometry of multiple stellar orbits, Astron. Astrophys. 657, L12 (2022), doi:10.1051/0004-6361/202142465, arXiv:2112.07478"
_EHT_M87 = "Event Horizon Telescope Collaboration, First M87 Event Horizon Telescope Results. I. The Shadow of the Supermassive Black Hole, Astrophys. J. Lett. 875, L1 (2019), doi:10.3847/2041-8213/ab0ec7, arXiv:1906.11238, Table 1"
_EHT_SGRA = "Event Horizon Telescope Collaboration, First Sagittarius A* Event Horizon Telescope Results. I. The Shadow of the Supermassive Black Hole in the Center of the Milky Way, Astrophys. J. Lett. 930, L12 (2022), doi:10.3847/2041-8213/ac6674, arXiv:2311.08680, Table 'Measured Parameters of Sgr A*'"
_GC_KEYS = ("galactic center", "sgr a*", "black hole", "astrophysics")

ASTRO_B13: tuple[Quantity, ...] = (
    _q("gravity2019.r0", "distance to the Galactic Center (Sgr A*), S2 orbit", "R_0", "8178", "13", "pc",
       kind=_SPLIT_KIND, systematic_text="22", source=_GRAVITY2019 + ", abstract", edition="A&A 625 (2019)",
       url="https://doi.org/10.1051/0004-6361/201935656", retrieved_from="https://arxiv.org/e-print/1904.05721",
       keys=_GC_KEYS, phrases=("sgr a*", "galactic center distance", "distance to the galactic center", "r0"),
       notes=("Printed as R_0 = 8178 +- 13_stat. +- 22_sys. pc.",)),
    _q("gravity2019.m_bh", "mass of Sgr A*, S2 orbit (noise model fit)", "M_SgrA*", "4.152 e6", "0.014 e6", "M_sun",
       kind="uncertainty as printed, level not stated", source=_GRAVITY2019 + ", Table 1 (noise model fit)", edition="A&A 625 (2019)",
       url="https://doi.org/10.1051/0004-6361/201935656", retrieved_from="https://arxiv.org/e-print/1904.05721",
       keys=_GC_KEYS, phrases=("sgr a*", "sgr a* mass", "galactic center black hole mass"),
       notes=("Printed in Table 1 as mass [10^6 M_sun] = 4.152 +- 0.014 in the 'noise model fit' column, which matches the adopted R_0 = 8178 pc. The paper says these are formal fit errors from the error matrix.",)),
    _q("gravity2019.f_redshift", "S2 gravitational-redshift parameter f (2019 update)", "f_redshift", "1.04", "0.05", "",
       kind="uncertainty as printed, level not stated", source=_GRAVITY2019 + ", abstract", edition="A&A 625 (2019)",
       url="https://doi.org/10.1051/0004-6361/201935656", retrieved_from="https://arxiv.org/e-print/1904.05721",
       keys=_GC_KEYS + ("gravitational redshift",), phrases=("s2 redshift", "sgr a*", "gravitational redshift s2"),
       notes=("Printed as f_redshift = 1.04 +- 0.05, 'detected with a significance level of 20 sigma'. Here f = 0 is Newtonian and f = 1 is GR.",)),
    _q("gravity2018.f_redshift", "S2 gravitational redshift plus transverse Doppler parameter f", "f", "0.90", "0.09", "",
       kind=_SPLIT_KIND, systematic_text="0.15", source=_GRAVITY2018, edition="A&A 615 (2018)",
       url="https://doi.org/10.1051/0004-6361/201833718", retrieved_from="https://arxiv.org/e-print/1807.09409",
       keys=_GC_KEYS + ("gravitational redshift",), phrases=("s2 redshift", "sgr a*", "gravitational redshift s2", "s2 pericentre"),
       notes=("Printed as f = 0.90 +- 0.09|stat +- 0.15|sys. f = 0 and f = 1 are the Newtonian and GR limits; it is stored as printed, with no check made here.",)),
    _q("gravity2022.r0", "distance to the Galactic Center, four-star fit", "R_0", "8277", "9", "pc",
       kind="uncertainty as printed, level not stated", source=_GRAVITY2022 + ", Conclusions and Table 1", edition="A&A 657 (2022)",
       url="https://doi.org/10.1051/0004-6361/202142465", retrieved_from="https://arxiv.org/e-print/2112.07478",
       keys=_GC_KEYS, phrases=("sgr a*", "galactic center distance", "distance to the galactic center", "r0"),
       notes=("Printed as R_0 = (8277 +- 9) pc, 'statistical errors'. The text puts the systematics at about 30 pc; that approximate figure is not stored as an uncertainty.",)),
    _q("gravity2022.m_bh", "mass of Sgr A*, four-star fit (S2, S29, S38, S55)", "M_SgrA*", "4.297 e6", "0.012 e6", "M_sun",
       kind="standard uncertainty", source=_GRAVITY2022 + ", Conclusions, Table 1 and Fig. caption", edition="A&A 657 (2022)",
       url="https://doi.org/10.1051/0004-6361/202142465", retrieved_from="https://arxiv.org/e-print/2112.07478",
       keys=_GC_KEYS, phrases=("sgr a*", "sgr a* mass", "galactic center black hole mass"),
       notes=("Printed as M = (4.297 +- 0.012) x 10^6 M_sun, statistical. A figure caption calls 12,000 M_sun its 1 sigma uncertainty. The text puts the systematics at about 40,000 M_sun; that is not stored.",)),
    _q("eht2019.m87_ring_diameter", "M87* emission ring diameter", "d (M87*)", "42", "3", "microarcsecond",
       kind="uncertainty as printed, level not stated", source=_EHT_M87, edition="ApJL 875 (2019)",
       url="https://doi.org/10.3847/2041-8213/ab0ec7", retrieved_from="https://arxiv.org/e-print/1906.11238",
       keys=("event horizon telescope", "black hole", "m87*", "astrophysics"), phrases=("shadow", "m87* shadow", "black hole shadow", "eht ring diameter", "m87"),
       notes=("Printed as ring diameter d = 42 +- 3 uas. Paper I prints no separate shadow diameter for M87*; the ring diameter is the stored observable, 'consistent with expectations for the shadow of a Kerr black hole'.",)),
    _q("eht2019.m87_mass", "M87* black hole mass from the EHT ring (at 16.8 Mpc)", "M (M87*)", "6.5 e9", "0.7 e9", "M_sun",
       kind="68% interval", source=_EHT_M87, edition="ApJL 875 (2019)",
       url="https://doi.org/10.3847/2041-8213/ab0ec7", retrieved_from="https://arxiv.org/e-print/1906.11238",
       keys=("event horizon telescope", "black hole", "m87*", "astrophysics"), phrases=("m87* mass", "m87 black hole mass", "m87"),
       notes=("Printed as M = (6.5 +- 0.7) x 10^9 M_sun for the adopted distance 16.8 +- 0.8 Mpc. The 'systematic error refers to the 68% confidence level and is much larger than the statistical error of 0.2 x 10^9 M_sun'.",)),
    _q("eht2022.sgra_ring_diameter", "Sgr A* emission ring diameter", "d (Sgr A*)", "51.8", "2.3", "microarcsecond",
       kind="68% interval", source=_EHT_SGRA, edition="ApJL 930 (2022)",
       url="https://doi.org/10.3847/2041-8213/ac6674", retrieved_from="https://arxiv.org/e-print/2311.08680",
       keys=("event horizon telescope", "black hole", "sgr a*", "astrophysics"), phrases=("sgr a*", "sgr a* ring", "eht ring diameter"),
       notes=("Printed as Diameter, d = 51.8 +- 2.3 uas; the table notes say 'Stated uncertainties correspond to 68% credible intervals.'",)),
    _q("eht2022.sgra_shadow_diameter", "Sgr A* angular shadow diameter", "d_sh (Sgr A*)", "48.7", "7.0", "microarcsecond",
       kind="68% interval", source=_EHT_SGRA, edition="ApJL 930 (2022)",
       url="https://doi.org/10.3847/2041-8213/ac6674", retrieved_from="https://arxiv.org/e-print/2311.08680",
       keys=("event horizon telescope", "black hole", "sgr a*", "astrophysics"), phrases=("shadow", "sgr a* shadow", "black hole shadow", "sgr a*"),
       notes=("Printed as angular shadow diameter d_sh = 48.7 +- 7.0 uas, 'determined solely from EHT data'; 68% credible interval per the table notes.",)),
)


_JONES1984 = "F. E. Jones, Interpolation formulas for viscosity of six gases: air, nitrogen, carbon dioxide, helium, argon, and oxygen, NBS Technical Note 1186 (1984), Table 1 'Viscosity of Dry Air'"
_JONES1984_URL = "https://nvlpubs.nist.gov/nistpubs/Legacy/TN/nbstechnicalnote1186.pdf"
_JONES_KL = "Table 1's first and third groups are taken from Table III of J. Kestin and W. Leidenfrost, Physica 25, 1033 (1959), an absolute oscillating-disk determination."
_JONES_DK = "Table 1's second and fourth groups are taken from Table II of R. DiPippo and J. Kestin, Proc. 4th Symp. Thermophysical Properties (ASME, 1968)."
_BERG2012 = "R. F. Berg and M. R. Moldover, Recommended viscosities of 11 dilute gases at 25 C, J. Phys. Chem. Ref. Data 41, 043104 (2012), doi:10.1063/1.4765368, Table 1(A)"
_BERG_NOTE = "Table 1(A) gives eta_0, the viscosity at 25 C and zero density, from a fit of 235 measured viscosity ratios (18 instruments) anchored to the ab initio helium value; the uncertainties are standard (k = 1), already multiplied by sigma = 1.89."
_TEOS10 = "IOC, SCOR and IAPSO, The international thermodynamic equation of seawater - 2010: Calculation and use of thermodynamic properties, Intergovernmental Oceanographic Commission, Manuals and Guides No. 56, UNESCO (2010)"
_TEOS10_URL = "https://www.teos-10.org/pubs/TEOS-10_Manual.pdf"


def _air(id, t, p, eta, group_note):
    return _q(f"jones1984.{id}", f"measured viscosity of dry air at {t} C and {p} atm", "eta_meas(air)", eta, "", "ug/(cm s)",
              kind="no uncertainty printed", source=_JONES1984, edition="NBS TN 1186 (1984)", url=_JONES1984_URL, retrieved_from=_JONES1984_URL,
              keys=("air", "viscosity", "fluids"), phrases=("measured air viscosity", "viscosity of air", "air viscosity data"),
              notes=(f"Printed in Table 1 as t = {t} C, P = {p} atm, mu_meas. = {eta} ug/cm-s (1 ug/(cm s) = 0.1 uPa s).", group_note,
                     "Table 1 prints no per-point uncertainty; the text quotes Kestin and Leidenfrost's estimate of a final accuracy 'of the order of +-0.05%'."))


def _berg(id, gas, eta, u, extra=()):
    return _q(f"berg2012.{id}", f"viscosity of {gas} at 25 C and zero density", f"eta_0({gas})", eta, u, "uPa s",
              kind="standard uncertainty", source=_BERG2012, edition="J. Phys. Chem. Ref. Data 41 (2012)", url="https://doi.org/10.1063/1.4765368",
              retrieved_from="https://srd.nist.gov/jpcrdreprint/1.4765368.pdf", keys=("viscosity", "dilute gas", "fluids"),
              phrases=(f"viscosity of {gas.lower()}", "dilute gas viscosity", "noble gas viscosity") + extra,
              notes=(f"Printed in Table 1(A) as eta_0 = {eta} uPa s, u = {u} uPa s.", _BERG_NOTE))


FLUIDS_B14: tuple[Quantity, ...] = (
    _air("air_eta_20c_1atm", "20.00", "1.00", "181.94", _JONES_KL),
    _air("air_eta_20c_35atm", "20.00", "34.97", "187.70", _JONES_KL),
    _air("air_eta_23c_1atm", "23.44", "1.07", "183.75", _JONES_DK),
    _air("air_eta_25c_1atm", "25.00", "1.00", "184.62", _JONES_KL),
    _air("air_eta_50c_2atm", "49.91", "1.70", "197.25", _JONES_DK),
    _berg("eta_he", "Helium", "19.8253", "0.0002", ("viscosity of helium gas",)),
    _berg("eta_ne", "Neon", "31.7088", "0.0100"),
    _berg("eta_ar", "Argon", "22.5666", "0.0060"),
    _berg("eta_kr", "Krypton", "25.3062", "0.0080"),
    _berg("eta_xe", "Xenon", "23.0183", "0.0072"),
    _berg("eta_n2", "Nitrogen", "17.7494", "0.0048"),
    _q("teos10.s_so", "standard-ocean Reference Salinity", "S_SO", "35.165 04", "exact", "g/kg",
       kind="exact", source=_TEOS10 + ", Eqn. (2.4.1) and Sect. 2.6", edition="TEOS-10 Manual (2010)", url=_TEOS10_URL, retrieved_from=_TEOS10_URL,
       keys=("seawater", "teos-10", "salinity", "fluids"), phrases=("seawater", "teos-10", "reference salinity", "standard ocean"),
       notes=("Printed as S_SO = 35 u_PS = 35.165 04 g kg^-1, with u_PS = (35.165 04/35) g kg^-1. A sample of Practical Salinity 35 has Reference-Composition Salinity 'of precisely 35.165 04 g kg^-1' by definition.",
              "The manual cites Millero et al. (2008a) for an absolute uncertainty of +-0.007 g kg^-1 when this value is used as an estimate of the Absolute Salinity of Reference-Composition Seawater; the defined value itself is exact.")),
    _q("teos10.c_p0", "TEOS-10 conservative-temperature heat capacity c_p^0", "c_p^0", "3991.867 957 119 63", "exact", "J/(kg K)",
       kind="exact", source=_TEOS10 + ", Eqn. (3.3.3)", edition="TEOS-10 Manual (2010)", url=_TEOS10_URL, retrieved_from=_TEOS10_URL,
       keys=("seawater", "teos-10", "fluids"), phrases=("seawater", "teos-10", "conservative temperature"),
       notes=("Printed as 'We adopt the exact definition for c_p^0 to be the 15-digit value', c_p^0 = 3991.867 957 119 63 J kg^-1 K^-1, motivated by [h(S_SO, 25 C, 0) - h(S_SO, 0 C, 0)]/(25 K).",)),
    _q("teos10.latent_heat_standard_ocean", "latent heat of evaporation at the standard-ocean surface (TEOS-10)", "L_p^SA", "2 498 510", "", "J/kg",
       kind="no uncertainty printed", source=_TEOS10 + ", Table 3.39.1", edition="TEOS-10 Manual (2010)", url=_TEOS10_URL, retrieved_from=_TEOS10_URL,
       keys=("seawater", "teos-10", "fluids"), phrases=("seawater", "teos-10", "latent heat of evaporation of seawater"),
       notes=("Printed in Table 3.39.1, row 'Standard ocean' (S_A = 35.165 04 g/kg, t = 0 C, p = 0 dbar), as L_p^SA = 2 498 510 J kg^-1. It is a TEOS-10 computed reference value, from Eqn. (3.39.7), not a measurement.",)),
)

_MARTIN1973 = "D. L. Martin, Specific heat of copper, silver, and gold below 30 K, Phys. Rev. B 8, 5357 (1973), doi:10.1103/PhysRevB.8.5357, abstract (erratum Phys. Rev. B 10, 5239 (1974), not reached)"
_MARTIN_NOTE = "The abstract says: 'The error limits are 95% confidence limits from the statistical analysis and do not include possible systematic errors.' The data are automatic-calorimeter specific heats from 2.5 to 30 K, analysed with data from 0.4 to 3.0 K."


def _martin(id, name, symbol, value, unc, unit, metal, printed_line, extra_phrases=()):
    return _q(f"martin1973.{id}", name, symbol, value, unc, unit, kind="95% interval", source=_MARTIN1973, edition="Phys. Rev. B 8 (1973)",
              url="https://doi.org/10.1103/PhysRevB.8.5357", retrieved_from="https://api.openalex.org/works/doi:10.1103/PhysRevB.8.5357",
              keys=("specific heat", "calorimetry", "condensed matter", metal.lower()), phrases=extra_phrases + (f"{metal.lower()} specific heat",),
              notes=(f"Printed in the abstract as {printed_line}.", _MARTIN_NOTE))


DEBYE_B14: tuple[Quantity, ...] = (
    _martin("theta0_cu", "calorimetric low-temperature limiting Debye temperature of copper", "Theta_0^c(Cu)", "344.3", "0.2", "K", "Copper",
            "Theta_0^c = (344.3 +- 0.2) K", ("calorimetric debye", "debye temperature of copper", "debye temperature")),
    _martin("theta0_ag", "calorimetric low-temperature limiting Debye temperature of silver", "Theta_0^c(Ag)", "226.6", "0.2", "K", "Silver",
            "Theta_0^c = (226.6 +- 0.2) K", ("calorimetric debye", "debye temperature of silver", "debye temperature")),
    _martin("theta0_au", "calorimetric low-temperature limiting Debye temperature of gold", "Theta_0^c(Au)", "161.8", "0.2", "K", "Gold",
            "Theta_0^c = (161.8 +- 0.2) K", ("calorimetric debye", "debye temperature of gold", "debye temperature")),
    _martin("gamma_cu", "electronic specific-heat coefficient of copper", "gamma(Cu)", "0.691", "0.001", "mJ/(K^2 mol)", "Copper",
            "gamma = 165.0 +- 0.2 ucal/K^2 g atom (0.691 +- 0.001 mJ/K^2 g atom); the mJ form is stored", ("electronic specific heat", "sommerfeld coefficient")),
    _martin("gamma_ag", "electronic specific-heat coefficient of silver", "gamma(Ag)", "0.640", "0.001", "mJ/(K^2 mol)", "Silver",
            "gamma = 152.8 +- 0.2 ucal/K^2 g atom (0.640 +- 0.001 mJ/K^2 g atom); the mJ form is stored", ("electronic specific heat", "sommerfeld coefficient")),
    _martin("gamma_au", "electronic specific-heat coefficient of gold", "gamma(Au)", "0.689", "0.001", "mJ/(K^2 mol)", "Gold",
            "gamma = 164.7 +- 0.3 ucal/K^2 g atom (0.689 +- 0.001 mJ/K^2 g atom); the mJ form is stored", ("electronic specific heat", "sommerfeld coefficient")),
)

_CCMGK2 = "S. Wu et al., CCM.G-K2.2017: CIPM Key Comparison of Absolute Gravimeters, Final Report, Metrologia 57, 07002 (2020) Technical Supplement, doi:10.1088/0026-1394/57/1A/07002, Table 5 'The official KCRVs of g'"
_CCMGK2_PDF = "https://www.bipm.org/documents/20126/48150829/CCM.G-K2.2017.pdf"
_CCMGK2_NOTE = "Table 5 caption: 'The constant value 980 122 000.0 uGal is subtracted from the KCRVs. The uncertainty U_site = 2 sigma ... is the expanded uncertainty at 95% confidence. All gravity values refer to 1.25 m above the marker.' The stored value is the printed residual; the subtracted constant is kept in the symbol, not added here."


def _ccm(site, value, u):
    return _q(f"ccmgk2.kcrv_site{site}", f"key comparison reference value of g at NIM Changping site {site} (CCM.G-K2.2017), minus 980 122 000.0 uGal",
              "g_KCRV - 980 122 000.0 uGal", value, u, "uGal", kind="95% interval", source=_CCMGK2, edition="CCM.G-K2.2017 Final Report",
              url="https://doi.org/10.1088/0026-1394/57/1A/07002", retrieved_from=_CCMGK2_PDF,
              keys=("absolute gravity", "gravimetry", "mechanics", "key comparison"), phrases=("key comparison", "absolute gravimeter comparison", "kcrv", "free-fall acceleration"),
              notes=(f"Printed in Table 5 as site {site}: KCRV = {value} uGal, U_site(k=2) = {u} uGal.", _CCMGK2_NOTE,
                     "The comparison was held at the Changping campus of NIM, China, in October-November 2017; each gravimeter measured at 4 of the 9 sites, and the KCRVs come from a weighted least-squares adjustment."))


CCM_B14: tuple[Quantity, ...] = (
    _ccm("1", "575.1", "1.3"),
    _ccm("2", "568.9", "1.3"),
    _ccm("3", "579.0", "1.4"),
    _ccm("4", "575.6", "1.3"),
    _ccm("5", "581.1", "1.4"),
    _ccm("6", "649.6", "1.4"),
    _ccm("7", "641.9", "1.3"),
    _ccm("8", "653.9", "1.3"),
    _ccm("9", "647.3", "1.3"),
)

_BASE2022 = "BASE Collaboration, M. J. Borchert et al., A 16-parts-per-trillion measurement of the antiproton-to-proton charge-mass ratio, Nature 601, 53 (2022), doi:10.1038/s41586-021-04203-w, arXiv:2311.16006"
_TORRES2010 = "G. Torres, J. Andersen, and A. Gimenez, Accurate masses and radii of normal stars: modern results and applications, Astron. Astrophys. Rev. 18, 67 (2010), doi:10.1007/s00159-009-0025-1, arXiv:0908.2624, Table 'Observed parameters and derived quantities for 95 binary systems, with mean errors'"
_ASPLUND2021 = "M. Asplund, A. M. Amarsi, and N. Grevesse, The chemical make-up of the Sun: A 2020 vision, Astron. Astrophys. 653, A141 (2021), doi:10.1051/0004-6361/202140445, arXiv:2105.01661"


def _torres(id, system, star, value, unc, printed_row):
    return _q(f"torres2010.{id}", f"mass of {system} {star} (detached eclipsing binary)", f"M({system} {star})", value, unc, "M_sun",
              kind="uncertainty as printed, level not stated", source=_TORRES2010, edition="A&ARv 18 (2010)", url="https://doi.org/10.1007/s00159-009-0025-1",
              retrieved_from="https://arxiv.org/e-print/0908.2624", keys=("eclipsing binary", "stellar mass", "astrophysics"),
              phrases=("eclipsing binary", "eclipsing binary mass", "stellar mass", system.lower()),
              notes=(f"Printed in the table as {printed_row}. The table heading says 'with mean errors'; no confidence level is stated.",
                     "Torres et al. recomputed the masses from the original data with uniform constants, so they need not equal the discovery papers' values."))


def _asplund(id, name, symbol, value, unc, phrases, printed_line):
    return _q(f"asplund2021.{id}", name, symbol, value, unc, "", kind="uncertainty as printed, level not stated", source=_ASPLUND2021 + ", abstract",
              edition="A&A 653 (2021)", url="https://doi.org/10.1051/0004-6361/202140445", retrieved_from="https://arxiv.org/e-print/2105.01661",
              keys=("solar abundance", "sun", "astrophysics"), phrases=("solar abundance", "solar composition") + phrases,
              notes=(f"Printed as {printed_line}.",))


QED_ASTRO_B14: tuple[Quantity, ...] = (
    _q("base2022.pbar_p_qm_ratio", "antiproton-to-proton charge-to-mass ratio", "R_pbar,p,exp", "-1.000 000 000 003", "0.000 000 000 016", "",
       kind="68% interval", printed="-1.000 000 000 003(16)", source=_BASE2022, edition="Nature 601 (2022)", url="https://doi.org/10.1038/s41586-021-04203-w",
       retrieved_from="https://arxiv.org/e-print/2311.16006", keys=("antiproton", "cpt", "penning trap", "qed"),
       phrases=("antiproton", "antiproton to proton charge to mass ratio", "base q/m", "cpt test"),
       notes=("Printed as R_pbar,p,exp = -1.000 000 000 003 (16), with 'an experimental uncertainty of 16 p.p.t. (C.L. 0.68)'.",
              "Measured as the cyclotron-frequency ratio of an antiproton and an H- ion; the paper's derived WEP_cc limit is not stored.")),
    _torres("v3903sgr_a", "V3903 Sgr", "A", "27.27", "0.55", "V3903 Sgr A, O7V, 27.27 +- 0.55 M_sun"),
    _torres("v3903sgr_b", "V3903 Sgr", "B", "19.01", "0.44", "V3903 Sgr B, O9V, 19.01 +- 0.44 M_sun"),
    _torres("v1143cyg_a", "V1143 Cyg", "A", "1.388", "0.016", "V1143 Cyg A, F5V, 1.388 +- 0.016 M_sun"),
    _torres("v1143cyg_b", "V1143 Cyg", "B", "1.344", "0.013", "V1143 Cyg B, F5V, 1.344 +- 0.013 M_sun"),
    _torres("aiphe_a", "AI Phe", "A", "1.2336", "0.0045", "AI Phe A, K0IV, 1.2336 +- 0.0045 M_sun"),
    _torres("aiphe_b", "AI Phe", "B", "1.1934", "0.0041", "AI Phe B, F7V, 1.1934 +- 0.0041 M_sun"),
    _torres("ewori_a", "EW Ori", "A", "1.174", "0.012", "EW Ori A, G0V, 1.174 +- 0.012 M_sun"),
    _torres("ewori_b", "EW Ori", "B", "1.1238", "0.0089", "EW Ori B, G5V, 1.1238 +- 0.0089 M_sun"),
    _torres("cmdra_a", "CM Dra", "A", "0.23102", "0.00089", "CM Dra A, M4.5V, 0.23102 +- 0.00089 M_sun"),
    _torres("cmdra_b", "CM Dra", "B", "0.21409", "0.00083", "CM Dra B, M4.5V, 0.21409 +- 0.00083 M_sun"),
    _asplund("log_eps_c", "solar photospheric carbon abundance", "log eps(C)", "8.46", "0.04", ("carbon abundance",), "log eps(C) = 8.46 +- 0.04 (H = 12.00)"),
    _asplund("log_eps_n", "solar photospheric nitrogen abundance", "log eps(N)", "7.83", "0.07", ("nitrogen abundance",), "log eps(N) = 7.83 +- 0.07"),
    _asplund("log_eps_o", "solar photospheric oxygen abundance", "log eps(O)", "8.69", "0.04", ("oxygen abundance",), "log eps(O) = 8.69 +- 0.04"),
    _q("asplund2021.log_eps_fe", "solar photospheric iron abundance", "log eps(Fe)", "7.46", "0.04", "",
       kind="uncertainty as printed, level not stated", source=_ASPLUND2021 + ", Table 2 (photosphere column)", edition="A&A 653 (2021)",
       url="https://doi.org/10.1051/0004-6361/202140445", retrieved_from="https://arxiv.org/e-print/2105.01661",
       keys=("solar abundance", "sun", "astrophysics"), phrases=("solar abundance", "solar composition", "iron abundance"),
       notes=("Printed in the abundance table for Z = 26 as 7.46 +- 0.04 (photosphere); the CI-chondrite column, 7.46 +- 0.02, is not stored.",)),
    _asplund("x_surface", "present-day solar surface hydrogen mass fraction", "X_surface", "0.7438", "0.0054", ("solar mass fractions",), "X_surface = 0.7438 +- 0.0054"),
    _asplund("y_surface", "present-day solar surface helium mass fraction", "Y_surface", "0.2423", "0.0054", ("solar mass fractions",), "Y_surface = 0.2423 +- 0.0054"),
    _asplund("z_surface", "present-day solar surface metal mass fraction", "Z_surface", "0.0139", "0.0006", ("solar metallicity", "solar mass fractions"), "Z_surface = 0.0139 +- 0.0006"),
    _asplund("z_over_x", "present-day solar surface metal-to-hydrogen mass ratio", "Z_surface/X_surface", "0.0187", "0.0009", ("solar metallicity",), "Z_surface/X_surface = 0.0187 +- 0.0009"),
)

_HPL1972 = "C. Y. Ho, R. W. Powell, and P. E. Liley, Thermal conductivity of the elements, J. Phys. Chem. Ref. Data 1, 279 (1972), doi:10.1063/1.3253100"
_HPL1972_PDF = "https://srd.nist.gov/jpcrdreprint/1.3253100.pdf"
_MILLS1973 = "R. Mills, Self-diffusion in normal and heavy water in the range 1-45 deg, J. Phys. Chem. 77, 685 (1973), doi:10.1021/j100624a025"
_MILLS1973_PDF = "https://fenix.ciencias.ulisboa.pt/downloadFile/2533412229372806/Mills1973.pdf"


def _hpl(id, element, t, k, table, remark, extra=()):
    return _q(f"hpl1972.{id}", f"thermal conductivity of {element} at {t} K", f"k({element}, {t} K)", k, "", "W cm^-1 K^-1",
              kind="no uncertainty printed", source=f"{_HPL1972}, {table}", edition="J. Phys. Chem. Ref. Data 1 (1972)", url="https://doi.org/10.1063/1.3253100",
              retrieved_from=_HPL1972_PDF, keys=("thermal conductivity", f"{element.split()[0].lower()} thermal conductivity"),
              phrases=(f"thermal conductivity of {element.split()[0].lower()}", "thermal conductivity of solids") + extra,
              notes=(f"Printed in the table as T = {t}, k = {k} W cm^-1 K^-1 (read from the scanned reprint page image).", remark))


def _db98x(key, name, symbol, value, unit, where, printed, phrases):
    return _q(f"db1998.he4.{key}", f"liquid helium-4 at saturated vapour pressure: {name}", symbol, value, "", unit, kind="no uncertainty printed",
              source=f"{_DB98_SOURCE}, {where}", edition="J. Phys. Chem. Ref. Data 27 (1998)", url="https://doi.org/10.1063/1.556028", retrieved_from=_DB98_URL,
              keys=("helium-4", "superfluid helium"), phrases=phrases + ("superfluid helium", "helium ii", "liquid helium properties"),
              notes=(f"{where} prints {printed}. These are recommended values from spline fits to an adopted database; the tables print no uncertainty for them.",))


_CU_REMARK = "The table's remarks: values are for well-annealed high-purity copper and are considered accurate to within +-2% near room temperature and +-4% at low and high temperatures."
_AL_REMARK = "The table's remarks: values are for well-annealed high-purity aluminum, thought accurate to within +-5% below room temperature and +-2 to +-3% above."
_SI_REMARK = "The table's remarks: values for high-purity silicon at 300 K and above are recommended, accurate to within +-5% from 300 to 1000 K; values below 300 K are merely typical."
_DIA_REMARK = "The diamond table is headed 'Typical values'; its remarks say the three sets only represent typical curves indicating the general trend for the three diamond types."

TRANSPORT_B15: tuple[Quantity, ...] = (
    _hpl("k_cu_273", "copper", "273.2", "4.03", "Thermal conductivity of copper, recommended values", _CU_REMARK),
    _hpl("k_cu_300", "copper", "300", "4.01", "Thermal conductivity of copper, recommended values", _CU_REMARK),
    _hpl("k_al_273", "aluminum", "273.2", "2.36", "Thermal conductivity of aluminum, recommended values", _AL_REMARK, ("thermal conductivity of aluminium",)),
    _hpl("k_al_300", "aluminum", "300", "2.37", "Thermal conductivity of aluminum, recommended values", _AL_REMARK, ("thermal conductivity of aluminium",)),
    _hpl("k_si_300", "silicon", "300", "1.48", "Thermal conductivity of silicon, recommended values", _SI_REMARK),
    _hpl("k_diamond_i_273", "diamond type I", "273.2", "9.94", "Thermal conductivity of diamond, typical values", _DIA_REMARK),
    _hpl("k_diamond_iia_273", "diamond type IIa", "273.2", "26.2", "Thermal conductivity of diamond, typical values", _DIA_REMARK),
    _q("mills1973.d_hto_h2o_25c", "tracer diffusion coefficient of HTO in H2O at 25 C (diaphragm cell)", "D*(HTO in H2O, 25 C)", "2.236", "0.004", "1e-9 m^2/s",
       kind="uncertainty as printed, level not stated", source=_MILLS1973 + ", Table I", edition="J. Phys. Chem. 77 (1973)", url="https://doi.org/10.1021/j100624a025",
       retrieved_from=_MILLS1973_PDF, keys=("diffusion coefficient", "water self-diffusion"), phrases=("diffusion coefficient", "tracer diffusion of water", "self-diffusion of water"),
       notes=("Printed in Table I as 2.236 +- 0.004 (D* x 10^9 m^2 s^-1) at 25 C; the abstract says the results 'are considered to be probably accurate to +-0.2%'.",)),
    _q("mills1973.d_h2o_25c", "self-diffusion coefficient of pure H2O at 25 C", "D*(H2O, 25 C)", "2.299", "", "1e-9 m^2/s",
       kind="no uncertainty printed", source=_MILLS1973 + ", Table III", edition="J. Phys. Chem. 77 (1973)", url="https://doi.org/10.1021/j100624a025",
       retrieved_from=_MILLS1973_PDF, keys=("diffusion coefficient", "water self-diffusion"), phrases=("diffusion coefficient", "self-diffusion of water", "water self-diffusion coefficient"),
       notes=("Printed in Table III, 'Calculated Self-Diffusion Coefficients of H2O and D2O', as 2.299 (D* x 10^9 m^2 s^-1) at 25 C. Mills calculated it from his HTO data and Longsworth's HDO data; it is the paper's own value, not recomputed here.",)),
    _q("mills1973.d_d2o_25c", "self-diffusion coefficient of pure D2O at 25 C", "D*(D2O, 25 C)", "1.872", "", "1e-9 m^2/s",
       kind="no uncertainty printed", source=_MILLS1973 + ", Table III", edition="J. Phys. Chem. 77 (1973)", url="https://doi.org/10.1021/j100624a025",
       retrieved_from=_MILLS1973_PDF, keys=("diffusion coefficient", "heavy water self-diffusion"), phrases=("diffusion coefficient", "self-diffusion of heavy water"),
       notes=("Printed in Table III as 1.872 (D* x 10^9 m^2 s^-1) for D2O-D2O at 25 C, calculated by Mills as for H2O.",)),
    _db98x("viscosity_1p5k", "viscosity at 1.5 K", "eta(1.5 K)", "1.346 e-6", "Pa s", "Table 12.3", "T90 = 1.5 K, eta = 1.346E-06 Pa s", ("helium ii viscosity", "viscosity of liquid helium")),
    _db98x("viscosity_2p0k", "viscosity at 2.0 K", "eta(2.0 K)", "1.468 e-6", "Pa s", "Table 12.3", "T90 = 2.0 K, eta = 1.468E-06 Pa s", ("helium ii viscosity", "viscosity of liquid helium")),
    _db98x("viscosity_4p0k", "viscosity at 4.0 K (helium I)", "eta(4.0 K)", "3.319 e-6", "Pa s", "Table 12.3", "T90 = 4.0 K, eta = 3.319E-06 Pa s", ("viscosity of liquid helium", "helium i viscosity")),
    _db98x("mutual_friction_b_1p5k", "mutual friction coefficient B at 1.5 K", "B(1.5 K)", "1.296", "", "Table 11.3", "T90 = 1.50 K, B = 1.296", ("mutual friction",)),
    _db98x("mutual_friction_bprime_1p5k", "mutual friction coefficient B' at 1.5 K", "B'(1.5 K)", "0.317", "", "Table 11.3", "T90 = 1.50 K, B' = 0.317", ("mutual friction",)),
    _db98x("mutual_friction_b_1p8k", "mutual friction coefficient B at 1.8 K", "B(1.8 K)", "1.024", "", "Table 11.3", "T90 = 1.80 K, B = 1.024", ("mutual friction",)),
    _db98x("mutual_friction_bprime_1p8k", "mutual friction coefficient B' at 1.8 K", "B'(1.8 K)", "0.052", "", "Table 11.3", "T90 = 1.80 K, B' = 0.052", ("mutual friction",)),
)

_LEMOINE2013 = "F. G. Lemoine et al., High-degree gravity models from GRAIL primary mission data, J. Geophys. Res. Planets 118, 1676-1698 (2013), doi:10.1002/jgre.20118"
_KONOPLIV2013 = "A. S. Konopliv et al., The JPL lunar gravity field to spherical harmonic degree 660 from the GRAIL Primary Mission, J. Geophys. Res. Planets 118, 1415-1434 (2013), doi:10.1002/jgre.20097"
_WILLIAMS2014 = "J. G. Williams et al., Lunar interior properties from the GRAIL mission, J. Geophys. Res. Planets 119, 1546-1578 (2014), doi:10.1002/2013JE004559"
_CHEN2015 = "W. Chen, J. C. Li, J. Ray, W. B. Shen, and C. L. Huang, Consistent estimates of the dynamic figure parameters of the earth, J. Geod. 89, 179-188 (2015), doi:10.1007/s00190-014-0768-y"
_LUNAR_K = ("lunar love number", "measured love number", "love numbers", "grail")


def _lem13(m, value, unc, extra=""):
    return _q(f"lemoine2013.moon_k{m}", f"lunar Love number k{m} from GRAIL (GSFC GRGM660PRIM)", f"k_{m}(Moon)", value, unc, "",
              kind="standard uncertainty", source=_LEMOINE2013 + ", abstract", edition="J. Geophys. Res. Planets 118 (2013)", url="https://doi.org/10.1002/jgre.20118",
              retrieved_from="https://ntrs.nasa.gov/api/citations/20140010292/downloads/20140010292.pdf", keys=("lunar love number", "love number"), phrases=_LUNAR_K,
              notes=(f"Printed in the abstract as k{m} = {value} +- {unc}; 'the Love number error sigmas are those obtained with VCE' (variance-component estimation)." + extra,
                     "NTRS serves only the first page (title and abstract) of the article."))


def _chen15(key, name, symbol, value, printed):
    return _q(f"chen2015.earth_{key}", f"Earth's {name}", symbol, value, "9.6", "1e33 kg m^2", kind="uncertainty as printed, level not stated",
              source=_CHEN2015 + ", abstract and Sect. 3 (EGM-IERS model)", edition="J. Geod. 89 (2015), open access", url="https://doi.org/10.1007/s00190-014-0768-y",
              retrieved_from="https://link.springer.com/article/10.1007/s00190-014-0768-y", keys=("earth moment of inertia", "moment of inertia"),
              phrases=("moment of inertia", "earth moment of inertia", "principal moments of inertia", "dynamic figure parameters"),
              notes=(f"Printed as {printed} x 10^33 kg m^2 (comma as thousands separator); the paper's preferred values, 'the accuracies being limited by the uncertainties of G and e'.",))


MECHANICS_B15: tuple[Quantity, ...] = (
    _lem13("20", "0.024615", "0.0000914"),
    _lem13("21", "0.023915", "0.0000132"),
    _lem13("22", "0.024852", "0.0000167"),
    _lem13("30", "0.00734", "0.0015", " The abstract calls this 'a preliminary solution'."),
    _q("konopliv2013.moon_k2", "lunar Love number k2 from GRAIL (JPL GL0660B)", "k_2(Moon)", "0.02405", "0.00018", "",
       kind="uncertainty as printed, level not stated", source=_KONOPLIV2013 + ", abstract and Sect. 7", edition="J. Geophys. Res. Planets 118 (2013)",
       url="https://doi.org/10.1002/jgre.20097", retrieved_from="https://authors.library.caltech.edu/records/vdhyj-f3q68", keys=("lunar love number", "love number"), phrases=_LUNAR_K,
       notes=("Printed as k2 = 0.02405 +- 0.00018 ('GRAIL has now determined the Love number to better than 1%'). The GL0660B solution constrained k20, k21 and k22 to be equal.",
              "Lemoine et al. 2013 (GSFC) give separate k20, k21, k22; both are kept.")),
    _q("williams2014.moon_k2_mean", "lunar Love number k2, average of the JPL and GSFC GRAIL solutions", "k_2(Moon)", "0.02416", "0.00022", "",
       kind="uncertainty as printed, level not stated", source=_WILLIAMS2014 + ", abstract and Sect. 5", edition="J. Geophys. Res. Planets 119 (2014)",
       url="https://doi.org/10.1002/2013JE004559", retrieved_from="https://authors.library.caltech.edu/records/2vaje-qnn35", keys=("lunar love number", "love number"), phrases=_LUNAR_K,
       notes=("Printed as 0.02416 +- 0.00022 'at a 1 month period with reference radius R = 1738 km'; Sect. 5 calls it 'the unweighted average of the two values and their uncertainties'.",
              "The paper also prints 0.02422 +- 0.00022 for R = 1737.151 km; only the R = 1738 km value is stored.")),
    _q("williams2014.moon_is_mr2", "normalized mean moment of inertia of the solid Moon", "I_s/(M R^2)", "0.392728", "0.000012", "",
       kind="uncertainty as printed, level not stated", source=_WILLIAMS2014 + ", abstract", edition="J. Geophys. Res. Planets 119 (2014)",
       url="https://doi.org/10.1002/2013JE004559", retrieved_from="https://authors.library.caltech.edu/records/2vaje-qnn35", keys=("lunar moment of inertia", "moment of inertia"),
       phrases=("moment of inertia", "lunar moment of inertia", "moment of inertia factor"),
       notes=("Printed in the abstract as Is/MR2 = 0.392728 +- 0.000012, for gravity reference radius R = 1738 km. The paper also prints 0.393112 +- 0.000012 for R = 1737.151 km; only the first is stored.",)),
    _chen15("a", "principal moment of inertia A", "A", "80085.1", "(80,085.1 +- 9.6)"),
    _chen15("b", "principal moment of inertia B", "B", "80086.8", "(80,086.8 +- 9.6)"),
    _chen15("c", "principal (polar) moment of inertia C", "C", "80349.0", "(80,349.0 +- 9.6)"),
    _chen15("i_mean", "mean moment of inertia I = (A+B+C)/3", "I", "80173.6", "(80,173.6 +- 9.6)"),
)

def _asd_tp_query(spectrum: str, low: str, high: str) -> str:
    return (
        f"https://physics.nist.gov/cgi-bin/ASD/lines1.pl?spectra={spectrum.replace(' ', '+')}&output_type=0&low_w={low}&upp_w={high}&unit=1&de=0&format=2"
        "&line_out=0&remove_js=on&en_unit=0&output=0&bibrefs=1&page_size=15&show_obs_wl=1&show_calc_wl=1&unc_out=1&order_out=0&show_av=2"
        "&tsb_value=0&A_out=0&f_out=on&intens_out=on&allowed_out=1&forbid_out=1&conf_out=on&term_out=on&enrg_out=on&J_out=on&submit=Retrieve+Data"
    )


_ASD_ACC = {"AAA": "<= 0.3%", "AA": "<= 1%"}


def _tp(key, label, spectrum, low, high, upper, a_printed, a_value, f_printed, f_value, acc, tp_ref):
    query = _asd_tp_query(spectrum, low, high)
    src = ASD_SOURCE.replace("Ionization Energies Data.", f"Lines Data, {spectrum}.")
    note = (f"ASD row for {label}: Aki = {a_printed} s^-1, fik = {f_printed}, Acc = {acc}, tp_ref {tp_ref}.",
            f"ASD prints no numeric uncertainty, only the accuracy grade {acc}, which the ASD legend defines as {_ASD_ACC[acc]}.")
    common = dict(kind="no uncertainty printed", source=src, edition=ASD_EDITION + ", queried 2026-11-25", url=query, retrieved_from=query)
    return (
        _q(f"asd512.tp.{key}_a", f"Einstein A coefficient of the {label} transition", f"A({label})", a_value, "", "s^-1",
           keys=("transition probability", "einstein a coefficient"), phrases=("transition probability", "einstein a coefficient", f"{upper} decay rate"), notes=note, **common),
        _q(f"asd512.tp.{key}_f", f"absorption oscillator strength of the {label} transition", f"f({label})", f_value, "", "",
           keys=("oscillator strength", "absorption oscillator strength"), phrases=("oscillator strength", f"{upper} oscillator strength"), notes=note, **common),
    )


def _oa(doi: str) -> str:
    return f"https://api.openalex.org/works/doi:{doi}"


def _life(id, name, symbol, value, unc, kind, source, edition, doi, printed, extra=()):
    return _q(id, name, symbol, value, unc, "ns", kind=kind, source=source + ", abstract", edition=edition, url=f"https://doi.org/{doi}", retrieved_from=_oa(doi),
              keys=("radiative lifetime", "excited-state lifetime"), phrases=("excited-state lifetime", "radiative lifetime", "atomic lifetime"),
              notes=(f"The abstract prints {printed}.",) + extra)


_VOLZ1996 = "U. Volz, M. Majerus, H. Liebel, A. Schmitt, and H. Schmoranzer, Precision lifetime measurements on NaI 3p 2P1/2 and 3p 2P3/2 by beam-gas-laser spectroscopy, Phys. Rev. Lett. 76, 2862 (1996), doi:10.1103/PhysRevLett.76.2862"
_GUTTERRES2002 = "R. F. Gutterres, C. Amiot, A. Fioretti, C. Gabbanini, M. Mazzoni, and O. Dulieu, Determination of the 87Rb 5p state dipole matrix element and radiative lifetime from the photoassociation spectroscopy of the Rb2 0g-(P3/2) long-range state, Phys. Rev. A 66, 024502 (2002), doi:10.1103/PhysRevA.66.024502"
_YOUNG1994 = "L. Young, W. T. Hill III, S. J. Sibener, S. D. Price, C. E. Tanner, C. E. Wieman, and S. R. Leone, Precision lifetime measurements of Cs 6p 2P1/2 and 6p 2P3/2 levels by single-photon counting, Phys. Rev. A 50, 2174 (1994), doi:10.1103/PhysRevA.50.2174"
_RAFAC1999 = "R. J. Rafac, C. E. Tanner, A. E. Livingston, and H. G. Berry, Fast-beam laser lifetime measurements of the cesium 6p 2P1/2,3/2 states, Phys. Rev. A 60, 3648 (1999), doi:10.1103/PhysRevA.60.3648"
_PATTERSON2015 = "B. M. Patterson, J. F. Sell, T. Ehrenreich, M. A. Gearba, G. M. Brooke, J. Scoville, and R. J. Knize, Lifetime measurement of the cesium 6P3/2 level using ultrafast pump-probe laser pulses, Phys. Rev. A 91, 012506 (2015), doi:10.1103/PhysRevA.91.012506, arXiv:1410.7364"
_CS_DISAGREE = ("Cs 6p 2P3/2 lifetimes are kept from Young 1994 (30.41(10)), Rafac 1999 (30.57 +- 0.07), and Patterson 2015 (30.462(46)); the board does not choose between them.",)

ATOMIC_B15: tuple[Quantity, ...] = (
    *_tp("h_1s_2p32", "H I 1s 2S1/2 - 2p 2P3/2 (Lyman-alpha)", "H I", "121.5", "121.6", "hydrogen 2p", "6.2647e+08", "6.2647 e8", "2.7760e-01", "2.7760 e-1", "AAA", "T7771"),
    *_tp("h_1s_2p12", "H I 1s 2S1/2 - 2p 2P1/2 (Lyman-alpha)", "H I", "121.5", "121.6", "hydrogen 2p", "6.2648e+08", "6.2648 e8", "1.3880e-01", "1.3880 e-1", "AAA", "T7771"),
    *_tp("na_3s_3p32", "Na I 3s 2S1/2 - 3p 2P3/2 (D2)", "Na I", "588.9", "589.7", "sodium 3p", "6.16e+07", "6.16 e7", "6.41e-01", "6.41 e-1", "AA", "T6617,T6568,T6567"),
    *_tp("na_3s_3p12", "Na I 3s 2S1/2 - 3p 2P1/2 (D1)", "Na I", "588.9", "589.7", "sodium 3p", "6.14e+07", "6.14 e7", "3.20e-01", "3.20 e-1", "AA", "T6617,T6567"),
    *_tp("cs_6s_6p32", "Cs I 6s 2S1/2 - 6p 2P3/2 (D2)", "Cs I", "852", "895", "cesium 6p", "3.279e+07", "3.279 e7", "7.142e-01", "7.142 e-1", "AAA", "T6469"),
    *_tp("cs_6s_6p12", "Cs I 6s 2S1/2 - 6p 2P1/2 (D1)", "Cs I", "852", "895", "cesium 6p", "2.863e+07", "2.863 e7", "3.435e-01", "3.435 e-1", "AAA", "T6469"),
    *_tp("rb_5s_5p32", "Rb I 5s 2S1/2 - 5p 2P3/2 (D2)", "Rb I", "780", "795", "rubidium 5p", "3.812e+07", "3.812 e7", "6.958e-01", "6.958 e-1", "AAA", "T6877,T6650,T1895"),
    *_tp("rb_5s_5p12", "Rb I 5s 2S1/2 - 5p 2P1/2 (D1)", "Rb I", "780", "795", "rubidium 5p", "3.614e+07", "3.614 e7", "3.424e-01", "3.424 e-1", "AAA", "T6877,T6650"),
    _life("volz1996.na_3p12_lifetime", "lifetime of the Na I 3p 2P1/2 level", "tau(Na 3p 2P1/2)", "16.299", "0.021", "standard uncertainty", _VOLZ1996, "Phys. Rev. Lett. 76 (1996)",
          "10.1103/PhysRevLett.76.2862", "16.299(21) ns, at a stated precision of +-0.13%, 1 sigma"),
    _life("volz1996.na_3p32_lifetime", "lifetime of the Na I 3p 2P3/2 level", "tau(Na 3p 2P3/2)", "16.254", "0.022", "standard uncertainty", _VOLZ1996, "Phys. Rev. Lett. 76 (1996)",
          "10.1103/PhysRevLett.76.2862", "16.254(22) ns, at a stated precision of +-0.13%, 1 sigma"),
    _life("gutterres2002.rb87_5p32_lifetime", "radiative lifetime of the 87Rb 5P3/2 level (from Rb2 photoassociation spectroscopy)", "tau(Rb 5P3/2)", "26.25", "0.08",
          "uncertainty as printed, level not stated", _GUTTERRES2002, "Phys. Rev. A 66 (2002)", "10.1103/PhysRevA.66.024502", "26.25(8) ns, 'with a precision (0.3%)'",
          ("Extracted from the 5p dipole matrix element fitted to molecular photoassociation spectra, not a direct decay measurement.",)),
    _life("gutterres2002.rb87_5p12_lifetime", "radiative lifetime of the 87Rb 5P1/2 level (from Rb2 photoassociation spectroscopy)", "tau(Rb 5P1/2)", "27.75", "0.08",
          "uncertainty as printed, level not stated", _GUTTERRES2002, "Phys. Rev. A 66 (2002)", "10.1103/PhysRevA.66.024502", "27.75(8) ns",
          ("Extracted from the 5p dipole matrix element fitted to molecular photoassociation spectra, not a direct decay measurement.",)),
    _life("young1994.cs_6p12_lifetime", "lifetime of the Cs 6p 2P1/2 level (single-photon counting)", "tau(Cs 6p 2P1/2)", "34.75", "0.07",
          "uncertainty as printed, level not stated", _YOUNG1994, "Phys. Rev. A 50 (1994)", "10.1103/PhysRevA.50.2174", "34.75(7) ns, with accuracies of about 0.2-0.3%"),
    _life("young1994.cs_6p32_lifetime", "lifetime of the Cs 6p 2P3/2 level (single-photon counting)", "tau(Cs 6p 2P3/2)", "30.41", "0.10",
          "uncertainty as printed, level not stated", _YOUNG1994, "Phys. Rev. A 50 (1994)", "10.1103/PhysRevA.50.2174", "30.41(10) ns", _CS_DISAGREE),
    _life("rafac1999.cs_6p12_lifetime", "lifetime of the Cs 6p 2P1/2 level (fast-beam laser)", "tau(Cs 6p 2P1/2)", "35.07", "0.10",
          "uncertainty as printed, level not stated", _RAFAC1999, "Phys. Rev. A 60 (1999)", "10.1103/PhysRevA.60.3648", "35.07 +- 0.10 ns",
          ("Young 1994 prints 34.75(7) ns for the same level; both are kept.",)),
    _life("rafac1999.cs_6p32_lifetime", "lifetime of the Cs 6p 2P3/2 level (fast-beam laser)", "tau(Cs 6p 2P3/2)", "30.57", "0.07",
          "uncertainty as printed, level not stated", _RAFAC1999, "Phys. Rev. A 60 (1999)", "10.1103/PhysRevA.60.3648", "30.57 +- 0.07 ns", _CS_DISAGREE),
    _q("patterson2015.cs_6p32_lifetime", "lifetime of the Cs 6P3/2 level (ultrafast pump-probe)", "tau(Cs 6P3/2)", "30.462", "0.046", "ns",
       kind="uncertainty as printed, level not stated", source=_PATTERSON2015 + ", abstract and Sect. IV", edition="Phys. Rev. A 91 (2015); arXiv:1410.7364v1",
       url="https://doi.org/10.1103/PhysRevA.91.012506", retrieved_from="https://arxiv.org/e-print/1410.7364", keys=("radiative lifetime", "excited-state lifetime"),
       phrases=("excited-state lifetime", "radiative lifetime", "atomic lifetime"),
       notes=("Printed as 30.462(46) ns; the paper says the Table I uncertainties 'were added in quadrature to determine an overall measurement uncertainty of 0.046 ns (0.15%)'.",) + _CS_DISAGREE),
)

_KL = "Kaye & Laby, Tables of Physical and Chemical Constants, NPL online edition (Version 1.0 content)"
_KL_MAG_WB = "https://web.archive.org/web/20160103231152/http://www.kayelaby.npl.co.uk/general_physics/2_6/2_6_6.html"
_KL_GAMMA_WB = "https://web.archive.org/web/20161203063541/http://www.kayelaby.npl.co.uk/general_physics/2_3/2_3_6.html"
_LEVITON_FS = "D. B. Leviton and B. J. Frey, Temperature-dependent absolute refractive index measurements of synthetic fused silica, NASA GSFC (CHARMS), arXiv:0805.0091"
_FREY_SIGE = "B. J. Frey, D. B. Leviton, and T. J. Madison, Temperature-dependent refractive index of silicon and germanium, Proc. SPIE 6273 (2006), doi:10.1117/12.672850, arXiv:physics/0606168"
_KHATIWADA = "R. Khatiwada, L. Dennis, R. Kendrick, M. Khosravi, M. Peters, E. Smith, and W. M. Snow, Materials with low DC magnetic susceptibility for sensitive magnetic measurements, Meas. Sci. Technol. 27, 025902 (2016), doi:10.1088/0957-0233/27/2/025902, arXiv:1506.09199"
_HAVENS = "G. G. Havens, The magnetic susceptibilities of some common gases, Phys. Rev. 43, 992 (1933), doi:10.1103/PhysRev.43.992"


def _klmag(key, name, value):
    return _q(f"kayelaby_mag.{key}", f"mass magnetic susceptibility of {name} at 20 C", f"chi_m({name})", value, "", "1e-8 m^3/kg", kind="no uncertainty printed",
              source=_KL + ", Sect. 2.6.6 Magnetic properties of materials, Table (1) Magnetic susceptibilities of paramagnetic and diamagnetic materials",
              edition="Kaye & Laby online, Wayback snapshot 2016-01-03", url=_KL_MAG_WB, retrieved_from=_KL_MAG_WB, keys=("magnetic susceptibility", "mass susceptibility"),
              phrases=("magnetic susceptibility", f"magnetic susceptibility of {name.split()[0].lower()}", "mass susceptibility"),
              notes=(f"Printed as {value} in the x 10^-8 column; the table heading says 'Values are mass susceptibility per kilogram, chi, at 20 C'.",
                     "The page was kayelaby.npl.co.uk/general_physics/2_6/2_6_6.html (NPL); the live site is retired, so the Wayback copy is cited.", "Note (1) of the table: to obtain values in CGS units per gramme, multiply the SI values by 10^3/4 pi. Not converted here."))


def _klgamma(key, gas, temp, value):
    return _q(f"kayelaby_gamma.{key}", f"ratio of principal specific heats of {gas} at {temp} C", f"gamma({gas})", value, "", "", kind="no uncertainty printed",
              source=_KL + ", Sect. 2.3.6 Specific heat capacities, 'Ratio of the principal specific heat capacities for gases and vapours'",
              edition="Kaye & Laby online, Wayback snapshot 2016-12-03", url=_KL_GAMMA_WB, retrieved_from=_KL_GAMMA_WB, keys=("heat capacity ratio", "adiabatic index"),
              phrases=("heat capacity ratio", "adiabatic index", f"heat capacity ratio of {gas.split()[0].lower()}", "ratio of specific heats"),
              notes=(f"The table row prints Gas {gas}, Temp./C {temp}, gamma {value}.", "The section says gamma 'is usually determined directly by some method involving an adiabatic expansion, such as the determination of the velocity of sound in the gas'.", "The page was kayelaby.npl.co.uk/general_physics/2_3/2_3_6.html (NPL); the live site is retired, so the Wayback copy is cited."))


def _dndt(prefix, key, material, wl, temp, printed, value, source, edition, url, retrieved, table):
    return _q(f"{prefix}.{key}", f"thermo-optic coefficient dn/dT of {material} at {wl} um and {temp} K", f"dn/dT({material}, {wl} um, {temp} K)", value, "", "1/K",
              kind="no uncertainty printed", source=f"{source}, {table}", edition=edition, url=url, retrieved_from=retrieved, keys=("thermo-optic coefficient", "dn/dt"),
              phrases=("thermo-optic", "thermo-optic coefficient", "dn/dt", f"thermo-optic coefficient of {material.lower()}"),
              notes=(f"{table} prints {printed} at {wl} microns and {temp} K.",))


_FS_NOTE_ARGS = dict(source=_LEVITON_FS, edition="arXiv:0805.0091v1", url="https://arxiv.org/abs/0805.0091", retrieved="https://arxiv.org/e-print/0805.0091",
                     table="Table 6 (thermo-optic coefficient of Corning 7980 fused silica)")
_SI_ARGS = dict(source=_FREY_SIGE, edition="arXiv:physics/0606168v1", url="https://doi.org/10.1117/12.672850", retrieved="https://arxiv.org/e-print/physics/0606168",
                table="Table 4 (measured thermo-optic coefficient of silicon)")
_GE_ARGS = dict(_SI_ARGS, table="Table 9 (measured thermo-optic coefficient of germanium)")

EMOPTICS_B15: tuple[Quantity, ...] = (
    _klmag("water", "water (H2O)", "-0.90"),
    _klmag("bismuth", "bismuth", "-1.70"),
    _klmag("aluminium", "aluminium", "+0.82"),
    _klmag("oxygen", "oxygen", "+133.6"),
    _klmag("copper", "copper", "-0.107"),
    _q("khatiwada2015.water_chi_v", "volume magnetic susceptibility of water (room temperature)", "chi_v(H2O)", "-0.716", "0.094", "1e-6 (cgs volume)",
       kind="uncertainty as printed, level not stated", source=_KHATIWADA + ", Table 1 (0% MnCl2 row)", edition="arXiv:1506.09199v1", url="https://doi.org/10.1088/0957-0233/27/2/025902",
       retrieved_from="https://arxiv.org/e-print/1506.09199", keys=("magnetic susceptibility", "water magnetic susceptibility"), phrases=("magnetic susceptibility", "magnetic susceptibility of water"),
       notes=("Printed as 0% MnCl2: -0.716 +- 0.094 (chi x 10^-6, cgs volume). The caption says 'The errors are dominated by systematic error'.",)),
    _q("havens1933.o2_chi_molar_provisional_20c", "molar magnetic susceptibility of O2 at 20 C (provisional reference value)", "chi_mol(O2, 20 C)", "3335", "", "1e-6 (cgs molar)",
       kind="no uncertainty printed", source=_HAVENS + ", abstract", edition="Phys. Rev. 43 (1933)", url="https://doi.org/10.1103/PhysRev.43.992", retrieved_from="https://api.openalex.org/works/doi:10.1103/PhysRev.43.992",
       keys=("magnetic susceptibility", "oxygen magnetic susceptibility"), phrases=("magnetic susceptibility", "magnetic susceptibility of oxygen"),
       notes=("The abstract says the reported values 'are based on the provisional value of chi(O2) = 3335 x 10^-6 at 20 C'; it is Havens's adopted calibration value, not a result of the paper.",)),
    _q("havens1933.n2_chi_molar_room", "molar magnetic susceptibility of N2 at room temperature", "chi_mol(N2)", "-11.938", "", "1e-6 (cgs molar)",
       kind="no uncertainty printed", source=_HAVENS + ", abstract", edition="Phys. Rev. 43 (1933)", url="https://doi.org/10.1103/PhysRev.43.992", retrieved_from="https://api.openalex.org/works/doi:10.1103/PhysRev.43.992",
       keys=("magnetic susceptibility", "nitrogen magnetic susceptibility"), phrases=("magnetic susceptibility", "magnetic susceptibility of nitrogen"),
       notes=("Printed in the abstract as chi(N2) = -11.938 (x 10^6, molecular susceptibility) at room temperature, by the Faraday test-body method.",)),
    _dndt("leviton2008", "fused_silica_dndt_0p5um_295k", "fused silica", "0.5", "295", "9.12E-06", "9.12 e-6", **_FS_NOTE_ARGS),
    _dndt("leviton2008", "fused_silica_dndt_0p6um_295k", "fused silica", "0.6", "295", "8.86E-06", "8.86 e-6", **_FS_NOTE_ARGS),
    _dndt("leviton2008", "fused_silica_dndt_1p0um_295k", "fused silica", "1.0", "295", "8.48E-06", "8.48 e-6", **_FS_NOTE_ARGS),
    _dndt("leviton2008", "fused_silica_dndt_0p5um_100k", "fused silica", "0.5", "100", "3.60E-06", "3.60 e-6", **_FS_NOTE_ARGS),
    _dndt("frey2006", "si_dndt_1p5um_295k", "silicon", "1.5", "295", "1.87E-04", "1.87 e-4", **_SI_ARGS),
    _dndt("frey2006", "si_dndt_4p0um_295k", "silicon", "4.0", "295", "1.70E-04", "1.70 e-4", **_SI_ARGS),
    _dndt("frey2006", "ge_dndt_4p0um_295k", "germanium", "4.0", "295", "4.25E-04", "4.25 e-4", **_GE_ARGS),
    _klgamma("helium_0c", "helium", "0", "1.63"),
    _klgamma("argon_0c", "argon", "0", "1.667"),
    _klgamma("nitrogen_20c", "nitrogen", "20", "1.401"),
    _klgamma("oxygen_5_14c", "oxygen", "5-14", "1.400"),
    _klgamma("air_m79c", "dry air", "-79.3", "1.405"),
    _klgamma("co2_4_11c", "carbon dioxide", "4-11", "1.300"),
    _klgamma("methane_20c", "methane", "20", "1.307"),
)

_NBS539_V1 = "https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular539v1.pdf"
_NBS539_V2 = "https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular539v2.pdf"
_NBS539_NOTE = "The circular prints the lattice constant with no uncertainty; it is the NBS powder-diffraction value, not a CODATA-style adjusted constant."
_IOFFE_BASIC = {
    "Ge": "https://web.archive.org/web/20251210060631/https://www.ioffe.ru/SVA/NSM/Semicond/Ge/basic.html",
    "GaAs": "https://web.archive.org/web/20260122004905/http://www.ioffe.ru/SVA/NSM/Semicond/GaAs/basic.html",
    "Diamond": "https://web.archive.org/web/20250513044705/http://www.ioffe.ru/SVA/NSM/Semicond/Diamond/basic.html",
}


def _nbs539(key: str, material: str, value: str, temp: str, vol: str, authors: str, url: str, page: str, header: str, phrases: tuple[str, ...]) -> Quantity:
    return _q(f"nbs1953.{key}.lattice_constant", f"lattice constant of {material} at {temp} C (NBS powder pattern)", f"a({material})", value, "", "Angstrom",
              kind="no uncertainty printed", source=f"{authors}, Standard X-ray Diffraction Powder Patterns, NBS Circular 539, {vol} (1953)",
              edition=f"NBS Circular 539, {vol}", url=url, retrieved_from=url,
              keys=("lattice constant", "unit cell"), phrases=phrases + ("lattice constants",),
              notes=(f"{page}: the table headed '{header}' gives the NBS value {value} at {temp} C.", _NBS539_NOTE))


def _ioffe_lattice(mol: str, value: str, printed: str, phrases: tuple[str, ...]) -> Quantity:
    return _q(f"ioffe.{mol.lower()}.lattice_constant_300k", f"lattice constant of {mol} at 300 K (Ioffe)", f"a({mol})", value, "", "Angstrom",
              kind="no uncertainty printed", source=f"Ioffe Institute, NSM Archive - Physical Properties of Semiconductors, {mol}: Basic Parameters.", edition="Ioffe NSM Archive",
              url=_IOFFE_BASIC[mol], retrieved_from=_IOFFE_BASIC[mol],
              keys=("lattice constant",), phrases=phrases + ("lattice constants",),
              notes=(f"The 'Basic Parameters at 300 K' table prints 'Lattice constant {printed}'.", f"Original page: https://www.ioffe.ru/SVA/NSM/Semicond/{mol}/basic.html.", _IOFFE_REACH))


LATTICE_CONSTANTS: tuple[Quantity, ...] = (
    _nbs539("al", "aluminium", "4.0494", "25", "Vol. I", "H. E. Swanson and E. Tatge", _NBS539_V1, "Vol. I p. 11", "Unit cell, angstroms at 25°C",
            ("lattice constant of aluminium", "lattice constant of aluminum", "aluminium lattice constant")),
    _nbs539("cu", "copper", "3.6150", "25", "Vol. I", "H. E. Swanson and E. Tatge", _NBS539_V1, "Vol. I p. 15", "Unit cell in angstroms at 25°C",
            ("lattice constant of copper", "copper lattice constant")),
    _nbs539("ge", "germanium", "5.6576", "25", "Vol. I", "H. E. Swanson and E. Tatge", _NBS539_V1, "Vol. I p. 19", "Unit cell, angstroms at 25°C",
            ("lattice constant of germanium", "germanium lattice constant")),
    _nbs539("diamond", "diamond", "3.5667", "26", "Vol. II", "H. E. Swanson and R. K. Fuyat", _NBS539_V2, "Vol. II p. 6", "Lattice constants in angstroms",
            ("lattice constant of diamond", "diamond lattice constant")),
    _nbs539("nacl", "sodium chloride", "5.6402", "26", "Vol. II", "H. E. Swanson and R. K. Fuyat", _NBS539_V2, "Vol. II p. 42", "Lattice constant in angstroms",
            ("lattice constant of sodium chloride", "lattice constant of nacl", "rock salt lattice constant")),
    _ioffe_lattice("Ge", "5.658", "5.658 A", ("lattice constant of germanium", "germanium lattice constant")),
    _ioffe_lattice("GaAs", "5.65325", "5.65325 A", ("lattice constant of gaas", "gallium arsenide lattice constant")),
    _ioffe_lattice("Diamond", "3.567", "3.567A", ("lattice constant of diamond", "diamond lattice constant")),
)

_KL_35_WB = "https://web.archive.org/web/20161211084624/http://www.kayelaby.npl.co.uk/chemistry/3_5/3_5.html"
_KL_35_SOURCE = "Kaye & Laby, Tables of Physical and Chemical Constants (NPL online, version 1.0), Sect. 3.5, Critical constants and second virial coefficients of gases (D. Ambrose, M. B. Ewing, M. L. McGlashan)"
_KL_35_NOTE = "kayelaby.npl.co.uk is retired; the page was read from the Internet Archive copy (original http://www.kayelaby.npl.co.uk/chemistry/3_5/3_5.html)."
_KL_FIT_NOTE = ("Sect. 3.5 fits B by B/(cm3 mol-1) = a - b exp{c (K/T)}, 'usually within experimental errors over the range of temperatures at which measurements have been made'; "
                "the coefficients are fit parameters, not measured B values, and are stored as printed. The page refers to Dymond and Smith (1980) for experimental B values.")


def _kl_virial(gas: str, coef: str, value: str, unit: str, tl: str, tu: str) -> Quantity:
    return _q(f"kayelaby_virial.{gas.replace(' ', '_')}_{coef}", f"second virial coefficient fit coefficient {coef} for {gas} (Kaye & Laby)", f"{coef}_B({gas})", value, "", unit,
              kind="no uncertainty printed", source=_KL_35_SOURCE, edition="Kaye & Laby online, v1.0", url=_KL_35_WB, retrieved_from=_KL_35_WB,
              keys=("second virial coefficient", "virial coefficient"), phrases=(f"second virial coefficient of {gas}", f"{gas} virial coefficient", "second virial coefficients"),
              notes=(f"Row '{gas.capitalize()}' prints a = {{a}}, b = {{b}}, c = {{c}} for T_L = {tl} K to T_U = {tu} K.".format(**_KL_ABC[gas]), _KL_FIT_NOTE, _KL_35_NOTE))


_KL_ABC = {"helium": {"a": "114.1", "b": "98.7", "c": "3.245"}, "argon": {"a": "154.2", "b": "119.3", "c": "105.1"}, "nitrogen": {"a": "185.4", "b": "141.8", "c": "88.7"}}


def _kl_crit(gas: str, which: str, value: str, unit: str, row: str) -> Quantity:
    label = {"t_c": "critical temperature", "p_c": "critical pressure"}[which]
    return _q(f"kayelaby_crit.{gas.replace(' ', '_')}_{which}", f"{label} of {gas} (Kaye & Laby)", f"{which[0].upper()}_c({gas})", value, "", unit,
              kind="no uncertainty printed", source=_KL_35_SOURCE, edition="Kaye & Laby online, v1.0", url=_KL_35_WB, retrieved_from=_KL_35_WB,
              keys=(f"{label} of {gas}",), phrases=(f"critical point of {gas}", f"{label} of {gas}", "critical constants"),
              notes=(f"Row '{row}' prints p_c/MPa, V_c,m/(cm3 mol-1), T_c/K, p_cV_c,m/RT_c as {_KL_CRIT_ROW[gas]}.", _KL_35_NOTE))


_KL_CRIT_ROW = {"helium": "0.227, 57.2, 5.19, 0.301", "nitrogen": "3.39, 89.5, 126.2, 0.289", "carbon dioxide": "7.38, 94.0, 304.1, 0.274"}


VIRIAL_CRITICAL: tuple[Quantity, ...] = (
    _kl_virial("helium", "a", "114.1", "cm^3 mol^-1", "7", "150"),
    _kl_virial("helium", "b", "98.7", "cm^3 mol^-1", "7", "150"),
    _kl_virial("helium", "c", "3.245", "", "7", "150"),
    _kl_virial("argon", "a", "154.2", "cm^3 mol^-1", "80", "1024"),
    _kl_virial("argon", "b", "119.3", "cm^3 mol^-1", "80", "1024"),
    _kl_virial("argon", "c", "105.1", "", "80", "1024"),
    _kl_virial("nitrogen", "a", "185.4", "cm^3 mol^-1", "75", "700"),
    _kl_virial("nitrogen", "b", "141.8", "cm^3 mol^-1", "75", "700"),
    _kl_virial("nitrogen", "c", "88.7", "", "75", "700"),
    _kl_crit("helium", "t_c", "5.19", "K", "Helium"),
    _kl_crit("helium", "p_c", "0.227", "MPa", "Helium"),
    _kl_crit("nitrogen", "t_c", "126.2", "K", "Nitrogen"),
    _kl_crit("nitrogen", "p_c", "3.39", "MPa", "Nitrogen"),
    _kl_crit("carbon dioxide", "t_c", "304.1", "K", "Carbon dioxide"),
    _kl_crit("carbon dioxide", "p_c", "7.38", "MPa", "Carbon dioxide"),
)

_SUB_NOTE = "The WebBook row renders the last digit as a subscript (Huber and Herzberg's marking of a less certain digit); it is kept here as an ordinary digit. Numbers after the value on the row are footnote links."


def _webbook_const(mol: str, cas: str, state: str, which: str, value: str, printed: str, extra: str = "") -> Quantity:
    label, sym, short = {"we": ("harmonic vibrational wavenumber omega_e", "omega_e", "vibrational frequency"), "be": ("equilibrium rotational constant B_e", "B_e", "rotational constant")}[which]
    m = mol.lower()
    return _q(
        f"hh1979.{which}_{m}", f"{label} of {mol}, ground state {state}", f"{sym}({mol})", value, "", "cm^-1",
        kind="no uncertainty printed", source=WEBBOOK_DIATOMIC_SOURCE, edition=_WEBBOOK_EDITION,
        url=f"https://webbook.nist.gov/cgi/cbook.cgi?ID={cas}&Mask=1000#Diatomic", retrieved_from=f"https://webbook.nist.gov/cgi/cbook.cgi?ID={cas}&Mask=1000",
        keys=(f"{short} of {m}",), phrases=(f"{short} of {m}", f"{m} {short}", f"{short}s of diatomic molecules"),
        notes=(f"Ground state {state}: the {sym} column prints '{printed}'.",) + ((_SUB_NOTE,) if "_" in printed else ()) + ((extra,) if extra else ()),
    )


_SHIMANOUCHI_URL = "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Mask=800"
_SHIMANOUCHI_SOURCE = ("T. Shimanouchi, Tables of Molecular Vibrational Frequencies Consolidated Volume I, NSRDS-NBS 39 (1972), "
                       "as served in NIST Chemistry WebBook, SRD 69, 'Vibrational and/or electronic energy levels' for water")


def _h2o_mode(n: str, mode: str, sym: str, value: str, ir: str) -> Quantity:
    return _q(f"shimanouchi1972.h2o.nu{n}", f"water fundamental vibrational frequency nu{n} ({mode}, {sym})", f"nu{n}(H2O)", value, "", "cm^-1",
              kind="no uncertainty printed", source=_SHIMANOUCHI_SOURCE, edition="NSRDS-NBS 39 (1972), via WebBook", url=_SHIMANOUCHI_URL, retrieved_from=_SHIMANOUCHI_URL,
              keys=("vibrational frequency of water", "vibrational frequency of h2o"), phrases=("vibrational frequency of water", "water vibrational frequencies", "h2o fundamentals"),
              notes=(f"The table prints the selected frequency {value} with rating A, and the gas-phase infrared value {ir}.",
                     "The page's notes define rating A as '0~1 cm-1 uncertainty'; this is a rating class, not a per-value uncertainty."))


MOLECULAR_CONSTANTS: tuple[Quantity, ...] = (
    _webbook_const("H2", "C1333740", "X 1Sigma_g+", "we", "4401.213", "4401.21_3"),
    _webbook_const("H2", "C1333740", "X 1Sigma_g+", "be", "60.8530", "60.853_0"),
    _webbook_const("N2", "C7727379", "X 1Sigma_g+", "we", "2358.57", "2358.57 Z", "The trailing 'Z' is a flag on the WebBook row and is not interpreted here."),
    _webbook_const("N2", "C7727379", "X 1Sigma_g+", "be", "1.998241", "1.99824_1"),
    _webbook_const("O2", "C7782447", "X 3Sigma_g-", "we", "1580.193", "1580.19_3 Z", "The trailing 'Z' is a flag on the WebBook row and is not interpreted here. The O2 B_e is printed in brackets ([1.4376766]) and is not stored."),
    _webbook_const("CO", "C630080", "X 1Sigma+", "we", "2169.81358", "2169.81358"),
    _webbook_const("CO", "C630080", "X 1Sigma+", "be", "1.93128087", "1.93128087"),
    _webbook_const("HCl", "C7647010", "X 1Sigma+", "we", "2990.9463", "2990.946_3", "The WebBook page lists constants for H35Cl."),
    _webbook_const("HCl", "C7647010", "X 1Sigma+", "be", "10.593416", "10.59341_6", "The WebBook page lists constants for H35Cl."),
    _h2o_mode("1", "symmetric stretch", "a1", "3657", "3656.65"),
    _h2o_mode("2", "bend", "a1", "1595", "1594.59"),
    _h2o_mode("3", "antisymmetric stretch", "b1", "3756", "3755.79"),
)

_BIPM_DOC = "https://www.bipm.org/documents/20126/"
_CIPM_NOTE = "Approved by the CCTF in September 2025, active on March 27, 2026."


def _cipm(key: str, atom: str, title: str, transition: str, f: str, lam: str, rel: str, path: str, phrases: tuple[str, ...], extra: str = "") -> Quantity:
    url = _BIPM_DOC + path
    printed = f"f = {f} Hz" + (f", lambda = {lam} fm" if lam else "") + f", relative standard uncertainty {rel.replace(' e', ' x 10^')}"
    return _q(f"bipm2025.{key}.frequency", f"{atom} {transition} frequency (CIPM recommended)", f"f({atom})", f.replace(" ", " "), rel, "Hz",
              kind="relative standard uncertainty", source=f"BIPM, Recommended values of standard frequencies, {title}, approved by the CCTF in September 2025, active on March 27, 2026.",
              edition="CIPM list of standard frequencies, 2025", url=url, retrieved_from=url,
              keys=("standard frequency", "optical clock"), phrases=phrases + ("optical clock frequencies", "standard frequencies"),
              notes=(f"Printed as {printed}.", _CIPM_NOTE) + ((extra,) if extra else ()))


_POL_CCCBDB = "https://cccbdb.nist.gov/pollistx.asp"


def _ddep16(key: str, nuclide: str, label: str, value: str, error: str, unit: str, printed: str, pdf: str, evaluator: str, dates: str) -> Quantity:
    url = f"https://www.lnhb.fr/nuclides/{pdf}_tables.pdf"
    return _q(f"ddep.t_half_{key}", f"half-life of {nuclide} (DDEP)", f"T1/2({label})", value, error, unit, kind="uncertainty as printed, level not stated",
              source=f"{_DDEP_SOURCE}, {pdf} tables, evaluation by {evaluator}", edition=f"DDEP {pdf} tables as served 2026-11-25", url=url, retrieved_from=url,
              keys=(f"half-life of {pdf.lower()}", f"{pdf.lower()} half-life"), phrases=(f"half-life of {pdf.lower()}", f"{pdf.lower()} half-life", f"half-life of {nuclide}", "medical isotope half-lives"),
              notes=(f"Section 2 prints {printed} (decimal comma, uncertainty in the last digits).", f"Evaluation dates on the table footer: {dates}."))


CLOCKS_POLARIZABILITY_HALFLIVES: tuple[Quantity, ...] = (
    _cipm("ca40_ion", "40Ca+", "Calcium 40 ion (f ~ 411 THz)", "4s 2S1/2 - 3d 2D5/2", "411 042 129 776 400.30", "729 347 276.793 942 83", "5.5 e-16",
          "288515003/40Ca+_411THz_2025/fb0a8014-32b2-e2ab-639f-f3313ded1edc", ("ca40+ clock frequency", "calcium ion clock frequency")),
    _cipm("in115_ion", "115In+", "Indium 115 ion (f ~ 1 267 THz)", "5s2 1S0 - 5s5p 3P0", "1 267 402 452 901 039.07", "236 540 853.549 545 96", "1.8 e-16",
          "288515121/115In+_1267THz_2025/18227b90-49fc-1a73-fe7a-f9fffd350dc1", ("in115+ clock frequency", "indium ion clock frequency")),
    _cipm("hg199", "199Hg", "Mercury 199 atom (f ~ 1 129 THz)", "6s2 1S0 - 6s6p 3P0", "1 128 575 290 808 154.33", "265 637 977.759 838 71", "2.5 e-16",
          "288515168/199Hg_1129THz_2025/ffd863a1-a0be-bd53-01f9-414a74a152bd", ("hg199 clock frequency", "mercury lattice clock frequency")),
    _cipm("hg199_ion", "199Hg+", "Mercury 199 ion (f ~ 1 065 THz)", "5d10 6s 2S1/2 (F=0) - 5d9 6s2 2D5/2 (F=2)", "1 064 721 609 899 146.95", "281 568 867.591 968 08", "2.5 e-16",
          "288514850/199Hg+_1065THz_2025/5e2a3382-c6c6-e61c-4cc0-b4ded661b859", ("hg199+ clock frequency", "mercury ion clock frequency")),
    _cipm("lu176_ion", "176Lu+", "Lutetium 176 ion (f ~ 353.6 THz)", "mean of the three 6s2 1S0 (F=7) - 5d6s 3D1 (F=6, 7, 8)", "353 638 794 073 800.35", "", "2.8 e-15",
          "288515214/176Lu+_353.6THz_2025/2b68827b-9b36-fbd3-6af5-5b73f09832a0", ("lu176+ clock frequency", "lutetium ion clock frequency"),
          "The sheet defines f(176Lu+) = (nu1 + nu2 + nu3)/3 and prints no wavelength."),
    _cipm("rb87", "87Rb", "Rubidium 87 atom (f ~ 6.835 GHz)", "ground-state hyperfine", "6 834 682 610.904 312 9", "", "3.4 e-16",
          "288515266/87Rb_6.835GHz_2025/011eeef3-7afe-166f-8962-5003978dd25e", ("rb87 hyperfine frequency", "rubidium hyperfine frequency", "rubidium clock frequency"),
          "The sheet says the radiation is endorsed as a secondary representation of the definition of the second."),
    _cipm("sr88", "88Sr", "Strontium 88 atom (f ~ 429 THz)", "5s2 1S0 - 5s5p 3P0", "429 228 066 418 007.008", "698 445 608.419 382 438", "1.9 e-16",
          "288515361/88Sr_429THz_2025/3d0db6ba-4c3f-2146-4bde-88a88b95c671", ("sr88 clock frequency", "strontium 88 clock frequency")),
    _cipm("sr88_ion", "88Sr+", "Strontium 88 ion (f ~ 445 THz)", "5s 2S1/2 - 4d 2D5/2", "444 779 044 095 485.347", "674 025 590.863 135 253", "1.7 e-16",
          "288516317/88Sr+_445THz_2025/6de68087-f958-96f9-23a2-2c5b944f5d35", ("sr88+ clock frequency", "strontium ion clock frequency")),
    _cipm("yb171_ion_e2", "171Yb+ E2", "Ytterbium 171 ion (f ~ 688 THz)", "6s 2S1/2 (F=0) - 5d 2D3/2 (F=2)", "688 358 979 309 308.31", "435 517 610.739 687 59", "1.9 e-16",
          "288516443/171Yb+_688THz_2025/b660ad09-7c1b-4629-e667-94e6d2fad827", ("yb171+ e2 clock frequency", "ytterbium ion quadrupole clock frequency")),
    _cipm("yb171_ion_e3", "171Yb+ E3", "Ytterbium 171 ion (f ~ 642 THz)", "6s 2S1/2 (F=0) - 4f13 6s2 2F7/2 (F=3)", "642 121 496 772 645.18", "466 878 090.060 496 74", "1.7 e-16",
          "288516395/171Yb+_642THz_2025/cdee7d00-642c-588e-cc7d-d0e760a9fc69", ("yb171+ e3 clock frequency", "ytterbium ion octupole clock frequency")),
    _q("amini2003.cs.alpha0", "static scalar dipole polarizability of the cesium 6 2S1/2 ground state", "alpha_0(Cs)", "6.611 e-39", "0.009 e-39", "C m^2 V^-1",
       kind="uncertainty as printed, level not stated",
       source="J. M. Amini and H. Gould, High Precision Measurement of the Static Dipole Polarizability of Cesium, Phys. Rev. Lett. 91, 153001 (2003), doi:10.1103/PhysRevLett.91.153001, abstract",
       edition="Phys. Rev. Lett. 91 (2003)", url="https://doi.org/10.1103/PhysRevLett.91.153001", retrieved_from="https://api.openalex.org/works/doi:10.1103/PhysRevLett.91.153001",
       keys=("polarizability of cesium", "cesium polarizability"), phrases=("polarizability of cesium", "polarizability of caesium", "cesium polarizability", "static polarizabilities"),
       notes=("Printed in the abstract as alpha_0 = 6.611 +- 0.009 x 10^-39 C m^2/V = 59.42 +- 0.08 x 10^-24 cm^3 = 401.0 +- 0.6 a_0^3; the SI form is stored.",
              "Measured from the time of flight of laser-cooled, launched cesium atoms through an electric field; the abstract calls the 0.14% uncertainty a factor of 14 improvement.")),
    _q("ekstrom1995.na.alpha", "ground-state electric polarizability of sodium", "alpha(Na)", "24.11 e-24", "0.06 e-24", "cm^3",
       kind="statistical and systematic, printed separately", systematic_text="0.06 e-24",
       source="C. R. Ekstrom, J. Schmiedmayer, M. S. Chapman, T. D. Hammond, and D. E. Pritchard, Measurement of the electric polarizability of sodium with an atom interferometer, Phys. Rev. A 51, 3883 (1995), doi:10.1103/PhysRevA.51.3883, abstract",
       edition="Phys. Rev. A 51 (1995)", url="https://doi.org/10.1103/PhysRevA.51.3883", retrieved_from="https://api.openalex.org/works/doi:10.1103/PhysRevA.51.3883",
       keys=("polarizability of sodium", "sodium polarizability"), phrases=("polarizability of sodium", "sodium polarizability", "static polarizabilities"),
       notes=("Printed in the abstract as 24.11(6)_statistical(6)_systematic x 10^-24 cm^3.", _SPLIT_NOTE,
              "The CCCBDB experimental list prints 24.110 A^3 for Na, citing Olney et al. (1997); it is not stored separately.")),
    _q("cccbdb_pol.he.alpha", "static dipole polarizability of the helium atom (CCCBDB experimental list)", "alpha(He)", "0.208", "", "Angstrom^3",
       kind="no uncertainty printed", source=CCCBDB_SOURCE.replace("Experimental > Energy > Atomization Energy.", "Experimental > Electrostatics > Polarizability (list of experimental polarizabilities)."),
       edition="CCCBDB experimental polarizabilities", url=_POL_CCCBDB, retrieved_from=_POL_CCCBDB,
       keys=("polarizability of helium", "helium polarizability"), phrases=("polarizability of helium", "helium polarizability", "static polarizabilities"),
       notes=("The list ('Polarizabilites in A^3') prints He, Helium atom, alpha 0.208, squib 1997Oln/Can:59.",
              "1997Oln/Can:59 is T. N. Olney, N. M. Cann, G. Cooper, and C. E. Brion, Chem. Phys. 223, 59-98 (1997), doi:10.1016/S0301-0104(97)00145-6: dipole sum rules over absolute photoabsorption spectra.",
              "Schmidt et al., Phys. Rev. Lett. 98, 254504 (2007) measured helium's molar polarizability, but the abstract prints only its ratio to theory, so no value is stored from it.")),
    _ddep16("f18", "fluorine-18", "18F", "1.82890", "0.00023", "h", "T1/2 (18F) : 1,82890 (23) h", "F-18", "V. Chiste, M. M. Be (LNHB), N. K. Kuzmenko (KRI)", "22/10/2002 - 29/8/2014"),
    _ddep16("tc99m", "technetium-99m", "99mTc", "6.0067", "0.0010", "h", "T1/2 (99mTc) : 6,0067 (10) h", "Tc-99m", "C. Morillon, M. M. Be (LNHB), V. Chechev, A. Egorov (KRI)", "01/01/00 - 5/1/2012"),
    _ddep16("i131", "iodine-131", "131I", "8.0233", "0.0019", "d", "T1/2 (131I) : 8,0233 (19) d", "I-131", "V. Chiste, M. M. Be (CEA/LNE-LNHB)", "13/11/2001 - 20/1/2014"),
    _ddep16("c11", "carbon-11", "11C", "20.361", "0.023", "min", "T1/2 (11C) : 20,361 (23) min", "C-11", "V. Chiste, M. M. Be (LNE-LNHB/CEA)", "23/07/2002 - 3/11/2011"),
    _ddep16("o15", "oxygen-15", "15O", "122.266", "0.049", "s", "T1/2 (15O) : 122,266 (49) s", "O-15", "X. Mougeot (CEA-LNHB)", "13/05/2002 - 03/03/2026"),
)

_KL_266_SOURCE = "Kaye & Laby, Tables of Physical and Chemical Constants (NPL online, version 1.0), Sect. 2.6.6, Magnetic properties of materials, table (3) Soft (low coercivity) materials"
_KL_266_NOTE = "kayelaby.npl.co.uk is retired; the page was read from the Internet Archive copy (original http://www.kayelaby.npl.co.uk/general_physics/2_6/2_6_6.html)."
_OA = "https://api.openalex.org/works/doi:"


def _kl_js(key: str, metal: str, row: str, value: str, curie: str) -> Quantity:
    return _q(f"kayelaby_ferro.{key}_js", f"saturation magnetic polarization J_s of {metal} (Kaye & Laby)", f"J_s({metal})", value, "", "T",
              kind="no uncertainty printed", source=_KL_266_SOURCE, edition="Kaye & Laby online, v1.0", url=_KL_MAG_WB, retrieved_from=_KL_MAG_WB,
              keys=("saturation magnetization", f"saturation magnetization of {metal}"), phrases=(f"saturation magnetization of {metal}", f"{metal} saturation magnetization", "magnetic moments of ferromagnets"),
              notes=(f"Under 'Ferromagnetic elements', the row '{row}' prints J_s = {value} T and Curie point {curie} C.", "The table gives no temperature for J_s and prints no uncertainty.", _KL_266_NOTE))


_DANAN = ("H. Danan, A. Herr, and A. J. P. Meyer, New Determinations of the Saturation Magnetization of Nickel and Iron, J. Appl. Phys. 39, 669-670 (1968), "
          "doi:10.1063/1.2163571, abstract")
_DANAN_NOTE = "The abstract calls the values absolute saturation, sigma_0,infinity: extrapolated to 0 K and corrected for demagnetizing fields, rotations, and paramagnetic terms."


def _danan(key: str, metal: str, which: str, value: str, unc: str, unit: str, printed: str) -> Quantity:
    label, sym = {"sigma": ("absolute saturation magnetization (per mass) at 0 K", "sigma_0"), "moment": ("saturation magnetic moment per atom at 0 K", "M")}[which]
    return _q(f"danan1968.{key}_{which}", f"{label} of {metal}", f"{sym}({metal})", value, unc, unit,
              kind="uncertainty as printed, level not stated" if unc else "no uncertainty printed", source=_DANAN, edition="J. Appl. Phys. 39 (1968)",
              url="https://doi.org/10.1063/1.2163571", retrieved_from=_OA + "10.1063/1.2163571",
              keys=("saturation magnetization", f"saturation magnetization of {metal}"), phrases=(f"saturation magnetization of {metal}", f"magnetic moment of {metal}", "magnetic moments of ferromagnets"),
              notes=(f"Printed in the abstract as {printed}.", _DANAN_NOTE))


_KL_310_1 = "https://web.archive.org/web/20160702062422/http://www.kayelaby.npl.co.uk/chemistry/3_10/3_10_1.html"
_KL_310_4 = "https://web.archive.org/web/20170120004136/http://www.kayelaby.npl.co.uk/chemistry/3_10/3_10_4.html"
_KL_310_SOURCE = "Kaye & Laby, Tables of Physical and Chemical Constants (NPL online, version 1.0), Sect. 3.10.{n}, {title} (M. L. McGlashan)"
_KL_RETIRED = "kayelaby.npl.co.uk is retired; the page was read from the Internet Archive copy named in retrieved_from."


def _kl_latent(key: str, substance: str, which: str, value: str, unit: str, temp: str, sect: str, note: str) -> Quantity:
    label = {"fus": "enthalpy of fusion", "vap": "enthalpy of vaporization"}[which]
    other = {"fus": "latent heat of fusion", "vap": "latent heat of vaporization"}[which]
    url, title = {"1": (_KL_310_1, "Standard molar heat capacities and properties of melting and evaporation of the elements"),
                  "4": (_KL_310_4, "Cryoscopic and ebullioscopic constants and enthalpies of fusion and of evaporation of some common solvents")}[sect]
    return _q(f"kayelaby_latent.{key}_{which}{'_' + temp.replace('.', 'p') + 'k' if sect == '4' and temp else ''}", f"{label} of {substance}" + (f" at {temp} K" if temp else ""), f"dH_{which}({substance})", value, "", unit,
              kind="no uncertainty printed", source=_KL_310_SOURCE.format(n=sect, title=title), edition="Kaye & Laby online, v1.0", url=url, retrieved_from=url,
              keys=(f"{label} of {substance}", f"{other} of {substance}"), phrases=(f"{label} of {substance}", f"{other} of {substance}", f"latent heat of {substance}", "latent heats"),
              notes=(note, _KL_RETIRED))


FERRO_LATENT: tuple[Quantity, ...] = (
    _kl_js("fe", "iron", "Iron, high purity (single crystals in preferred direction)", "2.16", "770"),
    _kl_js("co", "cobalt", "Cobalt", "1.76", "1115"),
    _kl_js("ni", "nickel", "Nickel", "0.615", "358"),
    _danan("fe", "iron", "sigma", "221.71", "0.08", "emu g^-1", "sigma_0,infinity = 221.71 +- 0.08 emu/g, corresponding to M = 2.216 mu_B"),
    _danan("fe", "iron", "moment", "2.216", "", "mu_B", "sigma_0,infinity = 221.71 +- 0.08 emu/g, corresponding to M = 2.216 mu_B"),
    _danan("ni", "nickel", "sigma", "58.57", "0.03", "emu g^-1", "sigma_0,infinity = 58.57 +- 0.03 emu/g, corresponding to M = 0.616 mu_B (1.6% above Weiss and Forrer's 0.606 mu_B)"),
    _danan("ni", "nickel", "moment", "0.616", "", "mu_B", "sigma_0,infinity = 58.57 +- 0.03 emu/g, corresponding to M = 0.616 mu_B (1.6% above Weiss and Forrer's 0.606 mu_B)"),
    _q("myers1951.co_hcp_sigma0", "spontaneous magnetization of hexagonal cobalt extrapolated to 0 K", "sigma_0(Co hcp)", "162.55", "", "",
       kind="no uncertainty printed", source="H. P. Myers and W. Sucksmith, The spontaneous magnetization of cobalt, Proc. R. Soc. Lond. A 207, 427-446 (1951), doi:10.1098/rspa.1951.0132, abstract",
       edition="Proc. R. Soc. A 207 (1951)", url="https://doi.org/10.1098/rspa.1951.0132", retrieved_from=_OA + "10.1098/rspa.1951.0132",
       keys=("saturation magnetization", "saturation magnetization of cobalt"), phrases=("saturation magnetization of cobalt", "spontaneous magnetization of cobalt", "magnetic moments of ferromagnets"),
       notes=("The abstract says: 'By extrapolation the value 162.55 was determined for the spontaneous magnetization of hexagonal cobalt at absolute zero of temperature.'",
              "The abstract prints no unit for 162.55, so none is stored; measured with Sucksmith's magnetic balance from -183 to 1121 C.")),
    _q("nigh1963.gd_moment", "absolute saturation magnetic moment of gadolinium (single crystal)", "M_s(Gd)", "7.55", "", "mu_B",
       kind="no uncertainty printed", source="H. E. Nigh, S. Legvold, and F. H. Spedding, Magnetization and Electrical Resistivity of Gadolinium Single Crystals, Phys. Rev. 132, 1092-1097 (1963), doi:10.1103/PhysRev.132.1092, abstract",
       edition="Phys. Rev. 132 (1963)", url="https://doi.org/10.1103/PhysRev.132.1092", retrieved_from=_OA + "10.1103/PhysRev.132.1092",
       keys=("saturation magnetization", "saturation magnetization of gadolinium"), phrases=("saturation magnetization of gadolinium", "magnetic moment of gadolinium", "magnetic moments of ferromagnets"),
       notes=("The abstract says: 'The absolute saturation magnetic moment was found to be 7.55 Bohr magnetons/atom.' It also reports a ferromagnetic Curie temperature of 293.2 K.",
              "Fields 0 to 18 kOe along three crystal axes, 1.4 to 900 K.")),
    _kl_latent("water", "water", "fus", "333", "J g^-1", "", "4", "The solvent table prints for H2O: k_fus 1.86, k_vap 0.51 K kg mol-1, massic enthalpy of fusion 333 J g-1, and of evaporation 2257 J g-1."),
    _kl_latent("water", "water", "vap", "2257", "J g^-1", "", "4", "The solvent table prints for H2O: k_fus 1.86, k_vap 0.51 K kg mol-1, massic enthalpy of fusion 333 J g-1, and of evaporation 2257 J g-1 (at the normal boiling temperature, per the page)."),
    _kl_latent("water_osg", "water", "vap", "2500.58", "J g^-1", "273.150", "4", "The page prints massic enthalpies of evaporation of water 'calculated, with temperatures T90 on ITS-90, from those measured by Osborne, Stimson, and Ginnings (1939)'; the row T90 = 273.150 K gives 2500.58 J g-1."),
    _kl_latent("water_osg", "water", "vap", "2256.57", "J g^-1", "373.124", "4", "The page prints massic enthalpies of evaporation of water 'calculated, with temperatures T90 on ITS-90, from those measured by Osborne, Stimson, and Ginnings (1939)'; the row T90 = 373.124 K gives 2256.57 J g-1."),
    _kl_latent("nitrogen", "nitrogen", "fus", "87", "R K", "", "1", "The N2 column prints T_fus 63.2 K and molar enthalpy of fusion 87 in units of R K (Delta H / (R K) = 87), with R = 8.314 51 J K-1 mol-1 given on the page; the value is stored in R K as printed."),
    _kl_latent("nitrogen", "nitrogen", "vap", "672", "R K", "", "1", "The N2 column prints T_vap 77.34 K and molar enthalpy of evaporation 672 in units of R K; the value is stored in R K as printed."),
    _kl_latent("helium", "helium", "fus", "2.4", "R K", "", "1", "The He column prints T_fus 3.5 K and molar enthalpy of fusion 2.4 in units of R K; the page gives no pressure for helium's melting point. Stored in R K as printed."),
    _kl_latent("helium", "helium", "vap", "9.6", "R K", "", "1", "The He column prints T_vap 4.22 K and molar enthalpy of evaporation 9.6 in units of R K; the value is stored in R K as printed."),
)

_DIP_URL = "https://cccbdb.nist.gov/diplistx.asp"
_DIP_SOURCE = CCCBDB_SOURCE.replace("Experimental > Energy > Atomization Energy.", "Experimental > Electrostatics > Dipole (list of experimental dipole moments).")


def _dipole(key: str, mol: str, name: str, value: str, unc: str, row: str, ref: str) -> Quantity:
    m = mol.lower()
    return _q(f"cccbdb_dip.{key}", f"electric dipole moment of {name} ({mol}, ground state)", f"mu({mol})", value, unc, "D",
              kind="uncertainty as printed, level not stated" if unc else "no uncertainty printed", source=_DIP_SOURCE, edition="CCCBDB experimental dipoles",
              url=_DIP_URL, retrieved_from=_DIP_URL, keys=(f"dipole moment of {m}", f"dipole moment of {name}"), phrases=(f"dipole moment of {m}", f"dipole moment of {name}", f"{name} dipole moment", "molecular dipole moments"),
              notes=(f"The list ('Dipole moments in Debye') prints the row: {row}.", f"Squib: {ref}."))


_KL_393 = "https://web.archive.org/web/20170214104813/http://www.kayelaby.npl.co.uk/chemistry/3_9/3_9_3.html"
_KL_398 = "https://web.archive.org/web/20161215143328/http://www.kayelaby.npl.co.uk/chemistry/3_9/3_9_8.html"


def _e0(key: str, couple: str, reaction: str, value: str, printed: str) -> Quantity:
    return _q(f"kayelaby_e0.{key}", f"standard electrode potential of {couple} at 25 C", f"E0({couple})", value, "", "V",
              kind="no uncertainty printed", source="Kaye & Laby, Tables of Physical and Chemical Constants (NPL online, version 1.0), Sect. 3.9.3, Standard potentials at 25 C",
              edition="Kaye & Laby online, v1.0", url=_KL_393, retrieved_from=_KL_393,
              keys=("standard electrode potential", f"electrode potential of {couple}"), phrases=(f"electrode potential of {couple}", "standard electrode potentials", "standard reduction potential"),
              notes=(f"The table prints '{reaction}' with E0/V = {printed} (IUPAC reduction convention, hydrogen electrode = 0).", _KL_RETIRED))


def _pks(key: str, salt: str, anion: str, cation: str, value: str) -> Quantity:
    return _q(f"kayelaby_ksp.{key}", f"pK_s0 (negative log solubility product) of {salt} in water", f"pK_s0({salt})", value, "", "",
              kind="no uncertainty printed", source="Kaye & Laby, Tables of Physical and Chemical Constants (NPL online, version 1.0), Sect. 3.9.8, Solubility products in aqueous solutions",
              edition="Kaye & Laby online, v1.0", url=_KL_398, retrieved_from=_KL_398,
              keys=("solubility product", f"solubility product of {salt}"), phrases=(f"solubility product of {salt}", f"{salt} solubility product", "solubility products"),
              notes=(f"Anion '{anion}', cation '{cation}': pK_s0 = {value}.", "The page says most values relate to 298 K and zero ionic strength, with others in Sillen and Martell (1964); it does not mark which.", _KL_RETIRED))


def _comb(key: str, cas: str, mol: str, phase: str, value: str, unc: str, ref: str, extra: str = "") -> Quantity:
    url = f"https://webbook.nist.gov/cgi/cbook.cgi?ID={cas}&Mask=3"
    return _q(f"webbook_comb.{key}", f"standard enthalpy of combustion of {mol} ({phase}), {ref}", f"dcH({mol})", value, unc, "kJ mol^-1",
              kind="uncertainty as printed, level not stated", source=f"NIST Chemistry WebBook, SRD 69, {mol} thermochemistry (Mask=3), Delta_cH {phase} row from {ref}",
              edition="NIST Chemistry WebBook, SRD 69", url=url, retrieved_from=url,
              keys=("enthalpy of combustion", f"enthalpy of combustion of {mol.lower()}", f"heat of combustion of {mol.lower()}"),
              phrases=(f"enthalpy of combustion of {mol.lower()}", f"heat of combustion of {mol.lower()}", "enthalpies of combustion"),
              notes=(f"The WebBook row prints Delta_cH {phase} = {value} +- {unc} kJ/mol, method Ccb or Cm, reference {ref}.",) + ((extra,) if extra else ()))


CHEM_B17: tuple[Quantity, ...] = (
    _dipole("h2o", "H2O", "water", "1.857", "", "H2O, Water, 1A1, tot 1.857, comment mu_0 = 1.85498", "1991Sho/Ebe:5875-5882 = S. L. Shostak, W. L. Ebenstein, and J. S. Muenter, J. Chem. Phys. 94, 5875 (1991), doi:10.1063/1.460471"),
    _dipole("nh3", "NH3", "ammonia", "1.476", "0.0029", "NH3, Ammonia, 1A1, 1.476, comment '+- 0.0029 D Laser resonance'", "1970Shi:3572-3576 = F. Shimizu, J. Chem. Phys. 52, 3572 (1970), doi:10.1063/1.1673524"),
    _dipole("hcl", "HCl", "hydrogen chloride", "1.093", "", "HCl, Hydrogen chloride, 1Sigma, 1.093, comment MB", "NISTDiatomic"),
    _dipole("co", "CO", "carbon monoxide", "0.112", "", "CO, Carbon monoxide, 1Sigma, 0.112, comment MW", "NSRDS-NBS10 = R. D. Nelson, D. R. Lide, and A. A. Maryott, Selected values of electric dipole moments for molecules in the gas phase, NSRDS-NBS 10 (1967)"),
    _dipole("hf", "HF", "hydrogen fluoride", "1.827", "", "HF, Hydrogen fluoride, 1Sigma, 1.827, comment MB", "NISTDiatomic"),
    _e0("li", "Li+/Li", "Li+ + e- -> Li", "-3.045", "- 3.045"),
    _e0("na", "Na+/Na", "Na+ + e- -> Na", "-2.714", "- 2.714"),
    _e0("zn", "Zn2+/Zn", "Zn2+ + 2e- -> Zn", "-0.762 6", "- 0.762 6"),
    _e0("cu", "Cu2+/Cu", "Cu2+ + 2e- -> Cu", "+0.340", "+ 0.340"),
    _e0("ag", "Ag+/Ag", "Ag+ + e- -> Ag", "+0.799 1", "+ 0.799 1"),
    _e0("agcl", "AgCl/Ag", "AgCl + e- -> Ag + Cl-", "+0.222 3", "+ 0.222 3"),
    _e0("cl2", "Cl2/Cl-", "Cl2 + 2e- -> 2Cl-", "+1.358 3", "+ 1.358 3"),
    _e0("o2", "O2/H2O", "O2 + 4H+ + 4e- -> 2H2O", "+1.229", "+ 1.229"),
    _pks("agcl", "silver chloride", "chloride", "silver (I)", "9.749"),
    _pks("agbr", "silver bromide", "bromide", "silver (I)", "12.30"),
    _pks("agi", "silver iodide", "iodide", "silver (I)", "16.08"),
    _pks("baso4", "barium sulfate", "sulphate", "barium", "9.99"),
    _pks("caco3", "calcium carbonate", "carbonate", "calcium", "8.32"),
    _pks("caf2", "calcium fluoride", "fluoride", "calcium", "10.31"),
    _pks("mgoh2", "magnesium hydroxide", "hydroxide", "magnesium", "11.3"),
    _pks("feoh3", "iron(III) hydroxide", "hydroxide", "iron (III)", "39.43"),
    _comb("ch4_pittam1972", "C74828", "Methane", "gas", "-890.7", "0.4", "Pittam and Pilcher, 1972"),
    _comb("ch4_prosen1945", "C74828", "Methane", "gas", "-890.35", "0.30", "Prosen and Rossini, 1945", "The WebBook lists four methane values (Pittam and Pilcher 1972, Prosen and Rossini 1945, Roth and Banse 1932, Rossini 1931); two are stored and both are kept."),
    _comb("c2h6_pittam1972", "C74840", "Ethane", "gas", "-1560.7", "0.3", "Pittam and Pilcher, 1972"),
    _comb("c3h8_pittam1972", "C74986", "Propane", "gas", "-2219.2", "0.46", "Pittam and Pilcher, 1972"),
    _comb("c2h5oh_chao1965", "C64175", "Ethanol", "liquid", "-1367.6", "0.3", "Chao and Rossini, 1965"),
)

ASD_QUERY_RB_CS = (
    "https://physics.nist.gov/cgi-bin/ASD/ie.pl?spectra=Rb-Cs&submit=Retrieve+Data&units=1&format=2&order=0"
    "&at_num_out=on&sp_name_out=on&ion_charge_out=on&el_name_out=on&seq_out=on&shells_out=on&level_out=on"
    "&ion_conf_out=on&e_out=0&unc_out=on&biblio=on"
)


def _asd_rbcs(id: str, z: int, element: str, spectrum: str, value_text: str, uncertainty_text: str, shells: str, level: str, ionized: str, refs: str) -> Quantity:
    lower = element.lower()
    names = (lower, "caesium") if lower == "cesium" else (lower,)
    return _q(id, f"first ionization energy of {lower} ({spectrum}, Z = {z})", f"E_i({spectrum})", value_text, uncertainty_text, "eV",
              kind="uncertainty as printed, level not stated", source=ASD_SOURCE, edition="NIST ASD ionization energies, as served 2026-11-25 (Rb-Cs query)",
              url=ASD_QUERY_RB_CS, retrieved_from=ASD_QUERY_RB_CS, keys=(),
              phrases=tuple(p for n in names for p in (f"ionization energy of {n}", f"{n} ionization energy", f"ionisation energy of {n}")),
              notes=(f"ASD ground shells {shells}, ground level {level}, ionized level {ionized}.", f"ASD bibliography codes: {refs}.",
                     "ASD prints this energy without brackets or parentheses, with the per-row uncertainty stored here.", _ASD_EV))


_IS_OA = "https://api.openalex.org/works/doi:"


def _ca_is(a: str, value: str, unc: str, printed: str) -> Quantity:
    return _q(f"knollmann2019.ca{a}_ca40_729nm", f"isotope shift of the Ca+ 4s 2S1/2 - 3d 2D5/2 (729 nm) transition, {a}Ca+ relative to 40Ca+", f"dnu({a}-40, Ca+ 729)", value, unc, "Hz",
              kind="uncertainty as printed, level not stated",
              source="F. Knollmann, A. N. Patel, and S. C. Doret, Part-per-billion measurement of the 4 2S1/2 -> 3 2D5/2 electric-quadrupole-transition isotope shifts between 42,44,48Ca+ and 40Ca+, Phys. Rev. A 100, 022514 (2019), doi:10.1103/PhysRevA.100.022514, abstract",
              edition="Phys. Rev. A 100 (2019)", url="https://doi.org/10.1103/PhysRevA.100.022514", retrieved_from=_IS_OA + "10.1103/PhysRevA.100.022514",
              keys=("isotope shift", "calcium ion isotope shift"), phrases=("isotope shift of calcium", "ca+ isotope shift", "isotope shifts"),
              notes=(f"The abstract prints shifts of 2 771 872 467.6(7.6), 5 340 887 394.6(7.8), and 9 990 381 870.0(6.3) Hz between 42,44,48Ca+ and 40Ca+; this is the {printed} entry.",
                     "Co-trapped ions excited simultaneously from one laser's sidebands."))


def _hd(key: str, ref: str, doi: str, value: str, unc: str, unit: str, printed: str, extra: str) -> Quantity:
    return _q(f"{key}.h_d_1s2s_isotope_shift", f"hydrogen-deuterium isotope shift of the 1S-2S two-photon transition ({ref})", "dnu(H-D, 1S-2S)", value, unc, unit,
              kind="uncertainty as printed, level not stated", source=f"{ref}, doi:{doi}, abstract", edition=ref.split(", ")[-1],
              url=f"https://doi.org/{doi}", retrieved_from=_IS_OA + doi,
              keys=("isotope shift", "hydrogen deuterium isotope shift"), phrases=("hydrogen-deuterium isotope shift", "h-d isotope shift", "1s-2s isotope shift", "isotope shifts"),
              notes=(f"Printed in the abstract as {printed}.", extra))


ATOMIC_B17: tuple[Quantity, ...] = (
    _asd_rbcs("asd512.ie.rb", 37, "Rubidium", "Rb I", "4.1771281", "0.0000012", "[Kr].5s", "2S<1/2>", "4p6 1S<0>", "L4740, L5783"),
    _asd_rbcs("asd512.ie.sr", 38, "Strontium", "Sr I", "5.69486745", "0.00000012", "[Kr].5s2", "1S0", "5s 2S<1/2>", "L15350, L5644"),
    _asd_rbcs("asd512.ie.y", 39, "Yttrium", "Y I", "6.21726", "0.00010", "[Kr].4d.5s2", "2D<3/2>", "5s2 1S<0>", "L8844, L2111, L9735"),
    _asd_rbcs("asd512.ie.zr", 40, "Zirconium", "Zr I", "6.634126", "0.000005", "[Kr].4d2.5s2", "3F<2>", "4d2.5s 4F<3/2>", "L21107"),
    _asd_rbcs("asd512.ie.nb", 41, "Niobium", "Nb I", "6.75885", "0.00004", "[Kr].4d4.5s", "6D<1/2>", "4d4 5D<0>", "L6829"),
    _asd_rbcs("asd512.ie.mo", 42, "Molybdenum", "Mo I", "7.09243", "0.00004", "[Kr].4d5.5s", "7S<3>", "4d5 6S<5/2>", "L6829"),
    _asd_rbcs("asd512.ie.tc", 43, "Technetium", "Tc I", "7.11938", "0.00003", "[Kr].4d5.5s2", "6S<5/2>", "4d5.5s 7S<3>", "L15237"),
    _asd_rbcs("asd512.ie.ru", 44, "Ruthenium", "Ru I", "7.36050", "0.00005", "[Kr].4d7.5s", "5F<5>", "4d7 4F<9/2>", "L10032"),
    _asd_rbcs("asd512.ie.rh", 45, "Rhodium", "Rh I", "7.45890", "0.00005", "[Kr].4d8.5s", "4F<9/2>", "4d8 3F<4>", "L10032"),
    _asd_rbcs("asd512.ie.pd", 46, "Palladium", "Pd I", "8.336839", "0.000010", "[Kr].4d10", "1S0", "4d9 2D<5/2>", "L20363"),
    _asd_rbcs("asd512.ie.ag", 47, "Silver", "Ag I", "7.576234", "0.000025", "[Kr].4d10.5s", "2S<1/2>", "4d10 1S<0>", "L11835"),
    _asd_rbcs("asd512.ie.cd", 48, "Cadmium", "Cd I", "8.993820", "0.000016", "[Kr].4d10.5s2", "1S0", "5s 2S<1/2>", "L18843"),
    _asd_rbcs("asd512.ie.in", 49, "Indium", "In I", "5.7863558", "0.0000005", "[Cd].5p", "2P*<1/2>", "5s2 1S<0>", "L21649"),
    _asd_rbcs("asd512.ie.sn", 50, "Tin", "Sn I", "7.343918", "0.000012", "[Cd].5p2", "3P0", "5s2.5p 2P*<1/2>", "L3936"),
    _asd_rbcs("asd512.ie.sb", 51, "Antimony", "Sb I", "8.608389", "0.000012", "[Cd].5p3", "4S*<3/2>", "5s2.5p2 3P<0>", "L8844, L6684"),
    _asd_rbcs("asd512.ie.te", 52, "Tellurium", "Te I", "9.009808", "0.000006", "[Cd].5p4", "3P<2>", "5s2.5p3 4S*<3/2>", "L21109"),
    _asd_rbcs("asd512.ie.i", 53, "Iodine", "I I", "10.451236", "0.000025", "[Cd].5p5", "2P*<3/2>", "5s2.5p4 3P<2>", "L13998, L22518"),
    _asd_rbcs("asd512.ie.xe", 54, "Xenon", "Xe I", "12.1298437", "0.0000015", "[Cd].5p6", "1S0", "5s2.5p5 2P*<3/2>", "L12013, L9794, L6426"),
    _asd_rbcs("asd512.ie.cs", 55, "Cesium", "Cs I", "3.89390572743", "0.00000000017", "[Xe].6s", "2S<1/2>", "5s2.5p6 1S<0>", "L19479"),
    _hd("parthey2010", "C. G. Parthey et al., Precision Measurement of the Hydrogen-Deuterium 1S-2S Isotope Shift, Phys. Rev. Lett. 104, 233001 (2010)", "10.1103/PhysRevLett.104.233001",
        "670 994 334 606", "15", "Hz", "670,994,334,606(15) Hz", "The abstract calls this a 10-times improvement over Huber et al. 1998, 'confirming its frequency value'; both are kept."),
    _hd("huber1998", "A. Huber et al., Hydrogen-Deuterium 1S-2S Isotope Shift and the Structure of the Deuteron, Phys. Rev. Lett. 80, 468 (1998)", "10.1103/PhysRevLett.80.468",
        "670 994 334.64", "0.15", "kHz", "670994334.64(15) kHz", "Measured with an optical frequency comb and a CH4-stabilized He-Ne reference."),
    _ca_is("42", "2 771 872 467.6", "7.6", "42Ca+"),
    _ca_is("44", "5 340 887 394.6", "7.8", "44Ca+"),
    _ca_is("48", "9 990 381 870.0", "6.3", "48Ca+"),
)

_NLEN_URL = "https://www.ncnr.nist.gov/resources/n-lengths/list.html"
_NLEN_SOURCE = ("V. F. Sears, Neutron scattering lengths and cross sections, Neutron News 3 (3), 29-37 (1992), as tabulated by the NIST Center for Neutron Research, "
                "column 8: absorption cross section for 2200 m/s neutrons")


def _sigma_a(key: str, nuclide: str, label: str, value: str, unc: str, row: str) -> Quantity:
    return _q(f"sears1992.{key}_sigma_abs", f"thermal (2200 m/s) neutron absorption cross section of {nuclide}", f"sigma_a({label})", value, unc, "b",
              kind="uncertainty as printed, level not stated" if unc else "no uncertainty printed", source=_NLEN_SOURCE, edition="Neutron News 3 (1992), via NIST NCNR",
              url=_NLEN_URL, retrieved_from=_NLEN_URL,
              keys=("thermal neutron cross section", f"neutron absorption cross section of {nuclide}"),
              phrases=(f"thermal neutron cross section of {nuclide}", f"neutron absorption cross section of {nuclide}", f"{label} cross section", "thermal neutron cross sections"),
              notes=(f"The NCNR row reads '{row}'; the last column is the 2200 m/s absorption cross section in barn, uncertainty in parentheses.",))


_LC_NOTE = "Read from the IAEA LiveChart of Nuclides API, ground_states set (rows extracted 2023-10-18)."


def _spin(key: str, nuclide: str, jp: str, value: str, cutoff: str) -> Quantity:
    return _q(f"ensdf.spin_{key}", f"ground-state nuclear spin of {nuclide} (ENSDF)", f"J({nuclide})", value, "", "hbar",
              kind="no uncertainty printed", source="Evaluated Nuclear Structure Data File (ENSDF), as served by the IAEA LiveChart of Nuclides API", edition=f"ENSDF, publication cut-off {cutoff}",
              url="https://www.nndc.bnl.gov/ensdf/", retrieved_from=_LIVECHART_URL,
              keys=("nuclear spin", f"nuclear spin of {nuclide}"), phrases=(f"nuclear spin of {nuclide}", f"spin of {nuclide}", "nuclear spins"),
              notes=(f"The API row prints jp = {jp}; the spin {value} is stored and the parity is in this note.", _LC_NOTE))


def _qmom(key: str, nuclide: str, value: str, unc: str, cutoff: str) -> Quantity:
    return _q(f"livechart.q_{key}", f"ground-state electric quadrupole moment of {nuclide}", f"Q({nuclide})", value, unc, "b",
              kind="uncertainty as printed, level not stated", source="IAEA LiveChart of Nuclides API, ground_states set, electric_quadrupole column", edition=f"LiveChart ground states (ENSDF cut-off {cutoff})",
              url=_LIVECHART_URL, retrieved_from=_LIVECHART_URL,
              keys=("nuclear quadrupole moment", f"quadrupole moment of {nuclide}"), phrases=(f"quadrupole moment of {nuclide}", f"nuclear quadrupole moment of {nuclide}", "nuclear quadrupole moments"),
              notes=(f"The API row prints electric_quadrupole {value} and unc_eq {unc} (barn).", _LC_NOTE))


_RCT1 = "https://www-nds.iaea.org/amdc/ame2020/rct1.mas20.txt"
_RCT2 = "https://www-nds.iaea.org/amdc/ame2020/rct2_1.mas20.txt"


def _ameq(key: str, column: str, row: str, reaction: str, value: str, unc: str, file: str, phrases: tuple[str, ...]) -> Quantity:
    url = _RCT1 if file == "rct1" else _RCT2
    return _q(f"ame2020.q_{key}", f"AME2020 reaction energy {column} on the {row} row ({reaction})", f"{column}({row})", value, unc, "keV",
              kind="standard uncertainty", source=AME2020_SOURCE.replace("file mass.mas20", f"file {file}.mas20"), edition=AME2020_EDITION, url=url, retrieved_from=url,
              keys=("q-value", f"q-value of {reaction}"), phrases=phrases + ("q-value", "reaction q-values"),
              notes=(f"File {file}.mas20 prints, on the {row} row, {column} = {value} +- {unc} keV.", _AME_SIGMA,
                     "AME prints the Q-value directly; no fission Q-value is printed in these files, so none is stored."))


NUCLEAR_B17: tuple[Quantity, ...] = (
    _sigma_a("h1", "hydrogen-1", "1H", "0.3326", "", "1H 99.985 -3.7406 25.274 1.7583 80.27 82.03 0.3326"),
    _sigma_a("he3", "helium-3", "3He", "5333.", "7.", "3He 0.00014 5.74-1.483 i -2.5+2.568 i 4.42 1.6 6 5333.(7.)"),
    _sigma_a("li6", "lithium-6", "6Li", "940.", "4.", "6Li 7.5 2.00-0.261 i -1.89+0.26 i 0.51 0.46 0.97 940.(4.)"),
    _sigma_a("b10", "boron-10", "10B", "3835.", "9.", "10B 20 -0.1-1.066 i -4.7+1.231 i 0.144 3 3.1 3835.(9.)"),
    _sigma_a("cd113", "cadmium-113", "113Cd", "20600.", "400.", "113Cd 12.22 -8.0-5.73 i --- 12.1 0.3 12.4 20600.(400.)"),
    _sigma_a("gd157", "gadolinium-157", "157Gd", "259000.", "700.", "157Gd 15.7 -1.14-71.9 i (+/-)5.(5.)-55.8 i 650.(4.) 394.(7.) 1044.(8.) 259000.(700.)"),
    _sigma_a("u235", "uranium-235", "235U", "680.9", "1.1", "235U 0.72 10.47 (+/-)1.3 13.78 0.2 14 680.9(1.1)"),
    _spin("h2", "deuterium (2H)", "1+", "1", "1-May-2003"),
    _spin("li7", "lithium-7", "3/2-", "3/2", "23-Aug-2001"),
    _spin("b10", "boron-10", "3+", "3", "31-Mar-2004"),
    _spin("n14", "nitrogen-14", "1+", "1", "1-JUL-1990"),
    _spin("o17", "oxygen-17", "5/2+", "5/2", "5-Aug-2021"),
    _spin("al27", "aluminium-27", "5/2+", "5/2", "30-Nov-2010"),
    _spin("cs133", "cesium-133", "7/2+", "7/2", "31-Oct-2010"),
    _spin("u235", "uranium-235", "7/2-", "7/2", "1-Feb-2014"),
    _qmom("h2", "deuterium (2H)", "0.0028578", "0.0000003", "1-May-2003"),
    _qmom("li7", "lithium-7", "-0.04", "0.0003", "23-Aug-2001"),
    _qmom("b10", "boron-10", "0.0846", "0.0002", "31-Mar-2004"),
    _qmom("n14", "nitrogen-14", "0.02044", "0.00003", "1-JUL-1990"),
    _qmom("o17", "oxygen-17", "-0.0256", "0.0002", "5-Aug-2021"),
    _qmom("al27", "aluminium-27", "0.1466", "0.001", "30-Nov-2010"),
    _qmom("cs133", "cesium-133", "-0.00343", "0.0001", "31-Oct-2010"),
    _qmom("u235", "uranium-235", "4.936", "0.006", "1-Feb-2014"),
    _ameq("alpha_po210", "Q(a)", "210Po", "alpha decay of 210Po", "5407.5307", "0.0713", "rct1", ("alpha decay q-value of polonium-210", "q-value of 210po")),
    _ameq("alpha_ra226", "Q(a)", "226Ra", "alpha decay of 226Ra", "4870.7028", "0.2545", "rct1", ("alpha decay q-value of radium-226", "q-value of 226ra")),
    _ameq("alpha_u238", "Q(a)", "238U", "alpha decay of 238U", "4269.8581", "2.1157", "rct1", ("alpha decay q-value of uranium-238", "q-value of 238u")),
    _ameq("alpha_am241", "Q(a)", "241Am", "alpha decay of 241Am", "5637.8203", "0.1199", "rct1", ("alpha decay q-value of americium-241", "q-value of 241am")),
    _ameq("d_alpha_h3", "Q(d,a)", "3H", "3H(d,a)n, D-T fusion", "17589.2999", "0.0005", "rct2", ("d-t fusion energy release", "fusion energy release", "q-value of d-t fusion")),
    _ameq("d_alpha_he3", "Q(d,a)", "3He", "3He(d,a)p, D-3He fusion", "18353.0548", "0.0002", "rct2", ("d-he3 fusion energy release", "fusion energy release", "q-value of d-3he fusion")),
    _ameq("d_alpha_li6", "Q(d,a)", "6Li", "6Li(d,a)4He", "22372.7716", "0.0015", "rct2", ("lithium-6 deuteron fusion energy release", "fusion energy release")),
    _ameq("p_alpha_li7", "Q(p,a)", "7Li", "7Li(p,a)4He", "17346.2440", "0.0042", "rct2", ("lithium-7 proton fusion energy release", "fusion energy release")),
    _ameq("n_alpha_li6", "Q(n,a)", "6Li", "6Li(n,a)3H, tritium breeding", "4783.4717", "0.0015", "rct2", ("tritium breeding q-value", "q-value of 6li(n,a)")),
    _ameq("n_alpha_b10", "Q(n,a)", "10B", "10B(n,a)7Li", "2789.9082", "0.0155", "rct2", ("boron-10 neutron capture q-value", "q-value of 10b(n,a)")),
)

_BOTHWELL_AAM = "https://eprints.gla.ac.uk/264685/2/264685.pdf"
_BOTHWELL_AAM_NOTE = ("Read from the Author Accepted Manuscript deposited at Enlighten (University of Glasgow) on 4 February 2022; its cover says there may be differences from the published version. "
                      "The Nature typeset version is behind a paywall and was not read. The numbers match the arXiv v1 text already stored as bothwell2022.redshift_gradient.")


def _bothwell_aam(key: str, name: str, value: str, unc: str, printed: str, extra: tuple[str, ...] = ()) -> Quantity:
    return _q(f"bothwell2022.aam_{key}", name, "d(df/f)/dz", value, unc, "mm^-1", kind=_LEVEL, source=_BOTHWELL_SOURCE,
              edition="Nature 602 (2022), Author Accepted Manuscript", url="https://doi.org/10.1038/s41586-021-04349-7", retrieved_from=_BOTHWELL_AAM,
              keys=("gravitational redshift", "optical clock"), phrases=("bothwell published version (accepted manuscript)", "millimetre redshift", "redshift within a millimeter"),
              notes=(f"The manuscript prints {printed}.",) + extra + (_BOTHWELL_AAM_NOTE,))


_TT_KEYS = ("top pair cross section", "ttbar cross section")
_TT_SPLIT = "The source prints further parts ({rest}) separately; they are kept in this note and are not combined with the stored parts."


def _ttbar(id: str, name: str, value: str, stat: str, syst: str, rest: str, source: str, edition: str, doi: str, arxiv: str, printed: str) -> Quantity:
    return _q(id, name, "sigma_tt", value, stat, "pb", kind=_SPLIT_KIND, systematic_text=syst, source=source, edition=edition,
              url=doi, retrieved_from=f"https://arxiv.org/abs/{arxiv}", keys=_TT_KEYS,
              phrases=("top pair cross section", "top quark pair production cross section", "ttbar cross section"),
              notes=(f"The abstract prints '{printed}'.", _SPLIT_NOTE) + ((_TT_SPLIT.format(rest=rest),) if rest else ()))


_ATLAS_HIGGS = "ATLAS Collaboration, A detailed map of Higgs boson interactions by the ATLAS experiment ten years after the discovery, Nature 607, 52-59 (2022), doi:10.1038/s41586-022-04893-w, HEPData record ins2104706 (doi:10.17182/hepdata.130266.v1)"
_CMS_HIGGS = "CMS Collaboration, A portrait of the Higgs boson by the CMS experiment ten years after the discovery, Nature 607, 60-68 (2022), doi:10.1038/s41586-022-04892-x, Fig. 2"


def _atlas_mu(kind_: str, key: str, label: str, value: str, up: str, down: str, table: str) -> Quantity:
    what = "production process" if kind_ == "prod" else "decay mode"
    assume = "decay branching fractions fixed to their SM values" if kind_ == "prod" else "production cross sections fixed to their SM values"
    return _q(f"atlas2022.higgs_mu_{kind_}.{key}", f"ATLAS Higgs signal strength (ratio to SM) for the {label} {what}, {assume}", f"mu_{label}", value, up, "",
              kind="68% interval", lower_text=down, source=_ATLAS_HIGGS, edition="Nature 607 (2022); HEPData v1", url="https://doi.org/10.1038/s41586-022-04893-w",
              retrieved_from=f"https://www.hepdata.net/download/table/ins2104706/{table.replace(' ', '%20')}/csv",
              keys=("higgs boson", "atlas", "atlas signal strength by channel"), phrases=(f"atlas {label} signal strength", "higgs signal strength by channel", "per-channel higgs signal strength"),
              notes=(f"HEPData table '{table}', block 'Ratio to SM', prints the row '{label},{value},{up},-{down}'.",
                     "The figure caption says the vertical bar on each point denotes the 68% confidence interval. The paper prints these only as plotted points; the numbers are from the collaboration's HEPData record."))


def _cms_mu(kind_: str, key: str, label: str, value: str, up: str, down: str, stat: str, syst: str) -> Quantity:
    what = "production mode" if kind_ == "prod" else "decay channel"
    assume = "B_f = (B_f)_SM" if kind_ == "prod" else "sigma_i = (sigma_i)_SM"
    return _q(f"cms2022.higgs_mu_{kind_}.{key}", f"CMS Higgs signal strength for the {label} {what}, assuming {assume}", f"mu_{label}", value, up, "",
              kind="68% interval", lower_text=down, source=_CMS_HIGGS, edition="Nature 607 (2022); arXiv:2207.00043 Fig. 2", url="https://doi.org/10.1038/s41586-022-04892-x",
              retrieved_from="https://arxiv.org/pdf/2207.00043",
              keys=("higgs boson", "cms", "cms signal strength by channel"), phrases=(f"cms {label} signal strength", "higgs signal strength by channel", "per-channel higgs signal strength"),
              notes=(f"Fig. 2 prints mu_{label} = {value} +{up} -{down} (total), with statistical part {stat} and systematic part {syst}; only the total 1 s.d. interval is stored.",
                     "The caption says the thick black lines indicate the 1 s.d. confidence intervals, stored here under the 68% interval kind."))


_LASER_RADIUS_NOTE = "Charge radii from laser spectroscopy are extracted from measured isotope shifts with calculated mass shifts; the paper's printed radius is stored as is."


def _laser_radius(id: str, nuclide: str, value: str, unc: str, source: str, doi: str, printed: str) -> Quantity:
    return _q(id, f"root-mean-square nuclear charge radius of {nuclide} from laser spectroscopy", f"R({nuclide})", value, unc, "fm",
              kind="uncertainty as printed, level not stated", source=source, edition="abstract, via OpenAlex", url=f"https://doi.org/{doi}", retrieved_from=f"https://api.openalex.org/works/doi:{doi}",
              keys=("charge radius", "laser spectroscopy radius", f"charge radius of {nuclide}"), phrases=("nuclear charge radii", "charge radius", "laser spectroscopy radius", "halo nucleus"),
              notes=(f"The abstract prints '{printed}'.", _LASER_RADIUS_NOTE))


_MUELLER2007 = "P. Mueller, I. A. Sulai, A. C. C. Villari, J. A. Alcantara-Nunez, R. Alves-Conde, K. Bailey, G. W. F. Drake, M. Dubois, et al., Nuclear charge radius of 8He, Phys. Rev. Lett. 99, 252501 (2007), doi:10.1103/PhysRevLett.99.252501"
_SANCHEZ2006 = "R. Sanchez, W. Noertershaeuser, G. Ewald, D. Albers, J. Behr, P. Bricault, B. A. Bushaw, A. Dax, et al., Nuclear charge radii of 9,11Li: the influence of halo neutrons, Phys. Rev. Lett. 96, 033002 (2006), doi:10.1103/PhysRevLett.96.033002"

GAPS_B18: tuple[Quantity, ...] = (
    _bothwell_aam("gradient", "fractional frequency gradient across a millimetre-scale Sr lattice clock sample, after systematic corrections (accepted manuscript)", "-9.8 e-20", "2.3 e-20",
                  "'a final frequency gradient of -9.8(2.3)x10-20/mm, consistent with the predicted redshift'"),
    _bothwell_aam("weighted_mean", "weighted-mean fractional frequency gradient over 14 datasets, before the final systematic corrections (accepted manuscript)", "-1.00 e-19", "0.12 e-19",
                  "a weighted-mean gradient of '-1.00(12)x10-19/mm' (standard error of the weighted mean)"),
    _bothwell_aam("synchronous", "fractional frequency gradient from the synchronous two-region comparison, after systematic corrections (accepted manuscript)", "-1.28 e-19", "0.27 e-19",
                  "'-1.30(18)x10-19/mm' before and 'a gradient of -1.28(27)x10-19/mm' after the additional systematic corrections"),
    _ttbar("atlas2023.ttbar_xsec_13tev", "inclusive top-quark-pair production cross section in pp collisions at 13 TeV, ATLAS dilepton e-mu, 140 fb^-1", "829", "1", "13", "luminosity 8 pb, beam energy 2 pb",
           "ATLAS Collaboration, Inclusive and differential cross-sections for dilepton ttbar production measured in sqrt(s) = 13 TeV pp collisions with the ATLAS detector, JHEP 07 (2023) 141, arXiv:2303.15340",
           "JHEP 07 (2023) 141; arXiv abstract", "https://arxiv.org/abs/2303.15340", "2303.15340", "sigma_tt = 829 +- 1 (stat) +- 13 (syst) +- 8 (lumi) +- 2 (beam) pb"),
    _ttbar("atlas2020.ttbar_xsec_13tev_ljets", "inclusive top-quark-pair production cross section in pp collisions at 13 TeV, ATLAS lepton+jets, 139 fb^-1", "830", "0.4", "36", "luminosity 14 pb",
           "ATLAS Collaboration, Measurement of the ttbar production cross-section in the lepton+jets channel at sqrt(s) = 13 TeV with the ATLAS experiment, Phys. Lett. B 810 (2020) 135797, arXiv:2006.13076",
           "Phys. Lett. B 810 (2020) 135797; arXiv abstract", "https://arxiv.org/abs/2006.13076", "2006.13076", "sigma_inc = 830 +- 0.4 (stat.) +- 36 (syst.) +- 14 (lumi.) pb, with a relative uncertainty of 4.6 %"),
    _ttbar("cms2019.ttbar_xsec_13tev", "inclusive top-quark-pair production cross section in pp collisions at 13 TeV, CMS dilepton, 35.9 fb^-1", "803", "2", "25", "luminosity 20 pb",
           "CMS Collaboration, Measurement of the ttbar production cross section, the top quark mass, and the strong coupling constant using dilepton events in pp collisions at sqrt(s) = 13 TeV, Eur. Phys. J. C 79 (2019) 368, arXiv:1812.10505",
           "Eur. Phys. J. C 79 (2019) 368; arXiv abstract", "https://arxiv.org/abs/1812.10505", "1812.10505", "sigma_tt = 803 +- 2 (stat) +- 25 (syst) +- 20 (lumi) pb, for a top quark mass parameter in the simulation of 172.5 GeV"),
    _ttbar("atlas2023.ttbar_xsec_13p6tev", "inclusive top-quark-pair production cross section in pp collisions at 13.6 TeV, ATLAS dilepton e-mu, 29 fb^-1 (2022 data)", "850", "3", "18", "luminosity 20 pb",
           "ATLAS Collaboration, Measurement of the ttbar cross section and its ratio to the Z production cross section using pp collisions at sqrt(s) = 13.6 TeV with the ATLAS detector, arXiv:2308.09529",
           "arXiv:2308.09529 abstract", "https://arxiv.org/abs/2308.09529", "2308.09529", "sigma_tt = 850 +- 3(stat.) +- 18(syst.) +- 20(lumi.) pb"),
    _atlas_mu("prod", "ggf_bbh", "ggF+bbH", "1.026", "0.06976", "0.06676", "Figure 2a"),
    _atlas_mu("prod", "vbf", "VBF", "1.1018", "0.13456", "0.12367", "Figure 2a"),
    _atlas_mu("prod", "wh", "WH", "1.1583", "0.22772", "0.21686", "Figure 2a"),
    _atlas_mu("prod", "zh", "ZH", "0.96205", "0.2213", "0.20568", "Figure 2a"),
    _atlas_mu("prod", "tth", "ttH", "0.73963", "0.24434", "0.23811", "Figure 2a"),
    _atlas_mu("prod", "th", "tH", "6.6137", "4.2384", "3.7563", "Figure 2a"),
    _atlas_mu("decay", "bb", "bb", "0.90952", "0.1458", "0.13908", "Figure 2b"),
    _atlas_mu("decay", "ww", "WW", "1.1951", "0.11902", "0.11211", "Figure 2b"),
    _atlas_mu("decay", "tautau", "tautau", "0.9613", "0.12234", "0.11378", "Figure 2b"),
    _atlas_mu("decay", "zz", "ZZ", "1.0415", "0.10774", "0.10007", "Figure 2b"),
    _atlas_mu("decay", "gamma_gamma", "gammagamma", "1.0883", "0.095217", "0.089531", "Figure 2b"),
    _atlas_mu("decay", "z_gamma", "Zgamma", "2.0991", "0.98358", "0.94682", "Figure 2b"),
    _atlas_mu("decay", "mu_mu", "mumu", "1.2135", "0.6178", "0.60331", "Figure 2b"),
    _cms_mu("prod", "ggh", "ggH", "0.97", "0.08", "0.07", "+-0.04", "+0.07 -0.06"),
    _cms_mu("prod", "vbf", "VBF", "0.80", "0.12", "0.12", "+0.09 -0.10", "+0.08 -0.07"),
    _cms_mu("prod", "wh", "WH", "1.44", "0.26", "0.25", "+-0.21", "+0.16 -0.15"),
    _cms_mu("prod", "zh", "ZH", "1.29", "0.22", "0.25", "+-0.20", "+0.09 -0.14"),
    _cms_mu("prod", "tth", "ttH", "0.94", "0.20", "0.19", "+-0.15", "+0.13 -0.12"),
    _cms_mu("prod", "th", "tH", "6.05", "2.66", "2.42", "+2.06 -1.99", "+1.69 -1.38"),
    _cms_mu("decay", "gamma_gamma", "gammagamma", "1.13", "0.09", "0.09", "+-0.06", "+0.07 -0.06"),
    _cms_mu("decay", "zz", "ZZ", "0.97", "0.12", "0.11", "+0.08 -0.07", "+0.09 -0.08"),
    _cms_mu("decay", "ww", "WW", "0.97", "0.09", "0.09", "+-0.05", "+-0.08"),
    _cms_mu("decay", "tautau", "tautau", "0.85", "0.10", "0.10", "+-0.06", "+-0.08"),
    _cms_mu("decay", "bb", "bb", "1.05", "0.22", "0.21", "+-0.15", "+0.16 -0.15"),
    _cms_mu("decay", "mu_mu", "mumu", "1.21", "0.45", "0.42", "+0.42 -0.38", "+0.17 -0.16"),
    _cms_mu("decay", "z_gamma", "Zgamma", "2.59", "1.07", "0.96", "+0.97 -0.93", "+0.45 -0.25"),
    _laser_radius("mueller2007.r_he8", "8He", "1.93", "0.03", _MUELLER2007, "10.1103/PhysRevLett.99.252501",
                  "The root-mean-square (rms) nuclear charge radius of 8He ... has been determined for the first time to be 1.93(3) fm"),
    _laser_radius("mueller2007.r_he6", "6He", "2.068", "0.011", _MUELLER2007, "10.1103/PhysRevLett.99.252501",
                  "the rms charge radius of 6He was measured to be 2.068(11) fm, in excellent agreement with a previous result"),
    _laser_radius("sanchez2006.r_li9", "9Li", "2.217", "0.035", _SANCHEZ2006, "10.1103/PhysRevLett.96.033002",
                  "The charge radius decreases monotonically from 6Li to 9Li, and then increases from 2.217(35) to 2.467(37) fm for 11Li"),
    _laser_radius("sanchez2006.r_li11", "11Li", "2.467", "0.037", _SANCHEZ2006, "10.1103/PhysRevLett.96.033002",
                  "The charge radius decreases monotonically from 6Li to 9Li, and then increases from 2.217(35) to 2.467(37) fm for 11Li"),
    _am2013("he6", "6He", "2.0660", "0.0111"),
    _am2013("he8", "8He", "1.9239", "0.0306"),
    _am2013("li6", "6Li", "2.5890", "0.0390"),
    _am2013("li7", "7Li", "2.4440", "0.0420"),
    _am2013("li9", "9Li", "2.2450", "0.0460"),
    _am2013("li11", "11Li", "2.4820", "0.0430"),
    _am2013("be9", "9Be", "2.5190", "0.0120"),
    _am2013("b11", "11B", "2.4060", "0.0294"),
    _am2013("n14", "14N", "2.5582", "0.0070"),
    _am2013("na23", "23Na", "2.9936", "0.0021"),
    _am2013("ca44", "44Ca", "3.5179", "0.0021"),
    _am2013("fe56", "56Fe", "3.7377", "0.0016"),
    _am2013("ni58", "58Ni", "3.7757", "0.0020"),
    _am2013("sn120", "120Sn", "4.6519", "0.0021"),
    _am2013("au197", "197Au", "5.4371", "0.0038"),
    _am2013("bi209", "209Bi", "5.5211", "0.0906"),
)


QUANTITIES = QUANTITIES + IUPAC_ATOMIC_WEIGHTS + CHEMISTRY + CONDENSED_MATTER + PARTICLE_B5 + ASTROPHYSICS + NUCLEAR_PARTICLE_B6 + ATOMIC_MOLECULAR_B6 + EARLY_UNIVERSE + EXOTIC_QED + NULL_RESULTS + THERMO_FLUIDS + OPTICS + MECHANICS_EM + EARTH_ROTATION + REDSHIFT_ZPOLE + NUCLEAR_DECAY_RADII + EM_EXTRAS + CONDENSED_EXTRAS + FLUIDS_HELIUM + CLOCKS_FRAME_LLR + PARTICLE_EXTRAS + OPTICS_EXTRAS + PARTICLE_HADRONS_BR + GRAV_EVENTS_SKYTREE + EM_MATERIALS + DESI_DR2_BAO + BOREXINO + BOLTZMANN_PRE2019 + ELECTRON_MASS_PENNING + POUND_REBKA_1960 + SME_LIMITS + NULL_B13 + COSMO_B13 + QED_B13 + ASTRO_B13 + FLUIDS_B14 + DEBYE_B14 + CCM_B14 + QED_ASTRO_B14 + TRANSPORT_B15 + MECHANICS_B15 + ATOMIC_B15 + EMOPTICS_B15 + LATTICE_CONSTANTS + VIRIAL_CRITICAL + MOLECULAR_CONSTANTS + CLOCKS_POLARIZABILITY_HALFLIVES + FERRO_LATENT + CHEM_B17 + ATOMIC_B17 + NUCLEAR_B17 + GAPS_B18
BOUNDS = BOUNDS + IUPAC_ATOMIC_WEIGHT_INTERVALS + HIGGS_WIDTH_BOUNDS + NULL_BOUNDS + GPA_BOUND + COULOMB_BOUNDS + NULL_B13_BOUNDS


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
        if item.truncated:
            item.truncation_bounds
        else:
            item.value
        if item.uncertainty_kind == _NONE_KIND:
            if item.uncertainty_text or item.lower_text or item.printed:
                raise ValueError(f"{item.id} prints no uncertainty, so it cannot carry one")
        elif item.uncertainty_kind in _RELATIVE_KINDS:
            if item.lower_text or item.printed or not item.relative_uncertainty or item.relative_uncertainty <= 0:
                raise ValueError(f"{item.id} needs one positive ppm figure and nothing else")
        elif not item.exact:
            upper = item.uncertainty
            lower = item.lower_uncertainty
            if upper is None or lower is None or upper <= 0 or lower <= 0:
                raise ValueError(f"{item.id} needs a positive uncertainty")
        elif item.lower_text:
            raise ValueError(f"{item.id} is exact and cannot carry an interval")
        if item.lower_text and item.uncertainty_kind not in _ASYMMETRIC_KINDS | {_SPLIT_KIND}:
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
        if item.upper is None:
            if not any("lower limit only" in condition for condition in item.conditions):
                raise ValueError(f"{item.id} has no upper end and must say it is a lower limit only")
        elif not item.lower < item.upper:
            raise ValueError(f"{item.id} has an empty interval")


audit_quantities()
audit_bounds()
