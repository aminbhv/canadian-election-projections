"""
Canadian Election Simulator - Visualization Module

Copyright (c) 2025 Amin Behbudov, Fares Abdulmajeed Alabdulhadi, Tahmid Wasif Zaman, Dimural Murat.

This module handles data visualization for the election simulator.
"""

import json
import logging
from typing import Dict

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure

from config import PARTY_COLORS

logging.basicConfig(level=logging.INFO)


def make_bar_chart(seat_dist: Dict[str, list]) -> Figure:
    """
    Create a bar chart of average projected seat distribution.

    Args:
        seat_dist (Dict[str, list]): Seat distribution lists by party.

    Returns:
        Figure: Plotly bar chart figure.
    """
    avg = {party: sum(v) / len(v) for party, v in seat_dist.items() if v}
    df = pd.DataFrame({"Party": list(avg.keys()), "Seats": list(avg.values())})
    return px.bar(
        df,
        x="Party",
        y="Seats",
        color="Party",
        color_discrete_map=PARTY_COLORS,
        title="Projected Seat Distribution",
    )


def make_choropleth(polling_data: Dict[str, Dict[str, float]]) -> Figure:
    """
    Create a choropleth map showing the polling leader in each province.

    Args:
        polling_data (Dict[str, Dict[str, float]]): Polling data by province.

    Returns:
        Figure: Plotly choropleth map figure.
    """
    winners = {prov: max(polls, key=polls.get) for prov, polls in polling_data.items()}
    df = pd.DataFrame({"Province": list(winners.keys()), "Winner": list(winners.values())})

    try:
        with open("canada_provinces.geojson") as f:
            geojson = json.load(f)
        logging.info("Successfully loaded GeoJSON file")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error("Error loading GeoJSON file: %s", e)
        return px.bar(
            df,
            x="Province",
            y=[1] * len(df),
            color="Winner",
            color_discrete_map=PARTY_COLORS,
            title="Map unavailable — GeoJSON error",
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
            zoom=2.8,
            title="Projected Seat Leaders by Province",
        )
    except (ValueError, KeyError) as e:
        logging.error("Error creating choropleth: %s", e)
        return px.bar(
            df,
            x="Province",
            y=[1] * len(df),
            color="Winner",
            color_discrete_map=PARTY_COLORS,
            title="Map unavailable — Plotly error",
        )


if __name__ == "__main__":
    from scraper import scrape_polling_data

    poll_data = scrape_polling_data()
    if poll_data:
        fig = make_choropleth(poll_data)
        fig.show()
    else:
        logging.error("No polling data found.")
