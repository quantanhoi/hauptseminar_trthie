import numpy as np
import pandas as pd
import pytest

from src.sequences import (
    attractor_candidate,
    dwell_runs,
    filter_short_states,
    normalize_transition_counts,
    return_summary,
    transition_counts,
)


def test_internal_short_run_extends_previous_valid_state():
    sequence = ["a"] * 5 + ["b"] * 2 + ["c"] * 5
    assert filter_short_states(sequence, min_dwell=5) == ["a"] * 7 + ["c"] * 5


def test_leading_short_run_uses_next_valid_state():
    sequence = ["b"] * 2 + ["a"] * 5 + ["c"] * 5
    assert filter_short_states(sequence, min_dwell=5) == ["a"] * 7 + ["c"] * 5


def test_trailing_short_run_uses_previous_valid_state():
    assert filter_short_states(["a"] * 5 + ["b"] * 2, min_dwell=5) == ["a"] * 7


def test_all_short_runs_become_mixed_transition():
    assert filter_short_states(["a"] * 2 + ["b"] * 2, min_dwell=5) == [
        "mixed_transition"
    ] * 4


def test_min_dwell_one_preserves_sequence_and_empty_input():
    sequence = ["a", "b", "a"]
    assert filter_short_states(sequence, min_dwell=1) == sequence
    assert filter_short_states([], min_dwell=5) == []
    with pytest.raises(ValueError):
        filter_short_states(sequence, min_dwell=0)


def test_dwell_runs_include_censoring_and_sample_based_seconds():
    runs = dwell_runs(["a", "a", "b", "a"], [0.0, 2.0, 5.0, 9.0])
    assert list(runs.columns) == [
        "state", "start_index", "end_index", "start_time", "end_time",
        "dwell_steps", "dwell_seconds", "left_censored", "right_censored",
    ]
    assert runs["state"].tolist() == ["a", "b", "a"]
    assert runs["dwell_steps"].tolist() == [2, 1, 1]
    assert runs["dwell_seconds"].tolist() == [6.0, 3.0, 3.0]
    assert runs["start_time"].tolist() == [0.0, 5.0, 9.0]
    assert runs["end_time"].tolist() == [2.0, 5.0, 9.0]
    assert runs["left_censored"].tolist() == [True, False, False]
    assert runs["right_censored"].tolist() == [False, False, True]


def test_dwell_runs_empty_and_invalid_times():
    assert dwell_runs([], []).empty
    with pytest.raises(ValueError):
        dwell_runs(["a"], [0.0, 1.0])
    with pytest.raises(ValueError):
        dwell_runs(["a", "b"], [1.0, 0.0])


def test_transition_counts_and_normalization_include_zero_outgoing_state():
    counts = transition_counts(["a", "a", "b", "a"], states=["a", "b", "c"])
    assert counts.loc["a", "a"] == 1
    assert counts.loc["a", "b"] == 1
    assert counts.loc["b", "a"] == 1
    assert counts.loc["c"].sum() == 0
    probabilities = normalize_transition_counts(counts)
    assert probabilities.loc["a", "a"] == pytest.approx(0.5)
    assert probabilities.loc["a", "b"] == pytest.approx(0.5)
    assert probabilities.loc["b", "a"] == pytest.approx(1.0)
    assert probabilities.loc["b", "b"] == 0
    assert probabilities.loc["c"].isna().all()


def test_transition_counts_reject_sequence_states_missing_from_catalogue():
    with pytest.raises(ValueError):
        transition_counts(["a", "b"], states=["a"])


def test_return_summary_excludes_truncated_departure():
    result = return_summary(
        ["a", "b", "a", "b"], [0.0, 1.0, 3.0, 6.0], "a", horizon=2
    )
    assert result["eligible_departures"] == 1
    assert result["returns"] == 1
    assert result["return_probability"] == 1.0
    assert result["mean_return_steps"] == 2.0
    assert result["mean_return_seconds"] == 3.0


def test_return_summary_without_complete_window_is_not_a_failure():
    result = return_summary(["a", "b"], [0.0, 1.0], "a", horizon=2)
    assert result["eligible_departures"] == 0
    assert result["returns"] == 0
    assert np.isnan(result["return_probability"])
    assert np.isnan(result["mean_return_steps"])
    assert np.isnan(result["mean_return_seconds"])


def test_return_summary_eligible_nonreturn_has_zero_probability_and_nan_mean():
    result = return_summary(["a", "b", "b", "c"], [0, 1, 2, 3], "a", horizon=2)
    assert result["eligible_departures"] == 1
    assert result["returns"] == 0
    assert result["return_probability"] == 0.0
    assert np.isnan(result["mean_return_steps"])


def test_return_summary_rejects_invalid_horizon_and_unsorted_times():
    with pytest.raises(ValueError):
        return_summary(["a"], [0], "a", horizon=0)
    with pytest.raises(ValueError):
        return_summary(["a", "b"], [1, 0], "a", horizon=1)


def test_attractor_candidate_passes_all_seminar_heuristics():
    result = attractor_candidate(0.1, 6, 0.4, 3, 0.8, total_seeds=3)
    assert result == {
        "frequency_ok": True,
        "mean_dwell_ok": True,
        "return_probability_ok": True,
        "seed_reproducibility": True,
        "label_agreement_ok": True,
        "candidate": True,
    }


@pytest.mark.parametrize(
    ("frequency", "dwell", "return_probability", "agreement"),
    [(0.05, 6, 0.4, 0.8), (0.1, 5, 0.4, 0.8), (0.1, 6, 0.3, 0.8), (0.1, 6, 0.4, 0.7)],
)
def test_attractor_candidate_strict_thresholds_do_not_pass(
    frequency, dwell, return_probability, agreement
):
    assert not attractor_candidate(
        frequency, dwell, return_probability, 3, agreement, total_seeds=3
    )["candidate"]


def test_attractor_candidate_distinguishes_unavailable_and_failed_seed_evidence():
    one_seed = attractor_candidate(0.1, 6, 0.4, 1, 0.8, total_seeds=1)
    assert one_seed["seed_reproducibility"] is None
    assert one_seed["candidate"] is False
    rare_across_three = attractor_candidate(0.1, 6, 0.4, 1, 0.8, total_seeds=3)
    assert rare_across_three["seed_reproducibility"] is False
    assert rare_across_three["candidate"] is False


def test_attractor_candidate_nan_is_unavailable_and_cannot_pass():
    result = attractor_candidate(0.1, np.nan, 0.4, 3, 0.8, total_seeds=3)
    assert result["mean_dwell_ok"] is None
    assert result["candidate"] is False
