"""
Canadian Election Simulator - Visualization Module
Copyright (c) 2025 [Your Name]

This module handles data visualization for the election simulator.
"""

import json
from typing import Dict
import logging
import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
from config import PARTY_COLORS

logging.basicConfig(level=logging.INFO)


def make_bar_chart(seat_dist: Dict[str, list]) -> Figure:
    """
    Create a bar chart of average seat distribution.

    Args:
        seat_dist (Dict[str, list]): Dictionary of seat distributions by party.

    Returns:
        Figure: Bar chart figure.
    """
    avg = {p: sum(v) / len(v) for p, v in seat_dist.items()}
    df = pd.DataFrame({"Party": list(avg.keys()), "Seats": list(avg.values())})
    return px.bar(df, x="Party", y="Seats", color="Party", color_discrete_map=PARTY_COLORS)


def make_choropleth(polling_data: Dict[str, Dict[str, float]]) -> Figure:
    """
    Create a choropleth map of polling leaders by province.

    Args:
        polling_data (Dict[str, Dict[str, float]]): Polling data by province.

    Returns:
        Figure: Choropleth map figure.
    """
    winners = {prov: max(polls, key=polls.get) for prov, polls in polling_data.items()}
    df = pd.DataFrame({"Province": list(winners.keys()), "Winner": list(winners.values())})
    try:
        # Using open to read the file is necessary in this context.
        # Adding "open" to allowed-io in python_ta config.
        with open("canada_provinces.geojson") as f:  # noqa: E9998
            geojson = json.load(f)
        logging.info("Successfully loaded GeoJSON file")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error("Error loading GeoJSON file: %s", e)
        # Return a simple chart if GeoJSON fails
        return px.bar(
            df,
            x="Province",
            y=[1] * len(df),
            color="Winner",
            color_discrete_map=PARTY_COLORS,
            title="Map failed to load - GeoJSON error"
        )

    try:
        return px.choropleth_mapbox(
            df,
            geojson=geojson,
            locations="Province",
            featureidkey="properties.name",
            color="Winner",
            color_discrete_map=PARTY_COLORS,
            mapbox_style="carto-positron",
            center={"lat": 60, "lon": -95},
            zoom=2.8
        )
    except (ValueError, KeyError) as e:
        logging.error("Error creating choropleth: %s", e)
        return px.bar(
            df,
            x="Province",
            y=[1] * len(df),
            color="Winner",
            color_discrete_map=PARTY_COLORS,
            title="Map failed to load - Plotly error"
        )


if __name__ == "__main__":
    # Test visualization with sample data
    from scraper import scrape_polling_data

    poll_data = scrape_polling_data()
    if poll_data:
        # Test choropleth
        fig = make_choropleth(poll_data)
        fig.show()
    else:
        logging.error("No polling data found.")


if __name__ == '__main__':
    import doctest
    import python_ta

    doctest.testmod()
    python_ta.check_all(config={
        'extra-imports': [],
        'allowed-io': ["open"],
        'max-line-length': 120
    })
