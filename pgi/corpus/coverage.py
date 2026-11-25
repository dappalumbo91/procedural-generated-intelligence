"""Board coverage by physics domain. Every record on the board belongs to exactly one domain.

This is bookkeeping, not physics: it sorts record ids so COVERAGE.md can say how much of each
domain is on the board. `python -m pgi.corpus.coverage` prints the count table."""
from __future__ import annotations

from collections import Counter

from pgi.corpus.records import RECORDS

DOMAINS: tuple[str, ...] = (
    "mechanics",
    "thermodynamics and statistical",
    "electromagnetism",
    "optics",
    "atomic",
    "molecular and chemistry",
    "nuclear",
    "particle",
    "condensed matter",
    "fluids",
    "gravitation",
    "astrophysics",
    "cosmology",
    "QED and precision",
    "null results and bounds",
    "SI defining constants",
    "foundations and status",
)

_CODATA = {
    "SI defining constants": {"delta_nu_cs", "h", "e", "k", "n_a", "k_cd"},
    "electromagnetism": {"mu_0", "epsilon_0", "r_k", "k_j", "r_k_90", "k_j_90", "f_faraday", "z_0", "phi_0", "g_0", "mu_b"},
    "QED and precision": {"alpha", "alpha_inverse", "r_inf", "a_0", "ryd_hc_ev", "a_e", "a_mu", "r_p", "m_p_over_m_e"},
    "particle": {"m_e", "m_p", "m_n", "m_e_c2_mev", "m_p_c2_mev", "m_n_c2_mev", "g_f"},
    "nuclear": {"e_b_deuteron", "m_d", "m_d_u", "m_d_c2_mev", "m_alpha", "m_alpha_u", "m_alpha_c2_mev", "mu_n_nuclear", "mu_p", "mu_n",
                "mu_p_over_mu_n_nuclear", "mu_n_over_mu_n_nuclear", "mu_n_over_mu_p"},
    "thermodynamics and statistical": {"sigma", "b_wien", "b_prime_wien", "r_gas", "v_m_100kpa", "v_m_101kpa", "n0_100kpa", "n0_101kpa", "c1", "c2", "std_atm"},
    "condensed matter": {"a_si", "d220_si", "vm_si"},
    "gravitation": {"g"},
    "mechanics": {"g_n"},
}

_PREFIX: dict[str, str] = {}
for _domain, _names in {
    "atomic": ("asd512", "rk2002", "blondel2001"),
    "molecular and chemistry": ("cccbdb", "hh1979", "holsch2019", "codata_key", "crc91", "iupac_pka", "janaf1998", "gurvich1991", "iupac2021", "iapws2024"),
    "nuclear": ("ame2020",),
    "particle": ("atlas2024", "cdf2022", "cms2026", "flag2024", "mulan2013", "ucntau2021", "ucntau2025", "nist_beam2013"),
    "condensed matter": ("arajs1964", "ioffe", "srm767a", "wu1987"),
    "mechanics": ("grs80", "leaman2015", "liu2024", "iers2010", "iersc04", "wgs84"),
    "electromagnetism": ("igrf14",),
    "optics": ("schott", "iapws1997", "bipm2003", "bipm2025"),
    "fluids": ("webbook", "iapws2014", "wong1986", "greenspan1987"),
    "thermodynamics and statistical": ("iapws1992", "iapws2011", "its90", "formula"),
    "gravitation": ("cassini", "double_pulsar", "psr_b1913", "gpb", "vlbi", "mercury", "inpop19a", "inpop20a", "inpop21a", "ppn", "g_input", "gw150914"),
    "astrophysics": ("bond2017", "joyce2018", "fonseca2021", "riley2021", "miller2021", "salmi2024", "dittmann2024", "haberreiter2008",
                     "iau2015", "iau2012", "iau2026", "nssdc", "williams2016"),
    "cosmology": ("aver2021", "cooke2018", "fields2020", "planck2018", "sh0es2022", "desi_dr2", "fixsen2009"),
    "QED and precision": ("antognini2013", "crema2013", "bezginov2019", "lundeen1981", "matveev2013", "parthey2011", "hellwig1970", "ishida2014",
                          "ritter1984", "kataoka2009", "alramadhan1994", "liu1999", "fan2023", "fnal2025", "zelevinsky2004", "george2001", "kato2018",
                          "heydarizadmotlagh2024"),
    "null results and bounds": ("bound", "jila2023", "abel2020", "microscope2022"),
    "SI defining constants": ("anchor",),
    "foundations and status": ("primitive", "obstruction", "open"),
}.items():
    for _name in _names:
        _PREFIX[_name] = _domain

_KNOWN = {"known.rayleigh_jeans": "thermodynamics and statistical", "known.opera_timing": "particle", "known.mechanical_ether_required": "electromagnetism"}


def domain(record_id: str) -> str:
    head, _, rest = record_id.partition(".")
    if head == "codata2022":
        for name, members in _CODATA.items():
            if rest in members:
                return name
    elif head == "pdg2026":
        if rest.startswith("bbn."):
            return "cosmology"
        return "QED and precision" if rest in {"a_mu", "a_e", "proton_radius"} else "particle"
    elif head == "asd512" and rest.startswith("line."):
        return "optics"
    elif head == "known":
        if record_id in _KNOWN:
            return _KNOWN[record_id]
    elif head in _PREFIX:
        return _PREFIX[head]
    raise KeyError(f"no coverage domain for {record_id}")


def counts(ids: tuple[str, ...] | None = None) -> dict[str, int]:
    tally = Counter(domain(id) for id in (ids if ids is not None else tuple(record.id for record in RECORDS)))
    return {name: tally.get(name, 0) for name in DOMAINS}


def table(ids: tuple[str, ...] | None = None) -> str:
    rows = counts(ids)
    lines = ["| Domain | Records |", "|---|---:|"]
    lines += [f"| {name} | {count} |" for name, count in rows.items()]
    lines.append(f"| **total** | **{sum(rows.values())}** |")
    return "\n".join(lines)


if __name__ == "__main__":
    print(table())
