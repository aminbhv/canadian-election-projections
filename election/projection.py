"""Project the next election from the 2025 results and the latest national polls.

Run:  python -m election.projection
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd

from election import config
from election.data import ElectionResult, load_polls, load_results, poll_average
from election.simulate import NoiseModel, SimulationResult, simulate
from election.swing import national_to_regional


@lru_cache(maxsize=1)
def baseline() -> ElectionResult:
    return load_results(config.RESULTS_2025)


@lru_cache(maxsize=1)
def latest_polls() -> pd.DataFrame:
    return load_polls(config.POLLS_LATEST)


def latest_poll_average() -> np.ndarray:
    return poll_average(latest_polls())


@dataclass(frozen=True)
class Projection:
    national: np.ndarray  # (P,) national shares used as input
    regional: np.ndarray  # (G, P) regional shares after uniform national swing
    sim: SimulationResult


def project(
    national: np.ndarray | None = None,
    method: str = "proportional",
    n_trials: int = 5_000,
    noise: NoiseModel = NoiseModel(),
    seed: int | None = 0,
) -> Projection:
    """Simulate seats for a national vote split (defaults to the latest poll average)."""
    base = baseline()
    if national is None:
        national = latest_poll_average()
    national = np.asarray(national, dtype=float)
    if national.shape != (len(config.PARTIES),) or (national < 0).any() or national.sum() <= 0:
        raise ValueError("national must be a non-negative vector with one entry per party")
    national = national / national.sum()

    regional = national_to_regional(national, base.national_shares(), base.regional_shares(), base.region_weights())
    sim = simulate(base, regional, n_trials, method=method, noise=noise, seed=seed)
    return Projection(national=national, regional=regional, sim=sim)


def riding_table(proj: Projection) -> pd.DataFrame:
    """One row per riding: projected favourite, its win probability, and the 2025 winner."""
    base = baseline()
    fav = proj.sim.win_prob.argmax(axis=1)
    df = base.ridings.reset_index()[["riding_id", "riding_name", "province"]].copy()
    df["projected"] = [config.PARTIES[i] for i in fav]
    df["win_prob"] = proj.sim.win_prob.max(axis=1).round(3)
    df["winner_2025"] = [config.PARTIES[i] for i in base.winners()]
    df["flip"] = df["projected"] != df["winner_2025"]
    return df


def main() -> None:
    polls = latest_polls()
    proj = project(n_trials=10_000)
    print(
        f"Polls: latest from each of {polls['pollster'].nunique()} firms, "
        f"{polls['end_date'].min():%Y-%m-%d} to {polls['end_date'].max():%Y-%m-%d}"
    )
    print("National input:", {p: f"{100 * s:.1f}%" for p, s in zip(config.PARTIES, proj.national, strict=True)})
    print()
    print(proj.sim.summary().round(2).to_string())


if __name__ == "__main__":
    main()
