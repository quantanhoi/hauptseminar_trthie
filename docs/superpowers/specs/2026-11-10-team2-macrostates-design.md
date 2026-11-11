# Team 2 – Makrozustände und Attractor Memory: Project Design

**Date:** 2026-11-10  
**Status:** approved by user, 2026-11-10  
**Authoritative assignment source:** `hauptseminar_pdf/2026-11-04_Aufgabenblatt_Team-2_V2.pdf` (extract with `pdftotext -layout`; §-references below point to it)

## Intent and why

Build the complete Team-2 seminar deliverable: a reproducible coarse-graining pipeline that turns Team-1 position trajectories into physically grounded distance zones, contact graphs, discrete macrostate sequences, persistence/return analyses, robustness checks, figures, a German methodological report, and a clean Team-3 CSV handoff (§5, §12–14, §18).

This is graded seminar work. The central scientific requirement is that a macrostate must be reproducible, persistent, jitter-robust, and dynamically relevant—not merely a convenient snapshot label (§3, §8). All user-facing prose and figure labels are German; code identifiers remain English.

## User decisions and scope

1. **Start with the existing Team-1 data**, build and test the complete Team-2 pipeline, and produce an initial honest analysis.
2. **Then extend Team 1** with `vdw` runs and additional seeds, rerun the final Team-2 analysis, and compare the three physically defined models across both materials.
3. **Do not implement `cl_meso_hypothesis`.** Neither assignment sheet supplies its equation. It remains explicitly unavailable; it is optional in §13. No arbitrary mesoscale attraction will be invented.
4. Leave the user's modified `team1_forces/notebooks/01_force_curves.ipynb` untouched.

## Current data and final comparison ensemble

Current `team1_forces/data/processed/` contains five preclustered runs: four N=20 runs ({`dlvo`, `cl_retarded`} × A_H = 0.5e-21/5e-21 J, seed 42) and one N=50 `cl_retarded` PMBC run, each with 1,000 recorded frames. Positions are metres, times seconds, radii 500 nm, salt 100 mM, initial surface gap 20 nm, and the periodic box is 20 µm.

For the final fair comparison, extend notebook 03 to export:

- N=20, models {`vdw`, `dlvo`, `cl_retarded`};
- materials {fatty_acid: A_H = 0.5e-21 J, PMBC: A_H = 5e-21 J};
- common seeds {0, 1, 42};
- 18 N=20 runs total, all with the existing 50,000 steps, record every 50 steps, 20 nm preclustered start, 100 mM salt, dt = 1e-7 s, force cap 20 pN;
- retain the N=50 `cl_retarded` PMBC seed-42 run as a separate size exploration, never pooled into the N=20 comparison.

The existing four N=20 runs are deterministically regenerated as part of this matrix; `vdw` and seeds 0/1 are added. Team-1 model names remain unchanged internally. Team 2 canonicalizes `vdw` → `vdw_only` and `dlvo` → `dlvo_classic` for the required Team-3 schema. Material labels are derived only for these two documented A_H values; unknown values remain `unknown`, never guessed.

## Goals

1. Validate Team-1 schemas and units; calculate surface distances with the minimum-image convention.
2. Preserve all six distance zones and construct `hard`, `near`, and `meso` graphs independently at every frame (§6–7).
3. Compute graph features and the small rule-based macrostate catalogue (§5, §8).
4. Store raw and persistence-filtered sequences; calculate dwell times, transition/self-transition probabilities, return probability, and mean return time (§7–9).
5. Measure deterministic jitter label agreement, graph-definition sensitivity, and seed reproducibility (§9–10).
6. Produce all seven mandatory figures, model/material comparisons, a German report with methodological reflection, and the Team-3 CSV export (§12–14).
7. Test the numerical/classification logic on small synthetic cases and run an end-to-end smoke test on real data.

## Non-goals

- No `cl_meso_hypothesis`, new force law, full Lifshitz/Matsubara calculation, or changes to Team-1 physics.
- No additional Team-1 parameter sweeps beyond the model/material/seed ensemble above.
- No 3D tetrahedron claim, ε-machine reconstruction, Team-3 analysis, or presentation slides.
- No claim that preclustered simulations demonstrate spontaneous cluster formation or that heuristics prove attractor memory.

## Anti-goals

- Using centre distance instead of surface gap L = ||x_j − x_i|| − 2R.
- Dropping isolated nodes, discarding raw labels, silently changing zone thresholds, or pooling different N values.
- Fabricating material/model labels or treating a single seed as reproducibility.
- Biased return statistics from truncated end-of-sequence windows.
- Sending flickering raw labels instead of the filtered sequence to Team 3.

## Approaches considered

- **A. Team-2 pipeline only on the five existing runs.** Smallest change, but lacks vdW and multi-seed reproducibility. This is the first implementation/checkpoint, not the final scope.
- **B. Combined pipeline plus targeted Team-1 export extension (chosen).** Reuses the existing tested `BrownianClusterSim`, `ProtocellForces`, and `export_run`; adds no new physical model. It supplies a fair three-seed comparison while keeping Team-1 changes small.
- **C. Synthetic demonstration only.** Useful for unit tests but cannot answer the model/material questions with real simulation data; rejected as a deliverable.
- **D. Invent a mesoscale hypothesis term.** Rejected by the user because its arbitrary amplitude/shape could manufacture the clustering under investigation.

## Implementation design

### Team-1 extension (after the initial Team-2 checkpoint)

Only `team1_forces/notebooks/03_cluster_simulation.ipynb` needs functional changes:

- give `run_cluster` an explicit `seed` argument instead of reading global `SEED`;
- pass that seed consistently to `BrownianClusterSim`, `lattice_positions`, `make_run_id`, and `export_run`;
- replace `EXPORT_CONFIGS` with the 18-run N=20 matrix plus the existing N=50 exploration;
- keep the existing CSV schemas, numerical parameters, physics functions, and idempotent export regeneration unchanged.

Update Team-1 README/report run counts and seed policy. Do not touch notebook 01. Existing Team-1 tests must remain green; add a small test only if a source helper changes.

### Team-2 project layout

Mirror the established Team-1 notebook-first convention, without adding packaging or a new dependency stack:

```
team2_macrostates/
├── README.md
├── requirements.txt          # same existing numpy/pandas/networkx/matplotlib/jupyter/pytest stack
├── conftest.py
├── src/
│   ├── zones.py              # surface distance, exact zone boundaries, allowed zones
│   ├── contact_graphs.py     # frame graph construction and graph features
│   ├── macrostates.py        # static rule-based labels
│   ├── sequences.py          # persistence filter, dwell/return/transition metrics
│   ├── robustness.py         # deterministic position jitter and label agreement
│   ├── pipeline.py           # validation, Team-1 loading, per-run analysis, exports
│   └── plots.py              # shared German plotting style/helpers only where reused
├── notebooks/
│   ├── 01_zones_graphs.ipynb
│   ├── 02_sequences_attractors.ipynb
│   └── 03_robustness_comparison.ipynb
├── tests/
├── data/processed/
├── figures/
└── report/report.md
```

Use the existing Team-1 virtual environment for execution; `requirements.txt` documents reproducible setup without installing duplicate dependencies during development.

### Input validation and units

`pipeline.py` loads `positions.csv` and `parameters.csv` from Team 1. Validate required columns, finite coordinates/times, unique `(run_id, t, particle_id)` rows, nonempty frames, consistent particle sets, one seed/model/A_H per run, and one positive R_nm per run. Sort frames by time and particles by the actual particle ID; graph nodes retain those IDs rather than assuming contiguous indices.

Document the input contract: x/y in m, t in s, R_nm in nm, A_H in J, and Team-1's fixed 20 µm periodic box. Use `box=20e-6` explicitly for these exports because the box is not a CSV column; do not infer it from observed coordinates. Surface gaps are not clipped: negative values remain visible as overlap diagnostics and classify as `hard_contact` under the assignment's literal L < 2 nm rule.

### Zones, graphs, and features

Use the assignment thresholds exactly in nm: `hard_contact` L < 2; `dlvo_zone` [2,5); `near_gap` [5,10); `meso_gap` [10,30); `far_gap` [30,100); `separated` L ≥ 100 (§6).

- `hard`: {hard_contact}
- `near`: {hard_contact, dlvo_zone, near_gap}
- `meso`: {hard_contact, dlvo_zone, near_gap, meso_gap}

Compute all pairs from positions with minimum-image distances. Save non-separated pair rows as `pair_zones.csv` with run/seed/time/i/j/L_nm/zone; graph variants are derivable from this single table. Save `graph_features.csv` with `graph_type`, largest cluster, edge/component counts, mean degree, and a stable cluster-size-distribution representation (e.g. semicolon-separated descending sizes).

### Macrostate catalogue

Use seven static labels: `monomer_gas` (no edges), `dimer_dominated` (largest component 2), `trimer_like` (3), `tetra_like` (4 and at least four edges in that component), `loose_four_cluster` (4 but fewer than four edges), `large_cluster` (≥5), and `mixed_transition` only as the fallback for otherwise unclassifiable input.

`tetra_like` is explicitly a 2D compactness proxy, not a geometric tetrahedron. `failure_disperse` is not added as a history-dependent label; dispersion can later be derived from transitions if Team 8 needs it. This keeps the catalogue at the requested small size and follows the appendix rules.

### Persistence and sequence metrics

Default `min_dwell_steps=5`; preserve `macrostate_raw` and `macrostate_filtered` for every graph variant. Filter complete runs by run length: replace a short internal run with the previous valid state, a leading short run with the next valid state, and use `mixed_transition` only if no run reaches the minimum. Keep sequence length and timestamps unchanged. Document that this heuristic can extend neighbouring states; report raw-sequence metrics as sensitivity where filtering materially affects interpretation.

- Dwell table: one row per contiguous run with state, start/end time, duration in steps and seconds; acknowledge first/last-run censoring in the report.
- Transition matrix: pool transition counts within the requested run group, then row-normalize; retain NaN for a state with no outgoing transitions. Self-transition is its diagonal.
- Return probability: denominator is departures from the target with a complete T=50-step future window; numerator returns within that window. Truncated final departures are excluded rather than counted as failures.
- Mean return time: first return after departure, T=200 steps, using the same complete-window eligibility; NaN when no eligible return exists. Include seconds using actual timestamps.
- Seed reproducibility: distinct seeds in which a state occurs, with the §9 heuristic flag requiring at least three. Initial seed-42-only results say `not assessable`.

`attractor_candidates.csv` reports each §9 heuristic separately (frequency >5%, mean dwell >5 steps, return probability >0.3, ≥3 seeds, label agreement >0.7) and an overall `candidate` flag only when all are available and satisfied. Never label this as proof of an attractor.

### Robustness and comparisons

Apply independent Gaussian position jitter with sigma = 1 nm and deterministic recorded seeds, then repeat zoning/graphs/raw labels. Report raw-label agreement per run and graph type; filtering is not allowed to hide jitter sensitivity. Compare hard/near/meso results as contact-definition sensitivity.

For final model/material comparisons use only the 18 N=20 runs and common seeds {0,1,42}. Aggregate by canonical model and material without averaging away run counts. Keep the N=50 run separate. The initial five-run checkpoint is overwritten only by final generated Team-2 outputs after the extended Team-1 export is validated.

### Outputs and figures

- `data/processed/pair_zones.csv`
- `data/processed/graph_features.csv`
- `data/processed/macrostate_sequences.csv` (all three graph types, raw + filtered + required metadata)
- `data/processed/dwell_times.csv`
- `data/processed/sequence_metrics.csv` (frequency, dwell, return, self-transition, seed counts, agreement)
- `data/processed/transition_matrices.csv` (long format)
- `data/processed/attractor_candidates.csv`
- `data/processed/team3_macrostates.csv`: meso graph only, exact §14 fields `run_id, seed, time, macrostate_raw, macrostate_filtered, model_type, material_type, A_H, salt_mM, noise, largest_cluster, mean_degree`.

Generate German-labelled PNGs at 200 dpi:

1. Raw vs filtered state time series for a documented representative N=20 run, meso graph.
2. Cluster-size distributions by model and material.
3. Dwell-time distributions by state (with raw/filtered distinction).
4. Transition-matrix heatmaps for the three models, common state ordering.
5. Return probability by state/model at T=50.
6. Jitter label agreement by model/material and graph type.
7. Fatty-acid vs PMBC macrostate/dynamics comparison, faceted by model.

### Tests and verification

Small pytest cases cover exact zone boundaries, surface vs centre distance and periodic wrapping, isolated graph nodes/features, every macrostate branch, persistence leading/internal/trailing/all-short cases, known dwell runs, row-normalized transitions, eligible-window return calculations, deterministic jitter/agreement, and the exact Team-3 schema. An end-to-end miniature DataFrame test checks metadata propagation and one row per frame/graph.

Verification commands:

- Team-1 existing pytest suite after notebook/export changes;
- Team-2 pytest suite;
- execute Team-1 notebook 03 to regenerate/validate the extended CSVs;
- execute all three Team-2 notebooks top-to-bottom with outputs embedded;
- programmatic checks for expected run/model/material/seed counts, finite labels, raw/filtered length equality, transition rows, seven nonempty figures, and Team-3 schema;
- inspect generated figures and report numerical summaries rather than claiming success from file existence alone.

### README and German report

README documents setup, input location, notebook order, units, seeds, graph/macrostate definitions, outputs, and regeneration. The report contains Einleitung, Daten/Einheiten, Zonen/Graphen, Makrozustände/Persistenz, Attractor-Memory-Metriken, Robustheit/Sensitivität, Modell-/Materialvergleich, Team-3-Export, Grenzen, and a results-backed reflection on robust states versus artefacts.

Mandatory limitations: preclustered starts measure persistence rather than spontaneous formation; 2D `tetra_like` is a proxy; three seeds are minimal statistics; persistence filtering is heuristic; finite observation windows censor dwell/return estimates; only 100 mM and the fixed Team-1 initial condition are compared; `cl_meso_hypothesis` is unavailable because no defining equation was provided.

## What remains to the builder

Representative run selection based on a stated deterministic rule, precise figure layout/colours, dataframe chunking if memory requires it, and concise German wording grounded in the generated numerical results. No scientific thresholds, model scope, or export semantics are left open.
