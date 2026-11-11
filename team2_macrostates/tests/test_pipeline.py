from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.pipeline import (
    TEAM3_COLUMNS,
    analyze_run,
    export_team3,
    load_team1_data,
    run_pipeline,
)

POSITION_COLUMNS = [
    "run_id", "seed", "t", "particle_id", "x", "y", "model_type",
    "A_H", "lambda_D", "noise", "T",
]
PARAMETER_COLUMNS = [
    "run_id", "model_type", "R_nm", "A_H", "salt_mM", "L_ret_nm",
    "p_ret", "dt", "mobility", "diffusion",
]


def _frames(run_id, seed, model_type, A_H, gap_nm):
    rows = []
    for index, gap in enumerate(gap_nm):
        positions = {
            10: 5e-6,
            20: 5e-6 + 1000e-9 + gap * 1e-9,
            30: 15e-6,
        }
        for particle_id in [10, 20, 30]:
            rows.append({
                "run_id": run_id, "seed": seed, "t": (index + 1) * 1e-7,
                "particle_id": particle_id, "x": positions[particle_id],
                "y": 5e-6, "model_type": model_type, "A_H": A_H,
                "lambda_D": 0.96e-9, "noise": 1e-16, "T": 298.15,
            })
    return rows


def _parameters(run_id, model_type, A_H):
    return {
        "run_id": run_id, "model_type": model_type, "R_nm": 500.0,
        "A_H": A_H, "salt_mM": 100, "L_ret_nm": 20.0, "p_ret": 2,
        "dt": 1e-7, "mobility": 1e8, "diffusion": 1e-16,
    }


def _write_dataset(directory, include_dlvo=True):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rows = _frames("vdw_run", 7, "vdw", 0.5e-21, [1, 1, 1, 1])
    parameters = [_parameters("vdw_run", "vdw", 0.5e-21)]
    if include_dlvo:
        rows += _frames("dlvo_run", 8, "dlvo", 5e-21, [7, 7, 7, 7])
        parameters.append(_parameters("dlvo_run", "dlvo", 5e-21))
    pd.DataFrame(rows, columns=POSITION_COLUMNS).to_csv(directory / "positions.csv", index=False)
    pd.DataFrame(parameters, columns=PARAMETER_COLUMNS).to_csv(directory / "parameters.csv", index=False)


def test_load_team1_data_validates_units_and_canonicalizes_metadata(tmp_path):
    _write_dataset(tmp_path)
    positions, parameters = load_team1_data(tmp_path)
    assert "time" in positions and "t" not in positions
    assert "temperature" in positions and "T" not in positions
    assert set(positions.model_type) == {"vdw_only", "dlvo_classic"}
    materials = positions.groupby("run_id").material_type.first().to_dict()
    assert materials == {"vdw_run": "fatty_acid", "dlvo_run": "PMBC"}
    assert (positions.R_nm == 500.0).all()
    assert (positions.salt_mM == 100).all()
    assert (positions.box_m == 20e-6).all()
    assert len(parameters) == 2


def test_unknown_hamaker_constant_is_not_assigned_a_material(tmp_path):
    _write_dataset(tmp_path, include_dlvo=False)
    path = tmp_path / "positions.csv"
    positions = pd.read_csv(path)
    positions["A_H"] = 2e-21
    positions.to_csv(path, index=False)
    loaded, _ = load_team1_data(tmp_path)
    assert set(loaded.material_type) == {"unknown"}


def test_analyze_run_reuses_pairs_and_preserves_real_particle_ids(tmp_path):
    _write_dataset(tmp_path)
    positions, _ = load_team1_data(tmp_path)
    run = positions[positions.run_id == "vdw_run"]
    pairs, features, sequences = analyze_run(run, min_dwell=2)
    assert len(pairs) == 4
    assert set(zip(pairs.i, pairs.j)) == {(10, 20)}
    assert np.allclose(pairs.L_nm, 1.0)
    assert set(pairs.zone) == {"hard_contact"}
    assert len(features) == 4 * 3
    assert set(features.graph_type) == {"hard", "near", "meso"}
    assert set(features.largest_cluster) == {2}
    assert features.cluster_size_distribution.str.contains(";").all()
    assert len(sequences) == 4 * 3
    assert set(sequences.macrostate_raw) == {"dimer_dominated"}
    pd.testing.assert_series_equal(
        sequences.macrostate_raw, sequences.macrostate_filtered,
        check_names=False,
    )


def test_graph_variants_differ_for_near_gap_pair(tmp_path):
    _write_dataset(tmp_path)
    positions, _ = load_team1_data(tmp_path)
    run = positions[positions.run_id == "dlvo_run"]
    pairs, _, sequences = analyze_run(run, min_dwell=2)
    assert set(pairs.zone) == {"near_gap"}
    labels = sequences.groupby("graph_type").macrostate_raw.first().to_dict()
    assert labels == {
        "hard": "monomer_gas", "near": "dimer_dominated", "meso": "dimer_dominated"
    }


def test_export_team3_has_exact_schema_and_meso_rows(tmp_path):
    _write_dataset(tmp_path)
    positions, _ = load_team1_data(tmp_path)
    _, _, sequences = analyze_run(positions[positions.run_id == "vdw_run"])
    output = tmp_path / "team3.csv"
    exported = export_team3(sequences, output)
    assert list(exported.columns) == TEAM3_COLUMNS
    assert len(exported) == 4
    assert output.exists()
    assert set(exported.model_type) == {"vdw_only"}
    assert set(exported.material_type) == {"fatty_acid"}
    assert (exported.largest_cluster == 2).all()


def test_run_pipeline_writes_stable_outputs(tmp_path):
    _write_dataset(tmp_path)
    outputs = run_pipeline(tmp_path, tmp_path / "out", min_dwell=2)
    assert set(outputs) == {"pair_zones", "graph_features", "macrostate_sequences"}
    for name in outputs:
        assert (tmp_path / "out" / f"{name}.csv").exists()
    assert len(outputs["pair_zones"]) == 8
    assert len(outputs["macrostate_sequences"]) == 24


def test_all_separated_run_has_empty_pairs_and_monomer_sequences(tmp_path):
    _write_dataset(tmp_path, include_dlvo=False)
    path = tmp_path / "positions.csv"
    positions = pd.read_csv(path)
    positions["x"] = positions.particle_id.map({10: 1e-6, 20: 5e-6, 30: 10e-6})
    positions.to_csv(path, index=False)
    loaded, _ = load_team1_data(tmp_path)
    pairs, features, sequences = analyze_run(loaded, box=None)
    assert pairs.empty
    assert list(pairs.columns) == [
        "run_id", "seed", "time", "i", "j", "L_m", "L_nm", "zone",
        "model_type", "material_type",
    ]
    assert set(features.largest_cluster) == {1}
    assert set(sequences.macrostate_raw) == {"monomer_gas"}


def test_missing_column_is_rejected(tmp_path):
    _write_dataset(tmp_path, include_dlvo=False)
    path = tmp_path / "positions.csv"
    pd.read_csv(path).drop(columns="x").to_csv(path, index=False)
    with pytest.raises(ValueError, match="positions"):
        load_team1_data(tmp_path)


def test_duplicate_frame_particle_is_rejected(tmp_path):
    _write_dataset(tmp_path, include_dlvo=False)
    path = tmp_path / "positions.csv"
    positions = pd.read_csv(path)
    pd.concat([positions, positions.iloc[[0]]]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Duplicate"):
        load_team1_data(tmp_path)


def test_nonfinite_position_is_rejected(tmp_path):
    _write_dataset(tmp_path, include_dlvo=False)
    path = tmp_path / "positions.csv"
    positions = pd.read_csv(path)
    positions.loc[0, "x"] = np.nan
    positions.to_csv(path, index=False)
    with pytest.raises(ValueError, match="finite"):
        load_team1_data(tmp_path)


def test_inconsistent_particle_set_is_rejected(tmp_path):
    _write_dataset(tmp_path, include_dlvo=False)
    path = tmp_path / "positions.csv"
    positions = pd.read_csv(path)
    positions = positions[~((positions.t == 2e-7) & (positions.particle_id == 30))]
    positions.to_csv(path, index=False)
    with pytest.raises(ValueError, match="particle set"):
        load_team1_data(tmp_path)


def test_nonpositive_radius_is_rejected(tmp_path):
    _write_dataset(tmp_path, include_dlvo=False)
    path = tmp_path / "parameters.csv"
    parameters = pd.read_csv(path)
    parameters["R_nm"] = 0.0
    parameters.to_csv(path, index=False)
    with pytest.raises(ValueError, match="R_nm"):
        load_team1_data(tmp_path)
