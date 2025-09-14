"""
main.py - Canadian Election Simulator - Main Module
Copyright (c) 2025 [Your Name]

This module serves as the entry point for the Canadian Election Simulator application.
It orchestrates the loading of data, building of models, and running the simulation dashboard.
"""


from data_loader import load_historical_data
from graph import build_historical_voter_graph
from dashboard import create_dashboard


def initialize_system():
    """
    Initialize the election simulation system by loading data and building models.

    Returns:
        tuple: Contains the voter graph and app instance
    """
    # Load historical election data
    votes_2015, votes_2019, votes_2021 = load_historical_data()

    # Build voter transition graph from historical data
    historical_voter_graph = build_historical_voter_graph(votes_2015, votes_2019, votes_2021)

    # Create Dash app
    app = create_dashboard(historical_voter_graph)

    return historical_voter_graph, app


def main():
    """
    Main function to initialize and run the election simulator.
    """
    print("Initializing Canadian Election Simulator...")
    historical_voter_graph, app = initialize_system()

    print("Starting simulator dashboard...")
    app.run(debug=True, port=8050, use_reloader=False)


if __name__ == "__main__":
    main()
