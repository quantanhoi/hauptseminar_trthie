import json

import numpy as np
import pandas as pd
import pytest

from interactive.export_data import (
    _aggregate_return_counts,
    _nan_to_none,
    _positions_to_pm,
    _validate_run_frames,
    replace_data_block,
)

BLOCK_START = '<script id="team2-data" type="application/json">'
BLOCK_END = "</script>"
HTML_SHELL = (
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    + BLOCK_START + "\n{}\n" + BLOCK_END
    + '\n</head>\n<body><h1>page</h1></body>\n</html>\n'
)


def _position_rows(*, run_id="r0", seed=0, model_type="vdw_only", A_H=5e-21, rows=None):
    if rows is None:
        rows = [
            (1e-7, 1, 5e-6, 5e-6),
            (1e-7, 2, 6e-6, 5e-6),
            (2e-7, 1, 5.5e-6, 5e-6),
            (2e-7, 2, 6.5e-6, 5e-6),
            (3e-7, 1, 6e-6, 5e-6),
            (3e-7, 2, 7e-6, 5e-6),
        ]
    return [
        {
            "run_id": run_id, "seed": seed, "t": t, "particle_id": pid,
            "x": x, "y": y, "model_type": model_type, "A_H": A_H,
            "lambda_D": 0.96e-9, "noise": 1e-16, "T": 298.15,
        }
        for t, pid, x, y in rows
    ]


def test_positions_to_pm_converts_metres_and_orders_particles():
    frame = pd.DataFrame(_position_rows(rows=[
        (1e-7, 2, 3e-9, 4e-9),
        (1e-7, 10, 1e-9, -2e-9),
        (2e-7, 10, 5e-9, 6e-9),
        (2e-7, 2, 7e-9, 8e-9),
    ]))
    packed = _positions_to_pm(frame)
    assert packed["particleIds"] == [2, 10]
    assert packed["timesSeconds"] == [1e-7, 2e-7]
    assert packed["frames"][0] == {"xPm": [30000, 10000], "yPm": [40000, -20000]}
    assert packed["frames"][1] == {"xPm": [70000, 50000], "yPm": [80000, 60000]}


def test_positions_to_pm_rejects_non_finite_positions():
    rows = _position_rows()
    rows[1]["x"] = np.nan
    with pytest.raises(ValueError, match="finite"):
        _positions_to_pm(pd.DataFrame(rows))


def test_validate_run_frames_accepts_complete_small_fixture():
    _validate_run_frames(
        pd.DataFrame(_position_rows()), expected_frames=3, expected_particles=2
    )


def test_validate_run_frames_rejects_duplicate_time_particle():
    rows = _position_rows()
    rows.append(dict(rows[0]))
    with pytest.raises(ValueError, match="duplicate"):
        _validate_run_frames(
            pd.DataFrame(rows), expected_frames=3, expected_particles=2
        )


def test_validate_run_frames_rejects_missing_particle():
    rows = _position_rows()
    del rows[3]
    with pytest.raises(ValueError, match="particles"):
        _validate_run_frames(
            pd.DataFrame(rows), expected_frames=3, expected_particles=2
        )


def test_validate_run_frames_rejects_non_finite_coordinate():
    rows = _position_rows()
    rows[4]["y"] = np.inf
    with pytest.raises(ValueError, match="finite"):
        _validate_run_frames(
            pd.DataFrame(rows), expected_frames=3, expected_particles=2
        )


def test_validate_run_frames_rejects_inconsistent_run_metadata():
    rows = _position_rows()
    rows[2]["seed"] = 1
    with pytest.raises(ValueError, match="metadata"):
        _validate_run_frames(
            pd.DataFrame(rows), expected_frames=3, expected_particles=2
        )


def test_validate_run_frames_rejects_wrong_frame_count():
    with pytest.raises(ValueError, match="frames"):
        _validate_run_frames(
            pd.DataFrame(_position_rows()), expected_frames=4, expected_particles=2
        )


def _metrics_rows():
    def row(sequence_type, n_particles, eligible, returns):
        return {
            "run_id": f"run_{sequence_type}_{n_particles}", "seed": 0,
            "model_type": "vdw_only", "material_type": "PMBC",
            "n_particles": n_particles, "graph_type": "hard",
            "sequence_type": sequence_type, "state": "dimer_dominated",
            "return_eligible_T50": eligible, "returns_T50": returns,
        }
    return [
        row("filtered", 20, 1, 0),
        row("filtered", 20, 2, 1),
        row("raw", 20, 5, 5),
        row("filtered", 50, 7, 7),
    ]


def test_aggregate_return_counts_pools_filtered_n20_only():
    counts = _aggregate_return_counts(pd.DataFrame(_metrics_rows()))
    assert counts == [{
        "model": "vdw_only", "material": "PMBC", "graph": "hard",
        "state": "dimer_dominated", "eligible50": 3, "returns50": 1,
    }]


def test_aggregate_return_counts_keeps_zero_eligible_as_zero():
    rows = [r for r in _metrics_rows() if r["sequence_type"] == "filtered" and r["n_particles"] == 20]
    rows[0]["return_eligible_T50"] = 0
    rows[0]["returns_T50"] = 0
    counts = _aggregate_return_counts(pd.DataFrame(rows))
    assert counts[0]["eligible50"] == 2
    assert counts[0]["returns50"] == 1


def test_nan_becomes_none_and_json_stays_finite():
    assert _nan_to_none(float("nan")) is None
    assert _nan_to_none(None) is None
    assert _nan_to_none(0.0) == 0.0
    body = json.dumps(
        {"probability": _nan_to_none(float("nan")), "zero": 0.0}, allow_nan=False
    )
    assert json.loads(body) == {"probability": None, "zero": 0.0}
    assert "NaN" not in body
    with pytest.raises(ValueError):
        json.dumps({"probability": float("nan")}, allow_nan=False)


def test_replace_data_block_replaces_only_the_json_block():
    generated = replace_data_block(HTML_SHELL.format("{}"), {"runs": [1, 2]})
    assert generated.startswith(HTML_SHELL.split(BLOCK_START)[0])
    assert generated.endswith(HTML_SHELL.split(BLOCK_END)[1])
    inner = generated.split(BLOCK_START, 1)[1].split(BLOCK_END, 1)[0]
    assert json.loads(inner) == {"runs": [1, 2]}


def test_replace_data_block_escapes_closing_script_tag():
    generated = replace_data_block(
        HTML_SHELL.format("{}"), {"note": "close </script> here"}
    )
    assert "</script>" not in generated.split(BLOCK_START, 1)[1].split(BLOCK_END, 1)[0]
    assert "<\\/script>" in generated
    inner = generated.split(BLOCK_START, 1)[1].split(BLOCK_END, 1)[0]
    assert json.loads(inner)["note"] == "close </script> here"


def test_replace_data_block_rejects_missing_block():
    with pytest.raises(ValueError, match="data block"):
        replace_data_block("<html><body>none</body></html>", {"a": 1})


def test_replace_data_block_rejects_duplicate_block():
    html = HTML_SHELL.format("{}") + HTML_SHELL.format("{}")
    with pytest.raises(ValueError, match="data block"):
        replace_data_block(html, {"a": 1})


from interactive.export_data import (  # noqa: E402
    _evidence_rows,
    _graph_block,
    _validate_parameters,
    _validate_run_selection,
)


def _selection_rows():
    rows = []
    for model in ("vdw_only", "dlvo_classic", "cl_retarded"):
        for material in ("PMBC", "fatty_acid"):
            for seed in (0, 1, 42):
                rows.append({
                    "run_id": f"{model}_{material}_{seed}", "model_type": model,
                    "material_type": material, "seed": seed,
                })
    return pd.DataFrame(rows)


def test_run_selection_must_cover_six_pairs_by_three_seeds():
    _validate_run_selection(_selection_rows())
    broken = _selection_rows()
    broken.loc[0, "seed"] = 1
    with pytest.raises(ValueError, match="selection"):
        _validate_run_selection(broken)


def _graph_frames(times):
    sequence = pd.DataFrame({
        "run_id": "r0", "seed": 0, "model_type": "vdw_only", "material_type": "PMBC",
        "n_particles": 20, "graph_type": "hard", "time": times,
        "macrostate_raw": ["monomer_gas"] * len(times),
        "macrostate_filtered": ["monomer_gas"] * len(times),
        "largest_cluster": [1] * len(times), "number_of_components": [20] * len(times),
        "number_of_edges": [0] * len(times), "mean_degree": [0.0] * len(times),
    })
    features = pd.DataFrame({
        "run_id": "r0", "graph_type": "hard", "n_particles": 20, "time": times,
        "largest_cluster": [1] * len(times), "number_of_components": [20] * len(times),
        "number_of_edges": [0] * len(times), "mean_degree": [0.0] * len(times),
        "cluster_size_distribution": ["1;1;1"] * len(times),
    })
    return sequence, features


def test_graph_block_rejects_duplicate_and_misaligned_times():
    times = [float(index) for index in range(1000)]
    duplicated = list(times)
    duplicated[1] = duplicated[0]
    sequence, features = _graph_frames(duplicated)
    with pytest.raises(ValueError, match="duplicate sequence time"):
        _graph_block(sequence, features, "r0", "hard", times)
    misaligned = list(times)
    misaligned[-1] = 5000.0
    sequence, features = _graph_frames(misaligned)
    with pytest.raises(ValueError, match="position grid"):
        _graph_block(sequence, features, "r0", "hard", times)
    sequence, features = _graph_frames(times)
    block = _graph_block(sequence, features, "r0", "hard", times)
    assert block["raw"] == ["monomer_gas"] * 1000


def test_parameters_are_checked_only_for_the_embedded_runs():
    parameters = pd.DataFrame({
        "run_id": ["a", "b", "n50"], "model_type": ["vdw", "vdw", "vdw"],
        "R_nm": [500.0, 500.0, 500.0], "dt": [1e-7, 1e-7, 1e-7],
    })
    _validate_parameters(parameters, {"a": "vdw_only", "b": "vdw_only"})
    wrong_radius = parameters.copy()
    wrong_radius.loc[0, "R_nm"] = 499.0
    with pytest.raises(ValueError, match="R_nm"):
        _validate_parameters(wrong_radius, {"a": "vdw_only", "b": "vdw_only"})
    duplicated = pd.concat([parameters, parameters.iloc[[0]]])
    with pytest.raises(ValueError, match="duplicate"):
        _validate_parameters(duplicated, {"a": "vdw_only", "b": "vdw_only"})


def _candidate_row(**overrides):
    row = {
        "n_particles": 20, "model_type": "vdw_only", "material_type": "PMBC",
        "graph_type": "meso", "state": "large_cluster", "frequency": 0.6,
        "mean_dwell_steps": 10.0, "return_probability_T50": 0.5,
        "mean_return_steps_T200": 20.0, "seed_count": 3, "total_seeds": 3,
        "label_agreement": 0.9, "frequency_ok": True, "mean_dwell_ok": True,
        "return_probability_ok": True, "seed_reproducibility": True,
        "label_agreement_ok": True, "candidate": True,
    }
    row.update(overrides)
    return row


def test_missing_candidate_flag_stays_unavailable_not_a_candidate():
    rows = _evidence_rows(pd.DataFrame([
        _candidate_row(),
        _candidate_row(state="tetra_like", candidate=np.nan),
    ]))
    by_state = {row["state"]: row["candidate"] for row in rows}
    assert by_state["large_cluster"] is True
    assert by_state["tetra_like"] is None
