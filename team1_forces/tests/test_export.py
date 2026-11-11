import numpy as np
import pandas as pd
import pytest

from src.export import export_run, make_run_id

POSITIONS_COLS = ["run_id", "seed", "t", "particle_id", "x", "y",
                  "model_type", "A_H", "lambda_D", "noise", "T"]
PAIRS_COLS = ["run_id", "seed", "t", "i", "j", "L_nm", "contact_zone", "force_mode"]
CLUSTER_COLS = ["run_id", "seed", "t", "largest_cluster", "mean_degree",
                "n_edges", "n_components"]
PARAMS_COLS = ["run_id", "model_type", "R_nm", "A_H", "salt_mM", "L_ret_nm",
               "p_ret", "dt", "mobility", "diffusion"]


def make_frames():
    """Zwei Frames mit n=3: ein nahes Paar (far_gap) und ein getrenntes Paar."""
    positions1 = np.array([[5e-6, 5e-6], [5e-6 + 2 * 500e-9 + 40e-9, 5e-6], [15e-6, 15e-6]])
    positions2 = positions1 + 1e-9
    pair_rows1 = [(0, 1, 40e-9, "far_gap"), (0, 2, 1e-5, "separated"), (1, 2, 1e-5, "separated")]
    pair_rows2 = pair_rows1
    return [(1e-7, positions1, pair_rows1), (2e-7, positions2, pair_rows2)]


def test_columns_exact(tmp_path):
    export_run(out_dir=tmp_path, run_id="r1", frames=make_frames())
    for name, cols in [
        ("positions.csv", POSITIONS_COLS),
        ("pairs.csv", PAIRS_COLS),
        ("cluster_metrics.csv", CLUSTER_COLS),
        ("parameters.csv", PARAMS_COLS),
    ]:
        df = pd.read_csv(tmp_path / name)
        assert list(df.columns) == cols, name


def test_two_runs_append(tmp_path):
    export_run(out_dir=tmp_path, run_id="run_a", seed=1, frames=make_frames())
    export_run(out_dir=tmp_path, run_id="run_b", seed=2, frames=make_frames())
    pos = pd.read_csv(tmp_path / "positions.csv")
    params = pd.read_csv(tmp_path / "parameters.csv")
    assert len(pos) == 2 * 2 * 3  # 2 Runs x 2 Frames x 3 Partikel
    assert set(pos.run_id) == {"run_a", "run_b"}
    assert len(params) == 2
    assert set(params.run_id) == {"run_a", "run_b"}
    assert set(pos.seed) == {1, 2}


def test_pairs_filter(tmp_path):
    export_run(out_dir=tmp_path, run_id="r1", frames=make_frames())
    pairs = pd.read_csv(tmp_path / "pairs.csv")
    zones = set(pairs.contact_zone)
    assert "far_gap" in zones
    assert "separated" not in zones
    assert np.isclose(pairs.L_nm.iloc[0], 40.0)
    # jede Paarzeile trägt den Modus
    assert set(pairs.force_mode) == {"dlvo"}


def test_run_id_format():
    assert make_run_id("cl_retarded", 5e-21, 100, 50, 42) == "cl_retarded_A5.0e-21_I100_N50_s42"
    assert make_run_id("dlvo", 0.5e-21, 50, 20, 0) == "dlvo_A5.0e-22_I50_N20_s0"


def test_empty_frames_writes_parameters_only(tmp_path):
    # frames weggelassen (= leerer Run) darf nicht abstürzen
    paths = export_run(out_dir=tmp_path, run_id="r_empty")
    params = pd.read_csv(tmp_path / "parameters.csv")
    assert params.run_id.item() == "r_empty"
    pos = pd.read_csv(tmp_path / "positions.csv")
    assert len(pos) == 0