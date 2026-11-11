"""Persistenzfilter und Sequenzmetriken mit expliziter Zensierung."""

import numpy as np
import pandas as pd

DWELL_COLUMNS = [
    "state", "start_index", "end_index", "start_time", "end_time",
    "dwell_steps", "dwell_seconds", "left_censored", "right_censored",
]


def _runs(sequence):
    sequence = list(sequence)
    if not sequence:
        return []
    runs = []
    start = 0
    for index in range(1, len(sequence)):
        if sequence[index] != sequence[start]:
            runs.append((sequence[start], start, index - 1))
            start = index
    runs.append((sequence[start], start, len(sequence) - 1))
    return runs


def _validated_times(sequence, times):
    sequence = list(sequence)
    times = np.asarray(times, dtype=float)
    if len(sequence) != len(times):
        raise ValueError("sequence and times must have matching lengths")
    if not np.all(np.isfinite(times)):
        raise ValueError("times must be finite")
    if len(times) > 1 and not np.all(np.diff(times) > 0):
        raise ValueError("times must be strictly increasing")
    return sequence, times


def filter_short_states(sequence, min_dwell=5):
    """Replace short runs without changing sequence length or raw input."""
    if min_dwell < 1:
        raise ValueError("min_dwell must be at least 1")
    sequence = list(sequence)
    runs = _runs(sequence)
    valid = [state for state, start, end in runs if end - start + 1 >= min_dwell]
    if not runs:
        return []
    if not valid:
        return ["mixed_transition"] * len(sequence)

    filtered = []
    previous_valid = None
    for state, start, end in runs:
        length = end - start + 1
        if length >= min_dwell:
            replacement = state
            previous_valid = state
        else:
            replacement = previous_valid if previous_valid is not None else valid[0]
        filtered.extend([replacement] * length)
    return filtered


def dwell_runs(sequence, times):
    """Return all contiguous stays; boundary runs are marked as censored."""
    sequence, times = _validated_times(sequence, times)
    if not sequence:
        return pd.DataFrame(columns=DWELL_COLUMNS)
    sample_interval = float(np.median(np.diff(times))) if len(times) > 1 else np.nan
    rows = []
    for state, start, end in _runs(sequence):
        steps = end - start + 1
        rows.append({
            "state": state,
            "start_index": start,
            "end_index": end,
            "start_time": times[start],
            "end_time": times[end],
            "dwell_steps": steps,
            "dwell_seconds": steps * sample_interval,
            "left_censored": start == 0,
            "right_censored": end == len(sequence) - 1,
        })
    return pd.DataFrame(rows, columns=DWELL_COLUMNS)


def transition_counts(sequence, states=None):
    sequence = list(sequence)
    states = sorted(set(sequence)) if states is None else list(states)
    missing = set(sequence) - set(states)
    if missing:
        raise ValueError(f"states missing from catalogue: {sorted(missing)}")
    counts = pd.DataFrame(0.0, index=states, columns=states)
    for source, target in zip(sequence[:-1], sequence[1:]):
        counts.loc[source, target] += 1.0
    return counts


def normalize_transition_counts(counts):
    totals = counts.sum(axis=1).replace(0, np.nan)
    return counts.div(totals, axis=0)


def return_summary(sequence, times, target_state, horizon):
    """Measure first returns after departures with complete future windows only."""
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    sequence, times = _validated_times(sequence, times)
    return_steps = []
    return_seconds = []
    eligible = 0
    for index in range(len(sequence) - 1):
        if sequence[index] != target_state or sequence[index + 1] == target_state:
            continue
        if index + 1 + horizon > len(sequence):
            continue
        eligible += 1
        for offset in range(1, horizon + 1):
            return_index = index + offset
            if sequence[return_index] == target_state:
                return_steps.append(offset)
                return_seconds.append(times[return_index] - times[index])
                break
    returns = len(return_steps)
    return {
        "return_probability": returns / eligible if eligible else np.nan,
        "mean_return_steps": float(np.mean(return_steps)) if returns else np.nan,
        "mean_return_seconds": float(np.mean(return_seconds)) if returns else np.nan,
        "eligible_departures": eligible,
        "returns": returns,
    }


def _available(value):
    return value is not None and not pd.isna(value)


def attractor_candidate(
    frequency, mean_dwell_steps, return_probability, seed_count,
    label_agreement, total_seeds,
):
    """Apply §9 heuristics; unavailable evidence never counts as success."""
    flags = {
        "frequency_ok": bool(frequency > 0.05) if _available(frequency) else None,
        "mean_dwell_ok": (
            bool(mean_dwell_steps > 5) if _available(mean_dwell_steps) else None
        ),
        "return_probability_ok": (
            bool(return_probability > 0.3) if _available(return_probability) else None
        ),
        "seed_reproducibility": (
            bool(seed_count >= 3)
            if _available(seed_count) and _available(total_seeds) and total_seeds >= 3
            else None
        ),
        "label_agreement_ok": (
            bool(label_agreement > 0.7) if _available(label_agreement) else None
        ),
    }
    flags["candidate"] = all(flag is True for flag in flags.values())
    return flags
