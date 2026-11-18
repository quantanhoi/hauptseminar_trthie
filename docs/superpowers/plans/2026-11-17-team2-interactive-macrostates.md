# Team 2 Interactive Macrostates Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an English standalone page that plays all 18 real N=20 Team-1 runs and explains Team 2's zones, contact graphs, macrostates, persistence filtering, and attractor-candidate evidence.

**Architecture:** Generate compact JSON from the existing CSVs into one self-contained HTML file. Keep geometry, graph, macrostate, sequence, and evidence-selection logic as pure JavaScript functions for Node tests; keep DOM rendering and playback in a separate initialization path. Reuse Team 2's exported aggregate metrics rather than reimplementing aggregate analysis in the browser.

**Tech Stack:** HTML5, inline CSS, vanilla JavaScript, inline SVG, JSON, Python 3.12 with existing pandas/pytest, Node.js built-in `node:test`/`assert`/`fs`/`vm`.

**Spec:** `docs/superpowers/specs/2026-11-17-team2-interactive-macrostates-design.md`

## Global Constraints

- Write learner-facing copy in English; preserve canonical identifiers `vdw_only`, `dlvo_classic`, `cl_retarded`, `fatty_acid`, and `PMBC`.
- Normal use opens `team2_macrostates/interactive/index.html` directly. No server, CDN, external font, package install, or runtime dependency.
- Embed all 1,000 frames for exactly 18 N=20 runs: three models × two materials × seeds 0, 1, 42. Never include N=50 in selectors or comparison aggregates.
- Use a 20,000 nm periodic box, 500 nm particle radius, surface gap rather than center distance, and preserve negative gaps as overlap diagnostics.
- Zone boundaries are exact: hard `<2`; DLVO `2–<5`; near `5–<10`; meso `10–<30`; far `30–<100`; separated `>=100` nm. Hard/near/meso graph cutoffs are 2/10/30 nm.
- Keep every particle as a graph node, including isolates. `tetra_like` means a largest four-node component with at least four internal edges, not 3D geometry.
- Real raw and filtered sequences come from Team 2. The five-frame filter may be reimplemented only as a tested explanatory/checking helper.
- Missing evidence is `null`/unavailable, never zero or a passing criterion. Zero returns with eligible departures is measured zero; no eligible departures is unavailable.
- Show preclustered-start, 5 ms finite-window, three-seed, 2D-label, vdW/CL no-core/overlap, and heuristic-not-proof caveats beside the relevant content, not only in collapsed details.
- Start paused; use native keyboard-operable controls, visible focus, 44 px targets, SVG text alternatives, non-color labels, reduced-motion handling, and no horizontal page overflow at 320 px.
- Do not modify established Team 2 analysis algorithms or processed source CSVs.
- Do not commit, push, or mutate a PR without explicit user authorization at execution time.

## Review Focus

- **Quantization near a zone boundary:** compact coordinates must not flip a label; Task 2's exhaustive real-data test gates all 54,000 frame/graph combinations.
- **Periodic and overlapping pairs:** opposite-box neighbors and negative gaps must remain correct; Task 2 pins minimum-image, negative-gap, and every zone boundary.
- **Missing versus measured-zero evidence:** blank CSV cells and empty departure sets must survive export and rendering as unavailable; Tasks 1 and 5 pin JSON `null`, counts, and display text.
- **Coincident particles and empty graphs:** visual overlap must not change node counts or hide all IDs, and zero-edge selections need a usable explanation; Tasks 3 and 6 pin the text alternative and browser behavior.
- **Long/backgrounded playback and narrow screens:** old timestamps must not jump the frame, and evidence tables must not create page-wide overflow; Tasks 4 and 6 pin visibility pause and browser layout.

---

### Task 1: Reproducible compact data exporter

**Files:**
- Create: `team2_macrostates/interactive/export_data.py`
- Create: `team2_macrostates/interactive/index.html` (minimal shell and empty data block only)
- Create: `team2_macrostates/tests/test_interactive_export.py`

**Interfaces:**
- Consumes: existing `team1_forces/data/processed/{positions,parameters}.csv` and Team 2's `macrostate_sequences.csv`, `graph_features.csv`, `attractor_candidates.csv`, `transition_matrices.csv`, and `sequence_metrics.csv`.
- Produces:
  - `build_interactive_data(repo_root: Path) -> dict`
  - `replace_data_block(html: str, payload: dict) -> str`
  - `main() -> None`, inferring the repository root from `__file__` and updating `interactive/index.html` in place.
  - Private helpers `_positions_to_pm(frame: pd.DataFrame) -> dict`, `_validate_run_frames(frame: pd.DataFrame, expected_frames=1000, expected_particles=20) -> None`, and `_aggregate_return_counts(metrics: pd.DataFrame) -> list[dict]` for focused tests.
- JSON contract consumed by later tasks:

```text
{
  schemaVersion: 1,
  pmPerUnit: 1,
  boxNm: 20000,
  radiusNm: 500,
  timesSeconds: number[1000],
  runs: [{
    id, model, material, seed, particleIds: number[20],
    frames: [{xPm: number[20], yPm: number[20]}] /* 1000 */,
    graphs: {
      hard|near|meso: {
        raw: string[1000], filtered: string[1000],
        features: [{largestCluster, componentCount, edgeCount, meanDegree, clusterSizes}] /* 1000 */
      }
    }
  }],
  evidence: [{
    model, material, graph, state, frequency, meanDwellFrames,
    returnProbability, meanReturnFrames, seedCount, totalSeeds, labelAgreement,
    checks: {frequency, dwell, returns, seeds, jitter}, candidate
  }],
  transitions: [{model, material, graph, source, target, count, probability}],
  returnCounts: [{model, material, graph, state, eligible50, returns50}]
}
```

- [ ] **Step 1: Write failing exporter tests**

Use pandas small fixtures and explicit expected values:

- `_positions_to_pm` converts `1e-9 m` to `1000 pm`, preserves x/y particle order, and rejects non-finite input.
- `_validate_run_frames` accepts one complete small fixture when its expected counts are overridden and rejects duplicate `(time, particle_id)`, missing particles, non-finite x/y, and inconsistent run metadata.
- `_aggregate_return_counts` ignores `raw` and N=50 rows; two filtered N=20 seeds with eligible counts 1 and 2 and return counts 0 and 1 produce `{eligible50: 3, returns50: 1}`.
- `replace_data_block` replaces only the `<script id="team2-data" type="application/json">` contents, preserves the surrounding HTML byte-for-byte, and produces parseable JSON when a string contains `</script>` by emitting `<\/script>`.
- Blank aggregate numerics become JSON `null`; serialization uses `allow_nan=False` so NaN/Infinity cannot leak into the data block.
- Missing or duplicate data blocks raise `ValueError` rather than silently writing a partial page.

- [ ] **Step 2: Run the focused tests and confirm the expected failure**

Run from `team2_macrostates/`:

```bash
../team1_forces/.venv/bin/python -m pytest tests/test_interactive_export.py -q
```

Expected: FAIL during import because `interactive/export_data.py` does not exist.

- [ ] **Step 3: Implement validation, selection, and compaction**

Create the exporter with the interfaces above. Use pandas for CSV parsing/grouping and `pathlib`/`json` for output. Select N=20 sequence metadata, require exactly 18 run IDs and three seeds per model/material, canonicalize Team-1 model aliases, sort particle IDs and frames by time, and validate one shared 1,000-point time grid.

Store x/y as integer picometres using `round(x_m * 1e12)` and set `pmPerUnit=1`. For every run/graph, align raw labels, filtered labels, and features by frame index. Map sequence fields to `largestCluster`, `componentCount`, `edgeCount`, and `meanDegree`; join `graph_features.csv` on run/time/graph and parse its semicolon-separated distribution into descending integer `clusterSizes`. Do not round labels or aggregate metrics.

- [ ] **Step 4: Implement authoritative aggregate extraction**

Map N=20 candidate rows to the `evidence` contract, preserving unavailable numerics and criterion flags as `None`. Use only `filtered` transition rows. Build `returnCounts` by summing filtered N=20 `return_eligible_T50` and `returns_T50` over each model/material/graph/state group. Require exactly four `candidate=true` evidence rows.

- [ ] **Step 5: Implement safe atomic HTML replacement and CLI**

Create a minimal valid HTML shell containing the data block and a visible `<noscript>` message. Serialize compact JSON with `allow_nan=False`, escape closing script text, replace the single marked block, and write via a temporary sibling file followed by `Path.replace()` so validation/serialization failures leave the prior page untouched.

- [ ] **Step 6: Run unit tests and generate the real data block**

Run the focused pytest command; expect PASS. Then run:

```bash
../team1_forces/.venv/bin/python interactive/export_data.py
```

Expected: `index.html` is updated with 18 runs, 1,000 frames each, three graph sequences per run, and four candidates. Print a compact summary and output size; do not impose an arbitrary file-size threshold.

### Task 2: Verified geometry, graph, and macrostate kernel

**Files:**
- Modify: `team2_macrostates/interactive/index.html`
- Create: `team2_macrostates/interactive/interactive.test.mjs`
- Consult: `team2_macrostates/src/zones.py`, `contact_graphs.py`, `macrostates.py`, and `sequences.py`

**Interfaces:**
- Consumes: Task 1 JSON and its exact field names.
- Produces: browser-independent `globalThis.Team2Interactive` with:
  - `distanceZone(gapNm: number): string`
  - `surfaceGapNm(a: {x,y}, b: {x,y}, radiusNm=500, boxNm=20000): number`
  - `frameParticles(run: object, frameIndex: number, pmPerUnit=1): Array<{id,x,y}>`
  - `buildGraph(particles: Array<{id,x,y}>, graphType: "hard"|"near"|"meso", radiusNm=500, boxNm=20000): {nodes, edges, components, clusterSizes, largestCluster, meanDegree}`
  - `macrostateFromGraph(graph: object): string`
  - `filterShortStates(sequence: string[], minDwell=5): string[]`
- Each graph edge is `{i, j, gapNm, zone}`; `components` contains sorted ID arrays, `clusterSizes` is descending, `largestCluster` is the first size or zero, and `meanDegree = 2 * edges.length / nodes.length`.

- [ ] **Step 1: Add failing independent kernel tests**

Load the single executable inline script with `vm`, without a DOM, and read JSON from `team2-data`. Pin:

- Opposite-boundary points `x=19999` and `x=1` have center distance 2 nm; with radius 500 nm their surface gap is `-998 nm`. A non-periodic 3000/4000 nm pair has center distance 5000 nm and gap 4000 nm.
- Zones at `-1`, `1.999`, `2`, `4.999`, `5`, `9.999`, `10`, `29.999`, `30`, `99.999`, and `100` nm follow the Global Constraints exactly.
- Two disconnected pairs plus one isolate produce two edges, component sizes `[2,2,1]`, largest 2, and mean degree 0.8; the isolated ID remains present.
- Synthetic graph fixtures produce every label: no-edge `monomer_gas`, largest 2 `dimer_dominated`, largest 3 `trimer_like`, four nodes/four internal edges `tetra_like`, four nodes/three edges `loose_four_cluster`, and largest 5 `large_cluster`.
- `filterShortStates` replaces a short internal run with the previous valid state, a short leading run with the first following valid state, and an all-short sequence with `mixed_transition`, without changing length.

- [ ] **Step 2: Add the exhaustive real-data agreement test**

For every run, frame, and graph type, call `frameParticles(run, frameIndex, data.pmPerUnit)` and `buildGraph`. Assert exact equality for raw macrostate, largest component, component count, edge count, and descending `clusterSizes`; assert mean degree within `1e-12`. Assert `filterShortStates(raw, 5)` equals the exported filtered array for every run/graph.

Also assert 18 unique runs, each model/material pair has seeds `[0,1,42]`, every run has 1,000 frames and 20 particles per frame, every graph has 1,000 aligned labels/features, and N=50 is absent.

- [ ] **Step 3: Run tests and confirm failure**

Run from `team2_macrostates/`:

```bash
node --test interactive/interactive.test.mjs
```

Expected: FAIL because `Team2Interactive` or its functions are absent; generated data validation may already pass.

- [ ] **Step 4: Implement the pure kernel**

Add one executable inline script and call `initPage()` only when `typeof document !== "undefined"`. Compute component-wise minimum-image displacement, all unordered pairs once, selected-graph edges, connected components with BFS/DFS, features, and the exact established label rules. Do not clamp negative gaps or drop isolates. Keep the deterministic ordering defined in Interfaces.

- [ ] **Step 5: Run all kernel and real-data tests**

Run `node --test interactive/interactive.test.mjs`; expect PASS. If only quantization causes a real-data mismatch, change the exporter to 0.1 pm integers (`x_m * 1e13`), set `pmPerUnit=0.1`, regenerate, and rerun; never weaken the agreement assertions or substitute exported labels for computation.

Extract the executable script to `/tmp/opencode/team2-interactive.js` and run `node --check`; expect exit code 0.

### Task 3: Learner-first static page and accessible visuals

**Files:**
- Modify: `team2_macrostates/interactive/index.html`
- Test: `team2_macrostates/interactive/interactive.test.mjs`

**Interfaces:**
- Consumes: Task 1 data and Task 2 kernel.
- Produces semantic DOM IDs used by initialization: `data-error`, `model`, `material`, `seed`, `graph-type`, `play`, `reset`, `speed`, `frame-slider`, `scene`, `edge-select`, `time-readout`, `gap-readout`, `edges-readout`, `components-readout`, `largest-readout`, `degree-readout`, `macrostate-readout`, `macrostate-explanation`, `overlap-warning`, `raw-timeline`, `filtered-timeline`, `changed-count`, `dwell-readout`, `state-bars`, `state-evidence`, and `candidate-table`.

- [ ] **Step 1: Add failing structural and scientific-guardrail tests**

Assert exactly one executable inline script and one JSON data script; no external scripts, stylesheets, images, fonts, or links required for operation. Require every Interface ID, native `select`/`button`/`input type="range"` controls, SVG `<title>`/`<desc>`, a `<noscript>` message, and a visible error element.

Check visible copy for the preclustered/no-spontaneous-formation caveat, five-frame filter, 1 nm jitter, 5 ms window, three seeds, `tetra_like` 2D proxy, vdW/CL no-core overlap warning, and heuristic-not-formal-proof statement. Check that initial controls specify DLVO, PMBC, seed 0, meso, frame 0, and Play rather than autoplay.

- [ ] **Step 2: Run structure tests and confirm failure**

Run `node --test interactive/interactive.test.mjs`. Expected: kernel/data tests PASS; new structure tests FAIL on missing page elements.

- [ ] **Step 3: Build the four instructional sections**

Use this reading order:

1. Hero, one-sentence coarse-graining explanation, four-stage pipeline, and preclustered caveat.
2. “Explore a real frame”: run selectors, graph cutoff choices, spatial SVG, zone legend, edge inspector, metrics, macrostate explanation, and conditional overlap warning.
3. “Watch persistence and filtering”: playback controls, frame slider, aligned raw/filtered timelines, changed-frame count, dwell/censoring readout, and filter explanation.
4. “Inspect the evidence”: frequency bars, selected-state metrics/checklist, four-candidate table, and visible interpretation limits.

Add a compact `<details>` only for formulas/source-file provenance, never for the required caveats.

- [ ] **Step 4: Add responsive, accessible styling and SVG scaffolding**

Use system fonts, high-contrast colors, visible `:focus-visible`, minimum 44 px targets, stacked mobile cards, wrapping controls, and a labelled locally scrollable candidate-table region when needed. Give timelines and the spatial scene text alternatives and legends with written state/zone names. Use contiguous-run SVG paths for timelines rather than 2,000 permanent rectangles.

- [ ] **Step 5: Run all automated checks**

Run Node tests and the extracted-script syntax check. Expected: all kernel/data/structure tests PASS and syntax is valid.

### Task 4: Real-run explorer, playback, and persistence timelines

**Files:**
- Modify: `team2_macrostates/interactive/index.html`
- Test: `team2_macrostates/interactive/interactive.test.mjs`
- Consult: `team2_macrostates/data/processed/dwell_times.csv`

**Interfaces:**
- Consumes: all prior JSON, kernel functions, and DOM IDs.
- Produces:
  - `dwellAtFrame(sequence: string[], frameIndex: number, timesSeconds: number[]): {state,startIndex,endIndex,frames,seconds,leftCensored,rightCensored}`
  - `initPage(): void`
  - Internal state `{model, material, seed, graphType, frameIndex, selectedEdge, selectedState, speed, running}`.

- [ ] **Step 1: Add failing dwell and interaction checks**

For a sequence `["a","a","b","b","b"]` at index 2 with five equally spaced 5 µs timestamps, assert state `b`, start 2, end 4, three frames, 15 µs, `leftCensored=false`, and `rightCensored=true`; index 0 is left-censored. Empty or out-of-range input raises a clear error.

Read every filtered N=20 row in `dwell_times.csv`; at its `start_index`, compare `dwellAtFrame` on the corresponding embedded filtered sequence against the exported state, start/end indices, frame count, and both censoring flags, with seconds within `1e-15`.

Add static checks for `requestAnimationFrame`, no `setInterval`, a 100 ms elapsed-time clamp, a bounded per-display-frame advance, `visibilitychange`, and keyboard/native input handlers. Assert the real vdW-only/PMBC/seed-0 hard selection has exactly nine raw/filtered changes and every N=20 meso selection has zero changes.

- [ ] **Step 2: Run tests and confirm failure**

Run `node --test interactive/interactive.test.mjs`. Expected: previous tests PASS; dwell/interaction checks FAIL.

- [ ] **Step 3: Initialize and render the paused default state**

Parse the JSON with a guarded error path that reveals `data-error`. Initialize DLVO/PMBC/seed 0, meso, frame 0, speed 1, and paused. Populate selectors only from embedded runs. Render particles at actual x/y coordinates with radius 500 nm in a 20,000 nm SVG viewBox, selected edges, current metrics, macrostate rule copy, timelines, and dwell from the shared state.

- [ ] **Step 4: Wire run, graph, edge, and frame controls**

Changing model/material/seed or graph pauses, preserves a valid frame index, resets incompatible selected edge/state, and rerenders all dependent content. Populate `edge-select` with particle IDs, exact gap, and zone; disable it with an explicit no-edge option when empty. The native frame slider uses min 0, max 999, step 1, and an `aria-valuetext` containing frame, milliseconds, raw label, and filtered label.

Do not separate coincident nodes. Render a component/node roster so all 20 IDs and component membership remain inspectable even when markers coincide.

- [ ] **Step 5: Implement bounded playback and reset**

At speed 1, advance 60 recorded frames per display second; offer 0.5×, 1×, 2×, and 4×. Clamp real elapsed time to 100 ms, carry fractional recorded frames in an accumulator, and cap each display update at 24 recorded frames. Stop paused at frame 999. Reset restores all defaults and pauses. Visibility loss pauses and clears the previous timestamp; reduced motion suppresses cosmetic transitions but does not disable explicit real-frame Play.

- [ ] **Step 6: Render raw/filtered timelines and current dwell**

Draw both sequences from the selected graph, mark every changed frame, update the changed count, and place one current-frame marker across both views. Show the real nine-change hard-graph example and honest zero-change meso text. Use `dwellAtFrame` for current dwell and state its boundary censoring explicitly.

- [ ] **Step 7: Run automated checks**

Run Node tests and `node --check`. Expected: all tests PASS, including exhaustive data agreement and nine-change/zero-change pins.

### Task 5: Linked aggregate evidence and candidate inspection

**Files:**
- Modify: `team2_macrostates/interactive/index.html`
- Test: `team2_macrostates/interactive/interactive.test.mjs`

**Interfaces:**
- Consumes: Task 1 `evidence`, `transitions`, and `returnCounts`; shared selection state from Task 4.
- Produces pure helpers on `Team2Interactive`:
  - `evidenceFor(data: object, selection: {model,material,graph,state}): object|null`
  - `metricText(value: number|null, digits=3): string`
  - `candidateRows(data: object): object[]`

- [ ] **Step 1: Add failing evidence tests**

Assert selection returns only the exact model/material/graph/state row and null for an absent combination. `metricText(null)` is `Unavailable`; `metricText(0)` is `0.000`, proving the two cases differ. `candidateRows` returns exactly the four known rows: CL/fatty-acid/meso/large-cluster, vdW/fatty-acid/meso/tetra-like, vdW/fatty-acid/meso/large-cluster, and vdW/fatty-acid/near/dimer-dominated.

For every evidence row, verify pooled return probability against `returnCounts`: positive eligible counts require `returns50/eligible50` within `1e-12`; zero eligible counts require null probability. Verify the four exported candidate rows all have five true checks and no unavailable check counts as a pass.

- [ ] **Step 2: Run evidence tests and confirm failure**

Run `node --test interactive/interactive.test.mjs`. Expected: prior tests PASS and new helper/evidence tests FAIL.

- [ ] **Step 3: Implement frequency bars and selected-state details**

Render filtered-state frequencies for the selected model/material/graph as labelled native buttons with text percentages and `aria-pressed`. Selecting one updates `selectedState` and displays frequency, mean dwell, filtered source-equals-target self-transition, T=50 return probability, eligible/return counts, T=200 mean return, seed coverage, and 1 nm raw-label jitter agreement. Show explicit empty/unavailable states.

- [ ] **Step 4: Implement the five-check explanation and candidate table**

Render each criterion with its exact threshold, actual value, and Pass/Fail/Unavailable text. Render all four candidate rows with an Inspect button that updates run/graph/state selections and scrolls the evidence heading into view without starting playback. Keep finite-window, three-seed, overlap, and heuristic-not-proof copy visible beside this section.

- [ ] **Step 5: Run all automated checks**

Run Node tests and syntax check. Expected: all geometry, data, structure, playback, and evidence tests PASS.

### Task 6: Documentation, browser QA, and regression verification

**Files:**
- Create: `team2_macrostates/interactive/README.md`
- Modify: `team2_macrostates/README.md`
- Verify: all files created above

**Interfaces:**
- Consumes: completed standalone page and exporter.
- Produces: discoverable usage/regeneration instructions and final verification evidence; no new application API.

- [ ] **Step 1: Document normal use and regeneration**

In `interactive/README.md`, document direct browser opening, the 18-run/all-frame scope, controls, four candidates, scientific limitations, exporter command, Node test command, and focused pytest command. State that Python is needed only to regenerate data. Add a short Team 2 README section linking to `interactive/index.html` without changing existing analysis documentation.

- [ ] **Step 2: Run exporter, interactive, and full Team 2 suites**

From `team2_macrostates/` run:

```bash
../team1_forces/.venv/bin/python interactive/export_data.py
../team1_forces/.venv/bin/python -m pytest tests/test_interactive_export.py -q
node --test interactive/interactive.test.mjs
../team1_forces/.venv/bin/python -m pytest -q
```

Expected: exporter completes without changing a stable regenerated data block, all focused and existing tests PASS, and no source CSV changes. If the documented venv is unavailable, use the repository's established isolated environment; never install globally.

- [ ] **Step 3: Check syntax, links, assets, and diffs**

Run the extracted-script `node --check`, a Python standard-library local-link check for both READMEs, and `git diff --check`. Confirm the HTML has no external runtime asset URLs and all changes are limited to the planned page, exporter, tests, docs, and plan/spec files.

- [ ] **Step 4: Perform real-browser QA**

Open `index.html` directly in an available modern browser. Check every model/material/seed selector, all three graph definitions, Play/Pause/Reset, all speeds, slider/keyboard input, edge inspection, component roster, evidence linking, and all four Inspect actions. Confirm:

- Default state is paused and matches DLVO/PMBC/seed 0/meso/frame 0.
- Current graph features/labels match the displayed exported values.
- vdW/PMBC/seed 0/hard shows nine changes; meso shows zero.
- No eligible return is Unavailable, while eligible departures with no returns show zero.
- Coincident vdW/CL particles are not visually spread apart and all IDs remain available.
- Backgrounding pauses without a return jump; reduced motion has no decorative animation.
- At desktop and 320 px there is no page-wide horizontal overflow, clipped control, unreadable timeline, or color-only meaning; targets are at least 44 px.
- Browser console contains no errors.

If no real browser is available, record QA as not run rather than claiming it passed.

- [ ] **Step 5: Review final scientific copy and report evidence**

Read visible and collapsed copy against the spec and root README. Confirm the page does not claim spontaneous formation, formal attractors, exact 3D tetrahedra, or physically realistic vdW/CL contact clusters. Report exact test counts, generated HTML size, browser-QA evidence/limitations, and any deferred issue. Do not commit or push without new explicit authorization.
