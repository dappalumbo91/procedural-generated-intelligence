# Coverage

How much of each physics domain is on PGI's board, and what is missing. Every board record is assigned to one domain by `pgi/corpus/coverage.py`, and `python -m pgi.corpus.coverage` prints the table. The tests check that every record has a domain and that the table below matches the board, so this file cannot drift.

The counts are records, not importance. A domain with many AME mass rows is not "done", and one CODATA constant can matter more than a dozen table rows.

## Board now

<!-- counts:start -->
| Domain | Records |
|---|---:|
| mechanics | 37 |
| thermodynamics and statistical | 34 |
| electromagnetism | 28 |
| optics | 25 |
| atomic | 54 |
| molecular and chemistry | 55 |
| nuclear | 105 |
| particle | 88 |
| condensed matter | 11 |
| fluids | 12 |
| gravitation | 59 |
| astrophysics | 33 |
| cosmology | 30 |
| QED and precision | 37 |
| null results and bounds | 18 |
| SI defining constants | 7 |
| foundations and status | 9 |
| **total** | **642** |
<!-- counts:end -->

## Audit at pgi-0.79.0 (482 records)

This was the board when the audit was taken, before the batch 8 fills:

| Domain | Records |
|---|---:|
| mechanics | 0 |
| thermodynamics and statistical | 11 |
| electromagnetism | 7 |
| optics | 0 |
| atomic | 54 |
| molecular and chemistry | 55 |
| nuclear | 79 |
| particle | 78 |
| condensed matter | 11 |
| fluids | 0 |
| gravitation | 55 |
| astrophysics | 33 |
| cosmology | 30 |
| QED and precision | 37 |
| null results and bounds | 16 |
| SI defining constants | 7 |
| foundations and status | 9 |
| **total** | **482** |

Mechanics, optics, and fluids were empty, so those three are batch 8's fills. Electromagnetism (7), condensed matter (11), and thermodynamics (11) were the next thinnest.

## Most important missing observables, by domain

| Domain | Missing observables |
|---|---|
| mechanics | standard gravity, GRS80, and measured g at three Kibble-balance sites (batch 8); IERS Conventions (2010) Earth constants, IAU 2006 precession rate, nominal Love and Shida numbers, EOP 20 C04 length-of-day rows, and WGS 84 (batch 9); a wider set of absolute-gravity sites (the CCM key comparisons themselves); measured (not nominal) Love numbers from tides and SLR; the general precession in longitude p_A (not printed in TN36); lunar laser ranging tidal acceleration |
| thermodynamics and statistical | ITS-90 fixed points and the gas-constant family (batch 8); the pre-2019 Boltzmann-constant determinations (acoustic gas thermometry, DCGT, Johnson noise); heat-capacity ratios and second virial coefficients of common gases; latent heats; critical points beyond water |
| electromagnetism | Faraday constant, vacuum impedance, flux quantum, Bohr magneton, and IGRF-14 degree-1 Gauss coefficients (batch 8); the conductance quantum, the IACS copper standard, IAPWS water permittivity, and the Williams-Faller-Hill and Plimpton-Lawton Coulomb's-law tests (batch 9); measured copper resistivity versus temperature (Matula 1979 is a scan with no text layer); resistivities of other standard metals; permittivities of other solvents; the Verdet constant |
| optics | reference lines, N-BK7 and water indices, and the I₂ 633 nm, ⁸⁷Sr, and ¹⁷¹Yb standard frequencies (batch 8); fused-silica (Malitson 1965) and air (Ciddor 1996) indices; Verdet and thermo-optic constants; the rest of the CIPM frequency list |
| atomic | excited-state lifetimes and oscillator strengths; polarizabilities; alkali D-line frequencies; ionization energies above krypton; isotope shifts |
| molecular and chemistry | vibrational frequencies and rotational constants; dipole moments; standard electrode potentials; solubility products; enthalpies of combustion; more pKa values |
| nuclear | DDEP and ENSDF half-lives for 3H, 14C, 40K, 60Co, 238U, and 232Th, ENSDF's neutron half-life, and Angeli-Marinova charge radii for 13 nuclei (batch 9); half-lives of short-lived and medically used isotopes; the rest of the Angeli-Marinova table and newer laser-spectroscopy radii; thermal neutron cross sections; nuclear spins and quadrupole moments; fission and fusion Q-values |
| particle | the Z lineshape from the 2006 LEP combination and PDG 2026 (Gamma_Z, sigma_had0, R_l0, A_FB0l, N_nu, sin^2 theta_eff; batch 9); PDG's R_l; the heavy-flavour asymmetries and A_l from SLD; heavier meson and baryon masses; branching ratios; the top width; measured cross sections |
| condensed matter | elastic constants and Debye temperatures; thermal conductivities; more superconductors (MgB2, H3S); lattice constants beyond silicon; magnetic moments |
| fluids | water properties and air sound speed (batch 8); viscosity and thermal conductivity of air and the noble gases; seawater (TEOS-10); diffusion coefficients |
| gravitation | gravitational redshift from Galileo 5/6 (Delva 2018, Herrmann 2018), Pound-Snider 1965, and the Gravity Probe A agreement level (batch 9); Pound-Rebka 1960 itself (abstract not reachable); optical-clock height tests (e.g. Takamoto 2020 Tokyo Skytree); Lense-Thirring from LAGEOS/LARES; the LLR Nordtvedt parameter; Gdot/G; more GW events |
| astrophysics | solar neutrino fluxes (Borexino); Sgr A* mass and distance (GRAVITY); the M87* and Sgr A* shadow sizes; eclipsing-binary masses; the solar abundance scale |
| cosmology | BAO distances (DESI); the baryon-to-photon ratio; weak-lensing S8 (KiDS, DES); Omega_k; the age of the universe; the reionization redshift |
| QED and precision | the electron mass in u (Penning trap); He+ and HD+ spectroscopy; positronium and muonium 1S-2S; the 3He-4He isotope shift; the antiproton-to-proton charge-to-mass ratio |
| null results and bounds | Lorentz-invariance (SME) limits; neutrinoless double-beta decay (KamLAND-Zen); dark-matter cross sections (LZ); axion-photon coupling (CAST); fifth-force (Eot-Wash) limits; drift of alpha from clocks; the neutron-antineutron and charge-equality limits |

## Top gaps across the board

1. Mechanics had nothing: no g_n, no measured g, no Earth rotation or figure. Batch 8 added g_n, GRS80, and site g; batch 9 added IERS rotation, LOD, WGS 84, precession, and Love numbers.
2. Optics had nothing: no reference spectral lines and no refractive indices.
3. Fluids had nothing: no transport properties and no sound speeds.
4. Electromagnetism is thin and holds only unit constants. It has no geomagnetic field and no material constants. Batch 8 added IGRF-14 and CODATA EM constants; batch 9 added the conductance quantum, the IACS copper standard, water permittivity, and Coulomb's-law tests.
5. Nuclear half-lives and charge radii are missing, even though nuclear masses are well covered. Batch 9 added a starter set of DDEP and ENSDF half-lives and 13 Angeli-Marinova radii.
6. The Z lineshape is missing, so electroweak precision rests on masses and G_F alone. Batch 9 added the LEP 2006 combination and PDG 2026's Gamma_Z, sigma_had0, and A_FB0l.
7. Gravitational redshift is missing, so the clock test of GR is absent. Batch 9 added Galileo 5/6, Pound-Snider, and the GP-A agreement level.
