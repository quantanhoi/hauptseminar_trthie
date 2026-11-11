"""Übergabeformat an Team 2 (§17): positions, pairs, cluster_metrics, parameters.

Alle Dateien werden im Append-Modus geschrieben: ein Aufruf = ein Run,
mehrere Runs landen in denselben Dateien (unterscheidbar über run_id).
"""

from pathlib import Path

import pandas as pd

from src.metrics import cluster_metrics

POSITIONS_COLUMNS = ["run_id", "seed", "t", "particle_id", "x", "y",
                     "model_type", "A_H", "lambda_D", "noise", "T"]
PAIRS_COLUMNS = ["run_id", "seed", "t", "i", "j", "L_nm", "contact_zone", "force_mode"]
CLUSTER_COLUMNS = ["run_id", "seed", "t", "largest_cluster", "mean_degree",
                   "n_edges", "n_components"]
PARAMS_COLUMNS = ["run_id", "model_type", "R_nm", "A_H", "salt_mM", "L_ret_nm",
                  "p_ret", "dt", "mobility", "diffusion"]


def make_run_id(model_type, A_H, salt_mM, n, seed):
    """Deterministische Run-ID aus den Parametern, z. B. dlvo_A5.0e-21_I100_N20_s42."""
    return f"{model_type}_A{A_H:.1e}_I{salt_mM:g}_N{n}_s{seed}"


def export_run(out_dir="data/processed", run_id="", seed=0, model_type="dlvo",
               A_H=5e-21, lambda_D=0.96e-9, noise=1e-16, T=298.15,
               R_nm=500.0, salt_mM=100, L_ret_nm=20.0, p_ret=2,
               dt=1e-7, mobility=1e8, diffusion=1e-16, frames=()):
    """Schreibt einen Run in die vier Team-2-CSVs.

    frames: Iterable von (t in Sekunden, Positionsarray (n,2) in Metern,
    pair_rows aus pair_distance_table()). pairs.csv erhält nur Paare mit
    zone != "separated" (L < 100 nm) — entfernte Paare kann Team 2 aus x, y
    selbst rekonstruieren.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pos_rows = []
    pair_out = []
    cl_rows = []
    for t, positions, pair_rows in frames:
        for pid, (x, y) in enumerate(positions):
            pos_rows.append({
                "run_id": run_id, "seed": seed, "t": t, "particle_id": pid,
                "x": x, "y": y, "model_type": model_type, "A_H": A_H,
                "lambda_D": lambda_D, "noise": noise, "T": T,
            })
        for i, j, L, zone in pair_rows:
            if zone == "separated":
                continue
            pair_out.append({
                "run_id": run_id, "seed": seed, "t": t, "i": i, "j": j,
                "L_nm": L / 1e-9, "contact_zone": zone, "force_mode": model_type,
            })
        cl_rows.append({
            "run_id": run_id, "seed": seed, "t": t,
            **cluster_metrics(pair_rows, len(positions)),
        })

    params_row = {
        "run_id": run_id, "model_type": model_type, "R_nm": R_nm, "A_H": A_H,
        "salt_mM": salt_mM, "L_ret_nm": L_ret_nm, "p_ret": p_ret,
        "dt": dt, "mobility": mobility, "diffusion": diffusion,
    }

    written = []
    for name, columns, rows in [
        ("positions.csv", POSITIONS_COLUMNS, pos_rows),
        ("pairs.csv", PAIRS_COLUMNS, pair_out),
        ("cluster_metrics.csv", CLUSTER_COLUMNS, cl_rows),
        ("parameters.csv", PARAMS_COLUMNS, [params_row]),
    ]:
        path = out_dir / name
        pd.DataFrame(rows, columns=columns).to_csv(
            path, mode="a", header=not path.exists(), index=False
        )
        written.append(path)
    return written