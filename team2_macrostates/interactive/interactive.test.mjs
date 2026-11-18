import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const BLOCK_START = '<script id="team2-data" type="application/json">';

export const html = readFileSync(path.join(HERE, "index.html"), "utf8");
const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)];
const dataScript = scripts.find((m) => m[1].includes('id="team2-data"'));
export const executableScripts = scripts.filter((m) => !/\bsrc=/.test(m[1])
  && !/type="(application|text)\/(json|plain)"/.test(m[1]));
export const data = JSON.parse(dataScript[2]);

const context = vm.createContext({ console });
if (executableScripts.length) vm.runInContext(executableScripts[0][2], context);
export const K = context.Team2Interactive;
// Values built inside the vm realm are not reference-equal to host-realm values.
const host = (value) => structuredClone(value);

test("page has one executable inline script and no external runtime assets", () => {
  assert.equal(executableScripts.length, 1, "exactly one executable inline script");
  assert.equal(scripts.filter((m) => /\bsrc=/.test(m[1])).length, 0, "no external scripts");
  assert.ok(dataScript[1].includes('type="application/json"'));
  assert.equal((html.match(/<link\b[^>]*>/g) ?? []).length, 0, "no external stylesheets");
  assert.equal(html.match(/<img\b/g), null, "no external images");
  assert.equal(html.match(/https?:\/\//g), null, "no remote asset URLs");
});

test("kernel is exposed without a DOM", () => {
  assert.equal(typeof K, "object");
  for (const name of ["surfaceGapNm", "distanceZone", "frameParticles", "buildGraph",
    "macrostateFromGraph", "filterShortStates", "particleViewBox"]) {
    assert.equal(typeof K[name], "function", `missing kernel function ${name}`);
  }
});
test("minimum image and plain geometry give the expected surface gap", () => {
  const opposite = K.surfaceGapNm({ x: 19999, y: 5000 }, { x: 1, y: 5000 });
  assert.ok(Math.abs(opposite - (-998)) < 1e-9, `periodic gap ${opposite}`);
  const plain = K.surfaceGapNm({ x: 3000, y: 0 }, { x: 0, y: 4000 });
  assert.ok(Math.abs(plain - 4000) < 1e-9, `plain gap ${plain}`);
  assert.ok(Math.abs(K.surfaceGapNm({ x: 5000, y: 5000 }, { x: 5000.5, y: 5000 }) - (-999.5)) < 1e-9);
});

test("every zone boundary is classified exactly as the analysis defines it", () => {
  const expected = [
    [-1, "hard_contact"], [1.999, "hard_contact"], [2, "dlvo_zone"], [4.999, "dlvo_zone"],
    [5, "near_gap"], [9.999, "near_gap"], [10, "meso_gap"], [29.999, "meso_gap"],
    [30, "far_gap"], [99.999, "far_gap"], [100, "separated"],
  ];
  for (const [gap, zone] of expected) assert.equal(K.distanceZone(gap), zone, `gap ${gap}`);
});

test("the local view frames every particle without changing its coordinates", () => {
  const particles = [{ id: 1, x: 1000, y: 2000 }, { id: 2, x: 3000, y: 4000 }];
  assert.equal(K.particleViewBox(particles, 500, 0), "500 1500 3000 3000");
  assert.equal(K.particleViewBox([{ id: 1, x: 1000, y: 2000 }], 500, 0),
    "0 1000 2000 2000", "coincident particles still get a usable non-zero view");
  assert.throws(() => K.particleViewBox([], 500), /empty/i);
});

test("graph features keep isolated particles and count components", () => {
  const particles = [
    { id: 1, x: 5000, y: 5000 }, { id: 2, x: 6001.2, y: 5000 },
    { id: 3, x: 1000, y: 1000 }, { id: 4, x: 2001, y: 1000 },
    { id: 5, x: 15000, y: 15000 },
  ];
  const graph = K.buildGraph(particles, "hard");
  assert.equal(graph.edges.length, 2);
  assert.deepEqual(host(graph.clusterSizes), [2, 2, 1]);
  assert.equal(graph.largestCluster, 2);
  assert.equal(graph.meanDegree, 0.8);
  assert.equal(graph.nodes.length, 5);
  assert.deepEqual(host(graph.nodes), [1, 2, 3, 4, 5]);
  assert.deepEqual(host(graph.components.map((c) => c.length)), [2, 2, 1]);
  assert.ok(graph.components.flat().includes(5));
  assert.deepEqual(host(graph.components.map((c) => c.flat().sort((a, b) => a - b)).flat().sort((a, b) => a - b)),
    [1, 2, 3, 4, 5]);
  assert.equal(K.buildGraph(particles, "near").edges.length, 2);
  assert.equal(K.buildGraph(particles, "meso").edges.length, 2);
});

test("edge objects carry both particle ids, the gap and the zone", () => {
  const graph = K.buildGraph(
    [{ id: 7, x: 5000, y: 5000 }, { id: 9, x: 6007, y: 5000 }], "near");
  assert.equal(graph.edges.length, 1);
  const edge = host(graph.edges[0]);
  assert.equal(edge.i, 7);
  assert.equal(edge.j, 9);
  assert.ok(Math.abs(edge.gapNm - 7) < 1e-9, `gap ${edge.gapNm}`);
  assert.equal(edge.zone, "near_gap");
});
const LINE = (count) => Array.from({ length: count }, (_, index) =>
  ({ id: index + 1, x: 5000 + index * 1001, y: 5000 }));
const SQUARE = [
  { id: 1, x: 5000, y: 5000 }, { id: 2, x: 6001, y: 5000 },
  { id: 3, x: 5000, y: 6001 }, { id: 4, x: 6001, y: 6001 },
];
const FAR = [{ id: 1, x: 5000, y: 5000 }, { id: 2, x: 12000, y: 12000 }, { id: 3, x: 16000, y: 5000 }];

test("macrostate rules cover every label in the catalogue", () => {
  const label = (particles, graphType = "hard") =>
    K.macrostateFromGraph(K.buildGraph(particles, graphType));
  assert.equal(label(FAR), "monomer_gas");
  assert.equal(label([{ id: 1, x: 5000, y: 5000 }, { id: 2, x: 6001.5, y: 5000 },
    { id: 3, x: 12000, y: 12000 }]), "dimer_dominated");
  assert.equal(label(LINE(3)), "trimer_like");
  assert.equal(label(SQUARE), "tetra_like");
  assert.equal(label(LINE(4)), "loose_four_cluster");
  assert.equal(label(LINE(5)), "large_cluster");
  assert.equal(K.macrostateFromGraph({ edges: [], components: [[1], [2]] }), "monomer_gas");
});

test("the five-frame filter keeps sequence length and raw input", () => {
  const raw = ["a", "a", "a", "a", "a", "b", "c", "c", "c", "c", "c"];
  assert.deepEqual(host(K.filterShortStates(raw, 5)),
    ["a", "a", "a", "a", "a", "a", "c", "c", "c", "c", "c"]);
  assert.deepEqual(host(K.filterShortStates(["x", "a", "a", "a", "a", "a"], 5)),
    ["a", "a", "a", "a", "a", "a"]);
  assert.deepEqual(host(K.filterShortStates(["a", "b", "c"], 5)),
    ["mixed_transition", "mixed_transition", "mixed_transition"]);
  assert.deepEqual(raw, ["a", "a", "a", "a", "a", "b", "c", "c", "c", "c", "c"]);
});

test("embedded payload holds all 18 N=20 runs with aligned frames", () => {
  assert.equal(data.schemaVersion, 1);
  assert.equal(data.runs.length, 18);
  assert.equal(new Set(data.runs.map((r) => r.id)).size, 18);
  const pairs = new Map();
  for (const run of data.runs) {
    assert.equal(run.particleIds.length, 20);
    assert.equal(run.frames.length, 1000);
    assert.ok(!run.id.includes("N50"), `N=50 leaked into playback: ${run.id}`);
    const key = `${run.model}|${run.material}`;
    pairs.set(key, [...(pairs.get(key) ?? []), run.seed].sort((a, b) => a - b));
    for (const graphType of ["hard", "near", "meso"]) {
      const block = run.graphs[graphType];
      assert.equal(block.raw.length, 1000);
      assert.equal(block.filtered.length, 1000);
      assert.equal(block.features.length, 1000);
    }
  }
  assert.equal(pairs.size, 6);
  for (const seeds of pairs.values()) assert.deepEqual(seeds, [0, 1, 42]);
});

test("recomputed geometry reproduces every exported feature and raw label", () => {
  for (const run of data.runs) {
    for (let frame = 0; frame < run.frames.length; frame += 1) {
      const particles = K.frameParticles(run, frame, data.pmPerUnit);
      assert.equal(particles.length, 20);
      for (const graphType of ["hard", "near", "meso"]) {
        const graph = K.buildGraph(particles, graphType, data.radiusNm, data.boxNm);
        const block = run.graphs[graphType];
        const exported = block.features[frame];
        assert.equal(K.macrostateFromGraph(graph), block.raw[frame],
          `${run.id} frame ${frame} ${graphType}`);
        assert.equal(graph.largestCluster, exported.largestCluster, `${run.id}/${frame}/${graphType}`);
        assert.equal(graph.components.length, exported.componentCount, `${run.id}/${frame}/${graphType}`);
        assert.equal(graph.edges.length, exported.edgeCount, `${run.id}/${frame}/${graphType}`);
        assert.deepEqual(host(graph.clusterSizes), exported.clusterSizes, `${run.id}/${frame}/${graphType}`);
        assert.ok(Math.abs(graph.meanDegree - exported.meanDegree) < 1e-12,
          `${run.id}/${frame}/${graphType} meanDegree ${graph.meanDegree} vs ${exported.meanDegree}`);
      }
    }
  }
});

test("the filter reproduces every exported filtered sequence", () => {
  for (const run of data.runs) {
    for (const graphType of ["hard", "near", "meso"]) {
      const block = run.graphs[graphType];
      assert.deepEqual(host(K.filterShortStates(block.raw, 5)), block.filtered, `${run.id} ${graphType}`);
    }
  }
});

const PAGE_IDS = [
  "data-error", "model", "material", "seed", "graph-type", "play", "reset", "speed",
  "frame-slider", "scene", "scene-zoom", "edge-select", "time-readout", "gap-readout", "edges-readout",
  "components-readout", "largest-readout", "degree-readout", "macrostate-readout",
  "filtered-macrostate-readout", "macrostate-explanation", "overlap-warning", "raw-timeline",
  "filtered-timeline", "changed-count", "dwell-readout", "state-evidence", "candidate-cards",
  "node-roster", "frame-readout", "scene-desc", "evidence-title", "state-buttons",
  "raw-runs", "filtered-runs", "example-filter", "example-stable",
];
const svgBlocks = () => [...html.matchAll(/<svg\b[\s\S]*?<\/svg>/g)].map((m) => m[0]);

test("every page region the script writes into exists exactly once", () => {
  for (const id of PAGE_IDS) {
    const count = (html.match(new RegExp(`id="${id}"`, "g")) ?? []).length;
    assert.equal(count, 1, `id "${id}" appears ${count} times`);
  }
});

test("run, graph and frame controls are native form elements", () => {
  for (const id of ["model", "material", "seed", "speed", "edge-select"]) {
    assert.ok(new RegExp(`<select[^>]*id="${id}"`).test(html), `${id} must be a select`);
  }
  for (const id of ["play", "reset"]) {
    assert.ok(new RegExp(`<button[^>]*id="${id}"`).test(html), `${id} must be a button`);
  }
  const slider = html.match(new RegExp(`<input[^>]*id="frame-slider"[^>]*>`))?.[0];
  assert.ok(slider, "frame-slider must be an input");
  for (const pin of ['type="range"', 'min="0"', 'max="999"', 'step="1"', 'value="0"']) {
    assert.ok(slider.includes(pin), `frame-slider missing ${pin}`);
  }
  const graph = html.match(/<fieldset[^>]*id="graph-type"[\s\S]*?<\/fieldset>/)?.[0];
  assert.ok(graph, "graph-type must be a fieldset");
  for (const type of ["hard", "near", "meso"]) {
    assert.ok(new RegExp(`type="radio"[^>]*value="${type}"`).test(graph), `missing ${type} radio`);
  }
  assert.ok(/value="meso"[^>]*checked/.test(graph), "meso must be the checked default");
  for (const cutoff of ["2 nm", "10 nm", "30 nm"]) assert.ok(graph.includes(cutoff));
});

test("every SVG carries a title and a description", () => {
  const svgs = svgBlocks();
  assert.ok(svgs.length >= 4, `expected scene, two timelines and bars, found ${svgs.length}`);
  for (const svg of svgs) {
    assert.ok(/<title\b/.test(svg) && /<desc\b/.test(svg), svg.slice(0, 60));
    assert.ok(/role="img"/.test(svg), "svg needs an accessible role");
  }
});

test("the page tells the learner what the results do and do not show", () => {
  const text = html.toLowerCase();
  const phrases = [
    "preclustered", "not spontaneous", "five-frame", "1 nm", "5 ms", "three seeds",
    "tetra_like", "2d", "core repulsion", "overlap", "heuris", "not a formal",
    "basin", "attractor memory",
  ];
  for (const phrase of phrases) assert.ok(text.includes(phrase), `missing caveat: ${phrase}`);
});

test("the page starts paused on DLVO / PMBC / seed 0 at frame 0", () => {
  const selectBlock = (id) => html.match(new RegExp(`<select[^>]*id="${id}"[\\s\\S]*?</select>`))?.[0] ?? "";
  assert.ok(/value="dlvo_classic"[^>]*selected/.test(selectBlock("model")));
  assert.ok(/value="PMBC"[^>]*selected/.test(selectBlock("material")));
  assert.ok(/value="0"[^>]*selected/.test(selectBlock("seed")));
  const text = html.toLowerCase();
  const play = html.match(/<button[^>]*id="play"[\s\S]*?<\/button>/)?.[0] ?? "";
  assert.ok(/>Play<\/button>/.test(play), `play button label: ${play}`);
  assert.ok(!/autoplay/.test(text), "no autoplay");
  assert.ok(/<noscript>/.test(html));
  assert.ok(/id="data-error"[^>]*role="alert"/.test(html));
});

test("required caveats are never hidden inside details elements", () => {
  const details = [...html.matchAll(/<details[\s\S]*?<\/details>/g)].map((m) => m[0]).join("\n");
  for (const phrase of ["preclustered", "not a formal", "core repulsion", "5 ms",
    "1 nm", "three seeds", "2d compactness proxy"]) {
    assert.ok(!details.toLowerCase().includes(phrase), `caveat "${phrase}" must stay visible`);
  }
});

const DWELL_CSV = path.join(HERE, "..", "data", "processed", "dwell_times.csv");
const dwellRows = (() => {
  const lines = readFileSync(DWELL_CSV, "utf8").trim().split(/\r?\n/);
  const head = lines[0].split(",");
  return lines.slice(1).map((line) => {
    const cells = line.split(",");
    const row = {};
    head.forEach((name, index) => { row[name] = cells[index]; });
    return row;
  });
})();

test("dwellAtFrame reports the containing run, its length and both censoring flags", () => {
  const times = [0, 5e-6, 10e-6, 15e-6, 20e-6];
  const sequence = ["a", "a", "b", "b", "b"];
  const middle = host(K.dwellAtFrame(sequence, 2, times));
  assert.equal(middle.state, "b");
  assert.equal(middle.startIndex, 2);
  assert.equal(middle.endIndex, 4);
  assert.equal(middle.frames, 3);
  assert.ok(Math.abs(middle.seconds - 15e-6) <= 1e-15, `seconds ${middle.seconds}`);
  assert.equal(middle.leftCensored, false);
  assert.equal(middle.rightCensored, true);
  const first = host(K.dwellAtFrame(sequence, 0, times));
  assert.equal(first.state, "a");
  assert.equal(first.leftCensored, true);
  assert.equal(first.rightCensored, false);
  assert.ok(Math.abs(first.seconds - 10e-6) <= 1e-15);
  assert.throws(() => K.dwellAtFrame([], 0, []), /empty/i);
  assert.throws(() => K.dwellAtFrame(sequence, 5, times), /range/i);
  assert.throws(() => K.dwellAtFrame(sequence, -1, times), /range/i);
  assert.throws(() => K.dwellAtFrame(sequence, 1, times.slice(0, 3)), /length/i);
});

test("every exported filtered dwell row matches the browser dwell calculation", () => {
  let checked = 0;
  for (const row of dwellRows) {
    if (row.sequence_type !== "filtered" || Number(row.n_particles) !== 20) continue;
    const run = data.runs.find((candidate) => candidate.model === row.model_type
      && candidate.material === row.material_type && candidate.seed === Number(row.seed));
    assert.ok(run, `missing run for ${row.run_id}`);
    const sequence = run.graphs[row.graph_type].filtered;
    const dwell = host(K.dwellAtFrame(sequence, Number(row.start_index), data.timesSeconds));
    assert.equal(dwell.state, row.state, row.run_id);
    assert.equal(dwell.startIndex, Number(row.start_index), row.run_id);
    assert.equal(dwell.endIndex, Number(row.end_index), row.run_id);
    assert.equal(dwell.frames, Number(row.dwell_steps), row.run_id);
    assert.equal(dwell.leftCensored, row.left_censored === "True", row.run_id);
    assert.equal(dwell.rightCensored, row.right_censored === "True", row.run_id);
    assert.ok(Math.abs(dwell.seconds - Number(row.dwell_seconds)) <= 1e-15,
      `${row.run_id} seconds ${dwell.seconds} vs ${row.dwell_seconds}`);
    checked += 1;
  }
  assert.equal(checked, 170, `expected 170 filtered N=20 dwell rows, checked ${checked}`);
});

test("changed frames are reported and the documented example is pinned", () => {
  const raw = ["a", "a", "b", "c", "c"];
  assert.deepEqual(host(K.changedFrames(raw, ["a", "b", "b", "c", "d"])), [1, 4]);
  const changes = (run, graphType) =>
    K.changedFrames(run.graphs[graphType].raw, run.graphs[graphType].filtered).length;
  const example = data.runs.find((run) => run.model === "vdw_only"
    && run.material === "PMBC" && run.seed === 0);
  assert.equal(changes(example, "hard"), 9, "documented nine-frame example");
  for (const run of data.runs) assert.equal(changes(run, "meso"), 0, run.id);
});

test("playback is animation-frame driven, bounded and paused on hidden tabs", () => {
  const script = executableScripts[0][2];
  assert.ok(/requestAnimationFrame\(/.test(script), "needs requestAnimationFrame");
  assert.ok(!/\bsetInterval\b/.test(script), "no setInterval");
  assert.ok(/Math\.min\([^)]*,\s*100\)/.test(script), "elapsed time clamp of 100 ms");
  assert.ok(/Math\.min\([^)]*,\s*24\)/.test(script), "bounded per-display-frame advance");
  assert.ok(/visibilitychange/.test(script), "pauses when the document is hidden");
  assert.ok(/addEventListener\("input"/.test(script), "slider input handler");
  assert.ok(/addEventListener\("change"/.test(script), "native change handlers");
  assert.ok(/aria-valuetext/.test(script), "slider value text");
  assert.ok(/60\b/.test(script), "60 recorded frames per display second at 1x");
});

test("evidence lookup returns only the exact pooled row", () => {
  const row = host(K.evidenceFor(data, {
    model: "vdw_only", material: "fatty_acid", graph: "meso", state: "tetra_like",
  }));
  assert.ok(row, "known evidence row must be found");
  assert.equal(row.state, "tetra_like");
  assert.equal(row.graph, "meso");
  assert.equal(row.candidate, true);
  assert.equal(K.evidenceFor(data, {
    model: "dlvo_classic", material: "PMBC", graph: "meso", state: "tetra_like",
  }), null, "state absent from that group must not be invented");
  assert.equal(K.evidenceFor(data, {
    model: "no_such_model", material: "PMBC", graph: "meso", state: "tetra_like",
  }), null);
});

test("unavailable evidence is never formatted as zero", () => {
  assert.equal(K.metricText(null), "Unavailable");
  assert.equal(K.metricText(undefined), "Unavailable");
  assert.equal(K.metricText(0), "0.000");
  assert.equal(K.metricText(0.5, 1), "0.5");
});

test("candidateRows returns exactly the four exported passing rows", () => {
  const rows = host(K.candidateRows(data));
  assert.equal(rows.length, 4);
  assert.deepEqual(rows.map((row) => [row.model, row.material, row.graph, row.state].join("/")).sort(), [
    "cl_retarded/fatty_acid/meso/large_cluster",
    "vdw_only/fatty_acid/meso/large_cluster",
    "vdw_only/fatty_acid/meso/tetra_like",
    "vdw_only/fatty_acid/near/dimer_dominated",
  ]);
  for (const row of rows) {
    assert.equal(row.candidate, true);
    for (const key of ["frequency", "dwell", "returns", "seeds", "jitter"]) {
      assert.equal(row.checks[key], true, `${row.state} ${key} must pass`);
    }
  }
});

test("an unavailable criterion is never counted as a candidate pass", () => {
  const fake = {
    evidence: [{
      model: "m", material: "M", graph: "meso", state: "s", candidate: true,
      checks: { frequency: true, dwell: null, returns: true, seeds: true, jitter: true },
    }, {
      model: "m", material: "M", graph: "meso", state: "t", candidate: false,
      checks: { frequency: true, dwell: true, returns: true, seeds: true, jitter: true },
    }],
  };
  assert.deepEqual(host(K.candidateRows(fake)), []);
});

test("pooled return probabilities agree with the returned counts", () => {
  const counts = new Map(data.returnCounts.map((row) =>
    [`${row.model}/${row.material}/${row.graph}/${row.state}`, row]));
  assert.equal(counts.size, 67);
  for (const row of data.evidence) {
    const entry = counts.get(`${row.model}/${row.material}/${row.graph}/${row.state}`);
    assert.ok(entry, `missing counts for ${row.state}`);
    if (entry.eligible50 === 0) {
      assert.equal(row.returnProbability, null, `${row.state} must stay unavailable`);
    } else {
      assert.ok(Math.abs(row.returnProbability - entry.returns50 / entry.eligible50) <= 1e-12,
        `${row.state} probability ${row.returnProbability}`);
    }
  }
});

test("evidence has one native-button group and inspectable candidate cards", () => {
  assert.ok(/<div[^>]*id="state-buttons"[^>]*role="group"/.test(html), "state-buttons group");
  assert.ok(/<div[^>]*id="candidate-cards"/.test(html), "candidate cards region");
});

const parseCsv = (file) => {
  const lines = readFileSync(file, "utf8").trim().split(/\r?\n/);
  const head = lines[0].split(",");
  return lines.slice(1).map((line) => {
    const cells = line.split(",");
    const row = {};
    head.forEach((name, index) => { row[name] = cells[index]; });
    return row;
  });
};
const numberOrNull = (text) => (text === "" || text === undefined ? null : Number(text));
const flagOrNull = (text) => (text === "True" ? true : text === "False" ? false : null);

test("every exported evidence field matches attractor_candidates.csv", () => {
  const rows = parseCsv(path.join(HERE, "..", "data", "processed", "attractor_candidates.csv"))
    .filter((row) => Number(row.n_particles) === 20);
  assert.equal(rows.length, 67);
  const key = (row) => [row.model_type, row.material_type, row.graph_type, row.state].join("/");
  const expected = new Map(rows.map((row) => [key(row), row]));
  const floats = [["frequency", "frequency"], ["meanDwellFrames", "mean_dwell_steps"],
    ["returnProbability", "return_probability_T50"], ["meanReturnFrames", "mean_return_steps_T200"],
    ["labelAgreement", "label_agreement"]];
  const flags = [["frequency", "frequency_ok"], ["dwell", "mean_dwell_ok"],
    ["returns", "return_probability_ok"], ["seeds", "seed_reproducibility"],
    ["jitter", "label_agreement_ok"]];
  for (const row of data.evidence) {
    const source = expected.get(key({ model_type: row.model, material_type: row.material,
      graph_type: row.graph, state: row.state }));
    assert.ok(source, `missing CSV row for ${row.state}`);
    for (const [field, column] of floats) {
      const want = numberOrNull(source[column]);
      if (want === null) assert.equal(row[field], null, `${row.state}/${field}`);
      else assert.ok(Math.abs(row[field] - want) <= 1e-12, `${row.state}/${field} ${row[field]} vs ${want}`);
    }
    assert.equal(row.seedCount, numberOrNull(source.seed_count), `${row.state}/seedCount`);
    assert.equal(row.totalSeeds, numberOrNull(source.total_seeds), `${row.state}/totalSeeds`);
    for (const [field, column] of flags) {
      assert.equal(row.checks[field], flagOrNull(source[column]), `${row.state}/${field}`);
    }
    assert.equal(row.candidate, flagOrNull(source.candidate), `${row.state}/candidate`);
  }
});

test("every exported transition matches transition_matrices.csv", () => {
  const rows = parseCsv(path.join(HERE, "..", "data", "processed", "transition_matrices.csv"))
    .filter((row) => Number(row.n_particles) === 20 && row.sequence_type === "filtered");
  assert.equal(rows.length, data.transitions.length);
  assert.equal(rows.length, 882);
  const key = (row) => [row.model_type, row.material_type, row.graph_type, row.source, row.target].join("/");
  const expected = new Map(rows.map((row) => [key(row), row]));
  for (const row of data.transitions) {
    const source = expected.get(key({ model_type: row.model, material_type: row.material,
      graph_type: row.graph, source: row.source, target: row.target }));
    assert.ok(source, `missing transition ${row.source}->${row.target}`);
    assert.equal(row.count, numberOrNull(source.count));
    assert.ok(Math.abs(row.probability - numberOrNull(source.probability)) <= 1e-12,
      `${row.source}->${row.target} ${row.probability} vs ${source.probability}`);
  }
});

test("a zero box turns off the minimum image", () => {
  const plain = K.surfaceGapNm({ x: 19999, y: 5000 }, { x: 1, y: 5000 }, 500, 0);
  assert.ok(Math.abs(plain - 18998) < 1e-9, `non-periodic gap ${plain}`);
  const periodic = K.surfaceGapNm({ x: 19999, y: 5000 }, { x: 1, y: 5000 }, 500, 20000);
  assert.ok(Math.abs(periodic - (-998)) < 1e-9, `periodic gap ${periodic}`);
});

test("validateEmbeddedData rejects malformed payloads", () => {
  assert.doesNotThrow(() => K.validateEmbeddedData(data));
  const withoutEvidence = structuredClone(data);
  delete withoutEvidence.evidence;
  assert.throws(() => K.validateEmbeddedData(withoutEvidence), /evidence/);
  const badUnit = structuredClone(data);
  badUnit.pmPerUnit = 0;
  assert.throws(() => K.validateEmbeddedData(badUnit), /pmPerUnit/);
  const badGrid = structuredClone(data);
  badGrid.timesSeconds = [];
  assert.throws(() => K.validateEmbeddedData(badGrid), /time grid/);
  const badRun = structuredClone(data);
  badRun.runs[0].graphs.hard.raw = [];
  assert.throws(() => K.validateEmbeddedData(badRun), /hard/);
});

test("guided examples and timeline labels make persistence discoverable", () => {
  for (const id of ["example-filter", "example-stable"]) {
    assert.ok(new RegExp(`<button[^>]*id="${id}"`).test(html), `${id} must be a button`);
  }
  const raw = html.match(/<svg[^>]*id="raw-timeline"/)?.index ?? -1;
  const filtered = html.match(/<svg[^>]*id="filtered-timeline"/)?.index ?? -1;
  assert.ok(raw > 0 && filtered > raw, "both timelines exist in reading order");
  assert.ok(/<h3[^>]*>Raw labels/.test(html.slice(0, raw)));
  assert.ok(/<h3[^>]*>Filtered labels/.test(html.slice(raw, filtered)));
});

test("the page names the interaction model correctly and adds no other physics claim", () => {
  assert.ok(html.includes("Casimir–Lifshitz"));
  assert.ok(!html.includes("Coulomb"), "cl_retarded is Casimir-Lifshitz, not Coulomb");
});

test("particle and edge colours are explained in writing", () => {
  assert.ok(html.includes("Marker fill colour marks component membership"),
    "marker fill must be explained");
  assert.ok(html.includes("line colour follows the distance-zone legend"),
    "edge colour must point at the zone legend");
  assert.ok(html.includes("Colours repeat after eight components"),
    "repeated component colours must be disclosed");
});
