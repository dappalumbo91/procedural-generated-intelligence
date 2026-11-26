"""Board coverage by physics domain. Every record on the board belongs to exactly one domain.

This is bookkeeping, not physics: it sorts record ids so COVERAGE.md can say how much of each
domain is on the board. `python -m pgi.corpus.coverage` prints the count table."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

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
    "electromagnetism": {"mu_0", "epsilon_0", "r_k", "k_j", "r_k_90", "k_j_90", "f_faraday", "z_0", "phi_0", "g_0", "g_0_inverse", "mu_b"},
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
    "atomic": ("asd512", "rk2002", "blondel2001", "volz1996", "gutterres2002", "young1994", "rafac1999", "patterson2015", "amini2003", "ekstrom1995", "cccbdb_pol"),
    "molecular and chemistry": ("cccbdb", "hh1979", "holsch2019", "codata_key", "crc91", "iupac_pka", "janaf1998", "gurvich1991", "iupac2021", "iapws2024", "shimanouchi1972", "cccbdb_dip", "kayelaby_e0", "kayelaby_ksp", "webbook_comb"),
    "nuclear": ("ame2020", "ddep", "ensdf", "am2013"),
    "particle": ("atlas2024", "cdf2022", "cms2026", "flag2024", "mulan2013", "ucntau2021", "ucntau2025", "nist_beam2013", "lep2005", "atlas2022", "cms2022"),
    "condensed matter": ("arajs1964", "ioffe", "srm767a", "wu1987", "knowles2017", "migliori2008", "kamm1964", "vallin1964", "nagamatsu2001", "drozdov2015", "nair2008", "ribeiropalau2015", "martin1973", "hpl1972", "nbs1953", "kayelaby_ferro", "danan1968", "myers1951", "nigh1963"),
    "mechanics": ("grs80", "leaman2015", "liu2024", "iers2010", "iersc04", "wgs84", "ccmgk2", "lemoine2013", "konopliv2013", "williams2014", "chen2015"),
    "electromagnetism": ("igrf14", "nbs1966", "iapwsr897", "williams1971", "matula1979", "desai1984", "nist_tn1512", "kayelaby_mag", "khatiwada2015", "havens1933"),
    "optics": ("schott", "iapws1997", "bipm2003", "bipm2025", "malitson1965", "nist_emt", "sivaramakrishnan1956", "turvey1993", "leviton2008", "frey2006"),
    "fluids": ("webbook", "iapws2014", "wong1986", "greenspan1987", "lemmon2004", "db1998", "jones1984", "berg2012", "teos10", "mills1973"),
    "thermodynamics and statistical": ("codata2017", "iapws1992", "iapws2011", "its90", "formula", "kayelaby_gamma", "kayelaby_virial", "kayelaby_crit", "kayelaby_latent"),
    "gravitation": ("cassini", "double_pulsar", "psr_b1913", "gpb", "vlbi", "mercury", "inpop19a", "inpop20a", "inpop21a", "ppn", "g_input", "gw150914", "delva2018", "herrmann2018", "pound1960", "pound1965", "chou2010", "bothwell2022", "ciufolini2016", "williams2004", "hofmann2018", "takamoto2020", "gw170817", "gw190521", "gw190814", "gw190425", "gw200115", "gw230529", "gw231123", "gw250114"),
    "astrophysics": ("borexino", "bond2017", "joyce2018", "fonseca2021", "riley2021", "miller2021", "salmi2024", "dittmann2024", "haberreiter2008",
                     "iau2015", "iau2012", "iau2026", "nssdc", "williams2016", "gravity2018", "gravity2019", "gravity2022", "eht2019", "eht2022", "torres2010", "asplund2021"),
    "cosmology": ("kids2021", "desy3", "aver2021", "cooke2018", "fields2020", "planck2018", "sh0es2022", "desi_dr2", "fixsen2009"),
    "QED and precision": ("sturm2014", "antognini2013", "crema2013", "bezginov2019", "lundeen1981", "matveev2013", "parthey2011", "hellwig1970", "ishida2014",
                          "ritter1984", "kataoka2009", "alramadhan1994", "liu1999", "fan2023", "fnal2025", "zelevinsky2004", "george2001", "kato2018",
                          "heydarizadmotlagh2024", "fee1993", "meyer2000", "patra2020", "vanderwerf2025", "base2022"),
    "null results and bounds": ("bound", "sme2026", "filzinger2023", "jila2023", "abel2020", "microscope2022"),
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
        if rest.startswith("null."):
            return "null results and bounds"
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


# What each domain holds, by id prefix. Every record must fall under exactly one entry of its own domain
# (longest prefix wins), so a new record without a description here fails the coverage test.
HELD: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "mechanics": (
        ("GRAIL lunar Love numbers (Lemoine, Konopliv, Williams)", ("lemoine2013.", "konopliv2013.", "williams2014.",)),
        ("Earth's principal moments of inertia (Chen et al. 2015)", ("chen2015.",)),
        ("CCM.G-K2.2017 key comparison reference values", ("ccmgk2.",)),
        ("standard gravity", ("codata2022.g_n",)),
        ("GRS80 Earth model", ("grs80.",)),
        ("absolute g at Kibble-balance sites", ("leaman2015.", "liu2024.")),
        ("IERS Conventions (2010) Earth constants, precession, and Love numbers", ("iers2010.",)),
        ("EOP 20 C04 rotation rate and length of day", ("iersc04.",)),
        ("WGS 84", ("wgs84.",)),
    ),
    "thermodynamics and statistical": (
        ("latent heats of water, nitrogen, and helium (Kaye & Laby)", ("kayelaby_latent.",)),
        ("second virial coefficient fits (Kaye & Laby)", ("kayelaby_virial.",)),
        ("critical constants of He, N2, CO2 (Kaye & Laby)", ("kayelaby_crit.",)),
        ("heat-capacity ratios of gases (Kaye & Laby)", ("kayelaby_gamma.",)),
        ("CODATA radiation and gas constants", ("codata2022.",)),
        ("Planck and Rayleigh-Jeans spectra", ("formula.", "known.rayleigh_jeans")),
        ("water critical and triple points", ("iapws1992.", "iapws2011.")),
        ("ITS-90 fixed points and the He-4 lambda point", ("its90.",)),
        ("pre-2019 Boltzmann-constant data (AGT, DCGT, JNT) and the CODATA 2017 k", ("codata2017.",)),
    ),
    "electromagnetism": (
        ("magnetic susceptibilities (Kaye & Laby, Khatiwada, Havens)", ("kayelaby_mag.", "khatiwada2015.", "havens1933.",)),
        ("CODATA electromagnetic constants", ("codata2022.",)),
        ("the mechanical-ether known mistake", ("known.mechanical_ether_required",)),
        ("IGRF-14 dipole coefficients", ("igrf14.",)),
        ("IACS copper standard", ("nbs1966.",)),
        ("water's relative permittivity (IAPWS)", ("iapwsr897.",)),
        ("Coulomb inverse-square tests", ("williams1971.",)),
        ("resistivities of Cu, Ag, Au, Al, and W (JPCRD recommended values)", ("matula1979.", "desai1984.")),
        ("microwave permittivities of solid dielectrics (NIST TN 1512)", ("nist_tn1512.",)),
    ),
    "optics": (
        ("thermo-optic coefficients of fused silica, Si, and Ge (CHARMS)", ("leviton2008.", "frey2006.")),
        ("NIST ASD reference lines", ("asd512.line.",)),
        ("Schott N-BK7 indices and dispersion", ("schott.",)),
        ("water refractive index (IAPWS)", ("iapws1997.",)),
        ("CIPM standard frequencies (I2 633 nm and the 2025 list)", ("bipm2003.", "bipm2025.")),
        ("fused-silica Sellmeier coefficients (Malitson 1965)", ("malitson1965.",)),
        ("refractive index of air, Ciddor and modified Edlen (NIST)", ("nist_emt.",)),
        ("Verdet constants of fused silica and water", ("sivaramakrishnan1956.", "turvey1993.")),
    ),
    "atomic": (
        ("static polarizabilities (Cs, Na, He)", ("amini2003.", "ekstrom1995.", "cccbdb_pol.",)),
        ("transition probabilities and oscillator strengths (NIST ASD lines)", ("asd512.tp.",)),
        ("measured excited-state lifetimes (Na 3p, Rb 5p, Cs 6p)", ("volz1996.", "gutterres2002.", "young1994.", "rafac1999.", "patterson2015.",)),
        ("NIST first and second ionization energies", ("asd512.ie.", "asd512.ie2.")),
        ("H-alpha components", ("asd512.h_alpha.",)),
        ("electron affinities", ("rk2002.", "blondel2001.")),
    ),
    "molecular and chemistry": (
        ("dipole moments (CCCBDB), electrode potentials and solubility products (Kaye & Laby), enthalpies of combustion (WebBook)", ("cccbdb_dip.", "kayelaby_e0.", "kayelaby_ksp.", "webbook_comb.",)),
        ("diatomic vibrational and rotational constants (Huber-Herzberg) and water fundamentals (Shimanouchi)", ("hh1979.we_", "hh1979.be_", "shimanouchi1972.",)),
        ("dissociation energies", ("cccbdb.", "holsch2019.")),
        ("bond lengths", ("hh1979.",)),
        ("heats of formation", ("codata_key.", "janaf1998.", "gurvich1991.")),
        ("pKa values", ("crc91.", "iupac_pka.")),
        ("IUPAC atomic weights", ("iupac2021.",)),
        ("water ionization constant", ("iapws2024.",)),
    ),
    "nuclear": (
        ("AME2020 masses and binding energies", ("ame2020.",)),
        ("CODATA deuteron, alpha, and nucleon moments", ("codata2022.",)),
        ("DDEP and ENSDF half-lives, including medical isotopes", ("ddep.", "ensdf.")),
        ("Angeli-Marinova charge radii", ("am2013.",)),
    ),
    "particle": (
        ("CODATA particle masses and G_F", ("codata2022.",)),
        ("PDG boson, lepton, and quark masses, couplings, and CKM", ("pdg2026.",)),
        ("PDG light hadron masses", ("pdg2026.m_pi", "pdg2026.m_k", "pdg2026.m_eta", "pdg2026.m_rho", "pdg2026.m_omega", "pdg2026.m_p", "pdg2026.m_n", "pdg2026.m_lambda", "pdg2026.m_delta")),
        ("PDG neutrino mixing", ("pdg2026.nu.",)),
        ("PDG lifetimes and widths", ("pdg2026.neutron_lifetime", "pdg2026.tau_lifetime", "pdg2026.b_plus", "pdg2026.b0_", "pdg2026.bs_", "pdg2026.pi_plus_", "pdg2026.pi0_", "pdg2026.k_", "pdg2026.mu_lifetime", "pdg2026.gamma_h", "pdg2026.gamma_t")),
        ("PDG Z-pole values", ("pdg2026.gamma_z", "pdg2026.sigma_had0", "pdg2026.a_fb0", "pdg2026.r_", "pdg2026.z.")),
        ("PDG Higgs signal strengths", ("pdg2026.higgs_mu.",)),
        ("PDG charm, bottom, quarkonium, and hyperon masses", tuple(f"pdg2026.m_{k}" for k in ("d_plus", "d0", "ds", "b_plus", "b0", "bs", "jpsi", "upsilon1s", "sigma_", "sigma0", "xi", "omega_minus", "lambda_c", "lambda_b"))),
        ("PDG Higgs and Z branching fractions and the Z invisible width", ("pdg2026.br.", "pdg2026.gamma_z_invisible")),
        ("LEP/SLD Z-pole combination", ("lep2005.",)),
        ("W mass by experiment", ("atlas2024.", "cdf2022.", "cms2026.")),
        ("ATLAS and CMS global Higgs signal strengths", ("atlas2022.", "cms2022.")),
        ("lattice alpha_s", ("flag2024.",)),
        ("muon and neutron lifetimes by experiment", ("mulan2013.", "ucntau2021.", "ucntau2025.", "nist_beam2013.")),
        ("the OPERA timing known mistake", ("known.opera_timing",)),
    ),
    "condensed matter": (
        ("saturation magnetization of Fe, Co, Ni, Gd", ("kayelaby_ferro.", "danan1968.", "myers1951.", "nigh1963.",)),
        ("lattice constants (NBS Circular 539, Ioffe)", ("nbs1953.", "ioffe.ge.lattice", "ioffe.gaas.lattice", "ioffe.diamond.lattice",)),
        ("thermal conductivities of Cu, Al, Si, and diamond (Ho-Powell-Liley)", ("hpl1972.",)),
        ("calorimetric Debye temperatures and electronic gamma (Cu, Ag, Au)", ("martin1973.",)),
        ("silicon lattice constants (CODATA)", ("codata2022.",)),
        ("band gaps", ("ioffe.",)),
        ("superconductor T_c", ("srm767a.", "nagamatsu2001.", "drozdov2015.", "wu1987.")),
        ("iron Curie point", ("arajs1964.",)),
        ("elastic constants and elastic Debye temperatures", ("knowles2017.", "migliori2008.", "kamm1964.", "vallin1964.")),
        ("graphene transmittance", ("nair2008.",)),
        ("quantum Hall universality", ("ribeiropalau2015.",)),
    ),
    "fluids": (
        ("water self-diffusion (Mills 1973)", ("mills1973.",)),
        ("measured dry-air viscosity (Kestin et al., via NBS TN 1186)", ("jones1984.",)),
        ("dilute-gas viscosities at 25 C (Berg-Moldover)", ("berg2012.",)),
        ("TEOS-10 seawater reference values", ("teos10.",)),
        ("water properties at 20-25 C", ("webbook.",)),
        ("water surface tension", ("iapws2014.",)),
        ("speed of sound in air", ("wong1986.", "greenspan1987.")),
        ("air, N2, and O2 viscosity and thermal conductivity", ("lemmon2004.",)),
        ("liquid helium-4 densities and first and second sound", ("db1998.",)),
    ),
    "gravitation": (
        ("Newtonian G and its input measurements", ("codata2022.g", "g_input.")),
        ("Cassini, VLBI, ephemeris, and PPN tests", ("cassini.", "vlbi.", "inpop19a.", "inpop20a.", "inpop21a.", "ppn.")),
        ("Mercury's perihelion", ("mercury.",)),
        ("binary pulsars", ("double_pulsar.", "psr_b1913.")),
        ("Gravity Probe B and LAGEOS/LARES frame dragging", ("gpb.", "ciufolini2016.")),
        ("GW150914", ("gw150914.",)),
        ("later GWTC events: masses and distances", ("gw170817.", "gw190521.", "gw190814.", "gw190425.", "gw200115.", "gw230529.", "gw231123.", "gw250114.")),
        ("gravitational redshift (Galileo, Pound-Snider, optical clocks, Tokyo Skytree)", ("delva2018.", "herrmann2018.", "pound1960.", "pound1965.", "chou2010.", "bothwell2022.", "takamoto2020.")),
        ("LLR Nordtvedt eta and Gdot/G", ("williams2004.", "hofmann2018.")),
    ),
    "astrophysics": (
        ("detached eclipsing-binary masses (Torres et al. 2010)", ("torres2010.",)),
        ("solar abundance scale (Asplund et al. 2021)", ("asplund2021.",)),
        ("IAU nominal and astronomical constants", ("iau2015.", "iau2012.", "iau2026.")),
        ("Moon orbit and recession", ("nssdc.", "williams2016.")),
        ("Sirius B", ("bond2017.", "joyce2018.")),
        ("Sgr A* distance and mass (GRAVITY)", ("gravity2019.", "gravity2022.")),
        ("S2 gravitational-redshift parameter", ("gravity2018.", "gravity2019.f_redshift")),
        ("EHT ring and shadow diameters, M87* mass", ("eht2019.", "eht2022.")),
        ("neutron star masses and radii", ("fonseca2021.", "riley2021.", "miller2021.", "salmi2024.", "dittmann2024.")),
        ("solar irradiance", ("haberreiter2008.",)),
        ("Borexino solar neutrino fluxes", ("borexino.",)),
    ),
    "cosmology": (
        ("Planck 2018 parameters", ("planck2018.",)),
        ("SH0ES H0", ("sh0es2022.",)),
        ("DESI DR2 dark energy", ("desi_dr2.",)),
        ("DESI DR2 BAO distances", ("desi_dr2.bao.",)),
        ("weak-lensing S8 (KiDS-1000, DES Y3)", ("kids2021.", "desy3.")),
        ("baryon-to-photon ratio", ("cooke2018.eta10", "fields2020.eta10")),
        ("CMB temperature", ("fixsen2009.",)),
        ("primordial abundances", ("aver2021.", "cooke2018.", "fields2020.", "pdg2026.bbn.")),
    ),
    "QED and precision": (
        ("BASE antiproton-to-proton q/m ratio", ("base2022.",)),
        ("CODATA alpha, Rydberg, and g-factors", ("codata2022.",)),
        ("PDG g-2 and proton radius", ("pdg2026.",)),
        ("muonic hydrogen and the proton radius", ("antognini2013.", "crema2013.", "bezginov2019.")),
        ("hydrogen spectroscopy", ("lundeen1981.", "matveev2013.", "parthey2011.", "hellwig1970.")),
        ("positronium", ("fee1993.", "ishida2014.", "ritter1984.", "kataoka2009.", "alramadhan1994.")),
        ("muonium", ("liu1999.", "meyer2000.")),
        ("HD+ molecular-ion spectroscopy", ("patra2020.",)),
        ("helium-3 2S line and the helion-alpha radius difference", ("vanderwerf2025.",)),
        ("electron and muon g-2 experiments", ("fan2023.", "fnal2025.")),
        ("helium fine structure", ("zelevinsky2004.", "george2001.", "kato2018.", "heydarizadmotlagh2024.")),
        ("Penning-trap electron mass", ("sturm2014.",)),
    ),
    "null results and bounds": (
        ("null results and upper bounds", ("bound.", "jila2023.", "abel2020.", "microscope2022.")),
        ("SME Lorentz-violation maximal sensitivities (Kostelecky-Russell)", ("sme2026.",)),
        ("clock limits on alpha drift and the neutron charge", ("filzinger2023.", "pdg2026.null.")),
    ),
    "SI defining constants": (("SI defining constants", ("codata2022.", "anchor.")),),
    "foundations and status": (("primitives, obstructions, and open problems", ("primitive.", "obstruction.", "open.")),),
}


@dataclass(frozen=True)
class Gap:
    """An observable the board lacks. It closes itself once a record of its own domain matches one of
    its terms: a term starting with "id:" matches a record-id prefix, any other term matches the
    record's title, keys, or phrases (lower-cased). A closed gap stops being listed."""

    text: str
    terms: tuple[str, ...]


GAPS: dict[str, tuple[Gap, ...]] = {
    "mechanics": (
        Gap("more absolute-gravity sites (the CCM key comparisons)", ("key comparison",)),
        Gap("measured (not nominal) Love numbers from tides and SLR", ("measured love number",)),
        Gap("Earth's moments of inertia", ("moment of inertia",)),
    ),
    "thermodynamics and statistical": (
        Gap("pre-2019 Boltzmann-constant determinations (acoustic gas thermometry, DCGT, Johnson noise)", ("acoustic gas thermometry", "johnson noise")),
        Gap("heat-capacity ratios of common gases", ("heat capacity ratio", "adiabatic index")),
        Gap("second virial coefficients", ("virial coefficient",)),
        Gap("latent heats", ("latent heat", "enthalpy of vaporization", "enthalpy of fusion")),
        Gap("critical points beyond water", ("critical point of nitrogen", "critical point of carbon dioxide", "critical point of helium")),
    ),
    "electromagnetism": (
        Gap("copper resistivity versus temperature", ("copper resistivity versus temperature",)),
        Gap("silver resistivity", ("resistivity of silver",)),
        Gap("gold resistivity", ("resistivity of gold",)),
        Gap("aluminium resistivity", ("resistivity of aluminium", "resistivity of aluminum")),
        Gap("tungsten resistivity", ("resistivity of tungsten",)),
        Gap("relative permittivities of common solid dielectrics", ("permittivity of fused silica", "permittivity of ptfe", "permittivity of alumina", "permittivity of sapphire")),
        Gap("magnetic susceptibilities", ("magnetic susceptibility",)),
    ),
    "optics": (
        Gap("fused-silica refractive index (Malitson 1965)", ("fused silica",)),
        Gap("refractive index of air (Ciddor 1996 or Edlen)", ("refractive index of air",)),
        Gap("Verdet constants", ("verdet",)),
        Gap("thermo-optic coefficients", ("thermo-optic",)),
        Gap("the rest of the CIPM frequency list", ("ca40+", "hg199", "in115+")),
    ),
    "atomic": (
        Gap("excited-state lifetimes and oscillator strengths", ("oscillator strength", "excited-state lifetime")),
        Gap("static polarizabilities", ("polarizability",)),
        Gap("ionization energies above krypton", ("ionization energy of rubidium", "ionization energy of cesium")),
        Gap("isotope shifts", ("isotope shift",)),
    ),
    "molecular and chemistry": (
        Gap("vibrational frequencies and rotational constants", ("vibrational frequency", "rotational constant")),
        Gap("molecular dipole moments", ("dipole moment of",)),
        Gap("standard electrode potentials", ("electrode potential",)),
        Gap("solubility products", ("solubility product",)),
        Gap("enthalpies of combustion", ("enthalpy of combustion",)),
    ),
    "nuclear": (
        Gap("half-lives of short-lived and medical isotopes (e.g. Tc-99m, F-18)", ("tc-99m", "f-18")),
        Gap("the rest of the Angeli-Marinova table and newer laser-spectroscopy radii", ("laser spectroscopy radius",)),
        Gap("thermal neutron cross sections", ("thermal neutron cross section",)),
        Gap("nuclear spins and quadrupole moments", ("nuclear quadrupole moment", "nuclear spin")),
        Gap("fission and fusion Q-values", ("q-value", "fusion energy release")),
    ),
    "particle": (
        Gap("charm meson masses (D)", ("d meson mass", "mass of the d meson")),
        Gap("bottom meson masses (B)", ("b meson mass", "mass of the b meson")),
        Gap("quarkonium masses (J/psi, Upsilon)", ("j/psi", "upsilon")),
        Gap("strange baryon masses (Sigma, Xi, Omega)", ("sigma baryon", "xi baryon", "omega baryon")),
        Gap("heavy baryon masses (Lambda_c, Lambda_b)", ("lambda_c", "lambda_b")),
        Gap("Higgs branching ratios", ("higgs branching",)),
        Gap("the Z invisible width and branching ratio", ("z invisible",)),
        Gap("measured cross sections (e.g. top pair at 13 TeV)", ("top pair cross section",)),
        Gap("ATLAS and CMS per-channel signal strengths", ("atlas signal strength by channel",)),
    ),
    "condensed matter": (
        Gap("calorimetric Debye temperatures (Cu and Si have no reachable primary source yet)", ("calorimetric debye",)),
        Gap("thermal conductivities of solids", ("thermal conductivity of copper", "thermal conductivity of silicon", "thermal conductivity of diamond")),
        Gap("lattice constants beyond silicon", ("lattice constant of copper", "lattice constant of germanium", "lattice constant of aluminium", "lattice constant of gaas")),
        Gap("magnetic moments of ferromagnets", ("saturation magnetization",)),
    ),
    "fluids": (
        Gap("measured (not correlated) air transport data", ("measured air viscosity",)),
        Gap("noble-gas transport properties", ("viscosity of argon", "viscosity of helium gas")),
        Gap("seawater (TEOS-10)", ("seawater", "teos-10")),
        Gap("diffusion coefficients", ("diffusion coefficient",)),
        Gap("helium-4 viscosity and mutual friction", ("mutual friction", "helium ii viscosity")),
    ),
    "gravitation": (
        Gap("Pound-Rebka 1960 itself", ("id:pound1960.", "pound-rebka 1960")),
        Gap("Takamoto 2020 Tokyo Skytree clock test", ("skytree",)),
        Gap("Bothwell 2022 published-version numbers", ("bothwell published",)),
        Gap("gravitational-wave events beyond GW150914, with masses and distances", ("id:gw170817.", "id:gw190521.", "id:gwtc3.", "id:gwtc4.")),
    ),
    "astrophysics": (
        Gap("solar neutrino fluxes (Borexino)", ("borexino", "solar neutrino flux")),
        Gap("Sgr A* mass and distance (GRAVITY)", ("sgr a*",)),
        Gap("M87* and Sgr A* shadow sizes", ("shadow",)),
        Gap("eclipsing-binary masses", ("eclipsing binary",)),
        Gap("the solar abundance scale", ("solar abundance",)),
    ),
    "cosmology": (
        Gap("DESI BAO distances", ("bao distance",)),
        Gap("the baryon-to-photon ratio", ("baryon-to-photon",)),
        Gap("weak-lensing S8 (KiDS, DES)", ("kids", "weak lensing")),
        Gap("Omega_k", ("curvature density", "omega_k")),
        Gap("the age of the universe", ("age of the universe",)),
        Gap("the reionization redshift", ("reionization redshift",)),
    ),
    "QED and precision": (
        Gap("the electron mass in u from Penning traps", ("penning",)),
        Gap("He+ and HD+ spectroscopy", ("hd+", "he+ spectroscopy")),
        Gap("positronium and muonium 1S-2S", ("positronium 1s-2s", "muonium 1s-2s")),
        Gap("the 3He-4He isotope shift", ("helium isotope shift",)),
        Gap("the antiproton-to-proton charge-to-mass ratio", ("antiproton",)),
    ),
    "null results and bounds": (
        Gap("Lorentz-invariance (SME) limits", ("lorentz invariance", "sme coefficient")),
        Gap("neutrinoless double-beta decay (KamLAND-Zen)", ("double-beta", "double beta")),
        Gap("dark-matter cross sections (LZ)", ("dark matter cross section", "wimp")),
        Gap("axion-photon coupling (CAST)", ("axion",)),
        Gap("fifth-force (Eot-Wash) limits", ("fifth force", "eot-wash")),
        Gap("drift of alpha from clocks", ("alpha drift", "variation of the fine-structure constant")),
        Gap("neutron-antineutron and charge-equality limits", ("neutron-antineutron", "charge equality")),
    ),
    "SI defining constants": (),
    "foundations and status": (),
}

_HEAD = "| Domain | Records | On the board | Still missing |"


def _text(record) -> str:
    return " | ".join((record.title, *record.keys, *record.phrases)).lower()


def held(records=None) -> dict[str, list[tuple[str, int]]]:
    """Each domain's HELD entries with their record counts. Raises if a record has no entry, or an entry is empty."""
    records = RECORDS if records is None else records
    out: dict[str, list[tuple[str, int]]] = {name: [] for name in DOMAINS}
    tally: dict[tuple[str, str], int] = Counter()
    for record in records:
        name = domain(record.id)
        best = max(((len(prefix), label) for label, prefixes in HELD[name] for prefix in prefixes if record.id.startswith(prefix)), default=None)
        if best is None:
            raise KeyError(f"no HELD entry in {name} for {record.id}")
        tally[(name, best[1])] += 1
    for name in DOMAINS:
        for label, _ in HELD[name]:
            if not tally[(name, label)]:
                raise KeyError(f"HELD entry '{label}' in {name} matches no record")
            out[name].append((label, tally[(name, label)]))
    return out


def closing(gap: Gap, name: str, records=None) -> list[str]:
    """Ids of the records of domain `name` that close `gap`."""
    records = RECORDS if records is None else records
    hits = []
    for record in records:
        if domain(record.id) != name:
            continue
        text = _text(record)
        if any(record.id.startswith(term[3:]) if term.startswith("id:") else term in text for term in gap.terms):
            hits.append(record.id)
    return hits


def open_gaps(records=None) -> dict[str, list[Gap]]:
    return {name: [gap for gap in GAPS[name] if not closing(gap, name, records)] for name in DOMAINS}


def gap_table(records=None) -> str:
    """The domain-by-domain gap table and the thinnest-domains list, built only from the board."""
    have, missing, rows = held(records), open_gaps(records), counts(None if records is None else tuple(r.id for r in records))
    lines = [_HEAD, "|---|---:|---|---|"]
    for name in DOMAINS:
        on = "; ".join(f"{label} ({n})" for label, n in have[name])
        gone = "; ".join(gap.text for gap in missing[name]) or "nothing listed"
        lines.append(f"| {name} | {rows[name]} | {on} | {gone} |")
    lines += ["", "Thinnest domains that still have listed gaps, fewest records first:", ""]
    thin = sorted((n, name) for name, n in rows.items() if missing[name])[:7]
    lines += [f"{i}. {name} ({n} records): {missing[name][0].text}." for i, (n, name) in enumerate(thin, 1)]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    print(gap_table() if sys.argv[1:] == ["gaps"] else table())
