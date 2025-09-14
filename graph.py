"""
Canadian Election Simulator - Voter Transition Graph
Copyright (c) 2025 [Your Name]

This module handles building and manipulating voter transition graphs.
"""
import numpy as np
import networkx as nx
import plotly.graph_objects as go
from config import PARTY_COLORS


def build_voter_graph_from_history(votes_prev: dict, votes_curr: dict) -> nx.DiGraph:
    """
    Builds a voter transition graph based on historical election results.

    Args:
        votes_prev (dict): Previous election voting data
        votes_curr (dict): Current election voting data

    Returns:
        networkx.DiGraph: Directed graph representing voter transitions
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
                        g[from_party][to_party]['weight'] += flow
                    else:
                        g.add_edge(from_party, to_party, weight=flow)
    return g


def merge_graphs(g1: nx.DiGraph, g2: nx.DiGraph) -> nx.DiGraph:
    """
    Merges two voter transition graphs.

    Args:
        g1 (networkx.DiGraph): First graph
        g2 (networkx.DiGraph): Second graph

    Returns:
        networkx.DiGraph: Merged graph
    """
    gr = nx.DiGraph()
    for g in [g1, g2]:
        for u, v, data in g.edges(data=True):
            weight = data['weight']
            if gr.has_edge(u, v):
                gr[u][v]['weight'] += weight
            else:
                gr.add_edge(u, v, weight=weight)
    return gr


def build_historical_voter_graph(votes_2015: dict, votes_2019: dict, votes_2021: dict) -> nx.DiGraph:
    """
    Builds a comprehensive voter transition graph from all historical data.

    Args:
        votes_2015 (dict): 2015 election voting data
        votes_2019 (dict): 2019 election voting data
        votes_2021 (dict): 2021 election voting data

    Returns:
        networkx.DiGraph: Combined historical voter transition graph
    """
    graph_2015_2019 = build_voter_graph_from_history(votes_2015, votes_2019)
    graph_2019_2021 = build_voter_graph_from_history(votes_2019, votes_2021)
    return merge_graphs(graph_2015_2019, graph_2019_2021)


# --- UPDATED VOTER TRANSITION GRAPH FUNCTION ---
def make_voter_graph_figure(graph: nx.DiGraph) -> go.Figure:
    """
    Creates a Plotly figure of the voter transition graph with split colored segments.
    For each edge from party A to party B:
      • The first half is drawn in the source party's color.
      • The second half is drawn in the target party's color.
    An arrow annotation (using the target color) indicates the transition direction.
    The percentage is normalized so that for each source party, the outgoing transitions sum to 100%.
    """
    edge_weight_threshold = 0.02  # Only draw edges above 2%
    seperation = 0.2              # Offset for overlapping edges
    radius = 3.0                  # Radius for circular layout

    # Filter edges by weight
    edges_to_draw = [
        (u, v, d) for (u, v, d) in graph.edges(data=True)
        if d["weight"] >= edge_weight_threshold
    ]

    # Compute total outgoing flow for each source node (for normalization)
    outgoing_totals = {}
    for u, v, d in edges_to_draw:
        outgoing_totals[u] = outgoing_totals.get(u, 0) + d["weight"]

    # Use circular layout for nodes
    pos = nx.circular_layout(graph, scale=radius)

    # For overlapping edges, determine offset as before
    edge_multiplicity = {}
    for u, v, d in edges_to_draw:
        key = tuple(sorted((u, v)))
        edge_multiplicity[key] = edge_multiplicity.get(key, 0) + 1
    offset_map = {}

    edge_traces = []
    arrow_annotations = []

    # Helper: quadratic Bézier function
    def bezier_point(P0: tuple, P1: tuple, P2: tuple, t: float) -> tuple:
        x = (1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t ** 2 * P2[0]
        y = (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t ** 2 * P2[1]
        return (x, y)

    for (u, v, d) in edges_to_draw:
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        raw_weight = d["weight"]

        # Normalize weight based on source's total outgoing flow
        if outgoing_totals.get(u, 0) > 0:
            norm_weight = raw_weight / outgoing_totals[u]
        else:
            norm_weight = 0

        key = tuple(sorted((u, v)))
        total_edges = edge_multiplicity[key]
        current_index = offset_map.get(key, 0)
        offset_map[key] = current_index + 1

        # Compute offset for overlapping edges
        dx, dy = x1 - x0, y1 - y0
        length = (dx**2 + dy**2) ** 0.5 or 0.0001
        perp_x, perp_y = -dy / length, dx / length
        offset_amount = (current_index - (total_edges - 1) / 2) * seperation

        # Control point for quadratic curve
        cx = (x0 + x1) / 2 + perp_x * offset_amount
        cy = (y0 + y1) / 2 + perp_y * offset_amount

        P0 = (x0, y0)
        P1 = (cx, cy)
        P2 = (x1, y1)

        # Sample points along the curve (split into two segments)
        t_values_first = np.linspace(0, 0.5, 10)
        t_values_second = np.linspace(0.5, 1, 10)
        first_half = [bezier_point(P0, P1, P2, t) for t in t_values_first]
        second_half = [bezier_point(P0, P1, P2, t) for t in t_values_second]

        # Colors: first half in source's color, second half in target's color
        color_from = PARTY_COLORS.get(u, 'gray')
        color_to = PARTY_COLORS.get(v, 'gray')

        edge_traces.append(go.Scatter(
            x=[pt[0] for pt in first_half],
            y=[pt[1] for pt in first_half],
            mode='lines',
            line=dict(color=color_from, width=2),
            hoverinfo='none',
            showlegend=False
        ))
        edge_traces.append(go.Scatter(
            x=[pt[0] for pt in second_half],
            y=[pt[1] for pt in second_half],
            mode='lines',
            line=dict(color=color_to, width=2),
            hoverinfo='none',
            showlegend=False
        ))

        # Determine arrow annotation position (e.g., between t=0.75 and t=0.9)
        arrow_start = bezier_point(P0, P1, P2, 0.75)
        arrow_end = bezier_point(P0, P1, P2, 0.9)
        arrow_annotations.append(dict(
            x=arrow_end[0],
            y=arrow_end[1],
            ax=arrow_start[0],
            ay=arrow_start[1],
            xref="x", yref="y",
            axref="x", ayref="y",
            showarrow=True,
            arrowhead=3,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor=color_to,
            text=f"{norm_weight * 100:.1f}%",
            font=dict(color=color_to, size=12),
            align="center"
        ))

    # Create node scatter trace
    node_x, node_y, node_labels, node_colors = [], [], [], []
    for node in graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_labels.append(node)
        node_colors.append(PARTY_COLORS.get(node, 'gray'))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        text=node_labels,
        mode='markers+text',
        textposition='top center',
        marker=dict(size=25, color=node_colors, line=dict(color='black', width=1)),
        hoverinfo='text'
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
        plot_bgcolor="rgba(240,240,255,1)"
    )
    return fig


if __name__ == "__main__":
    # Test graph building (basic example)
    from data_loader import load_historical_data

    votes_2015, votes_2019, votes_2021 = load_historical_data()
    historical_graph = build_historical_voter_graph(votes_2015, votes_2019, votes_2021)

    print(f"Graph has {len(historical_graph.nodes())} nodes and {len(historical_graph.edges())} edges")
    for u, v, d in list(historical_graph.edges(data=True))[:5]:
        print(f"Edge {u} -> {v}: {d['weight']:.3f}")


if __name__ == '__main__':
    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'extra-imports': [],
        'allowed-io': [],
        'max-line-length': 120
    })
