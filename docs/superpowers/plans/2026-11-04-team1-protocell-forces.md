# Team 1 – Protocell Forces: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete Team-1 seminar project `team1_forces/` — a notebook-first Python model of protocell interactions (vdW-only, DLVO, retarded Casimir–Lifshitz) with Brownian dynamics, cluster metrics, mandatory figures, and Team-2 CSV export.

**Architecture:** Physics lives in a shared, tested `src/` package built from the assignment's starter code (§12); four German-language Jupyter notebooks are the analysis surface; `export.py` writes the four §17 CSVs. All dynamics runs use a force-capped, stability-checked configuration (§18 Fehler 6).

**Tech Stack:** Python 3.12 venv; numpy, pandas, matplotlib, networkx, jupyterlab, nbconvert, ipykernel, pytest.

**Spec:** `docs/superpowers/specs/2026-11-04-team1-protocell-forces-design.md` (approved). The authoritative assignment text is extracted into `docs/aufgabenblatt.txt` in Task 1 — formulas below are quoted from its §12/§4/§11/§17.

## Global Constraints

- Fresh git repo at the `hauptseminar/` root; frequent conventional commits. Ignore `.venv/`, `__pycache__/`, `.ipynb_checkpoints/`.
- All work inside `team1_forces/`; every command below runs with workdir `team1_forces/` unless stated. Python is `.venv/bin/python` (Task 1 creates the venv; system python is 3.7.4 — do not use it).
- Constructor defaults exactly as the appendix §12: `R=500e-9, A_H=1e-21, lambda_D=0.96e-9, B_kBT=20.0, T=298.15, L_core=0.5e-9, C_core_kBT=0.5, L_ret=20e-9, p_ret=2, L_min=0.2e-9` (potentials clip); pair dynamics clamp `L ∈ [0.5e-9, 200e-9]`; `dt=1e-4, mobility=1e8, diffusion=1e-16, box=20e-6, n=20`.
- Dynamics **runs** (notebooks) use `dt=1e-7 s` and `force_cap=20e-12 N` (20 pN); stability rule μ·F_max·dt ≤ 0.2 nm per step. Constructor defaults stay unchanged.
- Debye lengths: `{50: 1.36e-9, 100: 0.96e-9, 200: 0.68e-9}` (mM → m).
- Contact zones (§4): `hard_contact` L<2 nm, `dlvo_zone` <5, `near_gap` <10, `meso_gap` <30, `far_gap` <100, `separated` ≥100.
- Units: SI internally; pN for forces, U/kBT for energies, L in nm in all outputs. positions.csv x, y in meters.
- Never add a CL term to a vdW/DLVO term anywhere. Modes are only: `vdw`, `dlvo`, `cl_retarded`.
- German for all user-facing text (plot labels, notebook markdown, README, report); English identifiers/comments.
- Fixed, recorded seeds everywhere. Support points: (2, 3, 5, 10, 20, 30, 50, 100) nm; log L-grid 2–100 nm.
- A_H sweeps: fatty acid vesicles 0.2/0.5/1.0 ×10⁻²¹ J; PMBCs 1/3/5/10 ×10⁻²¹ J. Retardation sweep: L_r ∈ {10, 20, 30} nm, p ∈ {1, 2}.
- CSV schemas exactly as §17 (column names and order verbatim, in Task 8).
- Import style: `from src.<module> import ...` with team1_forces root on `sys.path` (conftest.py for tests, first notebook cell for notebooks).

## Review Focus

1. **Overlapping particles in the cluster sim** (dist < 2R → negative L): floored to 0.2 nm, finite forces, bounded step — no NaN, no box teleports. Tested in Task 6.
2. **Degenerate metric inputs**: empty zone sequence → `dwell_times` returns `[]`, `escape_time` returns `None`; a run that never leaves its zone must not crash. Tested in Task 5.
3. **Seed reproducibility**: same seed + same config → identical trajectories (rubric: "dokumentierte Seeds"). Tested in Task 4; relied on in Tasks 6, 12.
4. **Export zone filter**: pairs.csv keeps `far_gap` rows but drops only `separated` (L ≥ 100 nm). Tested in Task 8.
5. **Scalar-or-array force inputs**: notebooks pass grids, `force_table` passes scalars — every `ProtocellForces` method accepts both. Tested in Task 2.

---

### Task 1: Project scaffold, venv, git, assignment text

**Files:**
- Create: `team1_forces/requirements.txt`, `team1_forces/conftest.py`, `team1_forces/.gitignore`, directories `src/ notebooks/ data/raw/ data/processed/ figures/ report/ tests/`, `team1_forces/src/__init__.py` (empty)
- Create: `docs/aufgabenblatt.txt` (assignment text)
- Test: none yet (dependency check as verification)

**Interfaces:**
- Produces: repo root on `sys.path` for pytest via `conftest.py` containing exactly:
  ```python
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).resolve().parent))
  ```

- [ ] **Step 1: Create the directory tree** under `team1_forces/` as in the spec's structure diagram, plus `tests/` and an empty `src/__init__.py`; write `.gitignore` now (before the venv exists) with: `.venv/`, `__pycache__/`, `.ipynb_checkpoints/`.

- [ ] **Step 2: Write `requirements.txt`** — one per line: numpy, pandas, matplotlib, networkx, jupyterlab, nbconvert, ipykernel, pytest.

- [ ] **Step 3: Create venv and install**

Run (workdir `team1_forces/`): `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt`
Expected: exit 0.

- [ ] **Step 4: Verify imports**

Run: `.venv/bin/python -c "import numpy, pandas, matplotlib, networkx, nbconvert, ipykernel, pytest; print('deps ok')"`
Expected: `deps ok`.

- [ ] **Step 5: Extract the assignment text**

Run (workdir repo root): `pdftotext -layout hauptseminar_pdf/2026-05-20_Aufgabenblatt_Team-1_V2.pdf docs/aufgabenblatt.txt`
Expected: file exists, ~700 lines, German.

- [ ] **Step 6: Git init and first commit**

Run (workdir repo root): `git init && git add -A && git commit -m "chore: scaffold team1_forces project"`.
Expected: first commit contains `docs/`, `team1_forces/` scaffolding; `.venv/` not tracked.

### Task 2: `constants.py` + `potentials.py` (ProtocellForces)

**Files:**
- Create: `src/constants.py`, `src/potentials.py`
- Test: `tests/test_potentials.py`

**Interfaces:**
- Consumes: `conftest.py` path setup.
- Produces:
  ```python
  # src/constants.py — verbatim from §12
  kB = 1.380649e-23; T_REF = 298.15; NM = 1e-9; PN = 1e-12
  DEBYE_LENGTHS = {50: 1.36e-9, 100: 0.96e-9, 200: 0.68e-9}
  def kBT(T=T_REF) -> float  # kB*T

  # src/potentials.py
  class ProtocellForces:
      def __init__(self, R=500e-9, A_H=1e-21, lambda_D=0.96e-9, B_kBT=20.0,
                   T=298.15, L_core=0.5e-9, C_core_kBT=0.5, L_ret=20e-9,
                   p_ret=2, L_min=0.2e-9)  # sets R_eff=R/2, kappa=1/lambda_D,
                                          # B=B_kBT*kBT(T), C_core=C_core_kBT*kBT(T)
      def clip(self, L)                      # np.maximum(L, L_min)
      def U_vdw(self, L)                     # -A_H*R_eff/(6*clip)
      def F_vdw(self, L)                     # -A_H*R_eff/(6*clip**2)
      def U_el(self, L)                      # B*np.exp(-kappa*clip)
      def F_el(self, L)                      # kappa*U_el(L)
      def U_core(self, L)                    # C_core*(L_core/clip)**12
      def F_core(self, L)                    # 12*C_core*L_core**12/clip**13
      def U_dlvo(self, L)                    # U_el+U_vdw+U_core
      def F_dlvo(self, L)                    # F_el+F_vdw+F_core
      def retardation_factor(self, L)       # 1/(1+clip/L_ret)**p_ret
      def F_cl_retarded(self, L)             # F_vdw(L)*retardation_factor(L)
      def U_cl_retarded_numeric(self, L_grid)  # backward trapezoid over ascending
                                               # grid, U(L_max)=0
  ```
  All `L` methods accept float or ndarray and return matching shape. Sign convention: F < 0 attractive, F > 0 repulsive.

- [ ] **Step 1: Write failing tests** in `tests/test_potentials.py`:
  - `test_force_is_negative_gradient_of_potential`: for a **uniform** grid `L = np.linspace(0.5e-9, 100e-9, 4001)` (so `dL` is constant) and each of `(U_vdw, F_vdw), (U_el, F_el), (U_core, F_core), (U_dlvo, F_dlvo)`: `np.allclose(F(L)[1:-1], -(U(L)[2:] - U(L)[:-2])/(2*dL), rtol=5e-2)`; also `F_cl_retarded` vs numeric derivative of `U_cl_retarded_numeric(L)` on the same grid (rtol 5e-2).
  - `test_retardation_factor_bounds`: defaults → `r(5e-9) ≈ 1/(1.25)**2 = 0.64` (rtol 1e-6); `np.all(r(grid) <= 1)`; strictly decreasing on ascending grid; with `L_ret=20e-9, p_ret=2`: `r(20e-9) == 0.25`.
  - `test_clip_floors_small_L`: `U_vdw(1e-15) == U_vdw(0.2e-9)`.
  - `test_accepts_scalar_and_array`: `F_vdw(10e-9)` is a numpy scalar/float; `F_vdw(np.array([2e-9, 5e-9])).shape == (2,)`.
  - `test_mode_separation`: `F_dlvo(L)` does not equal `F_vdw(L)*retardation_factor(L)` on the grid (the models stay separate).

- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_potentials.py -v` — expected: FAIL (ModuleNotFoundError / ImportError).

- [ ] **Step 3: Implement `src/constants.py` and `src/potentials.py`** exactly per the Interfaces block (formulas verbatim from §12; `U_cl_retarded_numeric` per appendix: iterate backward, `U[i] = U[i+1] - 0.5*(F[i+1]+F[i])*dL`).

- [ ] **Step 4: Run** `.venv/bin/pytest tests/test_potentials.py -v` — expected: PASS.

- [ ] **Step 5: Commit** `src/constants.py src/potentials.py tests/test_potentials.py` with message `feat: ProtocellForces force model (vdW, DLVO, CL-retarded)`.

### Task 3: `force_table.py`

**Files:**
- Create: `src/force_table.py`
- Test: `tests/test_force_table.py`

**Interfaces:**
- Consumes: `ProtocellForces`, `kB, T_REF, PN` from constants.
- Produces: `force_table(model, L_nm_values=(2, 3, 5, 10, 20, 30, 50, 100)) -> pandas.DataFrame` with columns exactly `["L_nm", "F_vdw_pN", "F_el_pN", "F_dlvo_pN", "F_cl_ret_pN", "U_vdw_kBT", "U_dlvo_kBT", "retardation_factor"]`; forces divided by `PN`, energies by `kBT()`.

- [ ] **Step 1: Write failing tests**:
  - `test_columns_and_index`: `list(df.columns) == [...]` as above; `L_nm` values match the default tuple.
  - `test_known_value`: `ProtocellForces(A_H=5e-21)` → `df.loc[df.L_nm == 100, "F_vdw_pN"]` ≈ `-5e-21*250e-9/(6*(100e-9)**2)/1e-12 = -0.0208` (rtol 1e-3).
  - `test_dlvo_consistency`: `F_dlvo_pN ≈ F_vdw_pN + F_el_pN + F_core_pN` — core is not a column, so instead assert `F_dlvo_pN` at `L_nm=100` ≈ `F_vdw_pN` (core and electrostatics negligible there; rtol 1e-2).

- [ ] **Step 2: Run** — expected FAIL.
- [ ] **Step 3: Implement** per Interfaces block (appendix §12 structure: loop, dict per row, `pd.DataFrame(rows)`).
- [ ] **Step 4: Run** — expected PASS.
- [ ] **Step 5: Commit** — `feat: force_table support-point table`.

### Task 4: `pair_dynamics.py` (PairBrownian1D, contact zones)

**Files:**
- Create: `src/pair_dynamics.py`
- Test: `tests/test_pair_dynamics.py`

**Interfaces:**
- Consumes: `ProtocellForces`.
- Produces:
  ```python
  class PairBrownian1D:
      def __init__(self, force_model, L0=20e-9, dt=1e-4, mobility=1e8,
                   diffusion=1e-16, L_min=0.5e-9, L_max=200e-9, seed=0,
                   force_cap=None)   # None = appendix behavior
      def step(self, mode="dlvo") -> float
      def run(self, steps=10000, mode="dlvo") -> np.ndarray  # shape (steps,)
  def contact_zone(L) -> str  # six zones per Global Constraints
  ```
  `step`: F from `F_dlvo/F_vdw/F_cl_retarded` by mode (else `ValueError`); if `force_cap` set, `F = np.clip(F, -force_cap, force_cap)`; `L += mobility*F*dt + sqrt(2*diffusion*dt)*rng.normal()`; clamp to `[L_min, L_max]`.

- [ ] **Step 1: Write failing tests**:
  - `test_zone_boundaries`: `contact_zone` at 1.9e-9/2e-9/4.9e-9/5e-9/9.9e-9/10e-9/29e-9/30e-9/99e-9/100e-9 nm-scale inputs → `hard_contact, dlvo_zone, dlvo_zone, near_gap, near_gap, meso_gap, meso_gap, far_gap, far_gap, separated`.
  - `test_seed_reproducibility`: two `PairBrownian1D(model, seed=7)` with identical 500-step `run("dlvo")` → arrays `np.array_equal`.
  - `test_force_cap_bounds_drift`: `ProtocellForces(B_kBT=1e9)` (huge repulsion), `PairBrownian1D(model, L0=1e-9, dt=1e-7, force_cap=20e-12)`; 200 steps → every step's change in L ≤ `mobility*20e-12*1e-7 + sqrt(2*diffusion*dt)*6` (6σ noise margin) and trajectory finite everywhere.
  - `test_clamp`: with `force_cap=None`, `B_kBT=1e9`, 10 steps → all L within `[L_min, L_max]`.
  - `test_unknown_mode_raises`: `step(mode="bogus")` raises `ValueError`.

- [ ] **Step 2: Run** — expected FAIL.
- [ ] **Step 3: Implement** per Interfaces block; rng is `np.random.default_rng(seed)`.
- [ ] **Step 4: Run** — expected PASS.
- [ ] **Step 5: Commit** — `feat: 1D Brownian pair dynamics with force cap`.

### Task 5: zone metrics in `metrics.py`

**Files:**
- Create: `src/metrics.py` (graph functions come in Task 7; keep this file open)
- Test: `tests/test_zone_metrics.py`

**Interfaces:**
- Consumes: `contact_zone` from Task 4.
- Produces:
  ```python
  def dwell_times(zone_sequence, target_zone) -> list[int]     # durations of all contiguous stays (steps), verbatim §12
  def escape_time(zone_sequence) -> int | None                 # steps until first exit of the initial zone;
                                                               # None if the zone is never left
  def return_probability(zone_sequence, target_zone, window=10) -> float
      # over each exit from target_zone: 1 if target_zone reappears within
      # `window` steps, else 0; P = mean; 0.0 if there are no exits
  def contact_probability(L_values, L_contact=30e-9) -> float  # np.mean(L_values < L_contact)
  ```

- [ ] **Step 1: Write failing tests**:
  - `test_dwell_times`: `["near_gap"]*3 + ["meso_gap"]*2 + ["near_gap"]` target `near_gap` → `[3, 1]`; target never present → `[]`.
  - `test_escape_time`: `["meso_gap"]*5 + ["far_gap"]*4` → `5`; `["meso_gap"]*10` → `None`; `[]` → `None`.
  - `test_return_probability`: seq `["A", "A", "B", "B", "B", "A"]` (A=target, exit at index 2, return at index 5): `window=2` → 0.0 (return 3 steps after the exit), `window=5` → 1.0; target never present → 0.0.
  - `test_contact_probability`: `np.array([10e-9, 40e-9, 29e-9])` → `2/3` (default `L_contact=30e-9`).

- [ ] **Step 2: Run** — expected FAIL.
- [ ] **Step 3: Implement** in `src/metrics.py` (dwell_times per appendix §12; escape/return as one-pass loops).
- [ ] **Step 4: Run** — expected PASS.
- [ ] **Step 5: Commit** — `feat: dwell/escape/return/contact-probability metrics`.

### Task 6: `brownian_cluster.py` (vectorized 2D sim)

**Files:**
- Create: `src/brownian_cluster.py`
- Test: `tests/test_brownian_cluster.py`

**Interfaces:**
- Consumes: `ProtocellForces`, `contact_zone`.
- Produces:
  ```python
  class BrownianClusterSim:
      def __init__(self, n=20, R=500e-9, box=20e-6, dt=1e-4, mobility=1e8,
                   diffusion=1e-16, seed=0, force_cap=None, x=None)
          # x=None → rng.uniform(0, box, (n,2)); else x.copy()
      def minimum_image(self, delta)          # delta - box*round(delta/box)
      def step(self, force_model, mode="dlvo") -> np.ndarray  # positions (n,2)
      def pair_distance_table(self) -> list[tuple[int, int, float, str]]  # (i, j, L, zone)
  def lattice_positions(n, box, R, gap, seed=0) -> np.ndarray
      # ceil(sqrt(n))-sided square lattice, spacing 2R+gap, centered in box,
      # per-coordinate jitter U(-0.1*(2R+gap), +0.1*(2R+gap)), first n nodes
  ```
  `step` is the vectorized appendix math: broadcast all pairwise `delta` (n,n,2) → `dist` matrix (+1e-30) → `L = np.maximum(dist - 2R, 0.2e-9)` → scalar force matrix via the mode's method (methods accept arrays) → clip to ±`force_cap` if set → force vectors `F_matrix[...,None] * delta/dist` summed over axis 1 (Newton's third law: `forces[j] -=` equivalent by antisymmetry) → `x += mobility*forces*dt + sqrt(2*diffusion*dt)*rng.normal(size=(n,2))` → `np.mod(x, box)`.

- [ ] **Step 1: Write failing tests**:
  - `test_matches_loop_reference`: n=3, fixed seed, tiny box so all pairs interact; one `step` must equal a naive double-loop implementation written inside the test (same math incl. cap and mod) within `atol=1e-18`.
  - `test_overlap_is_floored`: two particles placed overlapping (`dist < 2R`): after one step with `force_cap=20e-12`, all positions finite, every per-step displacement norm ≤ `mobility*20e-12*dt + 6*sqrt(2*diffusion*dt)`.
  - `test_minimum_image`: box=20e-6, `minimum_image(np.array([19e-6, 0.0]))` → `[-1e-6, 0.0]`.
  - `test_pair_distance_table_zones`: constructed `x` with one pair at surface gap 3 nm → that row's zone is `dlvo_zone`; a far pair → `separated`.
  - `test_lattice_positions`: n=20, R=500e-9, box=20e-6, gap=20e-9 → no overlap (`dist >= 2R` for all pairs), all inside `[0, box]`, seed reproducible.
  - `test_seed_reproducibility`: same seed/config, 50 steps → identical `x`.

- [ ] **Step 2: Run** — expected FAIL.
- [ ] **Step 3: Implement** per Interfaces block.
- [ ] **Step 4: Run** — expected PASS.
- [ ] **Step 5: Commit** — `feat: vectorized Brownian cluster simulation`.

### Task 7: contact graphs and cluster metrics in `metrics.py`

**Files:**
- Modify: `src/metrics.py` (append)
- Test: `tests/test_cluster_metrics.py`

**Interfaces:**
- Consumes: `pair_rows` in the `(i, j, L, zone)` shape from Task 6.
- Produces:
  ```python
  CONTACT_ZONES = {"hard_contact", "dlvo_zone", "near_gap", "meso_gap"}
  def contact_graph(pair_rows, n, accepted_zones=CONTACT_ZONES) -> networkx.Graph  # nodes 0..n-1, edge attrs L, zone
  def cluster_metrics(pair_rows, n) -> dict  # {"largest_cluster": int, "n_components": int,
                                              #  "mean_degree": float, "n_edges": int}
  ```

- [ ] **Step 1: Write failing tests**:
  - `test_known_graph`: n=4, edges (0,1) `hard_contact`, (1,2) `near_gap`, (2,3) `separated` → `cluster_metrics` gives `largest_cluster=3, n_components=2, n_edges=2, mean_degree=1.0`; `contact_graph` edge attrs carry `L` and `zone`.
  - `test_no_edges`: no pair rows → `largest_cluster=1, n_components=n, n_edges=0, mean_degree=0.0`.
  - `test_accepted_zones_filter`: an edge with zone `far_gap` is excluded by default but included when passed in `accepted_zones`.

- [ ] **Step 2: Run** — expected FAIL.
- [ ] **Step 3: Implement** per appendix §12 (`networkx.Graph`, `connected_components`, `g.degree()`).
- [ ] **Step 4: Run** — expected PASS.
- [ ] **Step 5: Commit** — `feat: contact graph and cluster metrics`.

### Task 8: `export.py` (Team-2 CSVs)

**Files:**
- Create: `src/export.py`
- Test: `tests/test_export.py`

**Interfaces:**
- Consumes: `cluster_metrics` (per frame), constants.
- Produces:
  ```python
  def make_run_id(model_type, A_H, salt_mM, n, seed) -> str
      # f"{model_type}_A{A_H:.1e}_I{salt_mM:g}_N{n}_s{seed}"  e.g. "dlvo_A5.0e-21_I100_N20_s42"
  def export_run(out_dir="data/processed", run_id="", seed=0, model_type="dlvo",
                 A_H=5e-21, lambda_D=0.96e-9, noise=1e-16, T=298.15,
                 R_nm=500.0, salt_mM=100, L_ret_nm=20.0, p_ret=2,
                 dt=1e-7, mobility=1e8, diffusion=1e-16, frames=None) -> list[Path]
      # frames: iterable of (t_seconds, positions ndarray (n,2), pair_rows list)
      # appends to (creating with header if absent):
      # positions.csv:      run_id,seed,t,particle_id,x,y,model_type,A_H,lambda_D,noise,T
      # pairs.csv:           run_id,seed,t,i,j,L_nm,contact_zone,force_mode   (rows with zone != "separated")
      # cluster_metrics.csv: run_id,seed,t,largest_cluster,mean_degree,n_edges,n_components
      # parameters.csv:      run_id,model_type,R_nm,A_H,salt_mM,L_ret_nm,p_ret,dt,mobility,diffusion
      #     one row per export_run call; L_nm = L in nanometers; x,y in meters
  ```

- [ ] **Step 1: Write failing tests** (use `tmp_path` as out_dir):
  - `test_columns_exact`: read back with `pd.read_csv` → `list(df.columns)` equals each §17 schema verbatim (all four files).
  - `test_two_runs_append`: two `export_run` calls (distinct run_ids, 2 frames of n=3) → positions.csv has 12 rows, parameters.csv has 2 rows, run_id sets correct.
  - `test_pairs_filter`: frame with one `far_gap` pair and one `separated` pair → pairs.csv contains the `far_gap` row, not the `separated` row; `L_nm` value is `L/1e-9`.
  - `test_run_id_format`: `make_run_id("cl_retarded", 5e-21, 100, 50, 42)` → `"cl_retarded_A5.0e-21_I100_N50_s42"`.

- [ ] **Step 2: Run** — expected FAIL.
- [ ] **Step 3: Implement**: build DataFrames per run and `to_csv(mode="a", header=not file_exists, index=False)`; compute `cluster_metrics(pair_rows, n)` per frame.
- [ ] **Step 4: Run** — expected PASS.
- [ ] **Step 5: Commit** — `feat: Team-2 CSV export (§17 schemas)`.

### Task 9: `plots.py`

**Files:**
- Create: `src/plots.py`
- Test: `tests/test_plots.py`

**Interfaces:**
- Produces:
  ```python
  def setup_style() -> None      # rcParams: figure.figsize (7, 4.5), dpi 200, savefig.dpi 200,
                                 # font.size 11, axes.grid True, grid alpha 0.3; no seaborn, no external fonts
  def save_fig(fig, name) -> Path  # saves <root>/figures/<name>.png (root = parents[1] of this file), returns path
  ```

- [ ] **Step 1: Write failing test**: `test_save_fig` — `fig, ax = plt.subplots(); ax.plot(...)`; `save_fig(fig, "smoke")` → file exists at `figures/smoke.png`; cleanup after.
- [ ] **Step 2: Run** — expected FAIL.
- [ ] **Step 3: Implement** (two small functions).
- [ ] **Step 4: Run** — expected PASS.
- [ ] **Step 5: Commit** — `feat: shared plotting helpers`.

### Task 10: Notebook `01_force_curves.ipynb`

**Files:**
- Create: `notebooks/01_force_curves.ipynb`
- Consumes: `ProtocellForces`, `force_table`, `plots`, constants.

- [ ] **Step 1: Write the notebook** (German markdown cells, first cell):
  ```python
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()))
  ```
  Content (Plots 1–4 of §14, each saved to `figures/` and shown inline):
  - log L-grid `np.geomspace(2e-9, 100e-9, 300)` + support points; `setup_style()`.
  - Plot 1: F in pN vs L (log axes) for vdW-only, electrostatic, DLVO, CL-retarded — one material (PMBC, A_H=5e-21), salt 100 mM; German axis labels.
  - Plot 2: U/kBT vs L for fatty (A_H=0.5e-21) and PMBC (A_H=5e-21) — vdW and DLVO.
  - Plot 3: retardation factor r(L) for L_r ∈ {10, 20, 30} nm × p ∈ {1, 2}.
  - Plot 4: DLVO vs CL-retarded F in pN for fatty and PMBC.
  - Salt study: F_el and F_dlvo at 50/100/200 mM; a markdown cell answering §9 step 4 (from which L the electrostatic repulsion is practically gone, vs Debye lengths).
  - Force tables: `force_table(...)` for all A_H values (fatty 0.2/0.5/1.0, PMBC 1/3/5/10 ×10⁻²¹ J), rendered as DataFrames.
  - Interpretation cell (German) using §10's strict wording.
- [ ] **Step 2: Execute**

Run: `.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 notebooks/01_force_curves.ipynb`
Expected: exit 0, no cell errors; `figures/` contains plot-1–4 PNGs.
- [ ] **Step 3: Commit** — `feat: notebook 01 force curves (Pflichtplots 1–4)`.

### Task 11: Notebook `02_pair_dynamics.ipynb`

**Files:**
- Create: `notebooks/02_pair_dynamics.ipynb`
- Consumes: `PairBrownian1D`, `contact_zone`, zone metrics, `plots`.

- [ ] **Step 1: Write the notebook**: German markdown; config cell with `DT = 1e-7`, `FORCE_CAP = 20e-12`, `STEPS = 1_000_000`, `SEEDS = [0, 1, 2, 3]`.
  - L(t) trajectories (in nm vs t in s) for DLVO and CL-retarded, fatty and PMBC, L0 = 20 nm — Pflichtplot; zone shading bands (2/5/10/30/100 nm).
  - Zone-sequence computation per run (`contact_zone` applied to trajectory); per mode × material: contact probability, mean dwell/escape/return per zone, aggregated over seeds.
  - Dwell-time histograms for `dlvo_zone`, `near_gap`, `meso_gap` (Pflichtplot), in seconds (steps × DT).
  - Interpretation cell per §10.
- [ ] **Step 2: Execute** as in Task 10 (timeout 900). Expected: exit 0; trajectory + histogram figures saved.
- [ ] **Step 3: Commit** — `feat: notebook 02 pair dynamics and zone metrics`.

### Task 12: Notebook `03_cluster_simulation.ipynb` + Team-2 export

**Files:**
- Create: `notebooks/03_cluster_simulation.ipynb`
- Consumes: `BrownianClusterSim`, `lattice_positions`, graph metrics, `export_run`, `make_run_id`.

- [ ] **Step 1: Write the notebook**: German markdown; config cell `DT = 1e-7`, `FORCE_CAP = 20e-12`, `STEPS = 100_000`, record every 50th step.
  - Dilute baseline: n=20, box=20 µm, random start — show contact graph / cluster metrics are (nearly) empty; markdown explaining why (ties to §10 far-gap message).
  - Pre-clustered runs: `lattice_positions` initial gap sweep {5, 20, 50} nm, modes dlvo/cl_retarded, PMBC + fatty, N ∈ {10, 20, 50}: cluster-size distributions over time (Pflichtplot), largest component and mean degree time series, snapshots of configurations with contact graphs drawn (networkx spring layout).
  - Export runs (the spec's five, seed 42, pre-clustered start gap 20 nm, salt 100 mM, `dt=DT`): {dlvo, cl_retarded} × {PMBC A_H=5e-21, fatty A_H=0.5e-21} N=20, plus cl_retarded PMBC N=50 — `export_run` per run into `data/processed/`; final cell prints the four files' shapes and a schema summary for Team 2.
  - Interpretation cell per §10.
- [ ] **Step 2: Execute** (timeout 1200). Expected: exit 0; `data/processed/` holds the four CSVs; run_ids match `make_run_id`; positions.csv row count = 5 runs × 2000 frames × N (per run) summed.
- [ ] **Step 3: Sanity-check the export**

Run: `.venv/bin/python -c "import pandas as pd; df=pd.read_csv('data/processed/pairs.csv'); print(df.contact_zone.value_counts()); print(df.run_id.unique())"`
Expected: zones only from {hard_contact, dlvo_zone, near_gap, meso_gap, far_gap}; five run_ids.
- [ ] **Step 4: Commit** — `feat: notebook 03 cluster simulation and Team-2 export`.

### Task 13: Notebook `04_parameter_sweep.ipynb`

**Files:**
- Create: `notebooks/04_parameter_sweep.ipynb`
- Consumes: everything from src.

- [ ] **Step 1: Write the notebook**: German markdown; config cell (DT, FORCE_CAP, seeds fixed and listed).
  - Heatmap (Pflichtplot): A_H ∈ {0.2, 0.5, 1, 3, 5, 10} ×10⁻²¹ J × salt ∈ {50, 100, 200} mM, color = mean largest cluster (pre-clustered start, N=20, cl_retarded, 2×10⁴ steps, seed 42).
  - Noise sweep: diffusion ∈ {1e-17, 1e-16, 1e-15, 1e-14} m²/s → contact probability / persistence.
  - L_r ∈ {10, 20, 30} × p ∈ {1, 2} sweep on pair metrics (escape/dwell) — CL sensitivity.
  - Radius sweep R ∈ {100, 250, 500, 1000} nm; core sensitivity `C_core_kBT` ∈ {0.1, 0.5, 1.0} and `L_core` ∈ {0.3, 0.5, 1.0} nm.
  - Contact-definition sensitivity: `L_contact` ∈ {5, 10, 30} nm and accepted-zones variants → largest cluster vs definition (§15 week 6).
  - Negative control: A_H=0 (pure diffusion baseline) — pre-clustered start evaporates; markdown comparing to force runs.
  - Interpretation cell per §10.
- [ ] **Step 2: Execute** (timeout 1800). Expected: exit 0; heatmap + sweep figures saved.
- [ ] **Step 3: Commit** — `feat: notebook 04 sensitivity sweeps and negative control`.

### Task 14: README, report skeleton, final verification

**Files:**
- Create: `team1_forces/README.md`, `team1_forces/report/report.md`

**Interfaces:**
- Consumes: everything.

- [ ] **Step 1: Write `README.md` in German** — setup (python3.12 venv, `pip install -r requirements.txt`), how to run each notebook (`jupyter lab` or the nbconvert command), how to regenerate all figures and Team-2 CSVs, seed policy, structure map, one paragraph per model mode with the §3 separation rule, §10's strict interpretation statement, §8 Lifshitz outlook (TE/TM, Matsubara, shell model — text only), Team-2 CSV schema table.
- [ ] **Step 2: Write `report/report.md` in German** — skeleton with sections Einleitung · Modelle (4 Modi + Abgrenzung) · Methoden · Ergebnisse (per Pflichtplot, embedding `figures/*.png`, placeholders `[hier eigene Prosa ergänzen]`) · Interpretation (§10 statements pre-worded) · Grenzen (incl. force-cap effect and capped-dynamics discussion) · Übergabe an Team 2 (§17 schemas) · Literatur (§20 references).
- [ ] **Step 3: Full verification**

Run (workdir `team1_forces/`): `.venv/bin/pytest -q` → all tests PASS.
Run: re-execute all four notebooks with nbconvert (commands from Tasks 10–13) → exit 0 each.
Expected: tests green, all notebooks clean, `figures/` and `data/processed/` populated.
- [ ] **Step 4: Commit** — `docs: German README and report skeleton`; then a final `git add -A && git commit` if anything remains untracked.