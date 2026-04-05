"""
Canadian Election Simulator - Voter Transition Graph

Copyright (c) 2025 Amin Behbudov, Fares Abdulmajeed Alabdulhadi, Tahmid Wasif Zaman, Dimural Murat

This module handles building and visualizing voter transition graphs.
"""

import numpy as np
import networkx as nx
import plotly.graph_objects as go

from config import PARTY_COLORS

# Only draw edges above this weight threshold
EDGE_WEIGHT_THRESHOLD = 0.02
# Offset for overlapping edges
EDGE_SEPARATION = 0.2
# Radius for circular node layout
LAYOUT_RADIUS = 3.0


def build_voter_graph_from_history(
    votes_prev: dict,
    votes_curr: dict,
) -> nx.DiGraph:
    """
    Build a voter transition graph from two consecutive elections.

    Args:
        votes_prev (dict): Previous election voting data by province
        votes_curr (dict): Current election voting data by province

    Returns:
        nx.DiGraph: Directed graph representing voter transitions
    """
    g = nx.DiGraph()
    for prov in votes_prev:
        if prov not in votes_curr:
            continue
        prev_data = votes_prev[prov]
        curr_data = votes_curr[prov]
        for from_party in prev_data:
            for to_party in curr_data:
                if from_party == to_party:
                    continue
                flow = min(prev_data[from_party], curr_data[to_party]) * 0.5
                if flow > 0:
                    if g.has_edge(from_party, to_party):
                        g[from_party][to_party]["weight"] += flow
                    else:
                        g.add_edge(from_party, to_party, weight=flow)
    return g


def merge_graphs(g1: nx.DiGraph, g2: nx.DiGraph) -> nx.DiGraph:
    """
    Merge two voter transition graphs by summing edge weights.

    Args:
        g1 (nx.DiGraph): First graph
        g2 (nx.DiGraph): Second graph

    Returns:
        nx.DiGraph: Merged graph with combined edge weights
    """
    merged = nx.DiGraph()
    for g in [g1, g2]:
        for u, v, data in g.edges(data=True):
            if merged.has_edge(u, v):
                merged[u][v]["weight"] += data["weight"]
            else:
                merged.add_edge(u, v, weight=data["weight"])
    return merged


def build_historical_voter_graph(
    votes_2015: dict,
    votes_2019: dict,
    votes_2021: dict,
) -> nx.DiGraph:
    """
    Build a comprehensive voter transition graph from all historical data.

    Args:
        votes_2015 (dict): 2015 election voting data
        votes_2019 (dict): 2019 election voting data
        votes_2021 (dict): 2021 election voting data

    Returns:
        nx.DiGraph: Combined historical voter transition graph
    """
    graph_2015_2019 = build_voter_graph_from_history(votes_2015, votes_2019)
    graph_2019_2021 = build_voter_graph_from_history(votes_2019, votes_2021)
    return merge_graphs(graph_2015_2019, graph_2019_2021)


def _bezier_point(
    p0: tuple, p1: tuple, p2: tuple, t: float
) -> tuple:
    """Compute a point on a quadratic Bézier curve at parameter t."""
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
    return (x, y)


def make_voter_graph_figure(graph: nx.DiGraph) -> go.Figure:
    """
    Create a Plotly figure of the voter transition graph.

    Each edge is drawn as a split-color Bézier curve: the first half uses the
    source party's color and the second half uses the target party's color.
    Edge labels show the normalized percentage of outgoing flow.

    Args:
        graph (nx.DiGraph): Voter transition graph

    Returns:
        go.Figure: Plotly figure of the transition graph
    """
    edges_to_draw = [
        (u, v, d)
        for u, v, d in graph.edges(data=True)
        if d["weight"] >= EDGE_WEIGHT_THRESHOLD
    ]

    # Normalize each edge weight relative to its source node's total outflow
    outgoing_totals: dict = {}
    for u, v, d in edges_to_draw:
        outgoing_totals[u] = outgoing_totals.get(u, 0) + d["weight"]

    pos = nx.circular_layout(graph, scale=LAYOUT_RADIUS)

    # Track how many edges share the same node pair (for offset calculation)
    edge_multiplicity: dict = {}
    for u, v, _ in edges_to_draw:
        key = tuple(sorted((u, v)))
        edge_multiplicity[key] = edge_multiplicity.get(key, 0) + 1

    offset_map: dict = {}
    edge_traces = []
    arrow_annotations = []

    for u, v, d in edges_to_draw:
        x0, y0 = pos[u]
        x1, y1 = pos[v]

        norm_weight = d["weight"] / outgoing_totals[u] if outgoing_totals.get(u, 0) > 0 else 0

        key = tuple(sorted((u, v)))
        total_edges = edge_multiplicity[key]
        current_index = offset_map.get(key, 0)
        offset_map[key] = current_index + 1

        # Compute perpendicular offset for overlapping edges
        dx, dy = x1 - x0, y1 - y0
        length = (dx ** 2 + dy ** 2) ** 0.5 or 0.0001
        perp_x, perp_y = -dy / length, dx / length
        offset_amount = (current_index - (total_edges - 1) / 2) * EDGE_SEPARATION

        # Bézier control point
        cx = (x0 + x1) / 2 + perp_x * offset_amount
        cy = (y0 + y1) / 2 + perp_y * offset_amount
        p0_coord = (x0, y0)
        p1_coord = (cx, cy)
        p2_coord = (x1, y1)

        first_half = [_bezier_point(p0_coord, p1_coord, p2_coord, t) for t in np.linspace(0, 0.5, 10)]
        second_half = [_bezier_point(p0_coord, p1_coord, p2_coord, t) for t in np.linspace(0.5, 1.0, 10)]

        color_from = PARTY_COLORS.get(u, "gray")
        color_to = PARTY_COLORS.get(v, "gray")

        edge_traces.append(go.Scatter(
            x=[pt[0] for pt in first_half],
            y=[pt[1] for pt in first_half],
            mode="lines",
            line=dict(color=color_from, width=2),
            hoverinfo="none",
            showlegend=False,
        ))
        edge_traces.append(go.Scatter(
            x=[pt[0] for pt in second_half],
            y=[pt[1] for pt in second_half],
            mode="lines",
            line=dict(color=color_to, width=2),
            hoverinfo="none",
            showlegend=False,
        ))

        arrow_start = _bezier_point(p0_coord, p1_coord, p2_coord, 0.75)
        arrow_end = _bezier_point(p0_coord, p1_coord, p2_coord, 0.9)
        arrow_annotations.append(dict(
            x=arrow_end[0], y=arrow_end[1],
            ax=arrow_start[0], ay=arrow_start[1],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True,
            arrowhead=3, arrowsize=1, arrowwidth=2,
            arrowcolor=color_to,
            text=f"{norm_weight * 100:.1f}%",
            font=dict(color=color_to, size=12),
            align="center",
        ))

    node_x, node_y, node_labels, node_colors = [], [], [], []
    for node in graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_labels.append(node)
        node_colors.append(PARTY_COLORS.get(node, "gray"))

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        text=node_labels,
        mode="markers+text",
        textposition="top center",
        marker=dict(size=25, color=node_colors, line=dict(color="black", width=1)),
        hoverinfo="text",
    )

    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        title="Historical Voter Transition Graph (Normalized Percentages)",
        annotations=arrow_annotations,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        showlegend=False,
        hovermode="closest",
        plot_bgcolor="rgba(240,240,255,1)",
    )
    return fig


if __name__ == "__main__":
    from data_loader import load_historical_data

    votes_2015, votes_2019, votes_2021 = load_historical_data()
    historical_graph = build_historical_voter_graph(votes_2015, votes_2019, votes_2021)
    print(f"Graph has {len(historical_graph.nodes())} nodes and {len(historical_graph.edges())} edges")
    for u, v, d in list(historical_graph.edges(data=True))[:5]:
        print(f"Edge {u} -> {v}: {d['weight']:.3f}")
