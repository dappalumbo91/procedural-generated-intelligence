# Coverage

How much of each physics domain is on PGI's board, and what is missing. Every board record is assigned to one domain by `pgi/corpus/coverage.py`, and `python -m pgi.corpus.coverage` prints the table. The tests check that every record has a domain and that the table below matches the board, so this file cannot drift.

The counts are records, not importance. A domain with many AME mass rows is not "done", and one CODATA constant can matter more than a dozen table rows.

## Board now

<!-- counts:start -->
| Domain | Records |
|---|---:|
| mechanics | 0 |
| thermodynamics and statistical | 34 |
| electromagnetism | 7 |
| optics | 0 |
| atomic | 54 |
| molecular and chemistry | 55 |
| nuclear | 79 |
| particle | 78 |
| condensed matter | 11 |
| fluids | 12 |
| gravitation | 55 |
| astrophysics | 33 |
| cosmology | 30 |
| QED and precision | 37 |
| null results and bounds | 16 |
| SI defining constants | 7 |
| foundations and status | 9 |
| **total** | **517** |
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
| mechanics | standard gravity g_n (exact); measured local g at named sites; Earth's rotation rate and length of day; Earth's figure (GRS80/WGS84 a, f, J2); the precession constant; the lunar and solar tidal parameters |
| thermodynamics and statistical | ITS-90 fixed points and the gas-constant family (batch 8); the pre-2019 Boltzmann-constant determinations (acoustic gas thermometry, DCGT, Johnson noise); heat-capacity ratios and second virial coefficients of common gases; latent heats; critical points beyond water |
| electromagnetism | Faraday constant, vacuum impedance, flux quantum, conductance quantum, and Bohr magneton from CODATA; Earth's main field (IGRF-14 Gauss coefficients); Coulomb's-law tests; resistivity of copper and other standard materials; static permittivity of water |
| optics | spectral reference lines (Na D, Hg, Cd, He, H Fraunhofer lines); refractive indices of water, air, and standard glasses; CIPM recommended standard frequencies (I2-stabilised He-Ne, Sr and Yb clocks); dispersion and Verdet constants |
| atomic | excited-state lifetimes and oscillator strengths; polarizabilities; alkali D-line frequencies; ionization energies above krypton; isotope shifts |
| molecular and chemistry | vibrational frequencies and rotational constants; dipole moments; standard electrode potentials; solubility products; enthalpies of combustion; more pKa values |
| nuclear | half-lives (3H, 14C, 40K, 238U); charge radii (Angeli-Marinova); thermal neutron cross sections; nuclear spins and quadrupole moments; fission and fusion Q-values |
| particle | Z lineshape (Gamma_Z, sigma_had, R_l); sin^2 theta_eff; heavier meson and baryon masses; branching ratios; the top width; measured cross sections |
| condensed matter | elastic constants and Debye temperatures; thermal conductivities; more superconductors (MgB2, H3S); lattice constants beyond silicon; magnetic moments |
| fluids | water properties and air sound speed (batch 8); viscosity and thermal conductivity of air and the noble gases; seawater (TEOS-10); diffusion coefficients |
| gravitation | gravitational redshift (Gravity Probe A, Galileo 5/6); Lense-Thirring from LAGEOS/LARES; the LLR Nordtvedt parameter; Gdot/G; more GW events |
| astrophysics | solar neutrino fluxes (Borexino); Sgr A* mass and distance (GRAVITY); the M87* and Sgr A* shadow sizes; eclipsing-binary masses; the solar abundance scale |
| cosmology | BAO distances (DESI); the baryon-to-photon ratio; weak-lensing S8 (KiDS, DES); Omega_k; the age of the universe; the reionization redshift |
| QED and precision | the electron mass in u (Penning trap); He+ and HD+ spectroscopy; positronium and muonium 1S-2S; the 3He-4He isotope shift; the antiproton-to-proton charge-to-mass ratio |
| null results and bounds | Lorentz-invariance (SME) limits; neutrinoless double-beta decay (KamLAND-Zen); dark-matter cross sections (LZ); axion-photon coupling (CAST); fifth-force (Eot-Wash) limits; drift of alpha from clocks; the neutron-antineutron and charge-equality limits |

## Top gaps across the board

1. Mechanics had nothing: no g_n, no measured g, no Earth rotation or figure.
2. Optics had nothing: no reference spectral lines and no refractive indices.
3. Fluids had nothing: no transport properties and no sound speeds.
4. Electromagnetism is thin and holds only unit constants. It has no geomagnetic field and no material constants.
5. Nuclear half-lives and charge radii are missing, even though nuclear masses are well covered.
6. The Z lineshape is missing, so electroweak precision rests on masses and G_F alone.
7. Gravitational redshift is missing, so the clock test of GR is absent.
