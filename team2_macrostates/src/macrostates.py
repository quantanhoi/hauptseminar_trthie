"""Kleiner regelbasierter Makrozustandskatalog (Team 2, §8)."""

import networkx as nx


def macrostate_from_graph(G):
    """Classify the largest component; tetra_like is only a 2D compactness proxy."""
    if G.number_of_edges() == 0:
        return "monomer_gas"

    components = list(nx.connected_components(G))
    largest_nodes = max(components, key=len)
    largest = len(largest_nodes)
    if largest == 2:
        return "dimer_dominated"
    if largest == 3:
        return "trimer_like"
    if largest == 4:
        if G.subgraph(largest_nodes).number_of_edges() >= 4:
            return "tetra_like"
        return "loose_four_cluster"
    if largest >= 5:
        return "large_cluster"
    return "mixed_transition"
