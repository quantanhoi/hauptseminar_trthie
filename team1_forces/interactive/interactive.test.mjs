import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const htmlPath = new URL("./index.html", import.meta.url);

function readPage() {
  return readFileSync(htmlPath, "utf8");
}

const VOID_TAGS = new Set([
  "area", "base", "br", "col", "embed", "hr", "img", "input",
  "link", "meta", "source", "track", "wbr",
]);

function openAncestors(html, id) {
  const target = html.indexOf(`id="${id}"`);
  assert.ok(target >= 0, `missing #${id}`);
  const stack = [];
  const tagPattern = /<(\/?)([A-Za-z][\w:-]*)([^>]*)>/g;
  let match;
  while ((match = tagPattern.exec(html)) && match.index < target) {
    const [, closing, rawTag, attrs] = match;
    const tag = rawTag.toLowerCase();
    if (closing) {
      const index = stack.map((item) => item.tag).lastIndexOf(tag);
      if (index >= 0) stack.length = index;
    } else if (!match[0].endsWith("/>") && !VOID_TAGS.has(tag)) {
      stack.push({ tag, attrs });
    }
  }
  return stack;
}

function controlsMarkup(html) {
  const match = html.match(/<aside class="card controls-card"[\s\S]*?<\/aside>/);
  assert.ok(match, "missing controls card");
  return match[0];
}

function loadPhysics() {
  const html = readPage();
  const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)];
  assert.equal(scripts.length, 1, "expected exactly one inline script");
  const context = vm.createContext({ console });
  vm.runInContext(scripts[0][1], context, { filename: "index.html" });
  assert.ok(context.Team1Physics, "inline script must expose globalThis.Team1Physics");
  return context.Team1Physics;
}

const base = {
  model: "vdw",
  material: "pmbc",
  saltMm: 100,
};

function close(actual, expected, tolerance, label) {
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    `${label}: expected ${expected} ± ${tolerance}, got ${actual}`,
  );
}

test("non-retarded vdW contains only the signed PMBC attraction", () => {
  const physics = loadPhysics();
  const force = physics.forceAtGap(20, base);

  close(force.vdW, -0.520833333, 1e-9, "vdW");
  close(force.total, -0.520833333, 1e-9, "total");
  assert.equal(force.electrostatic, 0);
  assert.equal(force.core, 0);
});

test("retarded CL attenuates vdW without adding it again", () => {
  const physics = loadPhysics();
  const force = physics.forceAtGap(20, { ...base, model: "cl_retarded" });

  close(physics.retardationFactor(20), 0.25, 1e-12, "retardation factor");
  close(force.vdW, -0.520833333, 1e-9, "base vdW");
  close(force.total, -0.130208333, 1e-9, "CL total");
  assert.equal(force.electrostatic, 0);
  assert.equal(force.core, 0);
});

test("DLVO components sum to its net force at 2 nm", () => {
  const physics = loadPhysics();
  const force = physics.forceAtGap(2, { ...base, model: "dlvo" });

  close(force.electrostatic, 10.6781665, 1e-8, "electrostatic");
  close(
    force.total,
    force.electrostatic + force.vdW + force.core,
    1e-12,
    "component sum",
  );
  assert.ok(force.core > 0);
  assert.ok(force.vdW < 0);
});

test("fatty-acid attraction is one tenth of PMBC", () => {
  const physics = loadPhysics();
  const pmbc = physics.forceAtGap(20, base);
  const fattyAcid = physics.forceAtGap(20, { ...base, material: "fatty_acid" });

  close(fattyAcid.total, pmbc.total / 10, 1e-12, "material ratio");
});

test("salt weakens DLVO repulsion and cannot alter vdW or CL", () => {
  const physics = loadPhysics();
  const dlvo50 = physics.forceAtGap(2, { ...base, model: "dlvo", saltMm: 50 });
  const dlvo100 = physics.forceAtGap(2, { ...base, model: "dlvo", saltMm: 100 });
  const dlvo200 = physics.forceAtGap(2, { ...base, model: "dlvo", saltMm: 200 });
  assert.ok(dlvo50.electrostatic > dlvo100.electrostatic);
  assert.ok(dlvo100.electrostatic > dlvo200.electrostatic);

  for (const model of ["vdw", "cl_retarded"]) {
    const lowSalt = physics.forceAtGap(20, { ...base, model, saltMm: 50 });
    const highSalt = physics.forceAtGap(20, { ...base, model, saltMm: 200 });
    assert.equal(lowSalt.total, highSalt.total, `${model} must ignore salt`);
  }
});

test("Brownian step uses the documented drift, noise, cap, and clamp", () => {
  const physics = loadPhysics();
  const normal = { ...base, noise: "normal" };
  close(physics.advanceGap(20, normal, 0), 19.994791667, 1e-8, "drift");

  const lowNoise = { ...normal, noise: "low" };
  const highNoise = { ...normal, noise: "high" };
  const lowMove = Math.abs(physics.advanceGap(20, lowNoise, 2) - 20);
  const highMove = Math.abs(physics.advanceGap(20, highNoise, 2) - 20);
  assert.ok(highMove > lowMove, "high noise should produce a larger kick");

  for (let i = 0; i < 100; i++) {
    const gap = physics.advanceGap(0.5, { ...normal, model: "dlvo" }, 1e9);
    assert.ok(Number.isFinite(gap));
    assert.ok(gap >= 0.5 && gap <= 200);
  }

  const strongAttraction = physics.forceAtGap(1, { ...base, model: "dlvo" });
  assert.ok(strongAttraction.total < -20, "display force must remain uncapped");
  close(
    physics.advanceGap(1, { ...normal, model: "dlvo" }, 0),
    0.8,
    1e-12,
    "negative force cap",
  );
});

test("contact zones use the documented strict upper boundaries", () => {
  const physics = loadPhysics();
  const cases = [
    [-900, "hard_contact"],
    [0, "hard_contact"],
    [1.999999999, "hard_contact"],
    [2, "dlvo_zone"],
    [4.999999999, "dlvo_zone"],
    [5, "near_gap"],
    [9.999999999, "near_gap"],
    [10, "meso_gap"],
    [29.999999999, "meso_gap"],
    [30, "far_gap"],
    [99.999999999, "far_gap"],
    [100, "separated"],
    [200, "separated"],
  ];
  for (const [gap, zone] of cases) {
    assert.equal(physics.contactZone(gap), zone, `${gap} nm`);
  }
});

test("page uses bounded animation and accessible direct manipulation", () => {
  const page = readPage();
  assert.match(page, /requestAnimationFrame/);
  assert.doesNotMatch(page, /setInterval/);
  assert.match(page, /MAX_STEPS_PER_FRAME\s*=\s*200/);
  assert.match(page, /Math\.min\(100,\s*Math\.max\(0,\s*elapsed/);
  assert.match(page, /visibilitychange/);
  assert.match(page, /pointerdown/);
  assert.match(page, /pointermove/);
  assert.match(page, /pointerup/);
  assert.match(page, /pointercancel/);
  assert.match(page, /keydown/);
  assert.match(page, /Math\.sqrt\(-2\s*\*\s*Math\.log\(/);
  assert.match(page, /role=["']slider["']/);
  assert.match(page, /aria-valuenow/);
  assert.match(page, /aria-valuemin/);
  assert.match(page, /aria-valuemax/);
});

test("slider is exposed, limits are visible, and distance visuals stay honest", () => {
  const page = readPage();
  const scene = page.match(/<svg[^>]*id=["']scene["'][^>]*>/)[0];
  assert.match(scene, /role=["']group["']/);
  assert.match(scene, /aria-describedby=["']scene-desc["']/);

  const ancestors = openAncestors(page, "right-particle");
  for (const ancestor of ancestors) {
    assert.doesNotMatch(ancestor.attrs, /aria-hidden=["']true["']/i,
      `#right-particle has hidden <${ancestor.tag}> ancestor`);
    assert.doesNotMatch(ancestor.attrs, /role=["']img["']/i,
      `#right-particle has role=img <${ancestor.tag}> ancestor`);
  }
  assert.match(page, /id=["']slider-hit-target["']/);

  const controls = controlsMarkup(page);
  for (const required of [
    /compared, never added/i,
    /not a full Lifshitz/i,
    /no core repulsion/i,
    /deep overlap/i,
    /not evidence of spontaneous cluster formation/i,
    /didactic demonstration settings/i,
    /not a fitted experimental noise/i,
    /10⁻¹⁷/,
    /10⁻¹⁶/,
    /10⁻¹⁵/,
  ]) {
    assert.match(controls, required, `visible controls copy missing ${required}`);
  }

  for (const id of ["gap-tick-left", "gap-tick-right", "chart-offscale"]) {
    assert.match(page, new RegExp(`id=["']${id}["']`), `missing #${id}`);
  }
  assert.match(page, /gapTickLeft\.setAttribute\(["']x1["']/);
  assert.match(page, /gapTickRight\.setAttribute\(["']x1["']/);
  assert.match(page, /chartOffscale\.style\.visibility/);
  assert.match(page, /@media \(max-width: 560px\)[\s\S]*?#force-chart text[\s\S]*?font-size:\s*32px/);
});

test("force-curve path is finite across the full plotted range", () => {
  const physics = loadPhysics();
  assert.equal(typeof physics.forceCurvePath, "function");
  for (const model of ["dlvo", "vdw", "cl_retarded"]) {
    const path = physics.forceCurvePath({ ...base, model });
    assert.ok(path.startsWith("M "));
    assert.doesNotMatch(path, /NaN|Infinity/);
    assert.ok(path.split("L ").length >= 240, `${model} should sample 240 gaps`);
  }
});

test("page exposes the learner structure, native controls, and model caveats", () => {
  const page = readPage();
  const ids = [
    "model",
    "material",
    "salt",
    "noise",
    "play",
    "reset",
    "scene",
    "right-particle",
    "gap-readout",
    "force-readout",
    "time-readout",
    "zone-readout",
    "model-explanation",
    "control-explanation",
    "force-chart",
    "force-curve",
    "force-marker",
  ];
  for (const id of ids) {
    assert.match(page, new RegExp(`id=["']${id}["']`), `missing #${id}`);
  }

  for (const id of ["model", "material", "salt", "noise"]) {
    assert.match(page, new RegExp(`<select[^>]*id=["']${id}["']`), `${id} must be a select`);
  }
  for (const id of ["play", "reset"]) {
    assert.match(page, new RegExp(`<button[^>]*id=["']${id}["']`), `${id} must be a button`);
  }
  assert.match(page, /<svg[^>]*id=["']scene["']/);
  assert.match(page, /<svg[^>]*id=["']force-chart["']/);
  assert.match(page, /<title[^>]*>[\s\S]*?<\/title>/);
  assert.match(page, /<desc[^>]*>[\s\S]*?<\/desc>/);
  assert.match(page, /not to scale/i);
  assert.match(page, /prefers-reduced-motion/);
  assert.match(page, /min-height:\s*44px|min-block-size:\s*44px/);

  assert.doesNotMatch(page, /<(script|img)[^>]+src=["']https?:/i);
  assert.doesNotMatch(page, /<link[^>]+href=["']https?:/i);
  assert.doesNotMatch(page, /url\(\s*["']?https?:/i);

  assert.match(page, /replace(?:s|d)?[\s\S]{0,80}(?:vdW|van der Waals)[\s\S]{0,80}(?:CL|Casimir)/i);
  assert.match(page, /not (?:a )?full Lifshitz/i);
  assert.match(page, /no core (?:repulsion|bumper)/i);
  assert.match(page, /deep overlap/i);
  assert.match(page, /pair[- ]dynamics demonstration/i);
  assert.match(page, /not evidence of spontaneous[\s\S]{0,40}clusters?/i);
});
