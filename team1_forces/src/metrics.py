"""Metriken für Zonen- und Clusteranalyse (§11).

Zonenmetriken arbeiten auf Sequenzen von Zonenlabels (Strings) bzw.
Abständen (SI-Einheiten, Meter); Zeiten sind Schrittanzahlen.
"""

import networkx as nx
import numpy as np

CONTACT_ZONES = {"hard_contact", "dlvo_zone", "near_gap", "meso_gap"}


def dwell_times(zone_sequence, target_zone):
    """Dauern aller zusammenhängenden Aufenthalte in target_zone (in Schritten)."""
    out = []
    current = 0
    for z in zone_sequence:
        if z == target_zone:
            current += 1
        else:
            if current > 0:
                out.append(current)
                current = 0
    if current > 0:
        out.append(current)
    return out


def escape_time(zone_sequence):
    """Erste Austrittszeit aus der anfänglichen Zone (First-Passage, in Schritten).

    None, wenn die Zone nie verlassen wird (rechtszensiert).
    """
    if len(zone_sequence) == 0:
        return None
    start = zone_sequence[0]
    for i, z in enumerate(zone_sequence):
        if z != start:
            return i
    return None


def return_probability(zone_sequence, target_zone, window=10):
    """Anteil der Austritte aus target_zone, denen eine Rückkehr innerhalb
    `window` Schritten folgt. Ende der Sequenz zählt als beobachtete
    Nicht-Rückkehr."""
    exits = 0
    returned = 0
    for i, z in enumerate(zone_sequence):
        if z == target_zone:
            continue
        if i > 0 and zone_sequence[i - 1] == target_zone:
            exits += 1
            if any(w == target_zone for w in zone_sequence[i : i + 1 + window]):
                returned += 1
    return returned / exits if exits else 0.0


def contact_probability(L_values, L_contact=30e-9):
    """Anteil der Zeit mit L < L_contact (Standard: 30 nm, konsistent mit den
    akzeptierten Kontaktzonen des Kontaktgraphen)."""
    L_values = np.asarray(L_values)
    if L_values.size == 0:
        return 0.0
    return float(np.mean(L_values < L_contact))


def contact_graph(pair_rows, n, accepted_zones=CONTACT_ZONES):
    """Kontaktgraph: Knoten 0..n-1, Kanten für Paare in akzeptierten Zonen."""
    g = nx.Graph()
    g.add_nodes_from(range(n))
    for i, j, L, zone in pair_rows:
        if zone in accepted_zones:
            g.add_edge(i, j, L=L, zone=zone)
    return g


def cluster_metrics(pair_rows, n):
    """Größte zusammenhängende Komponente, Komponentenzahl, mittlerer Grad, Kantenzahl."""
    g = contact_graph(pair_rows, n)
    comps = [len(c) for c in nx.connected_components(g)]
    largest = max(comps) if comps else 1
    mean_degree = float(np.mean([d for _, d in g.degree()])) if n else 0.0
    return {
        "largest_cluster": largest,
        "n_components": len(comps),
        "mean_degree": mean_degree,
        "n_edges": g.number_of_edges(),
    }