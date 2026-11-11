import networkx as nx
import pandas as pd
import pytest

from src.contact_graphs import contact_graph, graph_features, pair_table
from src.zones import R_DEFAULT


def test_pair_table_preserves_particle_ids_and_units():
    positions = [
        [0.0, 0.0],
        [2 * R_DEFAULT + 7e-9, 0.0],
        [10e-6, 0.0],
    ]
    pairs = pair_table(positions, particle_ids=[5, 9, 12])
    assert list(pairs.columns) == ["i", "j", "L_m", "L_nm", "zone"]
    assert len(pairs) == 3
    close = pairs[(pairs.i == 5) & (pairs.j == 9)].iloc[0]
    assert close.L_m == pytest.approx(7e-9)
    assert close.L_nm == pytest.approx(7.0)
    assert close.zone == "near_gap"
    assert set(zip(pairs.i, pairs.j)) == {(5, 9), (5, 12), (9, 12)}


def test_pair_table_rejects_bad_positions_and_ids():
    with pytest.raises(ValueError):
        pair_table([[0.0, 0.0]], particle_ids=[1, 2])
    with pytest.raises(ValueError):
        pair_table([[float("nan"), 0.0]], particle_ids=[1])


def test_pair_table_empty_has_stable_schema():
    pairs = pair_table([], particle_ids=[])
    assert pairs.empty
    assert list(pairs.columns) == ["i", "j", "L_m", "L_nm", "zone"]


def _pairs():
    return pd.DataFrame(
        [
            {"i": 10, "j": 20, "L_m": 1e-9, "L_nm": 1.0, "zone": "hard_contact"},
            {"i": 20, "j": 30, "L_m": 7e-9, "L_nm": 7.0, "zone": "near_gap"},
            {"i": 30, "j": 40, "L_m": 20e-9, "L_nm": 20.0, "zone": "meso_gap"},
            {"i": 40, "j": 50, "L_m": 50e-9, "L_nm": 50.0, "zone": "far_gap"},
        ]
    )


@pytest.mark.parametrize(
    ("graph_type", "edges", "largest", "components", "mean_degree", "sizes"),
    [
        ("hard", {(10, 20)}, 2, 5, 2 / 6, [2, 1, 1, 1, 1]),
        ("near", {(10, 20), (20, 30)}, 3, 4, 4 / 6, [3, 1, 1, 1]),
        ("meso", {(10, 20), (20, 30), (30, 40)}, 4, 3, 1.0, [4, 1, 1]),
    ],
)
def test_contact_graph_variants_retain_isolates(
    graph_type, edges, largest, components, mean_degree, sizes
):
    nodes = [10, 20, 30, 40, 50, 60]
    graph = contact_graph(_pairs(), nodes, graph_type=graph_type)
    assert set(graph.nodes) == set(nodes)
    assert {tuple(sorted(edge)) for edge in graph.edges} == edges
    features = graph_features(graph)
    assert features["largest_cluster"] == largest
    assert features["number_of_components"] == components
    assert features["number_of_edges"] == len(edges)
    assert features["mean_degree"] == pytest.approx(mean_degree)
    assert features["cluster_size_distribution"] == sizes


def test_empty_pair_table_and_empty_graph_features():
    nodes = [3, 7]
    empty = pair_table([], particle_ids=[])
    graph = contact_graph(empty, nodes, graph_type="meso")
    assert set(graph.nodes) == set(nodes)
    assert graph.number_of_edges() == 0
    assert graph_features(graph)["cluster_size_distribution"] == [1, 1]
    assert graph_features(nx.Graph()) == {
        "largest_cluster": 0,
        "number_of_components": 0,
        "number_of_edges": 0,
        "mean_degree": 0.0,
        "cluster_size_distribution": [],
    }
