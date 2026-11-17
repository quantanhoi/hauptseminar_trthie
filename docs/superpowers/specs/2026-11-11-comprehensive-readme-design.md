# Comprehensive Root README Design

**Date:** 2026-11-11  
**Status:** approved by user with English language and physics-first ordering

## Intent and audience

Create a comprehensive root `README.md` for seminar readers, reviewers, and future users. It must teach the project from first principles, not merely list files or reproduce reports. Physics comes first: an accessible ELI5 explanation followed by a technically detailed explanation.

## User decisions

- Write the README and its figure explanations in **English**, overriding the earlier German-documentation convention for this file only.
- Cover the complete Team 1 → Team 2 project and all **21 existing figures** (14 Team-1 and 7 Team-2 figures).
- Explain the physics before introducing software, data schemas, results, or reproduction commands.
- Include both ELI5 intuition and detailed scientific explanations.
- Keep the existing team-specific READMEs unchanged unless a link or factual correction is strictly necessary.

## Approach

Create one root `README.md` as the unified entry point. Expanding both team READMEs was rejected because it would not provide a single narrative; a short link-only overview was rejected because it would not be comprehensive.

## README structure

1. Project purpose, central question, and honest one-paragraph summary.
2. **Physics first — ELI5:** protoCells as particles, attraction/repulsion, thermal motion, distance gaps, clusters, graphs, and macrostates using concrete analogies.
3. **Physics in detail:** surface separation, Hamaker interaction, non-retarded van der Waals, DLVO electrostatics and core repulsion, Debye screening, retarded Casimir–Lifshitz approximation, why vdW and CL are not added, Brownian dynamics, numerical stability, materials, and model limitations.
4. End-to-end workflow and repository map: Team 1 microphysics → Team 2 coarse-graining → Team 3 handoff.
5. Team-1 concepts: pair dynamics, cluster simulations, seeds, fair N=20 ensemble, and separate N=50 exploration.
6. Team-2 concepts: minimum-image distance, six exact distance zones, hard/near/meso graphs, graph features, seven macrostates, persistence filtering, dwell/transition/return metrics, jitter robustness, and attractor-candidate heuristics.
7. **Figure guide:** embed every existing PNG with a consistent explanation of what it shows, how to read it, the supported conclusion, and relevant caveats. Group figures by physics/workflow rather than dumping a gallery.
8. Results and interpretation, clearly separating observations from inference and avoiding claims of spontaneous formation or proven attractors.
9. Data contracts, setup, test and notebook reproduction commands.
10. Limitations, glossary, references, and links to the detailed German reports.

## Constraints and verification

- Ground equations, thresholds, numerical results, and conclusions in the existing source, reports, CSVs, notebooks, and figures.
- Inspect every included figure; do not infer a figure's contents from its filename alone.
- Preserve exact scientific thresholds and canonical names; do not modify physics, data, notebooks, dependencies, or generated figures.
- Use relative Markdown image paths that render from the repository root.
- Explain deep-overlap artefacts beside affected vdW/CL results, not only in a final limitations section.
- Distinguish unavailable return statistics from zero return probability.
- Validate all linked files and image paths and check the rendered Markdown structure after writing.

## Non-goals

No new scientific analysis, new figures, presentation slides, Team-3 implementation, translation of the existing reports, or git commit/push.
