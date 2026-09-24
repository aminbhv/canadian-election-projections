"""Plotly figures for the dashboard. Pure functions: projection in, figure out."""

import json
from functools import lru_cache

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from election import config
from election.projection import Projection, baseline

SHOWN_PARTIES = ("LPC", "CPC", "BQ", "NDP", "GPC")


def seat_bar_chart(proj: Projection) -> go.Figure:
    summary = proj.sim.summary().loc[list(SHOWN_PARTIES)]
    fig = go.Figure(
        go.Bar(
            x=[config.PARTY_NAMES[p] for p in summary.index],
            y=summary["mean"],
            marker_color=[config.PARTY_COLORS[p] for p in summary.index],
            error_y=dict(
                type="data",
                symmetric=False,
                array=summary["p90"] - summary["mean"],
                arrayminus=summary["mean"] - summary["p10"],
            ),
            hovertemplate="%{x}: %{y:.0f} seats<extra></extra>",
        )
    )
    fig.add_hline(
        y=config.MAJORITY_THRESHOLD,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Majority ({config.MAJORITY_THRESHOLD})",
    )
    fig.update_layout(
        title="Projected seats (bars: mean, whiskers: 80% interval)",
        yaxis_title="Seats",
        margin=dict(t=60, l=40, r=20, b=40),
    )
    return fig


def seat_histogram(proj: Projection, parties: tuple[str, ...] = ("LPC", "CPC")) -> go.Figure:
    fig = go.Figure()
    for p in parties:
        seats = proj.sim.seats[:, config.PARTIES.index(p)]
        fig.add_trace(
            go.Histogram(
                x=seats,
                name=config.PARTY_NAMES[p],
                opacity=0.65,
                marker_color=config.PARTY_COLORS[p],
                xbins=dict(size=2),
            )
        )
    fig.add_vline(x=config.MAJORITY_THRESHOLD, line_dash="dash", line_color="gray")
    fig.update_layout(
        barmode="overlay",
        title=f"Seat distribution across {proj.sim.n_trials:,} simulations",
        xaxis_title="Seats",
        yaxis_title="Simulations",
        margin=dict(t=60, l=40, r=20, b=40),
    )
    return fig


@lru_cache(maxsize=1)
def _geojson() -> dict:
    return json.loads(config.REGIONS_GEOJSON.read_text(encoding="utf-8"))


def region_map(proj: Projection) -> go.Figure:
    """Leading party by projected seats in each polling region (territories not drawn)."""
    base = baseline()
    region_of_riding = base.ridings["region"].to_numpy()
    fav = proj.sim.win_prob.argmax(axis=1)
    rows = []
    for g in config.REGIONS:
        if g == "TER":
            continue
        counts = np.bincount(fav[region_of_riding == g], minlength=len(config.PARTIES))
        leader = config.PARTIES[int(counts.argmax())]
        detail = ", ".join(f"{p} {c}" for p, c in zip(config.PARTIES, counts, strict=True) if c)
        rows.append({"region": config.REGION_NAMES[g], "leader": leader, "detail": detail})
    df = pd.DataFrame(rows)

    fig = go.Figure()
    for party, group in df.groupby("leader"):
        fig.add_trace(
            go.Choropleth(
                geojson=_geojson(),
                featureidkey="properties.name",
                locations=group["region"],
                z=[1] * len(group),
                colorscale=[[0, config.PARTY_COLORS[party]], [1, config.PARTY_COLORS[party]]],
                showscale=False,
                name=config.PARTY_NAMES[party],
                customdata=group["detail"],
                hovertemplate="<b>%{location}</b><br>%{customdata}<extra></extra>",
            )
        )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(title="Projected seat leader by region (hover for seat counts)", margin=dict(t=60, l=0, r=0, b=0))
    return fig
