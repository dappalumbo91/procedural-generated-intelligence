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
    }
)


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

QUANTITIES: tuple[Quantity, ...] = CODATA_2022 + PDG_2026


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
        if item.lower_text and item.uncertainty_kind != "asymmetric standard uncertainty":
            raise ValueError(f"{item.id} has a lower bound but a symmetric kind")
        if item.printed:
            value, sigma = parse_concise(item.printed)
            if value != item.value or sigma != item.uncertainty:
                raise ValueError(f"{item.id} does not match its printed form {item.printed}")


audit_quantities()
