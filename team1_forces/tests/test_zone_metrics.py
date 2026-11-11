import numpy as np
import pytest

from src.metrics import (
    dwell_times,
    escape_time,
    return_probability,
    contact_probability,
)


def test_dwell_times():
    seq = ["near_gap"] * 3 + ["meso_gap"] * 2 + ["near_gap"]
    assert dwell_times(seq, "near_gap") == [3, 1]
    assert dwell_times(seq, "meso_gap") == [2]
    assert dwell_times(seq, "hard_contact") == []


def test_escape_time():
    assert escape_time(["meso_gap"] * 5 + ["far_gap"] * 4) == 5
    assert escape_time(["meso_gap"] * 10) is None
    assert escape_time([]) is None


def test_return_probability():
    seq = ["A", "A", "B", "B", "B", "A"]
    # Exit aus A bei Index 2, Rückkehr bei Index 5 (3 Schritte später).
    assert return_probability(seq, "A", window=2) == 0.0
    assert return_probability(seq, "A", window=5) == 1.0
    assert return_probability(seq, "X", window=10) == 0.0


def test_contact_probability():
    L = np.array([10e-9, 40e-9, 29e-9])
    assert np.isclose(contact_probability(L), 2 / 3)
    assert np.isclose(contact_probability(L, L_contact=5e-9), 0.0)