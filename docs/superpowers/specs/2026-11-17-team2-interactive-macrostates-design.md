# Team 2 Interactive Macrostates Page — Design

**Date:** 2026-11-17
**Status:** design approved in conversation; written specification pending user review
**Audience:** seminar viewers and non-specialist readers
**Purpose:** guided explanation of Team 2's real analysis, from particle positions to macrostate evidence

## Intent and success criteria

Create an English, standalone webpage that lets a visitor explore how Team 2
turns real Team-1 trajectories into distance zones, contact graphs, macrostate
sequences, and heuristic attractor candidates. The page must teach the analysis
pipeline while keeping the underlying results inspectable.

A successful page lets a visitor:

1. Select any of the 18 fair-comparison N=20 runs and play or scrub all 1,000
   recorded frames.
2. Compare hard, near, and meso contact definitions on the same real frame.
3. Connect graph topology to the current rule-based macrostate label.
4. Compare raw and five-frame persistence-filtered sequences without losing the
   raw signal.
5. Inspect frequency, dwell, self-transition, return, seed-reproducibility, and
   jitter evidence pooled over the relevant three seeds.
6. Understand why four rows are heuristic attractor candidates and why that is
   not a formal attractor or attractor-memory proof.
7. See the preclustered-start, finite-window, 2D-topology, and deep-overlap
   limitations without opening collapsed technical details.

## Chosen approach and alternatives

### Chosen: self-contained compact data story

One `index.html` contains the page, inline CSS, vanilla JavaScript, SVG, and
compact JSON generated from the repository's real CSV exports. It opens directly
in a modern browser without a server, package installation, external asset, or
runtime dependency. A reproducible Python exporter refreshes the embedded data
when the source CSVs change.

### Rejected: browser-loaded full CSV explorer

Directly loading `positions.csv` and `pair_zones.csv` would expose more raw data,
but their roughly 50–63 MB sizes, local-file loading friction, and additional
CSV/UI complexity do not serve the guided seminar-story goal.

### Rejected: static figures plus synthetic schematic

This would be smaller, but it would not provide the approved real-run playback
or let visitors compare graph definitions on actual exported configurations.

## Scope and non-goals

### In scope

- All 18 N=20 comparison runs: three models × two materials × seeds 0, 1, 42.
- Every recorded frame of each run, covering the 5 ms observation window.
- Hard (`L < 2 nm`), near (`L < 10 nm`), and meso (`L < 30 nm`) graphs.
- Raw and filtered macrostate sequences for every playback run and graph type.
- Existing pooled aggregate metrics for the same 18 runs.
- All four rows whose exported `candidate` value is true.

### Out of scope

- The separate N=50 exploration run is neither embedded nor pooled into N=20
  comparisons.
- No new physical simulation, parameter sweep, formal attractor analysis, or
  Team-3 visualization.
- No full CSV table browser, file upload, server API, charting framework,
  external font, or build requirement for normal use.
- No changes to Team 2's established analysis algorithms or source CSV results.

## Files and responsibilities

- `team2_macrostates/interactive/index.html`: complete standalone deliverable,
  including generated JSON between explicit data-marker tags.
- `team2_macrostates/interactive/export_data.py`: standard-library-first data
  validation, compaction, aggregation, and HTML data-block replacement.
- `team2_macrostates/interactive/interactive.test.mjs`: Node built-in tests for
  pure browser logic, real-data agreement, page structure, and accessibility.
- `team2_macrostates/interactive/README.md`: opening the page, regenerating its
  data, and running its checks.
- `team2_macrostates/tests/test_interactive_export.py`: focused pytest coverage
  for exporter validation and compaction helpers.
- `team2_macrostates/README.md`: short discoverable link and usage summary.

The existing Python analysis modules remain authoritative. The browser adds only
the small geometry/graph/label kernel needed to visualize a frame; aggregate
analysis is not reimplemented in JavaScript.

## Data contract and provenance

### Playback data

The exporter reads Team 1's `positions.csv` and `parameters.csv`, canonicalizes
`vdw` to `vdw_only` and `dlvo` to `dlvo_classic`, and selects exactly the 18 N=20
runs identified through Team 2's `macrostate_sequences.csv`.

For each run, embed:

- run ID, canonical model, material, seed, particle count, radius, and box size;
- the common ordered time grid, stored once rather than repeated per particle;
- all particle IDs and x/y coordinates for all 1,000 frames;
- hard/near/meso raw and filtered labels and exported graph features aligned by
  frame index.

Coordinates are compact fixed-precision integers representing picometres
(0.001 nm), with the scale recorded in the JSON. This precision is
acceptable only if the browser reproduces every exported graph feature and raw
macrostate for all 18 runs × 1,000 frames × three graph types. If that gate
fails, the exporter must use finer fixed precision; it must not hide mismatches
or substitute the exported label for a failed browser computation.

### Aggregate evidence

Use existing processed outputs rather than recomputing their definitions in the
browser:

- `attractor_candidates.csv`: pooled state frequency, mean dwell, T=50 return
  probability, T=200 mean return, seed counts, label agreement, five criterion
  flags, and candidate status for each model/material/graph/state group.
- `transition_matrices.csv`: filtered, row-normalized self-transition
  probabilities for the selected model/material/graph group.
- `sequence_metrics.csv`: sums of eligible departures and observed returns over
  the selected group's three seeds, displayed alongside the pooled probability.
- `dwell_times.csv`: verification of current-dwell and censoring calculations;
  boundary runs are never presented as complete lifetimes. The browser derives
  the current contiguous dwell from the embedded exported sequence.

Missing numeric evidence remains unavailable. In particular, no eligible
departure means return probability is unavailable, not zero. Eligible departures
with no returns produce measured zero return probability while mean return time
remains unavailable.

### Export validation

The exporter fails clearly on missing files/columns, duplicate or incomplete
run/frame/particle keys, non-finite coordinates, inconsistent run metadata, an
unexpected particle count, or an incomplete 18-run selection. It excludes N=50
explicitly. Generated JSON is safely embedded without allowing a closing script
tag to terminate the data block.

## Browser architecture and data flow

Keep pure computation separate from DOM initialization within the single inline
script. Expose a browser-independent `globalThis.Team2Interactive` object for
Node tests and call page initialization only when a DOM exists.

Pure functions cover:

1. Minimum-image displacement in the 20 µm periodic box.
2. Surface gap `L = distance - 2R`, preserving negative overlap values.
3. Exact zone boundaries: hard contact `<2`; DLVO `2–<5`; near `5–<10`; meso
   `10–<30`; far `30–<100`; separated `>=100` nm.
4. Undirected graph edges for hard/near/meso definitions while retaining all
   particle IDs as nodes, including isolates.
5. Connected components, edge/component counts, largest component, sorted
   component sizes, and mean degree `2m/N`.
6. The established macrostate rules, including `tetra_like` only for a largest
   four-node component with at least four internal edges.
7. Five-frame persistence filtering for focused tests and explanation; displayed
   real filtered sequences remain the exported arrays.
8. Formatting and criterion-state helpers that distinguish pass, fail, and
   unavailable without coercing missing values to zero.

One state object contains model, material, seed, graph type, frame index,
selected state/edge, playback speed, and running status. The default is paused
DLVO/PMBC/seed 0, meso graph, frame 0. Changing run selection
preserves graph type and frame index where valid. Changing graph type updates
the current graph, macrostate, both timelines, evidence, and explanations.
Changing frame updates the spatial scene and current-run annotations. Playback
uses `requestAnimationFrame`, starts paused, stops at the final frame, and pauses
on document visibility loss.

## Page and interaction design

### 1. Orientation

The hero explains coarse-graining in one sentence and shows the four-stage
pipeline. A visible note states that preclustered starts measure persistence and
return, not spontaneous cluster formation from a dilute phase.

### 2. Explore a real frame

Native selectors choose model, material, and seed. Native buttons or radios
choose hard, near, or meso and always show the equivalent gap cutoff.

An inline SVG shows actual particle coordinates in the periodic box and edges
for the selected graph. Coordinates are not replaced with a misleading topology
layout. Overlapping particles remain overlapping; a node/component list makes
hidden coincident IDs inspectable rather than visually spreading them apart.

A keyboard- and pointer-accessible edge list identifies both particle IDs, exact
surface gap, and zone. It provides a text alternative to hover and makes an
empty graph explicit. Readouts show time, edge count, component count, largest
component, mean degree, and current macrostate. Adjacent copy explains the rule
that produced the label.

The page states that `tetra_like` is a 2D compactness proxy, not a 3D
tetrahedron. For vdW-only and retarded CL, a visible warning explains that no
core repulsion permits deep overlap and that contact labels must not be read as
realistic separated-sphere geometries.

### 3. Watch persistence and filtering

Play/Pause, Reset, speed, and a native frame slider control the same shared
frame state. Two aligned SVG timeline strips show all 1,000 raw and filtered
labels, using contiguous-run paths rather than thousands of decorative nodes.
Text labels and a legend supplement color. Changed frames are marked and counted.

The current contiguous dwell is shown in frames and milliseconds with left/right
censoring. A short explanation describes replacement of runs shorter than five
frames and preservation of sequence length and timestamps. Selecting the
vdW-only/PMBC/seed-0 hard graph exposes the real example with nine changed
frames; no synthetic filtering result is substituted.

### 4. Inspect evidence and candidates

State-frequency bars summarize filtered meso labels by default and follow the
selected model/material/graph controls. Selecting a state displays:

- pooled relative frequency and mean dwell;
- filtered self-transition probability;
- T=50 return probability plus eligible-departure and return counts;
- T=200 mean return when observed;
- state coverage across seeds and total seeds;
- raw-label agreement under reproducible 1 nm position jitter;
- five heuristic checks: frequency `>0.05`, mean dwell `>5` frames, return
  probability `>0.3`, at least three seeds with three available, and jitter
  agreement `>0.7`.

A compact candidate table lists exactly the four exported passing rows and links
their model/material/graph/state selection back to the evidence view. Nearby
visible copy states that the heuristics do not formally prove invariant sets,
basins of attraction, attractor memory, or physically realistic clusters.

## Accessibility, responsiveness, and motion

- Use semantic headings, native controls, visible focus, and minimum 44 px
  interactive targets.
- Provide accessible names and current values for selectors, graph choices,
  frame slider, playback buttons, edge list, and state bars.
- Give each SVG a title/description and provide equivalent textual readouts;
  never encode state or zone by color alone.
- Stack content at narrow widths, wrap controls, keep labels readable, and avoid
  horizontal overflow at a 320 px viewport.
- Start paused and suppress decorative transitions under reduced motion. After
  an explicit Play, reduced-motion users still receive the essential real-frame
  updates, with no autoplay or decorative animation.
- Pause on `visibilitychange`, with no large catch-up jump on return.

## Error and empty-state behavior

- Exporter validation errors identify the file/run/problem and produce no silent
  partial update.
- A missing or invalid embedded data object produces a visible page error rather
  than misleading zeroed charts.
- No graph edges, no observed state, no eligible departures, no observed return,
  and censored sequence boundaries each have distinct explanatory displays.
- The N=50 run cannot accidentally enter selectors or aggregate denominators.

## Verification strategy

### Automated

- Python exporter tests cover coordinate compaction, run selection, validation,
  safe data-block replacement, and N=50 exclusion using small fixtures.
- Node unit tests pin minimum-image examples, negative overlap, every zone
  boundary, graph thresholds, isolated nodes, components/features, every
  macrostate rule, persistence filtering, and unavailable candidate evidence.
- A real-data agreement test recomputes all graph features and raw labels for
  every embedded frame/graph and compares them to the exported arrays.
- Data tests confirm 18 runs, seeds 0/1/42, 1,000 aligned frames per run, three
  aligned sequences per frame, and exactly four true candidate rows.
- Structural tests confirm required controls, visible scientific caveats,
  accessible SVG/text alternatives, no external runtime assets, and no autoplay.
- Extracted JavaScript passes `node --check`; local documentation links resolve;
  `git diff --check` passes; the existing Team 2 pytest suite remains green.

### Browser QA

Verify all model/material/seed/graph combinations, Play/Pause/Reset, speed,
slider and keyboard input, edge inspection, state-to-evidence linking, timeline
censoring, the nine-frame filter example, and unavailable-versus-zero returns.
Check direct `file://` opening, console errors, visibility pause, reduced motion,
desktop layout, 320 px overflow, target sizes, and non-color text equivalents.
If a real browser is unavailable, report browser QA as not run rather than
claiming success.

## Delivery boundary

The implementation plan must preserve these scientific and data-integrity
requirements while keeping normal page use to one HTML file. No commit, push, or
PR mutation is authorized by this design approval.
