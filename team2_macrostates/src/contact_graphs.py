"""Paartabellen, Kontaktgraphen und Graphfeatures."""

import networkx as nx
import numpy as np
import pandas as pd

from src.zones import R_DEFAULT, allowed_zones, distance_zone, surface_distance

PAIR_COLUMNS = ["i", "j", "L_m", "L_nm", "zone"]


def pair_table(positions, particle_ids, R=R_DEFAULT, box=None):
    """Compute every unordered pair once; retain the real particle IDs."""
    positions = np.asarray(positions, dtype=float)
    if positions.size == 0:
        positions = np.empty((0, 2))
    particle_ids = list(particle_ids)
    if positions.ndim != 2 or len(positions) != len(particle_ids):
        raise ValueError("positions and particle_ids must have matching lengths")
    if not np.all(np.isfinite(positions)):
        raise ValueError("positions must be finite")

    rows = []
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            L = surface_distance(positions[i], positions[j], R=R, box=box)
            rows.append({
                "i": particle_ids[i], "j": particle_ids[j],
                "L_m": L, "L_nm": L * 1e9, "zone": distance_zone(L),
            })
    return pd.DataFrame(rows, columns=PAIR_COLUMNS)


def contact_graph(pair_df, particle_ids, graph_type="meso"):
    """Build one graph from cached pair rows, including isolated nodes."""
    graph = nx.Graph()
    graph.add_nodes_from(particle_ids)
    zones = allowed_zones(graph_type)
    for row in pair_df.itertuples(index=False):
        if row.zone in zones:
            graph.add_edge(row.i, row.j, L=row.L_m, zone=row.zone)
    return graph


def graph_features(G):
    components = sorted((len(c) for c in nx.connected_components(G)), reverse=True)
    n = G.number_of_nodes()
    m = G.number_of_edges()
    return {
        "largest_cluster": components[0] if components else 0,
        "number_of_components": len(components),
        "number_of_edges": m,
        "mean_degree": 2 * m / n if n else 0.0,
        "cluster_size_distribution": components,
    }
