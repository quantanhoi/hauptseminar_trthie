import pytest

from src.metrics import CONTACT_ZONES, contact_graph, cluster_metrics


def test_known_graph():
    n = 4
    pair_rows = [
        (0, 1, 1e-9, "hard_contact"),
        (1, 2, 7e-9, "near_gap"),
        (2, 3, 150e-9, "separated"),
    ]
    m = cluster_metrics(pair_rows, n)
    assert m["largest_cluster"] == 3
    assert m["n_components"] == 2
    assert m["n_edges"] == 2
    assert m["mean_degree"] == 1.0

    g = contact_graph(pair_rows, n)
    assert set(g.edges) == {(0, 1), (1, 2)}
    assert g[0][1]["zone"] == "hard_contact"
    assert g[0][1]["L"] == 1e-9


def test_no_edges():
    m = cluster_metrics([], 4)
    assert m == {
        "largest_cluster": 1,
        "n_components": 4,
        "mean_degree": 0.0,
        "n_edges": 0,
    }


def test_accepted_zones_filter():
    pair_rows = [(0, 1, 40e-9, "far_gap")]
    g_default = contact_graph(pair_rows, 2)
    assert g_default.number_of_edges() == 0
    g_wide = contact_graph(pair_rows, 2, accepted_zones=CONTACT_ZONES | {"far_gap"})
    assert g_wide.number_of_edges() == 1
    assert "far_gap" not in CONTACT_ZONES