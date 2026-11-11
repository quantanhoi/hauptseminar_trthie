"""Deterministische Positionsstörungen und Label-Robustheit."""

import numpy as np


def jitter_positions(positions, sigma_nm=1.0, seed=0, box=None):
    if sigma_nm < 0:
        raise ValueError("sigma_nm must be nonnegative")
    positions = np.array(positions, dtype=float, copy=True)
    rng = np.random.default_rng(seed)
    positions += rng.normal(scale=sigma_nm * 1e-9, size=positions.shape)
    if box is not None:
        positions = np.mod(positions, box)
    return positions


def label_agreement(seq_a, seq_b):
    seq_a = list(seq_a)
    seq_b = list(seq_b)
    if len(seq_a) != len(seq_b):
        raise ValueError("label sequences must have equal lengths")
    if not seq_a:
        return np.nan
    return sum(a == b for a, b in zip(seq_a, seq_b)) / len(seq_a)
