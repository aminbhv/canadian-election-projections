"""Interactive dashboard.  Run:  python dashboard.py  then open http://127.0.0.1:8050"""

import numpy as np
from dash import Dash, Input, Output, dash_table, dcc, html

from election import config
from election.figures import region_map, seat_bar_chart, seat_histogram
from election.projection import latest_poll_average, latest_polls, project, riding_table
from election.swing import SWING_METHODS

N_TRIALS = 5_000
INPUT_PARTIES = ("LPC", "CPC", "NDP", "BQ", "GPC", "PPC")


def _backtest_markdown() -> str:
    path = config.REPORTS_DIR / "backtest_2025.md"
    if not path.exists():
        return "Run `python -m election.backtest` to generate the backtest report."
    return path.read_text(encoding="utf-8")


def _poll_note() -> str:
    polls = latest_polls()
    return (
        f"Default inputs: average of the latest poll from each of {polls['pollster'].nunique()} "
        f"firms ({polls['end_date'].min():%b %d} to {polls['end_date'].max():%b %d, %Y}). "
        "Baseline: 2025 riding results."
    )


def compute(values: list[float | None], method: str) -> tuple:
    """Run a projection for the given national percentages; return all dashboard outputs."""
    shares = np.zeros(len(config.PARTIES))
    for party, value in zip(INPUT_PARTIES, values, strict=True):
        shares[config.PARTIES.index(party)] = max(float(value or 0), 0.0)
    shares[config.PARTIES.index("OTH")] = max(100.0 - shares.sum(), 0.0)
    if shares.sum() <= 0:
        shares = latest_poll_average() * 100

    proj = project(shares, method=method, n_trials=N_TRIALS)
    summary = proj.sim.summary()

    cards = [
        html.Div(
            [
                html.Div(config.PARTY_NAMES[p], style={"fontWeight": 600, "color": config.PARTY_COLORS[p]}),
                html.Div(f"{summary.loc[p, 'mean']:.0f} seats", style={"fontSize": "1.4rem"}),
                html.Div(f"80%: {summary.loc[p, 'p10']:.0f}–{summary.loc[p, 'p90']:.0f}"),
                html.Div(
                    f"Most seats: {100 * summary.loc[p, 'p_most_seats']:.0f}% · "
                    f"Majority: {100 * summary.loc[p, 'p_majority']:.0f}%"
                ),
            ],
            style=CARD,
        )
        for p in ("LPC", "CPC")
    ]
    total = sum(float(v or 0) for v in values)
    note = f"Inputs sum to {total:.1f}%; the remainder goes to Other and all shares are normalized."
    table = riding_table(proj).to_dict("records")
    return seat_bar_chart(proj), seat_histogram(proj), region_map(proj), table, cards, note


CARD = {"border": "1px solid #ddd", "borderRadius": "8px", "padding": "12px 16px", "minWidth": "220px"}


def create_app() -> Dash:
    defaults = dict(zip(config.PARTIES, latest_poll_average() * 100, strict=True))
    app = Dash(__name__, title="Canadian Election Projections")

    inputs = [
        html.Div(
            [
                html.Label(
                    config.PARTY_NAMES[p], htmlFor=f"in-{p}", style={"color": config.PARTY_COLORS[p], "fontWeight": 600}
                ),
                dcc.Input(
                    id=f"in-{p}",
                    type="number",
                    min=0,
                    max=100,
                    step="any",
                    value=round(defaults[p], 1),
                    debounce=True,
                    style={"width": "80px"},
                ),
            ],
            style={"display": "flex", "flexDirection": "column", "gap": "4px"},
        )
        for p in INPUT_PARTIES
    ]

    app.layout = html.Div(
        [
            html.H1("Canadian Federal Election Seat Projections"),
            html.P(_poll_note(), style={"color": "#555"}),
            html.Div(
                inputs
                + [
                    html.Div(
                        [
                            html.Label("Swing model", htmlFor="method", style={"fontWeight": 600}),
                            dcc.Dropdown(
                                id="method",
                                options=list(SWING_METHODS),
                                value="proportional",
                                clearable=False,
                                style={"width": "160px"},
                            ),
                        ],
                        style={"display": "flex", "flexDirection": "column", "gap": "4px"},
                    ),
                    html.Button("Reset to polls", id="reset", n_clicks=0, style={"alignSelf": "flex-end"}),
                ],
                style={"display": "flex", "flexWrap": "wrap", "gap": "16px", "alignItems": "flex-start"},
            ),
            html.P(id="note", style={"color": "#555", "fontSize": "0.9rem"}),
            dcc.Loading(html.Div(id="cards", style={"display": "flex", "gap": "16px", "flexWrap": "wrap"})),
            dcc.Tabs(
                [
                    dcc.Tab(label="Seats", children=[dcc.Graph(id="bar")]),
                    dcc.Tab(label="Distribution", children=[dcc.Graph(id="hist")]),
                    dcc.Tab(label="Regions", children=[dcc.Graph(id="map")]),
                    dcc.Tab(
                        label="Ridings",
                        children=[
                            dash_table.DataTable(
                                id="ridings",
                                columns=[
                                    {"name": "Riding", "id": "riding_name"},
                                    {"name": "Prov.", "id": "province"},
                                    {"name": "Projected", "id": "projected"},
                                    {
                                        "name": "Win prob.",
                                        "id": "win_prob",
                                        "type": "numeric",
                                        "format": {"specifier": ".0%"},
                                    },
                                    {"name": "2025 winner", "id": "winner_2025"},
                                ],
                                filter_action="native",
                                sort_action="native",
                                page_size=25,
                                style_cell={"textAlign": "left", "padding": "4px 8px"},
                                style_data_conditional=[
                                    {"if": {"filter_query": "{flip} = true"}, "backgroundColor": "#fff4d6"},
                                    *[
                                        {
                                            "if": {"filter_query": f'{{projected}} = "{p}"', "column_id": "projected"},
                                            "color": config.PARTY_COLORS[p],
                                            "fontWeight": 600,
                                        }
                                        for p in config.PARTIES
                                    ],
                                ],
                            ),
                            html.P(
                                "Highlighted rows are projected to change hands from 2025.", style={"color": "#555"}
                            ),
                        ],
                    ),
                    dcc.Tab(label="Backtest (2025)", children=[dcc.Markdown(_backtest_markdown())]),
                ]
            ),
            html.P(
                "Model: uniform national swing to regions, then the selected swing model to ridings, "
                f"with shared national and regional error plus independent riding-level error ({N_TRIALS:,} simulations).",
                style={"color": "#777", "fontSize": "0.85rem", "marginTop": "24px"},
            ),
        ],
        style={"maxWidth": "1100px", "margin": "0 auto", "padding": "16px", "fontFamily": "system-ui, sans-serif"},
    )

    @app.callback(
        [Output(f"in-{p}", "value") for p in INPUT_PARTIES],
        Input("reset", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset(_):
        return [round(defaults[p], 1) for p in INPUT_PARTIES]

    @app.callback(
        Output("bar", "figure"),
        Output("hist", "figure"),
        Output("map", "figure"),
        Output("ridings", "data"),
        Output("cards", "children"),
        Output("note", "children"),
        [Input(f"in-{p}", "value") for p in INPUT_PARTIES],
        Input("method", "value"),
    )
    def update(*args):
        *values, method = args
        return compute(values, method)

    return app


# Exposed for WSGI servers (e.g. `gunicorn dashboard:server`).
app = create_app()
server = app.server

if __name__ == "__main__":
    app.run(debug=False, port=8050)
