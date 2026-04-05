"""
Canadian Election Simulator - Dashboard Module

Copyright (c) 2025 Amin Behbudov, Fares Abdulmajeed Alabdulhadi, Tahmid Wasif Zaman, Dimural Murat

This module handles the Dash web interface for the election simulator.
"""

import time

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State

from scraper import scrape_polling_data
from visualization import make_bar_chart, make_choropleth
from graph import make_voter_graph_figure
from election_model import run_simulation

# Cache polling data so we don't re-scrape on every tab switch
_cached_polls = None


def get_polls():
    """Return cached polling data, scraping only on first call."""
    global _cached_polls
    if _cached_polls is None:
        _cached_polls = scrape_polling_data()
    return _cached_polls


def create_dashboard(historical_voter_graph):
    """
    Create the Dash app for the election simulation dashboard.

    Args:
        historical_voter_graph (networkx.DiGraph): Historical voter transition graph

    Returns:
        dash.Dash: Configured Dash app instance
    """
    app = dash.Dash(__name__)

    simulation_results = None

    app.layout = html.Div([
        html.H1("Canadian Federal Election Simulator"),
        html.Div([
            html.Button("Run Simulation", id="run-btn", n_clicks=0),
            html.Span("Simulations: 1000", style={"marginLeft": "10px"}),
        ]),
        dcc.Loading(
            id="loading-simulation",
            type="default",
            color="#119DFF",
            children=[
                html.Div(id="summary"),
                dcc.Tabs(id="tabs", value="map", children=[
                    dcc.Tab(label="Province Map", value="map"),
                    dcc.Tab(label="Seat Bar Chart", value="bar"),
                    dcc.Tab(label="Voter Transition Graph", value="graph"),
                    dcc.Tab(label="Compare Predictions", value="compare"),
                ]),
                html.Div(id="tab-content"),
            ],
        ),
        html.Div(id="status-message", style={"marginTop": "10px", "color": "gray"}),
    ])

    @app.callback(
        [
            Output("summary", "children"),
            Output("tab-content", "children"),
            Output("status-message", "children"),
        ],
        [Input("run-btn", "n_clicks"), Input("tabs", "value")],
        [State("summary", "children")],
    )
    def update_dashboard(n_clicks, tab, current_summary):
        """
        Update the dashboard based on button clicks and tab selections.

        Args:
            n_clicks (int): Number of button clicks
            tab (str): Currently selected tab
            current_summary: Current summary HTML element

        Returns:
            tuple: (summary, tab_content, status_message)
        """
        nonlocal simulation_results

        if n_clicks == 0:
            return dash.no_update, dash.no_update, "Ready to run simulation."

        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        polls = get_polls()
        status_message = ""

        if trigger_id == "run-btn":
            start_time = time.time()
            simulation_results = run_simulation(polls, 1000, historical_voter_graph)
            elapsed = time.time() - start_time

            seats, probs = simulation_results
            lines = [
                (
                    f"{party}: {100 * probs[party]['majority']:.1f}% majority, "
                    f"{100 * probs[party]['minority']:.1f}% minority, "
                    f"{100 * probs[party]['no_win']:.1f}% no win"
                )
                for party in probs
            ]
            summary = html.Ul([html.Li(line) for line in lines])
            status_message = f"Simulation completed in {elapsed:.2f}s."
        else:
            if simulation_results is None:
                simulation_results = run_simulation(polls, 1000, historical_voter_graph)
                status_message = "Initial simulation complete."
            else:
                status_message = "Displaying existing simulation results."
            summary = current_summary

        seats, probs = simulation_results

        if tab == "bar":
            content = dcc.Graph(figure=make_bar_chart(seats))
        elif tab == "graph":
            content = dcc.Graph(figure=make_voter_graph_figure(historical_voter_graph))
        elif tab == "compare":
            seats_with_graph, _ = run_simulation(polls, 1000, historical_voter_graph)
            seats_without_graph, _ = run_simulation(polls, 1000, None)

            fig_with = make_bar_chart(seats_with_graph)
            fig_without = make_bar_chart(seats_without_graph)
            fig_with.update_layout(title="With Voter Transition Graph")
            fig_without.update_layout(title="Without Transition Modeling")

            content = html.Div([
                html.Div([dcc.Graph(figure=fig_with)], style={"width": "48%", "display": "inline-block"}),
                html.Div([dcc.Graph(figure=fig_without)], style={"width": "48%", "display": "inline-block", "float": "right"}),
            ])
        else:
            content = dcc.Graph(figure=make_choropleth(polls))

        return summary, content, status_message

    return app


if __name__ == "__main__":
    from data_loader import load_historical_data
    from graph import build_historical_voter_graph

    votes_2015, votes_2019, votes_2021 = load_historical_data()
    historical_graph = build_historical_voter_graph(votes_2015, votes_2019, votes_2021)

    app = create_dashboard(historical_graph)
    app.run(debug=True, port=8050, use_reloader=False)            html.Button("Run Simulation", id="run-btn", n_clicks=0),
            html.Span("Simulations: 1000", style={"marginLeft": "10px"}),
        ]),

        dcc.Loading(
            id="loading-simulation",
            type="default",
            color="#119DFF",
            children=[
                html.Div(id="summary"),
                dcc.Tabs(id="tabs", value='map', children=[
                    dcc.Tab(label='Province Map', value='map'),
                    dcc.Tab(label='Seat Bar Chart', value='bar'),
                    dcc.Tab(label='Voter Transition Graph', value='graph'),
                    dcc.Tab(label='Compare Predictions', value='compare'),
                ]),
                html.Div(id="tab-content")
            ]
        ),
        html.Div(id="status-message", style={"marginTop": "10px", "color": "gray"})
    ])

    @app.callback(
        [Output("summary", "children"),
         Output("tab-content", "children"),
         Output("status-message", "children")],
        [Input("run-btn", "n_clicks"),
         Input("tabs", "value")],
        [State("summary", "children")]
    )
    def update_dashboard(n, tab, current_summary):
        """
        Update the dashboard based on button clicks and tab selections.

        Args:
            n (int): Number of button clicks
            tab (str): Selected tab
            current_summary (html.Element): Current summary HTML

        Returns:
            tuple: (summary, content, status_message)
        """
        nonlocal simulation_results

        ctx = dash.callback_context
        if not ctx.triggered:
            trigger_id = 'No triggers'
        else:
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if n == 0:
            return dash.no_update, dash.no_update, "Ready to run simulation"

        status_message = ""
        if trigger_id == "run-btn":
            status_message = "Starting simulation with 1,000 trials..."
            polls = scrape_polling_data()
            start_time = time.time()
            simulation_results = run_simulation(polls, 1000, historical_voter_graph)
            end_time = time.time()

            seats, probs = simulation_results
            lines = [
                (f"{p}: {100 * probs[p]['majority']:.1f}% majority, {100 * probs[p]['minority']:.1f}% minority, "
                 f"{100 * probs[p]['no_win']:.1f}% no win")
                for p in probs]
            summary = html.Ul([html.Li(line) for line in lines])
            status_message = f"Simulation completed in {end_time - start_time:.2f} seconds."
        else:
            if simulation_results is None:
                polls = scrape_polling_data()
                simulation_results = run_simulation(polls, 1000, historical_voter_graph)
                status_message = "Initial simulation complete."
            seats, probs = simulation_results
            summary = current_summary
            status_message = "Displaying existing simulation results."

        if tab == 'bar':
            content = dcc.Graph(figure=make_bar_chart(seats))
        elif tab == 'graph':
            content = dcc.Graph(figure=make_voter_graph_figure(historical_voter_graph))
        elif tab == 'compare':
            polls = scrape_polling_data()
            seats_graph, _ = run_simulation(polls, 1000, historical_voter_graph)
            seats_raw, _ = run_simulation(polls, 1000, None)

            fig1 = make_bar_chart(seats_graph)
            fig2 = make_bar_chart(seats_raw)
            fig1.update_layout(title="With Voter Transition Graph")
            fig2.update_layout(title="Without Transition Modeling")

            content = html.Div([
                html.Div([dcc.Graph(figure=fig1)], style={"width": "48%", "display": "inline-block"}),
                html.Div([dcc.Graph(figure=fig2)], style={"width": "48%", "display": "inline-block", "float": "right"})
            ])
        else:
            polls = scrape_polling_data()
            content = dcc.Graph(figure=make_choropleth(polls))

        return summary, content, status_message

    return app


if __name__ == "__main__":
    # Test the dashboard
    from data_loader import load_historical_data
    from graph import build_historical_voter_graph

    votes_2015, votes_2019, votes_2021 = load_historical_data()
    historical_graph = build_historical_voter_graph(votes_2015, votes_2019, votes_2021)

    app = create_dashboard(historical_graph)
    app.run(debug=True, port=8050, use_reloader=False)


if __name__ == '__main__':
    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'extra-imports': [],
        'allowed-io': [],
        'max-line-length': 120
    })
