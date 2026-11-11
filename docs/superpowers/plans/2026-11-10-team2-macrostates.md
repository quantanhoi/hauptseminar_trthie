# Team 2 Macrostates and Attractor Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Deliver the tested Team-2 coarse-graining/analysis project, then extend Team-1 exports to a fair three-model, two-material, three-seed ensemble and regenerate the final German deliverables.

**Architecture:** A small `src/` library implements zones, graphs, labels, sequence metrics, robustness, and Team-1 I/O. Three executed notebooks orchestrate analysis and figures from real CSVs; only after the initial checkpoint does Team-1 notebook 03 generate the extended ensemble, followed by a clean Team-2 rerun.

**Tech Stack:** Python 3.12, NumPy, pandas, NetworkX, Matplotlib, Jupyter/nbconvert, pytest; existing `team1_forces/.venv`.

**Spec:** `docs/superpowers/specs/2026-11-10-team2-macrostates-design.md`

## Global Constraints

- Follow the approved spec; Team-2 source is `hauptseminar_pdf/2026-11-04_Aufgabenblatt_Team-2_V2.pdf`.
- German user-facing prose/figure labels; English identifiers. SI positions internally, pair output L_nm in nm.
- Exact zones: hard `<2`, DLVO `[2,5)`, near `[5,10)`, meso `[10,30)`, far `[30,100)`, separated `>=100` nm.
- Final fair ensemble: N=20; {`vdw`, `dlvo`, `cl_retarded`} × A_H {0.5e-21, 5e-21} × seeds {0,1,42}; N=50 remains separate.
- Canonical Team-2/3 names: `vdw_only`, `dlvo_classic`, `cl_retarded`; materials `fatty_acid`, `PMBC` only for the two documented A_H values.
- No `cl_meso_hypothesis`, invented force law, new dependencies, Team-1 physics changes, or edits to notebook 01.
- Default min dwell 5, return horizons 50/200 recorded frames, jitter sigma 1 nm, Team-1 box 20e-6 m.
- Team 3 receives meso raw+filtered sequences with the exact approved §14 columns; never discard raw sequences.
- Do not run git mutations or create commits unless the user explicitly authorizes them at that point.

## Review Focus

- Periodic boundary pairs: positions across the 20 µm box must use minimum-image surface distance; Task 1 pins this with a numeric test.
- Degenerate filtering: leading/trailing/all-short runs must not leak unfiltered labels or invent a valid previous state; Task 3 pins all three cases.
- Right-censored returns: departures without a complete horizon must be excluded, not counted as failures; Task 3 pins eligibility and NaN behaviour.
- Empty/sparse frames: a run with no non-separated pairs must still emit valid schemas, isolated nodes, and monomer labels; Tasks 1 and 5 pin this.
- Metadata integrity: inconsistent particle sets, duplicate frame/particle rows, unknown A_H, and single-seed data must not be silently reinterpreted; Task 5 and Task 7 pin validation, `unknown`, and `not assessable` behaviour.

---

### Task 1: Distance Zones and Contact Graphs

**Files:**
- Create: `team2_macrostates/requirements.txt`, `team2_macrostates/conftest.py`, `team2_macrostates/src/zones.py`, `team2_macrostates/src/contact_graphs.py`
- Test: `team2_macrostates/tests/test_zones.py`, `team2_macrostates/tests/test_contact_graphs.py`

**Interfaces:**
- Produces: `surface_distance(p_i, p_j, R=500e-9, box=None) -> float`; `distance_zone(L) -> str`; `allowed_zones(graph_type="meso") -> set[str]`.
- Produces: `pair_table(positions, particle_ids, R=500e-9, box=None) -> pd.DataFrame` with columns `i,j,L_m,L_nm,zone`; `contact_graph(pair_df, particle_ids, graph_type="meso") -> nx.Graph`; `graph_features(G) -> dict` with `largest_cluster,number_of_components,number_of_edges,mean_degree,cluster_size_distribution`.

- [x] **Step 1: Write failing zone/graph tests**
  Assert exact boundaries at 2/5/10/30/100 nm, invalid graph types raising ValueError, and `surface_distance([0,0],[2R+5e-9,0]) == 5e-9`. For box=20e-6 and R=500e-9, points at x=0.5e-6 and x=19.495e-6 have direct centre distance 18.995e-6 but minimum-image centre distance 1.005e-6, hence L=5e-9; also assert a non-wrapping pair to distinguish the convention. Graph tests use isolated nodes plus pairs at 1, 7, 20, and 50 nm to assert hard/near/meso edge membership, retained isolates, feature counts, descending component sizes, and empty pair-table behaviour.
- [x] **Step 2: Run tests and verify import failure**
  From `team2_macrostates/`: `../team1_forces/.venv/bin/python -m pytest tests/test_zones.py tests/test_contact_graphs.py -v`; expected FAIL because modules do not exist.
- [x] **Step 3: Implement the minimal modules and project test/setup files**
  Implement scalar distances/zones from the appendix, one O(n²) pair-table pass, graph construction from cached pair rows, and NetworkX features. `cluster_size_distribution` is a descending list in the function result; serialization is Task 5. Validate matching position/ID lengths and finite positions. Requirements mirror Team 1; conftest inserts the Team-2 project root into `sys.path`.
- [x] **Step 4: Run focused tests**
  Run the Step-2 command; expected all PASS, including periodic, isolated-node, and empty-pair cases.

### Task 2: Rule-Based Macrostates

**Files:**
- Create: `team2_macrostates/src/macrostates.py`
- Test: `team2_macrostates/tests/test_macrostates.py`

**Interfaces:**
- Consumes: NetworkX graphs from Task 1.
- Produces: `macrostate_from_graph(G) -> str`.

- [x] **Step 1: Write failing branch tests**
  Construct graphs for no edges, largest components of size 2/3/≥5, a four-node component with 3 edges, one with 4 edges, and an invalid/fallback stub if reachable. Assert respectively `monomer_gas`, `dimer_dominated`, `trimer_like`, `large_cluster`, `loose_four_cluster`, `tetra_like`, `mixed_transition`; ensure a separate dimer does not change the largest-component decision.
- [x] **Step 2: Verify failure, implement, and verify pass**
  Run `../team1_forces/.venv/bin/python -m pytest tests/test_macrostates.py -v` from `team2_macrostates/`; implement only the approved static rules, then rerun expecting PASS. Document the 2D tetra proxy in the function docstring.

### Task 3: Persistence, Dwell, Transition, and Return Metrics

**Files:**
- Create: `team2_macrostates/src/sequences.py`
- Test: `team2_macrostates/tests/test_sequences.py`

**Interfaces:**
- Produces: `filter_short_states(sequence, min_dwell=5) -> list[str]`.
- Produces: `dwell_runs(sequence, times) -> pd.DataFrame` with `state,start_index,end_index,start_time,end_time,dwell_steps,dwell_seconds,left_censored,right_censored`.
- Produces: `transition_counts(sequence, states=None) -> pd.DataFrame`; `normalize_transition_counts(counts) -> pd.DataFrame`.
- Produces: `return_summary(sequence, times, target_state, horizon) -> dict` with `return_probability,mean_return_steps,mean_return_seconds,eligible_departures,returns`.
- Produces: `attractor_candidate(frequency, mean_dwell_steps, return_probability, seed_count, label_agreement, total_seeds) -> dict` with the five approved criterion flags and `candidate`; unavailable evidence is None and cannot pass. `total_seeds < 3` makes reproducibility unavailable; with ≥3 total seeds, a state present in fewer than three fails the criterion.

- [x] **Step 1: Write failing synthetic-sequence tests**
  Pin internal/leading/trailing short runs and all-short → `mixed_transition`; min_dwell=1 identity and length preservation. For `['a','a','b','a']`, assert dwell runs `(a,2),(b,1),(a,1)` with correct censor flags and median-sample-based seconds. Assert pooled counts, row normalization, empty outgoing rows → NaN, and self-transition diagonal. For `['a','b','a','b']`, horizon 2: only departure t=0 is eligible, return probability 1, mean return 2 steps and `times[2]-times[0]` seconds; a truncated departure must not enter the denominator. Assert no eligible departures and no observed returns produce NaN means/probabilities as appropriate. Candidate tests assert `(0.1,6,0.4,3,0.8,total_seeds=3)` passes, strict threshold boundaries do not pass `>` criteria, total_seeds=1 makes reproducibility unavailable, seed_count=1 with total_seeds=3 fails reproducibility, and NaN evidence yields an unavailable flag and `candidate=False`.
- [x] **Step 2: Verify failure**
  Run `../team1_forces/.venv/bin/python -m pytest tests/test_sequences.py -v`; expected import FAIL.
- [x] **Step 3: Implement metrics**
  Use run-length encoding shared by filtering/dwell, next-valid replacement for leading runs, previous-valid otherwise, complete-horizon eligibility for returns, and actual timestamps for return seconds. Implement the strict §9 candidate thresholds and unavailable-evidence flags. Reject min_dwell<1, nonpositive horizon, mismatched sequence/time lengths, and unsorted times.
- [x] **Step 4: Verify pass**
  Rerun the Task-3 test command; expected all PASS, especially right-censoring and all-short filtering.

### Task 4: Deterministic Jitter Robustness

**Files:**
- Create: `team2_macrostates/src/robustness.py`
- Test: `team2_macrostates/tests/test_robustness.py`

**Interfaces:**
- Produces: `jitter_positions(positions, sigma_nm=1.0, seed=0, box=None) -> np.ndarray`; `label_agreement(seq_a, seq_b) -> float`.

- [x] **Step 1: Write failing robustness tests**
  Assert same seed reproduces the same jitter, sigma=0 is exact, optional box wraps coordinates, identical labels agree at 1.0, disjoint labels at 0.0, empty labels return NaN, and unequal nonempty lengths raise ValueError rather than silently truncating.
- [x] **Step 2: Verify failure, implement, rerun**
  Run `../team1_forces/.venv/bin/python -m pytest tests/test_robustness.py -v`; implement NumPy Generator normal perturbations and exact sequence comparison, then rerun expecting PASS.

### Task 5: Team-1 Loading, Per-Run Pipeline, and Team-3 Schema

**Files:**
- Create: `team2_macrostates/src/pipeline.py`
- Test: `team2_macrostates/tests/test_pipeline.py`

**Interfaces:**
- Consumes: Tasks 1–3 and Team-1 `positions.csv`/`parameters.csv`.
- Produces: `load_team1_data(input_dir, box=20e-6) -> tuple[pd.DataFrame,pd.DataFrame]`; positions rename `t` to `time`, gain `R_nm,salt_mM,material_type`, and use canonical `model_type`.
- Produces: `analyze_run(df_run, box=20e-6, min_dwell=5) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]` for non-separated pairs, all graph features, and raw+filtered sequences for hard/near/meso.
- Produces: `run_pipeline(input_dir, out_dir, box=20e-6, min_dwell=5) -> dict[str,pd.DataFrame]`, writing `pair_zones.csv`, `graph_features.csv`, `macrostate_sequences.csv` with stable headers even when empty.
- Produces: `export_team3(sequences, out_path) -> pd.DataFrame`, meso only, exact columns `run_id,seed,time,macrostate_raw,macrostate_filtered,model_type,material_type,A_H,salt_mM,noise,largest_cluster,mean_degree`.

- [x] **Step 1: Write failing integration/validation tests**
  Build a two-run temporary Team-1 dataset (three particles, several frames) with known zone labels and metadata. Assert canonical names, exact A_H→material mapping plus unknown A_H→`unknown`, per-frame three graph rows, preserved particle IDs, raw/filtered length equality, non-separated pair filtering, feature propagation, and exact Team-3 columns/meso filtering. Assert duplicate `(run_id,t,particle_id)`, nonfinite coordinates, inconsistent particles within a run, missing columns, and nonpositive radius raise ValueError. Include an all-separated run and assert empty pair output with headers plus monomer sequences.
- [x] **Step 2: Verify failure**
  Run `../team1_forces/.venv/bin/python -m pytest tests/test_pipeline.py -v`; expected import FAIL.
- [x] **Step 3: Implement loader, orchestration, and export**
  Merge radius/salt by run_id, validate one run's metadata/particle sets, sort real times/IDs, canonicalize only known model aliases, call `pair_table` once per frame and reuse it for all three graphs. Serialize component sizes as semicolon-separated descending integers. Concatenate deterministically and write CSVs without mutating Team 1.
- [x] **Step 4: Verify integration and all prior tests**
  Run `../team1_forces/.venv/bin/python -m pytest tests -v` from `team2_macrostates/`; expected all PASS.

### Task 6: Core Notebooks, Dynamics Tables, and Figures 1–5

**Files:**
- Create: `team2_macrostates/src/plots.py`, `team2_macrostates/notebooks/01_zones_graphs.ipynb`, `team2_macrostates/notebooks/02_sequences_attractors.ipynb`, `team2_macrostates/README.md`
- Modify: `team2_macrostates/src/pipeline.py` only if a notebook exercise exposes a concrete defect, with a regression test.
- Test: `team2_macrostates/tests/test_plots.py`

**Interfaces:**
- Consumes: Task-5 real-data outputs and Task-3 metrics.
- Produces: real-data `dwell_times.csv`, long `transition_matrices.csv`, preliminary `sequence_metrics.csv`, `team3_macrostates.csv`, and figures 01–05 in `team2_macrostates/figures/`.

- [x] **Step 1: Add plotting smoke tests**
  Create tiny figures through each shared plotting helper; assert German-labelled axes/nonempty artists and 200 dpi PNG output without relying on interactive display. Run the focused test before implementation and verify import failure.
- [x] **Step 2: Implement shared plotting helpers and notebook 01**
  Notebook 01 validates/documents units and the current five-run inventory, runs `run_pipeline`, displays zone/graph examples and hard/near/meso sensitivity, and writes figure 02 (cluster sizes by available model/material). Save all real-data outputs under `data/processed/`.
- [x] **Step 3: Implement notebook 02**
  Use per-run sequences to calculate dwell tables and pooled transition counts; calculate T50 return probability and T200 mean return with eligibility counts. Generate figure 01 raw/filtered for a deterministically selected representative run, figure 03 dwell distributions with raw/filtered distinction, figure 04 model heatmaps on a common state order, and figure 05 return probabilities. Export meso Team-3 CSV via Task 5. Record the single-seed limitation as `not assessable`.
- [x] **Step 4: Execute and verify the initial core analysis**
  From `team2_macrostates/`: run nbconvert `--execute --inplace --ExecutePreprocessor.timeout=1800` for notebooks 01 and 02 using the existing venv. Run all tests. Programmatically assert nonempty real-data tables, five current run IDs, three graph rows per frame, exact Team-3 schema, and five nonempty figures; inspect the figures visually.

### Task 7: Robustness Notebook, Candidate Table, and Initial German Report

**Files:**
- Create: `team2_macrostates/notebooks/03_robustness_comparison.ipynb`, `team2_macrostates/report/report.md`
- Modify: `team2_macrostates/README.md`, `team2_macrostates/src/pipeline.py` only for a tested defect.
- Test: `team2_macrostates/tests/test_pipeline.py` if modified.

**Interfaces:**
- Consumes: saved positions plus Tasks 1–5 outputs.
- Produces: final-schema `sequence_metrics.csv`, `attractor_candidates.csv`, figures 06–07, and the complete initial report structure/reflection.

- [x] **Step 1: Implement deterministic real-data jitter analysis**
  For every current run/frame/graph, derive jitter seeds from recorded run/frame identifiers without Python's randomized `hash()`, recompute raw labels at sigma=1 nm, and save agreement per run/graph/state grouping. Filtering must not enter label agreement. Generate figure 06 and the fatty-acid/PMBC comparison figure 07; current single-seed reproducibility remains unavailable.
- [x] **Step 2: Implement candidate heuristics and report**
  Combine frequency, dwell, T50 return, distinct seed count, and agreement through `attractor_candidate`; a criterion with unavailable evidence cannot be silently passed, and one seed renders seed reproducibility unavailable. Write the German README/report with actual current-data numbers, figure links, Team-3 schema, preclustered-start and 2D-proxy limitations, no attractor proof, and an explicit absent `cl_meso_hypothesis` section.
- [x] **Step 3: Execute notebook 03 and verify initial checkpoint**
  Execute notebook 03 with nbconvert, rerun all Team-2 tests, assert seven nonempty figures and all approved CSV schemas, inspect figures 06–07, and record runtime/output sizes. Expected result: a complete honest five-run checkpoint before Team-1 changes.

### Task 8: Targeted Team-1 Multi-Seed/Model Export Extension

**Files:**
- Modify: `team1_forces/notebooks/03_cluster_simulation.ipynb` run helper, every caller (baseline, gap sweep, N sweep, exports), and export documentation cells.
- Modify: `team1_forces/README.md`, `team1_forces/report/report.md` run-count/seed sections.
- Test: `team1_forces/tests/test_export.py` only if schema behaviour changes (it should not).

**Interfaces:**
- Consumes: existing `BrownianClusterSim`, `lattice_positions`, `ProtocellForces`, `export_run`, `make_run_id` unchanged.
- Produces: 18 N=20 runs for modes `vdw,dlvo,cl_retarded`, both A_H values, seeds 0/1/42, plus existing N=50 CL/PMBC seed 42; unchanged Team-1 CSV schemas.

- [x] **Step 1: Update notebook configuration without executing other Team-1 notebooks**
  Make `run_cluster(..., seed)` explicit, update every baseline/gap/N-sweep/export caller, and thread the seed through simulation/start/export IDs. Build deterministic nested model/material/seed configuration for the approved matrix and retain N=50 separately. Update markdown from five to 19 runs and README/report scope. Do not alter notebook 01 or any force function/CSV column.
- [x] **Step 2: Run Team-1 tests before regeneration**
  From `team1_forces/`: `.venv/bin/python -m pytest tests -v`; expected all existing tests PASS.
- [x] **Step 3: Execute notebook 03 and validate the regenerated ensemble**
  Run notebook 03 with nbconvert timeout 1800 (increase only if measured runtime requires). Assert exactly 19 unique run_ids; the N=20 subset has every model/material/seed combination exactly once, 1,000 frames/run, consistent particle counts, no duplicate keys, and the same numerical metadata. Verify the N=50 run is not in the fair-comparison configuration. Inspect generated Team-1 figures for obvious failures.

### Task 9: Final Team-2 Regeneration and Whole-Deliverable Verification

**Files:**
- Modify: all three executed Team-2 notebooks, `team2_macrostates/README.md`, `team2_macrostates/report/report.md` with final results.
- Regenerate: `team2_macrostates/data/processed/*`, `team2_macrostates/figures/*`.

**Interfaces:**
- Consumes: validated 19-run Team-1 export and all prior Team-2 modules/notebooks.

- [x] **Step 1: Cleanly rerun the Team-2 analysis on extended data**
  Execute notebooks 01→02→03 with nbconvert. Ensure fair model/material tables filter N=20 and common seeds {0,1,42}; retain N=50 only in explicitly separate exploration. Replace preliminary five-run prose with actual final values and state where evidence remains weak.
- [x] **Step 2: Run complete automated verification**
  Run both projects' pytest suites and all notebook execution checks. Assert the final Team-3 file contains only `vdw_only,dlvo_classic,cl_retarded`, only `fatty_acid,PMBC`, all 19 validated run_ids (18 fair-comparison N=20 runs plus the separately interpreted N=50 run), three seeds per compared N=20 group, raw/filtered length equality, and no null labels. Validate dwell/return eligibility counts and transition normalization; assert all seven figures are nonempty and updated after the extended inputs.
- [x] **Step 3: Inspect and reconcile scientific claims**
  Visually inspect all final figures and compare report statements with generated metrics. Confirm `cl_meso_hypothesis` is marked unavailable, no spontaneous-formation or proven-attractor claim appears, `tetra_like` is a 2D proxy, filtering/censoring limitations are stated, and README regeneration instructions work from a clean shell.
- [x] **Step 4: Report evidence and remaining limits**
  Summarize test counts, executed notebooks, data/figure paths, final model/material findings grounded in outputs, runtime/size, and anything not verified. Do not commit or push without explicit user authorization.
