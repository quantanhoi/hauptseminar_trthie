# Comprehensive Root README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create an English, physics-first root `README.md` that teaches the complete project through ELI5 intuition, detailed theory, and explanations of all 21 generated figures.

**Architecture:** One root Markdown document is the unified entry point; existing team READMEs and German reports remain authoritative detailed companions. The narrative progresses from physics to simulation, coarse-graining, figure-guided results, data contracts, and reproduction.

**Tech Stack:** Markdown, LaTeX-style equations, existing PNG figures, Python 3 standard-library checks for links and document structure.

**Spec:** `docs/superpowers/specs/2026-11-11-comprehensive-readme-design.md`

## Global Constraints

- Write the root README and figure explanations in English; retain established English code identifiers.
- Physics comes first, with an ELI5 explanation followed by technical detail.
- Embed and explain all 14 Team-1 and 7 Team-2 PNG figures; inspect each visually.
- Ground claims in source code, reports, CSVs, notebooks, and figures; do not invent results.
- Preserve exact zone thresholds, canonical model names, seeds, units, and metric horizons.
- Do not modify physics, data, notebooks, dependencies, generated figures, or team READMEs unless a factual correction is strictly necessary.
- Do not commit or push without explicit user authorization.

## Review Focus

- A reader could think vdW and CL are additive; Task 1 must explicitly explain why `cl_retarded` replaces the non-retarded vdW term.
- A reader could confuse centre distance with surface gap or periodic displacement; Task 2 must define and check both equations and conventions.
- Cluster plots could be misread as spontaneous formation; Task 2 must place the preclustered-start caveat with the relevant figures.
- vdW/CL cluster results could hide deep-overlap artefacts; Task 2 must place the quantitative caveat beside those results.
- Stable states could be mislabeled proven attractors or missing return values read as zero; Tasks 2 and 3 must distinguish heuristic candidates, unavailable evidence, and measured probabilities.

---

### Task 1: Physics-first narrative and project workflow

**Files:**
- Create: `README.md`
- Consult: `team1_forces/src/{constants,potentials,pair_dynamics,brownian_cluster}.py`, `team1_forces/README.md`, `team1_forces/report/report.md`, `docs/superpowers/specs/2026-11-04-team1-protocell-forces-design.md`
- Consult: `team2_macrostates/src/{zones,contact_graphs,macrostates,sequences,robustness}.py`, `team2_macrostates/README.md`, `team2_macrostates/report/report.md`

**Interfaces:**
- Consumes: existing equations, parameter values, model names, and analysis definitions.
- Produces: the README title, table of contents, physics sections, workflow, and repository map used by later tasks.

- [ ] **Step 1: Verify source facts**

Read the consulted files and record the exact force/potential equations, sign convention, units, simulation parameters, zone boundaries, graph definitions, macrostate rules, filter length, return horizons, and candidate thresholds.

- [ ] **Step 2: Write the physics-first introduction**

Create `README.md` with: project purpose; an ELI5 section using accurate analogies; detailed vdW, DLVO, Debye screening, core repulsion, CL retardation, non-additivity, Brownian dynamics, and numerical-stability subsections; then the Team 1 → Team 2 → Team 3 workflow and repository map.

- [ ] **Step 3: Add Team-1 and Team-2 conceptual explanations**

Explain the 18-run fair N=20 ensemble plus separate N=50 run, surface gaps and minimum image, all six zones, hard/near/meso graphs, graph features, seven macrostates, persistence filtering, dwell/transition/return metrics, jitter agreement, and the five candidate heuristics.

- [ ] **Step 4: Check the scientific guardrails**

Confirm the text explicitly states: `L = ||x_j − x_i||_mic − 2R`; vdW and CL are compared rather than added; `tetra_like` is a 2D proxy; preclustered starts do not demonstrate spontaneous formation; candidates are not formal attractor proofs.

### Task 2: Complete figure guide and results interpretation

**Files:**
- Modify: `README.md`
- Inspect: `team1_forces/figures/*.png` (14 files)
- Inspect: `team2_macrostates/figures/*.png` (7 files)
- Consult: both `report/report.md` files and relevant processed CSVs for numerical claims

**Interfaces:**
- Consumes: the conceptual sections from Task 1 and all existing figure files.
- Produces: 21 embedded figures, each followed by what it shows, how to read it, its supported conclusion, and caveats.

- [ ] **Step 1: Inspect every figure visually**

Open all 21 PNGs and note axes, panels, units, legends, model/material labels, and visible patterns. Do not derive descriptions from filenames alone.

- [ ] **Step 2: Embed and explain Team-1 figures**

Group force/potential curves, pair dynamics, cluster simulations, sensitivity analyses, and the negative control into the relevant physics/results sections. Use root-relative links such as `team1_forces/figures/01_kraftkurven_pmbc.png`.

- [ ] **Step 3: Embed and explain Team-2 figures**

Cover raw/filtered sequences, cluster-size distributions, dwell times, transition matrices, return probabilities, jitter agreement, and material comparison. Keep deep-overlap and preclustered-start qualifications beside affected interpretations.

- [ ] **Step 4: Verify numerical interpretations**

Check every quoted frequency, dwell time, return probability, agreement score, overlap percentage, run count, and candidate classification against the report or processed data. State explicitly that unavailable DLVO return statistics are not zero probabilities.

- [ ] **Step 5: Check figure coverage**

Run a Python standard-library check extracting `![...](...)` paths from `README.md`; assert exactly 21 unique PNG paths, all exist, and the set equals the 21 files in both figure directories.

### Task 3: Practical documentation and final verification

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: the complete conceptual and figure narrative.
- Produces: the finished standalone root documentation.

- [ ] **Step 1: Add usage and reference sections**

Document setup, notebook order, test commands, input/output locations, CSV contracts, Team-3 schema, key limitations, an English glossary, literature pointers, and links to both team READMEs and detailed reports.

- [ ] **Step 2: Check all local links and reproduction commands**

Run a Python standard-library check that every relative Markdown file/image link resolves from the repository root. Run both full test suites with `team1_forces/.venv/bin/python -m pytest` from the respective project directories; expect Team 1: 40 passed and Team 2: 72 passed.

- [ ] **Step 3: Review readability and scope**

Read the README top to bottom. Confirm physics precedes software details, ELI5 precedes technical theory, each figure has an explanation rather than only a caption, observations are separated from inference, and no new scope or unsupported claim was introduced.

- [ ] **Step 4: Report completion evidence**

Report the README path, counts of explained Team-1/Team-2 figures, link-check result, and fresh test totals. Do not commit or push.
