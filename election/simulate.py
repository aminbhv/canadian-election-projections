"""Monte Carlo seat simulation under first-past-the-post.

Each trial draws three layers of error:

1. a national polling error per party, shared by every region
   (polls tend to miss in the same direction everywhere);
2. a regional error per party, shared by every riding in that region;
3. a riding-level error per party, independent across ridings.

The perturbed regional shares are swung onto every riding, and the party
with the most votes in a riding wins it. Because layers 1 and 2 are shared,
ridings move together, which is what makes seat totals uncertain. With only
independent riding noise, errors would average out across 343 ridings and
the simulation would be badly overconfident.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from election.config import MAJORITY_THRESHOLD, PARTIES
from election.data import ElectionResult
from election.swing import apply_swing


@dataclass(frozen=True)
class NoiseModel:
    """Standard deviations of each error layer, as vote-share fractions.

    Defaults were set before looking at the 2025 backtest: Canadian final-week
    polling averages typically miss a party's national share by about 1-3
    points (so national=0.02), regional subsamples miss by somewhat more, and
    riding-level error is scaled by sqrt(share) so a 40% party gets about
    5 points of riding noise and a 10% party about 2.5.
    """

    national: float = 0.02
    regional: float = 0.02
    riding: float = 0.08

    def scaled(self, factor: float) -> "NoiseModel":
        return NoiseModel(self.national * factor, self.regional * factor, self.riding * factor)


@dataclass(frozen=True)
class SimulationResult:
    seats: np.ndarray  # (T, P) seats won per trial
    win_prob: np.ndarray  # (R, P) share of trials each party won each riding
    point_shares: np.ndarray  # (R, P) projection with no noise

    @property
    def n_trials(self) -> int:
        return self.seats.shape[0]

    def point_winners(self) -> np.ndarray:
        return self.point_shares.argmax(axis=1)

    def point_seats(self) -> dict[str, int]:
        counts = np.bincount(self.point_winners(), minlength=len(PARTIES))
        return {p: int(c) for p, c in zip(PARTIES, counts, strict=True)}

    def summary(self) -> pd.DataFrame:
        """Seat distribution and government-formation odds for each party."""
        most = self.seats.max(axis=1, keepdims=True)
        sole_leader = (self.seats == most) & ((self.seats == most).sum(axis=1, keepdims=True) == 1)
        rows = []
        for j, party in enumerate(PARTIES):
            s = self.seats[:, j]
            rows.append(
                {
                    "party": party,
                    "mean": s.mean(),
                    "p10": np.percentile(s, 10),
                    "median": np.median(s),
                    "p90": np.percentile(s, 90),
                    "p_most_seats": sole_leader[:, j].mean(),
                    "p_majority": (s >= MAJORITY_THRESHOLD).mean(),
                }
            )
        return pd.DataFrame(rows).set_index("party")


def simulate(
    base: ElectionResult,
    regional_target: np.ndarray,
    n_trials: int = 10_000,
    method: str = "proportional",
    noise: NoiseModel = NoiseModel(),
    seed: int | None = 0,
    chunk_size: int = 2_000,
) -> SimulationResult:
    """Simulate seat outcomes.

    Args:
        base: the baseline election the swing is applied to.
        regional_target: projected regional shares, shape (G, P).
        n_trials: number of Monte Carlo trials.
        method: swing method, see election.swing.SWING_METHODS.
        noise: error standard deviations.
        seed: RNG seed for reproducibility (None for a fresh draw).
        chunk_size: trials processed per vectorized batch (bounds memory use).
    """
    rng = np.random.default_rng(seed)
    region_idx = base.region_index
    base_shares = base.shares
    base_reg_riding = base.regional_shares()[region_idx]  # (R, P)
    present_reg = regional_target > 0  # (G, P)
    n_regions, n_parties = regional_target.shape
    n_ridings = base_shares.shape[0]

    point = apply_swing(base_shares, base_reg_riding, regional_target[region_idx], method)

    seats = np.empty((n_trials, n_parties), dtype=np.int32)
    win_counts = np.zeros((n_ridings, n_parties))
    party_ids = np.arange(n_parties)

    for start in range(0, n_trials, chunk_size):
        t = min(chunk_size, n_trials - start)

        err_nat = rng.normal(0.0, noise.national, (t, 1, n_parties))
        err_reg = rng.normal(0.0, noise.regional, (t, n_regions, n_parties))
        reg = np.clip(regional_target[None] + (err_nat + err_reg) * present_reg, 0.0, None)
        totals = reg.sum(axis=-1, keepdims=True)
        reg = np.divide(reg, totals, out=np.zeros_like(reg), where=totals > 0)

        shares = apply_swing(base_shares, base_reg_riding, reg[:, region_idx], method)
        err_rid = rng.normal(0.0, noise.riding, shares.shape) * np.sqrt(shares)
        shares = np.where(shares > 0, shares + err_rid, -np.inf)

        winners = shares.argmax(axis=-1)  # (t, R)
        onehot = winners[..., None] == party_ids  # (t, R, P)
        seats[start : start + t] = onehot.sum(axis=1)
        win_counts += onehot.sum(axis=0)

    return SimulationResult(seats=seats, win_prob=win_counts / n_trials, point_shares=point)
