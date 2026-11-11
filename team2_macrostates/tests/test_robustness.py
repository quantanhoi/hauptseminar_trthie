import numpy as np
import pytest

from src.robustness import jitter_positions, label_agreement


def test_jitter_is_reproducible_for_same_seed():
    positions = np.array([[1e-6, 2e-6], [3e-6, 4e-6]])
    first = jitter_positions(positions, sigma_nm=1.0, seed=17)
    second = jitter_positions(positions, sigma_nm=1.0, seed=17)
    different = jitter_positions(positions, sigma_nm=1.0, seed=18)
    np.testing.assert_array_equal(first, second)
    assert not np.array_equal(first, positions)
    assert not np.array_equal(first, different)


def test_zero_jitter_is_exact_and_does_not_mutate_input():
    positions = np.array([[1e-6, 2e-6]])
    original = positions.copy()
    perturbed = jitter_positions(positions, sigma_nm=0.0, seed=0)
    np.testing.assert_array_equal(perturbed, original)
    np.testing.assert_array_equal(positions, original)
    assert perturbed is not positions


def test_optional_box_wraps_jittered_coordinates():
    positions = np.array([[-0.1e-6, 20.1e-6]])
    wrapped = jitter_positions(positions, sigma_nm=0.0, box=20e-6)
    np.testing.assert_allclose(wrapped, [[19.9e-6, 0.1e-6]])


def test_negative_jitter_scale_is_rejected():
    with pytest.raises(ValueError):
        jitter_positions([[0.0, 0.0]], sigma_nm=-1.0)


def test_label_agreement_compares_complete_sequences():
    assert label_agreement(["a", "b", "a"], ["a", "b", "a"]) == 1.0
    assert label_agreement(["a", "b"], ["b", "a"]) == 0.0
    assert label_agreement(["a", "a", "a"], ["a", "b", "a"]) == pytest.approx(2 / 3)


def test_label_agreement_empty_and_length_mismatch():
    assert np.isnan(label_agreement([], []))
    with pytest.raises(ValueError):
        label_agreement(["a"], ["a", "b"])
