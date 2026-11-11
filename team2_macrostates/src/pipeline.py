"""Team-1-CSV-Validierung und reproduzierbare Team-2-Analyse."""

from pathlib import Path

import numpy as np
import pandas as pd

from src.contact_graphs import contact_graph, graph_features, pair_table
from src.macrostates import macrostate_from_graph
from src.sequences import filter_short_states

GRAPH_TYPES = ("hard", "near", "meso")
MODEL_ALIASES = {
    "vdw": "vdw_only",
    "vdw_only": "vdw_only",
    "dlvo": "dlvo_classic",
    "dlvo_classic": "dlvo_classic",
    "cl_retarded": "cl_retarded",
}
PAIR_OUTPUT_COLUMNS = [
    "run_id", "seed", "time", "i", "j", "L_m", "L_nm", "zone",
    "model_type", "material_type",
]
FEATURE_COLUMNS = [
    "run_id", "seed", "time", "graph_type", "model_type", "material_type",
    "A_H", "salt_mM", "noise", "temperature", "R_nm", "largest_cluster",
    "number_of_components", "number_of_edges", "mean_degree",
    "cluster_size_distribution",
]
SEQUENCE_COLUMNS = [
    "run_id", "seed", "time", "graph_type", "macrostate_raw",
    "macrostate_filtered", "model_type", "material_type", "A_H", "salt_mM",
    "noise", "temperature", "R_nm", "largest_cluster", "mean_degree",
    "number_of_edges", "number_of_components",
]
TEAM3_COLUMNS = [
    "run_id", "seed", "time", "macrostate_raw", "macrostate_filtered",
    "model_type", "material_type", "A_H", "salt_mM", "noise",
    "largest_cluster", "mean_degree",
]


def _material_type(A_H):
    if np.isclose(A_H, 0.5e-21, rtol=1e-9, atol=0.0):
        return "fatty_acid"
    if np.isclose(A_H, 5e-21, rtol=1e-9, atol=0.0):
        return "PMBC"
    return "unknown"


def _validate_particle_sets(run):
    expected = None
    for _, frame in run.groupby("time", sort=True):
        particle_ids = tuple(sorted(frame.particle_id.tolist()))
        if expected is None:
            expected = particle_ids
        elif particle_ids != expected:
            raise ValueError("Inconsistent particle set within run")


def load_team1_data(input_dir, box=20e-6):
    """Load Team-1 SI data, canonicalize labels, and attach run parameters."""
    if box <= 0:
        raise ValueError("box must be positive")
    input_dir = Path(input_dir)
    positions = pd.read_csv(input_dir / "positions.csv")
    parameters = pd.read_csv(input_dir / "parameters.csv")
    time_column = "t" if "t" in positions.columns else "time"
    required_positions = {
        "run_id", "seed", time_column, "particle_id", "x", "y",
        "model_type", "A_H", "lambda_D", "noise", "T",
    }
    missing = required_positions - set(positions.columns)
    if missing:
        raise ValueError(f"positions.csv missing columns: {sorted(missing)}")
    missing_parameters = {"run_id", "R_nm", "salt_mM"} - set(parameters.columns)
    if missing_parameters:
        raise ValueError(f"parameters.csv missing columns: {sorted(missing_parameters)}")
    if positions.duplicated(["run_id", time_column, "particle_id"]).any():
        raise ValueError("Duplicate (run_id, time, particle_id) row")
    if parameters.run_id.duplicated().any():
        raise ValueError("Duplicate run_id in parameters.csv")

    coordinate_columns = ["x", "y"] + (["z"] if "z" in positions else [])
    if not np.all(np.isfinite(positions[coordinate_columns].to_numpy())):
        raise ValueError("positions must be finite")
    if not np.all(np.isfinite(parameters.R_nm)) or (parameters.R_nm <= 0).any():
        raise ValueError("R_nm must be finite and positive")

    metadata_columns = ["seed", "model_type", "A_H", "lambda_D", "noise", "T"]
    metadata_counts = positions.groupby("run_id")[metadata_columns].nunique(dropna=False)
    if (metadata_counts > 1).any().any():
        raise ValueError("Run metadata must be constant within each run")

    positions = positions.rename(columns={time_column: "time", "T": "temperature"})
    positions = positions.merge(
        parameters[["run_id", "R_nm", "salt_mM"]], on="run_id",
        how="left", validate="many_to_one",
    )
    if positions[["R_nm", "salt_mM"]].isna().any().any():
        raise ValueError("Every position run needs valid parameters")
    positions["model_type"] = positions.model_type.replace(MODEL_ALIASES)
    positions["material_type"] = positions.A_H.map(_material_type)
    positions["box_m"] = float(box)
    positions = positions.sort_values(
        ["run_id", "time", "particle_id"], ignore_index=True
    )
    for _, run in positions.groupby("run_id"):
        _validate_particle_sets(run)
    return positions, parameters


def analyze_run(df_run, box=20e-6, min_dwell=5):
    """Analyze one enriched run, computing each frame's pair distances once."""
    if df_run.empty:
        raise ValueError("df_run must not be empty")
    if df_run.run_id.nunique() != 1:
        raise ValueError("analyze_run expects exactly one run_id")
    required = set(SEQUENCE_COLUMNS) - {"graph_type", "macrostate_raw", "macrostate_filtered"}
    required -= {"largest_cluster", "mean_degree", "number_of_edges", "number_of_components"}
    missing = required - set(df_run.columns)
    if missing:
        raise ValueError(f"df_run missing columns: {sorted(missing)}")
    if box is not None and box <= 0:
        raise ValueError("box must be positive or None")
    if not np.isfinite(df_run.R_nm.iloc[0]) or df_run.R_nm.iloc[0] <= 0:
        raise ValueError("R_nm must be finite and positive")
    _validate_particle_sets(df_run)

    first = df_run.iloc[0]
    base = {
        "run_id": first.run_id, "seed": first.seed,
        "model_type": first.model_type, "material_type": first.material_type,
        "A_H": first.A_H, "salt_mM": first.salt_mM, "noise": first.noise,
        "temperature": first.temperature, "R_nm": first.R_nm,
    }
    coordinate_columns = ["x", "y"] + (["z"] if "z" in df_run else [])
    pair_rows = []
    feature_rows = []
    raw_labels = {graph_type: [] for graph_type in GRAPH_TYPES}
    sequence_bases = {graph_type: [] for graph_type in GRAPH_TYPES}

    for time, frame in df_run.groupby("time", sort=True):
        frame = frame.sort_values("particle_id")
        particle_ids = frame.particle_id.tolist()
        positions = frame[coordinate_columns].to_numpy(dtype=float)
        pairs = pair_table(positions, particle_ids, R=first.R_nm * 1e-9, box=box)
        for row in pairs[pairs.zone != "separated"].itertuples(index=False):
            pair_rows.append({
                "run_id": first.run_id, "seed": first.seed, "time": time,
                "i": row.i, "j": row.j, "L_m": row.L_m, "L_nm": row.L_nm,
                "zone": row.zone, "model_type": first.model_type,
                "material_type": first.material_type,
            })
        for graph_type in GRAPH_TYPES:
            graph = contact_graph(pairs, particle_ids, graph_type=graph_type)
            features = graph_features(graph)
            raw = macrostate_from_graph(graph)
            raw_labels[graph_type].append(raw)
            feature_rows.append({
                **base, "time": time, "graph_type": graph_type, **features,
                "cluster_size_distribution": ";".join(
                    str(size) for size in features["cluster_size_distribution"]
                ),
            })
            sequence_bases[graph_type].append({
                **base, "time": time, "graph_type": graph_type,
                "largest_cluster": features["largest_cluster"],
                "mean_degree": features["mean_degree"],
                "number_of_edges": features["number_of_edges"],
                "number_of_components": features["number_of_components"],
            })

    sequence_rows = []
    for graph_type in GRAPH_TYPES:
        filtered = filter_short_states(raw_labels[graph_type], min_dwell=min_dwell)
        for row, raw, filt in zip(
            sequence_bases[graph_type], raw_labels[graph_type], filtered
        ):
            sequence_rows.append({
                **row, "macrostate_raw": raw, "macrostate_filtered": filt,
            })

    return (
        pd.DataFrame(pair_rows, columns=PAIR_OUTPUT_COLUMNS),
        pd.DataFrame(feature_rows, columns=FEATURE_COLUMNS),
        pd.DataFrame(sequence_rows, columns=SEQUENCE_COLUMNS),
    )


def run_pipeline(input_dir, out_dir, box=20e-6, min_dwell=5):
    positions, _ = load_team1_data(input_dir, box=box)
    collected = {"pair_zones": [], "graph_features": [], "macrostate_sequences": []}
    for _, run in positions.groupby("run_id", sort=True):
        pairs, features, sequences = analyze_run(run, box=box, min_dwell=min_dwell)
        collected["pair_zones"].append(pairs)
        collected["graph_features"].append(features)
        collected["macrostate_sequences"].append(sequences)

    columns = {
        "pair_zones": PAIR_OUTPUT_COLUMNS,
        "graph_features": FEATURE_COLUMNS,
        "macrostate_sequences": SEQUENCE_COLUMNS,
    }
    outputs = {}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frames in collected.items():
        result = (
            pd.concat(frames, ignore_index=True)
            if frames else pd.DataFrame(columns=columns[name])
        )
        result.to_csv(out_dir / f"{name}.csv", index=False)
        outputs[name] = result
    return outputs


def select_filter_demo(sequences):
    """Pick the run/graph with the most raw-vs-filtered changes; tie-break stable."""
    missing = {'graph_type', 'run_id', 'macrostate_raw', 'macrostate_filtered'} - set(sequences.columns)
    if missing:
        raise ValueError(f"sequences missing columns: {sorted(missing)}")
    working = sequences.assign(
        changed=sequences.macrostate_raw != sequences.macrostate_filtered
    )
    counts = (
        working.groupby(['run_id', 'graph_type'], sort=True)
        .changed.sum().rename('changed').astype(int).reset_index()
    )
    if counts.empty:
        raise ValueError("A filter demo needs at least one sequence group")
    selection = counts.sort_values(
        ['changed', 'graph_type', 'run_id'], ascending=[False, True, True]
    ).iloc[0]
    return {
        'graph_type': selection.graph_type,
        'run_id': selection.run_id,
        'changed': int(selection.changed),
    }


def export_team3(sequences, out_path):
    """Write the default meso sequences in the exact §14 column order."""
    missing = set(TEAM3_COLUMNS + ["graph_type"]) - set(sequences.columns)
    if missing:
        raise ValueError(f"sequences missing columns: {sorted(missing)}")
    exported = sequences[sequences.graph_type == "meso"][TEAM3_COLUMNS].reset_index(drop=True)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    exported.to_csv(out_path, index=False)
    return exported
