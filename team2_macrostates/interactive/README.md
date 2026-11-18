# Team 2 interactive macrostates page

[index.html](index.html) is a self-contained, English-language page that plays Team 2's
real analysis: Team-1 particle positions → distance zones → hard/near/meso
contact graphs → rule-based macrostate labels → the pooled evidence and the
four heuristic attractor candidates. It is one file with inline CSS, vanilla
JavaScript, SVG and a compact JSON block whose 18 N=20 runs cover all 1,000
recorded frames.

## Open it

Open `index.html` directly in a modern browser (double-click, or
`file:///.../team2_macrostates/interactive/index.html`). No server, install,
network access, external font, image or charting library is used. Python is
needed only to regenerate the embedded data.

The page starts paused on DLVO (classic) / PMBC membrane / seed 0 / meso /
frame 0. The separate N=50 exploration run is deliberately excluded from
playback and from every aggregate.

## Fixed experiment conditions

A visible panel beside the run controls lists the conditions shared by all 18
runs: 20 particles in a 20 µm periodic box with radius 500 nm, a preclustered
start near 20 nm, 1,000 frames over 5 ms, 298.15 K, diffusion coefficient
10⁻¹⁶ m²/s, 100 mM salt (Debye length 0.96 nm), material-specific Hamaker
constants, Δt = 10⁻⁷ s with every 50th step recorded, and a ±20 pN force cap.
Salt screening applies only to `dlvo_classic`; `vdw_only` and `cl_retarded`
have no electrostatic or core term.

## What you can do

- Choose any of the 18 comparison runs: model (`dlvo_classic`, `vdw_only`,
  `cl_retarded`) × material (`PMBC`, `fatty_acid`) × seed (0, 1, 42).
- Switch between the hard (`L < 2 nm`), near (`L < 10 nm`) and meso
  (`L < 30 nm`) graph definitions and read the exact surface gap, zone, and
  the rule that produced the current label.
- Compare the full periodic box with a local zoom that preserves the exact same
  coordinates. Marker fill matches the component swatch in the roster; edge
  colour follows the distance-zone legend. Inspect an edge to highlight it and
  its two particles in both views, while every particle ID remains available.
  Component colours repeat after eight groups, so the IDs and roster remain the
  authoritative key.
- Read the raw and filtered macrostates separately, with the rule that produced
  the raw label and an explicit note when the filter changes it.
- Play, pause, reset, change speed (0.5×, 1×, 2×, 4×), or drag the frame
  slider. Keyboard users can focus the slider and use its native arrow keys,
  or focus Play and press Space; no custom section-level shortcuts intercept
  native control behaviour.
- Compare the labelled raw and five-frame filtered timelines, the changed-frame
  count and the current dwell time with its left/right censoring. Two guided
  buttons load the nine-change hard example and a zero-change meso example.
- Select a pooled state (the current filtered state is selected initially) to
  see frequency, mean dwell, self-transition, T=50 return probability with
  eligible/return counts, T=200 mean return, seed coverage, 1 nm jitter
  agreement, and the five heuristic checks, each explained in plain language.
- Use `Inspect evidence` on any of the four candidate cards to load that
  model/material/graph and state without starting playback.

## The four candidates

`cl_retarded`/fatty acid/meso/`large_cluster`,
`vdw_only`/fatty acid/meso/`large_cluster`,
`vdw_only`/fatty acid/meso/`tetra_like`, and
`vdw_only`/fatty acid/near/`dimer_dominated`.
All four pass the five exported heuristics over three seeds.

## Scientific limits (also visible on the page)

- Starts are preclustered, so the results measure persistence and return, not
  spontaneous cluster formation from a dilute phase.
- Every comparison is a 5 ms window with three seeds; dwell and return values
  are censored at the window boundaries.
- `tetra_like` is a 2D compactness proxy, not a 3D tetrahedron.
- `vdw_only` and `cl_retarded` have no core repulsion, so particles may overlap
  deeply; contact labels there are not realistic separated-sphere geometries.
- The five heuristics do not prove invariant sets, basins of attraction,
  attractor memory, or physical realism. Missing evidence is shown as
  unavailable, never as zero.

## Regenerate the embedded data

The exporter validates the real CSVs, selects the 18 N=20 runs, packs integer
coordinates (0.1 pm units, `pmPerUnit = 0.1`), and replaces only the marked
JSON block:

```bash
cd team2_macrostates
../team1_forces/.venv/bin/python interactive/export_data.py
```

Alternatively, from the repository root:
`python team2_macrostates/interactive/export_data.py`.

If the Team 1 virtual environment is absent, any Python 3.12 environment with
`numpy` and `pandas` works (for example `uv venv` plus
`uv pip install numpy pandas`); Python is only needed for regeneration and the
exporter tests. The Node checks need only Node 18 or newer.
The command is idempotent: re-running it on unchanged inputs produces the same
file. It refuses to run on missing files/columns, duplicate or incomplete
frames or export keys, non-finite coordinates, inconsistent run metadata,
duplicate or missing model/material/seed combinations, an unexpected particle
count, an incomplete 18-run selection, or Team-1 parameter rows that disagree
with the sequences.

Coordinates are stored as 0.1 pm integers. That precision is accepted only
because the Node agreement test recomputes every graph feature and raw label
for all 18 runs × 1,000 frames × three graphs from the stored integers; if a
future dataset placed a surface gap close enough to a cutoff for 0.1 pm to
flip it, that test fails first and the exporter should move to finer units.

## Checks

```bash
cd team2_macrostates
node --test interactive/interactive.test.mjs
../team1_forces/.venv/bin/python -m pytest tests/test_interactive_export.py -q
```

The Node suite pins the geometry/zone/graph/macrostate kernel, compares all
54,000 run/frame/graph combinations against the exported features and raw
labels, checks every exported filtered dwell row, and asserts the page
structure, accessibility scaffolding, caveat copy and playback bounds. The
pytest suite covers exporter validation, compaction and safe data-block
replacement. The existing Team 2 suite (`pytest -q`) remains the authority for
the analysis itself.
