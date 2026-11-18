# Team 1 interactive physics demo

This folder contains the learner-facing, dependency-free companion to Team 1's
pair-force model.

- `index.html` — standalone page; open it directly in a modern browser.
- `interactive.test.mjs` — Node tests for the force kernel, page structure,
  accessibility, and chart behavior.
- `speech_script.md` — German presentation script with cues for using the page.

Run the checks from this folder:

```bash
node --test interactive.test.mjs
```

The page shows one protocell pair. You can switch between van der Waals,
classical DLVO, and retarded Casimir–Lifshitz forces; select material, salt
concentration, and thermal motion; drag protocell B or use its keyboard slider
to set the surface gap; and play or pause the Brownian pair dynamics.

The page illustrates the force laws in `../src/`. It does not reproduce the
exported 2D many-particle ensemble, prove spontaneous cluster formation, or
replace the detailed model and caveats in `../README.md` and
`../report/report.md`.
