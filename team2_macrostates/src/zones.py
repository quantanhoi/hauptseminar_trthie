"""Oberflächenabstände und physikalische Abstandszonen (Team 2, §6)."""

import numpy as np

R_DEFAULT = 500e-9


def surface_distance(p_i, p_j, R=R_DEFAULT, box=None):
    """Return L = centre distance − 2R, optionally using minimum image."""
    delta = np.asarray(p_j, dtype=float) - np.asarray(p_i, dtype=float)
    if box is not None:
        delta = delta - box * np.round(delta / box)
    return float(np.linalg.norm(delta) - 2.0 * R)


def distance_zone(L):
    """Classify a surface gap in metres using the exact §6 boundaries."""
    L_nm = L * 1e9
    if L_nm < 2:
        return "hard_contact"
    if L_nm < 5:
        return "dlvo_zone"
    if L_nm < 10:
        return "near_gap"
    if L_nm < 30:
        return "meso_gap"
    if L_nm < 100:
        return "far_gap"
    return "separated"


def allowed_zones(graph_type="meso"):
    zones = {
        "hard": {"hard_contact"},
        "near": {"hard_contact", "dlvo_zone", "near_gap"},
        "meso": {"hard_contact", "dlvo_zone", "near_gap", "meso_gap"},
        "far": {"hard_contact", "dlvo_zone", "near_gap", "meso_gap", "far_gap"},
    }
    if graph_type not in zones:
        raise ValueError(f"Unknown graph_type: {graph_type}")
    return zones[graph_type]
