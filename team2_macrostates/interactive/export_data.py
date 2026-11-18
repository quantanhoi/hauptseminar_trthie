"""Build the compact JSON payload embedded in interactive/index.html."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

COORD_UNITS_PER_M = 1e13  # tenths of a picometre: whole-picometre storage flipped a 30 nm edge
PM_PER_UNIT = 0.1  # nm = stored value * PM_PER_UNIT / 1000
BOX_NM = 20000.0
RADIUS_NM = 500.0
GRAPH_TYPES = ("hard", "near", "meso")
MODEL_ALIASES = {
    "vdw": "vdw_only",
    "vdw_only": "vdw_only",
    "dlvo": "dlvo_classic",
    "dlvo_classic": "dlvo_classic",
    "cl_retarded": "cl_retarded",
}
EXPECTED_RUNS = 18
EXPECTED_FRAMES = 1000
EXPECTED_PARTICLES = 20
EXPECTED_N = 20
EXPECTED_SEEDS = {0, 1, 42}
EXPECTED_CANDIDATES = 4
BLOCK_START = '<script id="team2-data" type="application/json">'
BLOCK_END = "</script>"
RUN_METADATA = ("run_id", "seed", "model_type")
POSITION_COLUMNS = set(RUN_METADATA) | {"t", "particle_id", "x", "y"}
SEQUENCE_COLUMNS = {
    "run_id", "seed", "model_type", "material_type", "n_particles", "graph_type",
    "time", "macrostate_raw", "macrostate_filtered", "largest_cluster",
    "number_of_components", "number_of_edges", "mean_degree",
}
FEATURE_COLUMNS = {
    "run_id", "graph_type", "n_particles", "time", "largest_cluster",
    "number_of_components", "number_of_edges", "mean_degree",
    "cluster_size_distribution",
}
CANDIDATE_COLUMNS = {
    "n_particles", "model_type", "material_type", "graph_type", "state",
    "frequency", "mean_dwell_steps", "return_probability_T50",
    "mean_return_steps_T200", "seed_count", "total_seeds", "label_agreement",
    "frequency_ok", "mean_dwell_ok", "return_probability_ok",
    "seed_reproducibility", "label_agreement_ok", "candidate",
}
TRANSITION_COLUMNS = {
    "n_particles", "sequence_type", "model_type", "material_type",
    "graph_type", "source", "target", "count", "probability",
}
METRIC_COLUMNS = {
    "n_particles", "sequence_type", "model_type", "material_type",
    "graph_type", "state", "return_eligible_T50", "returns_T50",
}
PARAMETER_COLUMNS = {"run_id", "model_type", "R_nm", "dt"}
EXPECTED_PAIRS = {
    (model, material)
    for model in ("vdw_only", "dlvo_classic", "cl_retarded")
    for material in ("PMBC", "fatty_acid")
}
EXPECTED_COMBINATIONS = {
    (model, material, seed) for model, material in EXPECTED_PAIRS for seed in EXPECTED_SEEDS
}


def _require_columns(frame, columns, label):
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"{label} missing columns: {sorted(missing)}")


def _validate_run_selection(rows):
    """Reject a selection that is not exactly six pairs x three seeds."""
    pairs = {
        (_canonical_model(model), material, int(seed))
        for model, material, seed in rows[["model_type", "material_type", "seed"]].itertuples(index=False)
    }
    missing = EXPECTED_COMBINATIONS - pairs
    unexpected = pairs - EXPECTED_COMBINATIONS
    if missing or unexpected:
        raise ValueError(
            f"run selection differs from the 18-run contract: missing={sorted(missing)}, "
            f"unexpected={sorted(unexpected)}"
        )


def _nan_to_none(value):
    """Missing evidence stays missing: never coerce it to a number."""
    return None if value is None or pd.isna(value) else float(value)


def _canonical_model(model_type):
    if model_type not in MODEL_ALIASES:
        raise ValueError(f"unknown model_type: {model_type}")
    return MODEL_ALIASES[model_type]


def _validate_run_frames(frame, expected_frames=EXPECTED_FRAMES,
                         expected_particles=EXPECTED_PARTICLES):
    """Reject incomplete, duplicated, non-finite, or metadata-inconsistent rows."""
    missing = POSITION_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"position data missing columns: {sorted(missing)}")
    if frame.duplicated(subset=["t", "particle_id"]).any():
        raise ValueError("duplicate (time, particle_id) rows in run")
    if not np.isfinite(frame[["x", "y"]].to_numpy(dtype=float)).all():
        raise ValueError("x and y positions must be finite")
    for column in RUN_METADATA:
        if frame[column].nunique() != 1:
            raise ValueError(f"inconsistent run metadata: {column}")
    if frame["particle_id"].nunique() != expected_particles:
        raise ValueError(
            f"run has {frame['particle_id'].nunique()} particles, expected {expected_particles}"
        )
    if frame["t"].nunique() != expected_frames:
        raise ValueError(
            f"run has {frame['t'].nunique()} frames, expected {expected_frames}"
        )
    sizes = frame.groupby("t").size()
    if (sizes != expected_particles).any():
        raise ValueError("every frame must contain exactly the expected particles")


def _positions_to_pm(frame):
    """Pack one run's positions as 0.1 pm integers, ordered by time then ID."""
    frame = frame.sort_values(["t", "particle_id"], kind="mergesort")
    if not np.isfinite(frame[["x", "y"]].to_numpy(dtype=float)).all():
        raise ValueError("x and y positions must be finite")
    x_wide = frame.pivot(index="t", columns="particle_id", values="x")
    y_wide = frame.pivot(index="t", columns="particle_id", values="y")
    x_pm = np.rint(x_wide.to_numpy(dtype=float) * COORD_UNITS_PER_M).astype(np.int64)
    y_pm = np.rint(y_wide.to_numpy(dtype=float) * COORD_UNITS_PER_M).astype(np.int64)
    return {
        "particleIds": [int(column) for column in x_wide.columns],
        "timesSeconds": [float(time) for time in x_wide.index],
        "frames": [
            {"xPm": [int(v) for v in row_x], "yPm": [int(v) for v in row_y]}
            for row_x, row_y in zip(x_pm, y_pm)
        ],
    }


def _aggregate_return_counts(metrics):
    """Pool T=50 departures and returns per model/material/graph/state group."""
    _require_columns(metrics, METRIC_COLUMNS, "sequence_metrics.csv")
    frame = metrics[
        (metrics["n_particles"] == EXPECTED_N) & (metrics["sequence_type"] == "filtered")
    ]
    rows = []
    for (model, material, graph, state), group in frame.groupby(
        ["model_type", "material_type", "graph_type", "state"], sort=True
    ):
        rows.append({
            "model": model,
            "material": material,
            "graph": graph,
            "state": state,
            "eligible50": int(group["return_eligible_T50"].fillna(0).sum()),
            "returns50": int(group["returns_T50"].fillna(0).sum()),
        })
    return rows


def _graph_block(sequence_rows, feature_rows, run_id, graph_type, expected_times):
    """Align one run/graph's exported labels and features by frame index."""
    _require_columns(sequence_rows, SEQUENCE_COLUMNS, f"{run_id}/{graph_type} sequence export")
    _require_columns(feature_rows, FEATURE_COLUMNS, f"{run_id}/{graph_type} feature export")
    for label, frame in (("sequence", sequence_rows), ("feature", feature_rows)):
        if frame["time"].duplicated().any():
            raise ValueError(f"{run_id}/{graph_type}: duplicate {label} time keys")
    sequence_rows = sequence_rows.sort_values("time", kind="mergesort")
    feature_rows = feature_rows.sort_values("time", kind="mergesort")
    if not np.array_equal(sequence_rows["time"].to_numpy(), np.asarray(expected_times)):
        raise ValueError(f"{run_id}/{graph_type}: sequence times differ from the position grid")
    if len(sequence_rows) != EXPECTED_FRAMES or len(feature_rows) != EXPECTED_FRAMES:
        raise ValueError(
            f"{run_id}/{graph_type}: expected {EXPECTED_FRAMES} rows, got "
            f"{len(sequence_rows)} sequence and {len(feature_rows)} feature rows"
        )
    if not np.array_equal(sequence_rows["time"].to_numpy(), feature_rows["time"].to_numpy()):
        raise ValueError(f"{run_id}/{graph_type}: sequence and feature times do not align")

    sizes_column = feature_rows["cluster_size_distribution"].tolist()
    for column in ("largest_cluster", "number_of_components", "number_of_edges"):
        if not np.array_equal(sequence_rows[column].to_numpy(), feature_rows[column].to_numpy()):
            raise ValueError(f"{run_id}/{graph_type}: {column} disagrees between exports")
    largest = sequence_rows["largest_cluster"].tolist()
    components = sequence_rows["number_of_components"].tolist()
    edges = sequence_rows["number_of_edges"].tolist()
    degrees = sequence_rows["mean_degree"].tolist()
    features = []
    for index in range(EXPECTED_FRAMES):
        sizes = [int(size) for size in sizes_column[index].split(";") if size != ""]
        if sorted(sizes, reverse=True) != sizes:
            raise ValueError(f"{run_id}/{graph_type}: cluster sizes are not descending")
        features.append({
            "largestCluster": int(largest[index]),
            "componentCount": int(components[index]),
            "edgeCount": int(edges[index]),
            "meanDegree": _nan_to_none(degrees[index]),
            "clusterSizes": sizes,
        })
    return {
        "raw": sequence_rows["macrostate_raw"].tolist(),
        "filtered": sequence_rows["macrostate_filtered"].tolist(),
        "features": features,
    }


def _validate_parameters(parameters, models_by_run):
    """Cross-check the Team-1 parameter table against the embedded runs."""
    _require_columns(parameters, PARAMETER_COLUMNS, "parameters.csv")
    parameters = parameters[parameters["run_id"].isin(models_by_run)]
    if parameters["run_id"].duplicated().any():
        raise ValueError("parameters.csv has duplicate run_id rows")
    if set(parameters["run_id"]) != set(models_by_run):
        raise ValueError("parameters.csv run_ids differ from the embedded runs")
    for row in parameters.itertuples(index=False):
        if float(row.R_nm) != RADIUS_NM:
            raise ValueError(f"{row.run_id}: parameters R_nm={row.R_nm}, expected {RADIUS_NM}")
        if not float(row.dt) > 0:
            raise ValueError(f"{row.run_id}: parameters dt must be positive")
        if _canonical_model(row.model_type) != models_by_run[row.run_id]:
            raise ValueError(f"{row.run_id}: parameters model_type disagrees with sequences")


SOURCE_FILES = {
    "positions": "team1_forces/data/processed/positions.csv",
    "parameters": "team1_forces/data/processed/parameters.csv",
    "sequences": "team2_macrostates/data/processed/macrostate_sequences.csv",
    "graph_features": "team2_macrostates/data/processed/graph_features.csv",
    "candidates": "team2_macrostates/data/processed/attractor_candidates.csv",
    "transitions": "team2_macrostates/data/processed/transition_matrices.csv",
    "metrics": "team2_macrostates/data/processed/sequence_metrics.csv",
}


def _run_metadata(frame, run_id):
    """Read one run's metadata and reject any disagreement inside the export."""
    unique = {}
    for column in ("model_type", "material_type", "seed", "n_particles", "R_nm"):
        values = frame[column].unique()
        if len(values) != 1:
            raise ValueError(f"{run_id}: inconsistent {column}: {sorted(values)}")
        unique[column] = values[0]
    if int(unique["n_particles"]) != EXPECTED_N:
        raise ValueError(f"{run_id}: n_particles={unique['n_particles']}, expected {EXPECTED_N}")
    if float(unique["R_nm"]) != RADIUS_NM:
        raise ValueError(f"{run_id}: R_nm={unique['R_nm']}, expected {RADIUS_NM}")
    if int(unique["seed"]) not in EXPECTED_SEEDS:
        raise ValueError(f"{run_id}: seed {unique['seed']} outside {sorted(EXPECTED_SEEDS)}")
    return unique


def _evidence_rows(candidates):
    """Map the authoritative candidate CSV onto the page's evidence contract."""
    _require_columns(candidates, CANDIDATE_COLUMNS, "attractor_candidates.csv")
    rows = []
    for row in candidates[candidates["n_particles"] == EXPECTED_N].itertuples(index=False):
        rows.append({
            "model": row.model_type,
            "material": row.material_type,
            "graph": row.graph_type,
            "state": row.state,
            "frequency": _nan_to_none(row.frequency),
            "meanDwellFrames": _nan_to_none(row.mean_dwell_steps),
            "returnProbability": _nan_to_none(row.return_probability_T50),
            "meanReturnFrames": _nan_to_none(row.mean_return_steps_T200),
            "seedCount": None if pd.isna(row.seed_count) else int(row.seed_count),
            "totalSeeds": None if pd.isna(row.total_seeds) else int(row.total_seeds),
            "labelAgreement": _nan_to_none(row.label_agreement),
            "checks": {
                "frequency": None if pd.isna(row.frequency_ok) else bool(row.frequency_ok),
                "dwell": None if pd.isna(row.mean_dwell_ok) else bool(row.mean_dwell_ok),
                "returns": None if pd.isna(row.return_probability_ok) else bool(row.return_probability_ok),
                "seeds": None if pd.isna(row.seed_reproducibility) else bool(row.seed_reproducibility),
                "jitter": None if pd.isna(row.label_agreement_ok) else bool(row.label_agreement_ok),
            },
            "candidate": None if pd.isna(row.candidate) else bool(row.candidate),
        })
    return sorted(rows, key=lambda r: (r["model"], r["material"], r["graph"], r["state"]))


def _transition_rows(transitions):
    _require_columns(transitions, TRANSITION_COLUMNS, "transition_matrices.csv")
    frame = transitions[
        (transitions["n_particles"] == EXPECTED_N) & (transitions["sequence_type"] == "filtered")
    ]
    rows = [
        {
            "model": row.model_type, "material": row.material_type, "graph": row.graph_type,
            "source": row.source, "target": row.target,
            "count": _nan_to_none(row.count), "probability": _nan_to_none(row.probability),
        }
        for row in frame.itertuples(index=False)
    ]
    return sorted(rows, key=lambda r: (r["model"], r["material"], r["graph"], r["source"], r["target"]))


def build_interactive_data(repo_root):
    """Validate the real exports and return the page's embedded payload."""
    repo_root = Path(repo_root)
    tables, missing = {}, []
    for name, relative in SOURCE_FILES.items():
        path = repo_root / relative
        if not path.is_file():
            missing.append(str(path))
        else:
            tables[name] = pd.read_csv(path)
    if missing:
        raise ValueError(f"missing source files: {missing}")

    sequences = tables["sequences"]
    n20 = sequences[sequences["n_particles"] == EXPECTED_N]
    run_ids = sorted(n20["run_id"].unique())
    if len(run_ids) != EXPECTED_RUNS:
        raise ValueError(f"expected {EXPECTED_RUNS} N=20 runs, found {len(run_ids)}: {run_ids}")
    _validate_run_selection(n20.drop_duplicates(["run_id"]))

    runs, shared_times = [], None
    for run_id in run_ids:
        meta = _run_metadata(n20[n20["run_id"] == run_id], run_id)
        model = _canonical_model(meta["model_type"])
        material, seed = meta["material_type"], int(meta["seed"])

        positions = tables["positions"][tables["positions"]["run_id"] == run_id]
        if positions.empty:
            raise ValueError(f"{run_id}: no position rows")
        _validate_run_frames(positions)
        if _canonical_model(positions["model_type"].unique()[0]) != model:
            raise ValueError(f"{run_id}: position and sequence model_type disagree")
        if int(positions["seed"].unique()[0]) != seed:
            raise ValueError(f"{run_id}: position and sequence seed disagree")

        packed = _positions_to_pm(positions)
        if shared_times is None:
            shared_times = packed["timesSeconds"]
        elif packed["timesSeconds"] != shared_times:
            raise ValueError(f"{run_id}: time grid differs from the other runs")

        graphs = {
            graph_type: _graph_block(
                n20[(n20["run_id"] == run_id) & (n20["graph_type"] == graph_type)],
                tables["graph_features"][
                    (tables["graph_features"]["run_id"] == run_id)
                    & (tables["graph_features"]["graph_type"] == graph_type)
                    & (tables["graph_features"]["n_particles"] == EXPECTED_N)
                ],
                run_id, graph_type, shared_times,
            )
            for graph_type in GRAPH_TYPES
        }
        runs.append({
            "id": run_id, "model": model, "material": material, "seed": seed,
            "particleIds": packed["particleIds"], "frames": packed["frames"],
            "graphs": graphs,
        })
    runs.sort(key=lambda r: (r["model"], r["material"], r["seed"]))
    _validate_parameters(tables["parameters"], {run["id"]: run["model"] for run in runs})

    evidence = _evidence_rows(tables["candidates"])
    candidates = sum(1 for row in evidence if row["candidate"])
    if candidates != EXPECTED_CANDIDATES:
        raise ValueError(f"expected {EXPECTED_CANDIDATES} candidate rows, found {candidates}")

    return {
        "schemaVersion": 1,
        # One stored coordinate unit equals pmPerUnit picometres, so nm = value * pmPerUnit / 1000.
        "pmPerUnit": PM_PER_UNIT,
        "boxNm": BOX_NM,
        "radiusNm": RADIUS_NM,
        "timesSeconds": shared_times,
        "runs": runs,
        "evidence": evidence,
        "transitions": _transition_rows(tables["transitions"]),
        "returnCounts": _aggregate_return_counts(tables["metrics"]),
    }


def replace_data_block(html, payload):
    """Put compact JSON into the single marked block, leaving the rest untouched."""
    if html.count(BLOCK_START) != 1:
        raise ValueError("page must contain exactly one team2 data block")
    start = html.index(BLOCK_START) + len(BLOCK_START)
    end = html.index(BLOCK_END, start)
    body = json.dumps(payload, allow_nan=False, separators=(",", ":"))
    # Keep the block closed where HTML tokenisation would otherwise reopen it.
    body = body.replace("</", "<\\/").replace("<!", "<\\u0021")
    return html[:start] + body + html[end:]


def main():
    repo_root = Path(__file__).resolve().parents[2]
    target = repo_root / "team2_macrostates" / "interactive" / "index.html"
    if not target.is_file():
        raise ValueError(f"missing page to update: {target}")
    payload = build_interactive_data(repo_root)
    updated = replace_data_block(target.read_text(encoding="utf-8"), payload)
    temp = target.with_name(target.name + ".tmp")
    temp.write_text(updated, encoding="utf-8")
    temp.replace(target)
    print(
        f"updated {target}: {len(payload['runs'])} runs x {len(payload['timesSeconds'])} frames, "
        f"{len(GRAPH_TYPES)} graphs per run, {len(payload['evidence'])} evidence rows, "
        f"{sum(1 for row in payload['evidence'] if row['candidate'])} candidates, "
        f"{target.stat().st_size / 1e6:.1f} MB"
    )


if __name__ == "__main__":
    main()
