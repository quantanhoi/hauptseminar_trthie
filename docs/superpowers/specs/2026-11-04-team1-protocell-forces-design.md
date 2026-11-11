# Team 1 – Protocell Forces: Project Design

**Date:** 2026-11-04
**Status:** approved by user, 2026-11-04
**Authoritative assignment source:** `hauptseminar_pdf/2026-05-20_Aufgabenblatt_Team-1_V2.pdf` (extract text with `pdftotext -layout`; all §-references below point to it)

## Intent

The user needs the complete Team-1 deliverable for their German master seminar
"Construction Theory of Information und Software in the Natural World": a
transparent, reproducible Python model of the effective interaction between
prebiotic protocells (R = 500 nm, surface gap L = 2–100 nm) that keeps three
physics models strictly separate — vdW-only, classical DLVO, and a retarded
Casimir–Lifshitz approximation — adds Brownian pair and 2D cluster dynamics
with contact-zone metrics, and exports clean CSV data for Team 2.

Purpose: graded seminar work the user will present and defend. All
user-facing text (plot labels, README, report) is German; code identifiers are
English.

## Why

All later seminar teams depend on Team 1's microdata. The grading rubric (§16)
weights: physical cleanliness 25% (no double counting, clean units), modular
reproducible implementation 20% (documented seeds), analysis/metrics 20%, clean
CSV handoff to Team 2 15% (exact schemas, §17), interpretation 15% (no
overclaiming, per §10's strict rule), presentation 5%.

## Goals

1. Four model modes, strictly separated (§3): `vdw` (non-retarded near-field),
   `dlvo` (electrostatic + vdW + core), `cl_retarded` (vdW × retardation
   factor), plus a written Lifshitz/Matsubara outlook (§8 — documentation only,
   no numerics).
2. Force/potential analysis on a log grid 2–100 nm plus support points
   2, 3, 5, 10, 20, 30, 50, 100 nm (§9 steps 1–6), for two material classes:
   fatty-acid vesicles A_H = 0.2, 0.5, 1.0 ×10⁻²¹ J; PMBCs A_H = 1, 3, 5, 10
   ×10⁻²¹ J; salts I = 50, 100, 200 mM.
3. All 7 mandatory visualizations (§14).
4. Brownian pair dynamics (1D gap) with metrics: contact probability,
   dwell time, escape time, return probability, time-in-zone histograms
   (§11, §9 step 7).
5. 2D many-particle simulation, N = 10–50 protocells, periodic box, with
   contact graphs (networkx), cluster size distributions, largest component,
   mean degree (§9 step 8, §11).
6. Sensitivity sweeps with constant seeds (§9 step 9): A_H, salt, noise,
   L_r = 10/20/30 nm, p = 1/2, radius, core parameters; plus a negative control
   (A_H = 0, pure diffusion).
7. Team-2 export in the exact §17 schemas (below).
8. README (German) and a German report skeleton with the mandatory
   interpretation statements of §10.

## Non-goals

- No full Lifshitz/Matsubara/TE–TM computation (§8 is a documented outlook).
- No 3D, no hydrodynamics, no explicit lipid/protein chemistry.
- No week-8 presentation slides — the user's own work.
- No interim "week 2" deliverable process — the finished project covers it.

## Anti-goals (failure even if it runs)

- `F_total = F_el + F_vdw + F_CL` anywhere — vdW is the non-retarded limit of
  the Lifshitz framework and must never be added to a CL term (§3, §18 Fehler 1).
- Confusing surface gap L with center distance d = 2R + L (§18 Fehler 2).
- Claiming CL explains clustering across all of 2–100 nm; interpretation must
  follow §10's strict wording (plausible contribution 2–30 nm, especially
  PMBCs; 30–100 nm weak single-pair forces).
- Any run whose seed is not fixed and recorded.
- Overstating retardation as amplification (§18 Fehler 4).

## Constraints

- **Environment:** system default python is 3.7.4 without matplotlib/networkx;
  use a project venv from `python3.12`. `requirements.txt`: numpy, pandas,
  matplotlib, networkx, jupyterlab, pytest.
- **Structure:** exactly the assignment's suggested layout (§13):

  ```
  team1_forces/
  ├── README.md
  ├── requirements.txt
  ├── src/            # constants, potentials, force_table, pair_dynamics,
  │                   # brownian_cluster, metrics, plots, export
  ├── notebooks/      # 01_force_curves, 02_pair_dynamics,
  │                   # 03_cluster_simulation, 04_parameter_sweep
  ├── data/raw/       # (kept for assignment conformity; nothing writes here)
  ├── data/processed/ # Team-2 CSVs
  ├── figures/        # saved figures (also embedded in notebooks)
  ├── report/        # report.md (German skeleton)
  └── tests/         # small pytest suite (addition to §13)
  ```

- **Starter code:** the appendix (§12) classes are the base and are meant to be
  extended, tested, documented. Constructor defaults stay exactly as in the
  appendix: R = 500 nm, B_kBT = 20, L_core = 0.5 nm, C_core_kBT = 0.5,
  L_ret = 20 nm, p_ret = 2, potentials clip L_min = 0.2 nm, pair dynamics clamp
  L ∈ [0.5, 200] nm, dt = 1e-4 s, mobility = 1e8, diffusion = 1e-16 m²/s,
  box = 20 µm, T = 298.15 K. Debye lengths fixed: 1.36 / 0.96 / 0.68 nm for
  50 / 100 / 200 mM.
- **Numerical stability (§18 Fehler 6 — my call):** the appendix dt = 1e-4 s
  is only stable far from contact (at L = 5 nm a PMBC pair drifts ~80 nm per
  step; a near-contact core force teleports particles across the box). All
  dynamics runs therefore follow a documented, tested stability rule:
  per-step drift μ·F_max·dt ≤ 0.2 nm, enforced by a force cap F_max = 20 pN
  and dynamics dt = 1e-7 s (constructor defaults unchanged; the run's dt is
  recorded in parameters.csv). A test asserts the rule for every sweep
  configuration; the cap's effect is discussed in the report under Grenzen.
- **Units:** SI internally; forces in pN and energies in U/kBT in every output
  (§9 step 1).
- **Signs:** F < 0 attractive, F > 0 repulsive (appendix convention is
  consistent; verify in tests).

## Approaches considered

- **A. Package-first** — src library + runner scripts generate all plots/CSVs;
  notebooks optional wrappers. Most reproducible; matches rubric wording most
  literally.
- **B. Notebook-first (chosen)** — the four notebooks of §13 are the main
  analysis surface and the thing the user presents in the seminar; all physics
  lives in the shared, tested `src/` library so notebooks stay thin and
  consistent. Reproducibility risk vs. A is covered by: small pytest suite for
  `src/`, fixed seeds, and delivering the notebooks pre-executed (outputs
  embedded), each fully runnable top-to-bottom.
- **C. Minimal single script** — least code, but contradicts the "modular,
  reproducible code" rubric criterion directly. Rejected.

User decision: **B**, because the seminar presentation is the end product and
notebooks let them show each analysis step; German figure labels and README were
also accepted as stated.

## Decided how

### src/ modules (from §12, extended)

- `constants.py` — as given (kB, T_REF, NM, PN, DEBYE_LENGTHS, kBT()).
- `potentials.py` — `ProtocellForces` as given, including
  `retardation_factor(L) = 1/(1 + L/L_ret)^p` and
  `U_cl_retarded_numeric` (backward trapezoid from F, U(L_max) = 0).
  Extend only if a notebook needs a helper (e.g. force at zone boundaries).
- `force_table.py` — `force_table()` as given (columns L_nm, F_vdw_pN, F_el_pN,
  F_dlvo_pN, F_cl_ret_pN, U_vdw_kBT, U_dlvo_kBT, retardation_factor).
- `pair_dynamics.py` — `PairBrownian1D` (Euler–Maruyama: drift = mobility·F·dt,
  noise = sqrt(2·D·dt)·N(0,1), clamped to [L_min, L_max]) and `contact_zone()`
  with the six zones of §4. Add metrics helpers where §11 needs them.
- `brownian_cluster.py` — `BrownianClusterSim` as given (periodic, minimum
  image, N(0,1) noise per coordinate) but with the O(n²) pair loop vectorized
  in numpy — identical math, needed so notebook 04 sweeps run in minutes.
  Plus `lattice_positions(n, box, R, gap, seed=0)` for pre-clustered square-
  lattice initial conditions (spacing 2R + gap, centered in the box, ±10 %
  jitter) and an optional `x` constructor override.
  **Rationale (my call, addendum):** with diffusion = 1e-16 m²/s, dilute
  random starts never reach the force range in feasible simulated time —
  cluster notebooks therefore run (a) a dilute baseline (box = 20 µm: the
  honest "no clustering" result, §10's far-gap message) and (b) pre-clustered
  lattice starts (initial surface-gap sweep, default 20 nm) where persistence
  vs. evaporation — what the §11 metrics measure — is visible. The Team-2
  export runs use pre-clustered starts.
- `metrics.py` — `contact_graph`, `cluster_metrics`, `dwell_times` as given,
  plus: `escape_time` (first-passage time out of the zone the run starts in —
  §11's "Zeit bis Verlassen einer Zone"; deliberately distinct from
  `dwell_times`, which are the durations of all stays — my call),
  `return_probability`
  (P(return into zone within window T), window default 10·dt — configurable),
  `contact_probability` (fraction of time L < L_contact, default
  L_contact = 30 nm, matching the contact graph's accepted zones
  {hard_contact, dlvo_zone, near_gap, meso_gap}).
- `plots.py` — shared matplotlib helpers: German labels, one style, save to
  `figures/` and return the figure.
- `export.py` (new) — Team-2 CSV writers with the exact §17 schemas:

  | file | columns |
  |---|---|
  | positions.csv | run_id, seed, t, particle_id, x, y, model_type, A_H, lambda_D, noise, T |
  | pairs.csv | run_id, seed, t, i, j, L_nm, contact_zone, force_mode |
  | cluster_metrics.csv | run_id, seed, t, largest_cluster, mean_degree, n_edges, n_components |
  | parameters.csv | run_id, model_type, R_nm, A_H, salt_mM, L_ret_nm, p_ret, dt, mobility, diffusion |

  Written to `data/processed/`. `run_id` is deterministic from parameters
  (e.g. `dlvo_A5.0e-21_I100_s42`). The `noise` column carries the diffusion
  coefficient (that is how noise enters the model); `t` is step index times dt
  (seconds). All four files are written by one function from a finished run.

  **Export scope (user decision):** five runs — {dlvo, cl_retarded} ×
  {PMBC A_H = 5e-21, fatty A_H = 0.5e-21} at 100 mM, N = 20, fixed seed, plus
  one N = 50 cl_retarded PMBC run. positions.csv every 50th step; pairs.csv
  only pairs with L < 100 nm (zone ≠ separated) — Team 2 can recompute far
  pairs from x, y. A few MB per run; rerunning notebook 03 regenerates
  everything if Team 2 asks for more.

### Notebooks (German markdown, delivered executed with outputs embedded)

1. `01_force_curves.ipynb` — log L-grid + support points; Plots 1–4 of §14
   (F in pN vs L for vdW/el/DLVO/CL-retarded; U/kBT for fatty + PMBC;
   retardation factor for L_r = 10/20/30 nm × p = 1/2; DLVO vs CL-retarded per
   material); force tables for all A_H values; salt variation 50/100/200 mM;
   at which L the electrostatic repulsion becomes negligible (§9 step 4).
2. `02_pair_dynamics.ipynb` — pair runs per mode × representative A_H;
   L(t) trajectories (DLVO vs CL-retarded); contact probability, dwell/escape/
   return metrics; dwell-time histograms for dlvo_zone, near_gap, meso_gap
   (§14); several seeds per configuration for statistics.
3. `03_cluster_simulation.ipynb` — cluster runs for N = 10, 20, 50;
   contact graphs, cluster size distributions (§14), largest component, mean
   degree; Team-2 export of representative runs (all four CSVs).
4. `04_parameter_sweep.ipynb` — A_H × salt heatmap (color: mean largest
   cluster / persistence), noise sweep, L_r/p sweep on pair metrics, radius and
   core sensitivity, contact-definition sensitivity (vary L_contact / accepted
   zones — §15 week 6), negative control A_H = 0 (pure diffusion baseline);
   constant seeds, documented in-notebook.

Each notebook starts with a config cell (seed, parameters) and ends with a
short German "Interpretation" cell that follows §10's strict wording.

### Tests (tests/test_physics.py, small)

- F = −dU/dL numerically for every component and for DLVO total and CL total.
- Retardation factor: r ≤ 1, monotone decreasing, r(0) = 1.
- Zone boundaries at 2/5/10/30/100 nm exact per §4.
- Dwell/escape/return metrics on synthetic zone sequences.
- Cluster metrics on synthetic pair lists vs. direct networkx computation.
- CSV export: exact §17 column names and order.
- Clip/clamp behavior at L_min.
- Stability rule: for every sweep configuration, max per-step drift
  μ·F_max·dt ≤ 0.2 nm — no particle jumps across a meaningful fraction of a
  zone in one step.

### README.md (German)

Setup (python3.12 venv, requirements.txt), how to run each notebook, how to
regenerate all figures and Team-2 CSVs, seed policy, structure map, one-paragraph
summary of the four model modes, the §10 strict interpretation rule, and the §8
Lifshitz outlook (TE/TM, Matsubara, shell model — text only).

### report/report.md (German skeleton)

Sections: Einleitung · Modelle (4 Modi + Abgrenzung) · Methoden · Ergebnisse
(per mandatory plot, placeholders for user prose) · Interpretation (with §10's
mandatory statements pre-worded) · Grenzen · Übergabe an Team 2 (CSV schemas) ·
Literatur (§20). The user fills their own prose; physics statements are given.

## My calls (builder defaults — user may veto any)

- German for all user-facing text; English identifiers/comments.
- jupyterlab as the notebook frontend.
- Notebooks delivered pre-executed.
- `from src.x import ...` imports, project root inserted into `sys.path` in a
  first notebook cell (keeps the §13 layout and the appendix import style).
- Vectorized pair forces in `BrownianClusterSim` (same math, no loops).
- L_contact = 30 nm for pair contact probability; return window 10·dt.
- Runtime budget: each notebook runs end-to-end in a few minutes on a laptop;
  pair runs ~1e6 steps at dt = 1e-7 s (~0.1 s simulated time each); cluster
  sweeps sized accordingly.
- figures saved as PNG at 200 dpi into `figures/`, also shown inline.

## What's left to the builder

Exact step counts and sweep grid sizes within the runtime budget, plot styling
details, test case specifics, report wording, notebook cell breakdown.