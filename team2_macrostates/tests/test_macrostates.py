import networkx as nx

from src.macrostates import macrostate_from_graph


def _graph(nodes, edges):
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    return graph


def test_no_edges_is_monomer_gas():
    assert macrostate_from_graph(_graph(range(3), [])) == "monomer_gas"


def test_largest_two_is_dimer_dominated():
    graph = _graph(range(4), [(0, 1), (2, 3)])
    assert macrostate_from_graph(graph) == "dimer_dominated"


def test_largest_three_wins_over_separate_dimer():
    graph = _graph(range(5), [(0, 1), (1, 2), (3, 4)])
    assert macrostate_from_graph(graph) == "trimer_like"


def test_four_nodes_with_three_edges_are_loose_not_tetra():
    graph = _graph(range(5), [(0, 1), (1, 2), (2, 3)])
    assert macrostate_from_graph(graph) == "loose_four_cluster"


def test_four_nodes_with_four_edges_are_tetra_proxy():
    graph = _graph(range(4), [(0, 1), (1, 2), (2, 3), (3, 0)])
    assert macrostate_from_graph(graph) == "tetra_like"


def test_largest_five_or_more_is_large_cluster():
    graph = _graph(range(6), [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])
    assert macrostate_from_graph(graph) == "large_cluster"


def test_inconsistent_graph_uses_mixed_transition_fallback():
    class InconsistentGraph(nx.Graph):
        def number_of_edges(self):
            return 1

    graph = InconsistentGraph()
    graph.add_node(0)
    assert macrostate_from_graph(graph) == "mixed_transition"
