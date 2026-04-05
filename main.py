"""
Canadian Election Simulator - Entry Point

Copyright (c) 2025 Amin Behbudov

This module is the entry point for the Canadian Election Simulator. It loads
historical data, builds the voter transition graph, and launches the dashboard.
"""

from data_loader import load_historical_data
from graph import build_historical_voter_graph
from dashboard import create_dashboard


def initialize_system():
    """
    Load historical data and build the voter transition graph and Dash app.

    Returns:
        tuple: (historical_voter_graph, app)
    """
    votes_2015, votes_2019, votes_2021 = load_historical_data()
    historical_voter_graph = build_historical_voter_graph(votes_2015, votes_2019, votes_2021)
    app = create_dashboard(historical_voter_graph)
    return historical_voter_graph, app


def main():
    """Initialize and run the election simulator dashboard."""
    print("Initializing Canadian Election Simulator...")
    _, app = initialize_system()
    print("Starting dashboard — visit http://127.0.0.1:8050/")
    app.run(debug=True, port=8050, use_reloader=False)


if __name__ == "__main__":
    main()
