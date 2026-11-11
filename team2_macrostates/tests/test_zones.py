import numpy as np
import pytest

from src.zones import R_DEFAULT, allowed_zones, distance_zone, surface_distance


@pytest.mark.parametrize(
    ("L_nm", "expected"),
    [
        (-1.0, "hard_contact"),
        (1.999, "hard_contact"),
        (2.0, "dlvo_zone"),
        (4.999, "dlvo_zone"),
        (5.0, "near_gap"),
        (9.999, "near_gap"),
        (10.0, "meso_gap"),
        (29.999, "meso_gap"),
        (30.0, "far_gap"),
        (99.999, "far_gap"),
        (100.0, "separated"),
    ],
)
def test_distance_zone_boundaries(L_nm, expected):
    assert distance_zone(L_nm * 1e-9) == expected


def test_surface_distance_subtracts_diameter():
    centre_distance = 2 * R_DEFAULT + 5e-9
    assert surface_distance([0, 0], [centre_distance, 0]) == pytest.approx(5e-9)


def test_surface_distance_uses_minimum_image_across_boundary():
    p_i = np.array([0.5e-6, 0.0])
    p_j = np.array([19.495e-6, 0.0])
    direct = surface_distance(p_i, p_j)
    wrapped = surface_distance(p_i, p_j, box=20e-6)
    assert direct == pytest.approx(17.995e-6)
    assert wrapped == pytest.approx(5e-9)


def test_surface_distance_leaves_nonwrapping_pair_unchanged():
    p_i = np.array([1e-6, 0.0])
    p_j = np.array([4.005e-6, 0.0])
    assert surface_distance(p_i, p_j, box=20e-6) == pytest.approx(2.005e-6)


def test_allowed_zones_match_graph_definitions():
    assert allowed_zones("hard") == {"hard_contact"}
    assert allowed_zones("near") == {"hard_contact", "dlvo_zone", "near_gap"}
    assert allowed_zones("meso") == {
        "hard_contact", "dlvo_zone", "near_gap", "meso_gap"
    }
    assert allowed_zones("far") == {
        "hard_contact", "dlvo_zone", "near_gap", "meso_gap", "far_gap"
    }
    with pytest.raises(ValueError):
        allowed_zones("everything")
