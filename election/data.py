"""Load riding-level results and polls into NumPy arrays the model can use."""

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import numpy as np
import pandas as pd

from election.config import PARTIES, REGION_BY_PROVINCE, REGIONS, TOTAL_SEATS


@dataclass(frozen=True)
class ElectionResult:
    """One election's results: a (ridings x parties) vote matrix plus riding metadata."""

    ridings: pd.DataFrame  # indexed by riding_id; columns riding_name, province, region
    votes: np.ndarray  # shape (R, P), columns in PARTIES order

    @cached_property
    def totals(self) -> np.ndarray:
        return self.votes.sum(axis=1)

    @cached_property
    def shares(self) -> np.ndarray:
        """Vote share of each party in each riding, shape (R, P)."""
        return self.votes / self.totals[:, None]

    @cached_property
    def region_index(self) -> np.ndarray:
        """Index into REGIONS for each riding, shape (R,)."""
        return self.ridings["region"].map(REGIONS.index).to_numpy()

    def regional_votes(self) -> np.ndarray:
        out = np.zeros((len(REGIONS), len(PARTIES)))
        np.add.at(out, self.region_index, self.votes)
        return out

    def regional_shares(self) -> np.ndarray:
        """Vote-weighted share of each party in each region, shape (G, P)."""
        reg = self.regional_votes()
        totals = reg.sum(axis=1, keepdims=True)
        return np.divide(reg, totals, out=np.zeros_like(reg), where=totals > 0)

    def region_weights(self) -> np.ndarray:
        """Each region's fraction of all valid votes, shape (G,)."""
        reg = self.regional_votes().sum(axis=1)
        return reg / reg.sum()

    def national_shares(self) -> np.ndarray:
        return self.votes.sum(axis=0) / self.votes.sum()

    def winners(self) -> np.ndarray:
        """Index into PARTIES of the winning party in each riding."""
        return self.votes.argmax(axis=1)

    def seat_counts(self) -> dict[str, int]:
        counts = np.bincount(self.winners(), minlength=len(PARTIES))
        return {p: int(c) for p, c in zip(PARTIES, counts, strict=True)}


def load_results(path: Path) -> ElectionResult:
    """Load a tidy results CSV (riding_id, riding_name, province, party, votes)."""
    df = pd.read_csv(path)
    required = {"riding_id", "riding_name", "province", "party", "votes"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path.name} is missing columns: {sorted(missing)}")

    unknown = set(df["party"]) - set(PARTIES)
    if unknown:
        raise ValueError(f"{path.name} has unknown party codes: {sorted(unknown)}")
    if (df["votes"] < 0).any():
        raise ValueError(f"{path.name} has negative vote counts")

    wide = df.pivot_table(index="riding_id", columns="party", values="votes", aggfunc="sum")
    wide = wide.reindex(columns=list(PARTIES), fill_value=0).fillna(0).sort_index()

    ridings = df.drop_duplicates("riding_id").set_index("riding_id").sort_index()
    ridings = ridings[["riding_name", "province"]].copy()
    ridings["region"] = ridings["province"].map(REGION_BY_PROVINCE)
    if ridings["region"].isna().any():
        bad = sorted(ridings.loc[ridings["region"].isna(), "province"].unique())
        raise ValueError(f"{path.name} has unknown provinces: {bad}")

    if len(ridings) != TOTAL_SEATS:
        raise ValueError(f"{path.name} has {len(ridings)} ridings, expected {TOTAL_SEATS}")

    votes = wide.to_numpy(dtype=float)
    if (votes.sum(axis=1) <= 0).any():
        raise ValueError(f"{path.name} has ridings with zero valid votes")

    return ElectionResult(ridings=ridings, votes=votes)


def load_polls(path: Path) -> pd.DataFrame:
    """Load a polls CSV with one row per poll and one percentage column per party."""
    df = pd.read_csv(path, parse_dates=["end_date"])
    missing = {"pollster", "end_date", "region", *PARTIES} - set(df.columns)
    if missing:
        raise ValueError(f"{path.name} is missing columns: {sorted(missing)}")
    df[list(PARTIES)] = df[list(PARTIES)].fillna(0.0)
    return df


def poll_average(polls: pd.DataFrame, region: str = "NAT") -> np.ndarray:
    """Average the most recent poll from each pollster; returns shares summing to 1.

    Taking one poll per firm stops pollsters that publish daily rolling polls
    from dominating the average.
    """
    subset = polls[polls["region"] == region]
    if subset.empty:
        raise ValueError(f"no polls for region {region!r}")
    latest = subset.sort_values("end_date").groupby("pollster").tail(1)
    mean = latest[list(PARTIES)].mean().to_numpy(dtype=float)
    return mean / mean.sum()
